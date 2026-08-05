"""
Backup de saves de emuladores standalone no Android que rodam FORA do
RetroArch (não usam a convenção achatada saves_root/states_root) mas
já guardam save individualizado por jogo nativamente - achado em
05/08 explorando o aparelho real via adb:

  - **Dolphin (GameCube)**: um arquivo `.gci` por jogo, em
    `GC/<REGIÃO>/Card A|B/`. O nome do arquivo embute o código do jogo
    (ex: "70-GBTE-bayblade2002.gci" -> "GBTE").
  - **PPSSPP**: uma pasta por jogo em `SAVEDATA/<serial>` (ex:
    "ULUS10437GameData00" -> serial "ULUS-10437"). Nesse setup em
    particular o "memstick" do PPSSPP está configurado pra dentro da
    própria pasta de ROMs (`jogos_root/PSP/PSP/...`), não no local
    padrão do app.

Os dois guardam save E state juntos na mesma unidade (não tem uma
pasta "save" e outra "state" separada como o RetroArch) - por isso um
"item" aqui é sempre o arquivo/pasta inteiro de um jogo, ao contrário
da separação save/state que a galeria de capas faz pros sistemas
RetroArch (ver core/rom_rename.py find_flat_matches).

Achado ao explorar `~/Drive/Jogos/Saves/` no PC: o usuário já mantém
manualmente `Saves/Dolphin/` e `Saves/PPSSPP/` como espelho 1:1 da
pasta de dados de cada app no celular (`Saves/Dolphin/GC/<REGIÃO>/
Card X/*.gci`, `Saves/PPSSPP/SAVEDATA/<serial>/`) - o backup aqui
adota exatamente essa mesma estrutura em vez de inventar uma nova,
pra não duplicar convenção. "Backup" é só PUXAR (nunca escrever de
volta no celular) o que existe no aparelho e ainda não foi baixado -
como o destino já fica dentro da árvore sincronizada pelo Google
Drive, não precisa de nenhuma lógica de nuvem própria.

Dreamcast (Flycast, VMU compartilhado) e Wii/3DS (estrutura tipo NAND
por title-ID em hexadecimal, sem nome legível) ficaram de fora de
propósito - não são individualizados por jogo do jeito simples que dá
pra listar/nomear ainda. Ver docs/roadmap.md.
"""
import re
from pathlib import Path

from core import adb as adb_mod

_GC_GCI_RE = re.compile(r"^\d+-([A-Z0-9]{4})-")
_PSP_DIR_RE = re.compile(r"^([A-Z]{4})(\d{5})")

# android_root: pasta que espelha 1:1 com a local (dentro dela,
# scan_subdir é onde os itens individualizados ficam).
EMULATORS = {
    "GC": {
        "nome": "Dolphin - GameCube",
        "android_root": "/storage/emulated/0/Android/data/org.dolphinemu.dolphinemu/files",
        "local_root_name": "Dolphin",
        "scan_subdir": "GC",
        "kind": "file",
        "glob": "*.gci",
    },
    "PSP": {
        "nome": "PPSSPP",
        "android_root": "/storage/emulated/0/Jogos/PSP/PSP",
        "local_root_name": "PPSSPP",
        "scan_subdir": "SAVEDATA",
        "kind": "dir",
    },
}


def _gc_code(filename: str) -> str | None:
    m = _GC_GCI_RE.match(filename)
    return m.group(1) if m else None


def _psp_serial(dirname: str) -> str | None:
    m = _PSP_DIR_RE.match(dirname)
    return f"{m.group(1)}-{m.group(2)}" if m else None


def _resolve_name(emu: str, raw_name: str, serials_index: dict) -> str | None:
    if emu == "GC":
        code = _gc_code(raw_name)
        return serials_index.get("GC", {}).get(code) if code else None
    serial = _psp_serial(raw_name)
    return serials_index.get("PSP", {}).get(serial) if serial else None


def _local_root(emu: str, cfg: dict) -> Path:
    # irmã de saves_root/states_root, mesma árvore Saves/ sincronizada
    # pelo Google Drive - ver docstring do módulo.
    saves_root = Path(cfg["pc"]["saves_root"]).expanduser()
    return saves_root.parent / EMULATORS[emu]["local_root_name"]


def list_remote(emu: str, cfg: dict, serials_index: dict) -> list:
    """Lista os itens no celular via adb - um arquivo .gci (GC) ou uma
    pasta SAVEDATA/<serial> (PSP), cada um representando UM jogo.
    "rel_path" é o caminho relativo à raiz espelhada (ex:
    "GC/USA/Card A/x.gci"), usado tanto pra achar o local
    correspondente quanto pro pull preservar a mesma estrutura."""
    info = EMULATORS[emu]
    serial_dev = adb_mod.ensure_connected(cfg["android"].get("device_serial") or None)
    scan_root = f"{info['android_root']}/{info['scan_subdir']}"
    quoted = adb_mod.shquote(scan_root)
    if info["kind"] == "file":
        out = adb_mod.shell(f"find {quoted} -name {adb_mod.shquote(info['glob'])} 2>/dev/null", serial=serial_dev)
    else:
        out = adb_mod.shell(f"find {quoted} -mindepth 1 -maxdepth 1 -type d 2>/dev/null", serial=serial_dev)

    prefix = info["android_root"] + "/"
    items = []
    for path in (l.strip() for l in out.splitlines() if l.strip()):
        raw_name = path.rsplit("/", 1)[-1]
        rel_path = path[len(prefix):] if path.startswith(prefix) else raw_name
        items.append({
            "raw_name": raw_name, "path": path, "rel_path": rel_path,
            "name": _resolve_name(emu, raw_name, serials_index),
        })
    return items


def list_local(emu: str, cfg: dict) -> set:
    """Nomes já baixados na pasta local (mesma subárvore
    scan_subdir) - pra saber o que falta puxar."""
    info = EMULATORS[emu]
    scan_dir = _local_root(emu, cfg) / info["scan_subdir"]
    if not scan_dir.is_dir():
        return set()
    if info["kind"] == "file":
        return {p.name for p in scan_dir.rglob(info["glob"])}
    return {p.name for p in scan_dir.iterdir() if p.is_dir()}


def pull_item(emu: str, item: dict, cfg: dict) -> Path:
    """Puxa UM item (arquivo .gci ou pasta SAVEDATA/<serial> inteira)
    do celular, preservando a mesma estrutura relativa que já existe
    localmente. `adb pull` já copia pasta inteira recursivamente
    quando o remoto é um diretório."""
    dest = _local_root(emu, cfg) / item["rel_path"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    serial_dev = adb_mod.ensure_connected(cfg["android"].get("device_serial") or None)
    ok = adb_mod.pull(item["path"], dest, serial=serial_dev)
    if not ok:
        raise adb_mod.AdbError(f"falha ao puxar '{item['path']}'")
    return dest

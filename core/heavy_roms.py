"""
Gestão de ROMs dos consoles "pesados" (PS, SDC, PS2, GameCube, Wii, PSP,
3DS) - configurados em config.toml [heavy_systems]. Diferente de
[systems] (sempre sincronizado com o celular via Google Drive), esses
ficam só no PC até serem enviados sob demanda. Nintendo Switch fica de
fora de propósito - a gestão de ROM dele é feita por fora do PyRetro.

Um "item" aqui é qualquer entrada de primeiro nível dentro de
roms_root/<CODE>/ - normalmente um arquivo (.iso, .3ds, etc), mas o
suporte a pasta inteira como um item só fica pra formatos que usam
pasta por jogo (base + updates/DLC separados).

PS e SDC usam .cue/.gdi + .bin separado (achado em 02/08: .cue não está
sozinho na pasta - "Front Mission 3.cue" tem "Front Mission 3.bin" do
lado, e formatos multi-track como .gdi têm vários ".bin" tipo
"Sonic Adventure (Track 1).bin", "(Track 2).bin" etc). Mandar só o .cue/
.gdi sem os .bin quebra o jogo no celular - list_local soma o tamanho
dos sidecars no item, e send_to_phone manda todos juntos.

Visão do Google Drive (via `rclone`, achado em 04/08 - sugestão do
usuário): o Drive tem MUITO mais jogos do que o que já foi baixado pro
PC (ex: dezenas de PS2 na nuvem contra só 3 localmente) - list_drive_
names mostra o catálogo completo sem precisar do celular conectado via
adb, e download_from_drive baixa sob demanda. No PC, o download NUNCA
vai direto pra roms_root/<CODE>/ (que é a própria pasta sincronizada
pelo Google Drive Desktop - escrever ali enquanto o rclone baixa
arriscaria os dois mexerem no mesmo arquivo ao mesmo tempo) - baixa
primeiro em staging_dir (config [rclone], padrão ~/Downloads) e só
depois move pro lugar certo, um rename local instantâneo."""
import json
import re
import subprocess
from pathlib import Path

from core import adb as adb_mod

_TRACK_RE = re.compile(r"^(.+) \(Track \d+\)$")


def load_heavy_systems(cfg: dict) -> dict:
    return cfg.get("heavy_systems", {})


def _dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def _stem_matches(candidate_stem: str, primary_stem: str) -> bool:
    if candidate_stem == primary_stem:
        return True
    m = _TRACK_RE.match(candidate_stem)
    return bool(m and m.group(1) == primary_stem)


def _sidecars(primary: Path, exts_lower: set) -> list:
    """Arquivos vizinhos que pertencem ao mesmo item (mesmo nome base,
    ou "<nome> (Track N)") mas cuja extensão NÃO é uma das "primárias"
    do sistema - isso evita confundir um formato alternativo do mesmo
    jogo (ex: .cue E .chd juntos) com um sidecar de verdade."""
    sidecars = []
    for sib in primary.parent.iterdir():
        if sib == primary or not sib.is_file():
            continue
        if sib.suffix.lower().lstrip(".") in exts_lower:
            continue
        if _stem_matches(sib.stem, primary.stem):
            sidecars.append(sib)
    return sidecars


def list_local(code: str, roms_root: Path, exts: list) -> list:
    """[{name, size, is_dir, sidecar_count}], ordenado por nome. `name`
    é o que send_to_phone espera receber pra identificar o item. `size`
    já inclui os sidecars (.bin etc) quando existirem."""
    sysdir = roms_root / code
    if not sysdir.is_dir():
        return []
    exts_lower = {e.lower().lstrip(".") for e in exts}
    items = []
    for entry in sorted(sysdir.iterdir()):
        if entry.is_dir():
            items.append({"name": entry.name, "size": _dir_size(entry), "is_dir": True, "sidecar_count": 0})
        elif entry.is_file() and entry.suffix.lower().lstrip(".") in exts_lower:
            sidecars = _sidecars(entry, exts_lower)
            total = entry.stat().st_size + sum(s.stat().st_size for s in sidecars)
            items.append({"name": entry.name, "size": total, "is_dir": False, "sidecar_count": len(sidecars)})
    return items


def list_remote_names(code: str, jogos_root: str, serial: str | None) -> set:
    """Nomes (arquivo ou pasta) já presentes no celular pra esse
    sistema - uma chamada só via find, não uma por item. Retorna
    conjunto vazio (não levanta erro) se a pasta remota ainda não
    existir - é o caso normal na primeira vez."""
    remote_dir = f"{jogos_root.rstrip('/')}/{code}"
    try:
        out = adb_mod.shell(
            f"find {adb_mod.shquote(remote_dir)} -mindepth 1 -maxdepth 1 2>/dev/null",
            serial=serial,
        )
    except adb_mod.AdbError:
        return set()
    prefix = remote_dir + "/"
    names = set()
    for line in out.splitlines():
        line = line.strip()
        if line.startswith(prefix):
            names.add(line[len(prefix):])
    return names


def send_to_phone(code: str, name: str, roms_root: Path, jogos_root: str, serial: str | None,
                   exts: list, overwrite: bool = False) -> tuple[bool, str]:
    """Manda UM item (arquivo ou pasta) pro celular via adb push, junto
    com os sidecars (.bin de .cue/.gdi) se houver. Nunca sobrescreve por
    padrão - confere se o item principal já existe lá antes. Retorna
    (ok, mensagem)."""
    local_path = roms_root / code / name
    if not local_path.exists():
        return False, "não encontrado no PC"

    remote_dir = f"{jogos_root.rstrip('/')}/{code}"
    remote_path = f"{remote_dir}/{name}"

    if not overwrite:
        try:
            out = adb_mod.shell(f"[ -e {adb_mod.shquote(remote_path)} ] && echo EXISTS", serial=serial)
        except adb_mod.AdbError:
            out = ""
        if "EXISTS" in out:
            return False, "já existe no celular (use overwrite pra sobrescrever)"

    adb_mod.run(["shell", "mkdir", "-p", remote_dir], serial=serial, timeout=15)

    to_send = [local_path]
    if local_path.is_file():
        exts_lower = {e.lower().lstrip(".") for e in exts}
        to_send += _sidecars(local_path, exts_lower)

    for src in to_send:
        ok = adb_mod.push(src, f"{remote_dir}/{src.name}", serial=serial, timeout=1800)
        if not ok:
            return False, f"falha ao enviar '{src.name}'" + (f" ({len(to_send)} arquivos no total)" if len(to_send) > 1 else "")

    plural = "s" if len(to_send) != 1 else ""
    return True, f"enviado ({len(to_send)} arquivo{plural})"


def _rclone_cfg(cfg: dict) -> dict:
    rc = cfg.get("rclone", {})
    return {
        "remote": rc.get("remote", "drive"),
        "drive_roms_root": rc.get("drive_roms_root", "Jogos/ROMs"),
        "staging_dir": rc.get("staging_dir", "~/Downloads"),
    }


def list_drive_items(code: str, cfg: dict) -> list:
    """[{name, size, is_dir}] presentes no Google Drive pra esse sistema
    via `rclone lsjson` - não depende de adb nem do celular conectado,
    só do rclone configurado (`rclone config`, remote definido em
    config.toml [rclone]). Retorna lista vazia (não levanta erro) se o
    rclone não estiver instalado/configurado, ou a pasta não existir no
    Drive ainda.

    Achado em 04/08: pastas com muitos itens (PS2 com 97) podem levar
    até ~1min pra listar via API do Drive - um timeout de 30s cortava
    isso no meio e devolvia lista vazia silenciosamente (parecia "nada
    no Drive" quando na verdade só estava demorando). Timeout mais
    generoso (90s)."""
    rc = _rclone_cfg(cfg)
    remote_path = f"{rc['remote']}:{rc['drive_roms_root']}/{code}"
    try:
        r = subprocess.run(
            ["rclone", "lsjson", remote_path],
            capture_output=True, text=True, timeout=90,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    if r.returncode != 0:
        return []
    try:
        entries = json.loads(r.stdout)
    except ValueError:
        return []
    return [
        {"name": e["Name"], "size": max(e.get("Size", 0), 0), "is_dir": bool(e.get("IsDir"))}
        for e in entries
    ]


def download_from_drive(code: str, name: str, roms_root: Path, cfg: dict) -> tuple[bool, str]:
    """Baixa um item do Drive pro PC via rclone. Nunca escreve direto em
    roms_root/<CODE>/ (pasta sincronizada pelo Google Drive Desktop) -
    baixa primeiro em staging_dir e só move pro lugar certo depois que
    o download termina por completo (ver docstring do módulo)."""
    rc = _rclone_cfg(cfg)
    remote_path = f"{rc['remote']}:{rc['drive_roms_root']}/{code}/{name}"
    staging = Path(rc["staging_dir"]).expanduser()
    staging.mkdir(parents=True, exist_ok=True)

    dest_final = roms_root / code / name
    if dest_final.exists():
        return False, "já existe no PC"

    r = subprocess.run(
        ["rclone", "copy", remote_path, str(staging)],
        capture_output=True, text=True, timeout=3600,
    )
    if r.returncode != 0:
        return False, f"rclone falhou: {r.stderr.strip()[:200]}"

    staged_path = staging / name
    if not staged_path.exists():
        return False, "rclone terminou mas o arquivo não apareceu no staging"

    dest_final.parent.mkdir(parents=True, exist_ok=True)
    staged_path.rename(dest_final)
    return True, "baixado"

"""
Sync de verdade (mais recente vence) pros saves que moram DENTRO da
sandbox do próprio emulador, em vez de escrever direto na árvore
sincronizada pelo Google Drive - Dolphin (GC/Wii) nos dois lados
(PC/Android) e o lado Android do PS2 (AetherSX2, já que o PCSX2 do PC
já escreve direto em Saves/PS2 desde 22/08).

Substitui os dois mecanismos parciais que já existiam pra Dolphin:
- core/pc_backup.py só copiava PC->Drive (nunca trazia Drive->PC de
  volta pra quem ficou pra trás jogando no outro aparelho).
- core/emu_saves.py só puxava Android->Drive por PRESENÇA (nome já
  existe? não baixa de novo) - se o MESMO save fosse atualizado nos
  dois lados entre uma sync e outra, o mais recente podia nunca chegar
  no outro aparelho.

Aqui a comparação é sempre por mtime real (adb push/pull -a preserva
o mtime da origem, senão a comparação da próxima rodada ficaria
inventando "mudança" toda vez). O próprio arquivo em Drive serve de
"última versão conhecida" - não precisa de manifesto à parte. Se as
duas pontas fora do Drive (PC e Android) avançaram além do que Drive
tem E têm mtimes diferentes entre si, é conflito real: não decide
sozinho, entra numa lista pra revisão manual (mesma regra de
core/sync.py). Nunca apaga nada - só copia o que está mais novo pra
quem ficou pra trás, dry-run por padrão (só escreve com apply=True).

Rodando local no Android (Termux, ver docs/termux_setup.md) não tem
"outro lado" pra falar via adb - o próprio app já É o celular. Nesse
caso (local_mode=True, auto-detectado via running_in_termux()) a
perna "PC" nem existe (ninguém alcança a sandbox do emulador no PC
sem adb no sentido contrário) e a perna "Android" vira acesso a
arquivo local direto, sem adb nenhum - o PC roda a MESMA sync no seu
lado (local_mode=False) contra a mesma pasta do Drive, e é o próprio
Google Drive/FolderSync que carrega o resultado de um aparelho pro
outro (arquitetura de "dois modos" do roadmap.md - nenhum modo fala
com o outro diretamente, os dois só falam com Drive).

Exige permissão "Acesso a todos os arquivos" pro Termux (Android 11+)
pra alcançar a pasta de outro app (Android/data/<pacote>/files) -
mesma restrição que valeria pra qualquer app que não seja o `adb
shell` (que tem esse privilégio de depuração por padrão). Sem essa
permissão, a leitura local da pasta do emulador falha - não testado
ainda no aparelho real (ver docs/termux_setup.md)."""
import os
import shutil
from pathlib import Path

from core import adb as adb_mod

MTIME_EPSILON = 2.0


def running_in_termux() -> bool:
    return "com.termux" in os.environ.get("PREFIX", "")


def _dolphin_android_root(sub: str) -> str:
    return f"/storage/emulated/0/Android/data/org.dolphinemu.dolphinemu/files/{sub}"


SOURCES = {
    "dolphin_gc": {
        "nome": "Dolphin - GameCube",
        "get_pc_root": lambda cfg: Path(cfg["pc"]["dolphin_data_root"]).expanduser() / "GC",
        "get_drive_root": lambda cfg: Path(cfg["pc"]["saves_root"]).expanduser().parent / "Dolphin" / "GC",
        "android_root": _dolphin_android_root("GC"),
    },
    "dolphin_wii": {
        "nome": "Dolphin - Wii",
        "get_pc_root": lambda cfg: Path(cfg["pc"]["dolphin_data_root"]).expanduser() / "Wii" / "title",
        "get_drive_root": lambda cfg: Path(cfg["pc"]["saves_root"]).expanduser().parent / "Dolphin" / "Wii" / "title",
        "android_root": _dolphin_android_root("Wii/title"),
        # cada title-ID tem "content/" (o app/canal instalado em si -
        # .app/.tmd, é conteúdo de sistema, não save) e "data/" (o save
        # de verdade) - só o segundo interessa, senão sincronizaria
        # canal/firmware inteiro entre PC e celular à toa (achado real:
        # sem esse filtro, "all" gerou 330+ ações que eram tudo .app/.tmd).
        "rel_filter": lambda rel: "/data/" in rel.replace("\\", "/"),
    },
    "ps2_memcards": {
        "nome": "PS2 - Memory Cards",
        "get_pc_root": None,  # PCSX2 (PC) já escreve direto em Drive - só falta a perna Android
        "get_drive_root": lambda cfg: Path(next(iter(cfg["memcards"]["ps2"].values()))).expanduser().parent,
        "android_root": "/storage/emulated/0/Android/data/xyz.aethersx2.android/files/memcards",
    },
    "ps2_sstates": {
        "nome": "PS2 - Savestates",
        "get_pc_root": None,
        "get_drive_root": lambda cfg: Path(cfg["pc"]["saves_root"]).expanduser().parent / "PS2" / "sstates",
        "android_root": "/storage/emulated/0/Android/data/xyz.aethersx2.android/files/sstates",
    },
}


def _local_mtimes(root: Path) -> dict:
    if not root.is_dir():
        return {}
    return {str(p.relative_to(root)): p.stat().st_mtime for p in root.rglob("*") if p.is_file()}


def _android_mtimes(android_root: str, serial: str | None) -> dict:
    """Uma chamada só (find + stat), mesma técnica de core/sync.py -
    achado real lá: overhead de processo adb por arquivo não escala."""
    root = android_root.rstrip("/")
    quoted = adb_mod.shquote(root)
    out = adb_mod.shell(f"find {quoted} -type f -exec stat -c '%Y %n' {{}} \\; 2>/dev/null", serial=serial)
    prefix = root + "/"
    result = {}
    for line in out.splitlines():
        line = line.rstrip("\n")
        if " " not in line:
            continue
        mtime_s, path = line.split(" ", 1)
        try:
            mtime = float(mtime_s)
        except ValueError:
            continue
        rel = path[len(prefix):] if path.startswith(prefix) else path
        result[rel] = mtime
    return result


def plan(source_key: str, cfg: dict, serial: str | None = None, local_mode: bool = False) -> dict:
    """{"actions": [...], "conflicts": [...]}. action:
    {source, rel_path, direction} - direction em "pc->drive",
    "drive->pc", "android->drive", "drive->android". Nunca escreve
    nada - só lê (local via os.stat, Android via um `find`+`stat` só,
    ou local também quando local_mode=True - ver docstring do módulo).

    local_mode=True: sem perna PC (não alcançável a partir do celular
    sem adb no sentido contrário) e a perna "android" é lida como
    pasta local de verdade, sem adb."""
    info = SOURCES[source_key]
    drive_root = info["get_drive_root"](cfg)
    pc_root = None if local_mode else (info["get_pc_root"](cfg) if info["get_pc_root"] else None)

    drive_m = _local_mtimes(drive_root)
    pc_m = _local_mtimes(pc_root) if pc_root else {}
    android_m = _local_mtimes(Path(info["android_root"])) if local_mode else _android_mtimes(info["android_root"], serial)

    rel_filter = info.get("rel_filter")
    if rel_filter:
        drive_m = {k: v for k, v in drive_m.items() if rel_filter(k)}
        pc_m = {k: v for k, v in pc_m.items() if rel_filter(k)}
        android_m = {k: v for k, v in android_m.items() if rel_filter(k)}

    actions, conflicts = [], []
    for rel in sorted(set(drive_m) | set(pc_m) | set(android_m)):
        d, p, a = drive_m.get(rel), pc_m.get(rel), android_m.get(rel)
        pc_ahead = pc_root is not None and p is not None and (d is None or p > d + MTIME_EPSILON)
        android_ahead = a is not None and (d is None or a > d + MTIME_EPSILON)

        if pc_ahead and android_ahead and abs(p - a) > MTIME_EPSILON:
            conflicts.append({"source": source_key, "rel_path": rel, "pc_mtime": p, "android_mtime": a, "drive_mtime": d})
            continue

        winner = d
        if pc_ahead:
            actions.append({"source": source_key, "rel_path": rel, "direction": "pc->drive"})
            winner = p
        elif android_ahead:
            actions.append({"source": source_key, "rel_path": rel, "direction": "android->drive"})
            winner = a

        if pc_root is not None and not pc_ahead and winner is not None and (p is None or winner > p + MTIME_EPSILON):
            actions.append({"source": source_key, "rel_path": rel, "direction": "drive->pc"})
        if not android_ahead and winner is not None and (a is None or winner > a + MTIME_EPSILON):
            actions.append({"source": source_key, "rel_path": rel, "direction": "drive->android"})

    return {"actions": actions, "conflicts": conflicts}


def apply(actions: list, cfg: dict, serial: str | None = None, local_mode: bool = False) -> list:
    """Executa as ações do plan(). Retorna [{**action, "ok", "erro"?}].
    local_mode=True: "android->drive"/"drive->android" viram cópia de
    arquivo local (mesma pasta lida direto, sem adb) - ver plan()."""
    results = []
    for item in actions:
        info = SOURCES[item["source"]]
        drive_root = info["get_drive_root"](cfg)
        pc_root = None if local_mode else (info["get_pc_root"](cfg) if info["get_pc_root"] else None)
        android_root = Path(info["android_root"])
        rel = item["rel_path"]
        direction = item["direction"]
        try:
            if direction == "pc->drive":
                dest = drive_root / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(pc_root / rel, dest)
            elif direction == "drive->pc":
                dest = pc_root / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(drive_root / rel, dest)
            elif direction == "android->drive":
                dest = drive_root / rel
                if local_mode:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(android_root / rel, dest)
                elif not adb_mod.pull(f"{info['android_root'].rstrip('/')}/{rel}", dest, serial=serial, archive=True):
                    raise adb_mod.AdbError("adb pull falhou")
            elif direction == "drive->android":
                if local_mode:
                    dest = android_root / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(drive_root / rel, dest)
                elif not adb_mod.push(drive_root / rel, f"{info['android_root'].rstrip('/')}/{rel}", serial=serial, archive=True):
                    raise adb_mod.AdbError("adb push falhou")
            results.append({**item, "ok": True})
        except Exception as e:
            results.append({**item, "ok": False, "erro": str(e)})
    return results

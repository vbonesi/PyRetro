"""
Snapshot datado de retroarch.cfg + config/ (shaders/opções/remaps por
core) + playlists/ (incluindo builtin/ e logs/) pro PC e/ou celular -
mesma pasta/prefixo que já vinha sendo feito na mão
(Backups/retroarch_<pc|android>_<data>/, ver pasta existente, backups
de 31/07 e 20/08). Só esses três - não inclui cores/ (redownloadável,
ver docs/roadmap.md), nem saves/states/thumbnails (já têm sync próprio,
ver core/pc_backup.py e core/sync.py), nem downloads/screenshots/system
(BIOS - já vive em ROMs/<CODE>/, sincronizado pelo Drive).

Cada rodada cria uma pasta NOVA (nome com a data de hoje) - nunca
sobrescreve uma data anterior, mesma filosofia de nunca apagar do
resto do projeto (ver README "Princípios").

PC: retroarch_root em config.toml [pc] aponta pra raiz do profile
Flatpak (retroarch.cfg fica direto nela, config/ e playlists/ são
subpastas). Android: retroarch_root em [android] é a raiz pública
("/storage/emulated/0/RetroArch", tem config/ e playlists/ mas NÃO o
.cfg) - o retroarch.cfg do celular mora em local separado, dentro da
pasta privada do app (retroarch_cfg_path), só acessível porque o
arquivo em si é 0666 (confirmado via `adb shell stat` em 24/08).
"""
import shutil
from datetime import date
from pathlib import Path

from core import adb as adb_mod


def _copy_tree(src: Path, dst: Path) -> int:
    if not src.is_dir():
        return 0
    count = 0
    for f in src.rglob("*"):
        if f.is_file():
            dest = dst / f.relative_to(src)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)
            count += 1
    return count


def _count_files(root: Path) -> int:
    return sum(1 for f in root.rglob("*") if f.is_file()) if root.is_dir() else 0


def backup_pc(cfg: dict, backups_root: Path, apply: bool, today: str | None = None) -> dict:
    root = Path(cfg["pc"]["retroarch_root"]).expanduser()
    dest = backups_root / f"retroarch_pc_{today or date.today().isoformat()}"
    plan = {
        "dest": dest,
        "cfg_src": root / "retroarch.cfg",
        "config_src": root / "config",
        "playlists_src": root / "playlists",
    }
    if not apply:
        return plan
    dest.mkdir(parents=True, exist_ok=True)
    n_cfg = 0
    if plan["cfg_src"].is_file():
        shutil.copy2(plan["cfg_src"], dest / "retroarch.cfg")
        n_cfg = 1
    plan["counts"] = {
        "retroarch.cfg": n_cfg,
        "config": _copy_tree(plan["config_src"], dest / "config"),
        "playlists": _copy_tree(plan["playlists_src"], dest / "playlists"),
    }
    return plan


def backup_android(cfg: dict, backups_root: Path, serial: str | None, apply: bool, today: str | None = None) -> dict:
    android = cfg["android"]
    dest = backups_root / f"retroarch_android_{today or date.today().isoformat()}"
    root = android["retroarch_root"].rstrip("/")
    plan = {
        "dest": dest,
        "cfg_src": android["retroarch_cfg_path"],
        "config_src": f"{root}/config",
        "playlists_src": f"{root}/playlists",
    }
    if not apply:
        return plan
    dest.mkdir(parents=True, exist_ok=True)
    ok_cfg = adb_mod.pull(plan["cfg_src"], dest / "retroarch.cfg", serial=serial, timeout=60)
    ok_config = adb_mod.pull(plan["config_src"], dest / "config", serial=serial, timeout=300)
    ok_playlists = adb_mod.pull(plan["playlists_src"], dest / "playlists", serial=serial, timeout=300)
    plan["ok"] = {"retroarch.cfg": ok_cfg, "config": ok_config, "playlists": ok_playlists}
    plan["counts"] = {
        "retroarch.cfg": int(ok_cfg),
        "config": _count_files(dest / "config"),
        "playlists": _count_files(dest / "playlists"),
    }
    return plan

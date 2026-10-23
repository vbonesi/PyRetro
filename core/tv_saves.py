"""Saves de um jogo pelo modo TV, com escrita que sempre pode ser desfeita.

Nada é apagado de vez: guardar copia os arquivos do jogo para
`<backups_root>/Saves do modo TV/<código>/<label>/<data>/`; apagar guarda a
cópia e só então remove o original; restaurar guarda primeiro o que está em
uso e depois copia a versão escolhida de volta. Cada cópia tem um
`manifesto.json` com nome, tipo (save/state) e se o arquivo vinha da raiz
antiga (`legado`), para voltar ao mesmo lugar.
"""
import json
import shutil
import time
from pathlib import Path

from core import rom_rename

PASTA = "Saves do modo TV"


def _roots(saves_dir: Path, states_dir: Path) -> dict:
    return {"save": Path(saves_dir), "state": Path(states_dir)}


def _target(roots: dict, code: str, item: dict) -> Path:
    root = roots[item["kind"]]
    return (root if item["legado"] else root / code) / item["name"]


def _game_dir(backups_root: Path, code: str, label: str) -> Path:
    for part in (code, label):
        if not part or "/" in part or "\\" in part or part.startswith(".") or "\x00" in part:
            raise ValueError("nome inválido")
    return Path(backups_root).expanduser() / PASTA / code / label


def _stamp(base: Path) -> Path:
    stamp = time.strftime("%Y-%m-%d_%H%M%S")
    dest, n = base / stamp, 2
    while dest.exists():  # duas ações no mesmo segundo não se sobrepõem
        dest, n = base / f"{stamp}_{n}", n + 1
    return dest


def _copy(items: list, roots: dict, code: str, base: Path, motivo: str) -> str:
    dest = _stamp(base)
    dest.mkdir(parents=True)
    for item in items:
        shutil.copy2(_target(roots, code, item), dest / f"{item['kind']}-{item['name']}")
    manifesto = {"motivo": motivo, "arquivos": [{k: i[k] for k in ("name", "kind", "legado", "size")} for i in items]}
    (dest / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1))
    return dest.name


def backup(saves_dir, states_dir, backups_root, code: str, label: str, motivo: str = "cópia") -> dict:
    items = rom_rename.game_saves(saves_dir, states_dir, code, label)
    if not items:
        raise ValueError("este jogo não tem save nem estado no PC")
    stamp = _copy(items, _roots(saves_dir, states_dir), code, _game_dir(backups_root, code, label), motivo)
    return {"stamp": stamp, "files": len(items)}


def remove(saves_dir, states_dir, backups_root, code: str, label: str, name: str, kind: str, legado: bool) -> dict:
    """Apaga UM arquivo listado pela ficha, depois de guardar a cópia."""
    item = next((i for i in rom_rename.game_saves(saves_dir, states_dir, code, label)
                 if i["name"] == name and i["kind"] == kind and i["legado"] == bool(legado)), None)
    if item is None:
        raise LookupError("arquivo não pertence a este jogo")
    roots = _roots(saves_dir, states_dir)
    stamp = _copy([item], roots, code, _game_dir(backups_root, code, label), f"apagado: {name}")
    _target(roots, code, item).unlink()
    return {"stamp": stamp}


def list_backups(backups_root, code: str, label: str) -> list:
    base = _game_dir(backups_root, code, label)
    out = []
    if base.is_dir():
        for d in sorted(base.iterdir(), reverse=True):
            try:
                manifesto = json.loads((d / "manifesto.json").read_text())
            except (OSError, ValueError):
                continue
            out.append({"stamp": d.name, "motivo": manifesto.get("motivo", ""), "arquivos": manifesto.get("arquivos", [])})
    return out


def restore(saves_dir, states_dir, backups_root, code: str, label: str, stamp: str) -> dict:
    """Volta os arquivos de uma cópia. O que está em uso é guardado antes."""
    base = _game_dir(backups_root, code, label)
    if not stamp or "/" in stamp or "\\" in stamp or stamp.startswith("."):
        raise ValueError("cópia inválida")
    source = base / stamp
    try:
        manifesto = json.loads((source / "manifesto.json").read_text())
    except (OSError, ValueError):
        raise LookupError("cópia não encontrada") from None
    roots = _roots(saves_dir, states_dir)
    arquivos = manifesto.get("arquivos", [])
    for item in arquivos:
        if item.get("kind") not in roots or not rom_rename.is_save_of(item.get("name", ""), Path(label).stem) and \
                not rom_rename.is_save_of(item.get("name", ""), label):
            raise ValueError("manifesto com arquivo de outro jogo")
        if not (source / f"{item['kind']}-{item['name']}").is_file():
            raise LookupError(f"arquivo ausente na cópia: {item['name']}")
    current = rom_rename.game_saves(saves_dir, states_dir, code, label)
    safety = _copy(current, roots, code, base, f"antes de restaurar {stamp}") if current else None
    for item in arquivos:
        target = _target(roots, code, item)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / f"{item['kind']}-{item['name']}", target)
    return {"restored": len(arquivos), "safety": safety}

"""Registro local de "último jogado" pelo modo TV.

Fica em cache/ (não no library.json sincronizado): é um detalhe deste PC e
não precisa de campo novo no esquema da Biblioteca.
"""
import json
from datetime import datetime
from pathlib import Path

from core import covers as covers_mod
from core import file_lock


def rom_key(code, name):
    """Chave de uma ROM: sistema + nome normalizado do jogo (pasta ou arquivo sem extensão)."""
    first, _, rest = str(name).partition('/')
    stem = first if rest else Path(first).stem
    return f'rom:{code}:{covers_mod.normalize(stem)}'


def pc_key(game_id):
    return f'pc:{game_id}'


def load(path):
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, str)} if isinstance(data, dict) else {}


def touch(path, key, now=None):
    path = Path(path)
    with file_lock.exclusive(path):
        data = load(path)
        data[key] = (now or datetime.now()).isoformat(timespec='seconds')
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + '.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1))
        tmp.replace(path)

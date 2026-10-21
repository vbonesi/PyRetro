"""Leva junto, depois de renomear uma ROM, tudo que se liga a ela pelo nome.

A cascata de `rom_rename` cuida de arquivo (ROM, capa, save/state). O resto do
PyRetro também identifica o jogo pelo nome:

- Biblioteca: `find_for_rom` acha o registro pelo nome normalizado + sistema.
  Sem o nome novo em `nomes_alt`, progresso/nota/tempo da Biblioteca somem
  da ROM renomeada.
- Modo TV: favoritos, recentes, tempo e mídia usam `rom:<code>:<normalizado>`.
- Android: guarda favoritos/fixados/tempo/pendências com a mesma chave; o app
  lê `key_aliases.json` (via /api/tv/key_aliases) e migra o que tiver.

Renomear só tag de região ("Aladdin" → "Aladdin (USA)") não muda a chave
normalizada, então nada aqui é necessário nesse caso.
"""
import json
import os
import tempfile
from pathlib import Path

from core import covers as covers_mod
from core import file_lock
from core import library as library_mod
from core import playtime as playtime_mod
from core import recent as recent_mod
from core import tv_media as tv_media_mod

MAX_ALIASES = 5000


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name + '-')
    try:
        with os.fdopen(fd, 'w') as output:
            json.dump(data, output, ensure_ascii=False)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def rom_key(code: str, label: str) -> str:
    # label é o nome sem extensão; o sufixo evita que Path.stem corte "Mr. Driller".
    return recent_mod.rom_key(code, label + '.rom')


def link_library(library: dict, code: str, old_label: str, new_label: str) -> dict | None:
    """Acrescenta o nome novo em nomes_alt do registro da ROM antiga. Devolve o
    registro alterado, ou None se não havia vínculo ou se já casa sozinho."""
    if covers_mod.normalize(old_label) == covers_mod.normalize(new_label):
        return None
    index = library_mod.index_by_rom_name(library)
    game = library_mod.find_for_rom(index, old_label, code)
    if not game or library_mod.find_for_rom(index, new_label, code):
        return None
    game.setdefault('nomes_alt', [])
    if new_label not in game['nomes_alt']:
        game['nomes_alt'].append(new_label)
    return game


def move_tv_data(old: str, new: str, *, prefs_path, recent_path, playtime_path, media_root, aliases_path) -> dict:
    """Migra favoritos/recentes/tempo/mídia de `old` para `new` e registra o
    apelido. Nunca apaga dado: se a chave nova já tem algo, soma/mescla."""
    moved = {}
    if old == new:
        return moved
    prefs_path, recent_path, playtime_path = Path(prefs_path), Path(recent_path), Path(playtime_path)

    if prefs_path.exists():
        with file_lock.exclusive(prefs_path):
            data = json.loads(prefs_path.read_text())
            favorites = data.get('favorites', [])
            if old in favorites:
                data['favorites'] = list(dict.fromkeys(new if k == old else k for k in favorites))
                _write_json(prefs_path, data); moved['favorito'] = True

    if recent_path.exists():
        with file_lock.exclusive(recent_path):
            data = recent_mod.load(recent_path)
            if old in data:
                when = data.pop(old)
                data[new] = max(when, data.get(new, ''))
                _write_json(recent_path, data); moved['recente'] = True

    if playtime_path.exists():
        with file_lock.exclusive(playtime_path):
            games = playtime_mod.load(playtime_path)
            if old in games:
                source = games.pop(old)
                target = games.setdefault(new, {'seconds': 0, 'sessions': 0, 'automaticSeconds': 0, 'manualSeconds': 0, '_events': []})
                for field in ('seconds', 'sessions', 'automaticSeconds', 'manualSeconds'):
                    target[field] += source.get(field, 0)
                target['_events'] = list(dict.fromkeys(target['_events'] + source.get('_events', [])))
                if source.get('lastSession', '') > target.get('lastSession', ''):
                    target['lastSession'] = source['lastSession']
                _write_json(playtime_path, {'version': 1, 'games': games}); moved['tempo'] = True

    old_media, new_media = tv_media_mod.folder(media_root, old), tv_media_mod.folder(media_root, new)
    if old_media.is_dir() and not new_media.exists():
        old_media.rename(new_media); moved['midia'] = True

    aliases_path = Path(aliases_path)
    with file_lock.exclusive(aliases_path):
        aliases = load_aliases(aliases_path)
        # Encadeia renomeações antigas que apontavam para `old`.
        aliases = {k: (new if v == old else v) for k, v in aliases.items() if k != new}
        aliases[old] = new
        _write_json(aliases_path, dict(list(aliases.items())[-MAX_ALIASES:]))
    return moved


def load_aliases(path) -> dict:
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, str)} if isinstance(data, dict) else {}

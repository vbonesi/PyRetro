"""Preferências e tela inicial do console. Persistência local, fora da Biblioteca."""
import json
import os
from pathlib import Path
import tempfile

from core import file_lock, recent, playtime, tv_media, library, library_activity


def item_key(game):
    if game.get('code'):
        # romName pode ser um label sem extensão; acrescentá-la evita que
        # Path.stem remova parte de títulos como "Mr. Driller".
        name = game['romName']
        suffix = Path(name).suffix.lower()
        exts = {'.zip', '.7z', '.nes', '.sfc', '.smc', '.gb', '.gbc', '.gba', '.nds',
                '.n64', '.z64', '.v64', '.md', '.gen', '.bin', '.sms', '.gg', '.pce',
                '.cue', '.gdi', '.m3u', '.chd', '.iso', '.cso', '.pbp', '.rvz', '.wbfs', '.wad', '.gcz', '.3ds', '.cia'}
        return recent.rom_key(game['code'], name if suffix in exts or '/' in name else name + '.rom')
    return recent.pc_key(game['id'])


def load(path):
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    favorites = data.get('favorites', [])
    return {'favorites': list(dict.fromkeys(k for k in favorites if isinstance(k, str))) if isinstance(favorites, list) else [],
            'theme': data.get('theme') if data.get('theme') in ('dark', 'light') else 'dark'}


def update(path, *, key=None, favorite=None, theme=None):
    if key is not None and (not isinstance(key, str) or not key or len(key) > 512 or type(favorite) is not bool):
        raise ValueError('favorito inválido')
    if theme is not None and theme not in ('dark', 'light'):
        raise ValueError('tema inválido')
    path = Path(path)
    with file_lock.exclusive(path):
        data = load(path)
        if key is not None:
            data['favorites'] = [k for k in data['favorites'] if k != key]
            if favorite:
                data['favorites'].append(key)
        if theme is not None:
            data['theme'] = theme
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(dir=path.parent, prefix='.tv-preferences-')
        try:
            with os.fdopen(fd, 'w') as output:
                json.dump(data, output, ensure_ascii=False)
            os.replace(name, path)
        finally:
            Path(name).unlink(missing_ok=True)
        return data


def annotate(games, preferences, history, times=None, media_root=None):
    favorites = set(preferences['favorites'])
    for game in games:
        key = item_key(game)
        # Registros com ROM e ID mantêm a identidade da ROM e aceitam histórico
        # anterior por ID, caso o jogo tenha sido aberto antes pela Biblioteca.
        dates = [history.get(key)]
        if game.get('id'):
            dates.append(history.get(recent.pc_key(game['id'])))
        tracking = game.get('tracking') or {}
        game.update(key=key, favorite=tracking.get('favorite', key in favorites),
                    mobileCode=game.get('code') or library.rom_code_for_plataforma(game['platform']) or '',
                    lastPlayed=max((d for d in dates if d), default=None),
                    playtime=library_activity.public_time(tracking, (times or {}).get(key, {})))
        if media_root is not None:
            game['media'] = tv_media.describe(media_root, key)
    return games


def home(games, apps, preferences, history, times=None, media_root=None):
    games = annotate(games, preferences, history, times, media_root)
    recent_games = sorted((g for g in games if g['lastPlayed']), key=lambda g: g['lastPlayed'], reverse=True)
    recent_rank = {g['key']: i for i, g in enumerate(recent_games)}
    continued = sorted((g for g in games if g['tracking'].get('iniciado') and not g['tracking'].get('finalizado')),
                       key=lambda g: (not g['local'], recent_rank.get(g['key'], len(games)), g['name'].lower()))
    return {'recent': recent_games[:16], 'continue': continued[:16],
            'favorites': [g for g in games if g['favorite']][:24],
            'installed': [g for g in games if g['local'] and not g.get('code')][:16],
            'ready': [g for g in games if g['local']][:16],
            'mostPlayed': sorted((g for g in games if g['playtime']['seconds']), key=lambda g: -g['playtime']['seconds'])[:16],
            'apps': apps, 'preferences': preferences,
            'counts': {'catalog': len(games), 'local': sum(bool(g['local']) for g in games),
                       'pc': sum(bool(g['local']) and not g.get('code') for g in games)}}

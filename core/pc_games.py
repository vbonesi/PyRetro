"""Jogos de PC instalados que o modo TV pode abrir (Steam e Heroic).

Tudo é descoberto no disco local: o cliente só informa o id do registro da
Biblioteca e nunca um comando, appid ou caminho. Só jogos instalados e cuja
fonte no registro bate com a loja são oferecidos.
"""
import json
import re
import subprocess
from pathlib import Path

from core import covers as covers_mod
from core import library as library_mod

STEAM_ROOTS = ('~/.var/app/com.valvesoftware.Steam/.local/share/Steam', '~/.local/share/Steam')
STEAM_APP = 'com.valvesoftware.Steam'
HEROIC_APP = 'com.heroicgameslauncher.hgl'
IGNORED_STEAM = ('steam linux runtime', 'proton', 'steamworks common')
SAFE_ID = re.compile(r'^[A-Za-z0-9_-]{1,64}$')
NILE_ID = re.compile(r'^[A-Za-z0-9_.-]{1,160}$')
FIELD = r'"%s"\s+"([^"]*)"'


def _norm(name):
    # A Steam grava "The Sims™ 4"; a Biblioteca, "The Sims 4".
    return covers_mod.normalize(re.sub(r'[™®©]', '', name))


def _steamapps_dirs():
    dirs = []
    for root in STEAM_ROOTS:
        base = Path(root).expanduser() / 'steamapps'
        if not base.is_dir():
            continue
        dirs.append(base)
        try:
            extra = re.findall(r'"path"\s+"([^"]+)"', (base / 'libraryfolders.vdf').read_text(errors='replace'))
        except OSError:
            extra = []
        dirs += [Path(p) / 'steamapps' for p in extra]
    return list(dict.fromkeys(d for d in dirs if d.is_dir()))


def steam_installed():
    """{nome normalizado: appid} dos jogos Steam instalados."""
    out = {}
    for d in _steamapps_dirs():
        for manifest in d.glob('appmanifest_*.acf'):
            try:
                text = manifest.read_text(errors='replace')
            except OSError:
                continue
            appid = re.search(FIELD % 'appid', text)
            name = re.search(FIELD % 'name', text)
            if not appid or not name or not appid.group(1).isdigit():
                continue
            if any(name.group(1).lower().startswith(p) for p in IGNORED_STEAM):
                continue
            flags = re.search(FIELD % 'StateFlags', text)
            if flags and not (int(flags.group(1)) & 4 if flags.group(1).isdigit() else False):
                continue
            folder = re.search(FIELD % 'installdir', text)
            if folder and not (d / 'common' / folder.group(1)).is_dir():
                continue
            out[_norm(name.group(1))] = appid.group(1)
    return out


def _json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def heroic_installed(heroic_cfg, store):
    """{nome normalizado: app_name} de Epic (legendary) ou GOG instalados."""
    base = Path(heroic_cfg.get('config_dir') or '~/.config/heroic').expanduser()
    out = {}
    if store == 'legendary':
        data = _json(base / 'legendaryConfig/legendary/installed.json')
        for app, info in (data.items() if isinstance(data, dict) else []):
            if isinstance(info, dict) and not info.get('is_dlc') and info.get('title') and SAFE_ID.match(str(app)):
                if info.get('install_path') and not Path(info['install_path']).is_dir():
                    continue
                out[_norm(info['title'])] = app
    elif store == 'gog':
        installed = _json(base / 'gog_store/installed.json')
        entries = installed.get('installed', []) if isinstance(installed, dict) else []
        titles = {}
        library = _json(base / 'store_cache/gog_library.json')
        for g in (library.get('games', []) if isinstance(library, dict) else []):
            if g.get('app_name') and g.get('title'):
                titles[str(g['app_name'])] = g['title']
        for e in entries:
            app = str(e.get('appName') or e.get('app_name') or '')
            if e.get('install_path') and not Path(e['install_path']).is_dir():
                continue
            if app in titles and SAFE_ID.match(app):
                out[_norm(titles[app])] = app
    elif store == 'nile':
        installed = _json(base / 'nile_config/nile/installed.json')
        cache = _json(base / 'store_cache/nile_library.json')
        games = cache.get('library', []) if isinstance(cache, dict) else []
        titles = {str(g.get('app_name')): g.get('title') for g in games if isinstance(g, dict)}
        for info in (installed if isinstance(installed, list) else []):
            app = str(info.get('id', '')) if isinstance(info, dict) else ''
            if isinstance(info, dict) and info.get('path') and not Path(info['path']).is_dir():
                continue
            if titles.get(app) and NILE_ID.fullmatch(app):
                out[_norm(titles[app])] = app
    return out


def installed_indexes(cfg):
    return {'steam': steam_installed(), **{
        store: heroic_installed(cfg.get('heroic', {}), store)
        for store in ('legendary', 'gog', 'nile')}}


def find(cfg, game, indexes=None):
    """Descreve como abrir `game` (registro da Biblioteca) ou devolve None."""
    if library_mod.rom_code_for_plataforma(game.get('plataforma', '')):
        return None
    names = [_norm(n) for n in [game['nome'], *game.get('nomes_alt', [])]]
    sources = {'steam': 'steam', 'heroic:epic': 'legendary',
               'heroic:gog': 'gog', 'heroic:amazon': 'nile'}
    for fonte in game.get('fontes', []):
        store = sources.get(fonte)
        if not store:
            continue
        index = indexes[store] if indexes is not None else (steam_installed() if store == 'steam' else heroic_installed(cfg.get('heroic', {}), store))
        for n in names:
            if n in index:
                return {'store': store, 'id': index[n]}
    return None


def command(found):
    if found['store'] not in ('steam', 'legendary', 'gog', 'nile'):
        raise ValueError('loja inválida')
    if found['store'] == 'steam':
        if not str(found['id']).isdigit():
            raise ValueError('appid inválido')
        return ['flatpak', 'run', STEAM_APP, f"steam://rungameid/{found['id']}"]
    if not (NILE_ID if found['store'] == 'nile' else SAFE_ID).fullmatch(str(found['id'])):
        raise ValueError('identificador de jogo inválido')
    return ['flatpak', 'run', HEROIC_APP, f"heroic://launch/{found['store']}/{found['id']}"]


def launch(found):
    # Steam e Heroic entregam o pedido à instância aberta e retornam; não há
    # processo do jogo para acompanhar, então não vira sessão de emulador.
    subprocess.Popen(command(found), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True)

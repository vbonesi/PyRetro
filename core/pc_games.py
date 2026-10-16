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

STEAM_ROOTS = ('~/.var/app/com.valvesoftware.Steam/.local/share/Steam', '~/.local/share/Steam')
STEAM_APP = 'com.valvesoftware.Steam'
HEROIC_APP = 'com.heroicgameslauncher.hgl'
IGNORED_STEAM = ('steam linux runtime', 'proton', 'steamworks common')
SAFE_ID = re.compile(r'^[A-Za-z0-9_-]{1,64}$')
FIELD = r'"%s"\s+"([^"]*)"'


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
            out[covers_mod.normalize(name.group(1))] = appid.group(1)
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
                out[covers_mod.normalize(info['title'])] = app
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
            if app in titles and SAFE_ID.match(app):
                out[covers_mod.normalize(titles[app])] = app
    return out


def find(cfg, game):
    """Descreve como abrir `game` (registro da Biblioteca) ou devolve None."""
    names = [covers_mod.normalize(n) for n in [game['nome'], *game.get('nomes_alt', [])]]
    for fonte in game.get('fontes', []):
        if fonte == 'steam':
            index, store = steam_installed(), 'steam'
        elif fonte in ('heroic:epic', 'heroic:gog'):
            store = 'legendary' if fonte.endswith('epic') else 'gog'
            index = heroic_installed(cfg.get('heroic', {}), store)
        else:
            continue
        for n in names:
            if n in index:
                return {'store': store, 'id': index[n]}
    return None


def command(found):
    if found['store'] == 'steam':
        if not str(found['id']).isdigit():
            raise ValueError('appid inválido')
        return ['flatpak', 'run', STEAM_APP, f"steam://rungameid/{found['id']}"]
    if not SAFE_ID.match(str(found['id'])):
        raise ValueError('identificador de jogo inválido')
    return ['flatpak', 'run', HEROIC_APP, f"heroic://launch/{found['store']}/{found['id']}"]


def launch(found):
    # Steam e Heroic entregam o pedido à instância aberta e retornam; não há
    # processo do jogo para acompanhar, então não vira sessão de emulador.
    subprocess.Popen(command(found), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True)

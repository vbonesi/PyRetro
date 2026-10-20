"""Apps da TV. Só IDs conhecidos chegam do navegador; argv fixo, sem shell."""
from pathlib import Path
import subprocess
import shutil

DEFAULTS = {
    'steam': ('Steam', 'com.valvesoftware.Steam', '🎮'),
    'heroic': ('Heroic', 'com.heroicgameslauncher.hgl', '🚀'),
    'retroarch': ('RetroArch', 'org.libretro.RetroArch', '🕹'),
    'pcsx2': ('PCSX2', 'net.pcsx2.PCSX2', '🎮'),
    'dolphin': ('Dolphin', 'org.DolphinEmu.dolphin-emu', '🐬'),
    'ppsspp': ('PPSSPP', 'org.ppsspp.PPSSPP', '🎮'),
    'chiaki': ('PlayStation Remote Play', 'io.github.streetpea.Chiaki4deck', '🎮'),
    'greenlight': ('Xbox Remote Play', 'io.github.unknownskl.greenlight', '🎮'),
}


def entries(cfg):
    result = {}
    installed = set()
    if shutil.which('flatpak'):
        installed = set(subprocess.run(['flatpak', 'list', '--app', '--columns=application'],
                                       capture_output=True, text=True, timeout=10).stdout.splitlines())
    for key, (name, app, icon) in DEFAULTS.items():
        if app in installed:
            result[key] = {'nome': name, 'icone': icon, 'comando': ['flatpak', 'run', app] + (['-gamepadui'] if key == 'steam' else [])}
    duck = Path.home() / 'AppImages/DuckStation-x64.AppImage'
    if duck.is_file():
        result['duckstation'] = {'nome': 'DuckStation', 'icone': '🎮', 'comando': [str(duck)]}
    esde = Path.home() / '.local/bin/bonisarch-esde'
    if esde.is_file():
        result['esde'] = {'nome': 'ES-DE', 'icone': '🕹', 'comando': [str(esde)]}
    for key, value in cfg.get('apps', {}).items():
        command = value.get('comando')
        if not isinstance(command, list) or not command or not all(isinstance(x, str) and x and '\0' not in x for x in command):
            continue
        result[key] = value
    return result


def catalog(cfg):
    return [{'id': key, 'name': value.get('nome', key), 'icon': value.get('icone', '▣')}
            for key, value in entries(cfg).items()]


def launch(cfg, key):
    if not isinstance(key, str) or key not in (apps := entries(cfg)):
        raise ValueError('aplicativo não configurado')
    subprocess.Popen(apps[key]['comando'], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True)

"""Apps da TV. Só IDs conhecidos chegam do navegador; argv fixo, sem shell."""
from pathlib import Path
import os
import subprocess
import shutil
import json
import threading

from core.desktop_env import session_env

REMOTE_IDS = {'greenlight'}
_launch_lock = threading.Lock()
_remote_processes = {}

# Argumentos para abrir cada app na interface de controle/tela cheia. Só flags conferidas no
# --help ou no pacote de cada app (29/10/2026); Dolphin e Azahar não têm modo sem jogo.
TV_ARGS = {
    'steam': ['steam://open/bigpicture'],
    'heroic': ['--console', '--fullscreen'],
    'retroarch': ['-f'],
    'pcsx2': ['-bigpicture', '-fullscreen'],
    'ppsspp': ['--fullscreen'],
}

DEFAULTS = {
    'steam': ('Steam', 'com.valvesoftware.Steam', '🎮'),
    'heroic': ('Heroic', 'com.heroicgameslauncher.hgl', '🚀'),
    'retroarch': ('RetroArch', 'org.libretro.RetroArch', '🕹'),
    'pcsx2': ('PCSX2', 'net.pcsx2.PCSX2', '🎮'),
    'dolphin': ('Dolphin', 'org.DolphinEmu.dolphin-emu', '🐬'),
    'ppsspp': ('PPSSPP', 'org.ppsspp.PPSSPP', '🎮'),
    'azahar': ('Azahar (3DS)', 'org.azahar_emu.Azahar', '🎮'),
    'greenlight': ('Xbox remoto', 'io.github.unknownskl.greenlight', '⊗'),
}

# Emuladores em AppImage (não Flatpak), baixados pelo Victor: o de Switch 2 (24/11/2026). Mesmos caminhos que o
# `bonisarch-emulator switch2` procura (setup); em cada um vale o AppImage mais novo.
APPIMAGES = {
    'fritchii': ('Fritchii (Switch 2)', ('AppImages/fritchii*.appimage', 'AppImages/fritchii*.AppImage', 'AppImages/Fritchii*.AppImage'), '🎮'),
    'lichii': ('Lichii (Switch 2)', ('Applications/lichii*.AppImage', 'Applications/Lichii*.AppImage', 'AppImages/lichii*.AppImage'), '🎮'),
}


def appimage(patterns, home=None):
    home = home or Path.home()
    found = [p for pattern in patterns for p in home.glob(pattern) if p.is_file() and os.access(p, os.X_OK)]
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def entries(cfg, home=None):
    result = {}
    installed = set()
    if shutil.which('flatpak'):
        installed = set(subprocess.run(['flatpak', 'list', '--app', '--columns=application'],
                                       capture_output=True, text=True, timeout=10).stdout.splitlines())
    for key, (name, app, icon) in DEFAULTS.items():
        if app in installed:
            result[key] = {'nome': name, 'icone': icon, 'comando': ['flatpak', 'run', app, *TV_ARGS.get(key, [])]}
    for key, (name, patterns, icon) in APPIMAGES.items():
        if path := appimage(patterns, home):
            result[key] = {'nome': name, 'icone': icon, 'comando': [str(path)]}
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
    command = apps[key]['comando']
    # O cliente remoto pode demorar para ganhar foco. Cliques adicionais não
    # devem criar novos players, inclusive após reiniciar o serviço PyRetro.
    with _launch_lock:
        identity = tuple(command)
        if key in REMOTE_IDS:
            process = _remote_processes.get(identity)
            if process is not None and process.poll() is None:
                return {'already_running': True}
            _remote_processes.pop(identity, None)
            if command[:2] == ['flatpak', 'run'] and len(command) >= 3:
                try:
                    running = subprocess.run(['flatpak', 'ps', '--columns=application'],
                                             capture_output=True, text=True, timeout=5, check=True)
                    if command[2] in running.stdout.splitlines():
                        return {'already_running': True}
                except (OSError, subprocess.SubprocessError):
                    raise ValueError('não foi possível conferir se o cliente remoto já está aberto; tente novamente')
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True,
                                   env=session_env())
        if key in REMOTE_IDS:
            _remote_processes[identity] = process
        return {'already_running': False}

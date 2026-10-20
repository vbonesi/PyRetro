"""Apps da TV. Só IDs conhecidos chegam do navegador; argv fixo, sem shell."""
from pathlib import Path
import subprocess
import shutil
import ipaddress
import json
import threading

REMOTES_PATH = Path(__file__).resolve().parent.parent / 'cache/tv_remotes.json'
REMOTE_IDS = {'sysdvr', 'chiaki', 'greenlight'}
_launch_lock = threading.Lock()
_remote_processes = {}

DEFAULTS = {
    'steam': ('Steam', 'com.valvesoftware.Steam', '🎮'),
    'heroic': ('Heroic', 'com.heroicgameslauncher.hgl', '🚀'),
    'retroarch': ('RetroArch', 'org.libretro.RetroArch', '🕹'),
    'pcsx2': ('PCSX2', 'net.pcsx2.PCSX2', '🎮'),
    'dolphin': ('Dolphin', 'org.DolphinEmu.dolphin-emu', '🐬'),
    'ppsspp': ('PPSSPP', 'org.ppsspp.PPSSPP', '🎮'),
    'chiaki': ('PS4 remoto', 'io.github.streetpea.Chiaki4deck', '◈'),
    'greenlight': ('Xbox remoto', 'io.github.unknownskl.greenlight', '⊗'),
    'sysdvr': ('Switch Lite', 'com.github.exelix11.sysdvr', '◧'),
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
    if 'sysdvr' in result:
        try:
            data = json.loads(REMOTES_PATH.read_text())
            address = str(ipaddress.ip_address(data['switch_ip']))
        except (OSError, ValueError, KeyError, TypeError):
            address = None
        result['sysdvr']['comando'] += ['bridge', *([address] if address else []), '--fullscreen']
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
                                   stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True)
        if key in REMOTE_IDS:
            _remote_processes[identity] = process
        return {'already_running': False}

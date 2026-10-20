"""Ponte local do modo TV para o lançador de emuladores do setup.

Não escolhe jogo por aproximação nem aceita comandos do cliente. Apenas ROMs
com extensão configurada e contidas no diretório do sistema podem ser abertas.
"""
import os
from pathlib import Path
import re
import shlex
import subprocess
import threading
import time

SYSTEMS = {
    'FC': 'nes', 'SFC': 'snes', 'GB': 'gb', 'GBC': 'gbc', 'GBA': 'gba',
    'MD': 'megadrive', 'SMS': 'mastersystem', 'GG': 'gamegear', 'N64': 'n64',
    'ARCADE': 'arcade', 'PCE': 'pcengine', 'PCECD': 'pcenginecd',
    'PS': 'psx', 'PS2': 'ps2', 'PSP': 'psp', 'NGC': 'gc', 'WII': 'wii',
}
LAUNCHER = Path.home() / '.local/bin/bonisarch-emulator'
CORE_ROOT = Path.home() / '.var/app/org.libretro.RetroArch/config/retroarch/cores'
# Somente alternativas compatíveis conhecidas, se o core já estiver instalado.
ALTERNATIVES = {'MD': {'picodrive': 'PicoDrive'}, 'SMS': {'picodrive': 'PicoDrive'},
                'GG': {'picodrive': 'PicoDrive'}, 'PS': {'swanstation': 'SwanStation'}}


def emulators(code):
    return [{'id': '', 'name': 'Padrão do sistema'}, *[
        {'id': key, 'name': name} for key, name in ALTERNATIVES.get(code, {}).items()
        if (CORE_ROOT / (key + '_libretro.so')).is_file()]]


def restore_tv_focus():
    helper = Path(__file__).resolve().parent.parent / 'tools/raise-window.sh'
    if os.environ.get('DBUS_SESSION_BUS_ADDRESS') and helper.is_file():
        try:
            subprocess.Popen([str(helper), 'chrome-127.0.0.1__tv', '2'], stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        except OSError:
            pass


def safe_relative(value):
    if not isinstance(value, str) or not value or '\\' in value or '\x00' in value:
        raise ValueError('nome de ROM inválido')
    path = Path(value)
    if path.is_absolute() or any(p in ('.', '..') for p in value.split('/')):
        raise ValueError('nome de ROM inválido')
    return path


def checked_file(root, name):
    path = root / safe_relative(name)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('ROM ou arquivo associado fora da pasta do sistema')
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError('arquivo ausente ou vazio: ' + str(name))
    return path


def references(path):
    """Referências explícitas; nunca adivinha faixas pelo nome do jogo."""
    suffix = path.suffix.lower()
    if suffix == '.ccd':
        raise ValueError('CCD ainda sem validação de IMG/SUB; use outro formato completo')
    if suffix not in ('.cue', '.gdi', '.m3u'):
        return []
    text = path.read_text(encoding='utf-8-sig', errors='replace')
    refs = []
    if suffix == '.cue':
        for line in text.splitlines():
            if re.match(r'^\s*FILE\s', line, re.I):
                fields = shlex.split(line.strip())
                if len(fields) < 3:
                    raise ValueError('referência FILE inválida no CUE')
                refs.append(fields[1])
    elif suffix == '.gdi':
        lines = [line for line in text.splitlines() if line.strip()]
        try:
            count = int(lines[0])
            for line in lines[1:]:
                fields = shlex.split(line)
                if len(fields) < 6:
                    raise ValueError('faixa GDI inválida')
                refs.append(fields[4])
            if count != len(refs):
                raise ValueError('número de faixas GDI inválido')
        except (IndexError, TypeError):
            raise ValueError('GDI inválido') from None
    else:
        refs = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith('#')]
    if not refs:
        raise ValueError('descritor de disco sem arquivos associados')
    for ref in refs:
        safe_relative(ref)
    return refs


def validate_bundle(root, name, seen=None):
    seen = set() if seen is None else seen
    path = checked_file(root, name)
    resolved = path.resolve()
    if resolved in seen:
        raise ValueError('referência circular no conjunto de discos')
    if len(seen) >= 100:
        raise ValueError('conjunto de discos excessivamente profundo')
    branch = seen | {resolved}
    for ref in references(path):
        relative = (path.parent / ref).relative_to(root)
        validate_bundle(root, str(relative), branch)
    return path


def system_info(cfg, code):
    info = cfg.get('systems', {}).get(code) or cfg.get('heavy_systems', {}).get(code)
    if code not in SYSTEMS or not info:
        raise ValueError('sistema ainda sem lançador configurado: ' + str(code))
    return info


def candidates(cfg, code, name):
    info = system_info(cfg, code)
    root = Path(cfg['pc']['roms_root']).expanduser() / code
    # Impede que uma pasta de sistema inteira seja um symlink para fora do acervo.
    if not root.resolve().is_relative_to(root.parent.resolve()):
        raise ValueError('pasta do sistema fora do acervo')
    rel = safe_relative(name)
    item = root / rel
    if not item.resolve().is_relative_to(root.resolve()):
        raise ValueError('ROM fora da pasta do sistema')
    exts = {'.' + e.lower().lstrip('.') for e in info.get('exts', [])}
    if item.is_file():
        options = [item]
    elif item.is_dir():
        options = sorted(p for p in item.rglob('*') if p.is_file() and p.suffix.lower() in exts)
    elif item.parent.is_dir():
        options = sorted(p for p in item.parent.iterdir() if p.is_file() and p.stem == item.name and p.suffix.lower() in exts)
    else:
        options = []
    out = []
    for path in options:
        if path.suffix.lower() not in exts:
            continue
        # Faixas BIN não viram opções extras ao lado de seu descritor CUE.
        if path.suffix.lower() == '.bin' and path.with_suffix('.cue').is_file():
            continue
        relative = str(path.relative_to(root))
        try:
            validate_bundle(root, relative)
            error = None
        except (OSError, ValueError) as e:
            error = str(e)
        out.append({'name': relative, 'error': error})
    return out


def prepare(cfg, code, name, emulator=''):
    info = system_info(cfg, code)
    root = Path(cfg['pc']['roms_root']).expanduser() / code
    if not root.resolve().is_relative_to(root.parent.resolve()):
        raise ValueError('pasta do sistema fora do acervo')
    if Path(safe_relative(name)).suffix.lower().lstrip('.') not in {e.lower().lstrip('.') for e in info.get('exts', [])}:
        raise ValueError('extensão não configurada para este sistema')
    rom = validate_bundle(root, name)
    if emulator:
        if not isinstance(emulator, str) or emulator not in {g['id'] for g in emulators(code)}:
            raise ValueError('emulador alternativo não disponível neste sistema')
        return ['flatpak', 'run', 'org.libretro.RetroArch', '-f', '-L',
                str(CORE_ROOT / (emulator + '_libretro.so')), str(rom.resolve())]
    if not LAUNCHER.is_file() or not os.access(LAUNCHER, os.X_OK):
        raise ValueError('lançador bonisarch-emulator não instalado')
    return [str(LAUNCHER), SYSTEMS[code], str(rom.resolve())]


class Sessions:
    """Uma sessão por servidor. O estado pode ser retomado após recarregar a TV."""
    def __init__(self):
        self.lock = threading.Lock()
        self.process = None
        self.state = {'status': 'idle'}

    def _poll(self):
        if self.process is not None:
            code = self.process.poll()
            if code is not None:
                self.state.update(status='finished' if code == 0 else 'error', returncode=code)
                self.process = None
                restore_tv_focus()
        return dict(self.state)

    def status(self):
        with self.lock:
            return self._poll()

    def start(self, cfg, code, name, emulator=''):
        with self.lock:
            if self._poll()['status'] == 'running':
                raise ValueError('já existe um jogo aberto pelo PyRetro')
            cmd = prepare(cfg, code, name, emulator)
            # Sem shell e sem herdar stdin; os erros do lançador vão para o journal.
            process = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, close_fds=True)
            self.process = process
            self.state = {'status': 'running', 'code': code, 'name': name,
                          'session': time.time_ns()}
            return dict(self.state)

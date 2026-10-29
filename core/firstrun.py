"""Primeiros passos: o PyRetro confere e monta a própria estrutura de pastas e configuração.

Só cria o que falta (configuração e pastas vazias). Nunca sobrescreve a configuração, nunca mexe em
conteúdo de pasta existente e não instala programa: emuladores e rclone são do setup do sistema, e o
assistente apenas diz o que não encontrou. Não consulta a rede nem executa os programas encontrados.
"""
import shutil
import subprocess
import tomllib
from pathlib import Path

from core import storage as storage_mod

STORAGE_SECTION = '''

# Criado pelo assistente de primeiros passos (core/firstrun.py): acervo fora do Drive.
[storage]
games_root = "~/Games/PyRetro"
nsw_root = "~/Games/PyRetro/NSW"
migrated = ["roms", "bios", "nsw", "saves", "capas", "biblioteca", "backups"]
'''
FOLDERS = {'roms_root': 'ROMs', 'saves_root': 'Saves', 'states_root': 'Estados',
           'capas_root': 'Capas', 'library_root': 'Biblioteca', 'backups_root': 'Backups', 'nsw_root': 'Switch'}
# (nome, id Flatpak ou executável, obrigatório). Steam e Heroic são só lojas: faltar não impede o resto.
PROGRAMS = [('RetroArch', 'org.libretro.RetroArch', True), ('PCSX2', 'net.pcsx2.PCSX2', True),
            ('Dolphin', 'org.DolphinEmu.dolphin-emu', True), ('PPSSPP', 'org.ppsspp.PPSSPP', True),
            ('Azahar (3DS)', 'org.azahar_emu.Azahar', True), ('Steam', 'com.valvesoftware.Steam', False),
            ('Heroic', 'com.heroicgameslauncher.hgl', False)]


def _config(config_path):
    try:
        with open(config_path, 'rb') as handle:
            return storage_mod.apply_config(tomllib.load(handle))
    except FileNotFoundError:
        return None


def _planned_config(example_path):
    cfg = tomllib.loads(Path(example_path).read_text(encoding='utf-8') + STORAGE_SECTION)
    return storage_mod.apply_config(cfg)


def _folders(cfg):
    pc = cfg['pc']
    paths = {label: Path(pc[key]).expanduser() for key, label in FOLDERS.items() if pc.get(key)}
    layout = storage_mod.Layout.configured(cfg)
    paths['BIOS'] = layout.bios
    if pc.get('organizar_dir') and pc.get('roms_root'):
        paths['Organizar'] = Path(pc['roms_root']).expanduser() / pc['organizar_dir']
    return paths


def _flatpaks(run=subprocess.run, which=shutil.which):
    if not which('flatpak'):
        return set()
    done = run(['flatpak', 'list', '--app', '--columns=application'], capture_output=True, text=True, timeout=10)
    return set(done.stdout.splitlines())


def _remotes(run=subprocess.run, which=shutil.which):
    if not which('rclone'):
        return None
    done = run(['rclone', 'listremotes'], capture_output=True, text=True, timeout=10)
    return {line.rstrip(':') for line in done.stdout.splitlines() if line.strip()}


def status(config_path, example_path, home=None, flatpaks=None, remotes=None, which=shutil.which):
    home = Path(home) if home else Path.home()
    cfg = _config(config_path)
    steps = [{'id': 'config', 'label': 'Configuração do PyRetro', 'state': 'ok' if cfg else 'missing',
              'detail': '' if cfg else 'Ainda não existe; o assistente cria a partir do modelo.', 'fixable': cfg is None}]
    folders = _folders(cfg or _planned_config(example_path))
    missing = [name for name, path in folders.items() if not path.is_dir()]
    steps.append({'id': 'folders', 'label': 'Pastas do acervo', 'state': 'missing' if missing else 'ok',
                  'detail': ('Faltam: ' + ', '.join(missing) + '.') if missing else '', 'fixable': bool(missing)})
    remote = ((cfg or {}).get('cloud') or {}).get('remote', '')
    if remote:
        names = _remotes(which=which) if remotes is None else remotes
        name = remote.split(':', 1)[0]
        if names is None:
            state, detail = 'missing', 'rclone não encontrado; o setup do sistema instala.'
        elif name not in names:
            state, detail = 'missing', f'A conta "{name}" ainda não foi conectada. Rode: rclone config'
        else:
            state, detail = 'ok', ''
    else:
        state, detail = 'optional', 'Opcional: para sincronizar com o Google Drive, conecte uma conta com rclone config e defina [cloud] remote.'
    steps.append({'id': 'cloud', 'label': 'Nuvem (Google Drive)', 'state': state, 'detail': detail, 'fixable': False})
    installed = _flatpaks(which=which) if flatpaks is None else set(flatpaks)
    programs = [(name, app, need) for name, app, need in PROGRAMS if app not in installed]
    if not (home / 'AppImages/DuckStation-x64.AppImage').is_file():
        programs.append(('DuckStation', '', True))
    if not which('bonisarch-emulator') and not (home / '.local/bin/bonisarch-emulator').is_file():
        programs.append(('Lançador de jogos (bonisarch-emulator)', '', True))
    required = [name for name, _app, need in programs if need]
    optional = [name for name, _app, need in programs if not need]
    steps.append({'id': 'programs', 'label': 'Emuladores e lojas', 'state': 'missing' if required else ('optional' if optional else 'ok'),
                  'detail': ((('Não encontrados: ' + ', '.join(required) + '. ') if required else '')
                             + (('Opcionais ausentes: ' + ', '.join(optional) + '. ') if optional else '')
                             + ('O setup do sistema (setup-linux-bonesi) instala; o PyRetro não instala programas.' if programs else '')).strip(),
                  'fixable': False})
    return {'ready': steps[0]['state'] == 'ok' and steps[1]['state'] == 'ok', 'steps': steps}


def apply(config_path, example_path):
    """Cria a configuração (se faltar) e as pastas vazias que faltam. Devolve o que foi criado."""
    created = []
    config_path = Path(config_path)
    if not config_path.exists():
        text = Path(example_path).read_text(encoding='utf-8') + STORAGE_SECTION
        storage_mod.apply_config(tomllib.loads(text))  # valida antes de gravar
        with open(config_path, 'x', encoding='utf-8') as handle:  # 'x': nunca sobrescreve
            handle.write(text)
        config_path.chmod(0o600)  # guarda chaves de API
        created.append('config')
    cfg = _config(config_path)
    for label, path in _folders(cfg).items():
        if not path.is_dir():
            path.mkdir(parents=True, exist_ok=True)
            created.append(label)
    return {'created': created}

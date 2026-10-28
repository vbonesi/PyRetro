#!/usr/bin/env python3
"""Instala o atalho TV, com Steam fechada, preservando o VDF anterior.

Simula por padrão. --apply instala; --config permite selecionar explicitamente
uma conta quando houver mais de uma conta Steam nesta máquina.
"""
import argparse
from datetime import datetime
import os
from pathlib import Path
import struct
import shutil
import subprocess
import tempfile
import zlib

NAME = 'PyRetro'
LEGACY_NAME = 'PyRetro — Acervo'


def decode(data):
    offset = 0
    def string():
        nonlocal offset
        end = data.index(b'\0', offset)
        result = data[offset:end].decode('utf-8')
        offset = end + 1
        return result
    def entries():
        nonlocal offset
        nodes = []
        while offset < len(data):
            kind = data[offset]; offset += 1
            if kind == 8: return nodes
            key = string()
            if kind == 0: value = entries()
            elif kind == 1: value = string()
            elif kind in (2, 3, 4, 6, 7, 10):
                size = 8 if kind in (7, 10) else 4
                value = data[offset:offset + size]
                if len(value) != size: raise ValueError('VDF truncado')
                offset += size
            else: raise ValueError('tipo VDF não suportado; arquivo preservado')
            nodes.append((kind, key, value))
        raise ValueError('VDF sem terminador')
    result = entries()
    if offset != len(data): raise ValueError('dados extras no VDF; arquivo preservado')
    return result


def encode(nodes):
    data = bytearray()
    for kind, key, value in nodes:
        data.extend(bytes([kind]) + key.encode() + b'\0')
        if kind == 0: data.extend(encode(value))
        elif kind == 1: data.extend(value.encode() + b'\0')
        else: data.extend(value)
    data.append(8)
    return bytes(data)


def add_shortcut(data, launcher, home, icon=''):
    nodes = decode(data) if data else [(0, 'shortcuts', [])]
    roots = [value for kind, key, value in nodes if kind == 0 and key == 'shortcuts']
    if len(roots) != 1: raise ValueError('estrutura de atalhos Steam inesperada')
    shortcuts = roots[0]
    exe = '"/usr/bin/flatpak-spawn"'
    launch_options = '--host "' + str(launcher) + '"'
    for kind, key, fields in shortcuts:
        if kind != 0 or not key.isdigit(): raise ValueError('estrutura de atalho inesperada')
        if any(t == 1 and k.lower() == 'appname' and v in (NAME, LEGACY_NAME) for t, k, v in fields):
            values = {k.lower(): v for t, k, v in fields if t == 1}
            if values.get('exe') != exe or values.get('launchoptions') != launch_options:
                raise ValueError('atalho com mesmo nome e comando diferente; arquivo preservado')
            changed = False
            if values['appname'] == LEGACY_NAME:
                # Mantém appid, artes, tags e perfil Steam Input existentes.
                fields[:] = [(t, k, NAME if t == 1 and k.lower() == 'appname' else v) for t, k, v in fields]
                changed = True
            if icon and values.get('icon', '') != icon:
                # Só o ícone muda; appid, artes e tags ficam como estão.
                if any(t == 1 and k.lower() == 'icon' for t, k, v in fields):
                    fields[:] = [(t, k, icon if t == 1 and k.lower() == 'icon' else v) for t, k, v in fields]
                else:
                    fields.append((1, 'icon', icon))
                changed = True
            return (encode(nodes), True) if changed else (data, False)
    appid = zlib.crc32((exe + NAME).encode()) | 0x80000000
    fields = [(2, 'appid', struct.pack('<I', appid))]
    for k, v in {'AppName': NAME, 'Exe': exe, 'StartDir': '"' + str(home) + '"',
                 'icon': icon, 'ShortcutPath': '', 'LaunchOptions': launch_options}.items():
        fields.append((1, k, v))
    for k, v in {'IsHidden': 0, 'AllowDesktopConfig': 1, 'AllowOverlay': 1, 'OpenVR': 0,
                 'Devkit': 0, 'LastPlayTime': 0}.items():
        fields.append((2, k, struct.pack('<I', v)))
    fields.append((0, 'tags', [(1, '0', 'PyRetro')]))
    index = max((int(key) for _, key, _ in shortcuts), default=-1) + 1
    shortcuts.append((0, str(index), fields))
    return encode(nodes), True


BRAND = Path(__file__).resolve().parent.parent / 'assets/brand'


def install_icons(home):
    """Instala a marca no tema de ícones do usuário (hicolor): PNGs de 16 a 512 e o SVG."""
    root = home / '.local/share/icons/hicolor'
    for size in (16, 24, 32, 48, 64, 128, 192, 256, 512):
        target = root / f'{size}x{size}/apps'
        target.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(BRAND / 'png' / f'pyretro-{size}.png', target / 'pyretro.png')
    (root / 'scalable/apps').mkdir(parents=True, exist_ok=True)
    shutil.copyfile(BRAND / 'pyretro.svg', root / 'scalable/apps/pyretro.svg')


def install(apply=False, config=None):
    home = Path.home()
    source = Path(__file__).resolve().with_name('pyretro-tv.sh')
    launcher = home / '.local/bin/pyretro-tv'
    desktop = home / '.local/share/applications/pyretro-tv.desktop'
    configs = [Path(config).expanduser()] if config else list((home / '.var/app/com.valvesoftware.Steam/data/Steam/userdata').glob('*/config'))
    if len(configs) != 1:
        raise ValueError('selecione a conta Steam com --config; não foi encontrada uma conta única')
    vdf = configs[0] / 'shortcuts.vdf'
    old = vdf.read_bytes() if vdf.exists() else b''
    icon_name = 'pyretro'
    steam_icon = str(home / '.local/share/icons/hicolor/256x256/apps/pyretro.png')
    new, changed = add_shortcut(old, launcher, home, steam_icon)
    content = '[Desktop Entry]\nType=Application\nName=' + NAME + '\nExec="' + str(launcher) + '"\nIcon=pyretro\nCategories=Game;\nTerminal=false\n'
    if launcher.is_symlink():
        if launcher.resolve() != source: raise ValueError('lançador existente aponta para outro arquivo')
    elif launcher.exists(): raise ValueError('lançador existente preservado; revise-o antes de instalar')
    if desktop.exists():
        previous = desktop.read_text()
        if ('Exec="' + str(launcher) + '"') not in previous.splitlines() or not any(
                'Name=' + name in previous.splitlines() for name in (NAME, LEGACY_NAME)):
            raise ValueError('atalho desktop existente preservado; revise-o antes de instalar')
        content = previous.replace('Name=' + LEGACY_NAME + '\n', 'Name=' + NAME + '\n')
        content = '\n'.join('Icon=pyretro' if line.startswith('Icon=') else line for line in content.splitlines()) + '\n'
    legacy_desktop = home / '.local/share/applications/bonisarch-8000.desktop'
    legacy_content = None
    if legacy_desktop.is_file():
        previous = legacy_desktop.read_text()
        if 'Exec=xdg-open http://127.0.0.1:8000/' in previous.splitlines():
            legacy_content = '\n'.join(line for line in previous.splitlines() if not line.startswith(('Hidden=', 'NoDisplay='))) + '\nHidden=true\nNoDisplay=true\n'
    print('Lançador:', launcher)
    print('Atalho desktop:', desktop)
    print('Steam:', vdf, '(adicionar)' if changed else '(já existe)')
    if not apply:
        print('Simulação. Use --apply com a Steam fechada.')
        return
    # Não altera o arquivo enquanto a Steam pode regravá-lo da memória.
    if subprocess.run(['pgrep', '-x', 'steam'], capture_output=True).returncode == 0:
        raise ValueError('feche a Steam antes de instalar; nenhuma alteração aplicada')
    subprocess.run(['flatpak', 'info', 'com.google.Chrome'], check=True, capture_output=True)
    launcher.parent.mkdir(parents=True, exist_ok=True)
    desktop.parent.mkdir(parents=True, exist_ok=True)
    if not launcher.is_symlink(): launcher.symlink_to(source)
    desktop.write_text(content)
    install_icons(home)
    if legacy_content is not None:
        legacy_desktop.write_text(legacy_content)
    if changed:
        backup_dir = home / '.local/share/pyretro/steam-shortcuts'
        backup_dir.mkdir(parents=True, exist_ok=True)
        if old:
            backup = backup_dir / (datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.vdf')
            backup.write_bytes(old)
            print('Cópia anterior:', backup)
        fd, temporary = tempfile.mkstemp(prefix='.pyretro-', dir=vdf.parent)
        try:
            with os.fdopen(fd, 'wb') as file: file.write(new)
            if (vdf.read_bytes() if vdf.exists() else b'') != old:
                raise ValueError('atalhos mudaram durante a instalação; arquivo preservado')
            os.replace(temporary, vdf)
        finally:
            Path(temporary).unlink(missing_ok=True)
    print('Instalado. Abra o Big Picture e selecione ' + NAME + '.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--config')
    args = parser.parse_args()
    try: install(args.apply, args.config)
    except (OSError, ValueError, subprocess.CalledProcessError) as e:
        parser.exit(1, str(e) + '\n')

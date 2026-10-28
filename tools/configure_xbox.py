#!/usr/bin/env python3
"""Perfil Xbox do notebook; simula por padrão, aplica com cópia anterior e apps fechados.

Somente configurações de entrada/hotkeys: nunca acessa ROMs, memory cards ou estados.
"""
import argparse
from datetime import datetime
from pathlib import Path
import re
import shutil
import subprocess
import json


def edit(text, section, values, append=False):
    """Altera apenas chaves solicitadas; lista significa bindings INI repetidos."""
    lines = text.splitlines(keepends=True)
    start = next((i + 1 for i, line in enumerate(lines) if line.strip().lstrip('\ufeff') == '[' + section + ']'), None) if section else 0
    if start is None:
        if lines and not lines[-1].endswith('\n'):
            lines[-1] += '\n'
        if lines and lines[-1].strip():
            lines += ['\n']
        lines += ['[' + section + ']\n']; start = len(lines)
    end = next((i for i in range(start, len(lines)) if lines[i].lstrip().startswith('[')), len(lines))
    block = lines[start:end]
    for key, value in values.items():
        old = [line.split('=', 1)[1].strip() for line in block if '=' in line and line.split('=', 1)[0].strip() == key]
        new = value if isinstance(value, list) else [value]
        if append:
            new = old + [v for v in new if v not in old]
        if old == new:
            continue  # já igual: não reordena nem reformata (simulação repetida = sem mudança)
        positions = [i for i, line in enumerate(block) if '=' in line and line.split('=', 1)[0].strip() == key]
        if len(positions) == 1 and len(new) == 1:
            block[positions[0]] = key + ' = ' + new[0] + '\n'
            continue
        block = [line for line in block if not ('=' in line and line.split('=', 1)[0].strip() == key)]
        while block and not block[-1].strip():
            block.pop()
        block += [key + ' = ' + v + '\n' for v in new]
    if section and end < len(lines):
        while block and not block[-1].strip():
            block.pop()
        block.append('\n')
    return ''.join(lines[:start] + block + lines[end:])


def qt_edit(text, section, values):
    """Ini do Qt (Azahar): `chave=valor` sem espaços e `chave\\default=false` ao lado."""
    lines = text.splitlines(keepends=True)
    start = next(i + 1 for i, line in enumerate(lines) if line.strip() == '[' + section + ']')
    end = next((i for i in range(start, len(lines)) if lines[i].startswith('[')), len(lines))
    block = lines[start:end]
    for key, value in values.items():
        for name, val in ((key, value), (key + '\\default', 'false')):
            row = name + '=' + val + '\n'
            index = next((i for i, line in enumerate(block) if line.split('=', 1)[0] == name), None)
            if index is None:
                block.insert(len(block) - (1 if block and not block[-1].strip() else 0), row)
            else:
                block[index] = row
    return ''.join(lines[:start] + block + lines[end:])


REGISTRY = Path(__file__).resolve().parent.parent / 'assets/controllers/controllers.json'


def load_registry(path=REGISTRY):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def pick_controller(registry, controller_id=None):
    wanted = controller_id or registry['primary']
    for entry in registry['controllers']:
        if entry['id'] == wanted:
            return entry
    raise SystemExit('Controle desconhecido: ' + wanted + '. Opções: ' + ', '.join(c['id'] for c in registry['controllers']))


def dolphin_device(controller):
    """Nome do dispositivo no Dolphin; o Dolphin só encontra o controle pelo nome do SDL."""
    if not controller.get('sdl_name'):
        raise SystemExit(f"{controller['label']} ainda não foi medido: conecte só ele e rode --learn {controller['id']}")
    return 'SDL/0/' + controller['sdl_name']


def probe_pads():
    """Controles como o SDL do sandbox do Azahar os vê (ver tools/sdl_probe.py)."""
    probe = Path(__file__).with_name('sdl_probe.py')
    result = subprocess.run(['flatpak', 'run', '--filesystem=' + str(probe.parent) + ':ro', '--command=python3',
                             'org.azahar_emu.Azahar', str(probe)], capture_output=True, text=True, timeout=60)
    return [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]


def choose_pad(pads, controller):
    """Controle do SDL que corresponde ao perfil: pelo nome medido ou, sem medida, o primeiro Xbox."""
    usable = [pad for pad in pads if pad['controller']]
    if controller.get('sdl_name'):
        usable = [pad for pad in usable if pad['name'] == controller['sdl_name']]
    else:
        usable = [pad for pad in usable if 'xbox' in pad['name'].lower()]
    guid = usable[0]['guid'] if usable else ''
    return guid if len(guid) == 32 else None


def azahar_guid(home, controller=None):
    """GUID do controle como o SDL do sandbox do Azahar o vê; o do registro tem prioridade."""
    controller = controller or {}
    if controller.get('guid'):
        return controller['guid']
    return choose_pad(probe_pads(), controller)


def learn(registry, controller_id, pads, today):
    """Grava no registro o nome SDL e o GUID do único controle conectado."""
    entry = pick_controller(registry, controller_id)
    usable = [pad for pad in pads if pad['controller']]
    if len(usable) != 1:
        raise SystemExit(f'Conecte somente o {entry["label"]} (o SDL vê {len(usable)} controles) e rode de novo.')
    entry.update(sdl_name=usable[0]['name'], guid=usable[0]['guid'], measured=today)
    return entry


# SDL_GameController: botões e eixos (iguais em SDL2/SDL3 para o Xbox).
SDL_BUTTON = dict(A=0, B=1, X=2, Y=3, Back=4, Start=6, LS=7, RS=8, LB=9, RB=10, Up=11, Down=12, Left=13, Right=14)


def azahar_values(guid):
    def sdl(**params):
        return '"' + ','.join(f'{k}:{v}' for k, v in {'api': 'controller', **params, 'engine': 'sdl', 'guid': guid, 'port': 0}.items()) + '"'
    # Posição de Nintendo (A à direita), igual ao mapeamento automático do Azahar.
    buttons = dict(a='B', b='A', x='Y', y='X', l='LB', r='RB', start='Start', select='Back',
                   up='Up', down='Down', left='Left', right='Right')
    controls = {f'profiles\\1\\button_{k}': sdl(button=SDL_BUTTON[v]) for k, v in buttons.items()}
    controls['profiles\\1\\button_zl'] = sdl(axis=4, direction='+', threshold=0.5)
    controls['profiles\\1\\button_zr'] = sdl(axis=5, direction='+', threshold=0.5)
    controls['profiles\\1\\circle_pad'] = sdl(axis_x=0, axis_y=1, deadzone=0.1)
    controls['profiles\\1\\c_stick'] = sdl(axis_x=2, axis_y=3, deadzone=0.1)
    combo = lambda button: '"' + sdl(button=SDL_BUTTON['Back'])[1:-1] + '||' + sdl(button=SDL_BUTTON[button])[1:-1] + '"'
    hotkeys = {'Toggle%20Screen%20Layout': 'LS', 'Swap%20Screens': 'RS', 'Quick%20Save': 'LB',
               'Quick%20Load': 'RB', 'Toggle%20Turbo%20Mode': 'Right', 'Capture%20Screenshot': 'X',
               'Exit%20Azahar': 'Start'}
    ui = {f'Shortcuts\\Main%20Window\\{name}\\controller_keyseq': combo(button) for name, button in hotkeys.items()}
    # Back+L3 alterna entre Tela grande (2: a de cima grande, a outra menor ao lado) e uma tela
    # (1); Back+R3 troca qual aparece/qual é a grande. Empilhadas (0) ficavam pequenas em 16:9.
    layout = {'layout_option': '2', 'layouts_to_cycle': '2, 1'}
    return controls, ui, layout


PAD = dict(Up='DPadUp', Down='DPadDown', Left='DPadLeft', Right='DPadRight',
           Cross='A', Circle='B', Square='X', Triangle='Y', Select='Back', Start='Start',
           L1='LeftShoulder', R1='RightShoulder', L2='+LeftTrigger', R2='+RightTrigger',
           L3='LeftStick', R3='RightStick', LUp='-LeftY', LDown='+LeftY',
           LLeft='-LeftX', LRight='+LeftX', RUp='-RightY', RDown='+RightY',
           RLeft='-RightX', RRight='+RightX')


def planned(home, controller=None):
    out = {}
    def change(path, section, values, append=False):
        path = path.resolve()
        text = out.get(path, path.read_text(encoding='utf-8') if path.is_file() else '')
        out[path] = edit(text, section, values, append)
    pcsx = home / '.var/app/net.pcsx2.PCSX2/config/PCSX2/inis/PCSX2.ini'
    duck = home / '.local/share/duckstation/settings.ini'
    for path, section in ((pcsx, 'Pad1'), (duck, 'Controller1')):
        if not path.is_file():
            continue
        change(path, 'InputSources', {'SDL': 'true'})
        buttons = {'A': 'FaceSouth', 'B': 'FaceEast', 'X': 'FaceWest', 'Y': 'FaceNorth'} if path == pcsx else {}
        change(path, section, {key: 'SDL-0/' + buttons.get(value, value) for key, value in PAD.items()}, True)
        if path == duck:
            change(path, section, {'Type': 'AnalogController'})
        change(path, section, {'LargeMotor': 'SDL-0/LargeMotor', 'SmallMotor': 'SDL-0/SmallMotor'})
        names = dict(save='SaveStateToSlot', load='LoadStateFromSlot', next='NextSaveStateSlot', previous='PreviousSaveStateSlot', exit='ShutdownVM', speed='ToggleTurbo') if path == pcsx else dict(save='SaveSelectedSaveState', load='LoadSelectedSaveState', next='SelectNextSaveStateSlot', previous='SelectPreviousSaveStateSlot', exit='PowerOff', speed='ToggleFastForward')
        bindings = {names['save']: 'LeftShoulder', names['load']: 'RightShoulder',
                    names['next']: 'DPadUp', names['previous']: 'DPadDown',
                    names['exit']: 'Start', names['speed']: 'DPadRight',
                    'TogglePause': 'B', 'OpenPauseMenu': 'Y', 'Screenshot': 'X'}
        change(path, 'Hotkeys', {key: 'SDL-0/Back & SDL-0/' + buttons.get(value, value) for key, value in bindings.items()}, True)
    ra = home / '.var/app/org.libretro.RetroArch/config/retroarch/retroarch.cfg'
    if ra.is_file():
        values = {'input_enable_hotkey_btn': '6', 'input_save_state_btn': '4',
                  'input_load_state_btn': '5', 'input_state_slot_increase_btn': 'h0up',
                  'input_state_slot_decrease_btn': 'h0down', 'input_exit_emulator_btn': '7',
                  'input_menu_toggle_btn': '3', 'input_pause_toggle_btn': '1',
                  'input_screenshot_btn': '2', 'input_toggle_fast_forward_btn': 'h0right',
                  'input_rewind_btn': 'nul', 'input_toggle_slowmotion_btn': 'nul'}
        change(ra, '', {k: '"' + v + '"' for k, v in values.items()})
    dolphin = home / '.var/app/org.DolphinEmu.dolphin-emu/config/dolphin-emu'
    if dolphin.is_dir():
        change(dolphin / 'Dolphin.ini', 'Interface', {'ConfirmStop': 'False'})
        profile = home / '.local/share/flatpak/app/org.DolphinEmu.dolphin-emu/current/active/files/share/dolphin-emu/Sys/Profiles/GCPad/SDL Gamepad.ini'
        if not profile.is_file():
            raise ValueError('perfil SDL oficial do Dolphin ausente')
        values = {line.split('=', 1)[0].strip(): line.split('=', 1)[1].strip()
                  for line in profile.read_text().splitlines() if '=' in line}
        values['Device'] = dolphin_device(controller or pick_controller(load_registry()))
        # O perfil oficial preserva a disposição A/B/X/Y do Xbox.
        change(dolphin / 'GCPadNew.ini', 'GCPad1', values)
        keys = {'Save State/Save to Selected Slot': 'Shoulder L',
                'Load State/Load from Selected Slot': 'Shoulder R',
                'Other State Hotkeys/Increase Selected State Slot': 'Pad N',
                'Other State Hotkeys/Decrease Selected State Slot': 'Pad S',
                'General/Stop': 'Start', 'General/Toggle Pause': 'Button B',
                'General/Take Screenshot': 'Button X',
                'Emulation Speed/Disable Emulation Speed Limit': 'Pad E'}
        change(dolphin / 'Hotkeys.ini', 'Hotkeys', {'Device': values['Device'], **{
            key: '`Back` & `' + value + '`' for key, value in keys.items()}})
        wii = {'Device': values['Device'], 'Extension': 'Nunchuk',
               'Buttons/A': '`Button A`', 'Buttons/B': '`Trigger R`', 'Buttons/1': '`Button X`',
               'Buttons/2': '`Button B`', 'Buttons/+': '`Start`', 'Buttons/-': '`Back`',
               'Buttons/Home': '`Button Y`', 'Nunchuk/Buttons/C': '`Shoulder L`',
               'Nunchuk/Buttons/Z': '`Trigger L`', 'Nunchuk/Stick/Up': '`Left Y+`',
               'Nunchuk/Stick/Down': '`Left Y-`', 'Nunchuk/Stick/Left': '`Left X-`',
               'Nunchuk/Stick/Right': '`Left X+`', 'IR/Up': '`Right Y+`',
               'IR/Down': '`Right Y-`', 'IR/Left': '`Right X-`', 'IR/Right': '`Right X+`',
               'Shake/X': '`Shoulder R`', 'Shake/Y': '`Shoulder R`', 'Shake/Z': '`Shoulder R`'}
        for direction, control in [('Up','N'), ('Down','S'), ('Left','W'), ('Right','E')]:
            wii['D-Pad/' + direction] = '`Pad ' + control + '`'
        change(dolphin / 'WiimoteNew.ini', 'Wiimote1', wii)
    psp = home / '.var/app/org.ppsspp.PPSSPP/config/ppsspp/PSP/SYSTEM/controls.ini'
    if psp.is_file():
        controls = {'Save State': '194', 'Load State': '195', 'Next Slot': '19',
                    'Previous Slot': '20', 'Pause': '188', 'Pause (no menu)': '190',
                    'Screenshot': '191', 'SpeedToggle': '22', 'Exit App': '197'}
        text = psp.read_text(encoding='utf-8')
        values = {}
        for key, value in controls.items():
            match = re.search(r'^' + re.escape(key) + r'\s*=\s*(.*)$', text, re.M)
            old = match[1].split(',') if match else []
            combo = '10-196:10-' + value
            values[key] = ','.join(old + ([combo] if combo not in old else []))
        change(psp, 'ControlMapping', values)
    azahar = home / '.var/app/org.azahar_emu.Azahar/config/azahar-emu/qt-config.ini'
    if azahar.is_file():
        guid = azahar_guid(home, controller)
        if guid is None:
            print('Azahar: ligue o controle Xbox e rode de novo (o GUID vem do SDL do Azahar).')
        else:
            controls, ui, layout = azahar_values(guid)
            text = out.get(azahar.resolve(), azahar.read_text(encoding='utf-8'))
            for section, values in (('Controls', controls), ('UI', ui), ('Layout', layout)):
                text = qt_edit(text, section, values)
            out[azahar.resolve()] = text
    nds = home / '.var/app/org.libretro.RetroArch/config/retroarch/config/melonDS/NDS.opt'
    if nds.is_file():
        # Mouse faz a caneta (cursor desenhado pelo core, clique esquerdo toca); RT troca as
        # telas (Toggle); Hybrid Top = tela de cima grande + a outra menor (as duas cabem).
        change(nds, '', {'melonds_touch_mode': '"Mouse"', 'melonds_swapscreen_mode': '"Toggle"',
                         'melonds_screen_layout': '"Hybrid Top"'})
        # Escala inteira global deixava o DS em 2x (512x768) numa tela 1080p.
        change(nds.with_suffix('.cfg'), '', {'video_scale_integer': '"false"'})
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--controller', help='id do controle no registro (padrão: o principal, Xbox One)')
    parser.add_argument('--learn', metavar='ID', help='mede o controle conectado e grava no registro')
    parser.add_argument('--detect', action='store_true', help='lista os controles que o SDL vê e o que já está medido')
    args = parser.parse_args()
    registry = load_registry()
    if args.detect or args.learn:
        pads = probe_pads()
        if args.detect:
            known = {c['sdl_name']: c['id'] for c in registry['controllers'] if c.get('sdl_name')}
            for pad in pads:
                print(f"{pad['index']}: {pad['name']} guid={pad['guid']} -> {known.get(pad['name'], 'não medido')}")
            return
        entry = learn(registry, args.learn, pads, datetime.now().strftime('%Y-%m-%d'))
        REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print(f"Medido: {entry['label']} = {entry['sdl_name']} ({entry['guid']})")
        return
    for name in ('retroarch', 'pcsx2-qt', 'dolphin-emu', 'duckstation-qt', 'PPSSPPSDL', 'azahar'):
        if subprocess.run(['pgrep', '-x', name], capture_output=True).returncode == 0:
            raise SystemExit('Feche o emulador antes de configurar: ' + name)
    changes = planned(Path.home(), pick_controller(registry, args.controller))
    backup = Path(__file__).resolve().parent.parent / 'auditoria' / ('controle-xbox-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    for index, (path, text) in enumerate(changes.items()):
        old = path.read_text(encoding='utf-8') if path.is_file() else ''
        if old == text:
            continue
        print(path)
        if args.apply:
            backup.mkdir(parents=True, exist_ok=True)
            if path.is_file():
                shutil.copy2(path, backup / (str(index) + '-' + path.name))
            if (path.read_text(encoding='utf-8') if path.is_file() else '') != old:
                raise SystemExit('Arquivo mudou; aplicação interrompida: ' + str(path))
            path.write_text(text, encoding='utf-8')
    print('Aplicado. Cópias anteriores em ' + str(backup) if args.apply else 'Simulação. Use --apply.')


if __name__ == '__main__':
    main()

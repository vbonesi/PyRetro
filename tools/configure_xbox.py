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
        block = [line for line in block if not ('=' in line and line.split('=', 1)[0].strip() == key)]
        while block and not block[-1].strip():
            block.pop()
        block += [key + ' = ' + v + '\n' for v in new]
    if section and end < len(lines):
        while block and not block[-1].strip():
            block.pop()
        block.append('\n')
    return ''.join(lines[:start] + block + lines[end:])


PAD = dict(Up='DPadUp', Down='DPadDown', Left='DPadLeft', Right='DPadRight',
           Cross='A', Circle='B', Square='X', Triangle='Y', Select='Back', Start='Start',
           L1='LeftShoulder', R1='RightShoulder', L2='+LeftTrigger', R2='+RightTrigger',
           L3='LeftStick', R3='RightStick', LUp='-LeftY', LDown='+LeftY',
           LLeft='-LeftX', LRight='+LeftX', RUp='-RightY', RDown='+RightY',
           RLeft='-RightX', RRight='+RightX')


def planned(home):
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
        values['Device'] = 'SDL/0/Xbox One S Controller'
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
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    for name in ('retroarch', 'pcsx2-qt', 'dolphin-emu', 'duckstation-qt', 'PPSSPPSDL'):
        if subprocess.run(['pgrep', '-x', name], capture_output=True).returncode == 0:
            raise SystemExit('Feche o emulador antes de configurar: ' + name)
    changes = planned(Path.home())
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

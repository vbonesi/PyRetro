#!/usr/bin/env python3
"""Lista controles como o SDL do runtime os vê: índice, nome e GUID (para o Azahar).

Rodar dentro do sandbox do emulador, para usar a mesma biblioteca SDL:
    flatpak run --command=python3 org.azahar_emu.Azahar tools/sdl_probe.py
Imprime uma linha JSON por controle; nada é gravado.
"""
import ctypes
import json
import time

class SDL_GUID(ctypes.Structure):  # struct de 16 bytes passada por valor
    _fields_ = [('data', ctypes.c_uint8 * 16)]


sdl = ctypes.CDLL('libSDL2-2.0.so.0')
sdl.SDL_JoystickNameForIndex.restype = ctypes.c_char_p
sdl.SDL_JoystickGetDeviceGUID.restype = SDL_GUID
sdl.SDL_JoystickGetDeviceGUID.argtypes = [ctypes.c_int]
sdl.SDL_JoystickGetGUIDString.argtypes = [SDL_GUID, ctypes.c_char_p, ctypes.c_int]
sdl.SDL_SetHint(b'SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS', b'1')
if sdl.SDL_Init(0x200 | 0x2000) != 0:  # JOYSTICK | GAMECONTROLLER
    raise SystemExit('SDL_Init falhou')
time.sleep(1.5)  # dispositivos Bluetooth/HIDAPI aparecem com atraso
sdl.SDL_PumpEvents()
for index in range(sdl.SDL_NumJoysticks()):
    guid = sdl.SDL_JoystickGetDeviceGUID(index)
    text = ctypes.create_string_buffer(33)
    sdl.SDL_JoystickGetGUIDString(guid, text, 33)
    print(json.dumps({'index': index, 'name': (sdl.SDL_JoystickNameForIndex(index) or b'').decode(),
                      'guid': text.value.decode(), 'controller': bool(sdl.SDL_IsGameController(index))}))
sdl.SDL_Quit()

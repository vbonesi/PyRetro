"""Ambiente da sessão gráfica para os programas que o servidor abre.

O serviço `pyretro-gui` sobe com o systemd do usuário antes do Plasma exportar a sessão;
sem `WAYLAND_DISPLAY`/`DISPLAY` o emulador abria e fechava em 2 s sem janela (07/11/2026).
O valor atual vem de `systemctl --user show-environment`, lido a cada lançamento.
"""
import os
import subprocess

SESSION_KEYS = ('WAYLAND_DISPLAY', 'DISPLAY', 'XAUTHORITY', 'XDG_SESSION_TYPE',
                'XDG_CURRENT_DESKTOP', 'XDG_SESSION_DESKTOP', 'DBUS_SESSION_BUS_ADDRESS',
                'QT_QPA_PLATFORMTHEME')


def session_env(base=None, run=subprocess.run):
    env = dict(os.environ if base is None else base)
    try:
        out = run(['systemctl', '--user', 'show-environment'], capture_output=True,
                  text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return env
    for line in out.splitlines():
        key, sep, value = line.partition('=')
        # Valores com espaço/aspas vêm escapados ($'...'); os da sessão gráfica não têm.
        if sep and key in SESSION_KEYS and value and not value.startswith("$'"):
            env[key] = value
    return env

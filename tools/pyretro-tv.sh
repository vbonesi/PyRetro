#!/bin/sh
# Abre o modo TV na janela nativa (gui/app.py); sem PyQt6, cai no Chrome Flatpak.
# O processo fica ligado ao atalho da Steam até fechar a TV.
set -eu
root=$(dirname "$(dirname "$(readlink -f "$0")")")
# PYRETRO_TV_CHROME=1 força o Chrome (volta atrás sem mexer no código).
native() { [ -z "${PYRETRO_TV_CHROME-}" ] && python3 -c 'import PyQt6.QtWebEngineWidgets' >/dev/null 2>&1; }
if [ "${1-}" = '--dry-run' ]; then
    if native; then
        printf '%s\n' 'python3 gui/app.py'
    else
        printf '%s\n' 'systemctl --user start pyretro-gui' 'flatpak run com.google.Chrome --user-data-dir=<perfil PyRetro> --app=http://127.0.0.1:8000/tv --start-fullscreen'
    fi
    exit 0
fi
# Em segundo plano: o Big Picture fica ativo em tela cheia e esconderia a janela.
raise() { "$root/tools/raise-window.sh" "$1" 25 >/dev/null 2>&1 & }
if native; then
    raise pyretro-tv
    exec python3 "$root/gui/app.py"
fi
systemctl --user start pyretro-gui
raise chrome-127.0.0.1__tv
exec flatpak run com.google.Chrome \
    --user-data-dir="$HOME/.var/app/com.google.Chrome/config/pyretro-tv" \
    --no-first-run --no-default-browser-check \
    --app=http://127.0.0.1:8000/tv --start-fullscreen

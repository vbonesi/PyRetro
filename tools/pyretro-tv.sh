#!/bin/sh
# Perfil separado mantém o processo ligado ao atalho da Steam até fechar a TV.
set -eu
if [ "${1-}" = '--dry-run' ]; then
    printf '%s\n' 'systemctl --user start pyretro-gui' 'flatpak run com.google.Chrome --user-data-dir=<perfil PyRetro> --app=http://127.0.0.1:8000/tv --start-fullscreen'
    exit 0
fi
systemctl --user start pyretro-gui
# Em segundo plano: o Big Picture fica ativo em tela cheia e esconderia a janela.
"$(dirname "$(readlink -f "$0")")/raise-window.sh" chrome-127.0.0.1__tv 25 >/dev/null 2>&1 &
exec flatpak run com.google.Chrome \
    --user-data-dir="$HOME/.var/app/com.google.Chrome/config/pyretro-tv" \
    --no-first-run --no-default-browser-check \
    --app=http://127.0.0.1:8000/tv --start-fullscreen

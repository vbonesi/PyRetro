#!/bin/sh
# Traz para a frente a janela (KWin/Wayland) cuja classe contém o texto dado.
# Necessário porque o Big Picture fica em tela cheia e ativo; sem isso, o app
# aberto por um atalho da Steam surge atrás dele e não aparece no Steam Link.
# Uso: raise-window.sh <trecho-da-classe> [tentativas]
set -eu
pattern=${1:?uso: raise-window.sh <trecho-da-classe> [tentativas]}
tries=${2:-20}
case $pattern in *[!A-Za-z0-9._-]*) echo 'trecho de classe inválido' >&2; exit 2;; esac
script=$(mktemp "${XDG_RUNTIME_DIR:-/tmp}/pyretro-raise.XXXXXX.js")
name=pyretro-raise-$$
trap 'qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript "$name" >/dev/null 2>&1 || true; rm -f "$script"' EXIT
cat > "$script" <<JS
for (const w of workspace.windowList()) {
  if (w.resourceClass.toLowerCase().indexOf("$pattern") >= 0) { w.minimized = false; workspace.activeWindow = w; }
}
JS
i=0
while [ "$i" -lt "$tries" ]; do
    qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript "$name" >/dev/null 2>&1 || true
    qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript "$script" "$name" >/dev/null
    qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.start >/dev/null
    sleep 1
    i=$((i + 1))
done

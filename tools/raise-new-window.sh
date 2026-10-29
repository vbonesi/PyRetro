#!/bin/sh
# Ativa a próxima janela (KWin/Wayland) cuja classe contenha um dos trechos dados.
# O PyRetro fica em tela cheia e ativo; sem isso o emulador recém-aberto surgia atrás dele.
# Uso: raise-new-window.sh <segundos> <trecho-da-classe>...
set -eu
seconds=${1:?uso: raise-new-window.sh <segundos> <trecho-da-classe>...}
shift
[ "$#" -gt 0 ] || { echo 'informe ao menos um trecho de classe' >&2; exit 2; }
case $seconds in *[!0-9]*) echo 'segundos inválidos' >&2; exit 2;; esac
list=
for pattern in "$@"; do
    case $pattern in *[!A-Za-z0-9._-]*|'') echo 'trecho de classe inválido' >&2; exit 2;; esac
    list="$list\"$pattern\","
done
script=$(mktemp "${XDG_RUNTIME_DIR:-/tmp}/pyretro-raise-new.XXXXXX.js")
name=pyretro-raise-new-$$
trap 'qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript "$name" >/dev/null 2>&1 || true; rm -f "$script"' EXIT
cat > "$script" <<JS
const wanted = [$list];
const match = w => wanted.some(p => w.resourceClass.toLowerCase().indexOf(p) >= 0);
const raise = w => { if (match(w)) { w.minimized = false; workspace.activeWindow = w; } };
// No Wayland a classe só chega depois de a janela ser criada.
workspace.windowAdded.connect(w => { raise(w); w.windowClassChanged.connect(() => raise(w)); });
JS
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript "$name" >/dev/null 2>&1 || true
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript "$script" "$name" >/dev/null
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.start >/dev/null
sleep "$seconds"

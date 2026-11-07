#!/bin/sh
# Traz para a frente a janela (KWin/Wayland) cuja classe contém o texto dado.
# Necessário porque o Big Picture fica em tela cheia e ativo; sem isso, o app
# aberto por um atalho da Steam surge atrás dele e não aparece no Steam Link.
# Ativa a janela já aberta ou quando ela surgir; depois só a traz de volta se a
# Steam tomar o foco. Antes reativava a cada segundo e, se um jogo abrisse nesse
# intervalo, o PyRetro passava por cima dele (07/11/2026).
# Uso: raise-window.sh <trecho-da-classe> [segundos]
set -eu
pattern=${1:?uso: raise-window.sh <trecho-da-classe> [segundos]}
seconds=${2:-20}
case $pattern in *[!A-Za-z0-9._-]*) echo 'trecho de classe inválido' >&2; exit 2;; esac
case $seconds in ''|*[!0-9]*) echo 'segundos inválidos' >&2; exit 2;; esac
script=$(mktemp "${XDG_RUNTIME_DIR:-/tmp}/pyretro-raise.XXXXXX.js")
name=pyretro-raise-$$
trap 'qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript "$name" >/dev/null 2>&1 || true; rm -f "$script"' EXIT
cat > "$script" <<JS
const has = (w, text) => !!w && (w.resourceClass || "").toLowerCase().indexOf(text) >= 0;
const raise = w => { w.minimized = false; workspace.activeWindow = w; };
const target = () => workspace.windowList().find(w => has(w, "$pattern"));
const now = target();
if (now) raise(now);
// No Wayland a classe só chega depois de a janela ser criada.
workspace.windowAdded.connect(w => {
  if (has(w, "$pattern")) raise(w);
  w.windowClassChanged.connect(() => { if (has(w, "$pattern")) raise(w); });
});
workspace.windowActivated.connect(w => {
  if (has(w, "steam") && !has(w, "$pattern")) { const t = target(); if (t) raise(t); }
});
JS
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript "$name" >/dev/null 2>&1 || true
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript "$script" "$name" >/dev/null
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.start >/dev/null
sleep "$seconds"

/* Barra lateral com os cinco destinos (Início, Biblioteca, Desejados, Apps e stream, Ferramentas). Fica como
   trilho de ícones e abre com rótulos quando recebe o foco (View/Select, M, ← na borda esquerda, ou o mouse). */
import {load} from "./catalog.js";
import {$, button} from "./dom.js";
import {rememberFocus} from "./focus.js";
import {state} from "./state.js";
export const DESTINATIONS = [["home", "🏠", "Início"], ["library", "📚", "Biblioteca"], ["wishlist", "♡", "Desejados"], ["apps", "📺", "Apps e stream"], ["tools", "🛠", "Ferramentas"]];
// Coleções antigas (Neste PC, Favoritos, Sistemas, Jogando, Ranking, ROMs…) moram sob Biblioteca até o N4 virarem filtros.
const OWN = new Set(["home", "wishlist", "apps", "tools"]);
export const destinationOf = kind => OWN.has(kind) ? kind : "library";
export function renderSidebar() {
  const nav = $("destinations");
  if (!nav.children.length) nav.replaceChildren(...DESTINATIONS.map(([kind, icon, label], i) => {
    const b = button("", () => load(kind)); b.dataset.destination = kind; b.setAttribute("aria-label", `${label} (${i + 1})`);
    b.append(Object.assign(document.createElement("span"), {className: "dest-icon", textContent: icon}), Object.assign(document.createElement("span"), {className: "dest-label", textContent: label}));
    return b;
  }));
  const current = destinationOf(state.kind);
  for (const b of nav.children) { if (b.dataset.destination === current) { b.setAttribute("aria-current", "page"); rememberFocus(b); } else b.removeAttribute("aria-current"); }
}
export const inSidebar = () => $("sidebar").contains(document.activeElement);
export function focusSidebar() { ($("destinations").querySelector('[aria-current="page"]') || $("destinations").querySelector("button"))?.focus(); }
// De volta ao conteúdo: destaque do Início, primeira capa ou, na Biblioteca, a primeira visão.
export function focusContent() {
  const first = [$("spotlight-open"), $("home").querySelector("button"), $("gallery").querySelector("button"), $("collections").querySelector("button"), $("tools").querySelector("button")]
    .find(e => e && !e.hidden && e.getClientRects().length);
  first?.focus();
}
// Com LT/RT os cinco destinos giram: qualquer um fica a no máximo dois passos do Início.
export function stepDestination(delta) {
  const index = Math.max(0, DESTINATIONS.findIndex(d => d[0] === destinationOf(state.kind)));
  load(DESTINATIONS[(index + delta + DESTINATIONS.length) % DESTINATIONS.length][0]);
}
export function goDestination(number) { const d = DESTINATIONS[number - 1]; if (d) load(d[0]); }

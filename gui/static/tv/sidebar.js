/* Barra lateral com os cinco destinos (Início, Biblioteca, Desejados, Apps e stream, Ferramentas). Fica como
   trilho de ícones e abre com rótulos quando recebe o foco (View/Select, M, ← na borda esquerda, ou o mouse). */
import {load} from "./catalog.js";
import {$, button} from "./dom.js";
import {rememberFocus} from "./focus.js";
import {closeAllPages} from "./pages.js";
import {state} from "./state.js";
// Ícones SVG de traço único (currentColor, 24×24, mesmo peso): no lugar de emoji coloridos misturados com glifos de texto.
const ICONS = {
  home: "M3 11.5 12 4l9 7.5M5.5 10v10h13V10M10 20v-5.5h4V20",
  library: "M4 4h4.5v16H4zM10.5 4H15v16h-4.5zM16.6 5.4l4.2-1.1 3 14.3-4.2 1.1z",
  wishlist: "M12 20.5s-8-4.9-8-10.7A4.4 4.4 0 0 1 12 7a4.4 4.4 0 0 1 8 2.8c0 5.8-8 10.7-8 10.7z",
  apps: "M3 7h18v11H3zM8 3.5 12 7l4-3.5M8.5 21h7",
  tools: "M14.5 6.2a4.2 4.2 0 0 0-5.4 5.3L3.5 17.1 6.9 20.5l5.6-5.6a4.2 4.2 0 0 0 5.3-5.4l-2.7 2.7-2.6-.7-.7-2.6z",
};
function icon(kind) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg"), path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  svg.setAttribute("viewBox", "0 0 24 24"); svg.setAttribute("aria-hidden", "true"); svg.setAttribute("class", "dest-icon");
  for (const [k, v] of Object.entries({fill: "none", stroke: "currentColor", "stroke-width": "1.8", "stroke-linecap": "round", "stroke-linejoin": "round"})) svg.setAttribute(k, v);
  path.setAttribute("d", ICONS[kind]); svg.append(path); return svg;
}
export const DESTINATIONS = [["home", "", "Início"], ["library", "", "Biblioteca"], ["wishlist", "", "Desejados"], ["apps", "", "Apps e stream"], ["tools", "", "Ferramentas"]];
// Coleções antigas (Neste PC, Favoritos, Sistemas, Jogando, Ranking, ROMs…) moram sob Biblioteca até o N4 virarem filtros.
const OWN = new Set(["home", "wishlist", "apps", "tools"]);
export const destinationOf = kind => OWN.has(kind) ? kind : "library";
export function renderSidebar() {
  const nav = $("destinations");
  if (!nav.children.length) nav.replaceChildren(...DESTINATIONS.map(([kind, , label], i) => {
    const b = button("", () => go(kind)); b.dataset.destination = kind; b.setAttribute("aria-label", `${label} (${i + 1})`);
    b.append(icon(kind), Object.assign(document.createElement("span"), {className: "dest-label", textContent: label}));
    return b;
  }));
  const current = destinationOf(state.kind);
  for (const b of nav.children) { if (b.dataset.destination === current) { b.setAttribute("aria-current", "page"); rememberFocus(b); } else b.removeAttribute("aria-current"); }
}
export const inSidebar = () => $("sidebar").contains(document.activeElement);
export function focusSidebar() { ($("destinations").querySelector('[aria-current="page"]') || $("destinations").querySelector("button"))?.focus(); }
// De volta ao conteúdo: destaque do Início, primeira capa ou, na Biblioteca, a primeira visão.
export function focusContent() {
  const first = [$("details").hidden ? null : $("close"), $("tool-dialog").hidden ? null : $("tool-close"), $("spotlight-open"), $("home").querySelector("button"), $("gallery").querySelector("button"), $("quick").querySelector("button"), $("tools").querySelector("button")]
    .find(e => e && !e.hidden && e.getClientRects().length);
  first?.focus();
}
// Com LT/RT os cinco destinos giram: qualquer um fica a no máximo dois passos do Início.
export function stepDestination(delta) {
  const index = Math.max(0, DESTINATIONS.findIndex(d => d[0] === destinationOf(state.kind)));
  go(DESTINATIONS[(index + delta + DESTINATIONS.length) % DESTINATIONS.length][0]);
}
export function goDestination(number) { const d = DESTINATIONS[number - 1]; if (d) go(d[0]); }
function go(kind) { closeAllPages(); return load(kind); }

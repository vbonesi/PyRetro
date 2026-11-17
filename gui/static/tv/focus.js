import {$} from "./dom.js";
import {state} from "./state.js";
export function focusable() {
  const root = document.querySelector("dialog[open]") || document;
  return [...root.querySelectorAll("button:not(:disabled),a[href],input")].filter(e => !e.hidden && e.getClientRects().length);
}
function galleryMove(direction, current) {
  // Na grade: esquerda/direita seguem a ordem dos cards (quebrando de linha); no fim da lista ficam onde estão em vez de subir aos menus.
  const gallery = $("gallery"); if (!gallery || state.kind === "home" || !gallery.contains(current)) return false;
  const cards = [...gallery.querySelectorAll("button")].filter(e => !e.hidden && e.getClientRects().length);
  const index = cards.indexOf(current); if (index < 0) return false;
  const top = cards[0].getBoundingClientRect().top;
  const columns = Math.max(1, cards.filter(e => Math.abs(e.getBoundingClientRect().top - top) < 5).length);
  let target = direction === "right" ? index + 1 : direction === "left" ? index - 1 : direction === "down" ? index + columns : index - columns;
  if (direction === "up" && target < 0) return false;
  if (target >= cards.length) target = direction === "down" && Math.floor(index / columns) < Math.floor((cards.length - 1) / columns) ? cards.length - 1 : index;
  if (target < 0) target = 0;
  cards[target].focus({preventScroll: true}); cards[target].scrollIntoView({block: "nearest", inline: "nearest"});
  return true;
}
export function move(direction) {
  const nodes = focusable(); const current = document.activeElement;
  if (!nodes.includes(current)) { nodes[0]?.focus(); return; }
  if (galleryMove(direction, current)) return;
  const r = current.getBoundingClientRect(); const x = r.x + r.width / 2, y = r.y + r.height / 2;
  let best, score = Infinity;
  for (const e of nodes) {
    if (e === current) continue;
    const b = e.getBoundingClientRect(); const dx = b.x + b.width / 2 - x, dy = b.y + b.height / 2 - y;
    const primary = direction === "left" ? -dx : direction === "right" ? dx : direction === "up" ? -dy : dy;
    const cross = Math.abs(direction === "left" || direction === "right" ? dy : dx);
    if (primary <= 2) continue;
    const cost = primary + cross * 4;
    if (cost < score) { best = e; score = cost; }
  }
  if (best) { best.focus({preventScroll: true}); best.scrollIntoView({block: "nearest", inline: "nearest"}); }
}
export function page(direction) {
  const row = document.activeElement.closest?.(".shelf");
  const cards = [...(row || (state.kind === "home" ? $("home").querySelector(".shelf") : $("gallery")) || $("gallery")).querySelectorAll("button")]; if (!cards.length) return;
  const current = Math.max(0, cards.indexOf(document.activeElement));
  const first = cards[0].getBoundingClientRect();
  const columns = cards.filter(e => Math.abs(e.getBoundingClientRect().top - first.top) < 5).length;
  const height = innerHeight - document.querySelector("footer").getBoundingClientRect().height;
  const rows = Math.max(1, Math.floor(height / (first.height + 24)));
  const jump = state.kind === "home" ? Math.max(1, Math.floor((row?.clientWidth || innerWidth) / (first.width + 24))) : columns * rows;
  const target = cards[Math.max(0, Math.min(cards.length - 1, current + direction * jump))];
  target.focus({preventScroll: true}); target.scrollIntoView({block: "center"});
}
// Analógico direito: rola a área com foco (ficha, ferramenta, página, fileira de capas). A cruz só move o
// foco entre botões; num texto comprido não havia como subir/descer (pedido de 07/11/2026).
export function stickScroll(value, ms) {
  const dead = .25, magnitude = Math.abs(value);
  if (magnitude <= dead) return 0;
  return Math.sign(value) * ((magnitude - dead) / (1 - dead)) ** 1.5 * 1500 * Math.min(ms, 50) / 1000;
}
export function scrollTarget(start = document.activeElement, horizontal = false) {
  const [overflow, size, client] = horizontal ? ["overflowX", "scrollWidth", "clientWidth"] : ["overflowY", "scrollHeight", "clientHeight"];
  const scrollable = el => /(auto|scroll)/.test(getComputedStyle(el)[overflow]) && el[size] > el[client] + 1;
  for (let el = start; el && el !== document.body && el !== document.documentElement; el = el.parentElement)
    if (scrollable(el)) return el;
  const dialog = [...document.querySelectorAll("dialog[open]")].pop();
  if (dialog) return [dialog, ...dialog.querySelectorAll("*")].find(scrollable) || dialog;
  return document.scrollingElement || document.documentElement;
}

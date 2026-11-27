import {$} from "./dom.js";
import {state} from "./state.js";
// Prateleiras (fileiras do Início): o card focado fica na 1ª coluna visível e a fileira desliza por baixo, sem barra
// de rolagem. Uma animação por vez: passos repetidos (D-pad segurado) só guardam o destino mais novo.
const reduced = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
const shelfAnim = new WeakMap();
function ensureVisibleY(el) {
  const box = el.getBoundingClientRect(), footer = document.querySelector("footer")?.getBoundingClientRect().height || 0;
  const over = box.bottom - (innerHeight - footer - 8), under = box.top - 8;
  if (over > 0) scrollBy({top: over}); else if (under < 0) scrollBy({top: under});
}
export function alignShelf(card) {
  const row = card.closest(".shelf"); if (!row) return;
  ensureVisibleY(card);
  const state = shelfAnim.get(row) || {busy: false, target: null, last: null}; shelfAnim.set(row, state);
  state.target = Math.max(0, card.getBoundingClientRect().left - row.getBoundingClientRect().left + row.scrollLeft - parseFloat(getComputedStyle(row).paddingLeft || "0"));
  if (state.busy) return;
  const step = () => {
    const left = state.target; state.target = null; state.busy = true; state.last = left;
    row.scrollTo({left, behavior: reduced() ? "instant" : "smooth"});
    setTimeout(() => { state.busy = false; if (state.target != null && state.target !== state.last) step(); }, reduced() ? 0 : 160);
  };
  step();
}
document.addEventListener("focusin", e => { const card = e.target instanceof HTMLElement && e.target.closest?.(".shelf > button"); if (card) alignShelf(card); });
export function focusable() {
  const root = document.querySelector("dialog[open]") || document;
  // As setas ‹ › das fileiras são só do mouse: controle e teclado correm a fileira pelo próprio foco.
  const mouse = document.body.dataset.input === "mouse";
  return [...root.querySelectorAll("button:not(:disabled),a[href],input")].filter(e => !e.hidden && e.getClientRects().length && (mouse || !e.closest(".shelf-controls")));
}
function galleryMove(direction, current) {
  // Na grade: esquerda/direita seguem a ordem dos cards (quebrando de linha); no fim da lista ficam onde estão em vez de subir aos menus.
  const gallery = $("gallery"); if (!gallery || state.kind === "home" || !gallery.contains(current)) return false;
  const cards = [...gallery.querySelectorAll("button")].filter(e => !e.hidden && e.getClientRects().length);
  const index = cards.indexOf(current); if (index < 0) return false;
  const top = cards[0].getBoundingClientRect().top;
  const columns = Math.max(1, cards.filter(e => Math.abs(e.getBoundingClientRect().top - top) < 5).length);
  if (direction === "left" && index % columns === 0) return false; // borda esquerda: a geometria leva à barra lateral
  let target = direction === "right" ? index + 1 : direction === "left" ? index - 1 : direction === "down" ? index + columns : index - columns;
  if (direction === "up" && target < 0) return false;
  if (target >= cards.length) target = direction === "down" && Math.floor(index / columns) < Math.floor((cards.length - 1) / columns) ? cards.length - 1 : index;
  if (target < 0) target = 0;
  cards[target].focus({preventScroll: true}); cards[target].scrollIntoView({block: "nearest", inline: "nearest"});
  return true;
}
// Vizinho por geometria: dos retângulos candidatos, o que fica na direção pedida com menor custo (distância no
// eixo + 4× o desvio no eixo cruzado). Função pura: recebe e devolve retângulos {x, y, width, height}.
export function pickNeighbor(from, candidates, direction) {
  const x = from.x + from.width / 2, y = from.y + from.height / 2;
  let best = -1, score = Infinity;
  candidates.forEach((b, i) => {
    const dx = b.x + b.width / 2 - x, dy = b.y + b.height / 2 - y;
    const primary = direction === "left" ? -dx : direction === "right" ? dx : direction === "up" ? -dy : dy;
    const cross = Math.abs(direction === "left" || direction === "right" ? dy : dx);
    if (primary <= 2) return;
    const cost = primary + cross * 4;
    if (cost < score) { best = i; score = cost; }
  });
  return best;
}
// Memória por região: cada área marcada com data-region (menu, filtros, galeria, cada fileira) lembra o último
// botão focado; ao entrar nela por outra direção, o foco volta para ele em vez de cair no mais próximo.
const memory = new Map();
export function regionOf(el) { return el.closest?.("[data-region]")?.dataset.region || el.closest?.("dialog, .page")?.id || "pagina"; }
document.addEventListener("focusin", e => { if (e.target instanceof HTMLElement) memory.set(regionOf(e.target), e.target); });
export function rememberFocus(el) { memory.set(regionOf(el), el); }
export function recallFocus(region, nodes) { const el = memory.get(region); return el && el.isConnected && nodes.includes(el) ? el : null; }
export function move(direction) {
  const nodes = focusable(); const current = document.activeElement;
  if (!nodes.includes(current)) { (recallFocus(regionOf(current), nodes) || nodes[0])?.focus(); return; }
  if (galleryMove(direction, current)) return;
  const others = nodes.filter(e => e !== current);
  // ← sem vizinho à esquerda na própria região (destaque, cabeçalho, filtros, galeria, fileiras): vai à barra lateral.
  if (direction === "left" && regionOf(current) !== "barra") {
    const region = regionOf(current), same = others.filter(e => regionOf(e) === region);
    if (pickNeighbor(current.getBoundingClientRect(), same.map(e => e.getBoundingClientRect()), "left") < 0) {
      const bar = recallFocus("barra", nodes) || nodes.find(e => regionOf(e) === "barra");
      if (bar) { bar.focus({preventScroll: true}); return; }
    }
  }
  let best = others[pickNeighbor(current.getBoundingClientRect(), others.map(e => e.getBoundingClientRect()), direction)];
  if (best && regionOf(best) !== regionOf(current)) best = recallFocus(regionOf(best), nodes) || best;
  if (best) { best.focus({preventScroll: true}); if (best.closest(".shelf")) alignShelf(best); else best.scrollIntoView({block: "nearest", inline: "nearest"}); }
}
// Home/End: primeiro e último botão da região em foco (ou da página inteira).
export function jumpEdge(last) {
  const nodes = focusable(), region = regionOf(document.activeElement);
  const inRegion = nodes.filter(e => regionOf(e) === region), list = inRegion.length ? inRegion : nodes;
  const target = last ? list[list.length - 1] : list[0];
  target?.focus({preventScroll: true}); if (target?.closest(".shelf")) alignShelf(target); else target?.scrollIntoView({block: "center", inline: "nearest"});
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
  target.focus({preventScroll: true}); if (target.closest(".shelf")) alignShelf(target); else target.scrollIntoView({block: "center"});
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

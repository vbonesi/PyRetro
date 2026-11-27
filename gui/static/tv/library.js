/* Biblioteca única: um só catálogo (PC, ROMs leves e pesadas, Switch…) com filtros rápidos, painel de filtros
   (sistema, gênero, só local, ordem), estatísticas no cabeçalho e pulo por inicial. As antigas coleções
   (Neste PC, Favoritos, Jogando, Ranking, Sistemas, ROMs leves/pesadas, Pesquisa) são filtros daqui. */
import {$, button, report} from "./dom.js";
import {cardGames, state} from "./state.js";

export const QUICK = [
  ["all", "Tudo", () => true],
  ["playing", "Jogando", g => !!g.tracking.iniciado && !g.tracking.finalizado],
  ["local", "Neste PC", g => !!g.local],
  ["favorites", "Favoritos", g => !!g.favorite],
  ["ranking", "Ranking", g => g.tracking.nota != null],
  ["finished", "Finalizados", g => !!g.tracking.finalizado],
];
export const ORDERS = [["name", "Nome"], ["nota", "Nota"], ["recent", "Jogados recentemente"], ["time", "Tempo jogado"], ["platform", "Plataforma"]];
export const norm = s => String(s ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const byName = (a, b) => norm(a.name).localeCompare(norm(b.name), "pt-BR") || (a.platform || "").localeCompare(b.platform || "", "pt-BR") || String(a.key ?? a.id ?? "").localeCompare(String(b.key ?? b.id ?? ""));
const SORTERS = {
  name: byName,
  nota: (a, b) => (b.tracking.nota ?? -1) - (a.tracking.nota ?? -1) || byName(a, b),
  recent: (a, b) => String(b.lastPlayed || "").localeCompare(String(a.lastPlayed || "")) || byName(a, b),
  time: (a, b) => (b.playtime?.seconds || 0) - (a.playtime?.seconds || 0) || byName(a, b),
  platform: (a, b) => (a.platform || "").localeCompare(b.platform || "", "pt-BR") || byName(a, b),
};
export const currentOrder = () => state.order || (state.quick === "ranking" ? "nota" : "name");

// Coleções antigas viram filtros da Biblioteca (load("favorites"), #/neste-pc, #/roms-leves/FC…).
export function normalizeView(kind, code, view) {
  const quick = {local: "local", favorites: "favorites", playing: "playing", ranking: "ranking"}[kind];
  if (quick) return {kind: "library", code: "", view: {...view, quick}};
  if (kind === "heavy" || kind === "light") return {kind: "library", code: "", view: {...view, system: code}};
  if (kind === "systems" || kind === "search") return {kind: "library", code: "", view: view || (kind === "search" ? {query: state.query} : {})};
  return {kind, code, view};
}
// Estado de filtros da Biblioteca como objeto (endereço, recarregar, voltar).
export const viewOf = () => ({quick: state.quick, filter: state.filter, genre: state.genre, order: state.order, installed: state.installedOnly});

export function visibleItems() {
  const quick = QUICK.find(q => q[0] === state.quick)?.[2] || (() => true), q = norm(state.query);
  const items = state.items.filter(g => quick(g) && (!state.filter || g.platform === state.filter) && (!state.genre || g.tracking.genero === state.genre)
    && (!q || norm(g.name).includes(q)) && (!state.installedOnly || g.local));
  return items.sort(SORTERS[currentOrder()] || byName);
}
export function libraryStats(items) {
  const rated = items.filter(g => g.tracking.nota != null);
  return {total: items.length, playing: items.filter(QUICK[1][2]).length, finished: items.filter(QUICK[5][2]).length, local: items.filter(g => g.local).length,
    platinum: items.filter(g => g.tracking.platinado).length, average: rated.length ? rated.reduce((n, g) => n + g.tracking.nota, 0) / rated.length : null};
}
export function statsLine(items) {
  const s = libraryStats(items), n = v => v.toLocaleString("pt-BR");
  return [`${n(s.total)} jogos`, `${n(s.playing)} jogando`, `${n(s.finished)} finalizados`, `${n(s.platinum)} platinados`, `${n(s.local)} neste PC`,
    s.average == null ? "" : `nota média ${s.average.toFixed(2).replace(".", ",")}`].filter(Boolean).join(" · ");
}

// Filtros rápidos (LB/RB no controle) e ordem como botões. `changed` redesenha a seleção.
export function quickTabs(changed) {
  const nav = $("quick"); nav.replaceChildren();
  const all = state.items;
  for (const [id, label, test] of QUICK) {
    const b = button(`${label} (${id === "all" ? all.length : all.filter(test).length})`, () => { state.quick = id; changed(); $("quick").querySelector('[aria-pressed="true"]')?.focus(); }, state.quick === id);
    b.dataset.quick = id; nav.append(b);
  }
}
export function cycleQuick(delta) {
  const index = Math.max(0, QUICK.findIndex(q => q[0] === state.quick));
  state.quick = QUICK[(index + delta + QUICK.length) % QUICK.length][0];
  return state.quick;
}

// Pulo por inicial: vale na ordem por nome; leva ao primeiro jogo da próxima letra (ou à anterior).
export const initialOf = name => { const c = norm(name).trim()[0] || "#"; return /[a-z]/.test(c) ? c.toUpperCase() : "#"; };
export function letterJump(direction) {
  if (state.kind !== "library") return false;
  if (currentOrder() !== "name") { report("O pulo por letra vale na ordem por nome.", false); return false; }
  const cards = [...$("gallery").querySelectorAll(".game")].filter(c => cardGames.get(c));
  const current = cards.indexOf(document.activeElement.closest?.(".game") || document.activeElement);
  if (!cards.length) return false;
  const letters = cards.map(c => initialOf(cardGames.get(c).name));
  const from = current < 0 ? 0 : current;
  let target;
  if (direction > 0) target = letters.findIndex((l, i) => i > from && l !== letters[from]);
  else {
    const start = letters.indexOf(letters[from]);                 // primeira capa da letra atual
    target = from > start ? start : start > 0 ? letters.indexOf(letters[start - 1]) : 0;
  }
  if (target < 0) target = direction > 0 ? cards.length - 1 : 0;
  cards[target].focus({preventScroll: true}); cards[target].scrollIntoView({block: "center"});
  report(`Letra ${letters[target]} · ${cards.length} jogos nesta seleção`);
  return true;
}

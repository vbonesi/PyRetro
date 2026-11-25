import {api} from "./api.js";
import {gameCard} from "./cards.js";
import {$, button, formatHours, report} from "./dom.js";
import {openGame} from "./game.js";
import {renderHome} from "./home.js";
import {glifos} from "./input.js";
import {applyPreferences} from "./settings.js";
import {WISHLIST_STORES, collections, state} from "./state.js";
import {destinationOf, inSidebar, renderSidebar} from "./sidebar.js";
import {renderTools} from "./tools.js";
import {routeFor, replaceView, syncRoute} from "./router.js";
import {modalOpen, pageOpen} from "./pages.js";
import {currentOrder, norm, normalizeView, orderTabs, quickTabs, statsLine, viewOf, visibleItems} from "./library.js";
// Filtros secundários (plataforma e gênero) recolhíveis: mais área para os jogos.
let filtrosRecolhidos = true;
try { filtrosRecolhidos = localStorage.getItem("pyretro-filtros") !== "aberto"; } catch (_) {}
export function updateFilters() {
  const toggle = $("filters-toggle"), available = ["library", "wishlist"].includes(state.kind);
  const active = (state.filter ? 1 : 0) + (state.genre ? 1 : 0) + (state.order ? 1 : 0) + (state.installedOnly ? 1 : 0);
  toggle.hidden = !available;
  toggle.textContent = `Filtros${active ? ` (${active})` : ""} ${filtrosRecolhidos ? "▾" : "▴"}`;
  toggle.setAttribute("aria-expanded", String(!filtrosRecolhidos));
  document.body.classList.toggle("filters-collapsed", available && filtrosRecolhidos);
}
function drawTabs() {
  const nav = $("platforms"), genres = $("genres"); nav.replaceChildren(); genres.replaceChildren();
  if (state.kind !== "draw" || !state.sortear) { genres.hidden = true; return; }
  const groups = [{code: "", label: "🎲 Tudo"}, ...state.sortear.grupos];
  for (const g of groups) nav.append(button(g.label, () => { state.draw.group = g.code; drawTabs(); nav.querySelector(`[aria-pressed="true"]`)?.focus(); }, state.draw.group === g.code));
  genres.hidden = false;
  for (const name of ["", ...state.sortear.generos]) genres.append(button(name || "Qualquer gênero", () => { state.draw.genre = name; drawTabs(); genres.querySelector(`[aria-pressed="true"]`)?.focus(); }, state.draw.genre === name));
}
// Um filtro da Biblioteca mudou: redesenha as fileiras de filtros e a seleção, e atualiza o endereço sem empilhar histórico.
export function filtersChanged() {
  platformTabs(); render();
  if (state.kind === "library") replaceView(routeFor("library", "", state.query, viewOf()));
}
function platformTabs() {
  drawTabs(); updateFilters();
  const nav = $("platforms"), genres = $("genres"), library = state.kind === "library";
  $("quick").hidden = !library; $("orders").hidden = !library;
  if (library) { quickTabs(filtersChanged); orderTabs(filtersChanged); } else { $("quick").replaceChildren(); $("orders").replaceChildren(); }
  if (state.kind === "draw") return; nav.replaceChildren();
  const names = [...new Set(state.items.map(g => g.tracking?.genero).filter(Boolean))].sort();
  if (["library", "wishlist"].includes(state.kind) && names.length) {
    genres.hidden = false;
    for (const name of ["", ...names]) genres.append(button(name || "Qualquer gênero", () => {
      state.genre = name; filtersChanged(); genres.querySelector('[aria-pressed="true"]')?.focus();
    }, (state.genre || "") === name));
  }
  if (["library", "wishlist"].includes(state.kind)) {
    const platforms = [...new Set(state.items.map(g => g.platform))].sort();
    for (const p of ["", ...platforms]) {
      const tab = button(p || "Todos os sistemas", () => {
        state.filter = p; filtersChanged(); nav.querySelector(`[aria-pressed="true"]`)?.focus();
      }, state.filter === p);
      if (p) tab.prepend(plataformaIcone(plataformaInfo(p)));
      nav.append(tab);
    }
  }
}
export function collectionTabs() { renderSidebar(); }
// Resolve a chave da rota de uma ficha (#/jogo/<chave>) em qualquer coleção: chave do catálogo da TV, `pc:<id>` da
// Biblioteca (primeiro o item do catálogo com esse id, depois a Biblioteca e os Desejados) ou `<sistema>:<ROM>`.
export async function findGameByKey(key) {
  const catalog = await api("/api/tv/catalog");
  const found = catalog.find(g => g.key === key || (g.code && (`${g.code}:${g.romName}` === key || `${g.code}:${g.name}` === key)));
  if (found) return found;
  const id = /^pc:(.+)$/.exec(key)?.[1];
  if (!id) return null;
  const owned = catalog.find(g => g.id === id);
  if (owned) return owned;
  const book = (await api("/api/library")).find(g => g.id === id);
  if (book) return libraryItem(book);
  const lists = await api("/api/wishlist");
  for (const [source, label] of Object.entries(WISHLIST_STORES)) {
    const entry = (lists[source] || []).find(g => g.id === id);
    if (entry) return {...libraryItem(entry), platform: label, wishlist: source};
  }
  return null;
}
function libraryItem(g) {
  const item = {id: g.id, name: g.nome, platform: g.plataforma || "Biblioteca", cover: g.capa_url, tracking: g};
  if (g.rom_code) { item.code = g.rom_code; item.romName = g.nome; }
  return item;
}
function romItem(kind, c, sys, g) {
  return {
    name: kind === "heavy" ? g.label : (g.display_name || g.label), code: c,
    platform: sys.nome || sys.capas || c, cover: kind === "heavy" ? g.capa : (g.file ? `/images/${encodeURIComponent(c)}/${encodeURIComponent(g.file)}` : null),
    tracking: g.biblioteca || {}, downloadName: kind === "heavy" && !g.in_pc && g.in_drive ? g.name : null,
    local: kind === "heavy" ? g.in_pc : null,
    romName: kind === "heavy" ? g.name : g.label, driveName: kind === "heavy" && g.in_drive ? g.name : null,
  };
}
export async function load(kind = state.kind, code = "", view) {
  ({kind, code, view} = normalizeView(kind, code, view));
  const request = ++state.request;
  if (/^(Sessão encerrada|O emulador encerrou)/.test($("play-status").textContent)) report("", false, "play-status");
  if (view?.query !== undefined) state.query = view.query; else if (kind !== state.kind) state.query = "";
  state.kind = kind; state.code = code; state.quick = view?.quick || "all"; state.filter = view?.filter || ""; state.genre = view?.genre || "";
  state.order = view?.order || ""; state.system = view?.system || "";
  if (view && view.installed !== undefined) state.installedOnly = !!view.installed;
  syncRoute(routeFor(kind, state.code, state.query, viewOf()));
  state.items = []; collectionTabs(); platformTabs(); render();
  $("title").textContent = collections.find(x => x[0] === kind)?.[1] || "Biblioteca";
  $("installed-only").hidden = kind !== "library";
  for (const id of ["wishlist-add-psn", "wishlist-add-xbox", "wishlist-add-switch", "wishlist-add-switch2", "wishlist-steam"]) { $(id).hidden = kind !== "wishlist"; $(id).dataset.confirm = ""; }
  $("stats-open").hidden = kind !== "library"; $("draw-open").hidden = kind !== "library";
  $("wishlist-steam").textContent = "🔄 Steam";
  report("Carregando catálogo…");
  try {
    let items;
    if (kind === "home") {
      const home = await api("/api/tv/home");
      if (request !== state.request) return;
      state.home = home; applyPreferences(home.preferences || state.preferences); items = [];
    } else if (kind === "library") {
      // Um só catálogo: PC, ROMs leves e pesadas e Switch, cada jogo uma vez (a chave do catálogo é a chave canônica das rotas).
      items = await api("/api/tv/catalog");
      if (state.system && !state.filter) state.filter = items.find(g => g.code === state.system)?.platform || "";
    } else if (kind === "apps") {
      items = await api("/api/tv/apps");
    } else if (kind === "wishlist") {
      // Desejados: as lojas juntas; a loja vira a "plataforma" para filtrar.
      const lists = await api("/api/wishlist");
      items = Object.entries(WISHLIST_STORES).flatMap(([source, label]) => (lists[source] || []).map(g => ({...libraryItem(g), platform: label, wishlist: source})))
        .sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));
    } else if (kind === "stats") {
      const [stats, library, wishlist] = await Promise.all([api("/api/estatisticas"), api("/api/library"), api("/api/wishlist")]);
      if (request !== state.request) return;
      state.stats = {...stats, library: library.filter(g => !g.oculto), desejados: Object.values(wishlist).reduce((n, list) => n + list.length, 0)}; items = [];
    } else if (kind === "draw") {
      if (!state.sortear) state.sortear = await api("/api/sortear/systems");
      items = [];
    } else items = [];
    if (request !== state.request) return;
    state.items = items; platformTabs(); render();
    if (kind === "library") replaceView(routeFor("library", "", state.query, viewOf()));
    // Quem escolheu o destino pela barra continua nela (→ entra no conteúdo); de fora (voltar, recarga) o foco vai ao conteúdo.
    const fromSidebar = inSidebar();
    if (kind === "home") { if (!fromSidebar) ($("spotlight").hidden ? $("home").querySelector("button") : $("spotlight-open"))?.focus({preventScroll: true}); window.scrollTo(0, 0); }
    else if (!fromSidebar) (kind === "library" ? $("quick").querySelector('[aria-pressed="true"]') : $("gallery").querySelector("button"))?.focus();
  } catch (error) { if (request === state.request) report(`Não foi possível carregar: ${error.message}. Selecione o destino para tentar novamente.`, true); }
}
export function render() {
  const home = state.kind === "home";
  document.body.classList.toggle("home-screen", home);
  $("home").hidden = !home; $("gallery").hidden = home; $("spotlight").hidden = !home;
  if (!home) $("spotlight-video").pause();
  $("search-summary").textContent = state.query ? `Busca: ${state.query}` : "";
  $("installed-only").setAttribute("aria-pressed", String(state.installedOnly));
  $("library-stats").hidden = true;
  if (home) return renderHome();
  if (state.kind === "apps") return renderApps();
  if (state.kind === "stats") return renderStats();
  if (state.kind === "tools") return renderTools();
  const library = state.kind === "library";
  const items = library ? visibleItems() : state.items.filter(g => (!state.filter || g.platform === state.filter) && (!state.genre || g.tracking.genero === state.genre)
    && (!state.query || norm(g.name).includes(norm(state.query))) && (!state.installedOnly || state.kind === "draw"));
  const gallery = $("gallery"); gallery.replaceChildren();
  if (state.kind === "draw") gallery.append(drawPanel(items.length > 0));
  if (library) { $("library-stats").hidden = false; $("library-stats").textContent = statsLine(state.items); }
  if (library && state.quick === "ranking" && currentOrder() === "nota" && items.length) {
    gallery.append(podium(items));
    for (const g of items.slice(3)) gallery.append(gameCard(g));
  } else for (const g of items) gallery.append(gameCard(g));
  if (state.kind === "draw") return report(items.length ? "Sorteado! Escolha jogar, transmitir ou ver o progresso nos detalhes." : "Escolha grupo e gênero, depois sorteie.");
  report(items.length ? `${items.length} jogos · escolha uma capa` : state.quick === "favorites" ? `Escolha um jogo e pressione ${glifos().X} para guardar nos favoritos.` : "Nenhum jogo nesta seleção.");
}
// Top 3 da seleção atual (depois de filtro e busca); 2-1-3 em tela larga, 1-2-3 em retrato (CSS).
function podium(ranked) {
  const section = document.createElement("section"); section.className = "podium"; section.setAttribute("aria-label", "Top 3 desta seleção");
  const title = document.createElement("h3"); title.textContent = "Top 3 desta seleção";
  const row = document.createElement("div"); row.className = "podium-row";
  ranked.slice(0, 3).forEach((g, i) => { const card = gameCard(g); card.classList.add("podium-place", `place-${i + 1}`); card.dataset.place = String(i + 1); row.append(card); });
  section.append(title, row);
  const last = ranked[2]?.tracking.nota, tied = ranked.filter(g => g.tracking.nota === last).length;
  if (ranked.length > 3 && tied > 1 && ranked[3].tracking.nota === last) {
    const note = document.createElement("p"); note.className = "podium-note";
    note.textContent = `Empate na nota ${String(last).replace(".", ",")}: a ordem entre empatados é alfabética, não de preferência.`;
    section.append(note);
  }
  return section;
}
function drawPanel(hasResult) {
  const group = state.sortear?.grupos.find(g => g.code === state.draw.group)?.label || "Tudo";
  const panel = document.createElement("section"); panel.className = "draw-panel"; panel.setAttribute("aria-label", "Sortear jogo");
  const summary = document.createElement("p"); summary.className = "draw-summary";
  summary.textContent = `${group} · ${state.draw.genre || "Qualquer gênero"}`;
  const go = Object.assign(button(hasResult ? "🎲 Sortear novamente" : "🎲 Sortear jogo", drawGame), {className: "draw primary"});
  panel.append(summary, go); return panel;
}
function renderApps() {
  $("gallery").replaceChildren(...state.items.map(g => {
    const card = button(`${g.icon} ${g.name}`, () => launchApp(g)); card.className = "game system-card"; return card;
  }));
  report("Escolha um aplicativo para abrir.");
}
// Estatísticas: os números da web em cartões; cada um leva à coleção que explica o número.
function renderStats() {
  const s = state.stats, gallery = $("gallery"); gallery.replaceChildren();
  if (!s) return;
  const tile = (symbol, value, label, go) => {
    const card = button("", go); card.className = "game system-card stat-card";
    const big = document.createElement("span"); big.className = "system-symbol"; big.textContent = symbol;
    const name = document.createElement("strong"); name.textContent = value;
    const hint = document.createElement("small"); hint.textContent = label;
    card.append(big, name, hint); return card;
  };
  const byLibrary = (field, value) => async () => { await load("library", "", {[field]: value}); $("gallery").querySelector("button")?.focus(); };
  gallery.append(
    tile("🎮", s.total.toLocaleString("pt-BR"), "jogos na Biblioteca", () => load("library")),
    tile("▶", s.jogando, "jogando agora", () => load("playing")),
    tile("✓", s.zerados, "finalizados", () => load("library", "", {quick: "finished"})),
    tile("🏆", s.platinados, "platinados", () => load("library", "", {quick: "finished"})),
    tile("★", s.nota_media == null ? "—" : s.nota_media.toFixed(2).replace(".", ","), `nota média · ${s.com_nota} com nota`, () => load("ranking")),
    tile("⏱", formatHours(s.tempo_total_horas), "de jogo registrado", () => load("library", "", {order: "time"})),
    tile("♡", s.desejados, "nos Desejados", () => load("wishlist")));
  const top = (field, title, filter) => {
    const counts = new Map(); for (const g of s.library) if (g[field]) counts.set(g[field], (counts.get(g[field]) || 0) + 1);
    const heading = document.createElement("h3"); heading.className = "stats-heading"; heading.textContent = title; gallery.append(heading);
    for (const [name, n] of [...counts].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "pt-BR")).slice(0, 8))
      gallery.append(tile(n, name, `${n} jogos`, byLibrary(filter, name)));
  };
  top("plataforma", "Por plataforma", "filter"); top("genero", "Por gênero", "genre");
  report(`${s.total} jogos · ${s.com_genero} com gênero · escolha um cartão para ver a lista`);
}
export async function launchApp(app, target = "play-status") {
  if (state.busy) return; state.busy = true;
  try {
    const result = await api("/api/tv/apps/launch", {id: app.id});
    const message = result.already_running ? `${app.name} já está aberto. Volte à janela existente para continuar.` : app.id === "sysdvr" ? "Switch Lite: abrindo transmissão. Ative TCP Bridge no SysDVR do console e use os controles do Switch para jogar." : `${app.name}: abertura solicitada.`;
    report(message, false, "play-status");
    if (target !== "play-status") report(message, false, target);
  }
  catch (e) { report(e.message, true, "play-status"); if (target !== "play-status") report(e.message, true, target); }
  finally { state.busy = false; }
}
export async function reloadSelection(origin) {
  const {kind, code, filter, genre, quick, order} = state;
  await load(kind, code, kind === "library" ? {quick, filter, genre, order} : undefined);
  if (state.kind !== kind) return;
  if (kind !== "library") { state.filter = filter; state.genre = genre; platformTabs(); render(); }
  origin?.focus();
}
$("installed-only").onclick = () => { state.installedOnly = !state.installedOnly; filtersChanged(); $("installed-only").focus(); };
$("stats-open").onclick = () => load("stats");
$("draw-open").onclick = () => load("draw");
$("refresh").onclick = () => reloadSelection($("refresh"));
export async function drawGame() {
  if (state.busy || state.drawing) return;
  state.drawing = true; report("Sorteando…");
  try {
    const request = state.request;
    const query = new URLSearchParams(); if (state.draw.group) query.set("system", state.draw.group); if (state.draw.genre) query.set("genero", state.draw.genre);
    const r = await api(`/api/sortear?${query}`);
    if (request !== state.request || state.kind !== "draw") return;
    let item;
    if (r.game) item = r.game;
    else if (r.kind === "biblioteca") {
      const g = (await api("/api/library")).find(x => x.nome === r.nome && (!r.plataforma || x.plataforma === r.plataforma));
      if (!g) throw new Error(`"${r.nome}" não foi encontrado na Biblioteca`);
      item = libraryItem(g);
    } else {
      const kind = r.kind === "pesado" ? "heavy" : "light";
      const sys = (kind === "heavy" ? state.systems : state.light).find(s => s.code === r.codigo) || {code: r.codigo};
      const data = await api(kind === "heavy" ? `/api/heavy/roms/${encodeURIComponent(r.codigo)}` : `/api/covers/${encodeURIComponent(r.codigo)}`);
      const stem = r.nome.replace(/\.[^.]+$/, "");
      const g = (kind === "heavy" ? data.items : data).find(x => kind === "heavy" ? x.name === r.nome : x.label === stem || x.label === r.nome);
      if (!g) throw new Error(`"${r.nome}" não foi encontrado em ${r.label}`);
      item = romItem(kind, r.codigo, sys, g);
    }
    if (request !== state.request || state.kind !== "draw") return;
    state.items = [item]; render();
    const card = $("gallery").querySelector(".game");
    card?.focus();
    if (!modalOpen() && !pageOpen()) openGame(item, card);
  } catch (e) { report(`Não foi possível sortear: ${e.message}`, true); }
  finally { state.drawing = false; }
}
$("filters-toggle").onclick = () => {
  filtrosRecolhidos = !filtrosRecolhidos;
  try { localStorage.setItem("pyretro-filtros", filtrosRecolhidos ? "recolhido" : "aberto"); } catch (_) {}
  updateFilters(); if (!filtrosRecolhidos) ($("platforms").querySelector("button") || $("genres").querySelector("button"))?.focus();
};

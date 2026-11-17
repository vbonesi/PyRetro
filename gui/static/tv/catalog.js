import {api} from "./api.js";
import {gameCard} from "./cards.js";
import {$, button, formatHours, report} from "./dom.js";
import {openGame} from "./game.js";
import {renderHome} from "./home.js";
import {glifos} from "./input.js";
import {applyPreferences} from "./settings.js";
import {WISHLIST_STORES, collections, state} from "./state.js";
import {renderTools} from "./tools.js";
import {routeFor, syncRoute} from "./router.js";
// Filtros secundários (plataforma e gênero) recolhíveis: mais área para os jogos.
let filtrosRecolhidos = true;
try { filtrosRecolhidos = localStorage.getItem("pyretro-filtros") !== "aberto"; } catch (_) {}
export function updateFilters() {
  const toggle = $("filters-toggle"), available = !["home", "systems", "apps", "stats", "tools", "draw"].includes(state.kind);
  const active = (state.filter ? 1 : 0) + (state.genre ? 1 : 0);
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
function platformTabs() {
  drawTabs(); updateFilters();
  const nav = $("platforms"); if (state.kind === "draw") return; nav.replaceChildren();
  const genres = $("genres");
  const names = [...new Set(state.items.map(g => g.tracking?.genero).filter(Boolean))].sort();
  if (!["home", "systems", "apps", "stats", "tools"].includes(state.kind) && names.length) {
    genres.hidden = false;
    for (const name of ["", ...names]) genres.append(button(name || "Qualquer gênero", () => {
      state.genre = name; platformTabs(); render(); genres.querySelector('[aria-pressed="true"]')?.focus();
    }, (state.genre || "") === name));
  }
  if (["library", "playing", "ranking", "wishlist", "local", "search", "favorites"].includes(state.kind)) {
    const platforms = [...new Set(state.items.map(g => g.platform))].sort();
    for (const p of ["", ...platforms]) {
      const tab = button(p || "Todas as plataformas", () => {
        state.filter = p; platformTabs(); render(); nav.querySelector(`[aria-pressed="true"]`)?.focus();
      }, state.filter === p);
      if (p) tab.prepend(plataformaIcone(plataformaInfo(p)));
      nav.append(tab);
    }
  } else if (["heavy", "light"].includes(state.kind)) {
    const systems = state.kind === "heavy" ? state.systems : state.light;
    for (const s of systems) nav.append(button(s.nome || s.code, () => load(state.kind, s.code), state.code === s.code));
  }
}
export function collectionTabs() {
  $("collections").replaceChildren(...collections.map(([kind, title]) => button(title, () => load(kind), state.kind === kind)));
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
export async function load(kind = state.kind, code = "") {
  const request = ++state.request;
  if (/^(Sessão encerrada|O emulador encerrou)/.test($("play-status").textContent)) report("", false, "play-status");
  if (kind !== state.kind && kind !== "search") state.query = "";
  state.kind = kind; state.filter = ""; state.genre = "";
  const systems = kind === "heavy" ? state.systems : state.light;
  state.code = code || systems[0]?.code || "";
  syncRoute(routeFor(kind, state.code, state.query));
  state.items = []; collectionTabs(); platformTabs(); render();
  $("title").textContent = collections.find(x => x[0] === kind)?.[1] || "Pesquisa";
  $("installed-only").hidden = ["home", "systems", "apps", "draw", "local", "wishlist", "stats", "tools"].includes(kind);
  for (const id of ["wishlist-add-psn", "wishlist-add-xbox", "wishlist-steam"]) { $(id).hidden = kind !== "wishlist"; $(id).dataset.confirm = ""; }
  $("wishlist-steam").textContent = "🔄 Steam";
  report("Carregando catálogo…");
  try {
    let items;
    if (kind === "home") {
      const home = await api("/api/tv/home");
      if (request !== state.request) return;
      state.home = home; applyPreferences(home.preferences || state.preferences); items = [];
    } else if (["systems", "search", "favorites"].includes(kind)) {
      items = await api("/api/tv/catalog");
      if (kind === "favorites") items = items.filter(g => g.favorite);
    } else if (kind === "local") {
      items = await api("/api/tv/local");
    } else if (kind === "apps") {
      items = await api("/api/tv/apps");
    } else if (kind === "library" || kind === "playing" || kind === "ranking") {
      // Ranking: só quem tem nota, maior primeiro (mesma ordem da web).
      items = (await api(kind === "library" ? "/api/library" : kind === "ranking" ? "/api/ranking" : "/api/iniciados")).filter(g => !g.oculto).map(libraryItem);
      if (state.installedOnly) {
        const local = await api("/api/tv/local");
        for (const g of items) g.local = local.some(x => x.id && x.id === g.id || x.code && x.code === g.code && x.romName === g.romName);
      }
    } else if (kind === "wishlist") {
      // Desejados: as três lojas juntas; a loja vira a "plataforma" para filtrar.
      const lists = await api("/api/wishlist");
      items = Object.entries(WISHLIST_STORES).flatMap(([source, label]) => (lists[source] || []).map(g => ({...libraryItem(g), platform: label, wishlist: source})))
        .sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));
    } else if (kind === "stats") {
      const [stats, library, wishlist] = await Promise.all([api("/api/estatisticas"), api("/api/library"), api("/api/wishlist")]);
      if (request !== state.request) return;
      state.stats = {...stats, library: library.filter(g => !g.oculto), desejados: Object.values(wishlist).reduce((n, list) => n + list.length, 0)}; items = [];
    } else if (kind === "tools") {
      items = [];
    } else if (kind === "draw") {
      if (!state.sortear) state.sortear = await api("/api/sortear/systems");
      items = [];
    } else {
      if (!state.code) { report("Nenhum sistema configurado."); return; }
      const c = state.code;
      if (kind === "light") {
        // Sistemas leves: o catálogo junta o que está no PC e o que está no Drive (baixável sob demanda).
        items = (await api("/api/tv/catalog")).filter(g => g.code === c);
      } else {
        const data = await api(`/api/heavy/roms/${encodeURIComponent(c)}`);
        const sys = systems.find(s => s.code === c);
        items = data.items.map(g => romItem(kind, c, sys, g));
      }
    }
    if (["library", "playing", "heavy", "light"].includes(kind)) {
      const metadata = await api("/api/tv/catalog");
      const byId = new Map(metadata.filter(g => g.id).map(g => [`${g.code || ""}:${g.id}`, g]));
      const byRom = new Map(metadata.filter(g => g.code).flatMap(g => [[`${g.code}:${g.romName}`, g], [`${g.code}:${g.name}`, g]]));
      for (const g of items) {
        const matched = (g.id && byId.get(`${g.code || ""}:${g.id}`)) || byRom.get(`${g.code}:${g.romName}`) || byRom.get(`${g.code}:${g.name}`);
        if (matched) Object.assign(g, {key: matched.key, favorite: matched.favorite, lastPlayed: matched.lastPlayed, local: matched.local, playtime:matched.playtime, media:matched.media});
      }
    }
    if (state.installedOnly && ["heavy", "light"].includes(kind)) {
      const local = await api("/api/tv/local");
      for (const g of items) g.local = local.some(x => x.code === g.code && (x.romName === g.romName || x.romName === g.romName.replace(/\.[^.]+$/, "")));
    }
    if (request !== state.request) return;
    state.items = items; platformTabs(); render();
    if (kind === "home") { ($("spotlight").hidden ? $("home").querySelector("button") : $("spotlight-open"))?.focus({preventScroll: true}); window.scrollTo(0, 0); }
    else (code ? $("platforms") : $("collections")).querySelector('[aria-pressed="true"]')?.focus();
  } catch (error) { if (request === state.request) report(`Não foi possível carregar: ${error.message}. Selecione a coleção para tentar novamente.`, true); }
}
export function render() {
  const home = state.kind === "home";
  document.body.classList.toggle("home-screen", home);
  $("home").hidden = !home; $("gallery").hidden = home; $("spotlight").hidden = !home;
  if (!home) $("spotlight-video").pause();
  $("search-summary").textContent = state.query ? `Busca: ${state.query}` : "";
  $("installed-only").setAttribute("aria-pressed", String(state.installedOnly));
  if (home) return renderHome();
  if (state.kind === "systems") return renderSystems();
  if (state.kind === "apps") return renderApps();
  if (state.kind === "stats") return renderStats();
  if (state.kind === "tools") return renderTools();
  const norm = s => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  const items = state.items.filter(g => (!state.filter || g.platform === state.filter) && (!state.genre || g.tracking.genero === state.genre) && (!state.query || norm(g.name).includes(norm(state.query))) && (!state.installedOnly || ["local", "draw"].includes(state.kind) || g.local) && (state.kind !== "playing" || (g.tracking.iniciado && !g.tracking.finalizado)));
  const gallery = $("gallery"); gallery.replaceChildren();
  if (state.kind === "draw") gallery.append(drawPanel(items.length > 0));
  if (state.kind === "ranking" && items.length) {
    const ranked = [...items].sort((a, b) => (b.tracking.nota ?? -1) - (a.tracking.nota ?? -1) || norm(a.name).localeCompare(norm(b.name), "pt-BR") || (a.platform || "").localeCompare(b.platform || "", "pt-BR") || String(a.id ?? a.key ?? "").localeCompare(String(b.id ?? b.key ?? "")));
    gallery.append(podium(ranked));
    for (const g of ranked.slice(3)) gallery.append(gameCard(g));
  } else for (const g of items) gallery.append(gameCard(g));
  if (state.kind === "draw") return report(items.length ? "Sorteado! Escolha jogar, transmitir ou ver o progresso nos detalhes." : "Escolha grupo e gênero, depois sorteie.");
  report(items.length ? `${items.length} jogos · escolha uma capa` : state.kind === "favorites" ? `Escolha um jogo e pressione ${glifos().X} para guardar nos favoritos.` : "Nenhum jogo nesta seleção.");
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
function renderSystems() {
  const groups = new Map();
  for (const g of state.items) {
    const key = g.code || g.platform;
    if (!groups.has(key)) groups.set(key, {name: g.platform, code: g.code, total: 0, local: 0});
    const group = groups.get(key); group.total++; if (g.local) group.local++;
  }
  const gallery = $("gallery"); gallery.replaceChildren();
  for (const [key, g] of [...groups].sort((a, b) => a[1].name.localeCompare(b[1].name, "pt-BR"))) {
    const card = button("", async () => {
      state.query = "";
      if (g.code) await load(state.systems.some(s => s.code === g.code) ? "heavy" : "light", g.code);
      else { await load("library"); state.filter = key; platformTabs(); render(); }
      $("gallery").querySelector("button")?.focus();
    });
    card.className = "game system-card";
    const symbol = document.createElement("span"); symbol.className = "system-symbol";
    symbol.append(plataformaIcone(plataformaInfo(g.code, g.name)));
    const name = document.createElement("strong"); name.textContent = g.name;
    const count = document.createElement("small"); count.textContent = `${g.total} jogos · ${g.local} neste PC`;
    card.append(symbol, name, count); gallery.append(card);
  }
  report(`${groups.size} sistemas e plataformas · escolha por onde jogar`);
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
  const byLibrary = (field, value) => async () => { await load("library"); state[field] = value; platformTabs(); render(); $("gallery").querySelector("button")?.focus(); };
  gallery.append(
    tile("🎮", s.total.toLocaleString("pt-BR"), "jogos na Biblioteca", () => load("library")),
    tile("▶", s.jogando, "jogando agora", () => load("playing")),
    tile("✓", s.zerados, "finalizados", () => load("library")),
    tile("🏆", s.platinados, "platinados", () => load("library")),
    tile("★", s.nota_media == null ? "—" : s.nota_media.toFixed(2).replace(".", ","), `nota média · ${s.com_nota} com nota`, () => load("ranking")),
    tile("⏱", formatHours(s.tempo_total_horas), "de jogo registrado", () => load("library")),
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
  const {kind, code, filter, genre} = state;
  await load(kind, code);
  if (state.kind !== kind || state.code !== code) return;
  state.filter = filter; state.genre = genre; platformTabs(); render();
  origin?.focus();
}
$("installed-only").onclick = () => { state.installedOnly = !state.installedOnly; reloadSelection($("installed-only")); };
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
    if (!document.querySelector('dialog[open]')) openGame(item, card);
  } catch (e) { report(`Não foi possível sortear: ${e.message}`, true); }
  finally { state.drawing = false; }
}
$("filters-toggle").onclick = () => {
  filtrosRecolhidos = !filtrosRecolhidos;
  try { localStorage.setItem("pyretro-filtros", filtrosRecolhidos ? "recolhido" : "aberto"); } catch (_) {}
  updateFilters(); if (!filtrosRecolhidos) ($("platforms").querySelector("button") || $("genres").querySelector("button"))?.focus();
};

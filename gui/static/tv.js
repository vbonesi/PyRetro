/* Modo TV: cliente das mesmas APIs da GUI, sem acesso direto ao acervo. */
"use strict";
const $ = id => document.getElementById(id);
if (window.ResizeObserver) new ResizeObserver(entries => {
  document.documentElement.style.setProperty("--footer-height", `${entries[0].target.getBoundingClientRect().height}px`);
}).observe(document.querySelector("footer"));
let csrf;
async function api(url, body) {
  const options = body === undefined ? {} : {method: "POST", headers: {
    "Content-Type": "application/json", "X-PyRetro-CSRF": csrf || (csrf = (await api("/api/csrf")).token),
  }, body: JSON.stringify(body)};
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}
const state = {query: "", installedOnly: false, draw: {group: "", genre: ""}, sortear: null, kind: "home", code: "", filter: "", items: [], systems: [], light: [], request: 0, selected: null, draft: null, busy: false, download: null, preferences: {favorites: [], theme: "dark"}, home: null};
const collections = [["home", "Início"], ["local", "Neste PC"], ["favorites", "Favoritos"], ["systems", "Sistemas"], ["library", "Biblioteca"], ["playing", "Jogando"], ["heavy", "ROMs pesadas"], ["light", "ROMs leves"], ["draw", "🎲 Sortear"], ["apps", "Apps"]];
const cardGames = new WeakMap();
let spotlightGame, settingsReturnFocus;
function button(text, action, pressed) {
  const b = document.createElement("button"); b.textContent = text; b.type = "button";
  if (pressed !== undefined) b.setAttribute("aria-pressed", String(pressed));
  b.addEventListener("click", action); return b;
}
function report(message, error = false, target = "message") {
  $(target).textContent = message; $(target).classList.toggle("error", error);
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
  drawTabs();
  const nav = $("platforms"); if (state.kind === "draw") return; nav.replaceChildren();
  const genres = $("genres");
  const names = [...new Set(state.items.map(g => g.tracking?.genero).filter(Boolean))].sort();
  if (!["home", "systems", "apps"].includes(state.kind) && names.length) {
    genres.hidden = false;
    for (const name of ["", ...names]) genres.append(button(name || "Qualquer gênero", () => {
      state.genre = name; platformTabs(); render(); genres.querySelector('[aria-pressed="true"]')?.focus();
    }, (state.genre || "") === name));
  }
  if (["library", "playing", "local", "search", "favorites"].includes(state.kind)) {
    const platforms = [...new Set(state.items.map(g => g.platform))].sort();
    for (const p of ["", ...platforms]) nav.append(button(p || "Todas as plataformas", () => {
      state.filter = p; platformTabs(); render(); nav.querySelector(`[aria-pressed="true"]`)?.focus();
    }, state.filter === p));
  } else if (["heavy", "light"].includes(state.kind)) {
    const systems = state.kind === "heavy" ? state.systems : state.light;
    for (const s of systems) nav.append(button(s.nome || s.code, () => load(state.kind, s.code), state.code === s.code));
  }
}
function collectionTabs() {
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
async function load(kind = state.kind, code = "") {
  const request = ++state.request;
  if (kind !== state.kind && kind !== "search") state.query = "";
  state.kind = kind; state.filter = ""; state.genre = "";
  const systems = kind === "heavy" ? state.systems : state.light;
  state.code = code || systems[0]?.code || "";
  state.items = []; collectionTabs(); platformTabs(); render();
  $("title").textContent = collections.find(x => x[0] === kind)?.[1] || "Pesquisa";
  $("installed-only").hidden = ["home", "systems", "apps", "draw", "local"].includes(kind);
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
    } else if (kind === "library" || kind === "playing") {
      items = (await api(kind === "library" ? "/api/library" : "/api/iniciados")).filter(g => !g.oculto).map(libraryItem);
      if (state.installedOnly) {
        const local = await api("/api/tv/local");
        for (const g of items) g.local = local.some(x => x.id && x.id === g.id || x.code && x.code === g.code && x.romName === g.romName);
      }
    } else if (kind === "draw") {
      if (!state.sortear) state.sortear = await api("/api/sortear/systems");
      items = [];
    } else {
      if (!state.code) { report("Nenhum sistema configurado."); return; }
      const c = state.code;
      const data = await api(kind === "heavy" ? `/api/heavy/roms/${encodeURIComponent(c)}` : `/api/covers/${encodeURIComponent(c)}`);
      const sys = systems.find(s => s.code === c);
      items = (kind === "heavy" ? data.items : data).map(g => romItem(kind, c, sys, g));
    }
    if (["library", "playing", "heavy", "light"].includes(kind)) {
      const metadata = await api("/api/tv/catalog");
      const byId = new Map(metadata.filter(g => g.id).map(g => [`${g.code || ""}:${g.id}`, g]));
      const byRom = new Map(metadata.filter(g => g.code).flatMap(g => [[`${g.code}:${g.romName}`, g], [`${g.code}:${g.name}`, g]]));
      for (const g of items) {
        const matched = (g.id && byId.get(`${g.code || ""}:${g.id}`)) || byRom.get(`${g.code}:${g.romName}`) || byRom.get(`${g.code}:${g.name}`);
        if (matched) Object.assign(g, {key: matched.key, favorite: matched.favorite, lastPlayed: matched.lastPlayed, local: matched.local});
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
function render() {
  const home = state.kind === "home";
  document.body.classList.toggle("home-screen", home);
  $("home").hidden = !home; $("gallery").hidden = home; $("spotlight").hidden = !home;
  $("search-summary").textContent = state.query ? `Busca: ${state.query}` : "";
  $("installed-only").setAttribute("aria-pressed", String(state.installedOnly));
  if (home) return renderHome();
  if (state.kind === "systems") return renderSystems();
  if (state.kind === "apps") return renderApps();
  const norm = s => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  const items = state.items.filter(g => (!state.filter || g.platform === state.filter) && (!state.genre || g.tracking.genero === state.genre) && (!state.query || norm(g.name).includes(norm(state.query))) && (!state.installedOnly || ["local", "draw"].includes(state.kind) || g.local) && (state.kind !== "playing" || (g.tracking.iniciado && !g.tracking.finalizado)));
  const gallery = $("gallery"); gallery.replaceChildren();
  if (state.kind === "draw") gallery.append(Object.assign(button("🎲 Sortear", drawGame), {className: "game draw"}));
  for (const g of items) gallery.append(gameCard(g));
  if (state.kind === "draw") return report(items.length ? "Sorteado! Escolha jogar, transmitir ou ver o progresso nos detalhes." : "Escolha grupo e gênero, depois sorteie.");
  report(items.length ? `${items.length} jogos · escolha uma capa` : state.kind === "favorites" ? "Escolha um jogo e pressione X para guardar nos favoritos." : "Nenhum jogo nesta seleção.");
}
function gameCard(g) {
    const card = button("", () => openGame(g, card)); card.className = "game";
    cardGames.set(card, g); card.dataset.key = g.key || (g.id ? `pc:${g.id}` : `${g.code}:${g.romName}`);
    card.addEventListener("focus", () => { if (state.kind === "home") showSpotlight(g); });
    if (g.cover) { const img = document.createElement("img"); img.src = g.cover; img.alt = ""; img.loading = "lazy"; img.className = "art"; card.append(img); }
    else { const art = document.createElement("div"); art.className = "art placeholder"; art.textContent = "✦"; card.append(art); }
    const title = document.createElement("strong"); title.textContent = (g.favorite ? "★ " : "") + g.name;
    const meta = document.createElement("small"); const t = g.tracking;
    meta.textContent = [g.platform, g.downloadName && !g.local ? "Só no Drive" : g.local ? "No PC" : "", t.platinado ? "🏆 Platinado" : t.finalizado ? "✓ Finalizado" : t.iniciado ? "▶ Iniciado" : "", t.nota != null ? `★ ${t.nota}` : ""].filter(Boolean).join(" · ");
    card.append(title, meta); return card;
}
function showSpotlight(g) {
  spotlightGame = g;
  $("spotlight-title").textContent = g.name;
  $("spotlight-meta").textContent = [g.platform, g.local ? "Pronto neste PC" : g.downloadName ? "Disponível no Drive" : "Na sua biblioteca", g.tracking.genero, g.favorite ? "★ Favorito" : ""].filter(Boolean).join(" · ");
  $("spotlight-art").style.backgroundImage = g.cover ? `url(${JSON.stringify(g.cover)})` : "none";
  $("spotlight-open").textContent = g.local ? "Abrir jogo" : "Ver jogo";
}
$("spotlight-open").onclick = () => { if (spotlightGame) openGame(spotlightGame); };
function renderHome() {
  const box = $("home"); box.replaceChildren();
  const home = state.home; $("spotlight").hidden = !home;
  if (!home) return;
  const quick = document.createElement("section"); quick.className = "quick-access"; quick.setAttribute("aria-label", "Acesso rápido");
  for (const appId of ["greenlight", "chiaki", "sysdvr", "steam", "heroic"]) {
    const app = home.apps?.find(g => g.id === appId);
    if (app) { const b = button(`${app.icon} ${app.name}`, () => launchApp(app)); b.dataset.app = appId; quick.append(b); }
  }
  quick.append(button("🕹 Emuladores", () => load("systems")), button("▦ Todos neste PC", () => load("local")));
  box.append(quick);
  for (const [key, title] of [["recent", "Jogados recentemente"], ["continue", "Continuar jogando"], ["favorites", "Seus favoritos"], ["installed", "Steam e Heroic · prontos para jogar"], ["ready", "Explore seu acervo local"]]) {
    const games = home[key] || []; if (!games.length) continue;
    const section = document.createElement("section"); section.className = "home-section"; section.dataset.shelf = key;
    const heading = document.createElement("h3"); heading.textContent = title;
    const row = document.createElement("div"); row.className = "shelf"; row.setAttribute("aria-label", title);
    for (const game of games) row.append(gameCard(game));
    section.append(heading, row); box.append(section);
  }
  const all = [home.recent, home.continue, home.favorites, home.installed, home.ready].flatMap(g => g || []);
  const featured = all.find(g => spotlightGame?.key && g.key === spotlightGame.key) || all[0];
  $("spotlight").hidden = !featured; if (featured) showSpotlight(featured);
  if (!all.length) { const empty = document.createElement("p"); empty.className = "hint"; empty.textContent = "Sua próxima partida começa aqui. Abra Neste PC ou explore os sistemas. Os jogos que você abrir aparecerão em Recentes; X guarda seus favoritos."; box.append(empty); }
  report(home.counts ? `${home.counts.local || 0} jogos neste PC · ${home.counts.pc || 0} da Steam e Heroic` : "Escolha sua próxima partida.");
}
function applyPreferences(preferences) {
  state.preferences = preferences;
  document.documentElement.dataset.theme = preferences.theme || "dark";
  $("theme-dark").setAttribute("aria-pressed", String(preferences.theme !== "light"));
  $("theme-light").setAttribute("aria-pressed", String(preferences.theme === "light"));
}
function focusedGame() { return $("details").open ? state.selected : cardGames.get(document.activeElement) || (document.activeElement === $("spotlight-open") ? spotlightGame : null); }
function updateFavoriteButton(g) { $("favorite").textContent = g.favorite ? "★ Favorito" : "☆ Favoritar"; $("favorite").setAttribute("aria-pressed", String(!!g.favorite)); }
async function toggleFavorite(g = focusedGame()) {
  if (!g || state.busy) return;
  state.busy = true; const active = document.activeElement; const identity = active.dataset?.key; const shelf = active.closest?.("[data-shelf]")?.dataset.shelf;
  try {
    const preferences = await api("/api/tv/favorite", {key: g.key, id: g.id, code: g.code, name: g.romName, favorite: !g.favorite});
    g.key = preferences.key; g.favorite = !g.favorite; applyPreferences(preferences);
    for (const item of [...state.items, ...["recent", "continue", "favorites", "installed", "ready"].flatMap(k => state.home?.[k] || [])]) if (item.key) item.favorite = preferences.favorites.includes(item.key);
    if (state.home) state.home.favorites = [...state.home.favorites.filter(x => x.key !== g.key), ...(g.favorite ? [g] : [])];
    if (state.kind === "favorites") state.items = state.items.filter(x => x.favorite);
    render(); updateFavoriteButton(g);
    if (!$("details").open) {
      const cards = [...document.querySelectorAll("#home .game,#gallery .game")];
      (cards.find(c => c.dataset.key === (identity || g.key) && c.closest("[data-shelf]")?.dataset.shelf === shelf) || cards.find(c => c.dataset.key === g.key) || cards[0])?.focus();
    }
    report(g.favorite ? "Guardado nos favoritos." : "Removido dos favoritos.", false, $("details").open ? "detail-status" : "message");
  } catch (e) { report(`Não foi possível atualizar favorito: ${e.message}`, true, $("details").open ? "detail-status" : "message"); }
  finally { state.busy = false; }
}
$("favorite").onclick = () => toggleFavorite(state.selected);
function openSettings() {
  if (document.querySelector("dialog[open]")) return;
  settingsReturnFocus = document.activeElement; report("", false, "settings-status");
  $("settings-dialog").showModal(); $(state.preferences.theme === "light" ? "theme-light" : "theme-dark").focus();
}
function closeSettings() { $("settings-dialog").close(); (settingsReturnFocus?.isConnected ? settingsReturnFocus : $("settings-open")).focus(); }
$("settings-open").onclick = openSettings; $("settings-close").onclick = closeSettings;
$("settings-dialog").addEventListener("cancel", e => { e.preventDefault(); closeSettings(); });
$("settings-home").onclick = () => { closeSettings(); load("home"); };
for (const theme of ["dark", "light"]) $(`theme-${theme}`).onclick = async () => {
  if (state.busy) return; state.busy = true;
  try { applyPreferences(await api("/api/tv/preferences", {theme})); report("Tema salvo.", false, "settings-status"); }
  catch (e) { report(e.message, true, "settings-status"); }
  finally { state.busy = false; }
};
$("fullscreen").onclick = async () => { try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); } catch (_) { report("Use o atalho PyRetro do menu para abrir em tela cheia.", false, "settings-status"); } };
function updateClock() { $("clock").textContent = new Date().toLocaleTimeString("pt-BR", {hour: "2-digit", minute: "2-digit"}); }
updateClock(); setInterval(updateClock, 30000);
if (navigator.getBattery) navigator.getBattery().then(battery => {
  const update = () => { $("battery").hidden = false; $("battery").textContent = `${battery.charging ? "⚡" : "▰"} ${Math.round(battery.level * 100)}%`; };
  battery.addEventListener("levelchange", update); battery.addEventListener("chargingchange", update); update();
}).catch(() => {});
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
    symbol.textContent = g.code || ({Steam: "STEAM", GOG: "GOG", "Epic Games Store": "EPIC", "Amazon Games": "AMAZON", Switch: "NSW"})[g.name] || "🎮";
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
async function launchApp(app, target = "play-status") {
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
let searchReturnFocus;
function openSearch() {
  if (document.querySelector("dialog[open]")) return;
  searchReturnFocus = document.activeElement; $("search-input").value = state.query;
  $("search-dialog").showModal(); $("keyboard").querySelector("button")?.focus();
}
function closeSearch() { $("search-dialog").close(); (searchReturnFocus?.isConnected ? searchReturnFocus : $("search-open"))?.focus(); }
async function applySearch() {
  state.query = $("search-input").value.trim(); closeSearch();
  if (["home", "systems", "apps", "draw"].includes(state.kind)) await load("search"); else render();
  $("gallery").querySelector("button")?.focus();
}
for (const character of "1234567890QWERTYUIOPASDFGHJKLÇZXCVBNM -'") $("keyboard").append(button(character === " " ? "␣" : character, () => { const input = $("search-input"); input.value = (input.value + character).slice(0, 120); }));
$("keyboard").append(button("⌫", () => { $("search-input").value = $("search-input").value.slice(0, -1); }));
$("search-open").onclick = openSearch; $("search-close").onclick = closeSearch;
$("search-apply").onclick = applySearch;
$("search-clear").onclick = () => { $("search-input").value = ""; applySearch(); };
$("search-dialog").addEventListener("cancel", e => { e.preventDefault(); closeSearch(); });
$("search-input").addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); applySearch(); } });
async function reloadSelection(origin) {
  const {kind, code, filter, genre} = state;
  await load(kind, code);
  if (state.kind !== kind || state.code !== code) return;
  state.filter = filter; state.genre = genre; platformTabs(); render();
  origin?.focus();
}
$("installed-only").onclick = () => { state.installedOnly = !state.installedOnly; reloadSelection($("installed-only")); };
$("refresh").onclick = () => reloadSelection($("refresh"));
async function drawGame() {
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
    const card = $("gallery").querySelector(".game:not(.draw)");
    card?.focus();
    if (!document.querySelector('dialog[open]')) openGame(item, card);
  } catch (e) { report(`Não foi possível sortear: ${e.message}`, true); }
  finally { state.drawing = false; }
}
let returnFocus, returnIndex, returnGameKey;
function openGame(g, origin = document.activeElement) {
  returnFocus = origin; returnIndex = [...$("gallery").children].indexOf(returnFocus); state.selected = g;
  returnGameKey = origin?.dataset?.key;
  state.draft = {iniciado: !!g.tracking.iniciado, finalizado: !!g.tracking.finalizado, platinado: !!g.tracking.platinado, nota: g.tracking.nota ?? null};
  $("game-title").textContent = g.name; $("game-platform").textContent = g.platform;
  $("detail-cover").hidden = !g.cover; if (g.cover) $("detail-cover").src = g.cover;
  updateFavoriteButton(g); $("progress-fields").hidden = true; $("progress-toggle").setAttribute("aria-expanded", "false");
  report("", false, "detail-status"); renderTracking();
  $("download").hidden = !g.downloadName; $("download").textContent = "Baixar para o PC"; $("download").dataset.confirm = "";
  $("download").disabled = !!state.download;
  $("details").showModal(); $("close").focus();
  refreshPlayOptions(g);
}
$("progress-toggle").onclick = () => {
  $("progress-fields").hidden = !$("progress-fields").hidden;
  $("progress-toggle").setAttribute("aria-expanded", String(!$("progress-fields").hidden));
  if (!$("progress-fields").hidden) $("tracking").querySelector("button")?.focus();
};
function renderTracking() {
  const fields = [["iniciado", "Iniciado"], ["finalizado", "Finalizado"], ["platinado", "Platinado"]];
  $("tracking").replaceChildren(...fields.map(([key, label], index) => button(label, () => {
    const value = !state.draft[key];
    fields.forEach(([field], i) => { if (value ? i <= index : i >= index) state.draft[field] = value; });
    renderTracking(); $("tracking").children[index].focus();
  }, state.draft[key])));
  $("rating").textContent = state.draft.nota == null ? "Sem nota" : state.draft.nota.toFixed(1);
}
function adjustRating(delta) {
  if (state.busy) return;
  state.draft.nota = Math.max(0, Math.min(11, Math.round(((state.draft.nota ?? 0) + delta) * 10) / 10)); renderTracking();
}
$("rating-down").onclick = () => adjustRating(-1);
$("rating-up").onclick = () => adjustRating(1);
$("rating-fine-down").onclick = () => adjustRating(-0.1);
$("rating-fine-up").onclick = () => adjustRating(0.1);
$("rating-clear").onclick = () => { state.draft.nota = null; renderTracking(); };
function closeGame() { if (!state.busy) {
  $("details").close();
  const matching = [...document.querySelectorAll("#home .game,#gallery .game")].find(c => c.dataset.key === returnGameKey);
  (returnFocus?.isConnected ? returnFocus : matching || $("gallery").children[Math.max(0, returnIndex)] || $("home").querySelector("button") || $("collections").querySelector("button"))?.focus();
} }
$("close").onclick = closeGame;
$("details").addEventListener("cancel", e => { e.preventDefault(); closeGame(); });
$("save").onclick = async () => {
  if (state.busy) return;
  const g = state.selected; const campos = {...state.draft}; state.busy = true;
  $("details").querySelectorAll("button").forEach(b => { b.disabled = true; });
  report("Salvando…", false, "detail-status");
  try {
    await api(g.id ? "/api/library/edit" : "/api/library/track", g.id ? {id: g.id, campos} : {nome: g.name, code: g.code, plataforma: g.platform, fonte: `rom:${g.code}`, campos});
    Object.assign(g.tracking, campos); render(); report("Progresso salvo.", false, "detail-status");
  } catch (e) { report(`Não foi salvo: ${e.message}`, true, "detail-status"); }
  finally { state.busy = false; $("details").querySelectorAll("button").forEach(b => { b.disabled = b.dataset.unavailable === "true"; }); $("download").disabled = !!state.download; $("save").focus(); }
};
$("download").onclick = () => downloadGame(false);
async function downloadGame(playAfter) {
  if (state.download || state.busy) return;
  const b = $("download"); const g = state.selected;
  if (!b.dataset.confirm) { b.dataset.confirm = "yes"; b.textContent = "Confirmar download"; b.dataset.playAfter = String(playAfter); report(playAfter ? "Baixar este jogo e abrir o emulador ao concluir?" : "Baixar este jogo do seu Drive para o PC?", false, "detail-status"); return; }
  playAfter = b.dataset.playAfter === "true";
  b.disabled = true; state.download = g;
  report(`Baixando ${g.name}…`, false, "download-status");
  try {
    const {job} = await api("/api/heavy/download", {code: g.code, name: g.downloadName});
    const stream = new EventSource(`/api/fetch/stream?job=${encodeURIComponent(job)}`);
    let success = false, failure = "";
    function finish(message, error) { stream.close(); state.download = null; report(message, error, "download-status"); b.disabled = false; b.hidden = !state.selected?.downloadName; b.textContent = "Baixar para o PC"; b.dataset.confirm = ""; if (state.selected === g) report(message, error, "detail-status"); }
    stream.onmessage = e => {
      const data = JSON.parse(e.data);
      if (data.type === "system_done") { success = data.result.ok; if (!success) failure = data.result.message || "falha no download"; }
      if (data.type === "error") failure = data.message || "falha no download";
      if (data.type === "job_done") {
        if (success && !failure) { g.local = true; g.downloadName = null; render(); finish(`${g.name}: download concluído.`, false);
          if (state.selected === g && $("details").open) refreshPlayOptions(g);
          if (playAfter) playDownloaded(g); }
        else finish(`${g.name}: ${failure || "download não confirmado"}.`, true);
      }
    };
    stream.onerror = () => finish("A conexão com o download foi interrompida. Confira o resultado na coleção antes de tentar novamente.", true);
    if (state.selected === g) report("Download em andamento. Você pode voltar e navegar pelo acervo.", false, "detail-status");
  } catch (e) { state.download = null; b.disabled = false; b.dataset.confirm = ""; b.textContent = "Baixar para o PC"; report(e.message, true, "download-status"); }
}
let playRequest = 0, sessionTimer, sessionGame, emulatorRunning = false;
async function refreshPlayOptions(g) {
  const request = ++playRequest;
  const box = $("play-actions"); box.replaceChildren();
  $("play-hint").textContent = g.code ? "Conferindo arquivos para jogar…" : g.id ? "Conferindo se está instalado na Steam/Heroic…" : "";
  if (!g.code) return g.id ? refreshPcOption(g, request) : undefined;
  try {
    const data = await api(`/api/play/options?code=${encodeURIComponent(g.code)}&name=${encodeURIComponent(g.romName)}`);
    if (request !== playRequest || state.selected !== g) return;
    if (!data.launcher) throw new Error("O lançador bonisarch-emulator precisa estar instalado.");
    const options = data.options || [];
    try { g.emulator = localStorage.getItem(`pyretro-emulator:${g.code}:${g.romName}`) || ""; } catch (_) { g.emulator = g.emulator || ""; }
    if (!data.emulators?.some(e => e.id === g.emulator)) g.emulator = "";
    if (data.emulators?.length > 1) {
      for (const emulator of data.emulators) box.append(button(emulator.name, () => {
        g.emulator = emulator.id;
        try { localStorage.setItem(`pyretro-emulator:${g.code}:${g.romName}`, emulator.id); } catch (_) {}
        refreshPlayOptions(g);
      }, g.emulator === emulator.id));
    }
    for (const option of options) {
      const b = button(options.length === 1 ? "Jogar" : `Jogar: ${option.name}`, () => startGame(g, option.name));
      b.disabled = !!option.error; b.dataset.unavailable = String(!!option.error); box.append(b);
    }
    const broken = options.filter(o => o.error);
    $("play-hint").textContent = broken.length ? broken.map(o => `${o.name}: ${o.error}`).join(" · ") : options.length ? "Escolha o disco/formato quando houver mais de uma opção." : "A ROM precisa estar completa no PC para abrir o emulador.";
    if ((broken.length || !options.length) && g.driveName) {
      g.downloadName = g.driveName;
      $("download").hidden = false; $("download").disabled = !!state.download;
      $("download").textContent = g.local ? "Completar download" : "Baixar para o PC";
      box.append(button("Baixar e jogar", () => { $("download").dataset.confirm = ""; downloadGame(true); $("download").focus(); }));
    }
    if ($("details").open && [document.body, $("close")].includes(document.activeElement)) {
      const play = [...box.querySelectorAll("button:not(:disabled)")].find(b => !b.hasAttribute("aria-pressed"));
      play?.classList.add("primary"); play?.focus();
    }
  } catch (e) { if (request === playRequest && state.selected === g) $("play-hint").textContent = e.message; }
}
async function refreshPcOption(g, request) {
  try {
    const data = await api(`/api/pc/options?id=${encodeURIComponent(g.id)}`);
    if (request !== playRequest || state.selected !== g) return;
    const box = $("play-actions");
    if (data.remote || data.store_app) {
      const remote = data.remote || data.store_app;
      box.append(button(remote.label, () => launchApp(remote.app, "detail-status")));
      $("play-hint").textContent = remote.hint;
      box.querySelector("button")?.classList.add("primary");
      if ($("details").open && [document.body, $("close")].includes(document.activeElement)) box.querySelector("button")?.focus();
    } else if (data.available) {
      box.append(button(`Jogar (${data.store === "steam" ? "Steam" : "Heroic"})`, () => startPcGame(g)));
      $("play-hint").textContent = "Abre pela loja instalada neste PC; depois registre o progresso aqui.";
      box.querySelector("button")?.classList.add("primary");
      if ($("details").open && [document.body, $("close")].includes(document.activeElement)) box.querySelector("button")?.focus();
    } else $("play-hint").textContent = "Não instalado na Steam/Heroic deste PC; abra pela loja para jogar.";
  } catch (e) { if (request === playRequest && state.selected === g) $("play-hint").textContent = e.message; }
}
async function startPcGame(g) {
  if (state.busy) return;
  state.busy = true;
  try {
    await api("/api/pc/launch", {id: g.id});
    await refreshHomeAfterPlay();
    report(`${g.name} foi aberto pela loja. Ao terminar, volte aqui para registrar progresso e nota.`, false, "play-status");
    report("Pedido enviado à loja. A janela do jogo pode demorar a aparecer.", false, "detail-status");
  } catch (e) { report(`Não foi possível abrir: ${e.message}`, true, "play-status"); report(e.message, true, "detail-status"); }
  finally { state.busy = false; }
}
async function startGame(g, name) {
  if (state.busy) return;
  state.busy = true;
  try {
    const session = await api("/api/play/start", {code: g.code, name, ...(g.emulator ? {emulator: g.emulator} : {})});
    sessionGame = g; report(`Em jogo: ${g.name}. Ao sair, volte aqui para registrar progresso e nota.`, false, "play-status");
    if (state.selected === g) report("Emulador iniciado. Sair dele encerra a sessão; finalizar o jogo é uma escolha sua.", false, "detail-status");
    watchSession(session);
    refreshHomeAfterPlay();
  } catch (e) { report(`Não foi possível jogar: ${e.message}`, true, "play-status"); }
  finally { state.busy = false; }
}
async function refreshHomeAfterPlay() {
  if (!state.home) return;
  try {
    state.home = await api("/api/tv/home");
    if (state.kind === "home") render();
  } catch (_) { /* O próximo Atualizar relê os recentes, sem afetar o lançamento. */ }
}
async function playDownloaded(g) {
  try {
    const data = await api(`/api/play/options?code=${encodeURIComponent(g.code)}&name=${encodeURIComponent(g.romName)}`);
    const valid = data.options.filter(o => !o.error);
    if (valid.length !== 1) {
      report(valid.length ? `${g.name}: download concluído. Escolha o disco/formato em Jogar.` : `${g.name}: download concluído, mas os arquivos ainda não estão prontos para jogar.`, !valid.length, "play-status");
      return;
    }
    await startGame(g, valid[0].name);
  } catch (e) { report(e.message, true, "play-status"); }
}
function watchSession(session) {
  clearTimeout(sessionTimer);
  emulatorRunning = session.status === "running";
  if (session.status === "running") {
    if (!sessionGame) report(`Em jogo: ${session.name}`, false, "play-status");
    sessionTimer = setTimeout(async () => {
      try { watchSession(await api("/api/play/status")); }
      catch (e) { report(`Não foi possível acompanhar o emulador: ${e.message}. Recarregue para conferir a sessão.`, true, "play-status"); }
    }, 2000);
  } else if (session.status === "finished" || session.status === "error") {
    const error = session.status === "error";
    report(error ? `O emulador encerrou com erro (${session.returncode}). Consulte o log do serviço.` : "Sessão encerrada. Você pode marcar o progresso e dar uma nota.", error, "play-status");
    if (sessionGame && state.selected === sessionGame && $("details").open) {
      report(error ? "O emulador encerrou com erro." : "Como foi a sessão? Registre o progresso e a nota.", error, "detail-status");
      $("progress-fields").hidden = false; $("progress-toggle").setAttribute("aria-expanded", "true");
      $("tracking").querySelector("button")?.focus();
    }
    sessionGame = null;
  }
}

function focusable() {
  const root = document.querySelector("dialog[open]") || document;
  return [...root.querySelectorAll("button:not(:disabled),a[href],input")].filter(e => !e.hidden && e.getClientRects().length);
}
function move(direction) {
  const nodes = focusable(); const current = document.activeElement;
  if (!nodes.includes(current)) { nodes[0]?.focus(); return; }
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
function action(key) {
  if (state.busy) return;
  if (["left", "right", "up", "down"].includes(key)) move(key);
  else if (key === "accept") { if (!focusable().includes(document.activeElement)) focusable()[0]?.focus(); else document.activeElement.click(); }
  else if (key === "back") { if ($("search-dialog").open) closeSearch(); else if ($("settings-dialog").open) closeSettings(); else if ($("details").open) closeGame(); else if (state.kind !== "home") load("home"); else $("collections").querySelector("button")?.focus(); }
  else if (key === "search") openSearch();
  else if (key === "erase") { if ($("search-dialog").open) $("search-input").value = $("search-input").value.slice(0, -1); else if (!$("settings-dialog").open) toggleFavorite(); }
  else if (key === "submit") { if ($("search-dialog").open) applySearch(); else openSettings(); }
  else if (["page-up", "page-down"].includes(key) && !document.querySelector("dialog[open]")) page(key === "page-up" ? -1 : 1);
  else if (["previous", "next"].includes(key) && !document.querySelector("dialog[open]")) {
    const index = Math.max(0, collections.findIndex(x => x[0] === state.kind));
    load(collections[(index + (key === "previous" ? -1 : 1) + collections.length) % collections.length][0]);
  }
}
function page(direction) {
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
document.addEventListener("keydown", e => {
  if (e.target instanceof HTMLInputElement && e.key !== "Escape") return;
  const key = {ArrowLeft: "left", ArrowRight: "right", ArrowUp: "up", ArrowDown: "down", Escape: "back", PageUp: "page-up", PageDown: "page-down", y: "search", Y: "search"}[e.key];
  if (key) { e.preventDefault(); action(key); }
});
let held = new Set(), repeatAt = new Map(), foreground = true, awaitNeutral = false;
window.addEventListener("blur", () => { foreground = false; held.clear(); awaitNeutral = true; });
window.addEventListener("focus", () => { foreground = true; });
function pollGamepad(now) {
  const pads = Array.from(navigator.getGamepads?.() || []).filter(p => p && p.connected !== false && p.buttons.length >= 10);
  const pad = pads.find(p => p.mapping === "standard") || pads[0];
  if (pad) {
    $("controller").textContent = `Controle conectado: ${pad.id}`;
    const pressed = i => pad.buttons[i]?.pressed;
    const keys = new Set();
    if (pressed(14) || pad.axes[0] < -0.55) keys.add("left");
    if (pressed(15) || pad.axes[0] > 0.55) keys.add("right");
    if (pressed(12) || pad.axes[1] < -0.55) keys.add("up");
    if (pressed(13) || pad.axes[1] > 0.55) keys.add("down");
    if (pressed(0)) keys.add("accept"); if (pressed(1)) keys.add("back");
    if (pressed(2)) keys.add("erase"); if (pressed(3)) keys.add("search");
    if (pressed(4)) keys.add("page-up"); if (pressed(5)) keys.add("page-down");
    if (pressed(6)) keys.add("previous"); if (pressed(7)) keys.add("next");
    if (pressed(9)) keys.add("submit");
    if (!foreground || document.hidden || emulatorRunning) { held.clear(); awaitNeutral = true; requestAnimationFrame(pollGamepad); return; }
    if (awaitNeutral) { if (!keys.size) awaitNeutral = false; requestAnimationFrame(pollGamepad); return; }
    for (const k of keys) {
      if (!held.has(k)) { action(k); repeatAt.set(k, now + 380); }
      else if (["left", "right", "up", "down", "page-up", "page-down", ...($("search-dialog").open ? ["erase"] : [])].includes(k) && now >= repeatAt.get(k)) { action(k); repeatAt.set(k, now + 110); }
    }
    held = keys;
  } else { held.clear(); $("controller").textContent = "Controle: pressione um botão para conectar"; }
  requestAnimationFrame(pollGamepad);
}
async function openLinkedGame(key) {
  const game = (await api("/api/tv/catalog")).find(game => game.key === key);
  if (game) openGame(game);
  else report("O jogo desse link não está mais disponível no catálogo.", true);
}
async function init() {
  collectionTabs();
  try {
    [state.systems, state.light] = await Promise.all([api("/api/heavy/systems"), api("/api/systems")]); await load();
    const key = new URLSearchParams(location.search).get("game");
    if (key) await openLinkedGame(key);
  }
  catch (e) { report(`Não foi possível iniciar: ${e.message}. Recarregue para tentar novamente.`, true); }
  if (state.kind !== "home") $("collections").querySelector("button")?.focus();
}
requestAnimationFrame(pollGamepad); init();
api("/api/play/status").then(watchSession).catch(() => {});

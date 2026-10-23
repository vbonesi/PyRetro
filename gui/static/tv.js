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
const collections = [["home", "Início"], ["local", "Neste PC"], ["favorites", "Favoritos"], ["systems", "Sistemas"], ["library", "Biblioteca"], ["playing", "Jogando"], ["ranking", "Ranking"], ["wishlist", "Desejados"], ["stats", "Estatísticas"], ["heavy", "ROMs pesadas"], ["light", "ROMs leves"], ["draw", "🎲 Sortear"], ["apps", "Apps"]];
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
  if (!["home", "systems", "apps", "stats"].includes(state.kind) && names.length) {
    genres.hidden = false;
    for (const name of ["", ...names]) genres.append(button(name || "Qualquer gênero", () => {
      state.genre = name; platformTabs(); render(); genres.querySelector('[aria-pressed="true"]')?.focus();
    }, (state.genre || "") === name));
  }
  if (["library", "playing", "ranking", "wishlist", "local", "search", "favorites"].includes(state.kind)) {
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
  $("installed-only").hidden = ["home", "systems", "apps", "draw", "local", "wishlist", "stats"].includes(kind);
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
function render() {
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
    // Mouse: botão direito favorita, igual ao X do controle.
    card.addEventListener("contextmenu", e => { if (g.wishlist) return; e.preventDefault(); card.focus(); toggleFavorite(g); });
    if (g.cover) { const img = document.createElement("img"); img.src = g.cover; img.alt = ""; img.loading = "lazy"; img.className = "art"; card.append(img); }
    else { const art = document.createElement("div"); art.className = "art placeholder"; art.textContent = "✦"; card.append(art); }
    const title = document.createElement("strong"); title.textContent = (g.favorite ? "★ " : "") + g.name;
    const meta = document.createElement("small"); const t = g.tracking;
    meta.textContent = [g.platform, g.downloadName && !g.local ? "Só no Drive" : g.local ? "No PC" : "", t.platinado ? "🏆 Platinado" : t.finalizado ? "✓ Finalizado" : t.iniciado ? "▶ Iniciado" : "", t.nota != null ? `★ ${t.nota}` : "", g.playtime?.seconds ? `◷ ${formatTime(g.playtime.seconds)}` : ""].filter(Boolean).join(" · ");
    card.append(title, meta); return card;
}
function showSpotlight(g) {
  spotlightGame = g;
  $("spotlight-title").textContent = g.name;
  $("spotlight-meta").textContent = [g.platform, g.local ? "Pronto neste PC" : g.downloadName ? "Disponível no Drive" : "Na sua biblioteca", g.tracking.genero, g.favorite ? "★ Favorito" : ""].filter(Boolean).join(" · ");
  $("spotlight-art").style.backgroundImage = g.cover ? `url(${JSON.stringify(g.cover)})` : "none";
  $("spotlight-open").textContent = g.local ? "Abrir jogo" : "Ver jogo";
  const logo = $("spotlight-logo"), video = $("spotlight-video");
  logo.hidden = !g.media?.logo; if (g.media?.logo) logo.src = g.media.logo;
  const source = g.media?.video || "";
  if (video.dataset.source !== source) { video.pause(); video.removeAttribute('src'); video.dataset.source = source; if (source) video.src = source; }
  video.hidden = !source;
  if (source && !document.hidden && !document.querySelector('dialog[open]') && !matchMedia('(prefers-reduced-motion: reduce)').matches) video.play().catch(() => {});
}
function formatTime(seconds) { const minutes = Math.floor(seconds / 60); return minutes >= 60 ? `${Math.floor(minutes/60)} h ${minutes%60} min` : minutes ? `${minutes} min` : `${Math.floor(seconds)} s`; }
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
  for (const [key, title] of [["recent", "Jogados recentemente"], ["continue", "Continuar jogando"], ["favorites", "Seus favoritos"], ["mostPlayed", "Mais jogados"], ["installed", "Steam e Heroic · prontos para jogar"], ["ready", "Explore seu acervo local"]]) {
    const games = home[key] || []; if (!games.length) continue;
    const section = document.createElement("section"); section.className = "home-section"; section.dataset.shelf = key;
    const heading = document.createElement("h3"); heading.textContent = title;
    const row = document.createElement("div"); row.className = "shelf"; row.setAttribute("aria-label", title);
    for (const game of games) row.append(gameCard(game));
    section.append(heading, row); box.append(section);
  }
  const all = [home.recent, home.continue, home.favorites, home.installed, home.ready, home.mostPlayed].flatMap(g => g || []);
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
    for (const item of [...state.items, ...["recent", "continue", "favorites", "installed", "ready", "mostPlayed"].flatMap(k => state.home?.[k] || [])]) if (item.key) item.favorite = preferences.favorites.includes(item.key);
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
const WISHLIST_STORES = {steam: "Steam", psn: "PlayStation", xbox: "Xbox"};
function formatHours(hours) {
  const total = Math.round(hours), days = Math.floor(total / 24);
  return days ? `${days} dias e ${total % 24} h (${total.toLocaleString("pt-BR")} h)` : `${total} h`;
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
    tile("◷", formatHours(s.tempo_total_horas), "de jogo registrado", () => load("library")),
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
let searchReturnFocus, textEntry = null;
function openSearch() {
  if (document.querySelector("dialog[open]")) return;
  textEntry = null; searchDialogLabels("Pesquisar jogos", "Nome do jogo", "Pesquisar", "Limpar busca");
  searchReturnFocus = document.activeElement; $("search-input").value = state.query;
  $("search-dialog").showModal(); $("keyboard").querySelector("button")?.focus();
}
// O mesmo teclado da tela serve para editar texto (nome, gênero, comentário…) com o controle.
function openTextEntry(title, value, apply) {
  textEntry = apply; searchDialogLabels(title, title, "Confirmar", "Apagar tudo");
  searchReturnFocus = document.activeElement; $("search-input").value = value || "";
  $("search-dialog").showModal(); $("keyboard").querySelector("button")?.focus();
}
function searchDialogLabels(title, label, apply, clear) {
  $("search-title").textContent = title; $("search-label").textContent = label;
  $("search-apply").textContent = apply; $("search-clear").textContent = clear;
  $("search-hint").textContent = textEntry ? "Direcional e A no teclado abaixo; ⇧ troca maiúsculas. X apaga; Menu confirma; B cancela." : "Use o direcional e A no teclado abaixo. X apaga; Menu pesquisa; B cancela.";
}
function closeSearch() { $("search-dialog").close(); textEntry = null; (searchReturnFocus?.isConnected ? searchReturnFocus : $("search-open"))?.focus(); }
async function applySearch() {
  if (textEntry) { const apply = textEntry, value = $("search-input").value.trim(); closeSearch(); return apply(value); }
  state.query = $("search-input").value.trim(); closeSearch();
  if (["home", "systems", "apps", "draw"].includes(state.kind)) await load("search"); else render();
  $("gallery").querySelector("button")?.focus();
}
let keyboardLower = false;
function buildKeyboard() {
  const keys = [..."1234567890QWERTYUIOPASDFGHJKLÇZXCVBNM -':./,&!?()"].map(c => keyboardLower ? c.toLowerCase() : c);
  $("keyboard").replaceChildren(...keys.map(character => button(character === " " ? "␣" : character, () => { const input = $("search-input"); input.value = (input.value + character).slice(0, 2000); })),
    button("⌫", () => { $("search-input").value = $("search-input").value.slice(0, -1); }),
    button(keyboardLower ? "⇧ ABC" : "⇧ abc", () => { keyboardLower = !keyboardLower; buildKeyboard(); $("keyboard").lastChild.focus(); }));
}
buildKeyboard();
$("search-open").onclick = openSearch; $("search-close").onclick = closeSearch;
$("search-apply").onclick = applySearch;
$("search-clear").onclick = () => { $("search-input").value = ""; if (!textEntry) applySearch(); else $("search-input").focus(); };
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
  const textureCode = {PS:'PS1',PS2:'PS2',NGC:'GC',WII:'WII',PSP:'PSP'}[g.code];
  $("textures-link").hidden = !textureCode;
  if (textureCode) $("textures-link").href = '/?'+new URLSearchParams({textures:textureCode,game:g.name});
  $("detail-cover").hidden = !g.cover; if (g.cover) $("detail-cover").src = g.cover;
  $("spotlight-video").pause(); $("time-fields").hidden = true; $("media-fields").hidden = true;
  $("game-time").textContent = g.playtime?.seconds ? `${formatTime(g.playtime.seconds)} em ${g.playtime.sessions} sessão(ões) registrada(s).` : 'Ainda sem tempo registrado neste PC.';
  $("detail-video").pause(); $("detail-video").hidden = !g.media?.video;
  $("detail-video").removeAttribute('src'); if (g.media?.video) $("detail-video").src = g.media.video;
  $("saves-toggle").hidden = !g.code; $("saves-fields").hidden = true; $("saves-toggle").setAttribute("aria-expanded", "false");
  state.edits = {}; $("edit-fields").hidden = true; $("cover-fields").hidden = true; $("genre-list").hidden = true;
  $("edit-toggle").setAttribute("aria-expanded", "false"); $("cover-toggle").setAttribute("aria-expanded", "false");
  $("cover-toggle").hidden = !g.code && !g.id; $("edit-toggle").hidden = !g.code && !g.id;
  $("wishlist-actions").hidden = !g.wishlist;
  // Desejado ainda não é seu: sem favorito, tempo, mídia ou progresso.
  for (const id of ["favorite", "time-toggle", "media-toggle", "progress-toggle", "game-time"]) $(id).hidden = !!g.wishlist;
  for (const id of ["wishlist-bought", "wishlist-remove"]) { $(id).dataset.confirm = ""; $(id).textContent = id === "wishlist-bought" ? "✅ Comprado" : "🗑 Tirar da lista"; }
  updateFavoriteButton(g); $("progress-fields").hidden = true; $("progress-toggle").setAttribute("aria-expanded", "false");
  report("", false, "detail-status"); renderTracking();
  $("download").hidden = !g.downloadName; $("download").textContent = "Baixar para o PC"; $("download").dataset.confirm = "";
  $("download").disabled = !!state.download;
  $("details").showModal(); $("close").focus();
  if (g.wishlist) { $("play-actions").replaceChildren(); $("play-hint").textContent = `Na sua lista de desejos (${WISHLIST_STORES[g.wishlist]}). Comprou? Marque abaixo e ele entra na Biblioteca.`; }
  else refreshPlayOptions(g);
}
// ✎ Editar jogo: os mesmos campos do ✎ da web. ROM sem cadastro cria o registro na 1ª gravação
// (/api/library/track); nome e plataforma de ROM vêm do arquivo/sistema e não são editados aqui.
const EDIT_FIELDS = [["nome", "Nome"], ["plataforma", "Plataforma"], ["genero", "Gênero"], ["data_final", "Data que finalizou (aaaa-mm-dd)"], ["tempo", "Tempo jogado (ex.: 31:40:00)"], ["observacoes", "Comentário"]];
function editFields(g) { return g.code ? EDIT_FIELDS.filter(([f]) => !["nome", "plataforma"].includes(f)) : EDIT_FIELDS; }
function editValue(g, field) { return field in state.edits ? state.edits[field] : field === "nome" ? g.name : field === "plataforma" && !g.tracking.plataforma ? g.platform : g.tracking[field] ?? ""; }
function renderEdit(focusField) {
  const g = state.selected;
  $("edit-list").replaceChildren(...editFields(g).map(([field, label]) => {
    const value = editValue(g, field);
    const b = button(`${field in state.edits ? "• " : ""}${label}: ${value || "—"}`, () => editField(field, label));
    b.dataset.field = field; return b;
  }));
  if (focusField) $("edit-list").querySelector(`[data-field="${focusField}"]`)?.focus();
}
async function editField(field, label) {
  const g = state.selected;
  if (field !== "genero") return openTextEntry(label, editValue(g, field), value => { state.edits[field] = value; renderEdit(field); });
  const box = $("genre-list");
  if (!box.hidden) { box.hidden = true; return; }
  try { if (!state.sortear) state.sortear = await api("/api/sortear/systems"); } catch (_) { /* sem lista: só o teclado */ }
  const current = editValue(g, "genero");
  box.replaceChildren(...(state.sortear?.generos || []).map(name => button(name, () => { state.edits.genero = name; box.hidden = true; renderEdit("genero"); }, name === current)),
    button("Outro…", () => { box.hidden = true; openTextEntry(label, current, value => { state.edits.genero = value; renderEdit("genero"); }); }),
    button("Sem gênero", () => { state.edits.genero = ""; box.hidden = true; renderEdit("genero"); }));
  box.hidden = false; (box.querySelector('[aria-pressed="true"]') || box.querySelector("button"))?.focus();
}
$("edit-toggle").onclick = () => {
  const box = $("edit-fields"); box.hidden = !box.hidden; if (!box.hidden) closeOtherPanels("edit-toggle"); $("edit-toggle").setAttribute("aria-expanded", String(!box.hidden));
  if (!box.hidden) { renderEdit(); $("edit-list").querySelector("button")?.focus(); }
};
$("edit-save").onclick = async () => {
  const g = state.selected; if (state.busy || !g) return;
  // Só o que mudou de fato: escolher o mesmo valor não grava nada.
  const original = f => { const {edits} = state; state.edits = {}; const v = String(editValue(g, f) ?? ""); state.edits = edits; return v; };
  const campos = Object.fromEntries(Object.entries(state.edits).filter(([f, v]) => v.trim() !== original(f).trim()).map(([f, v]) => [f, v.trim() || null]));
  if (!Object.keys(campos).length) return report("Nada alterado.", false, "detail-status");
  if (campos.nome === null || campos.plataforma === null) return report("Nome e plataforma não podem ficar vazios.", true, "detail-status");
  state.busy = true; report("Salvando…", false, "detail-status");
  try {
    if (g.id) await api("/api/library/edit", {id: g.id, campos});
    else { const r = await api("/api/library/track", {nome: g.name, code: g.code, plataforma: g.platform, fonte: `rom:${g.code}`, campos}); g.id = r.id; }
    Object.assign(g.tracking, campos);
    if (campos.nome) { g.name = campos.nome; $("game-title").textContent = g.name; }
    if (campos.plataforma && !g.wishlist) { g.platform = campos.plataforma; $("game-platform").textContent = g.platform; }
    state.edits = {}; renderEdit(); render(); report("Dados do jogo salvos.", false, "detail-status");
  } catch (e) { report(`Não foi salvo: ${e.message}`, true, "detail-status"); }
  finally { state.busy = false; }
};
// 🖼 Capa: busca nas mesmas fontes da web. ROM: bases de ROM (libretro/LaunchBox/ScreenScraper) ou
// SteamGridDB; Biblioteca: SteamGridDB. Aplicar troca o arquivo da capa, como na web.
function coverLabel(g) {
  const fromCover = /\/images\/[^/]+\/([^?]+)/.exec(g.cover || "");
  if (fromCover) return decodeURIComponent(fromCover[1]).replace(/\.(png|jpg)$/i, "");
  return state.systems.some(s => s.code === g.code) ? g.romName.replace(/\.[a-z0-9]{2,4}$/i, "") : g.romName;
}
function renderCoverSources() {
  const g = state.selected, sources = g.code ? [["rom", "Bases de ROM"], ["sgdb", "SteamGridDB"]] : [["sgdb", "SteamGridDB"]];
  $("cover-query").textContent = `Busca: ${state.cover.query}`;
  $("cover-sources").replaceChildren(...sources.map(([id, label]) => button(label, () => { state.cover.source = id; renderCoverSources(); searchCover(); }, state.cover.source === id)));
}
$("cover-toggle").onclick = () => {
  const box = $("cover-fields"), g = state.selected; box.hidden = !box.hidden; $("cover-toggle").setAttribute("aria-expanded", String(!box.hidden));
  if (box.hidden) return;
  closeOtherPanels("cover-toggle");
  state.cover = {query: g.name, source: g.code ? "rom" : "sgdb"}; renderCoverSources(); searchCover();
};
$("cover-query").onclick = () => openTextEntry("Buscar capa", state.cover.query, value => { if (value.length < 2) return; state.cover.query = value; renderCoverSources(); searchCover(); });
let coverRequest = 0;
async function searchCover() {
  const g = state.selected, request = ++coverRequest, box = $("cover-results"), {query, source} = state.cover;
  box.replaceChildren(Object.assign(document.createElement("p"), {className: "hint", textContent: "Buscando capas… pode levar até um minuto."}));
  try {
    const found = source === "rom"
      ? (await api(`/api/cover/search?${new URLSearchParams({code: g.code, q: query})}`)).map(it => ({url: it.preview, name: it.name, label: {libretro: "libretro-thumbnails", launchbox: "LaunchBox", screenscraper: "ScreenScraper"}[it.source] || it.source, raw: it}))
      : (await api(`/api/cover/search_sgdb?${new URLSearchParams({q: query})}`)).map(it => ({url: it.url, name: it.nome, label: "SteamGridDB", raw: it}));
    if (request !== coverRequest || state.selected !== g) return;
    if (!found.length) return box.replaceChildren(Object.assign(document.createElement("p"), {className: "hint", textContent: "Nada encontrado. Troque a busca ou a fonte."}));
    box.replaceChildren(...found.slice(0, 24).map(item => {
      const card = button("", () => applyCover(g, item, source)); card.className = "game cover-choice";
      const img = document.createElement("img"); img.src = item.url; img.alt = ""; img.loading = "lazy"; img.className = "art";
      const name = document.createElement("strong"); name.textContent = item.name;
      const from = document.createElement("small"); from.textContent = item.label;
      card.append(img, name, from); return card;
    }));
  } catch (e) { if (request === coverRequest) box.replaceChildren(Object.assign(document.createElement("p"), {className: "hint error", textContent: `Busca falhou: ${e.message}`})); }
}
async function applyCover(g, item, source) {
  if (state.busy) return; state.busy = true; report("Aplicando capa…", false, "detail-status");
  try {
    const label = g.code ? coverLabel(g) : null;
    if (source === "rom") await api("/api/cover/select", {code: g.code, label, source: item.raw.source, name: item.raw.name, filename: item.raw.filename || "", ss_id: item.raw.ss_id || ""});
    const r = source === "rom" ? null : await api("/api/cover/apply_url", g.code ? {kind: "rom", code: g.code, label, url: item.url} : {kind: "biblioteca", id: g.id, url: item.url});
    g.cover = g.code ? `/images/${encodeURIComponent(g.code)}/${encodeURIComponent(label)}.png?v=${Date.now()}` : `/library-images/${r.file.split("/").map(encodeURIComponent).join("/")}?v=${Date.now()}`;
    $("detail-cover").src = g.cover; $("detail-cover").hidden = false;
    $("cover-fields").hidden = true; $("cover-toggle").setAttribute("aria-expanded", "false"); $("cover-toggle").focus();
    render(); report("Capa trocada.", false, "detail-status");
  } catch (e) { report(`Capa não aplicada: ${e.message}`, true, "detail-status"); }
  finally { state.busy = false; }
}
// Desejados: sair da lista é um jogo por vez, com confirmação (mesmas rotas do ✎ da web).
for (const [id, action, label] of [["wishlist-bought", "comprado", "✅ Comprado"], ["wishlist-remove", "remove", "🗑 Tirar da lista"]]) $(id).onclick = async () => {
  const g = state.selected, b = $(id); if (state.busy || !g?.wishlist) return;
  if (!b.dataset.confirm) { b.dataset.confirm = "yes"; b.textContent = action === "comprado" ? "Confirmar: comprado" : "Confirmar: tirar"; report(action === "comprado" ? `Marcar "${g.name}" como comprado? Sai dos Desejados e entra na Biblioteca.` : `Tirar "${g.name}" da lista de desejos?`, false, "detail-status"); return; }
  state.busy = true;
  try {
    await api(`/api/wishlist/${action}`, {source: g.wishlist, id: g.id});
    state.items = state.items.filter(x => x !== g); state.busy = false; closeGame(); render();
    report(action === "comprado" ? `${g.name} entrou na Biblioteca.` : `${g.name} saiu dos Desejados.`);
  } catch (e) { b.dataset.confirm = ""; b.textContent = label; report(e.message, true, "detail-status"); }
  finally { state.busy = false; }
};
// 💾 Saves do jogo no PC (RetroArch, pasta do sistema e raiz antiga). Só leitura.
// Saves, edição e capa dividem a ficha: abrir um painel fecha os outros.
function closeOtherPanels(keep) {
  for (const [toggle, panel] of [["saves-toggle", "saves-fields"], ["edit-toggle", "edit-fields"], ["cover-toggle", "cover-fields"]])
    if (toggle !== keep) { $(panel).hidden = true; $(toggle).setAttribute("aria-expanded", "false"); }
}
$("saves-toggle").onclick = async () => {
  const g = state.selected, box = $("saves-fields");
  box.hidden = !box.hidden; if (!box.hidden) closeOtherPanels("saves-toggle"); $("saves-toggle").setAttribute("aria-expanded", String(!box.hidden));
  if (box.hidden || !g?.code) return;
  box.replaceChildren(Object.assign(document.createElement("p"), {className: "hint", textContent: "Procurando saves neste PC…"}));
  try {
    const {items} = await api('/api/tv/saves?' + new URLSearchParams({code: g.code, label: g.romName || g.name}));
    if (state.selected !== g) return;
    const when = t => new Date(t * 1000).toLocaleString("pt-BR", {dateStyle: "short", timeStyle: "short"});
    const size = n => n >= 1048576 ? `${(n/1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(n/1024))} KB`;
    box.replaceChildren(...(items.length ? items.map(f => Object.assign(document.createElement("p"), {
      textContent: `${f.kind === "save" ? "💾" : "⏸"} ${f.name} · ${size(f.size)} · ${when(f.mtime)}${f.legado ? " · pasta antiga" : ""}`})) :
      [Object.assign(document.createElement("p"), {className: "hint", textContent: "Nenhum save ou estado deste jogo no RetroArch do PC."})]),
      Object.assign(document.createElement("p"), {className: "hint", textContent: "Para trocar saves com o celular, use 💾 Saves no app Android. Feche o emulador antes."}));
  } catch (error) { box.replaceChildren(Object.assign(document.createElement("p"), {className: "hint", textContent: error.message})); }
};
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
  $("detail-video").pause();
  $("details").close();
  if (state.kind === 'home' && spotlightGame) showSpotlight(spotlightGame);
  const matching = [...document.querySelectorAll("#home .game,#gallery .game")].find(c => c.dataset.key === returnGameKey);
  (returnFocus?.isConnected ? returnFocus : matching || $("gallery").children[Math.max(0, returnIndex)] || $("home").querySelector("button") || $("collections").querySelector("button"))?.focus();
} }
$("time-toggle").onclick = () => { $("time-fields").hidden = !$("time-fields").hidden; if (!$("time-fields").hidden) $("time-minutes").focus(); };
$("media-toggle").onclick = () => { $("media-fields").hidden = !$("media-fields").hidden; };
$("time-save").onclick = async () => {
  const g = state.selected; if (state.busy || !g?.key) return;
  state.busy = true;
  try { g.playtime = await api('/api/tv/playtime', {key:g.key,minutes:Number($("time-minutes").value)}); $("game-time").textContent = `${formatTime(g.playtime.seconds)} em ${g.playtime.sessions} sessão(ões) registrada(s).`; report('Tempo registrado.',false,'detail-status'); await refreshHomeAfterPlay(); }
  catch(error) { report(error.message,true,'detail-status'); }
  finally { state.busy = false; }
};
for (const kind of ['logo','video']) $("media-"+kind).onchange = async event => {
  const file = event.target.files[0], g = state.selected; if (!file || !g?.key || state.busy) return;
  if (file.size > 64*1024*1024) { report('Escolha um arquivo de até 64 MB.',true,'detail-status'); return; }
  state.busy = true; report('Importando mídia…',false,'detail-status');
  try {
    csrf = csrf || (await api('/api/csrf')).token;
    const response = await fetch('/api/tv/media?'+new URLSearchParams({key:g.key,kind}),{method:'POST',headers:{'X-PyRetro-CSRF':csrf,'Content-Type':'application/octet-stream'},body:file});
    const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Falha na importação');
    g.media = data; report('Mídia salva neste PC.',false,'detail-status');
    if (data.video) { $("detail-video").src = data.video; $("detail-video").hidden = false; }
    await refreshHomeAfterPlay();
  } catch(error) { report(error.message,true,'detail-status'); }
  finally { state.busy = false; event.target.value = ''; }
};
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
    const selected = state.selected;
    if (selected && $("details").open) {
      const fresh = Object.values(state.home).filter(Array.isArray).flat().find(g => g.key === selected.key);
      if (fresh?.playtime) { selected.playtime = fresh.playtime; $("game-time").textContent = `${formatTime(fresh.playtime.seconds)} em ${fresh.playtime.sessions} sessão(ões) registrada(s).`; }
    }
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
    if (session.timeError) report(`Sessão encerrada, mas o tempo não foi salvo: ${session.timeError}`,true,'play-status');
    refreshHomeAfterPlay();
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
  const key = {ArrowLeft: "left", ArrowRight: "right", ArrowUp: "up", ArrowDown: "down", Escape: "back", Backspace: "back", PageUp: "page-up", PageDown: "page-down", y: "search", Y: "search"}[e.key];
  if (key) { e.preventDefault(); action(key); }
});
// Mouse: o botão "voltar" lateral faz o mesmo que B.
document.addEventListener("mouseup", e => { if (e.button === 3) { e.preventDefault(); action("back"); } });
let held = new Set(), repeatAt = new Map(), foreground = true, awaitNeutral = false, noPadSince = null;
window.addEventListener("blur", () => { foreground = false; held.clear(); awaitNeutral = true; $("spotlight-video").pause(); });
document.addEventListener('visibilitychange', () => { if (document.hidden) { $("spotlight-video").pause(); $("detail-video").pause(); } else if (state.kind === 'home' && spotlightGame) showSpotlight(spotlightGame); });
window.addEventListener("focus", () => { foreground = true; });
function pollGamepad(now) {
  const pads = Array.from(navigator.getGamepads?.() || []).filter(p => p && p.connected !== false && p.buttons.length >= 10);
  const pad = pads.find(p => p.mapping === "standard") || pads[0];
  if (pad) {
    $("controller").textContent = `Controle conectado: ${pad.id}`; noPadSince = null; $("controller").classList.remove("warning");
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
  } else {
    held.clear();
    // A Gamepad API só lista o controle depois de um botão; se continuar vazia, a página não o vê.
    noPadSince ??= now;
    const waited = now - noPadSince > 10000;
    $("controller").textContent = !waited ? "Controle: pressione um botão para conectar"
      : "Controle não visto pelo navegador. Ligue o Xbox e aperte um botão; se continuar, o Chrome do modo TV precisa de acesso a /run/udev (setup, passo de acesso dos emuladores).";
    $("controller").classList.toggle("warning", waited);
  }
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

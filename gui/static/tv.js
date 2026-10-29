/* Modo TV: cliente das mesmas APIs da GUI, sem acesso direto ao acervo. */
"use strict";
const $ = id => document.getElementById(id);
if (window.ResizeObserver) new ResizeObserver(entries => {
  document.documentElement.style.setProperty("--footer-height", `${entries[0].target.getBoundingClientRect().height}px`);
}).observe(document.querySelector("footer"));
let csrf;
async function api(url, body, retried = false) {
  const options = body === undefined ? {} : {method: "POST", headers: {
    "Content-Type": "application/json", "X-PyRetro-CSRF": csrf || (csrf = (await api("/api/csrf")).token),
  }, body: JSON.stringify(body)};
  const response = await fetch(url, options);
  // Servidor reiniciado gera token novo: busca de novo e repete uma vez, sem exigir recarregar a página.
  if (response.status === 403 && body !== undefined && !retried) { csrf = null; return api(url, body, true); }
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}
const state = {query: "", installedOnly: false, draw: {group: "", genre: ""}, sortear: null, kind: "home", code: "", filter: "", items: [], systems: [], light: [], request: 0, selected: null, draft: null, busy: false, download: null, preferences: {favorites: [], theme: "dark"}, home: null};
// --- glifos do controle: Xbox (A/B/X/Y), PlayStation (✕/○/□/△) ou automático pelo controle conectado ---
const GLIFOS = {xbox: {A: "A", B: "B", X: "X", Y: "Y", L: "LB", R: "RB", LT: "LT", RT: "RT"}, ps: {A: "✕", B: "○", X: "□", Y: "△", L: "L1", R: "R1", LT: "L2", RT: "R2"}};
const GLIFO_NOMES = {auto: "Automático", xbox: "Xbox", ps: "PlayStation"};
let glifoPref = "auto", glifoDetectado = "xbox";
try { glifoPref = localStorage.getItem("pyretro-glifos") || "auto"; } catch (_) {}
function padFamily(id = "") { return /054c|sony|dualshock|dualsense|wireless controller/i.test(id) ? "ps" : "xbox"; }
function glifos() { return GLIFOS[glifoPref === "auto" ? glifoDetectado : glifoPref] || GLIFOS.xbox; }
function applyGlyphs() {
  const g = glifos();
  $("hints").textContent = `✚ Navegar · ${g.A} Escolher · ${g.B} Voltar · ☰ Opções`;
  $("hints-extra").textContent = `${g.X} Favoritar · ${g.Y} Pesquisar · ${g.L}/${g.R} Página · ${g.LT}/${g.RT} Coleção · Mouse: botão direito favorita`;
  $("search-open").textContent = `${g.Y} · Pesquisar`;
  $("glyphs-cycle").textContent = `Botões: ${GLIFO_NOMES[glifoPref]}`;
}
// Filtros secundários (plataforma e gênero) recolhíveis: mais área para os jogos.
let filtrosRecolhidos = true;
try { filtrosRecolhidos = localStorage.getItem("pyretro-filtros") !== "aberto"; } catch (_) {}
function updateFilters() {
  const toggle = $("filters-toggle"), available = !["home", "systems", "apps", "stats", "tools", "draw"].includes(state.kind);
  const active = (state.filter ? 1 : 0) + (state.genre ? 1 : 0);
  toggle.hidden = !available;
  toggle.textContent = `Filtros${active ? ` (${active})` : ""} ${filtrosRecolhidos ? "▾" : "▴"}`;
  toggle.setAttribute("aria-expanded", String(!filtrosRecolhidos));
  document.body.classList.toggle("filters-collapsed", available && filtrosRecolhidos);
}
const collections = [["home", "Início"], ["local", "Neste PC"], ["favorites", "Favoritos"], ["systems", "Sistemas"], ["library", "Biblioteca"], ["playing", "Jogando"], ["ranking", "Ranking"], ["wishlist", "Desejados"], ["stats", "Estatísticas"], ["heavy", "ROMs pesadas"], ["light", "ROMs leves"], ["draw", "🎲 Sortear"], ["tools", "🛠 Ferramentas"], ["apps", "Apps"]];
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
  if (/^(Sessão encerrada|O emulador encerrou)/.test($("play-status").textContent)) report("", false, "play-status");
  if (kind !== state.kind && kind !== "search") state.query = "";
  state.kind = kind; state.filter = ""; state.genre = "";
  const systems = kind === "heavy" ? state.systems : state.light;
  state.code = code || systems[0]?.code || "";
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
const observedSaves = new Map();
const badgeKey = g => g.key || (g.code ? `${g.code}:${g.romName}` : `pc:${g.id}`);
function gameBadges(g) {
  const t = g.tracking || {}, badges = [];
  if (t.platinado) badges.push(['🏆 Platinado', 'Jogo platinado']);
  else if (t.finalizado) badges.push(['✓ Finalizado', 'Jogo finalizado']);
  else if (t.iniciado) badges.push(['▶ Jogando', 'Jogo iniciado']);
  if (t.nota != null) badges.push([`${notaEspecial(t.nota) ? '✦' : '★'} ${String(t.nota).replace('.', ',')}`, notaEspecial(t.nota) ? 'Nota: jogo muito especial' : 'Nota', notaColor(t.nota)]);
  const minutes = Math.floor((g.playtime?.seconds || 0) / 60);
  if (minutes > 0) badges.push([minutes >= 60 ? `⏱ ${Math.floor(minutes/60)}h${String(minutes%60).padStart(2,'0')}` : `⏱ ${minutes}min`, 'Tempo registrado neste PC']);
  if (observedSaves.get(badgeKey(g))) badges.push(['💾', 'Save encontrado neste PC na última consulta']);
  return badges;
}
function fillBadges(target, g) {
  target.replaceChildren();
  for (const [label, title, color] of gameBadges(g)) {
    const badge = document.createElement('span'); badge.className = 'badge';
    if (color) { badge.style.color = color; badge.style.borderColor = color; }
    badge.textContent = label; badge.title = title; badge.setAttribute('aria-label', `${title}: ${label}`);
    target.append(badge);
  }
  target.hidden = !target.children.length;
}
function refreshBadges(g) {
  for (const card of document.querySelectorAll('.game')) {
    const item = cardGames.get(card);
    if (item && badgeKey(item) === badgeKey(g)) fillBadges(card.querySelector('.badges'), g);
  }
  if (state.selected === g) fillBadges($('game-badges'), g);
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
    const meta = document.createElement("small");
    meta.textContent = [g.platform, g.downloadName && !g.local ? "No Drive" : g.local ? "Neste PC" : ""].filter(Boolean).join(" · ");
    if (g.platform) meta.prepend(plataformaIcone(plataformaInfo(g.code, g.platform)));
    const badges = document.createElement('span'); badges.className = 'badges'; fillBadges(badges, g);
    card.append(title, meta, badges); return card;
}
function showSpotlight(g) {
  spotlightGame = g;
  $("spotlight-title").textContent = g.name;
  $("spotlight-meta").textContent = [g.platform, g.local ? "Pronto neste PC" : g.downloadName ? "Disponível no Drive" : "Na sua biblioteca", g.tracking.genero, g.favorite ? "★ Favorito" : ""].filter(Boolean).join(" · ");
  $("spotlight-art").style.backgroundImage = g.cover ? `url(${JSON.stringify(g.cover)})` : "none";
  $("spotlight-open").textContent = "Ver jogo";
  const logo = $("spotlight-logo"), video = $("spotlight-video");
  logo.hidden = !g.media?.logo; if (g.media?.logo) logo.src = g.media.logo;
  const source = g.media?.video || "";
  if (video.dataset.source !== source) { video.pause(); video.removeAttribute('src'); video.dataset.source = source; if (source) video.src = source; }
  video.hidden = !source;
  if (source && !document.hidden && !document.querySelector('dialog[open]') && !matchMedia('(prefers-reduced-motion: reduce)').matches) video.play().catch(() => {});
}
function formatTime(seconds) { const minutes = Math.floor(seconds / 60); return minutes >= 60 ? `${Math.floor(minutes/60)} h ${minutes%60} min` : minutes ? `${minutes} min` : `${Math.floor(seconds)} s`; }
function shelfControls(row, title) {
  const controls = document.createElement('div'); controls.className = 'shelf-controls';
  const move = direction => row.scrollBy({left: direction * Math.max(160, row.clientWidth * .8), behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
  const previous = button('‹', () => move(-1)), next = button('›', () => move(1));
  previous.setAttribute('aria-label', `Voltar na fileira: ${title}`);
  next.setAttribute('aria-label', `Avançar na fileira: ${title}`);
  const update = () => {
    previous.disabled = row.scrollLeft <= 1;
    next.disabled = row.scrollLeft >= row.scrollWidth - row.clientWidth - 1;
  };
  row.addEventListener('scroll', update, {passive:true});
  row.addEventListener('wheel', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || Math.abs(event.deltaX) >= Math.abs(event.deltaY)) return;
    const delta = event.deltaY * (event.deltaMode === 1 ? 20 : event.deltaMode === 2 ? row.clientWidth : 1);
    const end = row.scrollWidth - row.clientWidth;
    if (delta > 0 ? row.scrollLeft >= end - 1 : row.scrollLeft <= 1) return;
    event.preventDefault(); row.scrollLeft = Math.max(0, Math.min(end, row.scrollLeft + delta)); update();
  }, {passive:false});
  // ResizeObserver reage também à troca de largura do painel, não só à janela.
  const observer = new ResizeObserver(update); observer.observe(row);
  shelfObservers.push(observer);
  requestAnimationFrame(update); controls.append(previous, next); return controls;
}
const shelfObservers = [];
$("spotlight-open").onclick = () => { if (spotlightGame) openGame(spotlightGame); };
function renderHome() {
  shelfObservers.splice(0).forEach(observer => observer.disconnect());
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
    const head = document.createElement('div'); head.className = 'shelf-heading';
    head.append(heading, shelfControls(row, title));
    section.append(head, row); box.append(section);
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
const WISHLIST_STORES = {steam: "Steam", psn: "PlayStation", xbox: "Xbox"};
function formatHours(hours) {
  const total = Math.round(hours), days = Math.floor(total / 24);
  return days ? `${days} ${days === 1 ? "dia" : "dias"} e ${total % 24} h (${total.toLocaleString("pt-BR")} h)` : `${total} h`;
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
    const card = $("gallery").querySelector(".game");
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
  if (g.platform) $("game-platform").prepend(plataformaIcone(plataformaInfo(g.code, g.platform)));
  fillBadges($('game-badges'), g);
  const textureCode = TEXTURE_SYSTEMS[g.code];
  $("textures-toggle").hidden = !textureCode; $("textures-fields").hidden = true; $("textures-toggle").setAttribute("aria-expanded", "false");
  if (textureCode) $("textures-link").href = '/?'+new URLSearchParams({textures:textureCode,game:g.name});
  $("detail-cover").hidden = !g.cover; if (g.cover) $("detail-cover").src = g.cover;
  $("spotlight-video").pause(); $("time-fields").hidden = true; $("media-fields").hidden = true;
  $("game-time").textContent = g.playtime?.seconds ? `${formatTime(g.playtime.seconds)} em ${g.playtime.sessions} sessão(ões) registrada(s).` : 'Ainda sem tempo registrado neste PC.';
  $("detail-video").pause(); $("detail-video").hidden = !g.media?.video;
  $("detail-video").removeAttribute('src'); if (g.media?.video) $("detail-video").src = g.media.video;
  $("saves-toggle").hidden = !g.code; $("saves-fields").hidden = true; $("saves-fields").replaceChildren(); $("saves-toggle").setAttribute("aria-expanded", "false");
  state.edits = {}; $("edit-fields").hidden = true; $("cover-fields").hidden = true; $("genre-list").hidden = true;
  $("edit-toggle").setAttribute("aria-expanded", "false"); $("cover-toggle").setAttribute("aria-expanded", "false");
  $("cover-toggle").hidden = !g.code && !g.id; $("edit-toggle").hidden = !g.code && !g.id;
  $("wishlist-actions").hidden = !g.wishlist;
  const light = state.light.some(x => x.code === g.code);
  $("rom-rename").hidden = !g.code || !(light ? g.cover : g.local); $("rom-delete").hidden = !g.code || !(light || g.local);
  $("decompose").hidden = !g.id || !!g.code || !!g.wishlist;
  $("rom-delete").dataset.confirm = ""; $("rom-delete").textContent = "🗑 Apagar ROM";
  $("rom-remove").hidden = !g.code || !(g.local || g.downloadName || g.driveName);
  // Desejado ainda não é seu: sem favorito, tempo, mídia ou progresso.
  for (const id of ["favorite", "time-toggle", "media-toggle", "progress-toggle", "game-time"]) $(id).hidden = !!g.wishlist;
  for (const id of ["wishlist-bought", "wishlist-remove"]) { $(id).dataset.confirm = ""; $(id).textContent = id === "wishlist-bought" ? "✅ Comprado" : "🗑 Tirar da lista"; }
  updateFavoriteButton(g); $("progress-fields").hidden = true; $("progress-toggle").setAttribute("aria-expanded", "false");
  report("", false, "detail-status"); renderTracking();
  $("download").hidden = !g.downloadName; $("download").textContent = "⬇ Baixar para este PC"; $("download").dataset.confirm = "";
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
    if (campos.plataforma && !g.wishlist) { g.platform = campos.plataforma; $("game-platform").textContent = g.platform; $("game-platform").prepend(plataformaIcone(plataformaInfo(g.code, g.platform))); }
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
  state.cover = {query: g.name, source: g.code ? "rom" : "sgdb"}; renderCoverSources(); searchCover(); renderCoverFlag();
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
// 🎨 Texturas no PC: pacotes do catálogo deste sistema com nome parecido; instalar baixa e
// extrai como na web (/api/texturas/instalar). Importar arquivo ou link continua na web.
const TEXTURE_SYSTEMS = {PS: "PS1", PS2: "PS2", NGC: "GC", WII: "WII", PSP: "PSP"};
const looseName = s => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/\(.*?\)|\[.*?\]/g, " ").replace(/[^a-z0-9]+/g, " ").trim();
// 2 = mesmo nome (sem região/pontuação) ou serial; 1 = um nome começa pelo outro; 0 = outro jogo.
function textureMatch(pack, g) {
  const a = looseName(pack.nome), b = looseName(g.name);
  if (!b) return 0;
  if (a === b || pack.id_jogo.toLowerCase() === (g.romName || "").toLowerCase().replace(/\.[^.]+$/, "")) return 2;
  return a.startsWith(b + " ") || b.startsWith(a + " ") ? 1 : 0;
}
$("textures-toggle").onclick = () => {
  const box = $("textures-fields"); box.hidden = !box.hidden; if (!box.hidden) closeOtherPanels("textures-toggle");
  $("textures-toggle").setAttribute("aria-expanded", String(!box.hidden));
  if (!box.hidden) renderTextures();
};
async function renderTextures(focusId) {
  const g = state.selected, list = $("textures-list"), system = TEXTURE_SYSTEMS[g.code];
  list.replaceChildren(hint("Procurando pacotes…"));
  try {
    const {pacotes} = await api("/api/texturas?alvo=pc");
    if (state.selected !== g) return;
    const scored = pacotes.filter(p => p.sistema === system).map(p => [p, textureMatch(p, g)]);
    const exact = scored.filter(([, m]) => m === 2).map(([p]) => p), similar = exact.length ? [] : scored.filter(([, m]) => m === 1).map(([p]) => p).slice(0, 6);
    const found = [...exact, ...similar].sort((a, b) => b.instalado - a.instalado || b.tem_rom - a.tem_rom);
    const gb = n => n >= 1073741824 ? `${(n/1073741824).toFixed(1)} GB` : `${Math.round(n/1048576)} MB`;
    list.replaceChildren(...(found.length ? found.map(p => {
      const row = document.createElement("div"); row.className = "save-row";
      row.append(Object.assign(document.createElement("span"), {textContent: `${p.nome} [${p.id_jogo}] · ${gb(p.tamanho)}${p.instalado ? ` · instalado (${p.arquivos} arquivos)` : ""}`}));
      const b = p.instalado ? confirmButton("🗑 Remover", "Confirmar: remover", () => removeTexture(p)) : confirmButton(`⬇ Instalar`, `Confirmar: baixar ${gb(p.tamanho)}`, () => installTexture(p, b));
      b.disabled = p.em_andamento; b.dataset.textureId = p.id; row.append(b); return row;
    }) : [hint("Nenhum pacote do catálogo com este nome. Veja as fontes da comunidade na interface completa.")]));
    if (similar.length) list.prepend(hint("Sem pacote com o mesmo nome. Estes têm nome parecido: confira antes de instalar."));
    if (focusId) list.querySelector(`[data-texture-id="${CSS.escape(focusId)}"]`)?.focus();
  } catch (e) { list.replaceChildren(hint(e.message)); }
}
async function installTexture(p, b) {
  b.disabled = true; report(`Baixando texturas de ${p.nome}… pode levar vários minutos.`, false, "detail-status");
  try {
    const result = await runJob("/api/texturas/instalar", {id: p.id, alvo: "pc"}, data => {
      if (data.type === "progress") b.textContent = data.status === "baixando" && data.total ? `Baixando ${Math.floor(100 * data.feito / data.total)}%` : data.status === "extraindo" ? "Extraindo…" : "Instalando…";
    });
    report(result.message || (result.ok ? "Texturas instaladas." : "A instalação não terminou."), !result.ok, "detail-status");
  } catch (e) { report(e.message, true, "detail-status"); }
  if ($("details").open && !$("textures-fields").hidden) renderTextures(p.id);
}
async function removeTexture(p) {
  try { const r = await api("/api/texturas/remover", {id: p.id, alvo: "pc"}); report(`${r.removidos} arquivos de textura removidos.`, false, "detail-status"); }
  catch (e) { report(e.message, true, "detail-status"); }
  renderTextures(p.id);
}
// Job do servidor (SSE): devolve o resultado final e repassa cada evento a `progress`.
async function runJob(url, body, progress = () => {}) {
  const {job} = await api(url, body);
  return new Promise(resolve => {
    const stream = new EventSource(`/api/fetch/stream?job=${encodeURIComponent(job)}`);
    const result = {ok: true, lines: [], message: ""};
    stream.onmessage = e => {
      const data = JSON.parse(e.data); progress(data);
      if (data.type === "log") result.lines.push(data.line);
      if (data.type === "system_done") { result.ok = data.result.ok !== false; result.message = data.result.message || ""; }
      if (data.type === "error") { result.ok = false; result.message = data.message || "falha"; }
      if (data.type === "job_done") { stream.close(); resolve(result); }
    };
    stream.onerror = () => { stream.close(); resolve({...result, ok: false, message: result.message || "A conexão com o servidor caiu; confira o resultado antes de repetir."}); };
  });
}
// ⚑ Marcar capa (só ROM leve, mesmo registro da galeria da web): marcada = errada/duplicada.
async function renderCoverFlag() {
  const g = state.selected, b = $("cover-flag");
  b.hidden = !state.light.some(s => s.code === g.code); if (b.hidden) return;
  try {
    const item = (await api(`/api/covers/${encodeURIComponent(g.code)}`)).find(x => x.label === coverLabel(g));
    if (state.selected !== g) return;
    g.flagged = !!(item?.flagged || item?.duplicated);
    b.textContent = g.flagged ? "⚑ Marcada · desmarcar" : "⚑ Marcar capa errada ou duplicada"; b.setAttribute("aria-pressed", String(g.flagged));
  } catch (_) { b.hidden = true; }
}
$("cover-flag").onclick = async () => {
  const g = state.selected; if (state.busy || !g) return;
  state.busy = true;
  try { await api(`/api/cover/${g.flagged ? "unflag" : "flag"}`, {code: g.code, label: coverLabel(g)}); report(g.flagged ? "Marca removida." : "Capa marcada; aparece em \"só marcadas\" na galeria da web.", false, "detail-status"); }
  catch (e) { report(e.message, true, "detail-status"); }
  finally { state.busy = false; }
  await renderCoverFlag(); $("cover-flag").focus();
};
// ➕ Desejados pela TV: PSN/Xbox só acrescentam (um nome por vez); Steam sincroniza com a
// lista pública (pode tirar quem saiu de lá), por isso pede confirmação.
async function wishlistJob(source, texto) {
  if (state.busy) return; state.busy = true; report(source === "steam" ? "Sincronizando a lista da Steam…" : `Adicionando "${texto}"…`);
  try {
    const result = await runJob("/api/wishlist/sync", {source, texto, apply: true});
    state.busy = false;
    await reloadSelection($(source === "steam" ? "wishlist-steam" : `wishlist-add-${source}`));
    const summary = result.lines.filter(l => /novo|saiu|erro|vazia/.test(l)).join(" · ");
    report(summary || result.message || "Lista atualizada.", !result.ok || /erro/.test(summary));
  } catch (e) { report(e.message, true); }
  finally { state.busy = false; }
}
for (const source of ["psn", "xbox"]) $(`wishlist-add-${source}`).onclick = () =>
  openTextEntry(`Adicionar aos Desejados (${WISHLIST_STORES[source]})`, "", name => { if (name) wishlistJob(source, name); });
$("wishlist-steam").onclick = () => {
  const b = $("wishlist-steam");
  if (!b.dataset.confirm) { b.dataset.confirm = "yes"; b.textContent = "Confirmar: sincronizar Steam"; report("A Steam manda a lista inteira: quem saiu de lá sai daqui também."); return; }
  b.dataset.confirm = ""; b.textContent = "🔄 Steam"; wishlistJob("steam", "");
};
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
  for (const [toggle, panel] of [["saves-toggle", "saves-fields"], ["edit-toggle", "edit-fields"], ["cover-toggle", "cover-fields"], ["textures-toggle", "textures-fields"]])
    if (toggle !== keep) { $(panel).hidden = true; $(toggle).setAttribute("aria-expanded", "false"); }
}
$("saves-toggle").onclick = () => {
  const box = $("saves-fields");
  box.hidden = !box.hidden; if (!box.hidden) closeOtherPanels("saves-toggle");
  $("saves-toggle").setAttribute("aria-expanded", String(!box.hidden));
  if (!box.hidden) renderSaves();
};
// 💾 Saves do jogo no PC (RetroArch, pasta do sistema e raiz antiga). Escrever sempre guarda
// uma cópia antes em Backups/Saves do modo TV (core/tv_saves.py); nada é apagado de vez.
const hint = text => Object.assign(document.createElement("p"), {className: "hint", textContent: text});
async function renderSaves(focusId) {
  const g = state.selected, box = $("saves-fields"); if (!g?.code) return;
  observedSaves.delete(badgeKey(g)); refreshBadges(g);
  if (!box.children.length) box.replaceChildren(hint("Procurando saves neste PC…"));
  const label = g.romName || g.name, query = new URLSearchParams({code: g.code, label});
  try {
    const [{items}, {items: copies}] = await Promise.all([api('/api/tv/saves?' + query), api('/api/tv/saves/backups?' + query)]);
    if (state.selected !== g || box.hidden) return;
    observedSaves.set(badgeKey(g), items.some(item => item.kind === 'save')); refreshBadges(g);
    const when = t => new Date(t * 1000).toLocaleString("pt-BR", {dateStyle: "short", timeStyle: "short"});
    const size = n => n >= 1048576 ? `${(n/1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(n/1024))} KB`;
    const rows = items.map(f => {
      const row = document.createElement("div"); row.className = "save-row";
      row.append(Object.assign(document.createElement("span"), {textContent: `${f.kind === "save" ? "💾" : "⏸"} ${f.name} · ${size(f.size)} · ${when(f.mtime)}${f.legado ? " · pasta antiga" : ""}`}));
      const del = confirmButton("Apagar", "Confirmar: apagar", () => saveAction("remove", {name: f.name, kind: f.kind, legado: f.legado}, `${f.name} apagado; a cópia ficou em Backups.`));
      del.dataset.saveId = `del:${f.kind}:${f.name}`; row.append(del); return row;
    });
    const copy = button("📦 Guardar cópia agora", () => saveAction("backup", {}, "Cópia guardada em Backups/Saves do modo TV."));
    copy.id = "saves-backup"; copy.disabled = !items.length;
    const restores = copies.slice(0, 8).map(c => {
      const row = document.createElement("div"); row.className = "save-row";
      row.append(Object.assign(document.createElement("span"), {textContent: `📦 ${c.stamp.replace(/^(\d{4})-(\d\d)-(\d\d)_(\d\d)(\d\d).*/, "$3/$2/$1 $4:$5")} · ${c.arquivos.length} arquivo(s)${c.motivo && c.motivo !== "cópia" ? " · " + c.motivo : ""}`}));
      const b = confirmButton("Restaurar", "Confirmar: restaurar", () => saveAction("restore", {stamp: c.stamp}, "Cópia restaurada. O que estava antes também foi guardado."));
      b.dataset.saveId = `res:${c.stamp}`; row.append(b); return row;
    });
    box.replaceChildren(...(rows.length ? rows : [hint("Nenhum save ou estado deste jogo no RetroArch do PC.")]),
      Object.assign(document.createElement("div"), {className: "actions"}),
      ...(restores.length ? [hint("Cópias guardadas (mais recentes primeiro):"), ...restores] : []),
      hint("Feche o emulador antes de mexer nos saves. Para trocar saves com o celular, use 💾 Saves no app Android."));
    box.querySelector(".actions").append(copy);
    if (focusId) (box.querySelector(`[data-save-id="${CSS.escape(focusId)}"]`) || copy).focus();
  } catch (error) { box.replaceChildren(hint(error.message)); }
}
// Ação que mexe em arquivo: primeiro toque pede confirmação, o segundo executa.
function confirmButton(label, confirmLabel, run) {
  const b = button(label, () => {
    if (!b.dataset.confirm) { b.dataset.confirm = "yes"; b.textContent = confirmLabel; return; }
    b.dataset.confirm = ""; b.textContent = label; run();
  }); return b;
}
async function saveAction(kind, extra, done) {
  const g = state.selected; if (state.busy || !g) return;
  state.busy = true; report("Gravando…", false, "detail-status");
  try { await api(`/api/tv/saves/${kind}`, {code: g.code, label: g.romName || g.name, ...extra}); report(done, false, "detail-status"); }
  catch (e) { report(e.message, true, "detail-status"); }
  finally { state.busy = false; }
  await renderSaves("saves-backup");
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
  const rating = $("rating"); rating.textContent = state.draft.nota == null ? "Sem nota" : notaEspecial(state.draft.nota) ? "11 ✦" : state.draft.nota.toFixed(1).replace(".", ",");
  rating.style.color = notaColor(state.draft.nota) || "";
}
function adjustRating(delta) {
  if (state.busy) return;
  state.draft.nota = notaPasso(state.draft.nota, delta); renderTracking();
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
  try { g.playtime = await api('/api/tv/playtime', {key:g.key,minutes:Number($("time-minutes").value)}); $("game-time").textContent = `${formatTime(g.playtime.seconds)} em ${g.playtime.sessions} sessão(ões) registrada(s).`; refreshBadges(g); report('Tempo registrado.',false,'detail-status'); await refreshHomeAfterPlay(); }
  catch(error) { report(error.message,true,'detail-status'); }
  finally { state.busy = false; }
};
for (const kind of ['logo','video']) $("media-"+kind).onchange = async event => {
  const file = event.target.files[0], g = state.selected; if (!file || !g?.key || state.busy) return;
  if (file.size > 64*1024*1024) { report('Escolha um arquivo de até 64 MB.',true,'detail-status'); return; }
  state.busy = true; report('Importando mídia…',false,'detail-status');
  try {
    csrf = (await api('/api/csrf')).token; // token atual, mesmo depois de o servidor reiniciar
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
    Object.assign(g.tracking, campos); render(); refreshBadges(g); report("Progresso salvo.", false, "detail-status");
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
    function finish(message, error) { stream.close(); state.download = null; report(message, error, "download-status"); b.disabled = false; b.hidden = !state.selected?.downloadName; b.textContent = "⬇ Baixar para este PC"; b.dataset.confirm = ""; if (state.selected === g) report(message, error, "detail-status"); }
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
  } catch (e) { state.download = null; b.disabled = false; b.dataset.confirm = ""; b.textContent = "⬇ Baixar para este PC"; report(e.message, true, "download-status"); }
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
      const b = button(options.length === 1 ? "▶ Jogar neste PC" : `▶ Jogar: ${option.name}`, () => startGame(g, option.name));
      b.disabled = !!option.error; b.dataset.unavailable = String(!!option.error); box.append(b);
    }
    const broken = options.filter(o => o.error);
    $("play-hint").textContent = broken.length ? broken.map(o => `${o.name}: ${o.error}`).join(" · ") : options.length ? "Escolha o disco/formato quando houver mais de uma opção." : "A ROM precisa estar completa no PC para abrir o emulador.";
    if ((broken.length || !options.length) && g.driveName) {
      g.downloadName = g.driveName;
      $("download").hidden = false; $("download").disabled = !!state.download;
      $("download").textContent = g.local ? "⬇ Completar download" : "⬇ Baixar para este PC";
      box.append(button("⬇ Baixar e jogar", () => { $("download").dataset.confirm = ""; downloadGame(true); $("download").focus(); }));
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
      box.append(button(`▶ Jogar neste PC · ${data.store === "steam" ? "Steam" : "Heroic"}`, () => startPcGame(g)));
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

// --- Renomear, apagar e decompor pela ficha --------------------------------
function describeCascade(c, verb) {
  const rom = {renomeado: "ROM renomeada", apagado: "ROM apagada", nao_encontrado: "ROM não encontrada", conflito: "já existe uma ROM com esse nome", ambiguo: "mais de um arquivo bate com esse nome; nada foi mexido"}[c.rom.status] || c.rom.status;
  return [rom, c.capa?.length ? "capa apagada" : "", c.saves.length ? `${c.saves.length} save(s) ${verb}` : "", c.states.length ? `${c.states.length} estado(s) ${verb}` : "",
    c.flat_skipped ? "saves da pasta antiga mantidos (nome usado em outro sistema)" : ""].filter(Boolean).join(" · ");
}
async function afterFileChange(message, error = false) {
  state.busy = false; closeGame(); await reloadSelection($("collections").querySelector('[aria-pressed="true"]'));
  report(message, error);
}
$("rom-rename").onclick = () => {
  const g = state.selected, label = coverLabel(g), light = state.light.some(x => x.code === g.code);
  openTextEntry("Novo nome do arquivo", label, async name => {
    if (!name || name === label || state.busy) return;
    state.busy = true; report("Renomeando ROM, capa e saves…", false, "detail-status");
    try {
      const r = await api(light ? "/api/cover/rename" : "/api/heavy/rename", light ? {code: g.code, label, new_label: name} : {code: g.code, old_label: label, new_label: name});
      // Mantém o cadastro da Biblioteca ligado ao nome novo (mesmo cuidado da web).
      if (g.id) await api("/api/library/edit", {id: g.id, campos: {nome: r.new_label}}).catch(() => {});
      await afterFileChange(`${label} → ${r.new_label}: ${describeCascade(r.cascade, "renomeado(s)")}`);
    } catch (e) { state.busy = false; report(`Não renomeou: ${e.message}`, true, "detail-status"); }
  });
};
$("rom-delete").onclick = async () => {
  const g = state.selected, b = $("rom-delete"), light = state.light.some(x => x.code === g.code); if (state.busy || !g) return;
  if (!b.dataset.confirm) { b.dataset.confirm = "yes"; b.textContent = "Confirmar: apagar de vez"; report(`Apagar "${g.name}": ROM${light ? ", capa" : ""} e saves deste jogo no PC. Não tem como desfazer; para guardar os saves antes, use 💾 Saves → Guardar cópia.`, true, "detail-status"); return; }
  state.busy = true;
  try { const r = await api(light ? "/api/cover/delete" : "/api/heavy/delete", {code: g.code, label: coverLabel(g)}); await afterFileChange(`${g.name}: ${describeCascade(r.cascade, "apagado(s)")}`); }
  catch (e) { state.busy = false; b.dataset.confirm = ""; b.textContent = "🗑 Apagar ROM"; report(e.message, true, "detail-status"); }
};
// --- 🗑 Remover…: deste PC, do Drive (lixeira) ou dos dois, sempre com prévia (core/removal.py) ---
const fmtBytes = n => n >= 1e9 ? `${(n / 1e9).toFixed(1)} GB` : n >= 1e6 ? `${(n / 1e6).toFixed(0)} MB` : `${Math.max(1, Math.round(n / 1e3))} KB`;
$("rom-remove").onclick = () => {
  const g = state.selected; if (!g?.code) return; closeGame();
  const entry = g.driveName || g.romName;
  const scopes = [["local", "Só deste PC (continua no Drive)"], ["drive", "Só do Drive (vai para a lixeira)"], ["both", "Dos dois"]];
  openTool(`🗑 Remover: ${g.name}`, async body => {
    let scope = g.local ? "local" : "drive", revision = 0;
    const draw = async () => {
      const request = ++revision, chosen = scope;
      const buttons = scopes.map(([key, label]) => button(label, () => { scope = key; draw(); }, scope === key));
      body.replaceChildren(hint("Saves, estados, texturas, capa, cadastro, nota e tempo ficam. Tudo o que sai vai para a lixeira (PC: do sistema; Drive: recuperável por 30 dias)."), actions(...buttons), hint("Conferindo o que seria removido…"));
      let plan;
      try { plan = await api(`/api/storage/removal-plan?${new URLSearchParams({scope, code: g.code, entry})}`); }
      catch (e) { if (request !== revision || !body.isConnected) return; body.append(hint(e.message)); return toolStatus(e.message, true); }
      if (request !== revision || !body.isConnected) return;
      body.replaceChildren(hint("Saves, estados, texturas, capa, cadastro, nota e tempo ficam. Tudo o que sai vai para a lixeira (PC: do sistema; Drive: recuperável por 30 dias)."), actions(...buttons));
      if (plan.local.length) body.append(heading(`Neste PC (${plan.local.length})`), ...plan.local.map(f => row(f)));
      if (plan.drive.length) body.append(heading(`No Drive (${plan.drive.length} · ${fmtBytes(plan.bytes_drive)})`), ...plan.drive.map(f => row(f.path.split("/").slice(-1)[0], Object.assign(document.createElement("small"), {textContent: fmtBytes(f.size)}))));
      if (plan.preserved.length) body.append(hint(`Preservados (usados por outro jogo): ${plan.preserved.length}.`));
      for (const w of plan.warnings) body.append(hint("⚠ " + w));
      for (const b of plan.blocked) body.append(hint("⛔ " + b));
      if (!plan.local.length && !plan.drive.length && !plan.blocked.length) body.append(hint("Nada a remover nesta opção."));
      if (!plan.blocked.length && (plan.local.length || plan.drive.length)) {
        body.append(actions(confirmButton("Remover", "Confirmar: " + plan.confirm_text, async () => {
          try {
            const r = await api("/api/storage/removal-apply", {scope: chosen, code: g.code, entry: plan.entry, token: plan.token, confirm: plan.confirm_text});
            const failed = r.results.filter(x => !x.ok);
            toolStatus(failed.length ? `${r.results.length - failed.length} removido(s); ${failed.length} falhou(aram): ${failed[0].error}` : `Pronto: ${r.results.length} arquivo(s) para a lixeira. ${r.recover}`, failed.length > 0);
            await load(state.kind, state.code);
          } catch (e) { toolStatus(e.message, true); }
        })));
      }
    };
    await draw();
  });
};

$("decompose").onclick = () => {
  const g = state.selected; closeGame();
  let names = [];
  openTool(`⧉ Decompor: ${g.name}`, async body => {
    const draw = () => body.replaceChildren(hint("Os jogos que a coletânea contém (sugestão lida da pasta do Switch; corrija se precisar). A pasta fica vinculada a um deles, então a próxima varredura não recria a coletânea."),
      ...names.map((name, i) => row(name, button("Editar", () => openTextEntry("Nome do jogo", name, v => { if (v) names[i] = v; draw(); })), button("Tirar", () => { names.splice(i, 1); draw(); }))),
      actions(button("➕ Jogo", () => openTextEntry("Nome do jogo", "", v => { if (v) names.push(v); draw(); })),
        confirmButton("Decompor", "Confirmar: decompor", async () => {
          if (!names.length) return toolStatus("Informe ao menos um jogo.", true);
          try { const r = await api("/api/library/decompor", {id: g.id, nomes: names}); toolStatus(`${r.criados} jogo(s) criado(s), ${r.reaproveitados} reaproveitado(s); vínculo em "${r.vinculo_em}".`); }
          catch (e) { toolStatus(e.message, true); }
        })));
    body.replaceChildren(hint("Lendo a pasta da coletânea…"));
    try { const r = await api(`/api/switch/colecao?${new URLSearchParams({nome: g.name})}`); names = r.sugestoes || []; if (r.aviso) toolStatus(r.aviso); } catch (e) { toolStatus(e.message, true); }
    draw();
  });
};

// --- 🛠 Ferramentas: o que antes só a interface completa fazia ------------------
let toolReturnFocus;
const row = (text, ...buttons) => { const r = document.createElement("div"); r.className = "save-row"; r.append(Object.assign(document.createElement("span"), {textContent: text}), ...buttons); return r; };
const actions = (...buttons) => { const a = document.createElement("div"); a.className = "actions"; a.append(...buttons); return a; };
const heading = text => Object.assign(document.createElement("h3"), {textContent: text});
function toolStatus(message, error = false) { report(message, error, "tool-status"); }
function openTool(title, render) {
  toolReturnFocus = document.activeElement; $("tool-title").textContent = title;
  // Corpo novo a cada abertura: resposta atrasada da ferramenta anterior cai num elemento descartado.
  const body = Object.assign(document.createElement("div"), {id: "tool-body"}); $("tool-body").replaceWith(body);
  $("tool-log").hidden = true; $("tool-log").textContent = ""; toolStatus("");
  $("tool-dialog").showModal(); $("tool-close").focus();
  Promise.resolve(render(body)).catch(e => toolStatus(e.message, true)).then(() => { if (document.activeElement === $("tool-close")) body.querySelector("button")?.focus(); });
}
function closeTool() { $("tool-dialog").close(); (toolReturnFocus?.isConnected ? toolReturnFocus : $("collections").querySelector("button"))?.focus(); }
$("tool-close").onclick = closeTool;
$("tool-dialog").addEventListener("cancel", e => { e.preventDefault(); closeTool(); });
// Escolha entre opções como botões (o controle não abre <select>).
function choice(options, current, pick) {
  const box = document.createElement("div"); box.className = "actions choice";
  const draw = value => box.replaceChildren(...options.map(([v, label]) => button(label, () => { pick(v); draw(v); box.querySelector('[aria-pressed="true"]')?.focus(); }, v === value)));
  draw(current); return box;
}
async function toolJob(url, body, done) {
  const log = $("tool-log"); log.hidden = false; log.textContent = "";
  toolStatus("Rodando…"); $("tool-status").scrollIntoView({block: "nearest"});
  try {
    const result = await runJob(url, body, data => {
      if (data.type === "log") { log.textContent += data.line + "\n"; log.scrollTop = log.scrollHeight; }
      if (data.type === "progress" && data.status) toolStatus(`${data.status}${data.total ? ` ${Math.floor(100 * data.feito / data.total)}%` : ""}…`);
    });
    toolStatus(result.message || (result.ok ? "Concluído." : "Terminou com erro; veja o registro."), !result.ok);
    if (done) await done(result);
    return result;
  } catch (e) { toolStatus(e.message, true); }
}
function renderTools() {
  const tools = [
    ["🗂", "Organizar ROMs novas", "Move o que chegou na pasta de organizar para o sistema certo", toolOrganize],
    ["💾", "Memory cards PS1/PS2", "Exportar, transferir, importar e apagar saves dos cards", toolMemcards],
    ["📱", "Saves do celular (PSP)", "Baixa para o PC os saves do PPSSPP do celular, pelo cabo", toolPhoneSaves],
    ["☁", "Saves na nuvem", "Comparar, sincronizar e escolher versões em conflito", toolCloudSaves],
    ["🎨", "Texturas HD", "Catálogo completo, no PC ou no celular, e importar arquivo ou link", toolTextures],
    ["📚", "Biblioteca", "Atualizar Heroic, Steam e Switch, buscar capas e adicionar jogos", toolLibrary],
    ["🖼", "Capas dos sistemas", "Buscar capas que faltam nas ROMs leves e pesadas", toolCovers],
    ["🛠", "Manutenção", "Backups, nomes, playlists e sincronização de saves", toolMaintenance],
    ["⚙", "Configurações", "Pastas do PC e do celular usadas pelo PyRetro", toolSettings],
    ["🩺", "Diagnóstico", "Confere pastas e programas; relatório sem dados privados", toolDiagnostics],
  ];
  $("gallery").replaceChildren(...tools.map(([symbol, title, text, open]) => {
    const card = button("", () => openTool(`${symbol} ${title}`, open)); card.className = "game system-card stat-card";
    card.append(Object.assign(document.createElement("span"), {className: "system-symbol", textContent: symbol}),
      Object.assign(document.createElement("strong"), {textContent: title}), Object.assign(document.createElement("small"), {textContent: text}));
    return card;
  }));
  report("Ferramentas de organização e manutenção. Ações que mexem em arquivos pedem confirmação.");
}
async function toolCloudSaves(body) {
  let revision = 0, busy = false, showAll = false;
  const draw = async () => {
    const request = ++revision;
    body.replaceChildren(hint("Comparando saves com a nuvem…"));
    try {
      const status = await api("/api/cloud/saves/status" + (showAll ? "?all=1" : ""));
      if (request !== revision || !body.isConnected) return;
      if (!status.enabled) { body.replaceChildren(hint("Configure a nuvem para sincronizar saves.")); return; }
      body.replaceChildren(hint("Feche os emuladores. Saves são compartilhados; estados ficam separados por aparelho. Conflitos exigem escolha e a outra versão fica no histórico."),hint("Esquecer este save retira apenas o arquivo escolhido do uso em todos os aparelhos na próxima sincronização. Cópias antigas ficam no histórico; saves de outros jogos ficam."));
      const perform = async (url, data) => {
        if (busy) return; busy = true; body.querySelectorAll("button").forEach(b => b.disabled = true);
        try {
          const result = await api(url, data);
          if (result.ok === false || result.errors?.length) throw new Error(result.error || result.errors.map(e => `${e.path}: ${e.error}`).join("; "));
          if (!body.isConnected) return;
          toolStatus(result.conflicts?.length ? `${result.conflicts.length} conflito(s) ainda precisam de escolha.` : "Operação concluída. Versões anteriores preservadas.");
          await draw();
        } catch (e) { if (body.isConnected) { toolStatus(e.message, true); body.querySelectorAll("button").forEach(b => b.disabled = false); } }
        finally { busy = false; }
      };
      body.append(actions(button("Comparar novamente", draw), button(showAll ? "Mostrar só pendentes" : "Ver também saves em dia", () => { showAll = !showAll; draw(); }), button("Sincronizar sem resolver conflitos", () => perform("/api/cloud/saves/sync", {}))));
      if (!status.items?.length) body.append(hint("Saves em dia com a nuvem."));
      for (const item of status.items || []) {
        const box = document.createElement("section"); box.append(heading(item.path), hint(`${item.group || "saves"} · ${item.action === "conflict" ? "Conflito" : item.action}`));
        if (item.action === "conflict") {
          const choose = (choice, sha) => perform("/api/cloud/saves/resolve", {path: item.path, group: item.group || "saves", choice, ...(sha ? {sha} : {})});
          if (item.local) box.append(confirmButton("Manter deste PC", "Confirmar: manter deste PC", () => choose("local")));
          for (const [sha, devices] of Object.entries(item.heads || {})) box.append(confirmButton(`${item.deletedHeads?.includes(sha) ? "Usar exclusão confirmada" : "Usar da nuvem"}: ${devices.join(", ")} · ${sha.slice(0, 12)}`, "Confirmar: usar esta versão", () => choose("remote", sha)));
        }
        if (item.action !== "forget") box.append(confirmButton("Esquecer este save…", `Esquecer este save: ${item.path}`, () => perform("/api/cloud/saves/forget", {path:item.path, group:item.group || "saves", expectedLocal:item.local ?? null, expectedHeads:Object.keys(item.heads || {}), confirm:`Esquecer este save: ${item.path}`})));
        body.append(box);
      }
    } catch (e) { if (request === revision && body.isConnected) { body.replaceChildren(hint(e.message), button("Tentar novamente", draw));toolStatus(e.message, true); } }
  };
  await draw();
}
async function toolOrganize(body) {
  body.replaceChildren(hint("Lendo a pasta de organizar e os Downloads…"));
  const {staging_dir, downloads_dir, items} = await api("/api/organize/pending");
  const gb = n => n >= 1073741824 ? `${(n/1073741824).toFixed(1)} GB` : `${Math.max(1, Math.round(n/1048576))} MB`;
  const label = i => (i.member ? `${i.name} › ${i.member}` : i.name);
  body.replaceChildren(hint(`Origens: ROMs/${staging_dir}/ e ${downloads_dir}. Escolha o sistema de cada ROM: o nome sai limpo, a capa vem da imagem ao lado ou das bases de ROM e o gênero é preenchido. Se já existir, a antiga vai para a lixeira.`),
    ...(items.length ? items.map(item => {
      const r = row(`${item.source === "downloads" ? "⬇ " : ""}${label(item)} · ${gb(item.size)}${item.status !== "pronto" ? " · " + item.status : ` → ${item.final}`}${item.cover_image ? " · 🖼 " + item.cover_image : ""}${item.exists_in.length ? " · já existe em " + item.exists_in.join(", ") + " (substitui)" : ""}`);
      if (item.status === "pronto") for (const c of item.candidates) r.append(confirmButton(`→ ${c.code}`, `Mover para ${c.code}?`, async () => {
        toolStatus(`Organizando ${item.final}… (capa e gênero podem levar um pouco)`);
        try {
          const d = await api("/api/organize/move", {id: item.id, code: c.code});
          toolStatus(`${d.message} · capa: ${d.cover || "não achada"} · gênero: ${d.genero || "não achado"}`);
        } catch (e) { toolStatus(e.message, true); }
        await toolOrganize(body);
      }));
      if (item.status !== "baixando") r.append(confirmButton("Descartar", "Confirmar: para a lixeira", async () => {
        try { await api("/api/organize/discard", {id: item.id}); toolStatus(`${item.name} foi para a lixeira.`); } catch (e) { toolStatus(e.message, true); }
        await toolOrganize(body);
      }));
      return r;
    }) : [hint("Nada esperando organização.")]));
}
async function toolMemcards(body) {
  body.replaceChildren(hint("Lendo os memory cards…"));
  const cards = await api("/api/memcards");
  const lists = Object.fromEntries(await Promise.all(cards.filter(c => c.tool_ok).map(async c => [c.key, await api(`/api/memcards/list/${encodeURIComponent(c.key)}`).then(d => d.items, e => ({error: e.message}))])));
  const refresh = () => toolMemcards(body);
  const sections = cards.map(card => {
    const box = document.createElement("section"); box.className = "panel";
    const file = Object.assign(document.createElement("input"), {type: "file", hidden: true});
    file.onchange = () => { const f = file.files[0]; if (!f) return; const reader = new FileReader();
      reader.onload = async () => { try { await api("/api/memcards/import", {key: card.key, filename: f.name, data: reader.result.split(",")[1]}); toolStatus(`Importado: ${f.name}`); refresh(); } catch (e) { toolStatus(e.message, true); } };
      reader.readAsDataURL(f); };
    box.append(heading(`${card.console} · ${card.label}`), file, actions(button("📥 Importar save (arquivo)", () => file.click()),
      confirmButton("✕ Tirar da lista", "Confirmar: só desregistrar", async () => { try { await api("/api/memcards/remove", {console: card.console.toLowerCase(), label: card.label}); refresh(); } catch (e) { toolStatus(e.message, true); } })));
    const items = lists[card.key];
    if (!card.tool_ok) box.append(hint(`Ferramenta ${card.console === "PS1" ? "ps1vmc-tool" : "ps2vmc-tool"} não encontrada no PATH.`));
    else if (!items || items.error) box.append(hint(`Não foi possível ler: ${items?.error || "falha"}`));
    else {
      const saves = items.filter(i => i.type !== "link");
      if (!saves.length) box.append(hint("Card vazio."));
      for (const item of saves) {
        const others = cards.filter(c => c.console === card.console && c.key !== card.key && c.tool_ok);
        box.append(row(`${item.name || `(desconhecido · ${item.raw_name})`} · ${item.type === "dir" ? `${item.size} arquivo(s)` : `${Math.round(item.size / 1024)} KB`}`,
          button("⬇ Exportar", async () => { try { const d = await api("/api/memcards/export", {key: card.key, item}); toolStatus(`Exportado: ${d.file}`); } catch (e) { toolStatus(e.message, true); } }),
          ...others.map(o => confirmButton(`↔ ${o.label}`, `Mover para ${o.label}?`, async () => { try { await api("/api/memcards/transfer", {src_key: card.key, dest_key: o.key, item}); toolStatus(`Transferido para ${o.label}.`); refresh(); } catch (e) { toolStatus(e.message, true); } })),
          confirmButton("🗑 Apagar", "Confirmar: apagar de vez", async () => { try { await api("/api/memcards/delete", {key: card.key, item}); toolStatus(`Apagado: ${item.name || item.raw_name}`); refresh(); } catch (e) { toolStatus(e.message, true); } })));
      }
    }
    return box;
  });
  const add = {console: "ps1", label: "", path: "", mode: "open"};
  const addBox = document.createElement("section"); addBox.className = "panel";
  const drawAdd = () => addBox.replaceChildren(heading("Adicionar card"),
    choice([["ps1", "PS1"], ["ps2", "PS2"]], add.console, v => add.console = v),
    actions(button(`Nome: ${add.label || "—"}`, () => openTextEntry("Nome do card (ex.: Slot 3)", add.label, v => { add.label = v; drawAdd(); })),
      button(`Arquivo: ${add.path || "—"}`, () => openTextEntry("Caminho do arquivo do card (~/Drive/Jogos/…)", add.path, v => { add.path = v; drawAdd(); }))),
    choice([["open", "Card existente"], ["create", "Criar em branco"]], add.mode, v => add.mode = v),
    actions(button("Adicionar card", async () => {
      if (!add.label || !add.path) return toolStatus("Informe o nome e o arquivo do card.", true);
      try { await api("/api/memcards/add", add); toolStatus(`Card adicionado: ${add.label}`); refresh(); } catch (e) { toolStatus(e.message, true); }
    })));
  drawAdd();
  body.replaceChildren(...(sections.length ? sections : [hint("Nenhum card configurado.")]), addBox);
}
async function toolPhoneSaves(body) {
  body.replaceChildren(hint("Lendo os saves do PPSSPP no celular…"));
  const data = await api("/api/emu_saves/list/PSP");
  if (!data.android_ok) return body.replaceChildren(hint("Celular não conectado pelo cabo (adb). Conecte e abra de novo."), actions(button("Tentar de novo", () => toolPhoneSaves(body))));
  body.replaceChildren(hint("Saves do PSP no celular. “Baixar” copia para o PC; nada é apagado no celular."),
    ...(data.items.length ? data.items.map(item => {
      const r = row(`${item.name || `(desconhecido · ${item.raw_name})`} · ${item.in_pc ? "já no PC" : "só no celular"}`);
      if (!item.in_pc) r.append(button("⬇ Baixar para o PC", async () => { try { const d = await api("/api/emu_saves/pull", {emu: "PSP", item}); toolStatus(`Baixado: ${d.file}`); toolPhoneSaves(body); } catch (e) { toolStatus(e.message, true); } }));
      return r;
    }) : [hint("Nada encontrado no celular.")]));
}
const texturesTool = {alvo: "pc", termo: "", sistema: "", meus: true, imp: {sistema: "PS2", id_jogo: "", arquivo: "", url: ""}};
async function toolTextures(body, focusId) {
  const t = texturesTool;
  body.replaceChildren(hint("Carregando o catálogo de texturas…"));
  const data = await api(`/api/texturas?alvo=${t.alvo}`);
  const gb = n => n >= 1073741824 ? `${(n/1073741824).toFixed(1)} GB` : `${Math.round(n/1048576)} MB`;
  const again = id => toolTextures(body, id);
  const termo = looseName(t.termo);
  const found = data.pacotes.filter(p => (!t.sistema || p.sistema === t.sistema) && (!t.meus || p.tem_rom || p.instalado) && (!termo || looseName(p.nome).includes(termo) || p.id_jogo.toLowerCase().includes(t.termo.toLowerCase())))
    .sort((a, b) => b.instalado - a.instalado || b.tem_rom - a.tem_rom || a.nome.localeCompare(b.nome));
  const list = found.slice(0, 30).map(p => {
    const b = p.instalado ? confirmButton("🗑 Remover", "Confirmar: remover", async () => { try { const r = await api("/api/texturas/remover", {id: p.id, alvo: t.alvo}); toolStatus(`${r.removidos} arquivos removidos.`); } catch (e) { toolStatus(e.message, true); } again(p.id); })
      : confirmButton("⬇ Instalar", `Confirmar: baixar ${gb(p.tamanho)}`, async () => { b.disabled = true; await toolJob("/api/texturas/instalar", {id: p.id, alvo: t.alvo}); again(p.id); });
    b.disabled = p.em_andamento; b.dataset.textureId = p.id;
    return row(`${p.sistema} · ${p.nome} [${p.id_jogo}] · ${gb(p.tamanho)}${p.instalado ? ` · instalado (${p.arquivos})` : p.tem_rom ? " · você tem a ROM" : ""}`, b);
  });
  const imp = t.imp, impBox = document.createElement("section"); impBox.className = "panel";
  const importBody = extra => ({alvo: t.alvo, sistema: imp.sistema, id_jogo: imp.id_jogo, ...extra});
  const drawImport = () => impBox.replaceChildren(heading("Importar um pacote baixado"),
    hint(`Arquivo .zip/.7z/.rar na pasta ${data.importar_dir}, ou um link direto (use só fontes em que confia; o SHA-1 aparece no fim).`),
    choice(data.sistemas.map(x => [x, x]), imp.sistema, v => imp.sistema = v),
    actions(button(`ID do jogo: ${imp.id_jogo || "—"}`, () => openTextEntry("ID do jogo (SLUS-21065, ULUS10307…)", imp.id_jogo, v => { imp.id_jogo = v.toUpperCase(); drawImport(); })),
      button(`Arquivo: ${imp.arquivo || "—"}`, () => openTextEntry("Nome do arquivo na pasta de importação", imp.arquivo, v => { imp.arquivo = v; drawImport(); })),
      button(`Link: ${imp.url || "—"}`, () => openTextEntry("Link direto (https://…)", imp.url, v => { imp.url = v; drawImport(); }))),
    actions(confirmButton("Importar arquivo", "Confirmar: importar", () => imp.id_jogo && imp.arquivo ? toolJob("/api/texturas/instalar", importBody({arquivo: imp.arquivo})) : toolStatus("Informe o ID e o arquivo.", true)),
      confirmButton("Baixar do link", "Confirmar: baixar o link", () => imp.id_jogo && imp.url ? toolJob("/api/texturas/instalar", importBody({url: imp.url})) : toolStatus("Informe o ID e o link.", true)),
      confirmButton("Remover importado", "Confirmar: remover", async () => { try { const r = await api("/api/texturas/remover", importBody({})); toolStatus(`${r.removidos} arquivos removidos.`); } catch (e) { toolStatus(e.message, true); } })));
  drawImport();
  body.replaceChildren(
    choice([["pc", "Instalar no PC"], ["celular", `Instalar no celular${data.celular_ok === false ? " (desconectado)" : ""}`]], t.alvo, v => { t.alvo = v; if (!data.sistemas.includes(t.sistema)) t.sistema = ""; again(); }),
    choice([["", "Todos"], ...data.sistemas.map(x => [x, x])], t.sistema, v => { t.sistema = v; again(); }),
    actions(button(`Busca: ${t.termo || "—"}`, () => openTextEntry("Buscar pacote", t.termo, v => { t.termo = v; again(); })),
      button(t.meus ? "Só jogos que tenho ✓" : "Só jogos que tenho", () => { t.meus = !t.meus; again(); }, t.meus)),
    ...(list.length ? list : [hint("Nenhum pacote neste filtro.")]),
    ...(found.length > list.length ? [hint(`Mostrando ${list.length} de ${found.length}; use a busca para achar o resto.`)] : []),
    impBox);
  if (focusId) body.querySelector(`[data-texture-id="${CSS.escape(focusId)}"]`)?.focus();
}
// Simular mostra o que aconteceria; Aplicar grava (pede confirmação).
function jobRow(title, url, {apply = true, extra} = {}) {
  const box = document.createElement("section"); box.className = "panel";
  const go = applyIt => toolJob(typeof url === "function" ? url(applyIt) : url, {});
  box.append(heading(title), ...(extra ? [extra] : []), actions(...(apply ? [button("Simular", () => go(false)), confirmButton("Aplicar", "Confirmar: aplicar", () => go(true))] : [confirmButton("Rodar", "Confirmar: rodar", () => go(true))])));
  return box;
}
const q = (base, params, applyIt) => `${base}?${new URLSearchParams({...params, apply: applyIt ? "1" : "0"})}`;
async function toolLibrary(body) {
  const add = {preset: "Nintendo Switch|switch", plataforma: "", fonte: "", games: []};
  const addBox = document.createElement("section"); addBox.className = "panel";
  const drawAdd = () => addBox.replaceChildren(heading("Adicionar jogos à Biblioteca"),
    choice([["Nintendo Switch|switch", "Switch"], ["PlayStation 4|psn", "PS4 digital"], ["PlayStation 4|psn:fisico", "PS4 físico"], ["PlayStation 3|psn", "PS3 digital"], ["PlayStation 3|psn:fisico", "PS3 físico"], ["", "Outra"]], add.preset, v => { add.preset = v; drawAdd(); }),
    ...(add.preset ? [] : [actions(button(`Plataforma: ${add.plataforma || "—"}`, () => openTextEntry("Plataforma (ex.: Xbox)", add.plataforma, v => { add.plataforma = v; drawAdd(); })),
      button(`Fonte: ${add.fonte || "—"}`, () => openTextEntry("Fonte (ex.: xbox)", add.fonte, v => { add.fonte = v; drawAdd(); })))]),
    ...add.games.map((g, i) => row(g, button("Tirar", () => { add.games.splice(i, 1); drawAdd(); }))),
    actions(button("➕ Jogo", () => openTextEntry("Nome do jogo", "", v => { if (v) add.games.push(v); drawAdd(); })),
      button("Simular", () => send(false)), confirmButton("Adicionar", "Confirmar: adicionar", () => send(true))));
  const send = applyIt => {
    const [plataforma, fonte] = add.preset ? add.preset.split("|") : [add.plataforma, add.fonte];
    if (!add.games.length || !plataforma || !fonte) return toolStatus("Informe a plataforma, a fonte e ao menos um jogo.", true);
    return toolJob("/api/library/add", {games: add.games.join("\n"), plataforma, fonte, apply: applyIt});
  };
  drawAdd();
  body.replaceChildren(jobRow("Atualizar do Heroic", a => q("/api/library/refresh", {source: "heroic"}, a)), jobRow("Atualizar da Steam", a => q("/api/library/refresh", {source: "steam"}, a)),
    jobRow("Atualizar do Switch (pastas do Drive)", a => q("/api/library/refresh", {source: "switch"}, a)), jobRow("Buscar capas que faltam na Biblioteca", a => q("/api/library/fetch_covers", {}, a)), addBox);
}
async function toolCovers(body) {
  const light = {code: state.light[0]?.code || "", fallback: "0"}, heavy = {code: state.systems[0]?.code || ""};
  body.replaceChildren(
    jobRow("ROMs leves: buscar capas", a => `/api/fetch/${encodeURIComponent(light.code)}?${new URLSearchParams({apply: a ? "1" : "0", fallback: light.fallback})}`, {extra: actions(
      choice(state.light.map(s => [s.code, s.code]), light.code, v => light.code = v), choice([["0", "Normal"], ["launchbox", "LaunchBox"], ["screenscraper", "ScreenScraper"]], light.fallback, v => light.fallback = v))}),
    jobRow("ROMs pesadas: atualizar o catálogo do Drive", "/api/heavy_catalog", {apply: false}),
    jobRow("ROMs pesadas: buscar capas", a => q("/api/heavy/fetch_covers", {code: heavy.code}, a), {extra: choice(state.systems.map(s => [s.code, s.code]), heavy.code, v => heavy.code = v)}),
    jobRow("Capas do PyRetro no DuckStation, PCSX2 e Dolphin", a => q("/api/capas_emuladores", {}, a)));
}
async function toolMaintenance(body) {
  const o = {config: "all", sanitize: "all", playlist: state.light[0]?.code || "", playlistTarget: "all", sync: "all"};
  const sources = await api("/api/emu_sync/sources").catch(() => []);
  const targets = [["all", "PC + Android"], ["pc", "Só PC"], ["android", "Só Android"]];
  body.replaceChildren(
    jobRow("Backup de configs do RetroArch", a => q("/api/backup_config", {target: o.config}, a), {extra: choice(targets, o.config, v => o.config = v)}),
    jobRow("Backup de saves (Dolphin GameCube/Wii)", a => q("/api/backup_saves", {}, a)),
    jobRow("Sanitizar nomes (remove & : *)", a => q("/api/sanitize_names", {target: o.sanitize}, a), {extra: choice([["all", "Capas + ROMs"], ["capas", "Só Capas"], ["roms", "Só ROMs"]], o.sanitize, v => o.sanitize = v)}),
    jobRow("Reconstruir playlist do RetroArch", a => q(`/api/rebuild_playlist/${encodeURIComponent(o.playlist)}`, {target: o.playlistTarget}, a), {extra: actions(choice(state.light.map(s => [s.code, s.code]), o.playlist, v => o.playlist = v), choice(targets, o.playlistTarget, v => o.playlistTarget = v))}),
    jobRow("Sincronizar saves de emulador (PC/Drive/Android)", a => q("/api/emu_sync", {source: o.sync}, a), {extra: choice([["all", "Todos"], ...sources.map(x => [x.code, x.nome])], o.sync, v => o.sync = v)}));
}
// Relatório do Codex (core/diagnostics.py): só presença de pastas e programas, sem caminhos.
async function toolDiagnostics(body) {
  body.replaceChildren(hint("Conferindo…"));
  const r = await api("/api/diagnostics");
  const icon = {present: "✓", missing: "✗", unavailable: "?"};
  body.replaceChildren(
    ...r.checks.map(c => row(`${icon[c.status] || "?"} ${c.id}${c.action ? ` · ${c.action}` : ""}`)),
    hint(`Jogo aberto pelo PyRetro: ${{idle: "nenhum", running: "sim", starting: "abrindo", error: "erro na última sessão"}[r.play_state] || "desconhecido"}.`),
    ...r.limits.map(hint), hint(r.privacy),
    actions(button("Atualizar", () => toolDiagnostics(body))),
    Object.assign(document.createElement("p"), {className: "hint", innerHTML: 'Versão para copiar e enviar: <a href="/diagnostics">/diagnostics</a>.'}));
}
async function toolSettings(body) {
  const cfg = await api("/api/settings"), changed = {pc: {}, android: {}};
  const draw = () => body.replaceChildren(hint("Pastas usadas pelo PyRetro. Só os campos alterados mudam ao salvar."),
    ...["pc", "android"].flatMap(section => [heading(section === "pc" ? "PC" : "Android"), ...Object.entries(cfg[section] || {}).map(([key, value]) => {
      const now = changed[section][key] ?? value;
      return button(`${key in changed[section] ? "• " : ""}${key}: ${now}`, () => openTextEntry(key, now, v => { if (v !== value) changed[section][key] = v; else delete changed[section][key]; draw(); }));
    })]),
    actions(confirmButton("Salvar", "Confirmar: salvar", async () => {
      try { await api("/api/settings", {pc: {...cfg.pc, ...changed.pc}, android: {...cfg.android, ...changed.android}}); toolStatus("Configurações salvas."); Object.assign(cfg.pc, changed.pc); Object.assign(cfg.android, changed.android); changed.pc = {}; changed.android = {}; draw(); }
      catch (e) { toolStatus(e.message, true); }
    })));
  draw();
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
  else if (key === "back") { if ($("search-dialog").open) closeSearch(); else if ($("tool-dialog").open) closeTool(); else if ($("settings-dialog").open) closeSettings(); else if ($("details").open) closeGame(); else if (state.kind !== "home") load("home"); else $("collections").querySelector("button")?.focus(); }
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
    const family = padFamily(pad.id); if (family !== glifoDetectado) { glifoDetectado = family; applyGlyphs(); }
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

$("hints-more").onclick = () => { const open = $("hints-extra").hidden; $("hints-extra").hidden = !open; $("hints-more").setAttribute("aria-expanded", String(open)); $("hints-more").textContent = open ? "Menos atalhos" : "Mais atalhos"; };
$("filters-toggle").onclick = () => {
  filtrosRecolhidos = !filtrosRecolhidos;
  try { localStorage.setItem("pyretro-filtros", filtrosRecolhidos ? "recolhido" : "aberto"); } catch (_) {}
  updateFilters(); if (!filtrosRecolhidos) ($("platforms").querySelector("button") || $("genres").querySelector("button"))?.focus();
};
$("glyphs-cycle").onclick = () => {
  const order = ["auto", "xbox", "ps"]; glifoPref = order[(order.indexOf(glifoPref) + 1) % order.length];
  try { localStorage.setItem("pyretro-glifos", glifoPref); } catch (_) {}
  applyGlyphs(); report(`Botões: ${GLIFO_NOMES[glifoPref]}.`, false, "settings-status");
};
applyGlyphs(); updateFilters();

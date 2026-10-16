/* Modo TV: cliente das mesmas APIs da GUI, sem acesso direto ao acervo. */
"use strict";
const $ = id => document.getElementById(id);
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
const state = {kind: "library", code: "", filter: "", items: [], systems: [], light: [], request: 0, selected: null, draft: null, busy: false, download: null};
function button(text, action, pressed) {
  const b = document.createElement("button"); b.textContent = text; b.type = "button";
  if (pressed !== undefined) b.setAttribute("aria-pressed", String(pressed));
  b.addEventListener("click", action); return b;
}
function report(message, error = false, target = "message") {
  $(target).textContent = message; $(target).classList.toggle("error", error);
}
function platformTabs() {
  const nav = $("platforms"); nav.replaceChildren();
  if (state.kind === "library" || state.kind === "playing") {
    const platforms = [...new Set(state.items.map(g => g.platform))].sort();
    for (const p of ["", ...platforms]) nav.append(button(p || "Todas as plataformas", () => {
      state.filter = p; platformTabs(); render(); nav.querySelector(`[aria-pressed="true"]`)?.focus();
    }, state.filter === p));
  } else {
    const systems = state.kind === "heavy" ? state.systems : state.light;
    for (const s of systems) nav.append(button(s.nome || s.code, () => load(state.kind, s.code), state.code === s.code));
  }
}
function collectionTabs() {
  $("collections").replaceChildren(...[["library", "Biblioteca"], ["playing", "Jogando"], ["heavy", "ROMs pesadas"], ["light", "ROMs leves"]].map(([kind, title]) => button(title, () => load(kind), state.kind === kind)));
}
async function load(kind = state.kind, code = "") {
  const request = ++state.request;
  state.kind = kind; state.filter = "";
  const systems = kind === "heavy" ? state.systems : state.light;
  state.code = code || systems[0]?.code || "";
  state.items = []; collectionTabs(); platformTabs(); render();
  $("title").textContent = ({library: "Biblioteca", playing: "Jogando", heavy: "ROMs pesadas", light: "ROMs leves"})[kind];
  report("Carregando catálogo…");
  try {
    let items;
    if (kind === "library" || kind === "playing") {
      items = (await api(kind === "library" ? "/api/library" : "/api/iniciados")).filter(g => !g.oculto).map(g => ({id: g.id, name: g.nome, platform: g.plataforma || "Biblioteca", cover: g.capa_url, tracking: g}));
    } else {
      if (!state.code) { report("Nenhum sistema configurado."); return; }
      const c = state.code;
      const data = await api(kind === "heavy" ? `/api/heavy/roms/${encodeURIComponent(c)}` : `/api/covers/${encodeURIComponent(c)}`);
      const sys = systems.find(s => s.code === c);
      items = (kind === "heavy" ? data.items : data).map(g => ({
        name: kind === "heavy" ? g.label : (g.display_name || g.label), code: c,
        platform: sys.nome || sys.capas || c, cover: kind === "heavy" ? g.capa : (g.file ? `/images/${encodeURIComponent(c)}/${encodeURIComponent(g.file)}` : null),
        tracking: g.biblioteca || {}, downloadName: kind === "heavy" && !g.in_pc && g.in_drive ? g.name : null,
        local: kind === "heavy" ? g.in_pc : null,
      }));
    }
    if (request !== state.request) return;
    state.items = items; platformTabs(); render();
    (code ? $("platforms") : $("collections")).querySelector('[aria-pressed="true"]')?.focus();
  } catch (error) { if (request === state.request) report(`Não foi possível carregar: ${error.message}. Selecione a coleção para tentar novamente.`, true); }
}
function render() {
  const items = state.items.filter(g => (!state.filter || g.platform === state.filter) && (state.kind !== "playing" || (g.tracking.iniciado && !g.tracking.finalizado)));
  const gallery = $("gallery"); gallery.replaceChildren();
  for (const g of items) {
    const card = button("", () => openGame(g, card)); card.className = "game";
    if (g.cover) { const img = document.createElement("img"); img.src = g.cover; img.alt = ""; img.loading = "lazy"; img.className = "art"; card.append(img); }
    else { const art = document.createElement("div"); art.className = "art placeholder"; art.textContent = "✦"; card.append(art); }
    const title = document.createElement("strong"); title.textContent = g.name;
    const meta = document.createElement("small"); const t = g.tracking;
    meta.textContent = [g.platform, g.downloadName ? "Só no Drive" : g.local ? "No PC" : "", t.platinado ? "🏆 Platinado" : t.finalizado ? "✓ Finalizado" : t.iniciado ? "▶ Iniciado" : "", t.nota != null ? `★ ${t.nota}` : ""].filter(Boolean).join(" · ");
    card.append(title, meta); gallery.append(card);
  }
  report(items.length ? `${items.length} jogos · escolha uma capa` : "Nenhum jogo nesta seleção.");
}
let returnFocus, returnIndex;
function openGame(g, origin = document.activeElement) {
  returnFocus = origin; returnIndex = [...$("gallery").children].indexOf(returnFocus); state.selected = g;
  state.draft = {iniciado: !!g.tracking.iniciado, finalizado: !!g.tracking.finalizado, platinado: !!g.tracking.platinado, nota: g.tracking.nota ?? null};
  $("game-title").textContent = g.name; $("game-platform").textContent = g.platform;
  report("", false, "detail-status"); renderTracking();
  $("download").hidden = !g.downloadName; $("download").textContent = "Baixar para o PC"; $("download").dataset.confirm = "";
  $("download").disabled = !!state.download;
  $("details").showModal(); $("tracking").querySelector("button").focus();
}
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
function closeGame() { if (!state.busy) { $("details").close(); (returnFocus?.isConnected ? returnFocus : $("gallery").children[Math.max(0, returnIndex)] || $("collections").querySelector("button"))?.focus(); } }
$("close").onclick = closeGame;
$("details").addEventListener("cancel", e => { e.preventDefault(); closeGame(); });
$("save").onclick = async () => {
  const g = state.selected; const campos = {...state.draft}; state.busy = true;
  $("details").querySelectorAll("button").forEach(b => { b.disabled = true; });
  report("Salvando…", false, "detail-status");
  try {
    await api(g.id ? "/api/library/edit" : "/api/library/track", g.id ? {id: g.id, campos} : {nome: g.name, code: g.code, plataforma: g.platform, fonte: `rom:${g.code}`, campos});
    Object.assign(g.tracking, campos); render(); report("Progresso salvo.", false, "detail-status");
  } catch (e) { report(`Não foi salvo: ${e.message}`, true, "detail-status"); }
  finally { state.busy = false; $("details").querySelectorAll("button").forEach(b => { b.disabled = false; }); $("download").disabled = !!state.download; $("save").focus(); }
};
$("download").onclick = async () => {
  if (state.download) return;
  const b = $("download"); const g = state.selected;
  if (!b.dataset.confirm) { b.dataset.confirm = "yes"; b.textContent = "Confirmar download"; report("Baixar este jogo do seu Drive para o PC?", false, "detail-status"); return; }
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
        if (success && !failure) { g.local = true; g.downloadName = null; render(); finish(`${g.name}: download concluído.`, false); }
        else finish(`${g.name}: ${failure || "download não confirmado"}.`, true);
      }
    };
    stream.onerror = () => finish("A conexão com o download foi interrompida. Confira o resultado na coleção antes de tentar novamente.", true);
    if (state.selected === g) report("Download em andamento. Você pode voltar e navegar pelo acervo.", false, "detail-status");
  } catch (e) { state.download = null; b.disabled = false; b.dataset.confirm = ""; b.textContent = "Baixar para o PC"; report(e.message, true, "download-status"); }
};
function focusable() {
  return [...($("details").open ? $("details") : document).querySelectorAll("button:not(:disabled),a[href]")].filter(e => !e.hidden && e.getClientRects().length);
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
  else if (key === "back") { if ($("details").open) closeGame(); else { $("collections").querySelector("button")?.focus(); } }
}
document.addEventListener("keydown", e => {
  const key = {ArrowLeft: "left", ArrowRight: "right", ArrowUp: "up", ArrowDown: "down", Escape: "back"}[e.key];
  if (key) { e.preventDefault(); action(key); }
});
let held = new Set(), repeatAt = 0;
function pollGamepad(now) {
  const pad = Array.from(navigator.getGamepads?.() || []).find(Boolean);
  if (pad) {
    $("controller").textContent = `Controle conectado: ${pad.id}`;
    const pressed = i => pad.buttons[i]?.pressed;
    const keys = new Set();
    if (pressed(14) || pad.axes[0] < -0.55) keys.add("left");
    if (pressed(15) || pad.axes[0] > 0.55) keys.add("right");
    if (pressed(12) || pad.axes[1] < -0.55) keys.add("up");
    if (pressed(13) || pad.axes[1] > 0.55) keys.add("down");
    if (pressed(0)) keys.add("accept"); if (pressed(1)) keys.add("back");
    for (const k of keys) {
      if (!held.has(k)) { action(k); repeatAt = now + 380; }
      else if (!["accept", "back"].includes(k) && now >= repeatAt) { action(k); repeatAt = now + 140; }
    }
    held = keys;
  } else { held.clear(); $("controller").textContent = "Controle: pressione um botão para conectar"; }
  requestAnimationFrame(pollGamepad);
}
async function init() {
  collectionTabs();
  try { [state.systems, state.light] = await Promise.all([api("/api/heavy/systems"), api("/api/systems")]); await load(); }
  catch (e) { report(`Não foi possível iniciar: ${e.message}. Recarregue para tentar novamente.`, true); }
  $("collections").querySelector("button")?.focus();
}
requestAnimationFrame(pollGamepad); init();

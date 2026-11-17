import {filtersChanged, load} from "./catalog.js";
import {cycleQuick, letterJump} from "./library.js";
import {$, report} from "./dom.js";
import {toggleFavorite} from "./favorites.js";
import {focusable, move, page, scrollTarget, stickScroll} from "./focus.js";
import {closeGame} from "./game.js";
import {showSpotlight} from "./home.js";
import {applySearch, closeSearch, openSearch} from "./search.js";
import {closeSettings, openSettings} from "./settings.js";
import {focusContent, focusSidebar, goDestination, inSidebar, stepDestination} from "./sidebar.js";
import {state, ui} from "./state.js";
import {closeTool} from "./tools.js";
// --- glifos do controle: Xbox (A/B/X/Y), PlayStation (✕/○/□/△) ou automático pelo controle conectado ---
const GLIFOS = {xbox: {A: "A", B: "B", X: "X", Y: "Y", L: "LB", R: "RB", LT: "LT", RT: "RT"}, ps: {A: "✕", B: "○", X: "□", Y: "△", L: "L1", R: "R1", LT: "L2", RT: "R2"}};
const GLIFO_NOMES = {auto: "Automático", xbox: "Xbox", ps: "PlayStation"};
let glifoPref = "auto", glifoDetectado = "xbox";
try { glifoPref = localStorage.getItem("pyretro-glifos") || "auto"; } catch (_) {}
// GameSir Nova 2 Lite: letras Xbox, mas no Linux só funciona no modo PS4 (pelo cabo aparece com o nome
// antigo "Sony Computer Entertainment" e o PID 09cc do DS4 v2, combinação que o DS4 original não usa).
export function padFamily(id = "") {
  if (/sony computer entertainment wireless controller.*09cc/i.test(id)) return "xbox";
  // Pelo Bluetooth o Nova 2 Lite vem sem fabricante no nome, igual a um DS4 v2; no registro esse nome
  // só existe para ele (letras Xbox). Um DS4 de verdade usa "Botões: PlayStation" em Ferramentas.
  if (/^wireless controller \(.*054c.*09cc/i.test(id)) return "xbox";
  return /054c|sony|dualshock|dualsense|wireless controller/i.test(id) ? "ps" : "xbox";
}
export function glifos() { return GLIFOS[glifoPref === "auto" ? glifoDetectado : glifoPref] || GLIFOS.xbox; }
// Entrada em uso: "pad" (controle), "keys" (teclado) ou "mouse" (mouse/toque). Decide cursor, hover, anel de foco
// (tv.css, body[data-input]) e a barra de dicas; troca sem recarregar assim que o outro aparelho é usado.
export const inputMode = () => document.body.dataset.input || "pad";
export function setInputMode(mode) {
  if (document.body.dataset.input === mode) return;
  document.body.dataset.input = mode; applyGlyphs();
}
export function applyGlyphs() {
  const g = glifos(), mode = inputMode();
  $("hints").textContent = mode === "keys" ? "↑↓←→ Navegar · Enter Escolher · Esc Voltar · Y Pesquisar"
    : mode === "mouse" ? "Clique Escolher · Botão direito Favoritar · Botão voltar do mouse Voltar"
    : `✚ Navegar · ${g.A} Escolher · ${g.B} Voltar · ☰ Opções`;
  $("hints-extra").textContent = mode === "keys" ? "Backspace Voltar · PgUp/PgDn Página · Tab também navega · Mouse: botão direito favorita"
    : mode === "mouse" ? "Roda do mouse corre as fileiras · Y ou Pesquisar abre a busca · Teclado e controle seguem funcionando"
    : `${g.X} Favoritar · ${g.Y} Pesquisar · ${g.L}/${g.R} Página · ${g.LT}/${g.RT} Coleção · Mouse: botão direito favorita`;
  $("search-open").textContent = mode === "pad" ? `${g.Y} · Pesquisar` : "Pesquisar";
  $("glyphs-cycle").textContent = `Botões: ${GLIFO_NOMES[glifoPref]}`;
}
// Só deslocamento de verdade conta: o navegador repete pointermove nas mesmas coordenadas quando o layout muda sob o cursor.
let pointerX, pointerY;
document.addEventListener("pointermove", e => {
  const moved = e.movementX || e.movementY || (pointerX !== undefined && (e.clientX !== pointerX || e.clientY !== pointerY));
  pointerX = e.clientX; pointerY = e.clientY;
  if (moved) setInputMode("mouse");
});
document.addEventListener("pointerdown", () => setInputMode("mouse"));
export function action(key) {
  if (state.busy) return;
  if (["left", "right", "up", "down"].includes(key)) move(key);
  else if (key === "accept") { if (!focusable().includes(document.activeElement)) focusable()[0]?.focus(); else document.activeElement.click(); }
  else if (key === "back") { if ($("search-dialog").open) closeSearch(); else if ($("tool-dialog").open) closeTool(); else if ($("settings-dialog").open) closeSettings(); else if ($("details").open) closeGame(); else if (inSidebar()) focusContent(); else if (state.kind !== "home") load("home"); else focusSidebar(); }
  else if (key === "sidebar" && !document.querySelector("dialog[open]")) { if (inSidebar()) focusContent(); else focusSidebar(); }
  else if (key === "search") openSearch();
  else if (key === "erase") { if ($("search-dialog").open) $("search-input").value = $("search-input").value.slice(0, -1); else if (!$("settings-dialog").open) toggleFavorite(); }
  else if (key === "submit") { if ($("search-dialog").open) applySearch(); else openSettings(); }
  else if (["page-up", "page-down"].includes(key) && !document.querySelector("dialog[open]")) page(key === "page-up" ? -1 : 1);
  else if (["quick-prev", "quick-next"].includes(key) && !document.querySelector("dialog[open]")) {
    // LB/RB na Biblioteca trocam o filtro rápido (Tudo, Jogando, Neste PC, Favoritos, Ranking, Finalizados).
    const inQuick = $("quick").contains(document.activeElement);
    cycleQuick(key === "quick-prev" ? -1 : 1); filtersChanged();
    (inQuick ? $("quick").querySelector('[aria-pressed="true"]') : $("gallery").querySelector("button") || $("quick").querySelector('[aria-pressed="true"]'))?.focus();
  }
  else if (["letter-prev", "letter-next"].includes(key) && !document.querySelector("dialog[open]")) letterJump(key === "letter-prev" ? -1 : 1);
  else if (["previous", "next"].includes(key) && !document.querySelector("dialog[open]")) {
    stepDestination(key === "previous" ? -1 : 1);
  }
}
document.addEventListener("keydown", e => {
  if (!["Shift", "Control", "Alt", "Meta", "CapsLock"].includes(e.key)) setInputMode("keys");
  if (e.target instanceof HTMLInputElement && e.key !== "Escape") return;
  if (/^[1-5]$/.test(e.key) && !e.ctrlKey && !e.altKey && !e.metaKey && !document.querySelector("dialog[open]")) { e.preventDefault(); goDestination(Number(e.key)); return; }
  const key = {"[": "letter-prev", "]": "letter-next", m: "sidebar", M: "sidebar", ArrowLeft: "left", ArrowRight: "right", ArrowUp: "up", ArrowDown: "down", Escape: "back", Backspace: "back", PageUp: "page-up", PageDown: "page-down", y: "search", Y: "search"}[e.key];
  if (key) { e.preventDefault(); action(key); }
});
// Mouse: o botão "voltar" lateral faz o mesmo que B.
document.addEventListener("mouseup", e => { if (e.button === 3) { e.preventDefault(); action("back"); } });
let held = new Set(), repeatAt = new Map(), foreground = true, awaitNeutral = false, noPadSince = null;
window.addEventListener("blur", () => { foreground = false; held.clear(); awaitNeutral = true; $("spotlight-video").pause(); });
document.addEventListener('visibilitychange', () => { if (document.hidden) { $("spotlight-video").pause(); $("detail-video").pause(); } else if (state.kind === 'home' && ui.spotlightGame) showSpotlight(ui.spotlightGame); });
window.addEventListener("focus", () => { foreground = true; });
const RAW_PAD = {
  matches: pad => pad.mapping !== "standard" && pad.buttons.length === 15 && pad.axes.length >= 8,
  // índice padrão -> índice cru: A, B, X, Y, LB, RB, LT, RT, Back, Start
  buttons: {0: 0, 1: 1, 2: 3, 3: 4, 4: 6, 5: 7, 6: 8, 7: 9, 8: 10, 9: 11},
};
let stickLatched = false, lastPadFrame = null, scrollCarry = {x: 0, y: 0};
export function pollGamepad(now) {
  const pads = Array.from(navigator.getGamepads?.() || []).filter(p => p && p.connected !== false && p.buttons.length >= 10);
  const pad = pads.find(p => p.mapping === "standard") || pads[0];
  if (pad) {
    const family = padFamily(pad.id); if (family !== glifoDetectado) { glifoDetectado = family; applyGlyphs(); }
    $("controller").textContent = `Controle conectado: ${pad.id}`; noPadSince = null; $("controller").classList.remove("warning");
    // Sem mapeamento "standard" (G8 pelo evdev, medido em 29/10) o navegador entrega a ordem crua do Linux:
    // cruz nos eixos 6/7 e botões deslocados. A tabela traduz para os índices padrão usados abaixo.
    const raw = RAW_PAD.matches(pad);
    const pressed = i => pad.buttons[raw ? RAW_PAD.buttons[i] : i]?.pressed;
    const hat = (axis, sign) => raw && (pad.axes[axis] || 0) * sign > 0.55;
    const keys = new Set();
    if (pressed(14) || pad.axes[0] < -0.55 || hat(6, -1)) keys.add("left");
    if (pressed(15) || pad.axes[0] > 0.55 || hat(6, 1)) keys.add("right");
    if (pressed(12) || pad.axes[1] < -0.55 || hat(7, -1)) keys.add("up");
    if (pressed(13) || pad.axes[1] > 0.55 || hat(7, 1)) keys.add("down");
    if (pressed(0)) keys.add("accept"); if (pressed(1)) keys.add("back");
    if (pressed(2)) keys.add("erase"); if (pressed(3)) keys.add("search");
    // Na Biblioteca LB/RB trocam o filtro rápido; nas demais telas continuam paginando.
    if (pressed(4)) keys.add(state.kind === "library" ? "quick-prev" : "page-up"); if (pressed(5)) keys.add(state.kind === "library" ? "quick-next" : "page-down");
    if (pressed(6)) keys.add("previous"); if (pressed(7)) keys.add("next");
    if (pressed(9)) keys.add("submit"); if (pressed(8)) keys.add("sidebar");
    if (!foreground || document.hidden || ui.emulatorRunning) { held.clear(); awaitNeutral = true; requestAnimationFrame(pollGamepad); return; }
    const frame = lastPadFrame == null ? 16 : now - lastPadFrame; lastPadFrame = now;
    // Biblioteca: o analógico direito para os lados pula de inicial em inicial (a rolagem fina continua no eixo vertical).
    const stickX = pad.axes[raw ? 3 : 2] || 0, jumping = state.kind === "library" && $("gallery").contains(document.activeElement);
    if (Math.abs(stickX) > .7 && !stickLatched && jumping) { stickLatched = true; letterJump(Math.sign(stickX)); } else if (Math.abs(stickX) < .4) stickLatched = false;
    for (const [axis, index] of [["x", raw ? 3 : 2], ["y", raw ? 4 : 3]]) {
      if (axis === "x" && jumping) continue;
      scrollCarry[axis] += stickScroll(pad.axes[index] || 0, frame);
      if (Math.abs(scrollCarry[axis]) < 1) continue;
      const step = Math.trunc(scrollCarry[axis]); scrollCarry[axis] -= step;
      scrollTarget(document.activeElement, axis === "x").scrollBy({[axis === "x" ? "left" : "top"]: step, behavior: "instant"});
    }
    if (awaitNeutral) { if (!keys.size) awaitNeutral = false; requestAnimationFrame(pollGamepad); return; }
    if (keys.size) setInputMode("pad");
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
$("glyphs-cycle").onclick = () => {
  const order = ["auto", "xbox", "ps"]; glifoPref = order[(order.indexOf(glifoPref) + 1) % order.length];
  try { localStorage.setItem("pyretro-glifos", glifoPref); } catch (_) {}
  applyGlyphs(); report(`Botões: ${GLIFO_NOMES[glifoPref]}.`, false, "settings-status");
};

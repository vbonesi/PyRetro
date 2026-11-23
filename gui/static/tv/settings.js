import {api} from "./api.js";
import {load} from "./catalog.js";
import {$, report} from "./dom.js";
import {fullscreenText, isNativeApp} from "./native.js";
import {state} from "./state.js";
let settingsReturnFocus;
export function applyPreferences(preferences) {
  state.preferences = preferences;
  document.documentElement.dataset.theme = preferences.theme || "dark";
  $("theme-dark").setAttribute("aria-pressed", String(preferences.theme !== "light"));
  $("theme-light").setAttribute("aria-pressed", String(preferences.theme === "light"));
}
export function openSettings() {
  if (document.querySelector("dialog[open]")) return;
  settingsReturnFocus = document.activeElement; report("", false, "settings-status");
  fullscreenLabel(); $("settings-dialog").showModal(); $(state.preferences.theme === "light" ? "theme-light" : "theme-dark").focus();
}
export function closeSettings() { $("settings-dialog").close(); (settingsReturnFocus?.isConnected ? settingsReturnFocus : $("settings-open")).focus(); }
$("settings-open").onclick = openSettings; $("settings-close").onclick = closeSettings;
$("settings-dialog").addEventListener("cancel", e => { e.preventDefault(); closeSettings(); });
$("settings-home").onclick = () => { closeSettings(); load("home"); };
for (const theme of ["dark", "light"]) $(`theme-${theme}`).onclick = async () => {
  if (state.busy) return; state.busy = true;
  try { applyPreferences(await api("/api/tv/preferences", {theme})); report("Tema salvo.", false, "settings-status"); }
  catch (e) { report(e.message, true, "settings-status"); }
  finally { state.busy = false; }
};
// Janela nativa (QtWebEngine): o user agent traz PyRetroApp/1. Lá a tela cheia é da própria janela, alternada pelo Qt
// (ponte pyretro-app://…), e Fechar encerra a janela; no Chrome vale a tela cheia do elemento.
let nativeFull = null;  // estado da janela, devolvido pelo Qt (null até a primeira resposta)
window.pyretroFullscreen = full => { nativeFull = !!full; fullscreenLabel(); };
const bridge = action => { location.href = `pyretro-app://${action}`; };
// O <dialog> modal fica na camada superior; pedir a tela cheia com ele aberto o deixa como fantasma por baixo. Fecha antes.
export function fullscreenLabel() {
  $("fullscreen").textContent = fullscreenText(isNativeApp() ? nativeFull : document.fullscreenElement);
  $("quit-app").hidden = !isNativeApp();
}
export function toggleFullscreen() {
  if (isNativeApp()) { bridge("fullscreen"); return; }
  return (async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else { if ($("settings-dialog").open) closeSettings(); await document.documentElement.requestFullscreen(); }
    } catch (_) { report("Use o atalho PyRetro do menu para abrir em tela cheia.", false, "settings-status"); }
    fullscreenLabel();
  })();
}
$("fullscreen").onclick = toggleFullscreen;
document.addEventListener("keydown", e => { if (e.key === "F11" && isNativeApp()) { e.preventDefault(); bridge("fullscreen"); } });
// Fechar: dois toques (confirmação do botão); só encerra a janela, o servidor continua no ar.
let quitArmed = false;
$("quit-app").onclick = () => {
  if (!quitArmed) { quitArmed = true; $("quit-app").textContent = "Fechar o PyRetro?"; return; }
  quitArmed = false; $("quit-app").textContent = "Fechar o PyRetro"; bridge("quit");
};
$("settings-dialog").addEventListener("close", () => { quitArmed = false; $("quit-app").textContent = "Fechar o PyRetro"; });
document.addEventListener("fullscreenchange", fullscreenLabel);
function updateClock() { $("clock").textContent = new Date().toLocaleTimeString("pt-BR", {hour: "2-digit", minute: "2-digit"}); }
updateClock(); setInterval(updateClock, 30000);
if (navigator.getBattery) navigator.getBattery().then(battery => {
  const update = () => { $("battery").hidden = false; $("battery").textContent = `${battery.charging ? "⚡" : "▰"} ${Math.round(battery.level * 100)}%`; };
  battery.addEventListener("levelchange", update); battery.addEventListener("chargingchange", update); update();
}).catch(() => {});
$("hints-more").onclick = () => { const open = $("hints-extra").hidden; $("hints-extra").hidden = !open; $("hints-more").setAttribute("aria-expanded", String(open)); $("hints-more").textContent = open ? "Menos atalhos" : "Mais atalhos"; };

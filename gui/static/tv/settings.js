import {api} from "./api.js";
import {load} from "./catalog.js";
import {$, report} from "./dom.js";
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
// O <dialog> modal fica na camada superior; pedir a tela cheia com ele aberto o deixa como fantasma por baixo. Fecha antes.
export function fullscreenLabel() { $("fullscreen").textContent = document.fullscreenElement ? "Sair da tela cheia" : "Tela cheia"; }
$("fullscreen").onclick = async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else { if ($("settings-dialog").open) closeSettings(); await document.documentElement.requestFullscreen(); }
  } catch (_) { report("Use o atalho PyRetro do menu para abrir em tela cheia.", false, "settings-status"); }
  fullscreenLabel();
};
document.addEventListener("fullscreenchange", fullscreenLabel);
function updateClock() { $("clock").textContent = new Date().toLocaleTimeString("pt-BR", {hour: "2-digit", minute: "2-digit"}); }
updateClock(); setInterval(updateClock, 30000);
if (navigator.getBattery) navigator.getBattery().then(battery => {
  const update = () => { $("battery").hidden = false; $("battery").textContent = `${battery.charging ? "⚡" : "▰"} ${Math.round(battery.level * 100)}%`; };
  battery.addEventListener("levelchange", update); battery.addEventListener("chargingchange", update); update();
}).catch(() => {});
$("hints-more").onclick = () => { const open = $("hints-extra").hidden; $("hints-extra").hidden = !open; $("hints-more").setAttribute("aria-expanded", String(open)); $("hints-more").textContent = open ? "Menos atalhos" : "Mais atalhos"; };

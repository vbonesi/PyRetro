export const $ = id => document.getElementById(id);
export function button(text, action, pressed) {
  const b = document.createElement("button"); b.textContent = text; b.type = "button";
  if (pressed !== undefined) b.setAttribute("aria-pressed", String(pressed));
  b.addEventListener("click", action); return b;
}
export function report(message, error = false, target = "message") {
  $(target).textContent = message; $(target).classList.toggle("error", error);
}
export function formatTime(seconds) { const minutes = Math.floor(seconds / 60); return minutes >= 60 ? `${Math.floor(minutes/60)} h ${minutes%60} min` : minutes ? `${minutes} min` : `${Math.floor(seconds)} s`; }
export function formatHours(hours) {
  const total = Math.round(hours), days = Math.floor(total / 24);
  return days ? `${days} ${days === 1 ? "dia" : "dias"} e ${total % 24} h (${total.toLocaleString("pt-BR")} h)` : `${total} h`;
}
export const looseName = s => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/\(.*?\)|\[.*?\]/g, " ").replace(/[^a-z0-9]+/g, " ").trim();
// 💾 Saves do jogo no PC (RetroArch, pasta do sistema e raiz antiga). Escrever sempre guarda
// uma cópia antes em Backups/Saves do modo TV (core/tv_saves.py); nada é apagado de vez.
export const hint = text => Object.assign(document.createElement("p"), {className: "hint", textContent: text});
// Ação que mexe em arquivo: primeiro toque pede confirmação, o segundo executa.
export function confirmButton(label, confirmLabel, run) {
  const b = button(label, () => {
    if (!b.dataset.confirm) { b.dataset.confirm = "yes"; b.textContent = confirmLabel; return; }
    b.dataset.confirm = ""; b.textContent = label; run();
  }); return b;
}
// --- 🗑 Remover…: deste PC, do Drive (lixeira) ou dos dois, sempre com prévia (core/removal.py) ---
export const fmtBytes = n => n >= 1e9 ? `${(n / 1e9).toFixed(1)} GB` : n >= 1e6 ? `${(n / 1e6).toFixed(0)} MB` : `${Math.max(1, Math.round(n / 1e3))} KB`;
export const row = (text, ...buttons) => { const r = document.createElement("div"); r.className = "save-row"; r.append(Object.assign(document.createElement("span"), {textContent: text}), ...buttons); return r; };
export const actions = (...buttons) => { const a = document.createElement("div"); a.className = "actions"; a.append(...buttons); return a; };
export const heading = text => Object.assign(document.createElement("h3"), {textContent: text});
// Escolha entre opções como botões (o controle não abre <select>).
export function choice(options, current, pick) {
  const box = document.createElement("div"); box.className = "actions choice";
  const draw = value => box.replaceChildren(...options.map(([v, label]) => button(label, () => { pick(v); draw(v); box.querySelector('[aria-pressed="true"]')?.focus(); }, v === value)));
  draw(current); return box;
}

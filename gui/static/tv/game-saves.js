import {api} from "./api.js";
import {refreshBadges} from "./cards.js";
import {$, button, confirmButton, hint, report, row} from "./dom.js";
import {badgeKey, observedSaves, state} from "./state.js";
// 💾 Saves do jogo no PC (RetroArch, pasta do sistema e raiz antiga). Só leitura.
// Saves, edição e capa dividem a ficha: abrir um painel fecha os outros.
export function closeOtherPanels(keep) {
  for (const [toggle, panel] of [["saves-toggle", "saves-fields"], ["edit-toggle", "edit-fields"], ["cover-toggle", "cover-fields"], ["textures-toggle", "textures-fields"]])
    if (toggle !== keep) { $(panel).hidden = true; $(toggle).setAttribute("aria-expanded", "false"); }
}
$("saves-toggle").onclick = () => {
  const box = $("saves-fields");
  box.hidden = !box.hidden; if (!box.hidden) closeOtherPanels("saves-toggle");
  $("saves-toggle").setAttribute("aria-expanded", String(!box.hidden));
  if (!box.hidden) renderSaves();
};
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
async function saveAction(kind, extra, done) {
  const g = state.selected; if (state.busy || !g) return;
  state.busy = true; report("Gravando…", false, "detail-status");
  try { await api(`/api/tv/saves/${kind}`, {code: g.code, label: g.romName || g.name, ...extra}); report(done, false, "detail-status"); }
  catch (e) { report(e.message, true, "detail-status"); }
  finally { state.busy = false; }
  await renderSaves("saves-backup");
}

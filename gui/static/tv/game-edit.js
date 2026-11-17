import {api} from "./api.js";
import {render} from "./catalog.js";
import {$, button, report} from "./dom.js";
import {closeOtherPanels} from "./game-saves.js";
import {openTextEntry} from "./search.js";
import {state} from "./state.js";
// ✎ Editar jogo: os mesmos campos do ✎ da web. ROM sem cadastro cria o registro na 1ª gravação
// (/api/library/track); nome e plataforma de ROM vêm do arquivo/sistema e não são editados aqui.
const EDIT_FIELDS = [["nome", "Nome"], ["plataforma", "Plataforma"], ["genero", "Gênero"], ["data_final", "Data que finalizou (aaaa-mm-dd)"], ["tempo", "Tempo jogado (ex.: 31:40:00)"], ["observacoes", "Comentário"], ["sinopse", "Sinopse"]];
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

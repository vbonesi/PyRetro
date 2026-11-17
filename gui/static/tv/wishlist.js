import {api, runJob} from "./api.js";
import {reloadSelection, render} from "./catalog.js";
import {$, report} from "./dom.js";
import {closeGame} from "./game.js";
import {openTextEntry} from "./search.js";
import {WISHLIST_STORES, state} from "./state.js";
// ➕ Desejados pela TV: PSN/Xbox só acrescentam (um nome por vez); Steam sincroniza com a
// lista pública (pode tirar quem saiu de lá), por isso pede confirmação.
async function wishlistJob(source, texto) {
  if (state.busy) return; state.busy = true; report(source === "steam" ? "Sincronizando a lista da Steam…" : `Adicionando "${texto}"…`);
  try {
    const result = await runJob("/api/wishlist/sync", {source, texto, apply: true},
      d => { if (d.type === "log" && /^Steam: \d+ de \d+/.test(d.line)) report(`Sincronizando a lista da Steam… ${d.line.slice(7)}`); });
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

import {api, runJob} from "./api.js";
import {$, confirmButton, hint, looseName, report, row} from "./dom.js";
import {closeOtherPanels} from "./game-saves.js";
import {TEXTURE_SYSTEMS, state} from "./state.js";
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
    }) : [hint("Nenhum pacote do catálogo com este nome. Importe um pacote em Ferramentas → Texturas HD.")]));
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

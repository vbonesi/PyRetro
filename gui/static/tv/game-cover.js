import {api} from "./api.js";
import {render} from "./catalog.js";
import {$, button, report} from "./dom.js";
import {closeOtherPanels} from "./game-saves.js";
import {openTextEntry} from "./search.js";
import {state} from "./state.js";
// 🖼 Capa: busca nas mesmas fontes da web. ROM: bases de ROM (libretro/LaunchBox/ScreenScraper) ou
// SteamGridDB; Biblioteca: SteamGridDB. Aplicar troca o arquivo da capa, como na web.
export function coverLabel(g) {
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
// 📁 Capa a partir de um arquivo (PNG ou JPEG) do aparelho: mesma gravação da web (/api/cover/upload e /api/library/cover_upload).
$("cover-upload").onclick = () => $("cover-file").click();
$("cover-file").onchange = async event => {
  const file = event.target.files[0], g = state.selected; event.target.value = "";
  if (!file || !g || state.busy) return;
  if (!/\.(png|jpe?g)$/i.test(file.name)) return report("Escolha uma imagem PNG ou JPEG.", true, "detail-status");
  if (file.size > 8 * 1024 * 1024) return report("Escolha uma imagem de até 8 MB.", true, "detail-status");
  state.busy = true; report("Enviando capa…", false, "detail-status");
  try {
    const data = await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result.split(",")[1]); reader.onerror = () => reject(new Error("não foi possível ler o arquivo")); reader.readAsDataURL(file); });
    const label = g.code ? coverLabel(g) : null;
    const r = await api(g.code ? "/api/cover/upload" : "/api/library/cover_upload", g.code ? {code: g.code, label, filename: file.name, data} : {id: g.id, filename: file.name, data});
    g.cover = g.code ? `/images/${encodeURIComponent(g.code)}/${encodeURIComponent(label)}.png?v=${Date.now()}` : `/library-images/${r.file.split("/").map(encodeURIComponent).join("/")}?v=${Date.now()}`;
    $("detail-cover").src = g.cover; $("detail-cover").hidden = false;
    $("cover-fields").hidden = true; $("cover-toggle").setAttribute("aria-expanded", "false"); $("cover-toggle").focus();
    render(); report("Capa trocada.", false, "detail-status");
  } catch (e) { report(`Capa não enviada: ${e.message}`, true, "detail-status"); }
  finally { state.busy = false; }
};

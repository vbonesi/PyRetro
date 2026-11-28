import {api, refreshCsrf} from "./api.js";
import {setDetailCover} from "./cover-frame.js";
import {fillBadges, refreshBadges} from "./cards.js";
import {render} from "./catalog.js";
import {$, button, formatTime, report} from "./dom.js";
import {updateFavoriteButton} from "./favorites.js";
import {gameRoute, pushOverlay} from "./router.js";
import {closePage, openPage} from "./pages.js";
import {showSpotlight} from "./home.js";
import {playDownloaded, refreshHomeAfterPlay, refreshPlayOptions} from "./play.js";
import {TEXTURE_SYSTEMS, WISHLIST_STORES, state, ui} from "./state.js";
let returnFocus, returnIndex, returnGameKey;
export function openGame(g, origin = document.activeElement) {
  returnFocus = origin; returnIndex = [...$("gallery").children].indexOf(returnFocus); state.selected = g;
  returnGameKey = origin?.dataset?.key;
  pushOverlay(gameRoute(g.key || (g.id ? `pc:${g.id}` : `${g.code}:${g.romName}`)));
  state.draft = {iniciado: !!g.tracking.iniciado, finalizado: !!g.tracking.finalizado, platinado: !!g.tracking.platinado, nota: g.tracking.nota ?? null};
  $("game-title").textContent = g.name; $("game-platform").textContent = g.platform;
  if (g.platform) $("game-platform").prepend(plataformaIcone(plataformaInfo(g.code, g.platform)));
  fillBadges($('game-badges'), g);
  const textureCode = TEXTURE_SYSTEMS[g.code];
  $("textures-toggle").hidden = !textureCode; $("textures-fields").hidden = true; $("textures-toggle").setAttribute("aria-expanded", "false");
  setDetailCover(g.cover);
  $("spotlight-video").pause(); $("time-fields").hidden = true; $("media-fields").hidden = true;
  $("game-synopsis").textContent = g.tracking?.sinopse || ''; $("game-synopsis").hidden = !g.tracking?.sinopse;
  $("game-time").textContent = g.playtime?.seconds ? `${formatTime(g.playtime.seconds)} em ${g.playtime.sessions} sessão(ões) registrada(s).` : 'Ainda sem tempo registrado neste PC.';
  $("detail-video").pause(); $("detail-video").hidden = !g.media?.video;
  $("detail-video").removeAttribute('src'); if (g.media?.video) $("detail-video").src = g.media.video;
  $("saves-toggle").hidden = !g.code; $("saves-fields").hidden = true; $("saves-fields").replaceChildren(); $("saves-toggle").setAttribute("aria-expanded", "false");
  state.edits = {}; $("edit-fields").hidden = true; $("cover-fields").hidden = true; $("genre-list").hidden = true;
  $("edit-toggle").setAttribute("aria-expanded", "false"); $("cover-toggle").setAttribute("aria-expanded", "false");
  $("cover-toggle").hidden = !g.code && !g.id; $("edit-toggle").hidden = !g.code && !g.id;
  $("wishlist-actions").hidden = !g.wishlist; $("onde-actions").hidden = !g.id || !!g.code;
  const light = state.light.some(x => x.code === g.code);
  $("rom-rename").hidden = !g.code || !(light ? g.cover : g.local); $("rom-delete").hidden = !g.code || !(light || g.local);
  $("decompose").hidden = !g.id || !!g.code || !!g.wishlist;
  $("rom-delete").dataset.confirm = ""; $("rom-delete").textContent = "🗑 Apagar ROM";
  $("rom-remove").hidden = !g.code || !(g.local || g.downloadName || g.driveName);
  // Desejado ainda não é seu: sem favorito, tempo, mídia ou progresso.
  for (const id of ["favorite", "time-toggle", "media-toggle", "progress-toggle", "game-time"]) $(id).hidden = !!g.wishlist;
  for (const id of ["wishlist-bought", "wishlist-remove"]) { $(id).dataset.confirm = ""; $(id).textContent = id === "wishlist-bought" ? "✅ Comprado" : "🗑 Tirar da lista"; }
  updateFavoriteButton(g); $("progress-fields").hidden = true; $("progress-toggle").setAttribute("aria-expanded", "false");
  report("", false, "detail-status"); renderTracking();
  $("download").hidden = !g.downloadName; $("download").textContent = "⬇ Baixar para este PC"; $("download").dataset.confirm = "";
  $("download").disabled = !!state.download;
  $("more-menu").hidden = true; $("more-toggle").setAttribute("aria-expanded", "false"); $("more-toggle").hidden = !!g.wishlist;
  openPage($("details")); $("close").focus();
  if (g.wishlist) { $("play-actions").replaceChildren(); $("play-hint").textContent = `Na sua lista de desejos (${WISHLIST_STORES[g.wishlist]}). Comprou? Marque abaixo e ele entra na Biblioteca.`; }
  else refreshPlayOptions(g);
}
$("progress-toggle").onclick = () => {
  $("progress-fields").hidden = !$("progress-fields").hidden;
  $("progress-toggle").setAttribute("aria-expanded", String(!$("progress-fields").hidden));
  if (!$("progress-fields").hidden) $("tracking").querySelector("button")?.focus();
};
function renderTracking() {
  const fields = [["iniciado", "Iniciado"], ["finalizado", "Finalizado"], ["platinado", "Platinado"]];
  $("tracking").replaceChildren(...fields.map(([key, label], index) => button(label, () => {
    const value = !state.draft[key];
    fields.forEach(([field], i) => { if (value ? i <= index : i >= index) state.draft[field] = value; });
    renderTracking(); $("tracking").children[index].focus();
  }, state.draft[key])));
  const rating = $("rating"); rating.textContent = state.draft.nota == null ? "Sem nota" : notaEspecial(state.draft.nota) ? "11 ✦" : state.draft.nota.toFixed(1).replace(".", ",");
  rating.style.color = notaColor(state.draft.nota) || "";
}
function adjustRating(delta) {
  if (state.busy) return;
  state.draft.nota = notaPasso(state.draft.nota, delta); renderTracking();
}
$("rating-down").onclick = () => adjustRating(-1);
$("rating-up").onclick = () => adjustRating(1);
$("rating-fine-down").onclick = () => adjustRating(-0.1);
$("rating-fine-up").onclick = () => adjustRating(0.1);
$("rating-clear").onclick = () => { state.draft.nota = null; renderTracking(); };
// Fechar pela interface volta uma entrada do histórico (a ficha tem endereço); o tratamento de rota do
// tv.js chama hideGame direto quando o voltar vem do navegador.
export function closeGame() {
  if (state.busy) return;
  hideGame();
  if (/^#\/jogo\//.test(location.hash)) history.back();
}
export function hideGame() {
  $("detail-video").pause();
  closePage($("details"));
  if (state.kind === 'home' && ui.spotlightGame) showSpotlight(ui.spotlightGame);
  const matching = [...document.querySelectorAll("#home .game,#gallery .game")].find(c => c.dataset.key === returnGameKey);
  (returnFocus?.isConnected ? returnFocus : matching || $("gallery").children[Math.max(0, returnIndex)] || $("home").querySelector("button") || $("destinations").querySelector("button"))?.focus();
}
// "⋯ Mais" guarda o que é raro (mídia, baixar, remover, apagar); confirmações que dependem de um botão do menu o abrem.
export function showMoreMenu(show = true) { $("more-menu").hidden = !show; $("more-toggle").setAttribute("aria-expanded", String(show)); }
$("more-toggle").onclick = () => { showMoreMenu($("more-menu").hidden); if (!$("more-menu").hidden) $("more-menu").querySelector("button:not([hidden])")?.focus(); };
$("time-toggle").onclick = () => { $("time-fields").hidden = !$("time-fields").hidden; if (!$("time-fields").hidden) $("time-minutes").focus(); };
$("media-toggle").onclick = () => { $("media-fields").hidden = !$("media-fields").hidden; };
$("time-save").onclick = async () => {
  const g = state.selected; if (state.busy || !g?.key) return;
  state.busy = true;
  try { g.playtime = await api('/api/tv/playtime', {key:g.key,minutes:Number($("time-minutes").value)}); $("game-time").textContent = `${formatTime(g.playtime.seconds)} em ${g.playtime.sessions} sessão(ões) registrada(s).`; refreshBadges(g); report('Tempo registrado.',false,'detail-status'); await refreshHomeAfterPlay(); }
  catch(error) { report(error.message,true,'detail-status'); }
  finally { state.busy = false; }
};
for (const kind of ['logo','video']) $("media-"+kind).onchange = async event => {
  const file = event.target.files[0], g = state.selected; if (!file || !g?.key || state.busy) return;
  if (file.size > 64*1024*1024) { report('Escolha um arquivo de até 64 MB.',true,'detail-status'); return; }
  state.busy = true; report('Importando mídia…',false,'detail-status');
  try {
    const csrf = await refreshCsrf(); // token atual, mesmo depois de o servidor reiniciar
    const response = await fetch('/api/tv/media?'+new URLSearchParams({key:g.key,kind}),{method:'POST',headers:{'X-PyRetro-CSRF':csrf,'Content-Type':'application/octet-stream'},body:file});
    const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Falha na importação');
    g.media = data; report('Mídia salva neste PC.',false,'detail-status');
    if (data.video) { $("detail-video").src = data.video; $("detail-video").hidden = false; }
    await refreshHomeAfterPlay();
  } catch(error) { report(error.message,true,'detail-status'); }
  finally { state.busy = false; event.target.value = ''; }
};
$("close").onclick = closeGame;
$("details").addEventListener("cancel", e => { e.preventDefault(); closeGame(); });
$("save").onclick = async () => {
  if (state.busy) return;
  const g = state.selected; const campos = {...state.draft}; state.busy = true;
  $("details").querySelectorAll("button").forEach(b => { b.disabled = true; });
  report("Salvando…", false, "detail-status");
  try {
    await api(g.id ? "/api/library/edit" : "/api/library/track", g.id ? {id: g.id, campos} : {nome: g.name, code: g.code, plataforma: g.platform, fonte: `rom:${g.code}`, campos});
    Object.assign(g.tracking, campos); render(); refreshBadges(g); report("Progresso salvo.", false, "detail-status");
  } catch (e) { report(`Não foi salvo: ${e.message}`, true, "detail-status"); }
  finally { state.busy = false; $("details").querySelectorAll("button").forEach(b => { b.disabled = b.dataset.unavailable === "true"; }); $("download").disabled = !!state.download; $("save").focus(); }
};
$("download").onclick = () => downloadGame(false);
export async function downloadGame(playAfter) {
  if (state.download || state.busy) return;
  const b = $("download"); const g = state.selected;
  if (!b.dataset.confirm) { showMoreMenu(); b.dataset.confirm = "yes"; b.textContent = "Confirmar download"; b.dataset.playAfter = String(playAfter); report(playAfter ? "Baixar este jogo e abrir o emulador ao concluir?" : "Baixar este jogo do seu Drive para o PC?", false, "detail-status"); return; }
  playAfter = b.dataset.playAfter === "true";
  b.disabled = true; state.download = g;
  report(`Baixando ${g.name}…`, false, "download-status");
  try {
    const {job} = await api("/api/heavy/download", {code: g.code, name: g.downloadName});
    const stream = new EventSource(`/api/fetch/stream?job=${encodeURIComponent(job)}`);
    let success = false, failure = "";
    function finish(message, error) { stream.close(); state.download = null; report(message, error, "download-status"); b.disabled = false; b.hidden = !state.selected?.downloadName; b.textContent = "⬇ Baixar para este PC"; b.dataset.confirm = ""; if (state.selected === g) report(message, error, "detail-status"); }
    stream.onmessage = e => {
      const data = JSON.parse(e.data);
      if (data.type === "system_done") { success = data.result.ok; if (!success) failure = data.result.message || "falha no download"; }
      if (data.type === "error") failure = data.message || "falha no download";
      if (data.type === "job_done") {
        if (success && !failure) { g.local = true; g.downloadName = null; render(); finish(`${g.name}: download concluído.`, false);
          if (state.selected === g && $("details").open) refreshPlayOptions(g);
          if (playAfter) playDownloaded(g); }
        else finish(`${g.name}: ${failure || "download não confirmado"}.`, true);
      }
    };
    stream.onerror = () => finish("A conexão com o download foi interrompida. Confira o resultado na coleção antes de tentar novamente.", true);
    if (state.selected === g) report("Download em andamento. Você pode voltar e navegar pelo acervo.", false, "detail-status");
  } catch (e) { state.download = null; b.disabled = false; b.dataset.confirm = ""; b.textContent = "⬇ Baixar para este PC"; report(e.message, true, "download-status"); }
}

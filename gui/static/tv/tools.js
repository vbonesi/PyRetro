import {runJob} from "./api.js";
import {render} from "./catalog.js";
import {$, button, report} from "./dom.js";
import {pushOverlay, toolRoute} from "./router.js";
import {toolCloudSaves, toolCovers, toolDiagnostics, toolLibrary, toolMaintenance, toolMemcards, toolOrganize, toolPhoneSaves, toolSettings, toolSetup, toolTextures} from "./tools-pages.js";
// --- 🛠 Ferramentas: o que antes só a interface completa fazia ------------------
let toolReturnFocus, toolRouted = false;
export function toolStatus(message, error = false) { report(message, error, "tool-status"); }
// `id` dá endereço à ferramenta (#/ferramentas/<id>); sem id (remover, decompor) ela não tem rota.
export function openTool(title, render, id) {
  toolReturnFocus = document.activeElement; toolRouted = !!id; if (id) pushOverlay(toolRoute(id)); $("tool-title").textContent = title;
  // Corpo novo a cada abertura: resposta atrasada da ferramenta anterior cai num elemento descartado.
  const body = Object.assign(document.createElement("div"), {id: "tool-body"}); $("tool-body").replaceWith(body);
  $("tool-log").hidden = true; $("tool-log").textContent = ""; toolStatus("");
  $("tool-dialog").showModal(); $("tool-close").focus();
  Promise.resolve(render(body)).catch(e => toolStatus(e.message, true)).then(() => { if (document.activeElement === $("tool-close")) body.querySelector("button")?.focus(); });
}
export function closeTool() {
  const routed = toolRouted; hideTool();
  if (routed && /^#\/ferramentas\/./.test(location.hash)) history.back();
}
export function isToolRouted() { return toolRouted && $("tool-dialog").open; }
export function openToolById(id) {
  const tool = TOOLS.find(t => t[0] === id); if (!tool) return false;
  openTool(`${tool[1]} ${tool[2]}`, tool[4], id); return true;
}
export function hideTool() { toolRouted = false; $("tool-dialog").close(); (toolReturnFocus?.isConnected ? toolReturnFocus : $("collections").querySelector("button"))?.focus(); }
$("tool-close").onclick = closeTool;
$("tool-dialog").addEventListener("cancel", e => { e.preventDefault(); closeTool(); });
export async function toolJob(url, body, done) {
  const log = $("tool-log"); log.hidden = false; log.textContent = "";
  toolStatus("Rodando…"); $("tool-status").scrollIntoView({block: "nearest"});
  try {
    const result = await runJob(url, body, data => {
      if (data.type === "log") { log.textContent += data.line + "\n"; log.scrollTop = log.scrollHeight; }
      if (data.type === "progress" && data.status) toolStatus(`${data.status}${data.total ? ` ${Math.floor(100 * data.feito / data.total)}%` : ""}…`);
    });
    toolStatus(result.message || (result.ok ? "Concluído." : "Terminou com erro; veja o registro."), !result.ok);
    if (done) await done(result);
    return result;
  } catch (e) { toolStatus(e.message, true); }
}
const TOOLS = [
  ["organizar", "🗂", "Organizar ROMs novas", "Move o que chegou na pasta de organizar para o sistema certo", toolOrganize],
  ["memcards", "💾", "Memory cards PS1/PS2", "Exportar, transferir, importar e apagar saves dos cards", toolMemcards],
  ["celular-psp", "📱", "Saves do celular (PSP)", "Baixa para o PC os saves do PPSSPP do celular, pelo cabo", toolPhoneSaves],
  ["nuvem", "☁", "Saves na nuvem", "Comparar, sincronizar e escolher versões em conflito", toolCloudSaves],
  ["texturas", "🎨", "Texturas HD", "Catálogo completo, no PC ou no celular, e importar arquivo ou link", toolTextures],
  ["biblioteca", "📚", "Biblioteca", "Atualizar Heroic, Steam e Switch, buscar capas e adicionar jogos", toolLibrary],
  ["capas", "🖼", "Capas dos sistemas", "Buscar capas que faltam nas ROMs leves e pesadas", toolCovers],
  ["manutencao", "🛠", "Manutenção", "Backups, nomes, playlists e sincronização de saves", toolMaintenance],
  ["configuracoes", "⚙", "Configurações", "Pastas do PC e do celular usadas pelo PyRetro", toolSettings],
  ["diagnostico", "🩺", "Diagnóstico", "Confere pastas e programas; relatório sem dados privados", toolDiagnostics],
  ["primeiros-passos", "🚀", "Primeiros passos", "Cria a configuração e as pastas que faltam e avisa o que o setup precisa instalar", toolSetup],
];
export function renderTools() {
  $("gallery").replaceChildren(...TOOLS.map(([id, symbol, title, text, open]) => {
    const card = button("", () => openTool(`${symbol} ${title}`, open, id)); card.className = "game system-card stat-card";
    card.append(Object.assign(document.createElement("span"), {className: "system-symbol", textContent: symbol}),
      Object.assign(document.createElement("strong"), {textContent: title}), Object.assign(document.createElement("small"), {textContent: text}));
    return card;
  }));
  report("Ferramentas de organização e manutenção. Ações que mexem em arquivos pedem confirmação.");
}

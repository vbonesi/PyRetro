/* Modo TV: cliente das mesmas APIs da GUI, sem acesso direto ao acervo. */
import {api} from "./tv/api.js";
import {collectionTabs, drawGame, findGameByKey, load, updateFilters} from "./tv/catalog.js";
import {$, report} from "./tv/dom.js";
import {viewOf} from "./tv/library.js";
import {focusSidebar} from "./tv/sidebar.js";
import {closeGame, hideGame, openGame} from "./tv/game.js";
import {scrollTarget, stickScroll} from "./tv/focus.js";
import {action, applyGlyphs, padFamily, pollGamepad} from "./tv/input.js";
import {applyPreferences} from "./tv/settings.js";
import {toolCloudSaves} from "./tv/tools-pages.js";
import {watchSession} from "./tv/play.js";
import {state} from "./tv/state.js";
import {closeTool, hideTool, isToolRouted, openTool, openToolById} from "./tv/tools.js";
import {onRouteChange, parseRoute, replaceRoute, routeFor} from "./tv/router.js";
// Módulos que só ligam os botões da ficha e dos Desejados ao carregar: ninguém importa nada deles.
import "./tv/game-edit.js";
import "./tv/game-files.js";
import "./tv/game-textures.js";
import "./tv/wishlist.js";
if (window.ResizeObserver) new ResizeObserver(entries => {
  document.documentElement.style.setProperty("--footer-height", `${entries[0].target.getBoundingClientRect().height}px`);
}).observe(document.querySelector("footer"));
async function openLinkedGame(key) {
  const game = await findGameByKey(key);
  if (game) openGame(game);
  else { replaceRoute(routeFor(state.kind, state.code, state.query, viewOf())); report("O jogo desse link não está mais disponível no catálogo.", true); }
}
// Aplica o endereço atual à tela (carga inicial e voltar/avançar do navegador). A coleção só recarrega
// quando mudou; ficha e ferramenta sobem ou descem conforme o endereço, sem mexer no histórico.
async function applyRoute(route) {
  if (!route.game && $("details").open) hideGame();
  if (!route.tool && isToolRouted()) hideTool();
  if (route.kind === "library") {
    const same = state.kind === "library" && !route.view.system && JSON.stringify({...viewOf(), query: state.query}) === JSON.stringify({quick: route.view.quick, filter: route.view.filter, genre: route.view.genre, order: route.view.order, installed: route.view.installed, query: route.view.query});
    if (!same) await load("library", "", route.view);
  } else if (route.kind && route.kind !== state.kind) await load(route.kind);
  if (route.game && !$("details").open) await openLinkedGame(route.game);
  if (route.tool && !isToolRouted()) openToolById(route.tool);
}
async function init() {
  collectionTabs();
  // Instalação nova (sem config.toml ou sem pastas): abre os Primeiros passos em vez de falhar no catálogo.
  try { const setup = await api("/api/setup/status"); if (!setup.ready) { replaceRoute(routeFor("home")); openToolById("primeiros-passos"); return; } } catch {}
  try {
    [state.systems, state.light] = await Promise.all([api("/api/heavy/systems"), api("/api/systems")]);
    // Ficha e ferramenta abrem sobre a tela de baixo (Início ou o grid de Ferramentas), que entra no histórico
    // antes, para o voltar não sair do PyRetro.
    const route = parseRoute(), underlying = route.game ? {kind: "home"} : route.tool ? {kind: "tools"} : route;
    if (route.game || route.tool) replaceRoute(routeFor(underlying.kind));
    await load(underlying.kind, "", underlying.view);
    if (route.game) await openLinkedGame(route.game);
    if (route.tool) openToolById(route.tool);
    const key = new URLSearchParams(location.search).get("game");
    if (key) await openLinkedGame(key);
  }
  catch (e) { report(`Não foi possível iniciar: ${e.message}. Recarregue para tentar novamente.`, true); }
  if (state.kind !== "home") focusSidebar();
}
onRouteChange(applyRoute);
requestAnimationFrame(pollGamepad); init();
api("/api/play/status").then(watchSession).catch(() => {});

applyGlyphs(); updateFilters();

// Ganchos para os testes (tests/test_app.html): o código em módulo não vaza nomes para o escopo global.
Object.assign(window, {load, drawGame, watchSession, openLinkedGame, action, openTool, closeTool, openGame, closeGame, padFamily, stickScroll, scrollTarget, applyPreferences, toolCloudSaves});

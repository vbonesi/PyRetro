import {gameCard} from "./cards.js";
import {launchApp, load} from "./catalog.js";
import {$, button, report} from "./dom.js";
import {openGame} from "./game.js";
import {state, ui} from "./state.js";
export function showSpotlight(g) {
  ui.spotlightGame = g;
  $("spotlight-title").textContent = g.name;
  $("spotlight-meta").textContent = [g.platform, g.local ? "Pronto neste PC" : g.downloadName ? "Disponível no Drive" : "Na sua biblioteca", g.tracking.genero, g.favorite ? "★ Favorito" : ""].filter(Boolean).join(" · ");
  $("spotlight-art").style.backgroundImage = g.cover ? `url(${JSON.stringify(g.cover)})` : "none";
  $("spotlight-open").textContent = "Ver jogo";
  const logo = $("spotlight-logo"), video = $("spotlight-video");
  logo.hidden = !g.media?.logo; if (g.media?.logo) logo.src = g.media.logo;
  const source = g.media?.video || "";
  if (video.dataset.source !== source) { video.pause(); video.removeAttribute('src'); video.dataset.source = source; if (source) video.src = source; }
  video.hidden = !source;
  if (source && !document.hidden && !document.querySelector('dialog[open]') && !matchMedia('(prefers-reduced-motion: reduce)').matches) video.play().catch(() => {});
}
function shelfControls(row, title) {
  const controls = document.createElement('div'); controls.className = 'shelf-controls';
  const move = direction => row.scrollBy({left: direction * Math.max(160, row.clientWidth * .8), behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
  const previous = button('‹', () => move(-1)), next = button('›', () => move(1));
  previous.setAttribute('aria-label', `Voltar na fileira: ${title}`);
  next.setAttribute('aria-label', `Avançar na fileira: ${title}`);
  const update = () => {
    previous.disabled = row.scrollLeft <= 1;
    next.disabled = row.scrollLeft >= row.scrollWidth - row.clientWidth - 1;
  };
  row.addEventListener('scroll', update, {passive:true});
  row.addEventListener('wheel', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || Math.abs(event.deltaX) >= Math.abs(event.deltaY)) return;
    const delta = event.deltaY * (event.deltaMode === 1 ? 20 : event.deltaMode === 2 ? row.clientWidth : 1);
    const end = row.scrollWidth - row.clientWidth;
    if (delta > 0 ? row.scrollLeft >= end - 1 : row.scrollLeft <= 1) return;
    event.preventDefault(); row.scrollLeft = Math.max(0, Math.min(end, row.scrollLeft + delta)); update();
  }, {passive:false});
  // ResizeObserver reage também à troca de largura do painel, não só à janela.
  const observer = new ResizeObserver(update); observer.observe(row);
  shelfObservers.push(observer);
  requestAnimationFrame(update); controls.append(previous, next); return controls;
}
const shelfObservers = [];
$("spotlight-open").onclick = () => { if (ui.spotlightGame) openGame(ui.spotlightGame); };
export function renderHome() {
  shelfObservers.splice(0).forEach(observer => observer.disconnect());
  const box = $("home"); box.replaceChildren();
  const home = state.home; $("spotlight").hidden = !home;
  if (!home) return;
  const quick = document.createElement("section"); quick.className = "quick-access"; quick.dataset.region = "acesso-rapido"; quick.setAttribute("aria-label", "Acesso rápido");
  for (const appId of ["greenlight", "chiaki", "sysdvr", "steam", "heroic"]) {
    const app = home.apps?.find(g => g.id === appId);
    if (app) { const b = button(`${app.icon} ${app.name}`, () => launchApp(app)); b.dataset.app = appId; quick.append(b); }
  }
  quick.append(button("🕹 Emuladores", () => load("systems")), button("▦ Todos neste PC", () => load("local")));
  box.append(quick);
  for (const [key, title] of [["recent", "Jogados recentemente"], ["continue", "Continuar jogando"], ["favorites", "Seus favoritos"], ["mostPlayed", "Mais jogados"], ["installed", "Steam e Heroic · prontos para jogar"], ["ready", "Explore seu acervo local"]]) {
    const games = home[key] || []; if (!games.length) continue;
    const section = document.createElement("section"); section.className = "home-section"; section.dataset.shelf = key;
    const heading = document.createElement("h3"); heading.textContent = title;
    const row = document.createElement("div"); row.className = "shelf"; row.dataset.region = `fileira-${key}`; row.setAttribute("aria-label", title);
    for (const game of games) row.append(gameCard(game));
    const head = document.createElement('div'); head.className = 'shelf-heading';
    head.append(heading, shelfControls(row, title));
    section.append(head, row); box.append(section);
  }
  const all = [home.recent, home.continue, home.favorites, home.installed, home.ready, home.mostPlayed].flatMap(g => g || []);
  const featured = all.find(g => ui.spotlightGame?.key && g.key === ui.spotlightGame.key) || all[0];
  $("spotlight").hidden = !featured; if (featured) showSpotlight(featured);
  if (!all.length) { const empty = document.createElement("p"); empty.className = "hint"; empty.textContent = "Sua próxima partida começa aqui. Abra Neste PC ou explore os sistemas. Os jogos que você abrir aparecerão em Recentes; X guarda seus favoritos."; box.append(empty); }
  report(home.counts ? `${home.counts.local || 0} jogos neste PC · ${home.counts.pc || 0} da Steam e Heroic` : "Escolha sua próxima partida.");
}

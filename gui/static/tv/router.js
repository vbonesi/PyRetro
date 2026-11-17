/* Rotas por hash (#/biblioteca, #/jogo/<chave>, #/ferramentas/<id>…): recarregar volta à mesma tela e o
   voltar do navegador (Alt+←, botão do mouse) percorre as telas. Aqui só se lê e se grava o endereço;
   quem aplica a rota é o tv.js (evita dependência circular com as telas). */
const KIND_PATH = {
  home: "inicio", library: "biblioteca", wishlist: "desejados", apps: "apps", tools: "ferramentas",
  local: "neste-pc", favorites: "favoritos", systems: "sistemas", playing: "jogando", ranking: "ranking",
  stats: "estatisticas", draw: "sortear", heavy: "roms-pesadas", light: "roms-leves", search: "busca",
};
const PATH_KIND = Object.fromEntries(Object.entries(KIND_PATH).map(([kind, path]) => [path, kind]));

export function routeFor(kind, code = "", query = "") {
  const path = KIND_PATH[kind] || KIND_PATH.home;
  if ((kind === "heavy" || kind === "light") && code) return `#/${path}/${encodeURIComponent(code)}`;
  if (kind === "search" && query) return `#/${path}?q=${encodeURIComponent(query)}`;
  return `#/${path}`;
}
export const gameRoute = key => `#/jogo/${encodeURIComponent(key)}`;
export const toolRoute = id => `#/ferramentas/${encodeURIComponent(id)}`;

// {kind, code, query} para uma coleção; {game: chave} para a ficha; {kind: "tools", tool: id} para uma ferramenta.
export function parseRoute(hash = location.hash) {
  const [path, search = ""] = hash.replace(/^#\/?/, "").split("?");
  const [head = "", arg = ""] = path.split("/").map(decodeURIComponent);
  if (head === "jogo" && arg) return {game: arg};
  if (head === "ferramentas" && arg) return {kind: "tools", tool: arg};
  const kind = PATH_KIND[head];
  if (!kind) return {kind: "home"};
  return {kind, code: arg, query: new URLSearchParams(search).get("q") || ""};
}
export const isOverlayRoute = (hash = location.hash) => /^#\/(jogo|ferramentas)\/./.test(hash);

// Documento sem endereço próprio (about:srcdoc, o iframe dos testes) recusa pushState/replaceState: aí a
// tela funciona igual, só sem rota.
function writeHistory(method, hash) { try { history[method](null, "", hash); } catch (_) { /* sem rota */ } }
// Grava o endereço sem disparar o tratamento de rota. Primeira entrada (sem hash) e fechamento de
// ficha/ferramenta pendente substituem a entrada atual; o resto empilha, para o voltar funcionar.
export function syncRoute(hash) {
  if (location.hash === hash) return;
  writeHistory(!location.hash || isOverlayRoute() ? "replaceState" : "pushState", hash);
}
export function pushOverlay(hash) { if (location.hash !== hash) writeHistory("pushState", hash); }
export function replaceRoute(hash) { writeHistory("replaceState", hash); }
export function onRouteChange(handler) { window.addEventListener("popstate", () => handler(parseRoute())); }

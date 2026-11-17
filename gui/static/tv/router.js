/* Rotas por hash (#/biblioteca, #/jogo/<chave>, #/ferramentas/<id>…): recarregar volta à mesma tela e o
   voltar do navegador (Alt+←, botão do mouse) percorre as telas. Aqui só se lê e se grava o endereço;
   quem aplica a rota é o tv.js (evita dependência circular com as telas). */
const KIND_PATH = {home: "inicio", library: "biblioteca", wishlist: "desejados", apps: "apps", tools: "ferramentas", stats: "estatisticas", draw: "sortear"};
const PATH_KIND = Object.fromEntries(Object.entries(KIND_PATH).map(([kind, path]) => [path, kind]));
// Endereços das coleções antigas continuam valendo: viram filtros da Biblioteca única.
const LEGACY_QUICK = {"neste-pc": "local", favoritos: "favorites", jogando: "playing", ranking: "ranking"};

// Filtros da Biblioteca no endereço: ?f=<rápido>&s=<sistema>&g=<gênero>&o=<ordem>&l=1 (só local)&q=<busca>.
export function routeFor(kind, code = "", query = "", view = {}) {
  const path = KIND_PATH[kind] || KIND_PATH.home;
  if (kind !== "library") return `#/${path}`;
  const params = new URLSearchParams();
  if (view.quick && view.quick !== "all") params.set("f", view.quick);
  if (view.filter) params.set("s", view.filter);
  if (view.genre) params.set("g", view.genre);
  if (view.order) params.set("o", view.order);
  if (view.installed) params.set("l", "1");
  if (query) params.set("q", query);
  const text = params.toString();
  return `#/${path}${text ? `?${text}` : ""}`;
}
export const gameRoute = key => `#/jogo/${encodeURIComponent(key)}`;
export const toolRoute = id => `#/ferramentas/${encodeURIComponent(id)}`;

// {kind, view} para uma coleção (view: filtros da Biblioteca); {game: chave} para a ficha; {kind: "tools", tool: id} para uma ferramenta.
export function parseRoute(hash = location.hash) {
  const [path, search = ""] = hash.replace(/^#\/?/, "").split("?");
  const [head = "", arg = ""] = path.split("/").map(decodeURIComponent);
  const params = new URLSearchParams(search);
  if (head === "jogo" && arg) return {game: arg};
  if (head === "ferramentas" && arg) return {kind: "tools", tool: arg};
  const library = view => ({kind: "library", view: {quick: "all", filter: "", genre: "", order: "", installed: false, query: "", ...view}});
  if (head === "biblioteca") return library({quick: params.get("f") || "all", filter: params.get("s") || "", genre: params.get("g") || "", order: params.get("o") || "", installed: params.get("l") === "1", query: params.get("q") || ""});
  if (LEGACY_QUICK[head]) return library({quick: LEGACY_QUICK[head]});
  if (head === "sistemas") return library({});
  if (head === "busca") return library({query: params.get("q") || ""});
  if (head === "roms-pesadas" || head === "roms-leves") return library({system: arg});
  const kind = PATH_KIND[head];
  return {kind: kind || "home"};
}
export const isOverlayRoute = (hash = location.hash) => /^#\/(jogo|ferramentas)\/./.test(hash);

// Documento sem endereço próprio (about:srcdoc, o iframe dos testes) recusa pushState/replaceState: aí a
// tela funciona igual, só sem rota.
function writeHistory(method, hash, data = null) { try { history[method](data, "", hash); } catch (_) { /* sem rota */ } }
// Grava o endereço sem disparar o tratamento de rota. Primeira entrada (sem hash) e fechamento de
// ficha/ferramenta pendente substituem a entrada atual; o resto empilha, para o voltar funcionar.
export function syncRoute(hash) {
  if (location.hash === hash) return;
  writeHistory(!location.hash || isOverlayRoute() ? "replaceState" : "pushState", hash);
}
// Filtro mudou na mesma tela: troca o endereço sem empilhar histórico (nem mexe numa ficha/ferramenta aberta).
export function replaceView(hash) { if (location.hash !== hash && !isOverlayRoute()) writeHistory("replaceState", hash); }
// A ficha/ferramenta guarda no histórico de onde veio (coleção e filtros): recarregar nela e voltar levam à origem.
export function pushOverlay(hash) { if (location.hash !== hash) writeHistory("pushState", hash, {from: isOverlayRoute() ? (history.state?.from || "") : location.hash}); }
export const overlayOrigin = () => { const from = history.state?.from; return typeof from === "string" && from && !isOverlayRoute(from) ? from : ""; };
export function replaceRoute(hash) { writeHistory("replaceState", hash); }
export function onRouteChange(handler) { window.addEventListener("popstate", () => handler(parseRoute())); }

import {api} from "./api.js";
import {render} from "./catalog.js";
import {$, report} from "./dom.js";
import {applyPreferences} from "./settings.js";
import {cardGames, state, ui} from "./state.js";
function focusedGame() { return $("details").open ? state.selected : cardGames.get(document.activeElement) || (document.activeElement === $("spotlight-open") ? ui.spotlightGame : null); }
export function updateFavoriteButton(g) { $("favorite").textContent = g.favorite ? "★ Favorito" : "☆ Favoritar"; $("favorite").setAttribute("aria-pressed", String(!!g.favorite)); }
export async function toggleFavorite(g = focusedGame()) {
  if (!g || state.busy) return;
  state.busy = true; const active = document.activeElement; const identity = active.dataset?.key; const shelf = active.closest?.("[data-shelf]")?.dataset.shelf;
  try {
    const preferences = await api("/api/tv/favorite", {key: g.key, id: g.id, code: g.code, name: g.romName, favorite: !g.favorite});
    g.key = preferences.key; g.favorite = !g.favorite; applyPreferences(preferences);
    for (const item of [...state.items, ...["recent", "continue", "favorites", "installed", "ready", "mostPlayed"].flatMap(k => state.home?.[k] || [])]) if (item.key) item.favorite = preferences.favorites.includes(item.key);
    if (state.home) state.home.favorites = [...state.home.favorites.filter(x => x.key !== g.key), ...(g.favorite ? [g] : [])];
    if (state.kind === "favorites") state.items = state.items.filter(x => x.favorite);
    render(); updateFavoriteButton(g);
    if (!$("details").open) {
      const cards = [...document.querySelectorAll("#home .game,#gallery .game")];
      (cards.find(c => c.dataset.key === (identity || g.key) && c.closest("[data-shelf]")?.dataset.shelf === shelf) || cards.find(c => c.dataset.key === g.key) || cards[0])?.focus();
    }
    report(g.favorite ? "Guardado nos favoritos." : "Removido dos favoritos.", false, $("details").open ? "detail-status" : "message");
  } catch (e) { report(`Não foi possível atualizar favorito: ${e.message}`, true, $("details").open ? "detail-status" : "message"); }
  finally { state.busy = false; }
}
$("favorite").onclick = () => toggleFavorite(state.selected);

/* Menu de contexto do jogo (botão direito do mouse, tecla Menu do teclado): opções do jogo sem abrir a ficha inteira. */
import {$, button} from "./dom.js";
import {toggleFavorite} from "./favorites.js";
import {openGame} from "./game.js";
let owner;
const menu = () => $("context-menu");
export function closeContextMenu(refocus = true) {
  if (menu().hidden) return;
  menu().hidden = true; menu().replaceChildren();
  if (refocus && owner?.isConnected) owner.focus({preventScroll: true});
  owner = null;
}
export const contextMenuOpen = () => !menu().hidden;
// Abre a ficha e já expande o painel pedido (Editar, Capa, Saves, Progresso).
function openPanel(g, card, toggleId) { openGame(g, card); const toggle = $(toggleId); if (toggle && !toggle.hidden) toggle.click(); }
export function openContextMenu(g, card, x, y) {
  closeContextMenu(false); owner = card;
  const items = [["Abrir", () => openGame(g, card)]];
  if (!g.wishlist) {
    items.push([g.favorite ? "★ Tirar dos favoritos" : "☆ Favoritar", () => toggleFavorite(g)]);
    items.push(["✎ Editar jogo", () => openPanel(g, card, "edit-toggle")], ["🖼 Capa", () => openPanel(g, card, "cover-toggle")]);
    if (g.code) items.push(["💾 Saves", () => openPanel(g, card, "saves-toggle")]);
    items.push(["Progresso e tempo", () => openPanel(g, card, "progress-toggle")]);
  }
  menu().replaceChildren(...items.map(([label, run]) => button(label, () => { closeContextMenu(false); run(); })));
  menu().hidden = false;
  const box = menu().getBoundingClientRect();
  menu().style.left = `${Math.max(4, Math.min(x, innerWidth - box.width - 4))}px`;
  menu().style.top = `${Math.max(4, Math.min(y, innerHeight - box.height - 4))}px`;
  menu().querySelector("button")?.focus();
}
// Navegação própria: ↑/↓ percorrem o menu, Esc fecha e devolve o foco ao card; clicar fora também fecha.
document.addEventListener("keydown", e => {
  if (menu().hidden) return;
  const buttons = [...menu().querySelectorAll("button")], index = buttons.indexOf(document.activeElement);
  if (e.key === "Escape" || e.key === "ArrowLeft") { e.preventDefault(); e.stopImmediatePropagation(); closeContextMenu(); }
  else if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); e.stopImmediatePropagation(); buttons[(index + (e.key === "ArrowDown" ? 1 : -1) + buttons.length) % buttons.length]?.focus(); }
}, true);
document.addEventListener("pointerdown", e => { if (!menu().hidden && !menu().contains(e.target)) closeContextMenu(false); }, true);
window.addEventListener("blur", () => closeContextMenu(false));
document.addEventListener("scroll", () => closeContextMenu(false), true);

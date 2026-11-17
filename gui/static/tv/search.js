import {filtersChanged, load} from "./catalog.js";
import {$, button} from "./dom.js";
import {state} from "./state.js";
let searchReturnFocus, textEntry = null;
export function openSearch() {
  if (document.querySelector("dialog[open]")) return;
  textEntry = null; searchDialogLabels("Pesquisar jogos", "Nome do jogo", "Pesquisar", "Limpar busca");
  searchReturnFocus = document.activeElement; $("search-input").value = state.query;
  $("search-dialog").showModal(); $("keyboard").querySelector("button")?.focus();
}
// O mesmo teclado da tela serve para editar texto (nome, gênero, comentário…) com o controle.
export function openTextEntry(title, value, apply) {
  textEntry = apply; searchDialogLabels(title, title, "Confirmar", "Apagar tudo");
  searchReturnFocus = document.activeElement; $("search-input").value = value || "";
  $("search-dialog").showModal(); $("keyboard").querySelector("button")?.focus();
}
function searchDialogLabels(title, label, apply, clear) {
  $("search-title").textContent = title; $("search-label").textContent = label;
  $("search-apply").textContent = apply; $("search-clear").textContent = clear;
  $("search-hint").textContent = textEntry ? "Direcional e A no teclado abaixo; ⇧ troca maiúsculas. X apaga; Menu confirma; B cancela." : "Use o direcional e A no teclado abaixo. X apaga; Menu pesquisa; B cancela.";
}
export function closeSearch() { $("search-dialog").close(); textEntry = null; (searchReturnFocus?.isConnected ? searchReturnFocus : $("search-open"))?.focus(); }
export async function applySearch() {
  if (textEntry) { const apply = textEntry, value = $("search-input").value.trim(); closeSearch(); return apply(value); }
  state.query = $("search-input").value.trim(); closeSearch();
  if (state.kind !== "library") await load("library", "", {query: state.query}); else filtersChanged();
  $("gallery").querySelector("button")?.focus();
}
let keyboardLower = false;
function buildKeyboard() {
  const keys = [..."1234567890QWERTYUIOPASDFGHJKLÇZXCVBNM -':./,&!?()"].map(c => keyboardLower ? c.toLowerCase() : c);
  $("keyboard").replaceChildren(...keys.map(character => button(character === " " ? "␣" : character, () => { const input = $("search-input"); input.value = (input.value + character).slice(0, 2000); })),
    button("⌫", () => { $("search-input").value = $("search-input").value.slice(0, -1); }),
    button(keyboardLower ? "⇧ ABC" : "⇧ abc", () => { keyboardLower = !keyboardLower; buildKeyboard(); $("keyboard").lastChild.focus(); }));
}
buildKeyboard();
$("search-open").onclick = openSearch; $("search-close").onclick = closeSearch;
$("search-apply").onclick = applySearch;
$("search-clear").onclick = () => { $("search-input").value = ""; if (!textEntry) applySearch(); else $("search-input").focus(); };
$("search-dialog").addEventListener("cancel", e => { e.preventDefault(); closeSearch(); });
$("search-input").addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); applySearch(); } });

/* Páginas (ficha do jogo e ferramentas): ocupam a área de conteúdo, têm endereço e não são <dialog>. Só confirmações
   e o teclado da tela (busca, edição de texto) continuam como diálogo. O elemento ganha `open` e `close()` para
   o resto do código e os testes tratarem página e diálogo do mesmo jeito. */
import {$} from "./dom.js";
let scrollBefore = 0;
export const pageOpen = () => document.body.classList.contains("page-open");
// Algum diálogo modal (busca, opções, confirmação) aberto: bloqueia atalhos de navegação.
export const modalOpen = () => !!document.querySelector("dialog[open]");
export function openPage(el) {
  if (!pageOpen()) scrollBefore = window.scrollY;
  el.hidden = false; document.body.classList.add("page-open"); window.scrollTo(0, 0);
}
export function closePage(el) {
  el.hidden = true;
  if (![...document.querySelectorAll(".page")].some(p => !p.hidden)) { document.body.classList.remove("page-open"); window.scrollTo(0, scrollBefore); }
}
// Troca de destino (barra lateral, LT/RT, teclas 1–5) fecha qualquer página aberta.
export function closeAllPages() {
  $("detail-video").pause();
  for (const el of document.querySelectorAll(".page")) if (!el.hidden) closePage(el);
}
for (const id of ["details", "tool-dialog"]) {
  const el = $(id);
  Object.defineProperty(el, "open", {get: () => !el.hidden});
  el.close = () => closePage(el);
}

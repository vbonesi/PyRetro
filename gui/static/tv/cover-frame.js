import {$} from "./dom.js";
// Moldura 3:4 única para todas as capas (N10). A regra de encaixe é pura e testável:
// proporção (largura/altura) entre 0,62 e 0,9 preenche com corte leve; o resto fica inteiro sobre a própria capa desfocada.
export function coverFit(width, height) {
  if (!width || !height) return "contain";
  const ratio = width / height;
  return ratio >= 0.62 && ratio <= 0.9 ? "cover" : "contain";
}
function fitWhenLoaded(frame, img) {
  const apply = () => { frame.dataset.fit = coverFit(img.naturalWidth, img.naturalHeight); };
  frame.dataset.fit = "contain";
  if (img.complete && img.naturalWidth) apply(); else img.addEventListener("load", apply, {once: true});
}
function setBackdrop(frame, src) { frame.style.setProperty("--cover-url", `url(${JSON.stringify(src)})`); }
export function coverFrame(src, className = "") {
  const frame = document.createElement("div"); frame.className = `art cover-frame ${className}`.trim();
  const img = document.createElement("img"); img.src = src; img.alt = ""; img.loading = "lazy";
  setBackdrop(frame, src); frame.append(img); fitWhenLoaded(frame, img); return frame;
}
// Capa da ficha: o <img> já existe no HTML, dentro de #detail-cover-frame.
export function setDetailCover(src) {
  const frame = $("detail-cover-frame"), img = $("detail-cover");
  frame.hidden = !src; if (!src) return;
  setBackdrop(frame, src); img.src = src; fitWhenLoaded(frame, img);
}

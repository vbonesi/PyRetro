/* 🎮 Onde jogar (ficha): o card fora do retrô diz em quais plataformas do Victor o jogo existe (Switch, PS4, Xbox,
   PC, Switch 2) e onde ele o tem. Tudo grava por /api/onde-roda/* (core/onde_roda.py); a correção manual vence a pesquisa. */
import {api} from "./api.js";
import {render} from "./catalog.js";
import {$, report} from "./dom.js";
import {fillBadges} from "./cards.js";
import {openChoicePanel} from "./panel.js";
import {openTextEntry} from "./search.js";
import {RODA, rodaOf, state} from "./state.js";
const LOJAS = ["Steam", "Epic", "GOG", "Amazon"];
async function post(acao, body) {
  const g = state.selected; if (!g || state.busy) return;
  state.busy = true;
  try {
    const r = await api(`/api/onde-roda/${acao}`, {id: g.id, ...body});
    g.tracking = {...g.tracking, onde_roda: r.onde_roda, jogar: r.jogar};
    fillBadges($("game-badges"), g); render();
    report("Salvo.", false, "detail-status");
  } catch (e) { report(e.message, true, "detail-status"); }
  finally { state.busy = false; }
}
function askStore(from) {
  const items = [...LOJAS.map(l => [l, l]), ["__outra", "Outra loja…"]];
  openChoicePanel("Em qual loja do PC?", [{items}], "", v => {
    if (v === "__outra") openTextEntry("Loja do PC", "", loja => { if (loja) post("jogar", {estado: "tenho", plataforma: "pc", loja}); });
    else post("jogar", {estado: "tenho", plataforma: "pc", loja: v});
  }, from);
}
export function openOnde(from) {
  const g = state.selected; if (!g) return;
  const jogar = g.tracking?.jogar || {}, existe = id => g.tracking?.onde_roda?.[id];
  const mark = id => existe(id)?.existe === true ? "existe" : existe(id)?.existe === false ? "não existe" : "sem informação";
  openChoicePanel(`Onde jogar: ${g.name}`, [
    {items: [["quero", `${jogar.estado === "quero" ? "● " : ""}♡ Quero jogar`]]},
    {heading: "Baixei ou comprei em…", items: RODA.map(([id, label]) => [`tenho:${id}`, `${jogar.estado === "tenho" && jogar.plataforma === id ? "● " : ""}${label}${id === "pc" && jogar.loja && jogar.plataforma === "pc" ? ` (${jogar.loja})` : ""}`])},
    {heading: "Corrigir disponibilidade (vale mais que a pesquisa)", items: RODA.flatMap(([id, label]) => [
      [`sim:${id}`, `${label}: existe${existe(id)?.manual && existe(id).existe ? " ✎" : ""}`], [`nao:${id}`, `${label}: não existe${existe(id)?.manual && existe(id).existe === false ? " ✎" : ""}`]])
      .concat(RODA.filter(([id]) => existe(id)?.manual).map(([id, label]) => [`auto:${id}`, `${label}: voltar à pesquisa (hoje ${mark(id)})`]))},
  ], "", v => {
    const [acao, id] = v.split(":");
    if (v === "quero") post("jogar", {estado: "quero"});
    else if (acao === "tenho") id === "pc" ? askStore(from) : post("jogar", {estado: "tenho", plataforma: id});
    else if (acao === "sim" || acao === "nao") post("set", {plataforma: id, existe: acao === "sim"});
    else if (acao === "auto") post("reset", {plataforma: id});
  }, from);
}
$("onde-jogar").onclick = () => openOnde($("onde-jogar"));

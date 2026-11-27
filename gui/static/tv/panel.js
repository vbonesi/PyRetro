/* Painel lateral à direita (gaveta) para escolher filtro, gênero, ordem ou ação: uma lista vertical, ↑/↓ move,
   A escolhe, B fecha sem mudar. Substitui as faixas de chips com rolagem lateral do cabeçalho (N11).
   O painel é um <dialog> modal: o motor de foco (focus.js) já restringe o foco ao diálogo aberto. */
import {$, button} from "./dom.js";
let opener = null, borrowed = [];
export const panelOpen = () => $("panel").open;
const heading = text => Object.assign(document.createElement("h4"), {textContent: text});
// Grupos de plataformas no painel; o que não casa com nenhum vai para "Outros".
const PLATFORM_GROUPS = [
  ["Sony", /playstation|^ps\d?\b|\bpsp\b|vita|\bpsn\b/i], ["Nintendo", /nintendo|game ?boy|\bgba\b|\bnes\b|snes|\bn64\b|famicom|gamecube|\bwii\b|switch|\bds\b|3ds|virtual boy/i],
  ["Sega", /sega|mega drive|genesis|saturn|dreamcast|master system|game gear/i], ["Arcade", /arcade|neo.?geo|fbneo|mame|cps/i],
  ["PC e lojas", /steam|gog|epic|amazon|xbox|\bpc\b|heroic|windows|ubisoft|origin|biblioteca/i],
];
export const platformGroup = name => PLATFORM_GROUPS.find(([, test]) => test.test(name))?.[0] || "Outros";
export function groupPlatforms(names) {
  const groups = new Map(PLATFORM_GROUPS.map(([label]) => [label, []])); groups.set("Outros", []);
  for (const name of names) groups.get(platformGroup(name)).push(name);
  return [...groups].filter(([, list]) => list.length).map(([label, list]) => ({heading: label, items: list.sort((a, b) => a.localeCompare(b, "pt-BR"))}));
}
function show(title, from) {
  opener = from || document.activeElement; $("panel-title").textContent = title;
  $("panel").showModal();
}
// `groups`: [{heading?, items: [[valor, texto, ícone?]]}]; `current` marca o valor atual e recebe o foco.
export function openChoicePanel(title, groups, current, pick, from) {
  const list = $("panel-list"); list.replaceChildren(); list.className = "panel-choices";
  let focus = null;
  for (const group of groups) {
    if (group.heading) list.append(heading(group.heading));
    for (const [value, label, icon] of group.items) {
      const b = button(label, () => { closePanel(); pick(value); }, value === current);
      if (icon) b.prepend(icon);
      b.dataset.value = value; if (value === current) focus = b; list.append(b);
    }
  }
  show(title, from); (focus || list.querySelector("button"))?.focus({preventScroll: true}); focus?.scrollIntoView({block: "center"});
}
// ⋯ Ações: os botões reais (#tools) vêm para o painel enquanto ele está aberto, com os mesmos ids e ações.
export function openActionsPanel(from) {
  const list = $("panel-list"); list.replaceChildren(); list.className = "panel-actions";
  borrowed = [...$("tools").children]; list.append(...borrowed);
  show("Ações", from); list.querySelector("button:not([hidden])")?.focus({preventScroll: true});
}
export function closePanel() {
  if (!$("panel").open && !borrowed.length) return;
  if (borrowed.length) { $("tools").append(...borrowed); borrowed = []; }
  if ($("panel").open) $("panel").close();
  if (opener?.isConnected && opener.getClientRects().length) opener.focus({preventScroll: true});
  opener = null;
}
$("panel").addEventListener("cancel", e => { e.preventDefault(); closePanel(); });
// Um botão de ação clicado fecha o painel depois da própria ação (o clique chega antes, ao próprio botão).
$("panel-list").addEventListener("click", e => { const b = e.target.closest?.("button"); if (b && $("panel-list").classList.contains("panel-actions") && !b.dataset.confirm) queueMicrotask(closePanel); });
$("panel").addEventListener("click", e => { if (e.target === $("panel")) closePanel(); });

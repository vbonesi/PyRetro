import {$, button} from "./dom.js";
import {coverFrame} from "./cover-frame.js";
import {openContextMenu} from "./context.js";
import {openGame} from "./game.js";
import {showSpotlight} from "./home.js";
import {RODA, badgeKey, cardGames, observedSaves, rodaOf, state} from "./state.js";
function gameBadges(g) {
  const t = g.tracking || {}, badges = [];
  if (t.platinado) badges.push(['🏆 Platinado', 'Jogo platinado']);
  else if (t.finalizado) badges.push(['✓ Finalizado', 'Jogo finalizado']);
  else if (t.iniciado) badges.push(['▶ Jogando', 'Jogo iniciado']);
  if (t.nota != null) badges.push([`${notaEspecial(t.nota) ? '✦' : '★'} ${String(t.nota).replace('.', ',')}`, notaEspecial(t.nota) ? 'Nota: jogo muito especial' : 'Nota', notaColor(t.nota)]);
  const minutes = Math.floor((g.playtime?.seconds || 0) / 60);
  if (minutes > 0) badges.push([minutes >= 60 ? `⏱ ${Math.floor(minutes/60)}h${String(minutes%60).padStart(2,'0')}` : `⏱ ${minutes}min`, 'Tempo registrado neste PC']);
  // Selos de plataforma (Switch, PS4, Xbox, PC, Switch 2); ✓ marca onde o Victor tem o jogo.
  const jogar = t.jogar || {}, tamanho = id => t.onde_roda?.[id]?.gb;
  for (const [id, label] of rodaOf(g)) {
    const mine = jogar.estado === "tenho" && jogar.plataforma === id;
    badges.push([`${mine ? "✓ " : ""}${label}`, `${mine ? "Você tem este jogo" : "Existe"} no ${label}${tamanho(id) ? ` (~${String(tamanho(id)).replace(".", ",")} GB)` : ""}${mine && id === "pc" && jogar.loja ? ` · ${jogar.loja}` : ""}`]);
  }
  if (!rodaOf(g).length && jogar.estado === "quero") badges.push(["♡ Quero jogar", "Quero jogar; ainda sem plataforma conhecida"]);
  if (observedSaves.get(badgeKey(g))) badges.push(['💾', 'Save encontrado neste PC na última consulta']);
  return badges;
}
export function fillBadges(target, g) {
  target.replaceChildren();
  for (const [label, title, color] of gameBadges(g)) {
    const badge = document.createElement('span'); badge.className = 'badge';
    if (color) { badge.style.color = color; badge.style.borderColor = color; }
    badge.textContent = label; badge.title = title; badge.setAttribute('aria-label', `${title}: ${label}`);
    target.append(badge);
  }
  target.hidden = !target.children.length;
}
export function refreshBadges(g) {
  for (const card of document.querySelectorAll('.game')) {
    const item = cardGames.get(card);
    if (item && badgeKey(item) === badgeKey(g)) fillBadges(card.querySelector('.badges'), g);
  }
  if (state.selected === g) fillBadges($('game-badges'), g);
}
export function gameCard(g) {
    const card = button("", () => openGame(g, card)); card.className = "game";
    cardGames.set(card, g); card.dataset.key = g.key || (g.id ? `pc:${g.id}` : `${g.code}:${g.romName}`);
    card.addEventListener("focus", () => { if (state.kind === "home") showSpotlight(g); });
    // Mouse: botão direito favorita, igual ao X do controle.
    // Mouse: botão direito (ou a tecla Menu do teclado) abre as opções do jogo; do teclado o evento vem sem coordenadas.
    card.addEventListener("contextmenu", e => {
      e.preventDefault(); card.focus();
      const box = card.getBoundingClientRect(), keyboard = !e.clientX && !e.clientY;
      openContextMenu(g, card, keyboard ? box.left + box.width / 2 : e.clientX, keyboard ? box.top + box.height / 2 : e.clientY);
    });
    if (g.cover) card.append(coverFrame(g.cover));
    else { const art = document.createElement("div"); art.className = "art placeholder"; art.textContent = "✦"; card.append(art); }
    const title = document.createElement("strong"); title.textContent = (g.favorite ? "★ " : "") + g.name;
    const meta = document.createElement("small");
    meta.textContent = [g.platform, g.downloadName && !g.local ? "No Drive" : g.local ? "Neste PC" : ""].filter(Boolean).join(" · ");
    if (g.platform) meta.prepend(plataformaIcone(plataformaInfo(g.code, g.platform)));
    const badges = document.createElement('span'); badges.className = 'badges'; fillBadges(badges, g);
    card.append(title, meta, badges); return card;
}

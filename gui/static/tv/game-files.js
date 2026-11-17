import {api} from "./api.js";
import {load, reloadSelection} from "./catalog.js";
import {$, actions, button, confirmButton, fmtBytes, heading, hint, report, row} from "./dom.js";
import {closeGame, showMoreMenu} from "./game.js";
import {coverLabel} from "./game-cover.js";
import {openTextEntry} from "./search.js";
import {state} from "./state.js";
import {openTool, toolStatus} from "./tools.js";
// --- Renomear, apagar e decompor pela ficha --------------------------------
function describeCascade(c, verb) {
  const rom = {renomeado: "ROM renomeada", apagado: "ROM apagada", nao_encontrado: "ROM não encontrada", conflito: "já existe uma ROM com esse nome", ambiguo: "mais de um arquivo bate com esse nome; nada foi mexido"}[c.rom.status] || c.rom.status;
  return [rom, c.capa?.length ? "capa apagada" : "", c.saves.length ? `${c.saves.length} save(s) ${verb}` : "", c.states.length ? `${c.states.length} estado(s) ${verb}` : "",
    c.flat_skipped ? "saves da pasta antiga mantidos (nome usado em outro sistema)" : ""].filter(Boolean).join(" · ");
}
async function afterFileChange(message, error = false) {
  state.busy = false; closeGame(); await reloadSelection($("destinations").querySelector('[aria-current="page"]'));
  report(message, error);
}
$("rom-rename").onclick = () => {
  const g = state.selected, label = coverLabel(g), light = state.light.some(x => x.code === g.code);
  openTextEntry("Novo nome do arquivo", label, async name => {
    if (!name || name === label || state.busy) return;
    state.busy = true; report("Renomeando ROM, capa e saves…", false, "detail-status");
    try {
      const r = await api(light ? "/api/cover/rename" : "/api/heavy/rename", light ? {code: g.code, label, new_label: name} : {code: g.code, old_label: label, new_label: name});
      // Mantém o cadastro da Biblioteca ligado ao nome novo (mesmo cuidado da web).
      if (g.id) await api("/api/library/edit", {id: g.id, campos: {nome: r.new_label}}).catch(() => {});
      await afterFileChange(`${label} → ${r.new_label}: ${describeCascade(r.cascade, "renomeado(s)")}`);
    } catch (e) { state.busy = false; report(`Não renomeou: ${e.message}`, true, "detail-status"); }
  });
};
$("rom-delete").onclick = async () => {
  const g = state.selected, b = $("rom-delete"), light = state.light.some(x => x.code === g.code); if (state.busy || !g) return;
  if (!b.dataset.confirm) { showMoreMenu(); b.dataset.confirm = "yes"; b.textContent = "Confirmar: apagar de vez"; report(`Apagar "${g.name}": ROM${light ? ", capa" : ""} e saves deste jogo no PC. Não tem como desfazer; para guardar os saves antes, use 💾 Saves → Guardar cópia.`, true, "detail-status"); return; }
  state.busy = true;
  try { const r = await api(light ? "/api/cover/delete" : "/api/heavy/delete", {code: g.code, label: coverLabel(g)}); await afterFileChange(`${g.name}: ${describeCascade(r.cascade, "apagado(s)")}`); }
  catch (e) { state.busy = false; b.dataset.confirm = ""; b.textContent = "🗑 Apagar ROM"; report(e.message, true, "detail-status"); }
};
$("rom-remove").onclick = () => {
  const g = state.selected; if (!g?.code) return; closeGame();
  const entry = g.driveName || g.romName;
  const scopes = [["local", "Só deste PC (continua no Drive)"], ["drive", "Só do Drive (vai para a lixeira)"], ["both", "Dos dois"]];
  openTool(`🗑 Remover: ${g.name}`, async body => {
    let scope = g.local ? "local" : "drive", revision = 0;
    const draw = async () => {
      const request = ++revision, chosen = scope;
      const buttons = scopes.map(([key, label]) => button(label, () => { scope = key; draw(); }, scope === key));
      body.replaceChildren(hint("Saves, estados, texturas, capa, cadastro, nota e tempo ficam. Tudo o que sai vai para a lixeira (PC: do sistema; Drive: recuperável por 30 dias)."), actions(...buttons), hint("Conferindo o que seria removido…"));
      let plan;
      try { plan = await api(`/api/storage/removal-plan?${new URLSearchParams({scope, code: g.code, entry})}`); }
      catch (e) { if (request !== revision || !body.isConnected) return; body.append(hint(e.message)); return toolStatus(e.message, true); }
      if (request !== revision || !body.isConnected) return;
      body.replaceChildren(hint("Saves, estados, texturas, capa, cadastro, nota e tempo ficam. Tudo o que sai vai para a lixeira (PC: do sistema; Drive: recuperável por 30 dias)."), actions(...buttons));
      if (plan.local.length) body.append(heading(`Neste PC (${plan.local.length})`), ...plan.local.map(f => row(f)));
      if (plan.drive.length) body.append(heading(`No Drive (${plan.drive.length} · ${fmtBytes(plan.bytes_drive)})`), ...plan.drive.map(f => row(f.path.split("/").slice(-1)[0], Object.assign(document.createElement("small"), {textContent: fmtBytes(f.size)}))));
      if (plan.preserved.length) body.append(hint(`Preservados (usados por outro jogo): ${plan.preserved.length}.`));
      for (const w of plan.warnings) body.append(hint("⚠ " + w));
      for (const b of plan.blocked) body.append(hint("⛔ " + b));
      if (!plan.local.length && !plan.drive.length && !plan.blocked.length) body.append(hint("Nada a remover nesta opção."));
      if (!plan.blocked.length && (plan.local.length || plan.drive.length)) {
        body.append(actions(confirmButton("Remover", "Confirmar: " + plan.confirm_text, async () => {
          try {
            const r = await api("/api/storage/removal-apply", {scope: chosen, code: g.code, entry: plan.entry, token: plan.token, confirm: plan.confirm_text});
            const failed = r.results.filter(x => !x.ok);
            toolStatus(failed.length ? `${r.results.length - failed.length} removido(s); ${failed.length} falhou(aram): ${failed[0].error}` : `Pronto: ${r.results.length} arquivo(s) para a lixeira. ${r.recover}`, failed.length > 0);
            await load(state.kind, state.code);
          } catch (e) { toolStatus(e.message, true); }
        })));
      }
    };
    await draw();
  });
};

$("decompose").onclick = () => {
  const g = state.selected; closeGame();
  let names = [];
  openTool(`⧉ Decompor: ${g.name}`, async body => {
    const draw = () => body.replaceChildren(hint("Os jogos que a coletânea contém (sugestão lida da pasta do Switch; corrija se precisar). A pasta fica vinculada a um deles, então a próxima varredura não recria a coletânea."),
      ...names.map((name, i) => row(name, button("Editar", () => openTextEntry("Nome do jogo", name, v => { if (v) names[i] = v; draw(); })), button("Tirar", () => { names.splice(i, 1); draw(); }))),
      actions(button("➕ Jogo", () => openTextEntry("Nome do jogo", "", v => { if (v) names.push(v); draw(); })),
        confirmButton("Decompor", "Confirmar: decompor", async () => {
          if (!names.length) return toolStatus("Informe ao menos um jogo.", true);
          try { const r = await api("/api/library/decompor", {id: g.id, nomes: names}); toolStatus(`${r.criados} jogo(s) criado(s), ${r.reaproveitados} reaproveitado(s); vínculo em "${r.vinculo_em}".`); }
          catch (e) { toolStatus(e.message, true); }
        })));
    body.replaceChildren(hint("Lendo a pasta da coletânea…"));
    try { const r = await api(`/api/switch/colecao?${new URLSearchParams({nome: g.name})}`); names = r.sugestoes || []; if (r.aviso) toolStatus(r.aviso); } catch (e) { toolStatus(e.message, true); }
    draw();
  });
};


import {api} from "./api.js";
import {$, actions, button, choice, confirmButton, heading, hint, looseName, row} from "./dom.js";
import {openTextEntry} from "./search.js";
import {state} from "./state.js";
import {toolJob, toolStatus} from "./tools.js";
export async function toolCloudSaves(body) {
  let revision = 0, busy = false, showAll = false;
  const draw = async () => {
    const request = ++revision;
    body.replaceChildren(hint("Comparando saves com a nuvem…"));
    try {
      const status = await api("/api/cloud/saves/status" + (showAll ? "?all=1" : ""));
      if (request !== revision || !body.isConnected) return;
      if (!status.enabled) { body.replaceChildren(hint("Configure a nuvem para sincronizar saves.")); return; }
      body.replaceChildren(hint("Feche os emuladores. Saves são compartilhados; estados ficam separados por aparelho. Conflitos exigem escolha e a outra versão fica no histórico."),hint("Esquecer este save retira apenas o arquivo escolhido do uso em todos os aparelhos na próxima sincronização. Cópias antigas ficam no histórico; saves de outros jogos ficam."));
      const perform = async (url, data) => {
        if (busy) return; busy = true; body.querySelectorAll("button").forEach(b => b.disabled = true);
        try {
          const result = await api(url, data);
          if (result.ok === false || result.errors?.length) throw new Error(result.error || result.errors.map(e => `${e.path}: ${e.error}`).join("; "));
          if (!body.isConnected) return;
          toolStatus(result.conflicts?.length ? `${result.conflicts.length} conflito(s) ainda precisam de escolha.` : "Operação concluída. Versões anteriores preservadas.");
          await draw();
        } catch (e) { if (body.isConnected) { toolStatus(e.message, true); body.querySelectorAll("button").forEach(b => b.disabled = false); } }
        finally { busy = false; }
      };
      body.append(actions(button("Comparar novamente", draw), button(showAll ? "Mostrar só pendentes" : "Ver também saves em dia", () => { showAll = !showAll; draw(); }), button("Sincronizar sem resolver conflitos", () => perform("/api/cloud/saves/sync", {}))));
      if (!status.items?.length) body.append(hint("Saves em dia com a nuvem."));
      for (const item of status.items || []) {
        const box = document.createElement("section"); box.append(heading(item.path), hint(`${item.group || "saves"} · ${item.action === "conflict" ? "Conflito" : item.action}`));
        if (item.action === "conflict") {
          const choose = (choice, sha) => perform("/api/cloud/saves/resolve", {path: item.path, group: item.group || "saves", choice, ...(sha ? {sha} : {})});
          if (item.local) box.append(confirmButton("Manter deste PC", "Confirmar: manter deste PC", () => choose("local")));
          for (const [sha, devices] of Object.entries(item.heads || {})) box.append(confirmButton(`${item.deletedHeads?.includes(sha) ? "Usar exclusão confirmada" : "Usar da nuvem"}: ${devices.join(", ")} · ${sha.slice(0, 12)}`, "Confirmar: usar esta versão", () => choose("remote", sha)));
        }
        if (item.action !== "forget") box.append(confirmButton("Esquecer este save…", `Esquecer este save: ${item.path}`, () => perform("/api/cloud/saves/forget", {path:item.path, group:item.group || "saves", expectedLocal:item.local ?? null, expectedHeads:Object.keys(item.heads || {}), confirm:`Esquecer este save: ${item.path}`})));
        body.append(box);
      }
    } catch (e) { if (request === revision && body.isConnected) { body.replaceChildren(hint(e.message), button("Tentar novamente", draw));toolStatus(e.message, true); } }
  };
  await draw();
}
export async function toolOrganize(body) {
  body.replaceChildren(hint("Lendo a pasta de organizar e os Downloads…"));
  const {staging_dir, downloads_dir, items} = await api("/api/organize/pending");
  const gb = n => n >= 1073741824 ? `${(n/1073741824).toFixed(1)} GB` : `${Math.max(1, Math.round(n/1048576))} MB`;
  const label = i => (i.member ? `${i.name} › ${i.member}` : i.name);
  body.replaceChildren(hint(`Origens: ROMs/${staging_dir}/ e ${downloads_dir}. Escolha o sistema de cada ROM: o nome sai limpo, a capa vem da imagem ao lado ou das bases de ROM e o gênero é preenchido. Se já existir, a antiga vai para a lixeira.`),
    ...(items.length ? items.map(item => {
      const r = row(`${item.source === "downloads" ? "⬇ " : ""}${label(item)} · ${gb(item.size)}${item.status !== "pronto" ? " · " + item.status : ` → ${item.final}`}${item.cover_image ? " · 🖼 " + item.cover_image : ""}${item.exists_in.length ? " · já existe em " + item.exists_in.join(", ") + " (substitui)" : ""}`);
      if (item.status === "pronto") for (const c of item.candidates) r.append(confirmButton(`→ ${c.code}`, `Mover para ${c.code}?`, async () => {
        toolStatus(`Organizando ${item.final}… (capa e gênero podem levar um pouco)`);
        try {
          const d = await api("/api/organize/move", {id: item.id, code: c.code});
          toolStatus(`${d.message} · capa: ${d.cover || "não achada"} · gênero: ${d.genero || "não achado"}`);
        } catch (e) { toolStatus(e.message, true); }
        await toolOrganize(body);
      }));
      if (item.status !== "baixando") r.append(confirmButton("Descartar", "Confirmar: para a lixeira", async () => {
        try { await api("/api/organize/discard", {id: item.id}); toolStatus(`${item.name} foi para a lixeira.`); } catch (e) { toolStatus(e.message, true); }
        await toolOrganize(body);
      }));
      return r;
    }) : [hint("Nada esperando organização.")]),
    await switchUploads(body));
}
// Dumps de Switch (pastas e .nsp/.xci) em Downloads: sobem ao Drive com o nome e o gênero escolhidos; a origem vai
// para a lixeira depois de conferida (/api/switch/upload, o mesmo envio da web).
async function switchUploads(body) {
  const box = document.createElement("section"); box.className = "panel";
  let data;
  try { data = await api("/api/switch/upload/pending"); } catch (e) { box.append(heading("Dumps de Switch"), hint(e.message)); return box; }
  const gb = n => n >= 1073741824 ? `${(n / 1073741824).toFixed(1)} GB` : `${Math.max(1, Math.round(n / 1048576))} MB`;
  box.append(heading("Dumps de Switch em Downloads"));
  if (!data.items.length) { box.append(hint("Nenhum dump de Switch em Downloads.")); return box; }
  box.append(hint("Escolha o nome da pasta no Drive e o gênero (automático se vazio); depois Subir. A capa e o índice do Switch são atualizados no fim."));
  for (const item of data.items) {
    const pick = {nome: item.nome, genero: "", lista: false}, row = document.createElement("div"); row.className = "panel";
    const draw = () => row.replaceChildren(
      Object.assign(document.createElement("p"), {className: "hint", textContent: `📦 ${item.entry} · ${item.files.length} arquivo(s) · ${gb(item.size)}${item.baixando ? " · ainda baixando" : ""}`}),
      actions(button(`Nome: ${pick.nome || "—"}`, () => openTextEntry("Nome da pasta no Drive", pick.nome, v => { if (v) pick.nome = v; draw(); })),
        button(`Gênero: ${pick.genero || "automático"}`, () => { pick.lista = !pick.lista; draw(); }),
        Object.assign(confirmButton("Subir", `Confirmar: subir "${pick.nome}"`, () => toolJob("/api/switch/upload", {entry: item.entry, nome: pick.nome, genero: pick.genero}, () => toolOrganize(body))), {disabled: !!item.baixando})),
      ...(pick.lista ? [choice([["", "automático"], ...data.generos.map(g => [g, g])], pick.genero, v => { pick.genero = v; pick.lista = false; draw(); })] : []));
    draw(); box.append(row);
  }
  return box;
}
export async function toolMemcards(body) {
  body.replaceChildren(hint("Lendo os memory cards…"));
  const cards = await api("/api/memcards");
  const lists = Object.fromEntries(await Promise.all(cards.filter(c => c.tool_ok).map(async c => [c.key, await api(`/api/memcards/list/${encodeURIComponent(c.key)}`).then(d => d.items, e => ({error: e.message}))])));
  const refresh = () => toolMemcards(body);
  const sections = cards.map(card => {
    const box = document.createElement("section"); box.className = "panel";
    const file = Object.assign(document.createElement("input"), {type: "file", hidden: true});
    file.onchange = () => { const f = file.files[0]; if (!f) return; const reader = new FileReader();
      reader.onload = async () => { try { await api("/api/memcards/import", {key: card.key, filename: f.name, data: reader.result.split(",")[1]}); toolStatus(`Importado: ${f.name}`); refresh(); } catch (e) { toolStatus(e.message, true); } };
      reader.readAsDataURL(f); };
    box.append(heading(`${card.console} · ${card.label}`), file, actions(button("📥 Importar save (arquivo)", () => file.click()),
      confirmButton("✕ Tirar da lista", "Confirmar: só desregistrar", async () => { try { await api("/api/memcards/remove", {console: card.console.toLowerCase(), label: card.label}); refresh(); } catch (e) { toolStatus(e.message, true); } })));
    const items = lists[card.key];
    if (!card.tool_ok) box.append(hint(`Ferramenta ${card.console === "PS1" ? "ps1vmc-tool" : "ps2vmc-tool"} não encontrada no PATH.`));
    else if (!items || items.error) box.append(hint(`Não foi possível ler: ${items?.error || "falha"}`));
    else {
      const saves = items.filter(i => i.type !== "link");
      if (!saves.length) box.append(hint("Card vazio."));
      for (const item of saves) {
        const others = cards.filter(c => c.console === card.console && c.key !== card.key && c.tool_ok);
        box.append(row(`${item.name || `(desconhecido · ${item.raw_name})`} · ${item.type === "dir" ? `${item.size} arquivo(s)` : `${Math.round(item.size / 1024)} KB`}`,
          button("⬇ Exportar", async () => { try { const d = await api("/api/memcards/export", {key: card.key, item}); toolStatus(`Exportado: ${d.file}`); } catch (e) { toolStatus(e.message, true); } }),
          ...others.map(o => confirmButton(`↔ ${o.label}`, `Mover para ${o.label}?`, async () => { try { await api("/api/memcards/transfer", {src_key: card.key, dest_key: o.key, item}); toolStatus(`Transferido para ${o.label}.`); refresh(); } catch (e) { toolStatus(e.message, true); } })),
          confirmButton("🗑 Apagar", "Confirmar: apagar de vez", async () => { try { await api("/api/memcards/delete", {key: card.key, item}); toolStatus(`Apagado: ${item.name || item.raw_name}`); refresh(); } catch (e) { toolStatus(e.message, true); } })));
      }
    }
    return box;
  });
  const add = {console: "ps1", label: "", path: "", mode: "open"};
  const addBox = document.createElement("section"); addBox.className = "panel";
  const drawAdd = () => addBox.replaceChildren(heading("Adicionar card"),
    choice([["ps1", "PS1"], ["ps2", "PS2"]], add.console, v => add.console = v),
    actions(button(`Nome: ${add.label || "—"}`, () => openTextEntry("Nome do card (ex.: Slot 3)", add.label, v => { add.label = v; drawAdd(); })),
      button(`Arquivo: ${add.path || "—"}`, () => openTextEntry("Caminho do arquivo do card (~/Drive/Jogos/…)", add.path, v => { add.path = v; drawAdd(); }))),
    choice([["open", "Card existente"], ["create", "Criar em branco"]], add.mode, v => add.mode = v),
    actions(button("Adicionar card", async () => {
      if (!add.label || !add.path) return toolStatus("Informe o nome e o arquivo do card.", true);
      try { await api("/api/memcards/add", add); toolStatus(`Card adicionado: ${add.label}`); refresh(); } catch (e) { toolStatus(e.message, true); }
    })));
  drawAdd();
  body.replaceChildren(...(sections.length ? sections : [hint("Nenhum card configurado.")]), addBox);
}
export async function toolPhoneSaves(body) {
  body.replaceChildren(hint("Lendo os saves do PPSSPP no celular…"));
  const data = await api("/api/emu_saves/list/PSP");
  if (!data.android_ok) return body.replaceChildren(hint("Celular não conectado pelo cabo (adb). Conecte e abra de novo."), actions(button("Tentar de novo", () => toolPhoneSaves(body))));
  body.replaceChildren(hint("Saves do PSP no celular. “Baixar” copia para o PC; nada é apagado no celular."),
    ...(data.items.length ? data.items.map(item => {
      const r = row(`${item.name || `(desconhecido · ${item.raw_name})`} · ${item.in_pc ? "já no PC" : "só no celular"}`);
      if (!item.in_pc) r.append(button("⬇ Baixar para o PC", async () => { try { const d = await api("/api/emu_saves/pull", {emu: "PSP", item}); toolStatus(`Baixado: ${d.file}`); toolPhoneSaves(body); } catch (e) { toolStatus(e.message, true); } }));
      return r;
    }) : [hint("Nada encontrado no celular.")]));
}
const texturesTool = {alvo: "pc", termo: "", sistema: "", meus: true, imp: {sistema: "PS2", id_jogo: "", arquivo: "", url: ""}};
export async function toolTextures(body, focusId) {
  const t = texturesTool;
  body.replaceChildren(hint("Carregando o catálogo de texturas…"));
  const data = await api(`/api/texturas?alvo=${t.alvo}`);
  const gb = n => n >= 1073741824 ? `${(n/1073741824).toFixed(1)} GB` : `${Math.round(n/1048576)} MB`;
  const again = id => toolTextures(body, id);
  const termo = looseName(t.termo);
  const found = data.pacotes.filter(p => (!t.sistema || p.sistema === t.sistema) && (!t.meus || p.tem_rom || p.instalado) && (!termo || looseName(p.nome).includes(termo) || p.id_jogo.toLowerCase().includes(t.termo.toLowerCase())))
    .sort((a, b) => b.instalado - a.instalado || b.tem_rom - a.tem_rom || a.nome.localeCompare(b.nome));
  const list = found.slice(0, 30).map(p => {
    const b = p.instalado ? confirmButton("🗑 Remover", "Confirmar: remover", async () => { try { const r = await api("/api/texturas/remover", {id: p.id, alvo: t.alvo}); toolStatus(`${r.removidos} arquivos removidos.`); } catch (e) { toolStatus(e.message, true); } again(p.id); })
      : confirmButton("⬇ Instalar", `Confirmar: baixar ${gb(p.tamanho)}`, async () => { b.disabled = true; await toolJob("/api/texturas/instalar", {id: p.id, alvo: t.alvo}); again(p.id); });
    b.disabled = p.em_andamento; b.dataset.textureId = p.id;
    return row(`${p.sistema} · ${p.nome} [${p.id_jogo}] · ${gb(p.tamanho)}${p.instalado ? ` · instalado (${p.arquivos})` : p.tem_rom ? " · você tem a ROM" : ""}`, b);
  });
  const imp = t.imp, impBox = document.createElement("section"); impBox.className = "panel";
  const importBody = extra => ({alvo: t.alvo, sistema: imp.sistema, id_jogo: imp.id_jogo, ...extra});
  const drawImport = () => impBox.replaceChildren(heading("Importar um pacote baixado"),
    hint(`Arquivo .zip/.7z/.rar na pasta ${data.importar_dir}, ou um link direto (use só fontes em que confia; o SHA-1 aparece no fim).`),
    choice(data.sistemas.map(x => [x, x]), imp.sistema, v => imp.sistema = v),
    actions(button(`ID do jogo: ${imp.id_jogo || "—"}`, () => openTextEntry("ID do jogo (SLUS-21065, ULUS10307…)", imp.id_jogo, v => { imp.id_jogo = v.toUpperCase(); drawImport(); })),
      button(`Arquivo: ${imp.arquivo || "—"}`, () => openTextEntry("Nome do arquivo na pasta de importação", imp.arquivo, v => { imp.arquivo = v; drawImport(); })),
      button(`Link: ${imp.url || "—"}`, () => openTextEntry("Link direto (https://…)", imp.url, v => { imp.url = v; drawImport(); }))),
    actions(confirmButton("Importar arquivo", "Confirmar: importar", () => imp.id_jogo && imp.arquivo ? toolJob("/api/texturas/instalar", importBody({arquivo: imp.arquivo})) : toolStatus("Informe o ID e o arquivo.", true)),
      confirmButton("Baixar do link", "Confirmar: baixar o link", () => imp.id_jogo && imp.url ? toolJob("/api/texturas/instalar", importBody({url: imp.url})) : toolStatus("Informe o ID e o link.", true)),
      confirmButton("Remover importado", "Confirmar: remover", async () => { try { const r = await api("/api/texturas/remover", importBody({})); toolStatus(`${r.removidos} arquivos removidos.`); } catch (e) { toolStatus(e.message, true); } })));
  drawImport();
  body.replaceChildren(
    choice([["pc", "Instalar no PC"], ["celular", `Instalar no celular${data.celular_ok === false ? " (desconectado)" : ""}`]], t.alvo, v => { t.alvo = v; if (!data.sistemas.includes(t.sistema)) t.sistema = ""; again(); }),
    choice([["", "Todos"], ...data.sistemas.map(x => [x, x])], t.sistema, v => { t.sistema = v; again(); }),
    actions(button(`Busca: ${t.termo || "—"}`, () => openTextEntry("Buscar pacote", t.termo, v => { t.termo = v; again(); })),
      button(t.meus ? "Só jogos que tenho ✓" : "Só jogos que tenho", () => { t.meus = !t.meus; again(); }, t.meus)),
    ...(list.length ? list : [hint("Nenhum pacote neste filtro.")]),
    ...(found.length > list.length ? [hint(`Mostrando ${list.length} de ${found.length}; use a busca para achar o resto.`)] : []),
    impBox);
  if (focusId) body.querySelector(`[data-texture-id="${CSS.escape(focusId)}"]`)?.focus();
}
// Simular mostra o que aconteceria; Aplicar grava (pede confirmação).
function jobRow(title, url, {apply = true, extra} = {}) {
  const box = document.createElement("section"); box.className = "panel";
  const go = applyIt => toolJob(typeof url === "function" ? url(applyIt) : url, {});
  box.append(heading(title), ...(extra ? [extra] : []), actions(...(apply ? [button("Simular", () => go(false)), confirmButton("Aplicar", "Confirmar: aplicar", () => go(true))] : [confirmButton("Rodar", "Confirmar: rodar", () => go(true))])));
  return box;
}
const q = (base, params, applyIt) => `${base}?${new URLSearchParams({...params, apply: applyIt ? "1" : "0"})}`;
export async function toolLibrary(body) {
  const add = {preset: "Nintendo Switch|switch", plataforma: "", fonte: "", games: []};
  const addBox = document.createElement("section"); addBox.className = "panel";
  const drawAdd = () => addBox.replaceChildren(heading("Adicionar jogos à Biblioteca"),
    choice([["Nintendo Switch|switch", "Switch"], ["Nintendo Switch 2|switch2", "Switch 2"], ["PlayStation 4|psn", "PS4 digital"], ["PlayStation 4|psn:fisico", "PS4 físico"], ["PlayStation 3|psn", "PS3 digital"], ["PlayStation 3|psn:fisico", "PS3 físico"], ["", "Outra"]], add.preset, v => { add.preset = v; drawAdd(); }),
    ...(add.preset ? [] : [actions(button(`Plataforma: ${add.plataforma || "—"}`, () => openTextEntry("Plataforma (ex.: Xbox)", add.plataforma, v => { add.plataforma = v; drawAdd(); })),
      button(`Fonte: ${add.fonte || "—"}`, () => openTextEntry("Fonte (ex.: xbox)", add.fonte, v => { add.fonte = v; drawAdd(); })))]),
    ...add.games.map((g, i) => row(g, button("Tirar", () => { add.games.splice(i, 1); drawAdd(); }))),
    actions(button("➕ Jogo", () => openTextEntry("Nome do jogo", "", v => { if (v) add.games.push(v); drawAdd(); })),
      button("Simular", () => send(false)), confirmButton("Adicionar", "Confirmar: adicionar", () => send(true))));
  const send = applyIt => {
    const [plataforma, fonte] = add.preset ? add.preset.split("|") : [add.plataforma, add.fonte];
    if (!add.games.length || !plataforma || !fonte) return toolStatus("Informe a plataforma, a fonte e ao menos um jogo.", true);
    return toolJob("/api/library/add", {games: add.games.join("\n"), plataforma, fonte, apply: applyIt});
  };
  drawAdd();
  body.replaceChildren(jobRow("Atualizar do Heroic", a => q("/api/library/refresh", {source: "heroic"}, a)), jobRow("Atualizar da Steam", a => q("/api/library/refresh", {source: "steam"}, a)),
    jobRow("Atualizar do Switch e Switch 2 (pastas do Drive)", a => q("/api/library/refresh", {source: "switch"}, a)), jobRow("Buscar capas que faltam na Biblioteca", a => q("/api/library/fetch_covers", {}, a)),
    jobRow("Atualizar índice do Switch (Tinfoil)", "/api/switch/shop", {apply: false}), addBox);
}
export async function toolCovers(body) {
  const light = {code: state.light[0]?.code || "", fallback: "0"}, heavy = {code: state.systems[0]?.code || ""};
  body.replaceChildren(
    jobRow("ROMs leves: buscar capas", a => `/api/fetch/${encodeURIComponent(light.code)}?${new URLSearchParams({apply: a ? "1" : "0", fallback: light.fallback})}`, {extra: actions(
      choice(state.light.map(s => [s.code, s.code]), light.code, v => light.code = v), choice([["0", "Normal"], ["launchbox", "LaunchBox"], ["screenscraper", "ScreenScraper"]], light.fallback, v => light.fallback = v))}),
    jobRow("ROMs pesadas: atualizar o catálogo do Drive", "/api/heavy_catalog", {apply: false}),
    jobRow("ROMs pesadas: buscar capas", a => q("/api/heavy/fetch_covers", {code: heavy.code}, a), {extra: choice(state.systems.map(s => [s.code, s.code]), heavy.code, v => heavy.code = v)}),
    jobRow("Capas do PyRetro no PCSX2 e Dolphin", a => q("/api/capas_emuladores", {}, a)));
}
export async function toolMaintenance(body) {
  const o = {config: "all", sanitize: "all", playlist: state.light[0]?.code || "", playlistTarget: "all", sync: "all"};
  const sources = await api("/api/emu_sync/sources").catch(() => []);
  const targets = [["all", "PC + Android"], ["pc", "Só PC"], ["android", "Só Android"]];
  body.replaceChildren(
    jobRow("Backup de configs do RetroArch", a => q("/api/backup_config", {target: o.config}, a), {extra: choice(targets, o.config, v => o.config = v)}),
    jobRow("Backup de saves (Dolphin GameCube/Wii)", a => q("/api/backup_saves", {}, a)),
    jobRow("Sanitizar nomes (remove & : *)", a => q("/api/sanitize_names", {target: o.sanitize}, a), {extra: choice([["all", "Capas + ROMs"], ["capas", "Só Capas"], ["roms", "Só ROMs"]], o.sanitize, v => o.sanitize = v)}),
    jobRow("Reconstruir playlist do RetroArch", a => q(`/api/rebuild_playlist/${encodeURIComponent(o.playlist)}`, {target: o.playlistTarget}, a), {extra: actions(choice(state.light.map(s => [s.code, s.code]), o.playlist, v => o.playlist = v), choice(targets, o.playlistTarget, v => o.playlistTarget = v))}),
    jobRow("Sincronizar saves de emulador (PC/Drive/Android)", a => q("/api/emu_sync", {source: o.sync}, a), {extra: choice([["all", "Todos"], ...sources.map(x => [x.code, x.nome])], o.sync, v => o.sync = v)}));
}
// Relatório do Codex (core/diagnostics.py): só presença de pastas e programas, sem caminhos.
export async function toolDiagnostics(body) {
  body.replaceChildren(hint("Conferindo…"));
  const r = await api("/api/diagnostics");
  const icon = {present: "✓", missing: "✗", unavailable: "?"};
  body.replaceChildren(
    ...r.checks.map(c => row(`${icon[c.status] || "?"} ${c.id}${c.action ? ` · ${c.action}` : ""}`)),
    hint(`Jogo aberto pelo PyRetro: ${{idle: "nenhum", running: "sim", starting: "abrindo", error: "erro na última sessão"}[r.play_state] || "desconhecido"}.`),
    ...r.limits.map(hint), hint(r.privacy),
    actions(button("Atualizar", () => toolDiagnostics(body))),
    Object.assign(document.createElement("p"), {className: "hint", innerHTML: 'Versão para copiar e enviar: <a href="/diagnostics">/diagnostics</a>.'}));
}
// Assistente de primeira execução (core/firstrun.py): só cria configuração e pastas vazias; programas são do setup.
export async function toolSetup(body) {
  body.replaceChildren(hint("Conferindo…"));
  const r = await api("/api/setup/status");
  const icon = {ok: "✓", missing: "✗", optional: "○"};
  const fixable = r.steps.some(step => step.fixable);
  body.replaceChildren(
    hint(r.ready ? "Tudo no lugar para usar o PyRetro." : "Falta preparar o PyRetro neste computador."),
    ...r.steps.flatMap(step => [row(`${icon[step.state] || "?"} ${step.label}`), ...(step.detail ? [hint(step.detail)] : [])]),
    actions(...(fixable ? [button("Criar o que falta", async () => {
        try { const done = await api("/api/setup/apply", {}); toolStatus(done.created.length ? `Criado: ${done.created.join(", ")}.` : "Nada a criar."); await toolSetup(body); }
        catch (e) { toolStatus(e.message, true); }
      })] : []),
      button("Verificar de novo", () => toolSetup(body)),
      ...(r.ready && !state.systems?.length ? [button("Abrir o acervo", () => location.reload())] : [])),
    hint("O PyRetro não instala programas nem apaga arquivos: emuladores, rclone e o lançador vêm do setup do sistema."));
}
export async function toolSettings(body) {
  const cfg = await api("/api/settings"), changed = {pc: {}, android: {}};
  const draw = () => body.replaceChildren(hint("Pastas usadas pelo PyRetro. Só os campos alterados mudam ao salvar."),
    ...["pc", "android"].flatMap(section => [heading(section === "pc" ? "PC" : "Android"), ...Object.entries(cfg[section] || {}).map(([key, value]) => {
      const now = changed[section][key] ?? value;
      return button(`${key in changed[section] ? "• " : ""}${key}: ${now}`, () => openTextEntry(key, now, v => { if (v !== value) changed[section][key] = v; else delete changed[section][key]; draw(); }));
    })]),
    actions(confirmButton("Salvar", "Confirmar: salvar", async () => {
      try { await api("/api/settings", {pc: {...cfg.pc, ...changed.pc}, android: {...cfg.android, ...changed.android}}); toolStatus("Configurações salvas."); Object.assign(cfg.pc, changed.pc); Object.assign(cfg.android, changed.android); changed.pc = {}; changed.android = {}; draw(); }
      catch (e) { toolStatus(e.message, true); }
    })));
  draw();
}


let currentSystem = null;
let currentKind = "leve"; // "leve" | "pesado" | "biblioteca" - decide o que selectSystem/renderGallery fazem
let systems = [];
let currentItems = [];

// Aba única pra leve/pesado/Biblioteca (pedido do usuário, 27/08: os
// dois últimos eram popup, viraram aba com a mesma grade de capa da
// galeria normal). activateTab/setControlsForKind ficam genéricos pra
// não duplicar 3x a lógica de "qual aba tá ativa" / "qual barra de
// controle mostrar".
async function loadSystems() {
  const [lightRes, heavyRes] = await Promise.all([fetch("/api/systems"), fetch("/api/heavy/systems")]);
  systems = await lightRes.json();
  heavySystems = await heavyRes.json();

  const tabs = document.getElementById("system-tabs");
  tabs.innerHTML = "";
  for (const sys of systems) {
    const tab = document.createElement("div");
    tab.className = "tab";
    tab.dataset.code = sys.code;
    const warnClass = (sys.no_match > 0 || sys.missing > 0) ? "warn" : "";
    tab.innerHTML = `<span>${sys.code}</span><span class="badge ${warnClass}" title="${sys.count} capas · ${sys.no_match} sem correspondência · ${sys.missing} sem capa ainda">${sys.count}·${sys.no_match}·${sys.missing}</span>`;
    tab.addEventListener("click", () => selectSystem(sys.code));
    tabs.appendChild(tab);
  }
  for (const sys of heavySystems) {
    const tab = document.createElement("div");
    tab.className = "tab";
    tab.dataset.code = sys.code;
    tab.innerHTML = `<span>📦 ${sys.code}</span>`;
    tab.addEventListener("click", () => selectHeavyTab(sys.code));
    tabs.appendChild(tab);
  }
  const libTab = document.createElement("div");
  libTab.className = "tab";
  libTab.dataset.code = "BIBLIOTECA";
  libTab.innerHTML = "<span>📚 Biblioteca</span>";
  libTab.addEventListener("click", () => selectLibraryTab());
  tabs.appendChild(libTab);

  const consoleSelect = document.getElementById("global-search-console");
  consoleSelect.innerHTML = '<option value="">Todos</option>' +
    systems.map(s => `<option value="${s.code}">${s.code}</option>`).join("");
}

function activateTab(code) {
  document.querySelectorAll("#system-tabs .tab").forEach(tab => {
    tab.classList.toggle("active", tab.dataset.code === code);
  });
}

function setControlsForKind(kind) {
  document.getElementById("menubar").classList.toggle("hidden", kind !== "leve");
  document.getElementById("filterbar").classList.toggle("hidden", kind !== "leve");
  document.getElementById("library-controls").classList.toggle("hidden", kind !== "biblioteca");
  document.getElementById("heavy-controls").classList.toggle("hidden", kind !== "pesado");
  document.getElementById("library-add-card").classList.add("hidden"); // sempre fecha o formulário ao trocar de aba
}

let globalSearchTimer = null;

function runGlobalSearch() {
  const q = document.getElementById("global-search-input").value.trim();
  const code = document.getElementById("global-search-console").value;
  const results = document.getElementById("global-search-results");
  if (q.length < 2) {
    results.classList.add("hidden");
    results.innerHTML = "";
    return;
  }
  // Unificado (pedido do usuário 27/08: "unificar a pesquisa toda na
  // barra acima") - /api/search_library agora devolve leve + pesado +
  // Biblioteca junto (kind por item), essa é a ÚNICA busca por nome do
  // app inteiro (Biblioteca não tem mais campo de busca próprio).
  const KIND_ICON = { leve: "", pesado: "📦 ", biblioteca: "📚 " };
  fetch(`/api/search_library?q=${encodeURIComponent(q)}&code=${encodeURIComponent(code)}`)
    .then(r => r.json())
    .then(items => {
      results.innerHTML = "";
      if (items.length === 0) {
        results.innerHTML = '<div class="global-search-result">Nada encontrado.</div>';
      } else {
        for (const item of items) {
          const row = document.createElement("div");
          row.className = "global-search-result";
          const codeShown = item.kind === "biblioteca" ? "" : (item.code || "");
          row.innerHTML = `<span class="code">${KIND_ICON[item.kind] || ""}${codeShown}</span><span class="label">${item.display_name || item.label}</span>`;
          row.addEventListener("click", () => goToSearchResult(item));
          results.appendChild(row);
        }
      }
      results.classList.remove("hidden");
    });
}

async function goToSearchResult(item) {
  document.getElementById("global-search-results").classList.add("hidden");
  document.getElementById("global-search-input").value = "";

  let highlightLabel = item.label;
  if (item.kind === "pesado") {
    if (currentSystem !== item.code || currentKind !== "pesado") await selectHeavyTab(item.code);
  } else if (item.kind === "biblioteca") {
    if (currentKind !== "biblioteca") await selectLibraryTab();
  } else {
    if (currentSystem !== item.code || currentKind !== "leve") await selectSystem(item.code);
  }

  const card = document.querySelector(`#gallery .cover[data-label="${CSS.escape(highlightLabel)}"]`);
  if (card) {
    card.scrollIntoView({ behavior: "smooth", block: "center" });
    card.classList.add("search-highlight");
    setTimeout(() => card.classList.remove("search-highlight"), 2000);
  }
}

document.getElementById("global-search-input").addEventListener("input", () => {
  clearTimeout(globalSearchTimer);
  globalSearchTimer = setTimeout(runGlobalSearch, 300);
});
document.getElementById("global-search-console").addEventListener("change", runGlobalSearch);
document.addEventListener("click", (e) => {
  const row = document.querySelector(".global-search-row");
  if (row && !row.contains(e.target)) {
    document.getElementById("global-search-results").classList.add("hidden");
  }
});

async function selectSystem(code) {
  currentSystem = code;
  currentKind = "leve";
  activateTab(code);
  setControlsForKind("leve");
  const sys = systems.find(s => s.code === code);
  document.getElementById("current-system").textContent = `${code} — ${sys.count} capas, ${sys.no_match} sem correspondência`;
  document.getElementById("btn-fetch").disabled = false;
  document.getElementById("btn-fallback-launchbox").disabled = !sys.has_launchbox;
  document.getElementById("btn-fallback-screenscraper").disabled = !sys.has_screenscraper;

  const res = await fetch(`/api/covers/${code}`);
  currentItems = await res.json();
  renderGallery();
}

function renderGallery() {
  const gallery = document.getElementById("gallery");
  gallery.innerHTML = "";
  const onlyFlagged = document.getElementById("filter-flagged").checked;
  const onlyNoMatch = document.getElementById("filter-nomatch").checked;
  const onlyNoCover = document.getElementById("filter-nocover").checked;

  let items = currentItems;
  if (onlyFlagged || onlyNoMatch || onlyNoCover) {
    items = items.filter(item =>
      (onlyFlagged && (item.status === "flagged_wrong" || item.status === "duplicate")) ||
      (onlyNoMatch && item.status === "no_match") ||
      (onlyNoCover && item.status === "no_cover")
    );
  }

  if (items.length === 0) {
    const msg = (onlyFlagged || onlyNoMatch || onlyNoCover) ? "Nada bate com esse filtro." : "Nenhuma capa nessa pasta ainda.";
    gallery.innerHTML = `<div class="empty-state">${msg}</div>`;
    return;
  }
  for (const item of items) {
    gallery.appendChild(buildCoverCard(currentSystem, item));
  }
}

document.getElementById("filter-flagged").addEventListener("change", renderGallery);
document.getElementById("filter-nomatch").addEventListener("change", renderGallery);
document.getElementById("filter-nocover").addEventListener("change", renderGallery);

// Nota vira um "chip" clicável com setinha de cada lado, em vez do
// <input type=number> cru de antes - pedido do usuário 28/08: "o campo
// nota ficou estranho, tá um campo escrito 'no' pois está cortando,
// deixar ele apenas nas setinhas e um pouco mais elaborado e bonito".
// O "no" era o placeholder "nota" cortado pela largura fixa de 44px.
// Agora: −/+ ajustam de 0.1 em 0.1, clicar no número deixa digitar
// direto (nota tem decimal, ex: 7.1), e a cor da nota (notaColor) pinta
// o número, a borda e um fundo bem sutil - sem texto nenhum pra cortar.
function buildNotaBox(nota, onChange) {
  const box = document.createElement("div");
  box.className = "nota-box";
  box.innerHTML = `
    <button class="nota-step" type="button" data-d="-1" title="Diminuir">−</button>
    <span class="nota-valor" role="button" tabindex="0" title="Clique pra digitar a nota"></span>
    <button class="nota-step" type="button" data-d="1" title="Aumentar">+</button>
  `;
  const valor = box.querySelector(".nota-valor");
  let atual = nota;

  const pinta = () => {
    valor.textContent = notaTexto(atual);
    const cor = notaColor(atual);
    box.style.setProperty("--nota-cor", cor || "var(--text-dim)");
    box.classList.toggle("sem-nota", cor === null);
  };
  const grava = (novo) => {
    atual = novo;
    pinta();
    onChange("nota", novo);
  };

  box.querySelectorAll(".nota-step").forEach((btn) => {
    btn.addEventListener("click", () => {
      const base = atual === null || atual === undefined || atual === "" ? 0 : Number(atual);
      const novo = Math.round(Math.min(11, Math.max(0, base + Number(btn.dataset.d) * 0.1)) * 10) / 10;
      grava(novo);
    });
  });
  valor.addEventListener("click", () => {
    const digitado = prompt("Nota (0 a 11, vazio pra limpar):", atual ?? "");
    if (digitado === null) return;
    const limpo = digitado.trim().replace(",", ".");
    if (limpo === "") return grava(null);
    const n = parseFloat(limpo);
    if (Number.isNaN(n) || n < 0 || n > 11) return alert("nota precisa ser um número entre 0 e 11");
    grava(Math.round(n * 10) / 10);
  });

  pinta();
  // Deixa o cascateamento (ver buildTrackingRow) preencher a nota sem
  // simular clique: `silencioso` só pinta, sem regravar - usado quando
  // quem chamou já está gravando o campo por conta própria.
  box.definirNota = (novo, silencioso) => {
    atual = novo;
    pinta();
    if (!silencioso) onChange("nota", novo);
  };
  box.notaAtual = () => atual;
  return box;
}

// Tracking universal (iniciado/finalizado/platinado/nota/comentário) -
// pedido do usuário 27/08: mesma edição inline que a Biblioteca já
// tinha, reaproveitada em ROM leve E pesada; 28/08 o comentário virou
// botão -> popup (em vez de textarea no card, que empurrava tudo pra
// baixo e deixava a grade "jogada"). `biblioteca` pode vir null (ROM
// ainda sem registro na Biblioteca) - trata como "tudo zerado" pra
// exibir; a primeira mudança cria o registro sozinha (ver
// /api/library/track). `extras` é uma lista de {icone, titulo, ativo,
// onClick} pra botão específico do tipo de card (capa, ocultar).
function buildTrackingRow(biblioteca, onChange, nome, extras) {
  const b = biblioteca || { nota: null, iniciado: false, finalizado: false, platinado: false, observacoes: null };
  const div = document.createElement("div");
  div.className = "tracking-bar";

  const notaBox = buildNotaBox(b.nota, (campo, valor) => { b.nota = valor; onChange(campo, valor); });
  div.appendChild(notaBox);

  const flags = document.createElement("div");
  flags.className = "tracking-flags";
  flags.innerHTML = `
    <label class="library-check" title="Iniciado">
      <input type="checkbox" data-field="iniciado" ${b.iniciado ? "checked" : ""}><span>▶</span>
    </label>
    <label class="library-check" title="Finalizado">
      <input type="checkbox" data-field="finalizado" ${b.finalizado ? "checked" : ""}><span>✓</span>
    </label>
    <label class="library-check" title="Platinado">
      <input type="checkbox" data-field="platinado" ${b.platinado ? "checked" : ""}><span>🏆</span>
    </label>
  `;
  // Cascateamento das flags (pedido do usuário 28/08: "quando marcar
  // finalizado, já marcar o iniciado também, e solicitar a nota, idem
  // para o platinado"). Platinado implica finalizado, que implica
  // iniciado. Ao DESMARCAR vale o contrário (desmarcar iniciado tira
  // finalizado/platinado) - senão dá pra ficar com "platinado mas não
  // iniciado", que foi exatamente o estado incoerente que gerou
  // confusão. Cada campo que muda de verdade é gravado, um por um.
  const ORDEM = ["iniciado", "finalizado", "platinado"];
  const chk = (campo) => flags.querySelector(`input[data-field="${campo}"]`);

  flags.querySelectorAll("input").forEach((cb) => {
    cb.addEventListener("change", (e) => {
      const campo = e.target.dataset.field;
      const ligado = e.target.checked;
      const i = ORDEM.indexOf(campo);
      const alterados = [[campo, ligado]];

      if (ligado) {
        for (const anterior of ORDEM.slice(0, i)) {          // implica os de baixo
          if (!chk(anterior).checked) { chk(anterior).checked = true; alterados.push([anterior, true]); }
        }
      } else {
        for (const posterior of ORDEM.slice(i + 1)) {        // derruba os de cima
          if (chk(posterior).checked) { chk(posterior).checked = false; alterados.push([posterior, false]); }
        }
      }

      for (const [c, v] of alterados) { b[c] = v; onChange(c, v); }

      // Pede a nota ao concluir, se ainda não tiver uma.
      if (ligado && (campo === "finalizado" || campo === "platinado")
          && (notaBox.notaAtual() === null || notaBox.notaAtual() === undefined)) {
        const digitado = prompt(`Que nota você dá pra "${nome}"? (0 a 11, vazio pra deixar sem nota)`, "");
        if (digitado !== null) {
          const limpo = digitado.trim().replace(",", ".");
          if (limpo !== "") {
            const n = parseFloat(limpo);
            if (Number.isNaN(n) || n < 0 || n > 11) {
              alert("nota precisa ser um número entre 0 e 11 - deixei sem nota");
            } else {
              const nota = Math.round(n * 10) / 10;
              notaBox.definirNota(nota, true);
              b.nota = nota;
              onChange("nota", nota);
            }
          }
        }
      }
    });
  });
  div.appendChild(flags);

  const acoes = document.createElement("div");
  acoes.className = "tracking-acoes";

  const obsBtn = document.createElement("button");
  obsBtn.type = "button";
  obsBtn.className = "icon-btn" + (b.observacoes || b.tempo ? " ativo" : "");
  obsBtn.textContent = "💬";
  obsBtn.title = "Comentário e tempo jogado";
  obsBtn.addEventListener("click", () => {
    openObs(nome, b, (campos) => {
      for (const [campo, valor] of Object.entries(campos)) {
        if (valor === (b[campo] ?? null)) continue; // só grava o que mudou de verdade
        b[campo] = valor;
        onChange(campo, valor);
      }
      obsBtn.classList.toggle("ativo", !!(b.observacoes || b.tempo));
    });
  });
  acoes.appendChild(obsBtn);

  for (const extra of extras || []) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "icon-btn" + (extra.ativo ? " ativo" : "");
    btn.textContent = extra.icone;
    btn.title = extra.titulo;
    if (extra.arquivo) {
      // Upload de capa precisa de <input type=file> de verdade - o
      // botão só dispara o clique nele (escondido).
      const input = document.createElement("input");
      input.type = "file";
      input.accept = "image/png,image/jpeg";
      input.hidden = true;
      input.addEventListener("change", (e) => { if (e.target.files[0]) extra.onClick(e.target.files[0]); });
      btn.addEventListener("click", () => input.click());
      acoes.appendChild(input);
    } else {
      btn.addEventListener("click", () => extra.onClick(btn));
    }
    acoes.appendChild(btn);
  }
  div.appendChild(acoes);
  return div;
}

// `code` (código do sistema, ex: "SFC"/"PS2") é obrigatório - o
// servidor só cruza/cria registro pra ROM quando nome E plataforma
// batem com esse código (core.library.rom_code_for_plataforma), nunca
// só por nome (achado 27/08: nome igual em plataforma diferente pode
// ser jogo DIFERENTE de verdade - ver PLATAFORMA_ROM_CODES).
async function trackGame(nome, code, plataforma, fonte, field, value) {
  return salvarCampo("/api/library/track", { nome, code, plataforma, fonte, field, value });
}

function buildCoverCard(code, item, cacheBust) {
  const { file, label, flagged, duplicated, status, has_save, has_state, display_name, biblioteca } = item;
  // display_name só existe pro Arcade (nome real do jogo, ex: "Metal
  // Slug 2") - o romset continua se chamando "mslug2" no arquivo, no
  // rename, em tudo que mexe em disco. Isso aqui é só pra tela: mostra
  // o nome real, o label curto vira tooltip (title) no lugar dele.
  const shown = display_name || label;
  const noCover = status === "no_cover"; // ROM já organizada, mas sem capa nenhuma ainda (ver missing_cover_labels)
  const renamedPending = status === "renamed_pending";
  const src = file ? `/images/${code}/${encodeURIComponent(file)}` + (cacheBust ? `?t=${Date.now()}` : "") : null;
  // Cruzamento com a Biblioteca (server já casou por nome normalizado,
  // ver gui/server.py) - só mostra o que já está lá, não edita nada
  // daqui (edição continua na aba Biblioteca).
  const libBadges = [];
  if (biblioteca) {
    if (biblioteca.platinado) libBadges.push("🏆");
    else if (biblioteca.finalizado) libBadges.push("✓");
    else if (biblioteca.iniciado) libBadges.push("▶");
    if (biblioteca.nota !== null) libBadges.push(`★${biblioteca.nota}`);
  }
  // Errada e Duplicada eram 2 flags separadas - unificadas numa só
  // ("marcada"): com a galeria mais consolidada, o usuário mesmo olha
  // e decide se é duplicata ou capa errada, não precisa o sistema
  // distinguir os dois (pedido do usuário, 27/08). Item antigo
  // marcado "duplicate" no registry continua tratado como "marcado"
  // aqui - Desmarcar chama /api/cover/unflag, que já limpa qualquer
  // status (não só flagged_wrong), então nada fica preso no estado
  // antigo.
  const attention = flagged || duplicated;
  const div = document.createElement("div");
  div.className = "cover" + (attention ? " flagged" : "") + (renamedPending ? " renamed" : "") + (noCover ? " no-cover" : "");
  div.dataset.label = label;
  div.innerHTML = `
    <div class="cover-img-wrap">
      ${noCover
        ? '<div class="cover-placeholder">🖼<br>sem capa</div>'
        : `<img src="${src}" alt="${shown}">
           ${attention ? '<span class="flag-badge">⚑ marcada</span>' : ""}
           ${libBadges.length ? `<span class="lib-badge" title="Biblioteca">${libBadges.join(" ")}</span>` : ""}
           ${renamedPending ? '<span class="rename-badge">✎ renomeada</span>' : ""}`}
    </div>
    <div class="label" title="${label}">${shown}</div>
    ${has_save || has_state ? `<div class="save-state-row">
      ${has_save ? '<button class="tiny secondary" data-action="delete-save" title="Apagar save">💾 Save</button>' : ""}
      ${has_state ? '<button class="tiny secondary" data-action="delete-state" title="Apagar state">⏱ State</button>' : ""}
    </div>` : ""}
    <div class="cover-actions">
      ${noCover ? "" : `<button class="tiny ${attention ? "" : "secondary"}" data-action="flag">${attention ? "Desmarcar" : "⚑ Marcar"}</button>`}
      <button class="tiny secondary" data-action="edit">✎ Editar</button>
      ${noCover ? "" : '<button class="tiny danger" data-action="delete">🗑 Apagar</button>'}
    </div>
  `;
  if (!noCover) {
    div.querySelector("img").addEventListener("click", () => openLightbox(src, label, display_name));
    div.querySelector('[data-action="flag"]').addEventListener("click", () => toggleFlag(code, label, attention));
    div.querySelector('[data-action="delete"]').addEventListener("click", () => deleteCover(code, label));
  }
  div.querySelector('[data-action="edit"]').addEventListener("click", () => openEdit(code, label, display_name, noCover));
  const delSaveBtn = div.querySelector('[data-action="delete-save"]');
  if (delSaveBtn) delSaveBtn.addEventListener("click", () => deleteSaveOrState(label, "save", delSaveBtn));
  const delStateBtn = div.querySelector('[data-action="delete-state"]');
  if (delStateBtn) delStateBtn.addEventListener("click", () => deleteSaveOrState(label, "state", delStateBtn));

  // Tracking universal (iniciado/finalizado/platinado/nota) - pedido do
  // usuário 27/08: mesma edição inline que a Biblioteca já tinha, agora
  // em qualquer ROM leve também (cria o registro na Biblioteca sozinho
  // na primeira edição, ver /api/library/track).
  const sysLabel = (systems.find(s => s.code === code) || {}).capas || code;
  div.appendChild(buildTrackingRow(biblioteca, (field, value) => {
    item.biblioteca = { ...(item.biblioteca || { nota: null, iniciado: false, finalizado: false, platinado: false }), [field]: value };
    trackGame(shown, code, sysLabel, `rom:${code}`, field, value);
  }, shown));
  return div;
}

async function deleteSaveOrState(label, kind, btn) {
  const kindLabel = kind === "save" ? "save" : "state";
  if (!confirm(`Apagar o ${kindLabel} de "${label}"? Isso não pode ser desfeito.`)) return;
  const res = await fetch("/api/cover/delete_save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ label, kind }),
  });
  const data = await res.json();
  if (res.ok) {
    btn.remove();
    const idx = currentItems.findIndex(i => i.label === label);
    if (idx >= 0) currentItems[idx][kind === "save" ? "has_save" : "has_state"] = false;
  } else {
    alert(`erro ao apagar ${kindLabel}: ${data.error || "falha"}`);
  }
}

function describeDeleteCascade(cascade) {
  const parts = [];
  const romMsg = {
    apagado: "ROM apagada",
    nao_encontrado: "ROM não encontrada (nada pra apagar desse lado)",
    ambiguo: "mais de um arquivo bate com esse nome - nenhum foi apagado, resolva manualmente",
  }[cascade.rom.status] || cascade.rom.status;
  parts.push(romMsg);
  if (cascade.capa && cascade.capa.length) parts.push("capa apagada");
  if (cascade.saves.length) parts.push(`${cascade.saves.length} save(s) apagado(s)`);
  if (cascade.states.length) parts.push(`${cascade.states.length} state(s) apagado(s)`);
  return parts.join(" · ");
}

async function deleteCover(code, label) {
  if (!confirm(`Apagar "${label}" (capa + ROM + save/state)? Isso não pode ser desfeito.`)) return;
  const res = await fetch("/api/cover/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, label }),
  });
  const data = await res.json();
  if (res.ok) {
    alert(describeDeleteCascade(data.cascade));
    selectSystem(code);
  } else {
    alert(`erro ao apagar: ${data.error || "falha"}`);
  }
}

/** Troca só o card de UM jogo no lugar, sem recarregar a galeria inteira -
 * preserva a posição de rolagem e força o navegador a buscar a imagem
 * nova (cache-bust), já que o arquivo mudou mas a URL é a mesma. Também
 * atualiza currentItems (a fonte de verdade dos filtros) e some com o
 * card se ele deixou de bater com o filtro ativo (ex: desmarcar uma
 * capa com "só marcadas" ligado). */
function refreshCard(code, label, flagged, knownFile) {
  const idx = currentItems.findIndex(i => i.label === label);
  const old = document.querySelector(`#gallery .cover[data-label="${CSS.escape(label)}"]`);
  const file = knownFile || (old && decodeURIComponent(old.querySelector("img").src.split("/").pop().split("?")[0]));
  // Flag/Desmarcar sempre grava "flagged_wrong" agora (flag única,
  // duplicate/flagged_wrong unificados - ver buildCoverCard) - item
  // antigo com status "duplicate" só reaparece assim depois do
  // próximo toggle, até lá continua exibido via `duplicated` (abaixo).
  const status = flagged ? "flagged_wrong" : "manual";

  if (idx >= 0) {
    currentItems[idx] = { ...currentItems[idx], file: file || currentItems[idx].file, flagged, duplicated: false, status };
  }

  const onlyFlagged = document.getElementById("filter-flagged").checked;
  const onlyNoMatch = document.getElementById("filter-nomatch").checked;
  const stillMatchesFilter = !(onlyFlagged || onlyNoMatch) ||
    (onlyFlagged && status === "flagged_wrong") || (onlyNoMatch && status === "no_match");

  if (!old) {
    if (stillMatchesFilter) return selectSystem(code); // card não estava visível - recarrega tudo pra achar posição certa
    return;
  }
  if (!stillMatchesFilter) {
    old.remove();
    return;
  }
  const prev = idx >= 0 ? currentItems[idx] : {};
  const newCard = buildCoverCard(code, {
    file, label, flagged, duplicated: false, status,
    has_save: prev.has_save, has_state: prev.has_state, display_name: prev.display_name,
    biblioteca: prev.biblioteca,
  }, true);
  old.replaceWith(newCard);
}

async function toggleFlag(code, label, currentlyFlagged) {
  const endpoint = currentlyFlagged ? "unflag" : "flag";
  await fetch(`/api/cover/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, label }),
  });
  refreshCard(code, label, !currentlyFlagged);
}

function describeCascade(cascade) {
  const parts = [];
  const romMsg = {
    renomeado: "ROM renomeada",
    nao_encontrado: "ROM não encontrada (fica marcado como pendente)",
    conflito: "já existe uma ROM com esse nome (fica marcado como pendente)",
    ambiguo: "mais de um arquivo bate com esse nome (fica marcado como pendente)",
  }[cascade.rom.status] || cascade.rom.status;
  parts.push(romMsg);
  if (cascade.saves.length) parts.push(`${cascade.saves.length} save(s) renomeado(s)`);
  if (cascade.states.length) parts.push(`${cascade.states.length} state(s) renomeado(s)`);
  return parts.join(" · ");
}

function uploadCover(code, label, file) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = async () => {
    const base64 = reader.result.split(",")[1];
    const res = await fetch("/api/cover/upload", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, label, filename: file.name, data: base64 }),
    });
    if (res.ok) {
      const data = await res.json();
      refreshCard(code, label, false, data.file);
    } else {
      const data = await res.json();
      alert(`erro no upload: ${data.error || "falha"}`);
    }
  };
  reader.readAsDataURL(file);
}

function openLightbox(src, label, displayName) {
  const overlay = document.getElementById("lightbox");
  document.getElementById("lightbox-img").src = src;
  document.getElementById("lightbox-label").textContent = displayName || label;
  overlay.classList.remove("hidden");
}

function closeLightbox() {
  document.getElementById("lightbox").classList.add("hidden");
}

document.getElementById("lightbox").addEventListener("click", closeLightbox);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") { closeLightbox(); closeSettings(); closeEdit(); closeOrganize(); closeSortear(); closeMaint(); closeObs(); closeLista(); closeCapa(); closeEditar(); closeDecompor(); }
});

async function openSettings() {
  document.getElementById("settings-status").textContent = "";
  const res = await fetch("/api/settings");
  const cfg = await res.json();
  const form = document.getElementById("settings-form");
  form.innerHTML = "";
  for (const section of ["pc", "android"]) {
    const heading = document.createElement("strong");
    heading.textContent = section === "pc" ? "PC" : "Android";
    form.appendChild(heading);
    for (const [key, value] of Object.entries(cfg[section] || {})) {
      const label = document.createElement("label");
      label.dataset.section = section;
      label.dataset.key = key;
      label.innerHTML = `${key}<input type="text" value="${value.replace(/"/g, "&quot;")}">`;
      form.appendChild(label);
    }
  }
  document.getElementById("settings-modal").classList.remove("hidden");
}

function closeSettings() {
  document.getElementById("settings-modal").classList.add("hidden");
}

async function saveSettings() {
  const updates = { pc: {}, android: {} };
  document.querySelectorAll("#settings-form label").forEach(label => {
    const section = label.dataset.section;
    const key = label.dataset.key;
    const input = label.querySelector("input");
    updates[section][key] = input.value;
  });
  const status = document.getElementById("settings-status");
  status.textContent = "salvando...";
  const res = await fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
  if (res.ok) {
    status.textContent = "salvo";
    loadSystems();
    setTimeout(closeSettings, 600);
  } else {
    const data = await res.json();
    status.textContent = `erro: ${data.error || "falha ao salvar"}`;
    status.style.color = "var(--err)";
  }
}

document.getElementById("btn-settings").addEventListener("click", openSettings);
document.getElementById("btn-settings-close").addEventListener("click", closeSettings);
document.getElementById("btn-settings-save").addEventListener("click", saveSettings);
document.getElementById("settings-modal").addEventListener("click", (e) => {
  if (e.target.id === "settings-modal") closeSettings();
});

let searchCtx = { code: null, label: null };

function openEdit(code, label, displayName, noCover) {
  // searchCtx.label é sempre o nome curto de verdade (o que vira
  // arquivo em disco) - displayName só melhora o que aparece na tela,
  // o campo de renomear (prefill) e o termo de busca pré-preenchido
  // (buscar "Metal Slug 2" nas fontes de capa dá resultado bem melhor
  // que buscar "mslug2"). Um modal só pras 3 ações que antes eram
  // botões separados (Renomear/Buscar/Trocar) - pedido do usuário
  // (27/08): "unificar... e ai sim abre um popup pra ver se vai mudar
  // capa ou nome". Sem capa ainda (noCover) esconde Renomear (não tem
  // o que renomear até existir uma capa de verdade).
  searchCtx = { code, label, displayName };
  document.getElementById("search-label").textContent = displayName || label;
  document.getElementById("edit-rename-row").classList.toggle("hidden", noCover);
  document.getElementById("edit-rename-input").value = label;
  document.getElementById("search-query").value = displayName || label;
  document.getElementById("search-results").innerHTML = "";
  document.getElementById("search-modal").classList.remove("hidden");
  runSearch();
}

function closeEdit() {
  document.getElementById("search-modal").classList.add("hidden");
}

async function runSearch() {
  const results = document.getElementById("search-results");
  results.innerHTML = '<div class="empty-state">buscando...</div>';
  const q = document.getElementById("search-query").value.trim();
  let items;
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    const res = await fetch(`/api/cover/search?code=${searchCtx.code}&q=${encodeURIComponent(q)}`, { signal: controller.signal });
    clearTimeout(timeoutId);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    items = await res.json();
  } catch (e) {
    results.innerHTML = `<div class="empty-state">Erro na busca (${e.name === "AbortError" ? "demorou demais" : e.message}) - tenta de novo.</div>`;
    return;
  }
  results.innerHTML = "";
  if (items.length === 0) {
    results.innerHTML = '<div class="empty-state">Nada encontrado - tenta outro termo.</div>';
    return;
  }
  for (const item of items) {
    const card = document.createElement("div");
    card.className = "search-result";
    const sourceLabel = { libretro: "libretro-thumbnails", launchbox: "LaunchBox", screenscraper: "ScreenScraper" }[item.source] || item.source;
    card.innerHTML = `
      <img src="${item.preview}" loading="lazy" alt="${item.name}">
      <div class="search-result-name" title="${item.name}">${item.name}</div>
      <div class="search-result-source">${sourceLabel}</div>
    `;
    card.addEventListener("click", () => selectCandidate(item));
    results.appendChild(card);
  }
}

async function selectCandidate(item) {
  const results = document.getElementById("search-results");
  results.innerHTML = '<div class="empty-state">aplicando...</div>';
  let res;
  try {
    res = await fetch("/api/cover/select", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        code: searchCtx.code, label: searchCtx.label,
        source: item.source, name: item.name, filename: item.filename || "",
        ss_id: item.ss_id || "",
      }),
    });
  } catch (e) {
    results.innerHTML = `<div class="empty-state">Erro ao aplicar (${e.message}) - tenta de novo.</div>`;
    return;
  }
  if (res.ok) {
    closeEdit();
    refreshCard(searchCtx.code, searchCtx.label, false, searchCtx.label + ".png");
  } else {
    const data = await res.json();
    results.innerHTML = `<div class="empty-state">erro: ${data.error || "falha ao aplicar"}</div>`;
  }
}

document.getElementById("btn-search-close").addEventListener("click", closeEdit);
document.getElementById("btn-search-go").addEventListener("click", runSearch);
document.getElementById("search-query").addEventListener("keydown", (e) => {
  if (e.key === "Enter") runSearch();
});
document.getElementById("search-modal").addEventListener("click", (e) => {
  if (e.target.id === "search-modal") closeEdit();
});
document.getElementById("btn-edit-rename").addEventListener("click", async () => {
  const newLabel = document.getElementById("edit-rename-input").value.trim();
  if (!newLabel || newLabel === searchCtx.label) return;
  const res = await fetch("/api/cover/rename", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code: searchCtx.code, label: searchCtx.label, new_label: newLabel }),
  });
  const data = await res.json();
  if (res.ok) {
    closeEdit();
    selectSystem(searchCtx.code); // ordem alfabetica muda de posicao - recarrega a galeria inteira
    if (data.cascade) alert(describeCascade(data.cascade));
  } else {
    alert(`erro ao renomear: ${data.error || "falha"}`);
  }
});
document.getElementById("edit-upload-input").addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (!file) return;
  closeEdit();
  uploadCover(searchCtx.code, searchCtx.label, file);
});

function startFetch(fallbackSource) {
  if (!currentSystem) return;
  const apply = document.getElementById("apply-toggle").checked ? "1" : "0";
  const fallback = fallbackSource || "0";

  const panel = document.getElementById("progress-panel");
  const fill = document.getElementById("progress-fill");
  const log = document.getElementById("progress-log");
  panel.classList.remove("hidden");
  fill.style.width = "0%";
  log.innerHTML = "";

  document.getElementById("btn-fetch").disabled = true;
  document.getElementById("btn-fallback-launchbox").disabled = true;
  document.getElementById("btn-fallback-screenscraper").disabled = true;

  fetch(`/api/fetch/${currentSystem}?apply=${apply}&fallback=${fallback}`, { method: "POST" })
    .then(r => r.json())
    .then(({ job }) => {
      const evtSource = new EventSource(`/api/fetch/stream?job=${job}`);
      evtSource.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === "progress") {
          const pct = data.total ? Math.round((data.i / data.total) * 100) : 0;
          fill.style.width = pct + "%";
          const line = document.createElement("div");
          line.textContent = `[${data.code}] ${data.label} — ${data.status}`;
          log.appendChild(line);
          log.scrollTop = log.scrollHeight;
        } else if (data.type === "system_done") {
          const line = document.createElement("div");
          line.textContent = `[${data.code}] concluído: ${JSON.stringify(data.result)}`;
          log.appendChild(line);
          log.scrollTop = log.scrollHeight;
        } else if (data.type === "error") {
          const line = document.createElement("div");
          line.textContent = `erro: ${data.message}`;
          line.style.color = "var(--err)";
          log.appendChild(line);
        } else if (data.type === "job_done") {
          evtSource.close();
          document.getElementById("btn-fetch").disabled = false;
          document.getElementById("btn-fallback-launchbox").disabled = false;
          document.getElementById("btn-fallback-screenscraper").disabled = false;
          loadSystems().then(() => {
            if (currentSystem) selectSystem(currentSystem);
          });
        }
      };
    });
}

document.getElementById("btn-fetch").addEventListener("click", () => startFetch(""));
document.getElementById("btn-fallback-launchbox").addEventListener("click", () => startFetch("launchbox"));
document.getElementById("btn-fallback-screenscraper").addEventListener("click", () => startFetch("screenscraper"));

let heavySystems = [];
let heavyItems = [];

// ROMs pesadas agora é aba do #system-tabs, não popup (pedido do
// usuário, 27/08: "mesma visualização das ROMs normais") - grade de
// capa igual a galeria leve, com botões próprios (Enviar/Baixar no
// lugar de Editar, já que não faz sentido editar capa/nome de um item
// que pode nem estar baixado ainda).
async function selectHeavyTab(code) {
  currentSystem = code;
  currentKind = "pesado";
  activateTab(code);
  setControlsForKind("pesado");
  const sys = heavySystems.find(s => s.code === code);
  document.getElementById("current-system").textContent = `${code} — ${sys.nome} (pesado)`;

  const gallery = document.getElementById("gallery");
  gallery.innerHTML = '<div class="empty-state">carregando (catálogo do Drive pode demorar)...</div>';
  const res = await fetch(`/api/heavy/roms/${code}`);
  const data = await res.json();
  heavyItems = data.items;
  if (!data.android_ok) {
    document.getElementById("current-system").textContent += " · celular não conectado";
  }
  renderHeavyGrid();
}

function renderHeavyGrid() {
  const gallery = document.getElementById("gallery");
  gallery.innerHTML = "";
  const onlyNoCover = document.getElementById("heavy-filter-nocover").checked;
  const items = onlyNoCover ? heavyItems.filter(i => !i.capa) : heavyItems;

  if (heavyItems.length === 0) {
    gallery.innerHTML = `<div class="empty-state">Nada em roms_root/${currentSystem}/ nem no Drive.</div>`;
    return;
  }
  if (items.length === 0) {
    gallery.innerHTML = '<div class="empty-state">Nada bate com esse filtro.</div>';
    return;
  }
  for (const item of items) {
    gallery.appendChild(buildHeavyCard(currentSystem, item));
  }
}

document.getElementById("heavy-filter-nocover").addEventListener("change", renderHeavyGrid);

function buildHeavyCard(code, item) {
  const notInPc = !item.in_pc;
  const onCelular = item.status === "no_celular";
  const div = document.createElement("div");
  div.className = "cover";
  div.dataset.label = item.name;
  // item.capa já vem conferido pelo servidor (existe no disco ou não,
  // ver gui/server.py) - evita <img> quebrada gerando 404 no console
  // pra todo item sem match exato (PS1 nunca tem, ver COVERS_EXCLUDED).
  const coverHtml = item.capa
    ? `<img src="${item.capa}" alt="${item.name}">`
    : `<div class="cover-placeholder">${item.is_dir ? "📁" : "🖼<br>sem capa"}</div>`;
  div.innerHTML = `
    <div class="cover-img-wrap">
      ${coverHtml}
      ${notInPc ? '<span class="lib-badge">☁ só no Drive</span>' : (item.in_drive ? '<span class="lib-badge">☁ no Drive</span>' : "")}
    </div>
    <div class="label" title="${item.name}">${item.is_dir ? "📁 " : ""}${item.name}</div>
    <div class="card-meta">${notInPc ? "só no Drive" : (onCelular ? "no celular" : "só no PC")}</div>
    <div class="cover-actions">
      ${notInPc
        ? '<button class="tiny" data-action="download">⬇ Baixar</button>'
        : `<button class="tiny secondary" data-action="rename">✎ Renomear</button>
           <button class="tiny ${onCelular ? "secondary" : ""}" data-action="send">${onCelular ? "Reenviar" : "Enviar"}</button>
           <button class="tiny danger" data-action="delete">🗑 Apagar</button>`}
    </div>
  `;

  if (notInPc) {
    div.querySelector('[data-action="download"]').addEventListener("click", () => downloadHeavyItem(code, item.name));
  } else {
    div.querySelector('[data-action="rename"]').addEventListener("click", () => renameHeavyItem(code, item));
    div.querySelector('[data-action="send"]').addEventListener("click", () => sendHeavyItem(code, item.name, onCelular));
    div.querySelector('[data-action="delete"]').addEventListener("click", () => deleteHeavyItem(code, item));
  }

  // Tracking universal (iniciado/finalizado/platinado/nota) - mesmo
  // mecanismo da ROM leve (ver buildCoverCard), fonte "rom:<CODIGO>" e
  // nome sempre o stem sem extensão (mesmo valor que a Biblioteca já
  // cruza, ver biblioteca_info em /api/heavy/roms).
  const sysLabel = (heavySystems.find(s => s.code === code) || {}).nome || code;
  const nome = stemOf(item);
  div.appendChild(buildTrackingRow(item.biblioteca, (field, value) => {
    item.biblioteca = { ...(item.biblioteca || { nota: null, iniciado: false, finalizado: false, platinado: false }), [field]: value };
    trackGame(nome, code, sysLabel, `rom:${code}`, field, value);
  }, nome, [
    { icone: "🖼", titulo: "Buscar/trocar capa",
      onClick: () => openCapa(nome, { kind: "rom", code, label: nome }, () => selectHeavyTab(code)) },
  ]));
  return div;
}

function sendHeavyItem(code, name, overwrite) {
  if (overwrite && !confirm(`"${name}" já está no celular. Sobrescrever?`)) return;
  const row = document.querySelector(`.cover[data-label="${CSS.escape(name)}"]`);
  const btn = row && row.querySelector('[data-action="send"]');
  if (btn) { btn.disabled = true; btn.textContent = "Enviando..."; }

  fetch("/api/heavy/send", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, name, overwrite }),
  })
    .then(r => r.json())
    .then(({ job }) => {
      const evtSource = new EventSource(`/api/fetch/stream?job=${job}`);
      evtSource.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === "progress" && btn) {
          btn.textContent = data.status === "conectando" ? "Conectando..." : "Enviando...";
        } else if (data.type === "system_done") {
          if (!data.result.ok) alert(`falha ao enviar: ${data.result.message}`);
        } else if (data.type === "error") {
          alert(`erro: ${data.message}`);
        } else if (data.type === "job_done") {
          evtSource.close();
          if (currentSystem === code) selectHeavyTab(code); // recarrega status
        }
      };
    });
}

function downloadHeavyItem(code, name) {
  const row = document.querySelector(`.cover[data-label="${CSS.escape(name)}"]`);
  const btn = row && row.querySelector('[data-action="download"]');
  if (btn) { btn.disabled = true; btn.textContent = "Baixando..."; }

  fetch("/api/heavy/download", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, name }),
  })
    .then(r => r.json())
    .then(({ job }) => {
      const evtSource = new EventSource(`/api/fetch/stream?job=${job}`);
      evtSource.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === "system_done") {
          if (!data.result.ok) alert(`falha ao baixar: ${data.result.message}`);
        } else if (data.type === "error") {
          alert(`erro: ${data.message}`);
        } else if (data.type === "job_done") {
          evtSource.close();
          if (currentSystem === code) selectHeavyTab(code); // recarrega status
        }
      };
    });
}

async function renameHeavyItem(code, item) {
  const oldLabel = stemOf(item);
  const input = prompt("Novo nome (sem extensão) - também tenta renomear save/state junto:", oldLabel);
  if (input === null) return;
  const newLabel = input.trim();
  if (!newLabel || newLabel === oldLabel) return;
  const res = await fetch("/api/heavy/rename", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, old_label: oldLabel, new_label: newLabel }),
  });
  const data = await res.json();
  if (res.ok) {
    if (data.cascade) alert(describeCascade(data.cascade));
    selectHeavyTab(code);
  } else {
    alert(`erro ao renomear: ${data.error || "falha"}`);
  }
}

async function deleteHeavyItem(code, item) {
  const label = stemOf(item);
  if (!confirm(`Apagar "${item.name}" (ROM + save/state)? Isso não pode ser desfeito.`)) return;
  const res = await fetch("/api/heavy/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, label }),
  });
  const data = await res.json();
  if (res.ok) {
    alert(describeDeleteCascade(data.cascade));
    selectHeavyTab(code);
  } else {
    alert(`erro ao apagar: ${data.error || "falha"}`);
  }
}

function openOrganize() {
  document.getElementById("organize-modal").classList.remove("hidden");
  loadOrganizePending();
}

function closeOrganize() {
  document.getElementById("organize-modal").classList.add("hidden");
}

async function loadOrganizePending() {
  const list = document.getElementById("organize-list");
  list.innerHTML = '<div class="empty-state">carregando...</div>';
  const res = await fetch("/api/organize/pending");
  const data = await res.json();
  document.getElementById("organize-status").textContent = `(roms_root/${data.staging_dir}/)`;
  renderOrganizeList(data.items);
}

function renderOrganizeList(items) {
  const list = document.getElementById("organize-list");
  list.innerHTML = "";
  if (items.length === 0) {
    list.innerHTML = '<div class="empty-state">Nada esperando organização.</div>';
    return;
  }
  for (const item of items) {
    const row = document.createElement("div");
    row.className = "heavy-item";
    row.dataset.name = item.name;

    let controls;
    if (item.candidates.length === 0) {
      controls = '<div class="heavy-item-status">extensão não reconhecida</div>';
    } else {
      const options = item.candidates
        .map(c => `<option value="${c.code}">${c.code} - ${c.nome}</option>`)
        .join("");
      controls = `
        <select class="organize-select">${options}</select>
        <button class="tiny" data-action="move">Mover</button>
      `;
    }

    row.innerHTML = `
      <div class="heavy-item-name" title="${item.name}">${item.is_dir ? "📁 " : ""}${item.name}</div>
      <div class="heavy-item-size">${formatGB(item.size)}</div>
      ${controls}
    `;
    const btn = row.querySelector('[data-action="move"]');
    if (btn) {
      btn.addEventListener("click", () => {
        const code = row.querySelector(".organize-select").value;
        moveOrganizeItem(item.name, code);
      });
    }
    list.appendChild(row);
  }
}

async function moveOrganizeItem(name, code) {
  const res = await fetch("/api/organize/move", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, code }),
  });
  const data = await res.json();
  if (res.ok) {
    const statusEl = document.getElementById("organize-status");
    const prevText = statusEl.textContent;
    const coverMsg = {
      exact: "✓ capa baixada automaticamente",
      fuzzy: "capa parecida encontrada - revise em \"Buscar capas\"",
      no_match: "sem capa correspondente - use 🖼 Só sem capa na galeria pra buscar/subir manualmente",
    }[data.cover];
    if (coverMsg) {
      statusEl.textContent = `${name} → ${code}/: ${coverMsg}`;
      setTimeout(() => { statusEl.textContent = prevText; }, 5000);
    }
    loadOrganizePending();
    loadSystems(); // contagem de capas do sistema destino pode ter mudado
  } else {
    alert(`erro ao mover: ${data.error || "falha"}`);
  }
}

document.getElementById("btn-organize").addEventListener("click", openOrganize);
document.getElementById("btn-organize-close").addEventListener("click", closeOrganize);
document.getElementById("organize-modal").addEventListener("click", (e) => {
  if (e.target.id === "organize-modal") closeOrganize();
});

let savesCards = [];       // [{console, label, key, tool_ok}]
let savesItemsByKey = {};  // key -> items[] (carregado uma vez, uma seção por card)
let emuSaves = {}; // "GC"/"PSP" -> {items, android_ok} | {error}
let currentSavesConsole = "PS1";
const SAVES_CONSOLES = [
  { key: "PS1", label: "PS1" }, { key: "PS2", label: "PS2" },
  { key: "GC", label: "GameCube" }, { key: "PSP", label: "PPSSPP" },
];

function openSaves() {
  document.getElementById("saves-modal").classList.remove("hidden");
  loadSavesCards();
}

function closeSaves() {
  document.getElementById("saves-modal").classList.add("hidden");
}

function savesStatus(msg) {
  document.getElementById("saves-status").textContent = msg;
}

async function loadSavesCards() {
  const list = document.getElementById("saves-list");
  list.innerHTML = '<div class="empty-state">carregando...</div>';
  savesStatus("");
  const res = await fetch("/api/memcards");
  savesCards = await res.json();

  // Carrega o conteúdo de tudo de uma vez (troca de aba fica
  // instantânea, sem esperar a rede de novo) - uma seção por card em
  // PS1/PS2 (pedido do usuário de não precisar trocar de card pra
  // comparar), mais o backup de saves individualizados do
  // Dolphin(GameCube)/PPSSPP. Navegação entre CONSOLES é por aba,
  // igual o resto do app (galeria, ROMs Pesadas).
  await Promise.all([
    ...savesCards.filter(c => c.tool_ok).map(async (card) => {
      const r = await fetch(`/api/memcards/list/${encodeURIComponent(card.key)}`);
      const data = await r.json();
      savesItemsByKey[card.key] = r.ok ? data.items : { error: data.error || "falha ao ler o card" };
    }),
    ...["GC", "PSP"].map(async (emu) => {
      const r = await fetch(`/api/emu_saves/list/${emu}`);
      const data = await r.json();
      emuSaves[emu] = r.ok ? data : { error: data.error || "falha ao ler" };
    }),
  ]);

  renderSavesTabs();
  selectSavesConsole(currentSavesConsole);
}

function renderSavesTabs() {
  const tabs = document.getElementById("saves-console-tabs");
  tabs.innerHTML = "";
  for (const c of SAVES_CONSOLES) {
    const tab = document.createElement("div");
    tab.className = "tab";
    tab.dataset.console = c.key;
    tab.textContent = c.label;
    tab.addEventListener("click", () => selectSavesConsole(c.key));
    tabs.appendChild(tab);
  }
}

function selectSavesConsole(consoleName) {
  currentSavesConsole = consoleName;
  document.querySelectorAll("#saves-console-tabs .tab").forEach(tab => {
    tab.classList.toggle("active", tab.dataset.console === consoleName);
  });
  savesStatus("");
  renderSavesList();
}

function formatSaveSize(item) {
  // PS2 "size" no -ls é contagem de arquivos dentro da pasta, não
  // bytes (só o PS1 devolve tamanho real do save) - formata diferente
  // pra não mostrar "0 KB" enganoso.
  return item.type === "dir" ? `${item.size} arquivo${item.size === 1 ? "" : "s"}` : `${(item.size / 1024).toFixed(0)} KB`;
}

function renderSavesList() {
  const list = document.getElementById("saves-list");
  list.innerHTML = "";

  if (currentSavesConsole === "PS1" || currentSavesConsole === "PS2") {
    const cards = savesCards.filter(c => c.console === currentSavesConsole);
    if (cards.length === 0) {
      list.innerHTML = `<div class="empty-state">Nenhum card de ${currentSavesConsole} configurado em config.toml [memcards].</div>`;
      return;
    }
    for (const card of cards) {
      const cardBox = document.createElement("div");
      cardBox.className = "saves-card-section";
      const header = document.createElement("div");
      header.className = "saves-card-header";
      header.innerHTML = `
        <span>${card.label}</span>
        <div class="saves-card-actions">
          <label class="tiny secondary import-label">📥 Importar save<input type="file" class="import-input" hidden></label>
          <button class="tiny secondary" data-action="remove-card">✕ Remover</button>
        </div>
      `;
      header.querySelector(".import-input").addEventListener("change", (e) => {
        if (e.target.files[0]) importSaveFile(card.key, e.target.files[0]);
      });
      header.querySelector('[data-action="remove-card"]').addEventListener("click", () => removeMemcard(card));
      cardBox.appendChild(header);

      if (!card.tool_ok) {
        cardBox.innerHTML += `<div class="empty-state">Ferramenta "${currentSavesConsole === "PS1" ? "ps1vmc-tool" : "ps2vmc-tool"}" não encontrada no PATH - veja docs/memory_card_editor.md.</div>`;
        list.appendChild(cardBox);
        continue;
      }
      const data = savesItemsByKey[card.key];
      if (!data || data.error) {
        cardBox.innerHTML += `<div class="empty-state">erro: ${data ? data.error : "falha ao ler o card"}</div>`;
        list.appendChild(cardBox);
        continue;
      }
      const saveItems = data.filter(i => i.type !== "link");
      if (saveItems.length === 0) {
        cardBox.innerHTML += '<div class="empty-state">Card vazio.</div>';
        list.appendChild(cardBox);
        continue;
      }
      for (const item of saveItems) {
        const row = document.createElement("div");
        row.className = "heavy-item";
        const title = item.name || `(desconhecido - ${item.raw_name})`;
        // "individualizado" aqui seria enganoso - TODO save de PS1/PS2
        // vive dentro de um card compartilhado, o que essa badge mostra
        // de fato é se o nome do jogo foi resolvido a partir do serial.
        const badge = item.name ? "nome identificado" : "serial desconhecido";
        row.innerHTML = `
          <div class="heavy-item-name" title="${item.raw_name}">${title}</div>
          <div class="heavy-item-size">${formatSaveSize(item)}</div>
          <div class="heavy-item-status ${item.name ? "ok" : ""}">${badge}</div>
          <button class="tiny secondary" data-action="export">⬇ Exportar</button>
          <button class="tiny secondary" data-action="transfer">↔ Transferir</button>
          <button class="tiny danger" data-action="delete">🗑 Apagar</button>
        `;
        row.querySelector('[data-action="export"]').addEventListener("click", () => exportSaveItem(card.key, item));
        row.querySelector('[data-action="transfer"]').addEventListener("click", () => transferSaveItem(card.key, item, row));
        row.querySelector('[data-action="delete"]').addEventListener("click", () => deleteSaveItem(card.key, item));
        cardBox.appendChild(row);
      }
      list.appendChild(cardBox);
    }
    return;
  }

  // GC / PSP - lista flat (sem card, um único inventário no celular).
  const emu = currentSavesConsole;
  const data = emuSaves[emu];
  if (!data || data.error) {
    list.innerHTML = `<div class="empty-state">erro: ${data ? data.error : "falha ao carregar"}</div>`;
    return;
  }
  if (!data.android_ok) {
    list.innerHTML = '<div class="empty-state">Celular não conectado - conecte via USB pra ver/baixar saves.</div>';
    return;
  }
  if (data.items.length === 0) {
    list.innerHTML = '<div class="empty-state">Nada encontrado no celular.</div>';
    return;
  }
  for (const item of data.items) {
    const row = document.createElement("div");
    row.className = "heavy-item";
    const title = item.name || `(desconhecido - ${item.raw_name})`;
    row.innerHTML = `
      <div class="heavy-item-name" title="${item.raw_name}">${title}</div>
      <div class="heavy-item-status ${item.in_pc ? "ok" : ""}">${item.in_pc ? "no PC" : "só no celular"}</div>
      ${item.in_pc ? "" : '<button class="tiny secondary" data-action="pull">⬇ Baixar do celular</button>'}
    `;
    const pullBtn = row.querySelector('[data-action="pull"]');
    if (pullBtn) pullBtn.addEventListener("click", () => pullEmuSaveItem(emu, item, pullBtn));
    list.appendChild(row);
  }
}

async function pullEmuSaveItem(emu, item, btn) {
  btn.disabled = true;
  btn.textContent = "Baixando...";
  const res = await fetch("/api/emu_saves/pull", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ emu, item }),
  });
  const data = await res.json();
  if (res.ok) {
    savesStatus(`baixado: ${data.file}`);
    item.in_pc = true;
    renderSavesList();
  } else {
    btn.disabled = false;
    btn.textContent = "⬇ Baixar do celular";
    alert(`erro ao baixar: ${data.error || "falha"}`);
  }
}

async function exportSaveItem(key, item) {
  const res = await fetch("/api/memcards/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key, item }),
  });
  const data = await res.json();
  if (res.ok) {
    savesStatus(`exportado: ${data.file}`);
  } else {
    alert(`erro ao exportar: ${data.error || "falha"}`);
  }
}

async function deleteSaveItem(key, item) {
  const title = item.name || item.raw_name;
  if (!confirm(`Apagar o save de "${title}" do card? Ação irreversível.`)) return;
  const res = await fetch("/api/memcards/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key, item }),
  });
  const data = await res.json();
  if (res.ok) {
    savesStatus(`apagado: ${title}`);
    const r = await fetch(`/api/memcards/list/${encodeURIComponent(key)}`);
    const d = await r.json();
    savesItemsByKey[key] = r.ok ? d.items : { error: d.error };
    renderSavesList();
  } else {
    alert(`erro ao apagar: ${data.error || "falha"}`);
  }
}

function transferSaveItem(key, item, row) {
  const consoleName = key.split(":")[0].toUpperCase();
  const others = savesCards.filter(c => c.console === consoleName && c.key !== key && c.tool_ok);
  if (others.length === 0) {
    alert("Não há outro card desse console configurado pra transferir.");
    return;
  }
  const controls = row.querySelector(".transfer-controls");
  if (controls) { controls.remove(); return; } // toggle: clicar de novo cancela
  const box = document.createElement("div");
  box.className = "transfer-controls";
  const options = others.map(c => `<option value="${c.key}">${c.label}</option>`).join("");
  box.innerHTML = `
    <select class="organize-select">${options}</select>
    <button class="tiny" type="button">Mover</button>
  `;
  box.querySelector("button").addEventListener("click", async () => {
    const destKey = box.querySelector("select").value;
    const res = await fetch("/api/memcards/transfer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ src_key: key, dest_key: destKey, item }),
    });
    const data = await res.json();
    if (res.ok) {
      savesStatus(`transferido: ${item.name || item.raw_name} -> ${destKey.split(":")[1]}`);
      const keys = [key, destKey];
      await Promise.all(keys.map(async (k) => {
        const r = await fetch(`/api/memcards/list/${encodeURIComponent(k)}`);
        const d = await r.json();
        savesItemsByKey[k] = r.ok ? d.items : { error: d.error };
      }));
      renderSavesList();
    } else {
      alert(`erro ao transferir: ${data.error || "falha"}`);
    }
  });
  row.appendChild(box);
}

async function addMemcard() {
  const consoleName = document.getElementById("saves-add-console").value;
  const label = document.getElementById("saves-add-label").value.trim();
  const path = document.getElementById("saves-add-path").value.trim();
  const mode = document.getElementById("saves-add-mode-create").checked ? "create" : "open";
  if (!label || !path) {
    alert("preencha o nome e o caminho do card");
    return;
  }
  const res = await fetch("/api/memcards/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ console: consoleName, label, path, mode }),
  });
  const data = await res.json();
  if (res.ok) {
    document.getElementById("saves-add-card").classList.add("hidden");
    document.getElementById("saves-add-label").value = "";
    document.getElementById("saves-add-path").value = "";
    document.getElementById("saves-add-mode-create").checked = false;
    await loadSavesCards();
    selectSavesConsole(consoleName.toUpperCase());
    savesStatus(`card adicionado: ${label}`);
  } else {
    alert(`erro ao adicionar card: ${data.error || "falha"}`);
  }
}

async function removeMemcard(card) {
  if (!confirm(`Desregistrar "${card.label}" (${card.console})? O arquivo do card NÃO é apagado, só some da lista.`)) return;
  const res = await fetch("/api/memcards/remove", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ console: card.console.toLowerCase(), label: card.label }),
  });
  const data = await res.json();
  if (res.ok) {
    await loadSavesCards();
  } else {
    alert(`erro ao remover: ${data.error || "falha"}`);
  }
}

function importSaveFile(key, file) {
  const reader = new FileReader();
  reader.onload = async () => {
    const data_b64 = reader.result.split(",")[1];
    const res = await fetch("/api/memcards/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key, filename: file.name, data: data_b64 }),
    });
    const data = await res.json();
    if (res.ok) {
      savesStatus(`importado: ${file.name}`);
      const r = await fetch(`/api/memcards/list/${encodeURIComponent(key)}`);
      const d = await r.json();
      savesItemsByKey[key] = r.ok ? d.items : { error: d.error };
      renderSavesList();
    } else {
      alert(`erro ao importar: ${data.error || "falha"}`);
    }
  };
  reader.readAsDataURL(file);
}

document.getElementById("btn-saves").addEventListener("click", openSaves);
document.getElementById("btn-saves-close").addEventListener("click", closeSaves);
document.getElementById("saves-modal").addEventListener("click", (e) => {
  if (e.target.id === "saves-modal") closeSaves();
});
document.getElementById("btn-saves-add-toggle").addEventListener("click", () => {
  document.getElementById("saves-add-card").classList.toggle("hidden");
});
document.getElementById("saves-add-confirm").addEventListener("click", addMemcard);

// Biblioteca - jogos "de fora" das ROMs (Steam/Heroic/PSN/Xbox +
// planilha importada, ver core/library.py). V1 é só visualização/busca
// - carrega tudo de uma vez (few centenas de jogos, não escala mal) e
// filtra no cliente; cadastro continua via CLI (library-add etc).
let libraryGames = [];

async function selectLibraryTab() {
  currentSystem = "BIBLIOTECA";
  currentKind = "biblioteca";
  activateTab("BIBLIOTECA");
  setControlsForKind("biblioteca");
  await loadLibrary();
}

async function loadLibrary() {
  document.getElementById("gallery").innerHTML = '<div class="empty-state">carregando...</div>';
  const res = await fetch("/api/library");
  libraryGames = await res.json();
  renderLibraryGroupTabs();
  renderLibraryGrid();
}

// Sub-abas por plataforma/loja: o agrupamento em si mora em
// logic.js (libraryTabGroupsFor); aqui é só a navegação. "Todos" é a
// aba default.
let currentLibraryGroup = "";

function renderLibraryGroupTabs() {
  const nav = document.getElementById("library-group-tabs");
  const groups = new Set();
  for (const g of libraryGames) {
    for (const label of libraryTabGroupsFor(g)) groups.add(label);
  }
  if (!groups.has(currentLibraryGroup)) currentLibraryGroup = "";

  nav.innerHTML = "";
  const allTab = document.createElement("div");
  allTab.className = "tab" + (currentLibraryGroup === "" ? " active" : "");
  allTab.textContent = "Todos";
  allTab.addEventListener("click", () => { currentLibraryGroup = ""; renderLibraryGroupTabs(); renderLibraryGrid(); });
  nav.appendChild(allTab);

  for (const label of [...groups].sort()) {
    const tab = document.createElement("div");
    tab.className = "tab" + (currentLibraryGroup === label ? " active" : "");
    tab.textContent = label;
    tab.addEventListener("click", () => { currentLibraryGroup = label; renderLibraryGroupTabs(); renderLibraryGrid(); });
    nav.appendChild(tab);
  }
}

function renderLibraryGrid() {
  const gallery = document.getElementById("gallery");
  const status = document.getElementById("library-filter-status").value;
  const noCover = document.getElementById("library-filter-nocover").checked;
  const mostrarOcultos = document.getElementById("library-filter-ocultos").checked;
  const sortBy = document.getElementById("library-sort").value;

  let filtered = libraryGames.filter(g => libraryMatchesFilters(g, currentLibraryGroup, status, noCover, mostrarOcultos));
  if (sortBy === "nota") {
    // Ranking: maior nota primeiro, sem nota vai pro final (não é
    // "nota zero" nem some da lista, só não participa da ordenação).
    filtered = filtered
      .filter(g => g.nota !== null)
      .sort((a, b) => b.nota - a.nota || a.nome.localeCompare(b.nome));
  } else {
    filtered.sort((a, b) => a.nome.localeCompare(b.nome));
  }

  document.getElementById("current-system").textContent = `📚 Biblioteca — ${filtered.length} de ${libraryGames.length} jogo(s)`;

  gallery.innerHTML = "";
  if (filtered.length === 0) {
    gallery.innerHTML = sortBy === "nota"
      ? '<div class="empty-state">Nenhum jogo com nota pra rankear (ajuste os filtros ou dê uma nota primeiro).</div>'
      : '<div class="empty-state">Nenhum jogo encontrado.</div>';
    return;
  }
  filtered.forEach((g, i) => {
    gallery.appendChild(buildLibraryCard(g, sortBy === "nota" ? i + 1 : null));
  });
}

function buildLibraryCard(g, rank) {
  // Badge só quando diz algo que a linha de plataforma já não diz -
  // achado 27/08 (print do usuário): jogo sem fonte de loja mostra
  // [plataforma] como badge também (libraryGroupsFor cai pra
  // `[g.plataforma]` quando não tem fonte), duplicando o texto que já
  // aparece uma linha acima; e jogo com UMA fonte só, cujo rótulo
  // amigável é igual à plataforma gravada (ex: plataforma "Steam" +
  // fonte "steam" -> "Steam"), duplicava do mesmo jeito. Só filtra o
  // que é idêntico (case-insensitive) à plataforma - jogo com mais de
  // uma fonte (ex: mesclado por nome com uma loja a mais) continua
  // mostrando a(s) outra(s) como badge normalmente.
  // Meta numa linha só (plataforma + loja extra) em vez de duas linhas
  // separadas + fileira de badges - pedido do usuário 28/08 olhando o
  // print do GOG: "os campos todos meio jogados ainda". Badge só quando
  // diz algo que a plataforma já não diz (jogo sem fonte de loja tem
  // badge = a própria plataforma, ver libraryGroupsFor; e fonte cujo
  // rótulo é igual à plataforma duplicava do mesmo jeito).
  // Dedup pelo APELIDO, não pelo texto cru (correção 28/08): "Epic
  // Games Store" (plataforma) e "Epic Games" (rótulo da fonte
  // heroic:epic) são a mesma loja escrita de dois jeitos, e apareciam
  // as duas lado a lado ("Epic Games Store · Epic Games"); mesma coisa
  // em "PSN físico (PS4) · PSN (físico)". GROUP_TAB_ALIASES já sabe
  // quem é quem (é o mesmo mapa que junta as abas), então passar os
  // dois lados por ele antes de comparar resolve.
  const apelido = (s) => GROUP_TAB_ALIASES[s] || s;
  const platApelido = apelido(g.plataforma);
  const extras = [...new Set(
    g.fontes.map(f => fonteLabel(f)).filter(label => apelido(label) !== platApelido)
  )];
  const meta = [g.plataforma, ...extras].join(" · ");

  const div = document.createElement("div");
  div.className = "cover" + (g.oculto ? " oculto" : "");
  div.dataset.label = g.id;
  div.innerHTML = `
    <div class="cover-img-wrap">
      ${g.capa_url
        ? `<img src="${g.capa_url}" alt="">`
        : `<div class="cover-placeholder">🖼<br>sem capa</div>`}
      ${rank ? `<span class="lib-badge">#${rank}</span>` : ""}
    </div>
    <div class="label" title="${g.nome}">${g.nome}</div>
    <div class="card-meta" title="${meta}">${meta}</div>
  `;

  div.appendChild(buildTrackingRow(g, (field, value) => {
    g[field] = value;
    updateLibraryField(g.id, field, value);
  }, g.nome, [
    { icone: "🖼", titulo: "Buscar/trocar capa",
      // Recarrega do servidor em vez de só mexer no objeto local: é
      // ele que monta a capa_url com a versão nova (ver com_versao),
      // e sem isso o navegador continuaria mostrando a capa antiga.
      onClick: () => openCapa(g.nome, { kind: "biblioteca", id: g.id }, () => loadLibrary()) },
    { icone: "✎", titulo: "Editar dados do jogo",
      onClick: () => openEditar(g, () => loadLibrary()) },
    { icone: "⧉", titulo: "Decompor coletânea nos jogos que ela contém",
      onClick: () => openDecompor(g, () => loadLibrary()) },
    {
      icone: "👁", titulo: g.oculto ? "Mostrar de novo" : "Ocultar da Biblioteca", ativo: g.oculto,
      onClick: (btn) => {
        g.oculto = !g.oculto;
        btn.classList.toggle("ativo", g.oculto);
        btn.title = g.oculto ? "Mostrar de novo" : "Ocultar da Biblioteca";
        div.classList.toggle("oculto", g.oculto);
        updateLibraryField(g.id, "oculto", g.oculto);
        // Com "mostrar ocultos" desligado, o card some na hora de quem
        // acabou de ser ocultado (senão fica um card "fantasma" que já
        // não bate mais com o filtro ativo).
        if (g.oculto && !document.getElementById("library-filter-ocultos").checked) div.remove();
      },
    },
  ]));
  return div;
}

// Erro de gravação precisa ser VISÍVEL e deixar claro que a tela ficou
// diferente do disco (achado 28/08: o usuário clicou numa flag enquanto
// o servidor estava fora do ar - a tela marcou, o disco não, e ficou a
// impressão de "bugou"; só um F5 mostrava a verdade). Erro de rede
// estourava sem try/catch nenhum e nem o alert aparecia.
async function salvarCampo(url, corpo) {
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    });
    if (res.ok) return true;
    const data = await res.json().catch(() => ({}));
    alert(`Não consegui salvar: ${data.error || "falha"}\n\nRecarregue a página (F5) - a tela pode estar mostrando algo diferente do que está salvo.`);
  } catch (e) {
    alert(`Não consegui salvar (servidor fora do ar?): ${e.message}\n\nRecarregue a página (F5) - a tela pode estar mostrando algo diferente do que está salvo.`);
  }
  return false;
}

async function updateLibraryField(gameId, field, value) {
  return salvarCampo("/api/library/update", { id: gameId, field, value });
}

// Sorteio - traz a mesma lógica do comando "sortear" (core/sortear.py)
// pra tela: pool único leve (local) + pesado (catálogo cacheado), peso
// por jogo. Carrega a lista de sistemas só na primeira abertura.
let sortearSystemsLoaded = false;

function openSortear() {
  document.getElementById("sortear-modal").classList.remove("hidden");
  if (!sortearSystemsLoaded) {
    loadSortearSystems();
    sortearSystemsLoaded = true;
  }
}

function closeSortear() {
  document.getElementById("sortear-modal").classList.add("hidden");
}

async function loadSortearSystems() {
  const select = document.getElementById("sortear-system");
  const res = await fetch("/api/sortear/systems");
  const systems = await res.json();
  select.innerHTML = '<option value="">Sortear de tudo</option>' +
    systems.map(s => `<option value="${s.code}">${s.label} (${s.kind})</option>`).join("");
}

async function runSortear() {
  const result = document.getElementById("sortear-result");
  const system = document.getElementById("sortear-system").value;
  result.innerHTML = '<div class="empty-state">sorteando...</div>';

  const res = await fetch(`/api/sortear?system=${encodeURIComponent(system)}`);
  const data = await res.json();
  if (!res.ok) {
    result.innerHTML = `<div class="empty-state">${data.error || "falha ao sortear"}</div>`;
    return;
  }

  let extra = "";
  if (data.kind === "pesado") {
    extra = data.local
      ? '<div class="sortear-note">já está no PC</div>'
      : `<div class="sortear-note">só no Drive - baixe com "heavy-roms ${data.codigo} --download"</div>`;
  }
  const cover = data.capa
    ? `<img class="sortear-cover" src="${data.capa}" alt="">`
    : "";
  result.innerHTML = `
    <div class="sortear-body">
      ${cover}
      <div>
        <div class="sortear-nome">${data.nome}</div>
        <div class="sortear-meta">${data.codigo} - ${data.label} (${data.kind}, ${data.pool_size} jogo(s) no pool)</div>
        ${extra}
      </div>
    </div>
  `;
}

// Decompor coletânea nos jogos que ela contém (pedido do usuário
// 29/08). A tela já abre pré-preenchida com o que existe DENTRO da
// pasta do Switch (ver /api/switch/colecao) - é chute, o usuário
// corrige na mão. O que o backend garante é o vínculo: o nome da
// coletânea vira apelido de um dos jogos, senão a próxima varredura
// recria a coletânea do zero.
let decomporCtx = { id: null, onDone: null };

async function openDecompor(g, onDone) {
  decomporCtx = { id: g.id, onDone };
  document.getElementById("decompor-label").textContent = g.nome;
  document.getElementById("decompor-nomes").value = "";
  document.getElementById("decompor-status").textContent = "";
  const dica = document.getElementById("decompor-dica");
  dica.textContent = "lendo o conteúdo da pasta...";
  document.getElementById("decompor-modal").classList.remove("hidden");

  try {
    const r = await fetch(`/api/switch/colecao?nome=${encodeURIComponent(g.nome)}`).then(x => x.json());
    if (r.sugestoes && r.sugestoes.length) {
      document.getElementById("decompor-nomes").value = r.sugestoes.join("\n");
      dica.textContent = `Sugestão a partir de "${r.pasta}" - confira e corrija.`;
    } else {
      dica.textContent = r.aviso || "Não consegui ler a pasta - digite os jogos na mão.";
    }
  } catch (e) {
    dica.textContent = `Não consegui ler a pasta (${e.message}) - digite os jogos na mão.`;
  }
}

function closeDecompor() {
  document.getElementById("decompor-modal").classList.add("hidden");
  decomporCtx = { id: null, onDone: null };
}

async function salvarDecompor() {
  if (!decomporCtx.id) return;
  const nomes = document.getElementById("decompor-nomes").value
    .split("\n").map(s => s.trim()).filter(Boolean);
  const status = document.getElementById("decompor-status");
  if (!nomes.length) { status.textContent = "informe ao menos um jogo"; return; }
  status.textContent = "decompondo...";
  status.style.color = "";
  const res = await fetch("/api/library/decompor", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: decomporCtx.id, nomes }),
  });
  const data = await res.json();
  if (!res.ok) {
    status.textContent = `erro: ${data.error || "falha"}`;
    status.style.color = "var(--err)";
    return;
  }
  const done = decomporCtx.onDone;
  closeDecompor();
  alert(`${data.criados} jogo(s) criado(s), ${data.reaproveitados} reaproveitado(s).\n\n` +
        `A pasta original ficou vinculada a "${data.vinculo_em}", então a próxima ` +
        `varredura do Switch não vai recriar a coletânea.`);
  if (done) done();
}

document.getElementById("btn-decompor-close").addEventListener("click", closeDecompor);
document.getElementById("btn-decompor-save").addEventListener("click", salvarDecompor);
document.getElementById("decompor-modal").addEventListener("click", (e) => {
  if (e.target.id === "decompor-modal") closeDecompor();
});

// Editor de todos os campos de um jogo da Biblioteca (pedido do
// usuário 28/08: "estender o editar nome para todos os campos" - o
// gatilho foi um nome errado herdado da planilha que ele não tinha como
// consertar pela tela). Grava tudo de uma vez em /api/library/edit
// (tudo-ou-nada); nota/flags continuam na barra do card, que é edição
// de um clique só. `id` e `fontes` ficam de fora de propósito - ver
// EDITABLE_FIELDS em core/library.py.
const EDITAR_CAMPOS = [
  { campo: "nome", rotulo: "Nome" },
  { campo: "plataforma", rotulo: "Plataforma" },
  { campo: "genero", rotulo: "Gênero" },
  { campo: "subgenero", rotulo: "Subgênero" },
  { campo: "desenvolvedora", rotulo: "Desenvolvedora" },
  { campo: "lancamento", rotulo: "Lançamento", dica: "aaaa-mm-dd" },
  { campo: "data_final", rotulo: "Data que finalizou", dica: "aaaa-mm-dd" },
  { campo: "tempo", rotulo: "Tempo jogado", dica: "ex: 31:40:00" },
  { campo: "meta", rotulo: "Meta" },
  { campo: "observacoes", rotulo: "Comentário", textarea: true },
];

let editarCtx = { id: null, onDone: null };

function openEditar(g, onDone) {
  editarCtx = { id: g.id, onDone };
  const box = document.getElementById("editar-campos");
  box.innerHTML = EDITAR_CAMPOS.map(({ campo, rotulo, dica, textarea }) => `
    <label class="obs-campo">${rotulo}${dica ? ` <span class="dica">(${dica})</span>` : ""}
      ${textarea
        ? `<textarea data-campo="${campo}" rows="4"></textarea>`
        : `<input type="text" data-campo="${campo}">`}
    </label>
  `).join("");
  // Valor via .value (não no HTML) pra não precisar escapar aspas do
  // conteúdo - nome de jogo tem apóstrofo o tempo todo ("Where's...").
  for (const { campo } of EDITAR_CAMPOS) {
    box.querySelector(`[data-campo="${campo}"]`).value = g[campo] ?? "";
  }
  document.getElementById("editar-status").textContent = "";
  document.getElementById("editar-modal").classList.remove("hidden");
}

function closeEditar() {
  document.getElementById("editar-modal").classList.add("hidden");
  editarCtx = { id: null, onDone: null };
}

async function salvarEditar() {
  if (!editarCtx.id) return;
  const campos = {};
  document.querySelectorAll("#editar-campos [data-campo]").forEach((el) => {
    campos[el.dataset.campo] = el.value.trim() || null;
  });
  const status = document.getElementById("editar-status");
  status.textContent = "salvando...";
  status.style.color = "";
  const res = await fetch("/api/library/edit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: editarCtx.id, campos }),
  });
  const data = await res.json();
  if (!res.ok) {
    status.textContent = `erro: ${data.error || "falha"}`;
    status.style.color = "var(--err)";
    return;
  }
  const done = editarCtx.onDone;
  closeEditar();
  if (done) done();
}

document.getElementById("btn-editar-close").addEventListener("click", closeEditar);
document.getElementById("btn-editar-save").addEventListener("click", salvarEditar);
document.getElementById("editar-modal").addEventListener("click", (e) => {
  if (e.target.id === "editar-modal") closeEditar();
});

// Capa: busca (SteamGridDB) + upload num popup só, servindo as TRÊS
// abas (pedido do usuário 28/08: "para todos os itens da biblioteca,
// não consigo buscar nem alterar capa... quero ir capeando todos os
// jogos de todas as abas"). ROM leve já tinha isso via "✎ Editar" com
// as fontes dela (libretro/LaunchBox/ScreenScraper); Biblioteca e ROM
// pesada não tinham busca nenhuma, só upload. `alvo` é
// {kind:"biblioteca", id} ou {kind:"rom", code, label}.
let capaCtx = { alvo: null, onDone: null };

function openCapa(nome, alvo, onDone) {
  capaCtx = { alvo, onDone };
  document.getElementById("capa-label").textContent = nome;
  document.getElementById("capa-query").value = nome;
  document.getElementById("capa-results").innerHTML = "";
  document.getElementById("capa-modal").classList.remove("hidden");
  buscarCapa();
}

function closeCapa() {
  document.getElementById("capa-modal").classList.add("hidden");
  capaCtx = { alvo: null, onDone: null };
}

async function buscarCapa() {
  const box = document.getElementById("capa-results");
  const q = document.getElementById("capa-query").value.trim();
  if (q.length < 2) return;
  box.innerHTML = '<div class="empty-state">buscando...</div>';
  let itens;
  try {
    const res = await fetch(`/api/cover/search_sgdb?q=${encodeURIComponent(q)}`);
    itens = await res.json();
    if (itens.error) throw new Error(itens.error);
  } catch (e) {
    box.innerHTML = `<div class="empty-state">erro: ${e.message}</div>`;
    return;
  }
  if (!itens.length) {
    box.innerHTML = '<div class="empty-state">Nada encontrado - tenta outro termo.</div>';
    return;
  }
  box.innerHTML = "";
  for (const item of itens) {
    const card = document.createElement("div");
    card.className = "search-result";
    card.innerHTML = `
      <img src="${item.url}" loading="lazy" alt="${item.nome}">
      <div class="search-result-name" title="${item.nome}">${item.nome}</div>
      <div class="search-result-source">SteamGridDB</div>
    `;
    card.addEventListener("click", () => aplicarCapa(item.url));
    box.appendChild(card);
  }
}

async function aplicarCapa(url) {
  const box = document.getElementById("capa-results");
  box.innerHTML = '<div class="empty-state">aplicando...</div>';
  const res = await fetch("/api/cover/apply_url", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...capaCtx.alvo, url }),
  });
  const data = await res.json();
  if (!res.ok) {
    box.innerHTML = `<div class="empty-state">erro: ${data.error || "falha"}</div>`;
    return;
  }
  const done = capaCtx.onDone;
  closeCapa();
  if (done) done(data.file);
}

document.getElementById("btn-capa-close").addEventListener("click", closeCapa);
document.getElementById("btn-capa-go").addEventListener("click", buscarCapa);
document.getElementById("capa-query").addEventListener("keydown", (e) => {
  if (e.key === "Enter") buscarCapa();
});
document.getElementById("capa-modal").addEventListener("click", (e) => {
  if (e.target.id === "capa-modal") closeCapa();
});
document.getElementById("capa-upload").addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (!file || !capaCtx.alvo) return;
  const alvo = capaCtx.alvo, done = capaCtx.onDone;
  const reader = new FileReader();
  reader.onload = async () => {
    const base64 = reader.result.split(",")[1];
    const url = alvo.kind === "biblioteca" ? "/api/library/cover_upload" : "/api/cover/upload";
    const body = alvo.kind === "biblioteca"
      ? { id: alvo.id, filename: file.name, data: base64 }
      : { code: alvo.code, label: alvo.label, filename: file.name, data: base64 };
    const res = await fetch(url, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) return alert(`erro no upload: ${data.error || "falha"}`);
    closeCapa();
    if (done) done(data.file);
  };
  reader.readAsDataURL(file);
  e.target.value = "";
});

// Comentário + tempo saíram do card pra um popup (pedido do usuário
// 28/08: "o campo comentario, transformar em um botão -> pop up") - a
// textarea no card empurrava tudo pra baixo e era o que mais deixava a
// grade "jogada". Genérico: serve pro card da Biblioteca e pro de ROM
// (leve/pesada), cada um passa seu próprio `onSave`.
let obsCtx = { onSave: null };

function openObs(nome, estado, onSave) {
  obsCtx = { onSave };
  document.getElementById("obs-label").textContent = nome;
  document.getElementById("obs-tempo").value = estado.tempo ?? "";
  document.getElementById("obs-text").value = estado.observacoes ?? "";
  document.getElementById("obs-status").textContent = "";
  document.getElementById("obs-modal").classList.remove("hidden");
  document.getElementById("obs-text").focus();
}

function closeObs() {
  document.getElementById("obs-modal").classList.add("hidden");
  obsCtx = { onSave: null };
}

function salvarObs() {
  if (!obsCtx.onSave) return;
  obsCtx.onSave({
    tempo: document.getElementById("obs-tempo").value.trim() || null,
    observacoes: document.getElementById("obs-text").value.trim() || null,
  });
  document.getElementById("obs-status").textContent = "salvo";
  setTimeout(closeObs, 400);
}

document.getElementById("btn-obs-close").addEventListener("click", closeObs);
document.getElementById("btn-obs-save").addEventListener("click", salvarObs);
document.getElementById("obs-modal").addEventListener("click", (e) => {
  if (e.target.id === "obs-modal") closeObs();
});

// Ranking e Iniciados (pedido do usuário 28/08: botões próprios ao lado
// de Sortear). Diferente das abas, cruzam a coleção INTEIRA de uma vez
// - ROM leve, pesada e Biblioteca juntas - porque desde o tracking
// universal o library.json é a fonte única de progresso pra qualquer
// tipo de jogo (ver GET /api/ranking e /api/iniciados). Só leitura:
// pra editar, o usuário vai no card do jogo na aba dele.
async function openLista(tipo) {
  const titulo = tipo === "ranking" ? "🏅 Ranking (por nota)" : "▶ Iniciados (ainda não finalizados)";
  document.getElementById("lista-titulo").textContent = titulo;
  const box = document.getElementById("lista-conteudo");
  box.innerHTML = '<div class="empty-state">carregando...</div>';
  document.getElementById("lista-modal").classList.remove("hidden");

  const res = await fetch(`/api/${tipo}`);
  const jogos = await res.json();
  if (!jogos.length) {
    box.innerHTML = `<div class="empty-state">${tipo === "ranking"
      ? "Nenhum jogo com nota ainda."
      : "Nenhum jogo em andamento - comece algum e marque ▶."}</div>`;
    return;
  }

  box.innerHTML = "";
  jogos.forEach((g, i) => {
    const linha = document.createElement("div");
    linha.className = "lista-item";
    const cor = notaColor(g.nota);
    linha.innerHTML = `
      ${tipo === "ranking" ? `<span class="lista-pos">${i + 1}</span>` : ""}
      ${g.capa_url
        ? `<img class="lista-capa" src="${g.capa_url}" alt="" loading="lazy" title="Ampliar capa">`
        : '<span class="lista-capa lista-capa-vazia">🖼</span>'}
      <span class="lista-nome" title="${g.nome}">${g.nome}</span>
      <span class="lista-plataforma">${g.plataforma}</span>
      ${g.nota !== null ? `<span class="lista-nota" style="color:${cor};border-color:${cor}">${notaTexto(g.nota)}</span>` : ""}
      <button class="icon-btn${g.observacoes || g.tempo ? " ativo" : ""}" type="button"
              title="Comentário e tempo jogado">💬</button>
    `;
    // Capa amplia; 💬 abre o comentário (pedido do usuário 28/08:
    // "em ranking e iniciados, permitir abrir a capa do jogo e ver o
    // comentario feito"). Editável aqui também - grava por id, igual
    // o card da Biblioteca (vale pra ROM também: desde o tracking
    // universal todo jogo com progresso tem registro no library.json).
    const img = linha.querySelector("img.lista-capa");
    if (img) img.addEventListener("click", () => openLightbox(g.capa_url, g.nome));
    linha.querySelector(".icon-btn").addEventListener("click", (e) => {
      const btn = e.currentTarget;
      openObs(g.nome, g, (campos) => {
        for (const [campo, valor] of Object.entries(campos)) {
          if (valor === (g[campo] ?? null)) continue;
          g[campo] = valor;
          updateLibraryField(g.id, campo, valor);
        }
        btn.classList.toggle("ativo", !!(g.observacoes || g.tempo));
      });
    });
    box.appendChild(linha);
  });
}

function closeLista() {
  document.getElementById("lista-modal").classList.add("hidden");
}

document.getElementById("btn-ranking").addEventListener("click", () => openLista("ranking"));
document.getElementById("btn-iniciados").addEventListener("click", () => openLista("iniciados"));
document.getElementById("btn-lista-close").addEventListener("click", closeLista);
document.getElementById("lista-modal").addEventListener("click", (e) => {
  if (e.target.id === "lista-modal") closeLista();
});

document.getElementById("btn-sortear").addEventListener("click", openSortear);
document.getElementById("btn-sortear-close").addEventListener("click", closeSortear);
document.getElementById("sortear-modal").addEventListener("click", (e) => {
  if (e.target.id === "sortear-modal") closeSortear();
});
document.getElementById("btn-sortear-go").addEventListener("click", runSortear);

// Executor genérico de job (SSE) - usado por tudo que só tem
// ação/lista simples (sem "por item" estruturado que valha renderizar
// individual): refresh/add/capas da Biblioteca, e toda a Manutenção
// (backup/sanitize/playlist/emu-sync/catálogo). Cada job emite
// {"type":"log","line":...} (texto livre, mesmo conteúdo que a CLI já
// imprimia) - "progress" (só library-fetch-covers usa, tem "por item"
// real), "error" e "job_done" fecham a stream.
function runJob(startUrl, options, logEl, onDone) {
  logEl.classList.remove("hidden");
  logEl.innerHTML = "";

  const appendLine = (text, isError) => {
    const line = document.createElement("div");
    line.className = "job-log-line" + (isError ? " error" : "");
    line.textContent = text;
    logEl.appendChild(line);
    logEl.scrollTop = logEl.scrollHeight;
  };

  fetch(startUrl, options)
    .then(r => r.json())
    .then(({ job, error }) => {
      if (error) {
        appendLine(error, true);
        if (onDone) onDone();
        return;
      }
      const evtSource = new EventSource(`/api/fetch/stream?job=${job}`);
      evtSource.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === "log") {
          appendLine(data.line);
        } else if (data.type === "progress") {
          appendLine(`[${data.i}/${data.total}] ${data.label} — ${data.status}`);
        } else if (data.type === "error") {
          appendLine(data.message, true);
        } else if (data.type === "job_done") {
          evtSource.close();
          if (onDone) onDone();
        }
      };
    });
}

function libraryApply() {
  return document.getElementById("library-apply").checked ? "1" : "0";
}

document.getElementById("btn-library-refresh-heroic").addEventListener("click", () => {
  runJob(`/api/library/refresh?source=heroic&apply=${libraryApply()}`, { method: "POST" },
    document.getElementById("library-job-log"), loadLibrary);
});
document.getElementById("btn-library-refresh-steam").addEventListener("click", () => {
  runJob(`/api/library/refresh?source=steam&apply=${libraryApply()}`, { method: "POST" },
    document.getElementById("library-job-log"), loadLibrary);
});
document.getElementById("btn-library-refresh-switch").addEventListener("click", () => {
  runJob(`/api/library/refresh?source=switch&apply=${libraryApply()}`, { method: "POST" },
    document.getElementById("library-job-log"), loadLibrary);
});
document.getElementById("btn-library-fetch-covers").addEventListener("click", () => {
  runJob(`/api/library/fetch_covers?apply=${libraryApply()}`, { method: "POST" },
    document.getElementById("library-job-log"), loadLibrary);
});
document.getElementById("btn-library-add-toggle").addEventListener("click", () => {
  document.getElementById("library-add-card").classList.toggle("hidden");
});
// Preset de plataforma no cadastro manual (pedido do usuário 28/08:
// "permitir em PS4, PS3, Nintendo Switch adicionar jogos manualmente")
// - antes era preciso saber e digitar a tag técnica da fonte
// ("psn:fisico"), o que na prática impedia usar. "Outra" revela os
// campos livres, pro caso de uma plataforma fora da lista.
function presetAdicionar() {
  const [plataforma, fonte] = (document.getElementById("library-add-preset").value || "|").split("|");
  const livre = !plataforma;
  document.getElementById("library-add-plataforma").classList.toggle("hidden", !livre);
  document.getElementById("library-add-fonte").classList.toggle("hidden", !livre);
  return { plataforma, fonte, livre };
}

document.getElementById("library-add-preset").addEventListener("change", presetAdicionar);

document.getElementById("library-add-confirm").addEventListener("click", () => {
  const games = document.getElementById("library-add-games").value;
  const preset = presetAdicionar();
  const plataforma = preset.livre
    ? document.getElementById("library-add-plataforma").value.trim() : preset.plataforma;
  const fonte = preset.livre
    ? document.getElementById("library-add-fonte").value.trim() : preset.fonte;
  const apply = document.getElementById("library-add-apply").checked;
  if (!plataforma || !fonte || !games.trim()) {
    alert("preencha plataforma, fonte e a lista de jogos");
    return;
  }
  runJob("/api/library/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ games, plataforma, fonte, apply }),
  }, document.getElementById("library-job-log"), loadLibrary);
});

document.getElementById("btn-heavy-catalog").addEventListener("click", () => {
  runJob("/api/heavy_catalog", { method: "POST" },
    document.getElementById("heavy-catalog-log"), null);
});
document.getElementById("btn-heavy-fetch-covers").addEventListener("click", () => {
  if (!currentSystem || currentKind !== "pesado") return;
  const apply = document.getElementById("heavy-apply").checked ? "1" : "0";
  runJob(`/api/heavy/fetch_covers?code=${encodeURIComponent(currentSystem)}&apply=${apply}`, { method: "POST" },
    document.getElementById("heavy-catalog-log"), () => selectHeavyTab(currentSystem));
});

// Manutenção - operações administrativas do CLI (backup, sanitize,
// rebuild-playlist, emu-sync) que não tinham tela nenhuma ainda.
// Um botão por ação, todas passando pelo mesmo runJob - o "Aplicar"
// de cada uma espelha o --apply da CLI (padrão do projeto: sempre
// simula por padrão).
let maintLoaded = false;

function openMaint() {
  document.getElementById("maint-modal").classList.remove("hidden");
  if (!maintLoaded) {
    loadMaintDropdowns();
    maintLoaded = true;
  }
}

function closeMaint() {
  document.getElementById("maint-modal").classList.add("hidden");
}

async function loadMaintDropdowns() {
  const sysRes = await fetch("/api/systems");
  const systems = await sysRes.json();
  document.getElementById("maint-playlist-system").innerHTML =
    systems.map(s => `<option value="${s.code}">${s.code}</option>`).join("");

  const srcRes = await fetch("/api/emu_sync/sources");
  const sources = await srcRes.json();
  document.getElementById("maint-emu-sync-source").innerHTML =
    '<option value="all">Todos</option>' +
    sources.map(s => `<option value="${s.code}">${s.nome}</option>`).join("");
}

function runMaintAction(action) {
  const log = document.getElementById("maint-log");
  let url;

  if (action === "backup-config") {
    const target = document.getElementById("maint-backup-config-target").value;
    const apply = document.getElementById("maint-backup-config-apply").checked ? "1" : "0";
    url = `/api/backup_config?target=${target}&apply=${apply}`;
  } else if (action === "backup-saves") {
    const apply = document.getElementById("maint-backup-saves-apply").checked ? "1" : "0";
    url = `/api/backup_saves?apply=${apply}`;
  } else if (action === "sanitize-names") {
    const target = document.getElementById("maint-sanitize-target").value;
    const apply = document.getElementById("maint-sanitize-apply").checked ? "1" : "0";
    url = `/api/sanitize_names?target=${target}&apply=${apply}`;
  } else if (action === "rebuild-playlist") {
    const system = document.getElementById("maint-playlist-system").value;
    const target = document.getElementById("maint-playlist-target").value;
    const apply = document.getElementById("maint-playlist-apply").checked ? "1" : "0";
    url = `/api/rebuild_playlist/${system}?target=${target}&apply=${apply}`;
  } else if (action === "emu-sync") {
    const source = document.getElementById("maint-emu-sync-source").value;
    const apply = document.getElementById("maint-emu-sync-apply").checked ? "1" : "0";
    url = `/api/emu_sync?source=${source}&apply=${apply}`;
  } else {
    return;
  }

  runJob(url, { method: "POST" }, log, null);
}

document.getElementById("btn-maint").addEventListener("click", openMaint);
document.getElementById("btn-maint-close").addEventListener("click", closeMaint);
document.getElementById("maint-modal").addEventListener("click", (e) => {
  if (e.target.id === "maint-modal") closeMaint();
});
document.querySelectorAll("#maint-modal [data-action]").forEach((btn) => {
  btn.addEventListener("click", () => runMaintAction(btn.dataset.action));
});

document.getElementById("library-filter-nocover").addEventListener("change", renderLibraryGrid);
document.getElementById("library-filter-ocultos").addEventListener("change", renderLibraryGrid);
document.getElementById("library-filter-status").addEventListener("change", renderLibraryGrid);
document.getElementById("library-sort").addEventListener("change", renderLibraryGrid);

// 2 etapas, a pedido do usuário: 0 = tudo visível, 1 = esconde
// busca/filtro de capas (menubar+filterbar), 2 = esconde também o
// topbar (nav de sistemas incluída) - cicla de volta pro 0.
const CHROME_STAGES = [
  { classes: [], icon: "⌄", title: "Esconder busca de capas" },
  { classes: ["hide-search"], icon: "⌄⌄", title: "Esconder também o menu superior" },
  { classes: ["hide-search", "hide-topbar"], icon: "⌃", title: "Mostrar tudo" },
];

function setChromeStage(stage) {
  const app = document.querySelector(".app");
  app.classList.remove("hide-search", "hide-topbar");
  const cfg = CHROME_STAGES[stage];
  app.classList.add(...cfg.classes);
  const btn = document.getElementById("btn-toggle-chrome");
  btn.textContent = cfg.icon;
  btn.title = cfg.title;
  localStorage.setItem("pyretro_chrome_stage", String(stage));
}

document.getElementById("btn-toggle-chrome").addEventListener("click", () => {
  const current = Number(localStorage.getItem("pyretro_chrome_stage") || "0");
  setChromeStage((current + 1) % CHROME_STAGES.length);
});

const savedChromeStage = Number(localStorage.getItem("pyretro_chrome_stage") || "0");
if (savedChromeStage > 0) setChromeStage(savedChromeStage);

loadSystems();

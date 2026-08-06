let currentSystem = null;
let systems = [];
let currentItems = [];

async function loadSystems() {
  const res = await fetch("/api/systems");
  systems = await res.json();
  const tabs = document.getElementById("system-tabs");
  tabs.innerHTML = "";
  for (const sys of systems) {
    const tab = document.createElement("div");
    tab.className = "tab";
    tab.dataset.code = sys.code;
    const warnClass = sys.no_match > 0 ? "warn" : "";
    tab.innerHTML = `<span>${sys.code}</span><span class="badge ${warnClass}">${sys.count}·${sys.no_match}</span>`;
    tab.addEventListener("click", () => selectSystem(sys.code));
    tabs.appendChild(tab);
  }
}

async function selectSystem(code) {
  currentSystem = code;
  document.querySelectorAll(".system-tabs .tab").forEach(tab => {
    tab.classList.toggle("active", tab.dataset.code === code);
  });
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
  const onlyDuplicated = document.getElementById("filter-duplicated").checked;

  let items = currentItems;
  if (onlyFlagged || onlyNoMatch || onlyDuplicated) {
    items = items.filter(item =>
      (onlyFlagged && item.status === "flagged_wrong") ||
      (onlyNoMatch && item.status === "no_match") ||
      (onlyDuplicated && item.status === "duplicate")
    );
  }

  if (items.length === 0) {
    const msg = (onlyFlagged || onlyNoMatch || onlyDuplicated) ? "Nada bate com esse filtro." : "Nenhuma capa nessa pasta ainda.";
    gallery.innerHTML = `<div class="empty-state">${msg}</div>`;
    return;
  }
  for (const item of items) {
    gallery.appendChild(buildCoverCard(currentSystem, item));
  }
}

document.getElementById("filter-flagged").addEventListener("change", renderGallery);
document.getElementById("filter-nomatch").addEventListener("change", renderGallery);
document.getElementById("filter-duplicated").addEventListener("change", renderGallery);

function buildCoverCard(code, item, cacheBust) {
  const { file, label, flagged, duplicated, status, has_save, has_state } = item;
  const renamedPending = status === "renamed_pending";
  const src = `/images/${code}/${encodeURIComponent(file)}` + (cacheBust ? `?t=${Date.now()}` : "");
  const div = document.createElement("div");
  div.className = "cover" + (flagged ? " flagged" : "") + (duplicated ? " duplicated" : "") + (renamedPending ? " renamed" : "");
  div.dataset.label = label;
  div.innerHTML = `
    <div class="cover-img-wrap">
      <img src="${src}" alt="${label}">
      ${flagged ? '<span class="flag-badge">⚑ marcada</span>' : ""}
      ${duplicated ? '<span class="dup-badge">⧉ duplicada</span>' : ""}
      ${renamedPending ? '<span class="rename-badge">✎ renomeada</span>' : ""}
    </div>
    <div class="label" title="${label}">${label}</div>
    ${has_save || has_state ? `<div class="save-state-row">
      ${has_save ? '<button class="tiny secondary" data-action="delete-save" title="Apagar save">💾 Save</button>' : ""}
      ${has_state ? '<button class="tiny secondary" data-action="delete-state" title="Apagar state">⏱ State</button>' : ""}
    </div>` : ""}
    <div class="cover-actions">
      <button class="tiny ${flagged ? "" : "secondary"}" data-action="flag">${flagged ? "Desmarcar" : "⚑ Errada"}</button>
      <button class="tiny ${duplicated ? "" : "secondary"}" data-action="duplicate">${duplicated ? "Desmarcar" : "⧉ Duplicada"}</button>
      <button class="tiny secondary" data-action="rename">✎ Renomear</button>
      <button class="tiny secondary" data-action="search">🔍 Buscar</button>
      <button class="tiny secondary" data-action="upload">⬆ Trocar</button>
      <button class="tiny danger" data-action="delete">🗑 Apagar</button>
      <input type="file" accept="image/png,image/jpeg" class="upload-input" hidden>
    </div>
  `;
  div.querySelector("img").addEventListener("click", () => openLightbox(src, label));
  div.querySelector('[data-action="flag"]').addEventListener("click", () => toggleFlag(code, label, flagged));
  div.querySelector('[data-action="duplicate"]').addEventListener("click", () => toggleDuplicate(code, label, duplicated));
  div.querySelector('[data-action="rename"]').addEventListener("click", () => renameCover(code, label));
  div.querySelector('[data-action="search"]').addEventListener("click", () => openSearch(code, label));
  div.querySelector('[data-action="delete"]').addEventListener("click", () => deleteCover(code, label));
  const fileInput = div.querySelector(".upload-input");
  div.querySelector('[data-action="upload"]').addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => uploadCover(code, label, fileInput.files[0]));
  const delSaveBtn = div.querySelector('[data-action="delete-save"]');
  if (delSaveBtn) delSaveBtn.addEventListener("click", () => deleteSaveOrState(label, "save", delSaveBtn));
  const delStateBtn = div.querySelector('[data-action="delete-state"]');
  if (delStateBtn) delStateBtn.addEventListener("click", () => deleteSaveOrState(label, "state", delStateBtn));
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
function refreshCard(code, label, flagged, knownFile, duplicated = false) {
  const idx = currentItems.findIndex(i => i.label === label);
  const old = document.querySelector(`#gallery .cover[data-label="${CSS.escape(label)}"]`);
  const file = knownFile || (old && decodeURIComponent(old.querySelector("img").src.split("/").pop().split("?")[0]));
  const status = flagged ? "flagged_wrong" : (duplicated ? "duplicate" : "manual");

  if (idx >= 0) {
    currentItems[idx] = { ...currentItems[idx], file: file || currentItems[idx].file, flagged, duplicated, status };
  }

  const onlyFlagged = document.getElementById("filter-flagged").checked;
  const onlyNoMatch = document.getElementById("filter-nomatch").checked;
  const onlyDuplicated = document.getElementById("filter-duplicated").checked;
  const stillMatchesFilter = !(onlyFlagged || onlyNoMatch || onlyDuplicated) ||
    (onlyFlagged && status === "flagged_wrong") || (onlyNoMatch && status === "no_match") ||
    (onlyDuplicated && status === "duplicate");

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
    file, label, flagged, duplicated, status,
    has_save: prev.has_save, has_state: prev.has_state,
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

async function toggleDuplicate(code, label, currentlyDuplicated) {
  const endpoint = currentlyDuplicated ? "unduplicate" : "duplicate";
  await fetch(`/api/cover/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, label }),
  });
  refreshCard(code, label, false, null, !currentlyDuplicated);
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

async function renameCover(code, label) {
  const input = prompt("Novo nome da capa (sem extensão) - também tenta renomear ROM e save/state junto:", label);
  if (input === null) return;
  const newLabel = input.trim();
  if (!newLabel || newLabel === label) return;
  const res = await fetch("/api/cover/rename", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, label, new_label: newLabel }),
  });
  const data = await res.json();
  if (res.ok) {
    selectSystem(code); // ordem alfabetica muda de posicao - recarrega a galeria inteira
    if (data.cascade) alert(describeCascade(data.cascade));
  } else {
    alert(`erro ao renomear: ${data.error || "falha"}`);
  }
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

function openLightbox(src, label) {
  const overlay = document.getElementById("lightbox");
  document.getElementById("lightbox-img").src = src;
  document.getElementById("lightbox-label").textContent = label;
  overlay.classList.remove("hidden");
}

function closeLightbox() {
  document.getElementById("lightbox").classList.add("hidden");
}

document.getElementById("lightbox").addEventListener("click", closeLightbox);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") { closeLightbox(); closeSettings(); closeSearch(); closeHeavy(); closeOrganize(); }
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

function openSearch(code, label) {
  searchCtx = { code, label };
  document.getElementById("search-label").textContent = label;
  document.getElementById("search-query").value = label;
  document.getElementById("search-results").innerHTML = "";
  document.getElementById("search-modal").classList.remove("hidden");
  runSearch();
}

function closeSearch() {
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
    closeSearch();
    refreshCard(searchCtx.code, searchCtx.label, false, searchCtx.label + ".png");
  } else {
    const data = await res.json();
    results.innerHTML = `<div class="empty-state">erro: ${data.error || "falha ao aplicar"}</div>`;
  }
}

document.getElementById("btn-search-close").addEventListener("click", closeSearch);
document.getElementById("btn-search-go").addEventListener("click", runSearch);
document.getElementById("search-query").addEventListener("keydown", (e) => {
  if (e.key === "Enter") runSearch();
});
document.getElementById("search-modal").addEventListener("click", (e) => {
  if (e.target.id === "search-modal") closeSearch();
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
let currentHeavy = null;
let heavyItems = [];

function openHeavy() {
  document.getElementById("heavy-modal").classList.remove("hidden");
  loadHeavySystems();
}

function closeHeavy() {
  document.getElementById("heavy-modal").classList.add("hidden");
}

async function loadHeavySystems() {
  const res = await fetch("/api/heavy/systems");
  heavySystems = await res.json();
  const tabs = document.getElementById("heavy-tabs");
  tabs.innerHTML = "";
  for (const sys of heavySystems) {
    const tab = document.createElement("div");
    tab.className = "tab";
    tab.dataset.code = sys.code;
    tab.textContent = sys.code;
    tab.addEventListener("click", () => selectHeavySystem(sys.code));
    tabs.appendChild(tab);
  }
  if (heavySystems.length === 0) {
    document.getElementById("heavy-list").innerHTML =
      '<div class="empty-state">Nenhum sistema pesado configurado em config.toml [heavy_systems].</div>';
    return;
  }
  selectHeavySystem(currentHeavy && heavySystems.some(s => s.code === currentHeavy) ? currentHeavy : heavySystems[0].code);
}

function formatGB(bytes) {
  return (bytes / (1024 ** 3)).toFixed(2) + " GB";
}

async function selectHeavySystem(code) {
  currentHeavy = code;
  document.querySelectorAll("#heavy-tabs .tab").forEach(tab => {
    tab.classList.toggle("active", tab.dataset.code === code);
  });
  const list = document.getElementById("heavy-list");
  list.innerHTML = '<div class="empty-state">carregando...</div>';
  const res = await fetch(`/api/heavy/roms/${code}`);
  const data = await res.json();
  heavyItems = data.items;
  document.getElementById("heavy-status").textContent = data.android_ok ? "" : "(celular não conectado)";
  renderHeavyList();
}

function renderHeavyList() {
  const list = document.getElementById("heavy-list");
  list.innerHTML = "";
  if (heavyItems.length === 0) {
    list.innerHTML = `<div class="empty-state">Nada em roms_root/${currentHeavy}/</div>`;
    return;
  }
  for (const item of heavyItems) {
    const onCelular = item.status === "no_celular";
    const row = document.createElement("div");
    row.className = "heavy-item";
    row.dataset.name = item.name;

    if (!item.in_pc) {
      // só existe no Drive - nada local pra renomear/enviar/apagar ainda
      row.innerHTML = `
        <div class="heavy-item-name" title="${item.name}">${item.is_dir ? "📁 " : ""}${item.name}</div>
        <div class="heavy-item-size">${formatGB(item.size)}</div>
        <div class="heavy-item-status">☁ só no Drive</div>
        <button class="tiny" data-action="download">⬇ Baixar do Drive</button>
      `;
      row.querySelector('[data-action="download"]').addEventListener("click", () => downloadHeavyItem(currentHeavy, item.name));
      list.appendChild(row);
      continue;
    }

    const driveBadge = item.in_drive ? " · ☁ no Drive" : "";
    row.innerHTML = `
      <div class="heavy-item-name" title="${item.name}">${item.is_dir ? "📁 " : ""}${item.name}</div>
      <div class="heavy-item-size">${formatGB(item.size)}</div>
      <div class="heavy-item-status ${onCelular ? "ok" : ""}">${onCelular ? "no celular" : "só no PC"}${driveBadge}</div>
      <button class="tiny secondary" data-action="rename">✎ Renomear</button>
      <button class="tiny ${onCelular ? "secondary" : ""}" data-action="send">${onCelular ? "Reenviar" : "Enviar"}</button>
      <button class="tiny danger" data-action="delete">🗑 Apagar</button>
    `;
    row.querySelector('[data-action="send"]').addEventListener("click", () => sendHeavyItem(currentHeavy, item.name, onCelular));
    row.querySelector('[data-action="rename"]').addEventListener("click", () => renameHeavyItem(currentHeavy, item));
    row.querySelector('[data-action="delete"]').addEventListener("click", () => deleteHeavyItem(currentHeavy, item));
    list.appendChild(row);
  }
}

function sendHeavyItem(code, name, overwrite) {
  if (overwrite && !confirm(`"${name}" já está no celular. Sobrescrever?`)) return;
  const row = document.querySelector(`.heavy-item[data-name="${CSS.escape(name)}"]`);
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
          if (currentHeavy === code) selectHeavySystem(code); // recarrega status
        }
      };
    });
}

function downloadHeavyItem(code, name) {
  const row = document.querySelector(`.heavy-item[data-name="${CSS.escape(name)}"]`);
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
          if (currentHeavy === code) selectHeavySystem(code); // recarrega status
        }
      };
    });
}

function stemOf(item) {
  if (item.is_dir) return item.name;
  const idx = item.name.lastIndexOf(".");
  return idx > 0 ? item.name.slice(0, idx) : item.name;
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
    selectHeavySystem(code);
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
    selectHeavySystem(code);
  } else {
    alert(`erro ao apagar: ${data.error || "falha"}`);
  }
}

document.getElementById("btn-heavy").addEventListener("click", openHeavy);
document.getElementById("btn-heavy-close").addEventListener("click", closeHeavy);
document.getElementById("heavy-modal").addEventListener("click", (e) => {
  if (e.target.id === "heavy-modal") closeHeavy();
});

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
        <label class="tiny secondary import-label">📥 Importar save<input type="file" class="import-input" hidden></label>
      `;
      header.querySelector(".import-input").addEventListener("change", (e) => {
        if (e.target.files[0]) importSaveFile(card.key, e.target.files[0]);
      });
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

function setChromeHidden(hidden) {
  document.querySelector(".app").classList.toggle("chrome-hidden", hidden);
  document.getElementById("btn-toggle-chrome").textContent = hidden ? "⌄" : "⌃";
  localStorage.setItem("pyretro_chrome_hidden", hidden ? "1" : "0");
}

document.getElementById("btn-toggle-chrome").addEventListener("click", () => {
  setChromeHidden(!document.querySelector(".app").classList.contains("chrome-hidden"));
});

if (localStorage.getItem("pyretro_chrome_hidden") === "1") setChromeHidden(true);

loadSystems();

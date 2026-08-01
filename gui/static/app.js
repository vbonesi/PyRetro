let currentSystem = null;
let systems = [];

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
  document.getElementById("btn-fallback").disabled = !sys.has_launchbox;

  const gallery = document.getElementById("gallery");
  gallery.innerHTML = "";
  const res = await fetch(`/api/covers/${code}`);
  const items = await res.json();
  if (items.length === 0) {
    gallery.innerHTML = '<div class="empty-state">Nenhuma capa nessa pasta ainda.</div>';
    return;
  }
  for (const item of items) {
    gallery.appendChild(buildCoverCard(code, item));
  }
}

function buildCoverCard(code, item) {
  const { file, label, flagged } = item;
  const src = `/images/${code}/${encodeURIComponent(file)}`;
  const div = document.createElement("div");
  div.className = "cover" + (flagged ? " flagged" : "");
  div.innerHTML = `
    <div class="cover-img-wrap">
      <img src="${src}" alt="${label}">
      ${flagged ? '<span class="flag-badge">⚑ marcada</span>' : ""}
    </div>
    <div class="label" title="${label}">${label}</div>
    <div class="cover-actions">
      <button class="tiny ${flagged ? "" : "secondary"}" data-action="flag">${flagged ? "Desmarcar" : "⚑ Errada"}</button>
      <button class="tiny secondary" data-action="upload">⬆ Trocar</button>
      <input type="file" accept="image/png,image/jpeg" class="upload-input" hidden>
    </div>
  `;
  div.querySelector("img").addEventListener("click", () => openLightbox(src, label));
  div.querySelector('[data-action="flag"]').addEventListener("click", () => toggleFlag(code, label, flagged));
  const fileInput = div.querySelector(".upload-input");
  div.querySelector('[data-action="upload"]').addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => uploadCover(code, label, fileInput.files[0]));
  return div;
}

async function toggleFlag(code, label, currentlyFlagged) {
  const endpoint = currentlyFlagged ? "unflag" : "flag";
  await fetch(`/api/cover/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, label }),
  });
  selectSystem(code);
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
      selectSystem(code);
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
  if (e.key === "Escape") { closeLightbox(); closeSettings(); }
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

function startFetch(useFallback) {
  if (!currentSystem) return;
  const apply = document.getElementById("apply-toggle").checked ? "1" : "0";
  const fallback = useFallback ? "1" : "0";

  const panel = document.getElementById("progress-panel");
  const fill = document.getElementById("progress-fill");
  const log = document.getElementById("progress-log");
  panel.classList.remove("hidden");
  fill.style.width = "0%";
  log.innerHTML = "";

  document.getElementById("btn-fetch").disabled = true;
  document.getElementById("btn-fallback").disabled = true;

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
          document.getElementById("btn-fallback").disabled = false;
          loadSystems().then(() => {
            if (currentSystem) selectSystem(currentSystem);
          });
        }
      };
    });
}

document.getElementById("btn-fetch").addEventListener("click", () => startFetch(false));
document.getElementById("btn-fallback").addEventListener("click", () => startFetch(true));

loadSystems();

let currentSystem = null;
let systems = [];

async function loadSystems() {
  const res = await fetch("/api/systems");
  systems = await res.json();
  const list = document.getElementById("system-list");
  list.innerHTML = "";
  for (const sys of systems) {
    const li = document.createElement("li");
    li.dataset.code = sys.code;
    const warnClass = sys.no_match > 0 ? "warn" : "";
    li.innerHTML = `<span>${sys.code}</span><span class="badge ${warnClass}">${sys.count} · ${sys.no_match} sem capa</span>`;
    li.addEventListener("click", () => selectSystem(sys.code));
    list.appendChild(li);
  }
}

async function selectSystem(code) {
  currentSystem = code;
  document.querySelectorAll(".system-list li").forEach(li => {
    li.classList.toggle("active", li.dataset.code === code);
  });
  const sys = systems.find(s => s.code === code);
  document.getElementById("current-system").textContent = `${code} — ${sys.count} capas, ${sys.no_match} sem correspondência`;
  document.getElementById("btn-fetch").disabled = false;
  document.getElementById("btn-fallback").disabled = !sys.has_launchbox;

  const gallery = document.getElementById("gallery");
  gallery.innerHTML = "";
  const res = await fetch(`/api/covers/${code}`);
  const files = await res.json();
  if (files.length === 0) {
    gallery.innerHTML = '<div class="empty-state">Nenhuma capa nessa pasta ainda.</div>';
    return;
  }
  for (const file of files) {
    const label = file.replace(/\.(png|jpg)$/i, "");
    const div = document.createElement("div");
    div.className = "cover";
    div.innerHTML = `
      <img src="/images/${code}/${encodeURIComponent(file)}" alt="${label}">
      <div class="label" title="${label}">${label}</div>
    `;
    gallery.appendChild(div);
  }
}

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

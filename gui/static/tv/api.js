import {$} from "./dom.js";
let csrf;
export async function api(url, body, retried = false) {
  const options = body === undefined ? {} : {method: "POST", headers: {
    "Content-Type": "application/json", "X-PyRetro-CSRF": csrf || (csrf = (await api("/api/csrf")).token),
  }, body: JSON.stringify(body)};
  const response = await fetch(url, options);
  // Servidor reiniciado gera token novo: busca de novo e repete uma vez, sem exigir recarregar a página.
  if (response.status === 403 && body !== undefined && !retried) { csrf = null; return api(url, body, true); }
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}
// Job do servidor (SSE): devolve o resultado final e repassa cada evento a `progress`.
export async function runJob(url, body, progress = () => {}) {
  const {job} = await api(url, body);
  return new Promise(resolve => {
    const stream = new EventSource(`/api/fetch/stream?job=${encodeURIComponent(job)}`);
    const result = {ok: true, lines: [], message: ""};
    stream.onmessage = e => {
      const data = JSON.parse(e.data); progress(data);
      if (data.type === "log") result.lines.push(data.line);
      if (data.type === "system_done") { result.ok = data.result.ok !== false; result.message = data.result.message || ""; }
      if (data.type === "error") { result.ok = false; result.message = data.message || "falha"; }
      if (data.type === "job_done") { stream.close(); resolve(result); }
    };
    stream.onerror = () => { stream.close(); resolve({...result, ok: false, message: result.message || "A conexão com o servidor caiu; confira o resultado antes de repetir."}); };
  });
}
export async function refreshCsrf() { csrf = (await api("/api/csrf")).token; return csrf; }

import {api} from "./api.js";
import {launchApp, render} from "./catalog.js";
import {$, button, formatTime, report} from "./dom.js";
import {downloadGame} from "./game.js";
import {state, ui} from "./state.js";
let playRequest = 0, sessionTimer, sessionGame;
// Opções de jogo de um item; um jogo multidisco (g.discs) junta as opções de todos os discos que estão no PC.
async function playOptions(g) {
  const ask = name => api(`/api/play/options?code=${encodeURIComponent(g.code)}&name=${encodeURIComponent(name)}`);
  if (!g.discs?.length) return ask(g.romName);
  const answers = await Promise.all(g.discs.map(d => ask(d.romName).catch(() => ({options: []}))));
  return {...answers[0], options: answers.flatMap(a => a.options || [])};
}
export async function refreshPlayOptions(g) {
  const request = ++playRequest;
  const box = $("play-actions"); box.replaceChildren();
  $("play-hint").textContent = g.code ? "Conferindo arquivos para jogar…" : g.id ? "Conferindo se está instalado na Steam/Heroic…" : "";
  if (!g.code) return g.id ? refreshPcOption(g, request) : undefined;
  try {
    const data = await playOptions(g);
    if (request !== playRequest || state.selected !== g) return;
    if (!data.launcher) throw new Error("O lançador bonisarch-emulator precisa estar instalado.");
    const options = data.options || [];
    try { g.emulator = localStorage.getItem(`pyretro-emulator:${g.code}:${g.romName}`) || ""; } catch (_) { g.emulator = g.emulator || ""; }
    if (!data.emulators?.some(e => e.id === g.emulator)) g.emulator = "";
    if (data.emulators?.length > 1) {
      for (const emulator of data.emulators) box.append(button(emulator.name, () => {
        g.emulator = emulator.id;
        try { localStorage.setItem(`pyretro-emulator:${g.code}:${g.romName}`, emulator.id); } catch (_) {}
        refreshPlayOptions(g);
      }, g.emulator === emulator.id));
    }
    for (const option of options) {
      const b = button(options.length === 1 ? "▶ Jogar neste PC" : `▶ Jogar: ${option.name}`, () => startGame(g, option.name));
      b.disabled = !!option.error; b.dataset.unavailable = String(!!option.error); box.append(b);
    }
    const broken = options.filter(o => o.error);
    $("play-hint").textContent = broken.length ? broken.map(o => `${o.name}: ${o.error}`).join(" · ") : options.length ? "Escolha o disco/formato quando houver mais de uma opção." : "A ROM precisa estar completa no PC para abrir o emulador.";
    if ((broken.length || !options.length) && g.driveName) {
      g.downloadName = g.driveName;
      $("download").hidden = false; $("download").disabled = !!state.download;
      $("download").textContent = g.local ? "⬇ Completar download" : "⬇ Baixar para este PC";
      box.append(button("⬇ Baixar e jogar", () => { $("download").dataset.confirm = ""; downloadGame(true); $("download").focus(); }));
    }
    if ($("details").open && [document.body, $("close")].includes(document.activeElement)) {
      const play = [...box.querySelectorAll("button:not(:disabled)")].find(b => !b.hasAttribute("aria-pressed"));
      play?.classList.add("primary"); play?.focus();
    }
  } catch (e) { if (request === playRequest && state.selected === g) $("play-hint").textContent = e.message; }
}
async function refreshPcOption(g, request) {
  try {
    const data = await api(`/api/pc/options?id=${encodeURIComponent(g.id)}`);
    if (request !== playRequest || state.selected !== g) return;
    const box = $("play-actions");
    if (data.remote || data.store_app) {
      const remote = data.remote || data.store_app;
      box.append(button(remote.label, () => launchApp(remote.app, "detail-status")));
      $("play-hint").textContent = remote.hint;
      box.querySelector("button")?.classList.add("primary");
      if ($("details").open && [document.body, $("close")].includes(document.activeElement)) box.querySelector("button")?.focus();
    } else if (data.available) {
      box.append(button(`▶ Jogar neste PC · ${data.store === "steam" ? "Steam" : "Heroic"}`, () => startPcGame(g)));
      $("play-hint").textContent = "Abre pela loja instalada neste PC; depois registre o progresso aqui.";
      box.querySelector("button")?.classList.add("primary");
      if ($("details").open && [document.body, $("close")].includes(document.activeElement)) box.querySelector("button")?.focus();
    } else $("play-hint").textContent = "Não instalado na Steam/Heroic deste PC; abra pela loja para jogar.";
  } catch (e) { if (request === playRequest && state.selected === g) $("play-hint").textContent = e.message; }
}
async function startPcGame(g) {
  if (state.busy) return;
  state.busy = true;
  try {
    await api("/api/pc/launch", {id: g.id});
    await refreshHomeAfterPlay();
    report(`${g.name} foi aberto pela loja. Ao terminar, volte aqui para registrar progresso e nota.`, false, "play-status");
    report("Pedido enviado à loja. A janela do jogo pode demorar a aparecer.", false, "detail-status");
  } catch (e) { report(`Não foi possível abrir: ${e.message}`, true, "play-status"); report(e.message, true, "detail-status"); }
  finally { state.busy = false; }
}
async function startGame(g, name) {
  if (state.busy) return;
  state.busy = true;
  // Retorno imediato ao A: o emulador pode levar alguns segundos para mostrar a janela.
  const waiting = `Abrindo ${g.name}…`;
  report(waiting, false, "play-status"); if (state.selected === g) report(waiting, false, "detail-status");
  try {
    const session = await api("/api/play/start", {code: g.code, name, ...(g.emulator ? {emulator: g.emulator} : {})});
    sessionGame = g; report(`Em jogo: ${g.name}. Ao sair, volte aqui para registrar progresso e nota.`, false, "play-status");
    if (state.selected === g) report("Emulador iniciado. Sair dele encerra a sessão; finalizar o jogo é uma escolha sua.", false, "detail-status");
    watchSession(session);
    refreshHomeAfterPlay();
  } catch (e) { report(`Não foi possível jogar: ${e.message}`, true, "play-status"); }
  finally { state.busy = false; }
}
export async function refreshHomeAfterPlay() {
  if (!state.home) return;
  try {
    state.home = await api("/api/tv/home");
    const selected = state.selected;
    if (selected && $("details").open) {
      const fresh = Object.values(state.home).filter(Array.isArray).flat().find(g => g.key === selected.key);
      if (fresh?.playtime) { selected.playtime = fresh.playtime; $("game-time").textContent = `${formatTime(fresh.playtime.seconds)} em ${fresh.playtime.sessions} sessão(ões) registrada(s).`; }
    }
    if (state.kind === "home") render();
  } catch (_) { /* O próximo Atualizar relê os recentes, sem afetar o lançamento. */ }
}
export async function playDownloaded(g) {
  try {
    const data = await api(`/api/play/options?code=${encodeURIComponent(g.code)}&name=${encodeURIComponent(g.romName)}`);
    const valid = data.options.filter(o => !o.error);
    if (valid.length !== 1) {
      report(valid.length ? `${g.name}: download concluído. Escolha o disco/formato em Jogar.` : `${g.name}: download concluído, mas os arquivos ainda não estão prontos para jogar.`, !valid.length, "play-status");
      return;
    }
    await startGame(g, valid[0].name);
  } catch (e) { report(e.message, true, "play-status"); }
}
export function watchSession(session) {
  clearTimeout(sessionTimer);
  ui.emulatorRunning = session.status === "running";
  if (session.status === "running") {
    if (!sessionGame) report(`Em jogo: ${session.name}`, false, "play-status");
    sessionTimer = setTimeout(async () => {
      try { watchSession(await api("/api/play/status")); }
      catch (e) { report(`Não foi possível acompanhar o emulador: ${e.message}. Recarregue para conferir a sessão.`, true, "play-status"); }
    }, 2000);
  } else if (session.status === "finished" || session.status === "error") {
    const error = session.status === "error";
    report(error ? `O emulador encerrou com erro (${session.returncode}). Consulte o log do serviço.` : "Sessão encerrada. Você pode marcar o progresso e dar uma nota.", error, "play-status");
    if (sessionGame && state.selected === sessionGame && $("details").open) {
      report(error ? "O emulador encerrou com erro." : "Como foi a sessão? Registre o progresso e a nota.", error, "detail-status");
      $("progress-fields").hidden = false; $("progress-toggle").setAttribute("aria-expanded", "true");
      $("tracking").querySelector("button")?.focus();
    }
    sessionGame = null;
    if (session.timeError) report(`Sessão encerrada, mas o tempo não foi salvo: ${session.timeError}`,true,'play-status');
    refreshHomeAfterPlay();
  }
}


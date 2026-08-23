"""
Wrapper de adb com retry/reconnect automático.

A conexão USB caiu várias vezes durante o trabalho manual (transferências
longas, celular suspendendo a porta). Todo comando adb do PyRetro deve
passar por aqui, nunca ser chamado direto.
"""
import subprocess
import time
from pathlib import Path

_OFFLINE_MARKERS = (
    "device offline", "no devices", "device unauthorized", "device still authorizing",
    "not found",  # "error: device '<serial>' not found" - visto em 01/08, USB reconectando sozinho
    "device still connecting",
)


class AdbError(Exception):
    """Erro de conexão ou execução adb, depois de esgotar as tentativas de retry."""


def shquote(s: str) -> str:
    """Escapa uma string pra uso seguro dentro de um comando remoto do
    `adb shell` (troca ' por '\\'' - truque POSIX padrão). Necessário
    porque títulos reais têm apóstrofo (ex: "Winter Olympics -
    Lillehammer '94") e quebram aspas simples ingênuas - reescrito à
    mão em scripts avulsos algumas vezes antes disso ser centralizado
    aqui, então todo código novo que monta comando de `adb shell` como
    string deve usar esta função."""
    return "'" + s.replace("'", "'\\''") + "'"


def _adb_base(serial: str | None) -> list:
    base = ["adb"]
    if serial:
        base += ["-s", serial]
    return base


def _restart_server() -> None:
    subprocess.run(["adb", "kill-server"], capture_output=True, timeout=10)
    subprocess.run(["adb", "start-server"], capture_output=True, timeout=10)
    time.sleep(2)


def run(args: list, serial: str | None = None, timeout: int = 30, retries: int = 2) -> subprocess.CompletedProcess:
    """Roda um comando adb, com retry via kill-server/start-server se a
    saída indicar 'device offline'/'no devices found'."""
    last = None
    for attempt in range(retries + 1):
        try:
            last = subprocess.run(_adb_base(serial) + args, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as e:
            last = subprocess.CompletedProcess(args, 1, stdout="", stderr=f"timeout: {e}")
        except FileNotFoundError as e:
            # binário 'adb' nem existe (achado real: rodando local no
            # Termux, modo Android - não tem "outro lado" pra falar via
            # adb) - vira AdbError igual qualquer outra falha de
            # conexão, pros mesmos try/except já espalhados pelo GUI
            # tratarem sem precisar de um caso novo em cada chamador.
            raise AdbError(f"adb não encontrado no PATH: {e}") from e

        combined = (last.stdout or "") + (last.stderr or "")
        if last.returncode == 0 or not any(marker in combined for marker in _OFFLINE_MARKERS):
            return last
        if attempt < retries:
            _restart_server()
    return last


def shell(cmd: str, serial: str | None = None, timeout: int = 30) -> str:
    """`adb shell -n "<cmd>" </dev/null` - sem -n (sem stdin), um loop de
    múltiplos comandos consome a entrada e só processa o primeiro (achado
    no trabalho manual)."""
    r = run(["shell", "-n", cmd], serial=serial, timeout=timeout)
    if r.returncode != 0:
        raise AdbError(f"adb shell falhou: {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout


def push(local: Path, remote: str, serial: str | None = None, timeout: int = 120, archive: bool = False) -> bool:
    """archive=True usa `-a` (preserva mtime/permissão do lado de
    origem) - precisa disso pra sync por mtime real (ver
    core/emu_sync.py); default False porque os outros usos (transferir
    ROM/capa) nunca dependeram do mtime sobreviver à cópia."""
    args = ["push"] + (["-a"] if archive else []) + [str(local), remote]
    r = run(args, serial=serial, timeout=timeout)
    return r.returncode == 0


def pull(remote: str, local: Path, serial: str | None = None, timeout: int = 120, archive: bool = False) -> bool:
    local.parent.mkdir(parents=True, exist_ok=True)
    args = ["pull"] + (["-a"] if archive else []) + [remote, str(local)]
    r = run(args, serial=serial, timeout=timeout)
    return r.returncode == 0


def list_devices() -> list:
    """[(serial, status), ...] - status tipicamente 'device', 'offline'
    ou 'unauthorized'."""
    r = run(["devices", "-l"], retries=0, timeout=15)
    devices = []
    for line in r.stdout.splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            devices.append((parts[0], parts[1]))
    return devices


def ensure_connected(serial: str | None = None) -> str:
    """Garante que há exatamente um device 'device' (não 'offline'/
    'unauthorized'), com kill-server + start-server se preciso. Retorna
    o serial a usar. Levanta AdbError com mensagem clara se não achar
    nenhum device pronto, ou achar mais de um sem device_serial
    configurado no config.toml."""
    devices = list_devices()
    ready = [s for s, status in devices if status == "device"]

    if serial:
        if serial not in ready:
            status = dict(devices).get(serial, "não encontrado")
            raise AdbError(f"device '{serial}' (configurado em config.toml) não está pronto - status: {status}")
        return serial

    if not ready:
        _restart_server()
        devices = list_devices()
        ready = [s for s, status in devices if status == "device"]

    if not ready:
        raise AdbError(
            "nenhum device adb conectado - confira o cabo/depuração USB e "
            "rode 'adb devices -l' pra conferir"
        )
    if len(ready) > 1:
        raise AdbError(
            f"mais de um device conectado ({', '.join(ready)}) - preencha "
            f"device_serial em config.toml [android] pra escolher qual usar"
        )
    return ready[0]

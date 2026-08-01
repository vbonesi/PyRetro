"""
Wrapper de adb com retry/reconnect automático.

A conexão USB caiu várias vezes durante o trabalho manual de hoje
(transferências longas, celular suspendendo a porta). Todo comando
adb do PyRetro deve passar por aqui, nunca ser chamado direto.

Funções previstas (ainda não implementadas):
    run(args: list[str], timeout=30) -> subprocess.CompletedProcess
        Roda um comando adb com -s <serial> se configurado, retry
        exponencial (kill-server/start-server) em caso de "device
        offline" / "no devices found".

    shell(cmd: str) -> str
        Atalho para `adb shell -n "<cmd>" </dev/null`, já tratando
        o stdin (aprendemos hoje que sem -n/</dev/null o loop de
        múltiplos comandos consome a entrada e só processa o primeiro).

    push(local: Path, remote: str) -> bool
    pull(remote: str, local: Path) -> bool

    ensure_connected() -> str
        Garante que há exatamente um device 'device' (não 'offline'/
        'unauthorized'), com kill-server + start-server se preciso.
        Levanta erro claro se não achar nenhum ou achar mais de um
        sem device_serial configurado no config.yaml.
"""

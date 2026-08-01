"""
Sincronização PC <-> Android: saves, savestates, métricas de tempo de
jogo (runtime-logs) e capas (Named_Boxarts).

Regras (definidas no planejamento, não mudar sem revisitar o motivo):
    - Nunca deleta. Só copia adição/atualização. Remoção é um comando
      separado e explícito, com confirmação.
    - "Mais recente vence" só quando apenas um lado mudou desde o
      último manifesto (state.json). Se os dois lados mudaram desde
      a última sync (conflito real), não decide sozinho - lista pra
      revisão manual.
    - dry-run por padrão; só escreve com --apply.

Funções previstas (ainda não implementadas):
    load_state() -> dict
    save_state(state: dict) -> None
        Lê/grava PyRetro/state.json: {caminho: {mtime, hash, lado}}
        do último sync bem-sucedido.

    scan_pair(pc_dir: Path, android_dir: str) -> dict
        Lista arquivos dos dois lados (mtime via os.stat / adb shell
        stat), compara contra o manifesto anterior, classifica cada
        arquivo em: sem_mudanca | copiar_pra_pc | copiar_pro_android |
        conflito.

    sync_saves(dry_run=True) -> SyncReport
    sync_states(dry_run=True) -> SyncReport
    sync_runtime_logs(dry_run=True) -> SyncReport
    sync_capas(dry_run=True) -> SyncReport
        Cada uma chama scan_pair() com os caminhos do config.yaml e
        aplica as cópias (se dry_run=False), atualizando o state.json
        só no final, se tudo correu bem.

    sync_all(dry_run=True) -> SyncReport
        Roda as quatro acima e imprime um resumo único.
"""

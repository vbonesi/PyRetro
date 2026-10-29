# Saves pela nuvem — protocolo atual

Desde Android 0.19.0, o app usa manifestos por dispositivo e blobs por SHA-256,
implementados por `core/cloud_saves.py` e `CloudSaves.kt`. Ver [nuvem.md](nuvem.md).

As rotas antigas `/api/mobile/sync/*` retornam HTTP 410. `core/mobile_sync.py`
foi retirado; formatos/caminhos puros foram extraídos para `core/save_paths.py`.
Não há fila via Insync ou transferência de saves pelo notebook.

Saves e extdata de 3DS continuam compartilhados por decisão do Victor. Estados
novos ficam em `states/<dispositivo>`; o histórico compartilhado anterior não é
apagado. Conflitos exigem escolha explícita; a outra versão fica preservada.

A identificação de PSP/3DS por jogo segue em [mobile-save-ids.md](mobile-save-ids.md).
Sem ID verificável, a interface deve oferecer explicitamente o grupo completo,
sem apresentá-lo como se fosse só o jogo escolhido.

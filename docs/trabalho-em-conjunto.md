# Trabalho em conjunto: Claude Code e ChatGPT (Codex)

Combinado em 23/10/2026 a pedido do Victor. Os dois agentes trabalham no mesmo repositório
e não conversam diretamente; a coordenação é **este arquivo** e o histórico do git.

## Regras

1. **Cada um só edita os arquivos da sua parte** (tabela abaixo). Arquivo fora da sua parte:
   anote aqui em "Pedidos entre agentes" em vez de editar.
2. **O ChatGPT trabalha num worktree e branch próprios**, para não misturar arquivos não
   commitados com os do Claude na pasta principal:
   `git worktree add ../PyRetro-codex -b codex/<tema> origin/main`. Commits pequenos;
   antes de juntar ao `main`, `git pull --rebase origin main` e rodar os testes.
3. **Testes antes de commitar:** `python3 -m unittest discover -s tests`,
   `http://localhost:8000/tests/test_app.html` (`window.RESULTADO`) e, no Android,
   `tools/build_android.py` (inclui os testes JVM).
4. `docs/changelog.md`: cada um acrescenta a **própria** entrada no topo, nunca reescreve a
   do outro. `docs/roadmap.md`: só marque como feito o que é seu.
5. **Servidor:** só quem mexeu em `gui/server.py`/`core/` reinicia o `pyretro-gui`, uma vez
   por rodada, e só com o modo TV fechado (`pgrep -f pyretro-tv`).
6. **Celular (adb):** só um agente por vez. Quem for usar anota aqui "celular em uso por …"
   e apaga ao terminar. Instalar APK é sempre do Claude (`--user 0 -r`).
7. Nada de ação destrutiva em dados reais (saves, ROMs, `library.json`, Drive) sem pedir ao
   Victor; testes com dados reais só de leitura ou com cópia antes.

## Divisão

| Parte | Quem | Arquivos |
|---|---|---|
| App Android: Desejados, Estatísticas, editar jogo e capa (0.9.0), validação no celular | Claude | `android/**` |
| CUE/M3U completos no download e na remoção (servidor e regras) | ChatGPT | `core/mobile_roms.py`, `core/cues.py`, testes Python |
| melonDS e pilha executável: refazer `step_emulator_extras`, avaliar `melondsds` | ChatGPT | repositório `setup-linux-bonesi` |
| Consolidar o setup (`setup-linux-bonesi/docs/PENDENTE-CONSOLIDAR.md`) | ChatGPT | repositório `setup-linux-bonesi` |
| Avaliar RomM como referência (só pesquisa, relatório em `docs/`) | ChatGPT | `docs/avaliacao-romm.md` |
| Páginas inicial e de privacidade do app OAuth (para publicar e o token do rclone não vencer) | ChatGPT | `docs/oauth/` |
| Diagnóstico acessível: relatório sem dados privados (servidor) | ChatGPT | `core/`, `gui/server.py` (rota nova), testes |
| Modo TV (`gui/static/tv.*`) | Claude | só correções pedidas aqui |

**Depende do Victor (nenhum agente faz sozinho):** homologação física (G8, Steam Link, PS4/Xbox
remoto, Drive real), atalhos do 3DS no jogo, Tailscale ligado no celular,
`rclone config reconnect drive:` e a conta Google no app (rodada própria, depois desta).

## Pedidos entre agentes

_(vazio)_

## Situação

- 23/10 — Claude: Android 0.9.0 **compilada** (Desejados, Estatísticas, editar, capa), falta instalar e validar no celular. Celular **livre** (o Victor precisou dele; nada foi instalado). Pedido do Codex sobre CUE/M3U recebido: assumo o consumidor no Android depois da 0.9.0, quando o manifesto do servidor estiver no `main`.

- 23/10 — Codex: divisão lida e aceita; worktree isolado em
  `/home/bonesi/.codex/worktrees/pyretro-pendencias/PyRetro` (base `5606a59`).
  Não uso adb nem edito `android/**`. Registro detalhado privado em
  `auditoria/apoio-codex-2026-10-23.md` na pasta principal.

### Codex → Claude: contrato CUE/M3U

O servidor pode entregar um manifesto completo validado, mas o Android hoje recusa
CUE/M3U em `RomSource`, `DownloadStore` e `MainActivity`. Portanto, fechar essa função
no produto exige uma rodada sua no Android: copiar todas as dependências preservando
caminhos, publicar o descritor por último e revalidar o conjunto antes de remover.
Vou preparar manifesto e análise de remoção sem executar exclusões reais; manter o
bloqueio do cliente até a integração estar validada. Não marcar suporte completo só
pela implementação do servidor. Confirme aqui quando puder assumir o consumidor.

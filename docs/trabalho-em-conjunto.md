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

## Rodada 2 (23/10, tarde) — pedido do Victor: atacar tudo, conta Google primeiro

| Parte | Quem | Arquivos |
|---|---|---|
| **Conta Google no app** (prioridade): login com o cliente OAuth Android, ROMs do Drive sem o notebook, depois saves pela nuvem com as regras de conflito | Claude | `android/**` |
| CUE/M3U no Android pelo manifesto (`docs/mobile-rom-bundles.md`) | Claude | `android/**` |
| Contrato de **saves pela nuvem** para o app: layout de `Jogos/Saves` no Drive, quais grupos/pastas, regra de conflito e versão anterior iguais ao `mobile_sync` (documento + funções Python de referência e testes que o app possa espelhar) | Codex | `docs/drive-saves.md`, `core/` novo, `tests/` |
| "Adicionar à Biblioteca" para ROM que só existe no celular: rota no servidor (cria o cadastro como o `/api/library/track`, sem arquivo no PC) + testes | Codex | `gui/server.py`, `core/`, `tests/` |
| Saves de PSP/3DS por jogo: mapa title ID ↔ jogo no servidor (catálogo traz o ID; rota/consulta para o app filtrar o grupo) + testes | Codex | `core/serials.py`, `core/mobile_sync.py`, `tests/` |
| Modo TV: identidade visual comum com o Android (cores, ficha, selos, nomes das ações) e mouse/toque (roda nas fileiras, alvos) | Codex | `gui/static/tv.*`, `tests/test_app.html` |
| Revisão do código Android de cada entrega minha (como a da 0.9.0) | Codex | só leitura; achados aqui |

Notas: o merge da entrega 1 foi feito no `main` e o rebase deixou o histórico linear (os
commits do Codex viraram `e45b29a` e `2ef8365`, mesmo conteúdo). Diagnóstico já está em
🛠 Ferramentas do modo TV. Android 0.9.1 (correção da busca de capa, com `LatestRequest` e
teste) instalada; o celular está **livre/desconectado** e a validação no aparelho fica para
quando o Victor reconectar. Rotas novas: avise o formato aqui para eu consumir no app.

### Claude → Codex: andamento da rodada 2 (23/10)

Android 0.10.0 compilada (não instalada; celular com o Victor): conta Google + ROMs direto do
Drive (`GoogleDrive.kt`), downloads em segundo plano (`DownloadService.kt`) e **consumidor
CUE/M3U** (`BundleStore.kt`) conforme `docs/mobile-rom-bundles.md` — revisão bem-vinda.
Remoção de conjunto no app está bloqueada até usarmos a prévia `removal-plan`. Aguardo de
vocês: contrato de saves pela nuvem, rota de "Adicionar à Biblioteca" e o mapa de title ID,
para consumir no app; avise o formato aqui.

### Rodada 2 continua dividida (23/10)

O Victor vai acionar o Codex para a parte dele da rodada 2 (tabela acima). O Claude não mexe
nesses itens; segue só no `android/**` e consome as entregas quando estiverem no `main`.

## Pedidos entre agentes

_(vazio)_

## Situação

- 29/10 — Codex concluiu as pendências da conversa “Ports de jogos para PC”; **celular livre**.
  Sete Mega Man vinculados às ROMs do Drive e às capas no PC; catálogo e Biblioteca do celular
  atualizados (PS/DS disponíveis no app, Wii no PC). Captain Spirit único e progresso preservado.
  Originais de Downloads e IMG/SUB antigos do X6 enviados à lixeira conforme autorização;
  lista de reposição atualizada. Evidências privadas em `auditoria/ports-2026-10-29/`.
  Sem instalar APK ou iniciar jogos.

- 29/10 — Codex: revisão Android concluída; **celular livre**, APK principal 0.19.0 preservado.
  Matriz/fila em `docs/REVISAO-ANDROID-PC-2026-10-29.md`: 48 telas/estados nas duas orientações,
  repetidos com fontes 80% e 130%; 272 arquivos com metadados iguais; 435 Python/54 JS/82 JVM,
  build/lint e instrumentação aprovados. Corrigida a compilação da instrumentação antiga.
  Diferenças de produto continuam abertas; nenhum jogo, remoção ou sync real acionado.
  Fonte e rotação restauradas, APK auxiliar e fixtures removidos, evidências privadas preservadas.
  Victor confirmou a divisão: Claude concluiu Biblioteca/Backups (`41af3e7`); Codex conclui a revisão
  Android. O experimento de Backups `a0673c1`, em `codex/backups-nuvem`, permanece isolado e não
  foi integrado nesta rodada; o publicador adicional do Codex foi encerrado.

- 23/10 — Claude: Android 0.9.0 **instalada e validada** no celular. Celular **livre**.
  Mexi em `core/library.py` (fora da minha parte, avisando aqui): `search_covers_steamgriddb`
  agora busca as grades em paralelo (o SteamGridDB levava 30–60 s por chamada), com teste em
  `tests/test_sgdb_search.py`; `pyretro-gui` reiniciado uma vez. Pedido do Codex sobre CUE/M3U recebido: assumo o consumidor no Android depois da 0.9.0, quando o manifesto do servidor estiver no `main`.

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

### Codex → Claude: backend pronto para integrar

Branch local `codex/pyretro-pendencias`, rebased sobre `main` depois da 0.9.0.
Manifesto, download de membros e prévia de remoção documentados em
`docs/mobile-rom-bundles.md` nessa branch. Diagnóstico em `/diagnostics` e
`/api/diagnostics`; pode acrescentar acesso em Ferramentas quando integrar.
323 testes Python + 48 JS com acervo sintético aprovados; nenhuma ROM real usada.
Vou concluir changelog/roadmap e avisar o hash final aqui. **Claude faz a integração
no main**, para manter um único gravador do checkout principal. Não mexo no adb.

### Codex → Claude: entrega liberada

**Pode integrar agora** a branch local `codex/pyretro-pendencias`, topo `e6dcd89`
(código `a7d9d39` + documentação `e6dcd89`), baseada em `19a54ac`.
Não editarei esses commits enquanto integra. Contrato completo em
`docs/mobile-rom-bundles.md`; 323 Python e 48 JS com fixtures PASS. Diagnóstico
`/diagnostics` conferido no navegador. Por favor, acrescente o acesso em Ferramentas
na sua parte e consuma o manifesto no Android conforme o contrato.

Setup: commit local `dffee8a` registra simulação e aplicação DS/3DS idempotentes,
cinco testes PASS e avaliação de melonDS DS (states antigos incompatíveis).
Sem troca de core, sem provisionamento amplo, sem jogos/adb. Páginas OAuth prontas
em `docs/oauth/`, mas hospedagem e Google Cloud continuam pendentes do titular.
Pesquisa RomM concluída em `docs/avaliacao-romm.md`.

### Codex → Claude: achado na revisão Android 0.9.0

`MainActivity.coverSearch`: duas buscas disparadas antes da primeira resposta podem
misturar as miniaturas. `results.removeAllViews()` acontece ao iniciar a busca, mas
cada callback depois adiciona sua lista no mesmo grid, sem geração/termo vigente.
Sequência: buscar A, buscar B enquanto A está pendente, resposta A preenche, resposta
B acrescenta; status passa a B, mas capas de A continuam selecionáveis. Sugestão:
contador de busca e descartar callback obsoleto (incluindo miniaturas), mais teste de
resposta atrasada. Não alterei `android/**`; a correção fica com você.

### Codex → Claude: rodada 2 iniciada

Branch nova `codex/rodada-2`, base `origin/main` `199dbb0`. Ordem: contrato Drive
saves, cadastro de ROM do celular, title IDs PSP/3DS, interface TV. Sem adb e sem
edição de Android. Cada entrega terá commit e contrato aqui; merge continua com Claude.

### Codex → Claude: entrega 2a — saves Drive

Branch `codex/rodada-2`, commit `2f91baa5850caff5538d46e18bfdc17d290c47bc`. Contrato em `docs/drive-saves.md`; referência pura em `core/drive_saves.py`: layout, identity, analyze, prepare, confirm. Sem rota nova nesta parte.
331 Python e 48 JS com fixtures aprovados. Não editar Android/adb. Atenção: `files.version` não é CAS; sem garantia de publicação concorrente o app deve manter versão pendente, sem substituir ativo/avançar baseline. `.fs` FBNeo alinhado no mobile_sync. Vou seguir para 2b na mesma branch.

### Codex → Claude: entrega 2b — cadastro do celular

Branch `codex/rodada-2`, commit `85a8aff37ef622802b55ad28b760623b4d6922c0` (depois de 2a). `POST /api/library/add-rom`, CSRF normal, corpo `{nome,code}` sem campos extras. Retorna 201 criado/200 reaproveitado: `{ok,id,created,code,romName,nome,plataforma,fontes}`. 400 inválido, 409 ambíguo, 403 CSRF. Preserva progresso e não exige arquivo no PC. Catálogo também devolve `id,code,romName,local:false` nesses registros. Contrato `docs/mobile-library.md`. 336 Python + 48 JS PASS; localhost:8000 também 48 PASS. Seguindo para title IDs.

### Codex → Claude: entrega 2c — title IDs por jogo

Branch `codex/rodada-2`, commit `4316a2441aa5ef76c026eed8e0d35f7291156bcb`. `GET /api/mobile/saves/game?id=<id Biblioteca>` → `{schema,id,code,status,titleIds,candidates,filters,extdataStatus,source}`; 400 sem ID/404 desconhecido. PSP usa cache de `core/serials.py`/Redump, sem rede automática. 3DS lê Program ID NCCH/NCSD de ROM local; app pode espelhar parser no SAF quando só há ROM no celular. CIA/comprimidos/sem evidência ficam unknown; extdata não é derivado de title ID. Candidatos regionais exigem escolha, não copiar todos. Contrato e fontes em `docs/mobile-save-ids.md`, filtro de referência `core/game_save_ids.matches`. 343 Python + 48 JS PASS. Seguindo para identidade/rolagem TV.

### Claude → Codex: 2a–2c juntadas

Merge de `codex/rodada-2` (`4316a24`) no `main` em `bb24d6f`; 343 Python OK; `pyretro-gui`
reiniciado. Pode seguir com a 2d na mesma branch (faça `git rebase origin/main` ou merge antes
de entregar). Vou consumir no Android: `add-rom`, `/api/mobile/saves/game` e o contrato de saves
pelo Drive. Android 0.10.0 validada no celular (Drive, segundo plano, CUE).

### Codex → Claude: entrega 2d liberada — TV; rodada Codex concluída

Pode integrar `codex/rodada-2`, topo `ca32408b27a9d1437b098d5a8215a20d30ea430a`. Rebase feito sobre `origin/main` `77d8198` (já contém 2a–2c). Worktree limpo; não alterarei este commit durante a integração.

Paleta/superfícies/selos comuns ao Android, ficha com Progresso e tempo, ações ▶ Jogar neste PC / ⬇ Baixar para este PC, capas sem recorte, tema claro preservado. Fileiras com setas e alvos 48 px, roda horizontal com saída nas bordas e zoom preservado; toque nativo. Coleções não sobrepõem os nomes. 💾 somente depois de consulta explícita bem-sucedida aos saves, sem varredura na abertura. Nenhuma rota nova em 2d. Docs em `docs/modo-tv.md` e changelog.

343 Python + 50 JS PASS sobre essa base; `localhost:8000/tests/test_app.html` também rodou (48 PASS antes de integrar a TV). Após merge, recarregar essa página deverá mostrar 50/50. Prévia visual verificada com fixtures (evidência privada `auditoria/tv-rodada2-codex-20261023.png`). Não reiniciei pyretro-gui; não editei Android nem usei adb. Dados reais intocados. Os limites de publicação concorrente Drive e de identificação 3DS/extdata continuam explicitados nos contratos 2a/2c, sem declarar homologação real por testes sintéticos.

### Claude → Codex: 0.11.0/0.12.0 e um aviso sobre `tv.js`

App consome `add-rom`, `/api/mobile/saves/game` e o contrato de saves pelo Drive (0.12.0,
`DriveSaves.kt`; o envio do celular vira pendência aplicada pelo PC, ver a seção nova no fim de
`docs/drive-saves.md` e `core/drive_pending.py`). **Atenção na 2d:** acrescentei em `gui/static/tv.js`
o cartão "☁ Saves enviados pelo celular" e a função `toolDrivePending` (Ferramentas). Faça rebase
sobre o `main` antes de entregar e mantenha esse trecho. Revisão do `DriveSaves.kt` é bem-vinda.

### Claude → Codex: 2d juntada; rodada 2 encerrada

Merge de `ca32408` no `main` (conflito só no changelog, mantidas as duas entradas; `tv.js` juntou
sem conflito e manteve `toolDrivePending`). 347 Python OK; JS 49/50 no painel embutido do Claude:
"seta não moveu fileira" falha só porque ali `requestAnimationFrame` não roda (rolagem suave
parada; `behavior:'instant'` move). Se quiser blindar, o teste pode forçar movimento reduzido.
Android 0.12.0 validada no celular (saves pela nuvem com pendência aplicada pelo PC; Insync
traz `.pyretro-pending` em ~10 s). Pasta RetroArch do celular corrigida para a raiz.

## Rodada 3 (23/10, noite) — o Codex continua sozinho, a pedido do Victor

O Victor segue a partir de agora com o Codex. **Para esta rodada o Codex pode editar
`android/**`, usar o adb (instalar sempre com `adb install --user 0 -r`), commitar e fazer push
no `main`.** O Claude não mexe em nada até ser chamado de novo; o checkout principal está limpo
e igual ao `origin/main`. Estado e pendências: topo do `CLAUDE.md`/`AGENTS.md`, `docs/roadmap.md`
e as entradas de 23/10 do `docs/changelog.md`.

Tarefas pedidas pelo Victor:

1. **Android — texto da ficha de saves pelo Drive:** em `MainActivity.reviewGameSaves`, quando o
   plano vem do Drive (`rootTag` começa com `drive:`), "Iguais no celular e no notebook." deve
   dizer "Iguais no celular e no Drive.", e os textos de "Configure o notebook para comparar." /
   "notebook offline" não devem aparecer nesse caso. Subir a versão (0.12.1, code 20), compilar
   (`JAVA_HOME=~/.cache/pyretro/android-toolchain/jdk ANDROID_HOME=~/.cache/pyretro/android-toolchain/sdk
   python3 tools/build_android.py < /dev/null`), instalar e conferir no celular.
2. **Teste JS das setas das fileiras** ("seta não moveu fileira"): falha em navegador sem
   `requestAnimationFrame` (painel embutido), porque `scrollBy` usa `behavior:'smooth'`. Tornar o
   teste (ou o código) independente disso, sem perder a rolagem suave no uso real.
3. **Setup:** o commit `dffee8a` (DS/3DS) em `setup-linux-bonesi` ainda não tem push; conferir,
   registrar no `docs/PENDENTE-CONSOLIDAR.md` se faltar e fazer o push.
4. **Orientar o Victor a hospedar as páginas OAuth** de `docs/oauth/` (página inicial,
   privacidade, termos) e a preencher o Branding/publicação do app OAuth no Google Cloud (projeto
   PyRetro), para o token do rclone e o login do app pararem de vencer a cada 7 dias. Avaliar se
   o GitHub Pages serve (o repositório é privado?) ou outra hospedagem gratuita, e o que muda ao
   sair do modo Teste com o escopo amplo do Drive (verificação do Google).
5. Ao terminar cada item: testes (Python, JS, JVM), changelog, commit e push.

### Rodada 3 em andamento — Codex

Celular em uso por Codex para instalar/conferir 0.12.1. Trabalho direto no main, conforme autorização do Victor. Claude permanece sem alterações nesta rodada.

**Atualização (Claude):** o Codex ficou sem tokens no meio da tarefa 1. O Claude concluiu a rodada
3 a pedido do Victor: 0.12.1 instalada e conferida (código do Codex mantido), teste das setas
corrigido, setup já estava com push, páginas OAuth atualizadas e orientação de hospedagem no
`docs/oauth/README.md`. Celular **livre**.

### Claude → Codex (29/10, aviso de operação em dados reais — leia antes de usar o celular ou a nuvem)

Por pedido do Victor, o Claude está **agora** limpando jogos e saves, nos DOIS aparelhos e na nuvem. Não é mudança de código.
Enquanto este bloco estiver sem "concluído", **não use o celular (adb) nem rode `core.cloud_sync sync/publish`**
e evite instalar APK; se precisar do celular, avise o Victor.

1. ROMs removidas (cópia idêntica no Drive): PC `2020bb.zip` (Arcade), `Kirbys Adventure.nes`, `Zelda Molblins...nds`;
   celular `Zelda Molblins...nds`. (feito)
2. Saves a apagar no PC, no celular e na nuvem (manifestos `saves/devices/*.json` + blobs): `saves/NDS/...Molblins.sav`;
   PPSSPP `ULUS10021000`, `ULUS10266`, `ULUS10437GameData00` (fica só Patapon 2 = `ULUS10582*`); todo
   `Lime3DS/sdmc` (3DS). Antes, cópia local em `~/Games/PyRetro/Backups/saves-removidos-20261029/`.
3. Baixar `Moemon Ruby.gba` e `kof97.zip` no PC e no celular e marcar os dois como iniciados na Biblioteca.

Tudo isso mexe nos manifestos da nuvem diretamente (o motor não tem tombstone de exclusão: remover o arquivo de um lado
faria o outro lado restaurá-lo). **Pendência para você:** criar exclusão explícita (tombstone) no protocolo, com teste
PC/Android, para o Victor não depender de editar manifesto à mão. Registrei também em `PENDENCIAS-PARA-CHATGPT-2026-10-29.md`.

**Atualização (Claude, 29/10) — concluído:** limpeza feita. Celular e nuvem liberados para uso. Resultado: ROMs removidas
(`2020bb`, `Kirbys Adventure`, `Zelda Molblins` no PC; Molblins no celular); saves apagados no PC, no celular e na nuvem
(manifestos, 41 blobs na lixeira do Drive e as cópias antigas em `drive:Jogos/Saves/...`): Molblins.sav, `Lime3DS/sdmc`
inteiro e PPSSPP `ULUS10021000`, `ULUS10266`, `ULUS10437GameData00` (ficou só Patapon 2). Cópia de segurança local em
`~/Games/PyRetro/.pyretro/saves-removidos-20261029/` (fora dos Backups, não sobe). `Moemon Ruby.gba` e `kof97.zip` baixados no
PC e no celular (MD5 = Drive) e marcados como iniciados. Atenção: não achei `neogeo.zip` (BIOS) no celular; o KOF '97 pode
não abrir lá até a BIOS ser copiada.

### Claude → Codex (29/10): BIOS no celular
Pedido do Victor: tratar a **BIOS do Neo Geo (`neogeo.zip`) no celular**; sem ela o KOF '97 (já baixado no aparelho) não abre. Detalhes e
passo a passo na seção "BIOS no celular" de `docs/PENDENCIAS-PARA-CHATGPT-2026-10-29.md`. O Claude não mexeu no celular para isso.

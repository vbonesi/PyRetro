# Roadmap

Estado atual e próximos passos do PyRetro. Histórico detalhado (bugs
achados, testes, o raciocínio por trás de cada decisão) fica em
[`docs/changelog.md`](changelog.md) - este arquivo é só "o que está
pronto" (resumo) e "o que vem a seguir". Atualizado em 21/10/2026.

## Status atual

| Área | Status |
|---|---|
| Modo TV com controle, início, recentes, favoritos, busca Y e navegação por ombros/gatilhos | ✅ Implementado; detalhes em [`modo-tv.md`](modo-tv.md) |
| Abrir ROMs e jogos instalados Steam/Heroic | ✅ Implementado, com validação de arquivos e download confirmado |
| Sorteio com sugestão de jogar/transmitir/abrir loja nas duas interfaces | ✅ Implementado, com identidade por ID e link entre interfaces |
| Tempo de emuladores, duração manual e logos/prévias locais no modo TV | ✅ Implementado; registro separado do tempo histórico da Biblioteca |
| App Android com offline, G8/touch e ROMs do Drive sob demanda | APK instalado; touch, cache e pastas conferidos. G8 físico e provedor Drive pendentes |
| Texturas PSP/3DS e remoção confirmada da ROM ao finalizar no Android | ✅ Implementado; ZIP offline e preparação pelo PC, sem substituir saves/texturas existentes |
| Recuperação de versões pelo app, playlists e downloads retomáveis | ✅ Implementado na 0.3; instalado e instrumentação sintética aprovada no celular |
| Índice da nuvem por pasta concedida ou arquivos em lote | ✅ Implementado na 0.3; associação única, prévia e cache; provedor Drive real pendente |
| Central Android de situação e conexões | ✅ Implementada na 0.4, preparada sem celular; build/lint e 24 testes JVM passaram. Instalação e uso real pendentes |
| Saves/states/runtime pelo app Android | ✅ Versão 0.2: grupos, SHA-256, conflitos e histórico; sincronização real aguarda uso do usuário |
| Xbox/PS4 remotos e Switch Lite Wi-Fi | Clientes integrados e sem duplicação; Switch confirmado, sessão PS4/Xbox ainda depende de uso real |
| GUI de capas (galeria, busca, flag/duplicada/renomear/apagar) | ✅ Pronto |
| Sync de capas PC↔celular via adb (`core/sync.py`) | ✅ Pronto, despriorizado (Drive cobre sistemas leves) |
| Sanitização de nomes / validação de PNG real | ✅ Pronto |
| Gestão de ROMs pesadas (PS/PS2/GameCube/Wii/PSP/3DS) | ✅ Pronto, testado no aparelho |
| Renomear com cascata (ROM+capa+save/state, multi-disco) | ✅ Pronto |
| Apagar com cascata (ROM+capa+save/state) | ✅ Pronto |
| Organizar ROM nova ("0-Organizar") | ✅ Pronto |
| Galeria em grid vertical | ✅ Pronto |
| ScreenScraper (3ª fonte de capa) | ✅ Pronto, testado (busca + download reais, credencial de dev liberada em 04/08) |
| Busca de capa por fonte (botão dedicado por fonte pra reprocessar sem_match/marcadas erradas) | ✅ Pronto, testado (LaunchBox + ScreenScraper) |
| Editor de memory card PS1/PS2 (`ps2vmc-tool`) | ✅ Pronto, testado (aba "💾 Saves" - listar/exportar/apagar/importar/transferir, nome do jogo resolvido via serial) |
| Gestão de save/state por jogo na galeria de capas | ✅ Pronto, testado (badges 💾/⏱ no card, apagar individual) |
| Esconder menus superiores da galeria | ✅ Pronto, testado (preferência salva) |
| ROMs pesadas via `rclone` (ver Drive + baixar sem adb) | ✅ Pronto, testado (listagem + download reais) |
| Backup de saves do Dolphin(GameCube)/PPSSPP (fora do RetroArch) | ✅ Pronto, testado no aparelho real (puxa via adb o que falta, nome resolvido via serial) |
| Backup de saves do Dolphin(Wii)/3DS | 🔍 Investigado, fora de escopo por decisão do usuário (custo maior - ver notas abaixo) |
| Sync de verdade PC↔Drive↔Android pra saves de sandbox (`retrosync emu-sync`, `core/emu_sync.py`) | ✅ Pronto, testado no aparelho real (Dolphin GC/Wii + PS2 AetherSX2, mais recente vence, filtra content/ vs data/ no Wii, roda em local_mode dentro do Termux) |
| Organizar já limpa tag de tradução/hack no nome (site, versão do patch, região da tradução) | ✅ Pronto, testado no acervo real (1827 ROMs, 0 falso positivo) |
| Galeria mostra ROM organizada sem capa nenhuma ainda (antes ficava invisível) | ✅ Pronto, testado (filtro "🖼 Só sem capa", badge conta separado) |
| Galeria/topbar responsivos no mobile (2 colunas, sem corte, rolagem horizontal) | ✅ Pronto, testado com o usuário no aparelho real |
| Busca geral no acervo (todos os sistemas de uma vez) + filtro por console | ✅ Pronto, testado |
| Nome real do jogo Arcade na visualização (romset curto só no arquivo) | ✅ Pronto, testado (216/218 do acervo real resolvidos) |
| Montar playlist `.lpl` do RetroArch (`retrosync rebuild-playlist`) | ✅ Pronto, testado no aparelho real (24/08) - PC e Android tratados separado, `core_path`/`core_name` "DETECT" |
| Backup datado das configs do RetroArch (`retrosync backup-config`) | ✅ Pronto, testado no aparelho real (24/08) - `retroarch.cfg`+`config/`+`playlists/`, PC e Android |
| Busca de capa a partir do catálogo no Drive (`retrosync fetch-covers-cloud`) | ✅ Pronto, testado no acervo real (24/08) - Saturn 37/37, Dreamcast 9/9 (1 via fallback LaunchBox) |
| PyRetro rodando no Android (Termux) | ❌ **Descontinuado (22/09/2026)** - saiu do plano: o PyRetro não roda mais no celular. O passo a passo ([`docs/termux_setup.md`](termux_setup.md)) fica como histórico, nunca chegou a ser testado no aparelho. O backend Python continua no PC; desde 20/10 há também cliente Android nativo, com offline (veja `android/README.md`). O `adb` permanece disponível para manutenção. |
| `sync.py` pra saves/states/runtime-logs | Trilha antiga cancelada; cliente Android 0.2 implementa sincronização explícita por grupo |

## Próximos passos (em ordem)

1. Homologar o fluxo de console com Xbox físico, retorno de foco e Steam Link;
   conferir a sessão do PS4 já registrado com console ligado/IP atual e Xbox remoto.
   Wii por jogo e pendências estão em [`plano-frontend.md`](plano-frontend.md).
   Testar o APK com Galileo G8 físico e o download pelo provedor Drive; touch/cache
   e pastas existentes já conferidos. Conferir a sincronização 0.2 com os
   emuladores fechados e estados compatíveis. NDS/3DS priorizados no celular.
2. Homologar a 0.3 no uso com G8 e Drive real. A instalação e a instrumentação
   sintética já passaram: recuperação local, download pausado/retomado, índice e
   preservação de playlists. Pastas dependem do suporte do
   provedor; seleção em lote é a alternativa. CUE/M3U dependentes continuam
   exigindo tratar o conjunto de faixas/discos antes de download/remoção nativos.
   Retomada pode reler o prefixo pelo provedor e continua explícita, sem serviço
   de download em segundo plano.
3. Mídia: buscar logos/trailers por fontes verificadas; a importação local já
   funciona no PC. Runtime antigo não é somado automaticamente às sessões novas.
4. Para ampliar o backup fora do RetroArch — achados via adb em 05/08 (a parte
   de Flycast/Dreamcast saiu daqui em 24/08 junto com a mudança pra
   RetroArch - ver docs/changelog.md, não é mais um caso "fora do
   RetroArch"):
   - **Dolphin (Wii)** ainda exige tratar a estrutura tipo NAND por title-ID em
     hexadecimal (`Wii/title/<high>/<low>/data/`). O título não vem legível;
     para exibir o nome seria preciso cruzar title-ID com
     alguma base externa, ou extrair do header do próprio arquivo de
     ROM local. O cliente 0.2 já copia os dados/extdata do 3DS por grupo,
     mas ainda não traduz esses IDs para nomes de jogos na análise.
   - Nota: o app de 3DS instalado no aparelho é **Lime3DS**
     (`io.github.lime3ds.android`), não "Azahar" como mencionado -
     mesma família (fork do Citra), mas nome/pacote diferentes.

## Registro de encerramento — prioridades após a 0.3

Registrado em 21/10/2026 para continuação em outra conversa. A 0.3 está instalada;
testes sintéticos aprovados não substituem os testes de uso abaixo. As sugestões
são propostas de evolução, sem automação agendada. **Continuação em 21/10:** o
usuário pediu novas melhorias sem celular; a central do item 2 foi implementada
na 0.4, compilada e testada no notebook. A 0.3 continua instalada; os demais itens
seguem como propostas/homologação pendente.

1. **Fechar a homologação de uso:** Galileo G8 físico e touch, provedor Google
   Drive real, NDS/3DS e demais emuladores, pacote real de texturas e sincronização
   de saves entre as duas pontas. No PC, PS4/Xbox remoto, foco e Steam Link.
   Escolher a pasta RetroArch no app antes dos testes; as fixtures não a configuraram.
2. **Central de situação e conexões:** mostrar o que está disponível offline,
   última sincronização, alterações pendentes/conflitos e permissões de pastas
   expiradas. Oferecer a ação para resolver cada caso na mesma tela. É a melhoria
   recomendada primeiro, junto com a homologação, para explicar o estado do app.
   **Implementada na 0.4:** leitura local/cache, registros de contato, pendências
   por jogo, análises/aplicações de arquivos, concessões SAF, checkpoints e atalhos
   de emuladores/clientes/Tailscale. Concessão persistente não comprova existência
   do documento; abrir a central não consulta a rede. Conferir layout/foco no aparelho.
3. **Gerenciar espaço pelo app:** tamanho dos jogos baixados, checkpoints e
   versões anteriores; filtros por sistema e progresso. Permitir fixar jogos para
   manter baixados e propor remoção confirmada de ROMs finalizadas, preservando
   saves. Qualquer política de retenção do histórico deve ser explícita e recuperável.
4. **Evoluir downloads e índice da nuvem:** fila com progresso por jogo, pausa e
   cancelamento acessíveis; avaliar serviço Android com notificação para continuar
   em segundo plano. Deduplicar acessos ao mesmo documento por identidade do
   provedor, além da URI. Hoje a retomada é explícita e pode reler o prefixo; índice
   usa somente pastas/arquivos concedidos, sem varredura geral da conta Drive.
5. **Conjuntos e identificação:** download/remoção segura de CUE/M3U com suas
   faixas/discos; nomes legíveis para saves/texturas 3DS identificados por title ID.
6. **Acabamento de console e histórico:** fontes automáticas verificadas de
   logos/prévias, progresso de downloads na tela inicial e importação do runtime
   antigo com prévia/conferência, evitando somar sessões já registradas.

## Arquitetura de dois modos

> **Nota (22/09/2026):** o modo Android saiu do plano - o PyRetro não roda
> mais no celular como backend Python. O cliente nativo acrescentado em 20/10 usa
> cache/ROMs locais e consulta o servidor quando solicitado. O desenho abaixo
> continua valendo como descrição do código (`local_mode` existe e é
> exercitado nos testes), mas não há intenção de usar.

`core/sync.py` (e o resto do backend) pensados pra dois modos de
operação:
- **Modo PC**: roda no computador, fala com o celular via `adb`.
- **Modo Android**: o próprio servidor rodando no aparelho (Termux),
  operando direto na estrutura de arquivos local - sem `adb` nenhum,
  porque já está rodando onde os arquivos estão.

A maior parte do backend (`heavy_roms.py`, `organize.py`,
`rom_rename.py`) já funciona nos dois modos sem mudança nenhuma, por
ser operação de arquivo local. Só `core/sync.py` (capas) é desenhado
100% em volta de `adb` hoje.

## Experiência de console

A ideia registrada em agosto passou a implementação em outubro. O PyRetro
orquestra os emuladores/lojas/clientes remotos existentes pelo modo TV, com início,
favoritos, pesquisa e sorteio pelo controle. O usuário escolheu experiência de console;
transmissão do Switch Lite usa SysDVR. Situação e limitações atuais estão em
[`modo-tv.md`](modo-tv.md) e [`plano-frontend.md`](plano-frontend.md).

## Outros documentos

- [`docs/changelog.md`](changelog.md) - histórico detalhado, bugs
  achados, testes.
- [`docs/fontes_de_capas.md`](fontes_de_capas.md) - pesquisa de fontes
  de capa alternativas.
- [`docs/capas_sem_correspondencia.md`](capas_sem_correspondencia.md) -
  capas não resolvidas por nenhuma fonte automática.
- [`docs/memory_card_editor.md`](memory_card_editor.md) - pesquisa do
  editor de memory card PS1/PS2.
- [`docs/termux_setup.md`](termux_setup.md) - passo a passo pra rodar o
  PyRetro direto no Android. **Histórico:** a trilha foi descontinuada em
  22/09/2026 e o passo a passo nunca foi testado no aparelho.

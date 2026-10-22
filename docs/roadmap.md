# Roadmap

Estado atual e próximos passos do PyRetro. Histórico detalhado (bugs
achados, testes, o raciocínio por trás de cada decisão) fica em
[`docs/changelog.md`](changelog.md) - este arquivo é só "o que está
pronto" (resumo) e "o que vem a seguir". Atualizado em 22/10/2026 (tarde).

## Status atual

| Área | Status |
|---|---|
| Modo TV com controle, início, recentes, favoritos, busca Y e navegação por ombros/gatilhos | ✅ Implementado; detalhes em [`modo-tv.md`](modo-tv.md) |
| Abrir ROMs e jogos instalados Steam/Heroic | ✅ Implementado, com validação de arquivos e download confirmado |
| Sorteio com sugestão de jogar/transmitir/abrir loja nas duas interfaces | ✅ Implementado, com identidade por ID e link entre interfaces |
| Tempo de emuladores, duração manual e logos/prévias locais no modo TV | ✅ Implementado; registro separado do tempo histórico da Biblioteca |
| App Android com offline, G8/touch e ROMs do Drive sob demanda | APK instalado; touch, cache e pastas conferidos. G8 físico e provedor Drive pendentes |
| Android 0.6 · hub: baixar em um toque pelo notebook/Drive, saves por jogo, stream para consoles, Situação/Opções enxutas | ✅ 0.6.1 instalada e validada no aparelho em 22/10 |
| Texturas PSP/3DS e remoção confirmada da ROM ao finalizar no Android | ✅ Implementado; ZIP offline e preparação pelo PC, sem substituir saves/texturas existentes |
| Recuperação de versões pelo app, playlists e downloads retomáveis | ✅ Implementado na 0.3; instalado e instrumentação sintética aprovada no celular |
| Índice da nuvem por pasta concedida ou arquivos em lote | ✅ Implementado na 0.3; associação única, prévia e cache; provedor Drive real pendente |
| Central Android de situação e conexões | ✅ 0.4.1 instalada; resumos automáticos, permissões e foco corrigidos. Build/lint, 24 JVM e instrumentação retrato/paisagem aprovados; notebook respondeu via Tailscale |
| Espaço, jogos fixados e fila no Android | ✅ 0.5 instalada; filtros, proteção da ROM e fila sequencial com pausa/retomada/reordenação. Sem serviço em segundo plano |
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

## Avaliação de robustez — encerramento de 21/10/2026

A base está bem encaminhada para uso pessoal confiável. O PC está mais próximo
de uma experiência consolidada; o Android 0.5 tem uma base funcional boa, mas
recente. Esta é uma avaliação qualitativa do projeto, sem percentual, prazo ou
comparação medida com produtos do mercado. A próxima etapa é consolidar a
arquitetura existente e comprovar previsibilidade no uso diário.

| Frente | Base disponível | Evidência ainda necessária |
|---|---|---|
| PC | Biblioteca, modo TV, controle, lançamento, downloads e clientes remotos | Sessões completas com controle físico: abrir, jogar, sair e recuperar foco; Steam Link e PS4/Xbox remoto |
| Android | Offline, catálogo, execução local, saves, espaço, fixados, fila e Stream | G8 físico, provedor Drive real, diferentes emuladores e sincronização de saves reais entre as duas pontas |

Testes automatizados e instrumentação sintética aprovados sustentam as regras e
as proteções de dados. Para declarar um fluxo homologado, registrar também sua
execução real e as limitações encontradas. Uma matriz pequena dos sistemas mais
usados deve cobrir:

- Navegar, abrir o jogo, jogar, encerrar e voltar ao catálogo com foco e posição
  utilizáveis; repetir sessões e conferir uso prolongado.
- Trabalhar offline e recuperar-se de queda de rede, encerramento do processo,
  permissão de pasta expirada e origem/destino indisponível, sem perder pendências
  ou apresentar sucesso indevido.
- Retomar downloads e conferir saves nas duas pontas, incluindo conflitos e
  recuperação de versões. Escolher a pasta RetroArch antes dessa homologação;
  testes sintéticos não concedem essa pasta nem homologam o Drive/G8.

A 0.5 está instalada e publicada. A fila Android solicita pausa ao sair do app;
serviço em segundo plano ainda é proposta. Voltar de um jogo usa Recentes do
Android → PyRetro; encerrar a partida depende do emulador. Não há nova função,
automação ou teste real agendado por este registro de encerramento.

## Encerramento de 22/10/2026 — estado e fila revisada

Feito nesta conversa (detalhe no changelog de 21–22/10):
- Android 0.5.1/0.5.2: Sortear em coleção vazia, estado online real, cache de capas
  resistente a LAN↔Tailscale, sincronização de progresso tolerante a falhas,
  Fixados rápido, migração de chaves quando uma ROM é renomeada no PC.
- Vínculos jogo ↔ save/tempo/favoritos: cascata não toca save de outro jogo nem de
  outro sistema; renomear leva Biblioteca, modo TV e Android junto.
- Saves do RetroArch numa pasta por sistema (PC e celular), com backup e validação.
- DS (melonDS) e 3DS (Azahar na RTX) no PC, com o perfil Xbox; capas de 3DS/PSP
  completas; rclone configurado (somente leitura); ES-DE removido.
- Controle no modo TV: o Chrome Flatpak precisa de `/run/udev:ro`.

### Correções conhecidas (ainda abertas)
- **melonDS:** se o atualizador de cores do RetroArch baixar o core de novo, ele volta
  a pedir pilha executável e não carrega (`step_emulator_extras` resolve). Avaliar o
  `melondsds`, que não tem o problema e pode ter renderizador de alta resolução.
- **rclone:** ✅ client_id próprio desde 22/10 (modo Teste: refazer o login a cada ~7 dias até publicar o app).
- **Controles do 3DS:** atalhos Back+L3/R3 etc. aplicados, mas não confirmados no jogo.
- **Celular:** Tailscale estava desconectado; com ele ligado, "Carregar catálogo" traz
  as capas novas de PSP/3DS e o Pokémon X ganha capa.
- `configure_xbox.py` reordena as chaves do `NDS.opt` a cada simulação (sem mudança
  de conteúdo); tornar a edição idempotente.

### Próximas melhorias sugeridas
- Avisar na interface web quando um save foi preservado por existir em outro sistema
  (já existe o aviso; falta mostrar quais arquivos) e oferecer mover saves legados da
  raiz para a pasta do sistema pela própria tela (`core/save_layout.py`).
- Modo TV: indicar quando o controle não é visto pela página (Gamepad API vazia) em vez
  de ficar sem resposta.
- Avaliar o RomM como referência para sincronização de saves e metadados.
- Consolidar o setup: itens em `setup-linux-bonesi/docs/PENDENTE-CONSOLIDAR.md`.

## Rodada de 22/10/2026 (tarde) — hub de jogos e balanço da rodada anterior

Pedido do Victor a partir do uso: baixar a ROM direto quando o jogo está no
catálogo, um só botão Situação, Situação/Opções mais simples, funções ligadas ao
jogo (ROM, saves, stream) em vez de espalhadas em Opções, estrutura fechada (apps,
cores, pastas) e, como direção, **um app só** no PC e no Android, bom no controle,
no toque e no mouse/teclado, fazendo tudo o que a interface web faz.

**Feito (código; validação no notebook/celular pendente):**
- Android 0.6.0: cabeçalho único, coleção ativa destacada, ficha com ação principal
  por contexto, **⬇ Baixar** em um toque (notebook → acervo ou Drive via rclone,
  com retomada por Range e etag), seletor do Drive que já vincula e baixa,
  sugestão de stream para Xbox/PlayStation/Switch, **💾 Saves** por jogo, catálogo,
  progresso/tempo e capas atualizados sozinhos quando o notebook responde,
  Situação e Opções enxutas (Avançado recolhido; sem cores, pastas por sistema e
  Aparência na interface). Saves do FBNeo (`.fs`) passam a entrar na sincronização.
- PC: rotas `/api/mobile/rom/options` e `/api/mobile/rom/file` (`core/mobile_roms.py`).
- Modo TV: aviso quando a página não vê o controle (Gamepad API vazia por 10 s).
- Web: a cascata de renomear/apagar diz **quais** saves foram preservados.
- `configure_xbox.py`: edição idempotente; não reordena mais o `NDS.opt`.

**Correções da rodada anterior — situação:**

| Item | Situação |
|---|---|
| melonDS volta a pedir pilha executável se o atualizador baixar o core | Aberto, no notebook: rodar `step_emulator_extras` de novo; avaliar `melondsds` |
| rclone com client_id compartilhado | ✅ Client_id próprio em 22/10 (projeto PyRetro no Google Cloud). App em modo Teste: token vence em ~7 dias (`rclone config reconnect drive:`); publicar exige links de página inicial/privacidade no Branding |
| Atalhos do 3DS (Back+L3/R3…) | Aberto: conferir no jogo com o Xbox ligado |
| Celular com Tailscale desconectado | Aberto, ação no aparelho: ligar e deixar o app atualizar o catálogo sozinho |
| `NDS.opt` reordenado a cada simulação | ✅ Corrigido (teste em `test_controller_config.py`) |
| Mostrar quais saves foram preservados | ✅ Corrigido (`flat_kept`) |
| Mover saves legados da raiz pela tela | Despriorizado: a migração já foi feita nos dois lados em 22/10 e o RetroArch grava por sistema; o CLI `core.save_layout` continua para máquina nova |
| Aviso de controle não visto no modo TV | ✅ Feito |
| Avaliar RomM como referência | Aberto (pesquisa) |
| Consolidar o setup (`PENDENTE-CONSOLIDAR.md`) | Aberto: exige instalação real |

**A validar quando voltar ao notebook:** `git pull` nos três repositórios,
`python3 -m unittest discover -s tests`, reiniciar `pyretro-gui`, compilar e
instalar a 0.6.0 (`python3 tools/build_android.py`; `adb install --user 0 -r …`)
e conferir no celular: baixar um jogo leve que só está no PC, um PSP/3DS que só
está no Drive (rclone), pausar e retomar no meio, 💾 Saves de um jogo de RetroArch
com o notebook online e offline, stream de um jogo de Xbox/PS4 e de Switch, e
Situação/Opções nas duas orientações. A suíte `status` foi ajustada aos novos
textos, mas não rodou no aparelho.

### Continuação no notebook — fila da próxima rodada

Registrado em 22/10/2026 para a conversa local, que continua a implementação e
instala tudo no celular. Começar pelo roteiro de validação acima (branch
`claude/app-hub-mobile-ux-beurbv` nos três repositórios); só depois seguir o lote.

**Das anotações de uso ainda não atendidas:**
- **Adicionar o jogo:** ROM que só existe no celular → ação explícita "Adicionar à
  Biblioteca" no notebook (hoje nenhum cadastro é criado).
- **Nota 0–11 no app:** o dado vem no catálogo (`tracking.nota`) e o envio usa a
  mesma rota de edição do progresso (`/api/library/edit`); o modo TV já tem.
- **Saves de PSP/3DS por jogo:** hoje abrem o grupo inteiro (IDs do jogo, não nome
  da ROM); precisa do serial/title ID por jogo.
- **ROMs e saves sem o notebook (conta Google no app):** cliente OAuth Android já criado
  em 22/10 (projeto PyRetro). Além do download, o Victor quer **saves pela nuvem**: ler e
  gravar `Jogos/Saves` no Drive direto do celular, com as mesmas regras (conflito
  pergunta, versão anterior preservada). Exige escopo amplo do Drive (ok em modo Teste).
- **Um app só:** seguir a direção abaixo; nesta rodada só o Android deu o 1º passo.

**Lote de interface recomendado (só dados/rotas existentes, sem arquitetura nova):**
1. Android · **Início com fileiras** (Continuar jogando, Recentes, Mais jogados,
   Prontos no celular): online por `/api/tv/home`; offline pelo cache (progresso
   e `time:` locais). Maior ganho de fluidez.
2. Android · **Nota 0–11** na ficha.
3. Android · **Selos no cartão**: ✓ finalizado, ⏱ minutos, 💾 tem save, barra de
   download do próprio jogo (fila já expõe bytes/total).
4. Modo TV · **💾 Saves na ficha**, reaproveitando as rotas da aba Saves da web.
5. Modo TV · **coleções Jogando e Ranking** (depois Desejados e Estatísticas), com
   as consultas que a web já faz.

Depois do lote: filtro por plataforma/gênero na grade do Android (o sorteio já
filtra), ficha com capa grande e tempo no topo, contador no botão Situação quando
houver pendência/falha, mouse/toque melhores no modo TV (roda, hover, alvos),
trocar/buscar capa pela ficha do modo TV e identidade visual comum PC/Android
(cores, ficha, selos, nomes das ações) com a mesma ação principal por contexto.

**Correções ainda abertas:** melonDS e pilha executável (`step_emulator_extras`;
avaliar `melondsds`), client_id próprio do rclone (agora também serve o download
do celular), atalhos do 3DS no jogo, Tailscale ligado no celular, avaliar RomM,
consolidar o setup (`setup-linux-bonesi/docs/PENDENTE-CONSOLIDAR.md`) e a
homologação física (G8, Drive real, Steam Link, PS4/Xbox remotos).

**Notas práticas:** a suíte `status` do celular desliga a atualização automática
(`MainActivity.automaticUpdates=false`) para não mexer nas preferências reais. Na
sessão em nuvem o Maven Central respondia 429; lá o build usou um init script
local com o espelho do Google, que não foi versionado e não é necessário no notebook.

### Direção: um app só (PC e Android)

O modo TV (`/tv`) passa a ser a interface principal também no PC, e o app Android
segue o mesmo desenho. A interface web completa (`/`) continua existindo até cada
função ter lugar no app; nada é removido antes disso. Ordem proposta:

1. **Mesmo modelo de ficha nos dois:** ação principal por contexto, saves do jogo,
   stream sugerido para consoles, download — o Android 0.6 é o primeiro passo; o
   modo TV já tem parte disso (download do Drive, stream, tempo) e ganha **💾 Saves**.
2. **Entrada por toque e mouse no modo TV:** hoje é feito para controle; garantir
   clique/rolagem, teclado completo e alvos de toque sem perder a navegação por foco.
3. **Funções da web dentro do app, por uso:** capas (buscar/trocar/marcar), editar
   jogo e nota na Biblioteca, organizar ROM nova, saves/memory card, texturas,
   renomear/apagar com cascata e manutenção. Uma por vez, com os testes atuais.
4. **Quando a web não tiver nada exclusivo**, o atalho do navegador vira só
   diagnóstico.

## Próximos passos (em ordem)

1. **Homologação de uso:** executar a matriz acima e corrigir os atritos. No PC,
   Xbox físico, retorno de foco, Steam Link e sessões PS4/Xbox remoto; no Android,
   G8, Drive, emuladores (com NDS/3DS priorizados), pacote real de texturas e saves
   com emuladores fechados/estados compatíveis. Detalhes em
   [`plano-frontend.md`](plano-frontend.md) e [`../android/README.md`](../android/README.md).
2. **Acabamento da interface:** aproximar a identidade visual PC/Android, indicar
   claramente a aba ativa e reduzir passos nas ações frequentes. Preservar foco,
   rolagem e legibilidade com controle e touch, conferindo retrato/paisagem.
3. **Downloads Android em segundo plano:** avaliar serviço com notificação e
   recuperação após encerramento do processo. Manter pausa/cancelamento explícitos,
   integridade e checkpoints. A fila atual já é sequencial e persistente; a
   retomada continua explícita e pode reler todo o prefixo pelo provedor.
4. **Diagnóstico acessível:** explicar causa da falha e ação de recuperação na
   própria interface; oferecer relatório compartilhável sem contas, credenciais,
   endereços privados ou inventário pessoal.
5. **Conjuntos e distribuição:** tratar CUE/M3U com todas as faixas/discos no
   download e na remoção; simplificar atualização do APK com assinatura estável.
   Hoje CUE/M3U dependentes exigem gerenciador, e instalar atualização continua
   restrito ao usuário principal, preservando a assinatura.
6. **Evoluções posteriores:** nomes por title ID para saves/texturas 3DS, fontes
   verificadas de logos/prévias/trailers, identidade de documentos no índice da
   nuvem e importação de runtime antigo com prévia sem duplicar sessões. Retenção
   de versões deve ser explícita e recuperável; não há limpeza automática ativada.

### Notas para backup fora do RetroArch

Achados via adb em 05/08. Flycast/Dreamcast passaram para RetroArch em 24/08;
ver o histórico no changelog.

- **Dolphin (Wii)** ainda exige tratar a estrutura tipo NAND por title ID
  hexadecimal (`Wii/title/<high>/<low>/data/`). Para mostrar nomes legíveis seria
  preciso cruzar uma base externa ou extrair o título da ROM local. O cliente
  0.2 já copia dados/extdata do 3DS por grupo, mas a análise ainda não traduz
  esses IDs para nomes de jogos.
- O app de 3DS instalado no aparelho é **Lime3DS**
  (`io.github.lime3ds.android`); conferir o pacote efetivamente usado ao homologar.

## Registro de encerramento — prioridades após a 0.3

Registrado em 21/10/2026 para continuação em outra conversa. A 0.3 está instalada;
testes sintéticos aprovados não substituem os testes de uso abaixo. As sugestões
são propostas de evolução, sem automação agendada. **Continuação em 21/10:** o
usuário pediu novas melhorias sem celular; a central do item 2 foi implementada
na 0.4, compilada e testada no notebook. Depois o celular foi reconectado: a 0.4.1
foi corrigida, instalada e testada no aparelho. Em seguida, Victor autorizou os
itens 3 e 4: espaço/fixação e fila sequencial foram instalados na 0.5, com
instrumentação sintética no celular. Retenção de versões, serviço em segundo
plano e homologação dos fluxos reais continuam pendentes.

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
   do documento; abrir a central não consulta a rede. Na 0.4.1, layout/foco e
   atualização dos resumos foram conferidos por instrumentação em retrato/paisagem;
   G8 físico e homologação dos fluxos reais continuam pendentes.
3. **Gerenciar espaço pelo app:** tamanho dos jogos baixados, checkpoints e
   versões anteriores; filtros por sistema e progresso. Permitir fixar jogos para
   manter baixados e propor remoção confirmada de ROMs finalizadas, preservando
   saves. **0.5 implementada:** ROMs por tamanho, filtros, fixação e remoção
   individual confirmada/revalidada. Checkpoints têm consulta e descarte separados.
   Versões de saves não entram no total medido; retenção do histórico continua
   futura e deve ser explícita e recuperável.
4. **Evoluir downloads e índice da nuvem:** fila com progresso por jogo, pausa e
   cancelamento acessíveis; avaliar serviço Android com notificação para continuar
   em segundo plano. Deduplicar acessos ao mesmo documento por identidade do
   provedor, além da URI. Hoje a retomada é explícita e pode reler o prefixo; índice
   usa somente pastas/arquivos concedidos, sem varredura geral da conta Drive.
   **0.5 implementada:** fila sequencial persistente, bytes/estados, reordenação,
   pausa ao sair, retomada explícita e retirada sem descartar parcial. Não abre
   jogos automaticamente. Deduplicação da fila por documento/destino SAF; serviço
   com notificação e revisão ampla da identidade no índice continuam futuros.
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

# Plano: PyRetro como frontend no PC e celular

Levantado em 16/10/2026; situação do PC atualizada em 20/10/2026.

## PC

Implementado no modo TV (`/tv`):

- Tela inicial **Início** com destaque, recentes, continuar jogando, favoritos e fileiras
  dos jogos instalados. **Sistemas** mantém identificador, total do catálogo e quantidade local.
- **X** favorita o jogo; **Menu** abre opções de tema claro/escuro e tela cheia.
  Preferências ficam no cache do PC, sem alterar o acervo; recentes usam o histórico local.
- Sorteio nas duas interfaces oferece Jogar/Transmitir/loja/download, sem executar
  automaticamente. Na TV abre detalhes; a interface completa tem ações e link para o
  mesmo jogo na TV. Identidade por ID preserva homônimos e filtro de gênero correto.
- **Neste PC** reúne ROMs completas e instalações Steam/Epic/GOG/Amazon; plataforma e gênero
  são filtros navegáveis pelo controle. Capas, `.part`, ROMs vazias e descritores incompletos
  não comprovam instalação. Sistemas sem lançador continuam mostrando a presença local.
- **Y** abre busca com teclado virtual; A digita, X apaga, Menu confirma e B cancela.
  Na tela inicial a busca alcança todo o catálogo; nas coleções ela filtra a seleção atual.
- **LB/RB** pulam uma página da grade; **LT/RT** trocam de coleção. Direcional/analógico
  continuam navegando item a item; A confirma e B volta.
- **Apps** abre a lista fixa dos programas instalados: Steam em Big Picture, Heroic,
  emuladores, ES-DE e Remote Play Xbox/PlayStation. Entradas adicionais usam `[apps.<id>]`
  no arquivo de configuração; o navegador envia somente ID, nunca argv/comando.
- Acessos rápidos no Início para Xbox remoto, PS4 remoto, Steam, Heroic e emuladores.
  PS4 já registrado no Chiaki, com acesso direto preparado em tela cheia; dados de
  conexão no cache privado, sem copiar credenciais para o PyRetro.
  Cliente SysDVR oficial instalado e Switch Lite preparado para TCP Bridge por Wi-Fi,
  com IP apenas no cache privado. Transmite jogos; não encaminha automaticamente o
  controle Xbox nem captura HOME. Transmissão confirmada por Victor, com vídeo/áudio
  conectados. Pedidos repetidos reutilizam o cliente remoto já aberto.
- Alternativa por jogo quando há core compatível instalado (PicoDrive nos sistemas Sega;
  SwanStation em PS1 quando instalado). A escolha fica no perfil do navegador e é revalidada
  pelo backend. O padrão permanece o bridge do setup.
- Retorno do foco à janela da TV ao encerrar uma sessão de emulador, usando o helper KWin
  existente. Leitura do controle suspensa em segundo plano e durante a sessão; ao voltar,
  exige soltar os botões antes de aceitar novo comando.
- Nome do atalho de TV unificado em **PyRetro** no menu e na Steam. Migração preserva
  appid/artes/tags/perfil Steam Input. Atalho web antigo oculto; interface completa continua
  em `/`, pelo navegador.
- Perfil Xbox e hotkeys comuns nos cinco emuladores instalados, com simulação/cópia anterior
  por `tools/configure_xbox.py`. Detalhes em [`modo-tv.md`](modo-tv.md).

A integração de entrada/saída da sessão Plasma Bigscreen é mantida no setup do notebook,
fora do PyRetro. O fluxo escolhido é **botão Modo TV → Bigscreen → PyRetro/Steam/apps**,
sem substituir o desktop no boot. Guide pertence ao Bigscreen; Back modifica os hotkeys
nos emuladores. O remapeamento do Bigscreen deve ficar suspenso quando a TV ou um jogo
estiver em foco, para evitar teclado/mouse duplicados com Gamepad/SDL.

### Ainda depende de uso real

- Homologação física do Xbox nos jogos, foco, Steam Input e Steam Link.
- Ajustes por jogo no Wii (ponteiro/movimento e controle clássico).
- NDS/3DS foram priorizados no celular; não instalar emuladores no PC só para preencher a TV.
- Pareamento/uso real de Xbox e PS4. Switch Lite teve transmissão confirmada;
  controle Xbox no PC não é encaminhado ao Switch por essa integração.
- Tempo de sessão e importação de logos/prévias locais implementados; homologar no uso real.
  Busca automática de trailers/logos e importação de runtime antigo continuam futuras.
- ES-DE permanece instalado até a homologação do fluxo completo.

## Celular

### Inventário inicial por adb (16/10; validação atual abaixo)
- Instalados: RetroArch, PPSSPP Gold, DuckStation (Android), Lime3DS, FolderSync, Tailscale, Moonlight, Chrome.
  **Não havia** Termux, ES-DE, Daijishō nem NetherSX2/Dolphin. FolderSync foi retirado depois, preservando os arquivos.
- RetroArch abre por `am start -n com.retroarch/.browser.retroactivity.RetroActivityFuture` com extras
  `ROM`, `LIBRETRO`, `CONFIGFILE`: o comando foi aceito pelo adb (testado com uma ROM inexistente, para não
  tocar em estados salvos). Isso é o que frontends como ES-DE/Daijishō fazem.
- PPSSPP Gold aceita `VIEW` + `BROWSABLE` para arquivos `file`/`content` (um link `intent:` do Chrome
  consegue abri-lo; os padrões de extensão que li eram `.iso`, falta conferir `.chd`/`.cso`).
- DuckStation Android só expõe `MAIN/LAUNCHER`: **não achei como abrir um jogo por intent**.
- Capas já no celular: miniaturas do RetroArch (sincronizadas) e a pasta `covers` do DuckStation, onde
  acabei de copiar as capas de Castlevania SOTN e Diablo (os dois PS1 que estão lá).

### Continuação após a 0.5 (21/10)

A avaliação de robustez, a matriz de homologação PC/Android e a ordem das próximas
melhorias estão no [roadmap](roadmap.md#avaliação-de-robustez--encerramento-de-21102026).
Priorizar sessões reais e recuperação de falhas; o registro de encerramento não
inicia novas implementações nem agenda testes.

### Decisão (16/10): app Android nativo
Você quer um app de verdade. É a opção C da análise: um app pequeno em Kotlin que lista o acervo com as capas
do PyRetro e abre cada emulador por intent.

**Como cada emulador abre (verificado por `pm dump`/adb em 16/10):**
| Sistema | Emulador | Intent | Situação |
|---|---|---|---|
| 8/16-bit, N64, arcade, PS1 (SwanStation), etc. | RetroArch | componente explícito `RetroActivityFuture` + extras `ROM`/`LIBRETRO`/`CONFIGFILE` | aceito pelo adb (ROM inexistente, sem tocar em estados) |
| PSP | PPSSPP Gold | `VIEW` + `BROWSABLE`, `file`/`content` | padrões de extensão vistos: `.iso`; faltam `.chd`/`.cso` |
| 3DS | Lime3DS | `VIEW` com `content://` e `application/octet-stream` em `EmulationActivity` | exige URI `content` (permissão SAF da pasta de ROMs) |
| PS1 (DuckStation) | DuckStation Android | só `MAIN/LAUNCHER` | **sem intent de jogo conhecido**; usar RetroArch/SwanStation |

### Decisões e implementação de 20/10

- Banco inteiro permanece no computador. APK consulta catálogo projetado via HTTPS/Tailscale
  e guarda cache de metadados/capas; não lê a antiga cópia de `library.json` no telefone.
- Interface nativa para Galileo G8 **e touch**, com busca Y, favoritos X, paginação
  LB/RB, coleções LT/RT, foco visível, grade responsiva e botões de pelo menos 48 dp.
- Sem notebook/Tailscale: ROMs locais, catálogo já carregado, capas consultadas,
  favoritos, progresso e tempo continuam acessíveis. Progresso/tempo sincronizam por
  escolha explícita, com comparação no servidor sob lock e preservação de conflitos.
- NDS/3DS priorizados no celular; RetroArch (NDS e sistemas leves/PS1), PPSSPP Gold e
  Lime3DS/Azahar abrem por intent. Core do RetroArch pode ser escolhido por sistema;
  defaults NES/Nestopia e PC Engine/Beetle PCE seguem os cores existentes.
  Cores/BIOS permanecem sob gestão dos emuladores.
- Xbox chama **XBXPlay**, PS4 chama o **PS Remote Play oficial**, PC chama **Moonlight**.
  Pareamento e seleção do console continuam nos próprios aplicativos.
- ROMs sob demanda diretamente do Drive pelo provedor de arquivos do Android:
  vínculo escolhido uma vez por jogo, cópia para pasta local, staging exclusivo,
  conferência do tamanho informado, sem substituir arquivos existentes. PS1 sob
  demanda aceita CHD/PBP; CUE/M3U dependentes aguardam suporte específico.
- FolderSync retirado preservando arquivos; APK reaproveita as pastas existentes.
  Limpeza de ROMs somente por decisão explícita, com conferência das cópias no PC;
  saves/states/BIOS/texturas preservados. Ao finalizar no APK, confirmação oferece
  manter ou remover somente a ROM local. CUE/M3U dependentes exigem gerenciador.
- ZIP de texturas PSP/3DS pode ser importado offline; RAR/7z e fontes do catálogo
  são preparados pelo notebook e recebidos como ZIP. Não substitui textura diferente.
  Sync de saves/states/runtime disponível desde 21/10 na versão 0.2: grupos,
  SHA-256, conflitos e versões anteriores preservadas. BIOS/configurações ficam
  fora desses planos; runtime não é somado automaticamente. Uso real aguarda Victor.
- Versão 0.3: recuperar versões locais/PC pelo app, playlists
  JSON com prévia e atualização opcional, índice da nuvem por concessões SAF (pasta
  ou lote de arquivos), checkpoints para pausar/continuar downloads. Prefixo é
  validado de novo e pode ser relido; não há serviço de download em segundo plano.
  Build/lint/JVM passaram; instalado após reconexão, instrumentação ampliada aprovada
  com fixtures próprias e inventário real preservado. Uso com G8/Drive continua pendente.
- JDK/SDK/Gradle preparados em cache local persistente, sem instalação global/root.
  Versão 0.4 preparada sem celular: central de situação/conexões com registros de
  contato, pendências por jogo, resultados de saves, concessões SAF e checkpoints;
  atalhos para corrigir pastas, consultar nuvem e abrir emuladores/clientes/Tailscale.
  Após reconexão, 0.4.1 instalada: atualização automática dos resumos, tratamento
  de pastas/observações inválidas e foco inicial dos diálogos corrigidos. Build/lint,
  24 JVM e instrumentação retrato/paisagem aprovados; notebook respondeu após
  reconectar Tailscale. G8 físico, Drive e sync de uso ainda pendentes.
  Projeto, wrapper e `tools/build_android.py` versionados. Build, lint e testes JVM
  executados; APK pessoal em `cache/artifacts/`, fora do Git.
- Versão 0.5 instalada: gestão de espaço por ROM com filtros e fixação para manter
  baixado, remoção individual revalidada e fila sequencial persistente com estados,
  bytes, pausa/retomada/reordenação. Sair pausa; abrir não retoma sozinho e concluir
  não abre jogos. Sem serviço em segundo plano. Interface com barras horizontais,
  grupos de ações recolhidos, opções de ocultar dicas e retorno à coleção,
  busca e posição anteriores por Recentes → PyRetro. Aba Stream concentra Xbox,
  PS4 e PC/Switch por Moonlight, substituindo a fileira fixa do topo. 29 JVM, build/lint e suítes
  nativas de interface/armazenamento aprovados; arquivos reais preservados.
- Depois da preparação inicial, aparelho conectado e APK instalado: catálogo por
  Tailscale, cache offline, pastas, sorteio e importação de ZIP mínimo conferidos.
  Interface horizontal compacta, teclado virtual Y e reutilização da tela ao abrir
  novamente. Instalação restrita ao perfil principal evita duplicação Dual App.
  Galileo G8 físico, download real pelo Drive e os demais emuladores seguem em
  homologação; não confundir eventos de botões injetados com teste do controle.

Uso, arquitetura, compilação e limites: [`../android/README.md`](../android/README.md).

### Texturas no celular (PSP e 3DS validados em jogo em 16/10; PS1 instalado, a validar)
| Sistema | Pasta | Como liga | No código |
|---|---|---|---|
| PS1 | `Android/data/com.github.stenzek.duckstation/files/textures/<SERIAL>/replacements` | por jogo, em `gamesettings/<SERIAL>.ini` (o `settings.ini` do app é privado) | `instalar_celular` |
| PSP | `/sdcard/Jogos/PSP/PSP/TEXTURES/<ID>` (pasta já existe) | `ReplaceTextures` em `SYSTEM/ppsspp.ini` | idem |
| 3DS | `/sdcard/Jogos/3DS/load/textures/<TITLE ID 16 hex>` | `custom_textures = true` em `config/config.ini` do Lime3DS | idem |

Pelo PC, o envio é por `adb push` (`instalar_celular` em `core/texturas.py`); a aba Texturas tem o alvo celular e upload de arquivo local. O APK instala ZIP PSP/3DS por SAF, conforme o README Android. PS1: o dump não
liga no app Android, então o pacote vem de um dump feito no PC com o mesmo jogo.

### Alternativas descartadas por ora
Termux + PyRetro (exige permissão de sobreposição e não resolve o DuckStation), links `intent:` do Chrome
(só o PPSSPP é `BROWSABLE`) e Daijishō/ES-DE Android (sem o tracking do PyRetro).

## Texturas: o que falta no catálogo (pesquisa de 16/10/2026)
- PSP: 10 pacotes no catálogo (Internet Archive, verificados).
- GameCube/Wii: 39 pacotes em `nintendo-gamecube-roms/Dolphin - Texture Packs/`, todos com HTTP 401; ficam de fora até
  alguém liberar. Os nomes não trazem o ID do jogo (Dolphin aceita pasta pelo ID de 3, 4 ou 6 caracteres).
- 3DS e PS1: sem fonte verificável; usar "Importar um pacote de arquivo".
- Dolphin sem capa do PyRetro: ignorado.

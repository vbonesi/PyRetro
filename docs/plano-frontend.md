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
- Sistemas sem bridge/core instalado, como NDS/3DS, continuam sem lançamento pela TV.
- Pareamento/uso real de Xbox e PS4. Switch Lite teve transmissão confirmada;
  controle Xbox no PC não é encaminhado ao Switch por essa integração.
- Logos oficiais, vídeo/marquee/screenshot e tempo de sessão são melhorias futuras.
- ES-DE permanece instalado até a homologação do fluxo completo.

## Celular

### Verificado hoje (adb, Samsung SM-S928B, Android 16, tela bloqueada)
- Instalados: RetroArch, PPSSPP Gold, DuckStation (Android), Lime3DS, FolderSync, Tailscale, Moonlight, Chrome.
  **Não há** Termux, ES-DE, Daijishō nem NetherSX2/Dolphin.
- RetroArch abre por `am start -n com.retroarch/.browser.retroactivity.RetroActivityFuture` com extras
  `ROM`, `LIBRETRO`, `CONFIGFILE`: o comando foi aceito pelo adb (testado com uma ROM inexistente, para não
  tocar em estados salvos). Isso é o que frontends como ES-DE/Daijishō fazem.
- PPSSPP Gold aceita `VIEW` + `BROWSABLE` para arquivos `file`/`content` (um link `intent:` do Chrome
  consegue abri-lo; os padrões de extensão que li eram `.iso`, falta conferir `.chd`/`.cso`).
- DuckStation Android só expõe `MAIN/LAUNCHER`: **não achei como abrir um jogo por intent**.
- Capas já no celular: miniaturas do RetroArch (sincronizadas) e a pasta `covers` do DuckStation, onde
  acabei de copiar as capas de Castlevania SOTN e Diablo (os dois PS1 que estão lá).

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

**De onde o app lê o acervo:** `library.json` e as capas já chegam ao celular pelo FolderSync (as capas do
RetroArch estão em `/sdcard/RetroArch/thumbnails`); o app lê esses arquivos locais e, quando houver rede
(Tailscale), sincroniza progresso/nota com o servidor do PyRetro.

**Pré-requisito no PC:** não há JDK nem Android SDK (verificado). Seria preciso baixar JDK 17 e as ferramentas de
linha de comando do SDK (cerca de 1,5 GB, instaladas na sua pasta, sem root) e usar o Gradle. Eu só baixo com
o seu OK; o app é instalado pelo adb.

**Esforço:** 4–6 sessões (toolchain e esqueleto; lista com capas e controle; lançamento RetroArch/PPSSPP;
3DS e SAF; sincronização de progresso). Os testes precisam do celular **desbloqueado**.

### Texturas no celular (PSP e 3DS validados em jogo em 16/10; PS1 instalado, a validar)
| Sistema | Pasta | Como liga | No código |
|---|---|---|---|
| PS1 | `Android/data/com.github.stenzek.duckstation/files/textures/<SERIAL>/replacements` | por jogo, em `gamesettings/<SERIAL>.ini` (o `settings.ini` do app é privado) | `instalar_celular` |
| PSP | `/sdcard/Jogos/PSP/PSP/TEXTURES/<ID>` (pasta já existe) | `ReplaceTextures` em `SYSTEM/ppsspp.ini` | idem |
| 3DS | `/sdcard/Jogos/3DS/load/textures/<TITLE ID 16 hex>` | `custom_textures = true` em `config/config.ini` do Lime3DS | idem |

O envio é por `adb push` (`instalar_celular` em `core/texturas.py`); a aba Texturas já tem o alvo celular e a importação de arquivo. PS1: o dump não
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

# Plano: PyRetro como frontend no lugar do ES-DE (PC e celular)

Levantado em 16/10/2026. Nada abaixo foi implementado; o que foi **verificado** está marcado.

## PC

### O que já existe (verificado no código e em `docs/modo-tv.md`)
- Modo TV (`/tv`, `gui/static/tv.js`): navegação por controle/teclado, capas, coleções, plataformas,
  gêneros, Sortear, Jogando (últimos abertos), progresso/nota, baixar ROM do Drive sob demanda.
- Lançar jogo: `core/play.py` chama `~/.local/bin/bonisarch-emulator` (o mesmo que o ES-DE usa) só
  com ROM validada dentro da pasta do sistema, sem shell; uma sessão por vez; no fim oferece
  registrar progresso. Jogos de PC (Steam/Heroic) abrem pela loja.
- Atalho Steam que abre o Chrome em tela cheia no `/tv` (`tools/pyretro-tv.sh`), com `raise-window.sh`.
- Capas do PyRetro já aparecem no ES-DE, DuckStation e PCSX2 (`core/capas_emuladores.py`).

### O que falta para dispensar o ES-DE
1. **Tela inicial por sistema**, com logo e contagem, como a do ES-DE (hoje são abas).
2. **Busca e filtros no controle** (teclado na tela).
3. **Seção "Apps"**: lista no `config.toml` (`[apps.<id>]` com nome, comando fixo, ícone). O navegador só
   manda o id; nunca um comando. Cobre "qualquer coisa do PC" sem abrir uma porta para execução livre.
4. **Alternar emulador por jogo** (o ES-DE tem; hoje o lançador escolhe por sistema).
5. **Integração de boot**: trocar `bonisarch-esde` por `pyretro-tv.sh` no atalho/autostart, mantendo o ES-DE
   instalado até a homologação.
6. **Foco ao sair do emulador** e controle (Steam Input × API Gamepad do Chrome): o próprio `modo-tv.md`
   lista como "precisa ser conferido com os emuladores reais".
7. Opcional: vídeo/marquee/screenshot (hoje só capa), tempo de jogo, favoritos.

### Riscos
- Controle disputado entre Chrome e emulador (ações duplicadas); depende de Steam Input.
- O Chrome fica aberto durante o jogo (RAM). Dá para minimizar/fechar a janela ao lançar e reabrir ao sair.
- Homologação exige você na TV; eu não consigo conferir controle físico daqui.

### Etapas e esforço (estimativa; cada "sessão" = um bloco de trabalho como os de hoje)
| Etapa | Conteúdo | Esforço |
|---|---|---|
| 1 | Tela de sistemas + busca por controle | 1 sessão |
| 2 | Seção Apps com lista fixa no `config.toml` + testes | 1 sessão |
| 3 | Emulador alternativo por jogo | 1 sessão |
| 4 | Boot/foco/Steam Input, com você testando na TV | 1 sessão + testes seus |
| 5 | Vídeos/marquees (opcional) | 1–2 sessões |
Total: **4 sessões** para o essencial; ES-DE continua instalado até a etapa 4 passar.

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

O envio é por `adb push` (`instalar_celular` em `core/texturas.py`); falta ligar isso à aba Texturas. PS1: o dump não
liga no app Android, então o pacote vem de um dump feito no PC com o mesmo jogo.

### Alternativas descartadas por ora
Termux + PyRetro (exige permissão de sobreposição e não resolve o DuckStation), links `intent:` do Chrome
(só o PPSSPP é `BROWSABLE`) e Daijishō/ES-DE Android (sem o tracking do PyRetro).

# Configuração gráfica dos emuladores (PC × celular)

Ajuste feito em 16/10/2026 para deixar os jogos o mais bonitos possível **no PC**,
dentro do limite real do hardware. O celular não foi alterado: as configs dos dois
lados são independentes (ver "Onde cada config mora").

## Hardware do PC (medido, não suposto)

- Acer Nitro V 15 **ANV15-52** (DMI), i7-13620H, 16 GB, tela 1920×1080 (165 Hz de fábrica,
  usada em **60 Hz** desde 16/10, sem VRR).
- GPU híbrida: Intel UHD (iGPU, compõe a área de trabalho) + **RTX 4060 Laptop**.
  `nvidia-smi`: limite padrão **60 W**, máximo **75 W** (Dynamic Boost). Os 140 W
  citados em algumas lojas/reviews não valem para esta unidade.
- Os emuladores rodam na NVIDIA porque o `bonisarch-emulator` exporta as variáveis
  de PRIME offload (confirmado no `nvidia-smi pmon` durante os testes).

Critério: render interno na faixa 1080p–1440p (cabe nos 60–75 W com folga e ainda
fica nítido na TV por HDMI). Nada de opção que custa muito e quase não aparece
(blending alto do PCSX2, SSAA no Dolphin, upscale de textura).

## O que ficou em cada emulador do PC

| Sistema | Emulador | Antes | Agora |
|---|---|---|---|
| PS1 | DuckStation (AppImage) | padrão de fábrica; **não iniciava jogo** pelo lançador | Vulkan **fixado na RTX** (`[GPU] Adapter`), **5x** (1200p), PGXP (geometria/textura/cor + culling), true color sem dithering, suavização de croma em FMV, FMV forçado 4:3, deinterlace adaptativo, VSync |
| PS2 | PCSX2 (Flatpak) | 1x nativo, renderer automático, sem VSync | Vulkan, **3x** (~1344p), anisotrópico 16x, CAS só nitidez (40), VSync, **patches de widescreen e de remover entrelaçamento** ligados |
| GC / Wii | Dolphin (Flatpak) | padrão de fábrica (1x) | Vulkan, **3x** (1584p/1440p), MSAA 2x, anisotrópico 16x, detecção de mipmap arbitrário, shaders assíncronos (ubershaders) + pré-compilação no início, VSync |
| PSP | PPSSPP (Flatpak) | sem `ppsspp.ini` (nunca aberto) | Vulkan, **5x** (1360p), anisotrópico 16x, filtragem 2D inteligente, VSync, tela cheia |
| N64 | RetroArch / Mupen64Plus-Next | GLideN64 1920×1440, MSAA 4x, CRT royale global por cima, **rodando a 40 fps** (rewind) | **rewind desligado só neste núcleo** (`Mupen64Plus-Next.cfg`) → 60 fps; filtro filtro **3-point** (o do N64 real) + texrects nativos otimizados; preset **bilinear** no lugar do CRT (CRT em imagem de 1440 linhas gera moiré) |
| Dreamcast | RetroArch / Flycast | padrão (640×480) + CRT global | **1920×1440**, rewind desligado (`Flycast.cfg`), anisotrópico 16x, mipmap, alpha sorting por pixel; preset bilinear. Naomi/Atomiswave (pasta `ARCADE`) fica em 640×480 para o CRT royale continuar fazendo sentido |
| 2D (FC, SFC, MD, PCE, Neo Geo, arcade, GB/GBC/GBA, GG, 2600, Saturn) | RetroArch | presets já escolhidos (CRT royale, Mega Bezel, guest NTSC, LCD grid) | **sem mudança** — já é a escolha visual de vocês e é a mesma do celular |

Ajustes por jogo que já existiam (Super Mario 64, Pokémon Stadium) continuam valendo
por cima do padrão do núcleo.

## Testes (16/10, pelo `bonisarch-emulator`, tela desbloqueada a 60 Hz)

Feitos com contador de fps ligado temporariamente e print da tela; os contadores
foram desligados depois. As telas testadas são abertura/menu, não gameplay pesado.

| Jogo | Resultado |
|---|---|
| Mario Kart 64, Super Mario 64, Jet Force Gemini (N64) | **estava a 40 fps** (2/3 da velocidade) também com as opções antigas. Causa: `rewind_enable = "true"` global, com o RetroArch salvando o estado do N64 a cada 2 quadros e o áudio segurando o ritmo (com `audio_sync` desligado ia a 60). Descartados por teste: VSync, VRR, GPU (Intel dava igual), driver de áudio, latência, ParaLLEl-RDP, CountPerOp, Framerate. Com override de núcleo sem rewind: **60 fps**. A "tela branca" do Mario 64 era só o fade de entrada em câmera lenta |
| ActRaiser 2 (SFC) | 60 fps, CRT royale |
| Rayman (PS1) | 5x (1600×1280), PGXP, PAL a 50 VPS, GPU ~3%. **Antes não iniciava**: o `-batch` parava na pergunta do AppImage "Deseja criar um atalho para o DuckStation?" e o Vulkan pegava a **Intel**. Corrigido com `[Main] NoDesktopFile = true`, `SetupWizardIncomplete = false`, `ConfirmPowerOff = false`, `[AutoUpdater] CheckAtStartup = false` e `[GPU] Adapter = NVIDIA GeForce RTX 4060 Laptop GPU` |
| NFS Underground 2 (PS2) | 59,94 fps, Vulkan 3x, patches de widescreen carregados |
| Metroid Prime 2 (GC) | 59,94 fps, 3x, imagem limpa |
| Mario Galaxy (Wii) | 60 fps, 3x, 16:9 |
| Patapon 2 (PSP) | Vulkan, 5x, texto nítido. O travamento em Vulkan da primeira rodada era efeito da tela bloqueada |

Observações:
- Com a tela **bloqueada**, Vulkan no PPSSPP nunca apresenta o primeiro quadro e o
  processo fica parado; desbloqueada funciona. Se isso acontecer, o PPSSPP marca o
  Vulkan como falho em `FailedGraphicsBackends.txt` (mesma pasta do `ppsspp.ini`) e cai
  para OpenGL na próxima abertura: esvazie o arquivo para voltar.
- O **PCSX2 abriu atrás** da janela que estava em foco (o KWin impede roubo de foco).
  Pelo modo TV vale conferir; `tools/raise-window.sh pcsx2` traz a janela para frente.
- Jogo **PAL** (como esse Rayman) roda a 50 Hz numa tela de 60 Hz, então tem um leve
  tranco periódico. É do conteúdo; a versão NTSC do jogo evita isso.
- O RetroArch **grava a config ao sair** (`config_save_on_exit`), inclusive valores
  passados por `--appendconfig`. Para testar opção sem sujar o `retroarch.cfg`, salve
  uma cópia antes e restaure depois.
- O PCSX2 não consegue gravar o NVRAM da BIOS porque o Flatpak vê `~/Drive/Jogos` como
  somente leitura (`errno 30`). Só afeta relógio/idioma do console; saves não.

## PC × celular

| Sistema | PC | Celular (último espelho/backup) |
|---|---|---|
| PS1 | DuckStation 5x, PGXP completo | SwanStation (RetroArch) **1x**, PGXP desligado |
| PS2 | PCSX2 3x + widescreen | NetherSX2 (config não espelhada) |
| GC / Wii | Dolphin 3x, MSAA 2x, aniso 16x | Dolphin **3x**, Vulkan, sem MSAA (GFX.ini de 15/08) |
| PSP | PPSSPP 5x (Vulkan), sem upscale de textura | PPSSPP **5x**, Vulkan, aniso 16x, **upscale de textura xBRZ 2x** |
| N64 | GLideN64 1920×1440, MSAA 4x, sem CRT, sem rewind | GLideN64 1920×1440, MSAA 4x, **CRT royale global por cima**, sem rewind (override de 16/10, 60 fps medidos) |
| Dreamcast | Flycast 1920×1440, aniso 16x, alpha por pixel | Flycast **1440×1080**, aniso 4x, alpha por triângulo, sem rewind (override de 16/10) |
| NDS | núcleo melonDS **não instalado** no PC | melonDS (RetroArch) |
| 2D | mesmos presets | mesmos presets (+ MAME, Gearboy, NeoPop, SwanStation, que o PC não tem) |

O celular não estava conectado por `adb` nesta sessão; a coluna dele vem de
`Backups/retroarch_android_2026-08-24/` e do espelho manual em `Saves/Dolphin/Config`
e `Saves/PPSSPP/SYSTEM` (15/08). Pode estar desatualizada.

**Rewind no celular (16/10, via `adb`).** O `retroarch.cfg` do celular
(`Android/data/com.retroarch/files/`) tem `rewind_enable = "true"` com
`rewind_granularity = "2"`, igual ao PC. Foram criadas as overrides de núcleo
`RetroArch/config/Mupen64Plus-Next/Mupen64Plus-Next.cfg` e
`RetroArch/config/Flycast/Flycast.cfg`, só com `rewind_enable = "false"` (nenhuma das duas
existia). Super Mario 64 com a override: **60,1 fps** na tela de título (128 quadros
contados pelo `dumpsys SurfaceFlinger --latency`, intervalo mediano de 16,6 ms, tela a
60 Hz). A medição sem a override (para confirmar os ~40 fps) não foi feita; veja Pendências.

## Onde cada config mora

| Emulador | Arquivo no PC | Compartilha com o celular? |
|---|---|---|
| RetroArch | `~/.var/app/org.libretro.RetroArch/config/retroarch/` (`retroarch.cfg`, `config/<núcleo>/*.opt` e `*.slangp`) | Não |
| PCSX2 | `~/.var/app/net.pcsx2.PCSX2/config/PCSX2/inis/PCSX2.ini` | Não |
| Dolphin | `~/.var/app/org.DolphinEmu.dolphin-emu/config/dolphin-emu/{Dolphin,GFX}.ini` | Não. `Saves/Dolphin/Config` no Drive é o espelho do **celular**; o Flatpak do PC enxerga o Drive só como leitura |
| PPSSPP | `~/.var/app/org.ppsspp.PPSSPP/config/ppsspp/PSP/SYSTEM/ppsspp.ini` | Não. `Saves/PPSSPP/SYSTEM` é o espelho do celular |
| DuckStation | `~/.local/share/duckstation/settings.ini` | Não (memory cards e save states sim, em `Saves/PS1-DuckStation`) |

**Não copie** os `.ini` do espelho do Drive para o PC nem o contrário: os caminhos
(`content://` no Android) e as escolhas de desempenho são diferentes.

## Backup e como desfazer

Cópia de tudo antes da mudança: `~/Drive/Jogos/Backups/emuladores_pc_2026-10-16_antes/`
(o Google Drive também guarda versões). Para voltar um emulador, copie os arquivos
dele de lá para o caminho da tabela acima, com o emulador fechado.

Se algum jogo pesar demais (queda abaixo de 60 fps com a GPU em ~75 W), o primeiro
passo é descer a resolução **daquele jogo** pelo menu do próprio emulador
(configuração por jogo), não o padrão global. Se um patch de widescreen do PCSX2
quebrar a HUD de algum jogo, desligue-o só nas propriedades daquele jogo.

## Pendências

- **Gameplay pesado**: os testes pegaram abertura/menu. Se algum jogo cair abaixo de
  60 fps em cena pesada, descer a resolução só daquele jogo.
- **Rewind no celular**: override sem rewind criada para Mupen e Flycast em 16/10; N64
  medido a 60 fps com ela. Não foi medido sem a override, então não se sabe se o celular
  estava mesmo a ~40 fps. Testar um N64 em gameplay (não só a tela de título) e um
  Dreamcast. **Cuidado ao testar:** o celular usa `savestate_auto_save`/`auto_load`, então
  abrir e fechar um jogo regrava `states/<jogo>.state.auto`. O teste de 16/10 regravou o
  `Super Mario 64.state.auto` do celular (sem cópia anterior).
- **60 Hz**: a tela fica fixa em 60 Hz (165 Hz sem VRR deixava a cadência irregular).
  O RetroArch está com `vrr_runloop_enable = "false"`, que é o certo para tela fixa.
  Se um dia o VRR for ligado, volte essa chave para `"true"`.
- **NDS no PC**: falta instalar o núcleo melonDS DS e mapear `nds` no lançador.

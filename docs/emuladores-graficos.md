# Configuração gráfica dos emuladores (PC × celular)

Ajuste feito em 16/10/2026 para deixar os jogos o mais bonitos possível **no PC**,
dentro do limite real do hardware. O celular não foi alterado: as configs dos dois
lados são independentes (ver "Onde cada config mora").

## Hardware do PC (medido, não suposto)

- Acer Nitro V 15 **ANV15-52** (DMI), i7-13620H, 16 GB, tela 1920×1080 a 165 Hz.
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
| PSP | PPSSPP (Flatpak) | sem `ppsspp.ini` (nunca aberto) | **OpenGL** (ver testes), **5x** (1360p), anisotrópico 16x, filtragem 2D inteligente, VSync, tela cheia |
| N64 | RetroArch / Mupen64Plus-Next | GLideN64 1920×1440, MSAA 4x, CRT royale global por cima | igual + filtro **3-point** (o do N64 real) + texrects nativos otimizados; preset **bilinear** no lugar do CRT (CRT em imagem de 1440 linhas gera moiré) |
| Dreamcast | RetroArch / Flycast | padrão (640×480) + CRT global | **1920×1440**, anisotrópico 16x, mipmap, alpha sorting por pixel; preset bilinear. Naomi/Atomiswave (pasta `ARCADE`) fica em 640×480 para o CRT royale continuar fazendo sentido |
| 2D (FC, SFC, MD, PCE, Neo Geo, arcade, GB/GBC/GBA, GG, 2600, Saturn) | RetroArch | presets já escolhidos (CRT royale, Mega Bezel, guest NTSC, LCD grid) | **sem mudança** — já é a escolha visual de vocês e é a mesma do celular |

Ajustes por jogo que já existiam (Super Mario 64, Pokémon Stadium) continuam valendo
por cima do padrão do núcleo.

## Testes de abrir/fechar (16/10, pelo `bonisarch-emulator`)

| Jogo | Resultado |
|---|---|
| Super Mario 64, Jet Force Gemini (N64) | abre na NVIDIA, carrega `Mupen64Plus-Next.slangp` (bilinear), fecha |
| ActRaiser 2 (SFC) | abre na NVIDIA, fecha |
| Rayman (PS1) | **antes não iniciava**: o `-batch` ficava parado na pergunta do AppImage "Deseja criar um atalho para o DuckStation?", e o Vulkan pegava a **Intel** (primeiro dispositivo da lista). Corrigido com `[Main] NoDesktopFile = true`, `SetupWizardIncomplete = false`, `ConfirmPowerOff = false`, `[AutoUpdater] CheckAtStartup = false` e `[GPU] Adapter = NVIDIA GeForce RTX 4060 Laptop GPU`. Agora inicia em 5x na RTX e fecha |
| NFS Underground 2 (PS2) | Vulkan na RTX, 3x, 14 patches do jogo carregados (widescreen incluso), chega ao menu, fecha |
| Metroid Prime 2 (GC), Mario Galaxy (Wii) | Vulkan na RTX, fecha |
| Patapon 2 (PSP) | em **Vulkan**, o processo abre a NVIDIA e fica parado antes do primeiro quadro, e não fecha com SIGTERM. Em **OpenGL** abre na RTX e fecha normalmente; ficou em OpenGL, sem diferença visual |

Limitação: a tela estava **bloqueada** durante os testes, então nenhum quadro chegou
a ser mostrado (o print só pegou a tela de bloqueio). A trava do PPSSPP em Vulkan
pode ser só isso; vale testar de novo com a tela desbloqueada antes de voltar para
Vulkan (`GraphicsBackend = 3 (VULKAN)` e esvaziar `FailedGraphicsBackends.txt` na
mesma pasta do `ppsspp.ini`). O consumo da GPU medido (2–11 W) também não vale como
referência de desempenho pelo mesmo motivo.

Achado à parte: o PCSX2 não consegue gravar o NVRAM da BIOS porque o Flatpak vê
`~/Drive/Jogos` como somente leitura (`errno 30`). Só afeta configurações do
relógio/idioma do console PS2; não afeta saves (memory cards ficam em outro lugar).

## PC × celular

| Sistema | PC | Celular (último espelho/backup) |
|---|---|---|
| PS1 | DuckStation 5x, PGXP completo | SwanStation (RetroArch) **1x**, PGXP desligado |
| PS2 | PCSX2 3x + widescreen | NetherSX2 (config não espelhada) |
| GC / Wii | Dolphin 3x, MSAA 2x, aniso 16x | Dolphin **3x**, Vulkan, sem MSAA (GFX.ini de 15/08) |
| PSP | PPSSPP 5x (OpenGL), sem upscale de textura | PPSSPP **5x**, Vulkan, aniso 16x, **upscale de textura xBRZ 2x** |
| N64 | GLideN64 1920×1440, MSAA 4x, sem CRT | GLideN64 1920×1440, MSAA 4x, **CRT royale global por cima** |
| Dreamcast | Flycast 1920×1440, aniso 16x, alpha por pixel | Flycast **1440×1080**, aniso 4x, alpha por triângulo |
| NDS | núcleo melonDS **não instalado** no PC | melonDS (RetroArch) |
| 2D | mesmos presets | mesmos presets (+ MAME, Gearboy, NeoPop, SwanStation, que o PC não tem) |

O celular não estava conectado por `adb` nesta sessão; a coluna dele vem de
`Backups/retroarch_android_2026-08-24/` e do espelho manual em `Saves/Dolphin/Config`
e `Saves/PPSSPP/SYSTEM` (15/08). Pode estar desatualizada.

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

- **Conferência visual**: os testes desta sessão foram feitos com a tela bloqueada.
  Abrir/fechar, renderer e GPU foram confirmados pelos logs e pelo `nvidia-smi`,
  mas a imagem em si e o fps sob carga ainda precisam ser vistos.
- **PPSSPP em Vulkan**: testar de novo com a tela desbloqueada (ver acima).
- **VRR**: a tela de 165 Hz está com VRR em "Nunca" no KDE. Jogo a 60 fps numa tela
  de 165 Hz sem VRR tem cadência irregular (165/60 = 2,75). Ativar VRR em
  Configurações do Sistema > Tela, ou usar 60 Hz para jogar, deixa o movimento liso.
  O RetroArch já está com "sincronizar com a taxa exata do conteúdo" ligado e
  aproveita o VRR assim que ele for ativado.
- **NDS no PC**: falta instalar o núcleo melonDS DS e mapear `nds` no lançador.

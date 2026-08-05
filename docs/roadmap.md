# Roadmap

Estado atual e próximos passos do PyRetro. Histórico detalhado (bugs
achados, testes, o raciocínio por trás de cada decisão) fica em
[`docs/changelog.md`](changelog.md) - este arquivo é só "o que está
pronto" (resumo) e "o que vem a seguir". Atualizado em 05/08/2026.

## Status atual

| Área | Status |
|---|---|
| GUI de capas (galeria, busca, flag/duplicada/renomear/apagar) | ✅ Pronto |
| Sync de capas PC↔celular via adb (`core/sync.py`) | ✅ Pronto, despriorizado (Drive cobre sistemas leves) |
| Sanitização de nomes / validação de PNG real | ✅ Pronto |
| Gestão de ROMs pesadas (PS/SDC/PS2/GameCube/Wii/PSP/3DS) | ✅ Pronto, testado no aparelho |
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
| Backup de saves do Flycast/Dolphin/PPSSPP/3DS (fora do RetroArch) | 🔍 Investigado no aparelho real - achados registrados abaixo, aguardando decisão de escopo/ordem com o usuário |
| PyRetro rodando no Android (Termux) | 📝 Passo a passo escrito ([`docs/termux_setup.md`](termux_setup.md)) - não testado no aparelho |
| `sync.py` pra saves/states/runtime-logs | ❌ Cancelado (sempre vai usar Google Drive pra isso) |

## Próximos passos (em ordem)

1. Decidir com o usuário o escopo/ordem do backup de saves do
   Flycast/Dolphin/PPSSPP/3DS - achados reais via adb em 05/08:
   - **Dolphin (GameCube)**: já individualizado nativamente - um
     arquivo `.gci` por jogo em `GC/<REGIÃO>/Card A|B/`, nome
     prefixado pelo game code (ex: `70-GBTE-bayblade2002.gci`). Fácil,
     mesmo padrão do memory card PS1/PS2 (cruzar prefixo com DAT de
     serial).
   - **PPSSPP**: já individualizado nativamente - uma pasta por save
     em `PSP/SAVEDATA/<serial>` (ex: `ULUS10021`), sem card
     compartilhado nenhum. Fácil, existe DAT de redump pro PSP
     também.
   - **Flycast (Dreamcast)**: usa VMU compartilhado
     (`vmu_save_A1.bin`/`A2.bin`, um "cartão" só pra vários jogos) -
     mesmo problema de fundo que PS1/PS2, mas sem uma ferramenta tipo
     `ps2vmc-tool` pronta pra VMU - precisaria parser novo ou achar
     outra ferramenta.
   - **Dolphin (Wii) e 3DS**: estrutura tipo NAND por title-ID em
     hexadecimal (`Wii/title/<high>/<low>/data/`,
     `Nintendo 3DS/.../title/<high>/<low>/data|extdata/`) - bem mais
     complexo, título não vem legível (precisaria cruzar title-ID com
     alguma base externa, ou extrair do header do próprio arquivo de
     ROM local). Mais caro que os outros quatro.
   - Nota: o app de 3DS instalado no aparelho é **Lime3DS**
     (`io.github.lime3ds.android`), não "Azahar" como mencionado -
     mesma família (fork do Citra), mas nome/pacote diferentes.
2. Testar [`docs/termux_setup.md`](termux_setup.md) contra o aparelho
   real.

## Arquitetura de dois modos

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

## Visão de longo prazo (fora de escopo agora, só registrado)

Pergunta feita em 04/08: seria possível o PyRetro virar uma "Switch"
completa e personalizada de ponta a ponta (interface + emulação em si),
excluindo os consoles pesados? Registrado como norte de longo prazo,
não como item de roadmap com desenho - envolveria decisões bem maiores
(rodar/embutir núcleos libretro ou orquestrar o próprio RetroArch a
partir do PyRetro, UI pensada pra uso com controle/tela cheia em vez de
navegador) que merecem conversa própria quando o resto da base
(organize/heavy-roms/memory card/modo Android) estiver mais madura.

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
  PyRetro direto no Android.

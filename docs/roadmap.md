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
| Editor de memory card PS1/PS2 (`ps2vmc-tool`) | ✅ Pronto, testado (aba "💾 Saves" - listar + exportar, com nome do jogo resolvido via serial) |
| ROMs pesadas via `rclone` (ver Drive + baixar sem adb) | ✅ Pronto, testado (listagem + download reais) |
| PyRetro rodando no Android (Termux) | 📝 Passo a passo escrito ([`docs/termux_setup.md`](termux_setup.md)) - não testado no aparelho |
| `sync.py` pra saves/states/runtime-logs | ❌ Cancelado (sempre vai usar Google Drive pra isso) |

## Próximos passos (em ordem)

1. Testar [`docs/termux_setup.md`](termux_setup.md) contra o aparelho
   real.
2. Editor de memory card - importar/injetar save de volta no cartão
   (`-in`/`-psu-import`), hoje só lista + exporta.
3. ~~ScreenScraper~~ - feito (ver Status atual).
4. ~~Editor de memory card (listar/exportar)~~ - feito (ver Status
   atual).

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

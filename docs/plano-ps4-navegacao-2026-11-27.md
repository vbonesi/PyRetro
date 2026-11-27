# Plano de 27/11/2026: PS4 nos Desejados, navegação sem rolagem lateral e análises "tem no PS4?"

Opus planejou; execução por sessões Sonnet. Itens espelhados na página PyRetro do Notion.
Marcas: **P** pesado, **L** leve, **V** Victor.

Regra de dados: a Biblioteca só é lida e escrita **pela API do `pyretro-gui`** (`/api/library`,
`/api/wishlist`, `/api/tv/catalog`, `/api/library/edit` com CSRF, `/api/wishlist/*`). Nunca abrir
`library.json` nem `config.toml`.

## Frente 1: PS4 nos Desejados (L)

Hoje os 26 Desejados da PSN são gravados com plataforma `"PSN"`, o modo TV os mostra como
PlayStation (o ícone/rótulo cai no PS1) e o botão diz "➕ PSN". O console do Victor é o **PS4**.

**PS1. Rótulo e plataforma (código)**
- `gui/static/tv/state.js`: `WISHLIST_STORES.psn` = `"PS4"`; `tv.html`: botão `➕ PS4`.
- `core/library.py`: `add_to_wishlist("psn", …)` grava `plataforma = "PlayStation 4"` (a fonte
  continua `wishlist:psn`, para não quebrar o casamento e o Android).
- Achar por que a plataforma `PSN` aparece como PS1 (ícone/sigla em `platforms.js`/`logic.js`/cards)
  e garantir que `PlayStation 4` mostra PS4 em card, ficha, filtros e Estatísticas.
- Android: mesmo rótulo onde aparecer "PSN" para o usuário (sem instalar APK; só compilar).
- Migração única pela API: os registros `wishlist:psn` com plataforma `PSN` passam a
  `PlayStation 4`. Shadow of the Colossus (gravado como PS2 na lista da PSN) vira o remake de PS4
  (2018, Bluepoint), mantendo o nome antigo em `nomes_alt`.
- Testes Python/JS cobrindo o rótulo e a plataforma nova.

**PS2. Limpeza dos nomes (dados, pela API, sempre com o nome antigo em `nomes_alt`)**

| Hoje | Fica |
|---|---|
| Ghost of Tsushima VERSÃO DO DIRETOR | Ghost of Tsushima |
| Guardiões da Galáxia da Marvel | Marvel's Guardians of the Galaxy |
| Nioh 2 Remastered – A Edição Completa | Nioh 2 Remastered (ver nota) |
| Pacote digital com UNCHARTED 4: A Thief's End e UNCHARTED: The Lost Legacy | Uncharted 4: A Thief's End |
| (novo cartão) | Uncharted: The Lost Legacy (jogo independente, 2017) |
| UNCHARTED The Nathan Drake Collection | Uncharted: The Nathan Drake Collection |
| Until Dawn 2015 | Until Dawn |
| The Last of Us: Left Behind Stand Alone | **sai dos Desejados** (rota `/api/wishlist/remove`) |
| (novo cartão) | Knack 2 (2017, Japan Studio) |

Nota Nioh 2: "Remastered" é a edição de PS5; no PS4 o jogo é "Nioh 2" (a edição completa de PS4 se
chama "Nioh 2 – The Complete Edition"). Sem resposta do Victor, fica "Nioh 2 Remastered" como ele
pediu; o executor pergunta antes.

Cartões novos com dados completos (capa, gênero, desenvolvedora, lançamento, sinopse em pt), como
os desejados de Switch de 24/11. Capa nova sobe para a nuvem como as demais.

Critério de pronto: `/api/wishlist` → `psn` mostra **27** jogos (26 − Left Behind + Lost Legacy + Knack 2), todos com plataforma `PlayStation 4`, nomes da
tabela, capa; modo TV mostra "PS4" no card e no botão; testes verdes; commit pequeno.

## Frente 2: navegação sem rolagem lateral (P)

### O problema
O cabeçalho tem cinco faixas com `overflow-x:auto` (`#quick`, `#platforms`, `#genres`, `#orders`,
`#tools`) e o Início tem prateleiras horizontais (`.shelf`). No controle, chegar a "Nintendo
Switch" exige dezenas de toques →, a faixa rola de forma imprevisível e a barra de rolagem fica
visível (print de 27/11). A barra lateral mistura emoji colorido (🏠 📚 📺 🛠) com um glifo de
texto fino (♡) e, fechada, o ícone não fica centrado no trilho com a marca de "atual".

### O que os frontends fazem (pesquisa de 27/11)
- **RetroArch XMB/Ozone:** cada nível rola em **um eixo só**. Ozone = lista vertical de sistemas à
  esquerda + lista vertical de jogos; nada de faixa horizontal de filtros.
- **Playnite (modo tela cheia):** filtros ficam num **painel lateral próprio** (lista vertical) e
  os presets de filtro ficam no topo, trocados por botão.
  [manual](https://api.playnite.link/docs/manual/gettingStarted/playniteFullscreenMode.html)
- **ES-DE:** Start abre menu, Select abre opções do jogo, LB/RB pulam 10 jogos na lista;
  "quick system select" troca de sistema sem voltar à tela de sistemas.
  [guia](https://repo.retrodeck.net/Xargon/ES-DE/raw/commit/dd4e21e2a3325ecac0cc5fca6068a26ddbc75b09/USERGUIDE.md)
- **LaunchBox Big Box:** plataformas e filtros como **lista de texto vertical** com detalhes à
  direita; item selecionado centralizado na lista.
  [views](https://feedback.launchbox-app.com/help/articles/9450321-big-box-views)
- **Steam Big Picture / PS5:** filtros num painel que desliza da lateral; prateleiras horizontais
  com **foco fixo** (o card focado fica parado na mesma coluna e a fileira desliza por baixo).

### Desenho
**N11 (P). Filtros em painel vertical, não em faixa.**
- Some a faixa de chips. No lugar, uma linha curta de 3–4 botões-resumo:
  `Plataforma: Todas ▾` · `Gênero: Qualquer ▾` · `Ordem: A–Z ▾` · `⋯ Ações`.
- Cada um abre um **painel lateral à direita** (gaveta) com **lista vertical** (↑/↓ move, A escolhe,
  B fecha sem mudar, item atual centralizado e marcado). Plataformas agrupadas
  (Sony, Nintendo, Sega, Arcade, PC/lojas) com cabeçalhos não focáveis.
- **X** abre o painel de filtros direto de qualquer lugar da Biblioteca/Desejados;
  **LB/RB** continuam trocando o filtro rápido (já existe); **Start** abre `⋯ Ações`
  (Atualizar, ➕ PS4/Xbox/Switch/Switch 2, 🔄 Steam, Estatísticas, Sortear, Só neste PC).
- Mouse: os mesmos botões abrem o mesmo painel; teclado: Esc fecha.
- Barra de dicas no rodapé mostra X/Start/LB/RB conforme a tela.

**N12 (L). Prateleiras do Início com foco fixo.**
- `.shelf` com `scroll-snap`; ←/→ move o foco mas o card focado fica na 1ª coluna visível
  (a fileira desliza), sem barra de rolagem visível; fim da fileira = card "Ver tudo →" que abre a
  Biblioteca já filtrada. LB/RB pulam uma tela inteira dentro da fileira.
- Rolagem por `transform`/`scrollTo({behavior:"smooth"})` com uma animação por vez
  (fila descartando passos repetidos, para o controle não "atropelar").

**N13 (L). Barra lateral: ícones coerentes.**
- Trocar os emoji/glifo por **um conjunto de ícones SVG monocromáticos** (`currentColor`), mesmo
  tamanho e peso; ícone sempre no mesmo X (centro do trilho) aberto ou fechado; o rótulo entra à
  direita sem empurrar o ícone; marca de "atual" como barra fina na borda, fora da caixa do ícone.
- Conferir no print com o trilho fechado e aberto, nos temas claro e escuro.

**N14 (L). Estabilidade.**
- Memória de foco por região e por rota (voltar da ficha cai no mesmo card); nenhuma rota abre com
  foco perdido; tempo de resposta do D-pad com repetição ao segurar (300 ms, depois 80 ms).

Critério de pronto da frente: nenhum elemento com `overflow-x` alcançável pelo controle no
cabeçalho; qualquer plataforma a ≤ 4 toques a partir da Biblioteca; testes JS novos para o painel
e para o foco fixo; capturas do antes/depois em 1080p e no tamanho do Steam Link; changelog e
`docs/modo-tv.md` atualizados. Android fica para depois do V1 (mesma ideia em Compose).

**V3 (V).** Victor usa uma semana com o Nova 2 Lite e diz o que ainda trava.

## Frente 3: análises "tem no PS4?" (P, internet)

Quatro TXT em `~/Downloads` (somente leitura no banco):

1. `PS4 - Desejados do Xbox.txt`
2. `PS4 - Desejados da Steam.txt`
3. `PS4 - Switch que tenho.txt`
4. `PS4 - Emulação (PS1, PS2 e outros).txt`

Regras:
- Só entra o jogo que **existe para PS4** (nativo, remaster, coleção, PS2 Classic/PS1 Classic na PS
  Store do PS4, ou compatível que roda no PS4). Dizer qual edição de PS4 (ex.: "Crash Bandicoot
  N. Sane Trilogy", "Final Fantasy VII (port de 2015)").
- **Ordenar pelo tamanho no PS4 em GB, do menor para o maior**. Fonte do tamanho: página da PS Store/PlayStation, sites de tamanho de
  instalação; sem dado do PS4, estimar pela versão de PS5/Xbox One/PC e marcar `~` (estimado).
- Linha: `tamanho GB | nome no meu banco | edição no PS4 | observação | fonte`.
- Marcar quem já está nos Desejados de PS4 ou no PS4 do Victor (`[já no PS4]`).
- Emulação: PS1 e PS2 primeiro e completos; depois os outros sistemas (só os que têm versão PS4).
- Cabeçalho com data, total e fontes usadas; no fim, a lista do que não existe no PS4 (só nomes).

Critério de pronto: quatro arquivos em `~/Downloads`, UTF-8, cada linha com fonte; nenhuma
escrita no banco; resumo no chat com os totais.

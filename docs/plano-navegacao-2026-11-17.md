# Plano da nova navegação (PC e Android) — 17/11/2026

Pedido do Victor depois do uso real: a navegação segue ruim no PC e no celular. Decisões dele em 17/11:

- Refazer a navegação com tempo, nos dois aparelhos, inspirada em Steam Big Picture (interface do Deck),
  Playnite, LaunchBox/ES-DE, Google TV/PS5 e Daijishō/iiSU.
- No PC a interface tem de funcionar **bem com mouse e teclado**, mas **principalmente com controle**.
  Uma interface só, não dois modos.
- **Descontinuar a web (`/`)**, depois que o modo TV cobrir o que só ela faz.
- Android: mesma estrutura, interface **nativa** (Jetpack Compose), mantendo as classes de dados atuais.
  O app continua funcionando sem o notebook.

Ciclo: **P** = pesado (desenho, risco, mais revisão), **L** = leve (critério claro), **V** = Victor.
Executado por outra sessão; cada item termina com testes verdes e um commit pequeno, sem push.

## Diagnóstico

- 14 coleções no topo do modo TV (`gui/static/tv.js`, `collections`), 8 no Android (`COLLECTIONS` em `MainActivity.kt`).
- "ROMs leves", "ROMs pesadas" e "Biblioteca" separam o jogo pelo lugar do arquivo.
- Ficha, ferramentas, busca e configurações são `<dialog>`: sem endereço, sem histórico, o voltar do mouse
  e o Alt+← não funcionam e o foco se perde.
- O mouse foi adaptado depois; a web cobria o mouse.

## Estrutura alvo

- **5 destinos** numa barra lateral: Início, Biblioteca, Desejados, Apps e stream, Ferramentas. Busca sempre no topo.
- **Início**: destaque "Continuar" e fileiras (Jogando, Favoritos, Neste PC, Adicionados há pouco, Recentes).
- **Biblioteca única**: jogos de PC, ROMs leves e pesadas e Switch juntos, sem duplicar. Filtros rápidos (Tudo,
  Jogando, Neste PC/celular, Favoritos, Ranking, Finalizados) trocados por LB/RB; painel de filtros (sistema,
  gênero, só local, ordem). Estatísticas no cabeçalho; Sortear é um botão. Analógico direito/letra pula por inicial.
- **Ficha do jogo é página** com endereço: uma ação principal (Jogar, Baixar e jogar, Transmitir), fileira
  secundária (Saves, Capa, Editar, Texturas, Progresso) e o raro num menu "⋯".
- **Voltar unificado**: B, Esc, Alt+←, botão voltar do mouse e gesto do Android fazem `history.back()`/pilha.
- **Entrada decide o visual**: mexeu o mouse, aparecem cursor, hover e setas; usou o controle, o cursor some e
  aparece o anel de foco. Barra de dicas no rodapé conforme o aparelho (Xbox, PlayStation, teclado/mouse).
- **Teclado**: digitar já busca; Ctrl+K busca; Enter abre; Esc volta. **Mouse**: botão direito = Menu = opções do jogo.
- **Um só motor de foco** por geometria, com memória por região/fileira, foco fixo na fileira (a fileira corre),
  sem armadilha.
- **Android**: barra inferior (Início, Biblioteca, Desejados, Busca) em retrato; barra lateral em paisagem ou com
  controle ligado. Mesmos nomes e ações do PC.

## Itens

### PC (modo TV)

- **N1 (P) — Módulos e rotas, sem mudar o comportamento.** Dividir `tv.js` em módulos ES (`api`, `state`,
  `router` por hash, `focus`, `input`, telas). Rotas `#/inicio`, `#/biblioteca`, `#/jogo/<chave>`, `#/desejados`,
  `#/apps`, `#/ferramentas/<id>`. Pronto: testes JS e Python verdes; todas as coleções atuais ainda abrem;
  recarregar a página numa rota volta à mesma tela; voltar do navegador funciona entre telas.
- **N2 (P) — Motor de foco e modo de entrada.** Módulo único de navegação espacial (vizinho por geometria,
  memória por região), `data-input="pad|mouse|keys"` no `<body>`, cursor escondido no modo controle, barra de dicas
  que muda com o aparelho. Pronto: testes JS do vizinho e da memória; trocar entre mouse e controle sem recarregar.
- **N3 (P) — Barra lateral com os 5 destinos e o novo Início.** Substitui a fileira de 14 coleções. View/Select abre
  a barra; ← na borda esquerda também. Pronto: nenhum destino exige mais de 2 movimentos a partir do Início.
- **N4 (P) — Biblioteca única.** Visão que junta tudo a partir do catálogo atual da TV (sem duplicar jogo com ROM e
  registro), filtros rápidos, painel de filtros, pulo por letra, Estatísticas e Sortear. Pronto: as antigas
  coleções Neste PC, Favoritos, Sistemas, Jogando, Ranking, ROMs leves/pesadas são alcançáveis como filtro; testes.
- **N5 (L) — Ficha do jogo como página.** Reaproveitar as ações atuais; ação principal por contexto; "⋯".
  Ferramentas também viram páginas (`#/ferramentas/<id>`). Pronto: nenhum `<dialog>` para ficha/ferramenta; só
  confirmações e teclado da busca continuam como diálogo.
- **N6 (L) — Mouse e teclado completos.** Hover, menu de contexto no botão direito, digitar para buscar, Ctrl+K,
  roda horizontal nas fileiras, botões 4/5 do mouse. Pronto: dá para usar tudo sem controle.
- **N7 (L) — Portar o que só a web faz.** Envio de dumps do Switch do Downloads (`/api/switch/upload*`) no Organizar;
  capa a partir de arquivo (`/api/cover/upload`, `/api/library/cover_upload`) no Capa; conferir que apagar
  save/state está coberto pela ficha. `/api/heavy/send` (adb) é obsoleto e não será portado.
- **N8 (L) — Desligar a entrada da web.** `/` redireciona para `/tv`; diagnóstico continua; tirar o "voltar à
  interface completa" do Menu; atualizar README e `docs/modo-tv.md`. Não apagar os arquivos ainda.
- **V1 (V)** — Uso real por 1–2 semanas no PC (mouse, Nova 2 Lite, Steam Link) e lista de atritos.
- **N9 (L) — Remover a web.** Depois do V1: apagar `index.html`, `app.js`, `style.css` e as rotas usadas só por
  eles; adaptar testes. Mudança no setup (links/atalhos que apontem para `/`) vai para o setup-linux-bonesi.

### Android

- **A1 (P) — Compose e casca nova.** Dependências do Compose, tema com a identidade atual, Activity com barra
  inferior/lateral e navegação com pilha. Telas antigas acessíveis durante a migração. Pronto: build, testes JVM,
  APK com versão nova.
- **A2 (P) — Início e Biblioteca únicos em Compose.** Neste celular, Catálogo, Sistemas, Favoritos e Ranking viram
  filtros; foco do controle com memória (G8/teclado de eventos `adb shell input gamepad keyevent`).
- **A3 (L) — Ficha do jogo em Compose**, com as mesmas ações e nomes do PC.
- **A4 (L) — Desejados, Stream, Situação/Opções em Compose**; remover as Views antigas da `MainActivity`.
- **V2 (V)** — Teste no celular com toque e com o G8.

Ordem: N1 → N8, V1, A1 → A4, V2, N9.

## Regras para a execução

- Testes: `python3 -m unittest discover -s tests` e `tests/test_app.html` pelo servidor; JVM e build pelo
  `tools/build_android.py` (ver README). Atualizar os testes que dependiam das coleções antigas.
- Antes de commitar: `git reflog` e `git diff --summary` (o Drive já regrediu refs e tirou `+x`).
- Reiniciar o `pyretro-gui` só com o modo TV fechado. `gui/static/*` não precisa de reinício.
- Não ler `library.json` nem `config.toml`; nada de endereço local, auditoria ou acervo no repositório (público).
- Registrar cada item no `docs/changelog.md` e marcar no Notion.

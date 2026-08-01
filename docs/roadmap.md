# Roadmap

Atualizado em 01/08/2026. Sequenciado por custo/dependência, não por
ordem de pedido - o que é rápido e sem dependência vem primeiro, o que
destrava outras coisas vem antes do que depende dele, e o que é
genuinamente caro fica marcado como tal em vez de subestimado.

## Feito

- **Fase 1 - GUI de capas**: galeria, busca com progresso ao vivo,
  fallback LaunchBox, layout mobile (menu de sistemas no topo, capas
  grandes em faixa horizontal).
- **Toque pra ampliar**: clicar numa capa da galeria abre em tela
  cheia (lightbox), fecha com toque fora ou Esc.
- **Tela de configuração de caminhos**: editor do `config.toml` pela
  GUI (`⚙ Configurações` no topo) - lê e grava só as chaves de
  caminho de `[pc]`/`[android]`, preservando o resto do arquivo
  (comentários, `[systems]`, `[cores]`) intacto.
- **Lista de fontes de capa alternativas**: pesquisa feita, ver
  [`docs/fontes_de_capas.md`](fontes_de_capas.md). ScreenScraper.fr é
  a recomendada como próxima fonte.
- **Correção manual de capa** (marcar errada + subir capa nova): botão
  "⚑ Errada" por capa (grava `flagged_wrong` no registry, some da
  lista de "resolvido"; "Desmarcar" reverte) + botão "⬆ Trocar" que
  sobe um arquivo novo direto pela interface (`status: manual`).
  Testado ponta a ponta com verificação de hash de arquivo.
- **Busca visual de capa alternativa**: botão "🔍 Buscar" por capa -
  busca por substring nas duas fontes já integradas (libretro-thumbnails
  + LaunchBox), mostra grid com a imagem real de cada candidato, um
  toque aplica direto. Isso cobriu na prática o que a "revisão visual
  de fuzzy match" ia fazer (ver item riscado abaixo), então esse item
  saiu do roadmap como redundante.

## Custo médio

Precisam de desenho novo (endpoint + tela), mas reaproveitam o que já
existe (`covers.py`, `launchbox.py`, o padrão de registry).

- ~~Revisão visual de fuzzy match~~ - coberto pela busca visual acima,
  que resolve o mesmo problema (escolher entre candidatos vendo a
  imagem) de forma mais direta (você escolhe o termo de busca, não
  fica limitado ao que o fuzzy match teria sugerido sozinho).
- **Integrar mais uma fonte de capa** (ex: ScreenScraper): o padrão já
  existe (`core/covers.py` + `core/launchbox.py` são os dois exemplos)
  - cada fonte nova é essencialmente repetir esse trabalho: entender o
    formato de resposta, mapear plataformas, cachear. Custo é por
    fonte, não um valor fixo - fontes com API key/conta (ScreenScraper,
    TheGamesDB) custam um pouco mais por causa do fluxo de
    autenticação. Não vale construir um "sistema de plugins" genérico
    agora - com 2-3 fontes reais, ainda é mais barato ter 2-3 módulos
    parecidos do que abstrair prematuramente.

## Custo médio-alto (mas destrava bastante coisa)

- **`core/adb.py` + `core/sync.py` de verdade**: retry/reconnect,
  manifesto de estado (`state.json`), detecção de conflito, sync de
  saves/states/métricas PC↔Android. Isso é o item que mais "paga a
  volta" - sem ele, nada de ROM/save/memory card aparece na GUI de
  jeito nenhum, porque a GUI só pode expor o que o backend sabe fazer.
  **Recomendo ser o próximo passo real**, antes dos itens de "custo
  alto" abaixo.

## Custo alto (merecem plano próprio antes de começar)

- **Upload de ROM + renomear com cascata** (renomear ROM já atualiza
  capa e save associados): ~~risco da playlist `.lpl`~~ - resolvido,
  o RetroArch reconstrói a playlist sozinho ao re-escanear a pasta,
  não precisamos tocar nela. Sobra só renomear ROM+capa+save/state
  juntos, bem mais simples do que eu tinha pensado. Ainda merece um
  desenho rápido (que arquivos contam como "associados" por sistema),
  mas não é mais "custo alto" de verdade - deveria ter descido pra
  "custo médio" na próxima revisão.
- **Editor de memory card PS1/PS2**: confirmado - vou procurar uma
  ferramenta open source já pronta (tipo MyMC pro PS2, ou uma lib
  Python de memcard PS1) pra envelopar em vez de reimplementar o
  parser binário do zero. Fica mais seguro que escrever isso na mão.
  Preciso pesquisar antes de estimar custo direito.

## Arquitetura de dois modos (confirmado, guia o design do `sync.py`)

`core/sync.py` vai ter dois modos de operação, não só um:
- **Modo PC**: roda no computador, fala com o celular via `adb` (é o
  que já existe hoje em espírito, mesmo não implementado).
- **Modo Android**: o próprio servidor rodando no aparelho (via
  Termux), operando direto na estrutura de arquivos local do Android -
  sem `adb` nenhum, porque já está rodando onde os arquivos estão.

Isso também responde o item "rodar tudo direto pelo celular": não é
uma feature separada, é o modo Android do mesmo `sync.py`. Vale
desenhar as duas interfaces (PC e Android) com essa divisão em mente
desde o início do `adb.py`/`sync.py`, pra não ter que retrofit depois.

## Ordem sugerida

1. Custo baixo (os 3 itens) - pode ser feito em qualquer ordem, são
   independentes entre si.
2. ~~Correção manual de capa + revisão visual de fuzzy match~~ - feito,
   a experiência de capas está fechada por enquanto.
3. `core/adb.py` + `core/sync.py` - o investimento estrutural que
   destrava o resto. **Próximo passo real.**
4. Só depois disso: upload/rename de ROM (já mais barato que parecia,
   ver acima) e o editor de memory card (esse continua exigindo
   pesquisa de ferramenta pronta antes de estimar direito). O modo
   Android do `sync.py` sai de graça junto do item 3, se o design já
   nascer pensando nos dois modos.

# Roadmap

Atualizado em 01/08/2026. Sequenciado por custo/dependência, não por
ordem de pedido - o que é rápido e sem dependência vem primeiro, o que
destrava outras coisas vem antes do que depende dele, e o que é
genuinamente caro fica marcado como tal em vez de subestimado.

## Feito

- **Fase 1 - GUI de capas**: galeria, busca com progresso ao vivo,
  fallback LaunchBox, layout mobile (menu de sistemas no topo, capas
  grandes em faixa horizontal).

## Custo baixo (próximo lote natural)

Pouca superfície nova, sem dependência de nada que ainda não existe.

- **Toque pra ampliar**: clicar numa capa da galeria abre em tela
  cheia. Só frontend.
- **Tela de configuração de caminhos**: editor do `config.toml` pela
  GUI (hoje é editar o TOML na mão). Formulário simples, ler/escrever
  o arquivo.
- **Lista de fontes de capa alternativas**: pesquisa que eu faço e te
  entrego pronta (não é código) - screenshot abaixo do porquê isso é
  "custo baixo": é trabalho de pesquisa, a parte cara é integrar cada
  fonte (ver mais abaixo).

## Custo médio

Precisam de desenho novo (endpoint + tela), mas reaproveitam o que já
existe (`covers.py`, `launchbox.py`, o padrão de registry).

- **Correção manual de capa** (marcar errada + subir capa nova): um
  botão "marcar como errada" por capa (grava no registry, tira da
  lista de "resolvido" pra poder tentar de novo depois) + upload de
  arquivo direto pela interface, salvando com o nome certo. As duas
  coisas compartilham a mesma tela/endpoint de "correção", faz sentido
  fazer juntas.
- **Revisão visual de fuzzy match**: candidata lado a lado com o nome
  local, aceitar/rejeitar com um toque. Troca os `.md` de baixa
  confiança por uma tela de verdade. Depende de eu persistir os
  candidatos fuzzy num lugar consultável (hoje só aparecem no log da
  rodada e somem) - pequeno ajuste no formato do registry antes de dar
  pra construir a tela.
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
  capa e save associados): a parte arriscada não é o upload em si, é a
  renomeação em cascata - precisa tocar no arquivo de ROM, na(s)
  capa(s), no(s) save(s)/state(s) **e** na entrada da playlist `.lpl`
  do RetroArch (que referencia o caminho/label específico). Errar isso
  pode órfão um save sem querer. Merece um desenho específico (que
  arquivos contam como "associados" por sistema, o que fazer se o
  save já teve conflito de sync) antes de eu escrever qualquer linha.
- **Editor de memory card PS1/PS2**: o formato binário desses cartões
  (blocos, checksums, ícones) é real - não é impossível, mas é o item
  de maior custo técnico do roadmap inteiro. Antes de reimplementar o
  parser do zero, vale eu pesquisar se dá pra **envelopar uma
  ferramenta já existente e testada** (tipo MyMC pro PS2, ou uma lib
  Python de memcard PS1) em vez de escrever o parser binário na mão -
  ficaria bem mais seguro. Preciso pesquisar isso antes de estimar
  custo direito.
- **Rodar tudo direto pelo celular**: preciso entender melhor o que
  isso significa na prática antes de estimar - "hospedar o servidor
  Python no Android via Termux" é uma coisa (viável pras telas de
  capas/galeria, que não dependem de `adb`); já operações que hoje
  dependem de `adb` (sync, por definição, fala PC↔Android) não fazem
  sentido rodando *dentro* do próprio Android alvo. Vale uma conversa
  rápida pra alinhar o que exatamente você imagina antes de eu
  arquitetar isso.

## Ordem sugerida

1. Custo baixo (os 3 itens) - pode ser feito em qualquer ordem, são
   independentes entre si.
2. Correção manual de capa + revisão visual de fuzzy match - fecham a
   experiência de capas por completo.
3. `core/adb.py` + `core/sync.py` - o investimento estrutural que
   destrava o resto.
4. Só depois disso: ROM management e memory card editor, cada um com
   seu próprio desenho antes de começar a codar. "Rodar pelo celular"
   entra quando tivermos alinhado o que significa.

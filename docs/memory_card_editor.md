# Pesquisa: editor de memory card PS1/PS2

Pesquisado em 02/08/2026, pra responder o item do roadmap "editor de
memory card PS1/PS2 - procurar ferramenta pronta em vez de reimplementar
o parser binário do zero".

## Recomendação: `bucanero/ps2vmc-tool`

https://github.com/bucanero/ps2vmc-tool

- **Linguagem/licença**: C, GNU GPLv3.
- **Cobre os dois consoles num projeto só**: inclui `ps2vmc-tool`
  (PlayStation 2) e `ps1vmc-tool` (PlayStation 1) - evita precisar de
  duas ferramentas separadas.
- **Manutenção**: moderada (23 commits na branch principal), com CI
  automatizado buildando pra macOS, Linux e Windows a cada release -
  release mais recente (v1.1.2) tem 6 assets disponíveis, sugerindo
  binário Linux pronto pra baixar (não confirmei 100% o conteúdo exato
  dos assets - a página de releases não carregou completa na pesquisa,
  vale conferir na hora de integrar).
- **CLI cobre o que precisa**: listar conteúdo do cartão, exportar save
  individual (formatos PSU/MCS/PSV/ARX/RAW), importar save (PSV/PSU),
  criar/remover diretório, formatar cartão, ver espaço disponível. O
  lado PS1 também tem visualizador de ícone.
- **Como envelopar**: mesma filosofia já usada no projeto pra
  `curl`/`convert` (ImageMagick) - baixar o binário pré-compilado (ou
  compilar da fonte se não tiver pra Linux) e chamar via `subprocess`,
  sem precisar reimplementar o parser binário do formato de memory
  card.

## Alternativas consideradas

- **`ps2dev/mymc`** (https://github.com/ps2dev/mymc) - Python, domínio
  público, só PS2. Seria a opção mais "nativa" pro projeto (poderia
  virar `import` direto em vez de subprocess), mas a própria doc se
  descreve como "alpha quality... sem testes extensivos" e tem só 6
  commits - risco maior de manutenção/confiabilidade que o
  `ps2vmc-tool`. Não cobre PS1 sozinho, precisaria de uma segunda
  ferramenta.
- **`PCSX2/myMCpp`** (https://github.com/PCSX2/myMCpp) - reescrita em
  C++ do mymc, mantida pela própria organização PCSX2 (bom sinal de
  confiabilidade), com GUI Qt + CLI. Só PS2. Boa opção se no futuro só
  PS2 importar e qualidade/suporte oficial pesar mais que cobrir os
  dois consoles num projeto só.
- **`ShendoXT/memcardrex`** (https://github.com/ShendoXT/memcardrex) -
  "Advanced PlayStation 1 Memory Card editor", C#/.NET, focado em GUI
  própria (Windows). Só PS1. Mais difícil de envelopar num projeto
  Python/Linux (dependência de .NET), e criaria a mesma necessidade de
  duas ferramentas separadas que o `ps2vmc-tool` já evita.

## Próximo passo (implementação, não pesquisa)

Não implementado ainda - fica pro próximo passo depois do
`ps2vmc-tool` ser baixado/compilado e testado manualmente contra um
save real da coleção (confirmar que lista/exporta/importa direito
antes de desenhar a integração com a GUI do PyRetro).

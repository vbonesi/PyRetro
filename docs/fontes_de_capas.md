# Fontes de capa alternativas (pesquisa de 01/08/2026)

Já integradas: **libretro-thumbnails** (`core/covers.py`) e **LaunchBox
Games DB** (`core/launchbox.py`), nenhuma das duas precisa de conta.
Isso aqui é o que mais vale considerar pra próxima fonte, em ordem de
recomendação.

## 1. ScreenScraper.fr — provavelmente a próxima certa

- **Conta**: precisa, gratuita, autenticação por usuário/senha (não é
  API key tradicional).
- **Limite grátis**: 20.000 requisições/dia - bem folgado.
- **Cobertura**: a maior e mais completa da comunidade retro - mais de
  180 mil jogos, várias mídias por jogo (capa, screenshot, vídeo,
  bezel, manual, cartucho). É provavelmente a fonte original por trás
  do Skraper (a ferramenta que você usava antes do PyRetro).
- **Por que é a recomendada**: cobre exatamente o buraco que sobrou -
  Arcade por nome de romset (registro central, muito usado por
  ferramentas de scraping) e os jogos mais nichados/japoneses que nem
  libretro-thumbnails nem LaunchBox pegaram.
- **Custo de integração**: médio - autenticação simples (usuário/senha
  na URL ou header), mas o formato de resposta é próprio deles, precisa
  mapear plataformas de novo (mesmo trabalho que fiz com LaunchBox).

## 2. TheGamesDB — alternativa mais simples, cobertura menor

- **Conta**: dá pra usar sem conta pra volume baixo; API key opcional
  (gratuita) pra aumentar o limite.
- **Limite grátis**: 3.000 requisições/mês sem chave - bem mais
  apertado que ScreenScraper, mas dá pra rodar em lotes espaçados.
- **Cobertura**: boa, mas menor que ScreenScraper e LaunchBox.
- **Quando faz sentido**: se ScreenScraper não cobrir algo específico,
  ou se você preferir não criar mais uma conta com senha.

## 3. IGDB (Twitch) — não recomendo pra esse uso

- **Conta**: precisa de conta de desenvolvedor Twitch + OAuth (mais
  burocrático que os outros dois).
- **Problema real**: não distingue bem versões por plataforma da
  mesma arte - pra ROM/retro isso é uma limitação chata (a capa que
  volta pode ser de outra versão/console do jogo).
- **Quando faz sentido**: praticamente nunca pro seu caso - é mais
  forte pra jogos modernos multi-plataforma do que pra retro.

## 4. Progetto SNAPS / arcade-history.com — só Arcade, sem conta

- Especializado em MAME/Arcade (flyers, cabinets, marquees), indexado
  por nome de romset como o DAT do FBNeo que já uso.
- Sem login pra uso básico.
- **Quando faz sentido**: só se ScreenScraper não resolver 100% do
  Arcade que sobrou (hoje já está 100% resolvido, então isso é baixa
  prioridade - guardar como plano B).

## Descartado

- **MobyGames**: bloqueou scraping direto (403) quando tentei buscar
  capas pontuais antes - teria que ser via API oficial deles, que é
  paga pra uso continuado.

## Recomendação prática

Se for integrar mais uma fonte, **ScreenScraper primeiro** - é o
maior salto de cobertura pelo menor custo de conta (só usuário/senha,
sem OAuth). Cria a conta quando quiser seguir com isso e me passa
usuário/senha (ou credencial equivalente) pra eu integrar.

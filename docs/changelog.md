# Changelog

Histórico detalhado do que foi feito, quando, e por quê - bugs achados,
testes realizados, decisões de desenho e o raciocínio por trás delas.
Pra "o que está pronto hoje" e "o que vem a seguir", ver
[`docs/roadmap.md`](roadmap.md) - este arquivo é o registro, não o
plano.

## Fase inicial (antes de 01/08/2026)

- **Fase 1 - GUI de capas**: galeria, busca com progresso ao vivo,
  fallback LaunchBox, layout mobile (menu de sistemas no topo).
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
  toque aplica direto. Cobriu na prática o que a "revisão visual de
  fuzzy match" ia fazer, então esse item saiu do roadmap como
  redundante.

## 01-02/08/2026

- **`core/adb.py` + `core/sync.py` (capas)**: implementado e **testado
  contra o aparelho real**. Achado no primeiro teste: `find -exec stat`
  funciona bem no toybox do S24 Ultra, mas o USB reconectou sozinho no
  meio (transport_id mudou) e o adb passou a devolver "error: device
  '<serial>' not found" - frase que `_OFFLINE_MARKERS` não reconhecia,
  então o retry não disparava. Corrigido (adicionado "not found" à
  lista de marcadores). Depois do fix: sync rodou de ponta a ponta,
  mtime dos dois lados comparado certo. Como era a primeira
  sincronização de sempre (sem manifesto anterior), tudo que já
  existia dos dois lados com mtime diferente virou "conflito" por
  precaução (53 capas) - resolvidos manualmente como "PC vence" (fonte
  da verdade essa noite, já que tudo foi editado por aqui) num script
  pontual, não uma mudança na regra padrão do `sync.py`. CLI:
  `retrosync sync covers [--apply]`.
- **Bug achado durante o teste real: `convert-covers` deixava `.jpg`
  órfão pra trás** quando o `.png` já existia (`covers.py`, função
  `convert_jpg_to_png`) - reportava "png_ja_existe" mas nunca apagava o
  `.jpg`. Corrigido (agora remove o `.jpg` órfão em vez de só
  reportar). 16 arquivos limpos no PC e replicado manualmente no
  celular (que tinha recebido esse lixo via push antes do fix).
- **Marcar capa pra renomear** (botão "✎ Renomear"): renomeia só o
  arquivo da capa e grava `status: renamed_pending` + `old_label` no
  registry - servia de lista do que faltava ajustar antes do rename
  com cascata existir (ver 04/08 abaixo). Badge azul "✎ renomeada" na
  galeria.
- **Marcar capa como duplicada** (botão "⧉ Duplicada"): grava
  `status: duplicate` no registry, badge laranja + filtro combinável
  "⧉ Só duplicadas". Não apaga nada sozinho - só sinaliza que capa+ROM
  precisam ser removidas manualmente depois.
- **Renomear/duplicada aplicadas nas ROMs**: `~/Drive/Jogos/aplicar_pendencias.sh`
  (fora do repo, script solto) lê `duplicate`/`renamed_pending` do
  registry e aplica na ROM correspondente. Rodado de verdade em 02/08 -
  35 duplicadas + 22 renomeações processadas com sucesso.
- **Sync de capas/ROM via adb - despriorizado pros sistemas "leves"**:
  o celular passou a sincronizar a pasta de Jogos direto com o Google
  Drive, então ROMs+capas dos sistemas que sempre ficam baixados
  propagam sozinhos - não precisa mais rodar `retrosync sync covers`
  nem o `aplicar_pendencias.sh` tocar no celular via adb pra esse caso
  (script simplificado pra só PC). `core/adb.py`/`core/sync.py`
  continuam existindo, testados, prontos pra quando entrar gestão de
  ROM dos consoles pesados.
- **Bug real: `.png` com bytes JPEG dentro** (achado via captura de
  tela mostrando capa sem aparecer no RetroArch mesmo com o arquivo no
  lugar certo): 5 capas da coleção tinham conteúdo JPEG salvo com
  extensão `.png` - RetroArch não mostra erro, só fica com o ícone
  genérico pra sempre. Causa: três pontos do código decidiam se
  precisavam converter olhando a EXTENSÃO declarada em vez do conteúdo
  real. Corrigido nos três (`gui/server.py` upload e
  `download_selected_cover`, `core/launchbox.py` `download_cover`) -
  agora sempre passam pelo `convert` do ImageMagick, que detecta o
  formato pelo conteúdo. Varredura na coleção inteira (1674 PNGs)
  confirmou só esses 5, todos corrigidos no lugar sem perda de imagem.
  Novo comando `retrosync validate-covers <sistema|all> [--apply]` pra
  detectar isso de novo no futuro.
- **Mapeamento de sistemas do ScreenScraper** (`core/screenscraper.py`,
  `SYSTEM_MAP`): as 18 plataformas do config.toml cruzadas contra o
  `systemeid` do ScreenScraper (via `systemesListe.php`, que ainda
  aceita o devid/devpassword placeholder). Achado incidentalmente: 3
  não batiam por cross-reference automático de nome (PCECD, NEOGEO -
  nome ligeiramente diferente do usado no LaunchBox; ARCADE - o
  ScreenScraper não tem um id único de arcade, usa o bucket genérico
  "Mame", id 75) e entraram como override manual. **ScreenScraper em
  si ficou bloqueado**: `jeuRecherche.php`/`jeuInfos.php` (os dois
  endpoints que realmente importam) recusam o devid/devpassword
  placeholder (`xxx`/`yyy`) com "Erreur de login : Vérifier vos
  identifiants développeur !" (HTTP 403) - mudança em relação ao que
  parecia funcionar mais cedo na mesma sessão. Só `systemesListe.php`
  continua aceitando o placeholder. Pedido de credencial real enviado
  no fórum deles, aguardando resposta.

## 04/08/2026

- **Gestão de ROMs pesadas (PS, SDC, PS2, GameCube, Wii, PSP, 3DS)**:
  `core/heavy_roms.py` + rotas na GUI (`📦 ROMs Pesadas`) + CLI
  (`retrosync heavy-roms <CODIGO> [--send NOME] [--overwrite]`).
  Nintendo Switch ficou de fora de propósito, gestão feita por fora do
  PyRetro. Achado real: PS/SDC usam `.cue`/`.gdi` + `.bin` separado
  (inclusive multi-track, tipo "Sonic Adventure (Track 1/2/3).bin") -
  `list_local` soma o tamanho dos sidecars no item, `send_to_phone`
  manda todos juntos. Testado ponta a ponta com o aparelho real - envio
  de 1MB de teste chegou intacto (byte a byte) no celular, progresso
  via SSE funcionando. Achado no teste: `send_to_phone` ganhou um
  parâmetro novo (`exts`, pros sidecars) e as duas chamadas (CLI e GUI)
  não foram atualizadas junto - corrigido (erro claro de `TypeError`,
  não silencioso).
- **Renomear com cascata (ROM + save/state, sistemas leves E pesados)**:
  `core/rom_rename.py` - o botão "✎ Renomear" da galeria de capas agora
  tenta renomear a ROM e qualquer save/state correspondente na mesma
  hora. Se a ROM não for encontrada, tiver mais de uma batendo, ou já
  existir uma com o nome novo, a capa ainda é renomeada mas cai no
  fallback antigo (`renamed_pending` no registry). Sistemas pesados
  ganharam o mesmo botão dentro do modal de ROMs Pesadas. Achado
  importante: PS/SDC guardam o nome do `.bin` dentro do texto do
  `.cue`/`.gdi` (`FILE "nome.bin" BINARY`) - só renomear o arquivo sem
  corrigir essa referência quebra o jogo. Criado `core/cues.py`
  (`rename_disc_set`) especificamente pra isso - testado com `.cue`
  single-track e `.gdi` multi-track, incluindo teste de conflito
  (nunca sobrescreve, nunca faz rename parcial). Save/state: RetroArch
  guarda tudo achatado (sem subpasta por sistema) - troca qualquer
  arquivo que bata exato com o label antigo; sistemas com save
  gerenciado por emulador standalone (PS1/SDC via DuckStation/Flycast)
  simplesmente não têm arquivo nesse padrão, então não acontece nada -
  comportamento correto sem precisar de tratamento especial.
- **Multi-disco (PS1/PS2, ex: "Jogo (Disc 1)/(Disc 2)/(Disc 3)")**:
  lacuna real apontada pelo usuário depois da primeira versão do rename
  com cascata - a versão inicial só agrupava múltiplas *tracks* dentro
  de UM disco, não múltiplos *discos* do mesmo jogo. Corrigido: se o
  label antigo termina em " (Disc N)", `core/rom_rename.py` acha os
  outros discos do mesmo título base e renomeia o grupo inteiro junto
  (cada um preservando seu próprio "(Disc N)"), com passe de dry-run em
  todos antes de aplicar em qualquer um - se um disco colidir, nenhum é
  tocado. Testado com 3 discos fictícios (rename bem-sucedido
  preservando cada `.cue`↔`.bin` corretamente, e conflito no meio do
  grupo abortando todos). Sem exemplo real na coleção atual pra validar
  contra um jogo de verdade ainda.
- **Upload de ROM vira a pasta "0-Organizar"**: `core/organize.py` +
  botão "🗂 Organizar" na GUI + `retrosync organize` (só lista, mover é
  só pela GUI). Design do usuário: `roms_root/0-Organizar/` (nome
  configurável em `config.toml` `[pc]` `organizar_dir`, editável direto
  na tela de Configurações - a chave já é genérica, não precisou de
  código novo pra isso) recebe o arquivo de qualquer lado (o "upload" É
  o Google Drive agora, sem precisar HTTP upload de ROM de vários GB),
  e o PyRetro identifica o sistema pela extensão. Muitas extensões são
  ambíguas entre sistemas (mapeado de verdade: 20 de 36 extensões
  configuradas batem em mais de um sistema) - não decide sozinho,
  mostra os candidatos num dropdown. Achado durante o desenho: PS e SDC
  estão configurados tanto em `[systems]` quanto em `[heavy_systems]`
  (mesmo código, destino igual) - o índice de extensões deduplicava
  errado e mostrava a mesma opção duas vezes no dropdown, corrigido
  (dedup por código). Testado ponta a ponta via GUI real com arquivo
  descartável, incluindo o caso ambíguo.
- **Dificuldade do editor de memory card - validada, não só
  pesquisada**: baixei o binário Ubuntu do `ps2vmc-tool` recomendado
  (311KB, sem precisar compilar) e testei de verdade contra os memory
  cards reais da coleção (`Saves/PS2/memcards/*.ps2`,
  `Saves/PS1-DuckStation/memcards/*.mcd`) - rodou de primeira, sem erro
  de biblioteca faltando, leu corretamente os saves reais (nomes de
  jogo por código de produto tipo BASLUS-21672). Dificuldade baixa pra
  uma integração básica (listar/info/extrair/injetar via subprocess,
  mesmo padrão já usado com `curl`/`convert`) - desceu de "custo alto"
  pra algo bem mais tratável.
- **Galeria e busca: rolagem vertical em vez de horizontal** (pedido
  pelo usuário, tanto Android quanto PC): `.gallery-strip` virou CSS
  grid (`repeat(auto-fill, minmax(220px, 1fr))`, várias colunas no PC,
  uma no celular) com rolagem vertical. Busca visual corrigida
  (`.search-result img` usava `object-fit: cover`, que corta a
  imagem - trocado pra `contain`). **Bug real de navegador achado e
  isolado durante o teste**: com centenas de linhas `auto` numa CSS
  grid contendo `aspect-ratio` (a galeria tem ~200-300 capas por
  sistema), o Chromium degenera a altura da linha pra ~0px -
  reproduzido isolado fora do projeto (não é bug do nosso CSS), some a
  partir de dezenas de linhas. Corrigido com um piso mínimo
  (`grid-auto-rows: minmax(480px, auto)`), testado em desktop (3
  colunas) e mobile (1 coluna), sem scroll horizontal nos dois.
- **`sync.py` pra saves/states/runtime-logs - cancelado** a pedido do
  usuário: sempre vai usar um sistema de nuvem (Google Drive) pra isso,
  não faz sentido manter/testar um caminho paralelo via adb que nunca
  vai ser usado no dia a dia.
- **Pesquisa: rclone como solução pra "ROMs pesadas via Drive sem
  adb"** - sugestão do usuário, validada: `rclone config` faz OAuth uma
  vez, depois `rclone lsjson gdrive:...` lista o Drive via API sem
  precisar montar nada (`rclone mount` seria outra coisa, exigiria
  FUSE). Mesmo padrão de "envelopar ferramenta externa" já usado no
  projeto. Implementação começando - usuário configurando `rclone
  config` (passo interativo, precisa da conta Google dele).
- **Passo a passo de instalação no Termux escrito**
  ([`docs/termux_setup.md`](termux_setup.md)) - ainda não testado
  contra o aparelho real.

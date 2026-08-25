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
- **Apagar com cascata** (ROM + capa + save/state numa ação só):
  `delete_with_cascade` em `core/rom_rename.py`, botão "🗑 Apagar" na
  galeria de capas e no modal de ROMs Pesadas, sempre com confirmação
  (ação irreversível). De propósito NÃO agrupa discos múltiplos como o
  rename faz - apagar "Jogo (Disc 2)" nunca apaga o Disc 1/3 do mesmo
  jogo (rename agrupar faz sentido pra manter nomes consistentes,
  apagar agrupar seria perigoso demais). Testado com dados descartáveis
  incluindo o caso `.cue`+`.bin` e o caso multi-disco (confirmado que
  só o disco alvo some).
- **`rclone` implementado e testado com dados reais**: remote
  configurado pelo usuário como `drive` (não `gdrive` como eu tinha
  sugerido - corrigido no código pra usar o nome real). `core/heavy_
  roms.py` ganhou `list_drive_items` (lista o catálogo completo do
  Google Drive via `rclone lsjson`, sem depender de adb/celular
  conectado) e `download_from_drive`. Achado real no primeiro teste:
  o PS2 tem **97 jogos no Drive contra só 3 baixados localmente** -
  a listagem une os dois lados numa visão só (local/Drive/celular).
  Restrição importante trazida pelo usuário: no PC, o download NUNCA
  vai direto pra `roms_root/<CODIGO>/` (que é a própria pasta
  sincronizada pelo Google Drive Desktop - escrever ali enquanto o
  rclone baixa arriscaria os dois mexerem no mesmo arquivo ao mesmo
  tempo) - baixa primeiro em `staging_dir` (`~/Downloads` por padrão,
  configurável em `[rclone]`) e só move pro lugar certo depois que o
  download termina por completo. Testado com download real de 439MB
  ("Dynasty Warriors 2.chd") - chegou com o tamanho exato, moveu certo,
  nada sobrou no staging. Bug real achado no meio do caminho: `rclone
  lsjson` pro PS2 (97 itens) levou até 54s pra responder via API do
  Drive, estourando o timeout de 30s que eu tinha posto - o código
  tratava timeout como "vazio" silenciosamente, fazendo parecer que não
  tinha nada no Drive quando só estava demorando. Corrigido (timeout
  90s). GUI: modal de ROMs Pesadas agora mostra itens que existem só no
  Drive (com botão "⬇ Baixar do Drive") e um selo "☁ no Drive" nos que
  já são locais - testado ponta a ponta incluindo o fluxo de erro
  (clique → job → SSE → mensagem de erro exibida corretamente).
- **ScreenScraper implementado e testado com a API real**: usuário
  conseguiu conta de desenvolvedor (devid/devpassword), o que
  destravou `jeuRecherche.php`/`jeuInfos.php` (os placeholders xxx/yyy
  tinham parado de funcionar pra esses dois endpoints, ver entrada de
  01-02/08). `core/screenscraper.py` reescrito: `search_game` busca
  por nome dentro do `systemeid` do sistema (mapeado em `SYSTEM_MAP`,
  cruzando `nom_launchbox` do `systemesListe.php` com
  `launchbox_mod.PLATFORM_MAP` - com dois overrides manuais pra PCECD e
  NEOGEO onde o texto diverge entre as duas fontes, e ARCADE fixado no
  id genérico "Mame" já que o ScreenScraper não tem um id único por
  núcleo/placa). **Cuidado de segurança**: as URLs de mídia que a API
  devolve já vêm com devid/devpassword/ssid/sspassword embutidos como
  parâmetro de URL - por isso nunca são repassadas pro navegador.
  Solução: cache em memória por processo em `gui/server.py`
  (`_ss_media_cache`, nunca gravado em disco) guarda a URL real por
  `code:id` durante a busca, e uma rota nova `GET
  /api/cover/ss_preview?code=&id=` busca a imagem no backend e
  devolve só os bytes pro cliente, com Content-Type detectado pelos
  magic bytes (PNG vs JPEG - mesma lição de não confiar em extensão
  declarada). `POST /api/cover/select` ganhou um branch pra
  `source == "screenscraper"`. Testado ao vivo contra a API de
  produção com a credencial real do usuário: busca por "Chrono
  Trigger" no SFC devolveu 5 resultados reais, download do primeiro
  produziu um PNG de capa correto (680×497, conferido visualmente).
  Testado também o fluxo completo pela GUI (clique num card de
  resultado ScreenScraper na busca → capa aplicada no disco), sem
  vazar a URL com credenciais pro cliente em nenhum momento (conferido
  via network tab). Artefatos de teste (`ZZZ_TESTE_SS*`) limpos do
  disco e do registry depois.

## 05/08/2026

- **Bug real achado e corrigido: busca de capa travando
  "infinitamente"** - reportado pelo usuário logo depois do
  ScreenScraper entrar no ar. Causa raiz: quando a API do
  ScreenScraper aceita a conexão mas demora mais que o timeout de
  leitura (comum sob carga, sobretudo em conta de dev gratuita), o
  Python levanta `socket.timeout`/`TimeoutError` - que NÃO é subclasse
  de `urllib.error.URLError`, então o `except (URLError, ValueError)`
  em `search_game`/`fetch_media_bytes` (`core/screenscraper.py`) não
  pegava. A exceção vazava, derrubava a thread da request no servidor
  sem nunca mandar resposta - e como `runSearch`/`selectCandidate` no
  `gui/static/app.js` não tinham `try/catch`, a tela ficava presa em
  "buscando..."/"aplicando..." pra sempre, sem erro visível nenhum.
  Corrigido nos dois lados: backend captura `OSError` (cobre
  `URLError` E `TimeoutError` de uma vez, já que `URLError` também é
  subclasse de `OSError`); frontend ganhou `try/catch` + timeout de
  30s via `AbortController`, mostrando mensagem de erro em vez de
  travar. Reproduzido e confirmado antes/depois com um
  `socket.timeout` simulado via monkeypatch, e testado ao vivo no
  navegador (fetch forçado a falhar → mensagem de erro aparece em vez
  de travar; busca normal continua funcionando igual).

- **Editor de memory card PS1/PS2 implementado** (item do roadmap,
  dificuldade já validada como baixa em 02/08) - ver
  [`docs/memory_card_editor.md`](memory_card_editor.md) pros detalhes
  completos. Resumo: `core/memcard.py` envelopa `ps1vmc-tool`/
  `ps2vmc-tool` via subprocess (binários instalados em `~/.local/bin`);
  nova aba "💾 Saves" na GUI lista o conteúdo de cada cartão
  configurado em `config.toml [memcards]` e exporta save individual
  pra `export_dir` (padrão `~/Downloads`).

  Pedido extra do usuário no meio da conversa: "seria bom uma aba SAVE
  ... pra verificar os que são individualizados" - só listar o
  conteúdo cru do cartão não bastava, porque um memory card guarda
  save só pelo SERIAL do disco (pasta "BASLUS-21672" no PS2, slot
  "BASCUS-9424400000000" no PS1), não pelo nome do jogo. Resolvido
  criando `core/serials.py`, que baixa e cacheia os DATs de **redump**
  do `libretro/libretro-database` (`metadat/redump/Sony -
  PlayStation{,  2}.dat` - já tem o campo `serial` no nível do jogo,
  não só por ROM/track) e cruza serial normalizado → nome. Achado no
  caminho: o DAT de **serial** puro do libretro-database (pasta
  `metadat/serial/`) não cobre PS1/PS2 (só consoles mais antigos) -
  por isso a escolha pelo DAT de redump em vez dele.

  Testado ponta a ponta contra os cartões reais do usuário
  (`~/Drive/Jogos/Saves/PS1-DuckStation/memcards/` e
  `~/Drive/Jogos/Saves/PS2/memcards/`): os 7 slots do PS1 (Crash
  Bandicoot - Warped, Gran Turismo 2 x2, Yu-Gi-Oh! Forbidden Memories,
  Jeremy McGrath Supercross 2000, Driver x2) e as 2 pastas do PS2
  (Guitar Hero III, Need for Speed Underground 2) resolveram certo pro
  nome do jogo; exportação real confirmada nos dois formatos (.mcs de
  8320 bytes no PS1, .psu de 330240 bytes no PS2), inclusive pelo
  clique de verdade no botão "⬇ Exportar" da GUI. Bug pequeno achado
  durante o teste na GUI: o campo "size" que o `-ls` do PS2 devolve
  pra uma pasta é a CONTAGEM de arquivos dentro dela, não bytes (só o
  PS1 devolve tamanho real do save) - mostrar isso como "0 KB"
  (dividindo por 1024) era enganoso; corrigido pra mostrar "N
  arquivos" quando o item é uma pasta.

  Fora de escopo por ora: importar/injetar save de volta no cartão -
  a v1 cobre só visualização + exportação, que já resolve o pedido
  original de "verificar quais são individualizados".
- **Editor de memory card v2**: usuário pediu importar/apagar/
  transferir save entre cards, e apontou que a badge "individualizado"
  da v1 estava enganosa. Corrigido: a badge media só se o NOME foi
  resolvido via serial, não se o save é um arquivo próprio (TODO save
  de PS1/PS2 vive dentro de um card compartilhado, nunca é
  "individualizado" de verdade) - renomeada pra "nome identificado"/
  "serial desconhecido". `core/memcard.py` ganhou `delete_save`,
  `import_save`, `transfer_save`. Achados reais testando contra cópias
  descartáveis dos cartões do usuário:
  - Os binários às vezes devolvem **returncode 0 mesmo imprimindo uma
    linha "Error: ..."** (ex: `-in` recusando por falta de espaço,
    `-pu` avisando que o diretório já existe mas sobrescrevendo mesmo
    assim) - `_run()` agora também escaneia a saída por "Error:" em
    vez de confiar só no returncode, senão essas falhas passavam
    batido como sucesso.
  - PS2 `-rm` não remove um diretório não-vazio direto (erro "-6") -
    `delete_save` esvazia (lista + remove cada arquivo) antes de
    `-rmdir`.
  - Hipótese inicial errada: achei que reimportar o MESMO jogo era
    bloqueado por duplicação - na verdade real hardware de PS1 permite
    duplicar, o bloqueio real era falta de espaço CONTÍGUO (um save de
    4 blocos não cabe com só 1 slot livre). Mensagem de erro corrigida
    pra falar em espaço, não em duplicação.
  - "Transferir" tinha virar "copiar" (export+import sem apagar a
    origem) até o usuário notar - corrigido pra mover de verdade
    (`transfer_save` só apaga a origem DEPOIS do import ter sucesso,
    pra nunca ficar sem nenhuma cópia se o import falhar no meio).
  - Bug de case: `card.key` vem em minúsculo ("ps1:Slot 1") mas
    `card.console` vem em maiúsculo ("PS1") - o filtro de "outros
    cards do mesmo console" no botão Transferir comparava os dois
    direto e nunca achava nada. Corrigido com `.toUpperCase()`.
  - Bug de nome de arquivo temporário: o endpoint de import montava o
    nome como `<card>.import<ext>.tmp` - como quem decide o formato é
    a ÚLTIMA extensão do nome (`Path.suffix`), isso fazia o código ler
    ".tmp" como formato em vez de ".mcs"/".psu". Corrigido pra
    `<card>.import.tmp<ext>`.
  - Aba reorganizada a pedido do usuário: PS1 e PS2 juntos na mesma
    tela (antes eram 4 abas separadas, uma por card - agora é uma
    seção por console, uma subseção por card, sem precisar trocar de
    aba pra comparar).
  Todo teste destrutivo (apagar/importar/transferir) rodou contra
  cópias descartáveis dos 4 cartões reais do usuário, nunca os
  arquivos de verdade - conferido hash antes/depois de cada sessão de
  teste pra garantir que os originais não foram tocados.
- **Gestão de save/state por jogo na galeria de capas**: pedido do
  usuário - cada capa agora mostra badges "💾 Save"/"⏱ State" quando o
  jogo tem arquivo correspondente em `saves_root`/`states_root`
  (convenção achatada do RetroArch, mesma comparação por prefixo
  exato - nunca glob - já usada em `rename_with_cascade`). Clicar
  apaga só aquele save/state (não a ROM/capa). No backend, em vez de
  escanear `saves_root`/`states_root` inteiro pra CADA capa da galeria
  (lento com centenas de capas), lista as duas pastas uma vez só e usa
  busca binária (`bisect`) pra checar o prefixo - O(log n) por capa em
  vez de O(n). Refatorado `core/rom_rename.py`: `_delete_flat_matches`
  virou público (`delete_flat_matches`) e ganhou uma versão só-leitura
  (`find_flat_matches`), reaproveitados tanto pela galeria quanto pelo
  apagar-com-cascata que já existia. Testado ao vivo: badge aparece
  certo pra "Daytona USA" (Saturn, tem save E state reais), apagar o
  save some só com o botão de save (state continua), arquivos restaurados
  do backup depois do teste.
- **Busca de capa por fonte**: usuário pediu um botão de fallback em
  massa por fonte, igual o "Buscar no LaunchBox" que já existia -
  criado "🔍 Buscar no ScreenScraper" ao lado. `core/screenscraper.py`
  ganhou `process_system_fallback` (mesmo papel do equivalente em
  `launchbox.py`: segunda passada só nos `no_match`, usa o label como
  termo de busca, primeiro resultado da API). Backend trocou o
  parâmetro `fallback` de booleano pra string ("launchbox"/
  "screenscraper"/vazio), pra caber uma terceira fonte sem duplicar
  rota. Testado ao vivo com um caso real: marcou "ActRaiser" (SFC)
  como `no_match` temporariamente no registry, rodou o fallback em
  modo simulação (sem aplicar) e confirmou "found:1" - restaurou o
  registry original depois.
- **Bug real corrigido: capa cortada no modal de busca** - usuário
  reportou "corta um bom pedaço" ao ver a prévia na busca. Mesma causa
  raiz do bug de `.gallery-strip` documentado acima (Chromium degenera
  a altura de linhas `grid-auto-rows: auto` com filhos de
  `aspect-ratio` quando tem dezenas de linhas), só que dessa vez em
  `.search-results` - que nunca tinha recebido o mesmo piso mínimo.
  Reproduzido e confirmado isolado: com `minmax(50px, auto)` a altura
  real da linha colapsava pra ~82px contra os ~245px que o conteúdo
  precisa (17 resultados já bastam pra disparar, não precisa de
  "dezenas" nesse container mais estreito) - a imagem de 209px ficava
  cortada quase pela metade. Corrigido com `grid-auto-rows: minmax(260px,
  auto)`, testado com 40 resultados (o máximo) sem nenhum corte.
- **Esconder menus superiores**: botão fixo (⌃/⌄, sempre visível
  independente do estado) esconde/mostra topbar+menubar+filterbar de
  uma vez, preferência salva em `localStorage` (sobrevive a reload).
- **Investigação real no aparelho: saves do Flycast/Dolphin/PPSSPP/
  3DS** - usuário pediu mapear a estrutura de save de cada emulador
  fora do RetroArch, pra decidir se/como estender o backup pra eles.
  Celular reconectado via adb (`RQCY207RB4N`) e explorado direto:
  - Dolphin (GameCube) e PPSSPP já guardam save individualizado por
    jogo nativamente (arquivo `.gci` e pasta `SAVEDATA/<serial>`,
    respectivamente) - encaixariam fácil no mesmo padrão do memory
    card PS1/PS2.
  - Flycast usa VMU compartilhado (mesmo problema estrutural do PS1/
    PS2, mas sem tool tipo `ps2vmc-tool` pronta pra esse formato).
  - Dolphin (Wii) e 3DS usam estrutura tipo NAND por title-ID
    hexadecimal - bem mais caro de implementar (título não vem
    legível sem cruzar com base externa).
  - App de 3DS instalado é **Lime3DS**, não "Azahar" (nome que o
    usuário mencionou) - mesma família de fork do Citra, mas outro
    projeto/pacote.
  Detalhes completos em [`docs/roadmap.md`](roadmap.md). Decisão de
  escopo/ordem de implementação ainda pendente com o usuário -
  registrado como próximo passo, nada implementado ainda pra esses
  quatro emuladores.
- **Backup de saves do Dolphin(GameCube)/PPSSPP implementado** -
  usuário escolheu começar só pelos dois fáceis (Flycast/Wii/3DS
  ficaram de fora por decisão dele, custo maior). `core/serials.py`
  ganhou os DATs de redump do GameCube e do PSP (`DAT_URLS["GC"]`/
  `["PSP"]`) - o GC tem um formato de serial diferente dos outros
  três, "DL-DOL-\<CODE\>-\<REGIÃO\>" em vez do serial direto, por isso
  ganhou um parser próprio (`_parse_gc_dat`) que extrai só o \<CODE\>
  de 4 caracteres (bate com o que aparece no nome real do `.gci`, tipo
  "70-GBTE-bayblade2002.gci" -> "GBTE"). `core/emu_saves.py` novo,
  lista via adb + resolve nome via serial + puxa (`adb pull`) o que
  falta.

  Achado real explorando `~/Drive/Jogos/Saves/` no PC antes de decidir
  a estrutura de pastas: o usuário **já mantém manualmente**
  `Saves/Dolphin/` e `Saves/PPSSPP/` como espelho 1:1 da pasta de
  dados de cada app no celular (`Dolphin/GC/<REGIÃO>/Card X/*.gci`,
  `PPSSPP/SAVEDATA/<serial>/`) - `emu_saves.py` adota exatamente essa
  mesma estrutura (preserva o caminho relativo do celular ao puxar) em
  vez de inventar uma pasta nova, pra não duplicar convenção.

  Testado ponta a ponta contra o aparelho real (reconectou duas vezes
  no meio do trabalho, adb caiu sozinho entre uma investigação e
  outra): `list_remote`/`list_local`/`pull_item` confirmados pros dois
  emuladores, incluindo puxar uma pasta INTEIRA de save do PSP (3
  arquivos dentro - `DISSIDIA.BIN`/`ICON0.PNG`/`PARAM.SFO`) num só
  `adb pull` (pasta remota puxa recursivo por padrão). GUI: aba
  "💾 Saves" ganhou duas seções novas (Dolphin-GameCube, PPSSPP) depois
  das de PS1/PS2 - lista os itens do celular com nome resolvido,
  badge "no PC"/"só no celular" e botão "⬇ Baixar do celular" pros que
  faltam. Testado clicando o botão de verdade na GUI (não só via
  script) - arquivo `.gci` real baixado no lugar certo, badge virou
  "no PC" na hora. Artefatos de teste (pull manual antes de existir a
  rota, e o clique de teste na GUI) limpos do disco depois de cada
  verificação, sempre restaurando o estado vazio original da pasta.
- **Rodada de ajustes testando no celular de verdade** (usuário mandou
  screenshot do mobile) - achados reais:
  - **Bug real: ações da capa "sumindo" no celular** - o piso fixo em
    px do `grid-auto-rows` (documentado acima, pensado pro desktop)
    era pequeno demais numa coluna só de mobile, onde a imagem sozinha
    já passa da altura do piso - resultado: os botões de ação ficavam
    cortados fora do card, invisíveis. Resolvido de vez (não só mais
    um ajuste de número): trocado `.gallery-strip` e `.search-results`
    de CSS Grid pra **flexbox com wrap** - flexbox não tem esse bug do
    Chromium (cada item cresce pro próprio conteúdo, sem track de
    linha compartilhado calculado errado), elimina a classe inteira do
    problema em vez de só mais um piso mágico em px. Também virou
    pedido explícito do usuário: 2 colunas no celular (antes 1,
    imagem enorme) - `flex-basis: calc(50% - Npx)` num media query.
  - **Bug real: topbar cortado/sobreposto no celular** - `.topbar-row`
    sem `flex-wrap` deixava os 4 botões overflowarem pra fora da tela
    (texto "Configurações" cortado na borda, sem scroll horizontal
    porque `body` tem `overflow: hidden`). Corrigido com
    `flex-wrap: wrap` no título+botões. O botão de esconder menu
    (⌃/⌄, `position: fixed; top: 4px`) ficava sobreposto ao primeiro
    botão que agora quebrava linha logo abaixo do título - corrigido
    reservando uma faixa própria pra ele via `padding-top` extra no
    `.topbar`, testado medindo a posição real dos elementos (toggle
    em y:4-22, título em y:26+, sem overlap).
  - Fundo preto puro (`#000`) atrás de capas com proporção diferente
    de 3:4 (letterbox do `object-fit: contain`) parecia um corte de
    verdade - trocado pra `var(--bg-panel)`, mais suave e consistente
    com o tema (inclusive no modo claro).
  - "Aplicar de verdade" → "Aplicar" (texto do checkbox).
  - Aba "💾 Saves" ganhou navegação por aba de novo (PS1/PS2/GameCube/
    PPSSPP, `<nav class="system-tabs">` igual o resto do app) em vez
    de uma rolagem única longa com as 4 seções empilhadas - mantém a
    separação por card dentro de PS1/PS2 (pedido anterior), só que
    agora escolhida por clique em vez de scroll, bem mais usável no
    celular.
  - 3DS e Wii seguem de propósito fora do escopo (backup manual do
    usuário) - confirmado de novo, nenhuma mudança de código.
  Testado inteiramente via geometria real (`getBoundingClientRect`)
  simulando mobile (375×812) e desktop (1280×800) no mesmo navegador -
  a Browser pane deste ambiente não composita frames pra screenshot,
  então a verificação foi feita medindo posição/tamanho real dos
  elementos em vez de inspeção visual.
- **Segunda rodada de ajustes de mobile, feedback direto do usuário
  testando no celular**:
  - **Topbar: voltou atrás na quebra de linha** - o `flex-wrap: wrap`
    da rodada anterior resolvia o corte, mas o usuário preferiu rolar
    horizontal (mesmo padrão que `.system-tabs` já usa) em vez de
    empilhar os botões em várias linhas. `.topbar-buttons` virou
    `overflow-x: auto` com os botões `flex-shrink: 0`.
  - **Esconder menu em 2 etapas** - antes era um único toggle
    (tudo/nada). Agora cicla em 3 estados: visível → esconde busca/
    filtro de capas (`menubar`+`filterbar`, classe `hide-search`) →
    esconde também o topbar (classe `hide-topbar` adicional) → volta
    pro visível. Ícone do botão muda por estado (⌄ / ⌄⌄ / ⌃) com
    `title` explicando a próxima ação.
  - **Busca geral no acervo + filtro por console** (pedido novo) -
    campo de busca no topbar (`/api/search_library?q=&code=`) procura
    por substring (case/acento-insensitive) o nome de qualquer capa em
    QUALQUER sistema configurado, não só o selecionado no momento -
    resultado mostra o código do sistema junto. Select ao lado filtra
    pra um sistema só. Clicar num resultado troca de sistema (se
    precisar) e rola até a capa, com um destaque temporário (2s) pra
    achar rápido numa galeria de centenas de capas. Testado ao vivo:
    busca cruzando sistemas ("mario" retornando FC/NDS/GBA juntos),
    filtro restringindo a um só (SFC), clique navegando e destacando o
    card certo.
  Testado de novo via geometria real (mobile 375×812 e desktop
  1280×800) - topbar em uma linha só rolável, sem overlap com o botão
  de esconder menu; ciclo dos 3 estados conferido classe por classe.
- **Nome real do jogo Arcade só na visualização** - pedido do usuário:
  romset do Arcade tem nome curto tipo "mslug2"/"19xx" no arquivo, quis
  ver o nome de verdade na tela sem perder o nome curto em operações
  como renomear. Achado real: `core/covers.py` já tinha exatamente o
  dado necessário (`load_romname_dat`/`ROMNAME_DATS["ARCADE"]`, DAT do
  FBNeo do libretro-database, "mslug2" -> "Metal Slug 2 - Super
  Vehicle-001/II") - usado até agora só internamente pra achar a capa
  certa, nunca exposto ao usuário. Extraído `_clean_dat_name` (lógica
  de limpeza que já existia em `find_match`) e criada
  `arcade_display_name(label, romname_dat)`, cosmética, nunca chamada
  por rename/apagar.

  Testado contra o DAT real e o acervo real do usuário: 216 dos 218
  romsets de Arcade resolvidos pro nome completo (só 2 sem
  correspondência, ex: "mvsc2" - cai de volta pro nome curto sem
  quebrar nada). `GET /api/covers/<code>` e `GET /api/search_library`
  ganharam o campo `display_name` (só preenchido pra ARCADE, `None`
  pros outros sistemas - sem custo nem mudança de comportamento pro
  resto do acervo). A busca geral também passou a bater pelo nome
  real, não só pelo romset - buscar "metal slug" agora acha os 6 jogos
  da série Arcade mesmo sem digitar "mslug"/"mslugx"/etc.

  Na GUI: card da galeria mostra o nome completo, com o nome curto
  virando tooltip (`title`) no lugar de texto visível. Lightbox e
  modal de busca de capa também mostram/usam o nome completo (inclusive
  pré-preenchendo a busca com ele - "Metal Slug 2" acha capa bem melhor
  que "mslug2" nas fontes externas). O prompt de renomear continua
  pré-preenchido com o nome CURTO de verdade (é o que vira arquivo),
  só ganhou o nome completo como dica no texto da pergunta - `label`
  (curto) segue sendo o único valor usado em toda operação de arquivo
  (`dataset.label`, `searchCtx.label`, corpo de toda request de
  rename/apagar/flag/duplicar), confirmado não mudou em nenhum desses
  pontos. Testado ao vivo: capa "19xx" mostrando "19XX: The War
  Against Destiny" na tela com tooltip "19xx"; sistema não-Arcade
  (SFC) confirmado sem nenhuma mudança de comportamento.
- **Bug real corrigido: ScreenScraper podia nunca aparecer na busca de
  capa** - usuário pediu pra priorizar o ScreenScraper. Causa raiz:
  `search_cover_candidates` monta os resultados na ordem
  libretro→LaunchBox→ScreenScraper e corta em 40 no final
  (`results[:40]`) - pra um título comum, a busca solta por substring
  no índice INTEIRO do libretro-thumbnails sozinha já enche as 40
  vagas, então o ScreenScraper (adicionado por último) nunca chegava a
  aparecer. Corrigido invertendo a ordem de montagem
  (ScreenScraper→LaunchBox→libretro) - ScreenScraper garante suas até
  20 vagas sempre, LaunchBox preenche o resto, libretro só entra se
  sobrar espaço. Testado ao vivo (SFC, "Mario"/"Super Mario World"):
  antes libretro sozinho já batia 40; depois os 10 primeiros
  resultados são todos ScreenScraper, seguidos de LaunchBox.
- **`rebuild-playlist` e `backup-config` (24/08)** - pedido do usuário:
  montar playlist `.lpl` do RetroArch pro Saturn e Dreamcast (PC +
  Android) e depois atualizar o backup datado das configs. Nenhum dos
  dois existia - `config.toml [cores.*]` já tinha um comentário
  mencionando "usado só pelo comando `rebuild-playlist`" mas o comando
  em si nunca tinha sido escrito (conferido: zero ocorrência de
  "playlist" em `retrosync.py`/`core/`/`gui/` antes disso).

  Achado ao gerar a primeira playlist de Saturn: sistemas pesados
  (`heavy_systems` - SS/SDC/PS2/...) não sincronizam PC↔Android
  sozinhos, então o mesmo código pode ter jogos DIFERENTES nos dois
  lados por design (heavy-roms manda um item de cada vez, sob
  demanda). No acervo real: SS no PC tinha "Daytona USA" + "Rabbit",
  no celular tinha "NiGHTS into Dreams" + "Virtua Fighter 2" + "Virtua
  Racing" - nenhum em comum. `core/playlist.py` trata PC e Android
  como duas listagens independentes de propósito (`list_local_names`
  via `Path.iterdir`, `list_remote_names` via `adb shell find`, mesmo
  padrão de `heavy_roms.list_remote_names`) em vez de uma lista
  compartilhada.

  Decisão de design: cada item da playlist usa `core_path`/`core_name`
  `"DETECT"` e `crc32` `"00000000|crc"` (conferido contra uma playlist
  real gerada pelo próprio RetroArch - "NEC - PC Engine CD -
  TurboGrafx-CD.lpl" - mesmo padrão em todo sistema de disco).
  `default_core_path`/`default_core_name` ficam em branco de
  propósito: nem Saturn nem Dreamcast tinham núcleo instalado no PC no
  momento (usuário confirmou que vai baixar depois via Online Updater
  do próprio RetroArch - PyRetro não baixa `.so` sozinho) e no Android
  não dá pra sequer conferir núcleo instalado via `adb` (`run-as
  com.retroarch` -> "package not debuggable", sem root - `cores/` do
  Android fica em storage privado do app). "DETECT" por item já
  resolve sozinho assim que o núcleo certo existir, sem precisar
  reescrever a playlist depois.

  Descoberta paralela sobre o layout do Android que também virou a
  base do `backup-config`: `playlists/`, `config/`, `cheats/` etc.
  ficam em `/storage/emulated/0/RetroArch/` (storage público, sem
  root) mas o `retroarch.cfg` fica em
  `/storage/emulated/0/Android/data/com.retroarch/files/` (pasta
  privada do app) - só acessível via `adb` porque o arquivo em si é
  `0666` (`adb shell stat` confirmou `Uid: shell` conseguindo ler,
  24/08). `config.toml [android]` ganhou `retroarch_root` (a raiz
  pública) e `retroarch_cfg_path` (o `.cfg`, caminho separado) pra
  refletir isso; `[pc]` ganhou `retroarch_root` (raiz única do profile
  Flatpak, `.cfg`+`config/`+`playlists/` juntos) e `backups_root`.

  `backup-config` replica exatamente o que já vinha sendo feito na
  mão (pasta `Backups/retroarch_<pc|android>_<data>/`, comparado
  contra os backups reais de 31/07 e 20/08 pra confirmar o escopo: só
  `retroarch.cfg`+`config/`+`playlists/`, sem `cores/`/saves/
  thumbnails - esses já têm caminho próprio) - cada rodada cria pasta
  nova, nunca sobrescreve uma data anterior.

  Testado ponta a ponta contra o acervo e o aparelho real (S24 Ultra):
  `rebuild-playlist SS`/`SDC` gerou os 4 arquivos esperados (2 PC + 2
  Android) com o conteúdo certo por lado; `backup-config` copiou 53
  arquivos de `config/` + 1 `.cfg` no PC e 61+159 no Android pra
  `Backups/retroarch_{pc,android}_2026-08-24/`, incluindo as
  playlists novas de Saturn/Dreamcast já dentro do snapshot.
- **Saturn e Dreamcast saíram de `[heavy_systems]` (24/08, mesmo dia)**
  - pedido do usuário logo depois do item acima: voltar SS/SDC a
  sistema leve normal, gerido só por `[systems]` (sync automático via
  Google Drive, sem gestão sob demanda). Removidos `[heavy_systems.SS]`
  e `[heavy_systems.SDC]` de `config.toml`/`config.example.toml`
  (`[systems.SS]`/`[systems.SDC]` continuam intactos - nunca saíram de
  lá, é o que `fetch-covers`/`sanitize-names`/`rebuild-playlist` usam).
  Efeito prático: `heavy-roms SS`/`SDC` agora dá "sistema pesado
  desconhecido" (esperado), o modal "📦 ROMs Pesadas" da GUI para de
  listar os dois, e `core/heavy_roms.py` nunca mais processa esses
  códigos - o exemplo de sidecar multi-track `.gdi` no docstring do
  módulo (Dreamcast, "Sonic Adventure (Track 1/2).bin") ficou só
  histórico, atualizado pra deixar isso claro.

  `COVERS_EXCLUDED` (`core/covers.py`) e o `cd_system=true` de
  SS/SDC em `[systems]` são independentes disso e não mudaram - PS1/
  Dreamcast/Saturn continuam fora da galeria de capas (standalone
  DuckStation/Flycast/Kronos busca capa sozinho, motivo não tem nada a
  ver com heavy_systems) e `organize`/rename-cascade continuam
  reconhecendo `.cue`/`.gdi`/`.chd`/`.cdi` como ROM desses sistemas
  normalmente. Nenhum arquivo físico precisou mover - `roms_root/SS/`
  e `roms_root/SDC/` (PC) e `jogos_root/SS/`, `/SDC/` (celular) já
  eram os mesmos caminhos usados tanto por `[systems]` quanto por
  `[heavy_systems]`, só a categoria de gestão dentro do PyRetro mudou.
  Textos de ajuda do CLI (`heavy-roms`, docstring do `rebuild-playlist`)
  e do README atualizados pra não listar mais SS/SDC como pesado.
- **`fetch-covers-cloud` (24/08, mesmo dia)** - usuário notou que tirar
  SS/SDC de `heavy_systems` não bastava: eles continuavam fora de
  `COVERS_EXCLUDED` (`core/covers.py`) e, mesmo removendo de lá,
  `fetch-covers` sozinho não ia descobrir nada, porque só REVISA capas
  que já existem em `capas_root` - nunca escaneia `roms_root`/nuvem do
  zero (isso é papel de `missing_cover_labels`, que só roda em cima de
  `roms_root` LOCAL, via GUI/organize). Saturn e Dreamcast tinham só
  1-2 jogos baixados no PC mas dezenas na nuvem (mesma assimetria
  achada com `rebuild-playlist` - ver entrada acima), então usar
  `fetch-covers` normal só cobriria uma fração ridícula do acervo.

  Solução: `core/covers.py` ganhou `process_system_cloud` - mesma
  lógica de match/download de `process_system` (exato baixa, fuzzy só
  relatório, `RateLimited` nunca vira `no_match`), mas a lista de
  labels vem de fora, tipicamente `core/heavy_roms.list_drive_items`
  (rclone) chamado pelo `retrosync.py` (novo comando
  `fetch-covers-cloud`) - sem import cruzado entre módulos `core/*`.
  `list_drive_items` não sabe nem se importa se o código está em
  `heavy_systems` - já funcionava genérico o bastante pra reaproveitar
  aqui sem mudar nada nele.

  Achado real ao rodar pra Saturn: `cache/covers_registry.json` já
  tinha 62 entradas `SS` marcadas `replaced_exact`/`replaced_fuzzy` -
  de antes de `COVERS_EXCLUDED` existir, provavelmente - mas
  `Capas/Sega - Saturn/` nem existia mais no disco (pasta inteira
  sumiu em algum momento, registry nunca foi limpo pra combinar). A
  primeira versão de `process_system_cloud` confiava cegamente em
  `label in reg_sys` (mesma regra de `process_system`, que é segura
  LÁ porque só olha label que já tem arquivo local - cache
  `replaced_exact` corresponde sempre a arquivo real nesse caso) e ia
  pular 32 dos 37 jogos achando que já tinham capa. Corrigido: cache
  só é confiável se `status == "no_match"` (nada esperado, nada mudou)
  OU se o `.png` ainda existir de verdade no disco - `no_match` sempre
  confiável, `replaced_exact`/`replaced_fuzzy` só se o arquivo
  sobreviver à checagem. Pego ANTES de rodar `--apply` porque
  inspecionei o registry na mão em vez de confiar só no resumo do
  dry-run.

  Testado ponta a ponta no acervo real: Saturn 37/37 capas (nuvem
  inteira, via libretro-thumbnails sozinho, 0 sem_match). Dreamcast
  8/9 via libretro-thumbnails + 1 via `fetch-covers-fallback`
  (LaunchBox) = 9/9. `validate-covers`/`convert-covers` rodados nos
  dois depois, 0 problema (tudo PNG de verdade, nada em `.jpg`). Pra
  qualquer jogo que ficasse sem match nas duas fontes, o usuário
  confirmou que é pra só listar sem capa mesmo (revisão manual depois,
  mesma regra de sempre) - não chegou a ser preciso dessa vez, as duas
  coleções fecharam 100%.
- **Removida a entrada "flycast" de `core/pc_backup.py` (24/08, mesmo
  dia)** - usuário perguntou se, com Saturn/Dreamcast agora no
  RetroArch, a sincronização de save deles ainda fazia sentido, ou se
  só o Dolphin continuava precisando. Conferido no código antes de
  responder: `core/emu_sync.py` (sync PC↔Drive↔Android de verdade)
  NUNCA teve Saturn/Dreamcast - só `dolphin_gc`, `dolphin_wii`,
  `ps2_memcards`, `ps2_sstates` desde sempre. Saturn (Kronos) também
  nunca precisou de nada - já escreve direto em `Saves/`. A única
  peça de código Dreamcast-específica era a entrada `"flycast"` em
  `core/pc_backup.py` (backup unidirecional PC->Drive do VMU do
  Flycast standalone, `~/.var/app/org.flycast.Flycast/data/flycast/
  *.bin` -> `Saves/Flycast/`) - nunca teve perna Android (só
  investigado em 05/08, sem ferramenta tipo `ps2vmc-tool` pra VMU).

  Confirmado com o usuário que faz sentido remover: RetroArch (core
  Flycast) escreve save normal em `saves_root`/`states_root`, mesmo
  mecanismo que qualquer outro sistema já sincronizado via Google
  Drive - não precisa mais escapar de sandbox nenhuma. Removido:
  entrada `"flycast"` de `SOURCES` (`core/pc_backup.py`), chave
  `flycast_data_root` de `config.toml`/`config.example.toml`, e as 3
  menções em `retrosync.py` (docstring + mensagem + help do argparse
  de `backup-saves`). `grep -r flycast_data_root` confirma zero
  sobra. Dolphin (GC/Wii) continua intacto nos dois módulos
  (`pc_backup.py` e `emu_sync.py`) - segue sendo standalone (decisão
  de 24/08 mais cedo, ver conversa sobre dificuldade de RetroArch
  pros sistemas da lista do usuário), nada muda aí.

  Achado de refile ao mexer nessa área: `core/sync.py`
  `sync_capas` tinha docstring desatualizada ("SDC e PS ficam fora")
  de antes do `COVERS_EXCLUDED` ser reduzido pra só `{"PS"}` mais
  cedo hoje - o código já lia `COVERS_EXCLUDED` direto (não tinha
  "SDC" fixo em lugar nenhum, comportamento sempre esteve correto),
  só o comentário estava errado. Corrigido pra não confundir leitura
  futura. `docs/roadmap.md` também tinha um item de "Próximos passos"
  sobre investigar sync de VMU do Flycast fora do RetroArch - removido
  (não é mais um caso "fora do RetroArch" pra investigar).
- **Neo Geo e Neo Geo CD saíram da coleção (24/08, sessão paralela)** -
  feito em outra sessão do Claude Code rodando ao mesmo tempo neste
  projeto, verificado depois por aqui: `ROMs/NEOGEO/`,
  `ROMs/NEOGEOCD/`, `Capas/SNK - Neo Geo/` e `Capas/SNK - Neo Geo
  CD/` removidos do disco; `config.toml`/`config.example.toml`
  perderam `[systems.NEOGEO]`/`[systems.NEOGEOCD]`; código atualizado
  em conjunto - `core/launchbox.py` (`PLATFORM_MAP`) e
  `core/screenscraper.py` (`SYSTEM_MAP`) perderam as entradas
  NEOGEO/NEOGEOCD, `core/organize.py` teve o comentário de extensões
  ambíguas ajustado (não lista mais NEOGEOCD entre PS/SDC/SS/PCECD/
  PS2). Busca por "NEOGEO" no projeto inteiro (código+config) não
  encontrou nenhuma referência solta depois da limpeza.

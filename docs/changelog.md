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
- **Saturn e Dreamcast saíram da coleção de vez (26/08)** - decisão do
  usuário: os dois emulam mal (Kronos/Flycast) e não valia mais o
  esforço de manter. `ROMs/SS/`, `ROMs/SDC/` e as pastas de capas
  correspondentes já tinham sido apagadas do disco antes desta sessão.
  Removido em conjunto: `[systems.SS]`/`[systems.SDC]` de
  `config.toml`/`config.example.toml`; entradas `"SS"`/`"SDC"` de
  `core/launchbox.py` (`PLATFORM_MAP`) e `core/screenscraper.py`
  (`SYSTEM_MAP`); comentário de extensões ambíguas em
  `core/organize.py` ajustado (não lista mais SS/SDC entre PS/PCECD/
  PS2). Comentários históricos em `core/heavy_roms.py`,
  `core/pc_backup.py`, `core/playlist.py`, `core/covers.py` e
  `core/rom_rename.py` que só registram o histórico de 24/08 (quando
  Saturn/Dreamcast passaram por `[heavy_systems]` e depois voltaram a
  ser sistema leve) foram mantidos como estão - são jornal de decisão
  passada, não afirmação de estado atual. `grep -rniE "saturn|dreamcast"`
  no código+config confirma que só sobraram menções históricas em
  comentário/changelog/README, nada que o código ainda leia.
- **Novo comando `sortear` + `heavy-catalog` (27/08)** - pedido do
  usuário: sortear um jogo aleatório da coleção, com filtro opcional
  de sistema, incluindo os sistemas pesados. Problema: pesado (PS/PS2/
  GameCube/Wii/PSP/3DS) não vive todo em `roms_root` - boa parte só
  existe no Google Drive, e listar isso ao vivo via `rclone` (`core/
  heavy_roms.list_drive_items`) pode levar ~90s POR sistema, inviável
  fazer isso em toda chamada de sorteio (6 sistemas = minutos de
  espera). Solução: `heavy-catalog --apply` consulta o Drive uma vez e
  salva `cache/heavy_catalog.json`; `sortear` só lê esse cache (nunca
  chama `rclone` sozinho), então funciona offline e fica rápido -
  testado na coleção real, `heavy-catalog` levou poucos segundos pros
  6 sistemas (134+82+17+15+45+18 = 311 jogos pesados) e cada `sortear`
  roda na hora. Lógica nova em `core/sortear.py`
  (`refresh_heavy_catalog`/`load_heavy_catalog`/`save_heavy_catalog`/
  `build_pool`/`draw`), reaproveitando `heavy_roms.list_drive_items` e
  `playlist.list_local_names` em vez de duplicar a leitura de arquivo.
  Pool sorteia por JOGO (não por sistema primeiro) - sistema com mais
  jogo tem mais chance, de propósito, pra refletir o tamanho real da
  coleção (leve testado com 1846 jogos combinados leve+pesado no
  pool). Sorteio de sistema pesado que só existe na nuvem avisa e
  sugere o `heavy-roms <CODIGO> --download` certo em vez de só falhar.
- **Nova `core/library.py` - biblioteca de jogos fora de ROM (27/08)** -
  pedido do usuário: unificar "jogos possuídos" nas lojas digitais
  (Steam/GOG/Epic/Amazon/PSN/Xbox) com a planilha de acompanhamento
  pessoal (Google Sheets: iniciado/finalizado/platinado/nota/tempo/
  observações, 94 jogos) que ele mantinha na mão, com o objetivo de
  aposentar a planilha. Decisão de onde guardar: `library_root`
  (`~/Drive/Jogos/Biblioteca/library.json`) fica dentro da MESMA pasta
  que o Google Drive Desktop já sincroniza sozinho pra ROMs/Capas/Saves
  - o celular ganha o arquivo de graça, sem sync novo nenhum; regra
  explícita é que o Android só LÊ isso pra exibir, nenhum comando
  `library-*` (que fala com Heroic/lojas) faz sentido rodando lá.

  Duas fontes hoje: `library-import-sheet <csv>` faz upsert (por
  nome+plataforma) a partir do CSV exportado da planilha - testado
  com o export real do usuário, 94/94 linhas reconhecidas de primeira
  (colunas em PT-BR: Nome do Jogo, Plataforma, Subgenero, Genero,
  Iniciado, Finalizado, Platinado, Nota "7,1" formato BR, Savestate,
  Data Final "DD/MM/AAAA", Tempo, Meta, Observações, Lançamento,
  Desenvolvedora). Coluna "Capa" da planilha é ignorada de propósito -
  conferido que os 3 formatos exportados (csv/xlsx/ods) não carregam
  nenhuma imagem de verdade, porque a fórmula original era
  `=IMAGE(...)` puxando uma busca ao vivo no Bing, não uma capa
  curada; capa de verdade fica pra depois (SteamGridDB, ainda não
  implementado).

  `library-refresh heroic` lê os 3 caches que o Heroic Games Launcher
  já mantém sozinho localmente (`store_cache/legendary_library.json`
  = Epic via legendary, `gog_library.json` = GOG via gogdl,
  `nile_library.json` = Amazon via nile) - decisão importante: usar o
  cache do Heroic em vez de reimplementar login de cada loja (frágil,
  sem API oficial nenhuma pra GOG/Epic/Amazon) - zero rede, zero
  credencial nova, só ler 3 JSON. Filtra `install.is_dlc` (achado:
  GOG tem uma entrada "Galaxy Common Redistributables" que não é jogo).
  Merge por nome normalizado EXATO (minúsculo, sem acento/pontuação) -
  bateu, só anota a fonte (ex: `"heroic:epic"`) no jogo que já existe
  na planilha, sem tocar nota/finalizado/etc; não bateu, vira registro
  novo (possuído, ainda sem acompanhamento). Mesma regra de fuzzy match
  do resto do projeto (`fetch-covers`): parecido demais só entra num
  relatório de possíveis duplicatas, nunca mescla sozinho - testado
  com a biblioteca real (123 Epic + 62 GOG + 13 Amazon, filtrando DLC),
  13 "possíveis duplicatas" reportadas (ex: "Fallout" vs "Fallout 2",
  "Twinmotion EDU 2020.2.3" vs "2020.1.2") eram todas jogos/versões
  DIFERENTES de verdade - confirma que o corte de 0.8 do difflib não
  auto-mesclou nada errado. Resultado final: 290 jogos (94 da planilha
  + 198 possuídos via Heroic - 2 que já batiam nos dois lados).
- **`library-refresh steam` (27/08, mesmo dia)** - segunda fonte da
  biblioteca, via API Web oficial da Steam (`IPlayerService/
  GetOwnedGames`, chave gratuita do usuário em `[steam] api_key` +
  `steamid64` no config.toml). Achado ao testar: a API não erra com
  perfil privado, só devolve `games` vazio/ausente - `read_steam_
  library` trata isso como `RuntimeError` explícito ("confira Detalhes
  do jogo Público") em vez de reportar "0 jogos" sem explicação.
  Testado contra a conta real do usuário: 102 jogos, 26 já batiam com
  a planilha/Heroic (merge por nome exato, mesma regra de sempre), 76
  novos, 9 "possíveis duplicatas" reportadas (Counter-Strike vs
  Counter-Strike 2, FINAL FANTASY VII/IX vs XIII...) - todos jogos
  diferentes de verdade, nenhum merge errado. Um detalhe curioso batido
  ao conferir a contagem: a própria Steam lista "Grand Theft Auto: San
  Andreas" duas vezes (dois appids diferentes) - `merge_owned` tratou
  certo (segunda ocorrência bateu como já-fonte, não duplicou registro
  na library). Total depois desse merge: 366 jogos.
- **`library-refresh psn` + `xbox` implementados, sem conta real pra
  testar ainda (27/08, mesmo dia)** - terceira e quarta fonte da
  biblioteca. Diferente de Steam (API oficial com chave simples), nem
  Sony nem Microsoft têm API pública de "biblioteca possuída" - tive
  que pesquisar o código-fonte de projetos da comunidade
  (achievements-app/psn-api no GitHub, e o cliente Go wolveix/openxbl-go)
  pra achar os endpoints exatos, já que a documentação em prosa (psn-api
  docs, xbl.io/docs) não lista os detalhes de request/response.

  **PSN**: fluxo de autenticação é reverso-engenheiro em 2 passos -
  1) `GET ca.account.sony.com/api/authz/v3/oauth/authorize` com o
  `npsso` do usuário como Cookie, SEM seguir o redirect 302 (por isso
  `http.client` cru em vez de `urllib.request`, que seguiria sozinho) -
  o `code` vem na query string do header `Location`; 2) troca esse
  `code` por um `access_token` via POST com Basic auth fixa (constante
  pública da API da Sony, não é credencial do usuário nem nossa).
  Jogos vêm do endpoint de troféus (`trophyTitles`, paginado de 800 em
  800) - achado importante: só aparece jogo que já foi ABERTO pelo
  menos uma vez (troféu sincroniza no 1º launch), diferente de
  Steam/Heroic onde "possuído" já basta. Documentado isso explicitamente
  no docstring e no README pra não confundir depois.

  **Xbox**: via OpenXBL (xbl.io, não-oficial). Achado durante a
  pesquisa: a doc oficial (`openapi.yaml` do repo OpenXBL/Docs) descreve
  `xbl.io/api/v2/player/titleHistory`, mas o cliente Go mais
  recentemente mantido (`wolveix/openxbl-go`) usa host e envelope
  diferentes - `https://api.xbl.io/v2/titles`, resposta embrulhada em
  `{"content": {...}, "code": ...}`. Fui atrás do Go porque é o mais
  recente/mantido e tem comentário explícito sobre o formato do
  envelope; ficou registrado no docstring de `read_xbox_library` pra
  quem for debugar depois se a Microsoft mudar algo e isso quebrar.
  Header de auth: `X-Authorization: <api_key>`.

  Erros de config ausente já testados (`ValueError` limpo via CLI, sem
  stack trace).
- **PSN e Xbox testados contra conta real (27/08, mesmo dia)** -
  usuário passou `npsso` e a API key do OpenXBL. PSN: 7 jogos (Nine
  Sols, Detroit: Become Human, The Last of Us Remastered, Marvel's
  Spider-Man, The Last Guardian...) - confirma a limitação já
  documentada (só jogo com troféu, não "toda a biblioteca").

  Xbox: primeira tentativa deu `403 Forbidden` - não era a chave errada,
  o Cloudflare na frente do `api.xbl.io` bloqueia especificamente a
  assinatura padrão do `urllib` (`error_code: 1010,
  "browser_signature_banned"`, resposta confirma isso explicitamente,
  não é erro genérico). Corrigido mandando um header `User-Agent` de
  navegador comum na request - segunda tentativa: 200 OK, 314 jogos.
  88 já batiam com o que já tava na library (planilha+Heroic+Steam+PSN),
  226 novos. 20 "possíveis duplicatas" reportadas - a maioria títulos
  DIFERENTES de verdade (Titanfall vs Titanfall 2, FIFA 14 vs FIFA 15),
  mas achado interessante: pelo menos uma ERA o mesmo jogo
  (`"NieR:Automata™ BECOME AS GODS Edition"` vs sem o `™`) que só não
  bateu no exato porque `_normalize` usa decomposição NFKD, e "™" vira
  literalmente "TM" nessa decomposição (não some) - ainda assim ficou
  certo NÃO mesclar sozinho (mesma regra de sempre), só reportado pra
  revisão manual.

  **Biblioteca completa, todas as 6 lojas: 599 jogos**
  (94 planilha + 198 heroic + 101 steam + 7 psn + 314 xbox, descontados
  os que bateram em mais de uma fonte).
- **PSN trocado pra biblioteca de compras de verdade + Xbox
  re-rotulado (27/08, mesmo dia)** - usuário revisou o resultado e
  apontou dois problemas reais: (1) PSN via troféu (item anterior) traz
  jogo físico jogado misturado com digital, "o foco é só o que eu tenho
  na biblioteca"; (2) Xbox tem jogo físico da era 360 e Game Pass junto,
  "o que eu joguei e zerei desses já tá zerado" (na planilha) - a
  intenção do merge de loja é só ownership digital, não histórico de
  jogo.

  **PSN**: achei o endpoint certo pesquisando o código-fonte do
  `psn-api` de novo - `getPurchasedGameList`, uma GraphQL "persisted
  query" (hash SHA256 fixo, `_PSN_PURCHASED_GAMES_HASH`) em
  `web.np.playstation.com/api/graphql/v1/op`, retorna a biblioteca de
  compras PS4/PS5 de verdade (`isActive: true`). Testado ao vivo: 1ª
  tentativa deu `400 "potential CSRF"` - faltava o header
  `apollo-require-preflight: true` (achado sem nenhuma doc, só tentativa
  e erro). Resultado real: 5 itens, mas 2 eram apps (Spotify, PS4 Media
  Player) que vieram junto na resposta sem nenhum flag "isGame" pra
  filtrar - adicionado `_PSN_NON_GAME_ENTITLEMENT_PREFIXES`, uma lista
  pequena e **best-effort** (só cobre o que apareceu nesta conta;
  outra conta com Netflix/YouTube instalado teria prefixos diferentes
  não cobertos). Sobrou o `trophyTitles` antigo como
  `read_psn_trophy_titles`, não usado por padrão. `library.json` foi
  **regenerado do zero** (import CSV + heroic + steam + psn corrigido)
  em vez de só re-rodar em cima do estado antigo, pra não deixar as 7
  entradas contaminadas da versão por-troféu misturadas com a versão
  nova - resultado limpo: 3 jogos (Marvel's Spider-Man, The Last of Us
  Remastered, Heavy Rain).

  **Xbox**: sem regenerar o merge (opção do usuário foi manter, só
  rotular diferente) - fonte trocada de `"xbox"` pra `"xbox:jogado"`
  em `read_xbox_library` e no rótulo do CLI, deixando explícito que é
  histórico de jogo (`/titles`, único endpoint que o OpenXBL oferece),
  não biblioteca possuída. Antes de decidir, testei se dava pra filtrar
  Game Pass usando `gamePass.isGamePass`: não dá, o campo bateu `false`
  pra jogos que sei que são Game Pass no PC (Victoria 3, Europa
  Universalis IV, Hearts of Iron IV) - não é confiável o suficiente pra
  filtrar sozinho sem risco de errar. Perguntado ao usuário como
  proceder (via AskUserQuestion) - escolheu importar tudo mesmo assim
  com o rótulo "jogado", revisão de quais fazem sentido manter fica
  manual no `library.json`.

  **Biblioteca final, pós-correção: 596 jogos** (94 planilha + 198
  heroic + 101 steam + 3 psn + 298 xbox:jogado, descontados os que
  bateram em mais de uma fonte).
- **Aba "Biblioteca" na GUI, v1 = visualização (27/08, mesmo dia)** -
  primeira fase de expor a biblioteca na interface gráfica (pedido do
  usuário: "implementar tudo isso na interface web"), escopo combinado
  antes de codar - v1 só lê/busca, edição (nota/tempo/finalizado/
  platinado/iniciado) e capas ficam pra fases seguintes. Seguido o
  padrão visual que já existia (botão no topbar abre modal, mesma
  estrutura de "Saves"/"ROMs Pesadas") em vez de inventar um layout
  novo. Endpoint `GET /api/library` (`gui/server.py`) só lê
  `library_root/library.json` via `core/library.load_library` -
  simétrico ao resto da GUI, que também só opera em arquivo local
  (funciona igual em modo Android/Termux). Front (`gui/static/
  app.js`+`index.html`+`style.css`) carrega os 417 jogos de uma vez
  (JSON pequeno, não compensa paginar) e filtra no cliente - busca por
  nome, fonte (dropdown populado dinamicamente a partir do que existe
  nos dados) e status. Testado ao vivo no navegador: busca "witcher"
  achou os 2 jogos certos, filtro por fonte "psn:fisico" achou os 6
  certos, filtro "platinado" achou os 11 certos, sem erro no console
  nem no servidor.
- **Edição inline na aba Biblioteca (27/08, mesmo dia)** - fase 2
  combinada com o usuário: nota/tempo (input) e iniciado/finalizado/
  platinado (checkbox) direto na lista, sem precisar abrir outra tela.
  `core/library.py` ganhou `EDITABLE_FIELDS`
  (`nota`/`tempo`/`iniciado`/`finalizado`/`platinado`) e `update_game`
  (atualiza 1 campo, valida contra essa lista, retorna `False` em vez
  de levantar erro se o jogo/campo não existir). Decisão de escopo:
  só esses 5 campos são editáveis pela GUI - nome/plataforma/fontes
  continuam só via CLI, porque o `id` do jogo é um slug de nome+
  plataforma (ver `core/library._slug`) e editar isso pela tela sem
  cuidado quebraria a referência.

  `POST /api/library/update` (`gui/server.py`) - diferente de
  `library-refresh` (PC-only, fala com Heroic/Steam), isso aqui é só
  leitura+escrita de `library.json` local, então funciona igual em modo
  Android/Termux (sem gate nenhum precisando ser adicionado). Testado
  ao vivo no navegador num jogo real (Batman: Arkham Knight, cadastrado
  sem acompanhamento ainda): nota 8.5, tempo "05:30:00", finalizado e
  platinado marcados - 4 POST, todos 200 OK, valores conferidos direto
  no `library.json`. Testado também limpar a nota (campo vazio -> volta
  a `null` de verdade, não string vazia). Dados de teste revertidos ao
  final pra não sujar a biblioteca real do usuário.
- **Ranking na aba Biblioteca (27/08, mesmo dia)** - terceiro item do
  combinado (visualização -> edição -> capas+ranking). Decisão de
  design: não virou tela separada - é um segundo modo do mesmo select
  de ordenação que já existia (nome/nota) na busca. "Por nota" filtra
  pra só quem já tem nota (sem nota não conta como "nota zero", só
  fica fora do ranking) e numera #1, #2... maior pra menor
  (`renderLibraryList` em `gui/static/app.js`, sem endpoint novo -
  mesmo dado que já vinha de `/api/library`). Testado ao vivo: 94 de
  417 jogos têm nota (exatamente os da planilha - nenhuma fonte
  automatizada preenche nota), #1 saiu Celeste, ordem decrescente
  conferida visualmente, sem erro no console.
- **Capas de ROMs pesadas via `fetch-covers-cloud` (27/08, mesmo dia)**
  - quarto item do combinado ("capear tudo, inclusive ROMs pesadas, só
  pra exibição"). Achado antes de mexer: `fetch-covers-cloud` já era
  genérico o bastante (usa `heavy_roms.list_drive_items(code, cfg)` -
  função que não distingue leve/pesado, só usa o código) - só faltava
  `capas`/`repo` no `[heavy_systems.*]` do config.toml e o
  `cmd_fetch_covers_cloud` só olhar `cfg["systems"]`. Confirmado que os
  repos existem no libretro-thumbnails antes de configurar (PS, PS2,
  GameCube, Wii, PSP, 3DS - todos 200 na API do GitHub). "all" continua
  só cobrindo leve de propósito - pesado pede código explícito, porque
  `list_drive_items` pode levar ~90s por sistema e não vale a pena isso
  rodar toda vez que só se quer atualizar os leves.

  PS (heavy) fica de fora - já estava em `COVERS_EXCLUDED` (mesmo
  motivo de sempre: DuckStation busca capa sozinho) e por acaso também
  seria inviável: `git/trees/master?recursive=1` do repo
  `Sony_-_PlayStation` devolve `500` vazio, consistente em 3 tentativas
  - repo grande demais pra API do GitHub processar de uma vez, ao
  contrário de PS2/GameCube/Wii/PSP/3DS (tentado e confirmado 200 nos
  5). PS2 teve um 500 transiente na primeira tentativa (retry resolveu,
  API do GitHub sem chave às vezes engasga em árvore grande) - achado
  registrado no código pra não confundir com bug nosso se acontecer de
  novo.

  Testado e aplicado nos 5 sistemas cobertos: **159 capas baixadas**
  (PS2 77/83, GameCube 16/17, Wii 10/15 +1 fuzzy reportado não
  aplicado, PSP 38/45, 3DS 18/18) - conferido que os arquivos existem
  de verdade em `Capas/<sistema>/Named_Boxarts/`.
- **Capas digitais via SteamGridDB, `library-fetch-covers` (27/08,
  mesmo dia)** - fecha o combinado de capas. Testado ao vivo antes de
  codar (`search/autocomplete/{termo}` -> id do jogo -> `grids/game/
  {id}?dimensions=600x900` -> url do grid 600x900 estilo "alternate",
  mesmo formato retrato que Steam/Heroic usam). Achado: mesmo bloqueio
  de Cloudflare do OpenXBL (`error code: 1010`, assinatura do urllib) -
  resolvido com o mesmo header de User-Agent de navegador.

  Match exato só, mesma disciplina de sempre: só baixa se o nome
  normalizado do 1º resultado da busca bater com o nome do jogo -
  busca por nome não é determinística que nem nome de arquivo de ROM,
  então o cuidado de "nunca aplicar fuzzy sozinho" vale igual ou mais
  aqui. `core/library.fetch_covers` roda em `library_root/capas/
  <id>.png`, salva o caminho relativo em `capa`.

  Testado primeiro com 3 jogos conhecidos (Stardew Valley, Hollow
  Knight, Celeste) antes de soltar o lote completo - 3/3 baixados,
  PNG 600x900 de verdade conferido no disco. Lote completo dos 417
  rodado em segundo plano: **340 capas baixadas, 76 sem match exato,
  1 erro** (rede, não travou o resto). Achado no meio do caminho:
  `cmd_library_fetch_covers` só salvava o `library.json` no final do
  lote inteiro - pra um lote de centenas (minutos de execução, 2
  chamadas de rede por jogo) isso arrisca perder a marcação de tudo já
  baixado se travar no meio; corrigido pra salvar a cada 20 jogos
  (found antes do lote terminar, não afetou essa rodada que já ia bem,
  mas vale pra próxima).

  GUI: endpoint `GET /library-images/<caminho>` (`gui/server.py`) serve
  direto do `capa` salvo em cada jogo - com checagem de path traversal
  (resolve + confere que o resultado ainda está dentro de
  `library_root`, já que o caminho vem cru da URL). Lista da Biblioteca
  ganhou miniatura (`gui/static/app.js`+`style.css`) - jogo sem capa
  mostra um placeholder vazio em vez de buraco no layout. Testado ao
  vivo: todas as requisições de imagem 200 OK, zero erro no console.
- **PSN e Xbox tirados do `library.json` por decisão do usuário (27/08,
  mesmo dia)** - mesmo com PSN já corrigido (biblioteca de compras de
  verdade, 3 jogos certos) e Xbox rotulado honestamente
  (`xbox:jogado`), o usuário decidiu que prefere não confiar nessas duas
  fontes automatizadas por enquanto: vai extrair a biblioteca real
  direto do navegador (Claude in Chrome, logado nas contas PSN/Xbox) e
  cadastrar na mão daqui pra frente, conforme for comprando jogo novo -
  um "cadastro" deliberado em vez de sync automático pras duas lojas
  mais difíceis de confiar. `library.json` regenerado do zero de novo
  (import CSV + heroic + steam, sem psn/xbox): **366 jogos** (94
  planilha + 198 heroic + 101 steam, descontados os 27 que bateram em
  mais de uma fonte). Código de `read_psn_library`/
  `read_psn_trophy_titles`/`read_xbox_library` mantido em
  `core/library.py` (testado, funcional) caso a decisão mude depois -
  só não é chamado no fluxo atual.
- **Novo comando `library-add` + primeiro cadastro manual PSN/Xbox
  (27/08, mesmo dia)** - usuário topou levantar a lista real na mão em
  vez de confiar nas APIs de PSN/Xbox, e pediu um jeito de repetir isso
  conforme for comprando jogo novo. `library-add <arquivo> --plataforma
  --fonte --apply`: arquivo texto, um jogo por linha, mesmo merge
  seguro de `library-refresh` (`core/library.read_manual_list` +
  `merge_owned` reaproveitado, nada duplicado). Primeira lista aplicada,
  em 3 arquivos (fonte diferente por grupo, a pedido do usuário -
  "Mídias Físicas PS4, bom separar"):
  - Xbox (`fonte=xbox`): 55 jogos digitados pelo usuário, corrigidos
    typos óbvios antes de cadastrar (ex: "Unreavel"->"Unravel",
    "CTR Nitro Fulled"->"Crash Team Racing Nitro-Fueled") e "1 e 2"
    expandido em 2 jogos separados (The Escapists, Overcooked, Life is
    Strange) - "Tell Me Why 1-2-3" ficou 1 jogo só (episódios do mesmo
    título, não jogos separados). 43 novos, 12 já rastreados (batendo
    com Heroic/Steam - confirma que dá pra ter o mesmo jogo em mais de
    uma loja sem duplicar). 3 duplicatas possíveis reportadas (Escapists
    vs Escapists 2, FF XII/XVI vs FF XV) - certo não mesclar, são jogos
    diferentes.
  - PSN digital (`fonte=psn`, plataforma "PSN (PS4)"): 3 jogos (Heavy
    Rain, The Last of Us Remastered, Marvel's Spider-Man) - bate 100%
    com o que a API (`getPurchasedGameList`, item anterior) já tinha
    achado antes de ser removida da automação, boa confirmação cruzada
    de que aquele endpoint estava certo.
  - PSN físico (`fonte=psn:fisico`, plataforma "PSN físico (PS4)"): 6
    jogos (Detroit: Become Human, TLOU Part II, The Last Guardian,
    Horizon Zero Dawn, The Order: 1886, Horizon Zero Dawn Complete
    Edition) - fonte nova, separada da digital a pedido do usuário.

  **Biblioteca após o cadastro manual: 417 jogos** (94 planilha + 198
  heroic + 101 steam + 55 xbox manual + 3 psn digital + 6 psn físico,
  descontados os que bateram em mais de uma fonte).
- **"Sortear" na GUI (27/08, mesmo dia)** - primeiro item de "trazer o
  resto do CLI pra web" (pedido explícito do usuário, citando o sortear
  como exemplo). Botão novo no topbar abre um modal simples: `<select>`
  de sistema (populado por `GET /api/sortear/systems`, leve+pesado
  juntos) + botão "Sortear!" chamando `GET /api/sortear?system=<code>`
  - reaproveita `core/sortear.py` inteiro (`build_pool`/`draw`), zero
  lógica de sorteio duplicada em `gui/server.py`. Resposta já inclui a
  dica de download quando o sorteado é pesado e só existe no Drive
  (mesmo texto do CLI, "heavy-roms CODIGO --download").

  Achado ao popular o `<select>`: o código `"PS"` existe TANTO em
  `[systems]` (leve) quanto em `[heavy_systems]` (pesado) no
  config.toml - aparece duas vezes na lista. Não é bug novo, é
  pré-existente: `core/sortear.build_pool` já checava leve antes de
  pesado, então `sortear --system PS` pela CLI sempre resolvia pro leve
  mesmo antes de existir GUI nenhuma - só ficou visível agora por
  aparecer numa lista visual. Não mexido (fora do escopo pedido, e
  funciona igual pros dois lados na prática já que nenhum comando novo
  depende de desambiguar isso).

  Testado ao vivo: sorteio restrito a PS2 (achou corretamente "só no
  Drive"), sorteio "de tudo" (pool de 1846), zero erro no console nos
  dois casos.
- **Resto do CLI trazido pra web - biblioteca, manutenção (27/08,
  mesmo dia)** - usuário escolheu "botão pra tudo" (opção via
  AskUserQuestion) em vez de deixar as operações administrativas só no
  terminal. Criado `_start_job` (`gui/server.py`) - helper genérico que
  roda qualquer função em thread separada emitindo eventos
  `{"type":"log","line":...}` na mesma fila/stream SSE que já existia
  (`/api/fetch/stream`) - evita duplicar o boilerplate de criar
  queue+thread+job_id pra cada comando novo (só a 3ª vez que copiava
  aquilo já doía). Front ganhou `runJob()`, um wrapper genérico
  equivalente pro lado do JS.

  Botões novos, todos reaproveitando a lógica de `core/*` já existente
  (nada de regra de negócio nova em `gui/server.py`):
  - **Biblioteca**: `🔄 Heroic`/`🔄 Steam` (`library-refresh`),
    `🖼 Capas` (`library-fetch-covers`), `+ Lista` (`library-add`, com
    textarea + plataforma + fonte, mesmo formato de arquivo texto da
    CLI). psn/xbox de propósito NÃO ganharam botão de refresh - decisão
    já tomada de não confiar nessas fontes automatizadas.
  - **ROMs pesadas**: `🔄 Catálogo` (`heavy-catalog`) - testado ao vivo,
    312 jogos catalogados via stream, log aparecendo em tempo real.
  - **Manutenção (modal novo)**: backup-config, backup-saves,
    sanitize-names, rebuild-playlist (com select de sistema) e
    emu-sync (com select de fonte) - cada um com seu próprio checkbox
    "aplicar" local, igual o padrão que a galeria principal já usa.

  **Achado sério ao testar**: os 3 primeiros botões da Biblioteca
  (Heroic/Steam/Capas) saíram do primeiro rascunho SEM gate de
  "aplicar" - sempre escreviam de verdade, quebrando o princípio do
  projeto ("Tudo roda em modo simulação por padrão", um dos
  "Princípios (não mudar sem revisitar o motivo)" do README). Pego
  ainda durante a bateria de testes, antes de qualquer escrita
  indesejada acontecer de verdade - corrigido com um checkbox
  "aplicar" único no cabeçalho do modal (mesmo padrão do toggle
  "Aplicar" da galeria principal), threadado até
  `run_library_refresh_job`/`run_library_fetch_covers_job` (agora só
  gravam se `apply=1`, senão só mostram o preview em memória - mesmo
  comportamento que a CLI sempre teve). Testado depois do fix:
  `library.json` com timestamp e conteúdo idênticos antes/depois de
  rodar sem marcar "aplicar" (Heroic simulado + um jogo de teste via
  "+ Lista", nenhum dos dois persistiu).

  `sanitize-names` testado em simulação achou um caso real (`Ratchet &
  Clank` -> `Ratchet and Clank`, capa não renomeada ainda);
  `backup-saves` testado retornou "nada pra fazer backup" (estado
  real, correto). Zero erro de console/servidor em toda a bateria.
- **Ajustes pós-uso da Biblioteca/Sortear/galeria (27/08, mesmo dia)** -
  lista de melhorias que o usuário trouxe depois de usar tudo:

  1. **`[systems.PS]` removido do config.toml/config.example.toml** -
     achado ao investigar a reclamação "PS Leve e PS Pesado não faz
     sentido": PS1 tinha config tanto em `[systems]` quanto em
     `[heavy_systems]`, resquício de antes da migração pra pesado
     (`COVERS_EXCLUDED={"PS"}` já documentava "PS1 saiu da biblioteca
     de capas" há tempo, mas a entrada leve nunca foi removida).
     Confirmado seguro remover: `roms_root/PS/` é a MESMA pasta que
     `[heavy_systems.PS]` já lê via `heavy_mod.list_local`, `cd_system`
     (só existia na entrada leve) nunca é lido em lugar nenhum do
     código, e `organize.py` já deduplicava esse exato caso priorizando
     pesado (`build_ext_index`, comentário próprio já dizia "alguns
     códigos (PS) existem nos dois"). `sortear PS` e o `<select>` do
     sorteio testados depois - PS aparece uma vez só, resolve pesado.
  2. **Rótulo de fonte amigável + fallback por plataforma na
     Biblioteca** - `FONTE_LABELS` (`gui/static/app.js`) traduz código
     técnico pra nome legível (psn -> "PSN (digital)", psn:fisico ->
     "PSN (físico)", heroic:epic -> "Epic Games", etc - só exibição,
     não toca o dado). Jogo sem fonte de loja (`fontes: []`, veio só da
     planilha) usa a própria `plataforma` como agrupamento
     (`libraryGroupsFor`) em vez de um "(sem fonte)" genérico - resolve
     o pedido "temos que linkar em cada plataforma". Testado: dropdown
     lista Arcade/Master System/Xbox One/etc ao lado de Steam/Epic/PSN,
     filtro por "Arcade" achou exatamente 1 jogo.
  3. **Flag iniciado/finalizado/platinado/nota na galeria de ROMs** -
     `GET /api/covers/<code>` agora cruza cada capa com `library.json`
     por nome normalizado (reaproveita `covers_mod.normalize`, mesma
     função que já casa capa - tags de região/artigo não atrapalham) e
     devolve um campo `biblioteca` por item; `gui/static/app.js` mostra
     um badge no canto (✓/🏆/▶ + ★nota) sem precisar abrir a Biblioteca.
     Só leitura, não edita nada da galeria. Testado ao vivo: "19XX: The
     War Against Destiny" (Arcade) mostrou "✓ ★7.1" direto no card,
     como pedido.
  4. **Capa no resultado do sorteio** - `GET /api/sortear` agora acha o
     arquivo de capa (mesmo nome/pasta que a galeria já usa, incluindo
     pesado - PS2/GameCube/Wii/PSP/3DS já tinham capa baixada no item
     anterior) e devolve a URL; `/images/<code>/<arquivo>` estendido
     pra aceitar código de sistema pesado também (antes só olhava
     `cfg["systems"]`). Testado: sorteio de Arcade mostrou a capa de
     "zupapa.zip" corretamente, 200 OK.
  5. **Unificado Renomear+Buscar+Trocar em "✎ Editar"; Errada+Duplicada
     em uma flag só** - pedido explícito de simplificação: "agora que
     tá mais consolidado, eu vejo que é duplicidade ou capa errada e
     tomo a decisão certa". Um botão "✎ Editar" abre a mesma modal de
     busca de sempre, com um campo de renomear e upload adicionados no
     topo - 3 ações, 1 popup. Flag/Duplicada viram um toggle só
     ("⚑ Marcar"/"Desmarcar", sempre grava `flagged_wrong`) - item
     antigo com status "duplicate" continua tratado como "marcado" pra
     exibição/filtro (unflag limpa qualquer status, não só
     flagged_wrong, então nada fica preso). Filtro "⧉ Só duplicadas" no
     topo removido (fundido em "⚑ Só marcadas"). `toggleDuplicate`/
     `renameCover` (versão antiga, com `prompt()`) e o CSS
     `.dup-badge`/`.cover.duplicated` removidos por ficarem sem uso.
     Testado ao vivo: card foi de 6 botões pra 3, Editar abre com nome
     pré-preenchido, flag/unflag preserva o badge da Biblioteca, zero
     erro no console.

  Ficou pendente (arquitetura maior, encaminhado à parte): ROMs
  Pesadas e Biblioteca virarem aba no `#system-tabs` em vez de popup,
  com a mesma visualização em grade da galeria normal.
- **ROMs Pesadas e Biblioteca viram aba, grade de capa igual a galeria
  normal (27/08, mesmo dia)** - fecha o item pendente acima. Confirmado
  com o usuário via AskUserQuestion antes de mexer (opção escolhida:
  "grade de capas nos 3", com controles próprios por tipo) - reescrita
  grande demais pra arriscar advinhar errado.

  `#system-tabs` agora lista leve + pesado + "📚 Biblioteca" numa fila
  só (`loadSystems` busca `/api/systems` e `/api/heavy/systems` juntos,
  `Promise.all`). `currentKind` ("leve"/"pesado"/"biblioteca") decide
  o que `activateTab`/`setControlsForKind` mostram - menubar+filterbar
  de capas só pra leve, `#heavy-controls` (botão de catálogo) só pra
  pesado, `#library-controls` (busca/fonte/status/sort/Heroic/Steam/
  Capas/+Lista) só pra Biblioteca. `<h2 id="current-system">` saiu de
  dentro do menubar (senão sumia junto quando escondido) pra ficar
  sempre visível, virou heading solto acima das 3 barras de controle.

  `buildHeavyCard`/`buildLibraryCard` novos, espelhando `buildCoverCard`
  (mesma classe `.cover`, grade igual) mas com ações próprias: pesado
  usa Enviar/Baixar/Renomear/Apagar (reaproveita `sendHeavyItem`/
  `downloadHeavyItem`/etc. que já existiam, só trocado o seletor de
  `.heavy-item[data-name]` pra `.cover[data-label]`); Biblioteca usa
  nota/tempo/checkboxes direto no card (reaproveita `updateLibraryField`
  sem mudar nada nele). Removidos por ficarem sem uso: `heavy-modal`/
  `library-modal` (HTML), `openHeavy`/`closeHeavy`/`loadHeavySystems`/
  `selectHeavySystem`/`renderHeavyList`/`openLibrary`/`closeLibrary`
  (JS) - `currentHeavy` virou só `currentSystem` (agora é uma fila só
  de abas, não precisa de variável separada por tipo).

  Achado ao portar `/api/heavy/roms/<code>`: sem checar arquivo no
  servidor, toda ROM pesada sem match exato de capa gerava um 404 de
  `<img>` no console (a galeria leve nunca teve esse problema porque
  `missing_cover_labels` já filtra isso do lado do servidor) - corrigido
  do mesmo jeito que `/api/sortear` já fazia: servidor confere
  `Path.is_file()` e só manda `capa` quando existe de verdade, cliente
  não tenta `<img src>` nenhuma pra item sem capa (vai direto pro
  placeholder). Testado ao vivo depois do fix: PS2 com 90 itens, 78 com
  `<img>` de verdade (200 OK) e 12 com placeholder, zero tentativa de
  rede desperdiçada (conferido via inspeção do DOM, não só do log de
  rede - a aba do navegador acumula entradas antigas de testes
  anteriores na mesma sessão, então log sozinho enganava).

  Testado ao vivo, ponta a ponta: FC (leve) sem regressão, 223 capas;
  PS2 (pesado) 90 itens em grade, ✓/🖼 corretos, celular desconectado
  reportado certo; Biblioteca 417 jogos em grade, busca ("witcher" → 2),
  ranking (#1 Celeste, 94 com nota), edição de nota persistindo e
  revertida depois do teste; Sortear e Manutenção continuam funcionando
  como popup (não fizeram parte do pedido de virar aba). Zero erro de
  servidor em toda a bateria.

## 27/08/2026

- **Banco de dados local pras ROMs pesadas** - pergunta direta do
  usuário: "manter um banco de dados das ROMs pesadas em arquivo como
  na biblioteca... acha uma boa?". Resposta: sim, e já existia pela
  metade - `cache/heavy_catalog.json` foi construído semanas atrás pro
  `sortear`, só faltava a aba "ROMs Pesadas" também ler de lá em vez de
  `heavy_roms.list_drive_items` (rclone ao vivo, ~90s por sistema).
  `GET /api/heavy/roms/<code>` agora lê o catálogo cacheado (mesmo
  arquivo do sortear); sem cache ainda pra aquele sistema, cai pra
  rclone ao vivo uma vez e já grava, populando sozinho pra próxima.

  Achado no caminho: o catálogo só guardava `{codigo: [nomes]}` (string
  crua) - suficiente pro sortear (só precisa do nome pra sortear), mas
  a aba de ROMs Pesadas também mostra tamanho, que se perdia por
  completo pra tudo que ainda não foi baixado pro PC. Corrigido na
  raiz: `core/sortear.py` (`refresh_heavy_catalog`/`build_pool`) agora
  guarda o item inteiro (`{"name","size","is_dir"}`), não só o nome.
  Cache regerado via `retrosync heavy-catalog --apply`: PS 134, PS2 83,
  NGC 17, WII 15, PSP 45, 3DS 18 = 312 jogos. Testado ao vivo: aba PS2
  carregou em ~2.4s (vs ~90s ao vivo), 83 itens, tamanhos reais (ex:
  "Ar Tolenico Melody of Elemia.iso" 3.73 GB), zero item com "0.00 GB"
  bugado, zero erro no console/servidor.

- **Segunda leva de ajustes de uso** (testando a unificação leve/
  pesado/Biblioteca do dia anterior) - 6 pedidos, resumo de cada um:

  1. **ROM da planilha não aparece mais duas vezes** - jogo da
     Biblioteca cujo nome bate com uma ROM de verdade (leve OU pesada)
     some da listagem da Biblioteca, porque o dado "mora" na aba da
     ROM agora (ver item 5). `GET /api/library` calcula, a cada
     chamada, o conjunto de nomes normalizados (`covers_mod.normalize`,
     mesmo comparador de sempre) de TODA ROM que existe - leve (arquivo
     local, todo sistema, incluindo nome de exibição do Arcade) +
     pesada (catálogo cacheado) - e filtra fora quem bate. Dinâmico, não
     mexe no arquivo: o registro nunca é apagado, só some dessa UMA
     tela. Testado: 417 → 400 jogos visíveis, os 17 excluídos conferidos
     um a um (19XX Arcade, Action Fighter Master System, Aerial Assault
     Game Gear, Donkey Kong Country SNES, Love Hina Advance GBA,
     Streets of Rage 2 Mega Drive, Super Mario Land Game Boy, Bomba
     Patch Legends + Super Bomba Patch 2025 PS2, Driver + Winning
     Eleven 2002 + Yu-Gi-Oh Forbidden Memories PS1, e 3 casos de "mesmo
     nome, sistema diferente" que merecem nota à parte: Chrono Trigger/
     Final Fantasy VII/Final Fantasy IX estavam catalogados como
     "Steam" na planilha mas também existem como ROM de PS1/SNES -
     união pelo nome exato é a mesma regra de identidade usada em
     TODO o resto do projeto (`merge_owned`, badge da Biblioteca na
     galeria, etc.), então ficou consistente, mas vale o usuário saber
     que o registro de progresso desses 3 agora só aparece/edita pela
     aba da ROM, não mais pela Biblioteca. Caso à parte, mais estranho:
     "Celeste" (Xbox One na planilha) bateu com um `Celeste.gba` que
     existe na coleção de GBA - quase certamente uma ROM-hack/demake
     amador, não o jogo indie de verdade, mas o nome bate exato então
     a regra atual funde os dois. Nenhum dado foi perdido (está tudo
     em `library.json`), só vale o usuário conferir esse caso
     manualmente se notar o progresso "sumido" da Biblioteca.

  2. **Filtro "sem capa" + upload manual também em ROM pesada e
     Biblioteca** - antes só a galeria leve tinha os dois. Checkbox
     "🖼 Só sem capa" novo em `#heavy-controls` e `#library-controls`
     (filtro só no cliente, mesmo padrão da galeria leve). Upload:
     `_cover_path` (resolvia só `cfg["systems"]`) passou a checar
     `heavy_systems` também - com isso `/api/cover/upload` (e de
     quebra `/api/cover/select`/`rename`/`delete`) já funcionam pra
     sistema pesado sem precisar de endpoint novo, só um botão "🖼
     Capa" a mais no card. Biblioteca tem pasta de capa própria
     (`library_root/capas/`, fora de `capas_root`), por isso ganhou um
     endpoint dedicado: `POST /api/library/cover_upload` (mesmo
     tratamento de sempre - `convert` decide o formato pelo conteúdo,
     não confia na extensão). Testado ao vivo: upload numa ROM PS2 sem
     capa (via `_cover_path` generalizado) e num jogo da Biblioteca,
     os dois gravaram o PNG certo; filtro "sem capa" testado em ambas
     as abas (PS2: 83 → 6, Biblioteca: 400 → 74).

     Achado testando (não é regressão desta mudança, é comportamento
     pré-existente do endpoint, só ficou mais alcançável agora que
     `_cover_path` cobre 6 sistemas pesados a mais): `/api/cover/upload`
     escreve o PNG convertido direto no destino final ANTES de checar
     se ficou grande demais/pequeno demais - se a checagem de tamanho
     falhar, o arquivo ruim fica no lugar do antigo em vez de ser
     desfeito. Só acontece com imagem de origem degenerada (nos testes,
     só um PNG sintético de cor sólida disparou isso - capa de verdade
     baixada da internet não chega perto de 1000 bytes convertida).
     Sinalizado à parte pra correção (não bloqueia nada deste pedido).

  3. **Biblioteca separada por plataforma/loja** - pedido: "separar a
     Biblioteca por plataforma, GOG, Amazon, Steam, PS4 e Xbox Series
     S". O agrupamento por fonte/plataforma já existia como `<select>`
     (rodada anterior); virou uma fila de sub-abas (`#library-group-
     tabs`, mesma pílula visual do `.tab` normal, só menor) - mesma
     lógica de agrupamento de sempre (`libraryGroupsFor`), só mudou a
     apresentação de dropdown pra aba, que "separa" mais de verdade
     como pedido. Testado: 16 sub-abas (Epic Games, GOG, Amazon Games,
     Steam, Xbox/Xbox One/Xbox 360/Xbox Series S, PSN digital/físico,
     PC, Android, Switch, PS3, iOS, Todos) - clicar em "GOG" mostrou
     exatamente 62 jogos, batendo com a contagem manual do
     `library.json`.

  4. **Busca unificada numa barra só** - antes a busca do topo
     (`#global-search-input`) só cobria ROM leve, e a Biblioteca tinha
     campo de busca próprio (`#library-search`, removido). `GET
     /api/search_library` agora também busca no catálogo pesado
     (cacheado) e na Biblioteca (excluindo quem já é ROM, ver item 1 -
     evita resultado duplicado do mesmo jogo) quando nenhum sistema
     leve específico está selecionado no filtro ao lado da busca; cada
     item vem com um campo `kind` (`leve`/`pesado`/`biblioteca`) que o
     cliente usa pra decidir se abre `selectSystem`/`selectHeavyTab`/
     `selectLibraryTab` antes de rolar até o card e destacar. Testado
     ao vivo: "bomba" → 2 resultados pesados (PS2); "chrono" → misto
     dos 3 tipos na mesma lista (Chrono Cross pesado, Chrono Cross
     Edition Steam na Biblioteca, Chrono Trigger leve); clique em cada
     um navegou pra aba certa e destacou o card certo.

  5. **Tracking universal (iniciado/finalizado/platinado/nota) em
     qualquer jogo** - antes só a Biblioteca editava; ROM leve/pesada
     só mostravam um badge somente-leitura (rodada anterior). Card de
     ROM (`buildCoverCard`/`buildHeavyCard`) ganhou a mesma fileira de
     controles da Biblioteca (sem "tempo" - não fazia parte do pedido).
     A cabeça da mudança é `core/library.get_or_create_by_name`: acha
     um jogo por nome normalizado cruzando a Biblioteca inteira (mesmo
     índice de `index_by_rom_name`, cross-sistema); sem bater, cria um
     registro novo com `plataforma` = nome amigável do sistema (mesmo
     valor que Sortear já usa como label) e `fonte = "rom:<CODIGO>"`.
     `POST /api/library/track` (nome/plataforma/fonte/campo/valor) faz
     esse find-or-create e delega a escrita de verdade pro
     `update_game` que a Biblioteca já usava - primeira edição na tela
     "cria" o registro sozinha, sem passar por planilha nem loja.
     Testado ao vivo: marquei "iniciado" numa ROM de SFC sem nenhum
     registro prévio (Aero The Acro-Bat) - criou `aero-the-acro-bat-
     nintendo-super-nintendo-entertainment-system` com `fontes:
     ["rom:SFC"]`, sem duplicar num segundo teste, e já saiu excluído
     da Biblioteca sozinho (ver item 1, é dinâmico). Revertido depois
     do teste (registro e capa de teste apagados) pra não sujar o
     `library.json` de verdade. Card de ROM pesada também mostrou
     corretamente o progresso já existente vindo da planilha (ex:
     "Bomba Patch Legends.iso" no PS2 → nota 8, iniciado/finalizado
     true, cruzado pelo mesmo nome).

  Testado ao vivo, ponta a ponta, depois de todos os itens acima:
  reload limpo sem erro de console; Biblioteca com 400 jogos (417 -
  17 ROM-backed), sub-abas, filtro sem capa e upload manual OK; PS2
  (pesado) com tracking cruzado, upload de capa e filtro sem capa OK;
  SFC (leve) com criação de tracking novo OK; busca do topo cobrindo
  os 3 tipos com navegação e destaque corretos.

- **Correção: cruzamento ROM↔Biblioteca precisa de nome E plataforma,
  não só nome** - reportado pelo usuário na hora, direto sobre o aviso
  que eu mesmo dei no item anterior (caso "Celeste"): "isso está
  errado mesmo, por isso deve se separar jogo/plataforma. eu tenho
  celeste na Steam, no Xbox e no GBA, quero vê-los separado mesmo,
  principalmente que Celeste de GBA é completamente diferente". Não
  era só o caso do Celeste - qualquer jogo da planilha catalogado como
  "Steam"/"Xbox"/etc cujo nome batesse com uma ROM de sistema
  qualquer estava sendo silenciosamente unido a ela (ver Chrono
  Trigger/Final Fantasy VII/Final Fantasy IX no item anterior).

  Causa raiz: todo cruzamento (exclusão da Biblioteca, badge de
  tracking na galeria, e o find-or-create do `/api/library/track`)
  comparava só `covers_mod.normalize(nome)`, sem checar se a
  `plataforma` gravada tinha QUALQUER relação com o sistema da ROM em
  questão. Corrigido com uma tabela de mapeamento nova,
  `PLATAFORMA_ROM_CODES` (`core/library.py`) - plataforma (texto livre
  da planilha/loja) → código de sistema ROM, só pros textos que
  realmente significam aquele console (ex: "PlayStation 2"/"SNES"/
  "Arcade"/"Game Boy Advanced" → PS2/SFC/ARCADE/GBA; "Steam"/"Xbox
  One"/"GOG"/etc → nenhum código, nunca cruza com ROM nenhuma). Nome
  igual sozinho não basta mais em lugar nenhum:
  - `index_by_rom_name` agora devolve TODOS os registros com aquele
    nome (lista, não um só) - pode haver mais de um jogo DIFERENTE com
    o mesmo nome em plataformas diferentes de verdade.
  - `find_for_rom(index, nome, code)` (nova) escolhe, entre os
    registros de mesmo nome, o único cuja `plataforma` mapeia pro
    `code` pedido - usada tanto pelo badge de tracking na galeria
    (`/api/covers/<code>`, `/api/heavy/roms/<code>`) quanto por
    `is_rom_backed` (exclusão da Biblioteca em `/api/library` e
    `/api/search_library`, agora recebendo `rom_normalized_names_by_code`
    - `{codigo: {nomes}}` em vez de um set achatado).
  - `get_or_create_by_name` virou `get_or_create_for_rom(library, nome,
    code, plataforma, fonte)` - exige `code` também, usa `find_for_rom`
    por baixo. `/api/library/track` e `trackGame()` (JS) passaram a
    mandar `code` no corpo da requisição.

  Efeito prático: dos 17 jogos excluídos da Biblioteca no item
  anterior, 5 voltaram a aparecer (Celeste, Chrono Trigger, Final
  Fantasy VII, Final Fantasy IX) porque a plataforma gravada pra eles é
  "Xbox One"/"Steam" - não mapeia pra ROM nenhuma, então não tinha
  motivo real pra ter sumido. Os outros 12 (plataforma já era
  literalmente "PlayStation 2"/"SNES"/"Arcade"/etc) continuam excluídos
  corretamente, é o mesmo jogo tratado do mesmo jeito de sempre.

  Testado ao vivo: Biblioteca voltou a mostrar "Celeste (Xbox One)",
  "CHRONO TRIGGER (Steam)", "FINAL FANTASY VII (Steam)" e "FINAL
  FANTASY IX (Steam)" (400 → 405 visíveis, 17 → 12 excluídos, os 12
  conferidos um a um - todos plataforma ROM de verdade); `GET
  /api/covers/GBA` e `/api/covers/SFC` confirmaram `biblioteca: null`
  pro Celeste/Chrono Trigger de ROM (não cruza mais com o registro de
  loja errado); `Bomba Patch Legends.iso`/`Super Bomba Patch 2025.iso`
  no PS2 (esses sim devem cruzar - plataforma gravada já é "PlayStation
  2" de verdade) continuaram mostrando nota/iniciado/finalizado
  corretamente, sem regressão. Criei um registro de teste novo
  marcando "iniciado" no Celeste da aba GBA: confirmado que virou um
  registro À PARTE (`celeste-nintendo-game-boy-advance`, fonte
  `rom:GBA`) sem tocar em nada do registro real "Celeste (Xbox One)"
  (nota 11, 4000+ mortes, etc. intactos) - revertido depois do teste.

- **Terceira leva: espaço da GUI, comentário perdido, Switch, badge
  duplicado, capa faltando, bug de upload** - 6 pedidos do usuário
  depois de usar a versão do dia:

  1. **Bug real por trás do "muito espaço"** - o usuário reportou a
     Biblioteca consumindo espaço demais (print mostrando `#menubar`/
     `#filterbar` LEVE + `#heavy-controls` PESADO + `#library-controls`
     todos empilhados ao mesmo tempo). Não era só volume de conteúdo:
     nunca existiu uma regra CSS genérica `.hidden { display: none }`
     no projeto - só regras específicas tipo `.modal.hidden`/
     `.lightbox.hidden` por widget. `setControlsForKind`
     (`classList.toggle("hidden", ...)`) rodava certinho, mas a classe
     não tinha efeito visual NENHUM em `#menubar`/`#filterbar`/
     `#heavy-controls`/`#library-controls` (nenhum tinha uma regra
     `.hidden` própria) - as 4 barras ficavam sempre visíveis juntas,
     em QUALQUER aba (leve/pesado/Biblioteca), não só na Biblioteca -
     só ficou óbvio agora que a Biblioteca cresceu pra 3 linhas.
     Corrigido com uma regra `.hidden { display: none !important; }`
     genérica em `style.css`. Testado ao vivo:
     `getComputedStyle(...).display` de cada barra antes/depois -
     `menubar`/`filterbar`/`heavy-controls` todas `"flex"` mesmo com
     `hidden` na classe (bug confirmado), viraram `"none"` depois do
     fix; altura total de `#library-controls` na aba Biblioteca caiu
     pra 134px, só ela visível.
  2. **Ações de importação da Biblioteca viraram retrátil** (Heroic/
     Steam/Switch/Capas/+Lista) - `<details>`/`<summary>` nativo
     (`#library-admin-details`), fechado por padrão no HTML - pedido
     do usuário: "permitir a retração, e alguns já começar retraído".
     Nativo em vez de JS próprio (grátis, sem estado extra).
  3. **Comentário da planilha não foi perdido** - `observacoes` sempre
     foi importada certo pelo `library-import-sheet` (94 dos 417 jogos
     têm, conferido direto no `library.json`), só nunca tinha campo
     na tela pra mostrar/editar. Adicionado `<textarea
     class="library-obs-input">` no card da Biblioteca +
     `"observacoes"` em `core/library.EDITABLE_FIELDS` (era só nota/
     tempo/iniciado/finalizado/platinado). Testado: card de "A Plague
     Tale: Innocence" mostrou o comentário real da planilha
     corretamente.
  4. **Badge de plataforma duplicado** - jogo sem fonte de loja mostra
     `[plataforma]` como badge (`libraryGroupsFor` cai pra
     `[g.plataforma]` sem fonte) igual ao texto que já aparece uma
     linha acima; jogo com uma fonte só cujo rótulo bate com a
     plataforma gravada (ex: plataforma "Steam" + fonte "steam") tinha
     o mesmo problema. `buildLibraryCard` agora filtra badge cujo
     rótulo é idêntico (case-insensitive) à `plataforma` mostrada -
     jogo com fonte extra de verdade (ex: Celeste: Steam+Xbox,
     plataforma "Xbox One") continua mostrando os dois badges
     normalmente, testado ao vivo.
  5. **Capa manual pra jogo sem capa da Biblioteca já existia** - "🖼
     Capa" + `/api/library/cover_upload` foram implementados na leva
     anterior (mesmo dia) - conferido que o botão está no card e o
     endpoint funciona; provavelmente só não foi notado no meio do
     resto. Nada novo feito aqui.
  6. **Importação de jogos de Switch** (`roms_root/NSW/`, pasta real
     com 22 jogos: `Animal Crossing New Horizons [NSP]`, `Nine Sols
     [NSZ]`, etc.) - "fazer o mesmo que fizemos pras ROMs... levando em
     consideração o nome da pasta, sem o [XXX]... importar minha nota e
     comentário pra lá". Decisão: NÃO virou aba tipo ROM pesada (send/
     download/rename/apagar via adb/rclone não fazem sentido pra
     Switch - não roda via RetroArch, e expor "Apagar"/"Renomear" numa
     tela pensada pra emulação arriscaria mexer em jogo de verdade à
     toa). Em vez disso, Switch virou mais uma FONTE de posse, igual
     Heroic/Steam: `core.library.read_switch_library(roms_root)` lista
     `roms_root/NSW/*/`, remove qualquer tag entre colchetes do nome da
     pasta (`re.sub(r"\s*\[[^\]]*\]", "", nome)`), devolve
     `{"nome", "plataforma": "Nintendo Switch", "fonte": "switch"}` por
     item. Reaproveita `merge_owned` (mesmo mecanismo de sempre - nome
     exato funde fonte no registro que já tem a nota/comentário da
     planilha; sem bater, cria registro novo; parecido demais só
     reporta, nunca mescla sozinho) - cobre o caso "Portal é parte de
     uma coletânea, não dá pra separar" citado pelo usuário sem
     esforço extra: nome da coletânea não bate exato com "Portal" da
     planilha, então não funde (fica como possível duplicata reportada
     ou registro novo separado, nada quebra). Fonte nova em 3 lugares:
     `library-refresh switch` (CLI, `retrosync.py`), `POST
     /api/library/refresh?source=switch` (já existia genérico, só
     precisava do branch novo em `run_library_refresh_job`), botão
     "🔄 Switch" na GUI ao lado de Heroic/Steam. Testado ao vivo (modo
     simulação, nada salvo): 22 jogos encontrados, nomes de pasta
     limpos corretamente (`"Nine Sols [NSZ]"` -> `"Nine Sols"`), 0 já
     rastreado (nenhum bate exato com a planilha agora), 3 possíveis
     duplicatas reportadas e corretamente NÃO mescladas (`Octopath
     Traveler 2` ~ `Octopath Traveler 0`, `Octopath Traveler` ~
     `Octopath Traveler 2`, `Resident Evil` ~ `Resident Evil 3`).

  Bônus - **ataquei o bug de upload sinalizado na leva anterior** (não
  pedido de novo, mas o usuário confirmou "atacar o bug que você
  citou"): `/api/cover/upload` convertia direto em cima do `dest`
  final - se a checagem de tamanho pós-conversão falhasse, a capa
  antiga (ou a ausência de uma) ficava substituída por um PNG quebrado
  mesmo com o endpoint respondendo erro. Corrigido: converte pra um
  arquivo temporário separado, só troca pro `dest` real (`Path.replace`,
  rename atômico) depois de validar tamanho/returncode. Achei e corrigi
  um bug NOVO que eu mesmo introduzi na primeira tentativa dessa
  correção antes de reportar como pronta: usei `label + ext + ".tmp"`
  pro arquivo de origem e `label + ".png.tmp"` pro de destino - quando
  a extensão de origem já é `.png` (caso mais comum), os dois nomes
  ficavam IDÊNTICOS, e o `convert` tentava ler e escrever o mesmo
  arquivo ao mesmo tempo (resultado: sempre falha "arquivo pequeno
  demais", mesmo com imagem boa - pego no meu próprio teste de
  regressão antes de reportar, não em produção). Corrigido usando
  sufixos `.src<ext>.tmp`/`.dst.png.tmp`, sempre distintos. Testado ao
  vivo: upload de imagem boa (205KB) funcionou e não deixou `.tmp`
  sobrando; upload de imagem degenerada (<1000 bytes convertida)
  respondeu erro 500 SEM tocar na capa boa que já estava lá (conferido
  por tamanho de arquivo antes/depois - ficou intacta, ao contrário do
  comportamento antigo).

- **Quarta leva: aplicar Switch de verdade, curar plataforma/grupo,
  cor na nota** - usuário validou pelo celular e voltou com mais 5
  pedidos:

  1. **`library-refresh switch --apply` rodado de verdade** - o pedido
     anterior só tinha sido testado em modo simulação (nada salvo);
     "NSW não está aparecendo" era esperado até rodar com `--apply`.
     Rodado: 22 novo(s), 0 já rastreado(s), as mesmas 3 possíveis
     duplicatas de antes reportadas e não mescladas -
     `library.json` foi de 417 pra 439 jogos.
  2. **iOS + Android → "Mobile"** e **Xbox/Xbox 360/Xbox One/Xbox
     Series S → "Xbox"** nas sub-abas - `GROUP_TAB_ALIASES` novo em
     `gui/static/app.js`, aplicado só na CURADORIA de navegação (rótulo
     amigável pós-`fonteLabel`), nunca no dado gravado - o card
     continua mostrando o modelo exato (`g.plataforma`) na sua própria
     linha, só a barra de abas fica mais enxuta. `libraryTabGroupsFor`
     novo (separado de `libraryGroupsFor`, que continua sem curadoria -
     usado pros badges por card, onde o modelo específico ainda
     importa). Achado testando: os 22 jogos de Switch recém-importados
     têm `fontes: ["switch"]` (não vazio, diferente dos 2 antigos só de
     planilha) - caíam no ramo de FONTE de `libraryGroupsFor`, não no
     de plataforma, e "switch" não estava em `FONTE_LABELS` -> abria
     uma aba solta "switch" ao lado de "Nintendo Switch" em vez de
     somar nela. Corrigido adicionando `"switch": "Nintendo Switch"`
     em `FONTE_LABELS`. Testado ao vivo: aba única "Nintendo Switch"
     com 24 jogos (2 da planilha + 22 da pasta), "Xbox" e "Mobile"
     aparecem uma vez cada na lista de sub-abas.
  3. **25 jogos de "PC" viraram "Steam"** - pedido explícito e
     delimitado ("Victoria II e The Sims 4 eu tenho lá, o resto não,
     mas só pra não ficar solto"). Editado direto no `library.json`
     (script Python, achando por nome exato "Victoria 2"/"The Sims 4"
     pra excluir - o resto dos 27 jogos com `plataforma: "PC"` virou
     `plataforma: "Steam"`). Só o campo `plataforma` mudou, `id` e
     `fontes` ficaram como estavam (id é permanente uma vez criado,
     mesmo princípio de sempre - ver `core/library.py`). Testado: aba
     "PC" ficou só com os 2 esperados, aba "Steam" cresceu.
  4. **Cor na nota** (vermelho 1 → verde 10 → dourado 11+) -
     `notaColor(nota)` novo em `gui/static/app.js`: interpola RGB entre
     as cores de tema já existentes (`--err`/`--ok`, não vermelho/verde
     puro, pra combinar com o resto da UI) proporcionalmente entre 1 e
     10; acima de 10 (só 11 visto na coleção real) usa `--warn`
     (dourado/âmbar). Sem nota, sem cor. Aplicado via `applyNotaColor`
     (borda mais grossa + texto em negrito na cor, não só borda fina)
     tanto no card completo da Biblioteca quanto na fileira de tracking
     universal (ROM leve/pesada) - mesma função, um lugar só. Testado
     ao vivo: nota 1 -> `rgb(224,92,92)` (=`--err` exato), nota 10 ->
     `rgb(76,175,125)` (=`--ok` exato), nota 5.5 -> meio-termo, nota 11
     (Celeste) -> `rgb(224,165,44)` (=`--warn` exato), sem nota -> sem
     cor; conferido também num card de ROM pesada (PS2, nota 8) com a
     cor certa aplicada.

  Esclarecimento do usuário sobre o item 3 (28/08): a maioria dos 25
  jogos já tinha `fontes: ["steam"]` confirmado pela sincronização real
  da Steam ANTES da edição - o agrupamento em aba (que usa `fontes`,
  não `plataforma`, ver `libraryGroupsFor`) já mostrava eles em "Steam"
  mesmo com o texto do card ainda dizendo "PC". A edição só corrigiu o
  TEXTO exibido, não era estritamente necessária pra navegação -
  perguntado ao usuário se queria reverter, resposta: manter como
  "Steam" (mais preciso, já que é posse confirmada de verdade).

## 28/08/2026

- **Quinta leva: fontes de capa novas, card redesenhado, curadoria de
  plataforma, Ranking/Iniciados** - o usuário validou pelo celular e
  voltou com 11 pontos ("ainda acho que está bem distante do ideal, mas
  caminhando").

  **Erro meu da leva anterior, corrigido**: na leva 4 ele pediu "os que
  tá lá em PC passar todos para Steam, o Victoria II e The Sims 4 eu
  tenho lá, o resto não, mas só pra não ficar solto" - eu li ao
  contrário e DEIXEI Victoria 2/The Sims 4 como "PC", movendo só os
  outros. O "eu tenho lá" queria dizer que esses dois ele tem NA STEAM
  de verdade (os outros não, mas iam junto mesmo assim pra não ficarem
  soltos). Agora os dois estão em Steam.

  1. **Capa de fonte remota pra ROM pesada e Biblioteca, com fonte
     NOVA** - até aqui pesada só tinha upload manual e a Biblioteca só
     SteamGridDB. Duas frentes:
     - **CDN oficial da Steam** (fonte nova): `read_steam_library`
       passou a devolver o `appid` de cada jogo, `steam_appid_index`
       monta {nome normalizado: appid} e `find_cover_steam_cdn` pega a
       arte de biblioteca 600x900 oficial (`library_600x900_2x.jpg`,
       com fallback pra resolução normal). Não precisa de chave nem
       login - é a mesma imagem que o cliente da Steam mostra. Cobre
       101 jogos da conta com arte oficial, melhor que qualquer
       curadoria de terceiro. `fetch_covers` tenta essa primeiro e cai
       pro SteamGridDB no resto.
     - **SteamGridDB melhorado**: antes só olhava o PRIMEIRO resultado
       da busca e desistia se não batesse exato ("Portal" podia
       devolver "Portal Knights" na frente e o jogo certo em 3º). Agora
       varre TODOS os resultados atrás do match exato, e faz uma
       segunda passada com `normalize(loose=True)` (tira parênteses)
       que pega coisas tipo "FINAL FANTASY VII (2013)". Continua sendo
       match exato - a trava de nunca aplicar capa de outro jogo
       sozinho está intacta, só deixou de desistir cedo demais.
     - **ROM pesada** ganhou botão "🖼 Buscar capas"
       (`POST /api/heavy/fetch_covers`, `run_heavy_fetch_covers_job`):
       passada 1 libretro-thumbnails (mesma lógica do
       `fetch-covers-cloud`, mas lendo o catálogo CACHEADO em vez de
       rclone ao vivo), passada 2 SteamGridDB pro que sobrou. Vale
       especialmente pro PS1, que está em `COVERS_EXCLUDED` (repo
       grande demais pra API do GitHub) e por isso nunca teve capa
       automática nenhuma - agora tem, via SteamGridDB.

     Achado rodando a curadoria em massa (bug real, não teórico): o
     lote de 262 jogos morreu no meio com `TimeoutError` no download da
     imagem. O `except` pegava `URLError`/`HTTPError`, mas timeout de
     LEITURA levanta `TimeoutError`, que não é subclasse de `URLError`
     (só de `OSError`) - um job longo morria inteiro por causa de uma
     imagem lenta. Trocado pra `except OSError` (cobre os três de uma
     vez) nos 4 pontos de rede do módulo.

  2. **Comentário virou botão -> popup, e sumiu o tamanho da ROM** - a
     textarea no card empurrava tudo pra baixo ("a visualização fica
     ruim"). Agora é um 💬 que abre popup com comentário + tempo
     jogado (o `tempo` saiu do card junto, pra não perder o campo).
     Botão fica destacado quando já tem conteúdo. O `formatGB` saiu do
     card de ROM pesada - sobrou só o status (só no Drive / no celular
     / só no PC), que é o que ajuda a decidir.
  3. **Nota redesenhada** - era um `<input type=number>` de 44px cujo
     placeholder "nota" aparecia cortado como "no" (foi isso que o
     usuário viu). Virou um chip: `−` `7.1` `+`, com o número, a borda
     e um fundo sutil na cor da nota (escala de 27/08), setas ajustando
     de 0.1 em 0.1 e clique no número pra digitar direto. Sem texto
     nenhum pra cortar.
  4. **Jogo que existe em duas lojas aparece nas duas abas** -
     `libraryGroupsFor` era "fonte se tiver, senão plataforma", então
     "A Plague Tale: Innocence" (plataforma "Xbox One", onde ele
     FECHOU + fonte "heroic:epic") só aparecia na aba Epic; o Xbox,
     onde o progresso aconteceu, ficava de fora. Agora é a UNIÃO de
     fontes + plataforma. Mesmo caso de Overcooked, The Escapists 2 e
     Mortal Kombat X (fonte steam, fechado no Xbox One). Aliases novos
     em `GROUP_TAB_ALIASES` pra loja com dois nomes ("Epic Games Store"
     = "Epic Games", "PSN (PS4)" = "PSN (digital)") não virarem duas
     abas.
  5. **Card mais limpo** ("olha do print da GOG como tá feio, os campos
     todos meio jogados") - eram 5 blocos empilhados com estilos
     diferentes (plataforma, badges, capa, tracking, textarea). Agora:
     uma linha de meta ("Xbox One · Epic Games", texto único) + UMA
     barra de tracking alinhada no rodapé do card (`margin-top:auto`,
     então a barra fica na mesma altura em todos os cards da linha).
  6. **Life is Strange: True Colors separado** - a planilha dizia
     Switch, mas ele FECHOU no Xbox (Game Pass) e está rejogando no
     Switch. Virou dois registros: o antigo passou a ser o do Xbox One
     (mantendo nota 7.5 e finalizado) e nasceu um do Switch zerado, só
     `iniciado`, com observação "rejogando no Switch (finalizado no
     Xbox)".
  7. **Switch: 163 jogos importados** - "sinto que tá faltando bastante
     jogo no Switch". Faltava mesmo: a pasta `ROMs/NSW/` (22 dumps) e o
     arquivo `Jogos Switch.txt` (163 títulos da eShop) são listas
     COMPLEMENTARES, quase sem sobreposição - só o txt não tinha sido
     importado. Via `library-add` (merge seguro de sempre): 162 novos,
     14 possíveis duplicatas reportadas e corretamente não mescladas
     (todas falso positivo - "Pikmin 2"~"Pikmin", "Xenoblade 3"~"2"
     etc). Biblioteca foi de 439 pra 601 jogos.
  8. **Victoria 2 + The Sims 4 -> Steam**, e a duplicata "Victoria II"
     (registro vazio vindo da API da Steam) absorvida no "Victoria 2"
     que tinha a nota 6.9 - era exatamente o caso de revisão manual que
     o `merge_owned` prevê ao só REPORTAR nome parecido.
  9. **Ocultar jogo** (`oculto`, campo novo) - pra tirar da vista jogo
     online tipo Black Desert sem apagar o registro. Botão 👁 no card,
     filtro "👁 Mostrar ocultos" pra rever/desfazer, e o
     `fetch_covers`/Ranking/Iniciados pulam oculto.
 10. **Curadoria de plataforma do Xbox** - a API do Xbox devolve tudo
     como "Xbox" genérico, sem geração. 42 dos 43 jogos passaram a ter
     a plataforma de LANÇAMENTO ORIGINAL, na mão: Xbox (MX Unleashed,
     Psychonauts, Sphynx), Xbox 360 (GTA V, Darksiders, Devil May Cry
     4/HD Collection, Far Cry Classic, The Wolf Among Us), Xbox One
     (Batman Arkham Knight/Return to Arkham, Witcher 3, RDR2, Cuphead,
     Stardew Valley, ...), Xbox Series S (EA FC 26, Final Fantasy XVI,
     Split Fiction, Mixtape, Zau). "Opus Castle" ficou como "Xbox" de
     propósito - não soube dizer com confiança, melhor genérico do que
     errado.
 11. **Ranking e Iniciados** ao lado de Sortear (`GET /api/ranking`,
     `GET /api/iniciados`) - listas que cruzam a coleção INTEIRA de uma
     vez (ROM leve + pesada + Biblioteca), o que faz sentido desde que
     o `library.json` virou fonte única de progresso pro tracking
     universal. Ranking numera do maior pro menor com a nota colorida;
     Iniciados mostra o que começou e não terminou. Capa resolvida nos
     dois mundos (pasta do sistema pra ROM, `library_root/capas` pra
     Biblioteca) pelo servidor, então a tela não precisa saber a
     diferença.

- **Sexta leva: busca de capa manual, Switch pelo Drive, curadoria do
  PlayStation, ajustes de design** - o usuário testou pelo celular e
  mandou prints com os problemas marcados.

  1. **Rótulo redundante** ("Epic Games Store · Epic Games", "PSN
     físico (PS4) · PSN (físico)") - a deduplicação do card comparava o
     TEXTO CRU da plataforma com o rótulo da fonte, e "Epic Games
     Store" != "Epic Games" mesmo sendo a mesma loja. Agora os dois
     lados passam por `GROUP_TAB_ALIASES` (o mesmo mapa que já junta as
     abas) antes de comparar.
  2. **PlayStation curado** - "o ideal é ter PlayStation 3 e
     PlayStation 4 apenas, e no jogo colocar a label PSN (digital) e
     Físico". As plataformas "PSN (PS4)"/"PSN físico (PS4)" viraram
     "PlayStation 4" nos 8 jogos; o digital/físico já estava na `fonte`
     (psn / psn:fisico), então o card agora mostra "PlayStation 4 · PSN
     (digital)" / "PlayStation 4 · PSN (físico)" sem redundância.
  3. **Barra de tracking cortando o 💬** (marcado em vermelho no print)
     - o `<input type=checkbox>` nativo + emoji custava ~34px por flag;
     as 3 estouravam a largura do card e o último botão ficava cortado
     na borda. Agora o checkbox é escondido e o próprio emoji é o
     botão (aceso/apagado via `:checked + span`), ~18px cada. Medido
     depois: `scrollWidth == clientWidth` (258px), nada mais transborda.
  4. **Busca de capa pra Biblioteca e ROM pesada** ("não consigo buscar
     nem alterar capa... quero ir capeando todos os jogos de todas as
     abas") - as duas só tinham upload de arquivo; busca existia só pra
     ROM leve (libretro/LaunchBox/ScreenScraper, que não cobrem
     Biblioteca nem PS2/GameCube/Wii/PSP/3DS). Novo:
     `search_covers_steamgriddb` (candidatos, sem exigir match exato -
     quem decide é o humano olhando a prévia, mesmo princípio da busca
     que os leves já tinham), `GET /api/cover/search_sgdb` e
     `POST /api/cover/apply_url` (um endpoint só pros dois destinos:
     `capas_root/<sistema>/Named_Boxarts/<label>.png` pra ROM,
     `library_root/capas/<id>.png` pra Biblioteca). Na tela, o 🖼 do
     card abre um popup com busca + upload no mesmo lugar. Testado ao
     vivo ponta a ponta: busca em português rendeu pouco ("As Aventuras
     Iradas de Captain Spirit" -> 4 candidatos ruins), refinei o termo
     pro nome em inglês no próprio campo -> 11 candidatos certos,
     apliquei e a capa gravou; mesma busca funcionando num item de PS2
     (12 candidatos).
  5. **Switch estava lendo a pasta errada** - `read_switch_library` só
     olhava `roms_root/NSW/` LOCAL, que tinha 22 jogos num dia e 4 no
     outro (o usuário puxa pro PC só o que vai jogar). O grosso da
     coleção está no Google Drive - ele mesmo corrigiu no meio da
     conversa: "tem que ver no drive com rclone". Agora lê as DUAS
     pontas (local + Drive via `list_drive_items`, a mesma função dos
     sistemas pesados) e une por nome: 133 jogos no Drive, 101 novos.
     Somando a lista `Jogos Switch.txt`, Switch foi de 24 -> **287
     jogos**, biblioteca total 601 -> 703.
  6. **Ranking/Iniciados: capa ampliável + comentário** - clicar na
     capa abre o lightbox, e um 💬 por linha abre o mesmo popup de
     comentário/tempo dos cards (editável, gravando por id).
  7. **"Iniciados" com poucos jogos** - investigado a fundo antes de
     mexer: o CSV atualizado em `~/Downloads` bate 100% com o
     `library.json` (0 divergência) e tem 0 jogos iniciados-e-não-
     finalizados, então não havia dado faltando. O usuário esclareceu:
     "essas flags valem para toda a biblioteca, exemplo, Final Fantasy
     VI de SNES eu iniciei" - ou seja, o esperado é que ROM entre na
     conta também. O mecanismo já fazia isso (a lista cruza tudo), só
     que a flag de uma ROM precisa ser marcada uma vez pra existir
     registro. Marcado o FF VI de SNES pra validar o caminho ponta a
     ponta: apareceu na hora em Iniciados, com a capa resolvida da
     pasta do SNES.

  Bug pego durante a curadoria em massa de capas (não teórico - matou o
  primeiro lote): timeout de LEITURA levanta `TimeoutError`, que não é
  subclasse de `URLError`, só de `OSError` - o `except` estreito deixava
  um lote de 262 jogos morrer inteiro por causa de uma imagem lenta.
  Trocado pra `except OSError` nos 4 pontos de rede de
  `core/library.py`. Depois do fix: 162 capas baixadas, **0 erros**.

  Limpeza: `uploadHeavyCover`/`uploadLibraryCover`/`applyNotaColor`
  removidas por ficarem órfãs (o popup de capa e o chip de nota
  substituíram as três).

- **Sétima leva: todas as fontes de capa nas ROMs pesadas + pente fino
  geral** - pergunta do usuário: "em ROMs pesadas, ele só procura no
  SteamGridDB? e as outras fontes que usamos, não é melhor? faz ele
  procurar em todas e já faz mais um pente fino geral". Procedente: o
  job de pesadas fazia libretro-thumbnails + SteamGridDB e ignorava
  ScreenScraper e LaunchBox - justamente as duas de curadoria melhor.
  Pior: o PS1 (o sistema com mais buraco, e o único em
  `COVERS_EXCLUDED`) É suportado pelas duas desde sempre e mesmo assim
  só recebia SteamGridDB.

  - **Cobertura das fontes ampliada**: `SYSTEM_MAP` (ScreenScraper) e
    `PLATFORM_MAP` (LaunchBox) ganharam PS2/NGC/WII/PSP/3DS, que antes
    só existiam pro libretro. Nada foi chutado: cada id do
    ScreenScraper foi conferido com uma busca real contra a API
    (PS2=58 Gran Turismo 4, NGC=13 Metroid Prime, WII=16 Super Mario
    Galaxy, PSP=61 Daxter, 3DS=17 Fire Emblem Awakening - o PSP tinha
    dado 0 no primeiro teste, mas era o NOME do jogo que não batia, não
    o id), e os nomes de plataforma do LaunchBox foram validados pela
    contagem do índice reconstruído (PS2 4671, WII 2172, PSP 1988, 3DS
    1650, NGC 760 jogos - nome errado teria dado 0).
  - **Cascata de 4 fontes** em `run_heavy_fetch_covers_job`, da melhor
    curadoria pra mais genérica: libretro-thumbnails -> ScreenScraper
    -> LaunchBox -> SteamGridDB, cada passo só tentando o que sobrou.
    Detalhe que era necessário: ScreenScraper/LaunchBox reprocessam a
    partir do `registry` (só quem está "no_match"), então quem nunca
    passou pelo libretro (PS1) precisou ser marcado antes, senão as
    duas não tinham o que fazer.
  - **ScreenScraper virou fonte da Biblioteca também**
    (`PLATAFORMA_SCREENSCRAPER` + `_find_cover_screenscraper`), entre a
    Steam e o SteamGridDB - motivado pelo perfil real do que faltava:
    57 dos 120 sem capa eram de Switch, que a Steam não cobre e o
    SteamGridDB não achava. Switch entrou no `SYSTEM_MAP` como "NSW"
    (id 225, conferido com Astral Chain) só como fonte de capa - não é
    sistema de ROM do PyRetro.

  Resultado do pente fino: **ROMs pesadas 284 -> 299 de 310 (96%)**,
  com o PS1 saindo de 115 pra 127 de 132; **Biblioteca 581 -> 593**
  (os 12 novos todos via ScreenScraper, todos de Switch). Sistemas
  leves conferidos e já estavam 100% (0 sem correspondência, 0 sem
  capa). Zero erro em toda a bateria.

- **Correção no mesmo dia: "PSN (digital)"/"PSN (físico)" não deviam
  virar aba** - o usuário mandou print mostrando as 4 abas
  ("PSN (digital)", "PSN (físico)", "PlayStation 3", "PlayStation 4")
  e disse "continua errado aqui do solicitado". Ele tinha pedido "o
  ideal é ter PlayStation 3 e PlayStation 4 apenas, e no jogo colocar a
  label PSN (digital) e Físico" - eu curei a plataforma (item 2 da
  sexta leva) mas deixei a FONTE virar aba do mesmo jeito, então
  sobraram as duas abas a mais. `TAB_NAO_AGRUPA` novo: rótulo que
  descreve COMO o jogo é possuído (não ONDE ele está) aparece no card
  mas nunca vira aba. Agora as abas são só as plataformas/lojas, e o
  card segue mostrando "PlayStation 4 · PSN (físico)".

- **Oitava leva: troca de capa, nome errado, Switch só da pasta, editor
  de todos os campos** - 4 achados do usuário depois de passar o pente
  fino na mão.

  1. **"Não é possível substituir capa"** - o arquivo ERA substituído no
     disco; o que não mudava era a tela. `/images` e `/library-images`
     servem sem nenhum header de cache, e a URL da capa era sempre a
     mesma - o navegador não tinha motivo pra buscar de novo e seguia
     mostrando a imagem antiga (cache heurístico). A galeria leve já
     driblava isso com `?t=Date.now()` no refresh, mas Biblioteca,
     pesadas, Ranking e Iniciados não. Corrigido na raiz com
     `com_versao()`: toda URL de capa sai do servidor com
     `?v=<mtime do arquivo>`. Trocar o arquivo troca a URL (aparece na
     hora); arquivo intocado mantém a URL e segue cacheado - importante,
     porque a grade tem centenas de imagens e desligar cache pra todas
     seria pior. `/api/library` passou a devolver `capa_url` pronta em
     vez do caminho cru, pro cliente não remontar a URL e perder a
     versão. Testado ao vivo: troquei a capa do Celeste por outro
     candidato, `?v=1787858110` -> `?v=1787946242` e a imagem nova
     carregou na hora (depois restaurei a original, que veio de volta
     da fonte oficial da Steam).
  2. **"Where's is my water?" -> "Where's My Water?"** - corrigido no
     dado. O `id` foi mantido de propósito (`where-s-is-my-water-ios`):
     ele é chave opaca desde a criação, e recalcular quebraria as
     referências.
  3. **Switch: só a pasta NSW, sem a lista de texto** - "retirar do
     Nintendo Switch o que está no txt, focar só na pasta NSW mesmo".
     Removidos 157 registros que só vinham do `Jogos Switch.txt`.
     **Um foi preservado de propósito**: "Portal" tinha nota 9.4 e
     estava finalizado - justamente o caso que o usuário tinha citado
     antes ("Portal eu fechei e dei nota"). A regra usada foi: sai só
     quem não está na pasta E não tem NENHUM progresso registrado
     (nota/iniciado/finalizado/platinado/tempo/comentário). Switch ficou
     com 130 (129 da pasta + Portal); biblioteca 703 -> 546. As capas
     dos removidos continuam em `library_root/capas/` - se algum voltar
     pra pasta, já volta capeado.
  4. **Editor de todos os campos** ("estender o editar nome para todos
     os campos") - `EDITABLE_FIELDS` foi de 7 pra 15, incluindo `nome` e
     `plataforma`, que eram CLI-only. Editar os dois é seguro porque o
     `id` NÃO é recalculado (mesma razão do item 2). Continuam fora:
     `id` (chave) e `fontes` (é posse confirmada por API, não opinião -
     muda via library-refresh/library-add). Endpoint novo
     `POST /api/library/edit` grava vários campos de uma vez e é
     tudo-ou-nada: valida numa cópia antes de tocar no arquivo, pra um
     valor ruim no meio não deixar metade salva. Botão ✎ no card abre o
     formulário. Testado: nome vazio -> 400 "nome não pode ficar
     vazio"; data "banana" -> 400 com a dica de formato; edição válida
     -> 200 e persistiu, com o `lancamento` original intacto depois das
     duas recusas.

- **Renomear precisava sobreviver à próxima sincronização** - o usuário
  viu o furo assim que o editor de nome ficou pronto: "tem que manter
  de alguma maneira que o jogo foi renomeado, para ele não aparecer de
  novo em novas verificações". Procedente e sério - o `merge_owned`
  casa por NOME, e a fonte externa (Steam/Epic/pasta do Switch)
  continua mandando o nome ORIGINAL pra sempre; renomear pela tela
  quebrava esse casamento e o próximo `library-refresh` recriaria o
  jogo como registro novo, duplicado e sem o progresso.

  Campo `nomes_alt` novo no registro: `update_game` empurra o nome
  antigo pra lá sempre que o `nome` muda, e tanto `merge_owned` quanto
  `index_by_rom_name` (usado pelo cruzamento com ROM) passaram a
  indexar nome atual + apelidos via `nomes_para_match`. Migrados os 546
  registros existentes, e o rename manual do "Where's is my water?" que
  eu tinha feito direto no arquivo (antes do mecanismo existir) ganhou o
  apelido correspondente.

  Confirmado que o bug era real antes de dar por resolvido: renomeando
  SEM apelido, o merge devolve `added=1` e a biblioteca vai pra 2
  registros; COM apelido, `added=0`, 1 registro, nota preservada.
  Testado também ponta a ponta pelos endpoints reais - renomeei "A
  Plague Tale: Innocence" pelo `/api/library/edit`, rodei
  `library-refresh heroic` (a Epic manda o nome antigo) e continuou
  "0 novo(s), 198 já rastreado(s)"; depois revertido. O cruzamento com
  ROM também honra apelido (`find_for_rom` acha pelo nome anterior).

- **"Cliquei em finalizado e não consigo mais acessar"** - investigado
  e resolvido em duas frentes.

  **Causa imediata (minha):** eu estava reiniciando o servidor várias
  vezes durante a sessão enquanto o usuário usava pelo celular. Pior:
  o comando `pkill -f "python3 gui/server.py" && nohup python3
  gui/server.py &` mata o próprio subshell junto (o pkill casa com o
  comando que está subindo), então em algumas dessas o servidor
  simplesmente FICOU FORA DO AR até eu perceber. Reproduzido de novo
  durante esta investigação (ps mostrou 0 processos depois do
  "restart"). Passei a subir o servidor sempre num comando separado.

  **Causa latente (de código, que teria dado o mesmo sintoma sozinha):**
  `save_library` fazia `path.write_text()` direto no arquivo final. A
  GUI é multi-thread (`ThreadingHTTPServer`) e ainda por cima eu rodei
  `library-refresh`/`fetch-covers` em paralelo com o usuário mexendo na
  tela - qualquer leitura que caísse no meio de uma escrita pegaria um
  JSON truncado, o `json.loads` estouraria e a tela não carregaria:
  exatamente "cliquei e não acesso mais". Corrigido:
  - `save_library` agora grava num `.tmp` e troca com `Path.replace`
    (atômico no mesmo filesystem) - quem lê sempre vê a versão inteira,
    a antiga ou a nova, nunca um pedaço.
  - `_library_lock` (RLock) novo em `gui/server.py` serializa o ciclo
    ler-modificar-gravar dos 5 endpoints que escrevem na biblioteca
    (`/api/library/update`, `/track`, `/edit`, `/cover_upload`,
    `/api/cover/apply_url`). Sem isso, duas escritas concorrentes
    davam "lost update": as duas carregavam a mesma versão e a última a
    gravar apagava a alteração da outra - uma marcação de "finalizado"
    sumindo sozinha. O resto do `do_POST` (jobs, memory card, organize)
    segue em paralelo como antes.

  Testado: 12 escritas SIMULTÂNEAS em jogos diferentes -> 12 respostas
  200, as 12 gravaram de verdade, arquivo íntegro (546 jogos). E o
  fluxo real na tela: marcar finalizado reflete no disco e desmarcar
  reverte. Dados de teste revertidos.

- **Nona leva: Switch do NSWTL, cascateamento de flags, cadastro manual
  guiado — e validação profissional do código.**

  1. **22 jogos de `~/Downloads/NSWTL-torrents/`** entraram como Switch
     (20 novos + 2 já rastreados), com as tags de formato removidas do
     nome. 19 dos 22 já saíram capeados; os 3 que faltam são coletâneas
     com nome não-oficial ("Touhou Project for Nintendo Switch",
     "Windjammers 1-2", "Baldurs Gate and Baldurs Gate 2 Enhanced
     Editions"), que se resolvem pelo 🖼 editando o termo de busca.
     (Contei "21" de olho ao ler o `ls` e o usuário pegou: eram 22 - o
     script já tinha contado certo, nada ficou de fora.)
  2. **Cascateamento das flags**: marcar `platinado` marca `finalizado`
     e `iniciado`; marcar `finalizado` marca `iniciado`. Desmarcar faz o
     caminho inverso (desmarcar `iniciado` limpa os outros dois) - senão
     dava pra ficar com "platinado mas não iniciado", exatamente o
     estado incoerente que gerou confusão. Ao concluir um jogo sem nota,
     a tela pede a nota na hora.
  3. **Cadastro manual guiado**: o "+ Lista" exigia digitar a tag
     técnica da fonte (`psn:fisico`), o que na prática impedia usar.
     Agora tem preset de Nintendo Switch / PlayStation 4 e 3 (digital ou
     físico), com "Outra" revelando os campos livres.
  4. **Falha de gravação agora é visível**: erro de rede no salvamento
     de uma flag estourava sem `try/catch` e nem o alerta aparecia - a
     tela ficava marcada e o disco não, dando a impressão de "bugou".
     Agora avisa e orienta a recarregar.

  **Auditoria (pedido: "chegar num nível bem profissional")**

  - **Travessia de caminho na escrita de capa (grave)**: os endpoints
    montavam `capas_dir / f"{label}.png"` com o label vindo da
    requisição, sem checar nada - e o servidor escuta em `0.0.0.0`, ou
    seja, qualquer um na rede local. No primeiro teste só falhou por
    ACASO (a contagem de `../` caiu numa pasta inexistente); com a
    contagem certa gravaria em qualquer lugar gravável. Corrigido em
    `_cover_path`, que é o funil de todos os endpoints de capa, mais os
    helpers `nome_de_arquivo_seguro`/`dentro_de` (este resiste a
    symlink). Reconferido depois: 5 payloads maliciosos bloqueados,
    nada escrito fora, e nome de jogo legítimo com apóstrofo/parênteses
    continua funcionando.
  - **Exceção não tratada matava a conexão**: qualquer erro imprevisto
    derrubava a requisição sem resposta nenhuma - do lado do celular
    isso aparece como "bugou", sem pista do motivo. Agora vira 500 com
    mensagem, e o traceback vai pro terminal.
  - **Suíte de testes criada** (não existia nenhuma): 32 testes,
    `unittest` da stdlib, sem dependência - `python3 -m unittest
    discover -s tests`. Cobrem as regras que quebram em silêncio
    (identidade de jogo, merge, rename, validação, atomicidade,
    segurança de caminho). Cada teste cita o problema real que o
    originou.
  - **Defeito encontrado PELOS testes**: renomear A->B->A deixava "B"
    como apelido permanente. Não é cosmético - se outro jogo se chamar
    "B" de verdade, a fonte da loja cairia no registro errado (cenário
    "Portal"/"Portal 2"). Corrigido em duas frentes: o nome vigente
    nunca fica na lista de apelidos, e o casamento por nome vigente tem
    prioridade sobre o casamento por apelido. Virou teste de regressão.
  - Removido um import órfão (`urllib` em `core/launchbox.py`).
    Varredura não achou `except:` nu nem `except Exception: pass`.
  - Tempo de resposta medido: `/api/library` 0,26s com 566 jogos,
    `/api/covers/SFC` 0,06s - sem gargalo a atacar.

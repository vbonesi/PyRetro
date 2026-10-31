# Changelog

## 29/10/2026 (noite) — Sinopses dos Desejados

- Os 239 jogos de Desejados (Steam 115, PSN 26, Xbox 98) ganharam `sinopse` em pt-BR (3 agentes com busca na web, mais fechamento de KAKU - Ancient Seal,
  Geoplanetical e retoque de Onimusha: Way of the Sword). Os lançamentos de 2026 (Pragmata, RE Requiem, Reanimal, Replaced, Life is Strange: Reunion,
  Blood of Dawnwalker, Subnautica 2) foram conferidos por busca. Menos verificados: Moss: The Forgotten Relic, Gestalt: Steam & Cinder, Fate Seeker II,
  Esoteric Ebb, Shutter Story, Witchbrook, Dead Static Drive, Transference, Visage, The Ninja Saviors, Out of Words.
- Observação aberta: Tropico 7 está com desenvolvedora Limbic; a busca indica Gaming Minds (não alterado).

## 29/10/2026 — Sinopses: levas complementares e conferência do catálogo completo

- Preenchidas **885 sinopses novas** em português, com textos completos ScreenScraper, páginas
  de editoras/autores, manuais e LaunchBox; fontes secundárias identificadas quando necessárias.
  Textos anteriores preservados e seis resumos desta própria rodada refinados. Os recibos privados
  conferem a preservação dos demais campos, dos IDs e da quantidade de registros.
- A lista `/api/library` omite ROMs já apresentadas nas abas dos sistemas. A conferência também
  considerou o catálogo completo e encontrou outros 305 campos vazios fora dessa lista inicial.
  Resultado: **2.549 de 2.568 jogos visíveis**, excluídos os registros somente de Desejados, com
  sinopse; **19 pendentes** por identidade, plataforma ou fonte insuficiente. Nenhum cadastro foi
  corrigido por aproximação de nome. Listas e fontes detalhadas permanecem na auditoria privada.
- Descrições incorretas de The Last Revelation e Digital Devil Saga 2 foram recusadas antes da
  gravação; as fontes corretas sustentam os novos textos. A leitura completa também recuperou
  Armadillo e Pokémon Water Blue, antes rejeitados a partir de trechos incompletos.
- 469 testes Python e 58 de interface aprovados. Escritas pela API normal, com diário da Biblioteca;
  sincronização automática conferida sem erro. Sem mudança funcional, instalação de APK, execução
  de jogos, remoção ou alteração de saves/ROMs.

## 29/10/2026 — Conclusão do lote Mega Man

- Conferidos os nove arquivos de sete jogos no Drive: Mega Man 8/X5/X6 (PS), ZX/ZX Advent (DS)
  e 9/10 (WiiWare). Hashes remotos iguais aos preparados; payloads iguais aos originais de Downloads.
  Catálogo do PC atualizado e os sete vínculos com os registros existentes conferidos; capas cadastradas
  também copiadas para as pastas dos sistemas, com hashes iguais e resposta HTTP 200 no modo TV.
- Biblioteca e índice do celular atualizados: sete cadastros com capa, gênero, desenvolvedora, lançamento
  e sinopse; cinco ROMs de PS/DS disponíveis para baixar no app. Wii permanece no PC. Captain Spirit
  conferido como registro único com fonte Xbox, nota 9,5 e platinado preservados.
- Sete originais de Downloads enviados à lixeira após a conferência, preservando o arquivo fora do lote.
  Lista de reposição atualizada localmente e no Drive: 63 itens principais e cinco linhas opcionais.
  IMG/SUB antigos do X6 enviados à lixeira do Drive após autorização explícita; CHD novo preservado.
- Nenhum jogo foi iniciado nesta conferência. O CUE de uma faixa do Mega Man 8 preparado pelo Claude
  foi preservado, com cópia privada do CUE original malformado; integridade e referências não comprovam
  reprodução de áudio nem homologação em emulador.
- Verificação do projeto ao encerrar: 469 testes Python e 58 testes JavaScript aprovados.

## 29/10/2026 (noite) — Desenvolvedora, lançamento e capas pelo LaunchBox

- `desenvolvedora`/`lancamento` preenchidos em **2.338 registros** que estavam vazios (agora 2.474 e 2.494 de 2.826), pelo
  Metadata.xml do LaunchBox: nome normalizado EXATO (nome + `nomes_alt`, com/sem "The") só na plataforma do registro
  (ROM → `PLATFORM_MAP`; Steam/Epic/GOG/Amazon → Windows; Switch → Switch; Xbox/PSN → consoles da loja). Nada foi sobrescrito.
  Ficaram sem casamento 326 (Switch 50, Steam 44, GBA 34 — hacks e traduções —, Xbox 28...).
- 30 valores que já existiam divergiam do LaunchBox. Com o OK do Victor, 20 foram trocados (19XX, Aerial Assault, Age of
  History II, Captain Spirit, Crime Scene Cleaner, FIFA 21, Football Manager 2016, TLOU Left Behind, The Sims 1/2/4,
  Where's My Water?, Zoo Tycoon UAC, Portal do Switch). Ficaram 10 em que o valor antigo é o certo e o LaunchBox erra
  (editora no lugar do estúdio, data de relançamento): FIFA 23, Fractured Minds, Limbo, Minecraft Dungeons, Streets of Rage 2,
  When the Past was Around, WorldBox, Yu-Gi-Oh! FM e Life is Strange: True Colors. Listas e backups (`library.json.antes`,
  `.antes-divergentes`) em `~/Games/PyRetro/Backups/Metadados LaunchBox 2026-10-29/`.
- Achado: Captain Spirit tem dois registros no Xbox One (um com o progresso do Victor, outro vindo da sincronização do Xbox).
- Capas: 32 de arcade que não tinham capa nem thumbnail do sistema (libretro FBNeo; Out Run e Oriental Legend escolhidas à mão;
  Chibi Maruko só tem a arte genérica do Neo Geo) e a do Trials of Mana do Switch, que estava com a do SNES (agora a do remake,
  LaunchBox). Sem capa ainda: Geoplanetical (Steam) e os 6 Twinmotion ocultos.

## 29/10/2026 (noite) — Sinopses: lojas, Google e ScreenScraper (1ª leva)

- **1.263 de 2.264 jogos** da Biblioteca já têm `sinopse` (máx. 297 caracteres, 2–3 frases em pt-BR). Origem: Steam pt-BR (97),
  busca no Google por dois agentes (332 jogos de Epic, GOG, Xbox, PS, Amazon, Android, iOS) e ScreenScraper (765 jogos retrô,
  arcade e Switch, textos condensados/traduzidos por seis agentes). A outra conversa cadastrou 67 jogos a repor já com sinopse.
- Regra mantida: gravação só em jogo sem sinopse, por `/api/library/edit`; nada sobrescrito. Textos de fonte ruim (notas de patch,
  comentário de usuário) não foram usados; esses jogos ficam para a rodada do Google.
- Pendente: coleta do ScreenScraper em curso (~1.125 de 1.764 jogos consultados, 1 consulta por vez), segunda leva dos que sobrarem,
  e Google para os jogos sem texto em qualquer fonte (Switch 106 sem, arcade 15 de 231, Mega Drive 6 de 200, etc.).

## 29/10/2026 (noite) — Limpeza das coletâneas do Switch e 1 pasta = 1 jogo

- Victor decidiu ficar na emulação (sem ports nativos). Saíram da Biblioteca 262 registros de coletâneas de Switch cobertas
  ou dispensadas, e as 182 pastas no NSW foram para a lixeira do Drive (~114 GB). Ficaram SEGA AGES Phantasy Star/Out Run e Eschatos.
  Backup: `~/Games/PyRetro/Backups/Limpeza Switch 2026-10-29/`.
- `merge_owned`: a fonte `switch` só casa com registro de Switch (`FONTES_SO_DA_PLATAFORMA`). Antes, a pasta do Switch virava
  fonte da ROM de SNES/NES (FF II–VI, Trials of Mana) ou de um registro de Steam/Xbox (FF VII, Stardew...). Corrigidos os 21 registros,
  criados 9 de Switch, juntados os duplicados de Twilight Princess e Tales of Vesperia. Agora: 238 pastas = 238 jogos de Switch.
- Cadastrados 67 jogos de ROMs que o Victor vai repor (vindos das coletâneas), ainda sem arquivo: capa (LaunchBox/libretro),
  gênero, desenvolvedora e lançamento (Metadata.xml do LaunchBox) e sinopse. Lista em `~/Drive/Jogos/Switch - jogos que faltam na emulação.txt`.
  MK4 e Salamander 2 de arcade ficaram de fora (o FBNeo não roda).

## 29/10/2026 (noite) — Sinopses dos jogos da Steam

- Preenchida a `sinopse` de 97 jogos de loja (Steam e relacionados): textos da Steam em pt-BR (`appdetails`, `l=brazilian`) resumidos
  em 2–3 frases por Claude; os que vieram em inglês/espanhol foram traduzidos. Para Civ V, Papers Please, Rise of the Tomb Raider,
  Super Meat Boy, Football Manager, Sims, Witcher 3 CE e outros em que o texto da Steam não descrevia o jogo, o resumo é do conhecimento do Claude
  (jogos bem conhecidos). Em aberto na Steam: Fishing Planet e Business Tour (para a rodada do Google).
- Próximas fontes: ScreenScraper (retrô/arcade) e Google para o restante. Gravação por `/api/library/edit` com o servidor no ar.

## 29/10/2026 (noite) — Campo Sinopse em todos os apps (Android 0.23.0)

- Novo campo `sinopse` no registro da Biblioteca: resumo do jogo em português, 2–3 frases, **separado** de `observacoes`
  (o comentário continua só para jogos zerados). Editável como os demais campos de texto (`EDITABLE_FIELDS`,
  `/api/library/track|edit`); `rom_tracking_info` também o devolve. Nenhuma migração: o campo nasce vazio e o journal já sincroniza
  campos arbitrários.
- Modo TV: a ficha mostra a sinopse sob o título; ✎ Editar tem o campo. Web: o campo está em ✎ Editar e o resumo aparece como
  dica (hover) no nome do card da Biblioteca. Android **0.23.0 (code 34)**: texto na ficha do jogo e campo "Sinopse (resumo do jogo)"
  no ✎ Editar dados; instalada e conferida no celular depois de "Atualizar Biblioteca e catálogo".
- Testes: 467 Python, 58 JS (o mock do modo TV passou a responder `/api/setup/status`), JVM + lint do build aprovados.
- Combinado com o Victor para preencher: Steam (`appdetails` em pt-BR) → ScreenScraper (pt) → o que ficar em branco, busca no Google
  e resumo/tradução pelo Claude em 2–3 frases; só texto com fonte real. Registro de teste: Super Metroid já tem sinopse.

## 29/10/2026 (noite) — Moonlight e Steam Link validados na janela nativa

- Victor confirmou: Moonlight com o PyRetro primeiro no Sunshine e o PyRetro aberto pelo Big Picture da Steam.
  Pendências restantes: atalhos Azahar/Lime3DS no celular, G8 prolongado e perfil do G8, e depois a retirada do
  override `/run/udev:ro` do Chrome (pelo setup).
- Decisão do Victor: o G8 é só para emergência (PS4 e Xbox são o uso diário) e já foi bem testado na navegação. O perfil
  de emuladores do G8 (`configure_xbox.py --learn galileo-g8`) fica adiado: corrigir se der problema no uso.

## 29/10/2026 — Arcade pelo título completo, em todo o PC e no Android 0.22.1

O arquivo de Arcade é o código do set (`kof97`), e o DAT traz o título com o código de revisão
(`The King of Fighters '97 (NGM-2320)`). O Android 0.22.0 só tirava etiquetas conhecidas, então o nome
não batia com o cadastro e o jogo ficava sem capa. Corrigido no Android (0.22.1, só Arcade, edições dos
outros sistemas continuam separadas) e no PC por uma regra única, `library.rom_name_keys`/`records_for_rom`/
`find_for_rom`, que usa a tabela do libretro em cache e a `<description>` do DAT do FBNeo (`arcade.load_titles`),
sem rede. Isso passa a valer para tempo de jogo ao abrir um Arcade (antes `kof97` não achava o cadastro),
Sortear, gêneros, renomear, cadastro explícito de ROM e **proteção de remoção de jogo iniciado**, que também
não reconhecia o código curto. Reinicie o `pyretro-gui` (com o modo TV fechado) para valer no servidor.

Nuvem: criação da pasta-pai uma vez antes dos envios paralelos (o Drive aceita pastas com o mesmo nome e o
upload paralelo criou 8 `states/`); árvores reorganizadas e verificadas por hash por outra sessão; 57 blobs
de saves repetidos (idênticos por MD5) removidos para a lixeira do Drive. Pastas antigas `Saves`, `Biblioteca`
e `Backups` do Drive comparadas por hash com o PC: sem perda.

## 29/10/2026 — Android 0.22.0 instalado e fechamento da revisão

Biblioteca, Desejados, cadastro, edição e estatísticas usam dados locais; novas sessões e alterações
entram no diário. Catálogo Arcade recebe nomes e dependências do DAT para vincular nomes curtos sem
cache do notebook e proteger pais. Operação individual “Esquecer” usa marcador v2, confirmação,
revalidação e histórico; uma edição offline divergente vira conflito, sem exclusão em lote de saves.

No aparelho: 96 verificações de interface (48 em cada fonte 80%/130%, ambas as orientações), SQLite
real, falha/retry de saves, SAF/fila e remoção/restauração sintética passaram. Os 231 arquivos reais
inventariados mantiveram nomes, tamanhos e datas. Fonte/rotação restauradas. Ícone instalado e nove
máscaras/temas renderizados; launcher temático real e Steam Big Picture ainda exigem conferência.
BIOS Neo Geo em system/fbneo tem MD5 igual ao PC; FBNeo iniciou KOF '97 sem arquivos faltantes,
com configuração/saves temporários e config original preservada. 103 JVM, 58 JS e build/lint aprovados.
448 Python passaram antes da integração do teste adicional do Claude, aprovado na suíte focada.

## 29/10/2026 — Integridade de Backups e prevenção de nomes duplicados no Drive

A contagem de 505 caminhos escondia diretórios homônimos criados por uploads concorrentes. Foi
montada uma árvore nova, verificada por hash e promovida: 505 arquivos de Backups e nove objetos de
estados. As árvores antigas ficaram em `*-preservado-20261029-*`, mantendo seus IDs e arquivos.
Criação de pastas e escritas no mesmo destino agora usam trava entre instâncias/processos no PC;
Android serializa escritas e só aceita aliases de arquivo com tamanho/checksum iguais. Divergências
bloqueiam a operação. Testes concorrentes conferem unicidade e uploads paralelos de destinos distintos.

## 29/10/2026 — Perfil automático do controle antes de Dolphin/Azahar

`configure_xbox.py --auto --apply` exige um único controle com GUID/nome já medidos. Configuração
fica bloqueada com emulador aberto, é idempotente, grava com cópia anterior e preserva o perfil
em ausência/ambiguidade/erro. Só bindings dependentes do modelo são selecionados, sem reaplicar
o layout do 3DS. Setup chama esse modo antes de GC/Wii/3DS, com prazo limitado; simulação não chama.
Nove testes do configurador e nove do lançador passaram. Sondagem física não encontrou controles;
G8 e alternância entre aparelhos ainda não homologados.

## 29/10/2026 — Remoção com revalidação no Android e prova PC/Drive

Ficha Android oferece celular, Drive ou ambos: prévia por arquivo, versões/hashes, proteção de
iniciados/fixados/fila, preservação de faixas compartilhadas e resultado por item. ROM local vai
para nomes .pyretro-trash- na própria pasta e pode ser restaurada em Opções; Drive usa a lixeira.
Saves, estados e cadastro permanecem. Arcade com dependências não verificadas bloqueia a remoção
no Android e orienta usar o notebook. Instrumentação SAF descartável preparada; celular desconectado.

PC agora analisa os descritores do próprio Drive, preserva faixas compartilhadas e inclui versão
local/hash remoto no token. Prova real com arquivo sintético próprio em FC: MD5 igual antes,
duas remoções aprovadas, arquivo local ausente e ID remoto conferido na lixeira do Drive.
437 testes Python e testes JVM/build auxiliar/lint aprovados; nenhuma ROM/save real foi removida.

## 29/10/2026 — Conflitos de saves no modo TV e regressões da interface

Ferramentas → Saves na nuvem compara, sincroniza sem resolver conflitos automaticamente e oferece
escolhas por dispositivo/hash, com confirmação e nova tentativa após falha. A tela de remoção
descarta prévias atrasadas ao trocar de escopo; aplicação envia o escopo da prévia exibida.
57 testes JavaScript passaram, incluindo pódio/empates, filtros recolhíveis, glifos Xbox/PS,
falha/retry de conflito e remoção com resposta fora de ordem. Dados de teste isolados.

## 29/10/2026 — Android 0.21.0: capas sob demanda e escopo de saves

Capas exibidas no PC ou Android vão para blobs por SHA-256 com ponteiro por jogo; versões antigas
permanecem. Android consulta a nuvem diretamente, preserva cache offline e pode buscar a capa
original em Jogos/Biblioteca no Drive. Pré-busca não publica capas de jogos ainda não exibidos.
Nenhuma varredura/envio dos 2,1 GB foi criado. Limites de leitura e hashes são conferidos.

Saves PSP/3DS na ficha usam ID verificado/escolhido, pedem região e árvore quando há ambiguidade;
sem evidência há uma opção explícita para todos os jogos do emulador. Extdata não é inferida
pelo Program ID. Rotas HTTP antigas de saves retornam 410, módulo antigo removido e regra pura
extraída para save_paths. 436 testes Python, JVM, build e lint passaram. O total Python diminuiu
pela retirada dos testes do protocolo encerrado. APK final ainda será instalado e conferido.

## 29/10/2026 — Biblioteca local Android, diário e estados por aparelho

Android ganhou SQLite por jogo, bootstrap pelo snapshot e diário imutável compatível com Python.
Progresso, notas, favoritos e sessões novas são gravados localmente e enviados pelo Drive;
pendências anteriores com cadastro migram, conflitos antigos ficam disponíveis para conferência.
Catálogo combina Biblioteca e pastas de ROMs do Drive, preservando ambiguidades para escolha.
Notebook recebe no início, após jogos e a cada cinco minutos; Android usa WorkManager com rede
e bateria suficiente (período de 15 minutos, sujeito ao agendamento do sistema).

LWW compara todas as origens por campo; relógio persistente avança mesmo se a hora recuar.
Recibos só avançam após gravação local. Sessões têm identidade imutável, sem importar totais
históricos ou repetir eventos do PC. Saves/extdata 3DS continuam compartilhados por decisão do
Victor; estados novos usam `states/<dispositivo>` e o histórico anterior permanece intacto.
444 testes Python passaram, fixture Python/Kotlin convergiu nas 24 ordens, JVM passou e teste
SQLite real do celular comprovou persistência, transações/rollback e replay. Validação completa
da interface e instalação final seguem nas próximas entregas; ainda há pendências abertas.

## 29/10/2026 — Android 0.20.0: filtros, Ranking e navegação visual

Desejados agora oferece os seus próprios filtros; filtros são guardados por coleção. Pódio em
retrato usa cartões legíveis na ordem 1–2–3; paisagem mantém 2–1–3. Empates usam nome em
português, plataforma e ID. Glifos automáticos/manuais Xbox/PlayStation/genérico preservam
bindings. Aba ativa e foco têm sinais distintos; a seleção volta ao trecho visível da barra.
Busca e paginação compactas em paisagem, marca PR no cabeçalho, nota especial na ficha e
botão Sortear novamente com filtros preservados. Build/lint e testes JVM passaram; validação
no aparelho será feita junto com as próximas entregas. Saves reais intocados.

## 29/10/2026 — Android 0.19.1: falhas de saves permanecem visíveis

Resolução de conflito só confirma sucesso depois do resultado positivo. Erros de grupos e de
arquivos entram no resumo; exceções mantêm o diálogo e a possibilidade de nova tentativa.
Botões ficam bloqueados durante a operação para impedir ações concorrentes. Uma execução com
falha não atualiza a data de sucesso daquele grupo. 85 testes JVM e build/lint passaram, incluindo
falhas de grupo, arquivo, exceção, conflito e resolução. APK compilado; instalação fica para a
validação conjunta das próximas correções. Nenhum save real foi alterado.

## 29/10/2026 — revisão da interface Android em comparação com o PC (Codex)

Matriz e fila de correções em [REVISAO-ANDROID-PC-2026-10-29.md](REVISAO-ANDROID-PC-2026-10-29.md).
Navegação instrumentada em 48 telas/estados, retrato/paisagem, com fontes 80% e 130% e dados sintéticos; 272 arquivos
de jogos/saves/playlists mantiveram nomes/tamanhos/datas. Paridade ainda incompleta: filtro de
Desejados com opções do Catálogo, pódio em retrato, glifos/foco, remoção no Drive e escopo de
saves PSP/3DS; leitura de código também encontrou confirmação de resolução após erro.
Retirado de `StatusSmoke` o teste de uma API de saves removida, que impedia compilar o APK
auxiliar. Novo roteiro `-e suite interface` e evidências privadas; APK principal 0.19.0 preservado.
Esta entrega não aplica as diferenças no produto nem homologa operações reais por navegação.
435 testes Python, 54 JS e 82 JVM, build/lint e as duas rodadas de instrumentação passaram.

## 28/10/2026 (noite) — Switch: 21 pastas de Downloads organizadas

Lote de torrents em `~/Downloads` (= `Drive/Temp`) organizado direto no Drive (`rclone moveto`, sem
reenvio). 15 títulos novos em `Jogos/ROMs/NSW` sem a tag `[NSZ]/[NSP]`: Omno, Planet of Lana (e II),
Princess Peach Showtime!, Roots of Pacha, Sea of Solitude, Sea of Stars, SMT III Nocturne HD Remaster,
The Gardens Between, Trials of Mana, Unicorn Overlord, Untitled Goose Game, Vampire Crawlers e
Rogue Legacy 1 e 2 (coletânea decomposta). Apagados (lixeira do Drive): 8 títulos já existentes com
arquivos idênticos (Arceus, Shovel Knight ×3, Galaxy 1 e 2, Bowser's Fury, Radiant Silvergun — o update
novo era mais antigo que o do Drive), mods russos (Unicorn Overlord, Arceus, Galaxy 1 e 2), o mod de
áudio LayeredFS do SMT III (versão beta) e o update antigo do Bowser's Fury. Biblioteca: 12 jogos
novos, capa e gênero conferidos (gêneros do LaunchBox corrigidos à mão onde erraram). Fora do lote,
de propósito: coletânea russa de ShootEmUp (ainda baixando, arquivos `.part`) e Outbound.

## 28/10/2026 — registro da auditoria independente

[Resultados e fila de correção](AUDITORIA-2026-10-28.md) para a base `721b9be`:
356 Python, 50 JavaScript e 69 JVM passaram; build Android reproduzido e lint
sem erros. Registrados três defeitos reproduzidos com fixtures (save inicial,
CUE incompleto e colisão de nomes), exposição de identificador em documentação
e conciliação do roadmap. Nenhuma correção de código, instalação ou operação
em dados reais nesta entrega documental. O plano de melhorias posterior segue
em sua frente própria.

Histórico detalhado do que foi feito, quando, e por quê - bugs achados,
testes realizados, decisões de desenho e o raciocínio por trás delas.
Pra "o que está pronto hoje" e "o que vem a seguir", ver
[`docs/roadmap.md`](roadmap.md) - este arquivo é o registro, não o
plano.

## 23/10/2026 (12) — Saves do Azahar (3DS do PC) no Drive

- A pasta `sdmc` do Azahar (`~/.var/app/org.azahar_emu.Azahar/data/azahar-emu/sdmc`) foi movida para
  `~/Drive/Jogos/Saves/Lime3DS/sdmc`, onde o PyRetro procura os saves de 3DS do PC (grupo
  `3ds-saves`), e no lugar antigo ficou um link. O Flatpak ganhou acesso só a
  `~/Drive/Jogos/Saves/Lime3DS` (`flatpak override --user --filesystem`); a leitura e a escrita de dentro do
  sandbox foram conferidas. Cópia do antes em `Backups/azahar_sdmc_2026-10-23_antes/`.
- O PC tinha um único save, Poochy & Yoshi's Woolly World (`00040000001a4100`), e o manifesto do PyRetro já o lista.
  O celular usa a mesma árvore (ID de console só com zeros) e tem outros jogos, sem nenhum em comum.
  Nada foi sincronizado: isso continua sendo uma ação explícita no app.

## 23/10/2026 (11) — Organizar a partir dos Downloads (PC e celular); Android 0.14.0

Pedido do Victor: organizar as ROMs baixadas (lote do romsportugues.com e uma ROM hack com capa
ao lado), já com gênero e capa, sobrescrevendo repetidas, tanto pelo modo TV quanto pelo celular.

- **Organizador novo** (`core/organize.scan/organize`, rotas `/api/organize/pending|move|discard`):
  origens `ROMs/0-Organizar` e **`pc.downloads_dir`** (padrão `~/Downloads`); ROMs dentro de
  `.zip/.7z/.rar` viram linhas próprias (lidas pelo `7z` sem extrair; o `.cue` é lido para saber
  quais `.bin` são faixas), patches `.bps` ignorados, `.crdownload/.part` aparecem como "baixando"
  e não podem ser mexidos. Mover extrai só o necessário, limpa os nomes, **reescreve o `.cue`**
  para os nomes novos das faixas, **substitui** o que já existe (o antigo vai para a lixeira) e
  manda para a lixeira o compactado esvaziado e a imagem usada como capa. **Capa:** imagem ao
  lado com o mesmo nome (prioridade) ou candidato com o nome exato nas bases de ROM (nunca
  "parecido"; uma fonte fora do ar não impede a próxima). **Gênero:** ScreenScraper e LaunchBox,
  gravado no cadastro. **Descartar** manda para a lixeira.
- **Modo TV** (Ferramentas → Organizar) e **Android 0.14.0** (Opções → 🗂 Organizar ROMs novas)
  usam essas rotas; os dois foram usados de verdade (Flicky pelo celular, Hook pelo modo TV).
- **Limpeza de nomes** (`core/sanitize`): região `BR-U-E`, patch `T107-Beta`/`T201_RC5`, `(DUB)`,
  site sem domínio e o grupo tradutor colado na versão do patch (`(DindoeCia) (T2.0)`,
  `(T1.0) (Starman)`); `(Track N)`, região, idioma, revisão e disco continuam.
- **Organizados (15):** SNES Brain Lord, Hook, Popeye, Terranigma (Brain Lord e Popeye
  substituídos); MD Flicky; GBC Lufia - The Legend Returns; GBA Metroid - Zero Mission
  (substituído), ProjectZM, Revamp, Pokémon Ghost Grey Version v103 (capa da imagem deixada pelo
  Victor; a edição coreana do mesmo zip foi para a lixeira); PS1 Bakusou Dekotora Densetsu
  (3 faixas), Vagrant Story, Vandal Hearts II; PS2 Castlevania - Lament of Innocence; PSP
  PoPoLoCrois; depois, GBA Magical Vacation (capa LaunchBox, RPG), o último download. Pasta de
  Downloads vazia no fim. Capas e gêneros completados à mão onde as bases não tinham nome igual: hacks do
  Metroid com a capa do original e Ação, Ghost Grey RPG, Bakusou Corrida (capa "Art Truck
  Battle", o primeiro da série), Vagrant Story (USA), Castlevania pelo SteamGridDB.
- Testes: 356 Python (8 novos em `test_organize_downloads.py`), 50 JS; JVM sem mudança.

## 23/10/2026 (10) — Saves criados por testes removidos (com cópia)

Pedido do Victor: apagar saves feitos em testes. Levantamento de tudo alterado desde 15/10 em
`RetroArch/saves|states`, PPSSPP, 3DS SDMC e memory cards (celular) e em `~/Drive/Jogos/Saves` (PC):

- **Removidos** (cópia em `Backups/Saves de teste removidos 2026-10-23/`): `7th Dragon.sav` e
  `.state.auto` no PC (criados 22/10 11:25–11:29, na sessão de teste do melonDS; único save de
  DS) e `The Adventure of Little Ralph.state.auto` no celular (23/10, jogo baixado só para teste).
- Em seguida, removidos também (mesma cópia) o save do Pokémon X no celular (o Victor nunca
  jogou) e, por engano de entendimento, os do Super Mario 64. O Victor tem save de Mario 64:
  **restaurados no PC** (`.srm` e `.state`, datas originais, conteúdo idêntico). **No celular a
  restauração ficou pendente** (desconectado): na próxima conexão, `adb push -a` de
  `Backups/Saves de teste removidos 2026-10-23/celular/RetroArch/{saves,states}/N64/` para
  `/sdcard/RetroArch/{saves,states}/N64/`.
- **Mantidos:** memory cards PS1/PS2 (Gran Turismo 2, Driver, Yu-Gi-Oh! Forbidden Memories,
  Toy Story Racer, Guitar Hero III, NFSU2 — o Victor confirmou que tem save do NFSU2) e o `.ini`
  de GPU do NFSU2 (correção intencional, não é save).

## 23/10/2026 (9) — Pendências 1, 3, 4 e 5: dados reais, CUE/M3U, 3DS e melonDS

Android **0.13.0 (code 21), instalada e validada no celular.**

- **Testes com dados reais (tudo desfeito depois):**
  - Modo TV: Organizar (ROM falsa em `0-Organizar` → GB), aplicar capa (ScreenScraper),
    renomear (ROM + capa), apagar (ROM + capa), Manutenção → backup de configs aplicado (90
    arquivos; pasta do teste removida), Configurações salvas sem mudança (`config.toml`
    idêntico), marcar/desmarcar capa (registro idêntico), textura instalada e removida (36
    arquivos, Spider-Man 2). Registro de capas e `library.json` conferidos iguais aos de antes.
  - App: Tirar da lista, Comprado, salvar edição (só o comentário) e aplicar capa (SteamGridDB)
    num desejado de teste criado pela lista PSN; cadastro e capa apagados no fim.
- **Defeitos achados e corrigidos:** salvar Configurações sempre falhava (`organizar_dir` é nome
  de pasta dentro das ROMs; `device_serial` vazio = detectar); o modo TV perdia o token CSRF
  quando o servidor reiniciava (agora repete com token novo; o envio de mídia busca token
  atual); a busca inicial do SteamGridDB esperava só 15 s (agora 45 s).
- **CUE/M3U (3):** remover pelo app com prévia montada no celular (lê CUE/M3U/GDI como o
  servidor; faixa usada por outro descritor fica; descritor ilegível bloqueia; refaz a análise
  antes de apagar; principal sai primeiro). Validado: prévia do Diablo (2 arquivos; mantido) e
  remoção real da Little Ralph baixada para o teste.
- **3DS (4):** com saves do mesmo título em mais de uma árvore `ID0/ID1`, o app pergunta qual o
  emulador usa e guarda por jogo; e lê o Program ID no cabeçalho NCSD/NCCH da ROM do celular
  quando o notebook não sabe (ROM só no Drive ou jogo sem cadastro), espelhando
  `read_3ds_id`. Validado no Pokémon X (`0004000000055d00`) com uma árvore falsa, apagada depois.
  Observação real: o PC ainda não tem os 2 saves do Pokémon X do celular (não sincronizado).
- **melonDS (5):** o lançador `bonisarch-emulator` (setup `6e5700e`) corrige sozinho o core com
  pilha executável antes de cada jogo de DS; o resto do `PENDENTE-CONSOLIDAR` exige instalação limpa.
- Testes: 349 Python, 50 JS, 69 JVM; setup 154.

## 23/10/2026 (8) — App OAuth publicado; Steam Link e PS4/Xbox remotos homologados

- **Google Cloud (projeto PyRetro):** o Victor preencheu o Branding com as páginas do GitHub
  Pages (`https://vbonesi.github.io/PyRetro/oauth/`, `privacy.html`, `terms.html`) e publicou
  o app OAuth (saiu do modo Teste). Com isso, novas autorizações deixam de vencer em 7 dias.
  O rclone foi reconectado logo em seguida (`rclone config reconnect drive:`, 16:02), já com o
  app publicado: o token novo não tem mais o vencimento de 7 dias. O app Android pode pedir o consentimento de novo
  na próxima vez (tela "o Google não verificou este app" → Avançado → Acessar PyRetro).
- **Homologação física pelo Victor:** Steam Link e sessões remotas de PS4 e Xbox validadas em
  uso real. Continua em aberto: G8 e atalhos do 3DS no jogo.

## 23/10/2026 (7) — Rodada 3: Android 0.12.1, teste das setas e páginas OAuth

Iniciada pelo Codex (que ficou sem tokens no meio) e concluída pelo Claude.

- **Android 0.12.1 (code 20), instalada e conferida:** a ficha de saves comparada pelo Drive diz
  "Iguais no celular e no Drive." e não mostra avisos do notebook; se a comparação com o Drive
  falhar, o aviso fala do Drive (`SaveReviewText`, com teste JVM; smoke de aparelho
  `SaveReviewSmoke`, suíte `save-review`, feito pelo Codex). Conferido no Final Fantasy VI.
- **Teste JS das setas das fileiras:** passa também sem `requestAnimationFrame` (o teste pede
  movimento reduzido, que usa rolagem instantânea); o uso real continua com rolagem suave.
- `tests/test_api.py`: instalação de textura por link não depende mais de DNS real (Codex).
- **Setup:** o commit `dffee8a` (DS/3DS) já estava no `origin` do `setup-linux-bonesi`.
- **Páginas OAuth** (`docs/oauth/`) atualizadas para a integração atual: login da Conta Google no
  app com escopo do Drive (lê ROMs e saves; só cria saves novos ou pendências, nunca apaga ou
  sobrescreve), rclone somente leitura no notebook. Hospedagem: ver orientação no fim de
  `docs/oauth/README.md`.
- Testes: 347 Python, 50 JS, 65 JVM.

## 23/10/2026 — Rodada 2, identidade TV e navegação por mouse/toque (Codex)

- Paleta, ficha e selos alinhados ao Android; Progresso e tempo agrupados,
  ações identificam o PC, capas sem recorte e tema claro preservado.
- Fileiras com setas, roda horizontal com saída nas bordas, zoom preservado,
  toque nativo e alvos de 48 px. Coleções não comprimem/sobrepõem os nomes.
- 💾 depende de consulta explícita bem-sucedida, sem varredura na abertura.
  Duas regressões JS novas cobrem rolagem/limites/390 px e evidência dos selos.
- 343 Python e 50 JS aprovados no worktree sobre `77d8198`; instância principal
  em `localhost:8000/tests/test_app.html` confirmou 48 JS antes da integração TV.
  Prévia conferida com jogos fictícios. Serviço principal não foi reiniciado por
  esta entrega; nenhum Android/adb, ROM ou save real foi alterado.
## 23/10/2026 (6) — Rodada 2 do Codex no main; Android 0.11.0 e 0.12.0 (saves pelo Drive)

Compiladas, **não instaladas** (celular com o Victor).

- **Merge** das entregas 2a–2c do Codex (contrato de saves pelo Drive, `POST /api/library/add-rom`,
  `GET /api/mobile/saves/game` com title IDs). 343 Python OK; servidor reiniciado.
- **Android 0.11.0:** 💾 Saves de PSP/3DS por ID do título (identificado filtra só o jogo;
  vários candidatos viram escolha guardada por jogo, como no Patapon 2 Europa/EUA; sem ID seguro
  abre o grupo inteiro), `SaveIdRules` espelhando `core/game_save_ids.matches`; ROM só do celular
  ganha **📚 Adicionar à Biblioteca**, com favorito/tempo/fixação migrados para a chave do cadastro.
- **Android 0.12.0 — saves pela nuvem (fase 2 da conta Google):** `DriveSaves.kt` compara com
  `Jogos/Saves` do Drive quando o notebook está fora (na ficha e por grupo, "Analisar com o
  Drive"); Drive → celular grava com histórico; celular → Drive cria arquivo novo ou deixa
  **pendência** (o Drive não tem gravação condicional). Detalhes em `docs/drive-saves.md`.
- **PC:** `core/drive_pending.py` + Ferramentas → **☁ Saves enviados pelo celular** aplica as
  pendências com `mobile_sync.receive` (condicional, com histórico); conflito pede escolha.
- Testes: 347 Python (4 novos em `test_drive_pending.py`), 48 JS, 63 JVM.
- **Validada no celular (23/10, 0.12.0):** saves PSP por título no Naruto Shippuden - Ultimate
  Ninja Impact (escolha USA `ULUS10582`, a pasta que já existia no celular; só os arquivos dele;
  "iguais"); Adicionar à Biblioteca com uma ROM falsa (cadastro criado e ligado ao arquivo);
  **saves pela nuvem** com uma pasta falsa `ULUS10582PYTEST` e o Tailscale desligado: arquivo
  novo criado no Drive, alteração no celular virou pendência (Drive manteve a v1), o **Insync
  trouxe `.pyretro-pending` para o PC em ~10 s**, a ferramenta ☁ aplicou (v1 no histórico,
  `.applied`), alteração no PC desceu para o celular com a anterior preservada. Tudo de teste
  foi apagado depois (celular, PC/Drive e o cadastro; `library.json` voltou a 2.985 jogos).
- **Corrigido na validação:** a ficha fecha na hora ao cadastrar; conflitos do Drive dizem
  "Usar a do Drive"; envio pendente que saiu da fila vira a base (sem falso conflito quando o
  PC muda depois); a Situação avisa quando a Pasta RetroArch está em `saves` (caso real do
  celular do Victor: escolha anterior à 0.6.1, os saves do RetroArch não apareciam).

## 23/10/2026 — Rodada 2, saves por jogo (Codex)

- `GET /api/mobile/saves/game?id=...`: seriais PSP do cache Redump existente;
  identificação 3DS por Program ID de cabeçalho NCCH/NCSD local. Sem rede/adb.
- Resultados separam identificado, candidatos que exigem escolha e desconhecido;
  filtros nunca inferem extdata, não incluem content/NAND/histórico. Contrato e
  fontes em `docs/mobile-save-ids.md`. 343 Python e 48 JS aprovados com fixtures.

## 23/10/2026 — Rodada 2, cadastrar ROM do celular (Codex)

- `POST /api/library/add-rom` cria/reaproveita cadastro sem arquivo no PC,
  com lock, CSRF, preservação de progresso e recusa de correspondência ambígua.
- Catálogo mantém código/identidade de ROM para cadastro presente só no celular.
  Formato/erros em `docs/mobile-library.md`. 336 Python e 48 JS aprovados;
  suíte da instância `localhost:8000` também confirmou 48 aprovados.

## 23/10/2026 — Rodada 2, contrato de saves Drive (Codex)

- `docs/drive-saves.md` e referência pura `core/drive_saves.py`: layout dos seis
  grupos, comparação de três hashes, identidade da conta/pastas, conflitos
  explícitos e histórico obrigatório. Sem rede ou escrita em dados reais.
- Revalidação e recibo de publicação separados: `version` do Drive não é CAS;
  integração deve manter pendente quando não puder garantir publicação segura.
- `.fs` FBNeo aceito também no servidor, em paridade com Android.

## 23/10/2026 (5) — Android 0.10.0: conta Google, downloads em segundo plano, conjuntos de discos

Compilada (code 17), **não instalada**: o celular está com o Victor. Instalar e validar na próxima
conexão.

- **Conta Google no app** (prioridade do Victor): Opções → Conectar conta Google, pelo Play
  Services (`play-services-auth` 21.2.0, cliente OAuth Android do projeto PyRetro, escopo do
  Drive; em modo Teste, a conta precisa estar entre os usuários de teste). Com o notebook fora
  do ar, **⬇ Baixar** procura a ROM em `Jogos/ROMs/<sistema>` do Drive (mesmo caminho do
  rclone), escolhe só nome exato/sem extensão e formatos que o celular abre (mais de um vira
  escolha), confere tamanho e md5 do Drive e retoma com Range (`GoogleDrive.kt`,
  `DriveSource` testável). Saves pela nuvem ficam para a fase 2, sobre o contrato do Codex.
- **Downloads em segundo plano:** sair do app não pausa mais a fila. `DownloadService`
  (serviço em primeiro plano, tipo dataSync) mostra o progresso com **Pausar** e, no fim, uma
  notificação de concluído/falhou/pausado (`DownloadNotice` testável). Permissão de
  notificação pedida uma vez (Android 13+). Se o Android encerrar o app, a fila não recomeça
  sozinha (decisão mantida).
- **CUE/M3U pelo manifesto do Codex** (`BundleStore`, `BundleRules`): quando o notebook só tem
  descritor, a ficha oferece o conjunto (M3U antes de CUE) com número de arquivos e tamanho.
  Cada arquivo vai para área privada com retomada; colisões são conferidas em **todos** os
  destinos antes de publicar (igual é reaproveitado, diferente cancela sem substituir nada);
  publica faixas/discos, depois descritores e o principal por último; `id` do conjunto
  conferido. Remover pelo app um jogo de vários arquivos fica **bloqueado** com aviso, até a
  remoção completa (prévia + inventário local) existir.
- Também nesta rodada: merge da entrega do Codex, 0.9.1 (busca de capa só aceita a resposta
  mais recente, `LatestRequest`) e 🩺 Diagnóstico em Ferramentas do modo TV.
- Testes: 59 JVM; Python e JS sem mudança nesta parte.
- **Validada no celular (23/10, mesma 0.10.0 reinstalada com ajustes):** conta Google conectada
  (consentimento feito pelo Victor); com o Tailscale desligado, Celeste (GBA, 1 MB) e Paper
  Mario 64 (N64, 40 MB) baixaram **pelo Drive** (origem `pyretro-gdrive`, md5 conferido);
  Metal Slug XX (PSP, 464 MB) continuou com o app fora da tela (parcial 339 → 415 MB → fim),
  serviço em primeiro plano com notificação e Pausar; The Adventure of Little Ralph (PS1, CUE +
  BIN, 98 MB) baixou como conjunto pelo notebook (Drive via rclone), CUE publicado por último,
  área temporária limpa. As ROMs de teste foram apagadas do celular depois.
- **Corrigido na validação:** a permissão de notificação era pedida uma vez só (o pedido caiu
  quando o app saiu da tela); agora até duas vezes e há **🔔 Permitir notificações de download**
  em Opções. Ficha diz "Pronto para baixar do Drive (conta Google)" com o notebook fora. O aviso
  final conta só o que terminou nesta sessão ("<jogo> está pronto em Neste celular").

## 23/10/2026 (4) — Conjuntos de discos e diagnóstico (Codex)

- Servidor: manifesto completo de CUE/M3U/GDI no PC ou Drive, ordem de dependências,
  deduplicação, limites e recusa de ciclos, faixas ausentes e caminhos externos.
  Download de cada membro exige identidade do manifesto e ETag; alterações durante
  a análise/retomada são recusadas. Identidade é de metadados, não checksum das ROMs.
- Prévia de remoção **somente do PC**, sem excluir nada: dependências usadas por
  outro descritor permanecem; leitura incerta bloqueia a proposta. Contrato e
  obrigações do cliente em `docs/mobile-rom-bundles.md`. Integração Android/SAF
  fica com Claude; isto não libera CUE/M3U no APK por si só.
- `/diagnostics`: verificação explícita de pastas/executáveis e download de relatório
  JSON por lista permitida, sem nomes de jogos, caminhos, contas, endereços ou logs.
  `/api/diagnostics` não consulta rede, executa programas nem lê conteúdo do acervo.
  Encontrar executável não comprova login; encontrar pasta não comprova escrita.
- Pesquisa RomM concluída em `docs/avaliacao-romm.md`; páginas OAuth preparadas em
  `docs/oauth/`, sem publicação de site ou mudança no Google Cloud.
- 323 testes Python e 48 JS aprovados com fixtures; diagnóstico conferido no navegador
  com acervo sintético. Nenhum save/ROM real alterado, nenhum jogo ou adb executado.
- Setup: auxiliar DS/3DS em simulação e `--apply` sem mudanças necessárias, cinco
  testes isolados aprovados; melonDS instalado com pilha RW (sem E). Avaliação do
  melonDS DS concluída: states antigos incompatíveis, migração não aplicada.
  Provisionamento limpo e homologação física continuam pendentes no setup.

## 23/10/2026 (3) — Android 0.9.0: Desejados, Estatísticas, editar jogo e capa

Compilada, **não instalada**: o celular foi desconectado (o Victor precisou dele). Instalar e
validar no aparelho na próxima conexão.

- **Desejados:** coleção nova com as três lojas juntas por nome (`/api/wishlist`), filtro por
  loja/gênero e cache em `wishlist.json` para abrir offline. Ficha com capa, **✅ Comprado** e
  **🗑 Tirar da lista** (confirmação; precisa do notebook). Adicionar fica no modo TV/web.
- **📊 Estatísticas** (atalho ao lado de Sortear): os mesmos números do modo TV
  (`/api/estatisticas`), cache em `stats.json` com a data quando offline, e atalhos para
  Ranking e Desejados.
- **Ficha → Mais opções:** **✎ Editar dados** (gênero da lista existente, data que finalizou,
  tempo, comentário; lê o registro atual e envia só o alterado por `/api/library/edit`) e
  **🖼 Trocar capa** (busca no SteamGridDB, grade de miniaturas, confirmação, aplica por
  `/api/cover/apply_url`; capa de ROM vai para o arquivo `/images/<código>/<label>`, a da
  Biblioteca para o cadastro). As duas exigem o notebook online e atualizam o catálogo depois.
- Regras sem Android em `ExtrasRules` (ordem dos desejados, horas, destino da capa, campos
  alterados); "1 dia" no singular também no modo TV.
- Testes: 310 Python, 48 JS, 50 JVM.
- **Validada no celular (23/10, Tailscale ligado):** Estatísticas iguais ao modo TV (2.957 jogos,
  18 jogando, 97 finalizados, 11 platinados, média 7,10, 4.572 h, 237 Desejados); Desejados com
  237 jogos e capas, ficha com Comprado/Tirar (não acionados); ✎ Editar do Celeste com os
  valores reais (Plataforma, 2025-10-25, 31:40:00, comentário), fechado sem salvar; 🖼 Trocar
  capa com 12 miniaturas, fechado sem aplicar. Nada foi gravado no notebook pelo teste.
- **Corrigido na validação:** (1) Estatísticas mostravam "0 nos Desejados" se a coleção nunca
  tinha sido aberta; agora leem os Desejados junto. (2) A busca de capa estourava os 60 s do
  app: o SteamGridDB levou 30–60 s por chamada. O servidor busca as grades em paralelo
  (`core/library.search_covers_steamgriddb`, teste novo) e o app espera até 2,5 min só nessa
  busca. Reinstalada a mesma 0.9.0 (code 15) com as correções.

## 23/10/2026 (2) — Modo TV com 🛠 Ferramentas: a web vira só diagnóstico

O que ainda só existia na interface completa agora está no modo TV, pelas mesmas rotas
(nenhuma mudança no servidor nesta rodada).

- **Ficha:** **Renomear arquivo…** (ROM leve com capa ou pesada no PC; cascata de ROM,
  capa e saves pelas rotas da web, e o cadastro da Biblioteca segue o nome novo),
  **🗑 Apagar ROM** (segundo toque, aviso de que não tem volta e sugestão de guardar os
  saves antes) e **⧉ Decompor coletânea** (jogos da Biblioteca, com a sugestão lida da
  pasta do Switch e lista editável pelo teclado da tela). O resultado da cascata aparece
  na mensagem.
- **Coleção 🛠 Ferramentas**, cada uma num diálogo próprio:
  - **Organizar ROMs novas:** itens da pasta de organizar com um botão por sistema
    candidato (confirmação), e o resultado da capa.
  - **Memory cards PS1/PS2:** exportar, transferir entre cards, apagar (confirmação),
    importar save por arquivo, adicionar card (existente ou em branco) e desregistrar.
  - **Saves do celular (PSP):** lista do PPSSPP pelo adb e "Baixar para o PC".
  - **Texturas HD:** catálogo completo com alvo PC ou celular, sistema, busca, "só jogos
    que tenho", instalar/remover e importar por arquivo da pasta de importação ou link.
  - **Biblioteca:** atualizar Heroic/Steam/Switch, buscar capas e adicionar jogos (presets
    da web ou plataforma/fonte livres).
  - **Capas dos sistemas:** busca de capas das ROMs leves (normal, LaunchBox,
    ScreenScraper), catálogo e capas das pesadas, capas nos emuladores.
  - **Manutenção:** backup de configs, backup de saves do Dolphin, sanitizar nomes,
    reconstruir playlist e sincronizar saves de emulador.
  - **Configurações:** pastas do PC e do Android; só os campos alterados mudam.
  - Jobs têm **Simular** e **Aplicar** (com confirmação); status e registro ficam no topo
    do diálogo. Escolhas viram botões (o controle não abre `<select>`).
- Corrigido antes de publicar: uma resposta atrasada de uma ferramenta podia redesenhar a
  ferramenta aberta em seguida (agora cada abertura usa um corpo novo).
- Testes: 310 Python, 48 JS. Ao vivo no navegador embutido: as 8 ferramentas abrem com os
  dados reais (memory cards, saves do PSP lidos do celular pelo cabo, texturas, pastas) e
  a simulação do backup de configs rodou ("modo simulação - nada foi copiado"). Mover,
  apagar, renomear, aplicar jobs e salvar configurações foram testados só com dados
  simulados.

## 23/10/2026 — Modo TV: adicionar desejados, marcar capa, saves com escrita, texturas no PC

Fecha o "uso eventual" que ainda obrigava a abrir a web (pedido do Victor).

- **Desejados:** na coleção, **➕ PSN** e **➕ Xbox** abrem o teclado da tela e adicionam um
  nome (job `/api/wishlist/sync` com `apply`, que em PSN/Xbox só acrescenta e busca capa e
  gênero). **🔄 Steam** sincroniza com a lista pública e pede segundo toque, porque quem saiu
  da Steam sai daqui também. O resumo do job ("novo(s): 1") aparece na mensagem.
- **Marcar capa:** no painel 🖼 Capa de ROM leve, **⚑ Marcar capa errada ou duplicada** /
  "Marcada · desmarcar", lendo o estado atual de `/api/covers/<código>` (mesma marca única da
  galeria da web: `/api/cover/flag` e `/unflag`).
- **Saves com escrita** (`core/tv_saves.py`, rotas `/api/tv/saves/{backup,remove,restore}`
  e `GET /api/tv/saves/backups`): **📦 Guardar cópia agora**, **Apagar** um arquivo e
  **Restaurar** uma cópia. Nada é apagado de vez: tudo vai antes para
  `Backups/Saves do modo TV/<código>/<jogo>/<data>/` com `manifesto.json` (nome, tipo,
  pasta antiga). Restaurar guarda primeiro o que está em uso. Recusa com jogo aberto pelo
  PyRetro (409), arquivo de outro jogo, nomes com caminho e sistema desconhecido. Apagar e
  Restaurar pedem segundo toque.
- **🎨 Texturas no PC:** painel na ficha (PS1, PS2, GC, Wii, PSP) com os pacotes do catálogo
  de mesmo nome (sem região/pontuação) ou serial; só se não houver nenhum, mostra até 6 de
  nome parecido com aviso. Instalar/remover com confirmação e progresso (Baixando %,
  Extraindo). Importar arquivo/link e fontes da comunidade continuam na web (link no painel).
- Um reinício só do `pyretro-gui` (o modo TV estava aberto, sem uso do controle desde 22/10).
- Testes: 310 Python (3 novos em `test_tv_saves.py`), 46 JS. Ao vivo no navegador embutido:
  texturas do NFSU2 aparecem instaladas (3085 arquivos), saves do Final Fantasy VI listados e
  **uma cópia real guardada** (idêntica ao `.srm`), botão de marcar capa e botões de
  Desejados. Apagar, restaurar, instalar textura, marcar capa e adicionar desejado foram
  testados só com dados simulados.

## 22/10/2026 (noite, 5) — Modo TV com Desejados, Estatísticas, editar e capa; Android 0.8.0

Itens 2, 3 e parte do 5 da "Ordem combinada" do roadmap, mais a fila de interface do Android.

- **Modo TV:**
  - **Desejados:** coleção com as três lojas juntas (`/api/wishlist`), ordenadas por nome;
    a loja vira o filtro de plataforma. A ficha esconde Jogar, favorito, tempo, mídia e
    progresso e oferece **✅ Comprado** e **🗑 Tirar da lista** (rotas da web, um jogo por
    vez, com segundo toque para confirmar).
  - **Estatísticas:** cartões com total, jogando, finalizados, platinados, nota média, tempo
    total e Desejados (`/api/estatisticas`), mais os 8 maiores por plataforma e por gênero
    (contados da `/api/library`). Cada cartão abre a coleção que explica o número; os de
    plataforma/gênero já abrem a Biblioteca filtrada.
  - **✎ Editar jogo** na ficha: nome, plataforma, gênero, data que finalizou, tempo e
    comentário (ROM: sem nome/plataforma, que vêm do arquivo/sistema; renomear continua só
    na web). Gênero por lista dos gêneros existentes ou "Outro…"; texto pelo **mesmo teclado
    da tela da busca** (agora com ⇧ minúsculas e pontuação `:./,&!?()`). Só os campos
    alterados são gravados (`/api/library/edit` ou `/api/library/track`, que cria o cadastro
    da ROM).
  - **🖼 Capa** na ficha: busca por bases de ROM (libretro/LaunchBox/ScreenScraper) ou
    SteamGridDB, termo editável pelo teclado da tela; escolher aplica pelas rotas da web
    (`/api/cover/select`, `/api/cover/apply_url`). A busca no SteamGridDB levou ~47 s no
    teste (igual na web); o aviso diz que pode levar até um minuto.
  - Saves, Editar e Capa são painéis exclusivos na ficha.
  - **Mouse/toque:** botão direito no cartão favorita, botão lateral "voltar" do mouse e
    Backspace fazem o B, realce ao passar o mouse e alvos de 48 px em tela de toque.
- **Android 0.8.0 (code 14), compilada, não instalada** (celular desconectado):
  - Coleção **Ranking** (só jogos com nota, maior primeiro; mesma ordem da web/TV).
  - **Filtro** ao lado da busca: plataforma e gênero que existem na coleção aberta; zera ao
    trocar de coleção.
  - **Ficha com capa grande** no topo e tempo no celular e nota na linha de situação.
  - **Contador no botão Situação** quando há progresso esperando o notebook, download com
    falha, pasta ilegível ou conflito de save adiado (`GridRules`).
- Testes: 307 Python, 45 JS, 46 JVM. Conferido no navegador embutido com os dados reais
  (sem gravar): Estatísticas e atalho Steam (92 jogos), Desejados (237) e ficha, lista de
  gêneros e teclado no ✎, busca de capa nas duas fontes, layout em largura de celular.
  Gravar edição, aplicar capa e Comprado foram testados só com dados simulados.
- **23/10, no celular (S24 Ultra):** 0.8.0 instalada (code 14). Conferidos Ranking (96 jogos
  com nota, 11,0 primeiro — bate com a web), Filtro "Ação" (12 jogos, botão vira "Filtro: Ação",
  zera ao voltar ao Início) e capa grande na ficha (Final Fantasy VI). Situação sem número,
  correto: nada pendente. O contador com pendência real não foi visto (só no teste JVM). O app
  estava offline porque o Tailscale do celular estava desligado; capas de jogos de stream
  sem cache aparecem como ✦ até o app falar com o notebook.

## 22/10/2026 (noite, 4) — Android 0.7.0 (nota e selos); modo TV com Saves e Ranking

- **Android 0.7.0 (code 13), instalada no celular** (conferência de uso na próxima rodada):
  - **Nota 0–11** em Progresso e tempo, com −1/−0,1/+0,1/+1 e Limpar (mesmo passo do modo
    TV). Fica pendente como o progresso, com o valor visto antes (`TrackingRules`), e vai
    pelo `/api/library/edit` com `expected`. Só para jogo da Biblioteca (com `id`).
  - **Selos no cartão:** ▶ Jogando / ✓ Finalizado / 🏆, ★ nota, ⏱ tempo no celular, 💾 se há
    save/estado do RetroArch no celular (lido junto com as pastas) e ⬇ % do download, que
    atualiza pela fila sem redesenhar a grade.
- **Servidor:** `/api/library/edit` aceita `nota` em `expected` (número ou vazio; booleano
  é recusado) com a mesma regra de conflito do progresso. Nova rota só de leitura
  `/api/tv/saves?code=&label=` (`rom_rename.game_saves`: pasta do sistema e raiz antiga,
  marcada como `legado`; label de ROM pesada com extensão também vale).
- **Modo TV:** 💾 Saves na ficha (lista saves/estados do PC com tamanho e data) e coleção
  **Ranking** (`/api/ranking`, maior nota primeiro). A coleção Jogando já existia.
- Testes: 307 Python, 43 JS (todos, inclusive o do modo TV), 43 JVM. Conferido no navegador
  embutido: Ranking e Saves do Final Fantasy VI.

## 22/10/2026 (noite, 3) — Texturas: índice de fontes da planilha comunitária

- **Fonte:** planilha "Texture Packs Archive" (mantida por Sad Origami; 1.456 pacotes de
  10 sistemas). Avaliada antes: quase nenhum link é arquivo direto (são tópicos do
  gbatemp/forums.ppsspp, Patreon pago ou espelho TeraBox, que pede conta e em boa parte
  copia pacote pago), então **não entra no download automático** (archive.org/GitHub com
  SHA-1). Vira só um índice de onde achar o pacote.
- **`tools/gerar_fontes_texturas.py`** lê o `.xlsx` só com a biblioteca padrão e gera
  `core/texturas_fontes.json` (943 páginas de PS1/PS2/PSP/GC/Wii/3DS). Ficam de fora os
  pagos (Patreon/Ko-fi/BuyMeACoffee ou restrição "Paywall"), os espelhos TeraBox, links sem
  `https://` e os sistemas sem texturas no PyRetro (N64, Dreamcast, Switch, Vita). Para
  atualizar: baixar a planilha de novo e rodar
  `python3 -I tools/gerar_fontes_texturas.py "~/Downloads/Texture Packs Archive.xlsx"`.
- **`texturas.fontes_da_biblioteca`** casa as páginas com os jogos da Biblioteca do mesmo
  sistema (nome ou `nomes_alt`, mesma regra do `tem_rom`, `&` = "and"). O ID do jogo vem
  do serial da planilha ou, sem ele, do pacote de mesmo nome no catálogo; ID inválido fica
  vazio. Hoje: 83 jogos, 121 páginas (PS2 63, PSP 31, PS1 23, GC 3, Wii 1).
- **Rota `GET /api/texturas/fontes?alvo=pc|celular`** (no celular só PS1/PSP/3DS).
- **Aba 🎨 Texturas:** seção recolhível "Outras fontes para jogos da Biblioteca", com os
  mesmos filtros de busca/sistema, "Abrir página ↗" (nova aba, `noopener`) e "Importar",
  que preenche sistema + ID na importação de arquivo e foca o campo que falta. A instalação
  continua pelo fluxo local (manifesto, remover só o que o PyRetro instalou). Avisos de
  Mega/anúncios e "também no catálogo".
- **Testes:** 5 novos em `tests/test_texturas.py` (casamento, alvo, índice real sem pagos,
  gerador). 305 Python e 43 JS passando. Conferido no navegador em desktop e 375 px
  (corrigido o `<details>` flex, que deixava a lista mais larga que o modal).

## 22/10/2026 (noite, 2) — Android 0.6.2/0.6.3: Início com fileiras; online sem reiniciar

- **Início (0.6.2, code 11):** nova primeira coleção, padrão para quem não escolheu outra.
  Fileiras horizontais **Continuar jogando** (iniciado e não finalizado; os do celular
  primeiro), **Recentes**, **Mais jogados**, **Favoritos** e **Prontos no celular**, até 15
  jogos cada; fileira vazia some. Tudo vem do cache e das preferências do celular, então é
  igual online e offline (o `/api/tv/home` reflete o PC e o `/api/tv/playtime` está vazio).
  O app passa a gravar `played:<chave>` ao abrir um jogo (Recentes); o tempo continua em
  `time:`. `played:` entra na migração de chaves renomeadas (fica o mais recente). Digitar
  na busca troca para a grade do catálogo. Regras em `HomeRules` (3 testes JVM).
- **Online sem reiniciar (0.6.3, code 12):** ligar o Tailscale com o app aberto não era
  percebido (a sondagem só rodava ao abrir/voltar, no máximo 1×/min) e "Testar conexão"
  não tirava o "Offline" do topo. Agora um `NetworkCallback` sonda de novo 2 s depois de a
  rede mudar (permissão `ACCESS_NETWORK_STATE`), offline a espera entre sondagens cai para
  5 s, e o teste de conexão atualiza o topo. Validado no aparelho. 42 testes JVM.

## 22/10/2026 (noite) — 0.6 validada no celular; 0.6.1; rclone com client_id próprio

Branch da nuvem unido ao `main` nos três repositórios. APK 0.6.0 compilado no notebook
(toolchain em `~/.cache/pyretro/android-toolchain`: `JAVA_HOME=…/jdk ANDROID_HOME=…/sdk`)
e instalado. Validado com o Victor no aparelho:
- Catálogo atualizou sozinho ao abrir (Tailscale, `https://notebook.tailnet.ts.net:8443`).
- ⬇ Baixar de jogo que só está no PC (3 Ninjas, SFC): SHA-256 igual ao do PC.
- ⬇ Baixar de PSP que só está no Drive (ATV Offroad, 679 MB): pausa e retomada pediram
  ao Drive a partir do byte exato do parcial (`rclone cat --offset`); MD5 igual ao do Drive.
  Os dois downloads de teste foram removidos depois.
- 💾 Saves com notebook online e offline, stream Xbox/PS/Switch/PC, Situação/Opções nas
  duas orientações: ok.

**Defeito achado → 0.6.1 (code 10):** escolher `RetroArch/saves` como "Pasta RetroArch"
fazia o app ler `saves/saves/`; o save local parecia faltar e o do notebook era oferecido
para baixar (foi baixado para `saves/saves/SFC/`, cópia idêntica; removida). Agora a
pasta `saves`/`states` é recusada com explicação, uma escolha antiga errada pede nova
escolha, e o 💾 Saves avisa quando vai baixar sem nenhum save local. A linha de status
não fica mais parada em "Conferindo saves…". 39 testes JVM.

**rclone:** client_id próprio (Google Cloud, projeto PyRetro, cliente "App para
computador"). App em modo Teste com o Victor como testador: o token vence em ~7 dias
(`rclone config reconnect drive:`). Publicar exige links de página inicial/privacidade no
Branding. Cliente OAuth **Android** criado no mesmo projeto para o login Google no app
(pacote `com.pyretro.app`, SHA-1 da chave de debug local), ainda sem código.

## 22/10/2026 (tarde) — Android 0.6: hub de jogos; download direto pelo notebook

Pedido do usuário depois de usar o app: baixar a ROM direto quando o jogo está no
catálogo (hoje exigia Opções → índice do Drive), um só botão Situação (havia dois em
retrato), Situação/Opções mais simples, funções ligadas ao jogo e estrutura fechada.
Feito fora do notebook e sem o celular: compilado e testado aqui, **não instalado**.

- **PC (`core/mobile_roms.py`, rotas `/api/mobile/rom/options|file`):** o notebook
  lista os arquivos que tem para o jogo (pasta do sistema; por rótulo, arquivo ou
  pasta) ou, para sistema pesado que só está no Drive, o item do catálogo em cache
  via `rclone lsjson`. O download aceita `Range` e confere o etag (tamanho + data;
  no Drive, tamanho + ModTime) em cada pedido: 409 se a ROM mudou. Drive vem por
  `rclone cat --offset/--count`, sem gravar no PC; rclone curto encerra a conexão
  em vez de parecer sucesso. Caminho fora do sistema, formato fora das extensões e
  nome fora do catálogo do Drive são recusados. Somente leitura.
- **Android 0.6.0 (code 9):**
  - Origem `pyretro-rom:<sistema>/<arquivo>?etag=&size=` na mesma fila/checkpoint;
    sem o endereço do notebook dentro, então LAN ↔ Tailscale não invalida a fila.
    Retomada por Range: o prefixo local entra no SHA-256 sem ser relido da rede
    (`ResumableCopy` com `resumed`); resposta 200 numa retomada cai na conferência
    antiga do prefixo. A publicação final é a mesma (SHA-256, sem substituir).
  - Ficha do jogo com ação principal por contexto (jogar, baixar, transmitir do
    Xbox/PlayStation, Switch pelo notebook, jogar no notebook); favoritar, fixar e
    💾 Saves logo abaixo; o resto em Mais opções. Console não oferece mais "iniciar
    no PC". PS5 usa o Remote Play.
  - Escolher um arquivo no seletor do Drive já vincula e inicia o download (antes:
    vincular → voltar → adicionar à fila → confirmar).
  - Quando o notebook responde: catálogo (se > 6 h), progresso/tempo pendentes e
    capas de jogos do celular/favoritos/fixados, no máximo a cada 15 min. A
    instrumentação desliga isso (`MainActivity.automaticUpdates`).
  - 💾 Saves por jogo: `SaveRules` (pasta do sistema, sufixo de extensão; raiz
    achatada fica de fora porque o nome pode ser de outro sistema) e plano parcial
    do `FileSync` que não sobrescreve o registro do grupo. Voltar de um jogo
    oferece "Salvar e ver saves". `.fs` (FBNeo) entrou nos saves aceitos.
  - Situação: uma linha por assunto e ação só quando há algo a fazer; detalhes
    técnicos recolhidos. Opções: Configurar este celular (Pasta Jogos, Pasta
    RetroArch, endereço), Uso e Avançado recolhido. Saíram da interface a escolha
    de core, as pastas por sistema, Aparência, o atalho de 3DS e o de Texturas na
    barra; escolhas antigas continuam valendo.
- **Modo TV:** depois de 10 s sem controle na Gamepad API, o rodapé explica que o
  navegador não vê o controle e aponta o `/run/udev` do Chrome Flatpak.
- **Web:** renomear/apagar diz quais saves legados foram preservados (`flat_kept`).
- **`configure_xbox.py`:** valor igual não é reescrito nem reordenado; valor novo
  fica no mesmo lugar (antes cada simulação "mudava" o `NDS.opt`).
- Validação aqui: 300 Python (OK, 2 pulados), build/lint/38 JVM do Android e APK de
  instrumentação compilado. Gradle usou um espelho do Maven Central por init script
  local da sessão (o Central respondia 429); nada disso foi versionado.

## 22/10/2026 — ES-DE removido do PC

- Decisão do usuário: o modo TV do PyRetro é o frontend. Saíram o app da TV
  (`core/tv_apps.py`), os links de capa (`core/capas_emuladores.py`, hoje só
  DuckStation/PCSX2/Dolphin) e o texto da tela de Manutenção. No setup, saíram o
  app do Sunshine (`apps.json` regravado com cópia), `bonisarch-stream`, ícones e
  o texto do lançador. AppImage, `bonisarch-esde`, item de menu e dados
  (`~/.local/share/bonisarch/ES-DE`, só configurações e 17 links) foram para a
  **lixeira**.
- Azahar entrou no menu de apps da TV, e um override do Flatpak com as variáveis
  PRIME faz ele usar a RTX também fora do lançador.
- "Controle não funciona no PyRetro": reiniciei o `pyretro-gui` duas vezes com o
  modo TV aberto (11:58:58 e 11:59:23; o `bonisarch-tv-controller` mostra o Chrome
  da TV em uso). A página ficou sem servidor por alguns segundos. O controle e as
  permissões (`devices=all`, ACL do `event19`) estavam certos, e a página `/tv`
  carrega sem erro depois.
- **Causa real (confirmada pelo usuário):** o Chrome Flatpak (156, atualizado em
  21/10) não tinha `/run/udev` no sandbox. A Gamepad API só reconhece o controle
  pelo `ID_INPUT_JOYSTICK` do udev, e o Chrome nem abria o `event19`. Com o Chrome
  da TV em foco, o `bonisarch-tv-controller` desliga as teclas do Bigscreen,
  então nada respondia. Correção: `flatpak override --user
  --filesystem=/run/udev:ro com.google.Chrome` (setup `bc5af81`,
  `step_emulator_access`). Reaberto o modo TV, o controle respondeu.

## 22/10/2026 — 3DS e DS no PC, capas de PSP/3DS, rclone

- **rclone** configurado pelo usuário (`drive`, `scope=drive.readonly`; o
  PyRetro só lê do Drive). Aviso do rclone: o client_id compartilhado será
  desativado em 2026. Criar um client_id próprio evita a interrupção.
  Catálogo do Drive atualizado: 351 jogos.
- **3DS:** `.cci`/`.cxi` faltavam em `[heavy_systems.3DS].exts` (o celular já
  aceitava). O catálogo foi de 18 para 48 jogos, incluindo Pokémon X e o
  Poochy & Yoshi local. Capas: 3DS 48/48 (29 libretro + 1 ScreenScraper) e PSP
  54/54 (9 libretro), só acrescentadas e com correspondência exata.
- **Azahar 2126.2** (Flathub, usuário, 33 MB) para 3DS: Vulkan na RTX
  (confirmado no log: `VK_DEVICE: NVIDIA GeForce RTX 4060 Laptop GPU`; em
  OpenGL/EGL ele ia para a Intel), 3x, shaders assíncronos. `physical_device=0`
  só aponta para a RTX com as variáveis do lançador (`__VK_LAYER_NV_optimus`);
  abrir o Azahar direto pelo menu usa a Intel. Layout: Tela grande ↔ Uma tela.
  Cópia do ini original em `qt-config.ini.antes-pyretro`.
- **DS no RetroArch:** core `melonds` baixado do buildbot. O build atual pedia
  pilha executável, e o glibc recusava carregar. Resolvido com
  `patchelf --clear-execstack`; **se o atualizador de cores baixar o melonDS de
  novo, repetir.** O renderizador OpenGL de alta resolução do melonDS legado
  não ativou (nem com `glcore` nem com `gl`, embora o GL rode na RTX); ficou o
  software, com Hybrid Top e sem escala inteira (`config/melonDS/NDS.cfg`).
  Toque por mouse (modo Mouse; no Joystick o mouse era ignorado), RT troca as
  telas.
- **Lançador** (`setup-linux-bonesi` `1b9b290`) e `core/play.py`: `nds`
  (melonDS) e `n3ds` (Azahar).
- **Controle no Azahar** em `tools/configure_xbox.py`: botões na posição de
  Nintendo e atalhos Back+L3 (2 telas ↔ 1 tela), Back+R3 (trocar),
  Back+LB/RB (salvar/carregar), Back+→, Back+X e Back+Start. O GUID vem do
  SDL do próprio sandbox (`tools/sdl_probe.py`). **Pendente:** aplicar com o
  Xbox ligado.
- **Desempenho do DS:** medido com `--max-frames`. Rewind e preemptive frames
  não mudaram a velocidade de forma perceptível nesse trecho (abertura de 7th
  Dragon, centenas de fps de folga); não é uma medição de jogo pesado.

## 22/10/2026 — Saves do RetroArch numa pasta por sistema (PC e celular)

Aprovado pelo usuário. Motivo: 68 nomes de ROM existem em mais de um sistema
e, com a pasta achatada, dividiam o mesmo `.srm`/`.state`.

- **Conferência antes:** os 10 arquivos de saves/states tinham conteúdo
  idêntico no PC e no celular. O `Super Mario 64.srm` só tinha a data
  diferente (16/10). O FolderSync não está mais instalado no celular,
  então cada lado foi migrado de forma independente.
- **Cópia de segurança:**
  `~/Drive/Jogos/Backups/saves_por_sistema_2026-10-21_1917_antes/` guarda os
  saves/states do PC (com `SHA256SUMS`), os do celular (`celular/`) e os dois
  `retroarch.cfg` originais.
- **RetroArch:** `sort_savefiles_by_content_enable` e
  `sort_savestates_by_content_enable` = `"true"` no PC (flatpak) e no
  celular. O diff confirmou que só essas duas linhas mudaram. A pasta nova é a
  pasta da ROM, que é o código do sistema nos dois lados (`ROMs/<código>/`,
  `Jogos/<código>/`).
- **Arquivos movidos** com `python3 -m core.save_layout [--celular] --aplicar`
  (confere tudo antes, nunca sobrescreve). Nos dois lados:
  `N64/Super Mario 64.srm` e `.state`, `SFC/Final Fantasy VI.srm`,
  `GBA/Moemon Ruby.srm`, `ARCADE/fbneo/kof97.fs`. As pastas `Backup/` ficaram
  intactas. Os hashes depois da mudança são iguais aos do backup.
- **Validado no RetroArch:** PC N64 (save e state lidos de `N64/`), PC FBNeo
  (`EEPROM successfully loaded from …/ARCADE/fbneo/kof97.fs`) e celular N64
  (save e state de `N64/`). Os testes usaram configuração anexa/temporária
  sem salvamento automático de state.
- **Cuidado aprendido:** `savestate_automatic_interval = "10"` grava
  `.state.auto` periodicamente mesmo com `savestate_auto_save = "false"`.
  O teste de 25 s no celular criou um `.state.auto` novo, que seria
  carregado no lugar do state real. Ele foi copiado para
  `artefato-do-teste/` no backup e removido do celular. Os `.lrtl` de
  runtime ganharam alguns segundos (Super Mario 64 e kof97 no PC, Super
  Mario 64 no celular).
- **Como desfazer:** voltar as duas opções para `"false"` e restaurar o backup.
- Migrador corrigido antes de aplicar: a listagem via adb cortava um nível de
  pasta (`PurePosixPath` descarta o `./`). Agora há `parse_find` com teste.

## 21/10/2026 — Relacional jogo ↔ save/tempo/favoritos (PC, web, TV, Android 0.5.2)

Validação no PC: 285 Python e 43 JS passam. Todas as rotas GET responderam
sem 500 contra o servidor real (catálogo: 2751 itens, 0,3 s). Cruzamento real:
10 saves/states, apenas 1 sem ROM (`Saves/saves/Backup/`, de propósito). Nenhum
dado por jogo órfão hoje: o modo TV e o celular ainda não registraram
favoritos, recentes ou tempo.

Riscos de projeto achados e corrigidos (latentes, sem dano real até aqui):

- **Save de outro jogo apagado/renomeado em cascata.** `saves_root` e
  `states_root` são achatados e o vínculo é só o nome. O prefixo `"<nome>."`
  pegava "Super Mario Bros. 3.srm" ao mexer em "Super Mario Bros". Agora só
  vale sufixo de extensão (`.srm`, `.state1`, `.state.auto`, `.state.png`).
- **Nome repetido entre sistemas divide o mesmo save.** 68 nomes de ROM
  existem em 2+ sistemas (Aladdin em NES/MD/SFC/SMS, Breath of Fire em
  SFC/GBA…). A cascata a partir de um sistema tocaria o save do outro. Agora
  renomear/apagar preserva esses saves (`flat_skipped`, avisado na tela) e
  "apagar save" recusa com 409. **Pendente, decisão do usuário:** o próprio
  RetroArch grava esses jogos no mesmo `.srm`; separar exige
  `sort_savefiles_by_content_enable`/`sort_savestates_by_content_enable` (PC e
  celular, que se espelham pelo FolderSync) e mover os saves existentes.
- **Renomear ROM perdia vínculos.** A cascata levava ROM, capa e save, mas não
  o registro da Biblioteca (progresso/nota) nem favoritos/recentes/tempo/mídia
  do modo TV (chave `rom:<code>:<normalizado>`). Agora `core/rename_links.py`
  grava o nome novo em `nomes_alt`, migra os dados da TV somando/mesclando e
  registra o apelido em `cache/key_aliases.json`. Só tag de região não muda a
  chave. As rotas de renomear entraram em `_ESCRITA_BIBLIOTECA`.
- **Android:** ao atualizar o catálogo, lê `/api/tv/key_aliases` e leva
  favoritos, fixados, tempo, sessões e pendências não enviadas, ROM escolhida e
  vínculo de nuvem para a chave nova (`KeyAliases`, 4 testes JVM). APK 0.5.2
  compilado (33 JVM, lint ok). **Não instalado**: o celular estava desconectado.

## 21/10/2026 — Android 0.5.1: consistência offline / cache / online

Revisão de código do app e do catálogo do PC (os STATUS em `auditoria/` eram
relatórios de entrega, não revisão). Defeitos achados e corrigidos:

- **Estado online falso na abertura.** `online` só virava verdadeiro depois de
  "Carregar catálogo" à mão: com o notebook acessível, o topo dizia "Offline" e
  nenhuma capa nova era baixada. Agora, ao abrir e ao voltar ao app, uma sondagem
  silenciosa (`/api/csrf`, no máximo 1×/min) atualiza só o estado em memória e o
  aviso ("Online · …" ou "Offline · …"). Não baixa catálogo nem sincroniza, e não
  grava registros de contato: esses continuam vindo só do teste explícito da
  central (a instrumentação exige que navegar não altere as preferências).
- **Cache de capas offline.** A chave incluía o endereço do servidor, então trocar
  LAN ↔ Tailscale esvaziava o cache. O limite era de 128 arquivos por ordem de
  criação (um acesso não renovava a capa). Agora a chave é só o caminho, o acesso
  renova a capa (LRU) e o limite é de 1500. Uma falha ao renomear não devolve
  mais um arquivo inexistente.
- **Capa trocada no PC nunca atualizava no celular.** O catálogo da TV
  (`core/tv.py`) agora manda `?v=<mtime>`, como o `com_versao` da web.
- **Sincronizar progresso/tempo.** Uma recusa HTTP (409/400) de um item abortava
  o resto. Uma queda de rede no meio tirava itens das pendências sem regravar o
  catálogo local, e o offline mostrava o estado antigo. Agora a recusa vira
  pendência preservada e o lote segue; o catálogo é gravado em `finally`.
- **Fixados lento.** `pinned()` copiava todas as preferências para cada um dos
  ~2750 jogos em cada renderização. Agora `pinnedChecker()` lê uma vez só.

Validação: 277 Python, 29 JVM, build e lint. No aparelho, as suítes
StorageSmoke, status e status+conexão deram PASS; inventário real (281 arquivos)
idêntico antes e depois; preferências reais iguais, salvo ui/contato; APK de
teste desinstalado. Teste manual: Online detectado na abertura; capas baixadas
ao navegar; com o serviço do PC parado, aviso Offline e capas do cache exibidas.

## 21/10/2026 — Android: Sortear em coleção vazia

- Relato: "o app não está sorteando". O sorteio funcionava em Neste celular e no
  Catálogo, mas o app reabria na última coleção usada (Fixados, 0 jogos; Favoritos
  também vazia). O botão só trocava a linha de status, então parecia não fazer
  nada.
- Agora, se a coleção atual está vazia, o sorteio usa os jogos do celular (ou o
  catálogo em cache, se não houver nenhum) e avisa isso no título da janela. O
  aviso "Nenhum jogo com esses filtros" virou Toast, porque antes ficava escondido
  atrás da janela.
- Build/JVM/lint passaram; APK 0.5.0 reinstalado e conferido no aparelho
  (Fixados vazia → sorteou Super Darius, PCE-CD).

## 21/10/2026 — Encerramento após a 0.5 e critérios de robustez PC/Android

- Registrada avaliação qualitativa: PC mais próximo de uma experiência
  consolidada; Android funcional, porém recente. A etapa recomendada é consolidar
  a arquitetura existente e comprovar previsibilidade no uso diário, sem prometer
  percentual, prazo ou equivalência medida com frontends do mercado.
- Roadmap passa a concentrar uma matriz de homologação: ciclo completo de jogo e
  retorno com foco/posição, sessões prolongadas, offline, falha de rede, processo
  encerrado, permissão expirada e recuperação de downloads/saves/conflitos.
  G8, Drive real, diferentes emuladores, Steam Link e PS4/Xbox remoto continuam
  pendentes; testes sintéticos aprovados não substituem essas evidências.
- Prioridades seguintes: homologação, acabamento visual e aba ativa, downloads
  Android em segundo plano com notificação/recuperação, diagnóstico acessível e
  relatório compartilhável sem dados privados, CUE/M3U completos e atualização
  do APK mais simples com assinatura estável. Mídia, title IDs, identidade de
  nuvem, runtime sem duplicação e retenção explícita de versões seguem posteriores.
- Encerramento somente documental, a pedido do usuário. A implementação 0.5 do
  commit `232f9db` permanece instalada e publicada. Nenhum novo teste, modificação
  de dados, configuração do aparelho ou automação foi executado por este registro.

## 21/10/2026 — Android 0.5: espaço, jogos fixados, fila e interface compacta

- Gestão de espaço lista ROMs por tamanho, com filtros de sistema/progresso/fixação
  e indicação de tamanho desconhecido/leitura parcial. Mede ROMs concedidas e
  espaço privado disponível; não soma saves/texturas/histórico ao total de ROMs.
  Remoção individual confirmada revalida nome/tamanho/data antes de excluir.
- Fixação para manter baixado é independente de favorito, acompanha downloads e
  protege aliases do mesmo documento SAF em todas as rotas de remoção. Jogos
  fixados não recebem proposta de remoção ao finalizar; fila e CUE/M3U também
  bloqueiam remoção. Nenhuma limpeza em lote ou retenção de versões ativada.
- Fila persistente de até 200 registros, um arquivo por vez, com bytes/estado,
  reordenação, tentativa após falha e retirada que preserva checkpoints. Identidade
  de documento/destino evita duplicar acessos equivalentes. Origem/pasta guardadas
  no item são revalidadas; cópias e descarte de parcial compartilham exclusão mútua.
  Capacidade privada e limite de 12 GB conferidos antes da cópia.
- Sair do app solicita pausa, falhas interrompem a sequência e abrir novamente
  não retoma sozinho. A publicação final já conferida pode terminar na pausa.
  Nenhum jogo abre automaticamente após download; andamento aparece no início.
  Sem serviço em segundo plano; prefixo retomado continua sendo comparado inteiro.
- Barras horizontais, diálogos com rolagem e grupos recolhidos nos detalhes liberam
  espaço. Aparência permite ocultar dicas/aviso offline/texturas, preservando
  avisos operacionais. Jogar local permanece primeira ação; coleção, busca, página,
  rolagem e seleção são guardadas ao sair. Ajuda explica Recentes → PyRetro e que
  a saída do jogo depende do emulador, sem alterar seus atalhos.
- Aba **Stream** concentra Xbox/XBXPlay, PS4/Remote Play e PC/Switch/Moonlight.
  A antiga fileira fixa do topo foi removida. Busca/paginação de jogos ficam
  ocultas na aba, clientes ausentes desativados; detalhes de cada título mantêm
  suas ações. Abrir Stream não liga consoles nem inicia transmissão.
- 0.5.0 (code6) instalada por atualização no usuário principal, assinatura
  preservada. 29 JVM, build/lint e instrumentação retrato/paisagem passaram. Suíte
  SAF ampliada verificou fila, recuperação de execução interrompida, pausa/retomada,
  reordenação, deduplicação, fixação por alias e recusa de remoção após alteração.
  Interface conferiu também restauração de coleção/página após recriar a Activity.
  Somente fixtures próprias usadas nas operações de arquivos; sem sync de saves
  reais ou lançamento de jogo. G8 físico, Drive real e sync de uso seguem pendentes.

## 21/10/2026 — Android 0.4.1 instalada: correções e validação no aparelho

- Abrir Situação durante a leitura inicial podia deixar a contagem em zero até
  reabrir a tela. Contagem, data e falhas passam a acompanhar a conclusão da
  leitura com a central aberta. O resumo de conexão também é atualizado na
  própria tela após o teste, tanto em sucesso quanto em falha.
- Concessões com URI inválida aparecem como necessidade de escolher novamente,
  sem derrubar a lista de pastas. Observações incompletas ou inválidas dos grupos
  de saves são ignoradas na central; nenhum arquivo ou baseline é descartado.
- Diálogos personalizados passam a focar a primeira ação habilitada. Aplicativos
  não encontrados ficam desativados no submenu de conexões, evitando uma ação
  cujo aviso só aparecia atrás do diálogo. Homologação do G8 físico continua pendente.
- Instrumentação ampliada (`-e suite status`) verifica estados com preferências
  isoladas, dados inválidos, atualização da leitura, foco e submenus nas duas
  orientações efetivamente aplicadas. Com `-e connection true`, consulta o notebook
  explicitamente e confere o resumo na mesma tela; preserva as demais preferências.
- 0.4.1 (code5) instalada somente no usuário principal com a assinatura existente.
  Build/lint e 24 JVM aprovados; suítes de situação e armazenamento SAF passaram
  no aparelho. Tailscale estava desconectado; sessão existente reconectada e
  notebook respondeu, sem mudança de conta/pareamento. Sem lançamento de jogo,
  sync de save real ou alteração de progresso/tempo. Inventário real de ROMs,
  saves/estados/playlists idêntico em caminho, tamanho e mtime antes/depois.
  APK auxiliar/fixtures temporários removidos. Pasta RetroArch ainda depende da
  concessão do usuário; Drive real, emuladores e G8 físico seguem para homologação.
- Cache gerado `android/.kotlin/` incluído no ignore; APK, chave, auditoria e
  preferências continuam privados.

## 21/10/2026 — Android 0.4: situação e conexões, sem celular

- Central **Situação**, acessível na tela principal/Opções e em paisagem, reúne
  jogos da última leitura local, falhas de leitura, data do cache, registros de
  contato e teste explícito do notebook. Abrir a central não consulta PC/Drive.
- Progresso e sessões de tempo pendentes aparecem por jogo. Pendências bloqueadas
  na sincronização ficam indicadas sem descartá-las; editar o payload invalida
  a indicação antiga. Data/resultado da sincronização concluída ficam no app.
  Resultados novos de contato e acompanhamento são invalidados ao trocar servidor.
- Grupos de saves/estados/runtime guardam a última análise/aplicação com data,
  conflitos adiados e falhas, vinculada às pastas e ao servidor. Resultado antigo
  não é apresentado como análise atual nem como prova de sincronização contínua.
- Pastas distinguem ausência de escolha, concessão sem leitura, somente leitura
  e leitura/escrita persistentes. Document IDs SAF são tratados como opacos;
  concessão salva não comprova existência/disponibilidade do documento. Atalhos
  permitem escolher novamente pastas, conferir índice/downloads/playlists e abrir
  emuladores/clientes/Tailscale encontrados, sem presumir login, VPN ou core.
- Checkpoints mostram quantidade e espaço privado ocupado; falha ao lê-los não
  descarta parciais nem impede conferir os demais estados. Resultados assíncronos
  do teste de conexão/checkpoints só atualizam a central que iniciou a consulta.
- APK 0.4.0 (code 4) compilado com a assinatura local preservada. 24 testes JVM e
  build/lint passaram; instrumentação existente recompilada, sem execução nesta
  etapa. Sem celular/adb, instalação ou alteração do acervo/configurações reais.
  Telefone permanece com a 0.3; layout/foco/G8/Drive/emuladores/sync real pendentes.

## 21/10/2026 — Encerramento e prioridades para continuação

- Consolidado no roadmap o que ainda exige uso real após a 0.3: G8, Drive,
  emuladores/texturas/saves e clientes remotos/foco/Steam Link.
- Registradas sugestões, sem implementá-las: central de situação/conexões,
  gestão de espaço com jogos fixados, fila e execução de downloads em segundo
  plano, identidade de documentos da nuvem, conjuntos CUE/M3U e nomes por title ID,
  mídia automática e importação do runtime sem duplicar sessões.
- Prioridade recomendada: homologar os fluxos atuais e tornar o estado do app
  visível antes de ampliar funções. Código/APK permanecem na versão 0.3 instalada.

## 21/10/2026 — Android 0.3: recuperação, playlists, nuvem e retomada

- Recuperação de versões nos grupos de saves/estados/runtime: histórico local
  funciona offline; histórico do notebook usa API com SHA-256, identidade da raiz
  e comparação do destino antes de restaurar. A versão selecionada e o arquivo
  atual são preservados. Alteração concorrente bloqueia a restauração.
- Playlists JSON do RetroArch recebem análise de entradas novas/ausentes por raiz
  e sistema, preservando itens externos e campos dos itens mantidos. Publicação
  com histórico e comparação; recuperação pelo app. Atualização após download/
  remoção é opcional, vinculada às pastas, e desativada ao restaurar uma versão.
  Falha de leitura/permissão/limites não vira uma lista vazia para apagar entradas.
- Índice da nuvem por sistema: pasta concedida quando o provedor suporta ou arquivos
  em seleção múltipla. Prévia, cache, associação única nos dois sentidos e entradas
  extras para ROMs sem cadastro no notebook. Escolhas manuais prevalecem. Não lê
  conteúdo das ROMs ao indexar nem varre a conta inteira; fontes são atualizadas
  explicitamente. Drive sem seleção de pasta usa a alternativa em lote.
- Downloads mantêm checkpoint privado e permitem pausar/continuar/descartar apenas
  o parcial. URI/destino/metadados e todo o prefixo existente são conferidos antes
  de acrescentar bytes; o provedor pode reler esse prefixo. Tamanho, SHA-256 e
  publicação local são verificados; destino diferente permanece preservado.
  Sem serviço em segundo plano ou retomada automática; limite de 12 GB/arquivo.
- Publicador SAF compartilhado por saves/playlists/downloads; instrumentação
  ampliada usa preferências e diretórios próprios. A primeira execução encontrou
  resolução incorreta de raiz derivada (tree URI versus document URI); corrigida
  para respeitar a subpasta e exigir isolamento antes de copiar no teste. Fixture
  sintética criada fora da pasta de teste removida após conferir SHA-256.
  Victor reconectou o aparelho durante a etapa; 0.3 instalada no usuário principal,
  com assinatura preservada. Instrumentação ampliada passou no aparelho; inventário
  real de ROMs/saves/states/playlists igual antes/depois. Fixtures e APK auxiliar limpos.
- Validação: 276 testes Python, 43 de interface e 18 JVM; build/lint sem erros.
  G8 físico, provedor Drive real e uso dos saves do usuário continuam para homologação.
  Documentação de produto e pendências atualizada.

## 21/10/2026 — Android 0.2: sincronização de saves, estados e runtime

- **Opções → Saves, estados e runtime** compara arquivos locais com o notebook por
  grupo: RetroArch (saves, estados e runtime), PPSSPP (SAVEDATA/PPSSPP_STATE) e 3DS
  (saves/extdata da SDMC). Usa pastas SAF concedidas, sem permissão geral de arquivos.
  Pastas padrão ausentes são vazias na análise e criadas somente ao aplicar cópias.
- Análise sem gravação, SHA-256 e último estado comum distinguem mudanças de um lado
  de conflitos. Primeira sincronização divergente, alterações nas duas pontas e
  arquivo removido após sincronizar exigem escolher celular, notebook ou adiar.
  Não há sincronização automática nem propagação de exclusões.
- Aplicação explícita revalida origem, destino e identidade das pastas. Downloads
  são recebidos em temporário e conferidos; uploads têm comparação do destino sob
  lock e repetição idempotente. Publicação preserva a versão anterior em histórico
  oculto, excluído das análises seguintes; conflitos não escolhem pela data do arquivo.
- Estados exigem emulador/core compatível. Runtime `.lrtl` é copiado como arquivo,
  sem somar acumulados nem importá-los no tempo do PyRetro. SDMC restringe os caminhos
  a dados/extdata dos jogos, sem conteúdo instalado, NAND, firmware, BIOS ou configuração.
- APK 0.2.0 mantém a assinatura local e instalação no usuário Android principal;
  script de build deriva o nome do artefato da versão. Documentação de uso e roadmap
  atualizados. Saves reais e catálogo não foram alterados pelos testes desta etapa.
- Validação: 272 testes Python, 43 de interface e 10 JVM; compilação e lint sem erros.
  Instrumentação no aparelho verifica publicação SAF real com arquivos sintéticos:
  criação, substituição/histórico, conflito, checksum e pasta padrão ainda inexistente.
  Teste completo dos emuladores, controle físico, Drive real e transferências dos
  saves do usuário permanece para homologação no uso.

## 20/10/2026 — Cliente Android offline, tempo, mídia e texturas

- Primeiro cliente Android nativo em Kotlin: banco permanece no PC, catálogo
  projetado/capas em cache, pastas por SAF, favoritos, progresso e tempo offline.
  Sincronização explícita revalida a base sob lock e preserva conflitos; eventos
  de tempo têm IDs para não duplicar sessões em uma repetição do envio.
- Navegação Galileo G8/controle padrão e touch: direcional/analógico, A/B,
  favoritos X, teclado virtual Y, avanço LB/RB e coleções LT/RT. Layout horizontal
  compacto e orientação do app acompanha a presença do controle. Sorteio com
  filtros abre detalhes e sugere jogo local, cliente remoto ou download.
- Intents para RetroArch, PPSSPP e Lime3DS/Azahar; NDS/3DS priorizados no telefone.
  XBXPlay, PS Remote Play oficial e Moonlight permanecem responsáveis pelas contas
  e transmissões. NES usa Nestopia e PC Engine usa Beetle PCE, conforme os cores
  existentes; escolha de core por sistema evita depender de um único nome fixo.
  ROM do Drive vinculada pelo seletor Android e copiada diretamente
  para pasta local, sem depender do notebook/Tailscale. PS1 sob demanda usa CHD/PBP;
  não baixa CUE/M3U isoladamente nem substitui arquivos existentes.
- Ao finalizar uma ROM local, pergunta se deseja mantê-la ou excluir apenas o
  arquivo local. Histórico, saves/states, BIOS e texturas são preservados.
  CUE/M3U dependentes exigem conferir o conjunto pelo gerenciador do notebook.
  Não há exclusão em lote automática nem alteração das playlists externas pelo APK.
- Tempo de emuladores lançados na TV registrado ao encerrar o processo, mesmo com
  a página fechada. Registro separado do tempo histórico da Biblioteca; duração
  manual para lojas/transmissões e fileira Mais jogados. Logos PNG/JPEG/WebP e
  prévias MP4/WebM locais, com validação e vídeo pausado fora do destaque/ao abrir modal.
- Texturas recebem upload ZIP/7z/RAR na interface do PC. Cliente Android importa ZIP
  local offline em PSP/3DS e recebe fontes PSP/pacotes preparados no notebook.
  Validação antes da extração bloqueia travessia, links e limites excessivos;
  instalação nativa preserva textura existente diferente. PS1 continua via USB.
- Gradle wrapper e script de build: compilação pessoal, testes JVM, lint e APK com
  SHA-256 em cache, sem versionar chave, banco ou artefatos pessoais. Instalação
  no perfil Android principal; atividade única evita empilhar telas repetidas.
- Validação: 265 testes Python, 43 de interface e 6 JVM passaram; build e lint sem
  erros. Aparelho conectado: catálogo HTTPS/Tailscale, cache/pastas/sorteio e ZIP
  de textura mínimo, confirmação de exclusão e NES/Nestopia conferidos. G8 físico
  e provedor Drive real ainda precisam de homologação. Sync de saves/states/runtime e busca automática de logos/trailers
  continuam nas próximas etapas.

## 20/10/2026 — Convenção de pastas do Nintendo Switch

- Organização manual do NSW usa uma pasta por título ou volume instalável,
  diretamente na raiz do sistema, reunindo sua base, updates e DLCs. Pastas
  gerais de lotes de download não devem agrupar títulos independentes.
- Decomposição de jogos internos de uma coletânea continua na Biblioteca,
  mantendo o alias do título instalável. Reorganizações devem conferir os
  aliases e atualizar o mapa privado sem perder os itens somente na nuvem.
- Correção do lote privado aplicada com backup, hashes e preservação de IDs,
  capas e acompanhamento; nenhuma alteração de código ou configuração.

## 20/10/2026 — Sorteio com próxima ação e consolidação das interfaces

- Sorteio da interface completa oferece Jogar (PC/ROM/disco), Transmitir do console,
  abrir loja para instalar ou continuar um download confirmado no modo TV. Resultado
  apenas sugere; nenhuma sessão/download é iniciado sem escolha. Na TV os detalhes
  do sorteado abrem diretamente, com foco na ação disponível e retorno ao card.
- `core/game_actions.py` concentra sugestões por instalação e plataforma. PS4, Switch
  e Xbox compatíveis usam clientes instalados; PS3, Xbox 360 e PSN genérico não são
  assumidos como consoles compatíveis. A transmissão abre o cliente e o usuário
  escolhe o jogo no console. Detalhes da TV também oferecem a loja quando não instalado.
- Biblioteca no pool mantém ID: homônimos de plataformas/gêneros distintos não
  trocam de identidade. Resultado inclui o mesmo item usado no catálogo e link
  `?game=CHAVE`, abrindo esse jogo na TV, sem cruzamento por nome apenas.
- Erros de abertura/transmissão permanecem visíveis, sem serem sobrescritos por dica.
  Respostas atrasadas do sorteio são ignoradas após sair; filtros podem ser carregados
  novamente após erro. Resultado/filtros usam texto/DOM e o modal se adapta a 390 px.
- Encontrado PS4 já registrado no Chiaki; acesso direto preparado em tela cheia,
  usando apenas nickname/IP no cache privado e credenciais mantidas pelo Chiaki.
  Descoberta no endereço salvo não respondeu; sessão real depende do console ligado
  e confirmação do endereço atual. Nenhuma configuração do console/conta foi alterada.
- README, modo TV, plano e roadmap consolidados com a experiência implementada e
  pendências reais. Validação: 248 testes Python e 41 de interface; sorteio real de
  Switch e link para os detalhes conferidos sem iniciar transmissão ou alterar acervo.

## 20/10/2026 — Switch transmitindo e proteção contra janelas duplicadas

- Victor confirmou a transmissão do Switch Lite por Wi-Fi. Quatro clientes estavam
  abertos, mas somente um mantinha vídeo e áudio conectados. As três cópias sem
  conexão foram fechadas, preservando a transmissão e os jogos do console.
- Pedidos para Xbox/PS4/Switch agora verificam o cliente já aberto antes de iniciar
  outro. Lock cobre pedidos simultâneos; detecção Flatpak preserva instâncias
  anteriores a um reinício do PyRetro. Um cliente encerrado pode ser aberto novamente.
  A TV mostra quando a janela já existe; Steam mantém o pedido de Big Picture.
- Validação: 242 testes Python e 39 da interface. Regressões cobrem concorrência,
  cliente externo, reabertura, falha de detecção sem duplicação e aviso na TV.

## 20/10/2026 — Tela inicial de console, favoritos e acessos remotos

- Início passa a abrir por padrão: destaque do jogo, recentes, continuar jogando,
  favoritos, jogos Steam/Heroic e acervo local em fileiras de capas. Recentes não
  dependem do marcador iniciado; continuar prioriza jogos locais e último uso.
- X favorita sem repetir ao segurar; Menu abre tema escuro/claro, tela cheia e volta
  ao início/interface completa. Relógio local e bateria quando disponível. Favoritos
  e tema persistem em cache privado com lock/gravação atômica; a Biblioteca não muda.
- Detalhes priorizam Jogar e recolhem edição de progresso/notas até o usuário abrir.
  Retorno de foco preservado após fechar detalhes e atualizar favoritos.
- Acessos rápidos para Xbox remoto/Greenlight, PS4 remoto/Chiaki, Steam, Heroic e
  emuladores. Cliente SysDVR 6.3 instalado da release oficial; Switch Lite abre TCP
  Bridge em tela cheia com IP validado e armazenado apenas no cache ignorado pelo Git.
  As portas do console recusaram conexão; ativação do módulo e teste real pendentes.
  SysDVR captura jogos compatíveis, sem HOME ou encaminhamento automático do Xbox.
- Confirmadas as entradas de menu: apenas PyRetro visível, antigo acesso web oculto.
  Caches KDE reconstruídos nos locales pt_BR/C; Steam/Bigscreen não reiniciados.
- Validação: 238 testes Python e 39 da interface com dados sintéticos, incluindo
  concorrência de favoritos, validação de entrada, preservação da Biblioteca,
  navegação, foco inicial visível e layout em 390 px. Nenhuma ROM/save alterada.

## 20/10/2026 — Frontend TV, Xbox e atalhos unificados

- Tela inicial Sistemas com contagens do catálogo/local; Neste PC reúne ROMs completas e
  instalações Steam/Epic/GOG/Amazon. O catálogo é montado por metadados locais e cache,
  sem refresh de posse/nuvem nem gravação na biblioteca. CUE/GDI/M3U incompletos, arquivos
  vazios, `.part`, capas e pastas fora do acervo não comprovam presença local.
  O catálogo segue o filtro de posse da Biblioteca: registros só de wishlist ficam fora;
  posse com desejo em outra loja continua visível.
- Y abre pesquisa com teclado virtual; X apaga, Menu pesquisa e B cancela. LB/RB pulam
  páginas, LT/RT trocam coleções. Plataforma/gênero e filtro de presença local funcionam
  no controle. Atualizar preserva os filtros da seleção.
- Apps oferece os aplicativos de jogos instalados, com Steam em Big Picture. ID fixo é
  revalidado pelo backend; o navegador não fornece comandos. Alternativa de emulador por
  jogo aparece apenas para cores compatíveis já instalados e fica no perfil do navegador.
- A leitura do controle ignora dispositivos virtuais sem botões suficientes e fica suspensa
  em segundo plano/durante o emulador. Retorno exige soltar os botões. Helper KWin tenta
  restaurar o foco ao encerrar a sessão; homologação física/Steam Link continua pendente.
- Detecção PC valida a presença do diretório informado pelo manifesto, recusa Steam ainda
  não instalada e distingue homônimo de plataforma de console. Amazon/Nile passou a abrir
  pelo Heroic, com IDs validados por loja e índices construídos uma vez por catálogo.
- Instalador migra PyRetro — Acervo para PyRetro preservando appid, artes e demais campos
  Steam. Atalho web antigo oculto no menu; interface completa continua disponível no navegador.
- `tools/configure_xbox.py`: simulação por padrão, exige apps fechados, preserva cópias
  anteriores na auditoria privada e altera apenas entrada/hotkeys/confirmação de parada.
  Xbox configurado em RetroArch, PCSX2, DuckStation, Dolphin (GC/Wii) e PPSSPP. Back modifica
  save/load, slots, pausa, captura, aceleração, menu e saída; Guide fica para o Bigscreen.
  Nenhum save/load real foi acionado. Wii pode exigir perfis por jogo. NDS/3DS sem lançador
  instalado continuam disponíveis para consulta/progresso.
- Validação: 231 testes Python e 38 testes da interface com dados sintéticos; teste adicional
  cobre Arcade sem nome no DAT. Acesso ao Xbox conferido nos quatro Flatpaks; aplicações,
  acervo, ROMs, saves e configurações privadas ficam fora do Git.

## 20/10/2026 — Wishlist Steam só com jogos e marcas registradas entre lojas

- A leitura da wishlist Steam confirma o tipo de cada produto e importa
  somente `game`, deixando DLC, software e demo fora da lista do PyRetro.
  Tipo ausente cancela a coleta inteira, preservando a proteção contra
  remoções causadas por respostas incompletas.
- Adição e sincronização de desejos ignoram `™` e `®` antes da normalização
  Unicode, evitando duplicatas entre lojas sem mudar IDs ou histórico.
  Base e Deluxe, subtítulos e sequências continuam distintos. A regra fica
  restrita às wishlists; o casamento de ROMs e a importação de posse não mudam.
- Quatro regressões novas cobrem tipos de produto, detalhes incompletos,
  preservação de histórico entre grafias e distinção entre edições.
  Validação: 220 testes Python e 37 de interface passaram com dados sintéticos.

## 16/10/2026 (fim, 2) — Texturas: importação por link

- **Importar por link** (aba Texturas > "Importar um pacote de arquivo" > link direto): para os sistemas sem fonte confiável no
  catálogo (GameCube/Wii, 3DS, PS1). `core/texturas.baixar_url` só aceita **https para host público** (recusa `http`, usuário/senha na
  URL, porta que não seja 443, localhost, rede local e tailnet, e cada redirecionamento passa pela mesma checagem), exige que o link
  seja direto para `.zip/.7z/.rar` (página HTML é recusada), limita o tamanho (12 GB, `[texturas] limite_gb`) e apaga o arquivo depois
  de instalar. Sem hash de referência, a tela pede confirmação e mostra o **SHA-1** calculado no fim, para você registrar.
  Testado de ponta a ponta com um link real (zip do repositório do PyRetro num ID falso de PS1, removido em seguida) e com testes
  novos (core e API). Links de Mega/Google Drive não são diretos e não funcionam; baixe o arquivo e use a importação por arquivo.
- `remover` agora também apaga a pasta vazia do pacote/jogo.

## 16/10/2026 (fim) — Catálogo com PSP, pesquisa dos demais, setup e registro

- **Catálogo de texturas: 352 pacotes** (342 de PS2 e 10 de PSP). O gerador (`tools/gerar_catalogo_texturas.py`) agora lê
  dois itens do Internet Archive (`pcsx2-hd-texture-packs` e `ppsspp-hd-texture-packs`); os de PSP têm download liberado
  (HTTP 200) e SHA-1 do próprio archive.org. **Pesquisa dos outros sistemas:** GameCube/Wii têm uma pasta de pacotes
  (`nintendo-gamecube-roms/Dolphin - Texture Packs/`, 39 arquivos: Mario Galaxy 1 e 2, Luigi's Mansion, Mario Kart Wii,
  Zelda Twilight Princess/Wind Waker, Smash Melee, Wii Sports...) mas todos respondem **401** (bloqueados), então não
  entram; os nomes não trazem o ID do jogo. 3DS: só o pacote de Ocarina of Time 3D via Patreon e nada de Pokémon X. PS1:
  sem pacote verificável (o DuckStation só troca texturas em poucos jogos). Para esses, a aba Texturas importa de arquivo.
- **Dolphin sem capa do PyRetro:** ignorado por decisão (links criados, mas a grade mostra os banners).
- **Planejado, não implementado:** PyRetro no lugar do ES-DE e app Android nativo (`docs/plano-frontend.md`).
- **setup-linux-bonesi** (commit `e766410`): `tools/install-emulator-access.py` + `step_emulator_access` (overrides Flatpak para
  PCSX2/Dolphin/PPSSPP lerem `~/Drive/Jogos`, PCSX2 gravar em `Saves/PS2`) e `docs/EMULADORES-PC.md` (Adapter do PCSX2,
  runtime NVIDIA, dependências). Registrado também no Notion (Ferramentas/PyRetro) e no `ContextoPessoal/10-projetos.md`.

## 16/10/2026 (madrugada, 2) — Aba Texturas com alvo celular e importação; saves de teste limpos

- **Aba 🎨 Texturas:** seletor "Instalar no PC / no celular" e bloco **Importar um pacote de arquivo** (sistema + ID do
  jogo + nome do .zip/.7z/.rar na pasta de importação, `[texturas] importar_dir`, padrão `~/Downloads`; só o nome do
  arquivo, nunca um caminho). Rotas `/api/texturas?alvo=`, `/instalar` e `/remover` aceitam `alvo` e pacote local
  (`sistema` + `id_jogo`). Instalar não falha mais se a opção de texturas não puder ser ligada: devolve um aviso.
  O catálogo ainda só tem PS2, então no celular o caminho é a importação. Testado de ponta a ponta com o celular
  (zip de teste do PSP instalado e removido pela rota). 3 testes novos em `tests/test_api.py` (209 no total).
- **Saves gerados pelos testes, removidos:** `Saves/PS2/sstates/SLUS-21065 (F5C7B45F).01.p2s` (F1 do teste do NFSU2) e
  `savestates/SLUS-00619_resume.sav` do DuckStation do celular (Diablo). **Deixei** os memory cards do PS2
  (`Mcd001/002.ps2`, tocados às 18:48) e `PS1-DuckStation/memcards/Mcd001.mcd` (18:41): podem ser só regravação ao fechar o
  emulador, mas são o seu progresso e não tenho como provar o que mudou; compare com a versão do Drive se quiser.
  Também ficaram `RetroArch/config/Nestopia/FC.opt` e `remaps/Nestopia/FC.rmp` do celular (criados/regravados pelo teste de
  intent do RetroArch; são opções, não saves) e `log/play_time.bin` do Lime3DS.

## 16/10/2026 (madrugada) — Texturas no celular (PSP e 3DS validados, PS1 instalado)

- `core/texturas.py` ganhou o alvo **celular** (`instalar_celular`, `remover_celular`, `estado_celular`,
  `set_loading_celular`), tudo por `adb`, com manifesto e validação de ID. Ainda não está na aba Texturas.
- **PSP (PPSSPP Gold, Patapon 2, `UCUS98732`)**: validado em jogo. Dump → textura vermelha 2× → instalada
  pelo PyRetro em `/sdcard/Jogos/PSP/PSP/TEXTURES/UCUS98732` (com `textures.ini`) → "Options" e cantos
  vermelhos na tela. Abrir o jogo por intent `VIEW` com `file://` **não** carregou o jogo (só abriu o menu);
  pelo toque no menu "Recentes" funciona.
- **3DS (Lime3DS, Pokémon X, `0004000000055D00`)**: validado em jogo. A pasta de usuário é `/sdcard/Jogos/3DS`;
  `dump_textures`/`custom_textures` em `config/config.ini` seção `[Utility]` (usei `1`/`0`, como no comentário
  do arquivo). Dump de 29 texturas → versões vermelhas 2× instaladas em `load/textures/<TITLE ID>` → a
  interface do jogo ficou toda vermelha.
- **PS1 (DuckStation Android 0.1-8969, Diablo `SLUS-00619`)**: textura **instalada**, troca **não validada em jogo**.
  O app não deixa ligar o dump por arquivo (o `settings.ini` é privado e o `gamesettings/<serial>.ini` com
  `DumpVRAMWrites` não gerou nada), então o dump foi feito no PC com o mesmo jogo (o nome da textura vem do
  conteúdo) e as texturas (invertidas e 2×) foram enviadas para
  `Android/data/com.github.stenzek.duckstation/files/textures/SLUS-00619/replacements`, com
  `EnableVRAMWriteReplacements = true` em `gamesettings/SLUS-00619.ini`. Para desfazer, use `remover_celular`
  (pacote `teste-ps1-diablo-cel`) e apague o `.ini` do jogo. Se não trocar, ligar a opção global no app.
- **PS1 no celular validado pelo usuário** (Diablo, 4 texturas): a imagem mudou na tela de título, mas "toda
  bugada". É esperado: no Diablo os `vram-write-*.png` de 160×240/128×240 são dados 8-bit crus da VRAM (não
  imagens), então inverter e ampliar 2× embaralha o resultado. O que ficou provado é o caminho (nomes
  iguais entre PC e celular, pasta certa, opção por jogo respeitada). Pacote de verdade para jogo com textura
  paletizada exige o modo "página" do DuckStation. Teste removido do celular depois.
- Celular: `svc power stayon true` foi ligado a pedido (tela sempre acesa no cabo);
  desligar com `adb shell svc power stayon false`.
- Bug achado nos testes: `set_loading_celular` falhava quando o `.ini` ainda não existia (`cat` com exit 1 no adb).
- Erro meu: simulei teclas (uinput) enquanto você digitava; não faço mais isso com a tela em uso.

## 16/10/2026 (fim da noite) — Texturas validadas nos 4 emuladores, capas no ES-DE/emuladores, GPUs

- **Texturas HD validadas em jogo com troca de ida e volta** (o emulador despeja uma textura, ela
  é editada e instalada pelo `core/texturas.py`, o jogo reabre): **Dolphin** (Metroid Prime 2,
  `Load/Textures/G2MP01`, `HiresTextures = True`), **PPSSPP** (Patapon 2, `PSP/TEXTURES/UCUS98732`,
  `ReplaceTextures = True`) e **DuckStation** (Rayman, `textures/SLES-00049/replacements`,
  `[TextureReplacements] EnableVRAMWriteReplacements = true`; PS1 entrou no módulo agora).
  Não existe pacote HD verificado para Metroid Prime 2/Patapon 2/Rayman nas buscas, então o
  catálogo continua só com PS2; os testes usaram texturas de teste (removidas depois).
  Achado: o PPSSPP **só carregou a troca com um `textures.ini`** na pasta do jogo (os pacotes
  costumam trazer o deles); sem ele nada mudou. Dolphin/PPSSPP/DuckStation voltaram ao normal
  (`DumpTextures`/`SaveNewTextures`/`DumpVRAMWrites` desligados; as chaves de carregar ficaram
  ligadas). Backups dos `.ini` em `~/Drive/Jogos/Backups/`.
- **GPU:** Dolphin e PPSSPP rodam na RTX (`nvidia-smi` listou os dois processos), mesmo com o
  adaptador vazio no `.ini`; o DuckStation já tinha `Adapter` fixo. Só o PCSX2 caía na Intel.
- **Modo TV (teste JS 36/37):** não era bug do app. O painel de navegador embutido do Claude não
  dispara `requestAnimationFrame` (nem na página principal), e o modo TV lê o controle por esse
  callback. Com o `rAF` simulado o teste passa **37/37**, também no código de antes das mudanças do
  dia. Rode o `test_app.html` num Chrome/Firefox normal.
- **Capas do PyRetro no ES-DE e nos emuladores** (`core/capas_emuladores.py`, Manutenção >
  "Capas do PyRetro no ES-DE, DuckStation, PCSX2 e Dolphin", `tests/test_capas_emuladores.py`):
  tudo por symlink para `Capas/<sistema>/Named_Boxarts`, sem copiar. ES-DE: `downloaded_media/<sistema>/covers`
  (17 sistemas; confirmado na tela do PS2). DuckStation: `covers/<nome da ROM>.png` (confirmado).
  PCSX2: `covers/<nome da ROM>.png` **e** `covers/<SERIAL>.png`, com o serial lido do `SYSTEM.CNF` da
  ISO, porque o PCSX2 dá prioridade à capa baixada por ele (nome = serial); as dele vão para
  `covers/_baixadas_pelo_emulador/` (confirmado: mostra as nossas). **Dolphin não confirmado:** os
  links `cache/GameCovers/<ID>.png` existem, mas a grade continuou com os banners.
- Python: 200 testes passando.

## 16/10/2026 (noite) — NFS Underground 2 a 40+ fps, texturas HD e GameCube fora do celular

- **Causa das quedas do NFSU2 (30–37 fps):** o PCSX2 estava no Vulkan com `Adapter` vazio e o
  log de 16/10 dizia "No GPU requested, using first (Intel RPL-P)": o jogo rodava na **GPU
  integrada**, não na RTX. O doc de gráficos dizia que o PCSX2 ia na NVIDIA pelo PRIME offload;
  isso valia para outros emuladores, não para o Vulkan do PCSX2. Fixado
  `Adapter = NVIDIA GeForce RTX 4060 Laptop GPU` em `PCSX2.ini` (backup do `.ini` anterior em
  `~/Drive/Jogos/Backups/PCSX2.ini.antes_nfsu2_2026-10-16`). Medido pelo OSD, na troca de carro
  da seleção: 60 fps parado, queda para ~40 só no instante de carregar o modelo, volta a 59–60.
  Em corrida real o usuário relatou "não crava 60, mas não baixa de 40, super jogável".
  EE 27%, GS 38%, GPU 30%: nada saturado, o piso de 40 é do próprio jogo (30 fps nativo).
- **Armadilha:** editar `PCSX2.ini` com o PCSX2 aberto não vale, ele regrava o arquivo ao sair
  e desfaz a edição (aconteceu no teste). Fechar antes (`pkill -x pcsx2-qt`).
- **Textura HD validada no PCSX2** (3x, Vulkan, RTX): dump de textura ligado (`textures/<SERIAL>/dumps`),
  uma textura de teste do Hummer trocada por uma versão 1024×1024 apareceu no jogo, e depois o
  pacote real "NFSU2 HD Remaster" (3.085 arquivos, 552 MB, Internet Archive, SHA-1 conferido) foi
  instalado pelo PyRetro: OSD mostrou **118 texturas substituídas a 60 fps**. Teste de dump/troca
  removido depois. Opção `LoadTextureReplacements = true` ficou ligada.
- **Nova aba 🎨 Texturas** (`core/texturas.py`, `tools/gerar_catalogo_texturas.py`,
  `core/texturas_catalogo.json`, rotas `/api/texturas`, `/instalar`, `/remover`, `tests/test_texturas.py`).
  Catálogo de 342 pacotes de PS2 gerado da listagem do item `pcsx2-hd-texture-packs` do Internet
  Archive (nome, tamanho e SHA-1 vêm de lá; só https de archive.org/github). Baixa, confere o
  SHA-1, extrai (zip/7z/rar), copia para a pasta do emulador e grava um manifesto; remover apaga só
  o que o PyRetro instalou. Apaga o arquivo baixado depois (o cache fica no ~/Drive sincronizado).
  Liga a opção de carregar texturas no `.ini` se o emulador estiver fechado. "Só jogos que tenho"
  cruza o título do pacote com as ROMs (igualdade de palavras).
  **Não testados:** Dolphin (GC/Wii) e PPSSPP (pastas e chaves de `.ini` seguem a convenção deles,
  mas o catálogo ainda não tem nenhum pacote para eles) e PS1/DuckStation (fora de propósito).
- **GameCube fora do celular** (pedido do usuário): `heavy_systems.NGC` ganhou `celular = false`
  (sem botão Enviar, sem consulta por adb, sem "celular não conectado", `/api/heavy/send` recusa);
  a aba Saves perdeu a seção GameCube; `emu_saves` e `emu_sync` perderam o Dolphin GC. O backup
  PC→Drive dos saves do Dolphin GC/Wii (`core/pc_backup.py`) continua, é do PC.
- Teste JS: `test_app.html` deu 36/37; a falha ("modo TV ... A não abriu jogo", polling de
  gamepad) é em arquivo que não foi tocado e não foi investigada. Python: 193 passando.

## 16/10/2026 — Saves dos testes removidos; RetroArch do PC sem pasta por núcleo

- Os testes de emulador do dia criaram saves novos, espelhados no PC e no celular pelo
  FolderSync: pastas `saves/` e `states/` `Mupen64Plus-Next` e `Snes9x` (3 `.srm` e 4
  `.state.auto`), `PS1-DuckStation/savestates/SLES-00049_resume.sav` e, no celular,
  `states/Super Mario 64.state.auto`. Todos removidos. Para saber o que era teste, valeu a
  data de **criação** no Google Drive (hoje), não a de modificação. Ficaram os cartões de
  memória de PS1 e PS2 (de julho) e o `Super Mario 64.srm` solto, que o teste só regravou
  com o mesmo conteúdo (md5 igual ao do PC).
- **Causa das pastas por núcleo:** o `retroarch.cfg` do PC tinha `sort_savefiles_enable` e
  `sort_savestates_enable` = `"true"` (já assim no backup de 24/08). O celular e o PyRetro
  (`rom_rename`, `emu_saves`) usam `saves/` e `states/` sem subpasta, então o PC não achava os
  saves antigos e criava outros. As duas chaves foram para `"false"` no PC, com o RetroArch
  fechado; nada mais mudou no arquivo.

## 16/10/2026 — Rewind desligado no N64 e no Dreamcast do celular

- Confirmado pelo `adb` que o `retroarch.cfg` do celular tem `rewind_enable = "true"`
  (granularidade 2), a mesma causa dos 40 fps do N64 no PC.
- Criadas no celular `RetroArch/config/Mupen64Plus-Next/Mupen64Plus-Next.cfg` e
  `RetroArch/config/Flycast/Flycast.cfg`, só com `rewind_enable = "false"`. Nenhuma
  existia antes; nada mais foi alterado.
- Super Mario 64 com a override: 60,1 fps na tela de título (`dumpsys SurfaceFlinger
  --latency`, tela a 60 Hz). Faltou medir sem a override e testar em gameplay e no
  Dreamcast.
- O teste regravou o `states/Super Mario 64.state.auto` do celular, porque lá
  `savestate_auto_save` está ligado. Não havia cópia anterior. Registrado em
  [`emuladores-graficos.md`](emuladores-graficos.md) para os próximos testes.

## 16/10/2026 — Teste real dos emuladores (tela desbloqueada, 60 Hz)

- **N64 rodava a 40 fps (2/3 da velocidade), já antes do ajuste gráfico.** Causa: rewind
  global ligado; salvar o estado do N64 a cada 2 quadros atrasava o núcleo e o áudio
  segurava o ritmo. Override `config/Mupen64Plus-Next/Mupen64Plus-Next.cfg` com
  `rewind_enable = "false"` (mesmo padrão do Saturn) → 60 fps. Flycast recebeu o mesmo.
  Hipóteses descartadas por teste: VSync, VRR, GPU, driver/latência de áudio,
  ParaLLEl-RDP, CountPerOp, Framerate.
- PPSSPP voltou para **Vulkan**: a trava anterior era só da tela bloqueada.
- Medido com contador de fps temporário: SFC 60, PS1 (PAL) 50 VPS a 5x, PS2 59,94 a 3x,
  GC 59,94 e Wii 60 a 3x, PSP Vulkan 5x. Prints conferidos.
- O RetroArch grava `--appendconfig` no `retroarch.cfg` ao sair (`config_save_on_exit`):
  os testes chegaram a deixar VSync e audio sync desligados, restaurados em seguida.
- O celular também tem rewind global (backup de 24/08): provável mesma lentidão no N64 lá.

## 16/10/2026 — Gráficos dos emuladores no PC (Nitro V 15, RTX 4060 a 60–75 W)

- Hardware medido: `nvidia-smi` dá 60 W padrão e 75 W máximo para a 4060 deste ANV15-52
  (os 140 W de lojas não valem aqui). Alvo: render interno de 1080p a 1440p.
- PCSX2 3x Vulkan + widescreen; Dolphin 3x + MSAA 2x; DuckStation 5x + PGXP; PPSSPP 5x;
  Flycast 1920×1440; N64 e Dreamcast com preset bilinear em vez do CRT global. Os presets 2D
  (CRT royale, Mega Bezel etc.) não mudaram. Detalhes e tabela PC × celular em
  [`emuladores-graficos.md`](emuladores-graficos.md).
- **DuckStation não abria jogo pelo lançador:** o `-batch` parava na pergunta do AppImage
  sobre criar atalho, e o Vulkan pegava a Intel. Corrigido no `settings.ini`
  (`NoDesktopFile`, `[GPU] Adapter`). A pergunta foi achada lendo o diálogo por AT-SPI,
  já que a tela estava bloqueada.
- PPSSPP ficou em OpenGL: em Vulkan parou antes do primeiro quadro com a tela bloqueada e
  não fechou com SIGTERM. Precisa de novo teste desbloqueado.
- Celular não alterado (sem `adb` nesta sessão). Backup do antes:
  `Backups/emuladores_pc_2026-10-16_antes/`.

## 16/10/2026 — Streaming: Steam Link descartado, Moonlight com Sunshine

- Pelo Steam Link o PyRetro abria preto e o ES-DE derrubava a transmissão; na captura
  Wayland a Steam também pedia permissão a cada reconexão. A TV LG (webOS) foi
  descartada por exigir sideload. Ficaram **Android e Switch Lite** como clientes
  (Moonlight) e, para a TV, o notebook por HDMI com o Big Picture, sem streaming.
- Servidor: Sunshine (Flatpak) com captura por portal do KDE, que lembra a permissão.
  Apps: Área de trabalho, PyRetro (modo TV), ES-DE, RetroArch, Heroic e Steam Big
  Picture, cada um trazendo sua janela para a frente com `tools/raise-window.sh`.
  Instalados também chiaki-ng (PS4) e Greenlight (Xbox). A instalação passou a fazer parte
  do setup-linux-bonesi; este repositório só mantém o `raise-window.sh`.
- Alcance: Android pelo Tailscale (`bonisarch.<tailnet>.ts.net`) funciona dentro e fora de
  casa; o Switch Lite só em casa, pelo IP da rede local (reservar no roteador).

## 16/10/2026 — Janela do modo TV atrás do Big Picture

- Teste pelo Steam Link: os atalhos PyRetro e ES-DE iniciavam (processos e log
  confirmados), mas a janela ficava atrás do Big Picture, que permanece ativo em
  tela cheia no KWin. `tools/raise-window.sh` ativa a janela pela classe via script
  do KWin; `pyretro-tv.sh` o chama em segundo plano. Ativação manual confirmada
  nesta máquina; o atalho completo ainda precisa de novo teste. O ES-DE usa o
  `bonisarch-esde` do setup-linux-bonesi e não foi alterado aqui.

## 15/10/2026 — Último jogado e jogos de PC no modo TV

- **Jogando por último jogado:** abrir uma ROM pela TV grava a data em
  `cache/last_played.json` (arquivo local, fora do `library.json` sincronizado).
  `/api/iniciados` devolve `ultimo_jogado` e a aba Jogando ordena do mais recente;
  quem nunca foi aberto por aqui fica depois, por nome. Jogos de ROM em Jogando
  agora têm `rom_code` e podem ser abertos direto do card.
- **Jogos de PC:** `core/pc_games.py` descobre jogos instalados na Steam (manifestos
  `appmanifest_*.acf`, ignorando runtimes/Proton) e no Heroic (Epic e GOG). Novas rotas
  `GET /api/pc/options?id=` e `POST /api/pc/launch`; o cliente só manda o id do
  registro, o comando é fixo (`flatpak run … steam://rungameid/N` ou
  `heroic://launch/<loja>/<app>`), com appid/app_name validados, sem shell. O jogo precisa
  estar instalado e a fonte do registro precisa bater com a loja. Não vira sessão
  acompanhada: a loja devolve o controle na hora; a TV só avisa e o progresso continua manual.
  Amazon (nile) ainda não é tratada.
- **Não verificado em máquina real:** abrir o jogo pela Steam Flatpak já aberta, e o formato
  `heroic://launch/<loja>/<app>` (pode variar com a versão do Heroic). Testado só com
  comando fictício e leitura dos arquivos reais (Steam: 2 jogos instalados; Epic: Alien: Isolation).
- Validação: 180 testes Python e 37 de interface passaram. Os testes de interface
  precisam do painel do navegador visível: com ele oculto o `requestAnimationFrame`
  pausa e o teste de controle falha (foi a causa das falhas intermitentes anteriores).

## 15/10/2026 — Sorteio no modo TV

- Nova aba **🎲 Sortear** em `/tv`: escolhe grupo (leves, pesadas, Biblioteca e
  subgrupos Switch/Xbox/PlayStation/PC) e gênero, chama o `/api/sortear` já
  existente e mostra o jogo sorteado como card normal (Jogar, Baixar e jogar,
  progresso). Sem rota nova no backend. Coexiste com o ES-DE, que segue instalado.
- "Continuar jogando" já era coberto pela aba **Jogando**; a ordenação por
  último jogado veio na entrada seguinte.
- Validação: 173 testes Python e 36 de interface passaram (novo teste do
  sorteio com APIs fictícias). Uma rodada isolada falhou no teste de controle
  por temporização de `requestAnimationFrame` e passou ao repetir.
  Homologação no sofá continua com o Victor.

## 15/10/2026 — Encerramento e publicação das pendências locais

- A pedido do Victor, incluídas na publicação as alterações de interface,
  progresso, wishlist e sorteio que já estavam locais ao iniciar esta conversa,
  com seus testes e histórico de 02–03/10. A validação da pasta completa nesta
  sessão passou com 173 testes Python e 35 de interface, usando dados fictícios.
- Preservados no repositório o pacote de revisão do Nitro de 15/10 e o ponteiro
  local para o relatório Google Docs. O `.gddoc` contém apenas o endereço e
  metadados do documento; o conteúdo do relatório não está embutido nele.
- Modo TV e atalho Steam instalados e publicados. Permanece a homologação de
  controle físico, retorno de foco dos emuladores reais e Steam Link. Contexto
  local de agentes atualizado para permitir encerrar a conversa sem perder essas
  pendências; `AGENTS.md` continua intencionalmente fora do versionamento.

## 15/10/2026 — Jogar pelo modo TV

- Botão Jogar usa `bonisarch-emulator` com mapeamento explícito de sistemas e
  argumentos sem shell. Valida a ROM local e as referências CUE/GDI/M3U,
  recusando traversal, symlinks externos, arquivos vazios e ciclos. Vários
  discos/formatos exigem escolha. CCD permanece bloqueado até validar IMG/SUB.
- Baixar e jogar exige confirmação e revalida os arquivos antes de executar.
  Sessão única acompanhada pelo servidor, com erros visíveis e oferta de
  registrar progresso/nota ao sair; não marca o jogo como finalizado sozinho.
- Download pesado passou a staging temporário exclusivo, `copyto` para arquivo
  e `copy` para pasta própria, incluindo faixas referenciadas. Completa
  descritores locais sem substituir arquivos; publicação recusa destino que
  surgiu durante a operação. Não modifica ROMs existentes nem apaga acervo.
- Instalador do atalho Steam com simulação, recusa enquanto Steam aberta,
  preservação dos atalhos existentes, cópia do VDF e execução idempotente.
  Atalho **PyRetro — Acervo** instalado nesta máquina; Chrome usa perfil separado
  em tela cheia. Script e contrato documentados em `docs/modo-tv.md`.
- Validação com acervo temporário: 173 testes Python e 35 de interface passaram.
  Ciclo baixar/abrir/encerrar conferido com lançador fictício. Homologação do
  controle físico, foco dos emuladores reais e Steam Link continua com o Victor.
  Cópia isolada desta etapa: 169 testes Python e 25 de interface passaram.

## 15/10/2026 — Modo TV

- Primeira etapa para Big Picture: `/tv`, com Biblioteca/Jogando, ROMs leves e
  pesadas, filtros de plataforma/sistema, navegação espacial por setas e Gamepad
  API (direcional/analógico, A/B), progresso e notas sem teclado. Download
  pesado pede confirmação e acompanha início/resultado via SSE existente.
- Tracking de ROM aceita `campos` em lote, validando tudo antes da gravação;
  clientes com `field/value` continuam compatíveis. Salvamento pela TV mantém
  cascata de iniciado/finalizado/platinado em uma única requisição.
- Documentado o contrato do atalho da Steam em `docs/modo-tv.md`. Execução de
  emuladores e homologação com controle físico/Steam Link ficam para a próxima
  etapa. Desenvolvimento e testes usam acervo temporário/APIs fictícias.
  Validação: 152 testes Python e 34 de interface passaram, incluindo A/B
  simulados, preservação de foco e ausência de transbordamento a 390 px.
  Cópia isolada deste commit: 148 testes Python e 24 de interface passaram
  sem depender das alterações locais anteriores, que permanecem fora dele.

## 03/10/2026

- **Alças unificadas com tudo recolhido.** Sobra uma alça; ela expande as
  duas faixas juntas. Com uma faixa aberta, os controles são independentes.
- **ROMs pesadas sem extensão na exibição.** O card mostra o nome sem
  extensão, mantendo o nome real nas ações de arquivo. Pastas conservam seu nome.
- **Desejos separados da Biblioteca.** Registros só com fontes de desejo
  ficam em Desejados e saem do sorteio; marcas de desejo em jogos possuídos
  não geram abas nem rótulos extras. Comprado atualiza a Biblioteca e encaminha
  a plataforma genérica para PS4, Xbox ou Steam, preservando plataformas específicas.
- **Sorteio exibe plataforma.** Jogos da Biblioteca tinham código ROM nulo,
  exibido literalmente como `null`; a resposta agora inclui a plataforma
  do registro e a interface a usa no resultado. Validação deste bloco:
  149 testes Python e 33 de interface passaram com acervo sintético.

- **Segunda alça para ações e filtros.** A faixa de título, ações e filtros
  pode recolher pela própria borda inferior, independentemente do menu
  superior. As duas alças permanecem visíveis recolhidas e guardam o estado
  separadamente no navegador. Validação: 145 testes Python e 29 de interface
  passaram com acervo sintético.

- **Progresso atualiza a tela sem F5.** Marcar/desmarcar iniciado, finalizado
  ou platinado agora aguarda a gravação e atualiza a Biblioteca carregada,
  os filtros e os cards de ROM. A cascata grava os campos em sequência antes
  da atualização. Antes, a ROM alterava o disco e seu objeto local, mas a
  Biblioteca em memória permanecia antiga. Regressões com jogos fictícios
  cobrem o filtro de iniciados, ROM leve e a cascata em ROM pesada.
  A primeira correção de atualização não resolvia a tela só com o fundo,
  relatada depois pelo Victor; a causa de rolagem foi reproduzida separadamente.
- **Tela permanece na janela.** Uma coleção sintética de 120 jogos reproduziu
  o documento rolando cerca de 9.900 pixels para fora da janela ao alcançar
  o último card. A estrutura principal agora fica fixa na janela, com altura
  dinâmica e rolagem interna da galeria, sem deslocar o documento inteiro.
- **Retração conforme o desenho.** A alça fica na borda inferior do menu
  superior, permanece acessível recolhida e alterna entre recolher e expandir.
  Substitui o botão fixo no topo e o ciclo antigo de três etapas.
  Validação: 145 testes Python e 28 de interface passaram; clique real no
  último jogo fictício salvou o progresso mantendo a tela visível. Chrome
  do Victor não estava conectado nesta sessão; uso real ainda requer conferência.

## 02/10/2026

- Ícone de controle na aba do navegador, servido localmente em SVG. O servidor
  reconhece o tipo `image/svg+xml` para arquivos estáticos.

## 25/09/2026

- **Orientação PSN/Xbox atualizada.** O README ainda dizia que colar um só nome
  apagava os desejos anteriores, apesar de o código já usar adição sem remoção.
  O aviso antigo foi retirado da orientação operacional; o incidente segue no
  histórico de 12/09 e 21/09.
- **Wishlist Steam protege contra resposta parcial.** Um erro de `appdetails`,
  appid ausente ou resposta incompleta cancela a sincronização antes de gravar
  a biblioteca. Regressões sintéticas cobrem detalhe indisponível e lista
  inválida; a remoção continua possível quando a leitura inteira conclui.

## 24/09/2026

- **Revisão dos commits de CSP e Wishlist de 21/09.** Conferidos os domínios
  usados nas prévias de capa, o `Referrer-Policy: no-referrer`, o `script-src
  'self'`, a separação entre adição manual (PSN/Xbox) e sincronização da Steam,
  e o lock das rotas que gravam `library.json`. A suíte passou com 142 testes
  Python e 23 no navegador.
- **Ação “Comprado” com ID de outra lista.** Uma requisição atrasada ou
  manipulada podia transformar um jogo fora da lista pedida em posse. Agora a
  operação recusa o ID sem a marca de desejo correspondente, sem gravar o
  arquivo. Há regressão no núcleo e na rota HTTP. O uso real da ação no
  celular continua para homologação do Victor.

## 21/09/2026

- **Lista de desejos de PSN/Xbox virou "só adicionar" - e 154 registros
  foram recuperados do Drive.** A caixa de texto das abas PSN/Xbox de
  🌟 Desejados era uma *sincronização*: o texto digitado valia como "minha
  lista inteira agora é essa", então tudo que não estivesse ali perdia a
  marca da fonte e, sem outra fonte no registro, era apagado
  (`sync_wishlist`). Registrar 3 jogos novos na PSN e 1 no Xbox apagou,
  por isso, **29 registros da PSN e 125 do Xbox**. É a segunda vez: o
  mesmo erro tinha apagado 125 jogos do Xbox em 12/09, e naquela vez a
  recuperação foi por acaso (um sync concorrente da Steam desfez o dano
  sozinho).

  *Recuperação:* a cópia do `library.json` no Google Drive ainda era a de
  16:50, anterior ao estrago - baixada com `rclone` e comparada registro a
  registro com a local. A diferença era exatamente o esperado: 154
  registros ausentes, 7 que só tinham perdido a marca de desejo (sobreviveram
  por serem posse real em outra fonte: ROM de PS2, Heroic, PSN físico) e os
  4 jogos novos que o usuário tinha acabado de adicionar. A restauração foi
  **aditiva** - devolveu os 154 e as 7 marcas sem desfazer nada do que existia
  no arquivo local, então os 4 novos continuaram lá. Nenhum dos apagados
  tinha nota, tempo ou comentário (eram registros de desejo com gênero e
  capa). Lista final: **PSN 34, Xbox 131, Steam 56**.

  *Correção (decidida pelo usuário):* PSN/Xbox só adicionam, nunca removem.
  `core/library.py` ganhou `add_to_wishlist` (só acrescenta, é o novo
  caminho de PSN/Xbox), `remove_from_wishlist` (tira um jogo de uma lista) e
  `mark_wishlist_owned` (troca a marca de desejo pela fonte de posse da
  mesma loja - ver `WISHLIST_FONTE_POSSE`). `sync_wishlist`, a única rotina
  do projeto que apaga registro sozinha, continua existindo mas **só a Steam
  usa**, e só porque lá a lista vem da API ao vivo, onde "não veio" significa
  mesmo "saiu da wishlist".

  Na tela, o botão "💾 Sincronizar" das abas PSN/Xbox virou "➕ Adicionar à
  lista", e sair da lista passou a ser ação de um jogo por vez dentro do ✎
  (pedido do usuário: *"eu possa apagar, no lapizinho, ou marcar como
  comprado e ele vai para minha biblioteca"*): **"✅ Comprado"** move o jogo
  pra Biblioteca levando capa, gênero e comentário que já tinha, e **"🗑 Tirar
  da lista"** só tira a marca - o registro só some se não sobrar nenhuma
  outra fonte nele. Rotas novas `/api/wishlist/remove` e
  `/api/wishlist/comprado`, ambas em `_ESCRITA_BIBLIOTECA` (lock da
  biblioteca). Testado de ponta a ponta contra o servidor real, inclusive o
  cenário do incidente: 1 nome enviado com 35 na lista, nada removido.
  Total: **138 testes Python**.

## 16/09/2026

- **Pendências #9–#11 da auditoria encerradas.** O levantamento
  `PATHFINDER-2026-08-07` (127 KB) foi arquivado e versionado em
  `docs/planning/`, explicitamente marcado como histórico. `app.js` ganhou
  teste de integração real no navegador: monta o HTML completo em documento
  local e comprova abas principais + CSRF em POST inválido e sem efeito. A
  Biblioteca teve o id duplicado das duas entradas de *Life is Strange: True
  Colors* reparado sem tocar no progresso: Xbox agora usa
  `life-is-strange-true-colors-xbox-one`; `save_library` recusa qualquer
  duplicata futura e os criadores de registro geram sufixo seguro em colisão.
  A coleção ficou com **2.838 IDs únicos**. Total: **126 testes Python + 23
  JavaScript**.

- **Sync de saves não sobrescreve destino alterado (#7 da auditoria).** Cada
  ação de `emu-sync` agora registra também o mtime que o destino tinha no
  planejamento. No `apply`, origem e destino são revalidados; se Insync,
  emulador ou outro processo criou/alterou o destino nesse intervalo, a
  ação é cancelada como conflito e o arquivo externo permanece intacto.
  Testes reproduzem tanto destino alterado quanto destino criado após o
  plano. Total: **123 testes Python + 22 JavaScript**.

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

- **Testes de integração e de JavaScript** - o usuário perguntou se dava
  pra cobrir as duas lacunas que eu mesmo tinha admitido (JS e
  integrações). Dava:

  - **`tests/test_api.py`** (16 testes): sobe o `ThreadingHTTPServer` de
    verdade contra um acervo temporário (config, ROMs, capas e
    biblioteca de mentira - nada toca no acervo real) e conversa por
    HTTP. Cobre o caminho completo: roteamento, leitura de config, JSON
    de ida e volta, gravação em disco. Inclui o `/api/library/edit`
    sendo tudo-ou-nada (nome válido + data inválida não pode gravar
    metade), o tracking de ROM criando registro na primeira edição sem
    duplicar na segunda, jogo oculto sumindo de Ranking/Iniciados, e a
    travessia de caminho pelos endpoints reais. Nenhum teste fala com
    Steam/SteamGridDB/ScreenScraper/rclone/adb.
  - **`gui/static/logic.js`** (novo) + **`tests/test_app.html`** (18
    testes): não há runtime JS nesta máquina (sem node/deno), então
    separei a lógica PURA da interface (cor da nota, agrupamento de
    abas, filtros, stemOf/formatGB) num módulo sem DOM e o navegador
    virou o executor - a página roda as asserções e publica o placar em
    `window.RESULTADO`. Além de testável, ficou uma separação melhor:
    `app.js` cuida de tela e eventos, `logic.js` só de regra.

  A extração quebrou o `app.js` no caminho: meu script cortou no meio de
  um bloco de comentário e uma linha de prosa virou código
  (`SyntaxError: Unexpected identifier 'só'`). Pego no teste de
  regressão no navegador logo depois, não em produção - corrigido e
  revarrido em busca de outras linhas órfãs (nenhuma).

  Total: **48 testes Python + 18 de JavaScript**.

  Correção de diagnóstico: eu vinha escrevendo que o "bugou" acontecia
  "no celular"; o usuário esclareceu que foi tudo no PC. Não muda a
  causa (servidor fora do ar pelos meus restarts + escrita não atômica),
  só o cenário - e reforça a primeira, já que ele estava clicando
  exatamente enquanto eu reiniciava.

- **Decompor coletânea (⧉)** - o usuário já tinha pedido "um método pra
  evitarmos isso" e eu não tinha entregado: rodei a varredura do Switch
  de novo e RECRIEI o "Portal Companion Collection" que ele já havia
  decomposto na mão (em "Portal", vindo da planilha com nota 9.4, e
  "Portal 2"). O `nomes_alt` que eu tinha feito resolve RENAME (1
  registro ↔ 1 nome de origem), mas não decomposição (1 pasta → N
  registros), que é o caso real: "muitos jogos são collections,
  eventualmente vou decompondo eles".

  Botão ⧉ no card + `POST /api/library/decompor`. O ponto crítico é o
  VÍNCULO: a pasta continua se chamando "Portal Companion Collection"
  pra sempre e a varredura casa por nome, então o nome da coletânea (e
  os apelidos que ela já tivesse) passa a ser `nomes_alt` do primeiro
  jogo resultante. Jogo que já existe é REAPROVEITADO, não duplicado -
  o "Portal" da planilha mantém nota e finalizado.

  A tela abre pré-preenchida com o conteúdo de DENTRO da pasta
  (`GET /api/switch/colecao` + `nomes_dentro_da_colecao`), como pedido.
  Os três formatos reais do acervo, conferidos no Drive:
  - subpasta por jogo ("Portal", "Portal 2") -> sai limpo;
  - arquivo com title-id/versão ("Pikmin 1 [0100AA...][v0].nsp") ->
    vira "Pikmin 1"/"Pikmin 2", com base+update deduplicados;
  - arquivo com o nome da própria coletânea (Castlevania Dominus) ->
    devolve ela mesma, que é honesto: não dá pra adivinhar o conteúdo.
  Anotação de tamanho ("Demonschool (0.89 GB)") também é removida.
  É sugestão assumida - patch de tradução, por exemplo, ainda aparece e
  o usuário apaga a linha.

  Pra não gastar minutos de rclone a cada clique, o mapa {nome limpo ->
  pasta real} fica em `cache/switch_pastas.json`, atualizado junto com
  o "🔄 Switch"; a tela faz UMA chamada só, na pasta específica.

  8 testes novos (56 no total), incluindo o que garante a propriedade
  que faltava: depois de decompor, `merge_owned` com o nome da PASTA
  devolve `added=0` - a coletânea não volta.

  Também adicionados nesta rodada: **Demonschool** e **Portal Companion
  Collection** entraram pela varredura da pasta; o segundo era
  justamente a recriação indevida, removida e substituída pelo vínculo.


## 29/08/2026

- **Varredura das 154 pastas do NSW e decomposição em massa.** Pedido:
  "veja pasta por pasta do NSW, mapeie os arquivos, para decompormos o
  que der - coletâneas como a do Castlevania ou Capcom Arcade, que você
  entra dentro do jogo para escolher o que quer jogar, não conta".

  O critério do usuário tem um equivalente mecânico exato, que evita
  chute: o **title-id** no nome do dump (`[0100XXXXXXXXXX000]` = jogo
  base, `...800` = update, resto = DLC). Coletânea de menu interno tem
  UM base; bundle de jogos separados tem N. Um `rclone lsjson -R` da
  NSW inteira (12.039 itens) respondeu as 154 de uma vez:
  **16 pastas com mais de um base**, 138 com um só.

  Três coisas que só a pesquisa resolveu, e que mudaram a conta:
  - **Kingdom of Asteborg é as outras duas.** A pasta tem 3 bases, mas
    o "Kingdom of Asteborg" é uma compilação que embala Demons of
    Asteborg + Astebros. Decompor em 3 registraria o mesmo conteúdo
    duas vezes - viraram 2.
  - **SEGA Ages tinha duplicata regional.** "Thunder Force IV" e
    "Lightening Force: Quest for the Darkstar" têm title-ids
    diferentes, mas são o mesmo jogo (retítulo da Sega of America nos
    EUA) - 19 de 20.
  - **Namco tem 3 subpastas e 4 títulos.** "NAMCO Museum Archive Vol
    1-2" é uma pasta com dois produtos dentro; ir pelo nome da subpasta
    perderia um.

  Três que PARECEM decomponíveis e não são: **Animal Crossing** (o 2º
  base é o Island Transfer Tool, utilitário), **Duke Nukem 3D homebrew**
  (os 3 extras são as expansões oficiais) e **Disney Classic Games** (o
  Jungle Book do nome da pasta é DLC, não título separado).

  Achado de passagem: **Sky Force Reloaded não tem jogo base** - os dois
  arquivos da pasta são update (`[01006FE005B6E800]`). Não instala.

  13 pastas decompostas em **177 jogos**: Switch 151 -> 315, biblioteca
  567 -> 731. As grandes são ACA NEOGEO (108), SEGA Ages (19) e Touhou
  (19).

- **Correção no `/api/library/decompor`: reaproveitamento cruzava
  plataforma.** Achado ao preparar o lote, antes de rodar. O endpoint
  procurava o jogo já existente varrendo a biblioteca inteira só pelo
  NOME - então decompor o "Final Fantasy 1-6 Bundle" do Switch acharia
  o "Final Fantasy VI" que já existe como ROM de SNES e enfiaria a
  fonte do Switch dentro do registro do SNES. É o mesmo erro do Celeste
  (GBA x Xbox) que o usuário já tinha corrigido em 27/08: **nome só é
  identidade DENTRO de uma plataforma**.

  Passou despercebido até agora porque o único caso real era o Portal,
  e o "Portal" da planilha por acaso já era Nintendo Switch - o acerto
  foi sorte, não regra. Agora o índice é restrito à mesma plataforma
  (e considera `nomes_alt`, com a mesma precedência de
  `index_by_rom_name`: nome atual primeiro, apelido só se a chave
  estiver livre).

  Teste novo, conferido nos dois sentidos - sem a correção ele falha
  com `(1, 1)` em vez de `(2, 0)`, exatamente o FF VI do SNES sendo
  reaproveitado. Verificado depois no arquivo de verdade: o FF VI
  aparece nas duas plataformas, separado, com a ROM de SNES intacta.

- **Numeração de ordem some da sugestão de decompor.** Nas pastas onde
  o usuário numera a subpasta pra manter a série na sequência ("1.
  Demons of Asteborg", "2. Astebros"), o número é da pasta, não do
  jogo. A trava é exigir ponto/parêntese **e** espaço: sem isso "1979
  Revolution" e "2020 Super Baseball" virariam "Revolution" e "Super
  Baseball". Teste pros dois casos.

  Total: **60 testes Python + 18 de JavaScript**.

  Verificação final: `library-refresh switch` depois do lote devolveu
  **"novo(s): 0   já rastreado(s): 154"** - nenhuma das 13 coletâneas
  voltou.

  O mapa completo das 154 pastas ficou fora do repositório (inventário
  de acervo pessoal, só na máquina).

- **Capa dos 177 jogos novos: 180 sem capa -> 22.** A primeira passada
  achou só 56. A causa das 124 restantes era o **selo da linha de
  relançamento grudado no título oficial**: o SteamGridDB não tem "ACA
  NEOGEO METAL SLUG", tem "Metal Slug".

  O ponto que decidiu o desenho é que os dois casos existem, em
  direções OPOSTAS (conferido na API antes de mexer):

  | busca | resultado |
  |---|---|
  | `ACA NEOGEO METAL SLUG` | nada |
  | `Metal Slug` | achou |
  | `SEGA AGES Out Run` | achou (arte do relançamento) |
  | `Out Run` | nada |

  Então `nomes_alternativos_de_capa` é **fallback**, nunca substituição
  - trocar a busca em vez de acrescentar perderia a outra metade. Teste
  pros dois sentidos, incluindo um que falha se o alternativo for
  consultado à toa quando o nome completo já resolveu.

  Não afrouxa a regra de nunca aplicar capa por aproximação: quem casa
  continua sendo o `find_cover_*`, sempre em match EXATO. O que muda é
  tirar um prefixo conhecido e fixo - reescrita de título, não chute de
  semelhança. Ainda assim é o lote que mais merece conferida, então o
  resultado passou a guardar o par (nome no registro, nome buscado) e a
  CLI lista isso nominalmente no fim.

  Segunda passada: **102 de 124**. Sobraram 22, sendo 3 delas antigas
  (Bomba Patch/Winning Eleven, hacks brasileiros que não estão em
  catálogo nenhum).


## 31/08/2026

- **22 jogos de `~/Downloads/NSWTL-torrents/` de volta pra Biblioteca**
  (o mesmo lote de 28/08, que tinha sumido em algum ponto antes do
  backup de 29/08 - causa não investigada por pedido do usuário, "não
  mexer nos arquivos, só add a biblioteca"). Via `/api/library/add`
  real. Achado no caminho: "Alex Kidd in Miracle World DX" mesclou com o
  registro já existente da Steam (mesmo jogo, duas fontes) - mesmo
  padrão de "A Plague Tale" Xbox+Epic. Dois nomes exigiram decisão:
  "Dusk - TLOZ Twilight Princess port..." é um port fã não-oficial (The
  Legend of Zelda: Twilight Princess via Dusklight/TwilitRealm, não
  Nintendo) e "! TOV (NSP eShop)" virou "Tales of Vesperia: Definitive
  Edition" por inferência (padrão dos outros "Tales of..." do mesmo
  lote) - nenhuma fonte confirmou o nome real.

- **Reorganização completa da pasta NSW no Google Drive** - pedido do
  usuário: "o nome dos arquivos não pode mexer, mas o nome das pastas
  sim, aí já separar também os jogos de coletânea... organizar mods,
  traduções (apagar as que não são em português)". Planejado por
  escrito primeiro (plano mantido fora do repositório), aprovado, e só
  então executado - 355 operações via rclone contra as 175 pastas de
  topo (154 do mapeamento de 29/08 + 21 chegadas por upload do Insync
  nesse meio tempo, incluindo 3 coletâneas novas: Pokémon Brilliant
  Diamond+Shining Pearl, Pokémon Scarlet+Violet, Super Mario Galaxy
  1-2). Resultado: **344 pastas de topo** (175 - 17 cascas de coleção
  decompostas + 186 jogos resultantes - a conta bate exata).

  Achado que mudou o desenho: **17 das 34 pastas "Russian ..." tinham
  update de jogo de verdade largado junto** (6,75 GB dos 12 GB que
  pareciam tradução) - resgatado pra fora antes de apagar. Terceiro
  achado na mesma varredura: **Kingdom of Asteborg (1+2)** tem title-id
  próprio (não é cópia solta) - promovido pro nível de topo mas
  NUNCA apagado/mesclado, decisão deixada pro usuário.

  **Dois bugs de verdade na minha própria execução, achados e
  corrigidos no processo:**
  1. `--fase-ate` do script executor tinha default=99 sem eu perceber -
     a primeira rodada parou aí, sem terminar as outras ~350 operações.
     Sem dano (rclone é seguro reprocessar o que já tinha dado certo,
     só reporta "não encontrado"), mas exigiu uma segunda varredura +
     replanejamento pra retomar do ponto certo.
  2. `achar_traducoes_pra_apagar()` batia o padrão "russian" em
     QUALQUER profundidade sem deduplicar aninhamento - a pasta
     "Failing Forward" do Phoenix Wright e suas DUAS subpastas ("Russian
     Text/Voice Mod") geraram 3 operações de apagar em vez de 1, e a
     ordem das fases também tinha um furo: o resgate dos 4 addons do
     Phoenix Wright (savegame, dublagem EN/JP, desbloqueio de episódios)
     rodava DEPOIS de apagar a pasta que os continha, então a pasta já
     não existia mais quando o resgate tentou - **4 addons foram parar
     na Lixeira do Drive por engano**. Recuperados sem perda via
     `rclone backend untrash` (a mesma chamada trouxe de volta a
     "Failing Forward" também, que só foi reapagada em seguida - sem
     problema, ela não tinha nada pra resgatar). Os dois bugs corrigidos
     no script antes de retomar a execução.

  **Verificação final, não assumida:** varredura fresca depois de tudo
  confirmou 0 pasta ainda com tag `[NSZ]`/`[NSP]`, 0 tradução não-PT
  sobrando (só a exceção do Dragon Quest X em inglês), as 3 PT-BR
  intactas, os 9 dumps extraídos redundantes sumidos, os 14 itens de mod
  todos dentro de `Mods/`.

- **Biblioteca sincronizada com as pastas físicas.** As 3 coletâneas
  novas (Pokémon BDSP, Pokémon Scarlet/Violet) decompostas via
  `/api/library/decompor` - "Super Mario Galaxy 1-2" já tinha sido
  decomposta em algum ponto anterior não identificado com precisão, mas
  conferida e correta (nota/fontes preservados, `nomes_alt` já linkado).

  A varredura seguinte (`library-refresh switch --apply`) achou **16
  "novos"** que não eram coleção recriada (isso o `nomes_alt` já
  bloqueia) - eram **divergência de grafia** entre o nome que eu digitei
  na Biblioteca (27-29/08) e o nome real derivado do arquivo agora que a
  pasta existe fisicamente: apóstrofo reto vs curvo (`'` vs `’`,
  ACA NEOGEO), região mantida vs removida (`(EU)`/`(JAP)`), pontuação
  "bonita" vs literal (":" e "&" vs "," e "and"). O `merge_owned`
  reportou como "possível duplicata" e corretamente NÃO mesclou sozinho
  - 15 desses foram limpos na mão (registro novo e vazio apagado, nome
  real vira `nomes_alt` do registro antigo que já tinha capa/fontes);
  "Kingdom of Asteborg (1+2)" é o único legítimo (nunca teve
  representação na Biblioteca antes, fica como está).

  Confirmado com `library-refresh switch --apply` de novo depois da
  limpeza: **"novo(s): 0 já rastreado(s): 344"** - bate exato com as
  344 pastas físicas. **760 jogos** no total, 340 no Switch.

- **Capa da Biblioteca gravava JPEG dentro de arquivo .png.** Achado ao
  validar as 116 capas recém-baixadas: 20 não eram PNG. O bug já era
  conhecido do projeto desde 02/08 - `launchbox.download_cover` converte
  por causa dele ("o metadado da fonte não é garantia do conteúdo
  real") e existe um `validate-covers` pra caçar o estrago - mas o
  `validate-covers` só varre `capas_root` (ROM), e o caminho da
  Biblioteca nunca tinha recebido a correção: gravava direto o que a URL
  devolvia.

  Novo `gravar_png()`, mesma política do launchbox (deixa passar quem já
  é PNG, converte o resto pelo ImageMagick, e na falta dele grava o que
  veio - melhor ter a capa do que não ter). Varrida a biblioteca
  inteira: **141 arquivos** estavam errados, não só os 20 do lote novo -
  as capas antigas carregavam o problema desde sempre. Todas convertidas,
  703 capas validadas byte a byte, nenhuma sobrou.

  Um erro meu no caminho, pego pelo próprio teste: copiei do launchbox a
  checagem `st_size > 1000` pra decidir se a conversão deu certo. Lá é
  checagem de download vazio; aqui derrubava conversão legítima, porque
  PNG de cor sólida comprime pra ~300 bytes. Agora o que prova a
  conversão é o conteúdo começar com a assinatura PNG.

  Total: **69 testes Python + 18 de JavaScript**.


## 11/09/2026

- **Dedup + capítulos.** Nier Automata, Opus Castle e Tell Me Why
  tinham duplicata (um registro "de posse" completo + um registro
  vazio vindo de sync do Xbox com nome ligeiramente diferente).
  Apagados os vazios, nome antigo virou `nomes_alt` no registro que
  ficou (evita a duplicata recriar numa sincronização futura). Criados
  Opus Castle - Chapter 2 a 6 e Tell Me Why: Capítulo 2 e 3 (mesmo
  gênero/subgênero do capítulo 1 de cada, sem progresso ainda).

- **Gênero 100% preenchido** em toda a coleção (ROM leve + pesada +
  Biblioteca + Desejados), incluindo pesquisa manual pros que
  ScreenScraper/LaunchBox não achavam. Achado um bug real no caminho:
  `.chd` não estava na lista de extensões do PSP em `config.toml` (PS2
  já tinha - só o cache `cache/heavy_catalog.json` estava
  desatualizado). A correção revelou 9 jogos de PSP e 23 de PS2 em
  `.chd` que estavam invisíveis.

- **Unificação de botões (ROMs leves/pesadas/Biblioteca).** Os 3 tipos
  de card ganharam o mesmo par de ícones 🖼 (buscar/trocar capa) + ✎
  (editar dados: nome, gênero, data que finalizou, tempo, comentário)
  no mesmo lugar. O botão de comentário (💬) separado foi removido dos
  cards - virou parte do ✎ - mas continua existindo na lista de
  Ranking/🎮 Jogando.

  ROMs pesadas tinham DUAS buscas de capa diferentes (LaunchBox/
  ScreenScraper por nome de ROM + SteamGridDB) - viraram um popup só
  com abas pra escolher a fonte. Renomear (arquivo de verdade) entrou
  pro mesmo modal do ✎ nas 3 abas.

  `rom_tracking_info()` em `core/library.py` virou o lugar único que
  monta os campos de tracking de uma ROM - antes essa lógica estava
  DUPLICADA (leve e pesada) e uma cópia nunca ganhou tempo/observações
  quando os outros campos foram adicionados, causando um bug real
  (modal de editar sempre aparecia vazio nesses dois campos mesmo com
  dado salvo).

- **Lista de Desejos (nova aba "🌟 Desejados").** Steam sincroniza
  sozinha (endpoint público `IWishlistService/GetWishlist` +
  `appdetails` pra nome/gênero/capa - o endpoint antigo `wishlistdata`
  foi descontinuado pela Valve sem aviso). PSN e Xbox não têm API de
  wishlist confiável, então o usuário cola a lista direto na tela.

  `sync_wishlist()` faz DIFF de verdade (diferente de `merge_owned`,
  que só adiciona) - nome que sai da lista colada perde a marca
  `wishlist:<fonte>`, e se não sobrar nenhuma outra fonte no registro,
  o registro inteiro é apagado via `remove_game()` (decisão explícita
  do usuário: lista de desejos não tem progresso pra perder). **Esse
  mecanismo voltou a morder de verdade na sessão seguinte, ver
  12/09.**

- **Tempo total "de todas as fontes".** `merge_owned()` passou a
  preencher `tempo` a partir do `playtime_forever` da Steam, só quando
  o registro ainda não tinha nenhum tempo digitado à mão. 24 jogos
  ganharam tempo que nunca tinham.

- **Filtros unificados.** ROMs leves, pesadas e Biblioteca ganharam os
  mesmos 4 filtros de tracking (▶/✓/🏆/🎭) como checkboxes
  independentes, combináveis em "OU" - `libraryMatchesFilters()`
  mudou de assinatura (status virou objeto de flags).

- **Pendências deixadas em aberto** (perguntadas ao usuário, sem
  resposta na hora): id duplicado entre duas "Life is Strange: True
  Colors" (mesmo id `life-is-strange-true-colors-nintendo-switch`,
  `_slug()` não checa colisão contra id "roubado" por edição anterior
  de plataforma); 6 registros "Twinmotion EDU" vindos do Heroic (não é
  jogo); 3 capas de DOOM sem match exato no SteamGridDB. **Nenhuma
  dessas foi resolvida ainda** (12/09 tratou de coisas diferentes).


## 12/09/2026

Sessão longa, em cima do que 11/09 deixou pronto (wishlist, sorteio,
filtros unificados).

- **Incidente real de perda de dado, recuperado sem perda final.** Ao
  adicionar 1 jogo na wishlist da Xbox pela tela, o campo colado ficou
  só com o nome novo (não a lista inteira) - `sync_wishlist()` (ver
  11/09) tratou isso como "a lista inteira agora é só esse 1 jogo":
  129 perderam a marca `wishlist:xbox`, 125 sem nenhuma outra fonte
  foram apagados de vez via `remove_game()`. O log da tela confirmou
  que rodou e salvou.

  Auditoria (Google Drive guarda até 100 versões/30 dias de cada
  arquivo via o Insync do usuário) achou a versão de 13:27 (antes do
  acidente) e a de 18:26 (depois) - mas comparando as duas, **o
  arquivo AO VIVO no disco não batia com nenhuma delas**: tinha os 129
  intactos E o playtime da Steam atualizado. Causa raiz real: a
  sincronização da Steam rodou CONCORRENTE com a da Xbox, carregou o
  `library.json` numa versão anterior ao estrago, e salvou por cima ao
  terminar - um "lost update" clássico que por sorte desfez o dano da
  Xbox (também apagou a tentativa de adicionar o jogo novo).

  **Causa raiz de fundo, ainda NÃO corrigida no código:** `_library_lock`
  (`gui/server.py`) só protege as rotas síncronas listadas em
  `_ESCRITA_BIBLIOTECA` - os jobs em background (`run_wishlist_sync_job`,
  `run_library_refresh_job`, `run_library_fetch_covers_job`, etc, todos
  em `gui/server.py`) fazem seu próprio ler→modificar→gravar sem
  nenhum lock. Dois desses rodando ao mesmo tempo colidem por
  definição. Funcionou por acaso dessa vez; **vale envolver esses jobs
  no mesmo lock antes que aconteça numa ordem que NÃO desfaça sozinho
  o problema.**

  Diablo® Prime Evil Collection (o jogo que a Xbox tentava adicionar)
  foi readicionado manualmente depois, com a lista completa dessa vez.

- **Editar gênero na Wishlist.** Card de Desejados ganhou o mesmo ✎ já
  usado em ROM/Biblioteca (`buildDesejadoCard`) - motivado
  diretamente pelo caso acima (Diablo sem gênero, sem forma de
  corrigir pela tela). `/api/wishlist` passou a devolver o registro
  inteiro (`{**g, "capa_url": ...}`, igual `/api/library` já fazia)
  em vez de só id/nome/gênero/capa_url - sem isso o modal zerava
  plataforma/tempo/observações existentes ao salvar. Achado no
  caminho: `#editar-modal` não tinha z-index alto o suficiente pra
  abrir por cima de OUTRO modal (Desejados) - mesmo bug já resolvido
  antes só pro modal de capa (`#capa-modal { z-index: 110 }`),
  replicado pro editar.

- **Sorteio ganha filtro de gênero**, combinável com o grupo/sistema
  já existente. Achado no processo: ROM leve/pesada guarda no pool o
  nome de ARQUIVO (com extensão), mas o cruzamento com o gênero da
  Biblioteca (`find_for_rom`) exige o nome sem extensão - sem tirar o
  `Path(nome).stem` antes, o filtro combinado com ROM sempre dava pool
  vazio, silenciosamente (só funcionava por acidente pra Biblioteca).
  Depois ganhou também sub-grupos de plataforma dentro da Biblioteca
  (Nintendo Switch/Xbox/PlayStation/PC) - Xbox junta as 4 gerações
  gravadas, PlayStation junta PSN/PS3/PS4 (só 39 jogos, não compensa
  separar), PC é o resto (Steam/GOG/Epic/Amazon + os poucos
  Android/iOS).

- **Pendências da reorganização de 31/08 fechadas.** "Kingdom of
  Asteborg (1+2)" confirmado redundante (mesmos 2 jogos já existiam
  separados, com title-ids diferentes - é só o cartucho de compilação
  por cima) e apagado. As 3 subpastas de title-id dentro de "Super
  Mario 3D All-Stars" confirmadas como estrutura legítima (o jogo
  empacota Mario 64/Sunshine/Galaxy como 3 programas de verdade) -
  mantidas, sem ação.

- **43 pastas de `~/Downloads` (torrent) organizadas e subidas pro
  Drive.** 4 coleções reais decompostas na mão conferindo cada
  arquivo por title-id (Deponia em 4, SNK NeoGeo Pocket Games em 13,
  MGS Master Collection em 5, Vol 2 em 3); resto só limpou a tag de
  formato do nome. Duas pastas de tradução russa tratadas com o mesmo
  padrão de 31/08 (Persona 4 Golden tinha um update de verdade
  escondido dentro - resgatado antes de apagar o resto; Metroid Prime
  Remastered não tinha nada pra resgatar). Achada e apagada 1
  duplicata (Mega Man Battle & Fighters" com "&" x "and", mesmo
  title-id, já existia de antes com o "and"). Depois do upload:
  sincronizado com a Biblioteca (38 jogos novos, 343 já rastreados),
  capa buscada (1569 baixadas na coleção inteira, incluída de brinde
  já que o job varre tudo que falta) e gênero preenchido pros novos
  (13 via LaunchBox, 25 sem match - a maioria exclusivo de console sem
  versão PC pra cruzar).

  Renomeios extras pedidos depois de ver o resultado: "! TOV (NSP
  eShop)" -> "Tales of Vesperia"; 15 pastas com `(US)`/`(EU)`/`(JAP)`/
  ano perderam o parêntese; "Duke Nukem 3D homebrew ..." perdeu a
  palavra "homebrew"; "Dusk - TLOZ Twilight Princess port for
  Nintendo Switch" virou "The Legend of Zelda Twilight Princess" (2
  passadas: primeiro só limpou o nome, depois tirou "Dusk" de vez -
  ver nota abaixo sobre o que sobrou). 9 desses já tinham registro
  rastreado - `nome` atualizado e nome antigo guardado em `nomes_alt`
  em cada um, pra não perder o vínculo (mesmo padrão de sempre pra
  rename de pasta).

  **Nota**: o "Dusk" no nome original era o NOME do forwarder homebrew
  usado pra rodar o jogo de GameCube/Wii no Switch (pasta interna
  `dusk/`, com `dusk.nro` + a imagem de disco) - o usuário decidiu
  tirar mesmo assim, então o vínculo com "como o jogo roda de verdade"
  ficou só no `nomes_alt`, não mais no nome visível.

- **Barra de filtro/ação virou linha única com rolagem nas 3 abas**
  (achado do usuário testando no celular - `.filterbar`/`.menubar`
  tinham `overflow` implícito em vez de rolagem, cortando "Só sem
  gênero" e outros itens sem nenhum jeito de alcançar; a Biblioteca
  usava a classe errada, `search-bar`, pensada pra campo de busca).
  ROM leve e pesada ganharam a mesma seção "▸ Ações" recolhível que a
  Biblioteca já tinha, fechada por padrão. `.actions` e `.menubar`
  eram a mesma coisa disfarçada de duas classes - unificadas numa só;
  botões de ROM leve trocaram o estilo padrão (azul, grande) pelo
  `tiny secondary` cinza que as outras duas abas já usavam, pra ficar
  visualmente coeso. O modal de Sortear (`search-bar` também) ficou de
  fora da primeira correção e só foi pego numa rodada seguinte.

- **Editar dados de ROM pesada funciona mesmo só-no-Drive.** O botão
  ✎ inteiro ficava escondido quando o arquivo não estava baixado
  (`notInPc`) - só o campo "Nome" precisa do arquivo de verdade
  (renomear), gênero/tempo/observações não. Agora só esse campo some
  (mesmo padrão já usado em ROM leve sem capa), o resto funciona e
  cria o registro na Biblioteca sem precisar baixar nada primeiro.

- **Auditoria completa de gênero: 43 categorias -> 33, revisão manual
  de 362 jogos.** Levantados todos os gêneros da coleção com contagem
  e amostra de jogos antes de mexer em qualquer coisa (pedido do
  usuário: "trazer as dúvidas" em vez de decidir sozinho). Fundidos
  duplicados de verdade (mesmo conceito, fonte devolvendo grafia/
  idioma diferente): Puzzle/Quebra-cabeças, Card Game/Jogo de cartas,
  Casual/Jogo casual, Compilação/Coletânea, "Corrida, Pilotagem"/
  Corrida, Educação/Educacional, "Jogo de Tabuleiro" (maiúsculo) e
  "... Asiático" tudo em "Jogo de tabuleiro", e Música/"Música e
  dança"/Ritmo em Ritmo (Patapon 2 e 3 tinham caído em categorias
  diferentes um do outro). Depois, mais 2 nichos de 2 jogos cada
  migrados pros parentes óbvios: "Esporte com animais" (corrida de
  cavalo) -> Corrida, "Tiro com Lightgun" -> Tiro.

  O achado mais importante ficava só no CÓDIGO: `NORMALIZACAO_FINAL`
  em `core/generos.py` mandava todo beat'em up pra "Luta", mas a
  coleção real tinha "Briga de rua" convivendo como categoria
  separada - com a MESMA franquia dividida entre as duas (Double
  Dragon ficou onde estava, Double Dragon Gaiden foi pra Luta;
  Streets of Rage 1-3 ficaram, Streets of Rage 4 foi pra Luta).
  Revisão manual dos 362 jogos de Luta+Briga de rua corrigiu 20 casos
  errados (toda a série Double Dragon, TMNT arcade, Streets of Rage
  4, X-Men arcade, Batman Beyond, Shadow Force, Rushing Beat, Dragon
  Ninja, Dynasty Warriors 1-2 pra Briga de rua; Panzer Bandit no
  sentido contrário) e a regra de normalização foi corrigida pra não
  voltar a divergir.

  **Ficou sem decisão** (título genérico demais ou franquia com
  versões diferentes, sem forma de saber qual é qual sem mais
  contexto): Hokuto no Ken / Hokuto no Ken 2 (em Luta) vs o Hokuto no
  Ken que já está em Briga de rua; Guardian e Legend (nome vago
  demais); Robot Wars - Advanced Destruction; e o gênero real de "The
  Super Spy" (único jogo em "Variados", categoria-lixo de 1 item).

  Total: **109 testes Python + 22 de JavaScript**.
## 15/09/2026

- **Auditoria técnica — travessia de caminhos fechada (#1 e #3).**
  `/api/heavy/delete` e `/api/heavy/rename` agora validam `label`/
  `old_label` antes de chegar às rotinas de arquivo; valores como `..`,
  caminhos absolutos e subpastas não podem mais escapar da pasta do sistema.
  `GET /images` passou a conferir o caminho resolvido com `dentro_de()` — o
  teste anterior usava `../` cru, normalizado pelo cliente HTTP, e por isso
  não reproduzia o bypass real com barras percent-encoded. O teste de
  integração agora usa esse payload real e também cobre os dois endpoints de
  ROM pesada.

- **Lost update de `library.json` corrigido (#4).** Os quatro jobs da GUI
  (refresh, wishlist, cadastro e busca de capas), as rotas síncronas, os
  checkpoints de gênero e os comandos equivalentes da CLI agora participam
  da mesma exclusão mútua. O lock combina `RLock` entre threads com `flock`
  entre processos locais; fica em `/tmp`, sem criar lixo na pasta
  sincronizada. Trabalhos longos de capa não seguram o arquivo por minutos:
  acumulam só as capas encontradas e aplicam esses campos sobre a versão mais
  recente em checkpoints. Um teste concorrente reproduz o incidente de 12/09
  e confirma que dois cadastros simultâneos sobrevivem.

- **`covers_registry.json` atômico e serializado (#5).** GUI e CLI usam o
  mesmo lock durante o ciclo completo, e a gravação passou a temporário +
  `replace`, evitando JSON parcial e alterações perdidas entre busca de capas
  e ações manuais. Total depois deste bloco: **112 testes Python + 22 de
  JavaScript**.

- **Autenticação/rede unificada com os apps pessoais (#2).** Em vez de criar
  outra senha dentro do PyRetro, o padrão comum ficou: identidade do
  Tailscale + HTTPS pelo Serve, backend preso a `127.0.0.1`. O PyRetro está
  publicado em `https://maquina.tailnet.ts.net:8443/`; a porta 8000
  direta deixou de aceitar LAN/Tailscale. O servidor agora usa localhost por
  padrão (`--host` explícito para exceções), exige token CSRF em todo POST e
  envia CSP, HSTS quando está atrás do proxy HTTPS, proteção contra iframe,
  MIME sniffing e vazamento de Referer. A interface injeta o token em todas
  as mutações por um wrapper central de `fetch`. Testes novos cobrem recusa
  sem token e os cabeçalhos.

- **Downloads, sync e configuração endurecidos (#6–#8).** Aplicar capa por
  URL agora aceita somente uma URL exata devolvida pela busca atual do
  SteamGridDB, não segue redirects, limita a resposta a 15 MB e mata o
  ImageMagick após 30 segundos. `config.toml` passou a lock + temporário +
  `replace`; caminhos vazios, relativos ou amplos como `/`/`$HOME` são
  recusados. `emu-sync` grava no plano o mtime da origem e o revalida antes
  de cada cópia; se o save mudou nesse intervalo, aquele arquivo é cancelado
  em vez de sobrescrito. Sync e envio de ROM pesada também compartilham um
  mutex entre GUI e CLI.

- **Manutenção defensiva da auditoria (#10/#11).** Corpo JSON tem teto de
  22 MB, erro 500 não expõe exceção interna, filas SSE e caches ficaram
  limitados, jobs consumidos saem do registro, transferências ADB ganharam
  timeout adequado a ROMs grandes e `/tests/test_app.html` só é servido
  diretamente em localhost. Total: **120 testes Python + 22 JavaScript**.
  A colisão de id de duas entradas de *Life is Strange: True Colors* segue
  sem mudança: é uma decisão de modelagem/dado já pendente com o usuário,
  não algo seguro de resolver automaticamente durante a auditoria.

## 28/10/2026 — auditoria (AUD28-01 a 04), Sortear, cor da nota e pódio

- **Auditoria:** hostname do tailnet trocado por exemplo neutro (com teste `test_public_docs.py` que
  barra novas ocorrências); save inicial do celular sem versão anterior agora é aplicado
  (`drive_pending.apply` manda `'-'`); Organizar recusa CUE com faixa faltando e recusa nomes que
  colidem depois da limpeza, antes de mover qualquer coisa, e publica o `.cue` por último.
  363 testes Python. O histórico do Git ainda contém o hostname antigo (etapa separada).
- **Modo TV:** Sortear com painel próprio (resumo de grupo/gênero, Sortear jogo / Sortear novamente).
- **Nota:** escala comum (vermelho 0–1, laranja 4, amarelo 6,5, verde 7→10; só a nota 11 é
  dourada, "jogo muito especial"). Não existe 10,x: o editor pula de 10 para 11 e de 11 para 10;
  valores já gravados entre 10 e 11 continuam visíveis com o verde de 10. Web, modo TV e Android
  (0.15.0, code 23, selos coloridos, ficha e testes JVM com as mesmas amostras).
- **Ranking:** Top 3 da seleção em pódio 2–1–3 (modo TV e Android), aviso de empate alfabético.
  Pódio conferido no modo TV; no celular só instalado (sem Tailscale, o cache não tinha notas).
- Testes: 363 Python, 51 JS, JVM com `NotaRulesTest`.

## 28/10/2026 — ícones de plataforma (etapa B do plano)

- **Manifesto único** `assets/platforms/manifest.json` (34 plataformas e lojas, aliases por código de ROM
  e por nome de fonte, cor e sigla). `tools/build_platform_icons.py` gera `gui/static/platforms.js`
  (web e modo TV) e `PlatformData.kt` (Android); `tests/test_platforms.py` falha se os gerados
  ficarem desatualizados, se um alias pertencer a duas plataformas ou se o contraste do texto
  branco ficar abaixo de 4,5.
- Plataforma sem ícone cai num selo neutro com as três primeiras letras (nunca fica sem selo).
- Selos são decorativos (o nome continua escrito ao lado) e não entram no texto do elemento.
- Aplicado em: cartões, ficha, abas de plataforma e Sistemas do modo TV; cartões e lista da web;
  cartões e ficha do Android **0.16.0 (code 24)**, instalada e conferida no celular
  (selos N64/GBC e pódio do Ranking). Os ícones são desenho próprio (cor + sigla), sem logotipos
  de fabricantes. Testes: 367 Python, 54 JS, JVM com `PlatformRulesTest`.

## 28/10/2026 — armazenamento do PC, etapa E (modelo e prévia, sem mover nada)

- `core/storage.py`: `Layout` (resolvedor único de destinos; NSW com raiz própria e uma pasta por
  título) e `plan` (prévia somente leitura: destinos, tamanhos, dependências CUE/GDI/M3U, colisões,
  links, espaço e consumidores da pasta antiga). `python3 -m core.storage` imprime a prévia.
- Nenhum consumidor foi religado e nada foi copiado. Detalhes e ordem da migração em
  [`armazenamento.md`](armazenamento.md). Pedido de ajustes (lançador, overrides do Flatpak,
  Insync) enviado à conversa do setup. 375 testes Python.

## 28/10/2026 — perfis de controle (Series S, G8 e WGP16 ao lado do Xbox One)

- Registro `assets/controllers/controllers.json` (principal: Xbox One). `tools/configure_xbox.py`
  ganhou `--detect`, `--learn <id>` e `--controller <id>`; o nome do Dolphin e o GUID do Azahar vêm
  do registro. Series S, G8 e WGP16 estão cadastrados, mas **ainda não medidos** (precisam estar
  conectados). 379 testes Python.
- Teste do Insync feito pelo Victor: desmarcar uma pasta apaga a cópia local (ver `armazenamento.md`).

## 28/10/2026 — migração de armazenamento, etapa (a): cópia verificada de ROMs e BIOS

- `core.storage.copy_verified/copy_items` + `python3 -m core.storage --copy roms,bios`: copia para
  arquivo parcial, confere SHA-256 na origem e no destino, recusa origem alterada durante a cópia,
  nunca sobrescreve nem apaga a origem, é idempotente e grava recibo.
- Rodada real: 1.915 arquivos, 41,7 GB (44.787.416.639 bytes), 0 erros; contagem e bytes conferem
  com o Drive. Insync não foi tocado. Setup: (b) lançador com duas raízes e (c) overrides do
  Flatpak preparados (`ed0ef33` no setup); (d) caminhos dos emuladores em andamento.

## 28/10/2026 — PyRetro religado às ROMs em ~/Games/PyRetro

- `core.storage.apply_config`: `[storage]` (`games_root`, `nsw_root`, `migrated`) troca as raízes
  por categoria na configuração carregada (`retrosync.load_config` e o servidor); `pc.nsw_root`
  mantém o NSW antigo até ele migrar (`library.pasta_nsw`). `config.toml` do Victor: roms e bios migrados.
- Playlists do RetroArch regeneradas (`rebuild-playlist`) pelo layout novo, com backup.
- A prévia resolve links: `~/Downloads` é `~/Drive/Temp`, então NSW em `~/Downloads/NSW` é bloqueado.
- Reteste dos emuladores pelo caminho novo (SNES, DS, PS1, PSP, GC, 3DS, PS2): abrem e rodam; os
  saves/estados gerados pelos testes foram removidos (lista de arquivos igual à original).
  Zelda Molblins (DS) mostra um erro de gravação do próprio jogo; pendente. 388 testes Python.

## 28/10/2026 — NSW em ~/Games/PyRetro/NSW, ROMs e BIOS prontas para desmarcar

- NSW fora do Drive: padrão `~/Games/PyRetro/NSW` (a raiz do NSW pode ser subpasta da de jogos).
  Título local copiado e verificado; `[storage] migrated` do Victor agora é roms, bios e nsw.
- Etapa F: `core/removal.py` (prévia/aplicação de remoção local, Drive e ambos) com testes; ainda
  sem servidor/interface, e o Drive espera o rclone com escrita. 396 testes Python.

## 28/10/2026 — remoção ligada ao servidor; Zelda Molblins; ROMs/BIOS desmarcadas

- Victor desmarcou ROMs e BIOS no Insync: local sumiu do Drive, nuvem manteve tudo (21 pastas de
  ROMs, 353 BIOS); `~/Games/PyRetro` íntegro. Setup foi pedido para limpar os caminhos antigos.
- `GET /api/storage/removal-plan` e `POST /api/storage/removal-apply` (PC; protege jogo iniciado e
  jogo em execução; Drive bloqueado enquanto `[rclone] can_write` não for verdadeiro).
- Zelda Molblins (DS): o erro "something bad happened while trying to write to your cart" some com
  um `.sav` em branco de 512 KB em `Saves/saves/NDS/` (o melonDS não tem tipo de save para essa ROM de
  fã). Criado esse arquivo; confirmar jogando.

## 28/10/2026 — modo TV: rodapé compacto, filtros recolhíveis e glifos do controle (etapa A)

- Rodapé com uma linha de atalhos e "Mais atalhos" expansível; avisos de fim de sessão somem ao
  trocar de coleção.
- Plataforma e gênero ficam atrás de um botão "Filtros (n) ▾/▴" (lembrado entre sessões); o Sortear
  continua sempre aberto.
- Glifos: Xbox (A/B/X/Y, LB/RB, LT/RT), PlayStation (✕/○/□/△, L1/R1, L2/R2) ou Automático pelo
  controle conectado; o botão "Botões" nas opções escolhe manualmente. Os bindings não mudam.
  Conferido no navegador; sem teste automatizado novo (as funções vivem no escopo do `tv.js`).

## 28/10/2026 — identidade visual (etapa D): ativos gerados, nada instalado

- `tools/build_brand.py` gera `assets/brand/` (SVG, monocromático claro/escuro com o play como furo
  real, PNG de 16 a 512, `favicon.ico`, folhas de conferência) a partir do símbolo proposto.
- **Aguardando aprovação do Victor** para trocar favicon, marca do modo TV, atalho do Steam e ícone
  do Android (assinatura e package ID não mudam). Falta ainda a variante simplificada de 16/24 px
  (nesses tamanhos o play se perde) e o ícone adaptativo do Android.

## 28/10/2026 — Capas migrada para ~/Games/PyRetro/Capas

- Cópia verificada por hash (1.931 arquivos, 1,1 GB, 0 erros); `[storage] migrated` do Victor agora
  é roms, bios, nsw e capas. Capas servidas de lá; links de capa dos emuladores refeitos.
- Biblioteca, Backups e Saves seguem no Drive: ver `armazenamento.md` (substitutos necessários).

## 28/10/2026 — identidade visual instalada (etapa D, aprovada pelo Victor)

- Monograma PR com play em negativo em todas as superfícies: favicon da web e do modo TV (variante
  sem o play em 16/24 px, `assets/brand/pyretro-pequeno.svg`), marca no cabeçalho do modo TV,
  atalho desktop (`Icon=pyretro` no tema hicolor do usuário, PNGs de 16 a 512 e SVG), ícone do
  atalho Steam (só o campo `icon`; appid, artes e tags preservados, cópia do VDF em
  `~/.local/share/pyretro/steam-shortcuts/`) e Android **0.17.0 (code 25)** com ícone adaptativo,
  monocromático (Android 13) e placeholder dos cartões. Package e assinatura não mudaram.
- `tools/build_brand.py` gera tudo a partir do SVG; `tools/install_tv.py` instala os ícones.

## 28/10/2026 — rclone com escrita (escopo drive)

- Victor reconectou o rclone com `scope = drive` (antes `drive.readonly`). Teste: gravar e mandar um
  arquivo descartável à lixeira do Drive (`deletefile` vai para a lixeira por padrão; lixeira
  confirmada com `--drive-trashed-only`). `[rclone] can_write = true` no `config.toml`; a prévia de
  remoção já lista as cópias reais do Drive (ex.: PS, 4 arquivos, ~650 MB). Nada foi removido.

## 28/10/2026 — camada de nuvem independente (início)

- `core/cloud.py` (interface `Storage`, `RcloneStorage`, `MemoryStorage`) e `core/cloud_saves.py`
  (saves por manifestos por dispositivo, sem escrita condicional; conflito explícito; histórico).
  21 testes, inclusive contra o remoto local do rclone. Plano em [`nuvem.md`](nuvem.md). Ainda não
  está ligado ao lançador nem ao Android.

## 28/10/2026 — limpeza das ROMs locais (só em andamento; o resto sob demanda)

- PC: 20 arquivos (20,5 GB: ROMs pesadas e NSW) apagados após `rclone check` com cópia idêntica no
  Drive; ROMs leves mantidas até o download sob demanda delas existir no PC.
- Celular: 12 ROMs (3,5 GB) apagadas após MD5 igual ao do Drive; saves e dados dos emuladores intactos.

## 28/10/2026 — ROMs leves sob demanda no PC; limpeza das leves

- `heavy_roms.downloadable_systems` (leves + pesados) no download; `download_staging` em
  `~/Games/PyRetro/.pyretro/staging`; `sortear.build_pool` sorteia leves também do Drive; o catálogo da
  TV lista e baixa leves do Drive; a lista de um sistema leve no modo TV passou a usar o catálogo.
  Catálogo do Drive atualizado com os leves (MD refeito à parte: a primeira consulta falhou sem erro).
- Prova: `Tennis.nes` apagado, oferecido pelo catálogo, baixado pela rota `/api/heavy/download`, hash
  idêntico. Depois, 1.318 ROMs leves (16,3 GB) apagadas com cópia idêntica no Drive; Arcade mantido.
- Castlevania SotN (jogo sorteado) apagado por engano do celular e do PC e restaurado nos dois (MD5 igual).

## 28/10/2026 — nuvem no PC (saves, Biblioteca, Backups), remoção na ficha e WGP16

- **Saves (G, lado PC):** copiados e verificados para `~/Games/PyRetro/Saves` (418 arquivos, 557 MB); `[cloud]`
  no `config.toml` (remoto `drive:Jogos/PyRetro-Nuvem`); `core/cloud_sync.py` + rotas
  `/api/cloud/saves/{status,sync,resolve}`; cache de hash (não relê 560 MB a cada vez). Primeiro envio feito
  em segundo plano. **Ainda não migrado:** caminhos dos emuladores e overrides (setup) e `[storage] migrated`.
- **Biblioteca e Backups sem Insync:** `core/cloud_snapshots.py` envia uma versão nova e imutável do
  `library.json` a cada gravação (com espera de 30 s), mantém as 30 últimas (as velhas vão para a lixeira do
  Drive), restaura com hash conferido e envia os arquivos novos dos Backups sem apagar nada. Rotas
  `/api/cloud/snapshots[/publish]` e CLI `python3 -m core.cloud_sync status|sync|publish|versions|restore-library`.
- **Remoção na ficha do jogo (modo TV):** botão "🗑 Remover…" com as três opções, prévia dos arquivos do PC e
  do Drive, proteção de jogo em andamento e confirmação com a frase exata. A prévia resolve o arquivo a
  partir do nome do catálogo e, sem cópia no PC, lê o descritor do Drive.
- WGP16 Nova II medido (aparece como "Sony Interactive Entertainment Wireless Controller", GUID no registro).
- 433 testes Python.

## 28/10/2026 — Android 0.18.0: camada de nuvem (saves) e envio paralelo no PC

- Android 0.18.0 (code 26): `CloudStorage`/`MemoryCloudStorage`, `DriveCloudStorage` (Drive da conta
  conectada, pasta `Jogos/PyRetro-Nuvem`), `CloudSavesEngine` (mesmo protocolo do notebook, com prefixo por
  grupo: saves/, states/, PPSSPP/SAVEDATA/, PPSSPP/PPSSPP_STATE/, Lime3DS/sdmc/), `CloudPhone` (pastas SAF
  pelo `FileSync`) e botão "☁ Saves na nuvem (novo)" em Situação. 85 testes JVM (9 de nuvem). Compilado e
  validado por lint; **não instalado nem testado no aparelho** (desconectado). O sync antigo continua.
- PC: o motor envia os blobs em paralelo (8); o primeiro envio ficava em ~4 objetos/minuto.

- Lançador: `Sessions(before, after)` — com `[cloud] auto = true` o PyRetro baixa/envia os saves antes de abrir
  (até 30 s) e depois de fechar o jogo; falha na nuvem nunca impede de jogar. Desligado por padrão até os
  caminhos dos emuladores migrarem. 434 testes Python.

## 28/10/2026 — saves migrados para ~/Games/PyRetro/Saves

- Primeiro envio à nuvem concluído (463 objetos, 578 MB, 0 erros; 405 conteúdos distintos, nenhum faltando).
  Caminhos de saves dos emuladores trocados pelo setup (com cópia) e `[storage] migrated += saves`.
  Aguarda a validação do Victor jogando em cada emulador.

## 28/10/2026 — saves validados; overrides do Drive retirados; sincronização automática ligada

- Victor validou os saves em cada emulador. `install-emulator-access.py --sem-drive --apply` retirou os
  overrides do Flatpak que apontavam para o Drive (cópia em `~/.local/state/bonisarch/backups/overrides-*`).
- `[cloud] auto = true`: o PyRetro baixa os saves antes de abrir um jogo e envia ao fechar.
- Falta: desmarcar `Saves` e `Capas` no Insync (Victor) e testar o app 0.18.0 no celular.

## 28/10/2026 — saves na nuvem testados no celular (Android 0.18.1)

- Teste real: o celular comparou com o Drive (27 enviar, 4 baixar, 1 conflito), sincronizou e resolveu o
  conflito do Final Fantasy VI a favor do celular; o notebook baixou a versão do celular (a do PC ficou em
  `.pyretro-history`) e os 27 arquivos de `Lime3DS/sdmc` do celular.
- Defeito achado no teste e corrigido (PC e Android): duas entradas que citam uma à outra em `base` se
  anulavam e o save "sumia" das cabeças. Agora uma entrada só substitui outra mais antiga. 25 testes de
  nuvem; JVM com teste de paridade.

## 28/10/2026 — Arcade sob demanda (zips pai) e limpeza do Arcade local

- `core/arcade.py`: lê o DAT do FinalBurn Neo (`romof`) e calcula a cadeia pai/BIOS; o download de um clone
  baixa os pais que faltam (BIOS fica em `BIOS/RetroArch`); a remoção não tira um pai que outro zip local usa.
  Nenhum jogo do acervo atual depende de outro jogo (só de BIOS), então a coleção já era segura.
- Arcade local apagado (219 arquivos, 3,4 GB, todos com cópia idêntica no Drive). Provado: `2020bb.zip`
  baixado pela rota e aberto no RetroArch (fbneo + BIOS local). Artefatos do teste (estado e .fs) removidos.

## 28/10/2026 — protocolo antigo de saves removido; Android 0.19.0

- **Android 0.19.0 (code 28):** o botão 💾 Saves da ficha e a tela "Saves e estados" usam só o motor de nuvem
  (por jogo no RetroArch; grupo inteiro em PSP/3DS). Removidos o sync com o notebook por HTTP (`FileSync.analyze/
  apply/upload/download`), `DriveSaves` (pendências pelo Insync), `SaveReviewText` e as telas antigas de
  comparação/versões do notebook. Teste real no aparelho: comparação e sincronização por jogo ("Tudo em dia").
- **Notebook:** removidos `core/drive_pending.py`, `core/drive_saves.py`, as rotas `/api/drive_pending*`, o cartão
  "Saves enviados pelo celular" do modo TV e seus testes. `core/mobile_sync.py` e `/api/mobile/sync/*` ficam por
  ora (só o app antigo os usava; `game_save_ids` ainda reutiliza as regras de grupo). 426 Python, 54 JS, JVM.
- A lista de um sistema leve no modo TV agora vem do catálogo (PC + Drive); testes ajustados.

## 29/10/2026 — Biblioteca com diário SQLite; Biblioteca e Backups em ~/Games/PyRetro; Series S medido

- `core/library_journal.py`: a cada gravação do `library.json` o diário (`library-journal.db`, SQLite) registra só
  o que mudou (jogo novo/removido, campo alterado/removido, metadados). A nuvem recebe segmentos imutáveis
  (`journal/<dispositivo>/de-até.json`, algumas centenas de bytes por edição) e o arquivo inteiro só como snapshot
  de compactação (o primeiro, a cada 24 h ou após 2.000 mudanças). `pull_library` junta mudanças de outro
  dispositivo campo a campo (vence a mais recente; remoção perde para edição local mais nova; sem eco).
- Biblioteca (2,2 GB com capas) e Backups copiados e verificados para `~/Games/PyRetro`; `[storage] migrated`
  inclui `biblioteca` e `backups`. Primeiro snapshot enviado; Backups subindo.
- Xbox Series S medido (SDL: "Xbox Series X Controller"). Registro: Xbox One, Series S e WGP16 medidos; G8 não.

## 29/10/2026 — limpeza de jogos e saves a pedido do Victor

- ROMs removidas (cópia idêntica no Drive): `2020bb.zip`, `Kirbys Adventure.nes`, Zelda Molblins (PC e celular).
- Saves apagados no PC, no celular e na nuvem: Molblins.sav, `Lime3DS/sdmc` (3DS) e PPSSPP `ULUS10021000`, `ULUS10266`,
  `ULUS10437GameData00`; ficou Patapon 2. Foi preciso editar os manifestos à mão (o motor não propaga exclusão): pendência
  de "tombstone" registrada para o Codex.
- Moemon Ruby e KOF '97 baixados em ambos e marcados como iniciados.

## 29/10/2026 — Switch → Drive pelo PyRetro (só PC)

- Outbound (base, update e DLC Schoolbus Adventures) subiu para `Jogos/ROMs/NSW/Outbound/` (conferido por hash),
  entrou na Biblioteca com capa (ScreenScraper) e gênero Simulação (escolha manual: nenhuma fonte achou).
- Novo `core/switch_upload.py` + seção "Switch → Drive" no 🗂 Organizar: lê dumps NSP/NSZ/XCI/XCZ em Downloads,
  sugere o nome limpo da pasta (editável), permite escolher o gênero (ou automático via ScreenScraper), envia com
  `rclone copyto`, confere com `rclone check` e só então manda a origem para a lixeira. Rotas
  `GET /api/switch/upload/pending` e `POST /api/switch/upload`. 5 testes novos (459 no total).

## 29/10/2026 — janela nativa do modo TV

- `gui/app.py`: janela PyQt6/QtWebEngine para `/tv` (ID `pyretro-tv`), inicia `pyretro-gui` se parado.
  `tools/pyretro-tv.sh` usa a janela nativa e cai no Chrome sem PyQt6 ou com `PYRETRO_TV_CHROME=1`;
  `core/play.py` traz de volta a janela nativa ou a do Chrome após o jogo. Android inalterado.
- Pendente: confirmar o controle (Gamepad API) e o Steam Link com a janela nativa antes de retirar o
  override `/run/udev` do Chrome e a web `/`. Requer `python-pyqt6-webengine` (setup).
- **Correção:** logo e ícones do `/tv` e da web davam 404 desde a identidade visual (28/10): a rota só servia
  `static/<arquivo>`, sem `static/brand/`. Rota ampliada (PNG/ICO com tipo correto); 51/51 imagens do `/tv` carregam.
- **Apps na TV (`core/tv_apps.py`):** Steam em Big Picture por URL, Heroic em `--console --fullscreen`, PCSX2 e DuckStation
  em `-bigpicture -fullscreen`, PPSSPP `--fullscreen`, RetroArch `-f`; todos conferidos em tela cheia pelo KWin.
- **Janela nativa:** instância única (a segunda chamada traz a janela). Orientação ao setup para abandonar o Plasma
  Bigscreen e abrir o PyRetro pelo Guide do Xbox e pelo botão PS do WGP16 Nova II: `docs/setup-pyretro-unico.md`.
- **G8 no modo TV:** o navegador entrega o Galileo G8 sem mapeamento "standard" (15 botões, 8 eixos): cruz nos eixos 6/7,
  Start = botão 11, X/Y = 3/4, LB/RB = 6/7, LT/RT = 8/9, Back = 10. `tv.js` ganhou `RAW_PAD`, que traduz para os
  índices padrão só nesse caso (controles com mapeamento padrão não mudam). Medido com sonda no QtWebEngine.
  O app Android não é afetado: usa `KeyEvent`/`AXIS_HAT_*` do sistema, já normalizados.
- **Foco do emulador:** o jogo aberto pelo PyRetro (tela cheia) surgia atrás dele e exigia Alt-Tab. `tools/raise-new-window.sh`
  (KWin) ativa a próxima janela de emulador; `core/play.py` o chama antes de abrir o jogo (40 s). A classe só chega depois
  de a janela existir no Wayland, por isso escuta `windowClassChanged`. Conferido com o Azahar: ativa passa de pyretro-tv a Azahar.
- **3DS (Azahar):** layout e troca de tela passaram de Back+L3/R3 para LT/RT sozinhos (hotkey por eixo do gatilho);
  ZL/ZR do New 3DS foram para L3/R3. `configure_xbox.py` atualizado com teste; **ainda não aplicado** (Azahar aberto) nem
  validado fisicamente. Celular não alterado.
- **Atalhos de tela no celular (conferido por adb, nada alterado):** DS (RetroArch/melonDS) já usa `melonds_swapscreen_mode =
  "Toggle"` como no PC. Lime3DS 2123.3 tem atalhos próprios (trocar tela, alternar layouts, turbo, quick load, pausar, fechar),
  mas as atribuições ficam nas preferências privadas do app (`/data/data`, app não depurável): não dá para gravar por arquivo/adb;
  configurar em Controles › Atalhos no próprio app. O `config.ini` em `/sdcard/Jogos/3DS/config/` é só modelo, sem os botões.
  Atalhos de tela no PC (LT/RT no Azahar) foram validados pelo Victor em 29/10.
- **Assistente de primeiros passos (`core/firstrun.py`, `/api/setup/status|apply`, 🚀 nas Ferramentas do modo TV):** confere
  configuração, pastas do acervo (`~/Games/PyRetro`), nuvem (rclone) e emuladores. Cria só `config.toml` (a partir do modelo +
  `[storage]`, modo 600, nunca sobrescreve) e pastas vazias; não instala programas: o que faltar é listado e fica com o
  `setup-linux-bonesi`. Numa instalação sem `config.toml` o `/tv` abre os Primeiros passos sozinho; o servidor deixou de
  encerrar com `sys.exit` quando falta a configuração. 7 testes novos (466 no total). Login do Drive continua manual (`rclone config`).
- **Metadados da Biblioteca (30/10):** desenvolvedora e lançamento preenchidos só em campos vazios, pelo servidor
  (`/api/library/edit`), com ScreenScraper (211 jogos de ROM/Switch, 40 gravados) e pesquisa na web (Google) com fonte
  confirmada. De 2.796 jogos visíveis: sem desenvolvedora 339 → 107; sem lançamento 319 → 165. Datas só com o ano não foram
  gravadas (o editor exige data completa). Capas: 239 dos 245 registros com `capa` vazio já têm imagem na pasta do sistema;
  só 6 não têm em lugar nenhum. Critério de data: Switch/modernos pela plataforma, retrô pelo primeiro lançamento conhecido.
- **Metadados (30/10, 2ª rodada):** mais ~47 jogos preenchidos pela web e 27 homebrews/hacks/traduções sem data com `1970-01-01` (valor genérico pedido pelo Victor). Datas só com o ano e conflitos entre fontes continuam vazios.
- **Metadados (30/10, 3ª rodada):** mais ~51 jogos preenchidos pela web (quatro agentes), datas só com o ano gravadas como
  `aaaa-01-01` e homebrew/hack sem data como `1970-01-01`, ambos por decisão do Victor. De 2.796 visíveis, restam 44 sem
  desenvolvedora e 47 sem lançamento: jogos ainda não lançados/cancelados, datas da Epic/GOG não confirmadas, hacks sem fonte.
- **Android 0.24.0 (code 35, 31/10):** Buscar e Filtro foram para o cabeçalho, ao lado de Situação e Opções; aba ativa
  centralizada na barra de abas; cartões compactos horizontais em paisagem (capa à esquerda, sem repetir o nome do sistema);
  nova visão **Sistemas** (uma ficha por plataforma, toca e abre o Catálogo filtrado); Stream em três colunas em paisagem;
  capas com nova tentativa se a rede falhar; textos de Favoritos/Fixados explicam a diferença. Direcional/analógico agora anda
  na grade em ordem (esquerda/direita quebram de linha, no fim da página vai para a próxima, não sobe às abas); RB/LB no fim
  da lista focam o último/primeiro cartão. Sobras sem sistema e sem arquivo deixam de aparecer como jogo. Modo TV (`tv.js`):
  mesma navegação linear na grade. Não testado no aparelho. 469 Python, 58 JS, JVM e lint passaram.
- **Android 0.24.1 (code 36, 31/10):** aba Fixados removida da barra (a proteção contra remoção continua nos detalhes do jogo e no gerenciador de espaço);
  LB/RB andam uma linha por vez (só no fim da página trocam de página); arquivos de índice com nome de uma letra (sobra "A") não viram jogo.
- **Android 0.24.2 (code 37, 31/10):** Sortear/Estatísticas continuam visíveis em Stream; cache local de capas guarda a biblioteca inteira
  (até 4000, reduzidas a 640 px em WebP, ~100–150 MB; com Wi-Fi o app baixa as capas em segundo plano).
  **Origem do "A":** os testes Python (`test_cloud_snapshots`) gravavam um `library.json` temporário com o jogo id `a`/nome `A`, e o gancho do
  `gui/server.py` registrava isso no diário real da nuvem; o celular recebia o jogo. O gancho agora só vale para a Biblioteca real, e os registros
  `a` e `a-steam` foram removidos do diário (op remove).

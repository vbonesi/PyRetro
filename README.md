# PyRetro

CLI de manutenção do meu acervo de RetroArch (PC + Android), pra manter as
duas plataformas o mais parecidas possível sem precisar fazer tudo na mão.

Escopo intencional: o script só mexe em duas coisas — a pasta sincronizada
(`~/Drive/Jogos`, via Insync/Google Drive) e o celular Android via `adb`.
Ele nunca precisa que RetroArch, DuckStation, PCSX2 etc. estejam instalados
na máquina onde ele roda, porque todos esses emuladores já foram configurados
pra ler/escrever direto na pasta sincronizada. Isso é proposital: dá pra
rodar o PyRetro de qualquer computador que tenha acesso à pasta e ao celular,
sem precisar reinstalar nada específico de emulador ali.

## Princípios (não mudar sem revisitar o motivo)

Essas regras existem por causa de incidentes reais durante o desenvolvimento,
não são só estilo:

- **Nunca apaga nada sozinho.** Toda operação é aditiva (copia o que falta,
  atualiza o que mudou). Remoção é sempre uma decisão manual, fora do script.
- **Nunca transfere jogo novo.** O script corrige/organiza o que já existe
  no acervo, não decide baixar ou copiar ROM pra lugar nenhum.
- **Fuzzy match nunca é aplicado sozinho.** Correspondência aproximada de
  nome (capas, principalmente) só entra num relatório pra revisão humana -
  mesmo com corte de similaridade alto (90%+), sequências como "Dragon Quest"
  vs "Dragon Quest II" já geraram capa errada aplicada sem querer.
- **Tudo roda em modo simulação por padrão.** Todo comando só escreve/copia
  de verdade com `--apply` explícito.
- **`.cue` sem `.bin` não é lixo.** É uma ROM que ainda vai ser baixada sob
  demanda (o acervo de PS1 é maior que o espaço que vale a pena manter
  local o tempo todo). Nunca deletar `.cue` órfão.
- **Capa sem ROM correspondente não é lixo.** O acervo de capas é
  intencionalmente maior que o de ROMs, pelo mesmo motivo acima.

## Testes

```bash
python3 -m unittest discover -s tests -v
```

Sem dependência externa (`unittest` da stdlib), igual ao resto do
projeto. Cobrem as regras que **quebram em silêncio** - as que não
levantam erro, só corrompem o acervo devagar e só aparecem dias depois
olhando a tela:

- **Identidade de jogo** (`tests/test_library.py`): cruzar ROM com
  Biblioteca exige nome E plataforma compatíveis; merge por nome exato
  nunca mescla "Pikmin 2" com "Pikmin"; renomear preserva o vínculo com
  a loja de origem, sem deixar o nome novo virar apelido (o que faria um
  jogo homônimo de verdade cair no registro errado); validação de nota/
  data/campo obrigatório; gravação atômica do `library.json`.
- **Servidor** (`tests/test_server.py`): nome de arquivo vindo da
  requisição não pode escapar da pasta de capas (nem por `../`, nem por
  caminho absoluto, nem por symlink), sem barrar nome de jogo legítimo
  ("Tony Hawk's Pro Skater", "Final Fantasy VI (USA)"); versão da capa
  na URL muda quando o arquivo muda.

Cada teste cita o problema real que o originou.

## Requisitos

- Python 3.11+ (usa `tomllib` da stdlib, sem dependência externa)
- `adb` no PATH, com o celular autorizado (`adb devices` deve listar o
  aparelho como `device`, não `unauthorized`/`offline`) - só necessário
  pros comandos que falam com o celular (`sync`, `heavy-roms --send`)
- `curl` no PATH (usado pro download de capas)
- `rclone` no PATH, com um remote `drive` configurado
  (`sudo apt install rclone` + `rclone config` - ver
  [`docs/roadmap.md`](docs/roadmap.md)) - só necessário pra ver/baixar
  ROMs pesadas direto do Google Drive sem precisar do celular
  conectado
- `ps1vmc-tool`/`ps2vmc-tool` no PATH (baixe o release "ubuntu" em
  https://github.com/bucanero/ps2vmc-tool/releases e coloque em
  `~/.local/bin`) - só necessário pra aba "💾 Saves" (editor de memory
  card PS1/PS2)

Sem `pip install` nenhum - tudo é stdlib de propósito, pra rodar em qualquer
máquina sem setup de ambiente virtual.

## Setup

```bash
cp config.example.toml config.toml
```

Edite `config.toml`: a seção `[pc]` tem os caminhos da pasta sincronizada
(`roms_root`, `capas_root`, `saves_root`...), a `[android]` os caminhos
equivalentes no celular. As seções `[systems.*]` mapeiam cada pasta de
sistema pro repositório de capas certo em `github.com/libretro-thumbnails/`
- normalmente não precisa mexer nelas.

`config.toml` está no `.gitignore` (é específico da sua máquina/celular).

## Comandos

### `fetch-covers` — busca capas no libretro-thumbnails

```bash
python3 retrosync.py fetch-covers PS              # simula, mostra o que faria
python3 retrosync.py fetch-covers PS --apply       # baixa de verdade
python3 retrosync.py fetch-covers all --apply      # todos os sistemas do config.toml
```

Casamento de nome em duas etapas: exato (normalizando tags de região/rev/beta)
e, se não achar, aproximado - mas aproximado só entra no relatório final,
nunca é baixado sozinho. Pra sistemas como Arcade, onde o nome do arquivo é
um código curto de ROM (`dariusg`, `karnovr`...), o script primeiro resolve
o nome de verdade via o `.dat` oficial do FBNeo antes de tentar casar contra
o repositório de capas - resolve a maioria dos casos que fuzzy match sozinho
erraria. Esse mesmo `.dat` também alimenta a exibição na GUI: a galeria mostra
o nome completo do jogo em vez do código curto (`core/covers.py`
`arcade_display_name`) - só cosmético, renomear/apagar continuam operando no
nome curto de verdade.

### `fetch-covers-cloud` — busca capas a partir do catálogo completo no Drive

```bash
python3 retrosync.py fetch-covers-cloud SS              # simula
python3 retrosync.py fetch-covers-cloud SS --apply       # baixa de verdade
python3 retrosync.py fetch-covers-cloud all --apply      # todos os sistemas (exceto COVERS_EXCLUDED)
```

Mesmo casamento exato/fuzzy do `fetch-covers` acima, mas a lista de jogos
vem do catálogo completo no Google Drive (via `rclone`,
`core/heavy_roms.list_drive_items`) em vez de escanear `roms_root` local -
pra sistema onde a nuvem tem muito mais jogo do que o que já foi baixado
pro PC. `fetch-covers` sozinho não serve pra isso porque só REVISA capas
que já existem em `capas_root` - nunca descobre um sistema novo do zero
(achado em 24/08 com Saturn/Dreamcast: as pastas de capas nem existiam
ainda). Não baixa ROM nenhuma, só a capa - mesmo princípio de "capa sem
ROM correspondente não é lixo" (ver Princípios acima), estendido pro lado
cloud-only. Sistema que dá `no_match` nas duas fontes (aqui +
`fetch-covers-fallback`) fica listado sem capa mesmo - revisão manual
depois, igual todo `no_match` do projeto.

Achado no mesmo dia: o `cache/covers_registry.json` já tinha 62 entradas
de Saturn marcadas `replaced_exact` de antes do sistema entrar em
`COVERS_EXCLUDED`, mas a pasta de capas nem existia mais no disco -
`process_system_cloud` (`core/covers.py`) só confia num cache
"replaced_exact"/"replaced_fuzzy" se o `.png` ainda existir de verdade;
`no_match` continua confiável sempre.

Também funciona pra **sistema pesado** (PS2/GameCube/Wii/PSP/3DS -
PS1 fica de fora, `COVERS_EXCLUDED`), desde que o código seja passado
explícito (`"all"` continua só leve, de propósito - `list_drive_items`
pode levar ~90s por sistema pesado, não vale rodar à toa em todo "all"):

```bash
python3 retrosync.py fetch-covers-cloud PS2 --apply
```

Capa de pesado é só pra **exibição** (Biblioteca/galeria) - não afeta
`heavy-roms --send`/`--download`, que continua sob demanda igual
sempre foi.

### `fetch-covers-fallback` — segunda fonte pros que sobraram (LaunchBox Games DB)

```bash
python3 retrosync.py fetch-covers-fallback SFC              # simula
python3 retrosync.py fetch-covers-fallback all --apply       # baixa de verdade
```

Só olha os itens que o `fetch-covers` já marcou como `sem_match` no
registro - não reprocessa tudo. Usa o [LaunchBox Games
Database](https://gamesdb.launchbox-app.com/) (não precisa de conta/API
key - baixa o `Metadata.zip` público deles, ~500MB descompactado, faz um
índice filtrado e cacheia em `cache/launchbox_index.json`; só reprocessa o
XML de novo com `--rebuild-index`). Tem cobertura melhor pra hack/tradução
de fã que o libretro-thumbnails não cataloga.

Casamento exato primeiro; se não achar, tenta por PREFIXO de palavras (o
arquivo local geralmente não tem o subtítulo que o LaunchBox guarda por
extenso, ex: local "Zool" vs LaunchBox "Zool: Ninja of the 'Nth'
Dimension") - com trava de segurança pra não deixar "Contra" casar com
"Contra III" (a palavra logo após o prefixo não pode ser um número/numeral
romano sozinho).

### `convert-covers` — converte capas `.jpg` pra `.png`

```bash
python3 retrosync.py convert-covers all --apply
```

**RetroArch só exibe thumbnail em `.png`** (confirmado em 01/08/2026) -
um `.jpg` na pasta `Named_Boxarts` fica invisível no menu mesmo com o
nome certo. Usa o `convert` do ImageMagick (dependência externa aceita,
igual o `curl`). Também corrigido na fonte: `fetch-covers-fallback` e a
busca manual da GUI agora convertem automaticamente se o arquivo de
origem (LaunchBox) vier em `.jpg`, então isso não deveria voltar a
acontecer sozinho - esse comando é só pra limpar o que já existia.

### `validate-covers` — confere se os `.png` são PNG de verdade

```bash
python3 retrosync.py validate-covers all --apply
```

Achado em 02/08/2026: 5 capas reais da coleção tinham **bytes JPEG
salvos com nome `.png`** (vieram de curadoria manual antiga, ou de
algum ponto que confiava na extensão declarada em vez do conteúdo real
- ver correção em `download_cover`/`download_selected_cover`/upload da
GUI, que agora sempre passam pelo `convert`, não importa a extensão).
O RetroArch não mostra erro nenhum nesse caso - só fica com o ícone
genérico de "sem capa" pra sempre, mesmo com o arquivo no lugar certo e
o nome batendo. Esse comando lê os primeiros bytes de cada `.png` (não
a extensão) e corrige no lugar via `convert` se o conteúdo real for
outra coisa. Vale rodar de vez em quando, principalmente depois de
subir capa manualmente pela GUI.

### `sanitize-names` — remove caracteres que o RetroArch não aceita

```bash
python3 retrosync.py sanitize-names all --apply
```

RetroArch não aceita `&`, `:`, `*` (nem `/`, mas isso não apareceria
literalmente num nome de arquivo) - troca `&`→`and`, `:`→`-`, `*`→
(removido). Roda em capas **e** ROMs juntos (senão o nome para de
bater entre os dois lados). Nunca sobrescreve um arquivo que já existe
com o nome novo (marca como conflito e não mexe).

### `sync` — sincroniza capas PC ↔ Android

```bash
python3 retrosync.py sync covers          # simulação
python3 retrosync.py sync covers --apply  # copia de verdade
```

Só `covers` está implementado (saves/states/métricas ficam pra depois,
mesma arquitetura). Compara o mtime de cada capa dos dois lados (via
`adb shell find`) contra o manifesto do último sync
(`cache/sync_state.json`) e decide: sem mudança, copiar pra PC, copiar
pro Android, ou **conflito** (mudou dos dois lados desde a última sync -
nunca decide sozinho, lista pra revisão manual). Nunca deleta. Requer
`adb devices -l` mostrando o celular como `device` (não `offline`/
`unauthorized`); se houver mais de um device, preencha `device_serial`
em `config.toml` `[android]`.

**Testado contra o aparelho real** (S24 Ultra) em 01/08. Achado no
teste: o USB reconectou sozinho no meio da sincronização (comum,
segundo o próprio `adb.py`) e o `adb` passou a devolver "device not
found" em vez de "device offline" - frase que o retry não reconhecia.
Corrigido. Depois do fix, sync completo funcionou ponta a ponta. Numa
primeira sincronização (sem manifesto anterior) espere vários
"conflitos" só porque não há baseline pra saber quem mudou primeiro -
isso é esperado, não é bug.

### `fix-cues` — corrige referências `.cue` → `.bin`

**Ainda não implementado como comando de CLI** (o scan/auditoria de
todos os `.cue` da coleção, `parse_cue`/`scan_folder`/`fix_all`,
continua no esqueleto). O que já existe e está testado é
`core/cues.py` `rename_disc_set()` - renomeia um `.cue`/`.gdi` + os
`.bin` sidecars (inclusive multi-track) e corrige a referência `FILE
"..."` dentro do texto, usado pelo rename com cascata (ver GUI abaixo).
Nunca mexe em `.ccd`/`.img` (formato diferente, sem referência de texto
pra corrigir) nem em `.chd` (arquivo único).

### `heavy-roms` — lista/envia ROMs de consoles pesados

```bash
python3 retrosync.py heavy-roms PS2                              # lista (PC + Drive)
python3 retrosync.py heavy-roms PS2 --send "Gradius V.iso"       # envia pro celular
python3 retrosync.py heavy-roms PS2 --download "Baroque.iso"     # baixa do Drive pro PC
```

Sistemas configurados em `config.toml` `[heavy_systems]` (PS,
PS2, GameCube, Wii, PSP, 3DS - Switch fica de fora de propósito, gestão
feita por fora do PyRetro). Diferente dos sistemas em `[systems]`
(sincronizados sozinhos via Google Drive), esses ficam só no PC até
serem enviados/baixados sob demanda - `retrosync heavy-roms <CODIGO>`
mostra o que existe em `roms_root/<CODIGO>/`, no Google Drive (via
`rclone`, config `[rclone]`) e no celular (via adb, se conectado). Um
"item" é um arquivo ou uma pasta inteira; PS soma o tamanho dos
`.bin` sidecars automaticamente. Nunca sobrescreve no celular sem
`--overwrite`. Download do Drive vai primeiro pra `staging_dir`
(`~/Downloads` por padrão) e só depois é movido pra
`roms_root/<CODIGO>/` - nunca escreve direto na pasta sincronizada pelo
Google Drive Desktop.

### `heavy-catalog` — cacheia o catálogo de pesados pro `sortear`

```bash
python3 retrosync.py heavy-catalog --apply
```

Consulta o Google Drive (via `rclone`) pra cada sistema de
`[heavy_systems]` e salva a lista completa (nome, tamanho, se é pasta)
em `cache/heavy_catalog.json`. Existe porque listar isso ao vivo pode
levar até ~90s por sistema (ver `heavy-roms` acima) - inviável fazer
isso toda vez que o `sortear` roda, ainda mais sorteando "de tudo" (6
sistemas pesados = minutos de espera). Rode de novo depois que a nuvem
mudar (jogo novo baixado no Drive) pra manter o catálogo em dia; sem
rodar nunca, `sortear` funciona só com sistemas leves.

A aba "ROMs Pesadas" da GUI (ver abaixo) lê o mesmo arquivo em vez de
consultar o Drive ao vivo a cada troca de aba - sem cache ainda pra um
sistema, ela cai pra consulta ao vivo uma vez e já popula o cache
sozinha pra próxima. Rodar `heavy-catalog --apply` (CLI) ou o botão
"🔄 Atualizar catálogo" (GUI, dentro da própria aba) faz a mesma coisa.

### `sortear` — sorteia um jogo aleatório da coleção

```bash
python3 retrosync.py sortear        # de tudo (leve local + pesado cacheado)
python3 retrosync.py sortear SFC    # só Super Nintendo
python3 retrosync.py sortear PS2    # só PlayStation 2 (a partir do catálogo)
```

Junta sistemas leves (lidos ao vivo de `roms_root/<CODE>/`) e pesados
(lidos do cache gerado por `heavy-catalog`) num pool só, cada JOGO com
peso igual - um sistema com mais jogos tem mais chance de propósito
(reflete o tamanho real da coleção). Se o sorteado for de um sistema
pesado que ainda não está no PC, avisa e sugere o `heavy-roms
<CODIGO> --download` certo pra baixar antes de jogar.

### `library-import-sheet` / `library-refresh` — biblioteca de jogos "de fora"

```bash
python3 retrosync.py library-import-sheet "Games do Bonis.csv" --apply   # planilha -> library.json
python3 retrosync.py library-refresh heroic --apply                      # cruza com Epic/GOG/Amazon
python3 retrosync.py library-refresh steam --apply                       # cruza com a Steam
python3 retrosync.py library-refresh switch --apply                      # cruza com roms_root/NSW/
python3 retrosync.py library-refresh psn --apply                         # cruza com a PSN
python3 retrosync.py library-refresh xbox --apply                        # cruza com a Xbox
```

Registro dos jogos que não são ROM - possuídos em lojas digitais
(Steam, PSN, Xbox e, via Heroic, GOG/Epic/Amazon) e o acompanhamento pessoal
(iniciado/finalizado/platinado/nota/tempo/observações) que antes vivia
numa planilha do Google Sheets. Fica em `library_root/library.json`
(`~/Drive/Jogos/Biblioteca/`, mesma pasta que o Google Drive Desktop já
sincroniza pra ROMs/Capas/Saves) - o celular só **lê** esse arquivo,
nunca gera sozinho (ver `core/library.py`).

`library-import-sheet` faz upsert por nome+plataforma a partir do CSV
exportado da planilha (Arquivo > Fazer download > CSV) - roda de novo
com um export mais recente sem duplicar. `library-refresh <fonte>` lê
os jogos possuídos e cruza pelo nome: bateu exato, só anota a fonte no
jogo que já existe; não bateu, vira registro novo (possuído, ainda sem
acompanhamento). Possíveis duplicatas por nome parecido entram só num
relatório - nunca são mescladas sozinhas, mesmo cuidado que o
`fetch-covers` já tem com fuzzy match de capa. Fontes de jogo possuído hoje:

- **`heroic`** - lê os 3 caches que o Heroic Games Launcher já mantém
  sozinho (`store_cache/{legendary,gog,nile}_library.json` -
  Epic/GOG/Amazon), zero login feito pelo PyRetro, zero rede. Caminho
  configurável em `[heroic] config_dir` no `config.toml`.
- **`steam`** - API Web oficial (`IPlayerService/GetOwnedGames`), via
  `[steam] api_key`/`steamid64` no `config.toml` (chave grátis em
  steamcommunity.com/dev/apikey). Só funciona com "Detalhes do jogo"
  público no perfil Steam - senão a API devolve biblioteca vazia sem
  erro nenhum.
- **`switch`** (27/08) - lê `roms_root/NSW/` (cada jogo é uma pasta,
  ex: `Nine Sols [NSZ]`), removendo qualquer tag entre colchetes do
  nome (formato do dump, não é parte do nome do jogo). Sem gestão de
  arquivo (send/download/rename/apagar não fazem sentido pra Switch -
  não roda via RetroArch) - só confirma posse e cruza pelo nome com o
  que a planilha já tem (nota/comentário preservados). Jogo que faz
  parte de uma coletânea sem nome exato igual ao da planilha não é
  forçado a casar - vira possível duplicata (relatório) ou registro
  novo separado, nunca mesclado às cegas.
- **`psn`/`xbox`** - implementados em `core/library.py`
  (`read_psn_library`, `read_psn_trophy_titles`, `read_xbox_library`) e
  funcionais, mas **não usados via `library-refresh`** por decisão do
  usuário (27/08) - PSN via API é impreciso (troféu mistura
  físico+digital) e Xbox não tem como separar Game Pass de comprado com
  confiança (ver `docs/changelog.md`). Essas duas entram por
  **`library-add`** (cadastro manual) em vez disso.

### `library-add` — cadastro manual (PSN/Xbox e qualquer lista avulsa)

```bash
python3 retrosync.py library-add jogos.txt --plataforma "Xbox" --fonte "xbox" --apply
```

Arquivo texto, um nome de jogo por linha (linha vazia ou `#` é
ignorada) - mesmo merge seguro de `library-refresh` (nome exato entra
como fonte a mais; parecido demais só é reportado). Existe porque PSN e
Xbox não têm fonte automatizada confiável (ver acima) - o usuário
levanta a lista real (ex: olhando a própria conta) e cadastra assim, e
repete conforme for comprando jogo novo.

### `library-fetch-covers` — capa dos jogos digitais (SteamGridDB)

```bash
python3 retrosync.py library-fetch-covers --apply
```

Busca capa (grid 600x900, estilo "alternate" - mesmo formato retrato
que Steam/Heroic usam) via [SteamGridDB](https://www.steamgriddb.com)
pra todo jogo da Biblioteca que ainda não tem `capa` - chave grátis em
`[steamgriddb] api_key` no `config.toml` (steamgriddb.com > Preferences
> API). Match exato só (nome normalizado igual ao 1º resultado da
busca) - sem match não trava nem é listado (potencialmente centenas),
só entra num contador. Salva em `library_root/capas/<id>.png` e grava
o caminho relativo em `capa`; salva o `library.json` a cada 20 jogos
processados (não só no final) - um lote de centenas demora minutos (2
chamadas de rede por jogo), sem isso um erro no meio perderia a
marcação de tudo já baixado até ali.

### `organize` — lista ROMs esperando organização

```bash
python3 retrosync.py organize
```

O "upload" de ROM nova virou a própria pasta `roms_root/0-Organizar/`
(nome configurável em `config.toml` `[pc]` `organizar_dir`, editável
direto na tela de Configurações da GUI): joga o arquivo ali (via Google
Drive, ou direto no PC) e o PyRetro identifica o sistema pela extensão.
Esse comando só **lista** o que está esperando e os sistemas candidatos
- mover é feito pela GUI (`🗂 Organizar`), porque muitas extensões são
ambíguas entre sistemas (`.iso`, `.cue`, `.chd`...) e decidir isso
direito pede uma tela com escolha manual, não um comando de linha.

### `rebuild-playlist` — monta playlist `.lpl` do RetroArch

```bash
python3 retrosync.py rebuild-playlist SS              # simula PC + Android
python3 retrosync.py rebuild-playlist SS pc --apply    # so PC
python3 retrosync.py rebuild-playlist SS android --apply # so Android
```

Lê o que existe DE VERDADE em `roms_root/<CODE>/` (PC) e/ou no celular
(via `adb find`) e monta a playlist a partir disso - não depende de
abrir o RetroArch e rodar o scan manual pela UI. Usa `[systems.<CODE>]`
do `config.toml` pro nome de exibição (`db_name`) e as extensões
reconhecidas. Cada item usa `core_path`/`core_name` `"DETECT"` (mesmo
padrão de toda playlist de sistema em disco gerada pelo próprio
RetroArch) - o núcleo certo é resolvido sozinho assim que estiver
instalado, não precisa reescrever a playlist depois de baixar o core.

Sistemas pesados (`PS2`, `GameCube`...) não sincronizam PC↔Android
sozinhos - achado em 24/08, quando Saturn e Dreamcast ainda eram
`heavy_systems` (voltaram a ser sistema leve normal logo em seguida, a
pedido do usuário - ver `docs/changelog.md`): o PC tinha "Daytona USA"
+ "Rabbit" de Saturn, o celular tinha "NiGHTS into Dreams" + "Virtua
Fighter 2" + "Virtua Racing", nenhum jogo em comum. A playlist de cada
lado reflete só o que aquele lado tem local - normal em qualquer
sistema pesado, não é bug. Rode de novo depois de mandar/tirar jogo de
um lado (`heavy-roms --send`) pra manter a playlist em dia.

### `backup-config` — snapshot datado das configs do RetroArch

```bash
python3 retrosync.py backup-config              # simula PC + Android
python3 retrosync.py backup-config pc --apply    # so PC
python3 retrosync.py backup-config --apply       # os dois
```

Copia `retroarch.cfg` + `config/` (shaders/opções/remaps por core) +
`playlists/` (incluindo `builtin/` e `logs/`) pro PC e/ou celular (via
`adb pull`) pra dentro de `Backups/retroarch_<pc|android>_<data>/` -
mesma pasta/convenção que já vinha sendo feita na mão. Cada rodada cria
uma pasta **nova** com a data de hoje, nunca sobrescreve um snapshot
anterior. Não inclui `cores/` (redownloadável, ver `docs/roadmap.md`)
nem saves/states/thumbnails (já têm sync próprio - `core/pc_backup.py`,
`core/sync.py`). No Android, `retroarch.cfg` mora numa pasta privada do
app diferente de `config/`/`playlists/` (que ficam em
`/storage/emulated/0/RetroArch/`, pública) - só é acessível via `adb`
porque o arquivo em si é `0666` (confirmado com `adb shell stat` em
24/08).

### Navegação unificada: leve + pesado + Biblioteca na mesma fila de abas

`#system-tabs` lista os três juntos (`GET /api/systems` + `GET
/api/heavy/systems` + uma aba fixa "📚 Biblioteca") - ROMs Pesadas e
Biblioteca eram popup até 27/08, viraram aba com a mesma grade de capa
da galeria normal a pedido do usuário ("deixando a visualização igual
das ROMs normais"). `currentKind` ("leve"/"pesado"/"biblioteca") decide
qual barra de controle aparece acima da grade - capas (leve),
🔄 Atualizar catálogo (pesado), busca/filtro/+Lista (Biblioteca, ver
abaixo) - só uma por vez, nunca as três juntas.

Card por tipo, todos com a mesma classe `.cover` (grade igual, ações
diferentes):
- **leve**: ✎ Editar, ⚑ Marcar, 🗑 Apagar.
- **pesado**: Enviar/Baixar (conforme já está no PC ou só no Drive),
  Renomear, Apagar, 🖼 Capa (upload manual) - reaproveita os mesmos
  endpoints/funções que o antigo modal "ROMs Pesadas" já usava.
- **Biblioteca**: 🖼 Capa (upload manual) + nota/tempo/checkboxes
  (iniciado/finalizado/platinado) direto no card.

Tracking universal (27/08): leve e pesado ganharam a mesma fileira de
iniciado/finalizado/platinado/nota que a Biblioteca já tinha (sem
"tempo" - só esse campo continua exclusivo do card completo da
Biblioteca). Grava via `POST /api/library/track`
(nome/**code**/plataforma/fonte/campo/valor, ver `core/library.
get_or_create_for_rom`) em vez de `/api/library/update` - acha o jogo
certo na Biblioteca e, sem bater, CRIA o registro sozinho na primeira
edição (`plataforma` = nome amigável do sistema, `fonte =
"rom:<CODIGO>"`) - nenhuma ROM precisa estar pré-cadastrada pra ganhar
acompanhamento. Card de ROM também mostra o que já existe
(`GET /api/covers/<code>` e `GET /api/heavy/roms/<code>`).

**Nome sozinho nunca é suficiente pra decidir "é o mesmo jogo"** -
achado em produção no mesmo dia (27/08): o usuário tem "Celeste" na
Steam, no Xbox e também um `Celeste.gba` (ROM-hack/demake, jogo
diferente de verdade) - cruzar só por nome misturava os três. Corrigido
com `core/library.PLATAFORMA_ROM_CODES`: mapeia o texto de `plataforma`
(livre, vindo da planilha ou de loja) pro código de sistema ROM
equivalente, só pros textos que realmente significam aquele console
("PlayStation 2"/"SNES"/"Arcade"/"Game Boy Advanced" etc. → PS2/SFC/
ARCADE/GBA); texto de loja ("Steam"/"Xbox One"/"GOG"/...) não mapeia
pra nada, então nunca cruza com ROM nenhuma. Todo cruzamento ROM↔
Biblioteca (tracking no card, exclusão da Biblioteca abaixo, find-or-
create do `/api/library/track`) agora exige nome **e** plataforma
batendo (`core/library.find_for_rom`/`is_rom_backed` em
`gui/server.py`) - texto de plataforma não mapeado nunca cruza às
cegas, o oposto do fuzzy match (aqui errar por "não uniu" é o lado
seguro).

Cover upload (leve já tinha, 27/08 estendeu pra pesado e Biblioteca):
`_cover_path` (`gui/server.py`) passou a resolver sistema pesado além
de leve, então `/api/cover/upload` funciona pros dois sem endpoint
novo. Biblioteca usa pasta própria (`library_root/capas/`, fora de
`capas_root`) - ganhou `POST /api/library/cover_upload` dedicado.
Filtro "🖼 Só sem capa" (mesmo padrão da galeria leve) também chegou em
`#heavy-controls` e `#library-controls`.

### Busca unificada (barra do topo)

Uma barra só (`#global-search-input`) busca nos três tipos de uma vez -
`GET /api/search_library` (substring, acento/case-insensitive) cobre
ROM leve (sempre), e desde 27/08 também ROM pesada (catálogo cacheado)
e Biblioteca (excluindo quem já é ROM de verdade - nome e plataforma
batendo, ver "Aba Biblioteca" abaixo - evita resultado duplicado do
mesmo jogo), quando o `<select>` de sistema ao lado está
em "Todos" (selecionar um sistema leve específico restringe a busca só
a ele, como antes). Cada resultado vem com `kind`
(`leve`/`pesado`/`biblioteca`); clicar navega pra aba certa
(`selectSystem`/`selectHeavyTab`/`selectLibraryTab`) e destaca o card.
Substituiu o campo de busca que a Biblioteca tinha só pra si
(`#library-search`, removido) - agora é a única busca por nome do app.

### Aba "📚 Biblioteca"

Visualização (status iniciado/finalizado/platinado, nota) + edição
inline de nota/tempo/iniciado/finalizado/platinado/observações direto
no card. `GET /api/library` só lê `library_root/library.json`; `POST
/api/library/update` grava um campo por vez (só os 6 editáveis,
`core/library.EDITABLE_FIELDS` - nome/plataforma/fontes continuam só
via CLI, pra não arriscar quebrar o `id`). Cadastro de jogo novo (nome/
fonte) tem botão também (ver "Ações de fundo" abaixo) -
`library-import-sheet` segue só CLI (migração pontual, não é ação do
dia a dia). Diferente das fontes automatizadas (Heroic/Steam,
PC-only), a edição inline é só leitura+escrita de arquivo local -
funciona igual em modo Android (Termux). `observacoes` (comentário
livre) já vinha da planilha importada mas não tinha campo na tela
(27/08) - textarea no card corrige isso.

Ações de importação (Heroic/Steam/Switch/Capas/+Lista) ficam dentro de
um `<details>` retrátil, fechado por padrão (27/08, pedido do usuário
de economizar espaço de tela - ver também o fix de `.hidden` em
"Estrutura do projeto"/changelog: as barras de controle de leve/pesado
ficavam vazando pra qualquer aba antes disso). Badge de plataforma/
fonte só aparece quando diz algo que a linha de `plataforma` já não diz
- jogo sem fonte de loja (badge = a própria plataforma) ou com fonte
cujo rótulo é idêntico à plataforma gravada não duplica mais o texto.

Jogo cujo nome **e** plataforma batem com uma ROM de verdade (leve ou
pesada) não aparece aqui (27/08) - o dado passa a "morar" na aba da ROM
correspondente em vez de duplicar a visualização (ver "Tracking
universal" acima, inclusive o porquê de exigir plataforma também, não
só nome). `GET /api/library` calcula isso a cada chamada
(`rom_normalized_names_by_code` + `is_rom_backed` em `gui/server.py`) -
nunca apaga o registro, só filtra essa UMA listagem. Um jogo com o
mesmo nome mas plataforma de loja (Steam/Xbox/GOG/...) continua
aparecendo normalmente, mesmo que exista uma ROM com esse nome em
algum sistema - só sistemas com que a `plataforma` gravada
literalmente corresponde entram na exclusão.

Sub-abas por plataforma/loja (27/08, `#library-group-tabs`) substituem
o antigo `<select>` de fonte - mesmo agrupamento de sempre
(`libraryGroupsFor`: fonte de loja quando existe, senão a própria
`plataforma`), só que virou navegação em vez de dropdown. Rótulo de
fonte é amigável (`FONTE_LABELS` em `gui/static/app.js`: psn -> "PSN
(digital)", heroic:epic -> "Epic Games", etc - só exibição, não muda o
dado gravado) - jogo sem fonte de loja (veio só da planilha) usa a
própria `plataforma` como agrupamento em vez de um "(sem fonte)"
genérico, então uma aba "Arcade" ou "Xbox One" aparece do mesmo jeito
que "Steam". `libraryTabGroupsFor` (27/08) aplica uma curadoria por
cima disso só pra navegação - iOS+Android viram uma aba "Mobile", e
Xbox/Xbox 360/Xbox One/Xbox Series S viram uma aba "Xbox" só
(`GROUP_TAB_ALIASES`) - o modelo específico continua na linha de
plataforma do card, só a lista de abas fica mais enxuta.

Nota tem cor (27/08): `notaColor()` interpola entre as cores de tema
`--err`/`--ok` proporcionalmente de 1 a 10, e usa `--warn` (dourado)
acima de 10 - aplicado na borda+texto do campo de nota, tanto na
Biblioteca quanto no tracking universal de ROM leve/pesada.

Ranking: o mesmo select de ordenação (nome ou nota) - "por nota" filtra
pra só quem já tem nota (sem nota não é "nota zero", só fica de fora do
ranking) e numera #1, #2... do maior pro menor. Não é uma tela
separada, é um jeito de olhar a mesma grade.

Capas (`library-fetch-covers`, ou busca/upload manual pelo 🖼 do
card), servidas por `GET /library-images/<caminho>` a partir do `capa`
de cada registro (`gui/server.py`, com checagem de path traversal).
Três fontes automáticas, nessa ordem (28/08):
1. **CDN oficial da Steam** - a mesma arte 600x900 que o cliente da
   Steam mostra, sem chave nem login, só com o `appid` que a API já
   devolve (`steam_appid_index`/`find_cover_steam_cdn`). É a de melhor
   qualidade e não depende de curadoria de terceiro, por isso vem
   primeiro.
2. **ScreenScraper** pras plataformas de console que ele cobre
   (`PLATAFORMA_SCREENSCRAPER`) - curadoria melhor que o SteamGridDB, e
   é o que resolve os jogos de Switch.
3. **SteamGridDB** pro resto (Epic/GOG/...). Match exato como sempre,
   mas varrendo TODOS os resultados da busca (não só o 1º) e com uma
   segunda passada `loose` que ignora parênteses - nunca aplica capa de
   outro jogo por aproximação.

O 🖼 de cada card abre um popup com **busca + upload** juntos, pra
capear na mão o que nenhuma fonte resolveu (`/api/cover/search_sgdb` +
`/api/cover/apply_url`) - funciona igual na Biblioteca e nas ROMs
pesadas.

Editar (✎ no card): formulário com TODOS os campos de texto do jogo -
nome, plataforma, gênero, subgênero, desenvolvedora, datas, tempo, meta
e comentário (`POST /api/library/edit`, grava tudo de uma vez ou nada).
`nome`/`plataforma` são editáveis porque o `id` nunca é recalculado -
ele é chave opaca desde a criação. `id` e `fontes` ficam de fora
(`fontes` é posse confirmada por API, muda via `library-refresh`).

Toda URL de capa sai do servidor com `?v=<mtime>` (`com_versao` em
`gui/server.py`) - sem isso, trocar a capa não aparecia na tela: o
arquivo mudava mas a URL não, e o navegador servia a imagem antiga do
cache. Com a versão, arquivo trocado = URL nova = imagem nova na hora,
e arquivo intocado segue cacheado.

Ocultar (👁 no card, campo `oculto`): tira o jogo da listagem sem
apagar nada - pra jogo online/de serviço que está na conta mas não faz
sentido acompanhar. O filtro "👁 Mostrar ocultos" traz eles de volta pra
desfazer; busca de capa, Ranking e Iniciados ignoram o que está oculto.

### Botões "🏅 Ranking" e "▶ Iniciados"

Duas listas que cruzam a coleção INTEIRA de uma vez - ROM leve, pesada
e Biblioteca juntas (`GET /api/ranking`, `GET /api/iniciados`) - o que
só faz sentido porque, desde o tracking universal, `library.json` é a
fonte única de progresso pra qualquer tipo de jogo. Ranking numera do
maior pro menor com a nota colorida; Iniciados lista o que começou e
ainda não terminou. Só leitura - pra editar, o card do jogo na aba
dele. A capa é resolvida pelo servidor nos dois mundos (pasta do
sistema pra ROM, `library_root/capas/` pra Biblioteca).

### Botão "🎲 Sortear" na GUI

Traz o comando `sortear` pra tela - `<select>` de sistema (leve+pesado
juntos, via `GET /api/sortear/systems`) + botão "Sortear!"
(`GET /api/sortear?system=<código>`). Reaproveita `core/sortear.py`
inteiro, sem duplicar a lógica de pool/peso no servidor da GUI. Se o
sorteado for pesado e só existir no Drive, mostra a mesma dica do CLI
("heavy-roms CODIGO --download"). Primeiro item de trazer o resto do
CLI (heavy-roms/organize/saves já tinham GUI; sortear era o que
faltava mais visível). Mostra a capa do sorteado quando existe (mesma
pasta que a galeria usa, incluindo pesado - `/images/<code>/<arquivo>`
aceita os dois desde a unificação acima).

### Manutenção e ações de fundo na GUI

Todo comando do CLI que ainda não tinha tela ganhou uma - decisão do
usuário de cobertura completa em vez de deixar operação administrativa
só no terminal. Mecanismo comum a todos: `_start_job` (`gui/server.py`)
roda a função em thread separada emitindo linha de log
(`{"type":"log","line":...}`) na mesma fila/stream SSE que a busca de
capas já usava (`GET /api/fetch/stream?job=<id>`) - o mesmo texto que a
CLI já imprimia, só que na tela. Front consome via `runJob()`, um
wrapper genérico (evita reimplementar `EventSource` pra cada botão).

- **Biblioteca**: `🔄 Heroic`/`🔄 Steam` (`library-refresh`), `🖼 Capas`
  (`library-fetch-covers`), `+ Lista` (`library-add` - textarea +
  campo plataforma + campo fonte), na barra de controles que aparece
  acima da grade quando a aba está ativa. Um checkbox "aplicar" único
  governa os três - **sem marcar, só mostra o preview em memória, nunca
  escreve** (mesmo princípio "simula por padrão" do resto do projeto;
  psn/xbox não ganharam botão de propósito, ver seção acima).
- **ROMs pesadas**: `🔄 Atualizar catálogo` (`heavy-catalog`), mesmo
  esquema de barra de controles acima da grade.
- **🛠 Manutenção** (modal novo): `backup-config`, `backup-saves`,
  `sanitize-names`, `rebuild-playlist` (com `<select>` de sistema) e
  `emu-sync` (com `<select>` de fonte) - cada um com seu próprio
  checkbox "aplicar" local.

## Interface gráfica (Fase 1)

```bash
python3 gui/server.py              # abre em http://localhost:8000
python3 gui/server.py --port 8080  # outra porta
```

Servidor local, stdlib só (`http.server`), sem dependência nova - mesma
filosofia do resto do projeto. Dá pra acessar do navegador do celular também,
se PC e celular estiverem na mesma rede (usa o IP da máquina em vez de
`localhost`).

O que tem até agora:
- Galeria pra navegar pelas capas de cada sistema
- Botões pra rodar `fetch-covers` e `fetch-covers-fallback` com progresso ao
  vivo (via Server-Sent Events), incluindo o toggle simulação/aplicar de
  verdade que os comandos de CLI já tinham
- Zoom e badge da Biblioteca (✓/🏆/▶ + ★nota) direto na capa
- **✎ Editar** - um popup só pras 3 ações que antes eram botão separado
  (Renomear/Buscar/Trocar, unificadas 27/08 a pedido do usuário):
  campo de renomear **com cascata** (tenta renomear a ROM e qualquer
  save/state correspondente na mesma hora, inclusive corrigindo a
  referência `.bin` dentro de `.cue`/`.gdi` pra PS/SDC - se a ROM não
  for encontrada, cair em conflito, ou tiver mais de uma batendo, a
  capa ainda é renomeada mas fica marcada `renamed_pending`), upload
  manual, e busca visual nas duas fontes (ver seção de comandos acima
  pro que cada uma faz)
- **⚑ Marcar** - flag única (`Errada`/`Duplicada` eram 2 botões
  separados até 27/08, unificados: "com a galeria mais consolidada, o
  usuário mesmo decide se é duplicata ou capa errada")
- **Apagar com cascata** (`🗑 Apagar`): apaga capa + ROM + save/state
  de uma vez, com confirmação antes (ação irreversível). Único item por
  vez - não agrupa discos múltiplos como o rename faz, por segurança
  (apagar "Jogo (Disc 2)" não apaga o Disc 1/3 do mesmo jogo)
- Filtros "⚑ só marcadas" / "só sem correspondência" / "só sem capa",
  combináveis entre si (união, não interseção)
- **💾/⏱ Save/State por jogo**: badges na própria capa quando o jogo
  tem save e/ou state (convenção achatada do RetroArch, `saves_root`/
  `states_root`) - clicar apaga só aquele save ou state, sem mexer na
  ROM/capa
- Botão de busca em massa por fonte pra reprocessar sem_match/
  marcadas erradas - "🔍 Buscar no LaunchBox" e "🔍 Buscar no
  ScreenScraper", cada um roda só na fonte escolhida
- ⌃/⌄ no topo esconde/mostra os menus em 2 etapas (1º clique: busca/
  filtro de capas; 2º clique: topbar também; 3º: volta a mostrar tudo)
  pra mais espaço de galeria - preferência salva
- **Busca geral do acervo**: campo no topo pesquisa por nome em
  qualquer sistema configurado de uma vez (não só o selecionado),
  filtro opcional por console - clicar num resultado troca de sistema
  e rola até a capa certa, com destaque temporário. Pro Arcade, busca
  também pelo nome real do jogo, não só pelo código curto do romset
- **📦 ROMs Pesadas**: modal separado (botão no topo) pra PS,
  PS2, GameCube, Wii, PSP e 3DS - lista o que existe no PC, no celular
  (via adb) e no **Google Drive** (via `rclone`, sem precisar de
  celular conectado), e manda/baixa um item de cada vez sob demanda
  (com progresso via SSE). Itens que só existem no Drive mostram botão
  "⬇ Baixar do Drive" - no PC, o download vai primeiro pra uma pasta
  de staging (`~/Downloads` por padrão) e só depois é movido pra
  `roms_root/<CODIGO>/`, nunca direto na pasta sincronizada pelo Google
  Drive Desktop (evita conflito entre os dois mexendo no mesmo arquivo
  ao mesmo tempo). Renomear e apagar também disponíveis aqui, com a
  mesma cascata de ROM/save/state (sem capa, que esses sistemas não
  têm).
- **🗂 Organizar**: modal separado - lista o que está esperando em
  `roms_root/0-Organizar/` (ver comando `organize` acima) com um
  dropdown de sistema candidato por item (pré-selecionado se só bater
  com um) e um botão "Mover".
- **💾 Saves**: modal separado - editor de memory card PS1/PS2
  (`core/memcard.py`, envelopa `ps1vmc-tool`/`ps2vmc-tool`). PS1 e PS2
  juntos na mesma tela, uma seção por card configurado em
  `config.toml [memcards]`, com o nome do jogo resolvido a partir do
  serial (o card só guarda o serial, tipo "BASLUS-21672" -
  `core/serials.py` cruza contra os DATs de redump do
  libretro-database). Por save: exportar (PSU/MCS pra uma pasta de
  staging), apagar, transferir pra outro card do mesmo console, e
  importar um arquivo PSU/MCS/PSV pro card. Mais duas seções na mesma
  aba pra **Dolphin (GameCube)** e **PPSSPP** (`core/emu_saves.py`) -
  esses já guardam save individualizado por jogo nativamente (sem
  memory card compartilhado), lista o que existe só no celular via adb
  e baixa pra pasta local sob demanda.

O que ainda não tem (fases futuras, ver [`docs/roadmap.md`](docs/roadmap.md)):
revisão visual de fuzzy match lado a lado, auditoria completa de `.cue`
fora do padrão (`fix-cues` como comando), importar/injetar save de
volta no cartão (editor de memory card hoje só lista + exporta).

## Comandos manuais equivalentes (saves/states - `sync` ainda só cobre capas)

Cópias mais comuns entre PC e celular, via `adb`. Ajuste os caminhos aos
do seu `config.toml` se forem diferentes dos exemplos abaixo.

**Puxar saves do celular pro PC** (depois de uma sessão jogando no Android):
```bash
adb pull /storage/emulated/0/RetroArch/saves ~/Drive/Jogos/Saves/saves
adb pull /storage/emulated/0/RetroArch/states ~/Drive/Jogos/Saves/states
```

**Mandar saves do PC pro celular** (depois de jogar no PC):
```bash
adb push ~/Drive/Jogos/Saves/saves /storage/emulated/0/RetroArch/saves
adb push ~/Drive/Jogos/Saves/states /storage/emulated/0/RetroArch/states
```

**Sincronizar capas de um sistema específico pro celular** (depois de rodar
`fetch-covers`):
```bash
adb push "~/Drive/Jogos/Capas/Sony - PlayStation/Named_Boxarts" \
  "/storage/emulated/0/RetroArch/thumbnails/Sony - PlayStation/"
```

**Sincronizar TODAS as capas pro celular:**
```bash
cd ~/Drive/Jogos/Capas
for d in */; do
  sys="${d%/}"
  adb push "$sys/Named_Boxarts" "/storage/emulated/0/RetroArch/thumbnails/$sys/"
done
```

**Puxar o `retroarch.cfg` do celular pra conferir/editar:**
```bash
adb pull /storage/emulated/0/Android/data/com.retroarch/files/retroarch.cfg \
  ~/Drive/Jogos/retroarch_android.cfg
```

**Mandar de volta depois de editar** (o caminho é dentro da pasta privada do
app - às vezes precisa primeiro mandar pra um caminho público e copiar por
dentro do celular, dependendo de como o ambiente que roda o comando lida com
permissão):
```bash
adb push ~/Drive/Jogos/retroarch_android.cfg \
  /storage/emulated/0/Android/data/com.retroarch/files/retroarch.cfg
```

**Conferir se o celular está conectado e autorizado:**
```bash
adb devices -l
```

## Estrutura do projeto

```
PyRetro/
├── retrosync.py          # CLI (argparse) - ponto de entrada
├── config.example.toml   # template de configuração
├── config.toml           # sua config real (git-ignored)
├── core/
│   ├── covers.py          # busca/substituição de capas - implementado
│   ├── launchbox.py       # segunda fonte de capas (LaunchBox Games DB) - implementado
│   ├── screenscraper.py   # terceira fonte de capas (busca + proxy de mídia) - implementado e testado
│   ├── sanitize.py        # remove caracteres que o RetroArch não aceita - implementado
│   ├── sync.py            # sincronização PC<->Android (só capas) - implementado e testado no aparelho
│   ├── cues.py             # rename_disc_set (.cue/.gdi+.bin) - implementado; scan/auditoria - esqueleto
│   ├── heavy_roms.py       # gestão de ROMs pesadas (PS/PS2/GC/Wii/PSP/3DS) - implementado
│   ├── organize.py         # organiza "0-Organizar" pra roms_root/<CODIGO>/ - implementado
│   ├── playlist.py         # monta playlist .lpl a partir do que existe de verdade (PC/Android) - implementado
│   ├── config_backup.py    # snapshot datado de retroarch.cfg+config/+playlists/ - implementado
│   ├── rom_rename.py       # rename e apagar com cascata (ROM+capa+save/state) - implementado e testado
│   ├── memcard.py          # editor de memory card PS1/PS2 (ps1vmc-tool/ps2vmc-tool) - implementado e testado
│   ├── serials.py          # serial -> nome do jogo (DAT de redump), usado por memcard.py/emu_saves.py - implementado e testado
│   ├── emu_saves.py         # backup de save individualizado Dolphin(GC)/PPSSPP via adb - implementado e testado
│   ├── sortear.py           # sorteio aleatorio (leve local + pesado via catalogo cacheado) - implementado
│   ├── library.py           # biblioteca de jogos fora de ROM (lojas + planilha importada) - implementado
│   └── adb.py              # wrapper de adb com retry - implementado
├── gui/
│   ├── server.py          # servidor local da interface gráfica (Fase 1)
│   └── static/             # HTML/CSS/JS do frontend
├── docs/
│   ├── roadmap.md                     # estado atual e próximos passos
│   ├── changelog.md                   # histórico detalhado (bugs, testes, decisões)
│   ├── fontes_de_capas.md             # pesquisa de fontes de capa alternativas
│   ├── capas_sem_correspondencia.md   # capas não resolvidas por nenhuma fonte
│   ├── memory_card_editor.md          # editor de memory card PS1/PS2 - pesquisa + implementação
│   └── termux_setup.md                # rodar o PyRetro direto no Android
├── cache/
│   ├── covers_registry.json   # histórico do que já foi processado por fetch-covers
│   └── heavy_catalog.json     # catálogo de pesados no Drive, gerado por heavy-catalog - usado pelo sortear
└── logs/
```

## Status / próximos passos

| Módulo | Status |
|---|---|
| `core/covers.py` | Implementado e testado - resolve exato, fuzzy (só relatório), DAT do FBNeo pro Arcade (também usado pra `arcade_display_name`, nome de exibição na GUI), fallback de download via API do GitHub, distingue rate-limit de sem_match real; `process_system_cloud` (24/08) busca a partir do catálogo no Drive em vez de `roms_root` local, testado ponta a ponta (Saturn 37/37, Dreamcast 9/9) |
| `core/launchbox.py` | Implementado e testado - segunda fonte (LaunchBox Games DB) só pros sem_match do covers.py, exato + prefixo com trava de segurança |
| `core/sanitize.py` | Implementado e testado - remove `&`/`:`/`*` de nomes de capa e ROM, nunca sobrescreve em conflito |
| `core/screenscraper.py` | Implementado e testado com API real - `search_game`/`download_cover`, mapeamento de sistemas (`SYSTEM_MAP`), URLs de mídia com credencial embutida nunca vão pro cliente (proxy `/api/cover/ss_preview` + cache em memória em `gui/server.py`) |
| `core/adb.py` | Implementado e testado contra o aparelho real - `run`/`shell`/`push`/`pull`/`ensure_connected` com retry via kill-server/start-server |
| `core/sync.py` | Implementado e testado contra o aparelho real, só pra capas (`sync_capas`) - manifesto em `cache/sync_state.json`, classifica sem_mudança/pra PC/pro Android/conflito, nunca deleta. Extensão pra saves/states/runtime-logs **cancelada** (sempre vai usar Google Drive pra isso) |
| `core/cues.py` | `rename_disc_set` implementado e testado (`.cue`/`.gdi` + sidecars `.bin`, corrige a referência de texto). Auditoria completa (`scan_folder`/`fix_all`) ainda esqueleto |
| `core/heavy_roms.py` | Implementado e testado ponta a ponta com o celular real - identifica ROMs de PS/PS2/GameCube/Wii/PSP/3DS e envia sob demanda via adb, somando sidecars |
| `core/organize.py` | Implementado e testado ponta a ponta via GUI - identifica ROMs em `0-Organizar/` pela extensão e move pro sistema certo, com desambiguação manual quando a extensão bate com mais de um sistema |
| `core/rom_rename.py` | Implementado e testado ponta a ponta via GUI - rename e apagar com cascata (ROM + capa + save/state) pra sistemas leves e pesados, incluindo grupos multi-disco no rename (PS1/PS2); `find_flat_matches`/`delete_flat_matches` reaproveitados pela gestão de save/state na galeria |
| `core/memcard.py` | Implementado e testado contra cartões reais - listar/exportar/apagar/importar/transferir save de memory card PS1/PS2 via `ps1vmc-tool`/`ps2vmc-tool` |
| `core/serials.py` | Implementado e testado - serial → nome do jogo via DAT de redump do libretro-database (PS1/PS2/GameCube/PSP), usado pelo `memcard.py` e `emu_saves.py` |
| `core/emu_saves.py` | Implementado e testado no aparelho real - lista/baixa save individualizado do Dolphin(GameCube)/PPSSPP via adb, espelhando a estrutura de pastas que o usuário já mantém manualmente |
| `core/playlist.py` | Implementado e testado ponta a ponta com o celular real (24/08) - monta `.lpl` a partir do que existe em `roms_root`/`jogos_root`, `core_path`/`core_name` "DETECT" por item, PC e Android tratados separado (sistemas pesados não sincronizam sozinhos, cada lado pode ter jogos diferentes) |
| `core/config_backup.py` | Implementado e testado ponta a ponta (24/08) - snapshot datado de `retroarch.cfg`+`config/`+`playlists/` pro PC (cópia local) e Android (`adb pull`), pasta nova por data, nunca sobrescreve |
| `core/sortear.py` | Implementado e testado ponta a ponta contra a coleção real (27/08) - pool único leve+pesado com peso por jogo, catálogo de pesados lido do cache (`heavy_catalog.json`, gerado por `heavy-catalog`) pra não depender de `rclone` ao vivo a cada sorteio |
| `core/library.py` | Implementado e testado ponta a ponta com dados reais (27/08). `library.json`: planilha (94) + heroic (198) + steam (102) via `library-refresh`, e PSN (9, digital+físico) + Xbox (55) via `library-add` (cadastro manual, listas levantadas pelo usuário) = **417 jogos**, merge por nome exato, fuzzy só reportado (nunca aplicado sozinho). `read_psn_library`/`read_psn_trophy_titles`/`read_xbox_library` (API) implementados e testados contra conta real mas não usados por decisão do usuário - ver `docs/changelog.md`. Capa via `library-fetch-covers` (SteamGridDB) testada nos 417: 340 baixadas, 76 sem match exato, 1 erro de rede. `get_or_create_for_rom` (27/08, revisado no mesmo dia pra exigir plataforma além de nome - ver `PLATAFORMA_ROM_CODES`) permite criar/achar registro por nome+plataforma, base do tracking universal na GUI; a aba Biblioteca mostra 405 dos 417 (12 já são ROM de verdade numa plataforma que bate de fato, filtrados dinamicamente - ver `docs/changelog.md`) |
| `retrosync.py` | `fetch-covers`, `fetch-covers-cloud` (leve + pesado), `fetch-covers-fallback`, `convert-covers`, `validate-covers`, `sanitize-names`, `sync covers`, `heavy-roms`, `heavy-catalog`, `sortear`, `library-import-sheet`, `library-refresh` (heroic/steam/psn/xbox), `library-add`, `library-fetch-covers`, `organize`, `rebuild-playlist` e `backup-config` conectados de verdade; `sync saves/states/metrics` (cancelado) e `fix-cues` (auditoria) levantam `NotImplementedError` |

Roadmap atual e próximos passos: [`docs/roadmap.md`](docs/roadmap.md).
Histórico detalhado (bugs achados, testes, decisões de desenho):
[`docs/changelog.md`](docs/changelog.md). Outros documentos:
pesquisa de fontes de capa alternativas
([`docs/fontes_de_capas.md`](docs/fontes_de_capas.md)), pesquisa e
notas de implementação do editor de memory card PS1/PS2
([`docs/memory_card_editor.md`](docs/memory_card_editor.md)), rodar o
PyRetro direto no Android
([`docs/termux_setup.md`](docs/termux_setup.md)).

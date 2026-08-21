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

Sistemas configurados em `config.toml` `[heavy_systems]` (PS, SS, SDC,
PS2, GameCube, Wii, PSP, 3DS - Switch fica de fora de propósito, gestão
feita por fora do PyRetro). Diferente dos sistemas em `[systems]`
(sincronizados sozinhos via Google Drive), esses ficam só no PC até
serem enviados/baixados sob demanda - `retrosync heavy-roms <CODIGO>`
mostra o que existe em `roms_root/<CODIGO>/`, no Google Drive (via
`rclone`, config `[rclone]`) e no celular (via adb, se conectado). Um
"item" é um arquivo ou uma pasta inteira; PS/SS/SDC somam o tamanho dos
`.bin` sidecars automaticamente. Nunca sobrescreve no celular sem
`--overwrite`. Download do Drive vai primeiro pra `staging_dir`
(`~/Downloads` por padrão) e só depois é movido pra
`roms_root/<CODIGO>/` - nunca escreve direto na pasta sincronizada pelo
Google Drive Desktop.

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
- Zoom, marcar capa errada, upload manual, busca visual nas duas fontes
  (ver seção de comandos acima pro que cada uma faz)
- Renomear capa **com cascata**: tenta renomear a ROM e qualquer
  save/state correspondente na mesma hora (inclusive corrigindo a
  referência `.bin` dentro de `.cue`/`.gdi` pra PS/SDC). Se a ROM não
  for encontrada, cair em conflito, ou tiver mais de uma batendo, a
  capa ainda é renomeada mas fica marcada (`renamed_pending`) - o
  fallback antigo continua existindo pra esses casos
- Marcar capa como duplicada (`⧉ Duplicada` - sinaliza que capa+ROM
  precisam ser removidas)
- **Apagar com cascata** (`🗑 Apagar`): apaga capa + ROM + save/state
  de uma vez, com confirmação antes (ação irreversível). Único item por
  vez - não agrupa discos múltiplos como o rename faz, por segurança
  (apagar "Jogo (Disc 2)" não apaga o Disc 1/3 do mesmo jogo)
- Filtros "só marcadas como erradas" / "só sem correspondência" / "só
  duplicadas", combináveis entre si (união, não interseção)
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
- **📦 ROMs Pesadas**: modal separado (botão no topo) pra PS, SS, SDC,
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
│   ├── heavy_roms.py       # gestão de ROMs pesadas (PS/SS/SDC/PS2/GC/Wii/PSP/3DS) - implementado
│   ├── organize.py         # organiza "0-Organizar" pra roms_root/<CODIGO>/ - implementado
│   ├── rom_rename.py       # rename e apagar com cascata (ROM+capa+save/state) - implementado e testado
│   ├── memcard.py          # editor de memory card PS1/PS2 (ps1vmc-tool/ps2vmc-tool) - implementado e testado
│   ├── serials.py          # serial -> nome do jogo (DAT de redump), usado por memcard.py/emu_saves.py - implementado e testado
│   ├── emu_saves.py         # backup de save individualizado Dolphin(GC)/PPSSPP via adb - implementado e testado
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
│   └── covers_registry.json   # histórico do que já foi processado por fetch-covers
└── logs/
```

## Status / próximos passos

| Módulo | Status |
|---|---|
| `core/covers.py` | Implementado e testado - resolve exato, fuzzy (só relatório), DAT do FBNeo pro Arcade (também usado pra `arcade_display_name`, nome de exibição na GUI), fallback de download via API do GitHub, distingue rate-limit de sem_match real |
| `core/launchbox.py` | Implementado e testado - segunda fonte (LaunchBox Games DB) só pros sem_match do covers.py, exato + prefixo com trava de segurança |
| `core/sanitize.py` | Implementado e testado - remove `&`/`:`/`*` de nomes de capa e ROM, nunca sobrescreve em conflito |
| `core/screenscraper.py` | Implementado e testado com API real - `search_game`/`download_cover`, mapeamento de sistemas (`SYSTEM_MAP`), URLs de mídia com credencial embutida nunca vão pro cliente (proxy `/api/cover/ss_preview` + cache em memória em `gui/server.py`) |
| `core/adb.py` | Implementado e testado contra o aparelho real - `run`/`shell`/`push`/`pull`/`ensure_connected` com retry via kill-server/start-server |
| `core/sync.py` | Implementado e testado contra o aparelho real, só pra capas (`sync_capas`) - manifesto em `cache/sync_state.json`, classifica sem_mudança/pra PC/pro Android/conflito, nunca deleta. Extensão pra saves/states/runtime-logs **cancelada** (sempre vai usar Google Drive pra isso) |
| `core/cues.py` | `rename_disc_set` implementado e testado (`.cue`/`.gdi` + sidecars `.bin`, corrige a referência de texto). Auditoria completa (`scan_folder`/`fix_all`) ainda esqueleto |
| `core/heavy_roms.py` | Implementado e testado ponta a ponta com o celular real - identifica ROMs de PS/SS/SDC/PS2/GameCube/Wii/PSP/3DS e envia sob demanda via adb, somando sidecars |
| `core/organize.py` | Implementado e testado ponta a ponta via GUI - identifica ROMs em `0-Organizar/` pela extensão e move pro sistema certo, com desambiguação manual quando a extensão bate com mais de um sistema |
| `core/rom_rename.py` | Implementado e testado ponta a ponta via GUI - rename e apagar com cascata (ROM + capa + save/state) pra sistemas leves e pesados, incluindo grupos multi-disco no rename (PS1/PS2); `find_flat_matches`/`delete_flat_matches` reaproveitados pela gestão de save/state na galeria |
| `core/memcard.py` | Implementado e testado contra cartões reais - listar/exportar/apagar/importar/transferir save de memory card PS1/PS2 via `ps1vmc-tool`/`ps2vmc-tool` |
| `core/serials.py` | Implementado e testado - serial → nome do jogo via DAT de redump do libretro-database (PS1/PS2/GameCube/PSP), usado pelo `memcard.py` e `emu_saves.py` |
| `core/emu_saves.py` | Implementado e testado no aparelho real - lista/baixa save individualizado do Dolphin(GameCube)/PPSSPP via adb, espelhando a estrutura de pastas que o usuário já mantém manualmente |
| `retrosync.py` | `fetch-covers`, `fetch-covers-fallback`, `convert-covers`, `validate-covers`, `sanitize-names`, `sync covers`, `heavy-roms` e `organize` conectados de verdade; `sync saves/states/metrics` (cancelado) e `fix-cues` (auditoria) levantam `NotImplementedError` |

Roadmap atual e próximos passos: [`docs/roadmap.md`](docs/roadmap.md).
Histórico detalhado (bugs achados, testes, decisões de desenho):
[`docs/changelog.md`](docs/changelog.md). Outros documentos:
pesquisa de fontes de capa alternativas
([`docs/fontes_de_capas.md`](docs/fontes_de_capas.md)), pesquisa e
notas de implementação do editor de memory card PS1/PS2
([`docs/memory_card_editor.md`](docs/memory_card_editor.md)), rodar o
PyRetro direto no Android
([`docs/termux_setup.md`](docs/termux_setup.md)).

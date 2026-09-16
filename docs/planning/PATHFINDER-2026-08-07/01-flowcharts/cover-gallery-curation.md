# Feature: Cover Gallery Curation

GUI-only per-cover human curation actions: flag as wrong, mark/unmark duplicate, rename
(cascading to ROM+save/state), delete (cascading), upload a manual cover image. Includes the
full trace of the shared cascade engine (`core/rom_rename.py`).

## Sources consulted

- `gui/server.py:43,58,189-194,328-393` (helpers), `:668-853` (all `/api/cover/*` POST handlers),
  `:943-993` (`/api/heavy/rename`, `/api/heavy/delete`, for shared-engine confirmation)
- `gui/static/app.js:100-341` (cover-card actions), `:417-505` inspected but excluded (manual
  search modal — belongs to Cover Acquisition Pipeline)
- `core/rom_rename.py` — full file (250 lines)
- `core/sanitize.py` — full file (59 lines)
- `core/cues.py` — signatures only (`find_bin_sidecars` L44, `rename_disc_set` L57)

## Concrete findings

**Rename flow.** "✎ Renomear" (`app.js:154,164`) → `renameCover()` (`:298-320`) → `prompt()` →
`POST /api/cover/rename`. Handler (`server.py:720-774`) resolves `_cover_path()`, sanitizes the
new name (`core/sanitize.py:26-29`, `server.py:735`), locates the current cover among
`.png/.jpg/.jpeg`, checks cover-level collision, and **renames the cover file unconditionally**
(`server.py:752`) *before* attempting the ROM cascade. Only then calls
`rom_rename_mod.rename_with_cascade()` (`core/rom_rename.py:164-175`, called at
`server.py:758-760`).

Inside the cascade, `_rename_rom()` (`rom_rename.py:100-141`) first checks
`_find_disc_group()` (`:51-68`): if `old_label` ends in `" (Disc N)"` and siblings sharing the
base title exist, the **whole group renames together** via `_rename_disc_group()` (`:71-97`,
two-pass: dry-run conflict check across all discs first, then apply) — confirming renaming
"Game (Disc 1)" cascades to Disc 2/3 as long as none conflict. `.cue/.gdi` discs go through
external `core/cues.py:rename_disc_set()`; other extensions get a plain `Path.rename()`. If no
disc group applies, single-item match yields `nao_encontrado`/`ambiguo`/`conflito`/`renomeado`.
Only on `renomeado` does the cascade rename save/state files via `_rename_flat_matches()`
(`:144-161`, called twice at `:173-174`) — exact-prefix match (`old_label + "."`, never `glob()`)
against `saves_root`/`states_root`, skipping any file whose destination already exists.

Back in `server.py:762-770`: the registry drops the old label; if the ROM cascade did **not**
succeed, a `renamed_pending` entry is written under the *new* label carrying `old_label` and
`rom_status` — the fallback letting the cover rename proceed even when the ROM side couldn't
keep up.

**Delete flow.** "🗑 Apagar" (`app.js:157,166`) → `deleteCover()` (`:209-223`) → `confirm()` →
`POST /api/cover/delete`. Handler (`server.py:776-798`) calls `delete_with_cascade()`
(`rom_rename.py:232-250`, called at `server.py:791-793`), passing the real `capas_dir` (unlike
the heavy-ROM variant). `delete_with_cascade` always attempts all four removals regardless of
partial state: `_delete_rom()` (`:178-211`, single-item match only, deletes `.bin` sidecars via
`cues_mod.find_bin_sidecars()` or `shutil.rmtree` for directories), then unlinks the cover, then
`delete_flat_matches()` for saves and states. **By design, delete never groups multi-disc
titles** (module docstring, `:35-41`) — deleting "Game (Disc 2)" removes only Disc 2. Registry
entry is unconditionally popped, no `renamed_pending`-equivalent for delete.

**Secondary paths.** Flag/unflag/duplicate/unduplicate (`server.py:681-718`) are pure registry
read-modify-write toggles, no filesystem side effects. Upload (`app.js:322-341` →
`server.py:814-853`) base64-decodes the file, writes to `.tmp`, unconditionally runs it through
ImageMagick `convert` to normalize to real PNG regardless of claimed extension (deliberate
defense per code comment `:833-840`), deletes stale sibling `.jpg`, marks `status: "manual"`.

## Flowchart

```mermaid
flowchart TD
  UI1["Click 'Renomear' button<br/>app.js:154,164"] --> RC["renameCover()<br/>app.js:298-320"]
  RC --> PR{"prompt() new name<br/>app.js:304"}
  PR -->|cancelled/empty/unchanged| RC_END["return, no request sent<br/>app.js:305-307"]
  PR -->|valid| POST1["POST /api/cover/rename<br/>app.js:308-312"]

  POST1 --> SR1["do_POST dispatch<br/>server.py:720"]
  SR1 --> CP1["_cover_path(code,label)<br/>server.py:344-354,730"]
  CP1 -->|sistema desconhecido| ERR1["404 error<br/>server.py:731-732"]
  CP1 -->|ok| V1{"new_label_raw vazio?<br/>server.py:733-734"}
  V1 -->|sim| ERR2["400 error<br/>server.py:734"]
  V1 -->|não| SAN["sanitize_mod.sanitize_name()<br/>core/sanitize.py:26-29"]
  SAN --> V2{"new_label == label?<br/>server.py:736-737"}
  V2 -->|sim| ERR3["400 error<br/>server.py:737"]
  V2 -->|não| FINDSRC["find cover file .png/.jpg/.jpeg<br/>server.py:739-746"]
  FINDSRC -->|não encontrada| ERR4["404 error<br/>server.py:745-746"]
  FINDSRC -->|achada| CHKDEST{"dest cover já existe?<br/>server.py:748-750"}
  CHKDEST -->|sim| ERR5["409 conflito<br/>server.py:749-750"]
  CHKDEST -->|não| RENSRC["src.rename(dest)<br/>cover file renamed<br/>server.py:752"]
  RENSRC --> LOADCFG["load_config() + resolve roots<br/>server.py:754-757"]
  LOADCFG --> CASCADE["rename_with_cascade()<br/>core/rom_rename.py:164-175<br/>call site server.py:758-760"]

  CASCADE --> RROM["_rename_rom()<br/>core/rom_rename.py:100-141"]
  RROM --> FDG["_find_disc_group()<br/>core/rom_rename.py:51-68"]
  FDG -->|multi-disc group found| RDG["_rename_disc_group()<br/>core/rom_rename.py:71-97"]
  RDG --> DRY["dry-run pass: check conflicts<br/>on ALL discs first<br/>core/rom_rename.py:79-84"]
  DRY -->|any conflict| DGCONF["rom status: conflito<br/>no files touched<br/>core/rom_rename.py:82,84"]
  DRY -->|ok| APPLY["apply pass: rename each disc<br/>.cue/.gdi via cues.rename_disc_set()<br/>else disc.rename()<br/>core/rom_rename.py:87-97"]
  APPLY --> ROMOK["rom status: renomeado<br/>core/rom_rename.py:97"]

  FDG -->|not multi-disc| MATCH["match single file or dir<br/>by stem+ext<br/>core/rom_rename.py:109-116"]
  MATCH -->|0 matches| ROMNF["rom status: nao_encontrado<br/>core/rom_rename.py:118"]
  MATCH -->|greater than 1 match| ROMAMB["rom status: ambiguo<br/>core/rom_rename.py:119-120"]
  MATCH -->|1 match| KIND{"dir? .cue/.gdi? other?<br/>core/rom_rename.py:123-141"}
  KIND -->|dir, dest exists| ROMCONF["rom status: conflito<br/>core/rom_rename.py:126"]
  KIND -->|dir, ok| RENDIR["rom.rename(dest)<br/>core/rom_rename.py:127"]
  KIND -->|".cue/.gdi"| CUES["cues.rename_disc_set(apply=True)<br/>core/cues.py:57 (external)"]
  KIND -->|other, dest exists| ROMCONF2["rom status: conflito<br/>core/rom_rename.py:138-139"]
  KIND -->|other, ok| RENFILE["rom.rename(dest)<br/>core/rom_rename.py:140"]
  RENDIR --> ROMOK
  CUES --> ROMOK
  RENFILE --> ROMOK

  ROMOK --> SAVEST["_rename_flat_matches(saves_dir)<br/>+ _rename_flat_matches(states_dir)<br/>core/rom_rename.py:173-174,144-161"]
  SAVEST --> CASCOK["cascade result assembled<br/>core/rom_rename.py:175"]

  DGCONF --> CASCFAIL["cascade returns early<br/>saves=[] states=[]<br/>core/rom_rename.py:171-172"]
  ROMNF --> CASCFAIL
  ROMAMB --> CASCFAIL
  ROMCONF --> CASCFAIL
  ROMCONF2 --> CASCFAIL

  CASCOK --> REG1["load_registry(), pop old label<br/>server.py:762-764"]
  CASCFAIL --> REG1

  REG1 --> PENDCHK{"cascade.rom.status<br/>!= renomeado?<br/>server.py:765"}
  PENDCHK -->|sim - FALLBACK| PEND["registry[new_label] =<br/>status renamed_pending<br/>server.py:766-769"]
  PENDCHK -->|não| SKIP["no pending entry written"]
  PEND --> SAVEREG["save_registry()<br/>server.py:193-194,770"]
  SKIP --> SAVEREG
  SAVEREG --> RESP1["JSON response ok<br/>new_label, file, cascade<br/>server.py:771-774"]
  RESP1 --> UI1DONE["selectSystem() reload gallery<br/>alert(describeCascade())<br/>app.js:315-316"]

  ERR1 --> UIERR1["alert error<br/>app.js:318"]
  ERR2 --> UIERR1
  ERR3 --> UIERR1
  ERR4 --> UIERR1
  ERR5 --> UIERR1

  UI2["Click 'Apagar' button<br/>app.js:157,166"] --> DC["deleteCover()<br/>app.js:209-223"]
  DC --> CONF{"confirm() dialog<br/>app.js:210"}
  CONF -->|cancel| DC_END["return, no request<br/>app.js:210"]
  CONF -->|ok| POST2["POST /api/cover/delete<br/>app.js:211-215"]

  POST2 --> SR2["do_POST dispatch<br/>server.py:776"]
  SR2 --> CP2["_cover_path(code,label)<br/>server.py:783"]
  CP2 -->|sistema desconhecido| ERR6["404 error<br/>server.py:784-785"]
  CP2 -->|ok| LOADCFG2["load_config() + resolve roots<br/>server.py:787-790"]
  LOADCFG2 --> CASCADE2["delete_with_cascade()<br/>core/rom_rename.py:232-250<br/>call site server.py:791-793"]

  CASCADE2 --> DROM["_delete_rom()<br/>core/rom_rename.py:178-211"]
  DROM --> DMATCH["match single file/dir<br/>NO disc grouping<br/>core/rom_rename.py:186-192"]
  DMATCH -->|0 matches| DROMNF["rom status: nao_encontrado<br/>core/rom_rename.py:195"]
  DMATCH -->|greater than 1 match| DROMAMB["rom status: ambiguo<br/>core/rom_rename.py:196-197"]
  DMATCH -->|1 match, dir| RMTREE["shutil.rmtree(rom)<br/>core/rom_rename.py:202-203"]
  DMATCH -->|"1 match, .cue/.gdi"| DELSIDE["cues.find_bin_sidecars()<br/>unlink sidecars + rom.unlink()<br/>core/cues.py:44 (external)<br/>core/rom_rename.py:205-210"]
  DMATCH -->|1 match, other file| RMFILE["rom.unlink()<br/>core/rom_rename.py:209-210"]
  RMTREE --> DROMOK["rom status: apagado<br/>core/rom_rename.py:211"]
  DELSIDE --> DROMOK
  RMFILE --> DROMOK

  DROMOK --> DCOVER["delete cover .png/.jpg/.jpeg<br/>if exists, unlink<br/>core/rom_rename.py:242-247"]
  DROMNF --> DCOVER
  DROMAMB --> DCOVER
  DCOVER --> DSAVEST["delete_flat_matches(saves_dir)<br/>+ delete_flat_matches(states_dir)<br/>core/rom_rename.py:248-249,225-229"]
  DSAVEST --> DCASCOK["cascade result assembled<br/>core/rom_rename.py:250"]

  DCASCOK --> REG2["load_registry(), pop label entirely<br/>save_registry()<br/>server.py:795-797"]
  REG2 --> RESP2["JSON response ok + cascade<br/>server.py:798"]
  RESP2 --> UI2DONE["alert(describeDeleteCascade())<br/>selectSystem() reload gallery<br/>app.js:217-219"]

  ERR6 --> UIERR2["alert error<br/>app.js:221"]

  UI3["Click Errada / Duplicada button<br/>app.js:152-153,162-163"] --> TFD["toggleFlag() / toggleDuplicate()<br/>app.js:264-282"]
  TFD --> POST3["POST /api/cover/flag|unflag|<br/>duplicate|unduplicate<br/>app.js:266,276"]
  POST3 --> SR3["set or pop registry status<br/>save_registry()<br/>server.py:681-718"]
  SR3 --> UI3DONE["refreshCard() patches card in place<br/>app.js:271,281,231-262"]

  UI4["Click Trocar -> pick file<br/>app.js:156,168-169"] --> UC["uploadCover()<br/>FileReader to base64<br/>app.js:322-341"]
  UC --> POST4["POST /api/cover/upload<br/>app.js:327-331"]
  POST4 --> SR4["validate ext/base64/min size<br/>write .tmp, run convert (ImageMagick)<br/>server.py:814-846"]
  SR4 -->|falha| ERR7["400/500 error<br/>server.py:823-824,827-830,845-846"]
  SR4 -->|ok| REMOVEOLD["unlink stale .jpg if replaced<br/>registry status: manual<br/>server.py:847-852"]
  REMOVEOLD --> RESP4["JSON ok + file<br/>server.py:853"]
  RESP4 --> UI4DONE["refreshCard() cache-bust reload<br/>app.js:334"]
  ERR7 --> UIERR4["alert error<br/>app.js:337"]

  CONFIGFILE[("config.toml<br/>via load_config()<br/>server.py:58")]
  REGISTRYFILE[("cache/covers_registry.json<br/>REGISTRY_PATH server.py:43,189-194")]
  IMAGEMAGICK[["convert (ImageMagick)<br/>external subprocess<br/>server.py:843"]]
  CUESMOD[["core/cues.py<br/>rename_disc_set:57, find_bin_sidecars:44"]]
  HEAVYRENAME["POST /api/heavy/rename handler<br/>server.py:943-974"]
  HEAVYDELETE["POST /api/heavy/delete handler<br/>server.py:976-993"]

  LOADCFG -.-> CONFIGFILE
  LOADCFG2 -.-> CONFIGFILE
  REG1 -.-> REGISTRYFILE
  SAVEREG -.-> REGISTRYFILE
  REG2 -.-> REGISTRYFILE
  SR3 -.-> REGISTRYFILE
  REMOVEOLD -.-> REGISTRYFILE
  SR4 -.-> IMAGEMAGICK
  CUES -.-> CUESMOD
  DELSIDE -.-> CUESMOD
  HEAVYRENAME -.->|"shares engine, call at server.py:962"| CASCADE
  HEAVYDELETE -.->|"shares engine, call at server.py:990, capas_dir=None"| CASCADE2
```

## External dependencies

- **core/cues.py** (not fully read): `rename_disc_set()` at `:57` — called from
  `rom_rename.py:81,90,131` for `.cue/.gdi` rename; `find_bin_sidecars()` at `:44` — called from
  `rom_rename.py:206` during `.cue/.gdi` delete.
- **ImageMagick `convert`** — invoked via `subprocess.run` at `gui/server.py:843`, upload path
  only, normalizes arbitrary image bytes to true PNG regardless of client-supplied extension.
- **`cache/covers_registry.json`** — touched by flag, unflag, duplicate, unduplicate, rename,
  delete, and upload.
- **`config.toml`** — via `load_config()`, supplies `roms_root`, `saves_root`, `states_root`,
  `capas_root`.
- **Heavy ROM Management — confirmed shared-engine relationship:**
  - `gui/server.py:962` — `POST /api/heavy/rename` calls the exact same `rename_with_cascade()`
    (`rom_rename.py:164-175`) that cover-rename calls at `server.py:758-760`.
  - `gui/server.py:990` — `POST /api/heavy/delete` calls the exact same `delete_with_cascade()`
    (`rom_rename.py:232-250`) that cover-delete calls at `server.py:791-793`, but with
    `capas_dir=None` (heavy systems skip the cover-deletion branch entirely).

## Confidence note and known gaps

High confidence: every node in the rename/delete cascades and registry side effects traced
directly against source, all line numbers verified.

- `core/cues.py` internals not read — treated as opaque external dependency.
- Manual-search-modal (`app.js:417-505`, `/api/cover/search`, `/api/cover/select`) inspected but
  excluded — triggered from the same card but semantically belongs to the Cover Acquisition
  Pipeline flowchart (automated match/select vs. manual upload).
- `delete_save` (`server.py:800-812`, `app.js:177-193`) read but not diagrammed in full — simple
  flat-match delete independent of registry, lower priority than the two main cascades.

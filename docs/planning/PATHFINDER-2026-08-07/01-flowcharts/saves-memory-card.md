# Feature: Saves & Memory Card Management

Two distinct backend systems sharing one GUI modal ("💾 Saves"): (A) a PS1/PS2 memory-card editor
wrapping external `ps1vmc-tool`/`ps2vmc-tool` binaries, and (B) per-game save backup for
Dolphin(GameCube)/PPSSPP pulled from the phone via adb. Both resolve display names from a serial
number via a shared redump DAT index.

## Sources consulted

- `core/memcard.py` — full read (196 lines)
- `core/emu_saves.py` — full read (141 lines)
- `core/serials.py` — full read (113 lines)
- `core/adb.py` lines 34-83 (`run`/`shell`/`push`/`pull`)
- `gui/server.py:340-380` (`_memcard_path`), `:595-643` (list routes), `:985-1084` (write routes)
- `gui/static/app.js:852-1151` (Saves modal, all `/api/memcards/*` and `/api/emu_saves/*` calls)

## Concrete findings

**Shared entry point.** `openSaves()` (`app.js:852`) → `loadSavesCards()` (`:865`) fetches
`/api/memcards` (`server.py:603`) to enumerate configured PS1/PS2 slots from
`config.toml [memcards]`, then in parallel fetches `/api/memcards/list/<key>` per card and
`/api/emu_saves/list/GC` + `/api/emu_saves/list/PSP` (`app.js:878-889`). Tab switching is
client-side over already-fetched data.

**Path A — memcard editor.** `list_card()` (`memcard.py:74`) runs
`subprocess.run([binname, card_path, "-ls", "/"])` (`:57-59,80`, `binname` = `ps1vmc-tool`/
`ps2vmc-tool`). For each row, `serials_mod.normalize_slot_serial(raw_name)` (`:91,108`) derives a
serial looked up directly as `index.get(console,{}).get(serial)` (`:94,111`) — **this bypasses
`serials.lookup()` and re-implements its two-line body inline.**
- Export (`:117`): `-mcs <slot> <dest>` (PS1) / `-px <raw_name> <dest>` (PS2) → `export_dir`
  (default `~/Downloads`).
- Delete (`:131`): `-rm <slot>` (PS1); PS2 lists folder, removes each child, then `-rmdir`
  (`:137-146`, folders can't be removed non-empty).
- Import (`:149`): writes uploaded file to server-side temp path, `-in <file>` (PS1) or
  `-pu`/`-pi <file>` (PS2, by extension), always unlinks temp in `finally`.
- Transfer (`:184`): export→import→delete, ordered so a failed import never touches the source.

**Path B — emu_saves backup.** `list_remote()` (`emu_saves.py:91`) calls `ensure_connected` then
`adb shell "find <scan_root> -name '*.gci' ..."` (GC) or `-type d` (PSP) (`:98-104`). For each item,
`_resolve_name()` (`:76`) extracts a code/serial via regex (`_gc_code`/`_psp_serial`) and looks it
up directly as `serials_index.get(emu,{}).get(...)` (`:78-81`) — **again bypassing
`serials.lookup()`, duplicating its logic with different regexes than memcard.py.** `list_local()`
(`:118`) scans the mirrored local folder to flag `in_pc`.
- Pull (`:130`): computes `dest = local_root/rel_path`, creates parent dirs, re-confirms adb
  connection, calls `adb_mod.pull()` (`:138` → `adb.py:80-83`, itself redundantly re-creating
  parent dirs, then `subprocess.run(["adb","pull",...])`).

## Flowchart

```mermaid
flowchart TD
    subgraph UI["gui/static/app.js — Saves modal (852-1151)"]
        Open["openSaves<br/>app.js:852"] --> LoadCards["loadSavesCards<br/>app.js:865"]
        LoadCards --> FetchCards["GET /api/memcards<br/>app.js:869"]
        LoadCards --> FetchMCList["GET /api/memcards/list/&lt;key&gt;<br/>app.js:880"]
        LoadCards --> FetchEmuList["GET /api/emu_saves/list/&lt;emu&gt;<br/>app.js:885"]
        FetchCards --> Tabs["renderSavesTabs + selectSavesConsole<br/>app.js:895,908"]
        FetchMCList --> Tabs
        FetchEmuList --> Tabs
        Tabs --> Render["renderSavesList<br/>app.js:924"]
        Render -->|"PS1/PS2 tab"| ExportBtn["exportSaveItem<br/>app.js:1041"]
        Render -->|"PS1/PS2 tab"| DeleteBtn["deleteSaveItem<br/>app.js:1055"]
        Render -->|"PS1/PS2 tab"| ImportBtn["importSaveFile<br/>app.js:1115"]
        Render -->|"PS1/PS2 tab"| TransferBtn["transferSaveItem<br/>app.js:1075"]
        Render -->|"GC/PSP tab"| PullBtn["pullEmuSaveItem<br/>app.js:1021"]
    end

    subgraph SrvA["gui/server.py — memcards routes"]
        RouteMCList["/api/memcards/list/&lt;key&gt;<br/>server.py:615-625"]
        RouteExport["/api/memcards/export<br/>server.py:995-1009"]
        RouteDelete["/api/memcards/delete<br/>server.py:1011-1023"]
        RouteImport["/api/memcards/import<br/>server.py:1025-1050"]
        RouteTransfer["/api/memcards/transfer<br/>server.py:1052-1069"]
        ResolveKey["_memcard_path(key)<br/>server.py:356"]
    end

    subgraph SrvB["gui/server.py — emu_saves routes"]
        RouteEmuList["/api/emu_saves/list/&lt;emu&gt;<br/>server.py:627-642"]
        RoutePull["/api/emu_saves/pull<br/>server.py:1071-1083"]
    end

    subgraph CoreA["core/memcard.py"]
        ListCard["list_card()<br/>memcard.py:74"]
        Run1["_run: subprocess.run([binname, card_path, '-ls','/'])<br/>memcard.py:57-59,80"]
        NormSerial["serials_mod.normalize_slot_serial(raw_name)<br/>memcard.py:91,108"]
        IdxLookupA["index.get(console,{}).get(serial)<br/>memcard.py:94,111 (inlined, bypasses serials.lookup)"]
        ExportFn["export_save(): '-mcs slot dest' (PS1) / '-px raw_name dest' (PS2)<br/>memcard.py:117-128"]
        DeleteFn["delete_save(): '-rm slot' (PS1) / ls+rm each+'-rmdir' (PS2)<br/>memcard.py:131-146"]
        ImportFn["import_save(): '-in file' (PS1) / '-pu'/'-pi file' (PS2)<br/>memcard.py:149-181"]
        TransferFn["transfer_save(): export→import→delete<br/>memcard.py:184-196"]
    end

    subgraph CoreB["core/emu_saves.py"]
        ListRemote["list_remote()<br/>emu_saves.py:91"]
        AdbShell["adb_mod.shell('find ... -name *.gci' / '-type d')<br/>emu_saves.py:98-104"]
        ResolveName["_resolve_name() -> _gc_code/_psp_serial<br/>emu_saves.py:66-81"]
        IdxLookupB["serials_index.get(emu,{}).get(code) (inlined, bypasses serials.lookup)<br/>emu_saves.py:78-81"]
        ListLocal["list_local()<br/>emu_saves.py:118"]
        PullFn["pull_item(): dest=local_root/rel_path; mkdir; adb_mod.pull()<br/>emu_saves.py:130-141"]
    end

    subgraph CoreC["core/serials.py"]
        BuildIndex["build_index()<br/>serials.py:84"]
        Lookup["lookup(console, raw, index) [defined but NOT called by memcard.py or emu_saves.py]<br/>serials.py:107-113"]
    end

    subgraph AdbMod["core/adb.py"]
        EnsureConn["ensure_connected()<br/>adb.py:101"]
        AdbPull["pull(): local.parent.mkdir(); subprocess.run(['adb','pull',remote,local])<br/>adb.py:80-83"]
    end

    FetchMCList --> RouteMCList --> ResolveKey
    RouteMCList --> BuildIndex
    RouteMCList --> ListCard --> Run1
    Run1 --> NormSerial --> IdxLookupA
    IdxLookupA --> BuildIndex

    FetchEmuList --> RouteEmuList --> BuildIndex
    RouteEmuList --> ListRemote --> EnsureConn
    ListRemote --> AdbShell --> ResolveName --> IdxLookupB
    IdxLookupB --> BuildIndex
    RouteEmuList --> ListLocal

    ExportBtn -->|"POST"| RouteExport --> ResolveKey
    RouteExport --> ExportFn
    DeleteBtn -->|"POST + confirm()"| RouteDelete --> ResolveKey
    RouteDelete --> DeleteFn
    ImportBtn -->|"POST base64"| RouteImport --> ResolveKey
    RouteImport -->|"tmp file write"| ImportFn
    TransferBtn -->|"POST"| RouteTransfer --> ResolveKey
    RouteTransfer --> TransferFn
    TransferFn --> ExportFn
    TransferFn --> ImportFn
    TransferFn --> DeleteFn

    PullBtn -->|"POST"| RoutePull --> PullFn
    PullFn --> EnsureConn
    PullFn --> AdbPull

    Lookup -.->|"unused by both callers - see duplication finding"| IdxLookupA
    Lookup -.->|"unused by both callers"| IdxLookupB
```

## External dependencies

- `ps1vmc-tool` / `ps2vmc-tool` binaries (bucanero/ps2vmc-tool) on PATH — `core/memcard.py:_run` (`:57`)
- `adb` binary on PATH — `core/adb.py:run` (`:53`), used by `core/emu_saves.py` (`shell`, `pull`, `ensure_connected`)
- Android device connected via USB (adb) for `emu_saves` list/pull
- redump DAT files fetched over HTTP from `raw.githubusercontent.com/libretro/libretro-database`
  (`serials.py:38-43`), cached at `cache/serials_index.json` (`serials.py:36`)
- Local filesystem: `config.toml [memcards]` card image files (PS1 `.mcd`/`.gme`, PS2 `.ps2`/`.bin`);
  export dir (default `~/Downloads`); mirrored `Saves/Dolphin/GC/...` and `Saves/PPSSPP/SAVEDATA/...`

## Duplication flagged (Phase 2 input)

Both `core/memcard.py` (lines 91-94, 108-111) and `core/emu_saves.py` (lines 76-81) independently
derive a serial/code from a raw name and do `serials_index.get(<console>,{}).get(<key>)` inline,
rather than calling the module-level `serials.lookup(console, raw_slot_name, index)` helper
(`serials.py:107-113`) that already exists for exactly this purpose. **`serials.lookup()` appears
unused by both consumer modules** — dead/parallel code — and the two backends reimplement its
body slightly differently (memcard.py normalizes via `normalize_slot_serial` first; emu_saves.py
uses its own `_gc_code`/`_psp_serial` regexes first).

## Confidence note and known gaps

High confidence: all five scoped files/route ranges read in full, subprocess/adb argument lists
captured verbatim. Gaps: `core/adb.py` not read in full (only relevant function signatures);
`gui/static/index.html` modal markup not read; `config.toml` itself not read. Error/fallback
branches (404 unknown card/emu, 400 empty item, 502 tool/adb failure, `android_ok=false`) noted
but not elaborated per scope instructions.

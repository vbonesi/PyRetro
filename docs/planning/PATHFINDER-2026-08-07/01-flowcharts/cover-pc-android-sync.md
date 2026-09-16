# Feature: Cover PC↔Android Sync

CLI-only two-way sync of cover art files between the PC's Google-Drive-synced
folder and the phone via adb, using a manifest file to detect conflicts.

## Sources consulted

- `core/sync.py` (189 lines, full read) — `scan_pair`, `sync_capas`, manifest handling against `cache/sync_state.json`
- `core/adb.py` (131 lines, full read) — `run`/`shell`/`push`/`pull`/`ensure_connected`, retry-on-reconnect logic
- `retrosync.py:314-348` — `sync` subcommand definition and `cmd_sync` handler

## Flowchart

```mermaid
flowchart TD
    CLI["CLI: retrosync.py sync covers --apply<br/>retrosync.py:346-348"] --> CMD["cmd_sync(args)<br/>retrosync.py:314-339"]
    CMD --> LOADCFG["load_config()<br/>retrosync.py:318"]
    LOADCFG --> CALLSYNC["sync_mod.sync_capas(cfg, dry_run=False)<br/>core/sync.py:120-189"]

    CALLSYNC --> CONNECT["adb_mod.ensure_connected(device_serial)<br/>core/adb.py:101-131"]
    CONNECT --> LISTDEV["list_devices() -> adb devices -l<br/>core/adb.py:86-98"]
    LISTDEV --> READYCHK{"ready device found?<br/>core/adb.py:108-119"}
    READYCHK -->|"no ready device"| RESTART1["_restart_server()<br/>kill-server + start-server + sleep(2)<br/>core/adb.py:41-44,117-118"]
    RESTART1 --> RELIST["list_devices() again<br/>core/adb.py:118-119"]
    RELIST --> READYCHK2{"ready now?<br/>core/adb.py:121"}
    READYCHK2 -->|"still none"| ERR_NONE["raise AdbError:<br/>'nenhum device adb conectado'<br/>core/adb.py:122-125"]
    READYCHK2 -->|"multiple, no serial cfg"| ERR_MULTI["raise AdbError:<br/>'mais de um device conectado'<br/>core/adb.py:126-130"]
    READYCHK -->|"configured serial not ready"| ERR_SERIAL["raise AdbError:<br/>device '&lt;serial&gt;' not ready<br/>core/adb.py:111-113"]
    ERR_NONE --> CATCH["except adb_mod.AdbError as e:<br/>sys.exit('erro de adb: ...')<br/>retrosync.py:324-325"]
    ERR_MULTI --> CATCH
    ERR_SERIAL --> CATCH
    READYCHK -->|"ready, single/matched"| SERIAL["serial resolved<br/>core/adb.py:114,131"]
    READYCHK2 -->|"exactly one ready"| SERIAL

    SERIAL --> LOADSTATE["load_state()<br/>read cache/sync_state.json<br/>core/sync.py:32-33,133-134"]
    LOADSTATE --> LOOP["for code, sysinfo in cfg['systems']<br/>skip if code in COVERS_EXCLUDED (SDC,PS)<br/>core/sync.py:138-140"]
    LOOP --> DIRCHK{"PC Named_Boxarts dir exists?<br/>core/sync.py:141-143"}
    DIRCHK -->|"no"| LOOP
    DIRCHK -->|"yes"| SCANPAIR["scan_pair(pc_dir, android_dir, prev_state, serial)<br/>core/sync.py:76-117,146"]

    SCANPAIR --> LOCALMT["_local_mtimes(pc_dir)<br/>Path.rglob + os.stat (no adb)<br/>core/sync.py:41-44,84"]
    SCANPAIR --> REMOTEMT["_remote_mtimes(android_dir, serial)<br/>core/sync.py:47-73,85"]
    REMOTEMT --> SHELLCALL["adb_mod.shell(<br/>find '&lt;dir&gt;' -type f -exec stat -c '%Y %n' {} \\;<br/>core/sync.py:56-59"]
    SHELLCALL --> RUNCALL["run(['shell','-n',cmd])<br/>core/adb.py:47-62,69"]
    RUNCALL --> OFFCHK{"returncode!=0 and<br/>output matches _OFFLINE_MARKERS?<br/>('device offline','no devices',<br/>'unauthorized','not found', etc)<br/>core/adb.py:12-16,58"}
    OFFCHK -->|"yes, attempts remain"| RESTART2["_restart_server()<br/>core/adb.py:60-61"]
    RESTART2 --> RUNCALL
    OFFCHK -->|"no / retries exhausted"| RETRESULT["return CompletedProcess<br/>core/adb.py:62"]
    RETRESULT --> RCCHK{"r.returncode != 0?<br/>core/adb.py:70"}
    RCCHK -->|"yes"| SHELLERR["raise AdbError('adb shell falhou: ...')<br/>core/adb.py:71"]
    SHELLERR --> CATCH
    RCCHK -->|"no"| PARSE["parse stdout into<br/>{relpath: mtime}<br/>core/sync.py:61-73"]

    LOCALMT --> CLASSIFY
    PARSE --> CLASSIFY["classify each relpath<br/>core/sync.py:87-116"]
    CLASSIFY --> ONESIDE{"present only<br/>on one side?"}
    ONESIDE -->|"PC only"| CTOA["copiar_pro_android<br/>core/sync.py:92-94"]
    ONESIDE -->|"Android only"| CTOPC["copiar_pra_pc<br/>core/sync.py:95-97"]
    ONESIDE -->|"both sides"| PREVCHK{"prior manifest<br/>entry exists?<br/>core/sync.py:99-103"}
    PREVCHK -->|"no baseline"| MTMATCH{"|local-remote|<=<br/>MTIME_EPSILON(2.0s)?"}
    MTMATCH -->|"yes"| NOCHANGE1["sem_mudanca<br/>core/sync.py:101"]
    MTMATCH -->|"no"| CONFLICT1["conflito<br/>core/sync.py:101"]
    PREVCHK -->|"yes"| CHANGECHK["compare vs baseline mtime_pc/mtime_android<br/>core/sync.py:105-106"]
    CHANGECHK --> BOTHCHK{"which side(s) changed?<br/>core/sync.py:108-115"}
    BOTHCHK -->|"neither"| NOCHANGE2["sem_mudanca<br/>core/sync.py:109"]
    BOTHCHK -->|"PC only"| CTOA
    BOTHCHK -->|"Android only"| CTOPC
    BOTHCHK -->|"both"| CONFLICT2["conflito<br/>core/sync.py:115"]

    CTOA --> PUSHLOOP["for relpath in copiar_pro_android:<br/>on_progress callback<br/>core/sync.py:153-166"]
    PUSHLOOP --> PUSH["adb_mod.push(local_path, remote_path, serial)<br/>-> adb push<br/>core/adb.py:75-77,161"]
    PUSH --> PUSHOK{"success?"}
    PUSHOK -->|"yes"| UPDST1["sys_state[relpath] =<br/>{mtime_pc, mtime_android}=local mtime<br/>core/sync.py:162-163"]
    PUSHOK -->|"no"| ERRLIST1["report['erros'].append<br/>'push falhou: code/relpath'<br/>core/sync.py:166"]

    CTOPC --> PULLLOOP["for relpath in copiar_pra_pc:<br/>on_progress callback<br/>core/sync.py:168-180"]
    PULLLOOP --> PULL["adb_mod.pull(remote_path, local_path, serial)<br/>-> adb pull (mkdir parents)<br/>core/adb.py:80-83,176"]
    PULL --> PULLOK{"success?"}
    PULLOK -->|"yes"| UPDST2["sys_state[relpath] =<br/>{mtime_pc: local stat, mtime_android: scan value}<br/>core/sync.py:177"]
    PULLOK -->|"no"| ERRLIST2["report['erros'].append<br/>'pull falhou: code/relpath'<br/>core/sync.py:180"]

    NOCHANGE1 --> REPORTNC["report['sem_mudanca'] += len(...)<br/>core/sync.py:150"]
    NOCHANGE2 --> REPORTNC
    CONFLICT1 --> REPORTCONF["report['conflitos'] +=<br/>['code/relpath', ...]<br/>(no copy, no state update)<br/>core/sync.py:151"]
    CONFLICT2 --> REPORTCONF

    UPDST1 --> REFRESHNC["refresh sem_mudanca baseline entries<br/>sys_state[relpath] updated too<br/>core/sync.py:182-184"]
    UPDST2 --> REFRESHNC
    REPORTNC --> REFRESHNC
    ERRLIST1 --> LOOP
    ERRLIST2 --> LOOP
    REFRESHNC --> LOOP
    REPORTCONF --> LOOP

    LOOP -->|"all systems processed"| SAVESTATE["save_state(state)<br/>write cache/sync_state.json<br/>core/sync.py:36-38,186-187"]
    SAVESTATE --> RETURNREPORT["return report dict<br/>core/sync.py:189"]
    RETURNREPORT --> PRINTOUT["print counters + conflitos + erros<br/>retrosync.py:327-337"]
    PRINTOUT --> DONE["done"]

    style CATCH fill:#f66,color:#000
    style SHELLERR fill:#f66,color:#000
    style ERR_NONE fill:#f66,color:#000
    style ERR_MULTI fill:#f66,color:#000
    style ERR_SERIAL fill:#f66,color:#000
    style REPORTCONF fill:#fc6,color:#000
    style ERRLIST1 fill:#fc6,color:#000
    style ERRLIST2 fill:#fc6,color:#000

    subgraph EXT["External dependencies"]
        ADBBIN["adb binary (subprocess)<br/>core/adb.py:8,53"]
        ANDROIDFS["Android filesystem<br/>thumbnails_root/&lt;system&gt;/Named_Boxarts<br/>via find/stat/push/pull"]
        PCFS["PC filesystem<br/>capas_root/&lt;system&gt;/Named_Boxarts<br/>Google-Drive-synced folder"]
        MANIFEST["cache/sync_state.json<br/>core/sync.py:24,32-38"]
        CFGTOML["config.toml [pc]/[android]/[systems]<br/>read via load_config()"]
    end
    SERIAL -.-> ADBBIN
    SHELLCALL -.-> ANDROIDFS
    PUSH -.-> ANDROIDFS
    PULL -.-> ANDROIDFS
    LOCALMT -.-> PCFS
    PUSH -.-> PCFS
    PULL -.-> PCFS
    LOADSTATE -.-> MANIFEST
    SAVESTATE -.-> MANIFEST
    LOADCFG -.-> CFGTOML
```

## External dependencies

- **`adb` binary** (external subprocess, `core/adb.py:8,53`) — every device interaction (`devices -l`, `shell`, `push`, `pull`) shells out to the system `adb` command; `core/adb.py` is shared infrastructure also used by Heavy ROM Management and Saves/Emu-saves — not traced here beyond noting the shared dependency.
- **Android filesystem** — `<thumbnails_root>/<system>/Named_Boxarts` on the phone, read via `find ... stat` (`core/sync.py:56-59`) and written/read via `adb push`/`adb pull` (`core/adb.py:75-83`).
- **PC filesystem** — `<capas_root>/<system>/Named_Boxarts`, the Google-Drive-synced folder; read via `Path.rglob`/`os.stat` (`core/sync.py:41-44`) and written via `adb pull`'s local target.
- **`cache/sync_state.json`** — sync manifest/baseline, read by `load_state()` and written by `save_state()` (`core/sync.py:24,32-38,133,186-187`).
- **`config.toml`** (`[pc]`, `[android]`, `[systems]`) — loaded via `load_config()` in `retrosync.py:318`.

## Confidence note and known gaps

High confidence — every node traces to a specific line range in the three fully-read files.

- `retrosync.py:319-320`: `scope="all"` also routes through `sync_capas` today (saves/states/metrics not implemented, would `sys.exit` before reaching adb) — `all` and `covers` currently behave identically.
- README's "device not found" bug (README.md:173-176) is confirmed **fixed** in current code: `core/adb.py:14` includes `"not found"` in `_OFFLINE_MARKERS`, with a comment citing the same incident.
- `load_config()` internals not read in full — only call sites and config keys consumed confirmed.
- `on_progress` callback (`core/sync.py:126-127,153-155,169-170`) exists as a hook parameter but `cmd_sync` (`retrosync.py:323`) doesn't pass it — effectively a no-op on the CLI path.

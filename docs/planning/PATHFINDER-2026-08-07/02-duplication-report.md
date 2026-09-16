# PyRetro — Duplication Report

Synthesized from two parallel Phase 2 subagents: a within-feature pass (each of the 7 features
checked against itself) and a cross-feature pass (concerns compared across feature boundaries).
Every claim below was independently verified by direct source reads or repo-wide grep — several
findings were reached independently by both agents, which is noted where it happens.

## Cross-cutting concerns (appear in 2+ features)

### 1. `serials.lookup()` exists, is correct, and is never called

**Locations:**
- `core/serials.py:107-113` — the helper: `serial = normalize_slot_serial(raw); return index.get(console,{}).get(serial)`
- `core/memcard.py:91,94` (PS1) and `:108,111` (PS2) — Saves & Memory Card feature — inlines the
  exact same two steps
- `core/emu_saves.py:76-81` — Saves & Memory Card feature, GC/PSP backend — inlines an
  equivalent lookup but derives the key via its own `_gc_code`/`_psp_serial` regexes instead of
  `normalize_slot_serial`
- Confirmed via repo-wide grep (both agents, independently): **zero** call sites of
  `serials.lookup(` anywhere in the codebase.

**Verdict:** Mostly accidental. The PS2 branch of `memcard.py` is an exact re-derivation of
`lookup()` with nothing extra — a trivial fix. The PS1 branch adds a `prod or ...` fallback
`lookup()` doesn't support, and `emu_saves.py` uses genuinely different regexes for GC/PSP name
formats — so `lookup()`'s signature is slightly too narrow to be a drop-in for all three callers
as currently written. This is really a **dead-code** finding (a helper nobody uses) sitting next
to a **duplication** finding (its body reimplemented twice, differently).

### 2. "adb find + parse remote listing" reimplemented 3x, with inconsistent quoting hygiene

**Locations:**
- `core/sync.py:47-73` (`_remote_mtimes`, Cover PC↔Android Sync) — builds
  `f"find '{android_dir}' -type f -exec stat -c '%Y %n' {{}} \;"` with **manual `'...'` quoting**
- `core/heavy_roms.py:90-109` (`list_remote_names`, Heavy ROM Management) — uses
  `adb_mod.shquote(remote_dir)`
- `core/emu_saves.py:98-104` (`list_remote`, Saves & Memory Card) — uses `adb_mod.shquote(...)`

All three shell out to `adb shell find`, then strip a known prefix off each output line to
compute a relative path — the same idiom, three separate implementations.

**Verdict:** Legitimate specialization at the "what to do with the result" level (mtime-diffing
vs. existence-set vs. display-name-resolved items are genuinely different shapes) but **accidental
duplication at the "shell out and parse" level**. The strongest evidence this is accidental
rather than deliberate: `core/adb.py:23-31`'s own docstring mandates
*"todo código novo que monta comando de `adb shell` como string deve usar [`shquote`]"* — and
`core/sync.py:57` doesn't follow that convention, while the other two (written later) do. A
shared `adb_mod.find(dir, predicate="") -> list[str]` primitive would let each caller post-process
differently while fixing the quoting inconsistency in `sync.py` as a side effect.

### 3. "fetch bytes → normalize to real PNG" duplicated 4-5x

**Locations:**
- `core/covers.py:310-317` (curl→`.tmp`) + `:384,423` (`convert`) — primary download and the
  standalone `convert-covers`/`validate-covers` commands
- `core/launchbox.py:194-195,202` — fallback source #2
- `core/screenscraper.py:145-157,167-169` (`fetch_media_bytes`, urllib not curl) — fallback source #3
- `gui/server.py:121-164` (`download_selected_cover`, Cover Gallery Curation's manual-search-select
  path) — curl→`.tmp`→`convert`, and also reaches directly into `covers_mod._download_via_api()` /
  `covers_mod.RateLimited` (underscore-prefixed internals of another module)
- `gui/server.py:833-846` (upload handler, Cover Gallery Curation) — base64-decode→`.tmp`→`convert`

Within `core/covers.py` itself, the same "curl to tmp, check HTTP 200 & size>1000, fall back to
GitHub Contents API" sequence is *also* duplicated between `process_system` (`:310-332`) and
`gui/server.py`'s `download_selected_cover` (`:142-156`) — the GUI code reimplements
`process_system`'s fallback chain rather than calling into it, importing private (`_`-prefixed)
symbols to do so.

**Verdict:** The *fetch* half legitimately differs per source (different URLs, auth, GitHub
Contents-API fallback only makes sense for the libretro-thumbnails source). The *normalize* half
— write bytes to `.tmp`, run `convert src dst`, verify size, clean up — is byte-for-byte the same
idiom copied four to five times, each with its own inline comment re-explaining the same lesson
("`convert` detecta o formato pelo conteúdo, não pelo nome"). Within `core/covers.py`,
`validate_png_content` additionally repeats its own "read 8 bytes, compare to `PNG_MAGIC`" check
twice in the same function (`:416-418` and `:425-426`). Strong, low-risk unification candidate.

### 4. "Never overwrite existing destination" guard reimplemented 5+ times

**Locations (mechanism noted):**
- `gui/server.py:748-750` (Cover Gallery Curation, cover-rename) — local `Path.exists()`
- `core/organize.py:67-68` (ROM Organize/Staging, `move_to_system`) — local `Path.exists()`
- `core/sanitize.py:51-53` (Support Utilities, `scan_and_rename`) — local `Path.exists()`
- `core/rom_rename.py:125-126,138-139,157-158` (shared cascade engine, used by both Cover Gallery
  Curation and Heavy ROM Management) — three more local `Path.exists()` checks
- `core/heavy_roms.py:125-131` (Heavy ROM Management, `send_to_phone`, PC→phone) — **remote**
  check via `adb shell "[ -e <remote_path> ] && echo EXISTS"`, skippable via `overwrite=True`
- `core/heavy_roms.py:202-204` (Heavy ROM Management, `download_from_drive`, Drive→PC) — local
  `Path.exists()`, **no overwrite override exists at all** for this direction — asymmetric with
  `send_to_phone`

**Verdict:** Correctly divergent at the local-vs-remote transport boundary (the one adb-based
check can't share code with the five local ones). But the **five local `Path.exists()` guards**
are the identical one-liner reimplemented rather than factored — low value to unify by itself, but
it enables a real inconsistency: whether "force an overwrite" is even possible differs per
feature with no single source of truth (`send_to_phone` supports it, `download_from_drive`
doesn't, cover-rename and `move_to_system` don't either).

### 5. `sanitize_name()` reused inline in two GUI routes, three different conflict mechanisms

**Locations:**
- `core/sanitize.py:26-29` (`sanitize_name`) + `:36-59` (`scan_and_rename`, the only complete,
  conflict-safe caller chain — Support Utilities, `retrosync.py:294`)
- `gui/server.py:735` (Cover Gallery Curation, `POST /api/cover/rename`) — bare `sanitize_name()`
  call, then its **own** ad-hoc conflict check at `:748-750` (`dest.exists()` → 409)
- `gui/server.py:955` (Heavy ROM Management, `POST /api/heavy/rename`) — bare `sanitize_name()`
  call, then delegates conflict detection to `rom_rename_mod.rename_with_cascade`'s status codes
  (`:965-972`) — a **third**, structurally different conflict-handling mechanism

**Verdict:** `scan_and_rename` is a *batch* directory scanner — not a drop-in for "sanitize this
one user-typed string and rename this one specific item," so the GUI routes' non-reuse of
`scan_and_rename` itself is justified. But three different mechanisms answering the same
"did sanitizing collide with something" question, none of them calling `needs_sanitizing()`
either, is the concrete duplicated concern. This is a three-feature intersection (Support
Utilities × Cover Gallery Curation × Heavy ROM Management).

### 6. Async job + SSE plumbing: one shared stream endpoint, but job-launch code tripled

**Locations:**
- `gui/server.py:644-663` — `GET /api/fetch/stream` is the **only** SSE route in the file
  (confirmed by grep) — correctly generic, drains whichever `queue.Queue` is registered under
  `job_id` in the shared `_jobs` dict regardless of job type. **No unification needed here.**
- Job-launch boilerplate duplicated 3x (identical 5-line shape: build `job_id` string with a
  hand-typed prefix, `queue.Queue()`, lock+store in `_jobs`, spawn thread, return `{"job": job_id}`):
  `gui/server.py:888-895` (cover fetch, prefix `""`), `:919-926` (heavy send, prefix `"heavy-"`),
  `:934-941` (heavy download, prefix `"heavydl-"`) — the inconsistent hand-typed prefixes are
  themselves a symptom of copy-paste.
- `emit()` closure duplicated 3x, identical body `def emit(event): q.put(event)`, each wrapped in
  an identical `try/except Exception → emit error / finally → emit job_done`:
  `run_fetch_job` (`:203-204`), `run_heavy_send_job` (`:269-270`), `run_heavy_download_job`
  (`:308-309`).

**Verdict:** Accidental duplication of infrastructure around a correctly-shared consumption
endpoint. The three job *bodies* legitimately differ (cover matching loop vs. one adb push vs.
one rclone copy) and shouldn't be merged, but the "register a job, get a queue, spawn a thread"
scaffolding and the `emit`/error/done wrapper are copy-pasted at every call site. Cleanest
unification candidate of the six cross-cutting findings — a `_start_job(prefix, target, args)`
helper plus a `run_job(fn)` decorator/wrapper would collapse all six sites with no behavior change.

## Within-feature findings

### Cover Acquisition Pipeline
- **A1** — `load_tree` (`core/covers.py:84-90`) and `load_romname_dat` (`:137-142`): identical
  "download to cache file if missing" block, differing only in path/URL. Trivial, safe fix.
- **A2** — `convert_jpg_to_png` (`:384-390`) and `validate_png_content` (`:423-429`) share a
  "run convert, check size, record status" shape; legitimately different pre/post-checks, low
  priority to merge. The PNG-magic-byte check inside `validate_png_content` is duplicated within
  itself (`:416-418`, `:425-426`) — a tiny `_is_real_png()` helper would fix that part cleanly.
- **A3** — overlaps with cross-cutting Finding 3 above (`process_system` vs `download_selected_cover`).

### Cover Gallery Curation
- **B1** — `_rename_rom` (`core/rom_rename.py:101-120`) and `_delete_rom` (`:182-197`): identical
  single-item match block (stem+ext, directory fallback, 0/ambiguous/1 branch). Clean win to
  extract `_find_single_match()`.
- **B2** — `_rename_flat_matches` (`:148-153`) reimplements `find_flat_matches` (`:219-222`)
  instead of calling it, unlike `delete_flat_matches` which correctly reuses `find_flat_matches`.
  Zero-risk fix: make rename follow the same pattern as delete.
- **B3** — **strongest single finding in the review**: `flag`/`unflag`/`duplicate`/`unduplicate`
  route handlers (`gui/server.py:682-687, 689-700, 703-708, 710-718`) are near-verbatim; `unflag`
  and `unduplicate` are **100% identical, no line differs**. Collapses 4 handlers (38 lines) into
  ~10 with a tiny status-literal dispatch table.
- **B4** — rename and delete handlers repeat an identical 3-line "load config + resolve
  roms/saves/states roots" block (`gui/server.py:754-757` vs `:787-790`); the same block recurs
  twice more in Heavy ROM Management (see D2) — 4 occurrences total across the file.
- **B5** — cover-file-lookup-by-extension appears in the rename handler (find-first,
  `gui/server.py:739-744`) and `delete_with_cascade`'s cover step (delete-all,
  `core/rom_rename.py:242-247`); different enough intent (first-match vs exhaustive) that this is
  a low-priority judgment call, not a clear win.

### Cover PC↔Android Sync
- **C1** — the push loop and pull loop in `sync_capas` (`core/sync.py:153-166` vs `:168-180`) are
  structurally identical ~13-line blocks, **but** contain an intentional asymmetry: post-push, the
  Android mtime is assumed equal to the local mtime just read; post-pull, it's taken from the
  value already captured during `scan_pair`. This reflects the module's "mais recente vence"
  correctness rule, not sloppiness. Consolidating is worth doing but must preserve this asymmetry
  exactly — flagged as higher-risk than the others in this report.

### Heavy ROM Management
- **D1** — `run_heavy_send_job` and `run_heavy_download_job` (`gui/server.py:262-278,296-299` vs
  `:302-316,322-325`) share a near-identical job-runner skeleton (queue/emit setup,
  try/except/finally, config+system lookup, progress→action→done). Overlaps with cross-cutting
  Finding 6 — same root cause, feature-local half of it.
- **D2** — overlaps with B4 above (identical "resolve roots" block at `gui/server.py:959-961` and
  `:987-989`).
- Examined and **rejected** as a finding: `send_to_phone`'s adb-based overwrite check vs
  `download_from_drive`'s local-filesystem overwrite check — different resource types, correctly
  not sharing code (see cross-cutting Finding 4 for the full picture).

### ROM Organize/Staging
- **E1** — `build_ext_index`'s two loops over `systems_cfg` and `heavy_systems_cfg`
  (`core/organize.py:25-29` vs `:30-34`) are structurally identical, differing only in the source
  dict, the display-name key (`"capas"` vs `"nome"`), and the `"kind"` literal. Only meaningful
  finding in this small (71-line) feature — cleanly parameterizable.

### Saves & Memory Card
- **F1** — `import_save`'s PS1 and PS2 branches (`core/memcard.py:164-170` vs `:175-181`) end
  with an identical `try/except MemcardError` "sem espaço" wrapper, differing only in the
  `_run()` argument list. Clean, low-risk fix.
- **F2** — same as cross-cutting Finding 1 (dead `serials.lookup()`), reached independently by
  both Phase 2 agents.
- **F3** — `/api/memcards/export` and `/api/memcards/delete` (`gui/server.py:996-1002` vs
  `:1012-1018`) share an identical 7-line request-guard prologue (parse body → resolve via
  `_memcard_path` → 400/404 checks); `transfer` repeats the same idiom twice more. ~14+ lines
  removable via a `_resolve_card_and_item()` helper.
- Examined and **rejected** as a finding: `list_card`'s PS1 vs PS2 row-parsing looks similar
  (same final dict shape) but the actual parsing differs by necessity (fixed-format regex vs
  pipe-split columns, because the underlying tool output formats genuinely differ).

### Support Utilities
- **G1** — the NFKD/ASCII-fold/lowercase normalization expression is duplicated within
  `search_library` itself (`gui/server.py:437` and `:459`), applied to the query and the haystack
  respectively. A 4-method call chain repeated verbatim — small but unambiguous, worth a local
  `_fold()` helper.
- The cross-feature `sanitize_name()` reuse (cross-cutting Finding 5) was originally surfaced
  here by Phase 1 and is not re-litigated as a separate within-feature finding.

## Deliberately rejected "duplications" (legitimate specialization)

- `send_to_phone` (adb-based) vs `download_from_drive` (local-filesystem) overwrite guards —
  different trust/transport models, cannot share code.
- `memcard.py`'s PS1 vs PS2 row-parsing — different underlying tool output formats (fixed-width
  regex vs pipe-delimited), only the final dict shape is shared, too small to abstract.
- The three "enumerate PC vs remote" call sites (sync.py, heavy_roms.py, emu_saves.py) — correct
  not to share a single *high-level* function (mtime-diffing vs existence-set vs
  name-resolution are different jobs), even though the low-level shell-and-parse step is
  duplicated (see cross-cutting Finding 2).

## Confidence and gaps

Both Phase 2 agents read every file directly (not relying solely on Phase 1 flowchart citations)
and cross-verified via repo-wide grep where relevant (`serials.lookup()` usage, `shquote()`
usage, `sanitize_name` call sites). The two agents reached Finding 1 / F2 (dead `serials.lookup()`)
completely independently, which is strong corroboration.

Known gaps, carried forward from both subagent reports:
- `core/cues.py` internals not read by either agent — treated as an opaque external dependency
  throughout (matches Phase 1's treatment).
- `gui/static/app.js` not re-examined for duplication in this phase — any client-side repetition
  (e.g. across `renameCover`/`deleteCover`/`uploadCover`'s fetch+alert patterns) is unassessed.
- `config.toml` itself not read by either agent — config-key names are taken from code
  references only, consistent with every Phase 1 flowchart.
- The `core/covers.py` / `core/launchbox.py` / `core/screenscraper.py` *download-cover* functions
  were compared to each other only at the cross-feature level (Finding 3), not internally
  re-diffed line-by-line beyond what's reported there.

# PyRetro — Handoff Prompts

Ten ready-to-run `/make-plan` prompts, one per unified component proposed in
[`03-unified-proposal.md`](03-unified-proposal.md). Each cites exact call sites from
[`02-duplication-report.md`](02-duplication-report.md) and the relevant flowchart in
[`01-flowcharts/`](01-flowcharts/). Copy any block below directly into `/make-plan`.

Grouped into three batches by risk/independence — safe to run in any order within a batch, but
batch 1 touches no shared state and is the best starting point.

---

## Batch 1 — pure extractions, zero behavior risk

### 1. `finalize_as_png` — cover normalization

```
Extract a shared `finalize_as_png(tmp_path: Path, dest_path: Path) -> bool` helper in
core/covers.py (or a new core/png_fetch.py) that does: run `convert <tmp> <dest>` via
subprocess, check returncode==0 and dest.exists() and dest.stat().st_size > 1000, unlink tmp,
return the bool.

Rewrite these 5 call sites to use it, changing nothing about their fetch logic (only the
write-tmp-then-convert-then-verify tail):
- core/covers.py:384-390 (convert_jpg_to_png)
- core/covers.py:423-429 (validate_png_content, in-place repair branch)
- core/launchbox.py:194-204 (download_cover)
- core/screenscraper.py:160-171 (download_cover)
- gui/server.py:142-164 (download_selected_cover) and gui/server.py:833-846 (upload handler)

Also: gui/server.py currently imports covers_mod._download_via_api and covers_mod.RateLimited
(underscore-prefixed internals) at gui/server.py:151. Export these two names properly from
core/covers.py's public surface (rename without the leading underscore, or add explicit
re-exports) instead of reaching into "private" symbols across module boundaries.

See PATHFINDER-2026-08-07/01-flowcharts/cover-acquisition-pipeline.md and
cover-gallery-curation.md for full context on how each call site is reached.

Anti-pattern guards: do not add a config flag for "skip conversion" or any speculative
parameter — every current caller always converts. Do not turn this into a class or introduce
a registry of "normalizers" — one function is sufficient.
```

### 2. `_fetch_cached_bytes` — generic download-to-cache

```
Extract a shared `_fetch_cached_bytes(cache_path: Path, url: str) -> None` helper in
core/covers.py that does: if cache_path exists, return; else mkdir parents, GET the url via
urllib.request with a "PyRetro" User-Agent and 30s timeout, write bytes to cache_path.

Rewrite these two call sites, which currently duplicate this exact block, to call it:
- core/covers.py:84-90 (load_tree)
- core/covers.py:137-142 (load_romname_dat)

Both functions should keep reading from cache_path after the call exactly as they do today —
this is a pure extraction with no behavior change.

See PATHFINDER-2026-08-07/01-flowcharts/cover-acquisition-pipeline.md for the surrounding
match/download flow these two functions feed into.
```

### 3. `_resolve_roots` — config path resolution

```
Extract a shared `_resolve_roots(cfg) -> tuple[Path, Path, Path]` helper (returning
roms_root, saves_dir, states_dir, all expanduser()'d) in gui/server.py.

Rewrite these 4 call sites, which currently repeat the identical 3-line resolution, to use it:
- gui/server.py:754-757 (POST /api/cover/rename handler)
- gui/server.py:787-790 (POST /api/cover/delete handler)
- gui/server.py:959-961 (POST /api/heavy/rename handler)
- gui/server.py:987-989 (POST /api/heavy/delete handler)

See PATHFINDER-2026-08-07/01-flowcharts/cover-gallery-curation.md and
heavy-rom-management.md for the handlers this feeds into (both call into
core/rom_rename.py's rename_with_cascade/delete_with_cascade right after this resolution).

Anti-pattern guard: this is a config-reading helper, not a config-caching layer — call
load_config() as before at each site, only the post-processing of cfg["pc"] is shared.
```

### 4. `_find_single_match` + fix `_rename_flat_matches` — core/rom_rename.py

```
Two related fixes in core/rom_rename.py, both pure refactors with no behavior change:

(1) Extract `_find_single_match(roms_dir: Path, label: str, exts_lower: set[str]) -> list[Path]`
from the identical single-item-match block duplicated in:
- core/rom_rename.py:101-120 (inside _rename_rom, called AFTER the disc-group check at
  lines 105-107 — keep that check outside the new helper, it's rename-only by design)
- core/rom_rename.py:182-197 (inside _delete_rom, which never does disc-group matching — keep
  it that way, delete deliberately never groups multi-disc titles per the module docstring at
  lines 35-41)

(2) Fix core/rom_rename.py:148-153 (_rename_flat_matches) to call the existing
find_flat_matches() (core/rom_rename.py:219-222) instead of re-implementing its filter logic
inline. delete_flat_matches (core/rom_rename.py:226) already does this correctly — make
_rename_flat_matches follow the same pattern.

See PATHFINDER-2026-08-07/01-flowcharts/cover-gallery-curation.md for the full rename/delete
cascade trace, including the two-pass disc-group dry-run/apply logic that must be preserved
exactly (core/rom_rename.py:79-97).

Anti-pattern guard: do not merge _rename_rom and _delete_rom themselves — their surrounding
logic (disc-group handling, single vs. exhaustive downstream actions) is intentionally
different. Only the single-item match-finding block is shared.
```

### 5. `_set_status`/`_clear_status` — registry flag dispatch

```
Replace 4 near-identical POST handlers in gui/server.py with a 2-entry status-literal dict and
two small methods:

_REGISTRY_STATUS = {"flag": "flagged_wrong", "duplicate": "duplicate"}

def _set_status(self, action, code, label): load_registry() -> set entry -> save_registry()
def _clear_status(self, code, label): load_registry() -> pop entry -> save_registry()

Rewrite:
- gui/server.py:682-687 (POST /api/cover/flag) -> self._set_status("flag", code, label)
- gui/server.py:703-708 (POST /api/cover/duplicate) -> self._set_status("duplicate", code, label)
- gui/server.py:689-700 (POST /api/cover/unflag) -> self._clear_status(code, label)
- gui/server.py:710-718 (POST /api/cover/unduplicate) -> self._clear_status(code, label)

Note: unflag and unduplicate are currently 100% byte-identical (verified in
PATHFINDER-2026-08-07/02-duplication-report.md, Finding B3) — this is the single highest-
confidence duplication in the whole review, safe to consolidate with no ambiguity.

See PATHFINDER-2026-08-07/01-flowcharts/cover-gallery-curation.md for how these fit alongside
the rename/delete/upload handlers in the same route group.

Anti-pattern guard: this is a 2-entry literal dict, not a general "action registry" — do not
generalize it to also cover rename/delete/upload, which have real per-action logic beyond a
status-literal swap.
```

### 6. Small local fixes (organize.py, search_library, memcard.py import, memcard routes)

```
Four independent, same-file, low-risk refactors — each is small enough to do in one pass:

(1) core/organize.py build_ext_index (lines 25-29 vs 30-34): replace the two near-identical
loops over systems_cfg and heavy_systems_cfg with one loop over
[(systems_cfg, "capas", "leve"), (heavy_systems_cfg, "nome", "pesado")].

(2) gui/server.py search_library handler (do_GET, ~lines 425-463): the NFKD/ASCII-fold/
lowercase chain `unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode().lower()`
appears identically at line 437 (for the query) and line 459 (for the haystack) inside the
same function. Extract a local `_fold(s)` closure and call it in both places.

(3) core/memcard.py import_save (lines 149-181): the PS1 branch (164-170) and PS2 branch
(175-181) both end with an identical try/except MemcardError wrapper that rewrites the error
message to mention "provavelmente não há espaço livre suficiente no card". Compute
(valid_exts, run_args) per console up front, then wrap a single _run() call in one
try/except instead of duplicating the wrapper.

(4) gui/server.py memcards routes: extract
_resolve_card_and_item(body) -> (path, console, item) | error_response from the identical
7-line prologue (parse body -> _memcard_path(key) -> 400/404 checks) shared by:
- gui/server.py:996-1002 (POST /api/memcards/export)
- gui/server.py:1012-1018 (POST /api/memcards/delete)
- gui/server.py:1053-1060 (POST /api/memcards/transfer, called twice — once per card key)

See PATHFINDER-2026-08-07/01-flowcharts/rom-organize-staging.md and saves-memory-card.md for
context on each.

Anti-pattern guard: keep these four as four separate small diffs in the same files — do not
invent a shared "request validation framework" across gui/server.py's route handlers; the
codebase's existing pattern (explicit checks per handler) is intentional and stdlib-only.
```

---

## Batch 2 — shared infrastructure, moderate scope

### 7. `adb_mod.find()` — shared remote-listing primitive

```
Add `find(remote_dir: str, predicate: str = "", serial: str | None = None) -> list[str]` to
core/adb.py: builds `find {shquote(remote_dir)} {predicate}`, runs it via the existing shell()
wrapper, returns non-empty stdout lines.

Rewrite these callers to use it for the shell-and-split step, keeping their own
post-processing (set-building, dict-building, or mtime-parsing) unchanged:
- core/heavy_roms.py:90-109 (list_remote_names) -> adb_mod.find(dir, "-mindepth 1 -maxdepth 1")
- core/emu_saves.py:98-104 (list_remote) -> adb_mod.find(dir, f"-name {shquote(glob)}") or
  "-type d" depending on the emulator's config
- core/sync.py:47-73 (_remote_mtimes) -> this one needs `stat -c '%Y %n'` output, not just
  paths, so it can't use find() as-is directly for its full command, BUT it currently builds
  its find command with manual `'...'` string quoting instead of adb_mod.shquote() (verified:
  core/sync.py:57 is the only adb-shell-command-building site in the repo not following
  core/adb.py's own documented convention at core/adb.py:23-31, which says all new code
  building an adb shell command as a string must use shquote()). Fix core/sync.py:57 to use
  adb_mod.shquote() for the directory argument even if the full find() helper isn't reused
  verbatim here.

See PATHFINDER-2026-08-07/01-flowcharts/heavy-rom-management.md,
saves-memory-card.md, and cover-pc-android-sync.md for the three call sites' full context.
PATHFINDER-2026-08-07/02-duplication-report.md Cross-cutting Finding 2 has the full comparison.

Anti-pattern guard: do NOT try to make one function return mtimes-or-names-or-dicts via a mode
flag — that's exactly the "configurable paths instead of one path" anti-pattern. find() returns
raw path strings; each caller's own post-processing (which differs for real reasons) stays
separate and unchanged.
```

### 8. `_start_job` + `run_job` — async job/SSE plumbing

```
In gui/server.py, add two small pieces of shared job infrastructure:

def _start_job(prefix: str, target, *args) -> str:
    # build job_id, create queue.Queue, store in _jobs under lock, spawn daemon thread, return job_id

def run_job(q: queue.Queue, body):
    # def emit(event): q.put(event)
    # try: body(emit) except Exception as e: emit({"type":"error","message":str(e)})
    # finally: emit({"type":"job_done"})

Rewrite the three job-launch POST handlers to call _start_job with a clear, consistent prefix
(currently these use inconsistent hand-typed prefixes "", "heavy-", "heavydl-" — pick
consistent ones like "fetch-", "heavy-send-", "heavy-dl-"):
- gui/server.py:888-895 (POST /api/fetch/<code>)
- gui/server.py:919-926 (POST /api/heavy/send)
- gui/server.py:934-941 (POST /api/heavy/download)

Rewrite the three job-runner functions to be a small body(emit) closure passed to run_job(),
keeping only their domain-specific logic:
- run_fetch_job (gui/server.py:197-259) — keep the cover matching/download loop, drop the
  duplicated emit/try/except/finally scaffolding
- run_heavy_send_job (gui/server.py:262-299) — keep the adb ensure_connected + send_to_phone
  call, drop the duplicated scaffolding
- run_heavy_download_job (gui/server.py:302-325) — keep the download_from_drive call, drop
  the duplicated scaffolding

Do NOT change GET /api/fetch/stream (gui/server.py:644-663) — it is already correctly generic
(the only SSE route in the file, works for all job types via the shared _jobs dict lookup by
job_id) and needs no modification.

See PATHFINDER-2026-08-07/01-flowcharts/cover-acquisition-pipeline.md and
heavy-rom-management.md for the full job-launch-to-completion trace of each of the three job
types. PATHFINDER-2026-08-07/02-duplication-report.md Cross-cutting Finding 6 has the full
before/after line citations.

Anti-pattern guard: do not build a generic "job type registry" or plugin system — three call
sites with three explicit body closures is simpler and sufficient; a registry would be the
"factory when a switch suffices" anti-pattern.
```

---

## Batch 3 — touches a shared helper's public contract, needs care

### 9. `sanitize_or_conflict` — unify the sanitize-then-check-collision step

```
Add `sanitize_or_conflict(name: str, exists_check) -> tuple[str, bool]` to core/sanitize.py:
calls sanitize_name(name), then calls exists_check(new_name) to determine collision, returns
both.

Rewrite gui/server.py:735,748-750 (POST /api/cover/rename handler) to call:
new_label, conflict = sanitize_mod.sanitize_or_conflict(
    new_label_raw, lambda n: (capas_dir / n).exists()
)
if conflict: return self._json({"error": "..."}, 409)  # same 409 behavior as today

For gui/server.py:955 (POST /api/heavy/rename handler): this one is DIFFERENT and should only
partially adopt the new helper. Its real conflict detection comes from
rom_rename_mod.rename_with_cascade's own multi-file status codes (gui/server.py:965-972),
not a single-path exists() check — that's checking a fundamentally different thing (a whole
ROM+save+state cascade, not one cover file). Only replace the bare sanitize_name() call with
sanitize_or_conflict(new_label_raw, lambda n: False) if you want a consistent call shape, OR
leave gui/server.py:955 calling sanitize_name() directly if that reads more honestly — do not
force the cascade's status-code conflict detection through the exists_check callback shape,
that would be misrepresenting what it actually checks.

core/sanitize.py's own scan_and_rename (lines 36-59) is the one caller that was already
correct (batch scan with its own conflict handling) — leave it as-is or optionally have its
inner loop call the new helper per-file, but this is low priority since it's not duplicated,
it's the reference implementation the other two should have been closer to.

See PATHFINDER-2026-08-07/01-flowcharts/support-utilities.md and cover-gallery-curation.md
for the full three-way comparison. PATHFINDER-2026-08-07/02-duplication-report.md
Cross-cutting Finding 5 explains why full unification of all three conflict mechanisms isn't
possible (two are genuinely the same concept, one is structurally different by necessity).

Anti-pattern guard: do not try to force heavy-rename's cascade-based conflict detection into
the same exists_check(name)->bool shape used by cover-rename — that would hide real
information (which of ROM/save/state conflicted) behind a boolean, a loss of capability the
report explicitly flags as unacceptable.
```

### 10. `serials.lookup()` — widen signature, wire up both real callers, delete the dead path

```
core/serials.py:107-113 defines a lookup(console, raw_slot_name, index) helper that is
currently called by NOTHING in the codebase (confirmed via repo-wide grep by two independent
Phase 2 review agents) — both real consumers reimplement its body instead.

Widen the signature to support both consumers' needs:

def lookup(console: str, index: dict, *, raw: str | None = None, key: str | None = None):
    resolved_key = key if key is not None else normalize_slot_serial(raw)
    return index.get(console, {}).get(resolved_key)

Rewrite:
- core/memcard.py:91,94 (PS1 branch of list_card) -> 
  name = serials_mod.lookup("PS1", serials_index, raw=raw_name)
  (if the existing `prod or normalize_slot_serial(raw_name)` fallback logic is needed, pass
  key=prod when prod is truthy, else raw=raw_name — preserve this exact fallback, it's real
  behavior, not incidental)
- core/memcard.py:108,111 (PS2 branch) -> 
  name = serials_mod.lookup("PS2", serials_index, raw=raw_name)
  (no prod fallback needed here — exact drop-in replacement)
- core/emu_saves.py:76-81 (_resolve_name) -> keep the existing _gc_code()/_psp_serial() regex
  extraction (these are genuinely different raw-name formats from memcard.py's, cannot be
  replaced by normalize_slot_serial), then call
  serials_mod.lookup(emu, serials_index, key=code) instead of the inline
  serials_index.get(emu, {}).get(code)

See PATHFINDER-2026-08-07/01-flowcharts/saves-memory-card.md for the full trace of both
consumers (memcard.py's PS1/PS2 card editor and emu_saves.py's GC/PSP backup, sharing one GUI
modal but different backends). PATHFINDER-2026-08-07/02-duplication-report.md Cross-cutting
Finding 1 has the full before/after and explains why this was reached independently by two
separate review passes (strong signal it's a real, non-speculative finding).

Anti-pattern guard: do not add a third "auto-detect raw vs key" mode — the caller always knows
which one it has (memcard.py has a raw name it may need to normalize; emu_saves.py already has
a resolved key from its own regex). Keyword-only raw= and key= make the caller's intent
explicit rather than guessed.
```

---

## Sequencing note

Batches 1 and 2 have no interdependencies and can be assigned to separate `/make-plan` +
`/do` runs in parallel. Batch 3's two items should land after Batch 1 (item 6's memcard fixes
overlap file regions with item 10's memcard.py changes — do item 6 first, or combine them into
one plan for core/memcard.py to avoid merge friction) and are lower urgency since they touch
call sites with existing test coverage per the project's own status table
([`README.md`](../README.md) — memcard.py and emu_saves.py are both marked "implementado e
testado contra o aparelho/cartões reais").

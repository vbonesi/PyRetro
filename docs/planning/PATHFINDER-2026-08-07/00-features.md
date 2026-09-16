# PyRetro — Feature Inventory

Source: full read of `retrosync.py` (426/426 lines) and `gui/server.py`
(1104/1104 lines) by the Phase 0 discovery agent — every argparse
subcommand and every `do_GET`/`do_POST` route branch enumerated, plus a
full function/`fetch(` grep of `gui/static/app.js` (1172 lines).

Two entry points feed every feature: the CLI (`retrosync.py`, stdlib
`argparse`) and the local GUI (`gui/server.py`, stdlib `http.server`,
serving `gui/static/*`). Business logic lives in `core/*.py`; the CLI
and GUI are both thin dispatchers onto the same core modules.

## Feature groups (used for Phase 1 fan-out)

| # | Feature | Entry points | Core files | Purpose |
|---|---|---|---|---|
| 1 | **Cover acquisition & repair pipeline** | CLI `fetch-covers` retrosync.py:350-352, `fetch-covers-fallback` :354-363, `convert-covers` :365-367, `validate-covers` :369-374; GUI `POST /api/fetch/<code>` server.py:881-895, `run_fetch_job` :197-259, `/api/cover/search,select,ss_preview` :526-555,855-879 | core/covers.py, core/launchbox.py, core/screenscraper.py | Find/download box-art from libretro-thumbnails → LaunchBox → ScreenScraper (fallback chain), then force-normalize to real PNG bytes. |
| 2 | **Cover gallery curation** | GUI only: `/api/cover/flag,unflag,duplicate,unduplicate,rename,delete,delete_save,upload` server.py:681-853; app.js:177-341 | core/rom_rename.py, core/sanitize.py | Per-cover human curation UI — flag wrong match, mark duplicate, rename/delete a game (cascading), upload manual art. |
| 3 | **Cascade rename/delete engine** | Invoked by #2 and #5, not directly exposed as its own route | core/rom_rename.py (`rename_with_cascade` L164, `delete_with_cascade` L232, multi-disc grouping L51-98) | Shared engine keeping ROM+cover+save/state filenames in lockstep on rename/delete. |
| 4 | **Cover PC↔Android sync** | CLI `sync` retrosync.py:346-348 (only `covers` scope live) | core/sync.py, core/adb.py | Two-way cover sync between Drive folder and phone, manifest/mtime diff, conflicts never auto-resolved. |
| 5 | **Heavy ROM management** | CLI `heavy-roms` retrosync.py:381-388; GUI `/api/heavy/*` server.py:565-601,912-993; app.js:567-761 | core/heavy_roms.py, core/adb.py, core/rom_rename.py | On-demand transfer of large-console ROMs (PS/SDC/PS2/GC/Wii/PSP/3DS) between Drive (rclone), PC, and phone. |
| 6 | **ROM organize/staging** | CLI `organize` retrosync.py:376-379 (list-only); GUI `/api/organize/pending,move` server.py:557-563,897-910; app.js:763-850 | core/organize.py | Classify files dropped in `0-Organizar/` into the correct system folder by extension, GUI resolves ambiguity. |
| 7 | **Saves & memory card management** | GUI only, shared "💾 Saves" modal: `/api/memcards/*` server.py:603-625,995-1069, `/api/emu_saves/*` :627-642,1071-1083; app.js:852-1151 | core/memcard.py, core/emu_saves.py, core/serials.py, core/adb.py | Two backend systems on one UI surface: PS1/PS2 memory-card editor (ps1vmc-tool/ps2vmc-tool) and Dolphin/PPSSPP per-game save pull via adb. Both resolve display names via redump serial DAT. |
| 8 | **Support utilities** (sanitize, settings, global search) | CLI `sanitize-names` retrosync.py:390-392; GUI `/api/settings` server.py:522-524,673-679, `/api/search_library` :425-463; app.js:359-417,27-79 | core/sanitize.py | Cross-cutting small features: strip RetroArch-illegal filename chars (also called inline from #2/#5 rename routes), edit `config.toml` paths from GUI, cross-system substring search. |

## Noted but out of Phase 1 fan-out

- **`fix-cues` / disc-set renaming** — `core/cues.py` (`rename_disc_set`
  L57) is implemented and (per README) tested standalone, but is
  **dead code from the entry-point graph**: the CLI subparser
  (retrosync.py:394-397) is never dispatched in `main()`
  (retrosync.py:402-422, raises `NotImplementedError`), and
  `gui/server.py` never imports `core.cues`. No live flowchart to
  trace — documented directly in the duplication/unified-proposal
  phase instead of spawning a subagent for it.

## Boundary adjustments from raw discovery

The Phase 0 agent proposed 13 items; consolidated to 8 for fan-out:
- Merged "cover format/content repair" into #1 (same pipeline, same
  core file, convert/validate are cleanup passes over the same PNG
  invariant the live download path already enforces).
- Kept #3 (cascade engine) separate from #2/#5 because it's shared
  infrastructure called by two different features — exactly the kind
  of thing Phase 2 duplication-hunting cares about.
- Merged memory-card editor + emu-save backup into #7 since they
  share one GUI modal and both depend on `core/serials.py`, but the
  flowchart subagent is told to trace both backends distinctly.
- Merged sanitize/settings/search into #8 — each is small (<70 lines
  of route logic) and none has enough internal complexity to warrant
  its own subagent.

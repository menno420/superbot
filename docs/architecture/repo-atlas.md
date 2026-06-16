# Repo architecture atlas — how to use it

> **Status:** `reference` — a how-to for `scripts/atlas.py`. **This page is curated and stable;
> the atlas *body* is generated on demand and intentionally not committed** (owner decision Q-0151a:
> the atlas is a **companion** to `AGENT_ORIENTATION.md`, not a replacement). Born from the
> architecture-atlas review ([capture](../ideas/architecture-atlas-and-structure-review-2026-06-16.md),
> PR #957) and [the plan](../planning/extension-taxonomy-crosswalk-plan-2026-06-16.md) (PR 2).

## What it is

A **thin, repo-wide composer** over the maps this repo already has. `scripts/context_map.py` answers
the orientation questions *for one file* (layer · owner · imports · blast radius · tests · docs · role);
the atlas answers them **across the whole repo** in one provenance-stamped index, by importing the
existing tools as libraries and joining their output:

| Fact | Source tool (composed, never re-implemented) |
|---|---|
| layer · importers · ownership | `scripts/context_map.py` |
| review unit (repo-review-map partition) | `scripts/_review_units.py` |
| role · backing-subsystem · registered | `scripts/extension_crosswalk.py` (PR #958) |

**Do-not-duplicate rule:** if you need a fact the atlas doesn't have, add it to the relevant *source*
tool, not to `atlas.py`. The atlas only joins and rolls up.

## How to run it

```bash
python3.10 scripts/atlas.py            # compact summary: rollups by layer / role / review-unit + provenance
python3.10 scripts/atlas.py --full     # the full per-file index to stdout
python3.10 scripts/atlas.py --check     # composite coherence guard (exit 1 on drift)
```

The body is **not committed** — regenerate it on demand. The provenance header carries the commit SHA
+ timestamp + generator version, so a generated copy is always self-dating.

## What `--check` guards (kept honest — no false-positive gates)

- **Delegates** classification + crosswalk-doc freshness to `extension_crosswalk.check()`, so
  `atlas.py --check` is one entrypoint that also covers the crosswalk guard.
- **Hard-fails** when a loaded extension has no source file on disk, or the index can't be built.
- **Reports (does not fail)** "orphan" files that classify into no layer and aren't a known top-level
  module — surfaced for a human, never a hard gate (a new top-level package is usually intentional).

It is **not wired into CI** by default (matching `check_sector_map.py` / `dispatch_menu.py` — ask the
owner before adding a `code-quality.yml` step; the crosswalk half is already CI-enforced via its test).

## Relation to the other navigation surfaces

- **`AGENT_ORIENTATION.md`** — the *curated reading-order router* (what to read, in what order). The
  atlas is its generated **companion**: orientation tells you where to start; the atlas gives you the
  repo-wide fact table. Orientation stays authoritative for *intent*.
- **`docs/agent/` context packs** — *curated per-area* reading context (folio + binding docs + source
  roots). The atlas is *generated + repo-wide + file-indexed*. They are complementary: packs answer
  "I'm working in area X, what do I read?"; the atlas answers "across the whole repo, where does
  everything sit?".
- **`context_map.py`** — the per-file version of the same questions; run it before editing a file.

## Provenance / disposability (Q-0105)

Added 2026-06-16. Read-only, stdlib + the sibling scripts, no bot-runtime dependency. If it proves
more nuisance than help across a few sessions, delete `scripts/atlas.py`, `tests/unit/scripts/test_atlas.py`,
and this page together.

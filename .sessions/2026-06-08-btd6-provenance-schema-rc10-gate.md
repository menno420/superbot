# 2026-06-08 — BTD6 provenance schema (RC-10 gate) + explore_gamedata tooling

## Arc

Maintainer asked what was still gating BTD6 data mapping. The single binding gate was
**ADR-006** — ratified 2026-06-05, but it deferred the actual implementation to "a
follow-on docs/schema PR" that hadn't been written. That PR is now PR #587.

The session also addressed a second question: whether tooling on the game-data dump
could make future decode sessions faster. Answer: yes — `explore_gamedata.py`.

## Built

**1. `DataProvenance` / `FactRow` / `extract_provenance`**
(`disbot/services/btd6_fact_store.py`)

The typed provenance envelope ADR-006 required. Before this, facts returned by
`fetch_for_intent` were raw dicts — the provenance fields (`source_id`, `source_name`,
`trust_tier`, `fetched_at`) were present but untyped, unnamed by any contract.

- `DataProvenance` — frozen dataclass: source_id, source_key, source_name, source_kind,
  trust_tier, fetched_at, game_version, freshness. `.is_official` / `.label` helpers.
- `extract_provenance(row)` — assembles it from the shape `fetch_for_intent` already
  returns (joined with `btd6_source_registry`). No DB schema changes needed.
- `FactRow` — frozen typed wrapper: body_json + provenance. `FactRow.from_row(raw_dict)`.
  New extraction code should use `FactRow`; `fetch_for_intent` stays raw-dict for the one
  existing caller (`btd6_context_service`) — no breaking change.
- `FreshnessBucket` / `bucket_freshness` now imported at module level from
  `btd6_source_registry` (services → services, architecture-clean).

**2. `docs/btd6/btd6-provenance-schema.md`** — new `binding` doc

The formal schema contract that ADR-006 required before any new extraction. Covers:
- Why the object exists and what problem it solves
- Python type definition (canonical spec)
- How to assemble `DataProvenance` from a fact row
- Owner matrix: which service writes / reads each fact-type family
- Hybrid storage: live facts → `btd6_facts`; static stats → committed JSON / `btd6_data_blobs`
- Relationship to `DataFreshness` in `btd6_view_model_service` (different layers, different purpose)
- Section on `explore_gamedata.py` with clone + usage examples

This doc, when merged, officially lifts the RC-10 extraction pause.

**3. `scripts/explore_gamedata.py`** — offline dump search tool

The BTD Mod Helper game-data dump is ~320 MB of deeply-nested JSON. Previously, decode
sessions required manually opening files or writing ad-hoc search scripts to find model
types or field names. This tool wraps that workflow.

Modes:
- `--list-types [--in SUBPATH]` — all unique `$type` short names with counts
- `--search PATTERN [--struct] [--show-path]` — find nodes by $type substring
- `--field FIELD_NAME` — find nodes that have a specific field
- `--list-files` — enumerate JSON files (useful to understand folder structure)

Key flags: `--in` narrows to files whose path contains a substring (e.g. `Towers/Village`);
`--struct` shows field keys only (good for deciding if a type is worth mapping);
`--show-path` shows the JSON path to each match (good for understanding nesting).

Provenance header per repo convention: unverified — confirm outputs against raw dump a few
times before trusting fully. The tool is a pure stdlib/pathlib script with no disbot imports.

**4. Supporting doc + state updates**

- `docs/btd6/README.md` — paused-work notice replaced with gate-lifted notice; schema doc
  linked under "Pipeline / backends / data".
- `docs/btd6/btd6-gamedata-decode-status.md` — added "Exploration tooling" block before the
  binding discipline section (the place decode agents read when starting a session), with
  clone instructions + annotated usage examples for each `explore_gamedata.py` mode.
  Updated header timestamp + gate status.
- `docs/subsystems/btd6.md` — current-state section updated from "paused" to gate-lifted.
- `docs/current-state.md` — BTD6 extraction gate updated from "stays paused" to "now
  implemented; may resume against the ordered backlog."

## Key decisions / findings

- **No new infrastructure needed.** `btd6_facts` already carries `source_id`, `fetched_at`,
  `version`, `confidence`, `game_version`. `btd6_source_registry` already tracks
  `trust_tier`, `source_kind`, etc. The gap was purely a typed envelope + formal doc.
- **`fetch_for_intent` stays raw-dict.** One caller; no value in breaking it. New code uses
  `FactRow`; the old path stays untouched.
- **Static facts are out of scope for `DataProvenance`.** Their provenance is the `source`
  field stamped inline by `parse_gamedata.py` / `fetch_bloonswiki.py`. The schema doc makes
  this split explicit to prevent future agents from incorrectly trying to attach
  `DataProvenance` to committed JSON files.
- **`explore_gamedata.py` is an offline tool only.** It has no disbot imports, no runtime
  path. Agents must clone the dump locally first.

## CI / quality

`python3.10 scripts/check_quality.py --full` — green: 8063 passed, 16 skipped, 0 failures.
mypy clean (585 files). check_docs clean (0 orphans). PR #587 pushed; CI in-progress at
session end.

## What's next (the now-unblocked backlog)

From `docs/btd6/btd6-gamedata-decode-status.md`, ordered:
1. Buff decode tail (9 → 38 types) — per-model semantic analysis, use `explore_gamedata.py`
   to inspect each type before mapping
2. `SCHEMA_FIRST` buff/zone types — extend the renderer before decoding
3. Zone effect tail (28 types) + zones nested in sub-towers (Heli `MoabShoveZoneModel` is next)
4. Economy-tower attack suppression + `paragon_cost`/`paragon_name`
5. Tower cutover (game-native over wiki)

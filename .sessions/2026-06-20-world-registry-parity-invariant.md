# 2026-06-20 — Explore world-registry parity invariant + folio docs

> **Status:** `complete` — small follow-up to the merged spine PR 1 (#1156). Docs + test only,
> no runtime code → self-merge on green (Q-0113).

> **Run type:** routine · dispatch

## What I did

Follow-up slice in the same dispatch run, after the federated Explore-hub **PR 1 merged (#1156)**.
Hardened + documented the new world-registry seam — a safe, self-mergeable slice. I deliberately did
**not** take the heavier next lanes this autonomous run:
- **Plan PR 2** (global vs per-game XP split) needs a `player_skills` **`game` discriminator
  migration** on a live progression table — a schema change I can't runtime-verify here; deferred to
  a runtime-verified session.
- **procedures→skills Batch 1** edits `.claude/CLAUDE.md`, which Q-0106 makes **read-only to me in
  an autonomous session** (propose, don't self-edit) — out of scope here.

## What shipped
- **`tests/unit/invariants/test_world_registry_parity.py`** (NEW) — a CI invariant asserting every
  registered Explore `WorldEntry.key` resolves to a real `SUBSYSTEMS` entry (no silent dead-end
  buttons), each entry has non-empty label/emoji/description, the hub's button custom_ids are
  unique, and the two built-ins (mining · fishing) register by default. A pytest invariant (not a
  `check_*.py` script) because the registry is **code** (openers are callables), not a generated
  JSON artifact — the same home as `test_command_synonyms_resolve_to_real_commands`.
- **`docs/subsystems/games.md`** (EDIT) — new "Federated Explore world spine" section documenting
  the seam (`world_registry` · `ExploreWorldHubView` · `!world` · the parity invariant) and **how to
  add a world** (register a `WorldEntry` at the owning cog's setup), with the next spine slices
  (PR 2/PR 3) + the Q-0182 gate noted, so the next agent finds the seam cold.

## Verification
- `python3.10 -m pytest tests/unit/invariants/test_world_registry_parity.py` → 4 passed.
- `python3.10 scripts/check_docs.py --strict` → all checks passed (folio edit clean, ratchets held).
- No `disbot/` runtime code changed → arch/lint trivially unaffected.

## Handoff
Federated Explore-hub **PR 2** (global vs per-game XP split — needs the `player_skills` `game`
discriminator migration, **runtime-verify**) then **PR 3** (cross-game identity card). Plan §4–§5.
The world-registry seam now has a parity invariant guarding it and a folio entry documenting it.

## ⚑ Self-initiated
None — this hardens/documents an already-merged, already-on-plan lane (PR 1). Not a new feature.

## 📤 Run report
- **Run type:** routine · dispatch
- **What shipped:** world-registry parity invariant + games-folio spine documentation (follow-up to
  merged PR #1156).
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none
- **⚑ Self-initiated:** none

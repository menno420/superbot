# 2026-06-24 — BTD6: unify five command groups under one `/btd6`

> **Status:** `in-progress`

## Goal (owner request, this session)

The maintainer asked: *"currently all the btd6 commands are divided into multiple
sections, btd6ops btd6ref, etc — is it possible that they all work with just
`!btd6`/`/btd6` and then the action `<income/round/strat/etc>` to make it less
confusing?"* He picked the **"Flattest"** layout.

Today there are **five** separate command groups (33 actions): `btd6` (ask/status/…),
`btd6ref` (tower/hero/round/income/rbe/relic/ct), `btd6ops` (admin),
`btd6strat` (strategy), `btd6events` (live events) — plus the `btd6menu` opener.

## What I'm about to do

Collapse all five into ONE `/btd6` (and `!btd6`) tree, **Flattest** shape:
- Everyday lookups flat: `/btd6 income`, `/btd6 round`, `/btd6 rbe`, `/btd6 tower`,
  `/btd6 hero`, `/btd6 relic`, `/btd6 ct`, `/btd6 ask`, `/btd6 status`, …
- Big buckets nest: `/btd6 strat …`, `/btd6 ops …`, `/btd6 events …`.
- Verified Discord rule: a top-level command may mix flat subcommands with nested
  subcommand-groups (max 25/level, one level deep) — so Flattest is buildable.

Implementation: a module-level command tree in `disbot/cogs/btd6/_commands/`
(cogs can't cleanly share one `app_commands.Group`; module-level is the supported
pattern and dodges the 800-LOC `*_cog.py` ceiling). Handlers stay thin — they
delegate to the existing `cogs/btd6/_builders.py` + services, so the verified
numbers don't move. The mother `btd6_cog` registers the tree.

Backward-compat: old **slash** groups (`/btd6ref`, `/btd6ops`, …) are removed (the
cleanup); old **prefix** groups (`!btd6ref …`) stay as *hidden* aliases so nothing
breaks for existing chat/muscle-memory.

## Status checklist
- [ ] Unified `/btd6` slash tree (flat lookups + strat/ops/events subgroups)
- [ ] Unified `!btd6` prefix tree mirroring it
- [ ] Strip old slash groups from the 5 cogs; keep prefix groups as hidden aliases
- [ ] Mother cog registers the tree
- [ ] Update parity / surface-ledger / reachability / scan_commands tests
- [ ] Update user-facing command strings (errors, footers, AI suggestions)
- [ ] `python3.10 scripts/check_quality.py --full` green
- [ ] Flip this card to complete → auto-merge on green CI

## Notes
- This is a large command-tree re-sync; it pairs naturally with the held
  hash-gated auto-sync idea (kept gated — external/production; offered, not yet
  greenlit). A docs sweep of the command-map docs is the natural PR-2 follow-up.

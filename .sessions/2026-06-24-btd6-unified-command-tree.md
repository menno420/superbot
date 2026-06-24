# 2026-06-24 — BTD6: unify five command groups under one `/btd6`

> **Status:** `complete`

## Goal (owner request, this session)

The maintainer asked: *"currently all the btd6 commands are divided into multiple
sections, btd6ops btd6ref, etc — is it possible that they all work with just
`!btd6`/`/btd6` and then the action `<income/round/strat/etc>` to make it less
confusing?"* He picked the **"Flattest"** layout.

Before: **five** separate command groups (33 actions) — `btd6`, `btd6ref`,
`btd6ops`, `btd6strat`, `btd6events` — plus the `btd6menu` opener.

After: **one** `/btd6` (and `!btd6`) tree. Everyday lookups flat
(`/btd6 income`, `/btd6 round`, `/btd6 rbe`, `/btd6 tower`, `/btd6 hero`,
`/btd6 relic`, `/btd6 ct`, `/btd6 ask`, `/btd6 status`, `/btd6 diagnostics`,
`/btd6 test-intent`), big buckets nested (`/btd6 strat …`, `/btd6 ops …`,
`/btd6 events …`). Verified against Discord's docs that a top-level command may
mix flat subcommands with nested subcommand-groups (max 25/level, one level).

## What shipped (PR #1419)

- **`cogs/btd6/_unified.py`** (new) — the module-level `/btd6` app tree + `!btd6`
  prefix tree. discord.py can't share one `app_commands.Group` across cogs, and
  one mega-cog would blow the 800-LOC ceiling, so the tree is module-level and
  the mother `btd6_cog` registers it in `setup()` (`register`/`teardown`, both
  idempotent). Handlers are thin — they delegate to the existing `_builders` /
  services, so the **verified numbers and gating are unchanged**; only the path
  moved.
- **`cogs/btd6/_ops_helpers.py`** (new) — the ops readiness/runs/toggle/seed/
  announce helpers, extracted from `btd6_ops_cog` so both the unified `/btd6 ops`
  subgroup and the hidden `!btd6ops` alias call one seam.
- **The five cogs slimmed** — old **slash** groups removed; old **prefix** groups
  kept as `hidden`, `legacy_duplicate`-classified aliases so `!btd6ref …` etc.
  still work. Cog sizes now 97–214 LOC (were ~195–343).
- **`scripts/scan_commands.py`** — taught to see module-level command trees (it
  was blind to anything outside a cog class, so the unified tree dropped the
  dashboard's slash count 70→37). Generalised group-finding to any body + a
  fixpoint for nested groups + path-based subsystem mapping. Dashboard back to
  74 slash / 436 commands.
- **User-facing strings** repointed to the new `!btd6 <bucket> <action>` form
  (error embeds, footers, AI suggestions, docstrings, settings-key help).
- **Tests** — rewrote the parity / surface-ledger / scan / defer-safety tests to
  the unified tree; repurposed the per-cog tests to pin the hidden-alias
  backward-compat; added `test_btd6_unified_tree.py` pinning the Flattest shape.
  Regenerated dashboard artifacts.

## Status checklist
- [x] Unified `/btd6` slash tree (flat lookups + strat/ops/events subgroups)
- [x] Unified `!btd6` prefix tree mirroring it
- [x] Strip old slash groups; keep prefix groups as hidden `legacy_duplicate` aliases
- [x] Mother cog registers the tree
- [x] Update parity / surface-ledger / reachability / scan tests (+ new shape test)
- [x] Update user-facing command strings
- [x] `python3.10 scripts/check_quality.py --full` green (12398 passed) + arch strict clean
- [x] Flip this card to complete → auto-merge on green CI

## Owner action after deploy
Run `!syncslash global` once after the redeploy so Discord drops the old
`/btd6ref` / `/btd6ops` / … commands and shows the unified `/btd6`. (The hash-
gated auto-sync, still offered & ungated, would retire this step entirely — and
this big re-sync is the strongest case yet for building it.)

## Follow-up (natural PR-2, docs-only — flagged, not orphaned)
The reference/command-map docs still describe the old 5-group layout:
`docs/setup-platform/settings-customization-command-map.md` (lines ~102-109,
~1750-1827), `docs/planning/platform-mapping-a-user-surface.md` (~1064-1122),
`docs/agent/index.yml` (add `_unified.py` as a source root + rebuild the pack),
`docs/subsystems/btd6.md`. A focused docs PR should sweep these.

## 💡 Session idea (Q-0089)
**A reconciliation test that compares `scan_commands.scan_commands()` to the
live `bot.tree.walk_commands()`.** This session relied on the AST scanner to
report the command surface, found it silently blind to module-level trees, and
had to hand-verify the fix. The scanner is marked "unverified (Q-0105)" exactly
because nothing checks it against ground truth. A test that builds a bot, loads
the cogs, and asserts the scanned slash set == the live tree's slash set would
graduate the scanner from "unverified" to "verified" and catch this whole class
of drift automatically (same spirit as the ledger/cadence false-green lesson,
Q-0120). Worth an idea file if it survives a sniff test next session.

## ⟲ Previous-session review (Q-0102)
Previous: `2026-06-24-btd6-round-range-command.md` (#1409 — dup-sync `clear`
scope + `/btd6ref round` range). **Did well:** correctly diagnosed the duplicate
listing as a global+guild double-registration (not a code bug) and added a
targeted `clear` scope rather than papering over it. **Missed / could improve:**
it treated the symptom (duplicates) and offered the structural fix (auto-sync)
but left it ungated — and *this* session's full-tree rename makes a manual
re-sync unavoidable, so the auto-sync is now overdue twice over. **System
improvement it surfaces:** the recurring "remember to `!syncslash` after a
command change" toil is a standing reliability gap; the hash-gated auto-sync
should stop being offered-and-deferred and get built (it's contained + testable;
only the *first* live sync is external). Carried into the owner-action note above.

## 📝 Doc audit (Q-0104)
- `check_quality --full` green; `check_architecture --mode strict` clean (only
  pre-existing known warnings).
- New owner decision recorded? No new router Q this session — the work is the
  direct execution of an in-chat owner request (layout chosen via AskUserQuestion).
- Ledger: PR #1419 is in-flight; `check_current_state_ledger --strict` stays
  green because it tracks *merged* PRs. Recorded on merge / next reconciliation.
- Known drift surfaced (not hidden): the command-map reference docs above —
  flagged for the PR-2 sweep so it isn't orphaned.

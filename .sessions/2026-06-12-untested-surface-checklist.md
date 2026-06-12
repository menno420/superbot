# 2026-06-12 — Untested-surface testing checklist (PR #731)

**PR:** [#731](https://github.com/menno420/superbot/pull/731) — `docs: untested-surface testing checklist (owner-commissioned)`
**Trigger:** owner-approved the roadmap queue item; checklist was explicitly
commissioned during the 2026-06-10 post-incident round (see `current-state.md`
last-updated stamp: "an untested-surface testing checklist commissioned").

## What shipped

`docs/audits/untested-surface-checklist.md` — the persistent successor to the
point-in-time `production-eval-checklist-2026-06-10.md`.

**18 sections, 70+ `[ ]` items** covering every command and UI surface that:
1. automated CI cannot verify (visual output, button UX, real Discord API), AND
2. has no live-walk record in this repo.

Sections: Economy & Inventory · General & Social · Utility · Roles & Reaction
Roles · XP System · Moderation · Channel Management · Word Filter · Counting Game ·
Admin & Operator · Diagnostic Commands · Logging Panel · BTD6 Ref/Strategy/Paragon ·
Deathmatch · Community/Games/420 · Server Management subpanels · Bootstrap/Access ·
Regression sweep.

Excludes surfaces already covered by CI or the 2026-06-10 eval checklist (table at
the bottom of the doc). Linked from hardening roadmap (`hardening-roadmap-2026-06-12.md`)
which already mentioned "the commissioned untested-surface checklist".

**Maintenance protocol built in:** when a feature ships, add its entry in the
same PR; when a surface is walked, tick ✅ with date; check_docs ensures the doc
stays reachable (orphan guard).

## Context delta (reflection interview)

1. **Route miss:** The `command_descriptions.py` module is not importable standalone
   (requires a live bot for `build_ledger()` to run). Had to fall back to AST grep
   over cog files — not pointed to anywhere. Worth noting in the journal.
2. **Route excess:** None; the explore agent gave a fast enumeration and the
   cog-level grep filled the rest. No wasted reads.
3. **Discovered by hand:** `check_docs` requires every new audit doc to be linked
   from a read-path doc (orphan check). The hardening roadmap already contained
   an unlinked prose mention of "untested-surface checklist" — the link commit
   satisfied the check and also upgraded that reference from prose to an actual link.
4. **Decisions made alone:**
   - Which surfaces to **exclude** (the table at the bottom) — chose all surfaces
     with both machine tests AND an eval-checklist entry. If the owner feels something
     is missing, the maintenance instructions say to add it.
   - Organized by subsystem (not by priority/risk) — matches how the owner navigates
     the bot for a walk session.
   - Kept the Moderation section's ⚠️ warning about using a test account — safety,
     not ceremony.
5. **Weak point:** The checklist was built from source-code enumeration, not from
   a live bot walk. Two gaps are possible: (a) commands that exist in source but are
   gated off by settings/governance and would never appear to a regular user; (b)
   panel-to-panel navigation flows that cross cog boundaries (e.g., the Community
   hub → XP board → rank card sequence). These are documented as "navigate to each
   works" rather than step-by-step sequences.
6. **One change that would have helped:** A `scripts/command_surface_dump.py` that
   can run without a live bot (offline from cog source + the surface ledger's YAML)
   and emit a structured list of commands by subsystem. Currently this requires either
   booting the bot or AST-grepping. → session idea below.

## 💡 Session idea (Q-0089)

**Offline command-surface dump script.**

`scripts/command_surface_dump.py` — runs without a live bot, reads cog source via
AST + the subsystem registry, and emits a structured JSON/table of all commands by
subsystem (name, aliases, kind prefix/slash, permission tier). This would replace
the AST-grep workaround used this session and make the untested-surface checklist
self-verifiable: `scripts/command_surface_dump.py --diff-checklist` could flag
commands that exist in source but have no entry in the checklist.

The same script would be useful for `context_map.py` output (the "what commands
does this cog expose?" question), the AI's self-awareness tools, and the command-
surface ledger's offline documentation. Read-only, no Discord dependency.
Dedup: not in `docs/ideas/`; adjacent to `scripts/review_scope.py` (a related
scope tool) but distinct in purpose.

## Grooming pass

No additional grooming needed this session — the checklist itself IS the gromed
idea (roadmap queue item #1: "untested-surface testing checklist, owner-
commissioned"). The `current-state.md` roadmap queue note was the groomed idea's
home; it's now executed.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (PR #731 open, CI pending) |
| CI-red rounds | 0 (local check-only green before push) |
| Repo-rule trips | 1 (check_docs orphan — fixed before push by linking from hardening roadmap) |
| New ideas contributed | 1 (offline command-surface dump script) |
| Ideas groomed | 1 (roadmap queue item #1 executed) |

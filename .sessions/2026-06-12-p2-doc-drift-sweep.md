# 2026-06-12 — P2 doc-drift sweep (band queue slot 2)

> **Status:** `audit`

**PR:** #764
**Branch:** `claude/wizardly-planck-c04laf` (fourth task of this conversation:
design #755 → build #758/#760/#762 → pass #763 → this sweep)

## Context

The owner's "continue" advanced the band queue
([night pass §4](../docs/planning/reconciliation-pass-2026-06-12-night.md)):
slot 2 = the hardening roadmap's P2 table — five known doc-drift fixes, cheap,
no gate. Each claim re-verified against source before editing (the readiness
maps are dated audits; verify-then-edit is the rule).

## What shipped (PR #764)

1. **Smoke checklist** — `!platform diagnostics` (nonexistent) → `!platform
   runtime` + `consistency`, dated correction note; `platform_panel.py`
   docstring no longer claims every subcommand is grouped (`startup`/`findings`
   are typed-only).
2. **AI runtime README** — "intentionally inert scaffold" → the live platform
   (gateway/routing/flags/NL-stage/providers), accurate file roles + flow +
   boundaries + binding-doc pointers.
3. **ADR-006** — dated status addendum (pause satisfied: provenance schema
   shipped, extraction resumed, Q-0066 cutover #649); decision text untouched
   (ADR immutability). Decode-status header v55.0→v55.1 @ cutover SHA;
   duplicate backlog item 3 renumbered.
4. **Media folio** — "bounded cached metadata" corrected to the raw-payload
   reality; bounded projection + purge framed as the Q-0099/P0-2 target.
5. **Flag owner** — `YOUTUBE_CONTEXT_ENABLED` `owner="ai"`→`"platform"`
   (ADR-007) with provenance comment — the one runtime-adjacent change
   (metadata only; flag/invariant suites green).

P2 table marked SWEPT with per-item outcomes. Verified: full CI mirror green ·
arch strict 0 errors · docs strict green · affected suites 28/28.

## Process notes

- Noted in passing, not touched: `views/diagnostic/platform_panel.py` carries a
  module-level `views → cogs` import (`cogs.diagnostic._platform_embeds`) — a
  pre-existing known-violation-class item, visible in its context map; belongs
  to the diagnostic slice's own cleanup, not this sweep.
- #757 (HermesCog) merged to main between sessions — the surface-map counts
  were already updated by that lane (38 extensions / 9 hookless); nothing for
  this sweep to reconcile there.
- Grooming (Q-0015): satisfied by queue execution (slot 2 of the band).

## 💡 Session idea (Q-0089)

**A docs command-reference linter** — compose two existing tools: run
`scripts/command_surface_dump.py --json` (every real prefix/slash command) and
grep `docs/**/*.md` for `` `!command` ``-style mentions; flag references to
commands that don't exist. Why I believe in it: the sweep's headline fix was
exactly this class — `!platform diagnostics` lived in a **binding, doc-test-
pinned** checklist for weeks because the doc-test pins *fields*, not *routes*;
a route linter makes the whole class checkable, and both halves already exist.
Quick-win lane; `check_docs`-style advisory first, Q-0105 header. Dedup-checked:
`command_surface_dump --diff-checklist` compares source↔checklist coverage, not
docs-prose mentions; nothing else covers this.

## ⟲ Previous-session review (Q-0102) — the #763 reconciliation pass

**Did well:** the false-green checker find was the self-auditing loop working
exactly as designed — a docs pass that distrusted its own green tooling,
root-fixed the shared regex with tests, and re-verified against reality before
relying on the result.
**Missed (small, structural):** its §4 queue listed "land #757" in the buffer
slot while #757 was already merging in parallel — the snapshot went stale
within the hour. That is inherent to parallel lanes, the record is dated, and
the next pass's scorecard absorbs it; no process change is warranted beyond
what already exists (the open-PR check + the scorecard). Genuinely little else
to fault in a docs-only pass that found and fixed a real tooling bug — saying
so per the no-filler bar.

## Context delta (reflection interview)

- **Route hit:** the hardening roadmap's P2 table was a ready-made work order;
  the readiness maps' Evidence columns pointed straight at file+line for every
  item.
- **Route miss:** none material.
- **Discovered by hand:** the decode-status duplicate-numbering location and
  the exact platform-panel docstring wording — both one grep each.
- **Decisions made alone:** ADR-006 fixed via addendum rather than in-place
  rewrite (ADR immutability); media folio fixed as doc-states-reality rather
  than code change (the code change IS P0-2, queued). Both reversible and
  recorded.
- **Weak point of what shipped:** the platform-panel completeness fix is a
  docstring honesty fix, not the "add startup/findings to a category" UX
  improvement the health map also sketched — that's deliberate (P2 = drift
  fixes; the UX addition is health-lane work), but worth naming.
- **One change that would have helped:** the command-reference linter above —
  it would have caught item 1 the day it drifted.

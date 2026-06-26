# 2026-06-26 — Sector ▶ Next freshness guard (S3 mechanism)

> **Status:** `complete`
> **Run type:** routine · dispatch
> **Branch:** `claude/funny-franklin-867vhz` · **PR:** #1476

## What I did
Autonomous dispatch fire (no work order). S2's offline anchor tail is exhausted (remaining
BTD6 correctness needs prod creds); the cleanest offline, self-mergeable slice was S3
self-improving-engine mechanism work.

While orienting I hit a real drift class: `docs/current-state/S3-ai-memory.md` ▶ Next listed
**"Consistency-linter AI-nav PR 1"** linking `ai-panel-inplace-navigation-plan-2026-06-19.md`,
a plan already **`historical` / SHIPPED** (#1376). A `▶ Next` that points at finished work
steers the *next* dispatch run into rebuilding shipped work — the exact mis-step this run
nearly made before I cross-checked the plan's status.

Shipped:
1. **`scripts/check_sector_next_freshness.py`** — read-only stdlib guard (Q-0105 disposable
   header). Scans each `docs/current-state/S*.md`, isolates the `▶ Next` section(s), extracts
   `../planning/*.md` links, and flags any whose plan `Status:` is `historical`. Scoped to the
   ▶ Next section only, so Recently-shipped / pass-record `historical` links don't false-positive.
   Not CI-wired (ask-first per the autonomy boundary) — run by hand / from the recon routine.
2. **Fixed the live S3 instance** (Q-0166 fix-on-sight): dropped the stale shipped pointer from
   S3 ▶ Next; preserved the shipped provenance as a Recently-shipped line (the `edit_in_place`
   rule graduated warn→error, #1375).
3. **`tests/unit/scripts/test_check_sector_next_freshness.py`** — 7 tests: live ground-truth
   (`run() == []` after the fix), section-scope isolation, link extraction, historical-flagging,
   buildable-not-flagged, missing-plan-not-flagged.

## Verification
- `python3.10 scripts/check_sector_next_freshness.py` → OK (5 sector files clean after the fix).
- `python3.10 scripts/check_quality.py --check-only` → all checks passed (check_docs +
  check_consistency green).
- `python3.10 scripts/check_architecture.py --mode strict` → 0 errors (only pre-existing
  `views/` WARNs, none from this change — it touches scripts/docs/tests only).
- `python3.10 -m pytest tests/unit/scripts tests/unit/docs -q` → **1078 passed**.
- Doc audit: `check_current_state_ledger --strict` (3 dashboard-refresh PRs newer than marker
  #1472 = benign lag, recorded by the next recon at #1500); `check_docs --strict` clean.

## Handoff — next dispatch
- This slice is complete and self-contained. No remaining sub-steps.
- **S2** offline BTD6 anchor tail is exhausted — the next BTD6 correctness step (live `llm_judge`
  battery + absence-guard Layer B) is **creds-gated / owner-paced**, not an autonomous slice.
- **S3** next offline-buildable: the **bot self-test walker** eval harness, or the **Hermes
  bug-triage write**. (`procedures→skills Batch 2` touches CLAUDE.md restructuring — I left it
  for a session with the owner live, given CLAUDE.md is read-only to an autonomous run, Q-0106.)
- **S1** offline-buildable: H3 card-engine incremental adoption (next card-bearing hubs set
  `help_nav_card` in their hook) — but several S1 ▶ Next items are blocked on running-bot
  verification; pick the offline ones.
- Remark for a later review: **CodeGraph up** (52525 nodes, build clean); Grimp not exercised
  this run. No arch warning I could retire (all pre-existing `views/` lifecycle WARNs).

## 💡 Session idea (Q-0089)
Turn the freshness guard from a *detector* into an *active filter* on the dispatch seam — but
note the real shape (verified this run, so the next session isn't misled): `dispatch_menu.py`
resolves from **`roadmap.md` § By sector**, whose Now/Next bullets are short labels with **no
plan links**, while this guard scans the **`current-state/S*.md` ▶ Next** links. They're
different sources. So the clean version is *either* (a) wire the guard into `/session-close`
so every session re-checks ▶ Next freshness on the way out (cheap, high-leverage — closes the
"3 days unguarded" gap), *or* (b) have the roadmap Now/Next bullets carry the same plan link
their current-state twin does, then a shared `plan_status()` can suppress a shipped lane from
the dispatch pick. (a) is the smaller, surer win; (b) needs a roadmap-convention change first.
A direct cross-script import is ruled out — `dispatch_menu.py`'s header pins the single-file
standalone convention (factor a shared module only when a third consumer appears).

## ⟲ Previous-session review (Q-0102)
The prior runs (projmoon grounding + faithfulness guard, #1467/#1469/#1470) were strong —
they shipped the cross-domain over-route guard *and* a one-line-registration recipe for the
next domain, which is exactly the "leave the next session better-equipped" bar. What they
**missed**: each shipped its arc but none re-checked the *sector ▶ Next pointers* for staleness
on the way out — the S3 stale pointer this run found had been live since #1376 (2026-06-23),
three days unguarded. **System improvement surfaced:** the per-sector ▶ Next layer had no
freshness guard at all (the recon routine only reconciles every 30 PRs) — this run's
`check_sector_next_freshness.py` closes that gap; consider running it from `/session-close`.

## 📤 Run report
- **Run type:** routine · dispatch
- **PR:** #1476
- **⚑ Self-initiated:** `check_sector_next_freshness.py` — an S3 mechanism guard I originated
  (no dispatch/owner ask) after spotting the S3 stale-pointer drift; idea→build is open
  (Q-0172), flagged here for owner review/revert.
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none

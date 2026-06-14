# Session: fix Hermes "always a bit behind" — pick next slice from live state, not plan PR-numbers

> **Status:** `in-progress` — fixing the Hermes dispatch "pick next slice" gap (Q-0142); flip to complete last.

**Branch:** `claude/sharp-ptolemy-5mzbvb` · **Date:** 2026-06-14 · **Type:** owner-directed workflow fix (Q-0142, in-session)

## What this session did

The owner shared the Telegram trace of how this very routine was dispatched and asked why Hermes
"always seems to be a bit behind." Root-caused and fixed it.

**Root cause.** When the owner says *"dispatch a continuation worker"* (no specific task), Hermes must
decide *what* to build. The `superbot-dispatch` skill had **no procedure for that no-explicit-task
case**, so he fell back to a planning doc's forward PR-number range — the band-#840 reconciliation
plan's *"the next ~9 PRs (band #841–#860)"* — and read those numbers as the schedule, producing a
stale "reconcile #848–#856" work order. The killer detail: he'd already run the live ledger guard
(it returned CLEAN = nothing to reconcile) but dispatched a reconciliation task anyway, because the
plan's numbers overrode live state. PR numbers in plans are a dated snapshot — GitHub assigns them
globally across all parallel/housekeeping PRs, so a forward range is wrong the moment any unplanned
PR merges (plan written at HEAD #840; live `main` was at #866 by dispatch).

**Fix (Q-0142, owner-directed in-session).**
- **`hermes-skills/dispatch.md`** — new **STEP 1b**: for the continuation-worker case, derive the
  task from LIVE state (read ▶ Next action → run the ledger guard; drift = the only reconciliation
  task, clean = nothing to reconcile → pick the next slice by **description/lane**, not a PR number,
  and confirm it isn't already shipped). New **PLAN-NUMBERS-ARE-DATED** rule + "live state wins".
- **`hermes-operating-prompt.md`** — the always-loaded "PICK THE NEXT THING BY DESCRIPTION, NOT BY PR
  NUMBER" rule + a reconciliation guard line (check, don't hand-build from a plan range).
- **`reconciliation-pass-2026-06-14-band840.md` §4** — de-numbered the heading ("The next ~9 slices
  (planned after #840)") and strengthened the caption so the misleading "#841–#860 schedule" artifact
  is gone at the source.
- **Router Q-0142** — the provenance entry.
- Regenerated `scripts/hermes/skills/dispatch/SKILL.md` via `build_skills.py`.

**Owner action:** re-paste the operating prompt + `superbot-dispatch` skill into Hermes' config on the
VPS for this to take effect (the repo is the source of truth; Hermes runs from a pasted copy).

Verification: `check_docs --strict` ✓; `build_skills.py` regenerated cleanly (only `dispatch` SKILL.md
diffs); diff scoped to 5 intended files. Docs/tooling only — no runtime bot code.

## 💡 Session idea (Q-0089)

A tiny `scripts/next_slice.py` (or a `--next` flag on an existing checker) that prints the single
current "what's next" — the ▶ Next action lane + live ledger-guard status + open-PR count — in one
line, so *both* Hermes and a fresh routine have a deterministic, always-live answer to "what should I
work on?" instead of each re-deriving it from prose (and occasionally from stale plan numbers, as
happened here). Captured to `docs/ideas/` pending a dedup-grep.

## ⟲ Previous-session review (Q-0102)

The previous run (this same routine's band #841–#860 ledger reconciliation, PR #867) did the
mechanical job correctly — but in hindsight it treated the *symptom* (a stale work order) as the whole
task and only flagged the deeper cause in its Q-0102 note. The better move, which this session takes,
was to follow the "stale work order" thread up to its source: the dispatch path that generated it.
System improvement surfaced + applied: the dispatch skill now has an explicit live-state procedure for
the continuation-worker case, closing the gap where a generic "dispatch a worker" request had no
defined way to choose work and silently fell back to dated plan numbers.

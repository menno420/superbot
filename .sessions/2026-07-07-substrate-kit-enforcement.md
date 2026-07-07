# 2026-07-07 — substrate-kit: adopt installs the enforcement (the forcing functions)

> **Status:** `complete`
> **Branch:** `claude/superbot-rebuild-final-review-nezu89` (restarted from main; prior PR #1778 merged) · **PR:** #1783
> **Provenance:** owner-directed follow-up to the final-review session — "make sure that's all correctly done."

## Why

The Phase-2.5 re-run showed the memory kit's docs get read but not written-back. Root cause the
owner surfaced: this repo's memory discipline isn't voluntary — it's forced by (1) an end-of-session
**nag hook** and (2) a **CI locked door** that won't let a session merge without its journal. The
kit shipped the *notebook* but only *stages* (never turns on) those forcing functions, and the kit's
`check --strict` even treats a **missing** session log as advisory-not-failure — so the door doesn't
actually lock. This session closes that.

## What I'm about to do

1. Give the kit a real session-gate: `check --require-session-log` makes a *missing* log a hard
   failure (the door).
2. Make `adopt --wire-enforcement` lay down a **live** (uncommented) CI workflow that runs the gate
   + the live nag hook (composes with the bootstrap.py vendoring shipped in #1778).
3. Regenerate `dist/bootstrap.py`; add tests.
4. **Prove it end-to-end** on a scratch repo: adopt with enforcement → a session that skips the
   journal → run the gate as CI would (RED) → add the journal (GREEN). Honest note: the nag hook's
   behavioral effect needs a live CLI session; the *door* I prove directly.
5. Update the G2 / final-review writeups honestly.

## What happened (close-out)

Shipped all five, PR #1783 (born-red → flipped complete):

1. **The gate:** `check --require-session-log` makes a *missing* session log a hard failure
   (`substrate-kit/src/engine/cli.py`) — closes the "advisory-not-failure" hole that meant a
   journal-less session passed CI.
2. **The door install:** `adopt --wire-enforcement` (+ CLI flag) lays down a live
   `.github/workflows/substrate-gate.yml` running the gate on every PR, and implies
   `--include-claude` (the live nag hook). `live_ci_workflow()` + `LIVE_CI_RELPATH` in `adopt.py`;
   opt-in, stage-only safety default preserved. `dist/bootstrap.py` regenerated (640 KB).
3. **Tests:** `test_cli_gate.py` (4 — advisory-by-default, MERGE-HELD-when-absent, opens-once-written,
   incomplete-also-fails) + 4 in `test_adopt.py` (live workflow uncommented + gates on the log;
   wire_enforcement plants live CI + live hooks; default never installs live CI; no-clobber). 440
   kit tests green; full CI mirror green.
4. **End-to-end proof:** scratch adoption with `--wire-enforcement` → nag hook wired + live workflow
   present → `check --strict --require-session-log` exits **1 (MERGE HELD)** with no journal, **0**
   after writing a complete card. The door locks and opens.
5. **Writeups:** G2 report **§6 enforcement addendum** (the durable home — the honest result + the
   lived-evidence behavioral proof); the auto-drafted-handoff idea updated (door shipped, draft is
   the complementary next step).

**Honest boundary recorded:** the *door* (CI blocks merge) is proven directly and is the stronger
forcing function; the *nag hook's* isolated behavioral effect is a live-CLI-only claim (subagents
don't fire Stop hooks). Behavioral proof for the door itself is lived: it's the same mechanism that
held every PR of this session-chain born-red until close-out.

**⚑ Self-initiated:** the whole PR is owner-directed; within it, the decision to keep enforcement
**opt-in** (rather than on-by-default) preserves the kit's deliberate "never install executable CI
silently" safety default — flagged as the one judgment call (reversible: a host/K0 flips one flag).

**💡 Session idea (Q-0089):** covered by the updated auto-drafted-handoff idea — the door is shipped,
so the genuinely-next idea is its complement: **auto-draft the session card from git diff + test
state** so the now-mandatory journal is also low-friction. (Not filler — it's the direct
"door without draft = grudging compliance" follow-through.)

**⟲ Previous-session review (Q-0102):** the final-review session (this chain's prior turn) did the
right thing reporting the Phase-2.5 re-run as an honest negative rather than dressing it up — that
honesty is exactly what let the owner spot the real cause (enforcement, not readability) and direct
this fix. What it could have done better: it framed "auto-draft the handoff" as *the* next step when
the more fundamental gap was the missing *door* — it under-weighted that the discipline here is
enforced, not encouraged. **Workflow improvement:** when a memory/workflow experiment fails, check
first whether the *enforcement* was even active before concluding anything about the *content* — an
unenforced convention is an untested convention.

**🛠 Friction → guard (Q-0194):** none new this session — the born-red gate + artifact-freshness gate
+ CI mirror all did their jobs (the mirror caught nothing because the heredoc-format rule from the
prior session's journal was followed: I ran `ruff format` on touched files before committing).

**Docs audit (Q-0104):** `check_docs --strict` ✓; new durable content homed (G2 §6 addendum, idea
update); no owner decisions to route (the design call is flagged on this card per Q-0240).

**Next:** build the auto-drafted-handoff complement; and (unchanged) the rebuild's real next action
is canonical §5 step 6 — create `superbot-next`, where the K0 session runs `adopt --wire-enforcement`
so the new repo is born with the door locked.

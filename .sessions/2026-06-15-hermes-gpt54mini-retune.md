# Session — Hermes retune for gpt-5.4-mini + memory/base cleanup

> **Status:** `in-progress`

## Goal

Owner-directed, live session. Now that **gpt-5.4-mini is confirmed working** (the model arc
#913→#921 closed), re-tune the Hermes control-plane base for the *capable* model and prune what was
built defensively around the old weak free model (`stepfun/step-3.7-flash:free`, ~256K). Goal: a
**cleaner base configured to the owner's wish** + a recorded understanding of gpt-5.4-mini's real
capabilities.

## What I'm doing

1. **SOUL.md retune** (`hermes-operating-prompt.md`) — replace the weak-model framing
   ("you forget after ~15 tool calls / ~256K window") with the capable-model reality (400K reasoning
   model; bounded sessions are now a **cost + re-grounding** habit, not a weakness crutch). Fix the
   dispatch bullet's stale "you're weaker on long loops" → the real reason (Claude Code runs the CI
   mirror Hermes can't).
2. **gpt-5.4-mini specs recorded** (`hermes-control-plane.md` § Model/provider) — verified
   2026-06-15: **400K ctx / 128K out, $0.75/$4.50 per 1M, Aug-2025 cutoff, reasoning model**, +
   `agent.reasoning_effort` tuning lever, + cost-not-window framing.
3. **Hermes memory cleanup** (owner applies on the VPS) — the owner shared the 4 live memory
   entries; 3 of 4 duplicate SOUL.md / the `dispatch` skill / current-state. Recommended lean
   replacement set (infra stickies + one behavioral sticky only).
4. **Deeper base cleanup** (in progress) — archive/demote the token-efficiency investigation doc
   (its conclusion was "it's the model"), slim `apply_context_fixes.sh` (compaction tuning now
   secondary to the capability fix), prune the long completed "Suggested next steps".

## Findings surfaced

- **Python pin drift (verified, real):** `.python-version` = **3.13.13** (Railway/prod) vs CI
  `code-quality.yml` = **3.10**. Prod and CI run different interpreters — a genuine parity gap.
  Hermes' memory flagged it correctly. Investigation + recommendation: see below (no change this
  session — touches CI/prod parity).

## Status

Checkpoint PR opened born-red (Q-0133); flips to `complete` as the final step after the cleanup
sweep + close-out enders land.

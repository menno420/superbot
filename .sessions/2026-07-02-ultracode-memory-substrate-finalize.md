# 2026-07-02 — Finalize the AI-memory substrate (handoff §5.B, ultracode)

> **Status:** `in-progress`
> **Branch:** `claude/ultracode-memory-substrate-2utgvc`
> **Session type:** ultracode (Fable 5) — owner-queued via rebuild handoff §5.B + 2026-07-02 addendum

## What I'm about to do

Execute rebuild handoff §5.B — the finalise-and-ship AI-memory system session:

1. **Re-establish the exact gap against source** (the §5.B-addendum inventory is the prior, not the truth):
   what of the nervous system (mode behaviors, drift/trigger detection, reflection buffer,
   self-review/maintenance loop, review-seam wiring, missing templates, hooks, memory-integrity,
   namespace/shadowing checkers, AgentContextPack generator) is actually absent in `substrate-kit/src/**`.
2. **Build the unbuilt nervous system** on the existing declaration/bootstrap layer (117 tests green today).
3. **Build the context-economy engine kit-native** (retention plan §10 + Q-0214): class/badge taxonomy,
   reading-route declaration, budget gauges + retention windows as config, checker+actuator (dry-run
   default), tombstone/harvest semantics, generalized retention simulator, `docs/decisions.md` ledger
   format with machine-readable `supersedes:`.
4. **Finalize + package**: regenerate `dist/bootstrap.py` (stdlib-only, single-file, proven in a scratch
   dir), one-step adopt flow, README, K0 interlock (doc skeletons · decision ledger · orientation-budget
   checker · namespace guard · seam-authority checks).
5. Honor §5.B-addendum owner-flag defaults (in-repo `substrate-kit` name · two-tier acceptance ·
   seam provisioned not hard-wired · skip the 7-file substep · journal stop-growth only) and session flags.

Hard rails: zero `disbot/` coupling · extend the test suite over every new capability ·
`python3.10 scripts/check_quality.py --full` before pushing · this card flips `complete` last.

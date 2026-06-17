# Generated-artifact freshness umbrella — one soft-drift reporter for every committed generated file

> **Status:** `ideas`
> **Origin:** session idea (2026-06-17, Q-0089), from the dashboard.json structural-drift reporter
> (PR #1025). Captured (not built) because it is a self-invented *new tool* and the phase gate is in
> fix-phase — the executable single-artifact case shipped; this generalizes it.

## The pattern this generalizes

PR #1025 added a **warn-only structural-drift reporter** for one committed generated artifact
(`dashboard/data/dashboard.json`): build a fresh copy, compare only the *structural identifier sets*
(not the volatile churn), and emit a soft warning when the committed file is behind its generator.
The committed file had silently drifted on `main` (missing env-vars + a setting key that shipped in
#1020/#1023) precisely because nothing reported it.

That same drift class applies to **every committed-and-generated artifact in the repo**, each guarded
(or not) in isolation today:

- `dashboard/data/dashboard.json` ← `scripts/export_dashboard_data.py` (now has `--drift`)
- `docs/operations/env-vars.md` ← `scripts/scan_env_usage.py`
- `docs/agent/generated/*.context.md` ← `tools/agent_context/build_pack.py`
- (any future generator → committed-path pair)

The repo has **no inventory** of "committed generated artifacts," so the same drift keeps being
re-discovered per-artifact, one PR at a time.

## The idea

A single small `scripts/check_generated_artifacts_fresh.py` umbrella, driven by a registry of
`(generator, committed_path, structural-key extractor)` tuples. For each registered artifact it
builds a fresh copy and emits a **soft, non-blocking** "this committed artifact is N structural
surfaces behind its generator" warning — the manifest-spine *"AST is drift-detection"* philosophy
generalized so no future generated file silently rots. Per-artifact extractors keep it honest about
the structural-vs-volatile split (the #1025 lesson: byte-equality reddens CI on every churn; identity
sets do not).

## Why it's worth having (and what to check before promoting)

- **Reuse:** `check_dashboard_data.py --drift` is the working single-artifact prototype to lift from;
  the agent-context system already has `validate_pack.py` — confirm the umbrella *complements* (a
  freshness signal) rather than *duplicates* those (per `docs/helper-policy.md`).
- **Risk:** none — read-only, stdlib, disposable (Q-0105), warn-only by design.
- **Promotion gate:** decide whether it stays a manual/ad-hoc tool or is wired into the
  docs-reconciliation routine's cadence pass (where the dashboard regen was just routed). The cadence
  routine, not per-session CI, is the natural home for "keep the generated artifacts fresh."

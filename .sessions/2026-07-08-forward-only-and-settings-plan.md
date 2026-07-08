# 2026-07-08 — Capture: forward-only Project experiment + per-repo settings ledger

> **Status:** `complete`

**Scope:** owner-directed idea capture ("before I forget") from the EAP-email finalization
thread. Two durable artifacts, docs-only:
1. `docs/ideas/forward-only-project-quality-experiment-2026-07-08.md` — reconfigure a Project to
   never attempt destructive git, run it, and measure the quality cost (empirical version of
   "friction not blockage"; feeds the Anthropic email).
2. `docs/planning/per-repo-settings-state-ledger-2026-07-08.md` — a plan for a durable,
   ideally auto-generated per-repo settings ledger so future sessions read the state instead of
   guessing (optionally surfaced on the dev website).

Also corrected in-thread: "first push must be the owner personally" was imprecise — it's the
auto-mode wall on an unattended session's first-publish-to-a-new-public-repo, clearable by any
non-walled path (human, token-backed Action, or the untested private-first trick).

## What shipped (PR)
- `docs/ideas/forward-only-project-quality-experiment-2026-07-08.md` + ideas-README index entry.
- `docs/planning/per-repo-settings-state-ledger-2026-07-08.md` (phased: capture → auto-generate →
  dashboard).
- Both reachable, `check_docs --strict` green.

## ⚑ Self-initiated
Owner-directed capture — no unprompted scope. Execution of either (run the forward-only Project;
build the settings ledger) awaits the owner's go.

## 💡 Session idea (Q-0089)
The per-repo settings ledger's "auto-mode capability facts" row is the natural home for the
coordinator's #1839 environment-capability-matrix idea — one doc that tells every future session
which actions are walled and what clears each, so nobody re-probes. (Captured inside the plan.)

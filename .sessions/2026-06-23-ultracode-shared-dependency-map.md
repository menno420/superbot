# 2026-06-23 — Ultracode shared-dependency / ownership map

> **Status:** `in-progress` — born-red session card (Q-0133). Flip to `complete` as the
> deliberate final step once the map docs are written, verified, and the report reconciled.

## What this run is about (the one line)

Create the durable, task-independent **Ultracode shared-dependency / ownership map** under
`docs/ultracode/` — the reference a future ultracode *coordinator* reads to dispatch a parallel
refactor fleet without file collisions. It **operationalizes** `docs/repo-review-map.md` (Axis B:
B-slice vs B-platform) with a parallel-safety rating (green/yellow/orange/red), a shared-platform
touch policy, a collision matrix, and a worker-scope template — it does **not** create a competing
taxonomy. Also reconciles the attached ZIP-based verification report against live source.

Mapping is read-only (subagents); only the coordinator (this session) edits docs. No refactor, no
runtime code moved.

<!-- Close-out (arc / shipped / findings / context delta / run report / telemetry) written as the final step. -->

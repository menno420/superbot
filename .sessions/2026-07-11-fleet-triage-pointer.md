# 2026-07-11 — fleet-triage register: supersede pointer to fleet-manager

> **Status:** `in-progress`

📊 Model: Claude (Fable family, fable-5) · lane worker dispatched by
coordinator cse_012o8pySy5K3AV6JWoPKryZL · P3 of the fleet centralization
plan (`docs/planning/fleet-centralization-plan-2026-07-11.md` §4/§5)

## Scope (docs-only, tiny)

The centralization plan §4 ports the fleet-review §1 keep/replace/archive
triage table to **fleet-manager `docs/fleet-triage.md`** as the standing,
re-reviewable register (cross-repo state is fleet-manager-canonical). The
fm-side port ships in fleet-manager PR #86. This PR adds the supersede
pointer in `docs/planning/fleet-review-2026-07-11.md` §1 so the frozen seed
snapshot routes readers to the living register — the same pattern as the
fleet-manifest → roster supersession.

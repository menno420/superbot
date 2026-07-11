# 2026-07-11 — fleet-triage register: supersede pointer to fleet-manager

> **Status:** `complete`

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

## Shipped

- One routing banner under fleet-review §1 (frozen snapshot → living
  register in fleet-manager `docs/fleet-triage.md`). Nothing else touched.
- fm-side context (same slice, fleet-manager PR #86): triage port + roster
  sub-rows + evidence index + hub-row consumption of `control/status.md`
  (#2003 → `c18a9c3`) + `gen_roster.py` graduated VERIFIED (run 3, 8/8 vs
  independently-fetched ground truth).

## Context delta

- **Needed but not pointed to:** nothing — the centralization plan §4 named
  the exact doc + section to edit.
- **Pointed to but didn't need:** n/a (single-file docs edit).

## 💡 Session idea (Q-0089)

The fleet-review §1 table and fm `docs/fleet-triage.md` can now silently
diverge in the OTHER direction — someone re-verdicting the frozen snapshot
here instead of the register. Cheap guard: a superbot docs-lint line (or a
fm `check` extension) that flags any post-supersession edit to the §1 table
body (banner excepted), same class as the fleet-manifest tombstone check.

## ⟲ Previous-session review (Q-0102)

The settle-once graduation session (#2004 lane) was exemplary bugs-first
work: it pinned the buggy scope in a test before fixing it, so the fix is
regression-proof. Nothing it missed that this session surfaced; the one
workflow improvement it already proposed (registry-vs-default drift guard)
still deserves a build slot rather than another restatement.

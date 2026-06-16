# Session (cont.) — solidify the dashboard finalized-vision plan with owner panel decisions

> **Status:** `in-progress`

## What I'm about to do (born-red declaration, Q-0133)

Continuation of the dashboard finalized-vision session (PR #1002, merged). The owner asked me to put the
plan's open forks to him via the question panel "so we can solidify this plan", then answered **8**
questions across two panels. This PR records those decisions durably — into the vision doc
(`docs/planning/dashboard-vision-finalized-state.md`) and the question router.

**The 8 decisions (owner, 2026-06-16):**

1. **Homepage** → **hybrid router landing** (newcomers → product tour; logged-in → straight to workspace)
   — *not* the pure product-site default.
2. **Manifest spine** → **yes, sequenced before the editors** (Q-0162 fork 1 answered).
3. **Owner zone** → **owner-only now, but scope-shaped** for later delegated roles (Q-0162 fork 2 answered).
4. **First live edits** → **help → settings → aliases/routing → panels**.
5. **Authority UX** → **cautious edits, open info** (show edit controls only when near-certain allowed;
   show read-only info + authority preview freely).
6. **Mobile** → **FULL management on mobile** (not just oversight) — a design constraint on every editor.
7. **Panel editor** → **last**, after the simpler editors.
8. **Setup** → **already completed and confirmed working** (owner's own answer) — the Discord OAuth +
   control-token Railway gating is **done**, so the live-editing path is **unblocked**, not a "don't rush"
   wait. This un-gates roadmap phases C/E/F's owner-setup dependency.

**Plan:** apply 5/6/8 (the genuine *changes*) + confirm the rest in the vision doc; mark Q-0162 DECIDED
(its two forks); add **Q-0163** for the other six panel decisions (preserve questions + owner choices).
Docs only; no `disbot/`. Will resync + renumber if a parallel session grabs Q-0163 first (the Q-0162→…
collision lesson from last PR).

## What shipped

_(filled in at close)_

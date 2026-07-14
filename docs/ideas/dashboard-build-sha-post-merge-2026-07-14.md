# Idea — dashboard `build.commit` should reflect the deployed (main) SHA, not the PR-branch HEAD

> **Status:** `ideas` — raised 2026-07-14 (forty-seventh Q-0107 reconciliation pass). **Class:**
> friction→guard · **Sector:** S4/S5 (docs-system / ops tooling) · **Origin:** Codex P3 on PR #2102.

## The friction

`scripts/export_dashboard_data.py` stamps `dashboard/data/dashboard.json` `meta.build.commit` with
the **current branch HEAD** at export time. On any PR that regenerates the export (the reconciliation
pass, and every `bot/dashboard-refresh` PR), that HEAD is a **transient PR-branch commit** — often a
local `Merge origin/main` commit that never lands on `main`. When the PR merges, `main` gets a *new*
merge commit, so the committed `build.commit` points at a SHA that isn't in `main`'s ancestry. The
dashboard/botsite status pages that surface this field then link build provenance to a dead
PR-branch revision instead of the deployed one (Codex P3, PR #2102).

## Why it's not fixable in the PR itself

The final `main` merge SHA is unknowable before the merge happens, so there is no correct value to
write from a PR branch — this is inherent, not a per-PR mistake.

## The improvement (pick the cheapest that holds)

1. **Omit the SHA in the committed artifact** — write `build.commit: null` (or drop the field) in the
   committed JSON and let the *deployed* dashboard fill it at serve time from the running revision
   (Railway exposes the deploy SHA). The committed artifact stops asserting a provenance it can't know.
2. **Post-merge backfill** — a tiny `main`-only workflow step that rewrites `build.commit` to the
   merge commit after merge (a generated-artifact refresh, same shape as the existing dashboard bot).
3. At minimum, record the **base `main` SHA** the export was generated against (knowable) rather than
   the branch HEAD, so the link at least resolves to a real `main` commit.

Option 1 is the cheapest and removes the misleading assertion entirely. Adopt-freely with the standard
Q-0105 provenance/kill-switch header on whatever lands.

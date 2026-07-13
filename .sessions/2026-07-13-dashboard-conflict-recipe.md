# 2026-07-13 — Durable mitigation for the generated-artifact merge-conflict class

> **Status:** `in-progress`
> **Branch:** `claude/dashboard-conflict-recipe` · **PR:** pending
> **Venue:** remote container (worker session, orchestrated). **📊 Model:** Fable 5 (Claude 5 family).
> **Scope:** tooling/gitattributes/docs ONLY — zero runtime behavior change (nothing under
> `disbot/` touched; the new script lives in `scripts/` and is never imported by the bot).

## Arc

The 2-hourly `dashboard-data-refresh.yml` workflow lands `chore(dashboard): refresh generated
data` merges on `main` (e.g. #2062, #2063, #2067), and every open branch that also regenerated
`dashboard/data/dashboard.json` (+ botsite exports) — which guard collateral makes routine —
re-conflicts on those files at every refresh. PR #2061 hit this 3× overnight 2026-07-12→13
(branch merges `1cc99af`, `c3db76c`, `a1c95fb` — the tip is literally "Merge origin/main into
claude/mineverse-flag-2 (regenerate dashboard data)"). The known-working manual recipe is
take-theirs + regenerate. This session codifies that recipe so every agent resolves identically,
and rules out the attribute-level "fixes" with empirical evidence.

## Plan

1. Empirically test `merge=union` on the real `dashboard.json` shape (expect corruption) and the
   custom-merge-driver path (expect per-clone config wall) — decide-and-flag the mechanism.
2. Ship `scripts/resolve_generated_conflicts.py` (stdlib-only, take-theirs + regenerate) + a short
   `docs/operations/generated-data-merge-recipe.md` + `.gitattributes` `linguist-generated`
   marks and a do-NOT-union warning comment.
3. Verify with `python3.10 scripts/check_quality.py --full`; open the PR ready; flip this card
   `complete` as the last commit.

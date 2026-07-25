# Idea — coalesce the dashboard-refresh loop into far fewer PRs (attack the churn at the source)

> **Status:** `ideas` — session idea (Q-0089), captured 2026-07-25 (fifty-first Q-0107 reconciliation
> pass, band-#2220). Not approved for implementation. · **Class:** friction→guard · **Subsystem:**
> S4/S5 (docs-system / ops tooling — the `bot/dashboard-refresh` producer loop).

## The observation

Band-#2220 (#2191–#2220) was **28 merged PRs: 27 were automated `bot/dashboard-refresh`
PRs** and **1** was the 50th-pass reconcile. Every one of those 27 refresh PRs opens a branch,
runs the **full Code Quality CI matrix** (black/isort/ruff + mypy + the whole pytest suite —
`.claude/CLAUDE.md` names `code-quality.yml` "the repo's dominant Actions cost"), arms
auto-merge, merges, and redeploys the `worker` (merge=deploy, Q-0193) — all to commit a
regenerated `dashboard/data/dashboard.json` (+ the botsite mirrors). This shape has held for
many bands (the band before it was 17/20 dashboard refreshes; #2100→#2130 was 22/29).

That is a large, recurring CI/Actions spend on a repo that is **intentionally frozen as the
superbot-next oracle** — the artifact only drifts because parallel sessions add cogs/settings/
env-vars, i.e. the real *rate of change* is a handful of structural deltas per week, not ~one
PR per hour.

## Why this is distinct from the 2026-07-19 idea

[`reconciliation-cadence-exclude-generated-prs-2026-07-19.md`](reconciliation-cadence-exclude-generated-prs-2026-07-19.md)
fixes the **consumer** side — it stops the refresh-PR *count* from advancing the Q-0107
reconciliation cadence, so the docs-routine fires at the real doc-drift rate. It does **not**
reduce the number of refresh PRs themselves. This idea is the **producer**-side complement:
emit far fewer refresh PRs in the first place, cutting the dominant CI cost directly. The two
compose — do both and the band stops being 90%+ artifact noise *and* stops advancing the
cadence.

## The idea

Coalesce/debounce the `bot/dashboard-refresh` loop so it produces far fewer, larger PRs.
Cheapest first:

1. **Single rolling refresh PR (amend-in-place).** Keep **one** open `bot/dashboard-refresh`
   PR; each refresh tick force-pushes the regenerated artifact onto that same branch (or
   no-ops when the diff is empty) instead of opening a new PR. It merges on its own schedule
   (daily, or when a substantive PR lands). One CI run per merge, not per tick.
2. **Debounced digest cadence.** Run the export loop unchanged but only *open/merge* a refresh
   PR on a fixed cadence (e.g. once/day) or when the diff exceeds a structural-change threshold
   (`check_dashboard_data.py --drift` already computes what changed — gate the PR on a non-noise
   delta). Trivial re-serializations that don't change any surface never mint a PR.
3. **Skip-if-noise guard.** At minimum, have the loop **not open a PR when the only diff is
   `meta.build.commit` / timestamps** — the exact churn the
   [`dashboard-build-sha-post-merge-2026-07-14.md`](dashboard-build-sha-post-merge-2026-07-14.md)
   idea already flags as a dead PR-branch SHA. That single guard removes the emptiest refreshes.

## Why it's worth having

`code-quality.yml` is the repo's dominant Actions cost and already cancels superseded PR runs
(Q-0126) — but that saving is per-PR; it can't help when the churn is *many separate PRs*.
Cutting 27 refresh PRs/band down to ~1–2 is the biggest single Actions-minutes lever available
while superbot stays frozen, with zero product risk (the artifact is generated and the freshness
loop's *intent* — a fresh committed export — is fully preserved). Reversible: it changes only how
often the refresh loop opens PRs, not what it produces.

## Route

Producer lives in the `bot/dashboard-refresh` automation (the workflow that runs
`scripts/export_dashboard_data.py` and opens the PR). Owner-gated where it touches a workflow
file; the `--drift`/skip-if-noise guard in the exporter/checker is a free-to-ship docs/tooling
change. Pair with the 2026-07-19 consumer-side cadence idea for the full fix.

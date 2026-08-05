# Idea — coalesce the dashboard-refresh loop into far fewer PRs (attack the churn at the source)

> **Status:** `ideas` — session idea (Q-0089), captured 2026-07-25 (fifty-first Q-0107 reconciliation
> pass, band-#2220). Not approved for implementation. · **Class:** friction→guard · **Subsystem:**
> S4/S5 (docs-system / ops tooling — the `bot/dashboard-refresh` producer loop).
>
> **▶ COLLECTED (2026-07-27, 52nd pass) → [`planning/routine-debt.md`](../planning/routine-debt.md) item 1**
> (⚑ owner-gated — touches a workflow; the highest-leverage item in the batch).

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

**Starting point — what already exists.** `dashboard-data-refresh.yml` already reuses **one**
branch (`bot/dashboard-refresh`, force-updated) and is **scheduled every ~2h** (not per-merge), so
"one rolling PR" is *partly* built. The churn is that each 2-hourly run with drift force-updates the
PR, it auto-merges, and the next run opens it afresh — ≈one merge per cadence tick over the band.
The lever is therefore the **cadence + the per-push CI**, not the PR count.

1. **Debounce the pushes/cadence themselves — not just the PR count.** Note the trap Codex flagged
   on this PR: `code-quality.yml` triggers on **every `pull_request` update** with
   `cancel-in-progress: false` (a merge-safety invariant, `check_workflow_concurrency.py`), and the
   refresh workflow force-updates the PR branch — so *every* drift tick starts a **full,
   un-cancellable** Code Quality run regardless of how rarely the PR merges. Consolidating into one
   rolling PR alone does **not** yield "one CI run per merge." The real fix debounces the
   **force-push cadence** (e.g. lengthen the 2h schedule to daily, or only push when a real delta
   exists) — or changes the gating so an artifact-only refresh PR runs a cheap docs-lane check
   instead of the full matrix.
2. **Gate the refresh on a *feed-aware* delta — not `--drift`.** Trap #2 Codex flagged: gating
   refresh PRs on `check_dashboard_data.py --drift` would **never fire for feed-only updates**,
   because `--drift` *deliberately* compares only structural identifier sets (cogs/commands/
   env-vars/settings/catalogue keys) and **ignores the volatile feeds — ideas/sessions/bugs — plus
   timestamps/build SHA** (its docstring says so). Those feeds are exactly what the scheduled
   workflow exists to keep current, so on a frozen repo they'd go stale indefinitely. Use a
   comparison that **excludes build-only metadata (timestamp, `meta.build.commit`) but still treats
   feed-content changes as meaningful** — i.e. a purpose-built "is this a real content change?"
   check, not the structural-only `--drift`.
3. **Skip-if-noise guard.** At minimum, have the loop **not push/open a PR when the only diff is
   `meta.build.commit` / timestamps** — the exact churn the
   [`dashboard-build-sha-post-merge-2026-07-14.md`](dashboard-build-sha-post-merge-2026-07-14.md)
   idea already flags as a dead PR-branch SHA. That single guard removes the emptiest refreshes, and
   is the concrete kernel of the feed-aware delta in (2).

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

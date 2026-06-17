# dashboard.json structural-drift reporter + freshness catch-up

> **Status:** `in-progress`
> **Branch:** `claude/magical-rubin-jnpnuw` · PR (auto-merge armed on green)
> **Dispatch:** scheduled fire, empty work order. The proven ungated BTD6 floor lane is exhausted
> and the remaining queue is plan-first / owner-gated; the previous run (#1020) surfaced a concrete,
> ungated, contained tooling gap with a recorded finding **and** a captured 💡 idea — `dashboard.json`
> silently drifts with **no freshness guard** (it was ~300 lines / 3 structural surfaces stale on
> `main`). Root-level inconvenience → bugs-first lane. This run ships the executable half of that idea.

## What I'm about to do

1. Add a **non-blocking structural-drift reporter** to `scripts/check_dashboard_data.py`:
   `check_structural_drift(committed, fresh)` compares only the *structural identifier sets*
   (cogs · (cog, command) · env-var names · (domain, setting-key) · catalogue keys · synonym
   canonicals) — **never** the volatile churn (timestamps / build-SHA / ideas / sessions / bugs /
   file-line locations). Emits `warning` Issues only, so it can never redden CI (the fragility the
   previous session flagged about byte-equality). Wired behind a `--drift` flag in `main()` that
   builds a fresh export and diffs it against the committed JSON.
2. **Regenerate the stale `dashboard/data/dashboard.json`** — the actual fix: today's fresh export
   adds env-vars `HEALTH_HOST` + `RAILWAY_GIT_COMMIT_SHA` (#1020) and setting key
   `moderation_dm_actions` (#1023) that shipped but were never re-exported.
3. Tests for the reporter (synthetic added/removed → warnings; clean → none; `--drift` exits 0).
4. A short note routing the *cadence* half of the idea (regenerate-each-pass) to the
   docs-reconciliation routine, so the artifact stays fresh without burdening every session.

## Verification gate
`python3.10 scripts/check_quality.py --full` + `python3.10 scripts/check_architecture.py --mode strict`
must be green before flipping this card to `complete`.

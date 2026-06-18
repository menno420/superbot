# dashboard.json structural-drift reporter + freshness catch-up

> **Status:** `complete`
> **Branch:** `claude/magical-rubin-jnpnuw` · **PR #1025** (auto-merge armed on green)
> **Dispatch:** scheduled fire, empty work order. The proven ungated BTD6 floor lane is exhausted
> and the remaining decade queue is plan-first / owner-gated; the previous run (#1020) surfaced a
> concrete, ungated, contained tooling gap with a recorded finding **and** a captured 💡 idea —
> `dashboard.json` silently drifts with **no freshness guard** (it was ~3 structural surfaces stale
> on `main`). Root-level inconvenience → bugs-first lane. This run ships the executable half.

## What shipped

1. **Non-blocking structural-drift reporter** — `check_structural_drift(committed, fresh)` in
   `scripts/check_dashboard_data.py`. Compares only the *structural identifier sets*
   (cogs · `(cog, command)` · env-var names · `(domain, setting-key)` · catalogue keys · synonym
   canonicals) via a `_STRUCTURAL_SURFACES` table; emits **`warning` Issues only**, so it can never
   redden CI (the byte-equality fragility the #1020 session flagged). Wired behind `--drift` in
   `main()`: builds a fresh export, diffs the committed JSON, reports, exits 0. Deliberately ignores
   the volatile churn (timestamps / build-SHA / ideas / sessions / bugs / file-line numbers).
2. **Regenerated the stale `dashboard/data/dashboard.json`** — the actual fix. Verified against
   ground truth (Q-0105) that the reporter catches exactly the real drift:
   - env vars `HEALTH_HOST` + `RAILWAY_GIT_COMMIT_SHA` (shipped #1020) — never re-exported
   - setting key `moderation_dm_actions` (shipped #1023) — never re-exported
   (cogs/commands/catalogue/synonyms were *not* drifted — proving the structural-vs-churn split).
3. **Tests** (`tests/unit/scripts/test_check_dashboard_data.py`, +5) — synthetic added/removed →
   warnings; clean → none; drift findings are warn-only against live; `--drift` exits 0.
4. **Cadence half routed** — added a STEP-2 bullet to `docs/operations/autonomous-routines.md` so
   the docs-reconciliation routine regenerates `dashboard.json` each pass (it already does a docs
   pass), keeping the artifact fresh without burdening every session.

`check_quality --full` green (10472 passed, +5) · `check_architecture --mode strict` 0 · check_docs ✓.

## Decisions / deviations
- **Warn-only by construction, not by a flag.** Drift between the committed file and a fresh build
  is *expected* between regenerations (many parallel sessions touch it), so a drift finding is never
  an `error` — it would gate CI on every churn. This is the whole reason byte-equality was rejected.
- **Regenerated the JSON here** (the #1020 session deliberately did not, to keep its PR focused).
  This session's *point* is freshness, so regenerating is the deliverable's other half; the diff is
  the genuine source truth (env-vars + setting key + the routine ideas/session churn), not noise.
- `--drift` is **not** wired into the default CI run — it's an on-demand / routine-cadence reporter,
  matching the idea (a soft reporter, not a gate). The dispatch routine can run it ad hoc.

## Handoff — next agent (▶ Next action sharpened in current-state)
The dashboard.json freshness loop is now closed (warn-only reporter + cadence regen routed). No
remaining sub-step here. The ungated `ready` queue stays thin — the next empty fire should take a
**fresh PLAN-FIRST lane** (band-#1020 §4: AI §7 next workflow family · Hermes bug-triage
`gh issue create` write Q-0121) since the BTD6 floor lane is exhausted and image-mod #941 /
security #929 are Hermes-gated, dashboard manifest-spine PR4 is owner/creds-paced.

## 💡 Session idea (Q-0089)
**A generic `check_generated_artifacts_fresh.py` umbrella for the soft-drift pattern.** This session
applied the "structural-surface diff, warn-only" idea to `dashboard.json`, but the repo has *other*
committed generated artifacts (`docs/operations/env-vars.md` from `scan_env_usage`, the agent-context
packs from `tools/agent_context/build_pack.py`, `docs/agent/generated/*.context.md`). Each can
silently drift the same way. Worth having one small umbrella reporter that, per registered artifact
(generator → committed path → structural-key extractor), emits a soft "this committed artifact is N
structural surfaces behind its generator" warning — the manifest-spine "AST is drift-detection"
philosophy generalized to *every* generated-and-committed file, so no future artifact silently rots.

## ⟲ Previous-session review (Q-0102)
The #1020 run (manifest spine PR3) did the right thing twice: it **recorded the dashboard.json
staleness as an explicit 🐞 finding *and* a 💡 idea instead of silently regenerating** (which would
have buried 300 lines of parallel-session churn in an unrelated PR) — that disciplined deferral is
exactly what let *this* focused session pick it up cleanly. Its judgment that "byte-equality would
constantly redden CI" was also correct and directly shaped this implementation (warn-only sets, not
equality). **One improvement it surfaces for the system:** the repo had *no inventory* of
"committed generated artifacts" — each (`dashboard.json`, `env-vars.md`, the context packs) is
guarded (or not) in isolation, so the same drift class keeps being re-discovered per-artifact. A
single registry of generated-and-committed artifacts (captured as the 💡 above) would turn a
recurring per-artifact discovery into one systemic guard.

## 📤 Run report
- **What:** shipped the warn-only `dashboard.json` structural-drift reporter + regenerated the stale
  export + routed cadence-regen to the reconciliation routine (PR #1025).
- **Next:** fresh PLAN-FIRST lane (AI §7 family or Hermes bug-triage write Q-0121); BTD6 floor lane
  exhausted, image-mod/security Hermes-gated, dashboard PR4 owner-paced.
- ⚑ Owner-decisions: none.
- ⚑ Owner-manual-steps: none.

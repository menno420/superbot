# Plan — `check_loop_health.py` gh-absent fallback (control-plane row, script-verifiable)

> **Status:** `plan` — executable. Promoted from
> [`ideas/loop-health-gh-unavailable-fallback-2026-06-19.md`](../ideas/loop-health-gh-unavailable-fallback-2026-06-19.md)
> by the band-#1170 reconciliation pass (2026-06-20, Q-0172 idea→plan gate). Ungated, disposable
> tooling (Q-0105). **Not docs-only — this is a `scripts/` change for a dispatch/executor session, not
> the reconciliation routine** (the reconciliation pass that promoted it stays docs-only).

## Problem (the gap this closes)

The Q-0107 reconciliation routine's STEP 2 control-plane reconcile runs
`python3.10 scripts/check_loop_health.py` (Q-0135) to verify the § Control-plane state table. But in the
in-container routine environment **`gh` is not installed/authenticated**, so the script reports
`SKIP — gh unavailable` on **every** cadence pass (band-#1050, #1080, #1110, #1140, and **#1170** —
observed again this pass). The routine's manual fallback — read the newest auto-opened `reconcile` issue's
*author* (a real-user login = `ROUTINE_PAT` set; `github-actions[bot]` = unset) — works every time, but
the *script* (the whole point of Q-0135) is silently non-functional in the one place it is meant to run.
So the ROUTINE_PAT row is only ever verified by a manual MCP read **no checker can see**.

## Goal

Make the ROUTINE_PAT verdict verifiable **by the script**, not only by hand, with zero new runtime deps
and a clean delete path if it proves flaky.

## Approach (one PR, ungated, self-merge on green)

`scripts/check_loop_health.py` today shells out to `gh` and degrades to SKIP when `gh` is absent. Add a
`gh`-absent fallback that performs the same read over the **GitHub REST API using stdlib `urllib`** (no
new dependency), authenticated with `GITHUB_TOKEN` from the environment.

1. **Refactor the issue fetch behind a small provider seam.** Keep the existing pure `classify(issues)`
   core (it already derives the verdicts from a list of issue dicts — see the module docstring). Introduce
   two fetchers feeding the same dict shape:
   - `_fetch_via_gh()` — the existing `gh issue list --json ...` path (unchanged).
   - `_fetch_via_rest()` — new: `GET https://api.github.com/repos/menno420/superbot/issues?state=all&labels=reconcile&sort=created&direction=desc&per_page=10`
     via `urllib.request` with `Authorization: Bearer $GITHUB_TOKEN` + `Accept: application/vnd.github+json`,
     parsed with stdlib `json`. Pull the same fields `classify` consumes (title, `user.login`, `state`).
     Also fetch the `Postgres backup failed` open issues for the DATABASE_PUBLIC_URL row, same as `gh`.
2. **Selection order:** try `gh` first (works in dev shells / Actions); on `FileNotFoundError`/non-zero,
   fall to `_fetch_via_rest()` when `GITHUB_TOKEN` is set; only if **both** are unavailable, emit the
   current SKIP — but make the SKIP **actionable**: print the manual instruction ("read the newest
   `reconcile` issue's author via the GitHub MCP — real-user login = ROUTINE_PAT set").
3. **Label the verdict source** in the output (`(via gh)` / `(via REST)` / `SKIP`) so a reader knows which
   path produced it.
4. **Tests** (`tests/unit/scripts/test_check_loop_health.py`): the `classify` core is already pure — add
   cases that (a) a real-user author → ROUTINE_PAT PASS, (b) `github-actions[bot]` author → FAIL, (c) an
   open backup-failed issue → DATABASE_PUBLIC_URL FAIL, (d) empty issue list → SKIP-with-instruction.
   The REST fetcher is mocked (no live network in CI). `pytest.importorskip` not needed — `urllib`/`json`
   are stdlib.

## Out of scope / non-goals

- Railway env-var deploys + console routine model/prompt config (rows 3–5) stay maintainer-verified — the
  REST API cannot see them; the script must not claim otherwise.
- No new runtime/dev dependency (`urllib` + `json` only).

## Verification

```
python3.10 scripts/check_loop_health.py            # advisory; now (via REST) when GITHUB_TOKEN is set
python3.10 -m pytest tests/unit/scripts/test_check_loop_health.py -v
python3.10 scripts/check_quality.py --check-only
```

## Disposability (Q-0105)

Convenience drift-guard, **not load-bearing**. If the REST read misclassifies across a few passes (rate
limits, token scope), **delete the fallback** and revert to the manual MCP read — the routine prompt
already documents it. Keep the provenance header on the script.

→ relates `scripts/check_loop_health.py` · `docs/operations/autonomous-routines.md` § "Control-plane
state" · the Q-0135 control-plane reconcile step.

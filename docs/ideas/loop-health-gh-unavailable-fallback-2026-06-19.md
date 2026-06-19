# Idea — `check_loop_health.py` should fall back when `gh` is unavailable

> **Status:** `ideas` — capture only. **Not a plan, not approval.** Session idea (2026-06-19, Q-0089,
> from the band-#1110 reconciliation pass). Workflow/tooling. Quick-win, disposable (Q-0105).

## The observation

The Q-0107 reconciliation routine's STEP 2 control-plane reconcile says to run
`python3.10 scripts/check_loop_health.py` (Q-0135) and reconcile the § Control-plane state table
against its PASS/FAIL/SKIP verdicts. But in the in-container reconciliation environment **`gh` is not
installed/authenticated**, so the script reports:

```
check_loop_health: SKIP — `gh` unavailable or unauthenticated (control-plane not probed).
```

This has now happened on **every recent cadence pass** (band-#1050, band-#1080, band-#1110). The routine
prompt already prescribes the manual fallback — read the newest auto-opened `reconcile` issue's *author*
via the GitHub MCP (`menno420` = `ROUTINE_PAT` set; `github-actions[bot]` = unset) — and that fallback
works every time. So the *script* is the part that is silently non-functional in the one place it is
supposed to run.

## The idea

Give `check_loop_health.py` a **`gh`-absent fallback path**: when `gh` is missing, fall back to the same
read the agent does by hand — query the newest `reconcile`/trigger issue's author via the GitHub REST API
(token from the environment) or, failing that, accept a cached/passed-in author value — and emit the
ROUTINE_PAT verdict from that instead of a blanket SKIP. Then the routine's control-plane row is
verifiable **by the script** (the Q-0135 intent) rather than only by a manual MCP read that no checker
can see.

Keep it disposable (Q-0105): stdlib + optional `requests`/`urllib`, no new runtime dep, and **delete it
if the GitHub-API read proves flaky across a few passes**. If the API path is also unavailable in the
container, the script should at minimum print the *manual* fallback instruction (the issue-author read)
so the SKIP is actionable, not a dead end.

## Why it's worth having

The control-plane table is exactly the surface that drifted before 2026-06-14 (it claimed the loop had
never self-fired when live GitHub already proved it had). The whole point of Q-0135 was a *script* that
re-checks that truth — but a script that SKIPs in its only runtime is back to a human-only check. Closing
the fallback gap makes the loop genuinely self-auditing in the environment it audits from.

→ relates `scripts/check_loop_health.py` · `docs/operations/autonomous-routines.md` § "Control-plane
state" · the Q-0135 control-plane reconcile step.

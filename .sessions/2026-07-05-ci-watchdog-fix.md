# 2026-07-05 — CI watchdog self-silencing fix + next-agent handoff

> **Status:** `in-progress` — born-red gate (Q-0133). Held until the fix is verified (tests green,
> CLI degrades cleanly, lint/docs green) and the handoff lands.

## What this session is doing (born-red declaration)

Closeout of the CI-setup arc (PRs #1737, #1739). The owner: *"properly complete the open items and then
close out with a preparation for a next agent."* The #1 open item — the **CodeQL merge-race** — is now
CLOSED (the owner enabled the `codeql-merge-protection` ruleset). This session completes the other real
defect and hands off the rest.

1. **`check_ci_coverage.py` — fix the self-silencing bug (§C.3 Mode 2 / A2).** The old check treated the
   *presence* of a `code-quality` check-run name as "covered" — so a `workflow_dispatch` re-kick (which
   produces a run *named* `code-quality`) silenced the watchdog even if that run never satisfied the PR's
   required check → the PR stalled forever. Rewrote it to classify by **triggering event**: only a
   `pull_request`/`push` run counts as covered; a completed `workflow_dispatch` re-kick that produced no
   PR-event run **escalates** to an owner-alert issue instead of self-silencing. Robust to the one thing
   offline testing can't confirm (whether a dispatched run satisfies the required check) — correct either
   way it resolves. Pure logic unit-tested (13 tests); gh I/O degrades cleanly.
2. **Correct the overstated re-kick comment** in `code-quality.yml` (it claimed a dispatched run *satisfies*
   the required check — that's exactly the unverified assumption the fix removes).
3. **[`docs/planning/ci-followups-handoff-2026-07-05.md`](../docs/planning/ci-followups-handoff-2026-07-05.md)**
   — the turn-key, ranked backlog for the next agent (live-verification first, then ruff migration, the
   `ci.yml`/`web-ci.yml` restructure, the stuck-scan watchdog, the two AST guards, and the owner-gated tail).
4. Reflect the **live CodeQL ruleset** in the design doc + what-runs-where map (codeql is now a merge gate).

# Session — CI strand root cause: code-quality cancel-in-progress (2026-06-22)

> **Status:** `complete`

Owner-directed (continuing the CI-flake investigation; owner's logic narrowed it). **Root cause of
the "CI didn't run on my latest commit" strands — CONFIRMED, not a hypothesis this time:**

`code-quality.yml` had `concurrency: cancel-in-progress: true` for PR refs (added 2026-06-20, #1195,
Q-0126 — to save minutes). Under the born-red flow's **rapid event burst** (open → push → push within
~2 min), GitHub's cancellation **races and drops the run for the head commit**, leaving the PR with no
passing required check → auto-merge stalls.

**Smoking gun:** on the *same* `pull_request: synchronize` event/commit (`64e4f86` on PR #1274),
`codex-final-review` (`cancel-in-progress: false`) **ran**, while `code-quality`
(`cancel-in-progress: true`) **did not**. Same trigger, same commit — the only difference was the flag.
This also explains the owner's key observation that *fix-pushes used to always re-run CI*: before
#1195 (June 20) code-quality had no cancellation, so every push got its own run.

This **supersedes** my two earlier wrong theories (synchronize inherently flaky; merge-ref
unavailable) — both disproved here (codex used the same synchronize event; #1274 is `blocked`, not
`dirty`). The owner's "something changed recently" + "too many checks/events" instincts were both right.

## Fix
- `code-quality.yml`: `cancel-in-progress: false` (matching codex). The cost rationale is moot — public
  repo, **unlimited** Actions minutes — so cancelling buys nothing and costs reliability. Redundant
  older-commit runs are free.

## Also
- Updated `docs/audits/dashboard-autopr-conflict-rootcause-2026-06-21.md` §6 — the "wider mystery"
  is now **resolved** (cancel-in-progress), correcting the earlier unconfirmed hypotheses.
- pytest analysis (the "why 4 min / only new tests?" question) — see chat + the audit doc: it's
  already parallelized (`-n auto`); "only new tests" is unsafe (misses regressions); the real lever is
  the slow-test long tail (profiled).

## Note on flow
Deviated from born-red (open red first) on purpose: pushed everything incl. this complete card, then
opened the PR once — so it rides the reliable `opened` event, not a post-open `synchronize`, while the
fix isn't yet live. Dogfoods the "avoid the strand" pattern.

No runtime `disbot/` code.

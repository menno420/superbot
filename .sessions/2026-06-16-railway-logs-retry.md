# Session — railway_logs.py: retry/backoff on transient 5xx

> **Status:** `complete`

## What I'm about to do

A live log-triage run (`railway_logs.py -n 20`) failed with `Railway API HTTP 503: upstream connect
error … reset reason: connection timeout` on the `deployments` query — a transient Railway-side
gateway 5xx. A plain retry seconds later succeeded, confirming it was a blip. But the script has a
30s timeout and **no retry**, so a single transient 5xx fails the whole `superbot-log-triage` Hermes
skill.

Harden the shared GraphQL `post()` in `scripts/hermes/railway_logs.py` with bounded
retry-with-backoff on retryable statuses (429/500/502/503/504) and connection-level errors
(URLError/timeout), honoring `Retry-After` on 429. Non-retryable 4xx and GraphQL-error bodies still
raise immediately (no masking of auth/bad-request failures). Injectable `sleep` + `max_retries` keep
the unit tests hermetic and fast.

## What was done

- `scripts/hermes/railway_logs.py`: `build_poster()` now retries inside `post()` — `max_retries=3`
  extra attempts (4 total) with exponential backoff (`backoff_base=0.5` → 0.5s/1s/2s). Retries on
  `RETRYABLE_STATUS = {429, 500, 502, 503, 504}` and on `URLError`/`TimeoutError` (connect/DNS/read
  timeouts). A 4xx other than 429, or a GraphQL-error body, still raises immediately — no masking of
  real auth/bad-request failures. New `_retry_delay()` honours a numeric `Retry-After` header
  (capped 30s) and is otherwise exponential. `sleep`/`max_retries`/`backoff_base` are injectable.
- `tests/unit/scripts/test_railway_logs.py`: +7 tests — retry-then-succeed (503 and connection
  error), exhaust-retries-then-raise (asserts attempt count + backoff sequence), no-retry-on-4xx,
  and `_retry_delay` exponential + `Retry-After`/cap behaviour.
- Live trigger: a `railway_logs.py -n 20` run 503'd on the `deployments` resolver, a manual retry
  succeeded — confirming the transient blip this hardens against (auth/token were already fine).

`check_quality --full` green (9980 passed, 37 skipped); arch unaffected (script lives outside
`disbot/`).

## 💡 Session idea

Apply the same bounded retry/backoff to `railway_vars.py` (the sibling Hermes tool sharing the same
Cloudflare-fronted backboard endpoint) — it has the identical single-shot transport and will fail on
the same transient 5xx. Small, mirrors this PR. (Dedup: not in `docs/ideas/`; it's a direct
extension of this fix, so noting here rather than a new idea file.)

## ⟲ Previous-session review

The prior session (the #936 manual-test bug fixes) did the diagnosis-from-video well and recovered
cleanly from a wedged shell via a worktree sub-agent. What it *missed* and this surfaces: the shell
wedged because a `cd disbot` left cwd inside the repo where the path-relative pre-commit hooks
(`scripts/check_branch_freshness.py`) can't resolve — and the harness only auto-resets cwd when it's
*outside* the project. **Concrete workflow improvement:** pin the hook commands to
`$CLAUDE_PROJECT_DIR/scripts/...` (or `cd "$CLAUDE_PROJECT_DIR"` inside each hook) so a stray `cd`
can't brick Bash/Edit for the rest of a session. That's an executable-config change (Q-0106 → owner
applies), so it belongs as a router DISCUSS Q-block rather than a self-edit.

# 2026-06-12 — 429 login rate-limit crash-loop fix (PR #729)

**PR:** [#729](https://github.com/menno420/superbot/pull/729) — `fix: sleep 60s
before exit when login returns 429 to break crash loop`
**Trigger:** owner-uploaded log showing the bot crashing and restarting 4× in ~2
minutes, each cycle hitting a Discord/Cloudflare 1015 rate limit.

## What happened (the incident)

The bot hit Cloudflare's HTTP 1015 (429 Too Many Requests) during `bot.start()`.
That raised `discord.HTTPException(status=429)`, exiting with code 1. Railway's
on-failure restart policy relaunched within ~2 s → same rate limit → same crash,
repeating 4× before the ban naturally lifted. The full Cloudflare HTML page was
logged as the error body (141 lines of noise).

## What shipped

`_maybe_backoff_on_rate_limit(exc)` — called from the `__main__` crash handler.
When the startup crash is specifically a `discord.HTTPException(status=429)`, the
function sleeps 60 s before the process exits so the platform restart fires after
the backoff has already elapsed. Non-429 crashes are completely unaffected.

Extracted as a module-level helper (matching `_exit_code_after_main`) so it is
directly unit-testable. 5 new tests added alongside the existing exit-code contract
tests in `tests/unit/runtime/test_restart_exit_code.py`.

## Context delta (reflection interview)

1. **Route miss:** None — the `__main__` block and its exit contract were the only
   relevant surfaces; `grep "Critical startup error"` found them in one shot.
2. **Route excess:** None; tiny scope.
3. **Discovered by hand:** The Cloudflare 1015 response body is HTML, not JSON,
   so `discord.HTTPException.code` is `0` (the Discord-specific code field only
   parses JSON). The correct detection is `exc.status == 429`, not `exc.code`.
4. **Decisions made alone:**
   - Backoff value = 60 s (no prior art in the repo). Rationale: the ban lifted
     within ~3 min in the incident log, and 60 s × 4 retries = 4 min. Reasonable
     first value; trivially tunable.
   - `time.sleep` in the process (not asyncio.sleep + re-raise) — correct because
     `asyncio.run(main())` has already raised by this point; there is no event loop
     to await in.
5. **Weak point:** 60 s may not be enough if the IP is banned for longer; we don't
   do exponential backoff across multiple restarts (each process restart is
   stateless). If Cloudflare bans for > 60 s the loop will still cycle, just more
   slowly. A counter persisted to the DB (or a simple `STARTUP_RATE_LIMIT_ATTEMPTS`
   env var incremented externally) could enable adaptive backoff — not worth it yet.
6. **One change that would have helped:** The 141-line Cloudflare HTML dumped into
   the error log is noise. Extracting the Ray ID from the body (`Ray ID: <hex>`)
   would make future incidents diagnosable in one line instead of 141. → session
   idea below.

## 💡 Session idea (Q-0089)

**Extract the Cloudflare Ray ID from 429 responses for one-line incident records.**

Currently `_maybe_backoff_on_rate_limit` logs a generic "sleeping 60s" message.
The Cloudflare HTML body contains a `Ray ID: <16-hex-char>` tag that uniquely
identifies the rate-limit incident and is the string you'd give Cloudflare support.

Proposal: regex `r'Ray ID:\s*([a-f0-9]+)'` against `exc.text` inside
`_maybe_backoff_on_rate_limit`; if found, log:

```
Login rate-limited (Cloudflare 1015, Ray-ID: a0a962fe781b0eab); sleeping 60s
```

instead of the current bare message. This turns a 141-line HTML wall into a
single actionable line in prod logs. Purely additive to the fix already shipped;
zero risk; one regex + one test change. The Ray ID is also worth storing in Postgres
for rate-limit frequency analysis (pairs with gap-analysis §5 AI spend metering).

Dedup: not in `docs/ideas/`; directly extends the fix in PR #729.

## Grooming pass

Gap-analysis §4 (session telemetry — quick-win lane, owner-granted 2026-06-11):
added a lightweight `📊 Telemetry` footer block to `.sessions/README.md` so every
session log captures four measurable counters (PRs merged, CI-red rounds, repo-rule
trips, ideas contributed). The heavier "caretaker weekly rollup" half stays
un-executed (roadmap Someday); the footer itself is live from this session.
Gap-analysis §4 updated to reflect the partial execution.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (PR #729 open, CI pending) |
| CI-red rounds | 0 (local `check_quality --full` green before push; CI in progress) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (Ray ID extraction, above) |
| Ideas groomed | 1 (gap-analysis §4 partial execution) |

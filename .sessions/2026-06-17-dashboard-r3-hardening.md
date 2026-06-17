# Session — dashboard R3: live-surface hardening (rate-limiting + CSRF)

> **Status:** `complete`

## What I'm about to do (born-red declaration, Q-0133)

Continuation of the overnight dashboard run (Phase E shipped #1013). The finalized-vision plan's reviewer
note **R3** flags the live control panel's two hardening gaps: it is **public + live** but has **no
rate-limiting** (control API or the public login) and only `SameSite=Lax` — **no explicit CSRF token** on
the editor forms. Neither is a write-authorization hole (the bot still gates every write via the live
member + audited seam), but the surface is live, so these are the named near-term hardening items.

**Planned (this PR):**

1. **CSRF token on the dashboard editor forms.** A per-session token (stored in the signed session cookie)
   embedded as a hidden field in every `/admin/{guild}` POST form; the POST handlers reject a missing/
   mismatched token (constant-time) before calling the control API. Stronger than the cookie's `Lax`.
2. **Rate-limit the public login** (`/auth/login`, per client IP) and **the edit POSTs** (per acting user) —
   a small stdlib sliding-window limiter (`dashboard/ratelimit.py`).
3. **Rate-limit the bot control API writes** (defense-in-depth) — a per-(guild,user) sliding window in
   `disbot/control_api.py`'s shared write context; exceeding it returns HTTP 429.

All additive; the control-API limiter is dormant-safe (only active when the API is). No change to the
audited-seam write path. Tests for the limiter + the CSRF reject + the 429.

## What shipped (PR #1014 — R3 hardening)

**CSRF token on the editor forms (`dashboard/`):**
- `_ensure_csrf` mints a per-session token (stored in the signed session cookie) on the `/admin/{guild}`
  GET; `_csrf_ok` constant-time-compares the submitted token in `_edit`. Every one of the six editor forms
  (settings ×2, help/overlay, help/home, routing ×2) now carries a hidden `csrf_token`. A missing/wrong
  token is refused **before** any control-API call, with a "stale form — reload" flash.

**Rate-limiting:**
- `dashboard/ratelimit.py` — a stdlib `SlidingWindowLimiter` (per-key, window-based, rejected calls don't
  consume budget). Wired in `app.py`: `/auth/login` per client IP (10 / 5 min), edit POSTs per acting user
  (40 / min) — over-budget → a "slow down" flash, no control call.
- `disbot/control_api.py` — a per-`(guild, user)` write limiter (60 / min) in the shared
  `_authed_write_context`; exceeding it returns **HTTP 429**. Defense-in-depth (the dashboard already
  limits); reads are unlimited; dormant-safe.

**Tests (24 new):** `test_ratelimit.py` (5, CI-runnable — stdlib, deterministic `now`); control-API 429 +
an autouse limiter-reset fixture; dashboard CSRF reject (missing + wrong token) + edit-rate-limit + the
existing POST test updated to submit a valid token.

**Verification:** `check_quality --full` green; `--check-only` all green; arch 0. The `importorskip`
dashboard suite run for real under `python3.10`. No change to the audited-seam write path.

**Process note (lesson for next session):** ran `black` *before* `ruff --fix`/`isort`, so black then
disagreed with their output → a `check_quality` black failure. Fix order is **isort → ruff → black**
(black last) for idempotency. Also: a bare `black --check .` flags files CI excludes (the
`(\.github|tests|venv|env|build|dist)` regex catches `env`/`build` substrings like `scan_env_usage`);
trust `check_quality`, not a raw `black .`. Third: **moving code in a file that references an env var
drifts `docs/operations/env-vars.md`** (it records `file:line`) — `--full` caught it via
`test_scan_env_usage`; refresh with `python3.10 scripts/scan_env_usage.py --write-doc` and commit the doc.
Net takeaway: only `check_quality --full` (not `--check-only` or targeted tests) catches this generated-doc
+ mypy class — always run it before flipping a card.

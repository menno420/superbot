# Session — dashboard R3: live-surface hardening (rate-limiting + CSRF)

> **Status:** `in-progress`

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

## What shipped

_(filled in at close)_

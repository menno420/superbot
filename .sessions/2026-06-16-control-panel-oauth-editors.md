# Session — control panel: Discord OAuth login + web editors (write side, step 2)

> **Status:** `complete`

## Origin

Owner directive (in-session, 2026-06-16): *"finish these steps completely — (2) the website's Discord
OAuth login + editors."* This is **step 2**, the website half, on top of #989 (control API + bridge) +
#993 (mutation endpoints). The owner confirmed the parallel session is done; `list_pull_requests` was
clean. Builds the **free, multi-user control panel**: anyone signs in with Discord and edits the
servers they administer.

## What shipped (this PR — dormant until the owner sets the secrets)

A complete login → pick-server → edit loop on the decoupled dashboard, every write flowing through the
bot's control API → existing audited seam (the website never writes the DB):

- **`dashboard/auth.py`** — Discord OAuth2 (`identify guilds` scopes): consent URL, code→token, the
  user + guild-list fetch, and the admin-guild filter (owner or `ADMINISTRATOR`). Dormant until
  `DISCORD_OAUTH_CLIENT_ID` / `_SECRET` / `_REDIRECT_URI` are set.
- **`dashboard/control_client.py`** — httpx client to the bot control API (`worker.railway.internal`),
  bearer-authed with `CONTROL_API_TOKEN`. Dormant when the token is unset (editor shows "not
  connected"); the authority bridge call + the `POST` over each seam.
- **`dashboard/websession.py`** — a **stdlib HMAC-signed-cookie session** (no `itsdangerous`, no
  middleware). See the constraint note below.
- **`dashboard/app.py`** — `/auth/login` · `/auth/callback` · `/auth/logout`; `/admin` (the admin-guild
  picker) · `/admin/{guild_id}` (the editor); and the `POST` handlers for settings / help-overlay /
  help-home / cog-routing, each gated on the session admin + PRG-redirecting with a flash. Forms are
  parsed with `urllib.parse.parse_qs` (stdlib — no `python-multipart`).
- **Templates** — `admin.html` (sign-in / setup / guild picker), `admin_guild.html` (the three
  editors), and the nav login state in `base.html` (via a Jinja context processor).
- **The bot stays the authority.** The browser asserts identity; the bot resolves the live member and
  the seam enforces real permissions on every write (#993). The session cookie is signed + httponly; a
  forged cookie reads as empty.

## The no-network constraint → stdlib session (why no itsdangerous / multipart)

This environment has **no PyPI access for new packages**, so `itsdangerous` (SessionMiddleware) and
`python-multipart` (form parsing) could not be installed — which made `tests/unit/dashboard/test_app.py`
skip entirely, leaving the templates **unverified** (the #979 trap). Fix: drop both deps — a small
stdlib HMAC-signed cookie + `urllib` form parsing — so the whole app is verifiable with just
`fastapi` + `jinja2` + `httpx` (already present). Leaner *and* testable; same security shape as a
signing library.

## Verification

- `pip install -r dashboard/requirements.txt` + `python3.10 -m pytest tests/unit/dashboard/` →
  **42 passed** (the editor page renders for a logged-in user via a minted signed cookie; dormant
  login/redirect paths; the OAuth/client logic + admin-guild filter).
- `python3.10 scripts/check_quality.py --check-only` → green (black/isort/ruff over the CI scope
  incl. `dashboard/`; check_docs). No `disbot/` change → mypy/bot-suite unaffected.

## Owner setup to activate (nothing changes in prod on merge)

On the **dashboard** Railway service: `DISCORD_OAUTH_CLIENT_ID`, `DISCORD_OAUTH_CLIENT_SECRET` (Reset
in the Discord portal → paste into Railway, never chat), `DISCORD_OAUTH_REDIRECT_URI` =
`https://superbot-dashboard.up.railway.app/auth/callback`, `DASHBOARD_SESSION_SECRET` (long random),
`CONTROL_API_TOKEN` (same value as the bot worker), and `CONTROL_API_URL` if not the default
`http://worker.railway.internal:8080`. On the **bot worker**: `CONTROL_API_TOKEN` (same value) +
confirm Railway private networking. Then the bot's control API + this login both wake up.

## 💡 Session idea (Q-0089)

**A `/admin/{guild}` "current values" read panel.** The editors currently write blind (you type a
setting/help value; the bot validates). Add control-API **GET** endpoints (`/control/settings/current`,
`/control/help/overlay`) so the editor shows the guild's *current* per-server value beside each field —
turning blind edits into see-then-change. Small, additive, read-only; the natural next control-API
slice once the write side is proven.

## ⟲ Previous-session review (Q-0102) — #993 (mutation endpoints)

**Did well:** fronted the audited seams cleanly (the bot stays the authority; dormant-by-default
preserved), mapped seam errors to precise HTTP codes, and 28 focused tests with the seams mocked.
**Could've flagged sooner:** it listed "aliases" as a seam but there's no audited synonym-overlay yet —
worth a one-line "aliases-live needs a new overlay" call-out in the PR body so the gap is unmissable
(it was in the session card but easy to miss). **System improvement:** when a directive lists N targets
and one lacks a seam, the PR description should explicitly enumerate *built vs deferred* targets so the
owner sees the gap without reading the code — a small honesty-of-scope habit.

## 📋 Documentation audit (Q-0104)

`check_docs --strict` green. New dashboard env vars (`DISCORD_OAUTH_*`, `DASHBOARD_SESSION_SECRET`,
`CONTROL_API_URL`) are **dashboard-side only** — `scan_env_usage` scans `disbot/`, so they don't enter
`docs/operations/env-vars.md`; they're documented in `admin.html`'s setup panel + this card +
(next) the dashboard README. Nothing from this session lives only in chat.

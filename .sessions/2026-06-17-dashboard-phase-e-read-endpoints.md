# Session — dashboard Phase E: control-API read endpoints (stop the editors writing blind)

> **Status:** `complete`

## What I'm about to do (born-red declaration, Q-0133)

Owner directive (overnight, unattended): *"execute as much of the [finalized dashboard] plan as you
possibly can … sync to latest main every once in a while … routines will work on the bot/btd6 plans so
they won't conflict."* The finalized-vision plan flags **Phase E** as the **top next priority**: the
live help/settings/cog-routing editors shipped (#993/#996) but **write blind** — they POST a new value
yet never show the server's *current* one, because the control-API **GET** endpoints don't exist. This
session builds them and turns the editor into **see-then-change**, then continues down the roadmap as
far as it can safely go.

**Planned slices (one PR on this branch, modular commits):**

1. **Phase E — control-API read endpoints (bot side).** Add to `disbot/control_api.py`, dormant-by-default
   like the rest of the surface, token-gated, per-guild authority-gated:
   - `GET /control/settings/current` — every subsystem's resolved current values (value · default ·
     provenance · valid · value_type · hint · allowed_values · capability) via `settings_resolution`.
   - `GET /control/help/overlay` — the guild's current help overlay (rows + Home) via `help_overlay`.
   - `GET /control/help/catalogue` — the editable hub/subsystem targets + their defaults.
   - `GET /control/routing` — the guild's current cog-routing rows via `command_routing.list_for_guild`.
2. **Dashboard wiring (see-then-change).** `control_client.get()` + the `/admin/{guild}` route fetches
   live current state and the editor renders it: per-setting inline editors pre-filled with the current
   value (default badge + capability), current help overlay shown, current cog on/off state shown.
3. **R3 live-surface hardening (reviewer note).** Rate-limit the control API + the public login; add an
   explicit CSRF token to the editor forms (today only `SameSite=Lax`).
4. **Phase C read workspace (remainder).** A per-server **overview** (authority + setup-health summary)
   and the **authority preview** ("you may read / you may change") over the new reads + the bridge.

Bot changes are **additive + read-only + dormant-by-default** (zero behaviour change with no token).

**Scope settled while building:** this PR (#1013) ships **slice 1 (Phase E) only** — a complete,
high-value, reviewable deliverable. **R3 hardening** and the **Phase C read workspace** ship as
**follow-up PRs on this same branch** (reset-to-main between each), keeping risky-runtime PRs small
(CLAUDE.md). The global-settings hot-path tier (Q-0157) + the manifest spine (Phase D) stay deferred to
their own focused sessions — not cramming a hot-path change into an overnight batch.

## What shipped (PR #1013 — Phase E)

**Bot — `disbot/control_api.py` (additive, read-only, dormant without `CONTROL_API_TOKEN`):**
- `GET /control/settings/current` — every subsystem's resolved current scalar settings, composing the
  canonical read path (`settings_resolution.resolve_batch`: value · provenance · valid) with the
  declaring `SettingSpec` (type · default · hint · allowed-values · governing capability). Admin-gated.
- `GET /control/help/overlay` — the guild's current help overrides + Home message. Admin-gated.
- `GET /control/help/catalogue` — the editable hub/subsystem targets + defaults. Token-only (global).
- `GET /control/routing` — the guild's current cog-routing rows. Admin-gated.
- New `_authed_read_context` (the GET mirror of `_authed_write_context`) + the four routes registered
  alongside the existing writes. 15 new unit tests (auth/params/404/403/admin-gate/serialization).

**Dashboard — `dashboard/`:**
- `control_client.get(path, params)` — the read sibling of `post` (dormant→503, unreachable→502).
- `/admin/{guild}` now fetches live current state (when the bot says you're an admin) and the editor
  renders **see-then-change**: per-setting inline editors pre-filled with the current value + a
  default/customised/invalid badge + governing capability; current help overrides shown + a real
  target picker from the catalogue + the Home form pre-filled; current per-cog enabled/disabled with a
  one-click toggle. Degrades cleanly to the prior blind forms when the reads fail/aren't configured.
- 2 new dashboard tests (the `get` dormant path + the see-then-change render — `importorskip`-guarded).

**Verification:** `check_quality --full` green (10307 passed) + `--check-only` all green; arch 0 errors;
the `importorskip` dashboard suite run for real under `python3.10` (fastapi installed) — the template
renders live values with no Jinja error. Every write still flows the audited seams (no parallel truth).

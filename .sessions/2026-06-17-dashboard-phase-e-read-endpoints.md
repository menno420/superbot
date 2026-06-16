# Session — dashboard Phase E: control-API read endpoints (stop the editors writing blind)

> **Status:** `in-progress`

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
Sync to main between slices. Defer the global-settings hot-path tier (Q-0157) + the manifest spine
(Phase D) to their own focused sessions — not cramming a hot-path change into this PR.

## What shipped

_(filled in at close)_

# Session — control API mutation endpoints (write side, step 1)

> **Status:** `complete`

## Origin

Owner directive (in-session, 2026-06-16): *"finish these steps completely — (1) mutation endpoints on
the control API, each over an existing audited seam (settings, help, cog routing, aliases) so the
website can write, not just read; (2) Discord OAuth login + editors."* This is **step 1** (the bot
runtime). The owner confirmed the parallel "mutation-endpoints session" is done; a clean
`list_pull_requests` + active-work scan (Q-0126) showed nothing in flight on `control_api.py`.

## What shipped (this PR — still dormant by default)

`disbot/control_api.py` gains five **POST** endpoints on the existing private control surface, each
fronting an **existing audited seam** (never a new write path — the CLAUDE.md blocker rule):

| Endpoint | Seam | Authority |
|---|---|---|
| `POST /control/settings` | `settings_mutation.SettingsMutationPipeline.set_value` | the pipeline's capability gate (`actor_holds_capability`) |
| `POST /control/help/overlay` | `help_overlay_mutation.set_overlay_fields` | the seam's `_check_admin` |
| `POST /control/help/home` | `help_overlay_mutation.set_home_message` | the seam's `_check_admin` |
| `POST /control/help/reset` | `help_overlay_mutation.reset_guild_overlay` | the seam's `_check_admin` |
| `POST /control/routing` | `command_routing.set_policy` | **handler-enforced** admin gate (that seam doesn't self-authorize — its in-bot caller does) |

- **The bot stays the authority.** Every request resolves the **live member** (`resolve_member`, not a
  raw `guild.get_member`) for `(guild_id, user_id)`; the seam (or the routing handler) enforces the
  same permission/capability gate every in-Discord surface uses. The dashboard's "who am I" claim is
  never trusted — the token only proves *the dashboard* is calling, never *who* the user is.
- **Still dormant** (routes register only when `CONTROL_API_TOKEN` is set) → zero production change on
  merge. Each seam validates → writes → invalidates cache → emits `audit.action_recorded`; the handler
  maps the seams' typed errors to HTTP codes (400 caller error · 403 authority · 503 kill-switch).
- The help-overlay endpoints honor the seam's `UNSET` sentinel: an **omitted** field is left
  untouched, a `null` field resets to inherit, a value overrides.

## Not in this PR (deliberate)

- **Live alias editing** has **no audited DB seam yet** — only the committed `utils/synonyms.py`
  `COMMAND_SYNONYMS` map. Making aliases live-editable needs a new synonym-overlay (migration + db +
  mutation service + `find_command` integration), a greenfield sub-build the plan already defers. The
  `/aliases` + `/commands` suggest→PR flow remains until then.
- **Discord OAuth login + editors** (owner step 2) — the website half — is the next PR.

## Verification

- `python3.10 -m pytest tests/unit/runtime/test_control_api.py` → **28 passed** (16 from #989 + 12 new:
  auth, body validation, guild/member resolution, the UNSET forwarding, the routing admin gate, and
  seam-error → HTTP mapping; seams mocked so no DB).
- `python3.10 scripts/check_quality.py --full` → green (10250 passed) after regenerating
  `docs/operations/env-vars.md` (the `CONTROL_API_TOKEN` reference line moved).
- `python3.10 scripts/check_architecture.py --mode strict` → 0 errors (`control_api` is composition-root
  infra; its `services` imports are allowed, like `healthserver`).

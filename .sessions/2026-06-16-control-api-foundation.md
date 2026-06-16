# Session — control-API foundation (bot side): auth + identity→authority bridge

> **Status:** `in-progress`

## Origin

Owner: *"yes go ahead"* — start the bot-ready foundation for the control panel (Q-0156/Q-0159). This
is the first runtime slice: a private control API on the bot so the decoupled dashboard can (read now,
edit later) drive the bot's existing audited seams. The owner is also setting up the Discord OAuth app
in parallel.

## What shipped (this PR — read-only, dormant-by-default)

- **`disbot/control_api.py`** — a `/control/*` surface added to the **existing** health server
  (`healthserver.py`), so no second server. **Dormant by default:** routes register **only** when
  `CONTROL_API_TOKEN` is set, so merging changes nothing on the current production bot. Every request
  needs `Authorization: Bearer <token>` (constant-time compared). Two read endpoints:
  - `GET /control/ping` — auth smoke.
  - `GET /control/authority?guild_id=&user_id=` — **the identity→authority bridge**: resolves the
    live member and reports the same visibility tier (`utils.visibility_rules`) every in-Discord
    surface uses, plus `is_admin` / `is_owner`. `tier=None` when the bot isn't in the guild or the
    user isn't a member there. The browser's "who am I" claim is never trusted — the bot decides.
- **`healthserver.py`** — calls `register_control_routes(app, bot)`, wrapped so a control-API issue
  can **never** break the health server / bot startup (the orchestration probes must always come up).
- Fail-safe + dormant + private-network-only + token = layered safety; no mutation endpoints yet
  (those land next, each over its existing audited seam).

## Repo invariants complied with (not suppressed)

- **Guild-resource resolver** (`test_guild_resources_invariant`): used `core.runtime.guild_resources.
  resolve_member` instead of a raw `guild.get_member`.
- **Architecture atlas** (`test_atlas`): registered `control_api` in `context_map.TOP_LEVEL_MODULES`
  (it's composition-root infra like `healthserver` — it can't live in a layer since it will import
  `services` for mutations) + updated the atlas test's allowed layer-less set.
- **Env-var doc** (`test_scan_env_usage`): regenerated `docs/operations/env-vars.md` for the new
  `CONTROL_API_TOKEN`; it now appears on the dashboard `/env` map too.

## Verification

- `python3.10 scripts/check_quality.py --full` → **green (10225 passed, 37 skipped)** — black/isort/
  ruff (CI scope) + mypy `disbot/` + full pytest.
- `python3.10 scripts/check_architecture.py --mode strict` → exit 0.
- New tests: `tests/unit/runtime/test_control_api.py` (auth, dormant-by-default, the authority bridge,
  handlers — 16 cases).

## How to activate (when the owner is ready — NOT done by this merge)

Set `CONTROL_API_TOKEN` (same value) on both the `worker` (bot) and `dashboard` Railway services; the
dashboard then calls `http://worker.railway.internal:8080/control/...` with the bearer token. Until
then the surface does not exist. **Merge ≠ activation.**

## 💡 Session idea (Q-0089)

**A "dormant-by-default runtime feature" pattern doc + checklist.** This PR established a reusable
shape for safely adding risky runtime surfaces to a production bot: *env-gated activation + fail-safe
wiring (never breaks startup) + private-network-only + token auth + atlas registration + a documented
activation runbook*. Capturing it as a short pattern (and a tiny `scripts/` checklist) would let the
coming control-API mutation PRs — and any future network/integration surface — follow the same proven
safety rails instead of re-deriving them.

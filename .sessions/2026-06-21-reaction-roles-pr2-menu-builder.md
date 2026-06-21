# 2026-06-21 — Reaction-roles PR 2: in-Discord role-menu builder

> **Status:** `complete` — PR 2 of the reaction-roles overhaul
> ([plan](../docs/planning/reaction-roles-overhaul-plan-2026-06-21.md)): the modern in-Discord
> role-menu builder (Surface B). Built in parallel with PR 1 (the foundation), then **reconciled
> onto PR 1 after it merged as #1220** — this branch now sits on PR 1's authoritative
> `reaction_role_service` / `utils/db/role_menus` / migration 078, with PR 2's menu methods +
> view/builder layered on top. Full CI green; boot-verified.

> **Run type:** `manual` · **PR:** #1219 (`needs-hermes-review`)

## Arc

The modern button/dropdown self-role surface Carl-bot lacks at its core (plan §4 PR 2 / Surface B,
owner decisions §9). **Dropdown is the default** (decision #2); server-side mode enforcement
(`unique` / `verify` / `max_roles`) means no stale reactions and an ephemeral confirm per click.

- `views/roles/role_menu_view.py` — `RoleMenuView(PersistentView)`: dropdown or one-button-per-role,
  restart-durable via static `role_menu:{menu_id}:*` custom_ids + `reattach_role_menus()` wired into
  `bot1.on_ready`. Deliberately **not** registered in the anchor registry (it's a public data-driven
  message re-bound by its own loop, not a per-user anchor panel — registering collided with
  `RoleHubPanelView`'s `SUBSYSTEM='role'` and tripped the identity-contract check; caught at boot).
- `views/roles/role_menu_builder.py` — operator builder + manager off the Reaction Roles panel:
  title/description, windowed role picker, style/mode/limit, **theme presets** (§4.6b), **template
  gallery** (§4.6c), **edit-in-place** (§4.6a, re-render → `message.edit`).
- `utils/role_menu_presentation.py` — theme + template catalogues (pure data on `ui_constants`).
- Service additions on PR 1's `reaction_role_service` — `create_menu`/`update_menu`/`delete_menu`
  (audited), `toggle_role` (button) + `apply_selection` (dropdown) with server-side mode enforcement;
  member self-assign is **not** audited (high-volume + opt-in, §9). Two DB helpers added to PR 1's
  `role_menus.py`: `replace_options` (transactional full-list replace) + `list_posted_menus` (reattach).

## ⚙️ PR 1 reconciliation (the headline coordination)

PR 1 was built in a parallel session and **merged as #1220** mid-session. A workflow auto-merged
`main` into this PR branch. PR 1's actual API diverged from the plan's "recommended" copy
(`get_options` not `get_menu_options`, `set_menu_message`, `delete_for_guild`, **no `template`
column**, `theme` NOT NULL, no `replace_options`/`list_posted_menus`). Reconciled by resetting to
PR 1's foundation, restoring only PR 2's non-overlapping files, then layering the menu methods onto
PR 1's real API + dropping `template` *persistence* (the gallery still pre-fills). PR 1's
`test_reaction_role_service.py` (emoji) + `test_guild_lifecycle_teardown.py` + `test_role_menus.py`
all kept intact; my menu tests live in a separate `test_reaction_role_service_menus.py`.

## ✅ Verification

`python3.10 scripts/check_quality.py --full` → **11165 passed, 10 skipped**, mypy clean.
`check_architecture --mode strict` → 0 errors. **Booted the test bot** (Galaxy Bot#6724): cogs load,
migration 078 applied, `reattach_role_menus` runs, no Traceback, identity-contract warning resolved.
Not live-interaction-tested in Discord (no interactive click harness here) → `needs-hermes-review`.

## 📤 Run report

- **Did:** built reaction-roles PR 2 (in-Discord role-menu builder, Surface B) + reconciled onto
  PR 1's merged foundation · **Outcome:** shipped to PR #1219 (`needs-hermes-review`, CI green)
- **Shipped:** #1219 (this PR, human-merge-gated) — builds on #1220 (PR 1, merged)
- **Run type:** `manual`
- **⚑ Self-initiated:** none (owner-requested: build PR 2→5 of the reaction-roles overhaul; this
  session delivered PR 2 end-to-end + the PR-1 reconciliation)
- **⚑ Owner manual steps:** review + merge #1219 (runtime UI; merge ≠ deploy — prod restart stays
  the maintainer's). Then PR 3/4/5/6 are unblocked.
- **↪ Next:** PR 3 (Carl-parity modes on the emoji surface + interactive emoji panel + settings
  bridge) · PR 4 (free temp roles — `role_grants` migration **079** + expiry sweep loop) · PR 5
  (role-pickup analytics, §10) · PR 6 optional (PIL banner cards). All ride the PR 1+2 seam.

## 💡 Session idea (Q-0089)

**CI guard: a registered `PersistentView` whose `SUBSYSTEM` isn't in `SUBSYSTEMS` should fail the
build, not just warn at boot.** This session's `SUBSYSTEM='role_menu'` mistake surfaced only as a
runtime `bot.identity_contract` **warning** at boot — the strict identity test (`test_identity_
contract_strict.py`) stayed green. A small invariant that iterates `persistent_views._REGISTRY` and
asserts every `SUBSYSTEM` ∈ `SUBSYSTEMS` (the parity the boot check already computes) would catch
this class pre-merge instead of needing a live boot. Cheap, stdlib-only, closes a "boot caught it,
CI didn't" gap. (Filed mentally; would be a `tests/unit/registry/` invariant.)

## ⟲ Previous-session review (Q-0102)

**Reviewed: the PR 1 foundation session (#1220).** *Did well:* a clean, well-tested audited seam +
data layer + teardown + a faithful migration that honored the owner-locked `dropdown` default and the
§4.6b `theme` column. *Could have gone better:* its DB/service **API names diverged** from the plan's
"recommended shape" copy that PR 2 was told to build against (`get_options` vs `get_menu_options`,
no `replace_options`/`list_posted_menus`, `template` dropped) — which made the parallel-PR-2
reconciliation non-trivial (rename every `menus_db.*` call, drop template persistence). **System
improvement it surfaces:** when a *foundation* PR and its *consumer* PR are built in parallel, the
foundation session should publish its **exact public signatures early** — either by pushing an API
stub first or by updating the plan's code block with the final names — so the consumer builds against
the real API, not a guessed copy. A lightweight convention worth adding to the parallel-execution
guidance in `ai-project-workflow.md` §9. (This is the internal-mirror of the Hermes-reviewer loop:
each session audits its predecessor's seams.)

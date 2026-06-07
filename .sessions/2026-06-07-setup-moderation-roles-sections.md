# 2026-06-07 — Setup wizard: moderation + roles sections (server-management PR11)

- **Arc:** "identify the next main thing, plan it, execute." Orientation route landed on
  the `current-state` ▶ Next action = **server-management PR11** (setup
  role/moderation/governance sections). Branch `claude/fervent-sagan-GdJz9`. Verified live
  GitHub (no open PRs); mapped the setup-section architecture (registry + `SetupOperation`
  dispatch + draft staging + Final-Review apply gate) via an Explore agent + direct reads.
- **Scope question (Q-0008, router):** PR11 bundles three sections, but source analysis
  showed only **moderation** maps cleanly (pure `set_setting`), **roles** needs a small new
  op-kind, and **governance** is genuinely ambiguous (its main write — cleanup — is already a
  wizard section). Maintainer chose **"Moderation + Roles"**; Governance deferred.
- **PR1 — Moderation section** (`views/setup/sections/moderation.py`, order 65, commit
  5bdd51d): surfaces PR10's moderation config via existing `set_setting` drafts
  (`dm_on_action` / `require_reason` / `warn_escalation_action` / `moderator_role`).
  Four-row detail view (usable as both card-Customize and wizard step-detail); recommended
  builder = DM-on-action + require-a-reason. No new infra, no migration.
- **PR2 — Roles section** (`views/setup/sections/roles.py`, order 55, commit dde45e0):
  time/XP auto-role tiers for existing roles. Added a new **`set_role_threshold`** op-kind to
  `setup_operations.py`, routed through a new audited **`role_automation.set_{time,xp}_threshold`**
  seam (a service + `emit_audit_action`, not raw DB — mirrors the `set_cog_routing`
  no-pipeline pattern; threshold writes previously had no audited seam). Final Review gained
  an explicit `role_threshold` apply phase.
- **Findings / gotchas:**
  - The Explore agent said `moderator_role`/`trusted_role` are *bindings*; the schema
    (`cogs/moderation/schemas.py`) shows they're **settings** (`SettingSpec`, role-id string).
    Source won — staged as `set_setting`, not `bind_role`. (Verify cross-agent output.)
  - Draft values round-trip as **strings**; `_coerce_for_write` (settings) and an explicit
    `int(op.value)` (threshold arm) coerce back. The identity section is the canonical
    `set_setting`-from-setup example.
  - **`guild.get_role(...)` trips the no-raw-guild-lookups invariant** (only caught by the
    *full* suite, not `--check-only`). Routed both new call sites through
    `core.runtime.guild_resources.resolve_role` (commit dc402b0). Lesson: run
    `check_quality --full` before trusting "lint clean."
  - `setup_draft.append` takes `section_slug=` → pass it for accurate progress badges;
    leave `op_kinds` empty for shared `set_setting` (per identity) but set it
    (`{"set_role_threshold"}`) for the roles-specific kind.
- **Gates:** `check_quality.py --full` green (7901 passed, mypy + black/isort/ruff +
  check_docs); `check_architecture --mode strict` 0 errors. **Live-booted** (Galaxy
  Bot#6724): both sections register (15 total), `set_role_threshold` known, 0
  ERROR/CRITICAL.
- **Deferred:** the **governance** setup section (Q-0008) — needs a scope decision (cleanup
  already owns the main governance write; capability-override/command-access is a separate
  feature). Next committed lane: **PR12** (setup diagnostics & repair).
- **State:** `docs/current-state.md` + the server-management
  [status tracker](../docs/planning/server-management-status-2026-06-05.md) PR11 subsection.

# 2026-06-30 — Bot-owner override: completeness follow-up (view gates + command decorators)

> **Status:** `in-progress`

**Run type:** owner-directed (bug report — "It still does not work", screenshot)

## What I'm about to do

#1573 (Q-0212) gave the bot owner full config authority at the governance / service / setup-access /
canonical-view seams — but the owner **still hits "❌ Administrator permission required."** (owner
screenshot). Root cause: #1573's view sweep was **incomplete** (its grep was truncated at 50 results),
so two whole gate classes were missed:

1. **View `interaction_check`s never routed through the canonical helper:** the entire
   `views/ai/policy/*` family (channel / category / role / chooser / list / preview), `views/ai/routing/
   matrix.py`, and `views/{xp,roles}/main_panel.py`. These do raw `guild_permissions.administrator`
   checks → deny the owner. **This is the screenshot bug** (AI policy = "the AI and which channels").
2. **Cog command decorators:** `@commands.has_permissions(administrator=True)` (101) +
   `@app_commands.checks.has_permissions(administrator=True)` (28) gate `!ai`, `/setup`, etc. *before*
   the body/view runs — `is_platform_owner` never touched these, so the owner can't use admin-config
   commands directly.

**Plan (complete + guarded this time):**
- New `core/runtime/permission_checks.py`: `admin_or_owner()` (prefix) + `app_admin_or_owner()` (slash)
  — administrator OR `config.is_platform_owner`, raising the same `MissingPermissions` for non-owners.
- Route every remaining view admin `interaction_check` / `_admin` helper through
  `views.base.interaction_is_admin` / `member_is_admin`.
- Replace every `has_permissions(administrator=True)` decorator (both forms) with the owner-aware check.
- **Guards (friction → guard, the exact miss-class):** a CI test that fails if (a) any view does a raw
  `guild_permissions.administrator` check outside the canonical helpers, or (b) any cog uses
  `has_permissions(administrator=True)` instead of `admin_or_owner`. These would have caught #1573's miss.
- Tests for the new checks; update Q-0212 / capability-authority with the decorator + view seams.

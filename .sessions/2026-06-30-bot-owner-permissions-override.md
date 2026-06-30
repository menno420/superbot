# 2026-06-30 — Bot-owner platform-admin override (full config authority in any guild)

> **Status:** `in-progress`

**Run type:** owner-directed (in-session request)

## What I'm about to do

Owner request: *"as bot owner I always have full bot permissions in any server that I'm in, even if
I don't actually have permissions there — not to alter the server, but to make sure the bot is
properly set up and has the right settings enabled, like the AI and which channels it can do
certain things in."*

**Finding (research):** the bot already treats the configured owner (`config.BOT_OWNER_USER_ID`,
the documented `PLATFORM_OWNER` tier) specially for **AI scope** (`_derive_scope` →
`AIScope.PLATFORM_OWNER`), **global settings** (owner-only), and a **bootstrap-command channel
bypass** (`command_access.py`). But there is **no** owner override for *per-guild configuration
authority*: a bot owner who is a plain member of a guild resolves to `tier="user"` and is denied
by every guild-config seam (settings/AI-policy/setup/governance). So today the owner can *open*
`!settings`/`!setup` (bootstrap bypass) but cannot actually apply AI / channel / setup changes.

**Plan — one source of truth, wired into every authority seam (additive: only ever GRANTS the
configured owner; one-user blast radius keyed on exact id match):**

1. `config.is_platform_owner(user_id)` — single canonical helper (config is a leaf importable by
   every layer; conceptually the right home for the deploy-declared owner id).
2. Governance: `capability.actor_holds_capability` (settings/binding/resource mutations),
   `resolver._resolve_member_tier` (visibility + `resolve_execution`/`can_execute`),
   `writes._validate_authority` (governance writes = per-channel subsystem visibility).
3. Services: the 5 duplicated `_check_admin` gates (ai_policy / ai_instruction / ai_orchestration /
   btd6_source / help_overlay) + `setup_access` (is_setup_admin / can_apply_setup / by-id).
4. Views: `base.interaction_is_admin` (canonical) + the inline raw-`guild_permissions` config gates
   (AI panel / behavior / tools, settings command-access, essential_setup) so the owner can *see &
   use* the config UI, not just pass the mutation check.
5. Consolidate the existing inline `== BOT_OWNER_USER_ID` checks onto the new helper.

Tests per seam (grant for owner, unchanged for non-owner), docs + a router Q-block recording the
owner decision, then flip this card to `complete`.

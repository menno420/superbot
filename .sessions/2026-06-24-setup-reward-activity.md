# Session — 2026-06-24 · Essential Setup step "Reward activity"

> **Status:** `in-progress` — born-red hold. Additive to `EssentialFlow` (no new cog/command/artifact);
> a 2-screen step. Reuses existing audited services — no new service needed.

**Trigger:** owner-directed (chat, 2026-06-24): build the spine's "Reward active members" step. Owner
chose: toggle role rewards (both/one/none), selectable XP ranges, **an extra step to choose the reward
role** (preset / create-your-own / reuse existing) — all via buttons/dropdowns/multi-selects.

## What I'm about to do

Add a **`RewardActivityStep`** to `EssentialFlow` (a 2-screen step via an internal `phase`):
- **Screen 1:** XP-rate dropdown (Keep current / Relaxed / Standard / Active → sets `xp_min`/`xp_max`/
  `xp_cooldown` via `SettingsMutationPipeline`) + a reward-types multi-select (level-up roles /
  time-in-server roles — both/one/none).
- **Screen 2** (only when ≥1 reward type is on): choose the reward role — **Recommended** (auto-create
  `@Regular`) / **Create one I name** (suggested-name dropdown) / **Reuse an existing role** (RoleSelect).
- On Save: set the XP rate if changed; for each enabled trigger call `role_automation.set_xp_threshold`
  (level 10 default) / `set_time_threshold` (30 days default); auto-create via `RoleLifecycleService.apply
  (operation="create")`. All services lazy-imported per the setup-view convention.

**Research notes (corrects an earlier assumption):** `role_automation.set_xp_threshold` /
`set_time_threshold` ALREADY provide the direct-apply audited path (guild_id/role_id/role_name/level|days/
actor_id) — so **no new service is required** (the context-delta "one genuine gap" was wrong). XP has **no
guild enable toggle** (always-on, per-user opt-out via participation) — so the step tunes rate + rewards,
it doesn't "turn XP on".

<!-- close-out written as the final step -->

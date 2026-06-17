# Session — per-action moderation DMs (Q-0147 standing DM policy)

> **Status:** `in-progress`

## What I'm about to do (born-red declaration, Q-0133)

Scheduled dispatch, empty work order. The live ▶ Next action names **moderation-DM config** as the
next ungated startable: per-action moderation DMs on the existing `moderation_service` seam, off by
default ([moderation-dm-config-plan-2026-06-17](../planning/moderation-dm-config-plan-2026-06-17.md),
Q-0147). Bug-book OPEN entries are infra-side (BUG-0011 Hermes/Telegram, needs live repro) or already
fixed (BUG-0010), so this is the right buildable slice.

**Planned slice (one PR, `disbot`-runtime, no migration):**
Turn the moderation `dm_on_action` master switch into an owner-controlled **per-action** DM policy:
1. `MOD_DM_ACTIONS` settings key (`moderation_dm_actions`) + re-export.
2. `moderation_config`: `DEFAULT_DM_ACTIONS`, a `dm_actions` field on `ModerationPolicy`, a
   `dm_action_set` parsed/validated property, and resolution in `load_policy`.
3. `moderation_service._notify_target`: gate on master **and** per-action membership.
4. `cogs/moderation/schemas.py`: a `dm_actions` `SettingSpec` (the "clear way to configure which
   actions trigger a DM" Q-0147 requires) + relabel `dm_on_action`'s hint as the master switch.
5. Tests covering master-off, master-on+in-list, master-on+not-in-list, closed-DM fail-open, and the
   `dm_action_set` parse/reject-unknown-token path.

**Deliberate deviation from the plan (documented):** the plan defaults `dm_actions` to `"warn,timeout"`.
But today, with `dm_on_action=True`, **all four** notify-eligible actions (warn/timeout/kick/ban) DM —
two existing service tests pin that. Defaulting to `"warn,timeout"` would silently stop kick/ban DMs
for guilds that already enabled the master switch (a behaviour change for configured guilds). So the
default is **`"warn,timeout,kick,ban"`** — the master switch keeps exactly today's behaviour and the
new field lets an owner *narrow* it. `auto_delete` is intentionally **not** in the vocabulary: it is a
system action that never reaches `_notify_target`, so listing it would be dead/misleading config (the
owner's "auto-delete → DM no" is structurally guaranteed).

Off by default (master `dm_on_action=False` unchanged), fail-open, no migration, no new mutation path.

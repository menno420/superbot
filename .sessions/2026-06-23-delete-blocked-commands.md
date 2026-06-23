# 2026-06-23 — Delete command-style messages in not-allowed channels (tied to Command Access)

> **Status:** `in-progress` — owner-directed. The owner's old bot instantly deleted any command typed in
> a channel where commands weren't allowed; restore it, tied to the existing **Command Access** setting,
> with a brief auto-deleting notice (owner answered the design question this session). Open PR born-red
> per Q-0133; flip to `complete` as the final step.

> **Run type:** `manual · owner-directed`

## What I'm about to do

The bot already has **Command Access** (`guild_command_access_policy`, migration 050): per-guild modes
`all_channels` / `selected_channels` / `disabled_except_bootstrap`. Today a denied command is silently
*not executed* — but the user's message stays. The owner wants it **deleted on sight** (their old-bot
behavior), gated behind an opt-in toggle, with a brief "commands aren't allowed here" notice that
auto-deletes.

Implementation (tied to Command Access, owner's choice):

1. **Migration 096** — add `delete_blocked_commands BOOLEAN NOT NULL DEFAULT FALSE` to
   `guild_command_access_policy`.
2. **`utils/db/command_access.py`** — read the column in `get_policy`; add `set_delete_blocked_commands`
   (upsert, defaults mode `all_channels` if no row yet).
3. **`utils/guild_config_accessors.py`** — add `delete_blocked_commands: bool` to
   `CommandAccessPolicySnapshot` + loader.
4. **`services/command_access_service.py`** — `set_delete_blocked_commands` mutation (6-step pattern:
   read prev → write → invalidate → audit).
5. **`core/runtime/command_access.py`** — a `from_message` adapter so the cleanup cog can build a
   `CommandAccessContext` from a raw `discord.Message` (operator + bot-owner classification reused).
6. **`cogs/cleanup_cog.py`** — in `remove_unwanted_message`, for a command-style message: if the guild's
   `delete_blocked_commands` is on AND `resolve_command_access` denies with reason `CHANNEL_NOT_ALLOWED`
   / `COMMANDS_DISABLED`, delete instantly + post the decision feedback as a brief auto-deleting notice.
   (Bootstrap/operator commands are exempt — the resolver allows them; DM/lifecycle denials never delete.)
7. **`views/settings/edit_command_access.py`** — a "🗑️ Delete blocked commands: On/Off" toggle button +
   embed line.
8. Tests across db/service/accessor/resolver-adapter/cog/UI.

**Operator UX:** `!settings → Command Access → Delete blocked commands`. Off by default (no behavior
change for anyone who doesn't enable it).

## What shipped

_(filled in at close)_

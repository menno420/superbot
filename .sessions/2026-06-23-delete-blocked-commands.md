# 2026-06-23 — Delete command-style messages in not-allowed channels (tied to Command Access)

> **Status:** `complete` — owner-directed. The owner's old bot instantly deleted any command typed in
> a channel where commands weren't allowed; restored it, tied to the existing **Command Access** setting,
> with a brief auto-deleting notice (owner answered the design question this session). PR #1359,
> auto-merge armed on green (Q-0127); owner-directed → merge immediately (Q-0191).

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

An opt-in per-guild "delete commands in not-allowed channels", wired into Command Access end-to-end:

- **Migration 096** — `delete_blocked_commands BOOLEAN NOT NULL DEFAULT FALSE` on
  `guild_command_access_policy` (default OFF → zero behaviour change until enabled).
- **`utils/db/command_access.py`** — `get_policy` now selects the column; `set_delete_blocked_commands`
  upsert (seeds the safe default mode `all_channels` if no row exists, so the toggle works before a mode
  is chosen; never overwrites mode on conflict).
- **`utils/guild_config_accessors.py`** — `delete_blocked_commands: bool = False` on
  `CommandAccessPolicySnapshot` + loader.
- **`services/command_access_service.py`** — `set_delete_blocked_commands` mutation (6-step: read prev →
  write → invalidate cache → audit; no-op skips the audit row) + new `MutationType`.
- **`core/runtime/command_access.py`** — `from_message` adapter (build a `CommandAccessContext` from a
  raw `discord.Message`; reuses the operator/bot-owner classification; tolerant of a missing bot).
- **`cogs/cleanup_cog.py`** — `_delete_if_command_blocked`: in the auto-mod path, a command-style message
  in a channel where Command Access denies it (reason `CHANNEL_NOT_ALLOWED` / `COMMANDS_DISABLED`) is
  deleted on sight + a brief `_BLOCKED_COMMAND_NOTICE_SECONDS` (8s) auto-deleting notice — **only** when
  the guild enabled the toggle. The snapshot read is defensive (a policy-read hiccup never crashes
  auto-mod). Bootstrap/operator commands are admitted by the resolver and never reach the delete; DM /
  lifecycle denials are explicitly excluded.
- **`views/settings/edit_command_access.py`** — a "🗑️ Delete blocked commands (toggle)" button (row 2,
  Back moved to row 3) + an embed field showing the On/Off state.
- **Tests** — +21 across db (column select + upsert), service (write/no-op/default/actor-guard), runtime
  (`from_message` builds/operator/owner/missing-bot), cog (deletes-with-notice · toggle-off-falls-through
  · access-allowed-no-delete · other-denial-reason-no-delete), and UI (embed state + toggle flips +
  admin guard). Full suite 12055 green; mypy clean; arch 0.

**Operator UX:** `!settings → Command Access → 🗑️ Delete blocked commands`. Off by default.

## Findings / decisions

- **Why "nothing changed" before:** the cleanup *level* (Off/Light/Standard/Strict) only deletes a
  command when that command's subsystem is *also hidden* in the channel — so setting a channel to "Strict"
  did nothing on its own. The owner's real ask ("delete commands where commands aren't allowed") maps to
  **Command Access**, which already knows allowed-vs-not channels but only *refused* the command silently.
  This PR makes that denial *delete* (opt-in).
- **Owner decision (in-session, via AskUserQuestion): tie delete-on-sight to Command Access**, not a
  standalone cleanup flag, and show a **brief auto-deleting notice**. Recorded here as the provenance.
- **Opt-in, not automatic.** Servers already using `selected_channels`/`disabled` modes didn't necessarily
  want deletion; a default-OFF toggle avoids surprising anyone. The owner enables it once.
- **Integration point = the cleanup auto-mod path**, not the command entry handler — the cleanup cog's
  regex already inspects *every* message (including command-shaped gibberish like `!notacommand`), which
  is exactly the "any command" the owner wants caught; the entry handler only sees parsed invocations.

## 💡 Session idea

**Surface the cleanup-vs-command-access distinction in the Cleanup Policies diagnostics embed.** This
session's root finding — that a cleanup *level* only deletes when the subsystem is *also* hidden — is a
genuine footgun: an operator sets "Strict" and reasonably expects commands to be deleted, but nothing
happens. The diagnostics panel could add a one-line note ("cleanup levels act on *blocked* commands;
to delete commands in a no-command channel, use Command Access → Delete blocked commands") so the two
systems' relationship is legible at the point of confusion. (Dedup-checked `docs/ideas/` — no existing
cleanup/command-access-legibility idea.)

## ⟲ Previous-session review (Q-0102)

The previous session (remove the whitelist, #1350) was the right call and set this one up well — but in
hindsight it removed the *only* "delete commands in these channels" mechanism the bot had, and the
follow-up note correctly anticipated that exemption now lives in cleanup policies *without* noticing that
the **inverse** (delete-on-sight) had no good home either. That's the gap this session fills. **System
improvement (initiated):** when a session *removes* a feature (even legacy), its close-out should
explicitly ask "what capability did users lose, and where does its replacement live?" — the whitelist
removal answered that for *exemption* but not for *deletion*. A one-line "capabilities removed → their new
home" entry in the removal session's run report would have surfaced the delete-on-sight gap immediately
rather than waiting for the owner to report "still hasn't changed much."

## 📤 Run report

- **Did:** Restored "instantly delete commands in not-allowed channels" as an opt-in Command Access
  toggle (migration + db + service + accessor + `from_message` adapter + cleanup-cog integration + UI
  toggle), with a brief auto-deleting notice · **Outcome:** shipped (PR #1359, auto-merge armed on green)
- **Shipped:** #1359 — delete command-style messages in not-allowed channels
- **Run type:** `manual · owner-directed`
- **⚑ Owner decisions needed:** none (the design choice was the owner's own AskUserQuestion answer:
  tie-to-Command-Access + brief notice)
- **⚑ Owner manual steps:** none — merged = deployed (Railway auto-redeploys `worker` on merge; migration
  096 runs on boot). **To turn it on:** `!settings → Command Access → 🗑️ Delete blocked commands` (it is
  OFF by default).
- **⚑ Self-initiated:** no — owner-directed (the "delete commands where commands aren't allowed" request).
- **↪ Next:** Part 2 of the owner's feedback — the **button/select-driven Custom cleanup level** (replace
  the typing modal) — is the immediate follow-up PR.

## ⟳ Doc audit (Q-0104)

`check_docs --strict` green; `check_consistency` 0 errors; arch 0; mypy clean. New audited mutation
(`set_delete_blocked_commands`) documented in-code + the session log. The PR isn't in `current-state`
Recently-shipped yet (benign newest-merge lag — recorded by the next reconciliation pass; #1350-band
recon is the routine's job, not this manual session — Q-0124).

# Karma subsystem — folio

> **Status:** `living-ledger` (area index). Source + `docs/current-state.md` win.
> **Last updated:** 2026-06-22 (built — owner-directed; plan
> [`planning/karma-reputation-plan-2026-06-22.md`](../planning/karma-reputation-plan-2026-06-22.md)).

## What & where

Karma is **peer reputation** (thanks/upvote): members grant each other karma, a
signal distinct from XP (activity) and coins (economy) — it measures how much the
community values you. The architecture mirrors economy/XP 1:1 (audited service seam
→ EventBus emit → cog → leaderboard provider).

- **DB:** `disbot/utils/db/karma.py` + migration `disbot/migrations/093_karma.sql`
  (two tables: `karma` running totals · `karma_audit_log` append-only history).
- **Service (the only write seam):** `disbot/services/karma_service.py` —
  `give(...)` / `get_record(...)`. INV-K (`tests/unit/invariants/test_inv_k_karma_service.py`)
  forbids any other caller of the write primitives.
- **Config read model:** `disbot/services/karma_config.py` (`KarmaPolicy` / `load_policy`)
  over the `karma_*` KV settings (`disbot/utils/settings_keys/karma.py`); schema in
  `disbot/cogs/karma/schemas.py`.
- **Cog (command surface):** `disbot/cogs/karma_cog.py`.
- **Leaderboard:** `KarmaProvider` in `disbot/services/rank_providers.py` (category
  `karma`, aliases `rep`/`reputation`/`karmalb`).

## Commands

- `!thanks @user [reason]` (aliases `!rep`, `!thank`) — grant one karma.
- `!karma give @user [reason]` — same grant via the karma group.
- `!karma [@user]` — show a member's karma card (points, rank, received/given).
- `/karma [member]` — ephemeral karma card.
- `!leaderboard karma` (or `!leaderboard rep`) — the karma leaderboard.

## Data model

- **`karma`** (PK `user_id, guild_id`): `karma_points` (clamped ≥ 0),
  `received_count`, `given_count`, `last_received`.
- **`karma_audit_log`** (append-only): `id`, `occurred_at`, `guild_id`, `from_user`,
  `to_user`, `delta` (signed — leaves room for a future downvote), `source`
  (`command`/`reaction`), `reason`. **Doubles as the anti-abuse source of truth** —
  `recent_grant_count` (cooldown) and `grants_given_since` (daily cap) read it, so
  there is no separate cooldown table.

## Rules & invariants (binding)

- **Positive-only** — `give` rejects `amount <= 0`; there is no downvote command.
- **No self-karma, no bot-karma** — self-grant raises `SelfKarmaError` in the
  service; bot recipients are rejected in the cog before the service is called.
- **Anti-farm** — per-(giver → receiver) cooldown (`KARMA_COOLDOWN`, default 1h) and
  per-giver rolling-24h cap (`KARMA_DAILY_CAP`, default 10). Both enforced in the
  service; a blocked grant writes nothing.
- **Audited seam** — every grant writes `karma_audit_log` and emits `karma.granted`
  (`guild_id`, `from_user`, `to_user`, `delta`, `new_total`, `source`). INV-K guards
  the write primitives against direct callers.
- **Settings** — `karma_enabled` (default on), `karma_cooldown`, `karma_daily_cap`,
  operator-editable via `!settings`.

## Free-for-everyone (Q-0190)

Karma is pure social reputation — non-spendable, no paywall, no P2W.

## Current state

- **Shipped (2026-06-22):** the command surface (`!thanks`, `!karma`, `/karma`), the
  audited service + DB seam, the leaderboard category, operator settings, and the
  governance-subsystem registration (homed under the **Community** hub, `parent_hub:
  "community"` — the hub view now wraps buttons past 5/row to fit it).

## Plans / pending (deferred)

- **Reaction-grant (react-to-thank)** — ✅ **shipped 2026-07-01 (PR #1620).** React with the guild's
  configured trigger emoji (`karma_reaction_emoji`, empty = off) to grant karma to the message author;
  the `on_raw_reaction_add` listener in `karma_cog` routes through the same audited
  `karma_service.give(source="reaction")` seam (cooldown + daily cap + self-give guard apply), silent,
  byte-identical when unset.

Per the plan's recommended defaults, the rest of **PR 3 stays deferred** (owner-gated):
- **Karma roles** — auto-assign a role at thresholds (e.g. "Trusted Helper" @ 50).
- **Milestone announcements** — a `karma.milestone` event + optional log channel.

# 2026-06-21 — Reaction roles: multi-role emoji bindings + menu reuse

> **Status:** `in-progress` — born-red HOLD (Q-0133). Owner-directed refinement (Q-0191 →
> merge immediately on green, not `needs-hermes-review`).

> **Run type:** `manual`

## What I'm about to do

Owner asked to refine the shipped reaction-roles feature on two points the overhaul plan
(`docs/planning/reaction-roles-overhaul-plan-2026-06-21.md`, PRs 1–5 merged) did **not** cover:

1. **Multiple roles per emote reaction.** Today the legacy emoji surface is one-role-per-emoji
   (`reaction_roles` PK `(guild_id, message_id, emoji)`). Widen the PK to include `role_id`
   (migration 082, purely additive) so one emoji can grant several roles; update the DB layer,
   the audited `reaction_role_service` (read/apply *all* roles for a reacted emoji), and the
   `ReactionRolesPanel` Add flow (accept one-or-more emojis + a **multi-role** picker).
2. **Reuse a configured menu again.** Today a saved role menu can only be edited in place or
   deleted — if its message is deleted there's no way to get it back, and you can't clone it.
   Add **📤 Repost** (re-post a saved menu to its channel) and **📋 Duplicate** (clone a menu
   as a new one) to `RoleMenuListView`.

Verify with `python3.10 scripts/check_quality.py --full` + `check_architecture.py --mode strict`.

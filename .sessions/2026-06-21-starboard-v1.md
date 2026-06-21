# 2026-06-21 — Starboard PR 1 (foundation + working v1)

> **Status:** `in-progress` — born-red HOLD (Q-0133). **⚑ Self-initiated** — executes the #1254
> Starboard plan (idea B1). Q-0191 → merge on green.

> **Run type:** `manual`

## What I'm about to do

Build the working v1 of Starboard / Hall-of-Fame per `docs/planning/starboard-plan-2026-06-21.md`,
reusing the hardened raw-reaction seam (reaction-roles #1234–#1250):

- **migration `082_starboard.sql`** — `starboard_settings` (guild_id PK, channel_id, threshold,
  emoji='⭐', enabled) + `starboard_entries` (PK guild_id+source_message_id, starboard_message_id,
  star_count). *(self_star/ignore-channels/XP deferred to PR 2 — kept v1 lean.)*
- **`utils/db/starboard.py`** — typed CRUD (pool.* only here) + export in `utils/db/__init__.py`.
- **`services/starboard_service.py`** — audited `configure`/`disable` + `handle_star_change` (the
  recount→post/edit/delete decision; no Discord I/O).
- **`cogs/starboard_cog.py`** — `on_raw_reaction_add/remove` (filter to the configured emoji; recount
  live; delegate) doing the Discord post/edit/delete + a `!starboard` config command. Register in
  `bot1.py` + `guild_lifecycle` teardown.
- Tests mirroring `test_reaction_role_service*`.

Verify: `check_quality.py --full` + `check_architecture.py --mode strict`.

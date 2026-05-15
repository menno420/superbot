-- Migration 005: Fix single-user-id PKs that prevent multi-guild isolation.
-- rps_players and deathmatch_stats both had user_id as their sole primary key,
-- causing cross-guild stat contamination when the same user plays in multiple guilds.
--
-- Migration 002 already added the guild_id column (DEFAULT 0), so all existing rows
-- have guild_id=0.  We drop the old PK and create a composite one.

-- rps_players
ALTER TABLE rps_players DROP CONSTRAINT IF EXISTS rps_players_pkey;
ALTER TABLE rps_players ADD PRIMARY KEY (user_id, guild_id);

-- deathmatch_stats
ALTER TABLE deathmatch_stats DROP CONSTRAINT IF EXISTS deathmatch_stats_pkey;
ALTER TABLE deathmatch_stats ADD PRIMARY KEY (user_id, guild_id);

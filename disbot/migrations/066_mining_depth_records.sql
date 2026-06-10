-- Personal depth record (deepest band ever reached) — the old system's
-- max-depth tracking, reborn for milestone XP awards and future titles
-- ("the Deep").  Backfilled from the current position so nobody loses a
-- record they already stand on.
ALTER TABLE mining_player_state
    ADD COLUMN IF NOT EXISTS max_depth INTEGER NOT NULL DEFAULT 0;

UPDATE mining_player_state SET max_depth = GREATEST(max_depth, depth);

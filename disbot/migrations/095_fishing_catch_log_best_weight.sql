-- Fishing trophy records (per-species "biggest caught").
--
-- v1 fishing went weightless: migration 076 DROPPED the `best_weight` column
-- that 075 had added, because the Q-0175 redesign ranked fish by static size
-- and paid no coins, so a per-catch weight had no purpose.  The owner design's
-- "Other ideas" list now calls for trophy records — a cheap long-tail goal where
-- each catch rolls its own weight and the log keeps the player's heaviest of
-- each species ("personal best beats raw counts for retention").  That gives
-- weight a real purpose, so this migration re-adds the column.
--
-- Forward-only + additive (the migration-chain invariant): a brand-new column
-- with a 0 default, so existing rows keep their counts and simply start with no
-- recorded best until their next catch.  An empty `fishing_catch_log` is still
-- byte-identical to the pre-fishing bot.  `IF NOT EXISTS` makes it idempotent
-- and safe whichever form of 075 a given database applied.
ALTER TABLE fishing_catch_log
    ADD COLUMN IF NOT EXISTS best_weight REAL NOT NULL DEFAULT 0;

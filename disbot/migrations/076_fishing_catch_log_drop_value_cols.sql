-- Fishing v1 was reconciled to the owner's design (Q-0175 / #1036): fish are
-- ranked by size and v1 pays NO coins (fish value/use is an explicitly OPEN
-- owner question), so the catch log's `best_weight` + `total_value` columns
-- (added in migration 075, deployed by #1033's interim coins design) are unused.
--
-- 075 was already applied in production (the version-numbered runner skips an
-- already-recorded migration, so editing 075 in place would never reach existing
-- databases and would diverge production from fresh schemas). Per migration
-- hygiene, 075 stays as it was deployed and THIS migration performs the schema
-- transition. `IF EXISTS` makes it idempotent + safe regardless of which form of
-- 075 a given database applied: production (with the columns) drops them; a fresh
-- database that already has the clean shape is a no-op.
ALTER TABLE fishing_catch_log DROP COLUMN IF EXISTS best_weight;
ALTER TABLE fishing_catch_log DROP COLUMN IF EXISTS total_value;

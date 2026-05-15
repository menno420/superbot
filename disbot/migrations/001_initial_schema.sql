-- Migration 001: Initial schema
-- Documents the tables created by _create_tables() at bot launch.
-- This migration is a no-op when applied after _create_tables() has already run;
-- it exists to establish the migration baseline and mark version 001 as applied.

-- All tables already created by _create_tables() via CREATE TABLE IF NOT EXISTS.
-- No additional SQL needed here.
SELECT 1;

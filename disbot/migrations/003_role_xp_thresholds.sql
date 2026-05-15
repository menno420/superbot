-- Migration 003: Add XP-based auto-assignment columns to role_thresholds
-- Additive-only: no DROP, no data loss, existing rows keep NULL/FALSE defaults.

ALTER TABLE role_thresholds
    ADD COLUMN IF NOT EXISTS level_required INTEGER DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS xp_auto_assign BOOLEAN NOT NULL DEFAULT FALSE;

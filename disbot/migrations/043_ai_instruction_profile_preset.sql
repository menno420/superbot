-- Migration 043: AI Behavior preset marker column (PR-B).
--
-- Adds an ``is_preset`` boolean to ``ai_instruction_profile`` so the
-- behavior preset catalog can live in the existing table without a
-- parallel schema. Built-in presets are seeded in migration 044 with
-- ``is_preset = TRUE`` and ``guild_id IS NULL``.
--
-- Reads from ``ai_behavior_profile_service.list_presets()`` filter on
-- this column. Writes through ``ai_instruction_mutation.upsert_profile``
-- refuse to set ``is_preset = TRUE`` unless the actor is the system
-- seeder, so guild operators cannot synthesise fake presets.
--
-- Forward-only and idempotent.

ALTER TABLE ai_instruction_profile
    ADD COLUMN IF NOT EXISTS is_preset BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS ai_instruction_profile_preset_idx
    ON ai_instruction_profile (is_preset) WHERE is_preset = TRUE;

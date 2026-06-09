-- Migration 062: AI tool-orchestration profile (Phase 3 — typed policy storage).
--
-- Adds a per-scope orchestration-profile reference to the existing AI policy
-- tables. The profile names a built-in orchestration preset (see
-- services/ai_orchestration_presets.py) that resolves to a toolset/tool-choice/
-- budget bundle for the model<->tool loop. It is deliberately SEPARATE from the
-- natural-language reply policy (mode / min_level / cooldown / instruction
-- profile): an operator picks "concise" reply behaviour with "BTD6 grounded"
-- tool orchestration independently (orchestration plan §4 — separate behaviour
-- from orchestration).
--
-- Storage shape (orchestration plan §9.1): built-in presets are code, so a
-- scope only stores a single profile-key string. NULL means "no opinion at this
-- scope" — the resolver inherits the next layer, and an all-NULL guild resolves
-- to the compatible default (today's behaviour: every scope-allowed tool offered
-- with automatic choice, hop-bounded budget). So this migration changes NO
-- behaviour on its own (plan §6.3 safe defaults).
--
-- Intentionally NO CHECK constraint on the value: the set of valid profile keys
-- lives in the service layer (ai_orchestration_presets), validated by the
-- audited ai_orchestration_mutation seam, so adding a preset never needs a
-- migration + CHECK bump.
--
-- Additive, nullable, idempotent (ADD COLUMN IF NOT EXISTS) — matches the AI
-- subsystem's additive-migration contract (docs/ai-config-ownership.md §7).
-- Forward-only.

ALTER TABLE ai_guild_policy
    ADD COLUMN IF NOT EXISTS orchestration_profile TEXT NULL;

ALTER TABLE ai_channel_policy
    ADD COLUMN IF NOT EXISTS orchestration_profile TEXT NULL;

ALTER TABLE ai_category_policy
    ADD COLUMN IF NOT EXISTS orchestration_profile TEXT NULL;

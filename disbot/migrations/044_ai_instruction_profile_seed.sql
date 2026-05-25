-- Migration 044: Seed built-in AI Behavior presets (PR-B).
--
-- Inserts the seven curated presets used by the Behavior UI's
-- preset picker. Each row sits at ``guild_id IS NULL`` (system-wide)
-- with ``scope = 'system'`` and ``is_preset = TRUE``. Policy rows
-- reference these by their auto-generated id; the id is looked up
-- by ``(guild_id, scope, name)`` to stay stable across replays.
--
-- The seven presets:
--   * disabled            — no replies
--   * mention_only_helper — concise mention-only assistant
--   * helpful_channel     — full natural-language behavior
--   * btd6_focused        — BTD6 grounding prioritised
--   * quiet_btd6_focused  — BTD6 grounding, mention-only
--   * staff_diagnostics   — expanded audit visibility, gated by role
--   * support_triage      — neutral copy, used by PR-H draft target
--
-- Forward-only and idempotent (``ON CONFLICT … DO UPDATE`` refreshes
-- the body text but never flips ``is_preset`` back to ``FALSE``).

INSERT INTO ai_instruction_profile
    (guild_id, name, body, scope, feature_key, is_preset, created_at, updated_at)
VALUES
    (NULL, 'disabled',
     'AI replies are disabled. The assistant does not respond to natural-language messages in this scope.',
     'system', NULL, TRUE, NOW(), NOW()),
    (NULL, 'mention_only_helper',
     'Reply only when explicitly mentioned. Keep answers concise, polite, and to the point. Decline gracefully when out of scope.',
     'system', NULL, TRUE, NOW(), NOW()),
    (NULL, 'helpful_channel',
     'Engage helpfully in natural-language messages within this scope. Answer questions, surface relevant context, and use the configured natural-language level gate as the only eligibility check.',
     'system', NULL, TRUE, NOW(), NOW()),
    (NULL, 'btd6_focused',
     'Prioritise BTD6 grounding. When a message resolves to a BTD6 intent, cite the grounding facts. Defer to the BTD6 response builder before composing free-form text.',
     'system', NULL, TRUE, NOW(), NOW()),
    (NULL, 'quiet_btd6_focused',
     'Reply only when explicitly mentioned. Prefer BTD6 grounding for resolved intents; for other messages, decline gracefully.',
     'system', NULL, TRUE, NOW(), NOW()),
    (NULL, 'staff_diagnostics',
     'Operator-facing diagnostics scope. Surface audit-quality detail (route, provider, model, policy_snapshot_hash) when asked about the assistant. Intended for channels gated by a staff role policy.',
     'system', NULL, TRUE, NOW(), NOW()),
    (NULL, 'support_triage',
     'Neutral, factual triage style for support contexts. Avoid speculation; cite recent audit context when relevant. Used by the PR-H draft surface.',
     'system', NULL, TRUE, NOW(), NOW())
ON CONFLICT (guild_id, scope, name) DO UPDATE SET
    body       = EXCLUDED.body,
    is_preset  = TRUE,
    updated_at = NOW();

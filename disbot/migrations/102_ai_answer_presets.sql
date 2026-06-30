-- Migration 102: AI vetted answer presets (the `ai_answer_presets` table).
--
-- Operator-authored exact answers the bot serves with ZERO model call. The
-- "make the bot answer it itself" half of the ai_review_log answer loop
-- (docs/operations/ai-review-backlog-runbook.md): when a question recurs, or has
-- no clean data fix (opinion / strategy), an operator stores the vetted answer
-- and the natural-language stage short-circuits to it — after routing, before
-- the gateway — on an exact normalized-question match.
--
-- Keyed on the normalized question (utils.ai_text_normalize.normalize_question)
-- so the lookup is EXACT-MATCH only — deliberately no fuzzy / semantic matching,
-- because a false match would confidently serve the wrong answer with no model
-- in the loop. The cost (a paraphrase needs its own preset) is acceptable for v1.
--
-- The write boundary is services/ai_preset_service.py (audited via
-- audit.action_recorded); CRUD primitives live in utils/db/ai_presets.py. Per-
-- guild teardown is wired in utils/db/ai.py::delete_for_guild. Rollback by
-- dropping the table (no readers exist outside those modules + the stage
-- short-circuit as of this migration).

CREATE TABLE IF NOT EXISTS ai_answer_presets (
    id            BIGINT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guild_id      BIGINT      NOT NULL,
    -- normalized question key (the exact-match lookup key)
    question_key  TEXT        NOT NULL,
    -- the question text as authored (for display / review)
    question      TEXT        NOT NULL,
    -- the vetted answer, served verbatim with no model call
    answer        TEXT        NOT NULL,
    -- optional routed-task tag for provenance (e.g. 'btd6.answer'); display only
    task          TEXT,
    -- where the answer came from: a review-log entry id, 'operator', etc.
    source        TEXT,
    enabled       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_by    BIGINT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- One preset per (guild, normalized question) — authoring the same question
-- again updates the stored answer (ON CONFLICT upsert in the service). This is
-- also the index the runtime exact-match lookup uses.
CREATE UNIQUE INDEX IF NOT EXISTS idx_ai_answer_presets_guild_key
    ON ai_answer_presets (guild_id, question_key);

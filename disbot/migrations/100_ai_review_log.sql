-- Migration 100: AI answer review log (the `ai_review_log` table).
--
-- A reviewable record of the two cases the maintainer wants to see:
--
--   1. "didn't-know" outcomes — the natural-language stage engaged a message
--      but could not answer it properly: a provider outage, an empty / no-route
--      reply, or the BTD6 / Project Moon faithfulness guard flooring an
--      ungrounded answer to a refusal. Recorded from the stage's existing audit
--      seams (kind = 'unknown').
--   2. user corrections — a member 👎-reacts to, or replies-with-a-correction
--      to, one of the bot's AI answers (kind = 'correction').
--
-- Unlike `ai_decision_audit` (decision metadata only, no text), this table
-- stores the redacted question + answer (and, for a correction, the redacted
-- correction text) so a human can actually review what went wrong. Text is
-- scrubbed through the bot's outbound redactor before it lands here.
--
-- The write boundary is services/ai_review_log_service.py; CRUD primitives live
-- in utils/db/ai_review.py; the Discord surface (listeners + review-channel
-- poster + !aireview) is cogs/ai_review_cog.py. Per-guild teardown is wired in
-- utils/db/ai.py::delete_for_guild. Rollback by dropping the table (no readers
-- exist outside those modules as of this migration).

CREATE TABLE IF NOT EXISTS ai_review_log (
    id               BIGINT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guild_id         BIGINT      NOT NULL,
    channel_id       BIGINT      NOT NULL,
    -- the member who asked the question
    user_id          BIGINT      NOT NULL,
    -- the triggering user message (join key back to ai_decision_audit)
    message_id       BIGINT,
    -- the bot's answer message a correction was attached to (NULL for 'unknown')
    reply_message_id BIGINT,
    -- 'unknown' (the AI could not answer) | 'correction' (a user corrected it)
    kind             VARCHAR(16) NOT NULL,
    -- for 'unknown': the AI decision reason (provider_unavailable /
    -- no_route_matched / grounding_failed / errored). for 'correction': the
    -- signal that flagged it ('reaction' | 'reply').
    reason_code      TEXT,
    -- the routed AI task + route (e.g. 'btd6.answer'), for filtering
    task             TEXT,
    route            TEXT,
    -- redacted text (scrubbed through the outbound redactor before storage)
    question         TEXT,
    answer           TEXT,
    -- redacted user correction text ('reply' corrections only; NULL otherwise)
    correction       TEXT,
    -- the member who corrected the answer (NULL for 'unknown')
    corrected_by     BIGINT,
    provider         TEXT,
    model            TEXT,
    -- operator review state (flip via `!aireview resolve <id>`)
    reviewed         BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- retention horizon (set by the service; physical purge is a follow-up)
    expires_at       TIMESTAMPTZ
);

-- Recent entries for a guild, newest first (the !aireview list + channel feed).
CREATE INDEX IF NOT EXISTS idx_ai_review_log_guild_created
    ON ai_review_log (guild_id, created_at DESC);

-- Filtered "unknowns only" / "corrections only" listings, newest first.
CREATE INDEX IF NOT EXISTS idx_ai_review_log_guild_kind_created
    ON ai_review_log (guild_id, kind, created_at DESC);

-- The "unreviewed backlog" count + listing (partial index — only open items).
CREATE INDEX IF NOT EXISTS idx_ai_review_log_guild_unreviewed
    ON ai_review_log (guild_id, created_at DESC)
    WHERE reviewed = FALSE;

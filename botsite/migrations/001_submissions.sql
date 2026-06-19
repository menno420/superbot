-- Submissions store — migration 001 (the public bug/suggestion intake table).
--
-- This is the ONE canonical schema for the `submissions` table, owned by the
-- website tier (NOT the bot). It lives in a **separate, dashboard-owned Postgres**
-- (plan §2.3 / §7.3 / Q-0178 decision 3) — deliberately not the bot's DB, so the
-- bot-decoupling rule holds and the public bot site can hold an INSERT-only role on
-- exactly this one table (plan §4.4 secret matrix).
--
-- Two independent helpers share ONLY this contract — never code (plan §2.2 / §5):
--   * botsite/submissions_db.py   — INSERT-only  (insert_pending)
--   * dashboard/submissions_db.py — SELECT+UPDATE (list_pending / set_status /
--                                   attach_issue_url)
--
-- Flow (plan §2.3): the public bot-site /submit form INSERTs a row with
-- status='pending'; it is NEVER shown publicly. The owner-gated dev-site
-- /admin/moderation lists pending rows and approves/rejects; on approve the dev
-- site mirrors the row to a GitHub issue and records github_issue_url.
--
-- Schema (plan §2.3):
--   id              bigserial PK
--   kind            'bug' | 'suggestion'  (maps to .github/ISSUE_TEMPLATE shapes)
--   title           length-capped, server-trimmed
--   body            length-capped; stored as plain text, rendered ESCAPED
--   surface         from the bug template dropdown (bot / dashboard / CI / other);
--                   nullable (suggestions need no surface)
--   contact         optional, never required, never published
--   status          'pending' (default) -> 'approved' | 'rejected'
--   submitted_at    timestamptz default now()
--   source_ip_hash  SALTED hash for rate-limit/abuse forensics — NEVER the raw IP
--   moderated_by    owner Discord id at decision time (nullable until moderated)
--   github_issue_url set when mirrored to a GitHub issue (nullable)
--
-- Deploy / rollback (plan §6): additive. Apply this file once against the
-- dashboard-owned Postgres at rollout (owner step). `DROP TABLE submissions;`
-- fully unwinds intake — nothing else references it. Forward-only and idempotent
-- (CREATE TABLE IF NOT EXISTS), so re-applying is a no-op.

CREATE TABLE IF NOT EXISTS submissions (
    id               BIGINT       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    kind             TEXT         NOT NULL,
    title            TEXT         NOT NULL,
    body             TEXT         NOT NULL,
    surface          TEXT,
    contact          TEXT,
    status           TEXT         NOT NULL DEFAULT 'pending',
    submitted_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    source_ip_hash   TEXT,
    moderated_by     TEXT,
    github_issue_url TEXT,
    CHECK (kind IN ('bug', 'suggestion')),
    CHECK (status IN ('pending', 'approved', 'rejected'))
);

-- The moderation queue reads `WHERE status='pending' ORDER BY submitted_at` — a
-- partial index keeps that hot read cheap as the approved/rejected history grows.
CREATE INDEX IF NOT EXISTS submissions_pending_idx
    ON submissions (submitted_at)
    WHERE status = 'pending';

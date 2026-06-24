-- Migration 098: support tickets (the `ticket` subsystem).
--
-- A staff support-ticket system: members open a ticket (by command, by a
-- panel button, or via the AI in natural language); the bot creates a private
-- channel visible to the opener + the configured staff role; staff claim,
-- add/remove participants, and close it; closing posts a transcript to a log
-- channel and DMs the opener.
--
-- Three tables, additive only (no existing table touched):
--
--   ticket_config     — one row per guild: the staff role, the category new
--                       ticket channels are created under, the transcript log
--                       channel, the launcher panel message, per-user open cap,
--                       and the enabled / ping-on-open switches.
--   tickets           — one row per ticket (open or closed history).
--   ticket_blacklist  — members barred from opening tickets in a guild.
--
-- The audited write boundary is services/ticket_mutation.py; the read model +
-- eligibility checks live in services/ticket_service.py; CRUD primitives in
-- utils/db/tickets.py. Rollback by dropping all three tables (no readers exist
-- outside those modules as of this migration).

CREATE TABLE IF NOT EXISTS ticket_config (
    guild_id          BIGINT  NOT NULL PRIMARY KEY,
    -- whether the subsystem is active in this guild (panel button + AI tool
    -- + `!ticket new` all refuse to open when false)
    enabled           BOOLEAN NOT NULL DEFAULT TRUE,
    -- the role granted view access to every ticket channel; NULL until setup
    staff_role_id     BIGINT,
    -- the category new ticket channels are created under (get-or-created by
    -- name when NULL)
    category_id       BIGINT,
    -- the channel closed-ticket transcripts are posted to; NULL = no log
    log_channel_id    BIGINT,
    -- the message hosting the public "Open a ticket" launcher panel
    panel_channel_id  BIGINT,
    panel_message_id  BIGINT,
    -- max simultaneously-open tickets one member may hold (anti-spam; also
    -- bounds the AI action tool)
    max_open_per_user INT     NOT NULL DEFAULT 1,
    -- mention the staff role in a freshly-opened ticket channel
    ping_staff_on_open BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at        BIGINT  NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tickets (
    id          BIGINT  GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guild_id    BIGINT  NOT NULL,
    -- the private channel created for this ticket (0 if creation failed)
    channel_id  BIGINT  NOT NULL,
    -- the member who opened it
    opener_id   BIGINT  NOT NULL,
    subject     TEXT    NOT NULL,
    -- 'open' | 'closed'
    status      VARCHAR(16) NOT NULL DEFAULT 'open',
    -- the staff member who claimed it (NULL while unclaimed)
    claimed_by  BIGINT,
    -- how it was opened: 'command' | 'panel' | 'ai'
    source      VARCHAR(16) NOT NULL DEFAULT 'command',
    created_at  BIGINT  NOT NULL,
    closed_at   BIGINT,
    closed_by   BIGINT,
    close_reason TEXT
);

-- Per-user open-ticket count (the cap check) + "your tickets" listings.
CREATE INDEX IF NOT EXISTS idx_tickets_guild_opener_status
    ON tickets (guild_id, opener_id, status);

-- Resolve a ticket from the channel a control-panel button was pressed in.
CREATE INDEX IF NOT EXISTS idx_tickets_channel
    ON tickets (channel_id);

-- Staff "all open tickets" listing, newest first.
CREATE INDEX IF NOT EXISTS idx_tickets_guild_status_created
    ON tickets (guild_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS ticket_blacklist (
    guild_id   BIGINT      NOT NULL,
    user_id    BIGINT      NOT NULL,
    added_by   BIGINT      NOT NULL,
    reason     TEXT,
    added_at   BIGINT      NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
);

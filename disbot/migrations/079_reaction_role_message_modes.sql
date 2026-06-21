-- Per-message modes for the legacy emoji reaction-role surface (overhaul PR 3).
--
-- Carl-bot applies a *mode* per reaction-role message (`rr <mode> <msg_id>`):
--   normal  — react adds the role, un-react removes it (the default).
--   unique  — only one role per message; reacting swaps out the member's
--             previous pick from the SAME message.
--   verify  — reacting only ever ADDS the role; the bot then removes the
--             member's reaction so the message stays clean, and un-reacting
--             never strips the role.
--
-- The legacy `reaction_roles` table is keyed per (guild, message, emoji); the
-- mode is a property of the *message*, so it lives in its own tiny table keyed
-- per (guild, message). No row ⇒ 'normal' (byte-identical to the pre-PR-3 bot,
-- so this migration is behaviour-preserving for every existing binding).

CREATE TABLE IF NOT EXISTS reaction_role_message_modes (
    guild_id   BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    mode       TEXT   NOT NULL DEFAULT 'normal',
    PRIMARY KEY (guild_id, message_id)
);

CREATE INDEX IF NOT EXISTS idx_reaction_role_modes_guild
    ON reaction_role_message_modes (guild_id);

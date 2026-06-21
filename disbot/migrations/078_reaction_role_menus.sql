-- Role menus (reaction-roles overhaul, PR 1 foundation).
--
-- The data model for modern button/dropdown role menus (the headline feature
-- built in PR 2). A menu is one bot-posted message in a guild channel; its
-- options pair a role with an optional emoji/label. The legacy emoji
-- `reaction_roles` table (bootstrap schema in utils/db/migrations.py) is left
-- untouched and continues to work — these tables are purely additive, so an
-- EMPTY pair of tables is byte-identical to the pre-overhaul bot.
--
-- `style` defaults to 'dropdown' (the owner-locked default, plan §9); other
-- values: 'button', 'reaction'. `mode` mirrors Carl-bot's modes
-- ('normal' | 'unique' | 'verify'). `max_roles` 0 = unlimited (the per-member
-- pick cap, Carl's `rr limit`). `theme` keys an embed theme preset (plan §4.6b).
-- message_id is NULL until the menu message is posted (build → store).

CREATE TABLE IF NOT EXISTS role_menus (
    menu_id     BIGSERIAL   PRIMARY KEY,
    guild_id    BIGINT      NOT NULL,
    channel_id  BIGINT      NOT NULL,
    message_id  BIGINT,
    title       TEXT        NOT NULL DEFAULT 'Pick your roles',
    description TEXT,
    style       TEXT        NOT NULL DEFAULT 'dropdown',
    mode        TEXT        NOT NULL DEFAULT 'normal',
    max_roles   INTEGER     NOT NULL DEFAULT 0,
    theme       TEXT        NOT NULL DEFAULT 'default',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_role_menus_guild ON role_menus (guild_id);
CREATE INDEX IF NOT EXISTS idx_role_menus_message ON role_menus (message_id);

CREATE TABLE IF NOT EXISTS role_menu_options (
    menu_id  BIGINT  NOT NULL REFERENCES role_menus (menu_id) ON DELETE CASCADE,
    role_id  BIGINT  NOT NULL,
    emoji    TEXT,
    label    TEXT,
    position INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (menu_id, role_id)
);

-- Temporary role grants (reaction-roles overhaul PR 4 — "free temp roles").
--
-- Carl-bot gates timed roles (`temp <time>`) behind Patreon; SuperBot offers
-- them free. A row records that a member was given a role until `expires_at`;
-- a periodic sweep (RoleGrantsCog) removes the role + the row once it lapses.
-- Re-granting the same (guild, member, role) extends the expiry (UPSERT on the
-- unique key), so a member never holds duplicate grants for one role.

CREATE TABLE IF NOT EXISTS role_grants (
    grant_id   BIGSERIAL   PRIMARY KEY,
    guild_id   BIGINT      NOT NULL,
    member_id  BIGINT      NOT NULL,
    role_id    BIGINT      NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    granted_by BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (guild_id, member_id, role_id)
);

-- The sweep scans by expiry; teardown + member lookups scan by guild.
CREATE INDEX IF NOT EXISTS idx_role_grants_expiry ON role_grants (expires_at);
CREATE INDEX IF NOT EXISTS idx_role_grants_guild ON role_grants (guild_id);

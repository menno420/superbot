-- Role-pickup analytics rollup (reaction-roles overhaul PR 5, plan §10).
--
-- Because every self-assignment routes through the audited service seam, an
-- aggregate pickup counter is nearly free: one row per (guild, role) tallies how
-- often the role was self-assigned (`picked`) / unassigned (`removed`) plus the
-- last pickup time. Surfaced in the role Diagnostics panel ("most popular" /
-- "barely-used — archive?"). AGGREGATE ONLY — no per-member history (privacy:
-- per-user logging stays the separate opt-in toggle from plan §9).

CREATE TABLE IF NOT EXISTS role_menu_pickup_stats (
    guild_id       BIGINT      NOT NULL,
    role_id        BIGINT      NOT NULL,
    picked         INTEGER     NOT NULL DEFAULT 0,
    removed        INTEGER     NOT NULL DEFAULT 0,
    last_picked_at TIMESTAMPTZ,
    PRIMARY KEY (guild_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_role_pickup_stats_guild
    ON role_menu_pickup_stats (guild_id);

-- Mining Vault — a per-player "safe stash" separate from the active mining
-- inventory (brainstorm §7.5: "Vault — inventory cap + safe stash").  Depositing
-- moves items OUT of mining_inventory and into this protected store; withdrawing
-- moves them back.  The shape mirrors mining_inventory exactly so a deposit /
-- withdraw is a symmetric pair of clamped item deltas: guild-scoped, user_id TEXT
-- to match mining_inventory's legacy column type, one row per item, quantity
-- clamped at >= 0.
--
-- v1 is a pure safe store with NO inventory cap yet — the cap that turns the
-- vault into a real sink (and the build-cost / capacity-upgrade economy) is a
-- documented follow-up (docs/planning/mining-structures-skill-tree-plan-2026-06-14.md),
-- so this migration is purely additive and changes no existing play.
CREATE TABLE IF NOT EXISTS mining_vault (
    user_id    TEXT    NOT NULL,
    guild_id   BIGINT  NOT NULL DEFAULT 0,
    item_name  TEXT    NOT NULL,
    quantity   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, guild_id, item_name)
);

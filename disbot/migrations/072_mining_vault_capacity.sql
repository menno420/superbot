-- Mining Vault v2 — an upgradeable vault capacity (brainstorm §7.5: turn the
-- safe stash into a real coin sink).  Slice A of
-- docs/planning/mining-structures-skill-tree-plan-2026-06-14.md.
--
-- vault_level is the per-player capacity tier: the vault holds
-- BASE_VAULT_CAP + level * VAULT_SLOTS_PER_LEVEL distinct item-types
-- (utils/mining/capacity.py).  Level 0 is the v1 default, so this column is
-- purely additive — every existing vault keeps its v1 (base) capacity and no
-- play changes.  It lives on mining_player_state (the per-(user,guild) mining
-- meta row, direct-lane game state) rather than a new table; the vault upgrade
-- spends coins through the audited economy lane (services/mining_workflow.py).
ALTER TABLE mining_player_state
    ADD COLUMN IF NOT EXISTS vault_level INTEGER NOT NULL DEFAULT 0;

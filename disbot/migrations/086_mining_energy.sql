-- Mining energy — the playable-pace "fuel" for digging (the owner's chosen
-- frequency brake, NOT a per-dig cooldown; 2026-06-22 rebalance).  Each dig
-- spends 1 energy, energy regenerates ~1 / 10s (= 360/hour, the sim-pinned
-- throttle in docs/planning/mining-economy-balance-2026-06-22.md), and food /
-- boosters top it up.
--
-- Two additive columns on mining_player_state (the per-(user,guild) mining meta
-- row, direct-lane game state): the stored energy value + the unix timestamp it
-- was last settled at.  Effective energy at any instant is computed from elapsed
-- time in pure code (utils/mining/energy.py) — no background ticker (ADR-001/002:
-- no external state, no scheduler).  energy defaults to the full bar (60) and
-- energy_updated_at to 0, so every existing player and every fresh row starts
-- with a full bar (a 0 timestamp settles to "full" on first read) — purely
-- additive, no play breaks.
ALTER TABLE mining_player_state
    ADD COLUMN IF NOT EXISTS energy INTEGER NOT NULL DEFAULT 60;
ALTER TABLE mining_player_state
    ADD COLUMN IF NOT EXISTS energy_updated_at BIGINT NOT NULL DEFAULT 0;

-- Mining titles — the equipped-title selection (brainstorm §7.6: profile &
-- identity).  Slice F of
-- docs/planning/mining-structures-skill-tree-plan-2026-06-14.md.
--
-- A player's EARNED titles are derived on read from existing progression (skill
-- allocation at cap, max depth, game level — utils/mining/titles.py), so the only
-- thing that needs persisting is which earned title the player chose to display.
-- equipped_title is that choice (NULL = none equipped → byte-identical to the
-- pre-titles Character card).  It lives on mining_player_state (the per-(user,
-- guild) mining meta row, direct-lane game state) — purely additive.
ALTER TABLE mining_player_state
    ADD COLUMN IF NOT EXISTS equipped_title TEXT;

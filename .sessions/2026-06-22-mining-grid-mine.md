# 2026-06-22 — Mining grid Mine (hub-redesign PR 3)

> **Status:** `in-progress` — born-red session card (Q-0133). Flip to `complete` as the
> deliberate last step once the work + close-out docs are in.

## Arc

Continue the mining plan. The two structures/exploration mining plans are `historical`
(all slices shipped); the one **active** mining plan is
[`mining-hub-redesign-2026-06-15.md`](../docs/planning/mining-hub-redesign-2026-06-15.md),
whose single unbuilt slice is **PR 3 — grid Mine**: the (x,y,z) world model + 6-direction
movement + discovery. All four design questions are owner-DECIDED (Q-0173): seed-deterministic
procedural grid · ONE shared grid per seed · vertical axis = existing depth bands · v1 free
movement, NO encounters.

About to build: pure `utils/mining/grid.py` (seed-deterministic cell content + movement + map
render) · migration 085 (pos_x/pos_y on `mining_player_state` + `mining_world` seed +
`mining_discovered` fog-of-war) · DB primitives + boundary-ratchet entries · `mining_workflow`
grid ops (`move` / `mine_here`) · a grid Mine navigator view replacing the interim
descend/ascend `MineView` · cog wiring · tests.

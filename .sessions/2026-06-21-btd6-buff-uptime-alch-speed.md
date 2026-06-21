# 2026-06-21 — BTD6 buff-uptime: model attack-speed buffs on the Alchemist

> **Status:** `in-progress`

## Arc (owner-chosen via question panel)
The capstone of buff-uptime realism: when the **Alchemist itself** is sped up (Jungle Drums,
Monkey Boost, Overclock, …), its brew-throw cadence drops — and below the per-target
`rebuffBlockTime` floor it can keep MORE towers buffed. This is the one scenario where the
`rebuffBlockTime` decoded in #1251 finally binds, and the case the calc couldn't express.

**Good news vs the ~2-PR estimate:** the speed multipliers are **already in committed data**, so
no decode pass is needed — this is one clean PR:
- "Jungle Drums" → Monkey Village 2-0-0 `RateSupport` ×0.85 (resolve_upgrade → tier rate buff).
- "Monkey Boost" → power `rate_scale` 0.5 (already decoded).
- "Overclock" → Engineer rate buff ×0.25 (same upgrade-buff path).

## Plan
1. `buff_uptime(..., alch_speed=<source>)` — resolve the source → a cooldown multiplier
   (Power `rate_scale`, else an upgrade's `rateMultiplier` < 1); `effective_cadence = base ×
   mult`; `rebuff_interval = max(targets × effective_cadence, rebuff_block)`. Honest found=False
   for an unknown/non-speed source.
2. `btd6_buff_uptime` tool: optional `alch_speed` param.
3. Tests (real data: Jungle Drums / Monkey Boost on 4-0-0 → 5-0-0 Ninja, single + multi-target,
   rebuffBlockTime binding; unknown source) + docs.

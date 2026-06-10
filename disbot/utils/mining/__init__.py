"""Mining domain — pure, shared game logic (no Discord, no DB, no views).

Relocated from ``cogs/mining/`` (RS02 stage 1) so the modules sit on the
layer every consumer may import: views use them module-level (killing the
old views→cogs lazy-import debt), and ``services/mining_workflow.py`` —
the audited write boundary — composes them without a services→cogs
violation.  Per ``docs/helper-policy.md``: logic needed by both services
and views belongs in ``utils/``.

Modules:
    items        — item taxonomy (kinds, tiers, values, tool ladders)
    rewards      — mining/harvest loot tables
    world        — depth↔biome model + descent gating
    exploration  — loadout-aware exploration outcome engine
    recipes      — JSON-driven crafting recipes (+ safe defaults)
    market       — pure pricing (sell values, the gear shop)
    workshop     — pure durability/repair/craft helpers (costs, bars, plans)
"""

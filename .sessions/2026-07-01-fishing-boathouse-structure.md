# 2026-07-01 — Fishing Boathouse (third coral structure — energy-regen payoff)

> **Status:** `in-progress`

**Run type:** `routine · dispatch`

## What I'm about to do

Empty-fire scheduled dispatch → advance S1's standing offline ▶ Next: **a third fishing structure**
(the explicit "next offline successor" after Tide Pool #1598 / Dock #1599 / Structures sub-hub #1603).

**The Boathouse** 🛖 — a coral + **wood** structure whose payoff is **faster fishing energy regen**, a
genuinely distinct third axis:

| Structure | Payoff | Axis |
|---|---|---|
| 🪸 Tide Pool | rarity-pull (rarer fish) | *quality* |
| ⚓ Dock | bite-speed (faster bites) | *throughput per cast* |
| 🛖 **Boathouse** | energy regen (shorter "line rest" wait) | *endurance / less waiting* |

Reuses the proven pattern end-to-end: a registry entry in `utils/mining/structures.py`
(`_BOATHOUSE_BUILD_LADDER` + `boathouse_regen_mult`), the audited `mining_workflow.build_structure`
seam (no new mutation path), the generic `mining_structures` table (**no migration**), a
`views/fishing/boathouse.py` panel + a Boathouse button in the 🏗 Structures sub-hub, and a `!boathouse`
command. **Additive-safety:** unbuilt (level 0) ⇒ `boathouse_regen_mult == 1.0` ⇒ the effective regen
interval is exactly `REGEN_SECONDS` ⇒ **byte-identical** energy behaviour.

**BUG-0030 lesson applied:** command name `!boathouse` (aliases `moorings`, `boat`) grep-verified
collision-free bot-wide (`sail`/`setsail` are the only nearby tokens; `boat`/`boathouse`/`moor` all clean).

## What shipped

_(filled at close)_

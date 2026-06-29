# 2026-06-29 — Project Moon (Limbus) combat-mechanics knowledge layer

> **Status:** `in-progress`

**Run type:** manual

## What this run is doing (HOLD — born-red per Q-0133)
Owner asked in-chat to check how the Project Moon work is going and continue it. A Project Moon
community member (screenshot) named the missing "majority" as **clashing · IDs and passives ·
speed · enemy stats and passives** — which is exactly the plan's documented **▶ Next = Slice A
item 1** (the combat layer the structural/lore PRs #1453…#1470 deliberately left out).

This run ships the **stable, hand-authorable, correct half** of that: a new **`mechanic`** entity
kind in the Limbus knowledge domain — the core combat *rules* (Clash · Coin/heads · Speed · Sanity ·
Stagger · damage-resistance levels · Resonance · skills · defensive skills · Identity · Passives ·
E.G.O/Corrosion · Mental Break) — browsable via `!pm mechanic` and grounded into the AI answer path.
The *volatile per-Identity / per-enemy exact stat numbers* (HP, speed values, coin power) stay
deferred to the StaticData ingest lane on purpose — hand-committing them would risk ungrounded
numbers (the groundedness discipline ADR-006 protects).

_(Close-out notes, telemetry, run report, and the Q-0089/Q-0102/Q-0104 enders are written as the
final step, which flips this badge to `complete`.)_

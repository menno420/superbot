# Session: UX — mining in-place image cards (stop the stacking ephemerals)

> **Status:** `in-progress` — born-red card (Q-0133). Flip to `complete` as the deliberate
> final step once the fix + tests + close-out docs are in.

**Branch:** `claude/amazing-volta-auxt2d` · **Date:** 2026-06-15 · **Type:** UX bug (S1 Bot · games/mining)

## What I'm about to do

Owner-directed UX work: the "too many ephemeral panels" complaint. This session is **PR 1** of the
ephemeral-panel cleanup — the **mining image-card** half (owner screenshots, 2026-06-15).

Diagnosis: the mining hub navigation already updates in place, but the **PNG cards** (inventory card,
character/gear paper-doll) are sent as **separate `interaction.followup.send(file=..., ephemeral=True)`
messages** that pile up below the panel (`_send_inventory_card`, `send_character_doll`). Every Inventory
/ Gear click spawns a new "Only you can see this" image message.

Fix: render the image **into** the panel's own message (one self-replacing anchor) instead of a separate
ephemeral follow-up, and clear a stale image when navigating to another action — so nothing stacks.

- thread an optional `attachments` through `core.runtime.interaction_helpers.safe_edit`
- `views/mining/main_panel.py`: inventory/gear attach the PNG to the in-place edit; every other hub
  action clears it (no lingering image)
- `views/mining/gear_panel.py`: the doll renders onto the gear panel message; cleared on back-to-hub
- tests pin: no ephemeral image follow-up; image rides the in-place edit; navigation clears it

PR 2 (separate session) = the AI panel **navigation** half (`!aimenu` → policy/behavior/tools subtrees
stop spawning a fresh ephemeral per step) via `navigation.transition_to` + Back buttons.

## Context delta

_(filled at close)_

## Handoff

_(filled at close)_

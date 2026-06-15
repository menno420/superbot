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

## Progress (live session — expanded scope)

The owner steered this into a fuller **mining hub UX overhaul** (live, 2026-06-15):

- **PR 1 — in-place image cards ✅** committed (PR #911), `check_quality --full` green (9784).
- **Hub declutter (Option A) confirmed** via rendered mockups — 16 buttons → 6 main; Character +
  Workshop sub-hubs; Build/Craft/Recipes consolidated into one **Craft**; Explore → open-world stub;
  Mine → 3D grid navigator (new world model, v1 proposed, awaiting sign-off). Full IA captured in
  [`docs/planning/mining-hub-redesign-2026-06-15.md`](../docs/planning/mining-hub-redesign-2026-06-15.md).
- **Live test blocked on the token:** `DISCORD_BOT_TOKEN_PRODUCTION` is malformed/truncated —
  Discord 401s it (the bot's own login). Postgres + all cogs boot clean; only the token blocks.
  Owner asked to regenerate + set it as the env secret. The restructure build is best done **live**
  with the owner once the token is restored (their iterate-live preference).

## AI panels (the other ephemeral-panel half — deferred)

`!aimenu` → policy/behavior/tools subtrees spawn a fresh ephemeral per navigation step; migrate to
in-place via `navigation.transition_to` + Back buttons (`docs/ideas/ai-panel-inplace-navigation-2026-06-11.md`).
Separate follow-up.

## Context delta

_(filled at close)_

## Handoff

_(filled at close)_

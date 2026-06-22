# 2026-06-22 — Fishing menu: real buttons (the interactable panel)

> **Status:** `in-progress` — born-red card. Owner-reported gap: *"I still don't see the buttons in
> the fishing menu."* Root cause + fix below. Owner-directed (a live bug report).

## Arc (what I'm about to do)

**Root cause:** `!fish` and `!rod` *do* show buttons, but the **fishing menu reached through the Help
hub** (`FishingCog.build_help_menu_view`) returned a **static embed + an empty `discord.ui.View()`** —
no buttons. Fishing was the *only* cog returning an empty view from that hook (every other cog —
blackjack, mining, games… — returns a real interactive panel). So navigating to Fishing in the menu
showed a plain overview, exactly what the owner saw.

**Fix:** build the interactive fishing menu the design doc §6 always called for — a `FishingMenuView`
(HubView) with action buttons, and wire `build_help_menu_view` (+ a `!fishing` command) to return it.

This session:
1. **`views/fishing/menu.py`** — `FishingMenuView(HubView)` with **🎣 Cast** (launches the minigame in
   place), **🎒 Rod** (swaps to the rod shop), **📖 Fishdex** (shows the collection, keeps the menu).
   Mirrors `views/games/blackjack_panel.py` (a panel whose button launches a real game).
2. **`prepare_cast()` helper** in `cast_view.py` — the cast-launch logic (active-guard → rod → roll →
   view+embed) shared by the `!fish` command *and* the menu's Cast button (one source of truth).
3. **`build_fishlog_embed()`** extracted so the Fishdex button + `!fishlog` share it.
4. **Wire** `build_help_menu_view` → `FishingMenuView`; add `!fishing`/`!fishmenu` to open it directly.
5. **Tests** — the menu buttons (cast launches, rod swaps, fishdex renders) + `prepare_cast`.

## Shipped

_(filled in at close)_

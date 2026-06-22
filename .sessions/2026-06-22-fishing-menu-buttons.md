# 2026-06-22 — Fishing menu: real buttons (the interactable panel)

> **Status:** `complete` — interactive fishing menu shipped & verified (full CI mirror green, 11,621
> tests). Owner-reported gap fixed. PR #1303 → auto-merges on green (Q-0191).

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

## Shipped (PR #1303)

- **Root cause found:** `FishingCog.build_help_menu_view` returned a static embed + an **empty
  `discord.ui.View()`** — fishing was the *only* cog returning an empty view from that hook. `!fish`
  and `!rod` always had buttons; the *menu* (reached via Help) had none. That's what the owner saw.
- **`views/fishing/menu.py`** — `FishingMenuView(HubView)` with **🎣 Cast** (launches the cast
  minigame in place — `prepare_cast` → `edit_message` → `view.start()`, then stops the menu so its
  timeout can't fight the cast view), **🎒 Rod** (swaps the panel to `RodShopView`), **📖 Fishdex**
  (renders the collection, keeps the menu so you can act again). Plus `build_menu_embed` +
  `build_fishlog_embed`.
- **`prepare_cast()`** in `cast_view.py` — the cast-launch flow (active-guard → rod → roll → embed +
  view) now shared by the `!fish` command *and* the menu Cast button (one source of truth).
- **Wired** `build_help_menu_view` → `FishingMenuView`; added `!fishing`/`!fishmenu`; `!fishlog` now
  uses the shared `build_fishlog_embed`.
- **Checker:** allowlisted `FishingMenuView` for the `back_button` rule (root panel; Help attaches
  Back externally — same class as `SettingsHubView`/`_CountingHubView`).
- **Tests** — `test_fishing_menu.py` (8: embeds + each button's behaviour) + 3 `prepare_cast` tests.
  Dashboard regenerated (new `!fishing`, commands 371→372). Full CI mirror green.

## Session enders

- **💡 Session idea (Q-0089):** *A `build_help_menu_view` "empty-view" guard.* Fishing silently
  shipped a buttonless menu for three PRs because nothing flags a `build_help_menu_view` that returns
  a bare `discord.ui.View()` while the cog clearly has actionable surfaces. A tiny consistency check —
  "a games/activity cog whose `build_help_menu_view` returns an empty view" → warn — would have caught
  this on day one. Cheap AST check; logged for the consistency-linter lane.
- **♻ Grooming (Q-0015):** advanced the fishing minigame's *menu/UX* lifecycle — the design doc §6
  "make the menu a place" panel is now real (Cast/Rod/Fishdex), which the prior three PRs had left as
  an empty stub. Games folio updated.
- **⟲ Previous-session review:** PR3 (#1301) shipped the rod ladder cleanly but, like PR1/PR2, surfaced
  fishing **only through typed commands** and left the Help hook returning an empty view — so the whole
  arc built rich mechanics the owner couldn't *reach* via a menu. **What the arc missed:** "is this
  reachable from the UI the owner actually uses?" was never asked until the owner hit it. The mechanics
  were right; the *entry point* lagged. **System note:** a feature isn't done when its command works —
  it's done when it's reachable from the menu/hub a non-CLI user navigates. Worth a checklist line in
  the cog-review skill ("does the Help/hub panel expose this, not just the command?").
- **🧾 Doc audit (Q-0104):** games folio updated; `check_docs --strict` ✓; dashboard regenerated;
  `back_button` allowlist documented. Ledger auto-updates on merge. Nothing left only in chat.

## ⚑ Self-initiated: none — owner-directed bug report ("I still don't see the buttons in the fishing
   menu"). The fix (the interactive menu) is the design doc §6 panel, not unprompted scope.

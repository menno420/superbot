# 2026-06-23 — Universal panel nav: every panel is one click from Help + its hub

> **Status:** `in-progress` — owner-directed (Option 1). Building the "never stranded"
> mechanism: every leaf panel auto-attaches **📚 Help** + **↩ <parent hub>** on construction, so
> a panel reached by *any* command (e.g. `!games`, `!farm`) is always one click from Help and its
> mother hub, and never loses them on a redraw. PR this session; auto-merge armed on green (Q-0127);
> owner-directed → merge immediately (Q-0191).

> **Run type:** `manual · owner-directed`

## What the owner asked (two messages, 2026-06-23)

1. *"is there no way to automatically attach a back button and help button to every panel? like just
   one script that dynamically loads them to all panels"* → **Option 1, registry-driven self-attach.**
2. *"every panel, no matter how it's opened (ie. `!games`), [should] show a help button … never need
   more than 1 command per session … one centralized application that does not ever leave you stranded."*

## Root cause (carried from the earlier diagnosis)

Leaf panels (farm, mining, rps/blackjack/deathmatch, AI, channel, ux_lab, casino) carried **no nav of
their own** — their Back/Help button was *externally attached* by the hub/help opener to that one view
instance. The `edit_in_place` idiom redraws onto a **fresh** instance (`FarmMenuView()` …), which never
re-attached it → the button vanished on the next action. (Self-navigating hub/operator panels — admin,
utility, logging, settings — define their own `📚 Help` / `↩ Overview` decorated buttons, so they
survived redraws and were never the bug.)

## The mechanism (Option 1)

- **`views/navigation.py`** — new `attach_standard_nav(view)`: reads `view.SUBSYSTEM`, and from the
  subsystem registry attaches a **📚 Help** button (`nav:help`, click-time builder = Help home) and, when
  the subsystem has a `parent_hub`, a **↩ <hub>** button (`nav:hub:<hub>`, click-time builder rebuilds the
  hub via its cog's `build_help_menu_view` — the universal `hub_children` seam). Click-time closures use
  the views→cogs function-local import idiom (no module-level layer break).
  - `_self_navigates(view)` guard: skip panels that already define their own Help/Overview/Back-to-hub
    (heuristic on the codebase's stable button copy) — auto-nav is **only** for the leaf panels that had
    none.
  - `attach_back_button` gained a **custom_id idempotency guard** + row-overflow safety — the lynchpin
    that lets auto-nav coexist with the legacy external pushers without ever duplicating a control.
  - `has_standard_nav(view)` — used by the two central external pushers to skip when auto-nav is present.
- **`views/base.py` `BaseView` + `core/runtime/persistent_views.py` `PersistentView`** — call
  `attach_standard_nav(self)` at the end of `__init__`, so the controls reappear on **every**
  construction/redraw. `SUBSYSTEM` / `STANDARD_NAV` opt-out classvars on both bases.
- **Dedupe**: `HubChildButton` and `help_cog._attach_back_to_help_button` skip their external push when
  `has_standard_nav(child)` — the child already carries its own nav.
- **`SUBSYSTEM` added** to the leaf panels that lacked it: `farm` (FarmMenuView/FarmShopView), `ux_lab`
  (UxLabHomeView), `channel` (_ChannelManagerView). `UxLabPersistentDemo` opts out (`STANDARD_NAV=False`
  — it's a teaching mockup). Reverted speculative `SUBSYSTEM` on admin/utility hubs (they self-navigate).

Verified live-construction: AI, blackjack, rps, deathmatch, mining, farm, ux_lab, casino, channel all now
carry `nav:help` + `nav:hub:<parent>`.

## Remaining (follow-up, not this PR)

- **Game-result dead-ends** — `deathmatch._BotDuelView` (and fishing/casino result screens) extend
  `discord.ui.View` directly (transient game-state), so they're outside the panel auto-nav; they need a
  per-game back/replay. Separate small fix.

## Tests

- `tests/unit/views/test_navigation.py` — idempotency guard + 8 `attach_standard_nav` / `has_standard_nav`
  cases. Updated leaf-panel pins (mining ×4, cleanup ×2, btd6 legacy ids) to the new contract; the
  self-navigating panels (admin/utility/logging/flag_manager/server_management) stayed green unchanged.

(Close-out enders at session close.)

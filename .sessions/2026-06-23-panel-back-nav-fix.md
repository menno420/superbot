# 2026-06-23 — Universal panel nav: every panel is one click from Help + its hub

> **Status:** `complete` — owner-directed (Option 1). Built the "never stranded"
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

## Close-out

**Verification:** full suite `12154 passed, 48 skipped`; `mypy disbot/` clean (824 files);
`check_architecture --mode strict` 0 errors; `check_quality --check-only` green;
ledger + `check_docs --strict` pass (Q-0104 docs audit — nothing this session belongs in a
durable home that isn't already here; no new owner *decision*, this was an owner *directive*
already captured in CLAUDE.md's Working agreement, so no router Q needed).

**💡 Session idea (Q-0089):** *A CI invariant test that every `SUBSYSTEM`-declaring panel
carries a reachable Help affordance.* This session made "never stranded" true at runtime via
`attach_standard_nav`; the natural next guard is to make it **machine-checkable** — construct each
registered panel (or each `build_help_menu_view` result) in a test and assert it exposes a
`nav:help` (or self-navigating Help/Overview) control, so a future panel can't regress into a
dead-end. Distinct from the existing `check_command_reachability` / `test_help_reachability`
(those pin *command/help discoverability*, not that a *constructed panel* carries Help). Worth
having — it converts the owner's "one centralized app, never stranded" directive into a contract
the next agent can't silently break. Captured here; substantial enough to promote to a
`docs/ideas/` file in a grooming pass.

**⟲ Previous-session review (Q-0102):** the prior session (commit `6f5a5b8`, `carry_back`) correctly
root-caused the fresh-view-redraw mechanism and shipped a working fix + tests for farm — solid
diagnosis. What it **missed**: it solved the class **per-redraw-site** (`carry_back(self, view)` at
every rebuild), which would mean ~30 hand-edits and stays regression-prone (a new panel/redraw site
silently lacks it). The owner's very next message ("one script that loads them to all panels")
pointed at the better altitude. **System improvement surfaced & applied:** when the *same* concern
recurs across many panels, prefer a **base-class/constructor-level mechanism** over per-call-site
patches — it's regression-proof and covers *future* panels for free. This session moved the fix from
`carry_back` (per-site) to `attach_standard_nav` in `BaseView`/`PersistentView.__init__` (universal).
The `carry_back` work isn't wasted — it's the primitive (recorded re-attachers + idempotency) the
universal layer builds on. General rule worth keeping: *reach for the constructor seam before the
call-site patch.*

**Claim** `docs/owner/claims/claude__panel-back-nav-fix.md` deleted at close (Q-0126).


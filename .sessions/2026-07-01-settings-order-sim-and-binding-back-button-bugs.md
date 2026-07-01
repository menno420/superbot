# 2026-07-01 — Server-logging: per-route binding crash + disappearing back button + settings-order sim

> **Status:** `in-progress`

**Run type:** `manual` — owner bug report (screen recording of the live bot).

## What I'm about to do

Owner sent a 50s Discord screen recording (`!settings` → Server Logging → Routes) with three
asks + a simulation. Frame-by-frame analysis (frames extracted via PyAV; contact sheets in the
session scratchpad) pinned all of it:

1. **Per-action binding crash (root cause found).** In the Routes panel, picking an *event* route
   (`events` / `message_log` / `member_log` / `role_log`) and clicking **Set Channel** shows
   *"An error occurred. Please try again."* Cause: `cogs/logging/select_view.py::_KIND_TO_LABEL`
   was never extended when the Q-0109 event routes were added to `_KIND_TO_BINDING` — it stops at
   `audit`. `_LogChannelSelect.__init__` does `_KIND_TO_LABEL[kind]` → **KeyError** for the four
   event routes → the view's `on_error` emits the generic message. `provision_view._KIND_TO_LABEL`
   *does* have them (so **Create** works, **Set** crashes) — a copy-paste drift the route-table
   consistency test never caught because it pins `_KIND_TO_BINDING` but not `_KIND_TO_LABEL`.
   Fix: complete the label map + make the lookup total (`_label_for`) + extend the pin test.

2. **Disappearing "Back to Settings"/"Back to Help" (root cause found).** `LoggingPanelView`
   declares `SUBSYSTEM="logging"` so the linter (`_class_gets_auto_nav`) assumes the universal
   `attach_standard_nav` gives it a Help/hub back button — but at runtime `_self_navigates()`
   sees its **"↩ Overview"** button (a no-op self-refresh) and *skips* the auto-nav. So the panel
   depends on the *externally*-attached "↩ Back to Settings"/"Back to Help", which is dropped the
   moment it rebuilds a fresh view instance (the Routes round-trip: `routes_btn` and
   `LoggingRoutesView.btn_back` rebuild without `carry_back`). Fix: stop treating "overview" as
   self-nav (so `attach_standard_nav` covers these panels) + `carry_back` across the Routes hops.
   Enumerating the other panels in this class ("↩ Overview" self-refresh under a `SUBSYSTEM`).

3. **Settings-order simulation + "easy and clear to change all this."** Build
   `tools/sim/settings_order_sim.py` (the `help_menu_grouping_sim` pattern): score orderings of the
   11 logging routes (fallback-coverage + category cohesion) and the settings-group dropdown
   (`ui_priority`/setup-journey), recommend + apply the winner, and make the routes panel state the
   "set `mod` + `events` first, the rest fall back" model up front.

Additive / reversible / test-covered. Then flip this card to `complete`.

## What shipped

_(pending — filled in at close)_

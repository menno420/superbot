# 2026-07-01 — Server-logging: per-route binding crash + disappearing back button + settings-order sim

> **Status:** `complete`

**Run type:** `manual` — owner bug report (50s Discord screen recording of the live bot).

## Arc

Owner recorded himself walking `!settings` → **Server Logging** → **Routes** and asked for four
things: (1) analyse the recording frame-by-frame; (2) a **simulation** to find the best order of
these settings, "easy and clear to change all this"; (3) why the **back-to-help / back-to-settings**
buttons disappear + which other menus; (4) why he **can't independently bind each action's channel**
("all enabled but I can't change their bindings"). Extracted frames with PyAV (no ffmpeg in the
sandbox), built contact sheets, and read every UI state. All four resolved on PR #1619.

## What shipped

### 1. Per-action binding crash — `fix(logging)` (commit 80747c2)
Frame #88 caught the live failure: picking an **event** route (`message_log`) + **Set Channel** →
*"An error occurred. Please try again."* Root cause: `cogs/logging/select_view.py::_KIND_TO_LABEL`
was never extended when the Q-0109 event routes (`events`/`message_log`/`member_log`/`role_log`) were
added to `_KIND_TO_BINDING`, so `_LogChannelSelect.__init__` did `_KIND_TO_LABEL[kind]` → **KeyError**
→ the view's `on_error` emitted the generic ephemeral. `provision_view` *had* the labels (so **Create**
worked, **Set** crashed) — a copy-paste drift the route-table consistency test missed because it pins
`_KIND_TO_BINDING` but not the label map. Fix: complete the map, add a **total** `_label_for()`
backstop (never `KeyError`) in both view modules, route every label lookup through it, and **pin
`_KIND_TO_LABEL` coverage** in the consistency test + a per-route construction test.

### 2. Disappearing "↩ Back to Settings" / "↩ Back to Help" — `fix(logging)` (commit 80747c2)
Frames u080 vs u113 caught it: the panel had "↩ Back to Settings" right after **Open Panel**, then
lost it after the Routes round-trip. **Two compounding defects:**
- `navigation._self_navigates()` treated the panel's **"↩ Overview"** (a *self-refresh*, not
  parent-nav) as self-navigation, so `attach_standard_nav` **skipped** `LoggingPanelView` — even
  though it declares `SUBSYSTEM="logging"` and the `back_button` linter (`_class_gets_auto_nav`)
  *assumes* SUBSYSTEM panels get auto-nav. Static check said "covered"; runtime opted out. Fix: drop
  "overview" from the self-nav signal → the panel now auto-gets **📚 Help + ↩ Moderation**.
- The externally-attached back was dropped on every fresh-instance rebuild. Fix: `carry_back()` at the
  three verified sites — `LoggingPanelView.routes_btn`, `LoggingRoutesView.btn_back`, and (same class,
  self-initiated) `_PlatformHubView.btn_flag_manager`.
- **Which other menus (verified sweep):** `EconomyPanelView` was the same "Overview false-positive"
  class — fixed by the single `_self_navigates` change (it now auto-gets 📚 Help). The other
  `↩ Overview` panels (four_twenty/admin/utility/general) **don't** declare `SUBSYSTEM`, so they were
  never in this class. `_PlatformHubView → Flag Manager` was the third drop-back site.

### 3. Settings-order simulation + apply — `feat(settings)` (commit 9cfc574)
`tools/sim/settings_order_sim.py` (the `help_menu_grouping_sim` pattern; live tables, stdlib, `--check`
guard) scores the two ordered surfaces in the clip:
- **Logging routes:** roots-first (`mod`, `events` lead — the two fallback roots) beats the old
  category-first order — **scroll-to-full-coverage 7 → 1**. Applied to `_ROUTE_DISPLAY_ORDER`; the
  Routes panel now opens with *"set `mod` + `events` and everything is covered."*
- **Settings dropdown:** `!settings` is admin-only, yet it sorted by the **global** `ui_priority`
  (games/economy first, admin/config last) — so the owner scrolled past ~15 fun groups to reach
  Logging(85)/Moderation(80). That's the long scroll in the clip. Fix: a **settings-surface-only**
  admin-config-first sort in `actionable_settings_groups()` (server-ops groups first, `ui_priority`
  within each tier) — mean config-group **find-cost ~28 → ~8 rows**. Global `ui_priority` (Help/hubs)
  is untouched (verified `actionable_settings_groups` is consumed only by the Settings hub).

## Verification

- `check_quality.py --full`: **green** — 13620 passed, 48 skipped, 2 xfailed; black/isort/ruff (CI
  scope) + `mypy disbot/` clean.
- `check_architecture --mode strict`: 0 new errors (only pre-existing warnings).
  `check_consistency --mode strict`: passed. `check_docs --strict`: passed.
- `settings_order_sim.py --check`: OK (shipped `_ROUTE_DISPLAY_ORDER` == the roots-first recommendation).
- Live-constructed `LoggingPanelView` → now carries `nav:help` + `nav:hub:moderation`;
  `EconomyPanelView` → now carries `nav:help`.

## Context delta

- **Needed but not pointed to:** the runtime-vs-static nav mismatch — `_self_navigates` (runtime, in
  `navigation.py`) and `_class_gets_auto_nav` (the `check_consistency` `back_button` rule) each decide
  "does this panel have nav" by *different* signals, so a panel can pass the linter while runtime
  strands it. Nothing documents that they must agree. Filed as the session idea.
- **Discovered by hand:** `ui_priority` is a **global** ordering knob shared by Help / hubs / selectors
  / the settings dropdown. The "best order" for an admin surface differs from the discovery order, so
  the fix had to be a settings-*local* sort, not a global re-prioritisation.
- **Pointed to but didn't need:** CodeGraph — a `context_map` + targeted grep + reading the four
  panel/view modules carried the whole diagnosis (the frames pre-localised it).
- **Decisions made alone:** (1) applied the routes reorder (local, reversible, guarded) but made the
  settings-dropdown change a *sort policy* rather than rewriting 19 subsystems' `ui_priority` (that
  would have reordered Help too). (2) Fixed `EconomyPanelView` + the platform→flag-manager drop-back
  as the same verified class (root-cause over the single reported symptom). All reversible.

## 💡 Session idea

**A guard that reconciles runtime auto-nav with the `back_button` linter's assumption.** This bug hid
in the seam between two "does this panel have a back?" oracles that use *different* signals:
`navigation._self_navigates` (runtime — label/custom_id heuristic that *excludes* a panel from
auto-nav) and `check_consistency._class_gets_auto_nav` (static — assumes any `SUBSYSTEM` panel *gets*
auto-nav). A `SUBSYSTEM` panel whose only nav-shaped control is an `↩ Overview` self-refresh satisfies
the linter but is stranded at runtime. Concrete guard: a consistency rule that flags a decorated
button whose label is back-shaped (`↩`/"Back"/"Overview") **but whose callback only re-renders
`view=self`** (a no-op masquerading as navigation) — the exact tell that let this ship. Complements the
2026-06-20 idea (extend `back_button` to `add_item` controls): that one widened *what* the linter sees;
this one checks the *label doesn't lie about behaviour*. Small, disposable, high-signal.

## ⟲ Previous-session review

The 2026-07-01 fishing-structures-subhub run (#1603) did the back-nav **right**: the new
`StructuresView` set `SUBSYSTEM="fishing"` explicitly "so `attach_standard_nav` keeps Help + Games —
never a dead-end," and re-parented each structure's ↩ to the sub-hub with tests for every hop. Clean,
and a good model. **What it (unknowingly) dodged:** it relied on `attach_standard_nav` as the safety
net — the very mechanism this session found had the `_self_navigates` "Overview" blind spot. Had that
sub-hub carried an `↩ Overview` button, it would have been silently excluded from the auto-nav it was
counting on, exactly like `LoggingPanelView`. **System improvement:** the session idea above closes
that blind spot so "I declared `SUBSYSTEM`, so I'm never stranded" is actually *true* — the assumption
every recent nav-conscious session (this one included) leans on.

## 📤 Run report

- **Did:** diagnosed a 50s screen recording frame-by-frame; fixed the per-route Set-Channel crash + the
  disappearing back button (2 root causes, 3 panels) + built a settings-order simulation and applied
  its roots-first routes / admin-config-first dropdown recommendations. · **Outcome:** shipped, CI green.
- **Shipped:** PR #1619 (`claude/settings-simulation-binding-bugs-5ohozq`), born-red → complete.
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none. (The settings-dropdown reorder is a defensible admin-UX default;
  say the word if you'd prefer the old global-priority order there.)
- **⚑ Owner manual steps:** none — merge auto-deploys (`worker` redeploys on merge to `main`); no data
  step. Live-verify the Routes → Set Channel binding + the reordered dropdown after deploy.
- **⚑ Self-initiated:** `EconomyPanelView` back-nav fix + `_PlatformHubView → Flag Manager` `carry_back`
  (same verified class as the reported logging bug, beyond the literal ask); the settings-dropdown
  admin-first sort (the sim surfaced it from the clip's long scroll).
- **↪ Next:** if the nav guard idea appeals, build it as a focused `check_consistency` rule.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs opened this session | 1 (#1619) |
| Commits | 4 (born-red card · bug fixes · sim+apply · test-format) |
| CI-red rounds | 0 (green first full run; one local black pass on the sim/tests) |
| Root causes fixed | 2 (label-map drift · Overview-false-positive + missing carry_back) |
| Panels de-stranded | 3 (Logging, Economy, Platform→FlagManager) |
| New tests | 8 (label coverage · per-route construct · overview-not-self-nav ×2 · sim guards ×3 · dropdown order) |
| New ideas contributed | 1 (nav runtime-vs-linter reconciliation guard) |
| New tools | 1 (`tools/sim/settings_order_sim.py`) |

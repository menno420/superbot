# 2026-06-23 — Economy panel → Treasury button (panel-link fix)

> **Status:** `in-progress` — born-red card (Q-0133); flips to `complete` as the final step.
> Owner-directed (the maintainer reported treasury wasn't reachable from any panel and asked me to
> find out what went wrong). Follow-up to the merged treasury build (#1334).
> PR: this session → auto-merges on green CI (Q-0123).

## The bug (what the maintainer caught)

Treasury (#1334) registered as an Economy `primary_child` with a `build_help_menu_view` hook and
passed CI — but it had **no clickable entry on any panel**. It was reachable only by *typing*
`!treasury` / `!bank` / `!pool` or `!help treasury`.

**Root cause:** the Help-Home dropdown lists only the 7 hubs; selecting *Economy* opens
`EconomyPanelView`, whose buttons are **hardcoded** (Daily · Work · Shop · Balance · Inventory ·
Jobs). Unlike the **Games** hub (`views/games/hub.py`, which renders its children dynamically via
`discover_game_children` + `_GameHubButton` — so the farm button appeared for free), the Economy
hub does **not** render its `primary_children`. So registering treasury as an economy child wired
the roster + `!help treasury` direct-nav, but added no button. `leaderboard` (the other economy
`primary_child`) has the same latent gap.

**Why CI passed:** the discoverability invariant (`tests/unit/invariants/test_discoverability.py`)
only asserts each subsystem has a `build_help_menu_view` hook **or** a panel command — i.e. that it
*can be opened by typing*. It does **not** assert that a parent hub's panel renders a clickable
entry per child. That is the real hole the maintainer's intuition pointed at.

## The fix

- **`disbot/views/economy/main_panel.py`** — added a 🏛️ **Treasury** button (`economy:treasury`,
  row 1) to `EconomyPanelView`, mirroring `inventory_btn`: defer → `open_treasury_panel` →
  `attach_back_to_economy_button` (so Back-to-Economy, and Help → Economy → Treasury → Back chains
  correctly) → edit in place. Imports `open_treasury_panel` from `views.treasury` — a clean
  **views→views** edge (better than `inventory_btn`'s function-body `views→cogs` import).
- **`tests/unit/views/test_economy_treasury_button.py`** — pins the button exists, edits in place
  (no detached panel), and the opened view carries `economy:back`.
- **`docs/help-command-surface-map.md`** — treasury row now records the panel button.

Scope kept tight to the reported issue (treasury). `leaderboard`'s identical gap and the deeper
"Economy hub should render children dynamically like Games" + "a guard that every `primary_child`
is panel-linked" are surfaced as follow-ups (Enders), not built here.

## Verification

- `pytest tests/unit/views/test_economy_treasury_button.py + test_economy_inventory_edit.py` → 8 passed.
- (to fill on close) full `check_quality.py --check-only` · `mypy disbot/` · `check_architecture`.

## Enders

- **💡 Session idea (Q-0089):** a **panel-link discoverability guard** — extend the discoverability
  invariant so that for every hub, each `primary_child` is either rendered by the hub's panel
  (a `custom_id="<hub>:<child>"` button or dynamic child-rendering) **or** explicitly exempted.
  This would have caught treasury (and catches `leaderboard` now). The current guard only checks the
  hook exists, which is *openable-by-typing*, not *clickable-from-a-panel* — the exact gap the
  maintainer's intuition named.
- **⟲ Previous-session review (Q-0102):** the treasury build (#1334, my prior session) was solid on
  the money paths but made a wrong assumption — that adding `treasury` to the Economy hub's
  `primary_children` would surface a button, by analogy to the Games hub. It doesn't; the Economy
  hub hardcodes buttons. The session's own context-delta even flagged "the full registration surface
  is scattered" — but stopped at *CI-green* rather than *actually clickable in the product*. Lesson:
  "passes the discoverability guard" ≠ "a user can reach it by clicking"; verify the real entry path,
  not just the invariant. (This is the `verify-bot`/headless-smoke-harness gap the prior review also
  raised — a harness that opened the Economy panel and enumerated buttons would have caught it.)
- **⚑ Self-initiated:** none — owner-reported bug; fix is the direct response. `leaderboard` parity +
  the dynamic-rendering refactor + the new guard are flagged for owner steer, not built unprompted.

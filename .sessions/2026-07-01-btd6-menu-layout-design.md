# 2026-07-01 — BTD6 menu layout design (simulator) + round-range NL answer fix

> **Status:** `complete`

**Run type:** `owner-directed`

## What I did

Owner sent a 40s Discord screen-recording (scrolling the `/btd6` slash autocomplete, which
lists **both** the mature reference bot **Cyber Quincy** and **SuperBot**) + two screenshots,
and asked me to review it, build a **simulator to find the best menu layout** (many functions,
clear subdivisions, few presses), and fix the miss behind *"list all the bloons from r29 till
r63"* (it only answered the two endpoint rounds).

## What shipped (PR #1617)

**1 · Round-range NL answer fix (runtime).** Root cause: the resolver's `_ROUND_PATTERNS`
extract isolated round numbers with no range concept, and the Ask-modal path bypassed the
deterministic list floor — so a range grounded only its endpoints (rounds 29 + 63).

- `round_range_bloon_roster(lo, hi, roundset)` in `services/btd6_data_service.py` — walks every
  round in the range, returns the distinct bloon types (first/last round, rounds-present, total
  spawned) + modifiers seen; fails closed on an unknown set/range. Pure, sim-pinnable.
- `deterministic_round_range_bloons_reply` in `services/btd6_context_service.py` — a new
  `_BTD6_LIST_BUILDERS` floor that owns the range roster. Fires on one range + a bloon/spawn cue;
  defers on economy cues (economy builder) and 2+ ranges (comparison builder) — incl. a bare
  second-range guard so *"which has more bloons, 20-40 or 40-60"* defers. Pinned in the
  floor-exclusivity invariant corpus (+ an economy-vs-bloon boundary case).
- `for_list_reply` (`btd6_response_builder.py`) + a `_deterministic_list_floor` check in
  `btd6_ai_service.answer_question` — the Ask modal / `!btd6 ask` now serve the same authoritative
  floor the conversational stage already used, instead of the endpoint-only intent.
- Now: *"list all the bloons from r29 till r63"* → all 35 rounds, all 13 bloon types
  (Yellow…BFB) with spans + counts. +~30 tests (`test_btd6_round_range_bloons.py`).

**2 · Menu layout simulator + design study (docs/tooling).**
- `tools/btd6/menu_layout_simulator.html` — a self-contained, dependency-free interactive tool:
  the current panel vs. two redesigns (category hub / select hybrid), a data-driven function
  inventory (SuperBot `have` vs Cyber-Quincy `add` gaps), live clicks-to-reach / coverage /
  footprint metrics, and clickable ephemeral drill-down. Verified via Playwright screenshots.
- `docs/btd6/btd6-menu-layout-design-2026-07-01.md` — the written companion: the finding that
  **SuperBot already owns most of Cyber Quincy's functions but the panel under-surfaces them as a
  flat 13-button wall**; the ten subdivisions; the **mobile button-truncation finding** (5/row
  collapses "Events"→"E…", even 4/row clips 6-letter emoji labels); the A/B/C candidates +
  recommendation (**B, category hub, ≤4/row**); and a back-compat `panel.py` implementation plan.
  **The B-vs-C pick is left to the owner — the simulator's whole purpose.** Reachable from the
  btd6 index.

CI mirror: `check_quality.py --full` green (13,6xx passed); arch 0; check_docs strict green.

## 📤 Run report

- **Did:** (1) fixed the owner-reported round-range NL miss end-to-end (data primitive + list
  floor + Ask-path wiring + tests); (2) built the requested menu-layout simulator + a design study
  with a back-compat implementation plan · **Outcome:** shipped, CI green, auto-merge armed.
- **Shipped:** #1617.
- **Run type:** `owner-directed`.
- **⚑ Owner decisions needed:** the **B-vs-C layout pick** (category hub vs select hybrid) — open
  the simulator, then tell me which to implement (the panel rewrite is a ready, back-compat PR per
  the design doc §6). Not blocking.
- **⚑ Owner manual steps:** none — the bug fix is pure logic, live on next auto-deploy. Re-test in
  prod: ask the bot *"list all the bloons from r29 till r63"*. The simulator is a static file —
  open `tools/btd6/menu_layout_simulator.html` in any browser.
- **⚑ Self-initiated:** the menu **redesign was NOT auto-applied** — deliberately left as a
  simulator + plan for the owner's visual pick (he designs/visualizes; the sim exists to decide).
  The round-range fix + the tooling are the owner-directed asks.
- **↪ Next:** implement the chosen layout (design doc §6 — top-level regroup keeping every legacy
  `btd6:*` custom_id) → then the `add` backlog (Calculators / Challenge-Index families) as their
  own slices.

## 💡 Session idea (Q-0089)

**A panel "coverage lint" for slash-vs-panel parity.** This session's core finding — SuperBot
*owns* ~28 BTD6 functions but the panel only surfaces 13 — was invisible until I hand-inventoried
the slash tree against the panel buttons. A tiny checker that lists every `@app_commands.command`
/ registered function in a subsystem and flags the ones with **no panel/menu entry** would turn
"discoverability drift" into a visible signal for any subsystem (BTD6, mining, economy…), not
just a thing an agent notices by eye. It's the menu analogue of the existing help-catalogue
projection. Genuine (it *is* the finding that drove the design study); captured here — it needs
an owner nod on scope (per-subsystem opt-in) before it becomes a plan.

## ⟲ Previous-session review (Q-0102)

The previous run (#1596, fishing coral→curios) was a clean completion-first slice with a strong
self-audit — no complaint. What it (and the recent S1 cadence) **models well and I reused**: the
"pure, sim-pinnable, no-migration, byte-identical-when-inactive" discipline — my
`round_range_bloon_roster` follows the same shape (pure data primitive, fails closed, deferring
floor). **System improvement it surfaced for me:** its own Q-0102 note asked for **inline gate
tags** (`[offline]`/`[owner]`) on completion punch-lists; I applied that spirit to my run report's
`↪ Next` and to the design doc, tagging the owner-gated layout pick explicitly so a dispatch run
can see at a glance what's self-buildable (the `add` backlog) vs. what needs the owner (the B-vs-C
choice). The chain is auditing itself — the ask from #1596 shaped how I wrote #1617's handoff.

## Doc audit (Q-0104)

- Owner decision to route: the **B-vs-C layout pick** is captured as an explicit owner-gated item
  in the design doc + run report (not a router Q — it's a product-visual choice the simulator
  exists to serve, not a durable rule).
- Ledger: #1617 is the newest merge; the living-ledger reconciliation is the recon routine's job
  (next pass at #1620) — no drift to fix on sight. Deliberately did **not** hand-add my own
  unmerged PR to the ledger (the born-red rule's exact anti-pattern).
- New docs reachable + badged: design doc `plan`, linked from `docs/btd6/README.md` (new "UI /
  menu" section); `check_docs --strict` green (pinned paths all exist). Simulator lives in
  `tools/btd6/` (not a doc, so no badge needed).

## 🛠 Friction → guard (Q-0194)

- **Friction:** two Ask-path tests used `asyncio.get_event_loop().run_until_complete()` — green in
  isolation, **red in the full suite** (a closed/foreign event loop leaked from earlier async
  tests). The `--check-only` + isolated runs hid it; only `check_quality.py --full` caught it.
  **Guard (shipped):** converted them to the repo's `@pytest.mark.asyncio` + `async def`
  convention (what `test_btd6_ai_service` already uses) — isolation-safe by construction. **Durable
  lesson (recorded):** never drive an `async def` under test via `get_event_loop()`; always
  `@pytest.mark.asyncio`. The enforcing guard already exists — it's `check_quality.py --full`;
  the lesson is to trust *it* over the fast/isolated runs before flipping born-red.
- **Friction:** Playwright's ESM import ignores `NODE_PATH` for a globally-installed module.
  **Guard (habit):** import from the absolute path
  (`/opt/node22/lib/node_modules/playwright/index.mjs`) + let `PLAYWRIGHT_BROWSERS_PATH` locate
  Chromium (don't pass `executablePath` a directory). Recorded here for the next agent that
  screenshots a mockup.

## Context delta

- **Needed but not pointed to:** the split between the two BTD6 answer paths — the **Ask modal /
  `!btd6 ask`** (`btd6_ai_service.answer_question`) vs. the **conversational stage**
  (`natural_language_stage` → `deterministic_btd6_list_reply`) — was the crux of the bug: the list
  floor only covered the second path. `docs/subsystems/btd6.md` describes grounding but doesn't
  call out that the two surfaces had *diverged* on the floor. Now unified via `for_list_reply`.
- **Pointed to but didn't need:** the CodeGraph symbol tools — the fix was a contained,
  well-understood edit across four known files, so `context_map` + targeted grep carried it
  (the "contained change" path from `codegraph-usage.md`).

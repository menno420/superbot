# BTD6 menu layout — design study + implementation plan

> **Status:** `plan` — owner-directed design study (2026-07-01). The interactive
> tool is [`tools/btd6/menu_layout_simulator.html`](../../tools/btd6/menu_layout_simulator.html);
> this doc is its written companion + the back-compat implementation plan. The live
> panel is [`disbot/views/btd6/panel.py`](../../disbot/views/btd6/panel.py). No panel
> code changed yet — the **B-vs-C pick is the owner's**, made from the simulator.

## Why this exists

The owner sent a 40-second screen-recording scrolling the `/btd6` slash
autocomplete. It lists **two** bots side by side: the mature reference bot
**Cyber Quincy** and **SuperBot**. The ask: compare the surfaces, then build a
*simulator to find the best menu layout* that packs as many useful functions as
possible into clear subdivisions, staying clear without too many button presses.

The recording also carried a concrete miss — *"list all the bloons from r29 till
r63"* only answered for the two endpoint rounds. That bug is **fixed and shipped
this session** (see [§5](#5-the-round-range-answer-fix-shipped)); this doc is the
menu-layout half.

## 1. What the recording showed

Cyber Quincy exposes ~40 BTD6 functions as **flat slash commands** — `round`,
`rbe`, `tower`, `hero`, `herolevel`, `paragon`, `tierlist`, `temple`, `relic`,
`quiz`, `race_lb`, `ct_lb`, `nft`, `ltc`/`lcc`/`lcd`/`2tc`/`2mp`/`fttc`,
`calc`, `cash`, `crosspath_compare`, `bloon`, `boss`, `alias`, `balance`,
`decay`, `gluetrap`, `adora-sac`, `income`, `map`, … .

The key insight: **SuperBot already owns most of those functions** — as
`/btd6 <sub>` slash commands (`round`, `rbe`, `income`, `hero`, `tower`, `relic`,
`estimate`, `ct`, `strat *`, `events *`, `ops *`, `ask`, `status`, `diagnostics`)
plus the panel buttons. SuperBot is *not* missing the capability; the **panel
under-surfaces it**. The `/btd6menu` panel
([`panel.py`](../../disbot/views/btd6/panel.py)) shows **13 flat buttons** (Ask,
Live Events, Towers, Heroes, Leaderboards, CT, Modes, Status, Paragon, Admin,
Maps, Strategy, Help) with no grouping — so on mobile it is a tall ungrouped
wall, and the ~27 non-buttoned functions have **no panel entry at all** (they are
slash-only, i.e. undiscoverable from the panel).

## 2. Function inventory & subdivisions

The full, interactive inventory (with per-function descriptions and a
have/add filter) lives in the simulator. Summary — **ten subdivisions**:

| Subdivision | Have today | Candidate additions (Cyber Quincy gaps) |
|---|---|---|
| 🧠 **Ask** | AI Q&A | — |
| 🗼 **Units** | Towers, Heroes, Paragon calc | Crosspath compare, Tier list |
| 🎲 **Rounds & Economy** | Round, RBE, Income/cash, Bloon, Boss estimate | — |
| 🧮 **Calculators** | — | Cost calc, Cash-goal, Sun-Temple sacrifice, Hero-leveling, Glue duration, CT decay, Adora sacrifice |
| 🎯 **Live Events** | Live events, Leaderboards, CT + map, Relic | — |
| 🗺️ **Maps & Modes** | Maps, Modes | Tier list (shared w/ Units) |
| 📋 **Strategy** | Browse, Submit, Mine, Pending | — |
| 🏆 **Challenge Index** | — | 2TC, 2MP, LTC, LCC, LCD, FTTC databases |
| ℹ️ **Help & Status** | Status, Diagnostics, Help, Data sources | — |
| 🛠️ **Admin** (staff) | Seed, Sources, Announce, Readiness, Admin panel | — |

So SuperBot ships **~28** panel-worthy functions today and there are **~15**
worthwhile additions — but the two empty subdivisions (**Calculators**,
**Challenge Index**) are *all* candidate work, so they stay off the live panel
until at least one function in each exists.

## 3. The mobile-truncation finding

Building the mock surfaced a constraint the static comparison hid: **Discord
truncates button labels hard on mobile.** At the recording's width, **5 buttons
per row** collapses "Events" → "E…", and even **4 per row** clips a 6-letter
emoji label ("Rou…"). A Discord message is also capped at **5 action rows**, each
**5 buttons OR one select**. So the real design space is:

- **≤ 3–4 category buttons per row**, or drop emojis, to stay glanceable; **or**
- **a select menu**, which stays fully readable at any width and scales to
  unlimited categories, at the cost of one tap to reveal the list.

## 4. Candidate layouts

| | A — Current (flat) | **B — Category hub** | C — Select hybrid |
|---|---|---|---|
| Top-level controls | 13 buttons | 10 category buttons (≤4/row) | 2 buttons + 1 select |
| Rows on mobile | ~5 | 3 | 2 |
| Functions reachable from panel | 13 / ~43 | **43 / 43** | **43 / 43** |
| Clicks to any function | 1 (for the 13) | ≤ 2 | ≤ 2 |
| Glanceable subdivisions | none | **yes** | in the dropdown |
| Label readability on mobile | good (≤3/row) | good at ≤4/row | **best** |

**Recommendation: B (category hub, ≤4 buttons/row).** It makes every subdivision
a labelled, glanceable button, keeps depth at ≤2 clicks, and has room for the
whole Calculators + Challenge-Index backlog without adding a top-level control.
**C** is the compact fallback if footprint matters more than glanceability. Both
are strictly better than A on coverage. The **B-vs-C pick is the owner's** — the
simulator exists to make it.

## 5. The round-range answer fix (shipped)

Independent of the layout, the recording's *"list all the bloons from r29 till
r63"* miss is fixed this session:

- `round_range_bloon_roster(lo, hi, roundset)` in
  [`btd6_data_service.py`](../../disbot/services/btd6_data_service.py) walks every
  round in the range and returns the distinct bloon types (first/last round,
  rounds-present, total spawned).
- `deterministic_round_range_bloons_reply` in
  [`btd6_context_service.py`](../../disbot/services/btd6_context_service.py) is a new
  `_BTD6_LIST_BUILDERS` floor that owns the range roster; `for_list_reply` +
  `answer_question` in
  [`btd6_ai_service.py`](../../disbot/services/btd6_ai_service.py) serve it on the
  Ask-modal path too (which previously bypassed the floor). Tests:
  [`test_btd6_round_range_bloons.py`](../../tests/unit/services/test_btd6_round_range_bloons.py).

## 6. Implementation plan (for the chosen layout)

A single, back-compat-safe restructure of the `BTD6PanelView` persistent view.
The persistent-view contract requires **stable `custom_id`s** for existing anchor
messages, so the plan **keeps every legacy `btd6:*` id working**.

**PR 1 — top-level regroup (no new capability).**
1. Repoint the top row(s) of `BTD6PanelView` to the chosen shape:
   - **B:** category buttons `btd6:cat:units` / `btd6:cat:rounds` / … , ≤4/row,
     each opening an ephemeral **sub-panel view** listing that category's
     existing `open_*` entries (reuse `open_tower_browser`, `open_hero_browser`,
     `open_paragon_calculator`, the round/rbe/income builders, etc.).
   - **C:** two buttons (`btd6:ask`, `btd6:events`) + a `discord.ui.Select`
     (`btd6:browse`) whose options are the categories, + `btd6:admin`.
2. **Back-compat:** keep the legacy leaf ids (`btd6:towers`, `btd6:heroes`,
   `btd6:modes`, `btd6:maps`, `btd6:strategy`, `btd6:status`, `btd6:paragon`,
   `btd6:ct`, `btd6:leaderboards`, `btd6:events`, `btd6:admin`) as **hidden
   handlers** so old anchor messages still route (the file already documents this
   pattern). New anchors render the new rows.
3. Surface the already-shipped-but-panel-invisible functions as sub-panel
   entries: **Round / RBE / Income / Boss estimate / Bloon / Relic / Diagnostics /
   Data sources** (all exist as slash commands today — they just gain a button).
4. Tests: extend the panel view tests to assert (a) every category button opens
   its sub-panel, (b) every legacy `custom_id` still resolves, (c) staff gating on
   Admin. Keep it `PersistentView`-conformant.

**PR 2+ (optional, backlog) — new capability.** Build the Calculators and
Challenge-Index families (the `add` column) behind their sub-panels: cost/cash
calculators reuse `btd6_data_service` cost engines; the challenge indices need a
new data source + `*_service`. These are separate, plannable slices — the panel
categories are ready to receive them.

## 7. Using the simulator

Open [`tools/btd6/menu_layout_simulator.html`](../../tools/btd6/menu_layout_simulator.html)
in a browser. Toggle **A / B / C**, click the phone's buttons/menu to walk the
real drill-down, and read the live metrics + inventory. The whole model is the
`DATA` object at the top of the file — edit the categories / functions / layout
rows to try your own grouping and everything re-renders. It is a static file
(no build, no server, no dependencies).

# 2026-07-01 — BTD6 menu layout design (simulator) + round-range NL answer fix

> **Status:** `in-progress`

**Run type:** `owner-directed`

## What I'm about to do

Owner sent a 40s Discord screen-recording (scrolling the `/btd6` slash autocomplete, which lists
**both** the mature reference bot **Cyber Quincy** and **SuperBot**) + two panel/response
screenshots, and asked me to:

1. **Review every frame** and compare Cyber Quincy's command surface to SuperBot's BTD6 menu.
2. **Build a "simulator" to find the best menu layout** — pack as many useful functions as
   possible into clear right-sized subdivisions, staying clear without too many button presses.
3. **Fix a real NL miss:** the question *"list all the bloons from r29 till r63"* only grounded
   the two endpoint rounds (29 + 62/63), not the whole range.

Plan:
- **Bug (root fix):** the resolver's `_ROUND_PATTERNS` extract isolated round numbers with no
  range concept, so a range query grounds only the endpoints. `_ROUND_RANGE_RE` /
  `round_composition(lo, hi)` already exist (used for cash/RBE totals) — add a deterministic
  **round-range bloon-listing** builder to `_BTD6_LIST_BUILDERS` + range-composition grounding,
  and reach the Ask-modal path too (it currently bypasses the list floor). Tests.
- **Simulator:** a self-contained interactive HTML page rendering the current panel + candidate
  redesigns (grouped category sub-panels / select-menu hybrid), with a full function inventory
  (SuperBot's existing slash surface + the Cyber Quincy gaps worth adding) and clicks-to-reach
  metrics — the maintainer's visualize-first design tool.
- **Redesign:** implement the recommended grouped layout in `panel.py` (back-compat custom_ids
  kept) + a design doc.

Aim: ship the bug fix + the simulator + a concrete panel improvement in one session.

## What shipped

_(filled in at close)_

## 📤 Run report

_(filled in at close)_

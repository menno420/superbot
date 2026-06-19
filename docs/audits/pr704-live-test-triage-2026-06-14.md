# PR #704 — live-test screenshot triage (2026-06-11 → reviewed 2026-06-14)

> **Status:** `historical` — a dated triage of the 11 Discord screenshots in PR #704 (owner's live
> **Superseded 2026-06-19 (was active):** Dated #704 triage; the AI grounding-consistency finding fed the P1-1 lane. Do not act on this — current map: [planning/README](../planning/README.md).
> testing, 2026-06-11), reviewed 2026-06-14 (the screenshots had sat un-triaged with zero comments).
> Findings reflect the 2026-06-11 bot state; **much shipped since** (e.g. #855 BTD6 path-resolution).
> This doc preserves the findings so #704 can be closed without losing them.

## Verdict
**Predominantly working.** The owner described "a mix of bugs and good working results" — it leans
heavily to *working*. The mining/crafting RPG and the BTD6 hub are functional and fairly polished.
Only one substantive issue, and it's already owned by the active **P1-1 eval-smoke** lane.

## What the screenshots show

| # | Screen | Verdict |
|---|---|---|
| 1, 10 | Equipment slot manager + PIL avatar render | ✅ works · cosmetic: avatar art is a crude stick-figure |
| 2, 5 | Equipment panel + AI **grounding-refusal** on round-economy ("20K by round 50 → round 60") | ✅ refusal working (absence-claim guard) |
| 3 | Grounding-refusal again, then a confident BTD6 price ("Despo = Plasma Monkey Fan Club $54,000", ×10,041 = $542,214,000) | ⚠️ math correct; **grounding-consistency** Q (see below) |
| 4 | BTD6 capability list + "Elite Lych HP per tier" answer (14k/52.5k/220k/525k/2.1M) | ⚠️ confident BTD6 numbers — accuracy unverified here |
| 6, 7 | BTD6 hub: live events (Cabin Fever race, Ability Mayhem odyssey…) + Mining ("mined 5x silver, Deep 2/3") | ✅ works — live data + mining loot/depth |
| 8 | Craft menu — recipes with resource costs, craftability checks | ✅ works |
| 9 | Workshop — durability (Diamond Pickaxe 391/400), repair costs, 39 recipes, balance | ✅ works, polished |
| 11 | Mining hub (Mine/Harvest/Explore/Build/Market/Workshop/…) + inventory + PIL inventory card | ✅ works |

## The one substantive finding — AI capability vs. behaviour inconsistency
The BTD6 capability message (screen 4) lists **"Round cash (per-round or range)"** as something it
*can* do, yet it **refuses every round-cash economy question** (screens 2/3/5: "how much would I have
by round 60", "8094$ round 60 → round 68") with the grounding-refusal. Meanwhile it *also* says "what
I don't have: modified-economy math (Double Cash, Half Cash, farm income)". So the **refusal is likely
correct** (cumulative multi-round projection is what it can't ground), but the **capability line
over-states** — it conflates "single-round cash lookup" with "multi-round projection."
- **Plus a grounding-consistency question:** it refuses round-economy numbers but confidently asserts
  *other* BTD6 numbers (Despo price, Elite Lych HP). Confirm those asserted values are actually
  grounded/correct (is "Despo" → Plasma Monkey Fan Club the right map? is $54k the Impoppable price?) —
  otherwise that's a grounding leak (asserting ungrounded facts), the exact class the absence-claim
  guard targets.

## Routing (nothing new to file urgently)
- The capability/grounding-consistency finding **feeds the active P1-1 eval-smoke matrix**
  (versioned AI/BTD6 gates · fallback · grounding-refusal) — it is a concrete test case for that lane,
  not a separate bug. Add it as a P1-1 eval case: *"capability message must match refusal behaviour;
  asserted BTD6 numbers must be grounded."*
- **Cosmetic:** equipment avatar PIL art is rudimentary — low-priority polish (games lane).
- Minor: username display showed `menno4207` (text) vs `Menno420` (image card) — verify truncation.

## Disposition
Findings preserved here → **#704 closed** (it was a screenshot drop, never a mergeable change; it sat
8 days with no triage). The screenshots remain in git history on `menno420-patch-2` if needed.

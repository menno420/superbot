# BTD6 QA accuracy corpus (2026-06-27)

> **Status:** `reference` — a verified question/answer corpus for BTD6 bot accuracy.
> Built from real player questions (r/btd6, Steam, GameFAQs, YouTube) cross-checked
> against the committed game-data dump and the Bloons wiki. Game-mechanical facts are
> verified against the dump and **win over** the wiki where they differ.

## Why this exists

The owner reported (live Discord screenshots) that the bot still answers many BTD6
questions wrong — most visibly the *"can glue / ice / avenger deal with a DDT?"* class.
This corpus is the durable record of:

1. **The questions players actually ask** (the "large list"), categorized.
2. **The verified-correct answer** for each, with a source.
3. **What the bot now grounds** after this session's damage-type interaction layer.

**Verification legend:**
- `[dump ✓]` — verified against the committed game-data dump (`disbot/data/btd6/`),
  which is sourced from the BTD Mod Helper game-data export + the Bloons wiki Cargo.
- `[wiki]` — sourced from the Bloons wiki (bloons.fandom.com / bloonswiki.com); stat
  numbers are **patch-dependent** — spot-check against the live wiki for a current patch.
- `[fixed]` — a fact the bot previously got wrong that this session corrected.

## Session corrections (what was wrong, and the fix)

The data dump's bloon **immunities are correct** (they are game-data-sourced). The bot's
errors were in **interaction reasoning** — the immunities and the tower descriptions were
grounded *separately*, so the model invented the rule connecting them. Fixes shipped:

| # | The bot said (wrong) | The truth | Fix |
|---|---|---|---|
| 1 | "DDTs have Lead properties, which **resist glue**" | Glue is a **status effect**, not damage — it ignores damage-type immunity and slows Lead fine. MOAB-class (incl. DDT) just needs **MOAB Glue (0-0-3)** to be *targeted*. | `[fixed]` new `[btd6_interaction]` glue fact |
| 2 | Avenger (Desperado) deals **Sharp** | Avenger's slug shrapnel is **Shatter** (still blocked by Lead, but for the right reason). | `[fixed]` shatter damage-type fact |
| 3 | Ice can't slow DDTs (stated, but missed the fix) | Base ice is **cold**, blocked by Lead — but **Cold Snap (2-0-0)** "can freeze and pop Lead and Camo", and **Embrittlement (4-0-0)** strips Lead immunity. | `[fixed]` slow/freeze fact names the crosspaths |
| 4 | Lead "immune to **Sharp**" (only) | Lead is immune to **Sharp, Shatter, Cold, Energy** (the `immune_to` line had all four; the prose didn't). | `[fixed]` Lead/DDT prose completed |
| 5 | (research agent claimed) "Sniper is **Normal** damage, pops Lead at base" | The game export says Sniper base is **Sharp**, `cannot pop Lead or frozen`. Trust the dump. | excluded from corpus |

---

## Core reference — damage types × bloon properties (fully `[dump ✓]`)

Derived by inverting the game-sourced `immune_to` fields in `bloons.json`, cross-checked
in `tests/unit/services/test_btd6_interaction_service.py`.

**A damage type CANNOT pop a bloon with these properties:**

| Damage type | Blocked by | Pops Lead? | Pops Black? | Pops Purple? |
|---|---|---|---|---|
| Normal | (nothing) | ✅ | ✅ | ✅ |
| Sharp | Lead, Frozen | ❌ | ✅ | ✅ |
| Shatter | Lead | ❌ | ✅ | ✅ |
| Explosion | Black | ✅ | ❌ | ✅ |
| Cold | White, Lead | ❌ | ✅ | ✅ |
| Glacier | White | ✅ (unlike Cold) | ✅ | ✅ |
| Frigid | White, Purple | ✅ | ✅ | ❌ |
| Energy | Lead, Purple | ❌ | ✅ | ❌ |
| Plasma | Purple | ✅ | ✅ | ❌ |
| Fire | Purple | ✅ | ✅ | ❌ |
| Acid | (nothing standard) | ✅ | ✅ | ✅ |

**Status effects (glue / slow / freeze / stun / knockback) are NOT damage** — they ignore
damage-type immunity, so they work on Lead/Black/Purple. But:
- **MOAB-class** (MOAB/BFB/ZOMG/DDT/BAD) needs a MOAB-targeting upgrade to be affected
  (MOAB Glue 0-0-3 for glue; MOAB Shove 0-0-3 for knockback; Embrittlement/Snowstorm for ice).
- The **BAD** is immune to ALL slow/glue/stun/knockback (except a few named abilities).

**How to deal with each property:** Lead → Explosion/Fire/Plasma/Glacier/Acid/Normal · Black
→ any non-Explosion · White → any non-Cold · Purple → Sharp/Explosion/Cold/Acid/Normal ·
Zebra → Sharp/Fire/Plasma/Acid (not Explosion, not Cold) · Camo → any tower with camo
detection · **DDT** → camo detection **+** Fire/Plasma/Normal/Acid/Glacier (not
Sharp/Shatter/Cold/Energy/Explosion).

---

## 1 — Damage-type interactions (the highest-error class, all `[dump ✓]`)

| Q | A |
|---|---|
| Can sharp/darts pop Lead? | **No** — Lead is immune to Sharp. Needs an upgrade that changes the type or a lead-popping buff (MIB, Alchemist). `[fixed]` |
| Can a Bomb Shooter pop Black bloons? | **No** by default — Explosion is blocked by Black. Needs MIB or a non-explosive crosspath. |
| Can you pop Purple with Plasma / lasers? | **No** — Purple is immune to Energy, Plasma, Fire, Frigid. Use Sharp, Explosion, Cold, or Acid. |
| Can a Wizard pop Lead? | Only with **Fireball (1-x-x)+** (fire). Base magic bolts are Energy → blocked by Lead. |
| Can base Glue Gunner pop/damage Lead? | Glue **slows** Lead fine (status). To *damage* Lead it needs **Corrosive Glue (2-x-x)**. |
| Can Ice Monkey freeze/pop Lead? | **No** at base (cold blocked by Lead). **Cold Snap (2-0-0)** adds it; **Embrittlement (4-0-0)** strips Lead immunity. |
| Can Ice Monkey freeze White or Zebra? | **No** — both are Cold-immune. |
| Can glue deal with a DDT? | Yes — with **MOAB Glue (0-0-3)** + camo detection. Lead does NOT resist glue. `[fixed]` |
| What is a DDT immune to? | Sharp, Shatter, Cold, Energy, Explosion (Lead + Black) — and it's Camo, so needs detection. |
| How do you pop a Camo-Lead bloon? | Camo detection **and** lead-popping at once — e.g. a fire/plasma tower with a camo crosspath, or a base lead-popper (Bomb/Mortar/Alch) under a camo-granting Village (Radar Scanner 0-2-0). |
| What is the simplest "pop everything" support? | Village **MIB (0-3-0)** or Alchemist **Acidic Mixture Dip (4-0-0)** — grants Normal-type popping (Lead **and** Purple). `[wiki]` |
| Is Glacier different from Cold? | Yes — Glacier pops Lead (Cold does not); both are blocked by White. |

## 2 — Bloon types & properties (`[dump ✓]` unless noted)

| Q | A |
|---|---|
| What is a DDT? | Dark Dirigible Titan — fast MOAB-class blimp with **Camo + Lead + Black**, 400 HP, splits into 4 Camo Regrow Ceramics. First appears **round 90**. |
| What does a Black bloon resist? | Explosion only. |
| What does a White bloon resist? | Cold/ice only. |
| What does a Zebra resist? | **Both** Explosion and Cold (Black + White). |
| What is a Lead bloon immune to? | Sharp, Shatter, Cold, Energy. Fortified Lead takes 4 hits. |
| What is a Purple bloon immune to? | Energy, Plasma, Fire, Frigid. |
| MOAB-class hierarchy + HP? | MOAB 200 → BFB 700 → ZOMG 4000 → BAD 20000. MOAB→4 Ceramics, BFB→4 MOABs, ZOMG→4 BFBs, BAD→2 ZOMG + 3 DDT. |
| What does a Ceramic split into? | 2 Rainbows; 10-HP shell (20 fortified). |
| What does Fortified do? | ~Doubles HP (Ceramic/MOAB-class); Lead → 4 hits. Applies to Lead, Ceramic, MOAB-class. |
| How do Regrow bloons work? | Regrow popped outer layers over time unless fully destroyed; stripped by tornadoes, Ezili, Monkey Sabotage. |
| Which towers see Camo unupgraded? | **Ninja, Spike Factory, and Desperado** innately (verified from the dump). Sniper is **not** innate — it needs **Night Vision Goggles (0-1-0)**. Others need a crosspath, Village Radar Scanner (0-2-0), Alchemist, or Etienne. `[dump ✓]` |
| Which towers pop Lead unupgraded? | **Bomb Shooter, Mortar, Alchemist** (verified from the dump). Sniper is **Sharp** at base and **cannot** pop Lead until **Full Metal Jacket (1-0-0)** makes its shots Normal. `[dump ✓]` |
| Is camo a bloon type? | No — a **modifier** that can apply to any bloon. |

## 3 — Economy & rounds (`[dump ✓]`)

| Q | A |
|---|---|
| How much money per round? | $1 per pop + end-of-round bonus ($100 + round#); pop-cash taxed −50% from round 51. `[wiki]` |
| When do MOABs first appear? | **Round 40.** |
| When do Ceramics first appear? | **Round 38** (round 35 is the first Rainbow). |
| When do Lead / Zebra appear? | Lead **round 28**, Zebra **round 26**. |
| When do BFB / ZOMG appear? | BFB **round 60**, ZOMG **round 80**. |
| When do DDTs / BADs appear? | DDT **round 90**, BAD **round 100**. |
| Basic Banana Farm income? | $80/round (4 bananas × $20). `[wiki]` |
| Banana Research Facility (4-2-0)? | ~$1,500/round. `[wiki]` |
| Difference: cash vs Monkey Money? | Cash = per-match, resets. Monkey Money = persistent meta-currency. `[wiki]` |
| Starting cash? | $650 on Easy/Medium/Hard; Half Cash $325; Deflation $20,000. `[wiki]` |

## 4 — Paragons (`[dump ✓]` for count/cost/towers)

| Q | A |
|---|---|
| How many Paragons / which towers? | **13** (dump has 13): Dart (Apex Plasma Master), Boomerang (Glaive Dominus), Ninja (Ascended Shadow), Buccaneer (Navarch of the Seas), Engineer (Master Builder), Ace (Goliath Doomship), Wizard (Magus Perfectus), Sub (Nautic Siege Core), Bomb (Ballistic Obliteration Missile Bunker), Ice (Herald of Everfrost), Spike Factory (Mega Massive Munitions Factory), Druid (Root of all Nature), Super Monkey (Crucible of Steel and Flame). |
| How do you make a Paragon? | Have all three Tier-5s of one tower on the map; the Paragon upgrade appears and sacrifices them + all other towers of that type. `[wiki]` |
| Cheapest Paragon? | **Apex Plasma Master (Dart) — $150,000** base. |
| Max Paragon Degree? | 100; solo caps ~91 without Geraldo totems / co-op extra T5s. `[wiki]` |
| Paragon limit? | One per tower type per game; capped at 4 per player in Boss/Contested Territory. `[wiki]` |

## 5 — Heroes (`[wiki]` — heroes.json has no cost field)

Quincy (cheapest), Gwendolin (fire/lead support), Obyn (best free, magic buffs), Striker
Jones (explosives, pops Black/Zebra), Ezili (MOAB shred, strips Regrow/Purple), Adora
(top-tier magic), Sauda (melee early carry), Psi (camo + telekinesis), Geraldo (shop items
incl. Paragon Power Totem), Corvus (spellcaster, high skill), Etienne (global camo at L8),
Benjamin (economy — **useless in CHIMPS**), Admiral Brickell (**water-only**), Captain
Churchill (tank — can't hit DDTs without abilities, they're camo). `[wiki]`

## 6 — Boss bloons (`[wiki]`)

Bloonarius (spawns bloons), Lych (spawns invulnerable-making Souls that drain lives),
Vortex (stuns towers in a radius at each skull), Dreadbloon (cycles immunity to whole tower
**categories**), Phayze (camo + Radar Jam, immune to decamo — use innate camo detection),
Blastapopoulos (fireballs debuff towers). **All bosses are immune to stuns, slows,
knockback, and instakills/%-HP removal**, and take bonus damage from Paragons. `[wiki]`

## 7 — Modes (`[wiki]`)

CHIMPS (no Continues/Hearts/Income/Knowledge/Powers/Selling; 1 life, R6→100, Hard prices),
ABR (alternate harder rounds; beat to unlock CHIMPS), Deflation ($20k, no income, R31→60),
Half Cash (all income incl. start halved), Impoppable (1 life, +20% cost), Magic Monkeys
Only, Double HP MOABs, Sandbox. `[wiki]`

---

## What the bot now grounds (verify with the probe)

The `[btd6_interaction]` facts fire for the interaction questions above. Probe any of them:

```
python3.10 scripts/btd6_probe.py "can glue strike deal with DDTs"
python3.10 scripts/btd6_probe.py "what pops lead bloons"
python3.10 scripts/btd6_probe.py "can ice monkey slow ddts"
```

A question that grounds **0 interaction facts** but is clearly an interaction question is a
gap — add a trigger token / alias to `btd6_interaction_service` or a row to
`damage_types.json` (and a cross-check stays green because the table is validated against
the game-sourced `immune_to` data).

## Testing the whole corpus at once

This corpus is wired into the eval system as `tests/evals/btd6_corpus.py` (the machine half),
keyed off the bot's REAL `btd6_context_service.build()` grounding:

- **Offline, free, every PR** — `python3.10 -m pytest tests/evals/test_btd6_qa_corpus.py` asserts
  each question grounds its answer-bearing fact. This is the trustworthy "all at once" check; it
  proves the stored data is accessible + correct per question with no model variance.
- **Live, paid, opt-in** — the *AI Evals* GitHub Action (**suite: btd6**), or
  `RUN_EVALS=1 … python3.10 scripts/run_evals.py --btd6-only`. This replays each question through the
  **REAL production answer path** (`tests/evals/btd6_live_path.py`): real router → real grounding → real
  instruction stack → real gateway call → real faithfulness guard + regenerate-once + refusal. The
  result is **what a live Discord user would get** (only Discord I/O + the audit log are skipped). It
  tests the provider set in `AI_DEFAULT_PROVIDER`.

## Session arc — what shipped (2026-06-27, all merged)

| PR | What it did |
|---|---|
| **#1487** | The root fix: `damage_types.json` + `btd6_interaction_service` ground damage-type ↔ bloon-property INTERACTION facts (the "Lead resists glue" class), cross-checked against the game-sourced `immune_to` data. Plus this corpus + bloon-prose completion. |
| **#1488** | Corpus wired into the evals: the offline grounding test (`test_btd6_qa_corpus.py`, free, every PR) + the live action suite picker. |
| **#1490** | The faithful **"exactly live"** runner (`btd6_live_path.py`) — replays the real production answer path (router → grounding → instruction stack → gateway → faithfulness guard). |
| **#1491** | Fixed the eval grader: live answers are graded **semantically** by `llm_judge` (the model paraphrases — substring-matching the fact wording gave false negatives). |
| **#1492** | Verified **DDT counter-tower grounding** (`towers_that_can_damage`) so "how do I deal with a DDT" recommends real towers instead of refusing. |

## Live verification checklist — what still needs a real-key / prod test

Everything above is offline-verified (1500+ tests, no creds). These need a real provider key or a live
bot to confirm, and are **not** done:

- [ ] **Re-run *AI Evals → suite: btd6*** after deploy. Expect: the interaction questions PASS on the
      semantic grader, and **`how do I deal with a DDT` now answers with towers instead of refusing**
      (the #1492 fix — not yet re-run live).
- [ ] **Live Discord spot-check** of the original screenshot questions (glue/avenger/DDT, "can ice slow
      DDTs") on the real bot — confirm the answers are now correct in production, not just in the eval.
- [ ] **The golden-set over-refusals are NOT fixed** — `knowledge.btd6_round_cash_*`,
      `btd6_elite_lych_hp`, `btd6_despo_bulk_cost`, `bomb_middle_path_moab`. Two parts: (a) the
      round-cash ones partly reflect a **harness limitation** — those answers need a DB-resolved
      orchestration profile that can't run in a keyless/DB-less eval; (b) the rest may be a real
      guard-strictness/grounding issue worth its own look. Separate from this session's scope.
- [ ] **A couple of golden rubrics look stale** (e.g. `knowledge.btd6_lead` expects "Sharp Shots lets
      Dart pop Lead" — it's +pierce, not lead-popping). Verify + fix the rubrics, not the bot.

## Open follow-ups (next sessions)

- **Generalize the counter grounding** beyond DDT — `towers_that_can_damage` is already general; extend
  the `_COUNTER_BLOON_FOR` map in `btd6_interaction_service` to camo-lead / the Camo bloon to close the
  same over-refusal there.
- **Broaden the live corpus** with strategy/opinion questions graded by `llm_judge` rubrics.
- **Newer-tower coverage** (Desperado, Mermonkey): the dump has them; spot-check their damage-type
  interaction questions ground correctly.
- **Hero costs** are absent from `heroes.json` — wiki-only for now; a future data pass could add them so
  cost questions are dump-verified like tower costs.

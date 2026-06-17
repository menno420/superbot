# Night work queue — 2026-06-16 (for the scheduled dispatch routine)

> **Status:** `plan` — a grounded, ordered queue of **bot-section (`disbot/` runtime)**
> slices for the autonomous **dispatch routine** to advance on its scheduled fires
> (`0 */2 * * *` UTC → 00:00 / 02:00 / 04:00 / 06:00 — "the ~4 that run overnight,
> including 12am"). Owner directive, in-session 2026-06-16.
>
> **How a fire consumes this:** a scheduled fire has no work order → it `git reset
> --hard origin/main`, reads `current-state.md` ▶ Next action (now pointed here), and
> **builds the topmost slice still marked `TODO` below**, verified against the live
> ledger (a slice another fire/agent already shipped is skipped). One slice = one PR.
> Each fire ships its slice, ticks it `✅ #NNN` here, and re-points ▶ Next action at the
> next `TODO` slice — the self-chaining loop. **Pick by description, never by a
> predicted PR number** (Q-0142).

## Why this lane (grounded)

The buildable `ready` decade-queue is otherwise thinned to `plan-first` / `creds` /
`owner` / `data`-gated work (band-#930 pass §3). But there is one **proven, ungated,
factory-pattern** runtime lane with real backlog: the **deterministic BTD6 floor
builders** (AI §7.5 comparison + §7.6 roster families). The routines have shipped this
exact shape five times — #946, #950, #955, #962, #975 — so it is low-risk and
well-understood. Every slice below is:

- **Read-only & deterministic** → ships under the **Q-0048** standing lift (no
  owner per-exposure ask, **no prod-check gate**, auto-deploys on merge).
- **Data-complete today** → reads a field that already exists in a committed
  `disbot/data/btd6/*.json` file (no `!btd6ops seed-data`, no new data sourcing).
- **Self-contained** → one new primitive in `btd6_data_service.py` (or a reader) +
  one `deterministic_*_reply` in `btd6_context_service.py` + registration in the
  `_BTD6_LIST_BUILDERS` seam + a corpus entry + one test file. ~one PR each.
- **Correctness work, not make-work** → each closes the **BUG-0009 class** ("grounded
  values, wrong *assembly*" — the value-only faithfulness guard can't catch a
  mislabeled/mis-grouped list), the standing P1 priority.

**Bugs-first override (standing):** if a `/bugreport` or a `continue` handoff arrives
overnight, that jumps this queue (the dispatch prompt already does this) — this queue is
the *default* work for an empty scheduled fire, not a lock.

## The seam (shared by every slice)

- **Registration:** `_BTD6_LIST_BUILDERS` tuple — `disbot/services/btd6_context_service.py:2856`
- **Dispatcher (the BTD6-path floor, before the model):** `deterministic_btd6_list_reply`
  — `disbot/services/btd6_context_service.py:2869`
- **Exactly-one-fires invariant:** `tests/unit/invariants/test_btd6_floor_builder_exclusivity.py`
  — a new builder **must** add one `_SHOULD_FIRE` corpus phrase (line ~38) or the
  coverage test fails; and it must `None`-defer on every other builder's should-fire
  phrase (no shadowing).
- **Reference PRs to mirror:** comparison → #962 (`compare_paragon_costs` +
  `deterministic_paragon_cost_comparison_reply`); roster → #975
  (`deterministic_capability_roster_reply` / `deterministic_bloon_roster_reply`).
- **Reference test scaffold:** `tests/unit/services/test_btd6_paragon_cost_comparison.py`
  (primitive edge-cases → reply match/defer → dispatcher + exclusivity).

> **Per-fire discipline (avoid the one structural conflict):** `_BTD6_LIST_BUILDERS`
> and the `_SHOULD_FIRE` corpus are shared append anchors. Fires are 2h apart and each
> slice merges to `main` before the next fire syncs — so **sync `origin/main` first**
> and append cleanly. Mind **dispatch order**: register a *narrower/more-specific*
> builder **before** a broader sibling so it isn't shadowed (the paragon-before-tower
> ordering #962 established).

---

## The queue (build the topmost `TODO`, newest progress ticked)

| # | Slice | Family | Status |
|---|---|---|---|
| 1 | **Hero cost comparison** | §7.5 | ✅ #1000 |
| 2 | **Power (activated-ability) cost comparison** | §7.5 | ✅ #1008 |
| 3 | **Relic category/effect roster** | §7.6 | ✅ #1009 |
| 4 | **Bloon property roster** | §7.6 | `NEEDS-REFRAME` (see below) |
| 5 | **Hero ability roster** | §7.6 | ✅ #1010 |

Buffer (if a fire is fast or a slice above turns out already-built): **Geraldo
items-by-unlock-level roster** · **Monkey-Knowledge category roster** (both §7.6,
data-complete — detailed at the foot).

---

### Slot 1 — Hero cost comparison (§7.5) · `ready`

- **Question shape:** "is Quincy or Benjamin cheaper?", "which hero costs less,
  Obyn or Churchill?", "cheapest hero out of Gwen, Striker, Ezili" — rank the **base
  cost** of **two or more** heroes. The model would otherwise assemble the ranking and
  can mis-state which is cheaper / by how much (BUG-0009 class).
- **Data:** `disbot/data/btd6/heroes.json` → `base_cost` (present for every hero;
  already read by `deterministic_roster_reply`).
- **Build:** `btd6_data_service.compare_hero_costs(names)` — resolve each hero, dedup on
  id, rank ascending by `base_cost`, **fail closed** on <2 distinct.
  `btd6_context_service.deterministic_hero_cost_comparison_reply` — fires on a hero
  reference + a cost-compare cue + ≥2 resolved heroes; defers otherwise. Register in
  `_BTD6_LIST_BUILDERS`.
- **Tests:** `tests/unit/services/test_btd6_hero_cost_comparison.py` (primitive +
  reply + dispatcher) + one `_SHOULD_FIRE` corpus phrase.
- **Mirror:** #962 almost exactly (paragon → hero; `compare_paragon_costs` is the
  template). The closest, lowest-risk slice — build it first.

### Slot 2 — Power (activated-ability) cost comparison (§7.5) · `ready`

- **Question shape:** "which power is cheaper, Banana Farmer or Time Stop?", "is Cash
  Drop or Pontoon more expensive?" — rank **monkey-money cost** of **two or more**
  powers.
- **Data:** `disbot/data/btd6/powers.json` → `monkey_money_cost` (present for every
  power).
- **Build:** `btd6_data_service.compare_power_costs(names)` (same shape as slot 1, axis
  = `monkey_money_cost`) + `deterministic_power_cost_comparison_reply`. Register after
  the entity-cost builders.
- **Tests:** `tests/unit/services/test_btd6_power_cost_comparison.py` + corpus phrase.

### Slot 3 — Relic category / effect roster (§7.6) · `ready`

- **Question shape:** "what economy relics are there?", "list all offensive relics",
  "which relics are utility?" — roster relics by `category` (and optionally name the
  `effect`). A *new entity* the roster family does not yet cover.
- **Data:** `disbot/data/btd6/ct_relics.json` → `category` (economy/offense/utility/
  lives/powerup) + `effect` (per relic).
- **Build:** a reader (e.g. `btd6_data_service.relics_by_category()`) + a
  `deterministic_relic_roster_reply` (relic cue + category keyword + enumeration cue).
  Register in `_BTD6_LIST_BUILDERS`.
- **Tests:** `tests/unit/services/test_btd6_relic_roster.py` + corpus phrase.
- **Mirror:** #975's roster builders (`deterministic_capability_roster_reply`).

### Slot 4 — Bloon property roster (§7.6) · `NEEDS-REFRAME` (not cleanly data-complete)

> **2026-06-17 finding (the #1010 fire, slot-4 pivot):** this slice is **not** as
> data-clean as assumed — do **not** build it as written. In BTD6, **camo /
> fortified / regrow are universal *modifiers*** applied to *any* bloon, not
> intrinsic per-type properties. In `bloons.json` they appear only on the three
> `category:"modifier"` marker pseudo-entries (`Camo property` / `Fortified
> property` / `Regrow property`) plus a couple of innate cases (DDT is innately
> camo+black+lead; the Lead Bloon is lead). A roster "which bloons are camo" served
> from `properties[]` would return just `[DDT, Camo-property-marker]` — itself a
> **BUG-0009-class wrong assembly** (it implies only DDT can be camo, when every
> bloon can). The existing `deterministic_bloon_roster_reply` already *excludes*
> `category:"modifier"` for exactly this reason. **Reframe options for a future
> fire:** (a) drop this slice; or (b) reframe to the *intrinsic mechanical*
> properties that genuinely are per-type (e.g. `knockback-immune`,
> `stuns-attackers`, `damage-capped` on specific special/MOAB bloons), which IS a
> clean roster but is rarely asked in those words; or (c) build a *modifier
> explainer* ("what does camo/fortified/regrow do") off the three marker entries'
> `description`, which is the genuinely useful answer the property data supports.
> Until reframed, **skip slot 4** and take the next clean `TODO`.

- **Question shape:** "which bloons are camo?", "list all fortified bloons", "what
  bloons have the regrow property?" — roster bloons by an entry in `properties[]`.
- **Data:** `disbot/data/btd6/bloons.json` → `properties[]` (camo/lead/fortified/
  regrow/…). Sibling to the shipped `deterministic_bloon_roster_reply` (category +
  `immune_to`), which it **must defer to** on the MOAB-class / immunity cues so the two
  don't both fire — extend the exclusivity corpus to pin the split.
- **Build:** `btd6_data_service.bloons_by_property(prop)` +
  `deterministic_bloon_property_roster_reply`. Register **near** the existing bloon
  roster, ordered so the more-specific cue wins.
- **Tests:** `tests/unit/services/test_btd6_bloon_property_roster.py` + corpus phrase
  (+ a should-defer phrase proving it doesn't shadow the immunity/MOAB roster).

### Slot 5 — Hero ability roster (§7.6) · `ready`

- **Question shape:** "what abilities does Quincy have?", "which heroes have an ability
  at level 3?", "list Adora's abilities" — roster a hero's `abilities[]` (level + name
  + summary), or heroes that have an ability at a given level.
- **Data:** `disbot/data/btd6/heroes.json` → `abilities[{level, name, summary}]`
  (present per hero).
- **Build:** `btd6_data_service.hero_abilities(name)` (and/or `heroes_with_ability_at_level`)
  + `deterministic_hero_ability_roster_reply`. Register in `_BTD6_LIST_BUILDERS`.
- **Tests:** `tests/unit/services/test_btd6_hero_ability_roster.py` + corpus phrase.
- **Care:** must defer to slot-1 hero **cost** comparison on cost cues (different shape,
  same entity) — pin both in the exclusivity corpus.

---

### Buffer slices (data-complete; promote if a fire is fast or a slot is pre-empted)

- **Geraldo items-by-unlock-level roster** (§7.6) — "what does Geraldo start with?",
  "which items unlock at level 5?". Data: `geraldo_items.json` → `unlock_level`. Sibling
  to the shipped `deterministic_geraldo_per_level_reply` — **must defer to it** on the
  per-level grouping cue (this is the *which-items-at-a-level* / starting-kit angle).
- **Monkey-Knowledge category roster** (§7.6) — "what Support monkey knowledges are
  there?". Data: `monkey_knowledge.json` → `category`. **Must defer** to the shipped
  `deterministic_mk_reference_reply` on a *tower* cue (that builder owns "MK related to
  <tower>") so it isn't shadowed.

### Explicitly **not** in this night queue (gated — leave for daytime/owner)

- BUG-0009 slice 3 (**newest-towers ordering**) — `data`-gated (`towers.json` has no
  release-order field; needs the ADR-006 / `!btd6ops seed-data` provenance lane first).
- **Relic *cost* comparison** — relic `cost` is **not** in `ct_relics.json` → data-gated;
  do the *category roster* (slot 3) instead.
- P1-1 absence-guard **Layer B**, the live-quality eval battery — `creds`/design-for-review.
- Anything needing prod creds, a Railway env var, an owner product decision, or a
  self-invented feature (phase gate). A scheduled fire never originates a feature.

## Definition of done (per slice, every fire)

`python3.10 scripts/check_quality.py --full` green · `check_architecture --mode strict`
0 errors · the new builder added to `_BTD6_LIST_BUILDERS` **and** the exclusivity corpus
(exactly-one-fires invariant passes) · a per-slice `Recently shipped` ledger line ·
this queue's row ticked `✅ #NNN` and ▶ Next action re-pointed at the next `TODO`.

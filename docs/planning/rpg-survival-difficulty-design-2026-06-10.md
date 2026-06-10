# RPG survival & difficulty design — structured plan (mining/character platform)

> **Status:** `plan` — structured from the owner's vision capture; **not
> implementation approval** (promotion gates below).
> **Horizon:** Later (games lane) — sequenced into the games queue behind the
> already-named next slices (structures §7.5, skill tree §7.4); phases may
> interleave with them where noted.
> **Source:** [`../ideas/superbot-vision-2026-06-10.md`](../ideas/superbot-vision-2026-06-10.md)
> V-05/V-06/V-07/V-08 + AG-05/06/07/11, picked as a next planning target by the
> owner (router **Q-0078**, 2026-06-10). The difficulty-switching rule (one-way
> ascent) was decided in the same round.
> **Boundary:** ADR-002 unaffected (all state is durable DB rows, no game
> sessions); the no-pay-to-win line holds (difficulty bonuses are earned by
> accepting risk, never bought).

## Planning contract

- Source code, merged PRs, binding contracts, the games folio, and
  `docs/current-state.md` outrank this draft.
- Every mining write stays behind `services/mining_workflow.py` (the #664
  fence + AST ratchet); pure domain logic goes in `utils/mining/`; no new
  background tasks — all clocks are **lazy** (computed from timestamps on
  read, the pets-plan precedent).
- **Easy mode ≡ today's game, byte-identical** — the whole layer ships as a
  pure addition behind the player's difficulty choice (the compatibility bar
  this repo uses everywhere, e.g. AI orchestration defaults).

## Context and objective

Brainstorm §6 explicitly deferred survival ("None in v1 — health/stamina
later") and even sketched reserved columns for it. The owner's 2026-06-10
vision statement is that deferred layer's design: **difficulty as an opt-in
journey contract** — Easy keeps the game exactly as it is today; Medium adds
health + hunger + energy; Hard turns the same systems into an intense,
high-reward experience. PvP is explicitly outside difficulty (equal-start
arenas, V-08).

**Q-0081 (2026-06-10) pins the core shape: solo core + co-op moments.** Each
player owns their world-state; multiplayer (duels, expeditions, party quest
sessions, server-wide events) is an opt-in *overlay* — so every system below
is designed single-player-first, and the future quest-engine plan inherits
single-party as its first constraint.

## Design

### D0 — Balance philosophy (Q-0087, 2026-06-10 — binding on every number below)

The owner's stated target (verbatim core in router §37): **a few minutes a day
must earn real progress**, grinders get **real rewards for long play and
goals**, and grinder goals must **never feel mandatory** for levels or core
capabilities. Operationally: every knob in the D1 contract table is tuned to a
**dual-track curve** — the casual track carries *capability* progression
(levels, unlocks, story); the grind track carries *prestige and surplus*
(records, cosmetics-class rewards, leaderboard standing, faster-but-never-
exclusive paths). A number that gates a core capability behind grind-hours
violates D0 and fails review. The **P0 simulation harness** (Phasing, below)
is the methodology that proves a tuning satisfies this before P1 ships.

### D1 — The difficulty contract (V-05 + Q-0078)

One new per-player field: `difficulty` (`easy` default · `medium` · `hard`).
**One-way ascent (Q-0078):** upgrade anytime via the World panel, never
downgrade. Leaderboard/depth-record rows carry the difficulty at earn time
(⭐/⭐⭐/⭐⭐⭐ flag — additive column, like the #665 depth records).

| Axis | Easy | Medium | Hard |
|---|---|---|---|
| Health | none (can't die/get hurt) | yes | yes, lower max |
| Hunger | none | yes, slow | yes, faster decay |
| Energy | **none (unlimited — today's behavior)** | cap 10, regen ~1/6 min (≈10/hr) | cap 5, regen ~1/12 min; **level-up refills to cap** |
| Encounters | rare, weak | normal | more + stronger |
| Loot | base | base | **+X% base loot** (tunable) |
| Skill points/level | 1 | 1 | 1, **chance of 2** (base ~10%, +small/level — tunable) |
| Death | impossible | mild: wake at camp, hunger reset cost | **rescue mission** (D5) |

All numbers live in one tunable table-in-code (the `_GEAR` precedent), not
scattered constants. Exact values are an **owner confirm at build time**
(promotion gate G2) — the table shape is the design, the numbers are tuning.

### D2 — Energy (V-06 + AG-05)

Regen-over-time toward a cap, **not** hourly buckets: no top-of-hour cliff,
and one glanceable line on the World panel (`⚡ 7/10 · next in 4 m`). Stored
as `(energy_at, energy_value)`; current energy is derived lazily on read.
Every gathering action (mine/chop/fish/explore) costs 1; refusal copy names
the regen time. Level-up refill on Hard (V-05) is a one-line rule at the
game-XP award seam (#665). Skills (§7.4 branch content) and structures
(Home/campfire, §7.5) later raise cap or regen — declared here so those
slices reserve the hook, built there.

### D3 — Health & hunger + the food loop (V-05/V-07 + AG-06)

Hunger decays lazily from `last_ate_at` (rate per difficulty); low hunger
first dents action effectiveness, then (Hard) health. Health damages from
encounters (D4) and starvation; regenerates by eating + resting at the fire.
**Food closes the loop:** fishing/foraging yield raw food → **cook at the
campfire** → cooked food restores hunger/energy and stacks in the existing
typed inventory as a new item group (non-sellable at first, like combat
gear). Food is the gathering activities' recurring consumable sink, exactly
parallel to gear durability (§7.5) — one economy, two sinks. Cooking awards
game-XP and is future Crafting-branch content.

### D4 — Activities & encounters (V-07 + AG-07)

The World panel grows to the vision's surface: ⛏️ Mine · 🎣 Fish · 🧭 Explore ·
🌲 Chop · 🔥 Fire/Eat (fishing gated to water-bearing biomes; the existing
`!chop` joins the energy/wear rules). Encounters are **deterministic roll
tables keyed (biome × difficulty)** owned by pure domain code — Hard raises
weight and strength; outcomes touch health/loot through the workflow service.
A **pet modifier hook** is reserved in the table inputs (scout = prevention
roll, gold-sense = treasure weight) per the pets-plan Q-0078 amendment — the
hook ships here, pets wire into it in their own plan. AI narration of
encounter/quest outcomes stays in the AI lane (Q-0040) — these tables are the
deterministic substrate it will narrate.

### D5 — Hard-mode death = a rescue mission (AG-11)

Death never deletes the character: carried (non-equipped) loot drops to a
death-site row; the player (or, later, another player or their pet) mounts a
recovery run to reclaim it; unclaimed sites expire to nothing after N days.
Death becomes content and a future social hook, not rage-quit fuel.

### D6 — PvP isolation (V-08)

Difficulty never touches duels: arenas stay equal-start + crafted-gear edge
(#608) with durability wear (Q-0054). The new piece: **game-XP for both
fighters** through the #665 award path (winner substantially more) — small
enough to ship as a quick-win ahead of the rest of this plan.

## Persistence & architecture fit

- Additive migration on `mining_player_state` (the §6.4 reserved-columns
  intent): `difficulty`, `energy_value`/`energy_at`, `health`,
  `last_ate_at` (+ a `death_sites` table at P5 only). Direct-lane game state
  per the shipped pattern; **all writes via `mining_workflow`** (one
  transaction per action, the #664 invariant).
- Pure rules (`utils/mining/survival.py`: regen math, hunger decay, contract
  table, encounter tables) — stdlib-only, fully unit-testable with fake
  clocks.
- Leaderboard difficulty flag: additive column consumed by the existing
  boards; no provider rewrite.
- No schedulers, no caches beyond existing read paths.

## Phasing (each ≈ one bounded PR, promoted individually)

**P0 — balance simulation harness (added 2026-06-10, Q-0087 — owner approved
simulation as the balance methodology).** Before P1: a pure-python model of
the D1 contract table + activity expected values (no Discord, no DB — repo
code imports the same constants the game will use). It simulates player-days
under behavior profiles (casual ≈ minutes/day · regular · grinder ≈ hours/day)
across difficulties and outputs three curves: **casual progress/day** (must
stay meaningful at every level), **grinder surplus per extra hour** (real but
diminishing), and the **mandatory-feel metric** — the *core-capability* gap
between a pure-casual and a grinder at the same calendar week (must stay
inside a pinned band; prestige/surplus gap may grow, capability gap may not —
D0). The bands ship as **tests**, so every future balance change re-proves
the philosophy in CI. G2's structured-choices round presents simulation
outputs, not guesses.

1. **P1 — Difficulty choice + energy.** Contract table, World-panel picker
   (one-way ascent enforced at the mutation seam), energy on Medium/Hard,
   level-up refill, board flags. *Easy-mode byte-identical pin test is the
   headline test.*
2. **P2 — Health/hunger + food consumption.** Lazy decay, eat/rest actions,
   starvation rules; food item group (seeded via existing loot for now).
3. **P3 — Fishing + campfire/cooking.** The two new activities, raw→cooked
   recipes, cooking XP; World panel reaches the vision's full surface.
4. **P4 — Encounters v1.** Biome × difficulty tables + the pet-modifier and
   AI-narration hooks; Hard loot/skill-point bonuses activate here (they need
   risk to be earnable).
5. **P5 — Death & rescue (Hard).** Death sites + recovery runs + expiry.

(D6's XP-both-sides is a standalone quick-win, independent of P1–P5.)

## Promotion gates

- **G1 — sequencing:** the games lane's named next slices (§7.5 structures,
  §7.4 skill tree) keep their place; this plan enters the queue after them or
  interleaves only with an explicit owner pick.
- **G2 — owner confirms the numbers** (T-2): Medium's energy existence +
  cap/regen, Hard's bonuses — at P1 build time, as a structured-choices round
  over the contract table **backed by P0 simulation outputs (Q-0087)**.
- **G3 — `docs/ideas/README.md` gates** (ownership ✓ mining workflow · reuse ✓
  extends shipped state/services · risk: balance only · mechanics listed
  here).

## Risks

- **Annoying-throttle risk (T-2):** mitigated by Easy = no limits, generous
  Medium defaults, visible regen timer, and G2.
- **Balance creep:** all knobs in one table + simulation-style tests pinning
  Hard's expected-value edge within a band.
- **Scope creep:** fishing/cooking are P3, not P1; quests/AI/pets integrate
  via reserved hooks, never inline here.

## Open (non-blocking, for the build sessions)

- **Fishing may be promoted from P3 activity to ecosystem #2** (V-13/Q-0090 —
  the 2026-06-10 teardown's verdict, owner ratification pending): P3's design
  should keep its seams ecosystem-ready (own loot ladder, local-currency hook,
  collection-log hook) so promotion extends rather than rewrites it.
- P3's campfire has no named fuel source — the ancestor bot (minebot, 2025)
  had a `chop` woodcutting command; wood-as-fuel is the natural echo (and a
  third gathering verb if fishing becomes ecosystem #2).
- Whether Medium death (P2) costs a small coin/food penalty or only time.
- Fishing loot table depth (own ladder vs. reskinned ore weights at v1).
- Whether cooked food may later be sellable (market interaction — economy
  review).

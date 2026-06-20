# Creature game — v1 design + playability sim (2026-06-20)

> **Status:** `plan` — design + a runnable balance simulator. **Not implementation approval.**
> Source, binding contracts, and owner decisions win. **Subsystem:** games.
>
> **Provenance:** owner request (2026-06-20): *"use a simulator to see how playable it is"*,
> *"PvP battles with the Pokémon would be great"*, and *"how is the copyright with Pokémon names —
> can we use them or do we need to create our own?"* This doc answers the copyright question, fixes
> a v1 ruleset, and ships a Monte-Carlo **playability simulator**
> (`tools/game_sim/creature_battle_sim.py`) so the loop is validated *before* it touches
> `disbot/`. Builds on the [feature-mapping plan](poketwo-musicbot-feature-mapping-plan-2026-06-20.md)
> (Lane A Wild Encounters is the catch engine this feeds) and the
> [explore-hub spine](explore-hub-federated-world-plan-2026-06-19.md).

## 1. Copyright — use our own creatures (recommended), not Pokémon

**The question:** can we use real Pokémon names/creatures, or make our own?

**The facts:**
- **Game *mechanics* are not copyrightable** — catching, elemental types, turn-based 3v3 battles,
  stats, rarity, shiny variants. We can build a monster-catching battler freely; that's idea/system,
  not expression.
- **Pokémon *names, designs, and the dex are* protected** — copyright + trademark owned by
  Nintendo / The Pokémon Company / Game Freak. Reproducing real names ("Charizard"), sprites, or
  the National Dex + its stat data is infringement exposure. Nintendo is famously aggressive
  (fan-game C&Ds, takedowns).
- **Pokétwo uses real Pokémon data and lives in a legal grey zone** — it survives by being
  hobby-scale and under the radar. That is the *same* "fly under the radar until enforcement hits"
  posture that took down the music bots (the report's own Rythm/Hydra history). For a bot we want to
  **publicly launch** (the bot-site ambition), inheriting that risk is the wrong trade.

**Why Pokétwo "can" use real names — survivorship, not permission (owner asked directly).** It has
**no license** and is straightforwardly infringing. It survives on *enforcement economics*, not a
right: Nintendo enforces **selectively** (suing every fan project is costly and bad PR), and
prioritizes targets that distribute the actual games/ROMs or ripped assets, make real money off the
IP, compete with a Nintendo product, or get big press. A niche Discord bot trafficking in *data* +
community art has dodged all four — so far. That is not safety; it is being **too small to bother
with**, and it can be struck at any time (AM2R, Pokémon Uranium, and the music bots all were). **The
load-bearing principle:** what makes Pokétwo possible — staying small and unpromoted — is the
*opposite* of what we want (a bot we **publicly launch and market** on the bot-site). **Growth /
visibility is the enforcement trigger; "publish-safe" means a design that does not depend on staying
invisible.** This same principle governs the parallel music-legal decision
([voice/music decision pack](voice-music-architecture-review-2026-06-20.md) §1) — there it forbids
YouTube-ripping; here it forbids real Pokémon names.

**Decision (recommended, routed as Q-0187):** **build an original creature roster** — our own
names, types, and (later) art. This is the proven path of Temtem / Cassette Beasts / Coromon /
Palworld: the *loop* people love, none of the IP risk, and it's **publishable**. It also fits our
world — we already have original fauna/flora (fish, ore); creatures are the same world's wildlife.
The v1 roster below is original (Cindling, Magmaul, Rippling, …).

## 2. v1 ruleset (what the sim models)

- **Elements (6, original) + Normal:** Ember · Tide · Bramble · Spark · Stone · Gust, plus a neutral
  **Normal** damage type. Symmetric type chart — each element is **strong vs the next two**, **weak vs
  the previous two**, neutral vs its opposite (`1.5×` / `0.67×` / `1.0×`); **Normal is always `1.0×`**.
  Symmetric by construction so no element is inherently best. (Full move/type/team spec in **§2b**.)
- **Creatures (roster size — see §2a):** **36** in the data-driven launch catalog
  (`tools/game_sim/creatures.json`, 6 per element); the sim loads them. Each is spread across
  **rarity** (Common→Epic, bigger stat budget) and **archetype** (attacker / tank / balanced /
  speedster). Stats: HP / ATK / DEF / SPD.
- **Catch:** wild encounters (Lane A) spawn a creature; catch chance = rarity base × a small
  player-level bonus. Rarer = harder. Caught creatures join your collection (reuses the
  fishing-style catch log + `game_xp`).
- **Battle (PvP, 6v6, turn-based — §2b):** teams are **6 creatures, the standard one of each
  element**; lead fights until it faints, then the next comes in; faster SPD acts first; each turn a
  creature picks **one of its 4 moves**; damage = `(ATK/DEF) × move power × type-mult × jitter`.
- **★ PvP level rule (the key design finding — see §3):** **PvP normalizes to a flat level.** Raw
  levels make a 1v1 deterministic (a +2 level gap wins ~100%), which would make ranked PvP a
  grind/whale-fest — exactly the **pay-to-win** outcome Q-0039 forbids. Normalizing to a flat level
  (competitive-Pokémon style) makes **types + team-building + ordering** decide, so PvP rewards
  *skill*, not *time spent*. (Raw levels still matter for PvE/collection prestige.)

## 2a. Roster size — how many creatures (owner asked: "how many should we use?")

**For scale: Pokétwo uses ~1,000+** real Pokémon (the full National Dex, currently 1,025 species)
**plus hundreds of alternate forms** (regional / mega / Gigantamax / event) and a **shiny variant of
every one** — a multi-hundred-hour completion grind that is itself a big part of the hook. We **can't
and shouldn't** mirror that: every original creature is a design + balance + (eventually) art cost we
own. Original monster-catchers ship far smaller even *with* art teams — Temtem ~160, Coromon ~120,
Cassette Beasts ~140, Palworld ~150.

**The v1 model (recommended, routed as Q-0187d) — tier the roster, make it data-driven:**

| Stage | Count | Purpose |
|---|---|---|
| **Sim / playable core** | **12** (current) | Prove the loop + balance — done, verdict PLAYABLE |
| **v1 launch roster** | **~30–40** (5–7 per element, spread across rarities) | Enough for a satisfying "dex" + real team variety, without art-blocking |
| **Growth ("waves" / seasons)** | +10–20 each | Expand like real catchers add generations — keeps the collection alive |

Twelve is right for *balance validation* but too thin for the *collection feel* that makes catching
fun (a dex you fill in one sitting isn't a hook). Two choices make ~30–40 cheap **and** safe:

1. **Text/emoji-first art (§5c)** — a bigger roster costs ~nothing when a creature is an emoji + name
   + stat block; sprites come later, like the gear paper-doll did.
2. **Creature-as-data** — the engine loads creatures from a **JSON catalog** (the `towers.json` /
   fish-roster pattern), so *adding* a creature is a data row, not code. This is what makes
   "ship 12 → grow to ~40 → seasons" a non-event architecturally, and it lets the **same
   `creature_battle_sim.py`** validate the *whole* launch roster before it ships (the
   balance-before-build gate).

**★ BUILT (2026-06-20):** the v1 launch catalog is real — **`tools/game_sim/creatures.json`, 36
original creatures** (6 per element; 12 Common / 12 Uncommon / 6 Rare / 6 Epic), and the sim now
**loads the roster from it** (stats derived: `budget = RARITY_BUDGET[rarity]` split by archetype
weights — no stored stats to drift). Re-running the sim on the full 36 still reports **PLAYABLE (no
flags)**, with type balance even *tighter* than the 12-roster (per-element 49.6–50.6%, **spread
1.0pt** — the uniform Common/balanced per-element "starter" makes it apples-to-apples) and catch
grind ~7 at L1. So **~30–40 is proven balanceable, not just asserted** (Q-0187d). *Flavor (names) is
owner-refinable — like the gear paper-doll, the system + a working default ship; the owner swaps the
creative skin. The catalog graduates to `disbot/data/` at the gated runtime build (Q-0186).*

## 2b. Combat model — types, moves, teams (owner design, 2026-06-20; sim-validated)

The owner specified the combat shape; the sim models and validates it. **All numbers here are
tunable defaults the sim landed on — the *structure* is the design, the values are knobs.**

### Damage types (6 elements + Normal)
- The **6 elements** carry the symmetric type chart (each strong vs the next two, weak vs the
  previous two, neutral vs its opposite: `1.5× / 0.67× / 1.0×`).
- **Normal** is a 7th *damage* type that is **always `1.0×`** — no creature *is* Normal-type, but
  every creature has a reliable Normal-damage move (below). It is the safe fallback when your
  element move would be resisted.

### Teams — 6 creatures, the standard "one of each element"
Teams are **6** (the familiar "6-mon team"). The **standard/recommended composition is one creature
of each element**, which also makes PvP type-symmetric (both sides hold all six types), so the game
comes down to **move choice, lead order, and setup** rather than who drew the better type — a clean,
skill-first competitive shape. (Players may skew duplicates; the sim models the standard team.)

### Moves — 4 per creature (2 damage + 2 status)
Every creature has **exactly four moves**, per the owner's spec:

| # | Move (default name) | Kind | Type | Effect |
|---|---|---|---|---|
| 1 | **Strike** | Damage | **Normal** | reliable hit, always `1.0×`, base power **9** |
| 2 | **signature** (per element) | Damage | the creature's **element** | type chart applies, base power **12** |
| 3 | **Bulwark** | Status (defensive) | — | **+DEF** to self (no damage) |
| 4 | **Onslaught** | Status (offensive) | — | **+ATK** to self (no damage) |

Per-element signature names (original, no Pokémon move IP): Ember **Cinderlash** · Tide **Tidal
Crash** · Bramble **Thorn Volley** · Spark **Voltstrike** · Stone **Boulder Smash** · Gust
**Galeforce**. *(Names are owner-refinable flavor; per-creature unique signatures can be a later
pass — the sim only needs type + power.)*

**Status-move model:** each use shifts the stat **+25%**, **capped at +50%** (two uses), so a turn
spent buffing is a real investment with diminishing returns — buff-spam can't run away. (The owner
named one **defensive** and one **offensive** status move; v1 models both as self-buffs — `+DEF` and
`+ATK`. *Open knob, §5:* the offensive one could instead **lower the enemy's DEF**, and the
defensive one could **heal** — same slot, different feel; easy to swap and re-validate.)

### The emergent skill — why 2 damage types matter
The signature move (power 12) out-damages Strike (power 9) **except vs a resistant target**
(`12 × 0.67 ≈ 8 < 9`). So a good player **uses the element move on neutral/weak matchups and falls
back to Normal vs resistances** — a real per-turn decision — *plus* decides **when to spend a turn
on setup** (Onslaught) vs pressing damage. Those are the v1 skill levers the sim measures (§3).

## 3. Simulator + headline findings

`tools/game_sim/creature_battle_sim.py` — stdlib-only, deterministic (`--seed`), Monte-Carlo.
Run: `python3.10 tools/game_sim/creature_battle_sim.py` (guarded by
`tests/unit/tools/test_creature_battle_sim.py`). Current verdict at the v1 numbers:
**PLAYABLE (no flags).** What it checks and found (seed 42, 2000 trials):

| Check | Result | Read |
|---|---|---|
| **Type balance** — avg 1v1 win-rate per element (best-move play) | 50.0–50.6%, **spread 0.6 pts** | PASS — no dominant element; smart play (Normal vs resistances) keeps it razor-even. |
| **Raw-level dominance** (informational) | +0 ≈ 50% · **+2 ≈ 100%** | The finding that **drives the level-normalization rule** — raw levels decide 1v1s. |
| **Normalized PvP fairness** — team-A win-rate, equal-level standard 6v6 | ~51% | PASS — engine is unbiased; once level is removed, roster/type/skill/moves decide. |
| **Skill impact** — setup + type-aware lead vs a beginner (element-spam) | **~71%** (seeds 42/7/123) | PASS — good play is clearly rewarded (target 52–80%), not absolute. |
| **Status-move value** — opening +ATK setup vs damage-only | **~55%** | PASS — the non-damage moves earn their slot (>50%) without being degenerate (<72%). |
| **Catch grind** — encounters to a 3-mon starter / full one-of-each-element team | ~7 / ~41 at L1 | PASS — starter team in one sitting; the full competitive team is a multi-session goal. |

**The simulator paid for itself twice.** The *first* (pre-move) version surfaced that battles were
decided by who strikes first and produced the **level-normalization rule**. Extending it to the
**4-move / 6v6 model** then caught a real tuning trap: against a *random-move* opponent the skilled
side won **93%** — too absolute — because random play wastes turns buffing at bad times. Swapping the
baseline to a realistic **beginner** (element-spam) landed skill impact at a fun **~71%**, and the
status-move check confirmed setup is **worth a turn (~55%) but not degenerate**. That is exactly the
"see how playable it is *before* building" the owner asked for — now validated on the full combat
model, not just stats.

## 4. How it docks into the bot (when greenlit — not built here)

- **Catch** = Lane A Wild Encounters (the activity-spawn engine) drops creatures instead of / in
  addition to items; reuses `economy_service` / `game_xp` / a fishing-style catch log.
- **Collection** = Lane B filters over the creature log; a "dex" of seen vs. caught.
- **Battle** = a new `cogs/creature_battle/` + `services/creature_battle_engine.py` (pure, the sim's
  math graduates here) + `views/creature_battle/` panels; PvP challenges mirror the existing
  `rps`/`deathmatch` PvP-challenge view pattern. Level-normalized.
- **World** = registers a `WorldEntry` in the Explore hub; creature standings on the world card.
- **Anti-P2W** = the normalization rule + Q-0039 (no buyable power); shinies are cosmetic (Lane D).

## 5. Open decisions (routed — owner is the designer)

Routed to **Q-0187**: (a) confirm **original creatures** (recommended) vs. real Pokémon names;
(b) confirm **PvP = level-normalized** (recommended) vs. raw-level PvP; (c) creature *art* approach
(emoji/text v1 → original sprite pack later, like the gear paper-doll); **(d) roster size — confirm
the tiered model (§2a): sim-core 12 → v1 launch ~30–40 → growth in waves, with a data-driven JSON
catalog and text-first art** (recommended). Build sequencing for the catch half stays under
**Q-0186** (Lane A first).

**Combat model (§2b) is owner-specified design** (6 types + Normal · teams of 6, one of each
element · 4 moves = 2 damage [Normal + signature] + 2 status [defensive/offensive]) — built and
**sim-validated PLAYABLE**, so it isn't an open question. The **one open knob** worth the owner's
eye: the *exact* status-move effects. v1 models both as **self-buffs** (`+DEF` defensive, `+ATK`
offensive); the natural alternatives are **defensive = heal** and/or **offensive = lower enemy DEF**
(same slots, different feel). All are a one-line change + a sim re-run — say which feel you want and
the sim confirms it stays balanced.

→ relates [feature-mapping plan](poketwo-musicbot-feature-mapping-plan-2026-06-20.md) ·
[explore-hub spine](explore-hub-federated-world-plan-2026-06-19.md) ·
[wild-encounters idea](../ideas/wild-encounters-activity-spawning-2026-06-20.md) ·
`tools/game_sim/creature_battle_sim.py` · Q-0187 · Q-0186 · Q-0039 (no P2W) · Q-0182 (world model).

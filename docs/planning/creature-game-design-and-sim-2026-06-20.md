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

- **Elements (6, original):** Ember · Tide · Bramble · Spark · Stone · Gust. Symmetric type chart —
  each is **strong vs the next two**, **weak vs the previous two**, neutral vs its opposite. (`1.5×`
  / `0.67×` / `1.0×`.) Symmetric by construction so no element is inherently best.
- **Creatures (roster size — see §2a):** **12** in the sim core (2 per element) for balance
  validation; the **v1 launch target is ~30–40** original creatures for collection depth. Each is
  spread across **rarity** (Common→Epic, bigger stat budget) and **archetype**
  (attacker / tank / balanced / speedster). Stats: HP / ATK / DEF / SPD.
- **Catch:** wild encounters (Lane A) spawn a creature; catch chance = rarity base × a small
  player-level bonus. Rarer = harder. Caught creatures join your collection (reuses the
  fishing-style catch log + `game_xp`).
- **Battle (PvP, 3v3, turn-based):** lead creature fights until it faints, then the next comes in;
  faster SPD strikes first; damage = `(ATK/DEF) × move power × type-mult × jitter`.
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
   balance-before-build gate). Building that catalog + sim-validating ~30–40 is the natural next
   design step before any catch-engine build.

## 3. Simulator + headline findings

`tools/game_sim/creature_battle_sim.py` — stdlib-only, deterministic (`--seed`), Monte-Carlo.
Run: `python3.10 tools/game_sim/creature_battle_sim.py` (guarded by
`tests/unit/tools/test_creature_battle_sim.py`). Current verdict at the v1 numbers:
**PLAYABLE (no flags).** What it checks and found (seed 42, 2000 trials):

| Check | Result | Read |
|---|---|---|
| **Type balance** — avg 1v1 win-rate per element | 40–60%, spread 20 pts | PASS — no dominant element; a roster-stat tweak could tighten the 40/60 tails. |
| **Raw-level dominance** (informational) | +0 ≈ 49% · **+2 ≈ 100%** | The finding that **drives the level-normalization rule** — raw levels decide 1v1s. |
| **Normalized PvP fairness** — team-A win-rate, equal levels | ~51% | PASS — engine is unbiased; once level is removed, roster/type/skill decide. |
| **Skill impact** — type-aware ordering vs random | ~58% | PASS — counterplay is rewarded (>50%) but not absolute (<75%). |
| **Catch grind** — encounters to a team of 3 | ~7 at L1 | PASS — a fresh player gets a starter team in one sitting, not a slog. |

**The simulator paid for itself immediately:** the first run flagged that battles were decided by
who strikes first (even a same-level mirror won 98%). That surfaced two fixes — a fair speed-tie
coin-flip and longer battles (lower damage-to-HP) — and, more importantly, the **level-normalization
design rule** above. This is exactly the "see how playable it is before building" the owner asked
for.

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

→ relates [feature-mapping plan](poketwo-musicbot-feature-mapping-plan-2026-06-20.md) ·
[explore-hub spine](explore-hub-federated-world-plan-2026-06-19.md) ·
[wild-encounters idea](../ideas/wild-encounters-activity-spawning-2026-06-20.md) ·
`tools/game_sim/creature_battle_sim.py` · Q-0187 · Q-0186 · Q-0039 (no P2W) · Q-0182 (world model).

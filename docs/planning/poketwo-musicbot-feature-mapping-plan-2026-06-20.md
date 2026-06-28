# Pokétwo + MusicBot research report → feature-mapping plan (2026-06-20)

> **✅ OWNER DECISION (Q-0186, 2026-06-28, question panel):** build order = **Lane A (Wild Encounters)
> first** (then B Collection / C Quests / D Shiny). Spawn defaults + guardrails ride this doc's
> documented defaults until Lane A's runtime session refines them. Canonical: router Q-0186.

> **Status:** `plan` — routing/mapping plan. **Not implementation approval.** Source code,
> the binding contracts, owner decisions (router `Q-####`), and `docs/current-state.md` win
> over this doc. **Subsystem:** games, ai, media.
>
> **Provenance:** the owner uploaded a research report comparing **Pokétwo** (the Pokémon
> catching Discord bot) and **JMusicBot/Rythm/Jockie** (music bots) and asked to *"implement
> as much of these features in a proper way."* The owner then steered this session
> (in-session answers, 2026-06-20): **plan only, build nothing yet**, and for the music half
> **architecture-review pack only** (respect the Q-0041 voice gate). This doc is that plan.

> **▶ Live demand signal (2026-06-20):** a real user in the owner's community said he still runs
> **multiple bots** specifically *"like poketwo and music bot"* because SuperBot lacks those
> features. The owner's directive: *"we should make sure we have a similar/better version of the
> Pokémon system."* This **raises the priority** of the Pokétwo half (especially Lane A + the
> catching/collection lanes below) from "nice extension" to "close a real why-I-need-another-bot
> gap" — the goal is **feature-parity-or-better with Pokétwo's loop**, built on our own world
> spine, not a literal Pokémon clone. (Music stays Q-0041-gated; the [arch-review
> pack](voice-music-architecture-review-2026-06-20.md) is the path to closing that gap too.)
>
> **▶ Creature game advanced (2026-06-20):** the owner greenlit **PvP battles** and asked about
> Pokémon-name copyright. Decision: **original creatures** (mechanics are free; the names/dex are
> not — same publish-safe stance as the music legal lane). A v1 ruleset + a **runnable playability
> simulator** now exist — see [`creature-game-design-and-sim-2026-06-20.md`](creature-game-design-and-sim-2026-06-20.md)
> (`tools/game_sim/creature_battle_sim.py`, verdict **PLAYABLE**; it surfaced the key rule that
> **PvP must be level-normalized** to stay skill-based, not pay-to-win). Decisions routed to Q-0187.

## 0. What Pokétwo actually does (one-screen reference)

So the owner-designer has the loop in front of him (he noted he's *"not sure what poketwo can
exactly do"*). Pokétwo recreates Pokémon in chat:

1. **Activity spawns** — wild Pokémon appear in a channel after ~N user messages (engagement
   loop). Players type `catch <name>` to claim; `hint` reveals letters.
2. **Collection** — every catch goes to a personal inventory; rich **filters/sort** (level, IV,
   rarity, region, shiny, favourite, duplicates) manage large collections; a Pokédex tracks
   seen/caught.
3. **Global marketplace + trading** — list/search/buy Pokémon with in-game currency; plus direct
   player-to-player trades.
4. **Battling** — turn-based 3v3 using real Pokémon moves.
5. **Shiny hunting & rarity** — tiny base shiny chance, boosted by streak "hunts" or a shop charm.
6. **Two currencies** — earned PokéCoins + premium (buyable) shards; shop sells boosts, evolution
   items, incense (forces spawns), etc.
7. **Quests, events, time/weather** — daily quests, seasonal events, time/weather-gated evolutions.

**Our parity map (verdicts in §2):** 1 → **Lane A Wild Encounters** (the missing engine) · 2 →
**Lane B** (extend fishing/inventory) + a "dex" of seen vs. caught · 3 → the **economy-marketplace
roadmap** (gated) · 4 → battles (owner-design, P2W-sensitive) · 5 → **Lane D** shiny/variant
(cosmetic, not buyable) · 6 → **single earned currency only** (Q-0039 rejects buyable advantage —
this is the deliberate "better, not P2W" divergence) · 7 → **Lane C** quests + (deferred)
time/weather under the Q-0182 world model.

## 1. The core reframe — most of this already has a lane

The report reads as "here are two successful bots, copy their features." The proper response in
*this* repo is **not** to clone Pokémon or bolt on a music player. Two facts from the research
change the shape of the work:

1. **Most Pokétwo mechanics already exist or are already planned here.** Catching → **fishing**
   and **mining** are shipped; **pets-companions** is planned. Trading → the
   **economy-marketplace roadmap** exists (gated on economy-health evidence). The "one world
   each game plugs into" → the **federated Explore hub** (`services/world_registry.py`, shipped
   #1156). So the job is mostly **extend + dock into existing seams**, governed by the repo's
   hard *"do not duplicate existing systems"* rule.
2. **Several report "improvements" are already owner-decided — some the *opposite* way.** The
   report pitches a **two-currency premium economy** (PokéCoins + buyable shards); the owner
   **rejected** purchasable advantage (**Q-0039**, cosmetic-only donations, no P2W). The report
   pitches **music**; the owner **wants it but gated it** behind a dedicated voice architecture
   review sequenced *after* alert integrations (**Q-0041**). Building either "as described"
   would violate a standing decision.

So this plan does three things: **(A)** map every report feature to its lane and verdict;
**(B)** spec the genuinely net-new, ungated, owner-aligned slices as PR-sized work; **(C)** route
the owner-decision forks instead of guessing them.

## 2. The mapping — every report feature → repo lane → verdict

Legend: **EXTEND** = grow an existing system · **BUILD** = net-new, ungated, owner-aligned ·
**GATED** = needs an owner decision / evidence first · **REJECTED** = conflicts with a standing
owner decision · **HAVE** = already shipped, nothing to do.

### Pokétwo half

| Report feature | Closest repo lane (verified) | Verdict |
|---|---|---|
| **Activity-based spawning** (chat messages accrue → a wild encounter appears) | **No analog anywhere.** Fishing/mining are manual command-only; there is no message-activity passive event in the repo. | **BUILD** — the signature net-new mechanic. See §3 Lane A. |
| **Catching a creature** | `fishing` (`!fish`, level-gated rolls, `fishing_catch_log`) + `mining`; `pets-companions` plan (eggs/hatch/care, no battles) | **EXTEND** — Lane A's claim routes a catch through these seams; do **not** build a parallel "Pokémon" game. |
| **Collection + robust filters** (region/level/IV/shiny/favourite/forms) | `fishing_catch_log` (per-species count + timestamps), `inventory_cog` (rarity/category, UI-only filters) | **EXTEND** — Lane B: real filter/sort/favourite layer over the existing logs. |
| **Hints / alternate names** | `utils/synonyms.py` (`find_command`), the AI's BTD6 name-resolution patterns | **EXTEND** (small) — folds into Lane A's encounter "guess the name" option if wanted. |
| **Global marketplace + trading** (listings, search, escrow, buy/sell) | **`economy-marketplace-rewards-roadmap-2026-06-08.md`** — designed, **gated** on economy-health evidence + anti-fraud/legality review; no trading code exists today. | **GATED** — do not build until the roadmap's gates clear. Lane A/B feed the *items* it would trade. |
| **Two currencies — PokéCoins + buyable shards** | `economy_service` is single-currency (coins); **Q-0039** rejects purchasable advantage. | **REJECTED** as "buyable premium currency." A *second earned* token (non-buyable) is a separate economy-balance decision, not this. |
| **Battling (3v3, moves)** | `deathmatch`/`rps`/`blackjack` PvP-challenge views exist; no creature-battle lane yet. | **DESIGNED (2026-06-20, owner-directed PvP)** — owner wants creature PvP; v1 ruleset + a **playability simulator** are in [`creature-game-design-and-sim`](creature-game-design-and-sim-2026-06-20.md) (verdict: PLAYABLE). Key rule: **PvP is level-normalized** (so it's skill, not grind/P2W — Q-0039). Build is its own runtime session; design choices routed to **Q-0187**. |
| **Shiny hunting / rarity / hunt streaks** | Loot rarity exists in mining/fishing; no "shiny variant" or streak mechanic. | **BUILD** (thin) — Lane D: a rare-variant flag riding on Lane A / fishing, anti-P2W (cosmetic prestige, not power). |
| **Quests / achievements / events** | Only **derived titles** (mining) exist; no quest log, achievement/badge store, or timed events. Captured in vision docs, intersects the open world-model questions (**Q-0182**). | **BUILD** (foundation) — Lane C, but it touches Q-0182; spec is foundation-only. |
| **Time & weather mechanics** | None. | **GATED/defer** — flavor layer best decided with the Q-0182 world model (biome/map fork). |
| **Modern UI (slash commands, buttons, embeds, dashboard)** | The repo is **already** button/HubView/panel-driven; a web dashboard + control API are shipped. | **HAVE** — the report's headline "improvement" is largely realized. |
| **Open-source / modular / public API** | Strict layered architecture, registries, EventBus; public bot-site in flight. | **HAVE** — keep docking new games into `world_registry`. |

### Music half (JMusicBot / Rythm / Jockie)

| Report feature | Repo reality | Verdict |
|---|---|---|
| **Music playback** (multi-source streaming, queue, DJ role, search, lyrics, playlists, control panel) | **Zero voice capability today.** Owner **wants** music but **Q-0041** sequences it behind a *dedicated voice architecture review*, itself behind YouTube→Twitch→Spotify alert integrations. | **GATED** — owner chose **architecture-review pack only** this session. See [`voice-music-architecture-review-2026-06-20.md`](voice-music-architecture-review-2026-06-20.md). Build no playback. |
| **DJ-role / role-based control / vote-skip** | `governance/` capability + `role` subsystem would supply this *if* music ships. | Maps cleanly **when** the gate lifts — captured in the arch-review pack. |
| **Legal/licensing posture** (the report's own DMCA/cease-and-desist warning) | The decisive constraint; Rythm/Hydra history is in the report. | The arch-review pack makes this the **first** decision, not an afterthought. |

## 3. The buildable lanes (specs only — nothing built this session)

Each lane is written so a future approved session can execute it cold. All four respect:
**route every mint/award through `economy_service` / `game_xp_service`; write through the
domain's audited `*_workflow`/`*_mutation` seam; dock UI into the world hub; stay anti-P2W
(free, earned by play — never buyable power).**

### Lane A — Wild Encounters (activity-based spawning) ★ highest-leverage net-new

The one Pokétwo mechanic with **no analog** and **no owner gate**, and the report's strongest
lesson ("spawns linked to activity encourage conversation"). It is also the engine the other
lanes feed.

- **New subsystem** `cogs/encounters_cog.py` (+ `cogs/encounters/`), `views/encounters/`,
  `services/encounter_service.py` (audited), `utils/db/encounters.py`, a migration for
  `encounter_spawn` / `encounter_claim` tables, and a `delete_for_guild` hook in
  `guild_lifecycle.py`. Use `scripts/new_subsystem.py` / the `/new-subsystem` skill.
- **Spawn loop:** a message listener accrues a per-channel activity counter (debounced, bot
  messages excluded — mirror the report's "~24 messages" but **config-driven**, off by default).
  At threshold, `encounter_service` spawns an encounter embed + **Claim** button in that channel
  (rate-limited; one live spawn per channel; respects the channel allow-list). **Anti-spam:**
  no auto-catch; cooldown per claimer; the threshold + enabled-per-channel are settings.
- **Claim → reward:** the first valid claimer (capability re-checked at callback time, Q-0080
  stranger-grade) gets a reward **routed through existing seams** — a fishing/mining item, coins
  via `economy_service`, and `game_xp` for a new `GAME_ENCOUNTERS`. No new currency.
- **Dock into the world hub:** register an Encounters `WorldEntry`; surface stats on the world
  card (`world_identity()`).
- **Tests:** spawn-threshold math (pure, in `utils/`), claim atomicity + double-claim guard,
  capability re-check, guild-teardown.
- **Owner forks (Q-0186):** default threshold + which reward pool; whether claiming is
  first-click vs. a "name the catch" guess (folds in the hint mechanic).
- **Why a real PR, not a one-liner:** new table + service + listener + view + world dock; size it
  as a small foundation PR (spawn+claim+reward) then a follow-up PR (filters/variety). Runtime
  code → small focused PRs (per CLAUDE.md), runtime-verified session.

### Lane B — Collection & filtering upgrade (EXTEND fishing + inventory)

The report's "robust filters" lesson, applied to what we already store.

- Add a real **filter/sort/favourite** layer over `fishing_catch_log` (and the unified
  `inventory` display): filter by rarity/level/owned-vs-missing/favourite; sort by count/recency;
  paginated `BaseView` (reuse `views/paginated_select.py` / `attach_windowed_select`).
- **Favourite** = one new boolean column on the catch log (audited via the fishing workflow); no
  new subsystem.
- Smallest, safest lane; good warm-up or parallel slice. Tests: filter predicates (pure),
  favourite write through the workflow.

### Lane C — Quest / achievement foundation (BUILD, but Q-0182-aware)

The report's quests/achievements/events. **Foundation only** — full design intersects the open
world-model questions (Q-0182), so this lane builds the *engine*, not a content catalogue.

- `services/quest_service.py` (audited) + `quest_progress` / `achievement_grant` tables + a
  read-only quest-log panel. A quest = `{key, predicate over existing events, reward}`; progress
  is driven by **existing EventBus events** (`game_xp.awarded`, `EVT_BALANCE_CHANGED`,
  encounter claims) — no new instrumentation, no polling.
- Achievements = milestone grants (generalizes mining's derived **titles**; reuse that prior
  art, don't fork it).
- **Defer**: timed/seasonal *events* and quest *content authoring* until Q-0182 fixes the world
  model (and per Q-0040, AI-chosen quests come from **bounded menus**, not free narration).

### Lane D — Shiny / rare-variant layer (BUILD, thin, anti-P2W)

The report's shiny hunting, reframed as **cosmetic prestige, never power**.

- A low-probability **variant flag** on a catch/encounter (e.g. `is_variant` + variant name),
  rolled at claim time; surfaced with a sparkle in collection views and the world card. Optional
  **streak** boost (deterministic, server-activity-driven) per the report — but **no buyable
  charm** (that would be Q-0039 P2W). Rides on Lane A or fishing; tiny schema add.

## 4. Anti-patterns (what "proper" explicitly rules out)

- ❌ **A new "Pokémon" catching game.** Catching already lives in fishing/mining/pets — extend
  and dock, don't duplicate (hard repo rule + Q-0182 world model).
- ❌ **A buyable premium currency / shards.** Q-0039 rejects purchasable advantage. Earned-only.
- ❌ **A standalone marketplace now.** Q-gated on economy-health evidence + fraud/legality review
  (economy-marketplace roadmap). Lanes A/B/D produce the *items* it will later trade.
- ❌ **Music playback now.** Q-0041 gate; this session ships the architecture-review pack only.
- ❌ **Creature battles / time-weather as a free-for-all.** Each is its own owner-design decision
  (battles = P2W risk; time/weather = Q-0182 biome fork).

## 5. Recommended sequencing + the open owner decision

1. **Owner answers Q-0186** (which net-new lane first; spawn defaults; reward pool). Recommended
   first build: **Lane A (Wild Encounters)** — highest engagement leverage, no gate, feeds the
   others. **Lane B** is the low-risk parallel/warm-up.
2. **Music:** owner reviews the [architecture-review pack](voice-music-architecture-review-2026-06-20.md)
   and makes the go/no-go + legal-lane call that **Q-0041** parks. Nothing builds until then.
3. **Lane C/D** follow Lane A; **marketplace** waits on its own roadmap gates; **battles /
   time-weather** wait on Q-0182 + their own design sessions.

Each lane, when greenlit, is its own runtime-verified, small-PR session — not a single mega-PR.

## 6. House-style anchors (so an executor builds a lane cold)

- New subsystem: `scripts/new_subsystem.py`, the `/new-subsystem` skill, `docs/architecture.md`
  § "Where to add a new subsystem".
- World dock: `services/world_registry.py`, `views/explore/world_hub.py`,
  [explore-hub plan](explore-hub-federated-world-plan-2026-06-19.md).
- Audited mutation / economy / XP seams: `services/economy_service.py`,
  `services/game_xp_service.py`, the `*_workflow.py` atomic pattern (Q-0071),
  `docs/runtime_contracts.md` § 9, `docs/ownership.md`.
- Pre-edit: `python3.10 scripts/context_map.py <file>` + `check_architecture.py --mode strict`.

→ relates [explore-hub plan](explore-hub-federated-world-plan-2026-06-19.md) ·
[economy-marketplace roadmap](economy-marketplace-rewards-roadmap-2026-06-08.md) ·
[pets-companions plan](pets-companions-plan-2026-06-09.md) ·
[fishing plan](fishing-open-world-expansion-plan-2026-06-18.md) ·
[voice/music arch-review pack](voice-music-architecture-review-2026-06-20.md) ·
[wild-encounters idea](../ideas/wild-encounters-activity-spawning-2026-06-20.md) ·
Q-0186 (build sequencing) · Q-0041 (voice gate) · Q-0039 (no P2W) · Q-0182 (world model) ·
Q-0040 (AI quests from bounded menus) · Q-0080 (stranger-grade) · Q-0071 (atomic workflow).

# Competitive teardown — game/economy bots + open-source ecosystems (V-14 dossier)

> **Status:** `reference` — research evidence for the **V-14 gateway** (vision doc §3)
> and the **Q-0090 ecosystem-#2 decision**. Produced 2026-06-10 by two parallel
> research agents (open-source ecosystems · game/economy giants), claims
> triangulated across official docs/wikis/fandom wikis, ≥2 sources for
> load-bearing claims. **Provenance: third-party product facts, unverified
> against the live bots — re-verify any mechanic before building on it.**
> A third lane (V-15 stat-migration API surfaces) reports separately.

## 1. The headline verdicts

1. **Ecosystem #2 recommendation: FISHING.** Dank Memer — the largest economy
   bot — chose fishing as its flagship standalone expansion and packed every
   proven retention mechanic into it (115-creature collection log, skill tree,
   idle fishing, locations/NPCs, tanks, rotating seasonal events). The
   collection bots (Pokétwo, Karuta, OwO) prove the underlying race-to-catch /
   rarity-ladder psychology at massive scale; fishing is the natural carrier.
   Fit is also highest for SuperBot: the survival plan already names
   fishing/cooking — fishing supplies cooking → energy → mining stamina
   (connected-but-separate; shared Forge-crafted rods; own local fish-market
   currency per Q-0090). **Farming had thin competitor evidence** (minor EPIC
   RPG feature); combat/dungeons overlaps existing duels + planned encounters;
   business/idle (TacoShack) is better harvested as Workshop *income
   mechanics* than as an ecosystem (weakest social ceiling studied).
2. **SuperBot's biggest genre gap is ritual, not systems:** daily
   streaks/quests/random channel events dominate both harvest tables. Deep
   systems exist here; *reasons to return today* mostly don't.
3. **The shared retention engine of the big three:** short-loop faucet →
   collection/upgrade sink → permanent-multiplier prestige → social spikes
   (events/raids/heists). **Casual protection is always structural** (cooldown
   caps, streak floors, idle automation) — never charity. This is Q-0087's
   philosophy independently validated by the whole genre.

## 2. Top harvest candidates — game/economy lane (appeal/fit 1–5)

| # | Mechanic (source) | A | F | Flag | Why |
|---|---|---|---|---|---|
| 1 | Snowballing daily streak w/ decay (Dank Memer) | 5 | 5 | core | Cheapest proven daily-return hook; bolts onto game-XP |
| 2 | Random channel events triggered by others' grinding (EPIC RPG coin rain/megalodon) | 5 | 5 | core | Makes mining visible/communal ("cave-in!") |
| 3 | Daily/weekly quest board (Dank Memer) | 5 | 5 | core | Directs casuals; reuses existing actions |
| 4 | Prestige reset w/ permanent multipliers (EPIC RPG TT / DM prestige) | 5 | 4 | core | The endgame mining lacks; voluntary reset = Q-0087-clean |
| 5 | Collection log/guidebook (DM fishing, OwO zoo) | 4 | 5 | 🎣 | Completionism is self-assigning homework |
| 6 | Upgradable official idle automation (OwO Huntbot) | 5 | 4 | 🏪/🎣 | "Upgrading automation IS the grind"; casual-core gold |
| 7 | Helper-scaled boss fights (EPIC RPG miniboss) | 4 | 4 | ⚔️ | Social spike; pairs with planned biome encounters |
| 8 | Sacrifice-surplus-for-essence sink (OwO) | 4 | 5 | 🎣 | Inflation control for ore/fish surpluses |
| 9 | Lootboxes via gameplay + vote crates (EPIC RPG, IdleRPG) | 4 | 4 | core | Variable reward; vote crates = free growth loop |
| 10 | Activity-scaled rare chat spawns (Karuta/Pokétwo) | 5 | 3 | 🎣 | Server-as-slot-machine; needs spam guardrails |
| 11 | Professions leveled by leftover materials (EPIC RPG) | 4 | 4 | core | Second progression bar from existing drops |
| 12 | Business income/hr upgrade tree (TacoShack) | 4 | 3 | 🏪 | Maps to Workshop/Home structures as income |
| 13 | Pet fusion + timed pet adventures (EPIC RPG) | 4 | 5 | core | Direct blueprint for the pets plan |
| 14 | Seasonal rotating modifiers (DM event weeks) | 4 | 4 | core | One config knob = an event |
| 15 | Group heist/PvE raid on shared target (DM bankrob, IdleRPG raids) | 4 | 3 | ⚔️ | Clan content once clans land; PvE raid > robbery |

## 3. Top harvest candidates — open-source lane

| # | Feature (source) | A | F | Why |
|---|---|---|---|---|
| 1 | Trivia engine w/ data-file question packs (Red) | 5 | 5 | BTD6 dataset → auto-generated trivia packs |
| 2 | Stocks/market sim on bot currency (FlameCogs) | 4 | 5 | Natural coins/market extension; audited mutations fit |
| 3 | Tournaments/brackets (Laggron) | 4 | 5 | Wrap existing duels/blackjack into scheduled brackets |
| 4 | Wager escrow on PvP minigames (crab-cogs) | 4 | 5 | One audited escrow service any game uses |
| 5 | Ambient catch games (Hunting/Snacktime) | 4 | 4 | Random chat spawns; ties into loot tables |
| 6 | Daily reward + streak (Nadeko) | 5 | 5 | Confirms game-lane #1 |
| 7 | Starboard (Trusty) | 4 | 4 | Member-driven highlights beside curated spotlight |
| 8 | RemindMe + user-facing scheduler slice (PCX/vrt) | 4 | 5 | Automation infra exists; expose a per-user slice |
| 9 | Economy analytics + decay (vrt EconomyTrack/BankDecay) | 3 | 5 | Owner-grade inflation telemetry; diagnostics identity |
| 10 | Collectible claim/trade (Nadeko waifus, reskinned) | 4 | 4 | Trade/collection feeds pets + market |
| 11 | Modmail/ticket panels (kyb3r, vrt) | 3 | 5 | Staff killer feature; server-management hub home; = AG-15 |
| 12 | Ban appeals flow (vrt) | 3 | 5 | Completes audited moderation lifecycle |
| 13 | Referral/invite rewards (vrt) | 3 | 4 | Growth loop wired to economy |
| 14 | AutoRoom temp voice channels (PCX) | 4 | 3 | Popular; provisioning fits; voice = new surface |
| 15 | Trigger→response expressions (Nadeko/ReTrigger) | 3 | 4 | Fits per-guild settings platform; admin-gated regex |

## 4. Retention-engine notes (the big three, compressed)

- **Dank Memer:** cooldown-command battery + quests + snowballing streak → one
  mega-economy of tradeable items → prestige multipliers + completionist
  tracks. Casuals: streaks+quests in minutes, passive-mode shields from
  robbery, never lose progress. Grinders: multipliers, market plays,
  collection completion.
- **EPIC RPG:** a *cooldown ladder* (1min hunt → hourly adventure → daily →
  weekly) so there's always a next button; random events + helper-scaled
  minibosses make grinding communal. Endgame: Time Travel resets with
  multipliers + sacrifice-score perks — **cooldowns structurally cap grinder
  advantage per day; casuals progress faster each run.**
- **OwO:** dirt-cheap hunt/battle spam + currency for merely chatting; zoo
  across 14 rarity ranks; surplus sacrifices into essence that upgrades the
  **Huntbot** (official idle hunter) — *upgrading the automation is the
  grind*; casuals check in twice a day and still fill the zoo.

## 5. Architecture lessons (open-source ecosystems)

- **Registry-as-data marketplace** (Red-Index: repo list + Action republishing
  gzipped JSON every 15 min; third-party UIs build on it).
- **Two-tier trust:** "approved" = vetted *author*, not artifact — maps to the
  repo's provenance-header discipline.
- **AI assistant as a platform** (vrt-cogs Assistant): other cogs register
  OpenAI-schema functions the assistant can call + admin-curated embeddings.
  Directly applicable to SuperBot's tool orchestration (per-cog tool
  registration seam).
- **Runtime plugin managers** are the ecosystems' growth engine — and the
  reason their audit story is weaker than SuperBot's.
- **Cautionary tales:** Loritta (1M+ guilds) went closed-source 2026-05 citing
  one-way value extraction; Nadeko gates music behind patron tiers.

## 6. V-15 stat-migration surfaces (verified lane, 2026-06-10)

- **MEE6 — feasibility HIGH, verified live today:** the unofficial public
  endpoint `mee6.xyz/api/plugins/levels/leaderboard/{guild_id}` returned
  HTTP 200 unauthenticated (pages of 100; per-player `id, xp, level,
  message_count, detailed_xp`). Gate: **401 unless the source guild enables
  "Make my server's leaderboard public"** — which doubles as a natural consent
  mechanism. **XP curve verified two ways** (official docs repo + live data):
  `xp_to_next(lvl) = 5·lvl² + 50·lvl + 100` — so both level-preserving and
  XP-preserving mappings are computable exactly. ToS posture: unofficial,
  undocumented, tolerated-but-unsupported (no evidence of blocking; all
  wrappers carry subject-to-change warnings). Rate limits undocumented —
  import must throttle politely.
- **Prior art proves the lane:** Lurkr's `/importxp` imports MEE6 levels +
  role-reward mappings to this day (admin-only, once/hour); Atom documents
  imports from **eight** bots (MEE6, Amari, Polaris, XP Bot, Lurkr, Arcane,
  Engauge, Level Up); multiple open-source MEE6 scrapers share the same
  endpoint. The owner's V-15 idea is established industry practice.
- **Ecosystem fragility warning:** Lurkr **disabled** its Amari and Polaris
  imports (2026-03) because *those bots' APIs died* (Amari API taken down;
  Polaris retired). Lesson: build importers source-by-source behind one seam,
  expect sources to vanish, MEE6 first (biggest incumbent + only live-verified
  surface).
- **Other surfaces (verified 2026-06-10):** **Lurkr** — real public API
  (`api.lurkr.gg/v2`, `X-API-Key`, 1500 req/min documented, XP curve
  published: `100 + 50·(level−1)²`) → clean import source. **UnbelievaBoat** —
  official token API with per-guild authorization (balance get/set +
  leaderboard) → *economy* import possible, pattern reference for our own
  future API. **Arcane** — no API (scrape-only, free tier caps leaderboard at
  top 100; curves documented: linear `level·100+75` / exponential
  `5·level²+50·level+75`). **Polaris** — API retired (JSON file export only;
  site 502 during research). **Atlas / Carl-bot** — no export surface; Carl's
  leveling is premium, **uses MEE6's exact curve and imports MEE6 itself**.
- **Level-channel parsing fallback — verdict: narrow but real.** MEE6's default
  is verified (`GG **{player}**, you just advanced to level **{level}**!`),
  Arcane's documented; but every bot allows full customization/disable, and
  Arcane can emit embeds/images — so history-parsing is only reliable on
  never-customized plain-text channels. Use as fallback for MEE6-style
  defaults, always behind a preview ("here's what we reconstructed — confirm").
- **Rate-limit reality:** MEE6 temp-bans (~30 min) aggressive readers;
  Lurkr self-limits its import to once/hour citing third-party limits.
  Import jobs must be slow, paged, resumable.
- **Curve mapping is established practice:** Lurkr ships selectable curve
  presets — "Lurkr Default, **Amari, or MEE6**" — plus custom polynomials;
  with MEE6's exact formula verified, level-preserving import is just math.
- **Amari — official keyed API documented as live** (`amaribot.com/api/v1`,
  key by application form, 60 req/min then 60-min lockout; member + paged
  leaderboard + **raw full-leaderboard** endpoints returning `exp`/`level`).
  **Conflict to resolve before building:** Lurkr's 2026-03 changelog says
  "Amari's API has been taken down" — docs/wrappers say otherwise; settle by
  applying for a key and probing. Curve: community-derived
  `20·(L−1)² + 35` (unofficial). Feasibility: **medium-high pending probe**.
- **Tatsu — official API live** (`api.tatsu.gg/v1`, key via `t!apikey`,
  60 req/60s, ToS PDF read: no API-specific clause; §6 forbids commercial
  exploitation/overreach) but guild endpoints expose **rank + score only — no
  per-guild XP/level** → feasibility for *level* import: **low** (score-
  threshold reconstruction at best).
- **Import priority that falls out:** MEE6 (live-verified, no key) → Lurkr
  (clean keyed API + curve presets) → Amari (after key probe) → UnbelievaBoat
  (economy, separate lane) → channel-parsing fallback → Tatsu/Arcane (low) →
  Atlas/Carl (none).

## 7. Sources

Game/economy: dankmemer.lol/tutorials · dankmemer.wiki (Fishing, Rob-and-Heist,
Advancements, Quests) · dank-memer.fandom (Prestige, Daily) · epic-rpg.fandom
(Time_Travel, Beginner's_Guide, Cooldowns, Regular_Events, Lootbox, Pets) ·
owobot.fandom (Hunting, Auto_Hunting, Gem_Animals, Animals) · idlerpg.xyz +
wiki.idlerpg.xyz (Gods, Favor, Adventures) · mudae.fandom (Kakera, Values) ·
karuta.wiki.gg (Cards) · docs.poketwo.net (Spawning & Catching) · tacoshack.dev
(+FAQ) · top.gg listings · blog.communityone.io deep-dives (OwO, Karuta).
Open-source: docs.discord.red · github: Cog-Creators/Red-Index, vertyco/vrt-cogs
(incl. assistant), TrustyJAID/Trusty-cogs, PhasecoreX/PCXCogs, AAA3A-AAA3A/
AAA3A-cogs, hollowstrawberry/crab-cogs, Flame442/FlameCogs, retke/Laggrons-
Dumb-Cogs, aikaterna/aikaterna-cogs, kyb3r/modmail, python-discord/bot,
LorittaBot/Loritta, jagrosh/MusicBot · nadeko.bot/commands.
V-15 lane: mee6.xyz leaderboard endpoint (live probe 2026-06-10) ·
github: Mee6/Mee6-documentation (levels_xp.md), rjt-rockx/mee6-levels-api,
hyperevo/mee6-py-api, GDColon/Polaris-Open, TFAGaming/NetLevel-Bot,
appgurueu/FREE6 · lurkr.gg/docs (importing-levels guide + changelog) ·
docs.leveling.gg (Atom import).

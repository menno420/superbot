# SuperBot product vision — owner statement + agent response (2026-06-10)

> **Status:** `ideas` (captured — **not approved for implementation**).
> Source: the maintainer's written vision statement (2026-06-10 ideation session) +
> the executing agent's creative response, dedup-checked against the existing capture
> docs, plans, and decided owner questions. Route each item through the lifecycle in
> [`README.md`](README.md) before implementing. Source code, binding contracts, and
> `docs/current-state.md` win over anything here.
>
> **How to read this:** §1 is the owner's vision in his own structure (owner-voice —
> preserve it). §2 maps it onto what already exists or is decided, so future sessions
> don't re-litigate or duplicate. §3 numbers the genuinely **new** owner items
> (`V-xx`). §4 is the agent's own additions (`AG-xx`). §5 flags the real tensions.
> §6 is the routing ledger.

---

## 1. The owner's vision (2026-06-10, owner-voice)

**The headline:** *"I want superbot to be the best bot ever made."*

**Feel:** easy and fun; you shouldn't have to think while using or setting it up. The
bot should *feel smart* — it correctly recognises your server layout and channel
purposes. All server-related management lives in one centralized place.

**Setup:** fully up and running on a new server **within 2 minutes**. Every wizard
step is clear; steps **combine multiple similar bindings at once** wherever
applicable; people always have a **clear overview of everything they have selected**.

**Panels:** people should **never have to look for the current active panel** — every
panel **updates in place** to prevent chat clutter. Every panel has a **clear,
persistent link to its mother panel and to the help menu**; related panels (e.g.
server management) can link directly to each other.

**The ideal help menu:** appealing, clear overview, not too many options. The first
view should have only **3–4 sections**, as **normal buttons** rather than the current
dropdown, and it should take a **maximum of 3 buttons** to reach any game, setting, or
action. The sections he sketched:

1. **"Games/actions"** (or a better name) — all the player-facing game panels (mining
   view, blackjack, eventually a "card games" section housing blackjack/poker/…), but
   never over-nested.
2. **Bot settings** — admin-only; *or* a different version for regular members so
   they can tune the bot for themselves **without changing it for others**.
3. **General commands** — info functions, help / bug reports / tickets, timers,
   polls, server stats, user stats, possibly later a weather command (enter a
   location, see the weather) — anything that fits between games and
   moderation/settings.
4. He lands on **4 main options being best**, one of which is bot settings.

*Owner clarification (2026-06-10, Q-0079): the "maximum of 3 buttons" is
**navigation depth** — at most ~3 presses from Help Home to any destination — **not**
a per-panel button cap. "The 3 buttons per panel is never going to work": panels keep
every useful button, and almost all current buttons are useful. The aim is cleaner UX
through fewer **or better-defined** buttons — clearer labels, grouping, placement —
never removal quotas.*

Every setting should be easily changed, and it should be clear **what each setting
does and why you would change it**.

**The flagship game:** many mini-games, but the main idea is **one open-world-like
RPG mining/exploration game**:

- You start on the **"world" panel** with options like **mining, fishing, exploring,
  chopping trees, making a fire / eating**.
- **Difficulty levels**, chosen at the start:
  - **Easy:** no health, no hunger, can't die or get hurt. (Only exception: PvP
    battles — those never touch your real character anyway.)
  - **Medium:** health + hunger systems, plus an **energy system** that decides how
    much you can mine/chop at once — noticeable but **not annoying**; ~**10 actions
    an hour** as base, upgradeable later via skills and level increases.
  - **Hard:** an intense experience — only **5 actions per hour** before energy is
    depleted, but **every level-up resets your energy**; rewarded the most: an
    **extra chance at 2 skill points per level instead of 1** (the chance increases
    slightly with level), plus bonuses like **extra % base loot**; you also get
    hungry faster, have less health, and meet **more and stronger monsters / random
    encounters** while mining and exploring.
- **PvP battles:** every battle is a **fresh ephemeral arena where everyone starts
  equal except for their crafted items**; the only things affected are
  **tool/weapon/armor durability** and **XP gains for both winning and losing**
  (winning gives substantially more). Your real game character is never harmed.
- **Pets:** you can obtain a pet on your journeys by **meeting one and helping it
  during a quest**, after which it joins you — **up to 3 animals at once** — giving
  buffs like **scouting** (a chance to prevent dangerous encounters) or **smelling
  gold** (find more treasure).
- **AI plays a large role:** it guides people during quests with **epic stories** —
  a game people want to play **together**, like a **D&D experience with actual
  characters**. The AI should be able to **activate command panels** — e.g. send a
  user their character view and tell them to equip a certain item, **after which the
  game/story automatically continues** — or send a **button view with a few
  different actions** instead of making people type, which also gives the AI freedom
  in deciding what the options are.

---

## 2. Where this lands on what already exists (dedup map)

Verified against source + the routed decisions on 2026-06-10. **Nothing in this
section is new work** — it's the ground the vision stands on.

| Vision element | Already exists / decided |
|---|---|
| "Bot recognises server layout / channel purpose" | `services/setup_ai_advisor.py` — a `GuildSnapshot` → validated `SetupPlanDraft` advisor seam (deterministic default + OpenAI impl) already exists; recommendations are schema-validated. The *wiring into a 2-minute wizard flow* is the open part (V-01/AG-02). |
| Centralized server management | The Server Management Hub shipped (#584); Access Map + Help Preview staff subpanels (#656). |
| Setup wizard | Wizard PR1–PR3 tranche shipped (#435 lineage; verified 2026-06-10); **PR4 `/myprofile` is the named next wizard slice** — it aligns directly with V-04/AG-04 (per-user surface). |
| Panels updating in place | `views/navigation.py` (Phase 3.5) already centralises defer→build→**edit-in-place** back-transitions; help Home swaps views in place. The *doctrine* (every panel, persistent mother/help links, one-active-panel) is the new part (V-02/AG-03). |
| Help menu structure | Help Home is `HelpCategoryView` — a **dropdown** of the 10 registry hubs + Advanced fallback, all five render paths on the reason-coded projection seam (#657) with guild overlay (#659). The **4-button restructure** (V-03) is new — and cheap *because* of the seam. |
| "What each setting does and why" | Settings hub actionable-groups discovery (#640) + Phase 2 declaration coverage (#654); presets-everywhere posture decided (Q-0070). Per-setting "why you'd change it" copy is a fit for the declared-schema lane. |
| Open-world mining RPG | The character platform vision (`mining_exploration_brainstorm.md` §7) + Waves 0–2 substantially **shipped**: depth/Descent (#607), equipment + `EffectiveStats` (#606/#608), market (#609), Workshop + durability (#624), every-write-behind-workflow + game-XP service + leaderboards + deeper ladders (#661–#665/#667). Next named slices: structures §7.5 (Forge/Vault/Home), then the §7.4 skill tree. |
| Chopping trees | `!chop` exists (surface activity); fishing/cooking do not (V-07). |
| PvP arena posture | Deathmatch duels already start from equal base stats + a small crafted-gear edge (#608) and tick **durability** on completion (Q-0054 closed). V-08 confirms the shipped shape and adds XP-both-sides (the `game_xp` service #665 is the award path). |
| Pets | A structured plan exists: [`../planning/pets-companions-plan-2026-06-09.md`](../planning/pets-companions-plan-2026-06-09.md) (egg drops → hatch → care-loop sink → ≤1–2% perks; owner pick Q-0053). V-09 **diverges in acquisition, party size, and perk strength** — see §5 tension T-1. |
| AI dungeon master | **Q-0040 answered (2026-06-09): bounded-menu posture** — AI *chooses* quest template / reward tier / difficulty from pre-approved, hard-capped menus enforced by deterministic code; thread-per-session first; per-guild opt-in, off by default; budget-capped on the orchestration seams (#612/#618/#619). Still needs its own plan + per-exposure lift + one small bounded-authority decision. V-10/AG-09 give that decision its concrete UI shape. |
| Difficulty / survival | §6 of the mining brainstorm explicitly **deferred** health/stamina ("None in v1 … later"; reserved columns sketched). V-05/V-06 are the first concrete design for that deferred layer. |
| Timers, polls, info, stats | `!remind`, `!poll`, `!info` exist (`utility_cog`); server stats = Community Spotlight (#613); user stats = the Character overview (#610). Tickets/bug-reports do **not** exist (AG-15). Weather does not exist (V-11). |
| Per-user settings | **Nothing exists** — settings are guild-scoped; the only per-user state is participation opt-in/out (`user_participation`). V-04 is a genuinely new scope. |
| Mobile-first, few-clicks UX | Owner-vision 2026-06-08 §8 (mobile-first) + the fun/ease brainstorm Catalog C. The **≤3-clicks rule as a checkable invariant** is new (AG-01). |

## 3. The genuinely new owner items (V-xx)

- **V-01 — The 2-minute-setup target.** A new-server install reaches "fully
  running" in ≤2 minutes: wizard steps combine similar bindings into one action;
  a persistent "everything you selected" overview; no step that does nothing.
  *(KPI framing for the setup lane — measurable, see AG-01/AG-02.)*
- **V-02 — Panel navigation doctrine.** Every panel updates in place; users never
  hunt for the active panel; every panel carries persistent links to its **mother
  panel** and the **help menu**; sibling panels may cross-link (server management).
- **V-03 — Help Home as 3–4 buttons.** Replace the Home dropdown with ~4 top-level
  buttons; **≤3 interactions to any destination**. Owner's sketch: Games/Actions ·
  General · Bot Settings (admin) · (a member-facing variant — see V-04).
  *(Q-0079: the ≤3 is navigation depth, not a per-panel button cap.)*
- **V-04 — Per-user bot preferences.** Regular members tune the bot for themselves
  without changing it for others — a third settings scope (platform > guild >
  **user**).
- **V-05 — RPG difficulty modes.** Easy (no health/hunger/death — i.e. exactly
  today's game), Medium (health + hunger + energy, ~10 actions/hr base,
  upgradeable), Hard (5 actions/hr; level-up resets energy; chance of 2 skill
  points per level, scaling with level; +% base loot; faster hunger; less health;
  more/stronger encounters). PvP always equal-start regardless of difficulty.
- **V-06 — Energy as the action-rate resource.** Governs mine/chop/etc. volume;
  noticeable, never annoying; upgradeable via skills and levels.
- **V-07 — New world activities: fishing + campfire/cooking/eating.** The world
  panel offers mining · fishing · exploring · chopping · fire/eat as one surface.
- **V-08 — PvP carry-out rule (confirm + extend).** Fresh equal-start arena; only
  durability + XP leave the arena; **XP for both winner and loser** (winner
  substantially more).
- **V-09 — Pets as story companions.** Acquired by meeting + helping an animal
  during a quest; up to **3 travel with you**; journey buffs (scout: chance to
  prevent dangerous encounters; gold-sense: more treasure).
- **V-10 — AI as panel orchestrator.** Within the Q-0040 bounded posture: the AI
  can *push* a relevant panel to a player (character view + "equip the lantern"),
  and the story **auto-continues when the game event actually happens**; the AI can
  present **its chosen subset of legal actions as buttons** instead of free-typing.
  The target experience: D&D-together with real characters.
- **V-11 — Weather command.** Enter a location → current weather. Tiny utility;
  external API; privacy posture per Q-0041 (don't store locations by default).
- **V-12 — "Don't make me think" as the design bar.** The bot feels smart: correct
  guesses about server layout, obvious next actions, no dead ends. (The qualitative
  umbrella over V-01/V-02/V-03; AG-01 makes slices of it measurable.)
- **V-13 — Multi-ecosystem open world (added 2026-06-10, brainstorm round 5).**
  Owner-voice: mining is "one of a couple of ecosystems, that should be connected
  but also separate, maybe they would get some different currency but the tools
  are the same, and for some tools maybe you'd need to invest a little time in
  another section… the mining is only going to be one part of the open world
  system, it just now be the main focus because it has all the variables in one
  section, so it makes the best foundation to lay the open world idea on top."
  Architecture intent: **federated ecosystems on one character/tool substrate** —
  per-ecosystem currencies (maybe), shared tool identity, deliberate light
  cross-investment links, mining as the proving ground whose patterns (energy,
  ladders, workshop seams, game-XP) get *extracted into the substrate* for
  ecosystems #2+. **Answered same night (Q-0090, router §37):** ecosystem #2 =
  **research-decided** (the V-14 teardown picks it from evidence) · currencies =
  **local per-ecosystem, no exchange** (main coins stay the one universal
  layer; no arbitrage, sinks stay local) · cross-links = **medium, special
  tools only** (a few advanced *optional/prestige* tools may require "a little
  time" in another ecosystem; **no core capability may be gated this way** —
  the Q-0087 boundary).
- **V-15 — Migrate game stats from existing bots (added 2026-06-10, round 5
  tail).** Owner-voice: "it should also be easily possible to migrate game
  stats from existing bots, and at least the XP/LVL should be automatically
  fetchable from either player stats directly or from the dedicated LVL
  channel if it exists." The adoption weapon for the Q-0080 public goal — a
  server switching to SuperBot keeps its members' levels. Two fetch paths as
  stated: (a) **direct stats** where the incumbent exposes them (e.g. public
  leaderboard APIs — availability/ToS per bot must be verified), (b) the
  **level-channel fallback** — parse the announcement channel's history ("GG
  @user, you reached level 12") to reconstruct levels bot-agnostically.
  Design notes for the future plan: level-preserving vs XP-preserving curve
  mapping is a real choice; import is a compound generated write → **draft
  lane** (SetupOperation preview + admin confirm, audited); ToS/privacy
  review per source bot. **Scope rider on the V-14 gateway session:** the
  teardown should also catalog each bot's export/API surface — that catalog
  *is* the migration design's input.
- **V-14 — Competitive feature mining (added 2026-06-10, brainstorm round 5).**
  Owner-endorsed research direction: systematically tear down the big bots'
  ("thousands of features") catalogs, "filter out some of the best ideas and
  combine them into another branch of the bot" — a deep-research session
  producing a verified, dedup-mapped candidate list routed through the normal
  idea conveyor (nothing auto-approved). **Answered same night (Q-0090): scope =
  game & economy bots first** (Dank Memer / EPIC RPG / OwO / idle bots), and the
  session is **elevated to gateway status — its findings decide ecosystem #2**
  of the V-13 open world (owner's pick: "let the research decide"). **Research
  executed the same night** (three parallel agents, same conversation):
  **[the teardown dossier](competitive-teardown-2026-06-10.md)** — ~95
  documented features, 30 scored harvest candidates, retention-engine
  analysis, V-15 surfaces verified live. **Ecosystem-#2 verdict: FISHING**
  (Dank Memer's own flagship-expansion choice + collection-bot psychology
  proven at scale + highest SuperBot fit via the cooking→energy cross-link) —
  **owner ratification pending** (asked in-conversation).

## 4. Agent response — what I'd add to make it the best bot ever (AG-xx)

*The agent's own creative input, requested by the owner this session. Same status as
§3: captured, not approved.*

**Platform / UX**

- **AG-01 — Make the UX laws checkable.** SuperBot's culture is self-maintaining
  invariants; apply it to UX: (a) a CI graph-check over the hub registry + help
  projection asserting **every registered command/panel is reachable in ≤3
  interactions from Help Home** (V-03's rule, pinned forever); (b) "time-to-
  configured < 2 min" as a scripted step in the production eval checklist (V-01);
  (c) zero-dead-buttons — every visible button's action resolves or renders a
  governed denial (the projection's reason codes already exist).
  *Owner-bounded (Q-0079, 2026-06-10): (a) checks navigation **depth** over the
  projection — a per-panel button-count lint is explicitly rejected. Cleaner UX
  means better-defined/grouped buttons; removal only for genuine redundancy,
  never to hit a number.*
- **AG-02 — Setup Smart Scan + readiness meter.** First-run wizard step: snapshot
  the guild (channels, names, topics, permissions), run the **existing advisor
  seam** (deterministic heuristics first, AI optional per guild policy), and
  present one **proposed binding map with confidence labels** and a single
  **"Accept all"** → the 2-minute goal for a typical server. Afterwards it stays
  available as a **readiness meter** ("Server 87% configured — 2 suggestions"),
  riding the shipped diagnostics/drift machinery instead of a new system.
- **AG-03 — One-active-panel + summon.** A small `panel_registry` (guild, user,
  panel-kind → message ref): opening a panel you already have **moves** it (edits
  the old message to a tombstone link, posts/updates the canonical one); a
  **"📍 bring my panel here"** action summons it to the current channel. Plus the
  V-02 standard: a breadcrumb line (`🏠 Home › 🎮 Games › ⛏️ Mining`) and two
  persistent row-4 buttons (Mother panel · Help) on every `BaseView` descendant —
  one shared implementation in `views/base.py`/`views/navigation.py`, not 30 copies.
- **AG-04 — `user_prefs` service (the V-04 third scope).** `utils/db/user_prefs.py`
  + an audited mutation seam; read at render time. Candidate prefs: compact vs.
  rich embeds · DM notification opt-ins (owner-vision §22) · quiet mode (never
  ping) · timezone/locale (feeds `!remind`, birthdays) · default-ephemeral game
  panels · pinned favorite games on the Games hub. Surfaced as the member-facing
  settings panel from V-03's "My Stuff" button — and the natural sibling of the
  wizard lane's named-next **PR4 `/myprofile`** slice: same surface, one plan.
- **AG-15 — Tickets / suggestion box.** The one V-03 "General" item with no owner
  today: `!ticket` / a Help button → modal → a staff triage panel (claim/resolve/
  reply), audited like every mutation. Closes the vision's "help/bug
  reports/tickets" gap with existing panel + audit patterns.

**The RPG (extending V-05…V-09 inside the shipped platform)**

- **AG-05 — Energy as smooth regen, not hourly buckets.** Model energy as
  regen-over-time (e.g. 1 per 6 min toward a cap) instead of a "per hour" window:
  no top-of-hour cliff, mobile-friendly glanceability (⚡ 7/10 · next in 4 m), and
  the same math supports Medium (~10/hr) and Hard (cap 5) tuning. Level-up refill
  (V-05 hard) becomes a one-line rule. Skills/structures raise cap or regen.
- **AG-06 — Close the loop: food is the consumable durability.** Fishing/hunting
  yield raw food → **cook at the campfire** (V-07) → food restores hunger/energy.
  Food mirrors gear durability as the *recurring consumable sink* for gathering
  activities; cooking awards game-XP and feeds the Crafting skill branch. One
  economy, two sinks (repair coins/ore · food), zero new currencies.
- **AG-07 — Encounter tables: biome × difficulty, pet-modified.** Deterministic
  roll tables own danger (Q-0040-compliant); Hard difficulty raises encounter
  weight/strength (V-05); a scouting pet applies a visible "prevented!" roll
  (V-09) — pets modify the *table inputs*, keeping perks honest and testable.
- **AG-08 — Quest engine as the deterministic substrate.** A small template set
  (fetch · escort · hunt · **rescue** · mystery) with bounded slot menus (target,
  biome, reward tier) — exactly the menus Q-0040 lets the AI pick from. **The
  rescue template doubles as V-09's pet-acquisition path** (see T-1). Quest log on
  the character panel; completions emit EventBus events.
- **AG-09 — The "Story Actions" view (V-10, mechanized).** The *one* component the
  AI may emit: title + 2–4 buttons, each bound to a **whitelisted legal action**
  computed by the game engine for that player *right now* (equip X · move to Y ·
  accept quest Z · talk). The AI chooses which legal actions to surface and the
  flavor labels; code enforces legality, caps, and authority at click time (the
  views rule). Story resume = the quest engine subscribing to game events
  (`item_equipped`, `depth_changed`), so "equip the lantern → the story continues"
  is event-driven, not poll-driven. This is the concrete candidate for Q-0040's
  named "small bounded-authority decision."
- **AG-10 — Expeditions (async co-op).** A party of 2–4 (+pets) commits energy to
  launch a timed expedition that resolves hours later from the party's **build
  synergy** (digger + fighter + looter beats three diggers — §7.3's build-identity
  engine doing social work). Co-op play without requiring everyone online —
  mobile-first multiplayer.
- **AG-11 — Hard-mode death = a rescue mission, not deletion.** On death you keep
  your character; carried (non-equipped) loot drops at the death site; you — or
  another player, or your pets — can mount a recovery run. Death becomes *content*
  and a social hook instead of rage-quit fuel.
- **AG-12 — The daily campfire scene.** First rest of the day: a short AI-narrated
  recap of your day's exploits at the fire (token-capped, Q-0040 narrator lane).
  Cheap recurring delight that makes the world feel alive and gives V-07's fire a
  daily reason to exist.
- **AG-13 — Seasonal "Depths League".** An opt-in fresh-character seasonal ladder
  (the owner already picked weekly/monthly resetting boards, owner-vision §14) —
  difficulty-flagged (⭐/⭐⭐/⭐⭐⭐ per V-05) so hard-mode runs get their glory.
- **AG-14 — Postcards.** Rare finds auto-render a small PIL share-card ("🌋 Found a
  Diamond at depth 52 — Hard mode"), postable to the spotlight feed. Revives
  brainstorm §2.7 as the social-sharing artifact; the PIL stat-card machinery
  (#665) already exists.

## 5. Tensions to resolve (flagged honestly, not silently merged)

- **T-1 — Pets: vision vs. plan.** The structured pets plan (Q-0053) says egg
  drops + care-loop + **≤1–2% perks, max 1 displayed companion**; V-09 says
  quest-rescue acquisition, **party of 3**, and stronger-feeling buffs
  (encounter-prevention, treasure-sense). Proposed reconcile: eggs stay the
  *common* path; the AG-08 rescue template becomes the *rare/unique-species* path;
  party cap grows 1 → 3 across the plan's phases; V-09's buffs implement as
  AG-07 table modifiers tuned small. **✅ Answered (Q-0078, 2026-06-10): "Both
  paths" — the proposed reconcile approved as written; the pets plan keeps its
  P1–P4 shape and gains the rescue path + 1→3 party growth as future phases.**
- **T-2 — Energy vs. "active sessions, idle parked" (§7.2) and "not annoying".**
  An action budget is a *throttle* on the active play the owner chose. The saving
  grammar: Easy mode has **no energy at all** (today's behavior unchanged — the
  feature ships as pure addition), and Medium's budget is generous with visible
  regen (AG-05). Numbers are tuning, not architecture — but the *existence* of
  energy on Medium should be an explicit owner confirm at promotion time.
- **T-3 — Difficulty switching.** Leaderboards (#665) become incomparable if
  players hop difficulties freely. Candidate rules: one-way ascent (easy→medium→
  hard) · free switch with per-difficulty board flags · locked at creation ·
  seasonal reset (AG-13). **✅ Answered (Q-0078, 2026-06-10): one-way ascent —
  upgrade anytime, never downgrade; board entries carry a difficulty flag
  (⭐/⭐⭐/⭐⭐⭐).**
- **T-4 — Help Home restructure vs. the in-flight Help lane.** The overlay editor
  UI plan (2 PRs) is queued on the same surface. Sequence V-03 *after or with* it,
  on the same projection seam — not as a parallel fork. The 10-hub → 4-button
  mapping needs one decision: where Economy and BTD6 live (proposal: 🎮 Play =
  games + btd6 + economy-as-player; 🧭 Server & Info = utility + community; 🙋 My
  Stuff = profile/prefs/reminders/tickets (needs V-04); ⚙️ Manage = settings +
  server-management + moderation + admin + diagnostics, governance-gated).
  **✅ Answered (Q-0078, 2026-06-10): the 4-button mapping approved as proposed;
  sequencing after/with the overlay editor UI stands.**
- **T-5 — AI DM scope creep risk.** V-10 is inside Q-0040's posture, but every
  concrete piece (panel push, Story Actions, auto-continue) **writes, costs money,
  and adds UI** — Q-0048's standing lift does *not* cover it. AG-08/AG-09 are the
  plan-shaped path; nothing ships without the per-exposure lift + the bounded-
  authority decision Q-0040 already names.
- **T-6 — Public scale × cosmetic-only donations × hard AI ceiling
  (Q-0080 × Q-0039 × Q-0082, added 2026-06-10).** A public bot's AI cost grows
  with guild count, while revenue is pinned ~zero (cosmetic-only, no bot-side
  billing) and the ceiling is fixed. Resolution grammar already in place: AI
  default-off per guild (Q-0040), tiny derived per-guild budgets, heavy
  caching/templates, visible in-world degradation ("the storyteller is
  sleeping"). If AI features ever prove core to the public product, Q-0039 is
  the lever to revisit — owner's call, flagged here so nobody resolves it
  silently.

## 6. Routing ledger (state: captured → routed; Q-0078 picks applied 2026-06-10)

> **Q-0078 (2026-06-10):** the owner picked **RPG survival design** and **Help
> home + navigation** as the next planning targets. The survival design is
> structured: [`../planning/rpg-survival-difficulty-design-2026-06-10.md`](../planning/rpg-survival-difficulty-design-2026-06-10.md).
> The help-home/navigation plan is the next grooming target (sequenced with the
> Help lane's overlay editor UI). Per-user prefs and AI DM v1 stay captured.
>
> **Q-0080–Q-0083 (2026-06-10, same session — agent-initiated deep round):**
> distribution ambition = **public bot is the goal** (Q-0080, a design filter
> every new plan inherits) · flagship RPG = **solo core + co-op moments**
> (Q-0081, binds the quest-engine plan single-party-first) · AI spend =
> **hard ceiling, graceful degrade** (Q-0082; the € figure is owed after the
> first prod measurements) · workflow end-state = **full self-driving,
> explicitly not near-term** (Q-0083). New tension **T-6** (§5). Details:
> router §35.

| Item | Owning lane / home | Rough size | Suggested next step |
|---|---|---|---|
| V-01 + AG-02 (2-min setup, Smart Scan, readiness meter) | Setup/wizard lane (adaptive-setup plan) | M | Fold into the wizard lane as its north-star KPI; AG-02 slice when the lane resumes |
| V-02 + AG-03 (navigation doctrine, one-active-panel, summon) | Building/interface (views/base + navigation.py) | M | Structure into a small `docs/planning/` plan — high leverage, low risk |
| V-03 + T-4 (4-button Help Home, ≤3-clicks) | Help lane (projection seam) | S–M | Sequence with/after the overlay editor UI plan; one design decision (hub mapping) |
| V-04 + AG-04 (per-user prefs / My Stuff) | New: `user_prefs` seam + wizard PR4 `/myprofile` | M | Structure into one plan with PR4 (same surface) |
| V-05/V-06 + AG-05/AG-07 + T-2/T-3 (difficulty, energy, encounters) | Games lane (character platform §7) | L | Dedicated design doc → owner confirms numbers + switching rule, then slices after §7.5 structures |
| V-07 + AG-06 (fishing, campfire/cooking, hunger) | Games lane | M | Same design doc as V-05 (one survival design, not three) |
| V-08 (PvP XP both sides) | Games lane — `game_xp` award path exists | S | Quick-win candidate next games session |
| V-09 + T-1 (story pets, party of 3) | Pets plan (amend, don't fork) | M | Owner pick on T-1, then amend the pets plan |
| V-10 + AG-08/AG-09 + T-5 (quest engine, Story Actions, AI DM v1) | AI lane × games lane (Q-0040 posture) | XL | Structure the quest-engine + Story-Actions plan; the bounded-authority decision rides it |
| V-11 (weather) | Utility hub | XS | Quick-win candidate (free no-key API, store nothing) |
| V-12 + AG-01 (UX laws as invariants) | Tooling/CI + eval checklist | S | Quick-win: the ≤3-clicks **depth** check is one test over existing registries (no button-count lint — Q-0079) |
| AG-10 (expeditions) | Games lane (§7.7 Wave 5 social) | L | Capture only; revisit at the social wave |
| AG-11 (death = rescue mission) | Games lane (rides V-05 hard mode) | S | Fold into the V-05 design doc |
| AG-12 (daily campfire scene) | AI lane (Q-0040 narrator) | S | Capture; candidate first AI-narration slice after the DM plan exists |
| AG-13 (Depths League seasons) | Games lane (leaderboards #665) | M | Capture; pairs with T-3's answer |
| AG-14 (postcards) | Games lane (PIL machinery #665) | S | Quick-win candidate after stat cards bed in |
| AG-15 (tickets/suggestion box) | New small subsystem (community/utility hub) | M | Structure when V-03's General section is designed |

---

*Cross-links: the character-platform vision this extends is
[`mining_exploration_brainstorm.md`](mining_exploration_brainstorm.md) §7 (its §7.8
"still-open threads" now also point here); the prior owner-preference capture is
[`owner-vision-ideas-2026-06-08.md`](owner-vision-ideas-2026-06-08.md); the AI DM
posture is router **Q-0040**; the pets plan is
[`../planning/pets-companions-plan-2026-06-09.md`](../planning/pets-companions-plan-2026-06-09.md).*

# Owner vision — ideas capture (2026-06-08)

> **Status:** `captured` (raw → captured). Nothing here is approved for implementation.
> Source: 20-question interactive session with the maintainer on 2026-06-08.
> All items below reflect the owner's stated preferences. Route each idea through
> the lifecycle in `docs/ideas/README.md` before implementing.

---

## 1. New games

### 1a. Poker — multi-player table (3–6 players)
**Selected:** Multi-player table (3-6)
Full Texas Hold'em table with a lobby, blinds, and hand progression. Currency
wagered via the bot economy. Not heads-up, not video-poker — a social table.

### 1b. Idle / clicker game — active + idle hybrid
**Selected:** Active + idle hybrid
Idle base with optional active boosts (clicking, events) for faster gains.
**Owner preference:** Tie this to the existing mining/exploration system — extend
it rather than creating a standalone resource loop. Resources accumulate offline;
active play gives multipliers.

---

## 2. Economy & progression

### 2a. Item marketplace — player-to-player trading
**Selected items:** Mining resources · Cosmetic roles/titles · Rare collectibles
- Raw ore, gems, and crafted mining materials are the primary trade goods.
- Cosmetic Discord roles / displayed titles purchaseable off the market.
- Unique or limited-edition collectibles with no gameplay function, only rarity
  (no XP boosts or pay-to-win consumables — *not selected*).

### 2b. Streak / subscription rewards
**Selected rewards:** Currency bonuses · Exclusive cosmetics · Lottery tickets/chances
- Consecutive daily interaction → bonus coins/gems.
- Streak-holder-only profile badges, titles, or colour variants.
- Streak days count as lottery entries in a weekly prize draw.
- *XP multipliers were not selected* — keep XP gain flat/non-pay-to-win.

---

## 3. AI-powered features

### 3a. AI dungeon master — all three delivery modes
**Selected:** Channel (persistent world) + Thread-per-session + DM (solo)
All delivery modes are wanted. Suggested priority: thread-per-session first
(easiest isolation, no persistent-state burden), then channel persistent world,
then DM mode.

### 3b. AI-generated in-game events — all four styles
**Selected:** Narrative flavor text · Dynamic difficulty scaling · Procedural quests · Player-prompted events
- Narrative text wraps a mechanically-set event in LLM-written story copy.
- Dynamic scaling reads server activity; adjusts boss HP, drop rates.
- Procedural quests: fully AI-generated text, objectives, and rewards.
- Player-prompted: a player writes a prompt → bot generates a custom event.

### 3c. Natural-language commands
**Selected:** Yes (confirmed in AI features round).
**Pain point identified:** The bot is *too narrow — only handles specific intents*.
Any text slightly off-script returns "unknown command". Widening intent coverage
is the primary fix needed before expanding NL further.

---

## 4. Social & community

### 4a. Guilds / clans
**Selected guild features:** Shared bank/treasury · Guild vs guild battles · Guild upgrades/levels
- Members contribute to a shared bank; officers control spending.
- Competitive inter-guild events (leaderboard, game tournaments).
- Guilds earn XP → unlock perks (bonus mining rates, cosmetic banners, etc.).
- *Guild missions/quests not selected* — keep scope tight initially.

**Top priority overall:** "More social — players interacting with each other" was
selected as the #1 thing that would make SuperBot feel noticeably more alive. Guilds
are the keystone social feature.

### 4b. Achievement / badge system
**Selected triggers:** Game milestones · Social actions · Hidden/secret
- Game milestones: win X blackjack hands, reach mining level 50, etc.
- Social: join a guild, trade with 5 players, recruit a member.
- Hidden: nobody knows until they stumble into them (no spoilers in `/help`).
- *Time-limited/seasonal not selected* — keep achievement roster persistent.

### 4c. Player profile cards
**Selected fields:** Economy stats · Guild membership & rank
- Economy stats: wallet balance, total earned, items owned, marketplace activity.
- Guild name, player's role in guild, and guild-wide rank.
- *Level/XP bar and game W/L records were not selected* for the card display,
  though they can exist elsewhere in the data model.

---

## 5. Automated / scheduled events

**Selected event types:** Daily bonus drops · Seasonal world events · Random in-channel events
- Daily: random item or currency drop in a designated channel.
- Seasonal: month-long events with special maps, bosses, or limited rewards.
- Random pop-up: "a treasure chest appears — first to react wins" style surprises.
- *Weekly auto-tournaments not selected* — tournaments can be manually scheduled.

---

## 6. External integrations

**Selected (all four):** Twitch stream alerts · YouTube video alerts · Spotify / Last.fm · Steam / gaming APIs
- Twitch: announce when a server member goes live.
- YouTube: post when a tracked channel uploads.
- Spotify / Last.fm: show what a user is listening to; music-themed commands.
- Steam: show player status, achievements, or recent games.

---

## 7. Moderation / server management

**Selected:** Anti-spam/abuse detection · Scheduled announcements
- Smarter rate-limiting or AI-based detection of abusive bot usage.
- Bot posts recurring announcements or reminders on a cron-like schedule.
- *Auto-role on game rank and per-channel game restrictions were not selected.*

---

## 8. UX

### Mobile-first
**Selected:** Very — most users are on mobile.
Prioritise short embeds, large buttons, minimal required typing. Desktop
power-user features are secondary, not a reason to use long forms or small UI.

---

## 9. Architecture notes (from answers)

- **Multi-tenant:** The bot is already fully multi-tenant. New features must
  continue to scope data per-server. No single-server assumptions.
- **Idle game:** Extend the existing mining/exploration system; do not create a
  parallel idle economy.
- **Profile card:** Two fields only (economy stats, guild rank) — keep it tight.
  Resist scope-creep from adding every stat.

---

## Routing summary (state: `captured → needs routing`)

| Idea | Rough size | Risk | Suggested next step |
|---|---|---|---|
| Poker — multi-player table | L | Medium (game logic, concurrency) | `docs/planning/` plan |
| Idle hybrid (extend mining) | M | Low | Quick-win or plan |
| Item marketplace | L | Medium (economy balance) | `docs/planning/` plan |
| Streak rewards | S | Low | Quick-win candidate |
| Guilds + guild battles | XL | High (cross-server data, balancing) | Plan + router discussion |
| Achievement system | M | Low | Quick-win / plan |
| Profile cards (economy + guild) | S | Low | Quick-win candidate |
| AI dungeon master | XL | High (LLM cost, persistence) | Router discussion (Q-block) |
| AI-generated events (all 4 styles) | L | Medium | Plan |
| NL commands — wider intent coverage | M | Medium | Plan (AI stage work) |
| Daily bonus drops | S | Low | Quick-win candidate |
| Seasonal world events | L | Medium | Plan + roadmap horizon |
| Random pop-up events | S | Low | Quick-win candidate |
| External integrations (4x) | M each | Low | Separate plan per integration |
| Anti-spam / abuse detection | M | Medium | Plan |
| Scheduled announcements | S | Low | Quick-win candidate |
| Mobile-first UX audit | S | Low | Groom into existing UI work |

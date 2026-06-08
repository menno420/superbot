# Owner vision — ideas capture (2026-06-08)

> **Status:** `captured` (raw → captured). Nothing here is approved for implementation.
> Source: two interactive Q&A rounds with the maintainer on 2026-06-08 (36 questions total).
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

---

## Round 2 — extended Q&A (2026-06-08, same session)

### 10. Existing game improvements

**Blackjack:** Side bets and variants (insurance, double-down, split, house-rule variants).
- *Spectator mode, RPS tournament, and quick-rematch not selected for now.*

### 11. BTD6 integration direction

**Selected:** More game-mode rules/trivia · Challenge generator · Score/run tracking
- Expand the rules database; add a BTD6 trivia command.
- Bot generates random BTD6 challenge configs (map, mode, tower restrictions).
- Players log their runs; bot tracks personal bests and leaderboards.
- *BTD6 tip-of-the-day not selected.*

### 12. New user onboarding

**Selected:** Starter currency/starter pack · Interactive onboarding flow
- New users automatically receive a small amount of currency + a starter item.
- Bot walks the user through a short interactive setup (pick a title, join/create a guild, etc.).
- *Welcome DM with guide and "keep it minimal" were not selected.*

### 13. Premium / VIP tiers

**Selected:** Both in-game earned AND donation (Patreon/cosmetic) tiers
- **In-game VIP:** unlocked by reaching milestones, no real money required.
- **Donation VIP:** real-money supporters get cosmetic perks only, no gameplay advantage.
- Two separate tracks that can stack.

### 14. Leaderboards

**Selected:** All-time global per game · Weekly/monthly resets · Guild leaderboard
- Permanent all-time leaderboard for each game.
- Resetting weekly/monthly boards to keep competition fresh alongside the all-time board.
- Guild-aggregate leaderboard ranking guilds by total points.
- *Friends/mutual leaderboard not selected.*

### 15. Economy inflation handling

**Selected:** Coin sinks (things to spend currency on) · "Let it inflate — number go up is fun"
- Regular cosmetics, lottery tickets, and upgrades drain excess currency passively.
- Don't fight inflation aggressively; big numbers feel rewarding. Scale rewards to match.
- *Tax on transactions and currency seasons/resets not selected.*

### 16. Bot personality

**Selected:** Funny / sarcastic
- Dry wit, occasional roasts, jokes when a player loses a game.
- Consistent across all commands — not just in game results.

### 17. Voice channel features

**Selected:** Music playback · Sound effects on game events · Voice-based game commands
- Play YouTube/Spotify tracks in voice channels.
- Short sounds on wins, losses, rare events.
- Voice speech recognition to trigger commands.
- *"No voice features" explicitly rejected.*

### 18. Command discoverability

**Selected:** Rich /help with categories · What's new changelog
- Paginated `/help` organized by category (games, economy, social, etc.).
- `/changelog` or auto-post to a #updates channel on each feature ship.
- *Contextual hints and tutorial quest-line not selected.*

### 19. Admin analytics / owner tools

**Selected (all four):** Usage stats per command · Economy health dashboard · Active user funnel · Error/abuse log
- Per-command usage frequency, by user, over time.
- Economy dashboard: total currency in circulation, top earners, marketplace volume.
- User funnel: new users who try the bot vs. become regulars.
- Error/abuse log: recent errors, rate-limit hits, flagged attempts.

### 20. Mining depth improvements

**Selected (all four):** Boss encounters · Deeper floors with rarer loot · Mining events · Co-op mining parties
- Rare powerful boss enemies requiring strategy or multiple players.
- Deeper floors = harder difficulty + better drop scaling.
- Random hazard events (cave-ins, floods) you must react to.
- 2–4 player mining parties with bonus rewards.

### 21. External website / dashboard

**Selected:** Full web dashboard
- A web UI where server owners configure the bot and players view profiles/leaderboards.
- This is a significant infrastructure investment — route to a planning doc + roadmap.

### 22. Notifications

**Selected (all four):** DM opt-in · Dedicated #bot-alerts channel · In-game inbox/mailbox · Embeds with CTAs
- Players opt in to DMs for: guild attacks incoming, streak about to break, rare drops.
- A #bot-alerts channel for server-wide time-sensitive posts.
- `/mail` in-game inbox: bot stores messages; player reads them on next login.
- Every alert ends with a button or command so the player knows what to do next.

### 23. Crafting (future, lower priority)

**Selected style:** Blueprint drops — rare recipes as loot
- Blueprints drop from mining/events; you can only craft what you've found.
- No auto-discover recipes; rarity gives blueprints value in the marketplace.

### 24. Balance change communication

**Selected:** In-game notice + changelog
- Post a #changelog note **and** show a small badge/tip the next time affected commands are used.

### 25. One-year regret test

**Selected:** AI dungeon master
> "The most creative, differentiating feature — nothing else in Discord bots does this well."
This is the owner's single highest-regret-if-missing feature. **It should sit high on
the long-term roadmap even though it is the most complex.**

---

## Updated routing summary (all 36 questions)

| Idea | Rough size | Risk | Suggested next step |
|---|---|---|---|
| Poker — multi-player table | L | Medium | `docs/planning/` plan |
| Blackjack side bets / variants | M | Low | Quick-win / plan |
| Idle hybrid (extend mining) | M | Low | Quick-win or plan |
| Item marketplace | L | Medium | `docs/planning/` plan |
| Streak rewards | S | Low | Quick-win candidate |
| Guilds + guild battles | XL | High | Plan + router discussion |
| Achievement system | M | Low | Quick-win / plan |
| Profile cards (economy + guild) | S | Low | Quick-win candidate |
| **AI dungeon master** ⭐ | XL | High | Router Q-block (owner #1 regret) |
| AI-generated events (all 4 styles) | L | Medium | Plan |
| NL commands — wider intent | M | Medium | Plan (AI stage) |
| Daily bonus drops | S | Low | Quick-win candidate |
| Seasonal world events | L | Medium | Plan + roadmap horizon |
| Random pop-up events | S | Low | Quick-win candidate |
| External integrations (4×) | M each | Low | Separate plan per integration |
| Anti-spam / abuse detection | M | Medium | Plan |
| Scheduled announcements | S | Low | Quick-win candidate |
| Mobile-first UX audit | S | Low | Groom into existing UI work |
| BTD6: rules/trivia + challenge gen + score tracking | M | Low | Quick-win / plan |
| New user onboarding (starter pack + flow) | M | Low | Plan |
| VIP tiers (in-game + donation) | L | Medium | Plan + router discussion |
| Leaderboards (all-time + weekly + guild) | M | Low | Plan |
| Economy coin sinks | M | Low | Groom into economy work |
| Funny/sarcastic bot personality | S | Low | Quick-win (tone/copy pass) |
| Voice: music + SFX + speech commands | L | Medium | Plan (separate from main bot) |
| Rich /help + changelog | S | Low | Quick-win candidate |
| Admin analytics dashboard | L | Medium | Plan |
| Mining: bosses + floors + events + co-op | L | Medium | Plan (extends mining subsystem) |
| Full web dashboard | XL | High | Router Q-block (infra investment) |
| Notifications (DM + channel + inbox + CTAs) | M | Low | Plan |
| Blueprint-drop crafting (future) | M | Low | Roadmap: Later horizon |
| Balance change: in-game notice + changelog | S | Low | Quick-win candidate |

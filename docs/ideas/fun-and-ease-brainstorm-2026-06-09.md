# Fun & ease-of-use brainstorm — ideas capture (2026-06-09)

> **Status:** `ideas` (captured — not approved for implementation).
> Source: a brainstorming session with the maintainer on 2026-06-09 ("see what exists,
> see what's already captured, then come up with *more*"). Every idea below was
> **dedup-verified against docs *and* source** before capture (see §1). Route each idea
> through the lifecycle in [`README.md`](./README.md) before implementing.
> Owner cluster picks from the same session are recorded in §2 and in the router
> (**Q-0053**); the ⭐ marks below are *his* reactions, not agent ranking.

---

## 1. Dedup check — what this capture does NOT repeat

This brainstorm is **additive** to the existing idea space. Checked against:
[`owner-vision-ideas-2026-06-08.md`](./owner-vision-ideas-2026-06-08.md) (36-question
capture), the four product-growth roadmap drafts (social / economy / games-idle / UX),
[`future-product-direction-2026-06-07.md`](./future-product-direction-2026-06-07.md),
[`mining_exploration_brainstorm.md`](./mining_exploration_brainstorm.md),
[`cog-improvement-audit-2026-06-08.md`](./cog-improvement-audit-2026-06-08.md), the
ideas-lab rejection ledger (§6, binding), and `grep` over `disbot/` + `docs/`.

Candidate ideas **dropped because they already exist or are already captured**:

| Dropped idea | Where it already lives |
|---|---|
| "Did you mean?" typo correction | **Shipped** — `disbot/utils/command_resolution.py` (auto-run + suggest, destructive-command guard) |
| PvP coin-stake challenges | **Shipped** — RPS Bet Match / blackjack Solo Bet + PvP (`views/games/rps_panel.py`, `views/games/blackjack_panel.py`) |
| Gifting / player-to-player transfer | Captured — mining brainstorm §"Trading & market" + cog-audit Gap 2 |
| Prestige / rebirth loop | Captured — mining brainstorm ("Prestige + leaderboard and a capped skill tree") |
| Member onboarding flow / starter pack | Captured — owner-vision §12 |
| Daily login rewards, streaks, lottery | Shipped (`!daily` streaks) / captured (owner-vision §2b) |
| General trivia / jokes / 8-ball | Shipped — `general_cog` |
| Admin digest / notification profiles | Captured — future-product-direction "Notification subscription profiles" |

None of the ideas below conflicts with the binding rejection ledger (no Redis, no
restart-safe game sessions, no second panel framework, no per-sub-action slash
commands, no AI write tools).

---

## 2. Owner reactions (2026-06-09, recorded — see router Q-0053)

Asked which clusters resonate most, the maintainer picked:

- **Fun: A1 Pets & companions** ⭐ — structured the same session into
  [`../planning/pets-companions-plan-2026-06-09.md`](../planning/pets-companions-plan-2026-06-09.md)
  (state: `structured`, horizon: Later on `docs/roadmap.md`).
- **Ease: C1 context-menu actions** ⭐ **and C4 persistent reminders** ⭐ — marked
  top quick-win candidates (small, decided-lane; good next-session picks).
- Session scope chosen: capture everything + structure the pets cluster (no feature
  code that session).

---

## 3. Catalog A — social & competition layer

The owner's stated #1 ("more social — players interacting with each other",
owner-vision §4a). **Every idea here is single-guild scoped on purpose** — none waits
on the open guild/clan tenancy question (Q-0038).

### A1. Pet companions 🐾 ⭐ *(structured → plan)*
Rare eggs drop from mining/exploration → hatch into nameable pets that appear on the
`!character` card. Feeding/care is a **recurring coin/ore sink** (the economy wants
sinks — owner-vision §15); perks stay tiny and flavor-first (≤1–2%, e.g. explore luck)
to keep the no-pay-to-win line. Later: pet showcase in Spotlight, marketplace
tradability once the captured marketplace lands.
**Seams:** mining drop tables (`cogs/mining/`), audited `economy_service` for coins,
inventory owner for ore, `utils/equipment.py` `EffectiveStats` composition for any
stat-touching perk, character panel (#610), Spotlight EventBus feed (#613).
**Size M-L · Risk low-med (balance) · Route:** structured —
[`../planning/pets-companions-plan-2026-06-09.md`](../planning/pets-companions-plan-2026-06-09.md).

### A2. Server goals & celebrations 🎯 (+ server mascot variant)
A weekly server-wide collective target ("the server mines 10,000 ore / wins 500
games") with a live progress bar in Community Spotlight; completion fires a
celebration embed + a temporary server-wide perk (e.g. +10% daily bonus weekend) and a
contributors shoutout. Charming variant: a **shared server mascot** — one tamagotchi
per guild that members feed (coin sink) and that levels/mood-shifts with collective
activity, rendered in Spotlight. Generalizes the mining brainstorm's one-line
"server-wide goals" social scope to the whole bot.
**Seams:** Spotlight (#613) + the EventBus events already emitted (`xp.awarded`,
`economy.balance_changed`, game results), `economy_service` for perk payouts.
**Size M · Risk low · Route:** plan when picked up (games/social lane).

### A3. Bounty board 💰
Players escrow a coin bounty ("first to beat me at RPS: 500 coins", "first to reach
depth 4 this week"); claims verified from game-result events, paid from escrow. A
bounty panel lists open bounties — instant PvP motivation between any two members.
**Seams:** economy escrow (the RPS Bet Match debit-at-start precedent), EventBus game
results, a small direct-lane bounty table.
**Size M · Risk med (verification/abuse review needed) · Route:** plan (economy+games).

### A4. Rivalries — head-to-head records ⚔️
Per-pair W/L records across games. Challenge embeds gain one line ("Bob leads 5–2 —
revenge time?"); a "rival of the week" line in Spotlight. Concretizes the mining
brainstorm's "head-to-head (PvP)" scope marker cross-game. Cheap, durable social glue
on top of results the bot already stores.
**Seams:** existing per-game result/leaderboard storage, challenge flows, Spotlight.
**Size S-M · Risk low · Route:** quick-win candidate (read-model + one embed line).

### A5. King of the Hill titles 👑
One transferable champion title per game ("Blackjack King"). Beat the current holder
in a direct challenge to take it. Holder shows in Spotlight and on their profile;
optionally a cosmetic role via the existing role-automation seam.
**Seams:** game results, role automation, Spotlight, character/profile card.
**Size S · Risk low · Route:** quick-win candidate.

### A6. Predictions / betting pools 🔮
Twitch-style predictions: a host opens "Who wins tonight's RPS tournament?", members
stake coins on outcomes, the pot splits among winners. Coins-only, tournament-anchored
first. `docs/architecture.md` already anticipates exactly this shape (matchmaking /
limited-quantity drops via scope locks).
**Seams:** tournaments (RPS/BJ), economy escrow, scope-lock transient registries.
**Size M · Risk med · Route:** **must ride the economy roadmap's chance-reward /
lottery legality review** (same gate as owner-vision §2b lottery tickets) — not before.

### A7. LFG / party board 📯
"Looking for players" slots: post a game + time + party size, others tap **Join**,
auto-ping when full. Generalizes the captured mining co-op parties and BTD6 co-op into
one reusable surface.
**Seams:** scope-lock transient-registry pattern (architecture §state-registry),
games hub, notifications-CTA convention (owner-vision §22).
**Size S-M · Risk low · Route:** plan (one bounded slice; reusable across games).

---

## 4. Catalog B — ambient fun & delight (the server feels alive daily)

### B1. Starboard / Hall of Fame ⭐(the emoji, not an owner pick)
N star-reactions on any message → immortalized in #hall-of-fame with a jump link;
optional small XP bonus to the author. The classic zero-typing community-memory
feature; SuperBot has the raw-reaction handling precedent in reaction roles.
**Size S-M · Risk low (dedupe + self-star rules) · Route:** quick-win / plan.

### B2. Quote board 💬
Save a member's message as a server quote — ideally via right-click → "Save Quote"
(see C1) — then `!quotes` random recall and a quote-of-the-day that can ride B4's
seam. Distinct from the existing `!quote` (famous quotes).
**Size S-M · Risk low (author opt-out posture) · Route:** quick-win / plan, pairs with C1.

### B3. Birthdays & cakedays 🎂
Opt-in birthday (day + month only — deliberately no year, privacy-light): celebration
embed + small coin gift + a 24h cosmetic role. Join-anniversary ("cakeday") shoutouts
come free from member data the bot already has.
**Seams:** role automation (temp role), economy (gift), a tiny opt-in table + daily tick.
**Size S-M · Risk low · Route:** quick-win candidate.

### B4. Question of the day ❓
A daily auto-posted conversation starter / would-you-rather / this-or-that in a
configured channel, with reaction voting. Zero game mechanics — pure social glue —
and the content pack is a natural home for the captured funny/sarcastic personality
(owner-vision §16).
**Seams:** the captured scheduled-announcements seam (owner-vision §7).
**Size S · Risk low · Route:** quick-win candidate.

### B5. Daily word game 🟩
Wordle-style shared daily word per server: guess via button + modal (mobile-friendly,
no typing in-channel), per-player streaks, and a new leaderboard category — the
leaderboard provider system is extensible by design. A third ambient channel game
beside counting and chain.
**Size M · Risk low · Route:** plan (games lane).

### B6. Treasure hunts 🗺️
A rare "treasure map" drop from mining/explore starts a 3-step riddle whose clues
point at bot features ("check the counting channel", "visit depth 2"); the finder
gets a chest (coins + a captured-idea collectible). Teaches the bot's surface area
while playing.
**Size M · Risk low-med · Route:** plan (games lane; pairs with captured collectibles).

### B7. Today's deals — rotating shop stock 🛒
The shop and mining market gain 2–3 **date-seeded** rotating featured items (small
discount or limited stock). Deterministic (seeded by date+guild), so no new state —
and it gives players a reason to peek in daily alongside `!daily`.
**Seams:** shop catalogue, mining market (#609 — static catalogues today).
**Size S · Risk low · Route:** quick-win candidate.

### B8. Seasonal theming 🎃
Month-aware embed accent colors/emoji via one shared styling helper (October spooky,
December festive). The cheap deterministic sibling of the captured seasonal world
events (owner-vision §5) — delight without event mechanics.
**Size S · Risk low · Route:** quick-win candidate (one helper + adoption).

### B9. Easter-egg reaction pack 🥚
Generalize the existing `four_twenty_cog` listener pattern into a small curated
trigger → rare reaction/reply pack (per-guild toggle, cooldowns), written in the
captured sarcastic voice. Rare on purpose — surprise is the point.
**Size S · Risk low (rate-limit care) · Route:** quick-win candidate.

### B10. Daily contracts 📜
2–3 deterministic daily tasks ("win 2 blackjack hands", "mine 50 stone", "post a
valid count") with coin rewards + a weekly mega-contract. The **non-AI sibling** of
the captured AI procedural quests — shippable now, no LLM cost — and it feeds the
captured streak system and C2's claim-all hub.
**Seams:** game-result events, economy, daily-reset pattern from `!daily`.
**Size M · Risk low-med (reward balance) · Route:** plan (economy/games lane).

---

## 5. Catalog C — easier to use (members; mobile-first per owner-vision §8)

### C1. Context-menu actions 📱 ⭐ *(owner ease pick)*
The bot's **first** right-click / long-press commands: user → View Profile / View
Rank / Challenge…; message → Save Quote (B2) / Pin to Hall of Fame (B1). Zero typing,
ephemeral responses, and **long-press is native on mobile** — the single biggest
mobile-first win available. The bot has zero `context_menu` registrations today;
discord.py supports them on the existing slash front-door pattern (they route into
existing panels, so no per-sub-action command sprawl).
**Size S-M · Risk low · Route:** quick-win candidate (start with View Profile + View Rank).

### C2. Claim-all daily hub ✅
One panel that shows everything claimable — daily reward, work cooldown, contracts
(B10), streak status, today's deals (B7) — each with a claim button, plus a "you have
3 things to claim" nudge on `!daily`. Pure composition over existing owners; each
claim still goes through its own service.
**Size S-M · Risk low · Route:** quick-win / plan (grows as B7/B10 land).

### C3. `!play` quick-launcher 🚀
Personal recents/favorites: one panel with your last 3 games as instant-launch
buttons + a "surprise me" button. One tap from "I'm bored" to playing.
**Size S · Risk low · Route:** quick-win candidate.

### C4. Persistent reminders ⏰ ⭐ *(owner ease pick)*
`!remind` is **in-memory today and silently loses every reminder on restart**
(verified in `cogs/utility` — the cog even says so). Persist reminders to a small
table and deliver on schedule. Distinct from the captured admin scheduled
announcements (owner-vision §7) — this is the member-facing utility.
**Size S-M · Risk low · Route:** quick-win candidate (root-causes a real silent-loss bug).

### C5. Mining hub discoverability ⛏️
~15 functional mining commands are hidden / prefix-only (`!build`, `!buildlist`,
`!use`, `!equip`, `!unequip`, `!minestats`…) and invisible in Help. Surface them as
buttons/selects on the existing mining hub (Build menu, Use-item select, Gear panel) —
the Wave-1 hub buttons (Descend/Market/Character) are the exact precedent.
**Size S · Risk low · Route:** quick-win in the **active mining lane** (fold into the
next Wave-1 slice or take standalone).

### C6. Member "what works here?" guide 🧭
A member-facing sibling of the staff Access Map: one ephemeral "what can I do in this
channel?" answer (which features respond here, where the others live). Reuses the
shipped `services/access_projection.py` (P1A) read model and must follow the
locked-reason copy posture (Q-0036).
**Size S-M · Risk low · Route — UNBLOCKED 2026-06-10 (groomed):** its stated gate
("after P1C ships its staff surfaces") cleared — P1C shipped the staff Access Map +
Help Preview in **#656**, and the Batch 6 Help projection seam (**#657**) added the
exact read path this idea needs: `services/help_projection.project_help_with_execution`
already buckets every feature into shown / routed-off / command-locked / hidden with
user-safe reason codes (`LockedReason.safe_text` only — the Q-0036 posture is built
into the model). Remaining design surface is genuinely small: entry point (a member
command like `!whatworks` vs a Help-Home button), and whether hidden features are
listed at all for members (recommend: no — show allowed + locked-with-reason only,
matching the not-found posture the seam shipped). **Next destination:** a small slice
in the Adaptive Setup/Access lane after P2, or a standalone quick-win PR once the
maintainer picks the entry point. Still requires the Q-0036 denial-copy wiring state
to be respected (copy is live in `_SAFE_TEXT` but the *denial-path* wiring awaits the
maintainer's #632 markup — this read-only surface may consume the safe text directly).

### C7. Slash autocomplete arguments ⌨️
Autocomplete for item/game/category names on the existing slash front doors (shop
items, game pickers) so phone users never type exact names. Bounded: front doors
only — no per-sub-action commands (rejection ledger).
**Size S per surface · Risk low · Route:** groom into the interface-completion lane.

---

## 6. Routing summary (state ledger)

| # | Idea | Size | Risk | Owner ⭐ | State → next destination |
|---|---|---|---|---|---|
| A1 | Pet companions | M-L | low-med | ⭐ fun pick | **structured** → [`pets-companions-plan-2026-06-09.md`](../planning/pets-companions-plan-2026-06-09.md) + roadmap Later (games) |
| A2 | Server goals & mascot | M | low | | captured → plan candidate (games/social) |
| A3 | Bounty board | M | med | | captured → plan + abuse review |
| A4 | Rivalries (head-to-head) | S-M | low | | captured → quick-win candidate |
| A5 | King of the Hill titles | S | low | | captured → quick-win candidate |
| A6 | Predictions / betting pools | M | med | | captured → **gated**: economy chance-reward review (with lottery) |
| A7 | LFG / party board | S-M | low | | captured → plan (reusable surface) |
| B1 | Starboard / Hall of Fame | S-M | low | | captured → quick-win / plan |
| B2 | Quote board | S-M | low | | captured → quick-win (pairs with C1) |
| B3 | Birthdays & cakedays | S-M | low | | captured → quick-win candidate |
| B4 | Question of the day | S | low | | captured → quick-win candidate |
| B5 | Daily word game | M | low | | captured → plan (games lane) |
| B6 | Treasure hunts | M | low-med | | captured → plan (games lane) |
| B7 | Today's deals (rotating stock) | S | low | | captured → quick-win candidate |
| B8 | Seasonal theming | S | low | | captured → quick-win candidate |
| B9 | Easter-egg reaction pack | S | low | | captured → quick-win candidate |
| B10 | Daily contracts | M | low-med | | captured → plan (economy/games) |
| C1 | Context-menu actions | S-M | low | ⭐ ease pick | captured → **top quick-win candidate** (next session) |
| C2 | Claim-all daily hub | S-M | low | | captured → quick-win / plan |
| C3 | `!play` quick-launcher | S | low | | captured → quick-win candidate |
| C4 | Persistent reminders | S-M | low | ⭐ ease pick | captured → **top quick-win candidate** (silent-loss fix) |
| C5 | Mining hub discoverability | S | low | | captured → quick-win (active mining lane) |
| C6 | "What works here?" guide | S-M | low | | **unblocked 2026-06-10** (P1C #656 + Help seam #657 supply the read path) → small Adaptive-lane slice or standalone quick-win; entry-point pick is the only open question |
| C7 | Slash autocomplete | S | low | | captured → groom into interface lane |

**No-orphan guarantee:** every row has a state and a next destination. Grooming
sessions (the standing secondary task) should pull from the ⭐ rows first, then the
quick-win column.

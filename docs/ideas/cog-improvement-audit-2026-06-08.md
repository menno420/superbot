# Cog improvement audit (2026-06-08)

> **Status:** `ideas` — captured from interactive Q&A with the maintainer.
> Nothing here is approved for implementation. Source: 36-question cog-by-cog
> review session on 2026-06-08.
> Route each item through `docs/ideas/README.md` before acting on it.

---

## Owner's stated top priority

> **"Fix setup wizard first"** — about half the steps have nothing actionable
> yet; the wizard is too long and loses people. This should become a priority.

---

## Game cogs

### Blackjack (`blackjack_cog.py`)
- **Gap:** No personal stats or history (win rate, biggest win, hands played).
- Side bets / variants (previously selected as desired) are not yet built.

### RPS tournament (`rps_tournament_cog.py`)
- **Architectural gap:** Tournament logic is currently tightly coupled to the
  cog. It should be extracted into a **standalone service / feature** that
  multiple cogs can use — not owned by any single cog.
- This is a refactor prerequisite before expanding tournament support to other
  games.

### Deathmatch (`deathmatch_cog.py`)
- **State:** Underused and feels incomplete. The mechanic works but lacks
  depth — limited moves, no items, no variety.
- **Action:** Flesh out the game mechanics before promoting it.

### Counting (`counting_cog.py`)
- **Gap 1:** No economy tie-in or rewards when milestones are hit.
- **Gap 2 (UX):** Per-channel settings can only be changed from within the
  channel you want to configure. The counting menu should let you select/change
  *any* channel's settings from anywhere.

### Games hub (`games_cog.py`)
- **State:** Works as a hub but is too bare — just a list, no per-game stats or
  context. Needs basic stats per game (active players, recent wins, etc.).

---

## Economy cogs

### Economy (`economy_cog.py`)
- **State:** Core commands (balance, pay, earn) are solid. No major gaps
  reported — foundation is healthy.

### Inventory (`inventory_cog.py`)
- **Gap 1:** Items sit in inventory but cannot be used or equipped.
- **Gap 2:** No player-to-player item transfer (gift, trade, drop).
- Both gaps are prerequisites for the marketplace feature (see
  `owner-vision-ideas-2026-06-08.md`).

### XP (`xp_cog.py`)
- **State:** Works and is visible to players. No urgent gaps reported.

### Leaderboard (`leaderboard_cog.py`)
- **Gap:** Leaderboards are not auto-posted or announced. Need periodic
  automated posting to a configured channel (weekly summary, etc.).

---

## Mining cogs (`mining_cog.py`, `mining/`)

> **All mining work is actively in progress — a plan already exists.**
> Do not interrupt the in-flight work. The items below are captured for
> post-plan reference only.

- Core loop: in progress.
- Exploration system: in progress.
- Recipes / crafting: in progress.
- Items: in progress.

**Owner's preferred crafting style** (from previous session): blueprint-drop
style — rare recipes as loot, not auto-discoverable.

---

## BTD6 cogs

### BTD6 main (`btd6_cog.py`)
- **State:** Hub works well. No urgent gaps.

### BTD6 events (`btd6_events_cog.py`)
- **Gap:** Embed quality needs improvement — embeds look dated or are hard to
  read.

### BTD6 strategy + ops (`btd6_strategy_cog.py`, `btd6_ops_cog.py`)
- **Gap:** Strategy content needs more entries. Ops commands are fine but
  strategy database is thin.

### BTD6 reference (`btd6_reference_cog.py`)
- No gaps reported.

### Paragon (`paragon_cog.py`)
- **State:** Works and is actively used. No urgent gaps.

---

## Server management cogs

### Admin (`admin_cog.py`)
- **Gap:** Missing bulk-action commands (mass role assign, mass purge, etc.).

### Settings (`settings_cog.py`)
- **Gap:** Some settings exist in the panel but have no visible effect in the
  bot (e.g. they're wired to nothing yet). These create confusion — settings
  that do nothing should either be implemented or hidden until ready.

### Setup (`setup_cog.py`) ⭐ TOP PRIORITY
- **Gap 1:** The wizard is too long and loses users halfway through.
- **Gap 2:** About **half the steps have nothing actionable yet** — they walk
  through setup flows that don't actually configure anything in the bot.
- **Owner direction:** Strip out the non-functional steps; only show steps
  whose configuration actually takes effect. Make the wizard shorter and
  trustworthy.

### Logging (`logging_cog.py`)
- **Gap:** Log channel routing (which event types go to which channel) is hard
  to configure. Needs a clearer UI for routing rules.

### Server management (`server_management_cog.py`)
- **State:** Solid. No gaps reported.

### Bootstrap access (`bootstrap_access_cog.py`)
- **State:** Works fine for first-time owner access setup.

---

## Community / social cogs

### AI (`ai_cog.py`) — multiple gaps
- **Gap 1 (settings UX):** Settings and routing are not easy to configure.
  Some settings appear to have no effect at all (e.g. custom instructions,
  default model selection).
- **Gap 2 (input method):** Still using an outdated input method for some
  actions — users must type their preferred setting instead of selecting it
  from a dropdown or button. Should be modernized to Discord select menus /
  buttons throughout.
- **Gap 3 (effectiveness):** Confirmed from previous session — intent coverage
  is too narrow; minor rewording breaks command recognition.

### Community (`community_cog.py`)
- **Gap:** No giveaway or raffle command. (Polls also missing per previous
  session; giveaway/raffle is the next most requested.)

### Chain (`chain_cog.py`)
- **State:** Currently does not do anything meaningful.
- **Owner direction:** Should be **reworked into something fun and usable** —
  the current implementation is effectively dead. Candidate for a redesign
  discussion before any build work.

### General (`general_cog.py`)
- **State:** Rarely used / low value. Commands exist but players don't
  reach for them.
- No specific gap flagged — low priority.

---

## Support / utility cogs

### Moderation (`moderation_cog.py`)
- **State:** Core commands (warn, mute, kick, ban) are solid. No urgent gaps
  reported.

### Role (`role_cog.py`)
- **Gap:** A list of **hardcoded role names** still exists and should be
  removed. It should be replaced by the **option role preset** system that
  already exists — but the preset system itself needs to be revised and
  improved before the hardcoded list is dropped.

### Help (`help_cog.py`)
- **State:** Pretty advanced.
- **Gap:** Needs **better customization** (unspecified — candidate for a
  follow-up Q to clarify what "customization" means here: per-server command
  hiding? custom descriptions? visibility toggles?).

### Utility (`utility_cog.py`)
- **State:** Commands feel **outdated** and should be reworked. No specific
  commands flagged — the whole cog needs a refresh pass.

### Cleanup (`cleanup_cog.py`)
- **State:** Core bulk-delete works.
- **Gap:** Lacks customization (e.g. delete only bot messages, only images,
  only messages from a specific user).

### Diagnostic (`diagnostic_cog.py`)
- **State:** Clear and useful. No urgent gaps.

### Proof channel (`proof_channel_cog.py`)
- **State:** Barely used and disconnected from a real workflow. No active
  integration with rewards or role assignment.
- Low priority until a proof-submission workflow is defined.

### Channel (`channel_cog.py`)
- **State:** Core commands work. No urgent gaps reported.

### Four twenty (`four_twenty_cog.py`)
- **State:** Works but needs more depth — currently a single-purpose announce
  with no customization or interactivity.

---

## Routing summary

| Cog / area | Issue | Size | Priority | Suggested next step |
|---|---|---|---|---|
| **Setup wizard** | Half the steps do nothing; too long | M | **P0 — top priority** | Plan: strip non-functional steps, shorten flow |
| **AI cog settings** | Settings have no effect; typed input instead of select menus | M | High | Plan: settings panel overhaul |
| **RPS tournament** | Logic coupled to cog; should be a standalone service | M | High | Plan: extract to service layer |
| Blackjack | No personal stats / history | S | Medium | Quick-win candidate |
| Counting | No economy tie-in; settings only configurable in-channel | S | Medium | Quick-win candidate |
| Inventory | Items unusable; no transfer | M | Medium | Prerequisite for marketplace |
| Leaderboard | Not auto-posted | S | Medium | Quick-win candidate |
| Settings cog | Settings that do nothing | S | Medium | Groom: hide or implement stub settings |
| Role cog | Hardcoded names; preset needs revision | M | Medium | Plan: revise preset system |
| Logging | Routing config hard to use | M | Medium | Plan: routing UI |
| Chain cog | Does nothing; needs redesign | M | Low–Medium | Router Q-block: what should it become? |
| Utility cog | Outdated commands | M | Low–Medium | Plan: full rework pass |
| Help cog | Needs better customization | S | Low–Medium | Follow-up Q: what kind of customization? |
| BTD6 events | Embed quality | S | Low | Quick-win candidate |
| BTD6 strategy | Needs more content | S | Low | Content addition |
| Deathmatch | Incomplete / lacks depth | M | Low | Plan: game mechanic expansion |
| Games hub | Too bare | S | Low | Quick-win: add per-game stats |
| Community | No giveaway/raffle | S | Low | Quick-win candidate |
| Admin | Missing bulk actions | M | Low | Plan |
| Cleanup | Lacks granularity | S | Low | Quick-win candidate |
| Four twenty | Needs more depth | S | Low | Idea: what "depth" means here |
| Proof channel | Disconnected | M | Low | Needs workflow definition first |
| Mining | All in progress | — | In-flight | Follow existing plan |

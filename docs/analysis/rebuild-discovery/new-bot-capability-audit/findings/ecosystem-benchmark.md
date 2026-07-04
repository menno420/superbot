# Lane F — Ecosystem benchmark (Axis 3): known-Discord-bot capability gaps + outperform targets

> **Status:** `audit` — the Axis-3 lane of the new-bot capability audit: what the known Discord-bot ecosystem
> does that SuperBot doesn't, and the per-capability **outperform target** the other six lanes deferred as
> `pending Lane F`.
> **Provenance:** external deep-research (owner-provided, 2026-07-02) **verified and corrected against shipped
> source by Opus 4.8** (Q-0120). The competitor catalog is the deep-research contribution; the SuperBot-status
> column and every correction are source-checked against the 43-subsystem ground truth + `disbot/` source.
> **Prepared:** 2026-07-02.

## ⚠ Corrections applied to the raw research (Q-0120 — read this first)

The raw Lane F deep-research **misread SuperBot's own surface**, repeatedly flagging **already-shipped
subsystems as missing "gaps."** The collaboration model requires cross-agent output be verified against
shipped source before it feeds the capstone; here is what changed and why. **The capstone must use the
corrected column, not the raw research's gap list.**

| Raw Lane F claim | Verified source reality | Corrected verdict |
|---|---|---|
| **Ticketing** is the #1 missing "strong-fit addition" | `ticket` subsystem — `ticket new/close/claim/add/remove`, `ticketpanel`, `ticketsetup`, `ticketlimit`, `ticketblacklist`; `services/ticket_service.py` + `ticket_mutation.py`; `views/tickets/{hub,config_panel,control,launcher,confirm}.py`; `utils/db/tickets.py` | **Already shipped.** Not a build — a *benchmark* target vs Ticket Tool. |
| **Advanced reaction roles** are a missing "strong-fit addition" | `role` subsystem — `views/roles/reaction_panel.py`, `role_menu_builder.py`, `role_menu_view.py`, `_role_pack_flow.py`, `main_panel.py` | **Already shipped** (menus + reaction panel + role packs). Benchmark vs Carl-bot UX. |
| **"No typical gambling/spins"** in games | `casino` subsystem — `cogs/casino_cog.py`, `views/casino/poker_table.py`, `hub.py`; gambling mechanics present | **Wrong.** Casino/poker ships; plus blackjack, deathmatch, rps_tournament. |
| **Welcome is "probably text only"** | `services/welcome_service.py` renders a `welcome_card` (image) | **Wrong.** Image welcome cards ship. |
| **"No polling_cog"** | `poll` implemented in `utility` (`cogs/utility_cog.py`) | Capability exists (no dedicated cog, but present). |
| **Web config "requires code changes"** | `dashboard/` Flask app — `app.py`, `auth.py`, `Procfile` | **Wrong.** A web dashboard exists (and a live-editor plan is in Lane E). |
| **Automod is only "basic"** | `automod` subsystem — `services/automod_service.py` + `automod_config.py` + `cogs/automod/listener.py` + `schemas.py` + `settings_keys/automod.py` | Understated. A real configurable automod subsystem ships. |

**Net effect:** SuperBot's shipped breadth is **wider than the raw research assumed** — it already covers the
mainstream bots' headline specialties (tickets, reaction roles, automod, welcome images, casino, web dashboard)
*and* carries domains **no mainstream bot has** (BTD6, Project Moon, mining/fishing/creature world-games). The
real Axis-3 work is therefore **UX/depth/config parity on features SuperBot already ships**, plus a small set of
**genuine** gaps — not "build the basics competitors have."

## Method & sources

Competitor capabilities were drawn from the owner-provided deep-research (official bot sites/docs/top.gg, with
fan-wikis avoided). The **SuperBot column is ground truth**: the 43-subsystem inventory
(`ground-truth/subsystems.json`), `ground-truth/command-surface.json`, and direct `disbot/` source reads. Every
"already shipped" correction above cites the source path. Competitor specifics that could not be re-verified
from source here are marked ⚠ and should be re-confirmed by the capstone before becoming hard outperform
commitments.

## Competitor capability catalog (who specializes in what)

Most popular bots lead with **one deep specialty** + standard moderation/utility. SuperBot is unusual in being
*broad-and-deep across many domains at once*.

| Bot | Headline specialty | Notable capabilities | Overlaps a SuperBot subsystem? |
|---|---|---|---|
| **MEE6** | Welcome/onboarding, leveling, custom commands | Level roles, reaction roles, automod, web dashboard (much paywalled) | welcome, xp, role, automod |
| **Carl-bot** | Reaction roles (best-in-class UX), automod | Button/dropdown role menus, logging, reminders, feeds, giveaways | role, automod, logging, community |
| **Dyno** | Moderation + web dashboard | Automod filters, modlog, mod actions, custom commands, web module toggles | moderation, automod, logging, admin |
| **YAGPDB** | Modular automod + feeds + self-roles | Grouped self-roles, RSS/reddit/YouTube feeds, custom command scripting | role, automod, community |
| **Ticket Tool** | Support tickets | Threaded/channel tickets, claim, transcripts, close-with-reason | **ticket** |
| **Dank Memer** | Economy game | Currency, gambling minigames, items, shops, memes | economy, casino, games, inventory |
| **Tatsu** | Global economy + social | Universal credits, pets, house/rooms, rank cards, leaderboards | economy, xp, leaderboard, creature |
| **ProBot** | Welcome + logs + levels | Image welcome, in-depth logs (DM/webhook), leveling | welcome, logging, xp |
| **Arcane** | Leveling + analytics | Rank cards, XP analytics, YouTube roles, leaderboards | xp, leaderboard |
| **Mudae** | Anime/character collectables | Gacha collection game (niche) | (unique to Mudae) |
| **Music bots** (Rythm/Groovy/etc.) | Voice/music streaming | Queue, playback | **none** (SuperBot has no voice) |

## Per-domain outperform targets (fills the six lanes' `pending Lane F`)

For each domain: SuperBot's **verified** status, the best-in-class competitor, and the concrete
**outperform/parity target** the capstone folds into that capability's done-definition.

| Domain | SuperBot status (verified) | Best-in-class | Outperform / parity target |
|---|---|---|---|
| **Moderation / automod** | `moderation`, `automod`, `security`, `image_moderation` all ship | Dyno | Match Dyno's filter configurability (badword/invite/caps/spam triggers→actions) via the audited mutation seam; **beat by being free** + fully audited. |
| **Tickets / support** | `ticket` ships (new/close/claim/blacklist/limit/panel) | Ticket Tool | Reach transcript export + thread-mode parity; SuperBot already has claim/blacklist/limits Ticket Tool gates behind premium. |
| **Reaction roles** | `role` ships (menu builder, reaction panel, role packs) | Carl-bot | Match Carl's button/dropdown UX polish + role-hierarchy preflight; SuperBot already has the builder + audit seam. |
| **Welcome / onboarding** | `welcome` ships incl. `welcome_card` image | ProBot / MEE6 | Match ProBot's card customization depth; unify with the visual-card-engine plan (Lane E). |
| **Leveling / XP** | `xp`, `leaderboard`, `karma` ship | Arcane / Tatsu | Add rank-card visuals (visual-card-engine, Lane E) + multi-leaderboard analytics; XP core already ships. |
| **Economy** | `economy`, `inventory`, `treasury`, `casino`, `games` ship | Dank Memer / Tatsu | Unify all games on one audited ledger (settle-once); SuperBot's game *breadth* already exceeds Dank Memer's. |
| **Logging / audit** | `logging` ships (8 gateway listeners, routes, panels) | ProBot / Carl-bot | Reach DM-log + webhook-route + out-of-channel-log depth; SuperBot has the route/panel spine. |
| **Community engagement** | `community`, `community_spotlight`, `counters`, `counting`, `four_twenty` ship; polls in `utility` | Carl / Dyno | Ship native **giveaways** (plan-only today — Lane E); promote poll to first-class. |
| **Web config** | `dashboard/` Flask app ships | Dyno / MEE6 | Reach live-editor + full module-toggle parity (Lane E dashboard/live-editor plans); keep it free. |
| **Knowledge / AI** | `ai`, `btd6`, `project_moon` ship (unique domains) | — (no mainstream equivalent) | **Category-defining, not catch-up** — no mainstream bot has grounded game-knowledge domains; the target is depth/eval quality, not a competitor. |
| **World / collection games** | `mining`, `fishing`, `creature`, `farm` ship | Tatsu (pets) / Mudae (gacha) | Unify on one world/economy primitive; SuperBot's world-game depth is already beyond mainstream bots. |

## Genuine verified gaps (real Axis-3 additions to consider)

- **Native giveaways** — not a shipped subsystem; **plan-only** (`giveaway-system-plan`, Lane E). Competitors
  (Carl, Dyno, GiveawayBot) have it. Genuine gap, already routed → build per the Lane E plan; outperform bar =
  free + native + audited.
- **Voice / music** — genuinely **absent** (no voice subsystem). See deliberate omissions.
- **External data feeds** (RSS/reddit/YouTube/weather) — YAGPDB/Dyno have them; SuperBot has no general feed
  primitive. ⚠ Candidate `deferred known option`, not a commitment.
- **Grouped self-roles** (YAGPDB-style role groups) — SuperBot has role menus/packs; explicit *exclusive-group*
  semantics ⚠ unverified. Minor; capstone to confirm against `role` schema.

## Deliberate omissions (documented, not gaps to close)

- **Voice / music streaming** — complexity + licensing + third-party dependency; consistent with the
  `voice-music-architecture-review` plan's caution. Deliberate scope exclusion.
- **Premium/paywall architecture** — SuperBot is free-for-everyone (owner mission); the competitor pattern of
  gating features behind payment is a *deliberate anti-goal*, not a missing feature.
- **Deep niche gacha** (Mudae-style anime collection) — a self-contained niche; SuperBot's creature/collection
  loop is its own design, not a Mudae clone.

## Deferred known options (documented for a future session — not build commitments)

- **Advanced/deep AI chat (open-domain NLP)** — fast-moving; SuperBot's `ai` is grounded/eval-first by design.
  Keep offline-first; revisit as the space matures.
- **External analytics dashboards** (public stat pages) — beyond current scope; the `dashboard/` app could grow
  here later.
- **Multi-bot / migration integrations** — the `bot-migration-assistant` plan (Lane E) is the routed home.

## Uncertainties & source caveats (⚠)

- Competitor feature sets change frequently; the catalog reflects *stated* capabilities at research time, not a
  guaranteed-current catalog. The capstone should treat specific competitor claims as directional.
- A few competitor specifics (exact automod trigger granularity, Ticket Tool transcript internals, Tatsu
  house/pet depth) were not independently re-verified from primary sources in this pass — marked directional.
- SuperBot claims are **not** caveated: every "already shipped" statement cites `disbot/` source or the
  43-subsystem ground truth and is authoritative.

## Handoff to the capstone

- Every domain now carries a concrete **outperform target** — the six merged lanes' `pending Lane F` cells can
  be resolved from the table above.
- The dominant capstone lesson: **SuperBot's shipped breadth already meets or exceeds mainstream-bot breadth,
  and its knowledge/world-game domains are category-defining.** The build plan's outperform column is therefore
  mostly **"match best-in-class UX/depth/config on what we already have"** + a short list of genuine gaps
  (giveaways = planned; feeds = deferred), **not** "build the basics."
- Cross-references: shipped subsystems (Lanes A–D), planned enhancements (Lane E: giveaways, reaction-roles
  overhaul, visual-card-engine, dashboard live-editor, bot-migration-assistant), L0 host (Lane G).

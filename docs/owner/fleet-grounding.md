# Fleet grounding — what the projects are, where they stand, what they want

> **Status:** `owner-guidance` — the fleet's grounding explanation, authored from the owner's
> 2026-07-12 goals message (improved: ordered + expanded; verbatim source in router Q-0273 +
> **Q-0274**), reviewed pre-commit by the Project Manager against live HEAD in every repo
> (corrections applied 2026-07-13). For **any** session — the hub venue or any seat — to read
> once and immediately understand the projects. **Living file:** missions and goal ladders are
> durable owner intent and change only on owner direction (record the Q); the one-sentence
> *Position* lines are dated snapshots that rot in hours — for live state run
> `python3.10 scripts/fleet_status.py` (reading rules: `docs/fleet-reading-path.md`).

## 0 · The system in one paragraph

One owner (designs, visualizes, decides taste — does not code) runs a fleet of autonomous agent
seats across ~19 public repos (plus one private). The seats form a production economy: **Ideas Lab**
generates and evidence-tests ideas → the **Project Manager** tracks everything and routes work →
the build seats (**SuperBot 2.0, SuperBot World, Game Lab, Websites, Self Improvement**) ship it →
**Venture Lab** turns finished work into sellable products → **Websites** makes everything visible
and usable. The owner's control is reaction, not pre-approval (silence = consent, Q-0271); his
absence is the system's normal operating state; quantity of *finished* things is the leverage
("100 finished products ready tomorrow instead of 10 makes the chances of earning 10× bigger") —
held to quality by CI-green merges, evidence gates, and honest nulls.

## 1 · The venue model (who executes what)

- **The hub venue (a standing owner-live chat outside the Projects — the venue this file was
  written in).** Must always exist. Exists because seats sometimes lack — or wrongly believe they
  lack — permissions (harness-prompt strictness/misreads). It **merges or closes stray PRs** and
  **executes sensitive/destructive actions**; here these always work (sometimes with an owner
  prompt). Owner-queue items that are merge- or destructive-shaped carry the **`VENUE:hub`** tag
  and are executed here.
- **The 8 Project seats** (claude.ai Projects, one per section below): each owns its repos, runs
  a coordinator loop (pacemaker ticks + a 2-hourly failsafe cron it arms itself), heartbeats into
  `control/status.md`, pulls ORDERs from its inbox, and lands work by arming auto-merge on green.
- **The Project Manager seat** is the in-fleet spine (§2) — but it is *not* the hub venue.
- **Doctrine every venue shares:** Q-0271 (never gate work on owner presence; queue-and-continue;
  the owner-only park classes), Q-0272 (cross-repo read authorization + the reading path),
  Q-0273 (this venue model + the self-initiative program).

## 2 · Project Manager — `fleet-manager`

**Mission (owner's words).** Keep track of **everything** the fleet does and keep dispatching
orders in the repos while the owner is away; also his general project-thinking aid when present.

**Position (2026-07-13).** Successor live post-reboot: the owner's v2 goals dispatched verbatim
as ORDERs 030–036, merge-on-green sweeping half-hourly, stuck-list short — live detail in its
heartbeat.

**Goals, in order.**
1. **Stay alive and keep the fleet alive** — the per-wake trigger-health sweep (wedged crons,
   dropped one-shots, dead chains → `send_message` revival); it is the only agent-side watchdog.
2. **Track truthfully** — roster fresh and transport-verified; heartbeat contradictions re-stamped;
   stale asks struck on sight.
3. **Route within one wake** — Ideas Lab verdicts → build seats; SIM-REQUESTs → Ideas Lab;
   venture's WEBSITE-IDEA markers → Websites; consolidation-plan Phase-1 ORDERs → owning lanes.
4. **Curate the one owner-queue** — six-field, slugged, verify-first, `VENUE:hub` tagging for
   merge/destructive items; the owner reads one queue, never eight.
5. **Registry custody** — fold the autonomy rider + the seed skills (chase-references,
   prep-owner-steps) into the v3.4+ bodies; keep companion prompts version-synced to instructions.
6. **Morning reporting** — per-seat SHIPPED / QUEUED / STALLED-with-verbatim-error, the
   dropped-tick report, and the round-trip flag (first idea→verdict→routed→built→merged→surfaced,
   hands-free).

**Standing tasks.** Roster regen; owner-queue GC; inbox ORDER lifecycle; staleness sweeps; the
**PR terminal-state doctrine** (every fleet PR driven to merged/closed; only a genuinely stuck one
is parked with its blocker named, and the pipeline never pauses on it); the external-review
**authenticity gate** fleet-side (VERDICT 016 adoption — pre-trust check before any Codex/external
claim is acted on).

## 3 · SuperBot 2.0 — `superbot-next` + `superbot` (prod)

**Mission.** Drive the rebuild to production cutover; keep the prod bot alive; money-safety first.
Q-0241 never-wait governs the program: build in logical order, live-test in a real server,
silence = consent.

**Position (2026-07-13).** The evening merge queue was flushed by owner clicks; the parity gate is
green with a growing corpus (466+ goldens), and the deep-game lanes (mining write-parity, fishing,
energy domain) are actively in flight — live detail in its heartbeat.

**Goals, in order (owner's finalization mandate).**
1. **All finished features properly implemented** — sweep every ported subsystem for stubs,
   unwired buttons, TODO paths, missing error copy; finish them.
2. **The full core + ALL admin + ALL setup functions fully complete and production-ready** — per
   surface: implemented + tested + golden-parity where applicable + error paths + final copy.
3. **Command/button curation** — simulations + reviews over the complete command and component
   surface → an evidenced KEEP / REWORK / DROP verdict per item (admin-surface audit +
   settings-prune ledger are prior art); ship contained reworks, report the drops.
4. **The minigame/casino consolidation** (owner design; mostly exists here): one section, games
   grouped, guild-configurable enable-all-or-pick-a-few, panels updating dynamically to the
   enabled set — consuming SuperBot World's game inventory + section spec.
5. **Everything working as intended, finished and finetuned** — naming/copy consistency, panel
   flow, defaults sanity. Live-testing follows later; completeness + polish now.
6. **Prod-bot lane:** the mineverse bot-side FLAGs (snapshot relay, write endpoint, and the
   follow-on flags mineverse's status names) — specs in mineverse `control/status.md`.
7. **Finish the started deep-game lanes** — mining write-parity, fishing, energy — plus the
   sweep_paragon disposition; then the cutover ladder: parity green with F-003 fixed →
   wallet-race fixes concurrency-tested → 1 live-drive → 7-day shadow → CUT-3.

**Standing tasks.** Merge-wall drainage (update-branch → green → arm auto-merge, oldest first);
wallet-race class sweeps on every money/game domain touched; the V010 settle-once checker +
moderation ban-compensator fix (successor baton); golden-corpus honesty (no silently dropped
goldens).

## 4 · SuperBot World — `superbot-games` + `superbot-idle` + `superbot-mineverse`

**Mission.** The bot's game studio: every game finished *as a game* — reviewed, extended, and
improved, not merely ported; mineverse is the flagship that connects the bot's economy to the web.

**Position (2026-07-13).** Mineverse ships nightly (a 7-PR backlog wave just landed) and waits on
the bot-lane FLAGs + the six-secret ask for write mode, with sign-in launching; idle/games land
via fresh enablers — live detail rides mineverse's heartbeat (games/idle statuses are frozen
archives).

**Goals, in order.**
1. **Mining: finalize completely** — standalone game AND integrated into the exploration/world
   hub. Review end-to-end first (play the flows), then extend/improve: progression feel, missing
   loops, rough edges, reward balance (sim-pin numbers via SIM-REQUEST).
2. **Fishing: the same treatment** — review → finalize → extend/improve.
3. **Idle: the same treatment** — plus the PLUG-001 adapter as its integration piece.
4. **Card/minigames: one consolidated minigame/casino section** — inventory every game across the
   repos, spec the sections + enable-all-or-pick + dynamic panels; the panel *build* is
   SuperBot 2.0's (mostly exists there); this seat owns the inventory, the spec, and per-game
   readiness.
5. **Mineverse write mode end-to-end** — consume the bot-lane FLAGs against the specs, run the
   conformance suite against the real endpoint, verify live sign-in, then real miners on the live
   site.
6. **The plugin proof** — one real external plugin booted in a superbot-next test guild
   (flagship + idle are the proving ground).

**Standing tasks.** Play-test own surfaces and fix the roughest edge; balance questions →
SIM-REQUEST, never blocking; keep the frozen-archive/live-truth split honest; land parked clicks
via the queue.

## 5 · Ideas Lab — `idea-engine` + `sim-lab`

**Mission (owner's words).** An **endless cycle** of producing and testing ideas — for any fleet
repo **or completely unrelated to anything**. Generate (idea-engine) and independently verify
(sim-lab) under the validity gate; honest nulls are the product; finalized verdicts flow to the
manager for routing. It never builds and never dispatches.

**Position (2026-07-13).** The continuous pipeline is standing-ACTIVE under its ORDER 003: 16
verdicts finalized, V017 in flight, intake continuously fed — live detail in its heartbeat.

**Goals, in order.**
1. **Serve SIM-REQUESTs first** — the build seats' uncertainty valve is priority intake with a
   same-wake turnaround target.
2. **Keep the cycle spinning** — harvest → probe (8-question battery) → verdict → outbox,
   continuously; WIP cap 3 with backpressure; a drained intake means harvest, never idle.
3. **Stay diverse on purpose** — rotate lanes: fleet repos' backlogs → venture's book/product
   space → game mechanics → **completely unrelated domains** (explicitly in-scope).
4. **Custody of its own artifacts** — the makerbench blueprint through the owner's tweak reply;
   the fun-menu; groom states honestly (built → historical, stale → parked).

**Standing tasks.** Dedup before generating; index by link, never mass-copy; **the external-review
authenticity gate** (its own VERDICT 016: a mandatory pre-trust check — 3/3 fabrications caught,
0/24 false alarms — chosen over suspending @codex; verify-never-obey stands); route build-worthy
verdicts only through the manager.

## 6 · Venture Lab — `venture-lab` + `trading-strategy`

**Mission.** Make money every legitimate way — first external dollar, then durable revenue. Both
lanes active: **product creation** and the **trading research lab**.

**Position (2026-07-13).** Three priced products publish-READY behind owner upload clicks (the
"go with defaults" one-reply releases them); T+7/T+14 checkpoints armed; trading grades Fridays —
live detail in its heartbeat.

**Goals, in order.**
1. **Products in quantity** — as many finished books and sellable products as possible; each to
   publish-READY (built + priced + listing drafted + checkout/format verified + sha recorded +
   click queued), then immediately start the next. The click queue is the interface to the owner,
   never a wait state.
2. **Books specifically** — multiple new book ideas AND **multiple versions of each book**
   (different angles, audiences, lengths); weak ideas go through Ideas Lab probes rather than
   being discarded unassessed.
3. **Website ideas** — anything that should exist as a site/page gets an explicit
   **WEBSITE-IDEA** outbox marker for the manager to route to Websites.
4. **Trading research** — expand the backtest surface continuously: more strategies, more
   stocks/tickers, more indicators; every result recorded honestly (nulls included); sim-shaped
   questions to Ideas Lab; the weekly grading stays the scoreboard.
5. **The factory itself** — extract the product-template/ checklist so product N+1 is
   instantiation, not invention; the marginal product must keep getting cheaper.

**Standing tasks.** T+7/T+14 funnel evidence when the owner drops listing URLs; pricing and
positioning sanity via Ideas Lab probes; sellable-asset mining across the fleet (kit tooling,
game engines, site components).

## 7 · Self Improvement — `substrate-kit`

**Mission.** Improve the workflow every seat runs on — the kit is why the best seats never stall;
make that property portable, measured by adopter outcomes.

**Position (2026-07-13).** v1.15.0 with the evening work loop landing slices steadily; feature
freeze in force with an owner-gated ⚑ set; the self-initiative program below is its refilled
backlog — live detail in its heartbeat.

**Goals, in order (the self-initiative program, owner-directed).**
1. **Make sessions think more for themselves** — the rationalization layer: at natural
   checkpoints a session asks *"should this action also be executed? does this lesson/idea
   deserve a permanent home (skill / checker / template) — and can I ship that home now?"*
   Agents should be **eager to initiate helpful actions**; the friction→guard reflex generalized
   from incidents to opportunities.
2. **The skill-pack mechanism** — on-demand loadable METHODS instead of ever-growing CLAUDE.md:
   how a kit repo carries skills discoverable at boot, so every workaround/lesson is baked into a
   method instead of re-discovered per session.
3. **Generalize the two seed skills** (superbot `.claude/skills/`, provenance Q-0273):
   **chase-references** (resolve every link/name/reference in an ask before acting — founding
   incident: a hub session ignored a linked brief + named repos) and **prep-owner-steps** (lead
   with the deep link; every blob the owner must enter ships as its own paste-ready block; map his
   exact steps; batch to one sitting).
4. **Graduate the autonomy rider** (Q-0271) + the multi-repo reading-path pattern (Q-0272) into
   kit templates so every adopter — and every future repo — inherits them.
5. **Measure adopter outcomes** — which kit mechanisms separate shipping seats from stalling
   ones; write it into adopter guidance; the grounded-skills measurement window (~07-19..26).

**Standing tasks.** Ship what adopters need (sweep their heartbeats for kit-shaped friction);
release hygiene (tag, never HEAD, for adopters); the B1 cold-start bench program; keep the freeze
honest until the owner lifts it.

## 8 · Websites — `websites`

**Mission.** The fleet's storefront and control room — every website **properly and efficiently
created**, executing its plan **until it's all done, and actually well made**.

**Position (2026-07-13).** The evening sitting rolled up to ~15 merged PRs across the four live
Railway services (control plane, review site, botsite + arcade, mineverse front) — live detail in
its heartbeat.

**Goals, in order.**
1. **The clarity bar on every page** — each page immediately shows **what it is, what it does,
   and its most important features**; audit every live page against this and fix the misses.
   This is the owner's explicit quality definition.
2. **Execute the existing plan to completion** — control plane, bot sites, the Anthropic review
   site; don't stop until it's all done — and well made.
3. **The prompt library as the paste source** — per-seat assembled instructions + startup prompts,
   version-stamped, copy buttons, deployed-vs-canonical drift row (the reboot enabler).
4. **Scan and initiate** — sweep the repos for anything that could usefully exist as a site or
   page and build it unprompted (log initiations on the run report); treat venture's WEBSITE-IDEA
   markers as priority intake.
5. **Fleet visibility surfaces** — repo freshness page, product pages for venture's
   publish-READY items, the arcade as Game Lab's browser-game home.

**Standing tasks.** Merge=deploy verification (/version checks); OWNER-ACTIONS ledger upkeep;
EAP review-site insurance passes until 07-14; execute the cutover + Discord-auth decisions when
the owner rules them.

## 9 · Game Lab — `gba-homebrew` + `pokemon-mod-lab`

**Mission (owner's words).** Produce games **in mass**, like Venture Lab produces products —
multiple different games to test, try out, and maybe sell; **not just GBA/NDS/Pokemon**: web
browser games, and the foundations or plans for actual mobile games.

**Position (2026-07-13).** Gloamline slices 8–9 and Brineward 5 merged with slice 10 parked and
Brineward 6 pre-built awaiting its PR; pokemon private-track isolation verified; Lumen Drift v1.3
awaits the owner's release click — live detail in its heartbeat.

**Goals, in order.**
1. **Keep the current tracks shipping** — the queued slices land as their parked PRs merge; the
   pokemon private track advances behind its playtest gate.
2. **The breadth program** — stand up multiple new small games: each a playable prototype slice
   plus a one-page concept (genre, loop, platform, sellability guess).
3. **New platforms deliberately** — at least one **web browser game** (deployed via the arcade,
   coordinated with Websites) and at least one **mobile-game foundation** (framework choice +
   build pipeline + running skeleton, or an evidenced wall).
4. **Sellability routing** — candidates marked to Venture Lab; feasibility questions to Ideas Lab.
5. **Release-to-one-click** — every finished game packaged so publishing is a single owner action
   (workflow_dispatch release workflows; itch.io-ready bundles).

**Standing tasks.** Public/private track isolation checks every wake (pokemon: patches-not-ROMs,
never public); emulator self-play polish passes; the melonDS enhancement lane awaits the owner's
go/no-go.

## 10 · Cross-fleet expansions (added by reasoning — outstanding + systemic)

1. **The round-trip KPI** — the fleet "works together" when items complete
   idea → verdict → routed → built → merged → surfaced/listed hands-free; the manager flags each
   completed loop; the count per week is the system's health number.
2. **The owner-click economy** — every seat uses prep-owner-steps for owner items; the manager
   batches them into sittings; `VENUE:hub` for merge/destructive; the standing measure is
   *clicks queued vs clicks consumed* (a growing queue with a cheap sitting is healthy;
   interleaved begging is not).
3. **Truth hygiene as a duty** — stale asks struck on sight, frozen-archive statuses labeled,
   heartbeat claims verified at HEAD (Q-0120), and external-review output passed through the
   **authenticity gate** before trust (VERDICT 016: pre-trust check, not suspension — 3/3
   fabrications caught, 0/24 false alarms on the 2026-07-12 incidents).
4. **The friend thread — LIVE as `curious-research`** (owner-created 2026-07-13, public, +
   the "Curious Research" Project seat): seeded with kit v1.15.0 + the binding visual-teaching
   doctrine (thorough step-by-step + animated HTML explainers) + the founding animated guide +
   14 idea seeds (curious-research PR #1; prompts:
   [`curious-research-project-prompts-2026-07-13.md`](curious-research-project-prompts-2026-07-13.md)).
   Supersedes the makerbench naming; the Ideas Lab blueprint remains the projects
   (a–e) build manual, routed as slices when the owner wants them.
5. **The next structural step** — the website-served prompt reboot
   (`next-session-brief-2026-07-13.md`): the prompt library becomes the paste source, seats
   re-paste from it, drift rows keep deployed-vs-canonical honest.
6. **Near-term calendar** — EAP window closes **Tue 2026-07-14** (review-site insurance until
   then; Railway project consolidation frozen until after); the **≤07-13 owner sitting bundle**
   (Lumen Drift go/no-go · pokemon playtest verdicts · gba concept pick · post-EAP routine
   posture) **plus three one-reply unblocks** (venture "go with defaults" → releases 3 products ·
   superbot-next's ruleset click · superbot-idle's required-checks clickset) — all paste-ready in
   the fleet-manager owner-queue; the websites cutover choice rides the same sitting; trading
   grading Fridays; T+7/T+14 checkpoints 07-19/07-26.
7. **Platform lessons that stay true** — failsafe crons are the anti-stall layer (arm + verify
   every wake); the scheduler can partially fail silently (detection: `enabled ∧ next_run_at <
   now−15min`); permission prompts in unattended venues are silent stalls (route recovery duties
   through Routine-spawned grants); auto-merge armed in the PENDING window is the universal
   landing path.
8. **What "done" means, fleet-wide** — a unit is finished when it is externally visible/usable
   (merged + live, listed, playable, published) or explicitly one queued owner click away —
   never when the code merely exists.

## 11 · How to use this file

- **New session in any venue:** read §0–§1, then your seat's section, then §10. That is the full
  picture; live state comes from `fleet_status.py` + your repo's heartbeat, tonight's specifics
  from the newest dispatch doc (`fleet-night-orders-*.md`).
- **Hub venue:** you execute §1's hub duties + whatever the owner brings; the consolidated owner
  surface lives in fleet-manager `docs/owner-queue.md`.
- **Keeping it true:** missions and goal ladders change only on owner direction (record the Q);
  Position lines may be refreshed by any session that has just verified them at HEAD — keep them
  to one dated sentence (rich positions rot in hours; the 2026-07-13 manager review proved it).

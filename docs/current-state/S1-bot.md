# S1 — Bot product · live state

> **Status:** `living-ledger` — per-sector live snapshot (Q-0195).

> Per-sector snapshot (Q-0195). Hub: [`../current-state.md`](../current-state.md) ·
> Forward queue: [`../roadmap.md`](../roadmap.md) § S1 · Folios:
> [server-management](../subsystems/server-management.md) ·
> [games](../subsystems/games.md) ·
> [settings-bindings-provisioning](../subsystems/settings-bindings-provisioning.md).

**Recently shipped (this sector):**
- **Reaction-roles arc — Carl-bot-mature** (#1234/#1237/#1242/#1243/#1245/#1246/#1248/#1250):
  multi-emote-per-message, channel/message pickers, role + gradient presets, free temp-roles
  member view, dead-binding self-heal. **PR 6 (PIL banner cards) shipped (#1279);** only the gated web
  builder (Surface A) remains
  ([plan](../planning/reaction-roles-overhaul-plan-2026-06-21.md)).
- **Creature game** — runtime catch/collection (#1208), level-normalized PvP engine + flow
  (#1213/#1230), leaderboard provider (#1244).
- **Mining grid** — seed-deterministic (x,y,z) grid + dig-moves-you (#1281/#1282).
- **Starboard / Hall-of-Fame** — plan #1254 → PR 1 #1259 → PR 2 #1270.
- **Fishing minigame** — cast/reel loop + rod ladder + energy (#1296–#1304, incl. the generous
  sell-value rebalance 1–7 → 1–21 in #1304); **Bait layer** — coin-bought consumable with **both**
  economy knobs: rarity (#1329) + the **bite-speed** half (#1337) on the same
  `CastStart`/cast-view seam, plus speed/combo baits. **Bait crafting** — turn small caught
  fish into bait packs (`fishing_workflow.craft_bait`, the `🪱 Bait` Craft select + `!craftbait`),
  closing `catch → craft → bait → bigger catch` (#1338). **⛵ Boat/deepwater venue** (#1340) — a
  persisted shore↔deepwater toggle (`!sail` + the menu button, migration 094 `fishing_venue`);
  deepwater holds 11 **boat-only species** (uncatchable from shore) and runs a **tougher minigame**
  (6–12 s bites · 22% base escape) so the rod escape-resist knob finally pays off — additive (the
  original 21 shore fish unchanged), the literal §5 shore-cap rebalance left as an owner balance
  call. **Daily weather forecast** (#1341) — a date-seeded global bias
  (`utils/fishing/weather.py`, no DB) compounding onto the cast as a third how-well knob
  (rod × bait × weather): clear/rain/calm/fog/storm, the same for everyone each day; `!forecast` +
  a menu/cast forecast line. **Trophy records per species** (#1351) — each catch now rolls
  an individual weight (`utils/fishing/weight.py`); the catch-log keeps your heaviest of each species
  (migration 095 re-adds `best_weight`), the Fishdex shows the personal-best beside each tally, and a
  fresh record celebrates "🏅 New personal best!" on the catch — a cheap long-tail retention goal.
  **Trophy follow-ups** (#1356, this PR) — the **soft-fail clue** (a *trophy* that slips the hook now
  names itself, `minigame.escape_clue`, so a lost big fish baits the next cast) + the **heaviest-catch
  leaderboard** `!trophies` (`bigfish`/`fishtrophy`, `db.top_trophies` off the `best_weight` record) —
  a "Biggest Catches" hall of fame where trophies compete server-wide.
- **Casino — multiplayer poker** (PR #1333) — a new Games-hub child for **group** card games with
  **per-player auto-updating ephemeral** hands; v1 = Texas Hold'em (play-chips). Pure `utils/cards/`
  + `utils/poker/` (eval + engine w/ side pots, fully tested) + the `views/casino/` ephemeral
  broadcast table. [design](../planning/casino-poker-design-2026-06-22.md).

**▶ Next startable (one of):**
- **Essential Setup spine — PR 1 COMPLETE + polished, incl. step 0, + CUT OVER as the primary `!setup`
  (owner-directed, 2026-06-24).** A new plain-language, button/dropdown/multi-select-only quick-setup flow
  (**7 steps**: what kind of server is this · greet · moderators · block spam · choose a log channel ·
  reward active members · help desk + summary). Each step applies immediately (direct lane) through an
  audited service; typing is optional everywhere (Q-0205). Shipped #1425/#1427/#1429/#1432/#1434 + polish
  #1435; decisions Q-0202/Q-0203/Q-0204/Q-0205. **Step 0 (server-type starter preset) shipped #1437** —
  `ServerTypeStep`, the new first step; five starter sets applied as pure direct-apply settings bundles
  (`_SERVER_TYPES`, automod/moderation/XP-rate), instant + reversible, no resource creation. **Cutover
  (owner-directed, 2026-06-24):** Essential Setup is now the **primary `!setup` / `/setup`** (was
  `!quicksetup`); the old section-list wizard moved to **`!setupadvanced` / `/setup-advanced`**; Essential
  Setup now opens in a separate **`#superbot-setup`** channel (not the invoking channel) and is what the
  on-join launcher's **Start Setup** opens. **PR 2 (extras menu + "Check my setup") SHIPPED 2026-06-25**
  (dispatch run) — the "All done" summary now offers **More to set up** (a plain menu of the optional
  features the spine skips, each with its setup command) + **Check my setup** (a jargon-free readiness
  health check). **▶ Next:** PR 3 (retire dead/legacy sections + rework the Advanced editor). Tracker:
  [`planning/setup-wizard-restructure-plan-2026-06-24.md`](../planning/setup-wizard-restructure-plan-2026-06-24.md).
- **✅ Consolidation / discoverability audit — COMPLETE (owner-directed, 2026-06-23).** All five goals
  shipped and CI-guarded where possible. Staging brief + per-cog rubric:
  [`planning/consolidation-discoverability-audit-brief-2026-06-23.md`](../planning/consolidation-discoverability-audit-brief-2026-06-23.md).
  - **Every command findable + buttonized** — per-command reachability guard (#1370); gap cogs closed
    (`btd6strat` #1372, `temproles` #1377) → **0 gaps**, baseline emptied, CI-enforced.
  - **No loose ends / forgotten panels** — the ultracode fleet cleared the `edit_in_place` backlog and
    **graduated the rule warn→error** (#1375; U1 AI panels #1376, U2 roles #1377, U3 games hub #1378);
    **universal Help + Back-to-hub on every panel** (#1382); **game-result continuation buttons** (#1383).
  - **Settings centralized** — the settings-reachability guard (#1385): 19/19 reachable, 0 gaps, CI-enforced.
  - **AI advisor finalized** — describe → propose → **Accept/Deny/Edit** → confirm → audited apply
    (#1386 + bind re-pick #1390); Q-0048 decided (AI applies only after confirmation) → recorded as
    **Q-0199** (#1389).
  - Shared primitives extracted along the way: `views/hub_children.py` `discover_hub_children` +
    `HubChildButton` (#1371/#1373); `views/navigation.py` `attach_standard_nav` (#1382).
  - **▶ Remaining (optional polish tail, not blocking):** the setup-wizard **per-section walk** (fleet
    unit U10 — confirm every *manual* section yields a real op / honest link-only; the AI-describe side
    is done) · **Essential Setup extras-menu live status badges** (follow-on to PR 2 #1449 — prefix each
    extra with ✅/➖ using the same `setup_readiness.collect` snapshot `build_check_setup_embed` already
    fetches; **blocked on running-bot verification** — reaction-roles has no dedicated readiness
    subsystem, so the extra→subsystem mapping can't be confirmed offline; a bot-access session should
    do it) · the **visual card-engine migration** — engine **H2** *renderer-dedup* half **🟡 partially
    shipped (welcome / UX-lab leaderboard+poster / role-menu rebased onto `CardCanvas`, 2026-06-24
    dispatch run)**; the **leaderboard card now ships as a real feature** (`!leaderboard` attaches a
    rendered top-N image with embed fallback, 2026-06-24 dispatch run) — remaining H2 is only the
    `mining_render` rebase (owner visual decision). **H3 *embed-feature → image-card* is underway:**
    `/myprofile` (H1) and now **`!rank`** both render real image cards (`utils/rank_render.py`, themed
    grid + level progress bar, re-rendered on the stat-toggle, embed fallback — 2026-06-24 dispatch
    run). The **`!xpmenu` hub panel** now renders the rank image card too (its direct surface +
    stat-switch buttons, embed fallback — 2026-06-24 dispatch run, PR #1413). The **help-nav
    attachment seam** then shipped (PR #1430, 2026-06-24 dispatch run) — hubs reached *through Help /
    hub navigation* now carry their image card too (`views.navigation.help_nav_card`, a non-viral
    duck-typed `view.help_nav_card` the central render sites forward; XP hub is the first consumer),
    closing the "card via the command, plain embed via Help" split at the root. Remaining H3 is
    **incremental adoption** (other card-bearing hubs set `help_nav_card` in their hook — profile/rank
    hubs are the next adopters) + other showpiece embeds —
    [vision](../ideas/visual-card-engine-vision-2026-06-23.md) ·
    [seam idea](../ideas/help-nav-attachment-seam-2026-06-24.md) · the
    `channel-deployed-component` roles primitive (idea, not yet built).
- **Fishing follow-ups** (turn-key, on the bait/venue seam) — *(bait speed knob ✅ #1337, sell-value
  re-tune ✅ #1304, bait-crafting ✅ #1338, and the **⛵ boat/deepwater venue** ✅ PR #1340 — shore↔
  deepwater toggle + boat-only species + tougher deep minigame — are all done)* — remaining:
  the literal §5 **shore-cap-at-12 rebalance** (owner balance call, flagged in #1340) ·
  *(weather/time-of-day modifier ✅ #1341 · trophy records per species ✅ #1351 · soft-fail clue +
  heaviest-catch leaderboard ✅ #1356 · fake-out bites + the **`premature_grace` rod knob** that makes
  them meaningful ✅ PR #1365 — the design's 5th rod knob, forgives one early reel per cast)* · the
  **open-world expansion**
  ([plan](../planning/fishing-open-world-expansion-plan-2026-06-18.md) Phase 2+: the
  boat-as-structure / travel-timer / destinations layer).
- **Project Moon runtime PR 1** — the `KnowledgeDomain` seam + first ingest
  ([plan](../planning/project-moon-knowledge-domain-plan-2026-06-21.md)).
- **botsite React-SPA migration PR 2** — serve the built React app from `botsite/` + cutover
  (PR 1 foundation shipped; [plan](../planning/botsite-react-spa-migration-plan-2026-06-20.md)).

**In flight (don't duplicate):** Starboard PR 2 (#1270) config polish · botsite React-SPA
migration **PR 1** (#1305 — runnable data-fed React app + `/site-data.json`; foundation).

**Owner-paced / gated:** reaction-roles web builder (Surface A; PR 6 shipped #1279) · creature PvP balance + art (Q-0187) ·
website rollout ·
[feedback-board PR 1](../planning/feedback-board-generalization-plan-2026-06-19.md) (owner auth) ·
AI-ticket build (Q-0183) · Explore-hub PR 2 + gated layers (Q-0182) · dashboard writes / control-API
(security review).

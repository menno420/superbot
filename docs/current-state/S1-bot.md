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
- **Gear loadout presets** (#1499, V-14/Q-0175 Phase-1 unified-loadout) — save your equipped gear as a
  named set (`mining`/`combat`/`fishing`, cap 10) and swap your whole loadout with one click (`💾 Loadouts`
  gear-panel button + `!loadout`). `mining_loadout_presets` (migration 101, direct-lane like
  `mining_equipment`) + `mining_workflow.{save,apply,list,delete}_loadout`; apply equips every still-owned
  item, clears other slots, reports anything no longer owned; reversible + additive.
- **Fishing-specific gear stats** (#1504, V-14/Q-0175 "matching gear → better fishing" half) — makes a
  fishing loadout a **real optimisation**, not just convenience. `EffectiveStats` gained `fishing_power` +
  `bite_luck` (additive, default-0 → existing reads byte-identical), a CHARM-slot **fishing-charm ladder**
  (fishing/anglers/master-angler charm, off the combat SET_SLOTS so duel balance is untouched) in
  `utils/equipment.py` + the gear shop, the pure converter `utils/fishing/gear.py`, and
  `fishing_workflow.begin_cast` now folds them in as the **4th** cast knob (rod × bait × weather ×
  **gear**). Coins-only (no recipe), sim-pinned
  ([numbers](../planning/fishing-gear-numbers-2026-06-27.md)); self-merged on green.
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
*(offline-fit tags — `[offline]` self-mergeable now · `[needs-live-bot]` needs a running bot / runtime
creds · `[owner]` needs an owner decision/action; see [`../repo-sector-map.md`](../repo-sector-map.md)
§ "the offline-fit startability tag". A tag reflects the arc's *next actionable* step.)*
- `[offline]` **Fishing-specific gear stats — SHIPPED 2026-06-27 (#1504)** (see Recently shipped above):
  the Q-0175 "matching gear → better fishing" half is done — `fishing_power`/`bite_luck` on
  `EffectiveStats`, a CHARM-slot fishing-charm ladder, and the cast's 4th knob in `begin_cast`.
  **Acquisition depth SHIPPED 2026-06-27 (PR #1508):** the three charms now have a **fish→charm craft
  path** (`!craftcharm`) mirroring the catch→bait loop — consume caught fish (smallest-first) → grant one
  charm into the mining inventory, so a dedicated fisher can earn the whole ladder by fishing; coins stay
  the fast alternative ([craft numbers](../planning/fishing-charm-craft-numbers-2026-06-27.md)). ▶ **Next
  offline successor:** a **fish-loot drop** (a small chance a cast yields charm/craft materials directly),
  or extend the same craft pattern to the **rod ladder** (caught-fish craft for the higher rods). Pure +
  sim-pinnable, self-mergeable.
- `[needs-live-bot]` **Essential Setup spine — PR 1 COMPLETE + polished, incl. step 0, + CUT OVER as the primary `!setup`
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
  health check). **PR 3a (retire dead/legacy sections) SHIPPED 2026-06-25** (dispatch run, PR #1451) — the
  7 dead read-only/metadata/announcement/link-only sections (`purpose`/`identity`/`btd6`/`ai_setup`/
  `readiness`/`diagnostics`/`suggestions`) deleted, `server_scan`'s button unregistered (cache module kept
  for `channels`), `cleanup` demoted advanced-only; the Advanced (`!setupadvanced`) wizard now only shows
  steps that do real config. **▶ Next:** **PR 3b** — rework the Advanced draft→Final-Review editor (Q-E,
  "currently most of it does not do anything") + delete the now-dead service code; **heavier, needs
  live-bot verification.** Tracker:
  [`planning/setup-wizard-restructure-plan-2026-06-24.md`](../planning/setup-wizard-restructure-plan-2026-06-24.md).
- `[needs-live-bot]` **✅ Consolidation / discoverability audit — COMPLETE (owner-directed, 2026-06-23).** All five goals
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
- `[offline]` **Fishing follow-ups** (turn-key, on the bait/venue seam) — *(bait speed knob ✅ #1337, sell-value
  re-tune ✅ #1304, bait-crafting ✅ #1338, and the **⛵ boat/deepwater venue** ✅ PR #1340 — shore↔
  deepwater toggle + boat-only species + tougher deep minigame — are all done)* — remaining:
  the literal §5 **shore-cap-at-12 rebalance** (owner balance call, flagged in #1340) ·
  *(weather/time-of-day modifier ✅ #1341 · trophy records per species ✅ #1351 · soft-fail clue +
  heaviest-catch leaderboard ✅ #1356 · fake-out bites + the **`premature_grace` rod knob** that makes
  them meaningful ✅ PR #1365 — the design's 5th rod knob, forgives one early reel per cast)* · the
  **open-world expansion**
  ([plan](../planning/fishing-open-world-expansion-plan-2026-06-18.md) Phase 2+: the
  boat-as-structure / travel-timer / destinations layer).
- `[offline]` **Project Moon (Limbus) — runtime PR 1 SHIPPED 2026-06-25** (dispatch run, PR #1453): a standalone
  **Limbus knowledge domain** — committed structural/lore facts (`disbot/data/projmoon/limbus/`: 12
  Sinners · 7 Sins · 3 damage types · 5 E.G.O grades · status keywords, provenance-tagged), a typed
  `services/projmoon_data_service.py` (loader + resolver), `utils/projmoon/keywords.py`
  (`has_limbus_context`), and a browsable `!pm` / `/pm` surface (`views/projmoon/`, its own top-level
  **Project Moon** Help hub like BTD6). Read-only, no DB, **no AI hot-path change**. **Lore-depth
  follow-on SHIPPED 2026-06-25** (dispatch run, PR #1456): each of the 12 Sinners now carries its
  canonical **`literary_origin`** (the work + author it is drawn from — Faust→Goethe, Outis→Homer,
  Gregor→Kafka, …), rendered in the `!pm` detail card + a new **Origins** cross-reference view
  (`!pm origins` + a panel button). Still read-only/offline. **PR 2 — the GROUNDING PATH — SHIPPED
  2026-06-26** (dispatch run, PR #1467): a Limbus-looking message now routes to the new
  **`AITask.PROJMOON_ANSWER`** (`ai_task_router` → `has_limbus_context`, after BTD6 / before video) and a
  thin `services/projmoon_context_service.build()` injects provenanced Limbus grounding facts (named
  entities + bounded roster queries) into `natural_language_stage._gather_feature_facts` —
  default-preserving (BTD6 path byte-identical), offline-unit-tested. **Faithfulness guard SHIPPED
  2026-06-26** (dispatch run, PR #1469): `services/projmoon_grounding_service.py` post-verifies a
  `PROJMOON_ANSWER` reply against the injected facts (the projmoon analogue of `validate_btd6_reply`,
  reusing `utils.btd6.name_guard` + the shared `GroundingResult`) — indexes the distinctive Sinner /
  E.G.O names, skips the common-English categories, reject → regenerate-once → deterministic Limbus
  refusal; offline-unit-tested. **Slice B *prep* — cross-domain over-route guard SHIPPED 2026-06-26**
  (dispatch run, PR #1470): a registry-driven harness
  (`tests/unit/runtime/ai/test_domain_routing_disjoint.py`) pins the previously-untested router invariant
  *"BTD6 keywords never collide with the distinctive Limbus tokens"* (routing · token disjointness across
  every domain pair · priority total-order) + a detector-curation recipe in the ai folio, so the next
  domain (LoR / LobCorp) is a one-line registration. ▶ **Next:** the live **Q-0086 runtime walk** (owner — confirm a real
  Limbus Q&A grounds well on both providers) + Slice A item 1 (StaticData exact-number ingest); then
  **Slice B** = extract the shared `KnowledgeDomain` seam from BTD6 + Limbus
  ([plan](../planning/project-moon-knowledge-domain-plan-2026-06-21.md)).
- `[offline]` **botsite React-SPA migration PR 2** — serve the built React app from `botsite/` + cutover
  (PR 1 foundation shipped; [plan](../planning/botsite-react-spa-migration-plan-2026-06-20.md)). *(The
  build/serve code is offline + self-mergeable like PR 1; the domain cutover itself is `[owner]`.)*

**In flight (don't duplicate):** Starboard PR 2 (#1270) config polish · botsite React-SPA
migration **PR 1** (#1305 — runnable data-fed React app + `/site-data.json`; foundation).

**Owner-paced / gated:** reaction-roles web builder (Surface A; PR 6 shipped #1279) · creature PvP balance + art (Q-0187) ·
website rollout ·
[feedback-board PR 1](../planning/feedback-board-generalization-plan-2026-06-19.md) (owner auth) ·
AI-ticket build (Q-0183) · Explore-hub PR 2 + gated layers (Q-0182) · dashboard writes / control-API
(security review).

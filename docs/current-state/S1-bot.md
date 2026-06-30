# S1 — Bot product · live state

> **Status:** `living-ledger` — per-sector live snapshot (Q-0195).

> Per-sector snapshot (Q-0195). Hub: [`../current-state.md`](../current-state.md) ·
> Forward queue: [`../roadmap.md`](../roadmap.md) § S1 · Folios:
> [server-management](../subsystems/server-management.md) ·
> [games](../subsystems/games.md) ·
> [settings-bindings-provisioning](../subsystems/settings-bindings-provisioning.md).

> **Posture — completion-first (Q-0209, 2026-06-27):** the bot is close to production-ready, so S1's
> standing bias is **finish/certify existing features before starting new ones** (a new idea that
> *deepens* an existing game/function counts as deepening, not new). Each game + server function is a
> per-feature unit scored `▢ → ◐ → ✔` in
> [`../planning/feature-completion/`](../planning/feature-completion/README.md); certified only on
> evidence + owner sign-off. Soft default — the owner greenlights brand-new units freely.

**Recently shipped (this sector):**
- **Reaction-roles RSVP roster ("Who's in?")** (PR #1571, owner-directed follow-on to #1570) — counted
  menus gain a persistent **👥 Who's in?** button that posts an **ephemeral** roster listing the members
  who currently hold each option (`build_roster_embed` in `role_menu_counter`; member names truncated to
  the field cap with a "…and N more" tail). Gated on the same opt-in `show_counts` + a component-budget
  check; read-only `role.members` (no storage, exposes nothing beyond Discord's member list). No
  migration, no new commands; +12 tests.
- **Reaction-roles live sign-up counter** (PR #1570, owner-directed deepening) — the event-RSVP
  counter from the Discord screenshots: an **opt-in `📊 Counts`** per-menu flag (migration 103
  `role_menus.show_counts`, default off) that renders a **live participant headcount** beside each
  role on the public menu embed + a distinct-member footer total. Counts **current holders**
  (`guild.members` ∩ roles — self-correcting, drops on un-sign/leave; distinct from the operator-only
  cumulative `role_menu_pickup_stats`), refreshed by a **debounced** message edit (≤1 per ~2.5 s
  window → rate-limit-safe). New `views/roles/role_menu_counter.py` (one-pass `collect_counts` +
  `schedule_count_refresh`); a **📣 Event RSVP** starter template (button + `unique` + counts) and
  matching role pack make the multi-option "Going / Maybe / Can't make it" live poll two taps away.
  Threaded through the audited `create_menu`/`update_menu` seam; +35 tests; no new commands; self-merge
  on green ([plan](../planning/reaction-roles-overhaul-plan-2026-06-21.md)).
- **Counters completion deepening** (PR #1568, completion-first deepening) — closed the Counters
  completion cert's offline punch-list #1/#2/#4/#5. Added a curated `{count}` **template preset** catalog
  (`TEMPLATE_PRESETS`: default/minimal/brackets/bullet) + `!counterpreset [name]` (lists them, or applies
  all three templates at once **through the audited `SettingsMutationPipeline`** — re-checks
  `counters.settings.configure`); a `/counters` **slash status** parity surface (ephemeral,
  manage-guild-gated, reuses `_policy_embed`); **channel-type coverage** (voice/text/category all rename,
  DM skipped — parametrized tests); and a **real end-to-end integration test** (stored settings →
  `load_policy` → `sync_guild` → `counters.updated`). Pure additions, no migration; +18 tests
  (~35 total on the unit). Remaining: #3 loop backoff (stateful) + owner walkthrough/sign-off.
- **Cleanup history filters — content-type modes + age gate** (#1566, completion-first deepening) —
  closed the Cleanup completion cert's buildable punch-list (#2/#3). `!cleanuphistory` gained three
  content-type sweep modes (`embeds` / `links` / `attachments`, Carl-bot/MEE6/Dyno parity) and an
  `older:<duration>` age gate (e.g. `older:7d`) composable with every mode — both in the pure
  `services/history_cleanup.py` (`HISTORY_CLEANUP_MODES`, `older_than` cutoff) with cog-side
  `older:`-token parsing + a `_parse_duration_seconds` helper. Found punch-list #1 (panel
  authority-recheck) **already covered** by `test_apply_button_requires_admin` — corrected the stale
  cert note. #4 (configurable spam window) honestly deferred (needs a config-input widget, not a
  constant rename). +12 tests; no migration; self-merged on green.
- **Operator command gaps — `!slowmode` · `!topic` · `!roleinfo`** (#1561, completion-first deepening) —
  the assessment punch-list's named *"best-in-class command gaps (channel slowmode/topic, utility
  roleinfo)"*. `!slowmode <ch> <secs>` (alias `!slow`) + `!topic <ch> <text>` (alias `!settopic`) are
  channel *mutations* so they ship through the audited `ChannelLifecycleService` seam (two REVERSIBLE ops
  `set_slowmode`/`set_topic`, clamped to Discord's 6h/1024-char caps) — each fires the audit companion +
  `channel.lifecycle_changed` event like `!rename`. `!roleinfo <@role|name|id>` (alias `!ri`) is a
  read-only role detail card (colour/members/position/flags/notable permissions) rendered in
  `views/roles/role_info.py` (extracted to keep `role_cog` under the 800-LOC decomposition threshold).
  +44 tests; no migration; self-merged on green.
- **Farm leaderboard provider** (#1542, completion-first deepening win) — the idle chicken farm now
  appears in the unified `!leaderboard` hub + select menu (`FarmProvider`, ranked by **flock size**,
  coop level as the tie-break), reusing a new `db.top_farmers` primitive. Mirrors `FishingProvider`;
  its own `harvest` card skin. **Honest scope note from the same investigation:** of the four games the
  Leaderboards assessment named, only Farm has a persisted per-player rankable stat — **Blackjack**
  (in-memory game state; coins via the economy audit only), **Casino/poker** (ephemeral play-chips, no
  persistence) and **Word-Chain** (per-channel `chain_count`, no per-user tracking) would each need a
  migration + a write-path before a leaderboard is possible (**not** turn-key). +6 provider tests + a db
  SQL-shape pin; no migration; self-merged on green.
- **Economy `!give` / `!pay`** (#1541, completion-first deepening win) — a peer coin-transfer command
  surfacing the already-audited `economy_service.transfer()` seam (atomic debit+credit, `economy_audit_log`,
  `EVT_BALANCE_CHANGED`), closing the assessment's finding (b). Guard-railed (rejects bot target /
  self / non-positive; friendly insufficient-funds message). Member-tier in the homed Economy cog
  (reachable, 0 new gaps). +7 tests; no migration; self-merged on green.
- **Fishing leaderboard provider** (#1540, completion-first deepening win) — fishing now appears in the
  unified `!leaderboard` hub + select menu (`FishingProvider`, top anglers by total fish caught, reusing
  the existing `db.top_fishers`), closing the "Fishing has its own `!fishtop`/`!trophies` boards but no
  unified-panel provider" gap surfaced by the Leaderboards completion assessment. Mirrors
  `CreaturesProvider`; new `fish_names()` catalog helper (dedups the `[s.name for s in SPECIES]` call
  sites); a new `tidal` ocean card-skin. +6 tests; self-merged on green.
- **No-dead-end terminal-view arch guard** (#1529, Q-0194 friction→guard) — a warn-tier `no_dead_end`
  rule in `scripts/check_architecture.py` flags any game-view terminal handler (calls `self.stop()`)
  that renders a message without swapping to a nav-carrying view; allowlist for genuine pre-game
  invite decline/timeout. Turns the recurring trapped-view catch (#1521/#1527) from a manual
  per-assessment check into an enforced one. +7 tests; clean on the current fleet.
- **Completion-first PvP dead-end fixes** (#1527, Q-0209) — closed the recurring **trapped-view** bug
  class in both competitive PvP games. **Deathmatch:** PvP `_DuelView`/`_ChallengeView` now swap to
  `_PvpDuelResultView` (Help/Games nav + 🔁 Rematch) on every terminal, and the latent panel-PvP
  `ctx=None` resolve crash was root-fixed (BUG-0028, explicit `guild_id` thread). **RPS:** the PvP
  match result now carries ◀ Back to RPS (`_RpsPvpResultView`) + a rules "Timeouts & forfeits" field.
  Both completion certs advanced toward ✔ (Deathmatch is now a ✔-ready candidate pending owner
  walkthrough). 11 new tests.
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
- `[offline]` **Completion deepening — clear the assessed certs' punch-lists (the standing offline
  ▶ Next).** Each `◐ assessed` cert ends in a concrete buildable punch-list; ship them to move units
  toward ✔. **✅ DONE 2026-06-29 (#1546): Creatures** — the headline rubric-B gap is closed: the
  interactive **game panel** (`CreatureMenuView`: catch · dex-browser · challenge · ladder · how-to)
  reached via `!creatures` + both cogs' Help hooks, the **interactive dex browser** (element filter),
  the `entry_points` fix, and a **battle settle-once** guard — cert #1/#2/#3/#5 cleared (#4 was a
  no-op). **▶ Next turn-key picks:** **Creatures game panel for Welcome's missing command panel** is a
  separate unit; the Mining how-to button (the ✔-ready candidate's last build gap) **shipped #1548**.
  **✅ DONE 2026-06-30 (#1565): Blackjack** punch #2 + #3 — the panel's PvP path now has a Free/preset/Custom
  **stake picker** (was command-only / hardcoded bet=0) and the three named **edge paths are tested**
  (tournament-timeout forfeit · guild-removal cleanup · natural-blackjack auto-payout); only the owner /
  live-bot items remain (#1 split/insurance/surrender product call, #4 walkthrough, #5 sign-off).
  server-fn deepening picks are listed in the assessments bullet below.
  **✅ DONE 2026-06-29 (#1550): Proof Channel** punch #1 + #2 —
  the lock/unlock now audit (`prize_access_grant`/`revoke`) and every mutation callback re-checks
  `manage_channels` authority; cert advanced (only the binding-write UI + owner walkthrough remain).
  **✅ DONE 2026-06-29 (PR #1553): Inventory punch #5 (sort + filter) CLOSED** — the category detail view
  gained a `🔀 Sort:` cycle (Rarity / Quantity / Name, pure `_sort_items`) **and** a `Filter by type…`
  select (shown only when a category mixes >1 type; `_apply` recomputes the shown slice + pages,
  page-clamped); +15 tests. Inventory's remaining gaps are now the **owner-gated** ones (#1 item actions ·
  #2 item-grant audit — *needs an owner call on audit-trail granularity, see note below* · #3 capability
  cleanup) + live walkthrough. **Also shipped this PR: the registry↔completion-ledger parity guard**
  (`scripts/check_completion_ledger_parity.py`, the Q-0089 follow-up the README flagged) — every
  certifiable registry subsystem has exactly one ledger row + cert, enforced by a pytest regression. (Creatures' `◐ → ✔` still needs the owner live walkthrough +
  sign-off, punch-list #6/#7.)
  **✅ DONE 2026-06-30 (#1566): Cleanup punch #2 + #3 CLOSED** — `!cleanuphistory` gained three
  content-type sweep modes (`embeds`/`links`/`attachments`, Carl-bot/MEE6/Dyno parity) + an
  `older:<duration>` age gate composable with every mode (`HISTORY_CLEANUP_MODES` + `older_than`
  cutoff in the pure `services/history_cleanup.py`; +12 tests). Punch #1 (panel authority re-check)
  found **already covered** (stale cert note corrected). Cleanup's remaining gaps: #4 spam-window
  setting (needs a config-input widget — deferred) + the owner walkthrough/sign-off (#5/#6).
  **▶ Next turn-key picks:** **Counters** loop backoff (punch #3) · **Diagnostics** list pagination
  (punch #2) · Cleanup #4 (spam-window setting *with* a Settings widget). *(Counters punch #1/#2/#4/#5
  ✅ #1568.)*
- `[owner]` **Feature-completion assessments — ALL 36 UNITS ◐ ASSESSED (100%; 0 certified).** The
  completion-first arc (Q-0209). The `▢ → ◐` assessment sweep is **COMPLETE** — every game + server-fn
  now has a rubric-filled, source-grounded certificate under
  [`../planning/feature-completion/units/`](../planning/feature-completion/README.md). The **final
  server-fn batch (PR #1545, this run)** assessed the last 17 unassessed units in one sweep: moderation
  (Cleanup · Automod · Image-moderation · Security · Proof-channel) · economy (Inventory · Treasury) ·
  community (Community-spotlight · Counters) · management (Channels · Setup-wizard) · platform (AI ·
  Logging · Diagnostics · Utility · Help · Admin). **Most are structurally strong** (audited mutation
  seams, Help, tests); the honest weak spots surfaced: **Inventory** (read-only browser, unenforced
  capabilities, unaudited item grants) · **Proof-channel** (lock/unlock mutates channel perms with no
  audit event + no modal authority re-check) · **AI** (carries OPEN **BUG-0019 #1**). **▶ Next startable:**
  the arc is now `◐ → ✔` certification work, which is **`[owner]`/`[needs-live-bot]`** by definition (each
  unit needs a `/verify-bot` live walkthrough + owner sign-off). **Offline deepening picks** from the
  punch-lists: Inventory item-grant audit + capability cleanup · Proof-channel lock/unlock audit + modal
  re-check · logging ignored-lists/channel+voice events · the AI BUG-0019 #1 owner decision · ~~best-in-class
  command gaps (channel slowmode/topic, utility roleinfo)~~ **✅ DONE 2026-06-29 (#1561): `!slowmode` +
  `!topic` (audited ChannelLifecycleService seam) + `!roleinfo` (read-only)** — `channelinfo`/`userinfo`
  already existed; these closed the remaining named gaps. The Blackjack/Casino/Word-Chain
  leaderboards still need persisted per-player tracking first (a feature, not a provider).
  **✅ (2) DONE 2026-06-28 (#1529):** the **"no-dead-end" arch guard** shipped — a warn-tier
  `no_dead_end` rule in `scripts/check_architecture.py` (config + allowlist in
  `architecture_rules/canonical_helpers.yaml`, +7 tests) flags a game-view terminal handler that
  `self.stop()`s + renders a message without swapping to a nav-carrying view, so the trapped-view bug
  class is caught automatically instead of per-assessment ([idea](../ideas/no-dead-end-terminal-view-guard-2026-06-28.md),
  now `historical`). **✅ DONE
  2026-06-28 (#1527):** the Deathmatch PvP trapped views (+ the panel-PvP `ctx=None` crash, BUG-0028)
  **and** the RPS PvP-result dead-end were both fixed — `_PvpDuelResultView` / `_RpsPvpResultView` with
  standard nav + rematch/back; both certs advanced toward ✔. Blackjack's offline punch-list (#2 stake
  picker + #3 edge tests) **shipped #1565**; its remaining **#1** (split/insurance/surrender — bigger
  engine work) is **owner-paced** (the product call to implement-or-waive). **▶ Owner decisions
  waiting:** Word Chain re-classify, Counting XP/coin reward, Deathmatch optional coin-staking, plus
  every assessed unit's `◐ → ✔` live-walkthrough sign-off
  (`[needs-live-bot]`/`[owner]`).
- `[offline]` **Fishing-specific gear stats — SHIPPED 2026-06-27 (#1504)** (see Recently shipped above):
  the Q-0175 "matching gear → better fishing" half is done — `fishing_power`/`bite_luck` on
  `EffectiveStats`, a CHARM-slot fishing-charm ladder, and the cast's 4th knob in `begin_cast`.
  **Acquisition depth SHIPPED 2026-06-27 (PR #1508):** the three charms now have a **fish→charm craft
  path** (`!craftcharm`) mirroring the catch→bait loop — consume caught fish (smallest-first) → grant one
  charm into the mining inventory, so a dedicated fisher can earn the whole ladder by fishing; coins stay
  the fast alternative ([craft numbers](../planning/fishing-charm-craft-numbers-2026-06-27.md)). **The
  rod-ladder craft path SHIPPED 2026-06-27 (PR #1515):** `!craftrod` (+ a **🎣 Craft from fish** button in
  the rod shop) crafts the next rod up from caught fish (smallest-first), mirroring the charm/bait loops —
  `rods.ROD_RECIPES` + `fishing_workflow.craft_rod` (inventory-only, one transaction, no coins/audit);
  coins stay the fast alternative via `buy_rod`
  ([rod craft numbers](../planning/fishing-rod-craft-numbers-2026-06-27.md)). **The fish-loot-drop
  successor ALSO SHIPPED 2026-06-27 (PR #1515):** a **🍀 lucky double catch** — `BONUS_CATCH_CHANCE`
  (0.10) that a successful reel lands a *second* copy of the same fish (extra craft fodder straight into
  the bait/charm/rod craft loops), rolled in `commit_catch` via pure `rewards.roll_bonus_catch`,
  byte-identical when it doesn't fire, never a second dex/trophy row
  ([bonus-catch numbers](../planning/fishing-bonus-catch-numbers-2026-06-27.md)). **The fish-loot
  rare-material drop ALSO SHIPPED 2026-06-28 (PR #1518):** the **pearl** 🦪 — a dedicated rare
  crafting material a successful reel can also yield (size-scaled chance: bigger fish → better odds,
  `utils/fishing/rewards.roll_pearl_drop`, byte-identical when it doesn't fire). Its **repeatable**
  sink is a **pearl-only craft path** for the premium **Royal Feast** bait (the one bait left with no
  fish recipe — a pure coin sink today): `!craftpearl` + a bait-shop "Craft from pearls" select spend
  `bait.PEARL_BAIT_RECIPES` pearls via `fishing_workflow.craft_pearl_bait`; coins stay the fast
  alternative. No DB migration (pearls reuse the generic `mining_inventory` store), sim-pinned
  ([pearl numbers](../planning/fishing-pearl-numbers-2026-06-28.md)). ▶ **Next offline successor:**
  a **fish-loot rare *material*-drop variant** (a dedicated craft material that feeds a *new* craft
  target rather than the premium bait — e.g. a "kelp"/"driftwood" that crafts a cosmetic or a
  structure) **or** the **rod-ladder recipe browser** UI. Pure + sim-pinnable, self-mergeable.
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
  domain (LoR / LobCorp) is a one-line registration. **Combat-mechanics layer — Slice A item 1
  (rules half) — SHIPPED 2026-06-29** (manual session, PR #1549): a new **`mechanic`** entity kind
  (`mechanics.json`, 13 entries grouped by `category`) covering the core combat **rules** a Project
  Moon community member flagged as the missing "majority" — Clash · Coin (heads/Sanity) · Speed ·
  Sanity · Stagger · damage-resistance levels · Resonance · Skills · Defensive skills · Identity
  (rarity 0/00/000) · Passives · E.G.O/Corrosion. Browsable (`!pm mechanic <name>` + a Mechanics
  button) and grounded through the existing `projmoon_context_service.build()` seam (per-entity +
  a "combat mechanics" roster trigger); router / NL-stage / faithfulness-guard / BTD6 path all
  unchanged. Read-only, offline-unit-tested. ▶ **Next:** the live **Q-0086 runtime walk** (owner —
  confirm a real Limbus Q&A grounds well on both providers) + the **numeric tail of Slice A item 1**
  (the StaticData exact per-Identity / per-enemy **stat numbers** — HP, speed values, coin power — via
  the ingest lane, *not* hand-committed, ADR-006); then **Slice B** = extract the shared
  `KnowledgeDomain` seam from BTD6 + Limbus
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

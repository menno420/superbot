# Rebuild Phase A · Stage 2 — the subsystem walk (owner-led)

> **Status:** `plan` — **living, in-progress.** This is the canonical Stage-2 artifact: the
> owner-led, one-subsystem-at-a-time walk of the frozen
> [`NEW-BOT-BUILD-PLAN.md`](../analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md)
> §1.1 capability corpus, using the
> [Stage-2 readiness review](rebuild-stage2-readiness-review-2026-07-03.md)'s per-row template and
> normalized verdict vocabulary. No prior Stage-2 walk artifact existed before this file (verified
> 2026-07-05 — only the readiness-review *contract* existed under
> `docs/planning/rebuild-stage2*`). **Do not create a competing Stage-2 record** — continue this one.
>
> **Precondition check (2026-07-05):** Prompt B (presentation/verification mechanics,
> `docs/analysis/rebuild-discovery/foundations/presentation-verification-mechanics-2026-07-03.md`)
> merged via PR #1691 — the readiness review's blocking precondition is satisfied. Gate-0
> (`docs/analysis/rebuild-discovery/foundations/gate-0/README.md`) explicitly states Stage 2 "runs in
> parallel against the frozen contracts — it does not depend on completing this L0 build." Stage 2 is
> **startable now**, independent of Gate-0 ratification and the substrate-kit D-4 gate.
>
> **Owner-led, decision-capturing, not autonomous.** Per the readiness review §5 rule 1: agents
> pressure-test and record; they do not approve surface choices. Only the primary session thread
> (Lane 0) presents owner questions and finalizes decisions — parallel research fans out, but the
> walk itself is one subsystem/coherent-group at a time, serialized on owner input.

---

## 1. Verdict vocabulary (frozen, per the readiness review + Q-0237(g))

Exactly one primary verdict per row: `keep` · `improve` · `merge` · `redesign` · `drop` · `defer` ·
`re-place` · `add`. A row may carry secondary tags: `blocked-by-gate-0`, `blocked-by-owner`,
`missing-prior-art`, `source-uncertain`, `needs-reconciliation` (cog exists but BUILD-PLAN
disposition looks stale/wrong — a finding, not a blocker).

## 2. Walk order — rationale

Ordered by the frozen BUILD-PLAN §2 build order (L0→L5, itself dependency-topological), with the
Stage-1 global review's **D-1 reorder** applied (welcome moves from L1b to L1c, immediately after
the visual card engine — an engine-class dependency correction, Q-0220). This satisfies the task's
three grounding criteria simultaneously: frozen dependency order, foundation-before-consumer (S-2),
and actual cross-cutting dependencies. **L0 (the kernel/runtime skeleton) is not walked as a Stage-2
owner row** — it is Lane G's territory (already GO-verdicted) and Gate-0's operational build, not a
Discord-facing capability with a product surface; it is tracked in the non-cog queue (§4) for
coverage-completeness only, not for a triage verdict.

The first walked row is **settings** (L1a, position 1): every other subsystem depends on the
settings/config-hub foundation (S-2 foundation-before-consumer), and it is the BUILD-PLAN's own
"generated-config-hub proof" — the frozen build order's own starting point.

## 3. Progress index

State vocabulary: `not-mapped` → `mapped` → `ready-for-owner` → `owner-discussing` → `decided` →
`blocked` → `needs-recheck`.

| # | Layer | BUILD-PLAN row | Lane | Current cog(s) | Research | Owner discussion | Verdict | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | L1a | settings | D | `settings_cog.py` + `settings/` pkg | mapped | decided | **improve** | first row walked this session; full record above |
| 2 | L1a | diagnostic | D | `diagnostic_cog.py` + `diagnostic/` pkg + `health_maintenance_cog.py` | mapped (deep dossier done) | decided | **improve** | hub merge (`!diagnostics`→`/platform`) + unified `DiagnosticProviderSpec` catalogue decided; mutation-surface ownership deferred to row 5. Full record above. |
| 3 | L1a | help | D | `help_cog.py` + `help/` pkg | mapped (deep dossier done) | decided | **improve** | R-11 + G-10 adoption + editor-stack persistence fix decided. **L1a complete** (settings→diagnostic→help all decided). Full record above. |
| 4 | L1b | admin | A | `admin_cog.py` + `admin/` pkg | mapped (verified zero drift vs. Lane A audit) | decided | **improve** | R-11 adoption + 9→8 nav collapse (row 2 fallout) + 2 live bugs (bot_spam typo, missing audit trail) decided fix-now, full scope — execution deferred to a bug-fix session. Full record above. |
| 5 | L1b | server_management | A | `server_management_cog.py` only (`setup_cog.py`/`quicksetup_cog.py` **split out to row 5a**, 2026-07-05) | mapped (deep dossier done) | decided | **improve** | Confirmed a pure zero-write router (5 nav buttons + fail-safe health badges); its own fit gap (58.8%→88.2%) is the exact same R-11/G-A3 dispatch pattern already decided at rows 3-4. Resolved row 2's deferred question: diagnostic's mutation surfaces stay put (no move). Full record above. |
| 5a | L1b (new row — split from row 5) | setup (BUILD-PLAN's own "register as real subsystem" note, now acted on) | A | `setup_cog.py` + `quicksetup_cog.py` + `views/setup/**` | mapped (deep dossier done) | decided | **redesign** | Advanced wizard's draft/Final-Review lane retired, folded into Essential Setup's direct-lane model; registered as one `SUBSYSTEMS` entry with two entry surfaces. Exact per-section fold mapping is Phase-B work. Full record above. |
| 6 | L1b | moderation | A | `moderation_cog.py` | mapped (deep dossier done) | decided | **improve** | 64.2% fit floor; confirmed live bug (`/moderation` ignores `moderator_role`) decided fix-now; case/appeal + bulk actions committed as scope, not deferred. Q-0119 corrected (was never this row's decision). Full record above. |
| 7 | L1b | logging | D | `logging_cog.py` + `logging/` pkg | mapped (deep dossier done) | decided | **keep** | Near-rubber-stamp exemplar confirmed (97% fit reproduced exactly). Admin-only surface confirmed intentional. Completion cert fixed (stale punch #2). Full record above. |
| 8 | L1b | automod | A | `automod_cog.py` + `automod/` pkg | mapped (deep dossier done) | decided | **improve** | 4-rule filter, fail-open discipline confirmed (detector-fault path untested). Auto-mod-tier consolidation **resolved at row 15**: gets its own minimal panel, linked from cleanup's hub. Full record above. |
| 9 | L1b | security | A | `security_cog.py` + `security/` pkg | mapped (deep dossier done) | decided | **improve** | Confirmed live unaudited slowmode bug, fix-now decided. Quarantine action committed as Phase-B scope (was approved at Q-0111, never built). Full record above. |
| 10 | L1b | cleanup | A | `cleanup_cog.py` + `cleanup/` pkg | mapped (deep dossier done) | decided | **improve** | Both unaudited paths confirmed live, fix-now decided. Auto-mod-tier consolidation **resolved at row 15**: cleanup's existing hub becomes the shared launcher (2 new buttons). Full record above. |
| 11 | L1b | counters | B | `counters_cog.py` + `counters/` pkg | mapped (deep dossier done) | decided | **keep** | Rubber-stamp row — zero live bugs, zero unaudited paths. Completion cert stale-verdict fixed. Full record above. |
| 12 | L1b | channel | A | `channel_cog.py` | mapped (deep dossier done) | decided | **improve** | No live bug found. Dead voice-create branch: owner decided to wire it up (new committed feature), not delete. 5 orphaned capability strings: deleted. Full record above. |
| 13 | L1b | role | A | `role_cog.py` + `role/` pkg + `role_grants_cog.py` | mapped (deep dossier done) | decided | **improve** | Teardown-gap bug confirmed + fix-now decided. **Resolved the Stage-1-open G-22 staging-lanes question** (bless RoleMenuBuilder as sole instance). Full record above. |
| 14 | L1b | ticket | A | `ticket_cog.py` | mapped (deep dossier done) | decided | **improve** | Cleanest audited seam confirmed. No live bug, but real gaps: dormant fields (2 exposed, 1 feature finished), slash+auto-close committed, untested mutation paths flagged. Full record above. |
| 15 | L1b | image_moderation | A | `image_moderation_cog.py` + `image_moderation/` pkg | mapped (deep dossier done) | decided | **improve** | No live bug, best fail-open coverage of the auto-mod trio. **Resolved rows 8/10's consolidation question**: minimal panels + 2 new buttons on cleanup's hub. Full record above. |
| 16 | L1b | proof_channel | D | `proof_channel_cog.py` + `proof_channel/` pkg | mapped | **owner-discussing (next)** | — | last row of L1b — completes the entire operator spine |
| 17 | L1c | visual card engine (ADD) | — | none (new) | mapped | not-started | — | 5+ consumers (welcome/rank/leaderboard/profile cards) — D-1 |
| 18 | L1c | welcome | A | `welcome_cog.py` | mapped | not-started | — | **re-homed here from L1b per D-1** (card-engine consumer) |
| 19 | L1c | ux_lab | D | `ux_lab_cog.py` | mapped | not-started | — | zero-write gallery |
| 20 | L2 | economy | B | `economy_cog.py` | mapped | not-started | — | `transfer()` ready-but-unwired to `!give/!pay` — live gap |
| 21 | L2 | inventory | B | `inventory_cog.py` | mapped | not-started | — | REDESIGN — merge two item tables |
| 22 | L2 | treasury | B | `treasury_cog.py` | mapped | not-started | — | |
| 23 | L2 | xp | B | `xp_cog.py` + `xp/` pkg | mapped | not-started | — | |
| 24 | L2 | karma | C | `karma_cog.py` + `karma/` pkg | mapped | not-started | — | highest-fit non-hub (87%) |
| 25 | L2 | community (hub) | C | `community_cog.py` | mapped | not-started | — | 100% tier-1 proof |
| 26 | L2 | community_spotlight | C | `community_spotlight_cog.py` | mapped | not-started | — | P-1 event-feed candidate |
| 27 | L2 | leaderboard | C | `leaderboard_cog.py` | mapped | not-started | — | **MERGE into kernel** verdict already frozen |
| 28 | L2 | profile surface (ADD) | — | **`utility_cog.py:114-146`** (`!myprofile`/`/myprofile`) + `views/profile/profile_view.py` + `views/profile/editor.py` | mapped | not-started | — | ⚠ **CAPSTONE CONTRADICTION** — BUILD-PLAN row says "PR C decided (Q-0147) but unbuilt"; it is in fact fully built, including a self-service editor. See §3.6. |
| 29 | L3 | games (hub) | C | `games_cog.py` | mapped | not-started | — | |
| 30 | L3 | blackjack | C | `blackjack_cog.py` | mapped | not-started | — | spike anchor; free-tournament double-pay live bug |
| 31 | L3 | rps_tournament | C | `rps_tournament_cog.py` | mapped | not-started | — | |
| 32 | L3 | deathmatch | C | `deathmatch_cog.py` | mapped | not-started | — | PvP double-settle live bug |
| 33 | L3 | fishing | B | `fishing_cog.py` | mapped | not-started | — | Q-0175 gates the sell leg |
| 34 | L3 | farm | B | `farm_cog.py` | mapped | not-started | — | 100% declarative once amendments land |
| 35 | L3 | creature | B | `creature_cog.py` + `creature_battle_cog.py` | mapped | not-started | — | |
| 36 | L3 | casino | B | `casino_cog.py` | mapped | not-started | — | honest floor 24%; no records store yet |
| 37 | L3 | counting + chain (merged family) | C | `counting_cog.py` + `chain_cog.py` | mapped | not-started | — | already-merged family per BUILD-PLAN |
| 38 | L3 | four_twenty | B | `four_twenty_cog.py` | mapped | not-started | — | |
| 39 | L3 | giveaways (ADD) | — | none (verified zero giveaway code) | mapped | not-started | — | the one genuine ecosystem gap |
| 40 | L3 | starboard (ADD) | — | `starboard_cog.py` (loaded, `disbot/config.py:90`) + `services/starboard_service.py` | mapped | not-started | — | ⚠ **CAPSTONE CONTRADICTION** — fully working (threshold/emoji/self-star/ignore-channels/panel), not a stub. See §3.6. |
| 41 | L3 | explore hub + wild encounters (ADD) | — | `games_cog.py` + `views/explore/world_hub.py`/`world_card.py` + `services/world_registry.py` (explore-hub half only) | mapped | not-started | — | ⚠ **PARTIAL CAPSTONE CONTRADICTION** — the registry-driven explore-hub router already ships; only "wild encounters" (Pokétwo-style catch loop) is genuinely new. Q-0182/Q-0186 order decided. See §3.6. |
| 42 | L3 | mining | B | `mining_cog.py` | mapped | not-started | — | **ports LAST** — whole-stack acceptance test |
| 43 | L4 | ai (platform) | D | `ai_cog.py` + `ai_review_cog.py` | mapped | not-started | — | REDESIGN into specs |
| 44 | L4 | btd6 | D | `btd6_cog.py` (mother cog: panel+ingestion lifecycle+unified `/btd6` tree), `btd6_reference_cog.py` (static lookups), `btd6_events_cog.py` (live NK data), `btd6_strategy_cog.py` (strategy memory+AI-denial diag), `btd6_ops_cog.py` (ingestion ops), `paragon_cog.py` (Paragon calculator) | mapped | not-started | — | confirmed 6-cog split is purely file-size hygiene (800-LOC cog ceiling), one KnowledgeDomainSpec-exemplar subsystem; legacy per-group cogs are now hidden prefix aliases behind the unified tree |
| 45 | L4 | project_moon | D | `project_moon_cog.py` | mapped | not-started | — | Limbus domain partially shipped |
| 46 | L4 | youtube / shared ingestion (ADD) | — | `media_maintenance_cog.py` + `services/youtube_fetch_service.py`/`video_reference_cache_service.py`/`youtube_context_service.py`/`youtube_diagnostics.py` | mapped | not-started | — | ⚠ **PARTIAL CAPSTONE CONTRADICTION** — YouTube fetch/cache/retention already ships (bespoke, ADR-007 shared-platform, deliberately not AI/BTD6-owned); the genuinely-new part is only the *shared, reusable* IngestionPipeline for btd6/project_moon to also consume. See §3.6. |
| 47 | L4 | utility | D | `utility_cog.py` | mapped | not-started | — | MERGE pack; also hosts `/myprofile` — see row 28 |
| 48 | L4 | general | D | `general_cog.py` | mapped | not-started | — | MERGE pack |
| 49 | L5 | web dashboard + live editor (ADD/REDESIGN) | — | `botsite/app.py` + `dashboard/app.py` (both read-only FastAPI, not a cog) | mapped | not-started | — | ⚠ **PARTIAL CAPSTONE CONTRADICTION** — two read-only dashboards already ship; genuinely new is only the write-capable live editor. See §3.6. |
| 50 | L5 | boards family (ADD) | — | none (new; `hermes_cog.py`'s admin-only dispatch bridge is a **dropped** near-neighbor, not a current implementation of this row) | mapped | not-started | — | one tagged-board primitive; likely P-1 2nd instance. **Owner-decided requirement (2026-07-05, replacing the dropped hermes_cog):** must include an AI-assisted, user-facing (not admin-gated) way for any member to report a bug or suggest an improvement about the bot, landing in this board. **Shape decided:** NL + a lightweight direct command (e.g. `/suggest`/`/feedback`) both land in the same board — owner-decided 2026-07-05. |
| 51 | L5 | bot-migration assistant (ADD) | — | none (new) | mapped | not-started | — | the anti-MEE6/Carl/Dyno wedge |
| 52 | L5 | Railway / ops control-plane (ADD, owner-gated) | — | none — `hermes_cog.py` does **not** map here (confirmed) | mapped | not-started | — | Railway/ops control-plane means drift-checker/deploy-alerts/shadow-clone/backups for the bot's *own hosting*; `hermes_cog.py` is a distinct thing (see non-cog queue) — no current cog implements this row |

## 3.7 Cross-cutting findings (recurring across rows — track once, don't re-litigate)

Findings that surface at multiple rows are platform-level, not per-subsystem. Tracked here once;
per-row records point back here instead of repeating the analysis.

- **Back/Home is not yet stack-aware.** Confirmed at rows 1 (settings) and 3 (help): "Back" is a
  fixed single jump or a shallow, non-persisted closure chain (`views/navigation.py` `BackTarget`/
  `chain_back`), not a real navigation-history stack, despite Q-0231 requiring contextual Back at
  every depth. "Home" (the universal 📚 Help button) **is** already fully solved — click-time
  re-resolved, works from anywhere. This is **Phase-B nav-engine work**, not any one subsystem's
  fix — no further owner decision needed per-row; every future row should just note "same known
  gap" rather than re-describing it.
- **Preset/template fragmentation, ≥7 reimplementations bot-wide.** Confirmed at row 1 (settings'
  numeric-presets widget) and row 3 (help has no preset concept at the hub level at all — only the
  unrelated setup-wizard `preset_select`). Already tracked pre-session as **C-3** (Q-0228). Stage-2's
  job per row is just to note "this row is a future C-3 consumer," not to design C-3 itself.
- **The `build_help_menu_view` dynamic-dispatch pattern (`get_cog`+`getattr`) is the entire
  cross-subsystem navigation backbone today** — confirmed used by 43 of 58 loaded extensions
  (`docs/help-command-surface-map.md`), and reached from **views-layer files** in at least 4 places
  (`views/settings/subsystem_view.py`, `views/hub_children.py`, `views/games/deathmatch_panel.py`,
  `views/games/rps_panel.py`) plus `views/navigation.py` itself importing `cogs.help_cog`/
  `cogs.help.panels` directly — a real `views → cogs` architecture-boundary violation, invisible to
  `scripts/check_architecture.py --mode strict` because every import is function-local/deferred.
  This is exactly what the already-ratified **R-11** (`HelpEntrySpec.dropdown_target: PanelRef`)
  retires. Not an owner decision — R-11 already exists as the fix; flagged here as concrete
  evidence for why R-11 matters, and as a candidate for this session's mandatory new-idea slot
  (improving the architecture checker to catch deferred cross-layer imports), not as rebuild scope.
- **G-10 (`ModalFormSpec`) breadth reconfirmed.** Help's own overlay editor uses 4 more hand-written
  `discord.ui.Modal` subclasses (`_RenameModal`, `_RedescribeModal`, `_TitleModal`, `_BodyModal`),
  consistent with the already-ratified 48-file G-10 count in `FINAL-REVIEW.md`. No new decision
  needed — reconfirms an existing ratified amendment applies here too.

## 4. Non-cog / platform capability queue (preserved separately per task instructions)

These must also receive a Stage-2 disposition but are not walked as ordinary product cogs:

| Item | What it is | Disposition state | Notes |
|---|---|---|---|
| L0 runtime skeleton | bootstrap, loader, config, bus, lifecycle, tasks, health, DB seam, namespace registry | `handled-via-gate-0` | Lane G already GO-verdicted (preserve 6 primitives field-for-field + build K1 namespace registry). `bootstrap_access_cog.py` is its one cog-visible slice (command-access gate installer) — pure platform wiring, not a product surface; carried here for coverage, no triage verdict needed. |
| `hermes_cog.py` | **confirmed**: the Discord-side entry point of the Hermes→Claude-Code dispatch bridge (`/bugreport`, `/dispatch` — both admin-gated slash commands that POST a work order to the Claude Code Routine `/fire` endpoint, spinning up an autonomous coding session). Not a guild/player-facing feature at all. | **decided — `drop`** (owner, 2026-07-05) | Does **not** map to the Railway/ops control-plane ADD row (that row is about the bot's own hosting/deploy ops, a different concern) — confirmed out of the bot-capability corpus per `NEW-BOT-BUILD-PLAN.md` §1.3's workflow/substrate carve-out. **Owner ruling:** not needed in the new bot's user-facing surface. Dependency recheck (S-2): zero dependents found (`hermes_cog.py`/`fire_work_order`/`HermesCog` referenced only by itself + the `disbot/config.py` extension list) — no dependent-row fallout. **The underlying goal survives, redirected**: an easy, AI-assisted way for *any* member (not admin-only) to report a bug or suggest an improvement about the bot — this becomes a concrete owner-endorsed requirement on the **boards family** ADD row (row 50), not a standalone row. Removing `hermes_cog.py` from the *current* repo (vs. just excluding it from the new-bot corpus) is a separate implementation action, out of this docs-only session's scope — flagged, not executed. |
| `setup_cog.py` / `quicksetup_cog.py` | **confirmed**: functioning today (`quicksetup_cog`=primary guided `!setup`/`/setup`, `setup_cog`=advanced `!setupadvanced`/`/setup-advanced` wizard + on-join launcher), reachable only via server_management's hub button | pending server_management walk (row 5) | **Confirmed structural gap** (not just "currently under"): `setup` has no `SUBSYSTEMS` registry key at all today. BUILD-PLAN's own note flags "register `setup` as real subsystem" — decide the split at row 5's walk. |

## 3.5 Command-surface ground truth (verified 2026-07-05 — supersedes the frozen 271-row JSON)

Per the readiness review's own warning, `ground-truth/command-surface.json` (271 rows: 224 prefix +
30 slash + 17 group) undercounts grouped command verbs — it is a **static AST scan** that stores one
row per top-level `@commands.group`/`app_commands.command` declaration and never descends into a
group's `.command()` subcommands. Booting the real bot in-process via the parity harness
(`parity/harness/boot.py`) and calling `disbot/core/runtime/command_surface_ledger.build_ledger()` —
the **live, fully-flattened** walk (`bot.walk_commands()` + `bot.tree.walk_commands()`) — gives the
actual current total:

**479 command entries = 406 prefix + 73 slash** (vs. the JSON's 271), confirmed independently by the
`parity/coverage.py` denominators (390/406 prefix, 64/73 slash). Example of the gap:
`btd6_ops_cog.py`'s `!btd6ops` group is **1 row** in the JSON but **7 real entries** live (the group
leaf + 6 subcommands). The live ledger also flags 13 cross-cutting findings today: 12 orphan
cog→subsystem mappings (cogs whose class name isn't a registered `SUBSYSTEMS` key — mostly the
btd6-family sub-cogs, `RoleGrantsCog`, `StarboardCog`, `SetupCog`/`QuickSetupCog`,
`CreatureBattleCog`) and 1 duplicate alias name (`create`).

**Per the Stage-1/readiness-review instruction, all future shared-verb / naming-collision / command
surface work in this walk uses `command_surface_ledger.build_ledger()` as ground truth, not the
frozen JSON.**

## 3.6 Capstone-accuracy contradictions found (rubric class 4 — stale/unanchored claim)

Verified 2026-07-05, source-cited. These are corrections *to the frozen BUILD-PLAN/FINAL-REVIEW
capstone itself* — not new owner decisions — surfaced here so no later reader trusts the stale label.
Each is also flagged on its row above (§3) and will get its full owner discussion when that row is
walked, not now:

1. **`/myprofile` is fully built** (row 28) — `utility_cog.py:114-146` + a read-only card
   (`views/profile/profile_view.py`) + a self-service editor (`views/profile/editor.py`) — but
   `NEW-BOT-BUILD-PLAN.md:82` calls it "decided (Q-0147) but unbuilt." Cleanest capstone miss found.
2. **Starboard ships today** (row 40) — `starboard_cog.py`, fully working (threshold/emoji/
   self-star/ignore-channels/panel) — but listed as `ADD-from-plans` (`NEW-BOT-BUILD-PLAN.md:94`).
3. **YouTube ingestion/caching ships today** (row 46) — bespoke fetch/cache/retention — but listed
   as a from-scratch ADD; the real gap is only the *shared, reusable* ingestion-pipeline
   abstraction btd6/project_moon would also consume.
4. **The "explore hub" half of "explore hub + wild encounters" already ships** (row 41) via
   `games_cog` + `views/explore/world_hub.py` (a registry-driven router into mining/fishing
   worlds); only "wild encounters" (the Pokétwo-style catch loop) is genuinely new.
5. **A read-only web dashboard already ships — twice over** (row 49): `botsite/app.py` (public
   site) and `dashboard/app.py` ("developer dashboard, read-only MVP"). The genuinely-new part of
   that ADD row is the write-capable live editor, not the dashboard's existence.

None of these change any row's eventual verdict by themselves — they change what "done" means for
that row (less net-new build, more "wire the existing thing into the unified manifest/hub"). Also
found, structural (not capstone-accuracy) gaps: **`setup` has no `SUBSYSTEMS` registry key** (row 5)
and **`hermes_cog.py` fits none of the 43+10 rows** (non-cog queue) — both flagged in place above.

## 5. Bidirectional coverage tracking

- **Coverage A (current → plan):** 58/58 loaded cogs assigned a row or non-cog-queue entry above.
  0 cogs currently unassigned. All 4 originally-flagged `needs-reconciliation` cogs resolved this
  round (starboard, media_maintenance, hermes, btd6-family split) — see §3.6.
- **Coverage B (plan → current):** all 43 shipped BUILD-PLAN rows + 9 ADD rows + L0 listed above.
  0 rows currently missing from this index. 5 rows carry a capstone-accuracy contradiction (§3.6).
- **Coverage C (commands/hidden functions):** not yet started at the per-command level — begins
  per-row during each walk. Ground truth for this work is now pinned (§3.5): 479 live commands.
- **Coverage D (dependency rechecks):** 2 rechecks completed — row 4 (admin) was the flagged
  dependent of row 2 (diagnostic)'s hub-merge decision (action recorded: 9→8 nav-button collapse);
  row 5 (server_management) resolved row 2's deferred mutation-surface-ownership question (no
  move — closed). No forward links open (the Q-0119 "open link" to row 6 was itself a
  documentation error, corrected this session — Q-0119 was already answered 2026-06-13, not a new
  decision to defer; row 6 ratifies execution only). 1 drop verdict processed — `hermes_cog.py`
  (owner, 2026-07-05, out of walk-order
  sequence): rechecked, zero dependents found, no fallout; its underlying goal redirected onto row
  50 (boards family). **1 new row created mid-walk** — row 5a (`setup`), split from row 5
  (`server_management`) per the BUILD-PLAN's own note + Lane A's explicit recommendation; carried
  into Coverage B below. **6 current-bot bug fixes queued (not implemented this session — scope
  boundary):** the settings AI-projection drift (row 1), admin's bot_spam typo + missing audit
  trail (row 4), moderation's slash-command authority bug (row 6), security's unaudited
  raid-lockdown slowmode edit (row 9), cleanup's two unaudited mutation paths (row 10), and role's
  3-of-8-table guild-teardown gap (row 13) — all owner-decided "fix now," all left as
  ready-to-execute specs for a dedicated bug-fix session. **1 long-standing Stage-1 decision
  resolved**: G-22 staging-lanes (open since 2026-07-03), closed at row 13 as a side effect of
  row 5a's earlier decision.

---

## 6. Per-subsystem records

Records are appended here as each row reaches a stable owner decision (§6 of the task template).
Rows in `owner-discussing` state show the dossier + questions presented, pending the owner's
answer — not yet a durable decision.

### Row 1 — settings

**Status: decided (2026-07-05).**

#### 0. Row identity
- BUILD-PLAN row: `settings` · Layer: L1a · Existing disposition: `KEEP`
- **Stage-2 verdict: `improve`** (owner-decided — tightens the bare capstone `keep`)
- Dependents to recheck: none — **correction (2026-07-05, caught verifying row 6):** Q-0119 was
  *not* an open decision to defer; it was already answered by the owner on 2026-06-13
  (`docs/planning/settings-pointer-lane-convergence-plan-2026-06-13.md` §5, "give authority its own
  home" — a reserved `governance` `SubsystemSchema` owns `moderator_role`/`trusted_role` as its own
  `BindingSpec`s, explicitly *not* re-homed under moderation). This session's earlier framing of it
  as "deferred to row 6" was itself a stale/unanchored-claim error (rubric class 4) — fixed here.
  The only real forward work is *executing* the already-decided answer in the rebuild's manifest
  grammar, ratified at row 6, not re-deciding it.
  (moderation)
- Source confidence: `source-confirmed` (live source read + 26 test files + design spec §4)

#### 1. User/job summary
- Primary user: guild administrators / the platform owner (operator-only surface)
- Job-to-be-done: "see and change how this bot behaves in my server without reading docs"
- Embarrassing-to-launch-without: one place to find every setting; a visible audit trail
- Prior art: itself — this is a port, not a new feature
- Competitor benchmark: Dyno/MEE6 web-config dashboards (target: parity, in-Discord, free)

#### 2. Command surface
| Command | Slash | Prefix | Aliases | Shared verb? | Kind | Effect | No-arg default? | Notes |
|---|---|---|---|---|---|---|---|---|
| Settings hub | `/settings` | `!settings` | none | no (unique verb) | both | read/safe-write (opens UI) | yes — opens hub | admin/owner-gated |
| Access explorer | — | `!settings access` | none | no | prefix-only | read | yes | independent of the manager kill-switch |
| Help direct-nav | — | — | — | — | panel-only | read | — | `build_help_menu_view` hook, becomes a declared `PanelRef` |

#### 3. Invocation and routing
- Fuzzy typo eligibility: `auto-run safe` (opening a hub is a safe read)
- NL intent eligibility: yes, candidate ("turn off welcome messages" → jump to that page) — not yet built
- NL orchestration eligibility: yes for compound requests, but rides the general C-2 draft/preview lane, not settings-specific; flag that scalar writes reached via any AI rung still need the Q-0225 confirm-before-act rule applied consistently
- Authority: one `settings.mutate`-class capability per setting (existing `capability_required`, empty = administrator floor) + platform-owner global override (already matches Q-0227 verbatim — no change needed)
- Cooldown: 2/10s/user today — folds into the future C-6 cooldown engine, no change needed now

#### 4. Namespace/collision review
- `settings` is a unique flat verb — stays flat top-level per Q-0224, no collision, K1 reserves it as-is

#### 5. Hub, navigation, presets
- Top-level bucket: Admin (hidden node per Q-0237(c))
- Direct-open: `!settings`/`/settings` already satisfies the navigation contract's direct-open rule (Q-0231)
- Gap found: today's "Back to Hub" is a single fixed jump, not the framework's contextual-stack-aware Back — flagged for the Phase-B nav-engine plan, not owner-blocking
- Preset membership: the Settings hub itself is not excludable by any preset (it's the config surface); per-subsystem page visibility follows that subsystem's own preset membership — flagged as an open point for Stage-3 consolidation

#### 6. Capability triage and exact scope
- **Keep:** three-lane split (scalar/binding/resource), one audited mutation pipeline, generated subsystem pages, 4 diagnostic sub-panels, Command Access panel, Access-policy explorer, tri-state resolve chain
- **Improve:** R-10 (`allowed_values` kernel enforcement at the mutation seam, not just a validator/widget hint); page-actionability (mutate bindings/resources in-place, not view+link-out only); Back/Home stack-awareness
- **Defer:** binding-mutation kill-switch parity → rebuild-scoped design note, no current urgency (owner-decided). Q-0119 is **not deferred — already answered 2026-06-13** (see corrected §0 above); ratified for execution at row 6.
- **Add:** none new for settings itself (the feedback-capability idea sits on row 50, not here)
- One-line reason: already the rebuild's best-fit subsystem (93%→96%) — `improve`, not bare `keep`, because 6 concrete named gaps are worth closing rather than silently porting forward unfixed.

#### 7. Concrete outperform targets
| Target type | Target |
|---|---|
| Parity target | Dyno/MEE6 web-config dashboards |
| Match | per-feature toggle, channel/role binding pickers, bounded numeric/enum editing, audit history |
| Beat | in-Discord (no separate site/login), free (no paywalled settings), full visible audit trail, tri-state per-guild/global default resolution |
| Self-explanatory edge | "Needs setup"/"Invalid settings"/"Missing bindings" self-diagnosis panels — no mainstream competitor bot ships this |

#### 8. Required engines/specs/seams
| Engine/spec/seam | Tier | In plan? | New/reused | Owner decision needed? |
|---|---|---|---|---|
| SettingSpec/BindingSpec/ResourceRequirement | T1 | yes (§2.5) | reused | no |
| SettingsMutationPipeline → kernel/workflow scalar lane | T1/T2 | yes (§4.1) | reused | no |
| R-10 `allowed_values` enforcement | T1 rider | yes (ratified) | reused | no |
| PanelSpec/NavigationSpec | T1 | yes (§2.3/§2.4) | reused | no |
| G-10 ModalFormSpec (number/text edit modals) | T2 | yes (ratified) | reused | no |
| C-3 preset/template primitive | T2 | proposed, unbuilt | reused-when-built | no — timing deferred this session |
| C-1 command resolver | T1 engine | proposed (endorsed) | reused-when-built | no |

#### 9. Data, import, lifecycle
- Stores: `guild_settings` (KV), `subsystem_bindings`, resource-requirement tables, `settings_mutation_audit`
- Import mapping: `imported` — verbatim tri-state import (design spec §4.4/§5.2): stored `false`/`true` import as explicit and keep winning forever; only *absent* rows arrive `unset` (the sole population any new `activation` default touches)
- Guild join/leave: no dedicated bootstrap/teardown beyond the `unset` terminus; each declaring subsystem owns its own binding/resource teardown
- Member erasure: n/a — guild-scoped, not member-scoped

#### 10. Verification oracle
- Oracle type: parity golden (a port+improve, not a new feature)
- Existing goldens: ~8,300 lines / 26 test files already cover round-trip edit/reset, every authority path, kill-switch behavior, audit-CHECK alignment — strong oracle to carry forward
- New goldens required: R-10 enforcement (reject an out-of-`allowed_values` write at the pipeline, not just the UI); the AI-projection atomicity fix (once built, see §12)

#### 11. Rubric pass — 10 probes
| # | Class | Result |
|---|---|---|
| 1 | Dependency-order inversion | None — settings correctly sits at L1a, before every consumer |
| 2 | Forgotten capability | None for settings itself (the adjacent forgotten item — hermes_cog's feedback-reporting goal — is resolved onto row 50) |
| 3 | Thin/underspecified step | N/A — unusually well-documented (93-96% fit, deep tests) |
| 4 | Stale/unanchored claim | **Found+fixed**: the 2026-06-12 production-readiness doc's 36/13/11 setting/binding/resource counts are stale vs. today's live 100/17/15 — recorded in-line so no later reader trusts the old figures |
| 5 | Fragmentation/reinvention | **Found**: presets reimplemented ≥7× bot-wide, settings' numeric-presets widget is one instance — tracked as C-3, timing deferred |
| 6 | Under/wrong-generalization | None found |
| 7 | Missing cross-cutting standard | **Found**: R-10 is exactly this class — already ratified as a rider |
| 8 | Verification hole | None — oracle is strong; the 2 live bugs found are correctness gaps, not verification holes (new goldens tracked in §10) |
| 9 | UX/lifecycle-contract gap | **Found**: Back is single-level, not stack-aware — flagged for Phase-B nav engine |
| 10 | Naming/collision risk | None — `settings` is a unique flat verb |

#### 12. Blockers and decisions
| Blocker type | Details | Resolution |
|---|---|---|
| Corrected finding | Q-0119 governance-binding schema home | **Already answered 2026-06-13** ("give authority its own home" — a reserved `governance` `SubsystemSchema`); this session's original "deferred to row 6" framing was a stale-claim error, corrected here. Row 6 ratifies execution, does not re-decide. |
| Live bug | AI-scalar → typed-policy projection is non-transactional (silent drift risk) | **Owner-decided 2026-07-05: queue a contained current-bot bug-fix PR.** Not implemented in this session — this Stage-2 walk is explicitly docs/planning-only and must not edit `disbot/` runtime code; recording it here is the durable "don't lose this" home until a bug-fix session picks it up. |
| Live bug | No operator kill-switch on binding mutation (asymmetric with settings/provisioning) | **Owner-decided 2026-07-05: defer to the rebuild's binding-lane design** — no evidence of live harm |
| Dependency not settled | Preset-widget migration timing to C-3 | Deferred — revisit when C-3 itself is scheduled, no artifact needed now |
| Source uncertainty | Restart-safety of the current `SettingsHubView` not confirmed either way this pass | Flagged for Phase-B verification, not owner-blocking |

#### 13. Stage-3 consolidation notes
- BUILD-PLAN row delta: verdict tightens from bare `KEEP` to `KEEP+IMPROVE` with 6 named closure items (R-10, page-actionability, Back/Home stack-awareness, preset-C3-candidacy, AI-projection atomicity, binding kill-switch parity)
- Gate-0 delta: none beyond the already-ratified R-10 rider — no new amendment needed
- Dependencies to recheck: row 50 (boards family) inherits the hermes_cog-replacement feedback requirement (already recorded there). Q-0119 is ratified for execution at row 6, not a dependency recheck (it was never an open question this walk introduced).
- Owner ratification needed: none outstanding — verdict and bug-fix priority were decided live this session; Q-0119 required no new decision, only correcting this record's mischaracterization of it

### Row 2 — diagnostic

**Status: decided (2026-07-05).**

#### 0. Row identity
- BUILD-PLAN row: `diagnostic` · Layer: L1a · Existing disposition: `IMPROVE`
- **Stage-2 verdict: `improve`** (confirmed, scoped concretely by 3 owner decisions)
- Dependents to recheck: mutation-surface ownership boundary deferred to row 5 (server_management)
- Source confidence: `source-confirmed`

#### 1. User/job summary
- Primary user: administrators / the platform owner only — no member-facing surface exists
- Job-to-be-done: "is the bot healthy, and can I see/fix operational state without SSH or raw logs"
- Embarrassing-to-launch-without: DB/migration integrity check, a health snapshot, log visibility
- Prior art: itself
- Competitor benchmark: "ops consoles of hobby bots" — no public comparator found; likely a genuine differentiator

#### 2. Command surface (52 total: 51 prefix + 1 slash — grouped; full per-command detail in the research transcript)
| Group | Commands | Verdict |
|---|---|---|
| Legacy hub | `!diagnostics`/`!diag` (8-button hub: status/latency/sysinfo/db/json/commands/errors/notify) | **merge** — becomes a hidden alias into `/platform` |
| `!lifecycle`/`!lc` | mirrors `!platform lifecycle` | **merge** — drop the duplicate, keep one implementation |
| `/platform` + 39 subcommands (runtime/status ×14, catalogues ×6, resources/rollout ×5, validation ×4, ops ×9) | the deep operator surface | **keep**, becomes the sole entry point |
| Unique-to-legacy-hub (4): `!list_commands_detailed`, `!find_command`, `!validate_json_files`, `!query_logs`/`!recent_errors`, `!test_notification` | not duplicated in `!platform` today | **keep**, fold into the unified `/platform` catalogue as new categories |
| Mutation surfaces (4): `!platform finding …`, `!platform flag`, `!platform backfill apply`, `!platform automation` | real audited writes inside a nominally read-only subsystem | **keep for now** — ownership boundary vs. server_management decided after row 5 |

#### 3. Invocation and routing
- Single entry point after merge: `/platform` (+ `!platform`); `!diagnostics`/`!diag`/`!lc` retained only as hidden legacy aliases resolving to the same panel
- Fuzzy typo eligibility: `auto-run safe` for every read-only view; the 4 mutation subcommands need the destructive/ambiguous confirm treatment already partially present (findings/flags/backfill/automation all route through audited pipelines today)
- Authority: single admin-or-owner floor today, matches Q-0227 as-is
- NL eligibility: plausible for read views ("is the bot healthy?" → health snapshot) — not yet built, not urgent

#### 4. Namespace/collision review
- `platform` stays the flat reserved verb; `diagnostics`/`diag`/`lc`/`lifecycle` become K1-reserved tombstone aliases pointing at the same panel, never a second implementation

#### 5. Hub, navigation, presets
- Top-level bucket: Admin (hidden node)
- One "Platform / Diagnostics" hub replaces the current two; 4 category selects (Runtime, Catalogues, Resources, Validation) plus the new unique-capability categories (Commands, Logs, Data-integrity, Notify-test)
- Direct-open: `/platform` already satisfies the navigation contract

#### 6. Capability triage and exact scope
- **Keep:** the `!platform` group's full 39-subcommand surface, all 4 mutation surfaces (ownership TBD), health_maintenance_cog's daily retention loop
- **Merge:** `!diagnostics`/`!diag` hub → into `/platform`; `!lifecycle` → drop duplicate, keep one
- **Improve:** adopt `DiagnosticProviderSpec` as one unified catalogue (owner-confirmed **required for done**), collapsing the two separate registries (`diagnostics_service`'s untyped sync callables + `health_snapshot_service`'s typed async adapters) and the ~20 hand-written command bodies
- **Defer:** mutation-surface ownership (findings/flags/automation/backfill vs. server_management) → decided after row 5
- One-line reason: functionality is complete and well-tested; the fit gap is pure registration-shape debt (two registries, hand-wired commands), not missing capability — collapsing to one hub + one catalogue is the entire "improve."

#### 7. Concrete outperform targets
| Target type | Target |
|---|---|
| Parity target | none found — likely a genuine differentiator vs. hobby-bot ops consoles |
| Beat | self-diagnosis breadth (11-adapter health snapshot, audience-redacted), in-Discord (no separate ops dashboard needed), fully audited mutation surfaces |

#### 8. Required engines/specs/seams
| Engine/spec/seam | Tier | In plan? | New/reused | Owner decision needed? |
|---|---|---|---|---|
| `DiagnosticProviderSpec` (name, provider HandlerRef, lane, audience, timeout, redaction, ownership) | T2 | proposed (sketched in `tools/grammar_spike/spec.py`) | **new — this row's core deliverable** | no — confirmed required this session |
| PanelSpec/SelectorSpec (the merged hub) | T1 | yes | reused | no |
| ManagedTaskSpec (health_maintenance's daily retention loop) | T1 | yes | reused | no |
| Audited mutation seam (findings/flags/automation/backfill) | T1/T3 | yes | reused | ownership deferred to row 5 |

#### 9. Data, import, lifecycle
- Stores: `operational_health_findings` + `operational_health_finding_aggregates` (migration 057); log ring buffer is in-memory only, not persisted
- Import mapping: `fresh-start` — this is process-generated operational telemetry, not user/guild data; nothing to import from the old bot
- Guild join/leave, member erasure: n/a — this data is process-scoped, not guild- or member-scoped

#### 10. Verification oracle
- Oracle type: parity golden
- Existing goldens: 30 dedicated test files already cover functional/reachability/authority/mutation-seam behavior (per the completion cert)
- New goldens required: merged-hub behavior (legacy aliases still resolve correctly); the unified `DiagnosticProviderSpec` catalogue's registration completeness (every command has exactly one provider entry)
- Known outstanding gap (pre-existing, not new): owner-led live Discord walkthrough has never happened (no sandbox AI-provider key) — carried forward, not blocking this row's verdict

#### 11. Rubric pass — 10 probes
| # | Class | Result |
|---|---|---|
| 1 | Dependency-order inversion | None — L1a position 2, after settings, before help |
| 2 | Forgotten capability | None |
| 3 | Thin/underspecified step | N/A |
| 4 | Stale/unanchored claim | **Found+fixed**: `docs/ownership.md` claimed diagnostic reads a `logs` table; actually an in-memory ring buffer — fixed this session. Also found, not yet fixed: a doc says "9 health-snapshot adapters," source shows 11 — flagged for someone to reconcile, not blindly edited (unverified by this pass) |
| 5 | Fragmentation/reinvention | **Found+decided**: `!diagnostics` vs `!platform` — owner decided merge |
| 6 | Under/wrong-generalization | **Found**: diagnostic (observability) has absorbed 4 real mutation surfaces — ownership boundary deferred to row 5, not resolved yet |
| 7 | Missing cross-cutting standard | **Found**: exactly the `DiagnosticProviderSpec` gap — owner confirmed required |
| 8 | Verification hole | None — strong existing oracle (30 test files) |
| 9 | UX/lifecycle-contract gap | None beyond the general Back/Home stack-awareness gap already flagged at row 1 (applies bot-wide, not diagnostic-specific) |
| 10 | Naming/collision risk | **Found+decided**: `!lifecycle` duplicates `!platform lifecycle` — owner decided merge to one implementation |

#### 12. Blockers and decisions
| Blocker type | Details | Resolution |
|---|---|---|
| Cross-row dependency | Mutation-surface ownership (findings/flags/automation/backfill: keep under diagnostic vs. move to server_management) | **Deferred to row 5's walk** — owner-decided 2026-07-05 |
| Doc drift (unverified) | "9 adapters" vs. 11 found in source for `health_snapshot_service` | Flagged for verification/fix by a future pass — not corrected here since only one source (the sub-agent) reported it |
| Known gap (pre-existing) | No owner-led live Discord walkthrough yet | Carried forward, not new, not blocking |

#### 13. Stage-3 consolidation notes
- BUILD-PLAN row delta: `IMPROVE` confirmed, scoped to 3 concrete deliverables (hub merge, unified catalogue, mutation-boundary TBD)
- Gate-0 delta: `DiagnosticProviderSpec` needs to be minted as a new amendment when Gate-0's grammar work resumes (it is currently only sketched in the grammar-spike prototype, not in the ratified G-1…G-24 list) — **flag for Gate-0**, not a Stage-2 owner call
- Dependencies to recheck: row 5 (server_management) inherits the mutation-boundary decision
- Owner ratification needed: none outstanding for this row

### Row 3 — help

**Status: decided (2026-07-05).**

#### 0. Row identity
- BUILD-PLAN row: `help` · Layer: L1a · Existing disposition: `KEEP`
- **Stage-2 verdict: `improve`**
- Dependents to recheck: none new this row (R-11's retirement of the dispatch pattern is a
  Phase-B kernel migration affecting all 43 consumer extensions, not a per-row Stage-2 recheck)
- Source confidence: `source-confirmed`

#### 1. User/job summary
- Primary user: everyone (discovery) + administrators (customization)
- Job-to-be-done: "what can this bot do, and how do I find it" / "let me customize what's shown without touching code"
- Embarrassing-to-launch-without: one coherent home — already avoided today
- Prior art: itself — explicitly named as shipped prior art to port in the rebuild's own hub/nav decisions doc (`rebuild-hub-navigation-presets-2026-07-03.md`)
- Competitor benchmark: Carl/Dyno help UX — target: "ours is generated so it cannot drift"

#### 2. Command surface
| Entry point | Slash | Prefix | Effect | Access |
|---|---|---|---|---|
| Category index / route | `/help [name]` | `!help [category]` (alias `!hilfe`) | read — opens index or routes to a hub panel | everyone (governance-filtered) |
| Help appearance editor | — | via `!settings` panel or staff-hub button | read/write — hide/rename/re-describe, Home-message builder | administrator/owner |
| `resolve_help_panel_state()` | — | internal API, not a command | lets other panels' own "📚 Help" buttons reuse Help's render logic | n/a |

#### 3. Invocation and routing
- Fuzzy: `auto-run safe` (read-only discovery)
- NL: a natural first target ("what can you do?") — not yet built, low-risk to add later
- Authority: everyone for discovery; administrator-or-owner for the editor (unchanged)
- R-11 target: replace the `get_cog`/`getattr(build_help_menu_view)` dispatch with a declared `PanelRef` per subsystem

#### 4. Namespace/collision review
- `help` is a unique flat verb, no collision, K1 reserves as-is

#### 5. Hub, navigation, presets
- Help **is** the front door/root, not nested under anything else
- Admin already lives inside as a hidden, gated node — matches Q-0230/Q-0237(c) with no further change needed
- **Owner-decided this session:** the overlay-editor view stack (`HelpEditorHomeView`/`EntityPickerView`/`HelpEntityEditorView`/`HomeMessageBuilderView`) upgrades from ephemeral 180s-timeout `BaseView`s to a **no-timeout persistent view**, fully closing the Q-0231 gap rather than accepting it as a scoped exception

#### 6. Capability triage and exact scope
- **Keep:** category index, the routing resolver, the overlay data model (hide/rename/re-describe), the Home-message builder's mandatory preview, the audit trail
- **Improve:** adopt **R-11** (`PanelRef` navigation, retiring the dynamic-dispatch pattern — affects all 43 consumer extensions at Phase-B); adopt **G-10** (modal-field schemas for the editor's 4 hand-written modals); **make the editor-stack views persistent/no-timeout** (owner-decided, upgraded from "accept exception")
- **Defer:** Back/Home stack-awareness and hub-level preset adoption — cross-cutting platform items, tracked once in §3.7, not this row's job
- One-line reason: already the rebuild's 2nd-best-fit subsystem (92%→96%) — `improve` means adopting the two amendments this subsystem is the poster child for, plus closing its own timeout gap.

#### 7. Concrete outperform targets
| Target type | Target |
|---|---|
| Parity target | Carl/Dyno help UX |
| Beat | generated-not-hand-written (cannot drift out of sync with the real command surface); audited customization; admin already hidden-not-shown-locked |

#### 8. Required engines/specs/seams
| Engine/spec/seam | Tier | In plan? | New/reused | Owner decision needed? |
|---|---|---|---|---|
| R-11 `HelpEntrySpec.dropdown_target: PanelRef` | T1 rider | yes (ratified) | reused when the kernel panel registry exists | no |
| G-10 `ModalFormSpec` | T2 | yes (ratified) | reused | no |
| Persistent/no-timeout view pattern (already exists, just needs applying to the editor stack) | T1 | yes | reused | no — confirmed this session |

#### 9. Data, import, lifecycle
- Store: `help_overlay` (migration 064, widened by 067)
- Import mapping: `imported` verbatim — a small deviation-only table, no transform needed
- Guild join/leave, member erasure: n/a — guild-scoped, absence-is-default

#### 10. Verification oracle
- Oracle type: parity golden
- Existing goldens: ~5,800 lines / 20 test files, including a reachability simulation and a doc-pinning test that fails CI on drift
- New goldens required: R-11 `PanelRef` resolution once the kernel panel registry exists; an editor-stack persistence/restart-recovery test (new, once the timeout fix ships)

#### 11. Rubric pass — 10 probes
| # | Class | Result |
|---|---|---|
| 1 | Dependency-order inversion | None — L1a position 3, correctly last of the foundation trio |
| 2 | Forgotten capability | None |
| 3 | Thin/underspecified step | N/A — unusually well documented |
| 4 | Stale/unanchored claim | **Found, not yet fixed**: `docs/help-command-surface-map.md`'s §1 hub table lists 7 rows but the registry has 8 (`project_moon` missing from that specific table, though present elsewhere in the doc) — flagged for a documentation-hygiene pass; not corrected here since it was reported by only one research pass and wasn't independently re-verified |
| 5 | Fragmentation/reinvention | Cross-cutting (§3.7) — help's lack of hub-level presets is part of the ≥7-instance preset fragmentation, tracked once, not re-litigated here |
| 6 | Under/wrong-generalization | None found specific to help |
| 7 | Missing cross-cutting standard | Cross-cutting (§3.7) — R-11/G-10, both already ratified |
| 8 | Verification hole | None — strong existing oracle |
| 9 | UX/lifecycle-contract gap | **Found+decided**: editor-stack timeout — owner decided to fix to no-timeout persistent, not accept as exception |
| 10 | Naming/collision risk | None |

#### 12. Blockers and decisions
| Blocker type | Details | Resolution |
|---|---|---|
| Doc drift (unverified) | `help-command-surface-map.md` §1 table undercounts hubs by 1 | Flagged for a future docs-hygiene pass — not fixed this session (single-source finding, not independently re-verified) |
| Owner decision | Editor-stack timeout | **Decided 2026-07-05: fix to no-timeout persistent view** |

#### 13. Stage-3 consolidation notes
- BUILD-PLAN row delta: `KEEP` → `KEEP+IMPROVE` (R-11, G-10, editor persistence)
- Gate-0 delta: none new — R-11/G-10 already ratified amendments, just confirmed applicable here
- Dependencies to recheck: none new
- Owner ratification needed: none outstanding

### Row 4 — admin

**Status: decided (2026-07-05).** Verified against the existing Lane A source-audit (2026-07-02) —
zero source drift found; all 11 commands and both known live bugs confirmed unchanged.

#### 0. Row identity
- BUILD-PLAN row: `admin` · Layer: L1b (first row of the operator spine) · Existing disposition: `KEEP+IMPROVE`
- **Stage-2 verdict: `improve`** (matches capstone as-is, no tightening debate needed)
- Dependents to recheck: none downstream; **admin is itself a dependent** of row 2's decided
  hub-merge (see §7 Notes below) — rechecked this row, action recorded
- Source confidence: `source-confirmed` (existing Lane A ledger + fresh zero-drift verification)

#### 1. User/job summary
- Primary user: bot owner / administrators (process control)
- Job-to-be-done: "manage the bot's own process — load code, sync commands, restart, tune logging — and jump to other admin panels from one place"
- Embarrassing-to-launch-without: cog lifecycle control, restart, slash sync
- Prior art: itself
- Competitor benchmark: typical hobby-bot admin cogs — "already ahead; audit trail completes it" (BUILD-PLAN's own words)

#### 2. Command surface (11, zero drift since 2026-07-02)
| Command | Access tier | Verdict |
|---|---|---|
| `!adminmenu`/`/admin`, `!serverstats`, `!coglist`, `!slashes`, `!loglevel` (6, `admin_or_owner()`) | `ADMINISTRATOR` | keep |
| `!cog`, `!loadall`, `!unloadall`, `!syncslash`, `!restart` (5, `commands.is_owner()`) | `PLATFORM_OWNER` (stricter, already a distinct tier in `governance/permission_tiers.py:29-60`) | keep — deliberate escape hatches, no declarative primitive should model these |

#### 3. Invocation and routing
- Two authority tiers map cleanly onto the rebuild's already-decided model (Q-0227/Q-0237(d)):
  `ADMINISTRATOR` for the 6, `PLATFORM_OWNER` for the 5 — no new authority primitive needed, just
  correct per-command tagging
- Fuzzy: the 5 `PLATFORM_OWNER` process-control commands must never auto-run from a fuzzy typo
  match (destructive/ambiguous class); the read-only commands (`serverstats`/`coglist`/`slashes`)
  qualify as safe auto-run candidates

#### 4. Namespace/collision review
- No collisions found. Final naming (`!adminmenu` vs. a shorter form, etc.) deferred to Stage-3's
  broader naming pass rather than decided in isolation here.

#### 5. Hub, navigation, presets
- Reached as a destination from Help, not itself the front door
- **Mechanical consequence of row 2 (diagnostic)'s decided hub-merge:** admin's hub currently has
  9 nav buttons; once diagnostic's `!diagnostics`→`/platform` merge ships, the separate
  "🩺 Diagnostics" and "🛰 Platform" buttons collapse to one, dropping admin to **8 nav buttons**.
  The surviving button should route through the standard `_open_via_help_hook` dispatch (calling
  `DiagnosticCog.build_platform_help_menu_view`, which already exists for exactly this) instead of
  its current hand-rolled direct `_PlatformHubView` construction — a code-duplication fix, not a
  new decision.

#### 6. Capability triage and exact scope
- **Keep:** all 11 commands, the cog manager view (incl. protected-cog denial), slash-sync tooling
- **Improve:** adopt **R-11** for the nav-button dispatch (already decided at row 3 — fixes admin's
  single biggest fit-driver automatically, no new work needed here beyond applying it); collapse
  9→8 nav buttons once row 2 ships; **build the `admin.operator_action` audit trail** (owner-decided
  full scope — all 5 mutation types: cog load/unload/reload, restart, log-level); **fix the
  `bot_spam`/`bot-spam` typo** (owner-decided, fix now)
- One-line reason: functionality is clean; the fit gap is dispatch-shape (already solved by R-11
  elsewhere) plus one real governance gap (no audit trail) plus one silly typo bug.

#### 7. Concrete outperform targets
| Target type | Target |
|---|---|
| Parity | typical hobby-bot admin cogs — already ahead |
| Beat | full audit trail on process-level operator actions (few/no hobby bots log "who restarted the bot and when") |

#### 8. Required engines/specs/seams
| Engine/spec/seam | Tier | In plan? | New/reused | Owner decision needed? |
|---|---|---|---|---|
| R-11 `PanelRef` navigation | T1 rider | yes (ratified, decided row 3) | reused | no |
| `PLATFORM_OWNER` authority tier | T1 | already exists (`governance/permission_tiers.py`) | reused — tagging only | no |
| Audited mutation seam (`services.audit_events.emit_audit_action`) | T1 | already exists, used bot-wide | reused — needs wiring into 5 new call sites | no — confirmed this session |

#### 9. Data, import, lifecycle
- No new store needed — the audit trail writes to the same shared audit log every other
  subsystem's mutations already use
- Import mapping: n/a — admin owns no persisted table of its own

#### 10. Verification oracle
- Oracle type: parity golden
- Existing goldens: strong on panel *shape* (15-component layout, 9 nav destinations by label,
  dispatch success/missing-cog/exception paths) but several buttons are asserted only for
  label/shape, not behavior (Stats, Reload All, Log Level)
- New goldens required once the bug fixes land: `on_ready` channel resolution (post-typo-fix);
  audit-trail emission for all 5 mutation types; the Platform button's post-merge single-hook
  dispatch

#### 11. Rubric pass — 10 probes
| # | Class | Result |
|---|---|---|
| 1 | Dependency-order inversion | None — L1b position 1 is correct; admin's hub only *launches into* other subsystems, it doesn't require them built first |
| 2 | Forgotten capability | None |
| 3 | Thin/underspecified step | N/A |
| 4 | Stale/unanchored claim | **Found+corrected before repeating it to the owner**: admin's 45.0% as-written is *not* the lowest in the 43-row corpus (casino 16%, channel 31.7%, moderation 41.5%, blackjack 44.4%, deathmatch 44.9% are all lower) — its real distinction is the largest single as-written→amended swing |
| 5 | Fragmentation/reinvention | **Found**: the Platform button duplicates `DiagnosticCog`'s own purpose-built sibling hook instead of calling it |
| 6 | Under/wrong-generalization | None |
| 7 | Missing cross-cutting standard | None new — R-11 and `PLATFORM_OWNER` already exist, just need applying |
| 8 | Verification hole | **Found**: `on_ready` untested; several buttons tested for shape only, not behavior — tracked as new-goldens-required |
| 9 | UX/lifecycle-contract gap | Cross-cutting Back/Home gap applies here too — tracked once in §3.7, not re-described |
| 10 | Naming/collision risk | None found |

#### 12. Blockers and decisions
| Blocker type | Details | Resolution |
|---|---|---|
| Live bug | `bot_spam`/`bot-spam` typo (dead `on_ready` greeting) | **Owner-decided 2026-07-05: fix now.** Exact fix: `admin_cog.py:412`, `"bot_spam"` → `"bot-spam"`. **Not implemented in this session** — this Stage-2 walk is explicitly docs/planning-only, and mixing a runtime fix into this docs-only born-red PR would also violate the repo's risk-based PR-sizing convention (small focused PRs for `disbot/` changes). Recorded here as a ready-to-execute one-line fix for the next bug-fix session. |
| Live bug | Zero audit trail on 5 high-privilege mutations | **Owner-decided 2026-07-05: fix now, full scope** (all 5 types, including log-level). **Not implemented in this session**, same reasoning as above. Ready-to-execute spec: wrap `cog_manager.py:96,105,114` (load/unload/reload), `admin_cog.py:365` (restart), and `admin_cog.py:393` + `_LogLevelModal` (`admin_cog.py:763-790`, log-level) with `services.audit_events.emit_audit_action(subsystem="admin", mutation_type=...)` calls, one per action. |
| Mechanical consequence | Admin's 9→8 nav-button collapse once row 2 ships | Recorded, not yet actionable (row 2's merge itself isn't built) |

#### 13. Stage-3 consolidation notes
- BUILD-PLAN row delta: none needed — capstone's `KEEP+IMPROVE` already matches exactly
- Gate-0 delta: none — R-11 and `PLATFORM_OWNER` are already-existing primitives
- Dependencies to recheck: **done this row** — admin was the flagged dependent of row 2's
  hub-merge decision (S-2 recheck), action recorded above
- Owner ratification needed: bug-fix priority is decided (fix now, full scope); execution itself
  is deferred to a dedicated current-bot bug-fix session, flagged clearly to the owner

### Row 5 — server_management

**Status: decided (2026-07-05).** Research confirmed `server_management` and `setup`/`quicksetup`
are operationally two subsystems today, joined only by one hub button — **`setup` is split out to
its own row (5a)** below, matching the BUILD-PLAN's own "register `setup` as real subsystem" note
and Lane A's explicit recommendation (`lane-A-governance.md:908,916`).

#### 0. Row identity
- BUILD-PLAN row: `server_management` (now scoped to just the hub+badges) · Layer: L1b · Existing disposition: `KEEP+IMPROVE`
- **Stage-2 verdict: `improve`**
- Dependents to recheck: **this row resolves row 2's deferred question** (see §6)
- Source confidence: `source-confirmed`

#### 1. User/job summary
- Primary user: administrators — a launch pad + at-a-glance health badges for 4 operator domains
- Job-to-be-done: "is my server basically healthy, and let me jump into moderation/channels/roles/cleanup from one place"
- Prior art: itself

#### 2. Command surface
| Command | Effect | Access |
|---|---|---|
| `!servermanagement`/`/server-management` (+2 aliases) | opens the hub | `admin_or_owner()` |

#### 3. Invocation and routing
- Administrator-or-owner floor throughout; R-11 (already decided at row 3) fixes this row's dispatch too — no new decision needed

#### 4. Namespace/collision review
- No collisions found

#### 5. Hub, navigation, presets
- Nested under Admin in Help; 5 buttons: 4 routed managers (Moderation/Channels/Roles/Cleanup) + Setup handoff (now points at row 5a) + Access Map/Help Preview/Help-editor/Refresh

#### 6. Capability triage and exact scope
- **Keep:** all 5 badges (each individually fail-safe, never blanks the hub), the routed-manager dispatch, Access Map/Help Preview projections
- **Improve:** adopt R-11 for the dispatch (2 distinct shapes today — 4 routed-manager buttons + a differently-built Help-editor button — both collapse to one declared `PanelRef` pattern)
- **Decided (Lane 0, not re-asked — strong, one-sided evidence):** diagnostic's 4 mutation surfaces (findings/flags/automation/backfill) do **NOT** move here. Reasoning: (1) server_management's entire `KEEP` verdict rests on being a zero-write, zero-capability, pure router — Lane A explicitly scores this as by-design; adding any mutation surface breaks the invariant its fit score depends on. (2) All 4 are platform/process-ops concerns (bot-wide operational health, feature-flag rollout, scheduled-automation rules, one-time legacy-pointer migration), categorically different from server_management's guild-facing moderation/channel/role/cleanup domain. (3) They're already correctly owned and documented under diagnostic/platform services. **This closes row 2's deferred question — no dependent fallout.**
- One-line reason: already the correct shape (a pure router); the only debt is the dispatch-pattern shape R-11 already fixes elsewhere.

#### 7-11. (Outperform / engines / data / oracle / rubric)
- Outperform: no new specific target beyond the platform-wide "in-Discord, free, live-health" framing already captured for the L1b band
- Engines: R-11 (reused, decided elsewhere); the `HubStatus` badge composer stays a justified, permanent tier-3 escape hatch (real branching diagnostic logic — no primitive should absorb it)
- Data: owns no table (confirmed)
- Oracle: parity golden; existing tests strong (664 lines covering routing, fallback, badge fail-safety)
- Rubric findings: **stale claim found** — `docs/subsystems/server-management.md` still lists `setup_cog.py`/`views/setup/` as part of server management without reflecting the 2026-06-24 Essential-Setup front-door cutover; **not fixed this session** (the split just happened — correcting the doc now would need to reflect the new row 5a boundary, deferred to row 5a's Stage-3 consolidation to avoid a second edit)

#### 12. Blockers and decisions
| Blocker type | Details | Resolution |
|---|---|---|
| Doc drift | `docs/subsystems/server-management.md` stale re: setup's cutover + the new row 5a split | Flagged; fix deferred to row 5a's Stage-3 consolidation |

#### 13. Stage-3 consolidation notes
- BUILD-PLAN row delta: row now scoped to hub+badges only; `setup` moves to its own row (5a)
- Dependencies to recheck: row 2's forward link **closed this row** (no move)
- Owner ratification needed: none outstanding

### Row 5a — setup (new row, split from server_management)

**Status: decided (2026-07-05).**

#### 0. Row identity
- BUILD-PLAN row: **new** — created this session per the BUILD-PLAN's own "register `setup` as real subsystem" note (`NEW-BOT-BUILD-PLAN.md:59`) and Lane A's explicit recommendation (`lane-A-governance.md:908,916`: setup should get its own registered `SUBSYSTEMS` entry + `SubsystemManifest`, not a sub-component nested in server_management's — it owns 2 tables, a delegated-authority model, a dedicated private channel, and ~15,000 lines of tests, none of which server_management's manifest has a field for)
- Layer: L1b (inherited from its former home)
- **Stage-2 verdict: `redesign`** — the user job (guided server configuration) stays, but the
  mechanism changes materially: the draft/Final-Review lane is retired, folded into Essential
  Setup's direct-lane model
- Dependents to recheck: **`setup_diagnostics.staged_repair_ops` currently stages its repair
  proposals through the same `SetupOperation`/Final-Review draft lane** being retired here — its
  replacement mechanism (direct-lane apply, or its own confirm step) is Phase-B design work, not
  decided this session, but flagged now so it isn't discovered late. No change to row 2's
  (diagnostic) own verdict — this is additive scope for whoever designs the fold.
- Source confidence: `source-confirmed`

#### 1. User/job summary
- Primary user: guild owners / delegated setup-admins, first-run and ongoing configuration
- Job-to-be-done: "get my server usably configured, guided, without needing to understand every setting"
- Prior art: itself (Essential Setup)
- Competitor benchmark: typical bot onboarding wizards — outperform via delegated authority, an AI "describe my server" advisor, and resumable multi-session setup (none of which are common)

#### 2. Command surface (14 entries — see the research dossier for full file:line detail; condensed here)
| Entry point | Lane | Effect | Access |
|---|---|---|---|
| `!setup`/`/setup` (quicksetup) | **direct** | opens Essential Setup's 8-step guided spine, each step writes immediately | `admin_or_owner()` |
| `!setupadvanced`/`/setup-advanced` | **draft** | opens the section-list → stage → Final Review wizard in a dedicated `#superbot-setup` channel | owner/delegate for write; plain admin gets read-only readiness |
| `!setupdescribe`/`/setup-describe` | draft (propose-only) | NL description → AI-proposed plan → review panel, no writes until accepted | `admin_or_owner()` |
| `/setup-delegate`/`/setup-undelegate` | — | grant/revoke delegated setup-admin | **owner-only** |
| `/setup-depth`, `/setup-skip`/`/setup-unskip`, `/setup-reset`, `/setup-status` | draft | wizard configuration/state commands | owner/delegate |
| `/setup-hub` | — | legacy section-list hub, **self-flagged `legacy_duplicate`** already | owner/delegate/admin ladder |
| `on_guild_join`/`on_ready` | — | launcher post/resume + Essential-Setup revive sweep | system |

#### 3. Invocation and routing
- Two genuinely different mutation lanes under one nominal subsystem (see §6) — this is the row's central architectural finding
- Delegated authority (`setup_delegate`) is a bounded, live-re-verified, auditable-as-distinct actor type — a real differentiator vs. typical bots
- On-join launcher deliberately opens Essential Setup only, never Advanced (existing source comment) — confirmed correct as the onboarding default, not a new decision

#### 4. Namespace/collision review
- `/setup-hub` already self-flagged `legacy_duplicate` — good existing hygiene, no action needed

#### 5. Hub, navigation, presets
- Reached via server_management's Setup button (row 5) **and** directly via its own commands (already satisfies Q-0231's direct-open rule)
- A dedicated private `#superbot-setup` channel backs the Advanced wizard — a genuinely different navigation shape than every other subsystem's panel-based UI

#### 6. Capability triage and exact scope
- **Keep:** Essential Setup's entire 8-step direct-lane spine (works, heavily tested — ~40 test functions per step); the on-join launcher + resume sweep; the delegated-authority model; the AI advisor (propose-only, never auto-applies)
- **Redesign (owner-decided 2026-07-05): retire the Advanced wizard's draft→Final-Review lane, fold into Essential Setup.** The unique sections only the Advanced wizard reaches today (`role_templates`, `cog_routing`, `ticket`, `preset_select`, and whatever of `channels`/`roles`/`moderation`/`cleanup`/`logging_presets` isn't already covered by Essential's 8 steps) become new Essential Setup steps or get folded into existing ones — **the exact per-section mapping is Phase-B design work**, not decided here; Stage 2 records the directional decision and target shape only. Once nothing consumes the draft lane, the `SetupOperation`/`FinalReviewView`/`PartialApplyRecoveryView` machinery itself is retired (with the noted diagnostic dependent, §0, needing its own new home).
- **Add:** register `setup` as **one** `SUBSYSTEMS` entry covering both entry surfaces (owner-decided 2026-07-05) — the direct-vs-draft split was an internal implementation detail, not a product-facing boundary, and this decision retires that split anyway.
- One-line reason: the guided/direct-lane half is real, tested, working product; the draft-lane half was the one genuinely broken piece, and folding it into the working model is more honest than maintaining two mutation lanes for one setup experience.

#### 7. Concrete outperform targets
| Target type | Target |
|---|---|
| Beat | delegated setup authority (most bots don't have this); an AI "describe my server" advisor (no comparator found); resumable multi-session setup surviving restarts |

#### 8. Required engines/specs/seams
| Engine/spec/seam | Tier | In plan? | New/reused | Owner decision needed? |
|---|---|---|---|---|
| `SetupOperation` draft lane (stage → Final Review) | T2 | exists | reused — pending the Q1 directional call | yes — see below |
| A proposed `WizardSpec`-class primitive for stateful, multi-step lifecycle (Lane A's own suggestion, `lane-A-governance.md:916`) | T2 | proposed, not in the ratified G-1…G-24 list | new | **owner-gated design work, flagged for Gate-0/Phase-B — not a Stage-2 call** |

#### 9. Data, import, lifecycle
- Stores: `setup_session` (one row/guild), `setup_draft_operations` (append-only staging)
- Import mapping: `fresh-start`, with a carried "already onboarded" completion signal — guilds that finished setup under the old bot should not be re-prompted to onboard under the new one; in-progress/draft state does not need to survive the cutover
- Guild join: the on-join launcher/channel-creation flow is itself the bootstrap — no separate bootstrap step needed

#### 10. Verification oracle
- Oracle type: parity golden
- Existing goldens: exceptionally strong on Essential Setup (~15,000 lines across 35+ files, per-step apply/skip/create-vs-reuse coverage) — this half needs little new verification work
- New goldens required: entirely dependent on the Q1 answer below — whichever path the Advanced wizard takes needs its own golden suite built fresh, since its current functional state is disputed

#### 11. Rubric pass — 10 probes
| # | Class | Result |
|---|---|---|
| 1 | Dependency-order inversion | **Found**: setup consumes nearly every other L1b subsystem's mutation seam (channel, role, ticket, cleanup, automation) — structurally it should port **near the end** of L1b, not adjacent to server_management (2nd position). Flagged for Stage-3 re-sequencing, not fixed in the live walk order this session. |
| 2 | Forgotten capability | None |
| 3 | Thin/underspecified step | N/A — very well documented |
| 4 | Stale/unanchored claim | Same `docs/subsystems/server-management.md` drift noted at row 5 — ties directly to this row's Stage-3 consolidation now that the split is real |
| 5 | Fragmentation/reinvention | None new beyond the already-tracked cross-cutting items |
| 6 | Under/wrong-generalization | **Found — the central finding**: "setup" conflates two incompatible mutation-lane models (direct vs. draft) under one nominal cog/name pairing |
| 7 | Missing cross-cutting standard | **Found**: the proposed `WizardSpec` primitive — flagged for Gate-0, not decided here |
| 8 | Verification hole | Tied to the Advanced wizard's disputed functional state — see §10 |
| 9 | UX/lifecycle-contract gap | Cross-cutting Back/Home applies (§3.7); otherwise none new |
| 10 | Naming/collision risk | None — `/setup-hub` already self-flagged |

#### 12. Blockers and decisions
| Blocker type | Details | Resolution |
|---|---|---|
| Owner decision | Advanced wizard's fate | **Decided 2026-07-05: retire, fold into Essential Setup** |
| Owner decision | Registration model | **Decided 2026-07-05: one `SUBSYSTEMS` entry, two entry surfaces** |
| Dependency fallout | `setup_diagnostics.staged_repair_ops` depends on the draft lane being retired | Flagged for whoever designs the fold (Phase-B) — not resolved this session |
| Gate-0 item | `WizardSpec` primitive design | Not a Stage-2 call — flagged for Gate-0/Phase-B |

#### 13. Stage-3 consolidation notes
- BUILD-PLAN delta: new row created (`setup`, split from `server_management`), verdict `redesign` — must be carried into the consolidated Stage-3 surface record
- Gate-0 delta: `WizardSpec`-class primitive needs consideration
- Dependencies to recheck: **build-order position** — likely needs to move later within/after L1b given its consumer relationship to channel/role/ticket/cleanup/automation; **`setup_diagnostics`'s repair-op mechanism** needs a new home once the draft lane retires; Stage-3 should re-sequence and re-check both
- Owner ratification needed: none outstanding — both decisions made live this session

### Row 6 — moderation

**Status: decided (2026-07-05).**

#### 0. Row identity
- BUILD-PLAN row: `moderation` · Layer: L1b · Existing disposition: `IMPROVE`
- **Stage-2 verdict: `improve`** (confirmed, matches capstone)
- Dependents to recheck: none — **Q-0119 correction**: this row does not re-decide the
  `moderator_role`/`trusted_role` binding-schema home; that was already answered 2026-06-13 (a
  reserved `governance` `SubsystemSchema`, not moderation's own). Row 1's mischaracterization of
  this as an open deferral is fixed (see row 1 §0). This row just ratifies executing that existing
  answer in the rebuild's manifest grammar.
- Source confidence: `source-confirmed` (Lane A audit + fresh zero-drift verification)

#### 1. User/job summary
- Primary user: moderators/administrators
- Job-to-be-done: warn/timeout/kick/ban with a consistent audit trail and an escalation ladder
- Embarrassing-to-launch-without: consistent authority across every surface a mod might use — the
  one thing currently broken (see §2)
- Competitor benchmark: Dyno — match configurability, beat on free + audited + privacy-forward
  public log; add case/appeal + bulk actions

#### 2. Command surface (9 entries) and a confirmed live bug
| Command/entry | Access mechanism | Verdict |
|---|---|---|
| `!warn`/`!timeout`/`!kick`/`!ban`/`!unban`/`!clearwarnings`/`!modlogs`, `!modmenu` (panel, 7 buttons) | dual-floor: raw Discord permission OR governance capability (`can_execute`/`can_execute_ctx`) | keep — this is the correct shape |
| `/moderation` (slash) | **confirmed bug**: raw Discord permission OR platform-owner only — never checks governance capability, so it ignores a configured `moderator_role` entirely | **improve — fix now** |

#### 3. Invocation and routing
- Three surfaces (prefix/panel/slash) currently resolve authority via 3 different code paths —
  R-2 (already ratified) unifies these onto one `authority_ref`, closing the slash bug structurally
  as a side effect of the redesign (not just the current-bot patch, see §12)
- The hierarchy check (can this mod act on this target) is implemented twice today (prefix vs.
  interaction) — R-2/the mod-action envelope collapses this to one declared field

#### 4. Namespace/collision review
- No collisions found

#### 5. Hub, navigation, presets
- Reached via Admin → Moderation; no changes needed beyond the bot-wide R-11 dispatch fix (already decided)

#### 6. Capability triage and exact scope
- **Keep:** the audited mutation seam (`_record_action`'s 3-signal fan-out — mod_logs row, audit
  event, domain event, all sharing one `mutation_id` — the cleanest part of this subsystem), the
  escalation ladder, DM-notify, post-action cleanup
- **Improve:** fix the slash-authority bug now (owner-decided, current-bot PR); convert the
  already-clean behavior (hierarchy check, DM step, cleanup step, escalation logic — all already
  isolated, thin functions) into the Q-0226 declarative mod-action envelope + R-2's unified
  authority — mostly conversion, not redesign, since the hard behavioral calls were made in the
  Phase-A conventions freeze
- **Add (owner-decided 2026-07-05, committed scope, not deferred):** a case/appeal system
  (persisted case ID + reopen flow) and bulk moderation actions (mass-ban/mass-timeout) — both
  named "outperform adds" in the frozen plan, now committed as required Phase-B deliverables for
  this row rather than accepted-but-unscoped future options
- One-line reason: the seam is already excellent; the gap is authority-story fragmentation (already
  solved by decided conventions) plus one live bug plus two committed new features

#### 7. Concrete outperform targets
| Target type | Target |
|---|---|
| Match | Dyno's automod-adjacent filter configurability |
| Beat | free + fully audited + a privacy-forward public log; case/appeal (Dyno lacks this); bulk actions |

#### 8. Required engines/specs/seams
| Engine/spec/seam | Tier | In plan? | New/reused | Owner decision needed? |
|---|---|---|---|---|
| Declarative mod-action envelope (Q-0226) | T2 | yes (decided) | reused — conversion target | no |
| R-2 `legacy_permission_floor`/resource-owner authority rider | T1 rider | yes (ratified) | reused | no |
| Case/appeal persistence (new) | T1/T2 | not yet designed | **new** | design work owed to Phase-B, scope committed here |
| Bulk-action batching (new) | T2 | not yet designed | **new** | design work owed to Phase-B, scope committed here |

#### 9. Data, import, lifecycle
- Stores: `warnings`, `mod_logs` (confirmed accurately owned, no drift)
- New stores needed: a case/appeal table (case ID, status, reopen history) — Phase-B design
- Import mapping: `imported` — existing warning counts and mod-log history carry forward verbatim

#### 10. Verification oracle
- Oracle type: parity golden
- Existing goldens: solid on the mutation/policy core (1,141-line service test alone); the
  three-surface authority-consistency gap is **confirmed untested** — `test_slash_privileged.py`
  only asserts *some* check exists, not *which* one, so it would not have caught the live bug
- New goldens required: all-three-surfaces-resolve-identically (would have caught the bug); case/appeal; bulk actions

#### 11. Rubric pass — 10 probes
| # | Class | Result |
|---|---|---|
| 1 | Dependency-order inversion | None — L1b position correct |
| 2 | Forgotten capability | None |
| 3 | Thin/underspecified step | N/A |
| 4 | Stale/unanchored claim | **Found+fixed**: row 1's Q-0119 mischaracterization (see row 1 §0) |
| 5 | Fragmentation/reinvention | **Found**: the hierarchy check duplicated across prefix/interaction — collapses under the envelope |
| 6 | Under/wrong-generalization | None |
| 7 | Missing cross-cutting standard | None new — R-2/Q-0226 already ratified |
| 8 | Verification hole | **Found**: no test proves all 3 surfaces resolve authority identically — exactly why the bug shipped unnoticed |
| 9 | UX/lifecycle-contract gap | Cross-cutting Back/Home applies (§3.7) |
| 10 | Naming/collision risk | None |

#### 12. Blockers and decisions
| Blocker type | Details | Resolution |
|---|---|---|
| Live bug | `/moderation` ignores configured `moderator_role` | **Owner-decided 2026-07-05: fix now.** Ready-to-execute spec: route `moderation_slash`'s authority check (`moderation_cog.py:96-97`) through `can_execute`/`can_execute_ctx` the same way the prefix (`_require_mod`, `:29-52`) and panel (`main_panel.py:45-61`) already do. Not implemented this session — scope boundary, same as the row 1/row 4 bug fixes. |
| Owner decision | Case/appeal + bulk actions scope | **Decided 2026-07-05: commit to building both**, not deferred |
| Corrected finding | Q-0119 | Not this row's decision — already answered 2026-06-13; ratify execution only |

#### 13. Stage-3 consolidation notes
- BUILD-PLAN row delta: `IMPROVE` confirmed; case/appeal + bulk actions promoted from "named outperform add" to "committed Phase-B deliverable"
- Gate-0 delta: none new — R-2/Q-0226 already ratified
- Dependencies to recheck: rows 8 (automod), 9 (security), 10 (cleanup) all reuse moderation's
  action seam (`auto_delete`/`warn`/`kick`) — the envelope conversion here affects their own
  Phase-B plans; flag when those rows are walked
- Owner ratification needed: none outstanding

### Row 7 — logging

**Status: decided (2026-07-05).**

#### 0. Row identity
- BUILD-PLAN row: `logging` · Layer: L1b · Existing disposition: `KEEP`
- **Stage-2 verdict: `keep`** (confirmed, not tightened — genuinely different from every other L1b
  row so far: no subsystem-specific gap found, only generic grammar-conversion work every
  subsystem gets)
- Dependents to recheck: none
- Source confidence: `source-confirmed` — the 97% fit figure independently reproduced from source

#### 1. User/job summary
- Primary user: administrators wanting audit visibility
- Job-to-be-done: route mod actions, generic audit events, and passive Discord activity to
  configured channels
- Competitor benchmark: ProBot/Carl — target: reach DM-log + webhook-route depth on the
  route/panel spine already present

#### 2. Command surface
6 commands under `!logging` (status/set/create/routes/test + bare), all `admin_or_owner()`. No
slash commands exist — confirmed, not a gap (no owner ask for one).

#### 3. Invocation and routing
- **Confirmed intentional, not a bug (owner-decided 2026-07-05):** `!logging`'s own surface stays
  admin-only even though the bindings/settings underneath independently honor finer delegated
  capability via `!settings`. Not aligned to match — a deliberate stricter default for this
  subsystem's native command surface, left as-is.

#### 4-5. Namespace / hub
- No collisions; reached via Admin → Moderation → Logging (unchanged)

#### 6. Capability triage and exact scope
- **Keep:** all 8 gateway listeners, the 11-route binding table, the fail-safe send paths (every
  path counts + swallows, never crashes the bus), the v2 audit-log integration
- **Grammar conversion only (not a subsystem-specific improvement):** G-1×8 (each listener as a
  declared `GatewayListenerSpec`), G-3 (the 11 routes as one `AnnouncementRouteSpec` family), the
  route-truth alias declaration (already true in runtime behavior — `resolve_log_channel` already
  tries the binding first — just needs to become declared data instead of hand-written branches)
- **Confirmed, not this row's decision:** the `on_when_bound` safe-default-ON flip is already
  ratified at the design-spec level as logging's reference case; it ships as part of that
  cross-cutting rollout-review gate, not a fresh triage call here
- One-line reason: the highest-fit subsystem in the whole corpus for a reason — behavior is
  already correct; only its *representation* (code vs. declared data) changes

#### 7-11. (Outperform / engines / data / oracle / rubric)
- Outperform: ProBot/Carl DM-log + webhook-route depth (already-declared target, no new decision)
- Engines: G-1, G-3 (both already ratified, reused)
- Data: owns no table (confirmed)
- Oracle: parity golden; 259 test functions + 7 golden fixtures — one of the strongest oracles in L1b
- Rubric findings: **stale claim found+fixed** — the completion cert (`docs/planning/feature-completion/units/logging.md`) predated the v2 work and listed punch #2 as open; fixed this session. Two stale in-source docstring comments found (zero functional impact) — not fixed (editing `disbot/` files is out of this session's scope even for comment-only changes); flagged for the next bug-fix session alongside the queued live-bug fixes.

#### 12. Blockers and decisions
| Blocker type | Details | Resolution |
|---|---|---|
| Owner decision | `!logging` admin-only vs. delegated-capability-aware | **Decided 2026-07-05: leave as admin-only, intentional** |
| Doc drift | Two stale docstring comments (`schemas.py`, `routes_panel.py`) — zero functional impact | Flagged for the next bug-fix/cleanup session, not fixed this session (comment-only edits to `disbot/` files are still out of this docs-only session's scope) |
| Doc drift | Completion cert stale re: punch #2 | **Fixed this session** (pure docs, no scope conflict) |

#### 13. Stage-3 consolidation notes
- BUILD-PLAN row delta: none — `KEEP` confirmed exactly as capstone stated
- Gate-0 delta: none — G-1/G-3 already ratified
- Dependencies to recheck: none new
- Owner ratification needed: none outstanding

### Row 8 — automod

**Status: decided (2026-07-05).**

#### 0. Row identity
- BUILD-PLAN row: `automod` · Layer: L1b · Existing disposition: `KEEP+IMPROVE`
- **Stage-2 verdict: `improve`** (confirmed, matches capstone)
- Dependents to recheck: inherits row 6 (moderation)'s flagged note — automod is one of the seam's
  current callers (`auto_delete`/`warn`), so its own Phase-B conversion tracks onto whatever shape
  the Q-0226 mod-action envelope takes
- Source confidence: `source-confirmed`

#### 1. User/job summary
- Primary user: administrators wanting baseline spam/abuse filtering without manual moderation effort
- Job-to-be-done: catch obvious spam/invite/caps/mention abuse automatically, defaulting OFF
- Competitor benchmark: MEE6/Carl/Dyno baseline — matched; ordered fail-open audited pipeline is the edge

#### 2. Command surface
`!automod` (read-only status embed) + the help-menu hook. No slash command, no panel — all
configuration via `!settings → Automod` (11 `SettingSpec`s, borrowing moderation's
`moderation.settings.configure` capability — "automod *is* moderation's automated layer").

#### 3-5. Invocation / namespace / hub
- No collisions; reached via Admin → Moderation → Automod (unchanged)

#### 6. Capability triage and exact scope
- **Keep:** all 4 rule detectors, the exempt list, the fail-open discipline at two independent
  fault classes, the pipeline order (5, before cleanup/counting/chain/image_mod)
- **Improve:** adopt G-11 (`MessagePipelineStageSpec` — collapses the hand-written `AutomodStage`
  shell + its load/unload registration boilerplate into one declared row, leaving only the
  `HandlerRef` to `process_message` as real code)
- **Decided (owner, 2026-07-05):** the "one auto-mod tier operator surface with cleanup/image_mod"
  aspiration (named in both capstone docs, never designed) is **punted, not committed either way**
  — revisit once rows 10 (cleanup) and 15 (image_moderation) are also walked, since the shape needs
  all three subsystems in view
- One-line reason: functionality and safety discipline are already correct; the fit gap is pure
  registration-shape debt, identical pattern to logging's G-1/G-3 conversion

#### 7-11. (Outperform / engines / data / oracle / rubric)
- Outperform: MEE6/Carl/Dyno baseline matched; ordered fail-open pipeline is the differentiator
- Engines: G-11 (ratified, reused)
- Data: owns no table (confirmed) — pure scalar settings
- Oracle: parity golden; 432-line test suite (matches BUILD-PLAN's own citation exactly) — but the
  **detector-fault fail-open path is implemented, not forced-fault-tested** (only the config-read
  fault has a forced-raise test) — new golden needed
- Rubric findings: stale/orphaned capability string `automod.settings.configure` found (declared,
  nothing checks it — the real enforced one is `moderation.settings.configure`) — pure registry
  drift, zero functional impact, **not fixed** (it's in `disbot/utils/subsystem_registry.py`, out
  of this session's scope even as a one-line correction)

#### 12. Blockers and decisions
| Blocker type | Details | Resolution |
|---|---|---|
| Owner decision | Auto-mod-tier consolidation with cleanup/image_mod | **Decided 2026-07-05: punt — revisit after rows 10/15** |
| Verification gap | Detector-fault fail-open path untested by forced-raise | Flagged for a future goldens pass, not blocking |
| Doc/registry drift | Orphaned `automod.settings.configure` capability string | Flagged, not fixed (in-scope-boundary `disbot/` file) |

#### 13. Stage-3 consolidation notes
- BUILD-PLAN row delta: **auto-mod-tier consolidation resolved at row 15** (2026-07-05) — automod
  gets a minimal single-page panel wrapping its existing status embed, linked from a new button on
  cleanup's hub; no new shared primitive built
- Gate-0 delta: none — G-11 already ratified
- Dependencies to recheck: none — resolved
- Owner ratification needed: none outstanding

### Row 9 — security

**Status: decided (2026-07-05).**

#### 0. Row identity
- BUILD-PLAN row: `security` · Layer: L1b · Existing disposition: `KEEP+IMPROVE`
- **Stage-2 verdict: `improve`** (confirmed, matches capstone)
- Dependents to recheck: inherits row 6 (moderation)'s flagged note — confirmed `security_service`
  calls `moderation_service.kick` directly for account-age auto-kick, zero parallel audit path of
  its own
- Source confidence: `source-confirmed`

#### 1. User/job summary
- Primary user: administrators wanting automated raid/join-abuse protection
- Job-to-be-done: catch and respond to raids and suspicious new-account joins automatically
- Competitor benchmark: Wick — close the quarantine/join-viz gaps; beat on no-PII/fail-open/audited-kick

#### 2. Command surface
`!security` — one read-only status embed. All configuration via `!settings → Security` (11
`SettingSpec`s). No panel, no slash command — matches automod's minimal-surface pattern.

#### 3-5. Invocation / namespace / hub
- No collisions; reached via Admin → Moderation → Security (unchanged)

#### 6. Capability triage and exact scope
- **Keep:** both approved tiers (raid detection, account-age filter), the fail-open join-dispatch
  discipline, the timed auto-restore mechanism, the deliberate absence of tiers 3/4 (privacy-declined)
- **Improve, owner-decided fix now:** the unaudited raid-lockdown slowmode edit — same live-bug
  class as rows 1/4/6, queued as a ready-to-execute current-bot fix
- **Add, owner-decided committed scope (matches row 6's pattern):** the quarantine (role-isolation)
  action approved at Q-0111 but never built — genuine new design work (role-isolation mechanism,
  reversibility decision), committed as a Phase-B deliverable, not deferred
- Adopt G-9 (`DeferredActionSpec`) for the restore timers — already ratified, this is the 3rd
  confirmed consumer alongside proof_channel and utility
- One-line reason: the approved tiers work correctly and safely; the gaps are one audit-trail bug
  and one never-built approved feature

#### 7-11. (Outperform / engines / data / oracle / rubric)
- Outperform: Wick — close quarantine/join-viz gaps; beat on no-PII/fail-open/audited-kick
- Engines: G-9 (ratified, 3rd confirmed consumer); quarantine likely reuses `role_automation`'s
  already-audited system-actor seam (the same one `welcome_service` uses for entry-role grants)
- Data: owns no table (confirmed) — pure scalar settings + in-memory detector state
- Oracle: parity golden; 27 tests confirmed exactly (not the stale cert's "~32") — but **every
  existing test uses alert-only mode; the actual buggy slowmode code path has zero test coverage**,
  exactly why the bug shipped unnoticed
- Rubric findings: **verification hole found** — the untested slowmode path; new goldens required
  once the fix lands

#### 12. Blockers and decisions
| Blocker type | Details | Resolution |
|---|---|---|
| Live bug | Unaudited raid-lockdown slowmode edit | **Owner-decided 2026-07-05: fix now.** Ready-to-execute spec: route `security_service.py:186-193,196-213` (`_apply_slowmode`/`_lift_lockdown`) through `ChannelLifecycleService().apply(operation="set_slowmode", ...)`, the same seam `!slowmode` already uses. Not implemented this session — scope boundary, same as the other queued bug fixes. |
| Owner decision | Quarantine action | **Decided 2026-07-05: commit to building now** as a Phase-B deliverable |

#### 13. Stage-3 consolidation notes
- BUILD-PLAN row delta: `IMPROVE` confirmed; quarantine promoted from "approved-but-unbuilt" to "committed Phase-B deliverable"
- Gate-0 delta: none — G-9 already ratified
- Dependencies to recheck: none new
- Owner ratification needed: none outstanding

### Row 10 — cleanup

**Status: decided (2026-07-05).**

#### 0. Row identity
- BUILD-PLAN row: `cleanup` · Layer: L1b · Existing disposition: `KEEP domain, IMPROVE impl`
- **Stage-2 verdict: `improve`** (confirmed, matches capstone)
- Dependents to recheck: inherits row 6 (moderation)'s flagged note — confirmed cleanup's
  per-message deletions route through `moderation_service.auto_delete`; inherits row 8 (automod)'s
  punted auto-mod-tier consolidation question — **still not decided**, awaiting row 15
  (image_moderation)
- Source confidence: `source-confirmed`

#### 1. User/job summary
- Primary user: administrators wanting message-hygiene automation + on-demand bulk cleanup
- Job-to-be-done: auto-delete prohibited content; let a mod bulk-clean a channel by criteria
- Competitor benchmark: Carl/MEE6/Dyno purge parity — outperform via scope-chain policies beyond it

#### 2. Command surface
6 commands, all prefix-only (confirmed zero slash commands): `!cleanuphistory` (7 scan modes:
keyword/commands/prohibited/spam/embeds/links/attachments), `!word` (+add/remove/list),
`!wordmenu`, `!cleanup` (policy hub).

#### 3. Invocation and routing
- The last true interactive `bot.wait_for` in the entire runtime is here (`!cleanuphistory`'s
  ✅/❌ reaction-confirm, `cleanup_cog.py:438-443`) — confirmed still live
- G-24 (or a simpler composition of existing `MutationPreview`/`ConfirmationSpec` primitives, per
  its own spec-pass instruction) replaces this interaction pattern — already a settled design
  answer, no new owner decision needed

#### 4-5. Namespace / hub
- No collisions; reached via Admin → Moderation → Cleanup (unchanged)

#### 6. Capability triage and exact scope
- **Keep:** the message-pipeline stage (order 10), the 7 scan modes, the policy panel's genuinely
  exemplary preview→confirm→audited-apply flow (this half is already correct)
- **Improve, owner-decided fix now:** both confirmed unaudited mutation paths — word/strict-list
  toggles (zero audit calls) and `!cleanuphistory`'s bulk delete (unaudited when cleanup calls it
  directly, audited when the identical function is called from moderation). **Important
  distinction the research surfaced**: fixing the `wait_for` confirm-UX (G-24) does **not** by
  itself fix the audit gap — these are two separate fixes, both needed.
- **Improve, accepted scope (no controversy, folded in without a separate question):** add a slash
  surface, matching every sibling L1b subsystem
- Adopt G-11 (`MessagePipelineStageSpec`) — cleanup is one of 3 named exemplars alongside automod/image_moderation
- One-line reason: the policy-panel half is already the exemplar; the command half has two real,
  confirmed audit gaps plus the one remaining legacy interaction pattern

#### 7-11. (Outperform / engines / data / oracle / rubric)
- Outperform: Carl/MEE6/Dyno purge parity (explicit target) + scope-chain policies beyond it
- Engines: G-24 (composition-first, ratified), G-11 (ratified, 3rd exemplar)
- Data: `prohibited_words`, `wordfilter_config`, `cleanup_policies` — confirmed accurately owned
- Oracle: parity golden; strong coverage on the 7 scan modes and the `wait_for` paths, but **no
  test asserts audit-trail emission for either unaudited path** — the same verification-hole
  pattern that let rows 4/6/9's bugs ship unnoticed
- Rubric findings: orphaned capability string `cleanup.settings.configure` (declared, not
  registered) — pure registry drift, zero functional impact, not fixed (in-scope-boundary `disbot/` file)

#### 12. Blockers and decisions
| Blocker type | Details | Resolution |
|---|---|---|
| Live bug (2 paths) | Word/strict toggles + `!cleanuphistory` bulk delete, both unaudited | **Owner-decided 2026-07-05: fix now, both paths.** Ready-to-execute spec: route `cleanup_cog.py:505,524,705` (word/strict writes) and `cleanup_cog.py:447`'s call into `history_cleanup.apply_history_cleanup_plan` through the same `_record_action`-style audited wrapper `moderation_service.py:292-350` already uses for the identical function. Not implemented this session — scope boundary, same as the other queued bug fixes. |
| Cross-row | Auto-mod-tier consolidation with automod/image_moderation | **Resolved at row 15**: cleanup's existing hub gains 2 new buttons linking to automod's/image_moderation's new minimal panels |
| Doc/registry drift | Orphaned `cleanup.settings.configure` capability string | Flagged, not fixed (in-scope-boundary `disbot/` file) |

#### 13. Stage-3 consolidation notes
- BUILD-PLAN row delta: none — verdict matches capstone exactly
- Gate-0 delta: none — G-11/G-24 already ratified
- Dependencies to recheck: none — resolved at row 15
- Owner ratification needed: none outstanding

### Row 11 — counters

**Status: decided (2026-07-05).** A near rubber-stamp row: zero live bugs, zero unaudited paths,
full test coverage — the first L1b row with no owner-sensitive open item.

#### 0. Row identity
- BUILD-PLAN row: `counters` · Layer: L1b · Existing disposition: `KEEP (re-bin)`
- **Stage-2 verdict: `keep`** (confirmed, matches capstone)
- Dependents to recheck: none
- Source confidence: `source-confirmed`

#### 1. User/job summary
- Primary user: administrators wanting a live server-stat "statdock" (member/human/bot counts on
  channel names)
- Job-to-be-done: rename up to 3 pre-existing operator-bound channels to show a live count via a
  `{count}` template — never creates channels
- Competitor benchmark: Statbot-class — declarative presets + rate-limit-aware sync

#### 2-6. Surface, invocation, hub, triage
- Commands: `!counters`/`/counters` (status), `!counterpreset [name]` (list/apply-all-3 via the
  audited `SettingsMutationPipeline`) — confirmed fully audited, no gaps
- **Confirmed re-bin is sound, not cosmetic**: originally filed under Lane B (economy) purely by
  file location; it's a pure operator-configuration feature (admin-gated even under its nominal
  Community hub placement today) with zero economy/game mechanics
- **Keep:** the rename-on-diff mechanism (rate-limit safety — zero Discord calls on a no-op sync),
  the per-guild exponential backoff (`GuildSyncBackoff`, shipped PR #1575), the preset catalog
- **Improve (mechanical, no owner decision needed):** port the 3 channel settings to `BindingSpec`
  (mirrors logging's already-established pattern — this is the BUILD-PLAN's "depends on: logging"
  note, a manifest-pattern dependency, not a runtime import); adopt R-7
  (`ManagedTaskSpec.error_policy += per_target_backoff`) — counters' own backoff is R-7's cited
  concrete example; fold `!counterpreset` into G-15's kernel workflow (already adversarially settled)

#### 7-11. (Outperform / engines / data / oracle / rubric)
- Fit: 21 units, 81.0% as-written → 95.2% with amendments (confirmed exact)
- Rubric findings: **stale claim found+fixed** — the completion cert's closing verdict still
  listed loop backoff as an open gap after it shipped (PR #1575, 2026-06-30); fixed this session
  (pure docs, no scope conflict)

#### 12. Blockers and decisions
None outstanding — no live bugs, no unaudited paths, no owner-sensitive open item.

#### 13. Stage-3 consolidation notes
- BUILD-PLAN row delta: none — `KEEP (re-bin)` confirmed exactly as capstone stated
- Gate-0 delta: none — R-7/G-15 already ratified
- Dependencies to recheck: build after row 7 (logging) for the `BindingSpec` pattern to exist first (already true in the frozen L1b build order)
- Owner ratification needed: none outstanding

### Row 12 — channel

**Status: decided (2026-07-05).** No live bug found — a first among the L1b rows so far; the gap
here is pure surface-shape debt, not correctness.

#### 0. Row identity
- BUILD-PLAN row: `channel` · Layer: L1b · Existing disposition: `IMPROVE`
- **Stage-2 verdict: `improve`** (confirmed, matches capstone)
- Dependents to recheck: none
- Source confidence: `source-confirmed`

#### 1. User/job summary
- Primary user: administrators managing server channel structure
- Job-to-be-done: create/delete/rename/move/configure channels without the Discord UI
- Competitor benchmark: web-dashboard bots — batch ops + in-Discord audit trail is structural (already an edge)

#### 2. Command surface (17 prefix verbs, 0 slash — confirmed 2nd-lowest as-written fit in the whole
43-row corpus, 31.7%, beaten only by casino)
All 17 route through the sole audited seam, `ChannelLifecycleService` — confirmed no bypass.
Verbs: `!channelmenu`, `!set`, `!evt`, `!create`, `!bulkdelete`, `!del`, `!list`, `!clone`, `!move`,
`!lock`, `!unlock`, `!channelinfo`, `!rename`, `!slowmode`, `!topic`, `!permissions`, `!bulkcreate`.

#### 3. Invocation and routing
- The exact verb→slash mapping is confirmed **Phase-B design work**, not this row's job — Stage 2
  scopes the amendments and dead-code decisions, matching the pattern already set at rows 4/5a
- Each verb re-derives its own channel/category text resolver instead of using native
  `ChannelSelect`/`RoleSelect` widgets already used elsewhere in the codebase — G-23 fixes this

#### 4-5. Namespace / hub
- No collisions; reached via Admin → Server Management → Channels (unchanged)

#### 6. Capability triage and exact scope
- **Keep:** the audited `ChannelLifecycleService` seam (typed request → per-target result →
  reversibility → audit+event → confirm gate — already the exemplar shape), the 5 panel views,
  the list pagination (already covered by the existing Table/List+BrowserView primitives, no new
  amendment needed — G-A8 was proposed but is redundant)
- **Improve:** adopt G-18 (`ResourceLifecycleSpec` — covers 12 of 17 commands + 5 panels, the
  "channel + role 2-for-1" confirmed via `RoleLifecycleService`'s identical shape) and G-23
  (`EntityResolverRef`/argument schema — same 12 commands, replaces the hand-written resolver)
- **Add, owner-decided (2026-07-05, against my recommendation — recorded as a genuine decision,
  not a rubber stamp):** wire up voice-channel creation as a real feature. The `kind="voice"` code
  path already exists in `ChannelLifecycleService` but no live caller ever reaches it (all 6 call
  sites create text channels) — this becomes committed scope to add a real command/panel entry
  point, not delete the branch.
- **Drop, owner-decided (2026-07-05):** the 5 orphaned capability strings
  (`channel.create.text`/`.create.voice`/`channel.delete.any`/`channel.restrict.apply`/
  `channel.visibility.configure`) — never actually checked by any command (the real gate is
  `audience_tier`-based `administrator-or-owner`); remove rather than carry forward
- One-line reason: the seam is already the exemplar; the fit gap is pure grammar/registration
  debt, plus two small dead-code decisions now resolved

#### 7-11. (Outperform / engines / data / oracle / rubric)
- Outperform: web-dashboard bots — batch ops + in-Discord audit trail (already structural)
- Engines: G-18, G-23 (both ratified, reused); G-A8/`PaginatedBlockSpec` confirmed **not needed** —
  already covered by the merged spec's existing Table/List + BrowserView primitives
- Data: owns no table (confirmed)
- Oracle: parity golden; strong existing coverage (557+193+306+119-line test files) — new goldens
  needed for the voice-creation feature once designed
- Rubric findings: **fragmentation found** — 17 independent resolver implementations where native
  Discord select widgets already solve this elsewhere in the codebase; fixed by G-23

#### 12. Blockers and decisions
| Blocker type | Details | Resolution |
|---|---|---|
| Owner decision | Dead voice-create branch | **Decided 2026-07-05: wire it up** (add a real command/panel entry point) — against Lane-0's delete recommendation, recorded as a genuine owner call |
| Owner decision | 5 orphaned capability strings | **Decided 2026-07-05: delete** (matches Lane-0's recommendation) |

#### 13. Stage-3 consolidation notes
- BUILD-PLAN row delta: voice-channel creation promoted from "dead code, wire-or-delete" to
  "committed new feature" — Phase-B needs a concrete design (command/panel shape) for it
- Gate-0 delta: none — G-18/G-23 already ratified; G-A8 confirmed redundant
- Dependencies to recheck: none new
- Owner ratification needed: none outstanding

### Row 13 — role

**Status: decided (2026-07-05).** The largest subsystem in the corpus (108 units, tied with
mining). This row also **closes the G-22 staging-lanes decision**, open since Stage 1
(2026-07-03) — a genuine pre-existing owner decision this walk resolved as a side effect of row
5a's earlier decision.

#### 0. Row identity
- BUILD-PLAN row: `role` · Layer: L1b · Existing disposition: `IMPROVE`
- **Stage-2 verdict: `improve`** (confirmed, matches capstone)
- Dependents to recheck: G-18 confirms the "channel + role 2-for-1" (`RoleLifecycleService`
  structurally mirrors `ChannelLifecycleService`, already decided at row 12)
- Source confidence: `source-confirmed`

#### 1. User/job summary
- Primary user: administrators (role config) and members (self-service role menus)
- Job-to-be-done: manual role CRUD, automated tenure/XP role progression, self-service reaction
  roles, temp-role grants
- Competitor benchmark: Carl-bot — already ahead on batched failure reporting + server-side menu
  modes + live counters (Carl paywalls these)

#### 2. Command surface
17 prefix commands, **zero slash commands** — confirmed the only Lane A subsystem with none. 7 of
the 17 are hidden legacy-duplicate commands, each self-tagged in its own code
(`legacy_duplicate`/`panel_action`/`internal_admin`) admitting they exist only because panel
buttons were added after the command surface.

#### 3. Invocation and routing
- **G-22 resolved this session (owner-decided): bless `RoleMenuBuilder`'s view-local staging
  pattern as the sole instance, do not build a shared `StagedBuilderSpec` primitive.** Row 5a's
  earlier decision to retire the setup-wizard's draft lane removed one of the three staging lanes
  G-22 was weighing (direct-mutation / setup's persisted draft / RoleMenuBuilder's in-memory
  draft) — leaving RoleMenuBuilder as the only real consumer of this shape. Per S-1's
  second-consumer rule, this is exactly the "keep it specific, shape behind a clean seam" case,
  not the "build the engine" case. **This closes a decision that had been open since Stage 1**
  (`rebuild-stage1-global-review-2026-07-03.md` §6).
- "Add slash mirrors" — accepted improve-scope, no separate question needed (matches the pattern
  every other L1b row is getting)

#### 4-5. Namespace / hub
- No collisions; reached via Admin → Server Management → Roles (unchanged)

#### 6. Capability triage and exact scope
- **Keep:** the automation engines (tenure/XP threshold reconciliation, `RoleAutomation`), the
  three reaction-role modes (normal/unique/verify) with server-side enforcement, live sign-up
  counters, temp-role grants
- **Improve, owner-decided fix now:** the 3-of-8-table guild-teardown gap
  (`role_thresholds`/`role_automation_exemptions`/`reaction_roles`) — same bug class as rows
  4/6/9/10, plus the false "self-cleans" code comment needs correcting
- **Improve, accepted scope (folded in without separate questions):** collapse the 7 hidden
  legacy-duplicate commands into pure panel actions; add slash mirrors for the highest-traffic
  commands; delete the dead `views/roles/main_panel.py` (`RoleHubView`, zero callers); delete the
  3 orphaned capability strings (only 1 of 4 is ever checked); de-duplicate the reconciliation
  logic shared between the daily sweep and on-join assignment
- Adopt G-18 (`ResourceLifecycleSpec`, already ratified, confirmed 2-for-1 with channel) and G-21
  (`RecordTableSpec`, ratified — role is its sole today-instance: exemptions, per-role config)
- One-line reason: the engines are sound and already beat Carl-bot on several axes; the gaps are a
  live teardown bug, command-surface debt from panel-button retrofitting, and one now-resolved
  cross-cutting design question

#### 7-11. (Outperform / engines / data / oracle / rubric)
- Outperform: already ahead of Carl-bot on batched failure reporting + server-side menu modes +
  live counters (paywalled there)
- Engines: G-18, G-21 (ratified, reused); G-22 **resolved this session** — not generalized
- Data: 8 tables confirmed; 5 have teardown, 3 don't (the live bug)
- Oracle: parity golden; extensive existing coverage (41 test files, ~8,965 lines)
- Rubric findings: **fragmentation found** — `role_check` (daily sweep) and `on_member_join`
  independently rebuild identical threshold-filtering logic; **dead code found** — 159-line unused
  view file; **capability mismatch found** — 3 of 4 declared strings never checked

#### 12. Blockers and decisions
| Blocker type | Details | Resolution |
|---|---|---|
| Owner decision (Stage-1 carryover) | G-22 staging-lanes standardization | **Resolved 2026-07-05: bless RoleMenuBuilder as the sole instance, don't generalize** — closes an item open since Stage 1 |
| Live bug | 3-of-8-table guild-teardown gap + false "self-cleans" comment | **Owner-decided 2026-07-05: fix now.** Ready-to-execute spec: add teardown calls for `role_thresholds`/`role_automation_exemptions`/`reaction_roles` to `guild_lifecycle.py` (alongside the existing 5-table pattern at `:661-768`), and correct the false comment at `guild_lifecycle.py:70-72,664-666`. Not implemented this session — scope boundary, same as the other queued bug fixes. |

#### 13. Stage-3 consolidation notes
- BUILD-PLAN row delta: none — `IMPROVE` confirmed exactly as capstone stated
- Gate-0 delta: **G-22 removed from the open-decision list** — resolved, "bless as sole instance"
- Dependencies to recheck: none new
- Owner ratification needed: none outstanding

### Row 14 — ticket

**Status: decided (2026-07-05).** No live correctness bug — a second row (after channel) where
the gap is unreachable functionality and verification holes, not broken behavior.

#### 0. Row identity
- BUILD-PLAN row: `ticket` · Layer: L1b · Existing disposition: `KEEP+IMPROVE`
- **Stage-2 verdict: `improve`** (confirmed, matches capstone)
- Dependents to recheck: none
- Source confidence: `source-confirmed`

#### 1. User/job summary
- Primary user: members needing support, staff managing tickets
- Job-to-be-done: open a private support channel, staff claim/manage it, close with a transcript
- Competitor benchmark: Ticket Tool — free transcripts (they paywall this); add auto-close/SLA,
  categories, reopen

#### 2. Command surface
17 prefix commands, **zero slash commands** — confirmed. **Verified "cleanest audited seam in
Lane A" reputation holds up exactly**: all 3 open entry points (command/panel/AI) funnel through
one eligibility gate and one mutation seam, 7 distinct audited call sites, every write transactional.

#### 3. Invocation and routing
- 4-condition authority mechanism confirmed exactly as documented: ticket opener OR staff role OR
  admin OR platform owner (`views/tickets/_shared.py:21-35` + an inline opener-only override
  duplicated at 2 sites)

#### 4-5. Namespace / hub
- No collisions; reached via Admin → Server Management → Tickets (unchanged)

#### 6. Capability triage and exact scope
- **Keep:** the audited open/claim/close/participant seam (the exemplar), the 3-entry-point
  eligibility gate, the transcript+DM+teardown close flow
- **Add, owner-decided (2026-07-05):** expose `category_id` (new category-picker dropdown on the
  config panel — currently read by ticket-open logic but never settable) and
  `ping_staff_on_open` (new on/off toggle — currently always-on, no way to disable); **finish
  wiring `panel_channel_id`/`panel_message_id`** into a real "bot tracks and can refresh/relocate
  its one canonical ticket-launcher panel" feature, rather than treating the columns as dead
  (`!ticketpanel` currently just posts a fresh duplicate message every run)
- **Add, owner-decided committed scope (2026-07-05):** slash command mirrors **and**
  auto-close-on-inactivity, both committed now (against Lane-0's split recommendation to defer
  auto-close pending design — recorded as a genuine owner call)
- Adopt G-20 (`InstanceLifecycleSpec`, ratified — ticket is the sole current consumer of all 4
  amendments it folds; absorbs ~350 lines of hand-written choreography) and R-4
  (`storage=typed_column` elaboration, ratified — ticket is the only Lane A subsystem with no
  `schemas.py`, its bespoke migration-owned table is its dominant tier-3 mass)
- One-line reason: the audited core is genuinely exemplary; the gaps are unreachable
  functionality (dormant fields), missing features (slash, auto-close), and an untested surface

#### 7-11. (Outperform / engines / data / oracle / rubric)
- Outperform: Ticket Tool — free transcripts (paywalled there); auto-close/SLA, categories, reopen
  (all now committed scope)
- Engines: G-20 (ratified, ticket is highest-leverage consumer — giveaways flagged as a plausible
  future 2nd consumer of an adjacent shape); R-4 (ratified)
- Data: `ticket_config`/`tickets`/`ticket_blacklist` (migration 098) — genuinely typed-column, not
  KV; confirmed accurate
- Oracle: parity golden; **but a real verification hole found**: `close`/`add_participant`/
  `remove_participant`/`update_config`/`set_blacklist` have zero direct unit tests, and the entire
  cog plus 4 of 5 views are untested — the least-tested row so far despite the audited-seam
  reputation
- Rubric findings: **verification hole found** (above) — new goldens needed once features land

#### 12. Blockers and decisions
| Blocker type | Details | Resolution |
|---|---|---|
| Owner decision | Dormant fields (category_id, ping_staff_on_open, panel_channel_id/panel_message_id) | **Decided 2026-07-05: expose the 2 toggles, finish wiring the panel-tracking pair as a real feature** — not dropped |
| Owner decision | Slash mirrors + auto-close-on-inactivity | **Decided 2026-07-05: commit to both now** (auto-close needs its own design pass for what "inactive" means, warn-before-close, timeout configurability — but is committed Phase-B scope, not deferred) |
| Verification gap | Untested mutation paths + 4/5 views | Flagged for a future goldens pass, not blocking |

#### 13. Stage-3 consolidation notes
- BUILD-PLAN row delta: dormant-field exposure scoped concretely (2 toggles + 1 finished feature,
  not "expose dormant fields" vaguely); auto-close promoted from named-scope to committed
- Gate-0 delta: none — G-20/R-4 already ratified
- Dependencies to recheck: none new
- Owner ratification needed: none outstanding

### Row 15 — image_moderation

**Status: decided (2026-07-05).** No live bug. This row also **resolves the auto-mod-tier
consolidation question punted at rows 8 and 10** — the last of the three subsystems needed to
give a concrete answer.

#### 0. Row identity
- BUILD-PLAN row: `image_moderation` · Layer: L1b · Existing disposition: `KEEP+IMPROVE`
- **Stage-2 verdict: `improve`** (confirmed, matches capstone)
- Dependents to recheck: **resolves** rows 8 (automod) and 10 (cleanup)'s punted consolidation question
- Source confidence: `source-confirmed`

#### 1. User/job summary
- Primary user: administrators wanting automated image-content filtering
- Job-to-be-done: scan posted images for sexual/violence/harassment/hate content, off by default
- Competitor benchmark: mainstream bots ship none — likely a genuine differentiator

#### 2-5. Surface / invocation / hub
- `!imagemod` (read-only status embed) + help hook — no panel, no slash. Confirmed `off_until_opt_in`
  correctly implemented: every setting defaults OFF, zero API spend for an unconfigured guild.
  Fail-open coverage is **broader than automod's** — 3 independently forced-fault-tested paths
  (config-read, provider-unavailable, classify-error), closing the gap automod's own row (8)
  flagged for itself.

#### 6. Capability triage and exact scope — including the resolved cross-row question
- **Keep:** the verdict/scoring logic, the strict `moderation_service` seam reuse (identical
  pattern to automod, no second audit ladder), the `off_until_opt_in` privacy posture
- **Improve:** adopt G-2 (list-valued settings — exempt roles/channels are currently CSV strings)
  and G-5 (declarative bounds — the threshold percent is a hand-written validator)
- **Add, owner-decided (2026-07-05) — resolves the rows 8/10 auto-mod-tier question with a
  concrete, reuse-first shape:** give automod and image_moderation each a minimal single-page
  panel wrapping their existing status embed (zero buttons in v1, matching the capstone's own
  manifest sketch), then add two new buttons to **cleanup's existing `CleanupPanelView`** — "🛡️
  Automod Status" and "🖼️ Image Moderation" — reusing its existing back-navigation wiring
  (`_attach_back_to_cleanup_button`). **No new hub primitive is built.** All three subsystems are
  already registry siblings under the same parent hub with adjacent priority ordering, so this is
  an extension of tested, working code, not new infrastructure.
- One-line reason: functionality and safety discipline are already correct (best fail-open
  coverage of the auto-mod-tier trio); the fit gap is standard grammar conversion, plus the
  now-resolved cross-row panel/consolidation question

#### 7-11. (Outperform / engines / data / oracle / rubric)
- Outperform: mainstream bots ship none — likely a genuine differentiator (per BUILD-PLAN)
- Engines: G-2, G-5 (both ratified, reused)
- Data: owns no table (confirmed) — pure scalar settings
- Oracle: parity golden; **no verification hole found** — the strongest fail-open test coverage of
  any auto-mod-tier subsystem so far
- Rubric findings: orphaned capability string `image_moderation.settings.configure` (declared,
  nothing checks it — same pattern as automod/cleanup) — flagged, not fixed (in-scope-boundary `disbot/` file)

#### 12. Blockers and decisions
| Blocker type | Details | Resolution |
|---|---|---|
| Cross-row decision (rows 8, 10, 15) | Auto-mod-tier consolidation | **Resolved 2026-07-05**: minimal panels for automod + image_moderation, linked from 2 new buttons on cleanup's existing hub — no new shared primitive |
| Doc/registry drift | Orphaned `image_moderation.settings.configure` capability string | Flagged, not fixed |

#### 13. Stage-3 consolidation notes
- BUILD-PLAN row delta: "give it a real panel" now has a concrete shape (minimal `PanelSpec`,
  linked from cleanup's hub) instead of an open aspiration
- Gate-0 delta: none — G-2/G-5 already ratified
- Dependencies to recheck: **rows 8 (automod) and 10 (cleanup) both inherit this resolved
  decision** — their own records should be read alongside this one for the full consolidated shape
- Owner ratification needed: none outstanding



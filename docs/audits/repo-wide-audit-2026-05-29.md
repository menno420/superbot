# SuperBot — Repo-Wide Architecture & Consistency Audit

> **Status:** audit snapshot (recommendations only — not implementation approval).
> **Date:** 2026-05-29 · **Branch:** `claude/loving-knuth-AQCfs` · **Base commit:** `5609fe8` (post-#392).
> **Method:** every source file under `disbot/` (510 files), every migration (51), every doc
> (43), and the test tree (512 files / 6,306 tests) was read in full by a fan-out of 22
> scoped auditors; flagship findings were hand-verified by grep. No code was changed.
>
> **Companion to the prior snapshots** (`docs/helper-debt-inventory.md`,
> `docs/ui-view-adoption-audit.md`, `docs/cog-hub-coverage-audit.md`,
> `docs/audits/mutation_boundary_audit.md`). This audit reconciles them against current code
> and **supersedes the open backlogs in `ui-view-adoption-audit.md` (PRs 1–7 all shipped)**.

---

## ⏱ Remediation Status — updated 2026-05-30 (post-#414)

> Added by a follow-up review (session on `claude/sleepy-fermi-Bsc0d`). **Original findings below are
> left verbatim** so the "what was wrong" stays visible — this banner only overlays current status.
> Legend: ✅ fixed · ⚠️ partly fixed / reframed · ❌ still open. Each claim was **re-verified against
> `main` at commit `8b40bb4`**, not taken from PR titles.
>
> **Only the audit's PR-1 (Foundation & safety) slice was executed** — tagged PRs #395–#401 + #405.
> Audit PRs 2–6 (shared helpers, cog cleanup, UX/multi-select, tests/docs, BTD6/automation) were **not
> started**. The other post-audit PRs (#402–#404, #406–#414) executed *unrelated* plans (AI-grounding
> fix, settings/flags clarity) and are **not** audit remediation — though #414 incidentally fixed a
> moderation read-path crash (separate from P1-2).

| Item | Status | PR | Note |
|---|---|---|---|
| **P0-1** services→views (`classify_channel_name`) | ✅ | #395 | moved to `utils/channel_classify.py`; arch-fix-1 removed |
| **P0-2** `DeathmatchProvider` guild scope | ✅ | #396 | fixed **both** read+write; the audit's literal read-only fix would have left the board permanently blank |
| **P1-1** economy/xp/mod skip `emit_audit_action` | ⚠️ | #397 | **xp slice only.** economy still open; moderation reframed (already emits `moderation.action_taken`) |
| **P1-2** mod modals bypass `moderation_service` | ❌ | — | `views/moderation/modals.py` still writes directly (its #414 change was the unrelated read-path fix) |
| **P1-3** XP-roles-on-boot regression test | ✅ | #399 | boot-loop test already existed; #399 added the missing join-path mirror |
| **P1-4** `task_enabled` doc vs default | ✅ | #398 | docs-only; `default=True` confirmed intentional, not a bug |
| **P1-5** automation event-triggers never fire | ❌ | — | `_compute_next_run_at` still returns `None` for them; PR-6 track |
| **P1-6** BTD6 freshness 7 d vs 2 d | ❌ | — | `btd6_knowledge_api.py:189` still `> 7*24*3600` |
| **P1-7** `validate_answer` dead | ❌ | — | still zero callers in `disbot/` |
| **P1-8** `_invalidate_cache` no-op + gov orphan-delete bypass | ❌ | — | both unchanged since audit (`binding_mutation.py`, `governance/writes.py:417`) |
| **P1-9** `ai_permission_service.forget_guild` | ✅ | #401 | added + wired into teardown |
| **P1-10** multi-select primitive | ⚠️ | (this branch) | primitive added (`views/selectors/multi.py`: `MultiSelect` + `MultiChannelSelector`) + 1st adoption (channel restrict panel, multi-channel lock/unlock). Also fixed the §9.3 visibility-toggle nav dead-end. **Remaining:** adopt in AI policy/behavior, logging routes, setup channels/cog-routing (the other candidate flows) |
| **P1-11** game/cog/governance tests + coverage floor | ❌ | — | a few targeted tests landed; no `--cov-fail-under`, 18 cogs still bare |
| **P1-12** stale docs | ⚠️ | #400 | fixed arch count, nav-map, marked ui-view SUPERSEDED. **Open:** ADR-003 §2, `navigation.py` docstring, `runbook.md` ref |
| **P1-13** deathmatch/blackjack terminal-state dead-ends | ❌ | — | both view files unchanged since audit |
| **`emit_audit_action` AST invariant** (§8/§10) | ❌ | — | `architecture_rules/canonical_helpers.yaml` still `auto_checked: false` |
| **P2 / P3** | ❌ | — | only §9.9 (`chain_cog ?→!`, #405) done; embed factory, paginator, selectors, dedup, dead-code removal all open |

**Still open from the critical PR-1 safety slice:** P1-1 (economy), P1-2, P1-8, + the `emit_audit_action` AST invariant.

---

## 1. Executive Summary

**Overall architecture health: strong skeleton, accreting drift at the edges.** SuperBot has
an unusually mature, well-documented platform core: the layering contract, identity contract,
mutation pipelines, session/anchor/task lifecycles, and the BTD6 query→view-model→embed
sandwich are real, enforced by AST invariants (INV-F/G/K/L) and largely honored. The bones
are good. The problems are **consistency drift, adoption gaps, and a long tail of
half-wired/abandoned scaffolds** — the predictable cost of a fast-moving multi-phase build.

**Biggest consistency problems**
1. **Select/menu UX is single-select everywhere.** The repo has exactly **two** multi-select
   widgets (`views/settings/edit_command_access.py:295`, `views/btd6/admin_panel.py:143`) against
   **61** hardcoded `max_values=1`. The four shared `views/selectors/*` primitives are all
   single-select, have no pagination, and have **zero adoption** outside their own package. Many
   flows force "select one → confirm → reopen → select again" where multi-target is natural
   (channel restrict/visibility, AI policy channel/role pickers, logging routes, setup
   channels/cog-routing).
2. **Embed building is fragmented.** `utils/embeds.py` (the intended consolidation point) has a
   single `error()` function and two consumers, while ~328 inline `discord.Embed(...)` calls live
   across cogs/views. There is no `format_coins()` and no `AI_COLOR`/`BTD6_COLOR` constant, so
   color and number formatting diverge per-surface.
3. **Audit observability is split.** `economy_service`, `xp_service.reset`, and
   `moderation_service` never call `services.audit_events.emit_audit_action()`, so the three most
   sensitive mutation classes are invisible to the shared `audit.action_recorded` stream that
   feeds server logging.

**Biggest maintainability risks**
- **61 suppressed layer violations** in `architecture_rules/layers.yaml` (clusters: `arch-fix-11`
  core→services ×17, `arch-fix-13` views→cogs ×20), plus a tail of **untracked** lazy-import
  violations the AST checker can't see (it skips function-body imports).
- **3 zero-tolerance `services/ → views/` imports** (`classify_channel_name` from
  `views.setup.scan_panel` in `channel_recommender`, `cleanup_profiles`, `cog_routing_profiles`).
- **Helper misplacement that drives the above**: pure functions and embed builders living in
  `cogs/` and `views/` that other layers need (`classify_channel_name`,
  `build_setup_readiness_embed`, `cogs/btd6/_freshness_render` shim).

**Biggest UX inconsistencies**: the multi-select gap (above); inconsistent terminal-state
handling in game views (deathmatch bot-duel and blackjack natural-BJ replay are **dead-ends** with
no back/replay, while RPS/blackjack solo were fixed); a navigation dead-end in the channel
visibility toggle grid; and divergent ephemeral-vs-public + success/error wording across sibling
commands.

**Biggest unfinished areas**: the **automation subsystem** (event-driven triggers installable but
never fire; `post_leaderboard_summary` is a live-run placeholder; scheduler ignores per-source
intervals and quiet-hours timezone); the **BTD6 live-ingestion pipeline** (supervisor refetches
every source hourly regardless of declared interval; odyssey-maps stage unreachable; patch-notes
never populated; `btd6_cache_service` orphaned); the **BTD6 passive AI stage** (fully built + tested
but never registered); and several **Phase-gated stubs** (`core/resources/mutation.py`,
`binding_mutation._invalidate_cache`, governance role-scope).

**Highest-priority fixes (P0/P1):** the 3 services→views violations; the missing
**`emit_audit_action` on economy/xp/moderation**; the **`DeathmatchProvider` guild-scope bug**
(leaderboard always empty); the **missing regression test for the just-fixed "XP roles stripped on
boot"** bug; the **`feature_flags.task_enabled` default=True vs "default off" docstring**
(security-relevant); and the **stale `ui-view-adoption-audit.md` / `architecture.md` / ADR-003**
docs that will actively mislead future agents.

**Readiness verdict:** the repo is **ready for broad implementation work after a focused
foundation/cleanup pass** (PR 1–2 below). The core contracts are sound; the cleanup is targeted
consolidation, not a rewrite. Do **not** start large feature work on top of the automation or
BTD6-ingestion subsystems until their wiring gaps are closed, because new features there would
build on dead paths.

---

## 2. Repo Map

```
disbot/
├── bot1.py · config.py · guild_lifecycle.py · healthserver.py   # entry-point layer
├── cogs/            28 *_cog.py + sub-packages   # Discord-facing dispatchers
├── core/
│   ├── events*.py · runtime/        37 platform primitives
│   ├── runtime/ai/   17 files       # provider gateway + NL stage + redaction/safety
│   └── resources/    7 files        # typed Discord-resource discovery/mutation(stub)
├── governance/      15 files        # visibility/cleanup/capability engine + pipeline
├── services/        103 files       # audited mutations + read models + BTD6/AI/setup clusters
├── utils/
│   ├── db/           37 files       # the only home of asyncpg
│   ├── btd6/ · settings_keys/       # pure render helpers + typed keys
│   └── *.py          leaf helpers (+ 2 grab-bags)
├── views/           ~120 files      # per-subsystem panels/modals/selectors
├── migrations/      51 .sql
└── data/            json + btd6 datasets + per-tower/hero stats
```

| Area | Owns | Ownership clean? |
|---|---|---|
| **bot1/config/guild_lifecycle/healthserver** | process lifecycle, cog load order, signal drain, teardown fan-out, health probes | **Yes** — strong. One documented bare `create_task`; 22 teardown steps (one gap: `ai_permission_service`). |
| **cogs/** (28 subsystems) | Discord command/listener/panel dispatch | **Mostly.** A handful do business/DB logic that belongs in services (moderation modals; xp/_helpers raw SQL). 18 cog entry-points have no test. |
| **core/runtime/** (37) | sessions, anchors, router, tasks, scope-locks, guild_config cache, persistent views, feature flags, command surface | **Yes** for contracts; naming/observability nits (`component_registry` misnamed; `ephemeral_surface_manager` "surface" prefix unrouted; PR-3 flag-cache invalidation unwired). |
| **core/runtime/ai/** (17) | provider abstraction, NL pipeline, redaction, safety, routing | **Yes.** Redaction/injection containment is solid. Docs (`README.md`, `contracts.py`) badly stale; `feature_flags` default mismatch. |
| **core/resources/** (7) | typed resource discovery/status | **Yes** (read side). `mutation.py` is a Phase-7.5 `NotImplementedError` stub; `__init__` has an untracked `core→services` import. |
| **governance/** (15) | visibility/cleanup/capability + `GovernanceMutationPipeline` | **Mostly.** Role-scope unwalked (ISSUE-007); `_run_governance_upgrade` orphan-delete bypasses the pipeline; dead `_guild_has_role_overrides`; `governance_template_applications` table unused. Tracked `governance→services` debt (arch-fix-12). |
| **services/** (103) | audited mutations + read models + BTD6/AI/setup pure logic | **Drifting.** 3 zero-tolerance views imports; several services do Discord I/O (`setup_channel`, `history_cleanup`); dense `setup_*` and `btd6_*context*` clusters with real overlap; economy/xp/moderation skip the shared audit event. |
| **utils/** (leaf) | pure helpers, registries, settings keys, BTD6 render | **Mostly.** `helpers.py`/`channels.py` do I/O (leaf-policy breach); `embeds.py` is a 1-fn stub; `damage_types`/`btd6_cache` keys are dead; some raw settings-key leaks. |
| **utils/db/** (37) | all SQL | **Yes.** `pool.py` imports core+services (the package's only upward imports); a few f-string-built (but parameterized) SQL sites; `set_mining_inventory` lacks a txn; duplicated JSON codecs. |
| **views/** (~120) | UI panels/modals/selectors | **Drifting.** Single-select everywhere; settings widgets duplicate `_refresh_parent`×8 and `_BackToHubButton`×6; game views duplicate bet/opponent/result scaffolds; many bypass `BaseView` without justification; thin test coverage (roles 0, blackjack/rps views 0). |
| **migrations/** (51) | schema | **Yes**, with two caveats: 005/017 `ADD PRIMARY KEY` non-idempotent; 044 `ON CONFLICT` on NULL `guild_id` won't dedupe on replay. |
| **tests/** (512) | 6,306 tests | **Uneven.** Platform core + invariants well-covered; cog entry-points and game/role views barely covered; no coverage floor; evals are manual-only. |
| **docs/** (43) | contracts + inventories + plans | **Several stale** (see §11). Binding docs mostly accurate; living-inventory audits and one ADR have drifted. |

---

## 3. Cog-by-Cog Audit

> Format: **Purpose · key issues**. Healthy/thin cogs are noted briefly. Every flagged item carries
> a file:line in §4–§9.

**admin** (`admin_cog`, `admin/cog_manager`) — operator hub + cog loader. *Issues:* `server_stats`
online-member count is always wrong (presences intent off, `admin_cog.py:84`); cog-manager
dropdown silently truncates >25 cogs; two coexisting back-button patterns. Healthy otherwise.

**settings** (`settings_cog`, `views/settings/*`) — config surface. *Issues:* `_FLAG_NAME` raw
string duplicates the registered flag name (`settings_cog.py:45`); `settings access` subcommand
lacks its own permission decorator; **8× duplicated `_refresh_parent`** and **6× hand-rolled
`_BackToHubButton`** across the edit widgets; `subsystem_view.py:338` imports `cogs.help_cog`
(views→cogs); stale "S6"/"roadmap" footers in diagnostic panels.

**setup** (`setup_cog`, `setup/_helpers`, `setup/_wizard_entry`, `views/setup/*`,
`services/setup_*`) — the largest UI. *Issues:* cross-layer `build_setup_readiness_embed` imported
from `cogs.diagnostic` by setup helpers, views, and a service; section **`order=5` collision**
(`purpose` vs `server_scan`); 5 sections call `setup_draft.append` **without `section_slug`** →
orphaned ops survive a skip; `logging_presets`/`channels` detail views pass `hub=None`/`snapshot=None`
in wizard mode (degraded/broken Custom path); `SetupLauncherView` bypasses `BaseView` uncommented;
`/setup-hub` legacy command has no removal trigger. The `setup_*` **service cluster overlaps**
(`setup_operations`/`setup_change_plan`/`setup_plan`/`setup_draft`/`setup_sections`) — see §6.

**channel** (`channel_cog`, `views/channels/*`) — channel admin. *Issues:* `_ChannelListPaginatorView`
bypasses `BaseView` without justification; very generic command names (`!set`/`!del`/`!list`);
`format_overwrites` duplicated with `proof_channel_cog`; **single-select** delete/restrict/visibility
vs multi-target `!bulkdelete`/`!lock`; visibility toggle grid is a **navigation dead-end**
(`visibility_panel.py:139` comment references a non-existent back button); `_ChannelSelectForVisibility`
truncates `text_channels[:25]` silently; custom `on_error` ladders not migrated.

**role** (`role_cog`, `views/roles/*`) — roles + reaction roles + time roles. *Issues:* `!roles` has
**no permission gate**; raw `"skip_roles"` key (`role_cog.py:255`); threshold-filter logic
duplicated between `_assign_roles` and `on_member_join`; **`views/roles/*` has zero dedicated
tests** (9 files); `DiagnosticsPanel` reaches into `cog._assign_roles` via `get_cog`; `time_roles`
reset writes 7 rows before a raw `edit_message` (no defer); **"Diamand" typo** in default thresholds.

**economy** (`economy_cog`, `economy/_helpers`, `views/economy/*`, `services/economy_service`) —
coins/jobs/shop. *Issues:* `!daily`/`!joblist` diverge from their panel buttons (odds/mastery shown
in one, not the other); **full duplication** of daily-claim and job-list logic across cog+panel;
shop/work subviews bypass `BaseView`; `economy_service` **does not emit `emit_audit_action`**;
`claim_daily_if_ready` (atomic) is unused (read-then-write race remains); `main_panel` lazy-imports
`inventory_cog` (untracked views→cogs). INV-F is clean.

**xp** (`xp_cog`, `xp/_helpers`, `xp/listener`, `views/xp/*`, `services/xp_service`) — XP/levels.
*Issues:* no `/xp` slash (asymmetry vs economy); **raw SQL in `xp/_helpers.py:54`** (should be a
`utils/db/xp` fn); 4× raw settings-key leaks in `views/xp/modals.py`; `rank_embed_style` and XP
visibility prefs are **wired-but-nonfunctional**; hub stat-switch buttons do 4 DB reads before a raw
edit (3 s risk); `xp_service.reset` skips `emit_audit_action`; **`views/xp/{rank_view,main_panel,
config_panel}` untested**. INV-G clean. *(Note: the recent "XP roles stripped on boot" fix has **no
regression test** — see §10.)*

**leaderboard** (`leaderboard_cog`, `services/rank_providers`) — *Issues:* **`DeathmatchProvider`
calls `get_deathmatch_leaderboard()` with no `guild_id` → always `guild_id=0` → empty in real
guilds** (`rank_providers.py:206,222` — confirmed bug); O(N) Python rank scans; `!rank` computes
rank differently from the providers; no back/close nav.

**inventory** (`inventory_cog`) — *Issues:* dead `_open_category` method; raw `edit_message` (no
`safe_edit`); hand-rolled back button; `get_mining_inventory(str(user_id))` type asymmetry
(mining `user_id` is TEXT).

**blackjack/deathmatch/rps_tournament/counting/mining** (game cogs) — *Issues:* RPS tournament
`start_round` is duck-typed with a `TextChannel` passed as `ctx`; `schedule_channel_deletion`
`await`ed inline (blocks the handler 5 min — should be `tasks.spawn`); RPS dead state
(`self.scores`, `self.inactivity_limit`); counting **admin** commands hold a cog-wide lock across
Discord I/O (the V/M/A anti-pattern the on-message handler fixed); dead `random` branch in
`counting/handler.py:162`; blackjack `_launch_tournament` not atomic (Forbidden mid-loop leaves
debited coins in limbo until restart); mining `use` torch/dynamite are stubs; **PvP bets hardcoded
to 0** in rps/blackjack panels; many game-state views bypass `BaseView` and lack `on_error`.
Counting follows V/M/A on the hot path (reference impl); others do not.

**games** (`games_cog`, `views/games/*`) — router hub. *Issue:* **deathmatch bot-duel dead-end**
(no replay/back after game-over — inconsistent with the RPS/blackjack fixes); bet-preset and
opponent-select views duplicated across all three games.

**btd6** (`btd6_cog`, `btd6/*`, `views/btd6/*`) — read-heavy reference subsystem. *Issues:* the
passive **`BTD6AssistantMessageStage` is fully built + tested but never registered** (dead prod
code); `_freshness_render.py` is a cog-side shim still imported by a view (views→cogs); several
prefix/slash commands read `btd6_facts` **directly** instead of via the view-model service
(`build_latest_data_embed`, `build_live_events_embed`, `build_event_payload`); `build_round_embed`
**has no context_id**; cog-layer context_ids built by raw f-string (bypass `make_context_handle`
sanitization); leaderboard/live-events list embeds show 10 items but the select shows 25 (divergent);
`btd6_why_no_response_slash` does a DB read before responding with **no defer**.

**ai** (`ai_cog`, `ai/*`, `views/ai/*`, `services/ai_*`) — operator AI surface. *Issues:* embed
builders live in the cog but are lazy-imported by `views/ai/panel.py` (untracked views→cogs);
**all** AI policy channel/role/category + behavior scope pickers are single-select (strongest
multi-select candidates); `routing/matrix.py` always resolves against a fictional level-5 user;
`preset_picker` crashes on an empty preset catalog (no guard); read-only invariants hold. AI views
lack `on_error`/`on_timeout` (bypass `BaseView`).

**moderation** (`moderation_cog`, `moderation/_helpers`, `views/moderation/*`) — *Issues:* **all 7
modals + the prefix commands bypass `moderation_service`** → no `moderation.action_taken` emitted →
server logging never fires for panel/prefix actions; warn/kick/clear logic duplicated cog↔modal;
permission mismatch (`manage_roles` on warn/clear vs `moderate_members` on panel); `views→cogs`
import of `_can_act_on_interaction` (tracked arch-fix-13); `_UnbanModal` uses raw followups.

**help** (`help_cog`, `help/route`) — **best-tested** slice; single resolver honored. *Issue:*
two `build_overview_embed`/`_build_page_embed` tier-iteration paths can diverge; two `_on_select`
resolution strategies coexist.

**diagnostic** (`diagnostic_cog`, `diagnostic/_platform_embeds` [1,489 LOC], `views/diagnostic/*`)
— `!platform` surface. *Issues:* `_platform_embeds` has repeated `not_built`/"By subsystem" embed
blocks (extractable); 19/24 builders use blurple regardless of error state; naive `datetime.now()`
in uptime calc; the platform paginator is one-off (3 paginators repo-wide); `automation` hub entry
opens a read-only embed but the typed command opens the interactive panel (misleading).

**logging** (`logging_cog`, `logging/*`) — *Issues:* `_KIND_TO_BINDING` duplicated in 3 places +
the service source-of-truth; routes select is single-select for 7 routes; panel exposes only
mod+cleanup directly (5 newer routes only via subpage); select view never `stop()`s after success;
stale "S7d" docstrings; new routes are declared but **inert** (no publisher until Phase 9c).

**cleanup** (`cleanup_cog`, `cleanup/panel`) — *Issues:* `!word` == `!word list` (dead duplicate);
reaction-based confirmation (inconsistent with button confirms elsewhere); modal caps at 500 vs
`MAX=1000`; dead `btn_logging` fallback would `AttributeError`; raw `edit_message` refresh.

**chain** (`chain_cog`) — *Issues:* **9 user-facing strings show `?chain`** (wrong prefix); raw
`discord.Color.blue()` (no constant); no back nav; modals can't pre-fill.

**proof_channel** (`proof_channel_cog`) — *Issues:* `_format_overwrites` duplicate; two-modal chain
with no cancel path; **zero tests**.

**community / utility / general / inventory / leaderboard** — thin routers/utilities. *Issues:*
`utility_cog` is the lone non-xp consumer of `utils/embeds.py` and duplicates server/user-info embed
builders cog↔panel; `general_cog` trivia button spawns a new message (breaks panel) + reveal stays
enabled + 8-ball is public while siblings are ephemeral; `community`/`utility`/`general` mostly
untested.

**bootstrap_access** — clean; loads first; reload-safe. No issues.

---

## 4. File-by-File Findings (appendix)

> The 22 per-slice reports produced a full path|purpose|health|concern row for **every** file. To
> avoid a 510-row dump while honoring "don't skip files silently," this section **names every file
> flagged non-healthy** (questionable / stale / duplicated / misplaced / unfinished). Files not
> listed here were reviewed and assessed **healthy**.

**Misplaced (wrong layer / wrong package):**
`services/channel_recommender.py`, `services/cleanup_profiles.py`, `services/cog_routing_profiles.py`
(import `views/`), `services/setup_channel.py` & `services/history_cleanup.py` (Discord I/O in a
service), `utils/channels.py` & `utils/helpers.py` (I/O in leaf utils), `views/youtube_renderers.py`
(AI renderer in `views/`), `core/runtime/component_registry.py` (UI helper misnamed "registry"),
`cogs/diagnostic/_platform_embeds.py::build_setup_readiness_embed` (consumed cross-layer; belongs in
services), `cogs/deathmatch_cog.py::{_DuelView,_ChallengeView}` (views in a cog), `services/governance_exceptions.py`
(imported upstream by governance — inverted; tracked arch-fix-12).

**Stale (out-of-date code/docstring/shim):**
`core/runtime/ai/README.md`, `core/runtime/ai/contracts.py` (docstring), `core/runtime/ai/suggestion_templates.py`
(inert), `cogs/btd6/stage.py` & `cogs/btd6/__init__.py` (passive stage never registered),
`cogs/btd6/_freshness_render.py` (shim), `views/selectors/_resource_helpers.py` ("one release" shim,
overdue), `services/btd6_cache_service.py` (orphaned), `services/btd6_patch_service.py`,
`services/parsers/_skeleton.py` (dead), `services/parsers/__init__.py` (docstring), `cogs/logging/__init__.py`
& `cogs/logging/schemas.py` (S7d docstrings), `views/settings/{invalid_settings,missing_bindings,subsystem_view}.py`
(stale footers/docstrings), `utils/db/codec.py::maybe_decode_legacy` (S6 removal), `utils/db/automation.py`
(JSONB docstring), `utils/embeds.py` (1-fn stub), `utils/helpers.py::CogMenuView` (dead).

**Duplicated (see §6 for targets):**
`views/settings/{edit_*}.py` (`_refresh_parent` ×8, `_BackToHubButton` ×6), `views/games/{blackjack,rps,deathmatch}_panel.py`
(bet/opponent/result scaffolds), `services/{setup_plan,setup_ai_advisor}.py` (`_validate_against_schema`),
`cogs/{channel_cog,proof_channel_cog}.py` (`format_overwrites`), `views/btd6/{panel,strategy_review}.py`
(`_is_staff`), `views/ai/policy/{channel_view,category_view}.py` (`_VALID_MODES`), `views/ai/*` (`_admin` ×5),
`utils/db/{automation,platform_migration_checkpoints,user_participation,btd6_strategies,youtube_video_cache}.py`
(JSON codecs), `utils/db/{automation,bindings,user_participation}.py` (`_parse_delete_count`),
`services/btd6_{context,ai_context,knowledge,knowledge_api,ai_knowledge_block}_service.py` (context/knowledge cluster),
`cogs/economy_cog.py`+`views/economy/*` (daily/joblist/shop flows), `cogs/utility_cog.py` (server/user-info embeds).

**Unfinished / wired-but-nonfunctional / stub:**
`services/automation_executor.py` (`post_leaderboard_summary` placeholder; event-trigger handlers
unwired), `services/automation_scheduler.py` (per-source interval ignored; quiet-hours UTC; default
off), `services/automation_templates.py` (`create_role` unimplemented), `services/btd6_ingestion_supervisor.py`
(hourly refetch of all sources), `services/parsers/ninjakiwi_odyssey.py` (`parse_odyssey_maps`
unreachable), `core/resources/mutation.py` (NotImplementedError stubs), `core/resources/discovery.py::validate_resource_permissions`
(stub), `services/binding_mutation.py::_invalidate_cache` (no-op), `services/setup_ai_advisor.py`
(ANTHROPIC branch no-op), `views/games/{rps,blackjack}_panel.py` (PvP bet=0), `views/blackjack/solo_view.py`
(replay→natural-BJ dead-end), `views/games/deathmatch_panel.py` (`_BotDuelView` dead-end),
`cogs/mining_cog.py::use` (torch/dynamite stubs), `governance/health.py` (`invalid_cleanup_configs`
always empty), `utils/btd6/damage_types.py` (`decode_damage_type` never called), `cogs/xp/schemas.py`
(`rank_embed_style` + visibility prefs), `cogs/inventory_cog.py::_open_category` (dead),
`utils/db/economy.py::claim_daily_if_ready` (unused).

**Questionable behavior (potential bug / risk):**
`services/rank_providers.py` (DeathmatchProvider guild scope), `cogs/admin_cog.py` (online count),
`services/btd6_knowledge_api.py` (7-day stale threshold vs registry 2-day), `services/btd6_ai_context_service.py`
(leaderboard `fetched_at` always None), `services/btd6_grounding_service.py` (`validate_answer` dead
in main pipeline), `services/btd6_view_model_service.py` (`build_latest_data_view_model` hardcodes
`context_type="event"`), `core/runtime/ai/feature_flags.py` (`task_enabled` default True vs docstring),
`core/runtime/ai/routing.py` (OpenAI table missing BTD6/NL defaults), `services/ai_permission_service.py`
(no `forget_guild`; unbounded dicts), `core/runtime/ephemeral_surface_manager.py` ("surface" prefix
unrouted), `core/runtime/feature_flags.py` (PR-3 cache invalidation unwired), `utils/db/games/mining.py`
(no txn), `utils/db/governance.py` (`write_governance_audit` drops `mutation_id`), `governance/writes.py`
(`_run_governance_upgrade` pipeline bypass), `governance/resolver.py`+`cache.py` (role-scope no-op +
dead dict), `migrations/{005,017}.sql` (non-idempotent PK), `migrations/044.sql` (NULL ON CONFLICT),
`migrations/042.sql` (partial idempotency), `services/setup_draft.py` (non-txn replace),
`services/setup_session.py` (non-atomic start; no audit on in-progress), `utils/db/pool.py`
(core+services imports).

---

## 5. Cross-Repo Inconsistency Matrix

| Pattern | Where it appears | How implementations differ | Best implementation | Should it be shared? | Priority |
|---|---|---|---|---|---|
| **Select / list flows** | every cog/view with a dropdown | all single-select; 2 multi-selects exist | `edit_command_access` multi-channel; `btd6/admin_panel` multi-source | **Yes** — add multi-select + paginated variants to `views/selectors/` and adopt | **P1** |
| **Multi-select gap** | channel restrict/visibility, AI policy/behavior, logging routes, setup channels/cog-routing, shop | forced "select→confirm→reopen"; `logging_presets` does all-at-once | `logging_presets` (one action configures everything) | Yes — shared `MultiSelect` primitive | **P1** |
| **Pagination** | `views/diagnostic/paginator`, `channel_cog` list, `leaderboard_cog`; btd6 browsers truncate | 3 independent paginators; btd6 list shows 10 but select 25 | `views/diagnostic/paginator` (BaseView-based) but back-button hardcoded | Yes — promote one canonical `PaginatorView` | P2 |
| **Back/cancel** | all subpanels | `attach_back_button` (canonical) vs 6 hand-rolled `_BackToHubButton` in `views/settings/*` | `views/navigation.attach_back_button` | Already canonical — migrate the 6 settings holdouts | P2 |
| **Error embeds** | repo-wide | `utils.embeds.error()` (2 callers) vs ~328 inline `discord.Embed` | a real embed factory | **Yes** — but needs its own PR + migration plan (helper-policy warns against opportunistic) | P2 |
| **Colors** | repo-wide | `ui_constants` (37 files) vs inline `discord.Color.*` (btd6/ai/deathmatch); no `AI_COLOR`/`BTD6_COLOR` | `ui_constants` | Yes — add missing constants, migrate | P2 |
| **Coin/number formatting** | economy/xp/games/leaderboard | `{n:,}` bold / `{n}` / raw int — ≥3 styles | `f"**{n:,}** 🪙"` | **Yes** — `format_coins()` in `utils/` | P2 |
| **Permission checks** | hub commands | `administrator` / `is_admin_or_owner` / `manage_channels` / **none** (`!roles`) / `manage_roles` vs `moderate_members` | per-domain but consistent within a domain | Document the intended gate per subsystem | P2 |
| **Cooldowns** | commands | `!help`/`!utilitymenu` have them; most games + `!platform`/`!logging` don't | — | Decide a policy; apply to spammy write commands (`!mine`,`!chop`) | P3 |
| **Ephemeral vs public** | slash vs prefix | slash often ephemeral, prefix public; 8-ball public; AI menu ephemeral-via-slash only | — | Document the convention | P3 |
| **Freshness indicators** | btd6 | `bucket_freshness` (registry, 2 d) vs `btd6_knowledge_api` (7 d) → conflicting "fresh" | `btd6_source_registry.bucket_freshness` | **Yes** — single freshness authority | P1 |
| **Timestamps** | repo-wide | mostly `datetime.now(tz=utc)` (correct); naive `.now()` in `diagnostic/_platform_embeds`, `_helpers`; `utcnow()` in a test | tz-aware | enforce via AST invariant (not just ruff) | P2 |
| **Logging / audit** | mutation services | governance/participation/automation-mutation/role-automation emit `emit_audit_action`; **economy/xp/moderation do not** | participation_mutation pattern | **Yes** — route the 3 holdouts through it | **P1** |
| **DB access** | services/cogs | mostly `utils.db.*`; raw `pool/conn.execute` in `economy_service.transfer`, `game_state_service`, `platform_consistency`, `binding_backfill`; raw SQL in `xp/_helpers` | `utils.db.<fn>()` | Yes — add the missing db fns | P2 |
| **Cache invalidation** | guild_config / governance / feature_flags / binding | guild_config + governance correct; feature_flags TTL-only (PR-3 unwired); `binding_mutation._invalidate_cache` no-op | guild_config version-stamp | Close the two unwired paths | P1 |
| **Background tasks** | repo-wide | `tasks.spawn` honored (INV-K); but `schedule_channel_deletion` `await`ed inline (5-min block) | `tasks.spawn` | fix the inline awaits | P2 |
| **AI context injection** | services/ai_* + btd6_* | 2 parallel context paths (`btd6_context_service` vs `btd6_ai_context_service`); `validate_answer` dead | one grounding path | consolidate (later) | P2 |
| **Help/command descriptions** | help_cog + command_descriptions | single resolver (good); 2 tier-iteration builders | help/route | minor | P3 |
| **Tests** | repo-wide | platform core deep; cog entry-points + game/role views shallow; no coverage floor | invariants pattern | add floor + targeted view/cog tests | P1 |

---

## 6. Duplicate and Near-Duplicate Logic

| # | Concept | Files / functions | Differences | Consolidation target | When |
|---|---|---|---|---|---|
| 1 | **`classify_channel_name`** (also the zero-tolerance violation) | `views/setup/scan_panel.py` imported by `services/{channel_recommender,cleanup_profiles,cog_routing_profiles}.py` | identical import | move to `utils/channel_classify.py` (pure) | **now (P0)** |
| 2 | **`_validate_against_schema`** | `services/setup_plan.py:246`, `services/setup_ai_advisor.py:343` | identical; advisor copy has a "mirror of…" comment | keep in `setup_plan`, import in advisor | now |
| 3 | **`build_setup_readiness_embed`** | defined in `cogs/diagnostic/_platform_embeds.py`; imported by setup helpers/views + `automation_executor` | crosses 3 layers | move to `services/setup_readiness.py` or `utils/` | P1 |
| 4 | **`_refresh_parent`** | 8 files in `views/settings/` | identical but for logger name | `views/settings/_widget_helpers.py` | P2 |
| 5 | **`_BackToHubButton`** | 6 files in `views/settings/` | identical class | use `attach_back_button` | P2 |
| 6 | **Bet-preset / opponent-select / result-view scaffolds** | `views/games/{blackjack,rps,deathmatch}_panel.py`, `views/{blackjack,rps}/*` | near-identical; `games/common.py` anticipated consolidation never landed | `views/games/common.py` | P2 |
| 7 | **`format_overwrites`** | `cogs/channel_cog.py:106`, `cogs/proof_channel_cog.py:309` | join style differs | `utils/channels.py` (when it's cleaned of I/O) | P2 |
| 8 | **`_is_staff`** | `views/btd6/panel.py:34`, `views/btd6/strategy_review.py:41` | identical | move to `utils/` | P3 |
| 9 | **`_admin` perms check** | 5× across `views/ai/*` | identical | `views/ai/_helpers.py` | P3 |
| 10 | **`_VALID_MODES`** | `views/ai/policy/{channel_view,category_view}.py` | identical | import from `channel_view` | P3 |
| 11 | **JSON encode/decode** | 5× `utils/db/*` (`automation`, `platform_migration_checkpoints`, `user_participation`, `btd6_strategies`, `youtube_video_cache`) | slightly different edge handling | extend `utils/db/codec.py` | P2 |
| 12 | **`_parse_delete_count`** | `utils/db/{automation,bindings,user_participation}.py` + inline elsewhere | identical | `utils/db/_helpers.py` or `pool.py` | P3 |
| 13 | **`_can_act_on` hierarchy** | `cogs/moderation_cog.py:33`, `cogs/moderation/_helpers.py:48` | ctx vs interaction | one `utils/` helper (also fixes the views→cogs import) | P2 |
| 14 | **daily-claim / job-list / shop-purchase flows** | `cogs/economy_cog.py` ↔ `views/economy/*` | panel omits odds/mastery; shop differs only in final response method | `cogs/economy/_helpers.py` shared functions | P2 |
| 15 | **server/user-info embeds** | `cogs/utility_cog.py` command ↔ panel | only source object + footer differ | module-level `_build_*_embed` | P3 |
| 16 | **BTD6 context/knowledge cluster** | `btd6_context_service`, `btd6_ai_context_service`, `btd6_knowledge_service`, `btd6_knowledge_api`, `btd6_ai_knowledge_block_service` | overlapping restriction/event rendering; `superlative` vs `knowledge.upgrades_by_price` | unify on `btd6_ai_context_service` as the fetch point | P2 (later) |
| 17 | **`response_to_embed`** | `utils/btd6/response_embed` (canon), `cogs/btd6/_embeds` (re-export), `cogs/btd6/stage.py::_response_to_embed` (partial copy) | stage copy omits 4 fields | stage should import the canon | P3 |
| 18 | **Paginators** | `views/diagnostic/paginator`, `channel_cog`, `leaderboard_cog` | 3 independent | promote diagnostic one (de-hardcode back) | P2 |
| 19 | **`_KIND_TO_BINDING`** | `cogs/logging/{select_view,provision_view}.py` + `server_logging._ROUTE_TO_BINDING` | 3 copies | import from `server_logging` | P2 |

**Not duplicates (verified distinct — do not merge):** `core/runtime/ai/feature_flags` vs
`core/runtime/feature_flags` (env kill-switch vs DB rollout); `core/runtime/ai/gateway` vs
`services/ai_gateway` (impl vs inversion shim); `governance/templates` vs `role_templates`;
`navigation_stack` vs `views/navigation`; `subsystem_schema`/`participation_schema`/
`*_capabilities`; `settings_registry`/`config_arbitration`/`guild_config`.

---

## 7. Unfinished, Stale, or Suspicious Code

**Wired-but-nonfunctional (highest concern — looks done, isn't):**
- **Automation event triggers** — `member_join`, `setup_readiness_below`, `binding_missing`,
  `channel_inactive` are registered, templated, and installable, but **no code dispatches them**
  (`automation_scheduler._compute_next_run_at` returns `None` for them). Operators can install
  welcome-message/notify-on-join rules that **never fire**.
- **`automation_executor._handle_post_leaderboard_summary`** returns `{"placeholder": True}` even on
  live (`dry_run=False`) runs. `weekly-leaderboard`/`economy-summary` templates silently no-op.
- **BTD6 ingestion supervisor** refetches **all 7 sources every hour** regardless of declared
  `interval_s` (`_run_loop` uses interval only for backoff). `nk_btd6_odyssey_diff_maps` is
  registered+enabled+fixtured but **unreachable** (dependency-chain gap) → odyssey-stage facts never
  ingested. `btd6_patch_service.upsert` is never called → patch notes never populate.
- **`cogs/btd6/stage.py::BTD6AssistantMessageStage`** — fully implemented + tested, **never
  registered** (cog_load explicitly unregisters it). Dead production code with a live test suite.
- **PvP bets = 0** — `views/games/{rps,blackjack}_panel.py` hardcode the stake; PvP staked games are
  non-functional.
- **`rank_embed_style` + XP visibility/DM prefs** (`cogs/xp/schemas.py`) — declared settings the code
  never reads.

**Phase-gated stubs (intentional, but undocumented removal triggers):**
`core/resources/mutation.py` (Phase 7.5 `NotImplementedError`), `discovery.validate_resource_permissions`
(Phase 4.5), `binding_mutation._invalidate_cache` (Phase 4c no-op — **stale binding cache**),
authority checks in `resource_provisioning`/`settings_mutation`/`readiness_repair` (Phase 4.5 — any
member can mutate), `setup_ai_advisor` ANTHROPIC branch (silent fallback to deterministic),
`config_arbitration` (no removal trigger), feature-flag PR-3 event invalidation (TTL-only).

**Dead code / dead data:**
`services/btd6_cache_service.py` (orphaned; cadence never wired), `services/parsers/_skeleton.py`,
`utils/btd6/damage_types.decode_damage_type`, `utils/helpers.CogMenuView`, `cogs/inventory_cog._open_category`,
`utils/db/economy.claim_daily_if_ready` (unused; race remains), `governance/cache._guild_has_role_overrides`
(never written; role-fingerprint cache logic dead), `governance_template_applications` table (no
code), `governance/health.invalid_cleanup_configs` (always empty), RPS `self.scores`/`inactivity_limit`,
counting `handler.py:162` random branch, `cogs/cleanup_cog` `!word`==`!word list`, dead `btn_logging`
fallback in `cleanup/panel.py`, `utils/settings_keys/btd6_cache.py` (3 unconsumed keys),
`views/youtube_renderers.py` (misplaced), several "one release" shims (`views/selectors/_resource_helpers`,
`cogs/btd6/_freshness_render`).

**TODO/marker debt:** ISSUE-007 (role-scope) open; DEBT-002 (audit-bypass before AI/plugin expansion)
open; no `TODO`/`FIXME` in `utils/` (good); milestone docstrings (M3A/M3B/S7d/M4/M6) stale in
`btd6_knowledge_api`, `parsers/__init__`, `cogs/logging/*`, `cogs/btd6/schemas`.

---

## 8. Architecture Boundary Issues

| Boundary | Instance(s) | Status | Correct owner |
|---|---|---|---|
| **`services/ → views/` (zero tolerance)** | `channel_recommender.py:36`, `cleanup_profiles.py:37`, `cog_routing_profiles.py:28` (`classify_channel_name`); `setup_sections.py:35` (TYPE_CHECKING) | suppressed (arch-fix-1) but violates the hardest rule | move `classify_channel_name` to `utils/`; type-only import is acceptable | 
| **service does Discord I/O** | `setup_channel.py` (`channel.edit/delete`), `history_cleanup.py` (`channel.history`) | headless breach | route through `core.runtime.guild_resources` / move to a cog | 
| **`utils/` does I/O** | `utils/channels.py` (create/delete), `utils/helpers.post_log_embed` (send) | leaf-policy breach | a `services/` channel/log service | 
| **`core/ → services` (non-metrics)** | `core/resources/__init__.py` (diagnostics_service, lazy-at-import) | **untracked** | add to known-violations or invert via a register hook | 
| **`core/ → views`** | `core/runtime/persistent_views.py:83` (`views.base.handle_view_error`) | **untracked** | move `handle_view_error` to `core` or pass a callback | 
| **`core/ → governance`** | `interaction_router.py:126`, `events_catalogue.py:34` | router lazy = untracked; catalogue module-level = tracked | governance should publish event names to a catalogue `core` owns | 
| **`utils/db → core+services`** | `utils/db/pool.py:28-29` (slow_path_log, metrics) | the DB layer's only upward imports | a thin `utils/db/telemetry.py` adapter | 
| **`governance/ → services`** | `cache.py:135` (module-level), `writes.py` (audit_events, governance_exceptions) | tracked arch-fix-12 | move `governance_exceptions` to `governance/`; lazy-load diagnostics | 
| **`views/ → cogs`** | ~20 tracked (arch-fix-13: economy/xp/mining/blackjack/games) + **untracked lazy** (`views/economy/main_panel`→inventory_cog; `views/mining/mine_view`→help_cog; `views/btd6/*`; `views/games/*`→help_cog; `views/ai/panel`→ai_cog; `views/setup/{launcher,sections/readiness}`→diagnostic) | mixed | move shared `_state`/embed builders down to `services/`/`utils/`; register cog panels via a hook registry | 
| **cog doing business/DB logic** | moderation modals (bypass `moderation_service`), `xp/_helpers` raw SQL, mining admin read-modify-write | boundary smell | services / `utils/db` | 
| **INV-E second bypass** | `governance/writes.py::_run_governance_upgrade` orphan DELETE (no audit, no cache invalidation) | undocumented | route through the pipeline or document like `_audit_internal_bypass` | 
| **audit-event rule unenforced** | `canonical_helpers.yaml` `audit_events: auto_checked: false` | no AST test | add an `emit_audit_action` AST invariant | 

**Net:** the file-level import graph is mostly clean (the checker passes); the **call graph** hides a
second tier of violations via lazy body imports that the AST checker deliberately skips. The
recurring root cause is **helper misplacement** (pure functions and embed builders in `cogs/`/`views/`
that lower layers need). Fixing placement (§6 items 1, 3, 7, 13) removes most of these.

---

## 9. UX and Interaction Issues

1. **Forced single-select** where multi-target fits (channel restrict/visibility, AI
   policy/behavior, logging routes, setup channels/cog-routing, shop). `logging_presets` shows the
   target pattern (one action configures everything). **[P1]**
2. **Terminal-state dead-ends:** deathmatch bot-duel (`_BotDuelView._finish` disables buttons, no
   replay/back); blackjack solo replay→natural-BJ sets `view=None`. RPS/blackjack solo were fixed —
   these two were missed. **[P1]**
3. **Navigation dead-end:** channel visibility toggle grid (`_SubsystemToggleView`) has no back
   button despite a comment claiming one. **[P2]** — ✅ **FIXED** (Back button re-attached on every
   `_rebuild_buttons`; alongside the P1-10 multi-select work).
4. **Controls active after terminal state:** `_TriviaRevealView` reveal button stays enabled
   (repeat reveals); trivia + 8-ball spawn new messages / public replies, breaking the panel
   contract. **[P2]**
5. **Silent >25 truncation:** visibility panel, settings hub/edit selects, flag manager, automation
   panel, cog manager, btd6 browsers — all drop the tail with no warning. **[P2]**
6. **`ChannelSelector` crashes on empty options** (no placeholder guard, unlike `RoleSelector`/
   `SubsystemSelector`). **[P2]**
7. **3 s token-expiry exposure:** xp hub buttons (4 DB reads before raw edit), `time_roles` reset (7
   writes before raw edit), `EditRoleModal` (defer *after* `role.edit`), several btd6 slash commands
   (DB read before `send_message`, no defer). **[P2]**
8. **Empty-state inconsistency:** help "All Commands" empty page still says "Select a category
   below"; shop shows owned items (then "you already own"); btd6 list embeds show 10 but the select
   offers 25. **[P3]**
9. **Wrong prefix in help text:** `chain_cog` shows `?chain` ×9 (bot prefix is `!`). **[P2]**
10. **Inconsistent confirmation patterns:** `!cleanuphistory` uses reactions; everything else uses
    button views. **[P3]**
11. **`!roles` opens a panel with no permission gate** (buttons error on click instead). **[P2]**
12. **Interactions that fail silently:** `cleanup/panel.btn_logging` dead fallback (`AttributeError`),
    moderation panel actions emit no audit (server logging never fires), automation rules that never
    fire. **[P1–P2]**

---

## 10. Testing, Observability, and Debuggability Gaps

**Testing (6,306 tests; platform core strong, edges thin):**
- **18 cog entry-points have zero dedicated tests** (counting, economy, blackjack, deathmatch, rps,
  moderation, logging, channel, chain, cleanup, leaderboard, community, inventory, help, general,
  diagnostic, utility, proof_channel). **[P1]**
- **Game views untested** (`views/blackjack/*`, `views/rps/*`) — the bet/settle callbacks that drive
  economy_service are not exercised. **[P1]**
- **`views/roles/*` (9 files) untested.** **[P2]**
- **No regression test for "XP roles stripped on boot"** (the bug just fixed in `b13ed56`). **[P1]**
- **`governance/writes.py` (GovernanceMutationPipeline) has no behavioral test** — INV-E is only a
  source-grep, not a "writes audit row + emits event" check. **[P1]**
- **`interaction_router.dispatch` error paths untested** (unknown prefix, handler raises, defer
  fail). **[P2]**
- **AI decision-audit once-per-invocation** is functionally covered but not explicitly asserted as an
  idempotency property. **[P2]**
- **Migration idempotency** is structural-only; no execution test (so the 005/017/044 hazards aren't
  caught). **[P2]**
- **No coverage floor**; **evals are manual-only** (`|| true`, no CI gate). **[P2]**
- **INV-M (no print) / INV-N (no utcnow)** are ruff-only, not AST invariants → a `noqa` slips
  through; a test already uses `datetime.utcnow()`. **[P2]**

**Observability:**
- economy/xp/moderation mutations **absent from the shared `audit.action_recorded` stream** (server
  logging blind to them). **[P1]**
- webhook failures logged at DEBUG only; feature-flag bootstrap-fallback, btd6 grounding DB failures,
  conversation LRU evictions, automation auto-disable, ingestion outcomes — all silent (no
  metric/WARNING). **[P2]**
- `ephemeral_surface_manager` "surface" prefix pollutes `interaction_unhandled_total` on every
  confirm click. **[P2]**
- AI policy-projection silent-failure has no counter (only surfaces via `drift_count` on demand).

**Recommended additions:** behavioral pipeline tests (governance/writes), game-view bet-callback
tests, an XP-boot-role regression test, an `emit_audit_action` AST invariant + `print`/`utcnow` AST
invariants, a `--cov-fail-under` floor, and one-shot WARNINGs/metrics on the silent failure paths
above.

---

## 11. Documentation Gaps

**Drift that will actively mislead a future agent (fix first):**
- **`ui-view-adoption-audit.md`** — its entire §7 + §9.3 backlog (PRs 1–7) is **done**; the doc still
  lists it open and still flags `work_panel.py:86` as bare. **[P1]**
- **`navigation.py` docstring** — says admin/settings/games back-button factories "stay as-is, migrate
  one PR at a time"; they were all converted to thin delegates of `attach_back_button`. Misleads into
  "finish the migration" (which would break callers). **[P1]**
- **ADR-003 §2** — lists PRs #253/#255/#256 as "open, blocked by canary"; all shipped. The ADR's own
  rule says to mark them `shipped in #NNN`. **[P1]**
- **`architecture.md`** — layer diagram says `cogs/ (×20)`; actual is **28**. ("51 migrations" is
  correct.) **[P2]**
- **`AGENT_ORIENTATION.md`** — "23 markdown files" (actual **43**); 3 docs unclassified
  (`btd6-ai-tool-calling-plan`, `btd6-data-pipeline`, `cog-hub-coverage-audit`). **[P2]**
- **`repo-navigation-map.md`** — ".github/workflows: one file"; there are **two** (`ai-evals.yml`). **[P2]**
- **`runtime_contracts.md:334`** — references `docs/runbook.md`, which **does not exist**. **[P2]**
- **`btd6-ai-tool-calling-plan.md`** — header "PLAN ONLY — not implemented", but `btd6_lookup`/
  `capability`/`superlative` tools are registered and live. **[P2]**

**Missing docs:** `docs/runbook.md` (referenced, absent); a metrics-inventory doc; an
`ai-evals.yml` operator note (paid API calls, no guidance); a one-paragraph "why INITIAL_EXTENSIONS
order matters."

**Rules that should be documented/enforced:** the `emit_audit_action` requirement (CLAUDE.md says
"always," but it's `auto_checked:false` and 3 services skip it); the two-tier `utils/db/__init__.py`
re-export convention; the deliberate single-process registry list (some primitives undocumented).

**Tooling drift (docs-adjacent):** `.pre-commit-config.yaml` tool versions lag CI badly (black 24
vs 26, isort 5 vs 8, ruff 0.4 vs 0.15, mypy 1.8 vs 2.1); `requirements-dev.txt` is unpinned despite a
"mirrors CI" claim; `check_quality.py --check-only` skips mypy and calls **bare** tool names (not
`python3.10 -m`), so the CLAUDE.md pre-PR command can silently use wrong-version tools. **[P2]**

---

## 12. Priority Ranking

### P0 — broken / dangerous / blocks future work

**P0-1 · Zero-tolerance `services/ → views/` imports** — ✅ **FIXED (#395)**
- *Evidence:* `services/channel_recommender.py:36`, `cleanup_profiles.py:37`, `cog_routing_profiles.py:28`
  → `from views.setup.scan_panel import classify_channel_name`.
- *Fix:* move `classify_channel_name` (pure text logic) to `utils/channel_classify.py`; update 3 imports.
- *Risk if ignored:* the hardest architectural rule is violated; any `views/` load-order change can
  crash service imports; normalizes the worst boundary breach.
- *Verify:* `grep -rn "from views" disbot/services` returns nothing; `python3.10 scripts/check_architecture.py --mode strict` clean.

**P0-2 · `DeathmatchProvider` always queries `guild_id=0`** — ✅ **FIXED (#396, read+write)**
- *Evidence:* `services/rank_providers.py:206,222` call `db.get_deathmatch_leaderboard()` (defaults
  `guild_id=0`); real guilds get an empty leaderboard.
- *Fix:* pass `guild.id`.
- *Risk:* a user-facing leaderboard category is permanently blank.
- *Verify:* a `rank_providers` test asserting `guild.id` is forwarded.

### P1 — serious inconsistency / drift / high maintenance risk

| ID | Issue | Evidence | Fix | Risk | Verify |
|---|---|---|---|---|---|
| P1-1 ⚠️ | economy/xp/moderation skip `emit_audit_action` | `economy_service`, `xp_service.reset`, `moderation_service`/modals | route through `services.audit_events` | sensitive mutations invisible to server logging | assert `audit.action_recorded` fires |
| P1-2 ❌ | Moderation modals/prefix bypass `moderation_service` | `views/moderation/modals.py` (7 modals), `moderation_cog` | call the service | no `moderation.action_taken`; duplicated logic | test modal → service call |
| P1-3 ✅ | Missing regression test for "XP roles stripped on boot" | bugfix `b13ed56`, `role_cog`/`xp` boot path | add `on_ready` role-retention test | silent re-regression | new test fails pre-fix |
| P1-4 ✅ | `feature_flags.task_enabled` default True vs "default off" docstring | `core/runtime/ai/feature_flags.py:16,74` | fix docstring (or default), add test | operator enables `AI_ENABLED` and silently gets all tasks | test asserts default |
| P1-5 ❌ | Automation event-triggers never fire | `automation_scheduler._compute_next_run_at`, registry/templates | wire a dispatcher or hide unsupported triggers | installable rules silently dead | integration test member_join→executor |
| P1-6 ❌ | BTD6 freshness threshold conflict (7 d vs 2 d) | `btd6_knowledge_api.py:189` vs `btd6_source_registry` | use the registry authority | AI presents stale facts as fresh | test consistency |
| P1-7 ❌ | `validate_answer` (verify-or-disclaim for AI output) dead in main pipeline | `btd6_grounding_service.validate_answer` (no NL-stage caller) | wire it or document the heuristic-only stance | unverified numeric claims unchecked | test stage calls it |
| P1-8 ❌ | `binding_mutation._invalidate_cache` no-op + `_run_governance_upgrade` orphan-delete bypass | `binding_mutation.py`, `governance/writes.py:418` | implement invalidation; route delete through pipeline | stale binding/visibility cache | test cache cleared post-write |
| P1-9 ✅ | `ai_permission_service` no `forget_guild` | `ai_permission_service.py:34-35`, `guild_lifecycle` step 20 | add hook + register | unbounded growth; stale cooldowns on re-invite | teardown test |
| P1-10 ⚠️ | Multi-select primitive missing | `views/selectors/*` all single-select | add `MultiSelect`/paginated selectors; adopt | repetitive admin UX repo-wide | view tests | **Primitive added + adopted in channel restrict panel; §9.3 dead-end fixed. Remaining: other candidate flows + paginated variant.** |
| P1-11 ❌ | Game-view bet callbacks + 18 cogs + governance pipeline untested | §10 | add targeted tests + coverage floor | regressions invisible | CI coverage report |
| P1-12 ⚠️ | Stale docs (ui-view-adoption, navigation docstring, ADR-003) | §11 | update to current state | agents redo/break shipped work | doc-pin or review |
| P1-13 ❌ | Deathmatch/blackjack terminal-state dead-ends | `deathmatch_panel._BotDuelView`, `blackjack/solo_view._replay` | add replay+back result view (match RPS) | user stuck on dead panel | view test |

### P2 — important cleanup / UX / tests / simplification
Embed factory + `format_coins` + `AI_COLOR`/`BTD6_COLOR` consolidation; migrate 6 settings
`_BackToHubButton` + 8 `_refresh_parent`; promote one canonical paginator; close >25-truncation +
`ChannelSelector` empty-guard; fix 3 s-defer ordering hotspots; de-duplicate JSON codecs /
`_parse_delete_count` / `_validate_against_schema` / `format_overwrites` / `_can_act_on` /
`_KIND_TO_BINDING`; move `build_setup_readiness_embed`; BTD6 supervisor per-source intervals +
odyssey-maps chain + patch-notes wiring; automation quiet-hours timezone + `post_leaderboard_summary`;
naive-datetime fixes + AST invariants for print/utcnow/audit_events; migration idempotency tests +
005/017/044 hardening; `set_mining_inventory` txn; pre-commit/CI version alignment + `check_quality`
fixes; `chain_cog` `?`→`!`; navigation dead-end + permission-gate fixes; doc count/runbook/workflow
drift.

### P3 — polish
`_is_staff`/`_admin`/`_VALID_MODES` dedup; rename `component_registry`; remove dead code
(`_skeleton`, `CogMenuView`, `decode_damage_type`, `_open_category`, `claim_daily_if_ready`,
`_guild_has_role_overrides`, `governance_template_applications`); cooldown/ephemeral policy docs;
empty-state wording; shop owned-item UX; trivia/8-ball panel consistency.

---

## 13. Recommended Implementation Sequence

> Grouped into coherent PRs. Each is independently shippable and CI-green. Run
> `python3.10 scripts/check_architecture.py --mode strict && python3.10 scripts/check_quality.py --full`
> before each.

**PR 1 — Foundation & safety (P0 + critical P1).**
- *Goal:* close the zero-tolerance violation and the silent data/audit bugs.
- *Scope:* move `classify_channel_name` → `utils/`; fix `DeathmatchProvider` guild scope; route
  economy/xp-reset/moderation through `emit_audit_action`; fix `feature_flags.task_enabled`
  doc/default; add `ai_permission_service.forget_guild`; implement `binding_mutation._invalidate_cache`
  + route `_run_governance_upgrade` delete through the pipeline; add the XP-boot-role regression test
  + a `governance/writes` behavioral test + an `emit_audit_action` AST invariant.
- *Files:* `services/{channel_recommender,cleanup_profiles,cog_routing_profiles,rank_providers,economy_service,xp_service,moderation_service,binding_mutation,ai_permission_service}.py`, `views/moderation/modals.py`, `governance/writes.py`, `core/runtime/ai/feature_flags.py`, `guild_lifecycle.py`, `utils/` (new `channel_classify.py`), `tests/unit/invariants/`.
- *Out of scope:* UI/select refactors; embed factory.
- *Risk:* moderation-modal rewire touches user-facing actions — keep behavior identical, add tests
  first. Cache-invalidation changes need a regression test to confirm no over-invalidation.
- *Verify:* arch strict clean; new tests fail pre-fix; full suite green.
- *Rollback:* each change is independent; revert per-file.

**PR 2 — Shared helpers / components.**
- *Goal:* remove the duplication that drives boundary drift.
- *Scope:* move `build_setup_readiness_embed` → `services/`; `_validate_against_schema`,
  `format_overwrites`, `_can_act_on`, `_KIND_TO_BINDING`, JSON codecs, `_parse_delete_count` →
  canonical homes; add `format_coins()` + `AI_COLOR`/`BTD6_COLOR`; add a **multi-select + paginated
  selector** to `views/selectors/` and a canonical `PaginatorView`.
- *Out of scope:* migrating every call site (do high-value ones; leave the rest for PR 4).
- *Risk:* low (pure moves + new primitives); grep-verify all importers.

**PR 3 — Cog-specific cleanup.**
- *Goal:* fix per-cog bugs and stubs.
- *Scope:* `chain_cog` `?`→`!`; counting admin V/M/A; RPS dead state + duck-typed `start_round` +
  `schedule_channel_deletion` → `tasks.spawn`; blackjack tournament atomicity/refund; mining
  `set_mining_inventory` txn; `xp/_helpers` raw SQL → `utils/db/xp`; remove dead code (§7);
  `!roles` permission gate; deathmatch/blackjack result-view dead-ends.
- *Risk:* game logic — add tests alongside.

**PR 4 — UX consistency pass.**
- *Goal:* uniform interaction patterns.
- *Scope:* adopt the new selectors for the multi-select candidates (channel restrict/visibility, AI
  policy/behavior, logging routes, setup channels/cog-routing); migrate the 6 settings
  `_BackToHubButton` + 8 `_refresh_parent`; consolidate game bet/opponent/result scaffolds into
  `views/games/common.py`; fix >25 truncation warnings + `ChannelSelector` empty-guard + 3 s-defer
  ordering; navigation dead-end; color/coin formatting migration.
- *Risk:* broad view churn — land behind tests added in PR 1–3.

**PR 5 — Tests / docs / observability.**
- *Goal:* close the coverage floor and doc drift.
- *Scope:* tests for the 18 cogs + game/role views + interaction_router error paths + migration
  idempotency; `--cov-fail-under`; print/utcnow AST invariants; one-shot WARNINGs/metrics on silent
  paths; update `ui-view-adoption-audit`, `navigation.py` docstring, ADR-003, `architecture.md`,
  `AGENT_ORIENTATION`, `repo-navigation-map`, `runtime_contracts` runbook ref; align
  pre-commit/CI tool versions + `requirements-dev.txt` pins + `check_quality.py`.

**PR 6 (separate track) — BTD6 ingestion + automation wiring.**
- *Goal:* make the half-built subsystems real (or explicitly shelve them).
- *Scope:* supervisor per-source intervals; odyssey-maps dependency chain; patch-notes fetch;
  retire/​wire `btd6_cache_service`; automation event-trigger dispatcher + quiet-hours timezone +
  `post_leaderboard_summary`; decide on `BTD6AssistantMessageStage` (register or delete).
- *Risk:* highest — these touch scheduled background work and external fetches. Gate behind feature
  flags; add idempotency + scheduling tests first. **Do not** bundle with PR 1–5.

---

## 14. Things Not To Change Yet

- **The BTD6 context/knowledge service cluster (§6-16).** Real overlap, but consolidation needs
  careful tracing of the two grounding paths (tool path vs NL-stage path) and the freshness contract;
  do it after PR 1–5 with dedicated tests. Premature merge risks AI-grounding regressions.
- **`governance_exceptions` relocation (arch-fix-12).** Correct target is `governance/`, but it's
  imported by `utils/subsystem_registry` and the pipeline; moving it is a cross-cutting change best
  done as its own small PR with the import graph re-verified.
- **`utils/embeds.py` expansion into a full factory.** `helper-policy.md` explicitly warns against
  opportunistic additions; this needs its own PR with a migration plan, not a drive-by.
- **Role-scope (ISSUE-007).** Latent but currently safe (the pipeline rejects role-scoped writes).
  Implement only alongside the role-fingerprint cache and a write path — not piecemeal.
- **Phase-gated stubs** (`core/resources/mutation.py`, authority checks, `config_arbitration`).
  Intentional; leave until their phase lands, but **document the removal trigger** (PR 5).
- **`pool.py` core+services imports.** Functionally fine; the telemetry-adapter extraction is a
  refactor with cycle risk — schedule deliberately, not under time pressure.
- **Single-process registries / ADR-001 deferrals.** Do not introduce Redis or new caches; the
  taxonomy is intentional.

---

## 15. Follow-Up Prompt

> Paste this to turn the audit into an execution plan.

```
Using docs/audits/repo-wide-audit-2026-05-29.md as the source of truth, produce a concrete
implementation plan for PR 1 ("Foundation & safety") only. For each finding in §12 P0 and the
PR-1-scoped P1 items (P1-1, P1-3, P1-4, P1-8, P1-9, and the moderation-service rewire P1-2):

1. Confirm the finding still holds by reading the cited file:line (the audit may be hours/days old).
2. Specify the exact change (function signature, call sites to update, new file paths) and the
   smallest diff that fixes it without altering unrelated behavior.
3. For each behavioral change, write the failing test FIRST (path + assertion), confirm it fails on
   current code, then describe the fix.
4. List every grep-verified call site that must move when relocating classify_channel_name.
5. Confirm `python3.10 scripts/check_architecture.py --mode strict` and the emit_audit_action AST
   invariant you will add both pass after the change, and that INV-F/INV-G still pass.
6. Keep PR 1 to foundation/safety only — defer all selector/embed/UX refactors to later PRs.

Do not touch the BTD6 ingestion or automation subsystems (PR 6 track). Open the PR against the
working branch when the plan is implemented and CI is green. Then ask whether to proceed to PR 2.
```

---

*End of audit. No source files were modified in producing this report.*

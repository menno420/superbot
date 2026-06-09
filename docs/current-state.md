# SuperBot — Current State

> **Status:** `living-ledger` — living status ledger (project state). **Not binding.**
> **Source code and merged PRs always win over this file.**
> The In-flight section below is a dated snapshot — **verify open PRs against
> live GitHub** before trusting it (two same-session reports already
> contradicted each other across a single merge).
>
> **▶ Next action:** Three active lanes (all PR #s reconciled 2026-06-09; verify open PRs live — **#620**, the test-only 062-storage integration test, was open at review time). **The decided cross-lane execution order (gate-lifting interview) is operationalized as a turn-key scoreboard in [`planning/multi-lane-execution-plan-2026-06-09.md`](planning/multi-lane-execution-plan-2026-06-09.md) — the autonomous test session starts there.**
>
> 1. **Mining character platform** — Wave 1 continues. Shipped: foundation **#606**, "The Descent" **#607**, combat gear→deathmatch **#608**, sell/buy market **#609**, Character overview **#610**; the **Workshop + durability keystone and the §6.3 mother-panel live overview were built 2026-06-09 in PR #624** (migration 063 `mining_gear_wear`, `cogs/mining/workshop.py`, Workshop panel + `!repair`/`!craft`/`!quickcraft` — verify merged on live GitHub; tuning + the Q-0050 lights-wear interplay flagged as **Q-0054**). **Next slices:** functional **structures** (Forge/Vault/Home — the remaining §7.5 sinks) or the first **Wave 2 platform layer** (game-XP service, §7.4). Route in: `docs/ideas/mining_exploration_brainstorm.md` §7.7 + the games folio.
> 2. **Adaptive Setup/Access platform** — Phase 0 complete; Phase 1 underway: Q-0026 identity repair + Phase 0 contracts **#588**, P1A Access Map projection **#589**, P0C groundwork **#591**, P0C seam conversion + P1B `routing_access_conflict` **#592**. **UNBLOCKED 2026-06-09 (gate-lifting interview):** P1B's `help_advertises_locked` proceeds via the **governance tier-input path** (Q-0045) with **Claude-drafted, maintainer-reviewed denial copy** (Q-0036); then P1C — Access Map + Help Preview as **staff-hub subpanels, no new command names** (Q-0032). Q-0028–Q-0031 + Q-0033 are also **answered** (catalogue committed · availability owns quiet mode · snapshots compound+high-risk · risk policy approved · account links deferred — router §20). Route in: plan §16.8.
> 3. **AI tooling (orchestration + answerability)** — orchestration Phases 1–3 shipped (**#612**, **#618**, **#619** — including the gate-lifted `ai:tools` Tools & Workflows operator UI; default byte-identical); answerability Phase 1A/1B (**#612**, Q-0043: range cash **inclusive**) + Phase 2 read model (**#616**) shipped. **Next (both scoped 2026-06-09):** orchestration **Phase 4 MVP = one vertical slice** (round-cash family plan→execute→verify + one typed answer contract, **Q-0046**) and answerability **Phase 3 = all three read-only self-awareness tools, gate lifted** (**Q-0047**). Standing posture change **Q-0048**: read-only deterministic tools ship without a per-case ask; writes/external/UI stay per-exposure. Plans: [`ai/ai-complex-request-tool-orchestration-plan.md`](ai/ai-complex-request-tool-orchestration-plan.md) · [`planning/ai-btd6-answerability-roadmap-2026-06-09.md`](planning/ai-btd6-answerability-roadmap-2026-06-09.md).
>
> Cross-cutting: **Community Spotlight** (side-lane **#613**/**#614** + hotfixes **#615**/**#617**) was hardened in the review session (canonical `utils/db/xp.py` read, `member_count` crash fix, first tests) and **Q-0044 is answered**: register it as a `community`-hub child **via the Q-0025 `new_subsystem.py` scaffold** (build scaffold → register Spotlight = the next platform slice), and the `!hub`/`!server` aliases were **dropped same day** (kept `!spotlight`/`!activity`). Also decided: BTD6 data-refresh automation = **manual-dispatch workflow** (Q-0049); mining descent lights **permanent, owner-confirmed** (Q-0050); the five product-vision questions (Q-0038–Q-0042) get a **draft-answer session** (Q-0051). Full repo review: [`audits/repo-review-2026-06-09.md`](audits/repo-review-2026-06-09.md).
>
> **Last updated:** 2026-06-09 · **Gate-lifting interview (same session, after #621 merged):** 16 open decisions answered and routed — Q-0028–Q-0033, Q-0036, Q-0044, Q-0045 flipped to Answered in the router; new Q-0046–Q-0051 recorded (orchestration P4 MVP slice · answerability P3 all-three-tools lift · **standing lift for read-only deterministic AI tools** · BTD6 manual-dispatch refresh · mining lights permanent · vision-batch draft-answer session). Spotlight `!hub`/`!server` aliases dropped (code). Earlier same day (repo-review pass, merged as **#621**): Reconciled every stale "(this session)" / "reconcile next session" marker against live GitHub: orchestration Phase 3 = **#619**, Character overview = **#610**, sell/buy market = **#609**, Context Compiler = **#594**, P0C seam conversion = **#592**. Recorded the side-lane **Community Spotlight** lane (**#613**/**#614** + hotfixes **#615**/**#617**) and hardened it (canonical `utils/db/xp.py` read, `member_count=None` crash fix, first tests). Docs refreshed in the same pass: `docs/roadmap.md` horizons (AI + games are now active lanes; at-a-glance table), `docs/ownership.md` (role-threshold cell → audited seam), `docs/repo-navigation-map.md` (+`community_spotlight` row), `docs/help-command-surface-map.md` (§3 open-gap banner), both AI plans + the wire-exploration plan (PR #s), adaptive plan §15/§16.8. New owner questions: **Q-0044** (spotlight integration + aliases), **Q-0045** (audience simulation — formalizes plan §16.8 item 3). Repo health at review: CI mirror green (**8352 passed, 16 skipped**), architecture **0 errors** (87 known warnings), docs checks pass. Full findings: [`audits/repo-review-2026-06-09.md`](audits/repo-review-2026-06-09.md). Source and live GitHub state supersede older wording; verify open PRs live.
> **Purpose:** the one file that answers "what is true right now?" so a new
> session does not reconstruct it from the journal + planning docs. Read it
> **second**, right after `.claude/CLAUDE.md`.

---

## Stability baseline

Operational stability **accepted after #535** (live cog walk: server-management,
economy, moderation, games, hub navigation). **Do not run a broad re-audit unless
a regression is reported** — this is an *accepted baseline*, not a fresh re-test.
Env-gated features (AI / scheduler / YouTube / Paragon / webhook) run **degraded
in the sandbox**, not broken. Known UX follow-ups remain (below).

## In flight (verify against live GitHub)

**Do not trust a hard-coded PR count here — it goes stale on every push.** Get the
real list at session start from live GitHub (`list_pull_requests`, state=open);
this snapshot deliberately names no open PRs. For an initiative's shipped/queued
status read its tracker (e.g. the server-management tracker), not this section.
Source code and merged PRs win over anything written here.

## Recently shipped (newest first)

> Convention: **merged PRs only** (with #numbers). In-flight work is *not* listed here —
> get it from live GitHub. The newest merge a session sees may not be added yet; that
> lag is expected (the next session reconciles). A merged PR tagged "pending" is the bug.

- **#619** — **AI tool orchestration — Phase 3 (typed policy storage + resolver + operator UI)**: closes the orchestration foundation. Migration **062** adds a nullable `orchestration_profile` column to `ai_guild_policy` / `ai_channel_policy` / `ai_category_policy`. New `services/ai_orchestration_presets.py` (built-in presets — `compatible_default` reproduces today's behaviour byte-for-byte, plus `balanced_helper` / `btd6_grounded` / `btd6_grounded_strict` / `no_tools`), `services/ai_orchestration_policy.py` (the most-specific-wins resolver — channel → category → guild → default — generation-cached, DB-fault-tolerant, dry-run trace), and `services/ai_orchestration_mutation.py` (the audited write seam: admin gate + built-in-key validation + `bump_generation` + cache-invalidate + `ai.orchestration.*_changed` events). `AIConfigSnapshot` gained a read-only `orchestration` sub-namespace (I-2 preserved + pinned). The resolved policy is wired into `natural_language_stage._invoke_gateway` (toolset narrowing via `build_registry` + `tool_choice`/`tool_budget` on `AIRequest`; **default byte-identical** — every guild that never opens the panel is unchanged). The **Tools & Workflows** AI-panel button (`ai:tools` → `views/ai/tools/`) gives per-scope profile pickers (through the audited seam) + a dry-run analyzer showing the resolved profile, offered/withheld tools with reason codes, and the loop budget. **The maintainer lifted the AI-exposure gate for this operator UI this session** (as with `btd6_round_cash`). ~40 tests + a live DB round-trip + clean boot (migration 062 applies, panel shows `ai:tools`, preview resolves). Binding doc `docs/ai-config-ownership.md` updated (read model / mutation seam / resolved semantics / custom_ids). Plan: [`ai/ai-complex-request-tool-orchestration-plan.md`](ai/ai-complex-request-tool-orchestration-plan.md) (Phase 3 / PR D+E). **Next: Phase 4** (complex BTD6 workflow) + the durable per-decision orchestration audit trace (§12.1, deferred).
- **#618** — **AI tool orchestration — Phase 2 (provider-neutral tool-choice + budgets)**: `core/runtime/ai/contracts.py` gained `ToolRequirementMode` (NONE / AUTO / REQUIRED_ANY / REQUIRED_GROUP / REQUIRED_TOOL), `AIToolChoice`, and `AIToolBudget`, plus `tool_choice`/`tool_budget` fields on `AIRequest`. A shared `ToolLoopState` + `cap_tool_result` (`core/runtime/ai/providers/base.py`) bound the model↔tool loop by hop / call / wall-time / result-size; the **OpenAI and Anthropic** adapters map the five modes onto their native `tool_choice` (`_openai_tool_choice` / `_anthropic_tool_choice` — REQUIRED_* forces a tool on the first hop then relaxes to auto; REQUIRED_GROUP rides the resolver-narrowed set; NONE offers no tools). **Defaults reproduce today's behaviour byte-for-byte** (AUTO + hop-bounded, no other caps) — every existing provider/gateway test stayed green. The gateway's redaction seam now uses `dataclasses.replace`, closing a latent drop-bug class for any future `AIRequest` field. 18 tests (all five modes × both adapters + budget exhaustion + redaction preservation). Plan: [`ai/ai-complex-request-tool-orchestration-plan.md`](ai/ai-complex-request-tool-orchestration-plan.md) (Phase 2 / PR C). **Next: Phase 3** (typed orchestration-policy storage + projection + Tools & Workflows admin UX).
- **#617** / **#615** / **#614** / **#613** — **Community Spotlight (side-lane)**: a live server-activity dashboard — `!spotlight` (panel: XP/coin leaders via `rank_providers`, per-game leaderboards, an EventBus-fed recent-level-ups feed). #613 and #614 merged 19 minutes apart outside the session workflow, then two hotfixes followed: **#615** (file rename → `community_spotlight_cog.py`) and **#617** (nonexistent `utils.logger` import → stdlib logging). Hardened in the 2026-06-09 review session: the inline `xp`-table SQL moved onto the canonical owner (`utils/db/xp.py get_guild_xp_totals` — was the only raw SQL in any cog), the `guild.member_count=None` format crash fixed, and the cog's first tests added. **Still open:** not registered in the subsystem/hub registries (Help-invisible) and the greedy `!hub`/`!activity`/`!server` aliases — owner question **Q-0044**; bannered in `docs/help-command-surface-map.md` §3.
- **#616** — **AI + BTD6 answerability — Phase 2 (central introspection read model)**: new read-only `services/ai_introspection_service.py` — a side-effect-free composition over the existing AI owners with **audience filtering at construction** (AR-08 tiers): `build_tool_catalog(scope)` (joins the new `ai_tools.all_tool_specs()` + the canonical `ai_tool_catalogue.CATALOGUE`; higher-scope tools are counted, never named), `build_btd6_answerability()` (deterministic fixtures + calculations + the one live domain + explicit unsupported gaps, from `btd6_data_service`), `build_ai_settings_view(guild_id, scope)` (reuses `ai_config_projection_service.build_snapshot`, redacted by tier — provider diagnostics platform-owner-only), and `build_policy_explanation(ctx, scope)` (composes the `ai_natural_language_policy.resolve` dry-run precedence trace + bounded `ai_decision_audit_service` history; trace + cross-user history admin+ only). Added the runtime-independent `ai_tools.all_tool_specs()` accessor (pinned == the catalogue). **No AI exposure, no UI** — those are the gated Phase 3/4; this is the additive read-*model* (the Phase 1A precedent: a deterministic owner ships before its gated exposure). 16 tests + a live smoke (real catalogue/dataset/DB; redaction verified per tier; full CI mirror **8307 passed**). Plan: [`planning/ai-btd6-answerability-roadmap-2026-06-09.md`](planning/ai-btd6-answerability-roadmap-2026-06-09.md) Phase 2. **Next: Phase 3** (the scope-filtered self-awareness tools that expose this — gated).
- **#612** — **AI tool orchestration — Phase 1 foundation (canonical catalogue + selector)**: new `services/ai_tool_catalogue.py` — the single source of truth for per-tool selection metadata (`AIToolMetadata` in `core/runtime/ai/contracts.py`: toolsets, grounding domain, freshness, …) with one `CATALOGUE` entry per registered tool, named toolset constants (§5.2), and a deterministic `select_tools` (with `ToolExclusionReason` codes). `build_registry` now consults it and gained optional `enabled_toolsets`/`disabled_tools` params that can only **narrow** the offered set — never grant above `AIScope` (proven live + tested). `BTD6_GROUNDING_TOOL_NAMES` is now **derived** from the catalogue (kills the hand-maintained drift). Default behaviour byte-identical (compatibility). This is the orchestration foundation **AR-10** wanted first; it now houses `btd6_round_cash`. Plan: [`ai/ai-complex-request-tool-orchestration-plan.md`](ai/ai-complex-request-tool-orchestration-plan.md) (Phase 1 / PR A+B). **Next: Phase 2** (neutral tool-choice + budgets).
- **#612** — **AI + BTD6 answerability — Phase 1A + 1B (round-cash, end-to-end)**: **1A** — `btd6_data_service.round_cash(round_start, round_end=None)`, the BTD6-owned, read-only round / **inclusive**-range cash query: the deterministic owner derives the range total (`range_cash`) instead of asking the model to subtract cumulative endpoints; structured per-round / range / cumulative-endpoint / `assumptions` fields + `invalid_range` / `cash_unavailable` refusals (never a fabricated number). **1B** — the read-only **`btd6_round_cash` AI tool** registered in the existing `ai_tools.build_registry` (not a parallel registry) + added to the BTD6 grounding allowlist; the instruction stack now defers range cash to the tool. **The maintainer explicitly lifted the AR-10 orchestration-first sequencing for this one read-only BTD6 tool.** **Owner decision Q-0043: range cash is INCLUSIVE of both endpoints** (r50→r60 = $19,840), correcting the prior exclusive `cumulative(B)−cumulative(A)` in the instruction stack + smoke checklist. Full CI mirror green (8266 passed); arch 0 errors. Plan: [`planning/ai-btd6-answerability-roadmap-2026-06-09.md`](planning/ai-btd6-answerability-roadmap-2026-06-09.md). **Next: Phase 2** (read-only AI introspection read model).
- **#610** — **Mining Character overview (§7.6 profile seed)**: read-only `!character`/`!profile` + a hub Character button (`views/mining/character_panel.py`) that aggregates position, equipped gear + `EffectiveStats`, coins, and inventory net worth from their existing owners — owns no data, grows as game-XP/skills/titles land. The stat-card-first step as an embed (PIL later). Tests + clean boot.
- **#609** — **Mining sell-ore / buy-gear market (Wave 1 economy loop)**: new `cogs/mining/market.py` (pure sell/buy prices — sell reuses `items.item_value`, the gear shop is a tunable coin catalogue) + `views/mining/market_panel.py` (Sell-All button + buy-gear select) + a hub Market button + `!sell`/`!sellall`/`!buy`/`!market`. Coins move **only** through the audited `economy_service` (`credit`/`debit`); inventory stays direct-lane; combat gear added to the item taxonomy so it's non-sellable + grouped correctly. Closes the mine→sell→upgrade→descend loop. 28 tests + a **live money round-trip** (sell→+coins, buy→−coins+item, insufficient-funds→rejected, coins safe).
- **#608** — **Mining combat gear → deathmatch (Wave 1 cross-game stat seam)**: promoted the pure gear→stats model from `cogs/mining/equipment.py` to **`utils/equipment.py`** (a shared, stdlib-only seam — brainstorm §7.4, extracted now that a 2nd game needed it; zero behaviour change); added **weapon/armor slots + combat gear** (`sword`/`iron sword`/`shield`/`armor` → `damage`/`defense`/`max_health`, craftable via recipes); and made **deathmatch duels read each fighter's `EffectiveStats`** (HP/attack/flat-reduction from equipped gear — a small, fair edge, tunable in `_GEAR`). 30+ new/updated tests; live-verified (clean boot, all cogs load, 0 errors).
- **#607** — **Mining "The Descent" (Wave 1 persistent depth)**: migration `061_mining_player_state` + direct-lane owner `utils/db/games/mining_player_state.py` (`get_depth`/`set_depth`) + pure `cogs/mining/world.py` (depth↔biome + descent gating, deriving one canonical `BIOME_ORDER` shared with `exploration.py`). `!explore` and `!mine` now resolve the player's **real biome** (deeper = richer ore + light-gated deep finds) instead of always Surface; new `!descend`/`!ascend` commands + hub Descend/Ascend buttons, gated by the equipped light's `depth_access` (torch→Cavern, lantern→Deep; **persistent, not consumed** — descent-gating decision in brainstorm §6.8, *flagged for owner confirm*). 31 new/updated mining tests; live-verified (migration 061 applies, `mining_player_state` table correct, MiningCog loads, 0 boot errors).
- **#606** — Mining **character-platform foundation** (brainstorm §7 vision + Wave 0/equipment): `!explore` wired to the loadout/depth engine, typed Inventory panel + net worth, the **equipment seam** (migration 060 `mining_equipment` + the `EffectiveStats` gear→stats read model + `!equip`/`!unequip`/`!gear`), and exploration reading equipped gear's stats. The reusable cross-game stat block the Descent (above) builds on; mining writes are intentional **direct-lane game state**, not an audited-service gap.
- **#594** — **SuperBot Context Compiler**: `docs/agent/index.yml` (7-subsystem manifest, curated for every folio + binding docs + source roots + do-not-create warnings + gates + verification), `tools/agent_context/build_pack.py` + `validate_pack.py`, 7 generated context packs in `docs/agent/generated/`, 13 pinning tests in `tests/unit/docs/test_agent_context_index.py`, `docs/agent/README.md`, `.claude/rules/` path-scoped Claude guidance files (mutation-and-db, discord-views, context-compiler), and updates to `docs/AGENT_ORIENTATION.md` + `docs/repo-navigation-map.md`.
- **#591** — Adaptive Setup **P0C groundwork**: the role-threshold direct-write drift-fence invariant (`tests/unit/invariants/test_no_direct_role_threshold_writes.py`) + a turn-key swap recipe (planning §16.5) + §16.8 plan-review refinements for the next agent. (The conversion itself shipped next; see ▶ Next action.)
- **#589** — Adaptive Setup **P1A**: the **Access Map projection service** (`services/access_projection.py`) — a side-effect-free composed read model (command-access + routing + governance + help axes, reusing existing owners) with 19 tests; no UI, no persistence.
- **#588** — Adaptive Setup **Q-0026 identity repair** (`cog_name_to_subsystem` CamelCase → snake_case; registry key `server_management`; latent `proof_channel`/`four_twenty` collapse fixed, regression-pinned) + Phase 0 **direct-vs-draft** and **access read-model** contracts (planning §16, `ownership.md`).
- **#585** — captured and routed owner decisions Q-0017–Q-0027 for the Adaptive Setup/Access/Routine planning lane.
- **#584** — merged the unified Server Management Hub as a first-class subsystem and completed the non-AI server-management lane.
- **#582** — server-management **PR13 deterministic slice**: `services/setup_role_templates.py` (built-in permission-free role bundles + pure `plan_template`) + the audited **`create_managed_role`** op-kind (routes through `RoleLifecycleService`, optional time/XP tier companion) + a **Role templates** setup section. Fixed a **latent PR11 regression** (the roles section's `set_role_threshold` op was never added to the DB op-kind gate/CHECK → couldn't stage): **migration 059** + a dispatcher↔gate↔CHECK drift-guard test close it. The **PR13 AI generation layer** + PR14 (hub) remained queued. (PR12 setup diagnostics & repair shipped 2026-06-07.)
- **#581** — idea-backlog grooming demo (Q-0015): promoted the mining-brainstorm `!explore` wiring into a structured plan + a `docs/roadmap.md` horizon; the standing end-of-session secondary task in action.
- **#570** — server-management **PR11** (moderation + roles setup sections) + workflow tooling + ecosystem docs (owner decision **Q-0008**: Moderation + Roles now, Governance deferred). The moderation section stages `set_setting` drafts for the PR10 knobs; the roles section adds the `set_role_threshold` op-kind for time/XP auto-role tiers. Setup diagnostics & repair (PR12) builds on top.
- **#567** — server-management **PR10 fourth slice**: optional post-kick/ban **message cleanup** (`post_action_cleanup`: none/kick/ban/both up to `post_action_cleanup_limit`, **default OFF**), owned at the `moderation_service` kick/ban seam and *requested from* `services/history_cleanup.py` (new author-scoped plan + a shared `apply_history_cleanup_plan` extracted from `!cleanuphistory` — one delete path). Best-effort: a blocked sweep never undoes the action.
- **#566** (merged) — **cross-area implementation roadmap** (`docs/roadmap.md`): the one by-area "what's planned, in what order" index (relative Now/Next/Later/Someday horizons + gates, not dates), linking each authoritative plan + folio, with a clearly-marked not-approved ideas section. Its AI section defers to the AI roadmap. Re-badged two mis-badged historical plans (`phase_2b_bindings_plan`, BTD6 extraction). Wired into `current-state` + `AGENT_ORIENTATION`.
- **#565** (Codex, merged) — source-verified **AI roadmap** (`docs/planning/ai-roadmap-2026-06-07.md`, Phase 0–11) + a 10-question batch. Opus-reviewed (sound; read-only boundary preserved). Owner answers (router §18): **AR-10** first Opus target = lock the orchestration foundation; **AR-08** tiered audience; **AR-09** explanation-only now. AR-01–07 hold at safe defaults until their lanes activate.
- **#564** — docs reachability cleanup: consolidated the 14-file BTD6 doc island into `docs/btd6/` behind the folio; archived the retired 2026-06 planning/audit burst into `docs/archive/`; corrected `AGENT_ORIENTATION`'s stale self-count and wired the orphaned `docs/context-map-tooling.md`. Added a **hard reachability gate** to `scripts/check_docs.py` (an unreachable doc fails CI unless badged `historical`/`archive`).
- **#563** — owner-workflow mapping: split the #562 capture into `docs/owner/maintainer-working-profile.md` (the *person*) + `docs/owner/ai-project-workflow.md` (the multi-agent pipeline, per-project roles, handoff templates, idea-state vocabulary); de-duplicated the restated rules to links; routed the **"a new idea is not a new priority"** rule into `.claude/CLAUDE.md` + `docs/collaboration-model.md`. Docs-only.
- **#558** — server-management **PR10 third slice**: configurable **warn escalation** owned at the `moderation_service` seam: `warn_escalation_action` (timeout/kick/ban/none at `warn_threshold`), `warn` returns a `WarnOutcome`, escalation deduplicated out of the cog + panel modal. Scalar/KV, no migration, behaviour-preserving by default.
- **#556** — server-management **PR10 second slice**: `require_reason` enforcement at the `moderation_service` seam (warn/kick/ban; timeout exempt) + a read-only bot-readiness diagnostics line on the mod panel (`utils/moderation_feasibility.py`).
- **#555** — server-management **PR10 first slice**: config-backed moderation behaviour (`moderation_config` policy + `dm_on_action` / `dm_template` / `ban_delete_message_days` / `max_timeout_minutes`) applied at the `moderation_service` mutation seam; behaviour-preserving by default.
- **#554** — implementation-readiness reconciliation: source-grounded readiness audit (`docs/audits/implementation-readiness-review-2026-06-06.md`) + reclassified stale Phase-2 / platform-consistency status cells so they aren't mistaken for current work queues; docs-only.
- **#553** — consistency-warning presentation fix (the health snapshot no longer flags benign `SKIPPED` consistency sections — bindings-from-DM / no-backfill-rows — as "needs attention") + role-hierarchy tiebreak (`role_feasibility` / `role_automation` compare hierarchy by (position, id) like discord.py, not raw `position`).
- **#552** — session journal made lean + self-maintaining: archive split (`.session-journal-archive.md`), a Quick reference, Rules regrouped, and a "tidy-each-session" protocol step (mirrored in `.claude/CLAUDE.md`); docs-only.
- **#551** — role-automation degradation fix: `role_automation.apply` preflight-guards at the mutation seam (via `utils.role_feasibility`), classifies failures, and keeps predictable Manage-Roles/hierarchy blockers off the ERROR-only health surface; operator + role-Diagnostics surfaces show the cause.
- **#550** — collaboration-model doc + truth-layer restructure (goal-first, prompts-as-guidance); docs-only.
- **#549** — server-management cleanup PR8+PR9: `policy_version` marker, presets builder + dry-run + panel diagnostics, and the guild-default `scope_id=0` no-op fix.
- **#548** — closed the migration-`057` persistence/dedupe/retention integration-test gap (test-only).
- **#546** — canonical subsystem folios (health/diagnostics, server-mgmt, settings, BTD6, games, media).
- **#544** — freshness-oriented docs route, lifecycle labels, ideas area, and subsystem-folio model.
- **#543** — boot / test-bot capability doc correction.
- **#542** — docs reconciled to shipped bot-awareness status.
- **#541** — bot-awareness **PR4–PR6**: grouped recent-error findings (opt-in),
  owner-gated `diagnostics_health_snapshot` AI tool (D1 resolved), persistent
  operational-health findings (migration `057`).
- **#539** — AI extra-tool capability **ideas backlog** (capture only, not approved work).
- **#537** — bot-awareness **PR1–PR3**: health contracts + aggregator, `!platform
  health`, startup-health snapshot.
- **#535** — back-to-Help navigation fix; stability baseline accepted.

> Older than this: see `docs/planning/*` trackers and `docs/decisions/*` ADRs.

## Next candidates

- **Cross-area sequencing + the plan index now live in [`docs/roadmap.md`](roadmap.md)**
  (by area, with Now / Next / Later / Someday horizons + gates — where to find which plan
  for which part of the code). The picks below are the current top of that list.
- Highest-value approved implementation lane: server-management. **PR10 is complete**
  (six slices, ADR-008). **PR11 (moderation + roles setup sections) merged via #570**;
  PR11's **governance** section is **deferred** (cleanup already owns the main governance
  write — revisit only with a scope decision). **PR12 (setup diagnostics & repair) was built
  2026-06-07** (read-only `setup_diagnostics` service + Diagnose & repair section). **PR13's
  deterministic role-templates slice was built 2026-06-08** (`setup_role_templates` catalogue +
  `create_managed_role` op + Role-templates setup section; also fixed a latent PR11 staging
  regression via migration 059). The next steps are the **PR13 AI generation follow-up**, then
  **PR14** (hub). The `docs/planning/server-management-status-2026-06-05.md` tracker is the
  authoritative queue — don't duplicate it here.
- Health/diagnostics maintainer live-tests (production AI tool + grouped findings):
  see `docs/subsystems/health-diagnostics.md`.
- **Docs consolidation (Q-0010) — executed 2026-06-08.** Top-level `docs/` is now **16**
  (the 13 binding contracts + `current-state` + `roadmap` + `context-map-tooling`); plans /
  audits / inventories / historical snapshots moved into clustered subdirs behind their
  folios, and `_TOP_LEVEL_DOCS_BUDGET` lowered 41 → 16. Paired with the idea-backlog
  lifecycle + grooming secondary task (Q-0015, `docs/ideas/README.md`) and the binding-doc
  section-ownership convention (`docs/owner/ai-project-workflow.md` §9). The original handoff
  was [`planning/docs-restructure-brief-2026-06-08.md`](planning/docs-restructure-brief-2026-06-08.md).
  Verify merge status on live GitHub.
- Use the canonical subsystem folios for area-specific implementation/planning. The
  2026-06-06 readiness audit classifies stale, gated, and ready workstreams.

## Gates / blocked work

- **AI / BTD6 feature expansion — re-postured 2026-06-09 (Q-0048):** AI tools that are
  **read-only AND deterministic** (no writes, no external calls, audience-tiered) carry a
  **standing lift** and may ship without a per-case ask. Anything that **writes, costs
  money, calls external services, or adds UI** still needs the per-exposure lift, and broad
  expansion stays gated on *all* of: bot-wide stability **+** provider/provenance checks
  **+** caching / source-health clarity **+** AI behavior/config correctness.
- **BTD6 data extraction** — ADR-006 provenance schema **now implemented**
  (`docs/btd6/btd6-provenance-schema.md`); extraction may resume against the ordered
  backlog in `docs/btd6/btd6-gamedata-decode-status.md`. The broader AI/BTD6
  feature-expansion gate (stability + provider/provenance + caching + AI config) still
  applies.
- `_derive_scope` → `PLATFORM_OWNER` (decision D1) — **RESOLVED** in #541; owner-only
  AI tools are now reachable.

## Known UX follow-ups (not stability bugs)

- Server-management member/role UX follow-ups: see
  `docs/subsystems/server-management.md`.
- Dense DiagnosticCog platform-subview pagination idea: see
  `docs/subsystems/health-diagnostics.md`.

## Near-term technical debt (decided, not yet implemented)

- **`new_subsystem.py` scaffold script (Q-0025) — now SCHEDULED (Q-0044, 2026-06-09).**
  Adding a hub/subsystem requires ~8 coordinated edits with no automation. Decided
  deliverable: a `new_subsystem.py` scaffold script in `scripts/` covering all
  touch-points — and the maintainer chose **build the scaffold first, then use it to
  register Community Spotlight** as a `community`-hub child (one lane, two backlog items
  closed; the scaffold gets battle-tested on a real consumer).

*(The Q-0026 `cog_name_to_subsystem` fix that used to sit here is reconciled: merged
in **#588**, listed under Recently shipped.)*

## Off-limits / do-not-propose

- No Redis / external state store (**ADR-001**).
- Game state is **not** restart-safe by design (**ADR-002**) — accepted, not a bug.
- Do not re-litigate the rejection ledger in
  `docs/planning/superbot-ideas-lab-2026-06-05.md` §6.
- Do not restate "bot fully tested & working" as *newly* verified without an actual
  boot + live walk — cite the #535 baseline instead.

## Where to read next

The **canonical read path + "what lives where"** lives in
**`docs/AGENT_ORIENTATION.md`** ("Reading order by task" + the document-classification
lists). This file is *step 3* of that path: read it for **what is true right now**, then
follow the orientation route for your task. The read-path table is **not** duplicated
here — one canonical home (`AGENT_ORIENTATION.md`).

**One-fact-one-home rule:** if a fact belongs in one of those homes, **link** to it —
do not restate it here. Restatement across files is where drift breeds. In particular,
**don't summarize plans'/trackers' PR numbers or status here** — link to the folio or
tracker, which is authoritative for its own area.

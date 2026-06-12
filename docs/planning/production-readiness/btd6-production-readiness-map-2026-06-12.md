# BTD6 production-readiness map — 2026-06-12

> **Status:** `audit` — point-in-time source/readiness review; source and live state win.

> **Mode:** docs-only mapping + production-readiness review. No runtime fixes are included.
> **Verdict:** **Partial — not production-ready for ungated expansion.** The existing BTD6 product is broad, registered, and heavily unit-tested; the deterministic v55.1 data cutover and its immediate carry-forward decode work are complete. Production readiness is still blocked by default-off ingestion, unwired cache settings, manual Postgres blob seeding, incomplete live/source-health verification, unresolved derived-value and absence-claim guarantees, and known model-faithfulness failures.
>
> **Decision rules used:** source and merged PRs win over docs; derived values are not marked Done without source/provenance evidence; no new extraction path is proposed; shared media/YouTube remains owned outside BTD6; expansion remains gated.

## Current verified state

- The five BTD6 cogs are registered in `disbot/config.py`: mother/Ask, reference, events/sources, strategy, and ops. The separate paragon cog is also registered and consumes BTD6 calculator surfaces.
- The deterministic fixture/data lane is substantial: `disbot/data/btd6/` contains 70 JSON files (catalogs plus tower, hero, and paragon stat trees). `btd6_data_service` can serve file, cloud, or warmed-Postgres providers. Production is documented as using `BTD6_DATA_BACKEND=postgres`, so a data merge is not live until `!btd6ops seed-data` updates `btd6_data_blobs`.
- The v55.1 towers cutover and post-cutover carry-forward decodes are merged. The live decode backlog is now demand-driven buff/zone decoding plus maintainer spot-checks; unexamined/undecoded dump areas remain and must not be treated as known absence.
- Live-source ingestion has a registry, fetch chokepoint, parsers, fact store, supervisor, source health, run audit, dependency refreshes, readiness view, manual refresh commands, and fixtures/tests. The supervisor is disabled by default, and cache override settings remain reserved/unwired.
- AI answerability is deterministic-first and has a large BTD6 grounding/context/tool surface. Recent merged fixes addressed elite bosses, shorthand/crosspath pricing, round-cash routing, carryover, and ABR qualifiers. Known failures remain in generated-answer faithfulness, absence claims, long-list completeness, and provenance-through-derivation.
- Shared media ownership is correct: there is no BTD6-owned YouTube/media pipeline. BTD6 strategy records may hold a guide URL, but media discovery/cache/ownership remains the shared Media/YouTube subsystem.
- **Live PR check (GitHub API, 2026-06-12):** no open PR whose title/body mentions BTD6. Recent merged BTD6-affecting PRs reviewed include #709 (ABR qualifier), #707 (live-testing fixes), #706 (round shorthand/capabilities), #703 (elite bosses, shorthand, round cash), #676 (self-applying seed-data/drift), #675 (live AI misses), #668 (carryover), #662 (Navarch/routing), #658 (Ask parity/views), #655/#653/#649 (cutover/decode), and #638 (ABR/income sets).
- `docs/decisions/006-btd6-data-provenance-ownership.md` still says extraction is paused pending schema implementation, while the schema, source, current-state ledger, and merged cutover PRs prove implementation and resumed extraction. This is documentation drift, not a live gate.

## Scope inventory table

### Cogs and command surfaces

| Item | Path | Type | State | Reason | Evidence |
|---|---|---|---|---|---|
| Mother BTD6 cog | `disbot/cogs/btd6_cog.py` | runtime cog | Done | Registered; owns lifecycle, status/diagnostics, Ask, intent test, CT team, and menu prefix/slash entrypoints. | `disbot/config.py`; cog `setup`; command/cog/parity tests |
| Reference cog | `disbot/cogs/btd6_reference_cog.py` | runtime cog | Done | Registered prefix/slash tower, hero, round, relic, and CT reference surfaces. | split-command and command-parity tests |
| Events/source cog | `disbot/cogs/btd6_events_cog.py` | runtime cog | Done | Registered live event, event detail, leaderboard, sources, source health, latest data, refresh, and grounding surfaces. | event/refresh/leaderboard/source tests |
| Strategy cog | `disbot/cogs/btd6_strategy_cog.py` | runtime cog | Partial | Browse/mine/detail/audit/submit/review and diagnostic surfaces exist; strategy-intake setting is reserved but unwired, and production moderation/use is not live-verified here. | `btd6_strategy_*`; `utils/settings_keys/btd6.py` |
| Ops cog | `disbot/cogs/btd6_ops_cog.py` | runtime cog | Partial | Readiness, runs, source enable/disable, seed-data, and announcement-channel surfaces exist with slash parity; actual production readiness depends on env/source state and manual seed operation. | ops parity/readiness/seed tests |
| BTD6 cog package helpers | `disbot/cogs/btd6/` | command builders/stage/schema | Partial | Builders, embeds, reply parity, schema, and passive stage are implemented; passive behavior and model output remain gated and not fully live-proven. | `stage.py`; builder/embed/stage tests |
| Paragon command cog | `disbot/cogs/paragon_cog.py` | BTD6-adjacent runtime cog | Partial | Registered calculator command uses BTD6 paragon surfaces; documented sandbox/degraded API behavior prevents a blanket production-verification claim. | registration; paragon views/tests |

### Runtime services, grounding, cache, and providers

| Item | Path | Type | State | Reason | Evidence |
|---|---|---|---|---|---|
| Deterministic data API | `disbot/services/btd6_data_service.py` | data/query owner | Done | Validates and queries catalogs, rounds/ABR, cash, costs, relics, powers, MK, Geraldo, bosses, and provider drift; cache reset and immediate reseed behavior exist. | broad `test_btd6_data_service*`, round/cash/relic tests |
| Raw providers | `disbot/services/btd6_data_provider.py` | provider path | Partial | File, cloud, and warmed-Postgres implementations exist; production Postgres data still requires explicit seeding and cloud/prod behavior is not live-verified in this review. | provider/cloud/postgres tests; migration 054 |
| Static blob DB adapter | `disbot/utils/db/btd6_data.py` | DB data path | Done | Fetch/count/upsert API for `btd6_data_blobs` exists and is used by the Postgres provider/seed lane. | migration 054; seed tests |
| Static fixture corpus | `disbot/data/btd6/` | production reference data | Partial | 70 committed JSON blobs cover broad v55.1 reference/stats data, but decode docs explicitly retain undecoded buff/zone and unexamined areas. | decode-status backlog; inventory/audit scripts |
| CSV staging corpus | `data/btd6/` | tooling input | Partial | README plus tower/hero CSVs support import preparation; it is not the production served-data lane. | import/fetch scripts |
| Stats owner | `disbot/services/btd6_stats_service.py` | query owner | Partial | Tower/hero/paragon combat structures and degree stats are broadly mapped; remaining buff/zone decode tail and accepted paragon fallback edge prevent full completeness. | decode-status; stats/paragon tests |
| Upgrade resolver/detail | `disbot/services/btd6_upgrade_service.py`; `btd6_upgrade_detail_service.py` | resolver/query owners | Partial | Named upgrade, aliases, notation, attacks/minions/buffs/zones are reachable; path-level phrasing and synonym/absence handling remain incomplete. | resolver/detail/minion tests; absence-claim design |
| Resolver/vocabulary | `disbot/services/btd6_resolver_service.py`; `btd6_resolver_vocabulary.py` | routing path | Partial | Broad deterministic entity routing and recent alias/plural fixes exist; recent PRs demonstrate continuing phrasing/routing misses. | recent #703/#707/#709; resolver tests |
| Context owner | `disbot/services/btd6_context_service.py` | AI grounding composer | Partial | Large deterministic grounding path auto-attaches catalogs, costs, stats, live facts, and carryover; known long-list/model-faithfulness and unresolved-subject gaps remain. | context/carryover/grounding tests; faithfulness findings |
| AI-safe live context facade | `disbot/services/btd6_ai_context_service.py` | read facade | Done | Typed, read-only summaries for events, entities, restrictions, leaderboard, source status, and fact search. | AI context tests |
| AI knowledge blocks | `disbot/services/btd6_ai_knowledge_block_service.py` | prompt grounding path | Partial | Live state, freshness, catalog, pricing, crosspath, and guidance blocks exist; generated model compliance is not guaranteed. | knowledge-block/guidance tests; live findings |
| BTD6 AI orchestrator | `disbot/services/btd6_ai_service.py` | answer orchestrator | Partial | Deterministic-first answer plus optional AI augmentation and grounding attachment exist; model faithfulness remains the frontier and feature behavior is gated. | AI service/augmentation/grounding-pin tests |
| Grounding verifier | `disbot/services/btd6_grounding_service.py` | safety/provenance gate | Partial | Live reply validation fails closed for unsupported names/numbers, but `validate_answer` is documented as legacy/unwired and negative-existential/absence claims are not fully guarded. | source comments; grounding tests; absence design |
| Fact store/provenance | `disbot/services/btd6_fact_store.py` | grounded live-fact path | Partial | `DataProvenance`, writer, and intent reads are implemented against source-linked rows; static blob facts and derived values do not uniformly carry row-level provenance through every response. | provenance schema/tests; derived-value finding |
| Knowledge API/service | `disbot/services/btd6_knowledge_api.py`; `btd6_knowledge_service.py` | grounded read API | Done | Typed fact bundles and read composition exist behind AI/grounding consumers. | knowledge API/service tests |
| Response builder | `disbot/services/btd6_response_builder.py` | deterministic response path | Partial | Deterministic responses and restriction composition exist; it does not eliminate all model-generated answer risks on AI paths. | response/restriction tests |
| Capability queries | `disbot/services/btd6_capability_service.py` | aggregate query | Done | Deterministic cross-entity capability lookup exists and is tool-exposed. | capability tests |
| Superlative queries | `disbot/services/btd6_superlative_service.py` | derived aggregate query | Partial | Runtime rankings exist, but DPS is explicitly rough/non-authoritative and must not be presented as a proven exact derived value. | service docstring/tests |
| View models | `disbot/services/btd6_view_model_service.py` | composition owner | Done | Typed view models, freshness, and context handles separate query services from presentation. | view-model tests and boundary tests |
| Paragon calculation service | `disbot/services/paragon_service.py` | BTD6-adjacent query/client | Partial | Calculator requirements/results path exists, but external API and documented fallback/degraded behavior prevent a blanket production claim. | paragon service/math/view tests |
| Cache cadence contract | `disbot/services/btd6_cache_service.py` | cache policy | Partial | Default cadence vocabulary exists; module describes itself as the M3A contract and cache override settings are reserved/unwired. | `utils/settings_keys/btd6_cache.py`; cache tests |
| Fetch chokepoint | `disbot/services/btd6_fetch_service.py` | external-source client | Partial | HTTP validation, pagination cap, breaker, and typed failures exist; production endpoint health and credentials were not live-probed here. | fetch/path/pagination tests |
| Source registry/health | `disbot/services/btd6_source_registry.py` | source-health owner | Partial | Freshness buckets, source specs, and health reads exist; readiness still depends on live populated registry and current fetch success. | registry/health tests; readiness service |
| Source mutation | `disbot/services/btd6_source_mutation.py` | audited write path | Done | Centralized enable/disable/create/audit mutations exist. | mutation tests; ops cog |
| Parsers | `disbot/services/btd6_source_parser.py`; `disbot/services/parsers/*btd6*` | ingestion parse path | Partial | Registered parsers and fixtures cover Ninja Kiwi/Steam source shapes; external schema drift remains an operational risk. | parser/mapping-coverage tests |
| Ingestion orchestration | `disbot/services/btd6_ingestion_service.py`; `btd6_ingestion_sources.py` | refresh path | Partial | Manual/dependency refresh, parent-source policy, parse/store/run auditing exist; successful production refresh was not live-verified. | ingestion/dependency/boss-chain tests |
| Ingestion supervisor | `disbot/services/btd6_ingestion_supervisor.py` | scheduled runtime service | Not Done | Implemented but disabled by default via `BTD6_INGESTION_ENABLED=false`; production-ready scheduled freshness cannot be claimed without enabled/live evidence. | module contract; supervisor tests |
| Ops readiness aggregation | `disbot/services/btd6_ops_readiness_service.py` | ops read model | Partial | Aggregates env gate, supervisor, registry, freshness, breakers, and runs; it can correctly report disabled/partial but does not itself make the lane ready. | readiness tests |
| Live queries | `disbot/services/btd6_live_query_service.py` | DB live-read path | Done | DB-read layer for active events/details/restrictions/leaderboards/CT facts exists with mapping coverage. | live-query/restriction/CT tests |
| Patch/version path | `disbot/services/btd6_patch_service.py`; `btd6_version_announce.py` | patch/ops path | Partial | Steam patch ingestion and per-guild announcements exist; legacy KV/binding convergence and live delivery verification remain. | migration 055; patch/version tests |
| CT team path | `disbot/services/btd6_ct_team_service.py` | guild/live query | Partial | Typed guild setting and on-demand bracket fetch exist; weekly group IDs stale by design and require manual repaste. | CT team tests; settings docs |
| Strategy services | `disbot/services/btd6_strategy_service.py`; `btd6_strategy_mutation.py`; `btd6_strategy_review_service.py` | reference/UGC path | Partial | Read, audited mutation, review, retention, and grounding validation exist; intake key and production moderation workflow remain unproven/unwired. | strategy tests; migration 041 |

### Views and reference/strategy surfaces

| Item | Path | Type | State | Reason | Evidence |
|---|---|---|---|---|---|
| Main/admin panels | `disbot/views/btd6/panel.py`; `admin_panel.py` | Discord views | Partial | Broad menu/admin navigation exists; environment/live interaction verification is incomplete. | panel/admin view tests and embed snapshots |
| Tower browser/stats/events | `disbot/views/btd6/tower_browser_view.py`; `tower_stats_view.py`; `tower_events_view.py` | reference views | Done | Browser, detail, pro stats/crosspath, and event status surfaces exist. | tower/view/embed tests; #658 |
| Hero browser/stats | `disbot/views/btd6/hero_browser_view.py`; `hero_stats_view.py` | reference views | Done | Hero browsing and stats surfaces exist. | view-model/embed tests |
| Live events/leaderboards | `disbot/views/btd6/live_events_view.py`; `leaderboard_browser_view.py` | live-source views | Partial | Interactive views exist; usefulness depends on live ingestion/source health. | live events/leaderboard tests |
| CT views | `disbot/views/btd6/ct_map_view.py`; `ct_group_flow.py` | live/guild views | Partial | CT map and preview-confirm team flow exist; live weekly external state and manually supplied group IDs remain operational dependencies. | CT builder/team tests |
| Paragon views/modals | `disbot/views/btd6/paragon_view.py`; `paragon_stats_view.py`; `paragon_modals.py` | calculator/reference views | Partial | Calculator, requirements, degree stats, and modal input exist; derived/fallback caveats and sandbox degradation prevent full production claim. | paragon math/stats tests; decode-status caveat |
| Strategy views | `disbot/views/btd6/strategy_browse.py`; `strategy_submit.py`; `strategy_review.py` | UGC views | Partial | Browse/submit/review UI exists with audited backend; intake routing and production moderation are not fully wired/verified. | strategy tests; reserved setting |
| Shared BTD6 view exports | `disbot/views/btd6/__init__.py` | package surface | Done | Central export surface exists for BTD6 view entrypoints. | imports/command tests |

### DB, data, scripts, ops, and AI-facing capability surfaces

| Item | Path | Type | State | Reason | Evidence |
|---|---|---|---|---|---|
| Live source/fact DB | `disbot/migrations/040_btd6_sources.sql`; `disbot/utils/db/btd6_sources.py` | DB/data path | Done | Registry, source audit, facts, CT facts, patch notes, snapshots, and typed query/write helpers exist. | JSONB writer/fact/source tests |
| Strategy DB | `disbot/migrations/041_btd6_strategies.sql`; `disbot/utils/db/btd6_strategies.py` | DB/data path | Done | Strategy store and audit log with retention/state operations exist. | strategy service/mutation/review tests |
| Ingestion-run DB | `disbot/migrations/048_btd6_ingestion_runs.sql` | ops DB path | Done | Run lifecycle/status/error metadata and indexes exist. | ingestion/supervisor/readiness tests |
| Static blob DB | `disbot/migrations/054_btd6_data_blobs.sql` | static data path | Partial | Production blob store exists, but `sha256` is informational rather than a runtime integrity gate and refresh is manual. | migration comments; seed path |
| Source enable/version migrations | `disbot/migrations/042_btd6_sources_enable_m3b.sql`; `053_btd6_ct_group_enable.sql`; `055_btd6_steam_patch_source.sql` | DB migrations | Done | Source enablement, CT setting, and Steam patch source migrations exist. | migrations/source registry |
| Settings keys | `disbot/utils/settings_keys/btd6.py`; `btd6_cache.py` | config surface | Partial | CT group and version announcement keys are consumed; strategy intake and all cache tuning keys are explicitly reserved/unwired. | module docs; reserved-key tests |
| BTD6 utility families | `disbot/utils/btd6/` | shared domain helpers | Partial | Helpers cover IDs/coercion, coverage, CT rendering/geometry, damage/difficulty/effects, freshness/grounding formatting, keywords/rules/name guards, paragon math, embeds, tiers, and restrictions; paragon fallback and decode/grounding caveats remain. | utility/service tests; decode-status |
| Seed/import/upload tools | `scripts/seed_btd6_data.py`; `import_btd6_data_from_csv.py`; `upload_btd6_data.py`; `fetch_btd6_wiki_data.py` | data tooling | Partial | Conversion, validation, blob seeding, cloud manifest/upload, and legacy wiki fetch tools exist; production still needs manual seed and wiki is not authority for new game-data extraction. | script tests; ADR/decode rules |
| Decode/inventory/diff tools | `scripts/btd6_decode_inventory_report.py`; `btd6_gamedata_inventory.py`; `btd6_patch_diff.py` | extraction/review tooling | Partial | SHA/audit/inventory/diff tools support safe review; decode backlog explicitly remains. | script tests; decode-status |
| Grounding probe | `scripts/btd6_probe.py` | AI/debug tooling | Done | Provides deterministic route/grounding triage for live-answerability failures. | probe tests; #666 |
| Manual refresh workflow | `.github/workflows/btd6-data-refresh.yml` | ops function | Partial | Manual-dispatch refresh exists; it is not evidence of automatic, successful production freshness. | workflow; ingestion readiness |
| AI BTD6 tool catalogue | `disbot/services/ai_tools.py` | AI capability surface | Partial | Exposes lookup, roster, capability, superlative, difficulty cost, round composition/cash, map, mode, relic, power, MK, Geraldo, boss, bloon filter, cumulative cost, power effect, paragon calculate/requirements/stats, CT team, and answerability tools. Tool availability is broad, but correct invocation/model use remains inconsistent. | AI tool catalogue/handler tests; recent live findings |
| AI routing/policy | `disbot/services/ai_task_router.py`; `ai_tool_catalogue.py`; `ai_introspection_service.py`; central AI stage | shared AI surface | Partial | BTD6 route/toolsets/introspection exist and recent routing bugs were fixed; live misses continue to prove routing/tool discipline is not closed. | router/tool/introspection tests; #703/#707/#709 |
| Media/YouTube ownership | shared Media/YouTube subsystem; strategy `guide_url` only | shared-media boundary | Done | No BTD6-owned media pipeline exists or is proposed; any media caching/discovery remains shared-owner work. | ADR-007 references; repository search |
| BTD6-focused tests | `tests/unit/btd6/`; BTD6-named tests across `tests/unit/{cogs,services,scripts,db,invariants,runtime}` | verification | Partial | Coverage is broad, but `tests/unit/btd6/` itself contains only paragon math and no live Discord/Postgres/external-source end-to-end proof. | test inventory |

## Required before production-ready

1. **Keep expansion gated.** Do not approve a broad BTD6 feature/extraction expansion until current-state and live PR state explicitly lift the gate. As of 2026-06-12, they do not.
2. **Prove the production data lane.** Record a production verification showing the served Postgres blob version/hash, successful `seed-data`, immediate cache reset/rewarm, and drift cleared. Decide Q-0077 (auto-seed-on-boot) rather than silently depending on operator memory.
3. **Prove the live-source lane.** Enable the ingestion supervisor only with an explicit operator decision, then demonstrate source registry population, successful scheduled/manual runs, breaker behavior, freshness buckets, stale-run recovery, and degraded-source rendering in production-like conditions.
4. **Wire or retire cache controls.** Reserved cache settings and source `cache_policy_key` claims must either become real read paths with SettingSpecs or be removed from readiness language. Do not claim tunable cache policy today.
5. **Close faithfulness blockers.** Pin and fix the known PMFC/POD substitution, long-list omissions/miscounts, cross-field conflation, and negative-existential behavior before treating generated BTD6 answers as production-reliable.
6. **Make derivations auditable.** Exact derived values must travel through deterministic tools/read models and retain input/source/version evidence. Rough estimates must remain explicitly labelled. No derived value gets a Done verdict merely because arithmetic exists.
7. **Verify live user surfaces.** Run the maintained smoke checklist plus maintainer spot-checks against the deployed bot, including Ask, menu, reference, events, CT, strategy moderation, ops, paragon, source labels, and degradation behavior.
8. **Reconcile binding/living docs.** Update ADR-006's stale pause wording and any stale decode-status summary rows without weakening its provenance ownership decision.

## Bugs, inconsistencies, and risks

- **Known model-faithfulness bugs:** correct grounding can still be replaced by a similarly named entity, long grounded lists can be truncated/miscounted, and separate attack/effect fields can be conflated.
- **Absence claims are not safely closed:** an unresolved lookup or an unsurfaced field can still license a confident false “no”; the proposed resolution-status gate remains design work, not shipped behavior.
- **Legacy/unwired grounding entry:** `btd6_grounding_service.validate_answer` is described in source as legacy/currently unwired; the live path is `validate_btd6_reply`. Future callers could choose the wrong seam.
- **Production data drift is operationally possible:** production serves Postgres blobs, not merged files. Manual seeding is a human dependency; blob `sha256` is informational, not an integrity gate.
- **External source drift:** Ninja Kiwi and Steam response shapes can change despite fixture-backed parser coverage. Production credentials/availability and current health were not probed in this docs-only review.
- **CT group staleness is expected:** the guild-supplied bracket ID changes weekly and requires operator/user action.
- **Strategy surface is only partially activated:** the strategy-submission-channel key is explicitly unwired, while submit/review commands and DB paths already exist.
- **Documentation contradiction:** ADR-006 says extraction stays paused; source/current-state/merged PRs prove the schema and extraction campaign shipped. Source wins, but the stale ADR wording can misroute a future agent.
- **Decode-status numbering and historical rows are noisy:** the current backlog has duplicate item number 3 and retains historical statements that are superseded later in the same document. Use its top/current backlog and source, not isolated old rows.

## Data provenance and groundedness gaps

- `DataProvenance` is implemented for live fact rows, source registry linkage, and freshness; that does **not** prove uniform per-fact provenance for every static blob field, composed view, deterministic answer, or model-generated sentence.
- The hybrid model is real: static reference blobs live in `btd6_data_blobs`; live facts/source health live in the source-registry/fact tables. The seam is operationally sound but can produce mixed answers whose provenance granularity differs by fact.
- Exact arithmetic paths such as cumulative costs and round cash have deterministic owners/tools. They are Done as calculations, but generated answers remain Partial until every presented derivation is tool/read-model grounded and version/source attributable.
- `btd6_superlative_service` explicitly labels DPS as rough. It must never be promoted to an authoritative exact ranking without a stronger model and evidence.
- Undecoded buff/zone/status/targeting/income behavior fields and unexamined dump domains are unknown, not evidence of absence.
- Wiki/CSV tooling remains useful for comparison/import preparation but does not supersede the pinned game-data/decode-status authority for new extraction.

## AI answerability / routing gaps

- The AI tool surface is broad, deterministic-first, and heavily tested, but recent PRs show that entity aliases, qualifiers, follow-ups, shorthand, and default-profile tool access continue to expose gaps.
- Tool availability is not tool discipline: the model may omit a needed deterministic call, ignore correct grounding, or freehand a derived value.
- The absence-claim backstop remains unimplemented. The safe behavior for unresolved subjects or unmodelled attributes is a bounded “I do not have that in committed data,” not an absolute negative.
- Long-list answers need a deterministic rendering or completeness check; grounding the full list is insufficient if the model can drop entries.
- The passive BTD6 message stage is configuration/channel/confidence/cooldown gated; its existence does not establish universal answerability.
- Carryover grounding has a first shipped slice, not a proof that all conversational references and qualifier inheritance are reliable.

## Source-health, cache, and refresh gaps

- The ingestion supervisor is default-off. Therefore scheduled production freshness is **Not Done** unless live environment evidence proves it intentionally enabled and healthy.
- Cache cadence defaults exist, but operator cache settings are reserved/unwired. Per-source policy claims should be treated as contract/design, not full runtime configurability.
- `!btd6ops readiness` can accurately report disabled/partial/ready based on registry, freshness, breaker, and run signals; no captured live verdict was available in this review.
- Manual refresh, dependency chains, parser/store auditing, circuit breakers, and stale-run recovery are implemented and tested. Current external-source health and credentials remain unverified.
- Static data refresh has multiple tools (import, upload, seed, manual workflow) but no proven automatic deploy-to-served-data convergence.

## Gated or blocked work

- Broad BTD6 expansion remains gated by the global stability/caching/AI-config and behavior requirements.
- New extraction must follow the current decode-status backlog and evidence rules; do not create a parallel extraction path.
- The remaining buff/zone tail is demand-driven and requires confirmed semantics/evidence before values are committed.
- The absence-claim gate is design-only and requires review before implementation.
- Strategy channel intake and cache tuning settings are reserved/unwired.
- Auto-seed-on-boot is an open owner decision (Q-0077).
- Shared media/YouTube work is outside BTD6 ownership and must remain in the shared subsystem.

## Simplification opportunities

- Retire the stale “M3A/M3B future” wording where runtime wiring already exists, while preserving the true unwired cache-setting gap.
- Make one operator-facing production data version/hash/status view the source of truth for bundled files versus served Postgres blobs, rather than relying on boot log plus status plus seed command knowledge.
- Consolidate duplicated historical/current claims in the decode-status document and fix its duplicate backlog numbering; do not change decode conclusions.
- Clearly deprecate or remove the unwired legacy grounding entrypoint so future code cannot accidentally bypass the live verifier.
- Prefer deterministic complete renderers for roster/list/table questions over asking a model to reproduce long grounded lists.
- Keep shared media references as URLs/IDs owned by the shared media subsystem; do not add BTD6-specific caching or ingestion.

## Tests and live-verification gaps

- The repository has extensive BTD6 unit coverage across cogs, services, scripts, DB helpers, routing, grounding, ingestion, views, and invariants. The narrowly named `tests/unit/btd6/` directory is not representative; it only contains paragon math.
- Missing from this review: a deployed Discord smoke pass, a live production Postgres seed/drift probe, current `!btd6ops readiness` output, a successful real scheduled ingestion cycle, and current external-source breaker/freshness evidence.
- Known model-faithfulness repros need durable regression coverage at the final-answer/verifier layer, not only context-builder assertions.
- Add live-verification records for manual source refresh, source disable/degradation, stale source display, CT weekly ID failure, strategy moderation, version announcement delivery, and passive-stage gating.
- Validate the current smoke checklist against v55.1 data before relying on pinned expected counts; historical expected values can drift by patch.

## Recommended next session

Run a **verification-only production-readiness session**, not an expansion or extraction session:

1. Check live open PRs again and confirm no conflicting BTD6 work.
2. Capture `!btd6 status`, `!btd6 diagnostics`, `!btd6ops readiness`, and recent ingestion runs from the deployed bot.
3. Verify served Postgres blob version/hash versus bundled files; run `seed-data` only if drift is real and record before/after evidence.
4. Exercise one manual refresh and one degraded/disabled source path; record freshness, breaker, run-audit, and user-visible behavior.
5. Run the maintained BTD6 smoke checklist plus the known PMFC/POD, map-list completeness, SOTF conflation, absence-claim, carryover, ABR, elite-boss, crosspath-price, and round-cash regressions.
6. Turn the observed failures into a bounded next plan. Do **not** start a new extraction path; consult the decode-status document first for any data gap.
7. Reconcile ADR-006's stale pause wording and current decode-status bookkeeping in a separate docs-only cleanup if live/source evidence confirms the present state.

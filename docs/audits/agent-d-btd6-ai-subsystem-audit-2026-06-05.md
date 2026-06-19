# Agent D — BTD6, AI, Paragon, and Video subsystem audit

> **Status:** `historical`
> **Superseded 2026-06-19 (was active):** 2026-06-05 audit burst; reconciled into superbot-audit-consolidation (also historical). Do not act on this — current map: [planning/README](../planning/README.md).

> **Superseded (2026-06-05):** reconciled into
> [`../planning/superbot-audit-consolidation-2026-06-05.md`](../planning/superbot-audit-consolidation-2026-06-05.md)
> (verified, RC-n IDs; drives RC-10/11/12). Read that first; this is historical context.

Date: 2026-06-05

Branch audited: `main`

Head commit verified through the GitHub connector: `d583dcb082580298e063d718ab7eb534a47ad3ea`

Scope: repository-state audit only, followed by this documentation-only handoff. No source code, migrations, tests, or runtime configuration were changed.

## Verification limits

The original audit prompt requested local shell checks such as `git status`, branch parity commands, full test execution, and architecture-quality scripts. This environment did not have a cloned repository and outbound cloning from `github.com` was unavailable, so those checks were **not run**. The audit below is based on direct GitHub connector reads of the current repository files and commit metadata. Any item that depends on local execution is marked as a missing verification step rather than inferred.

## Files and areas inspected

Primary files inspected directly:

- `disbot/cogs/btd6_cog.py`
- `disbot/cogs/btd6_reference_cog.py`
- `disbot/cogs/btd6_events_cog.py`
- `disbot/views/btd6/panel.py`
- `disbot/views/btd6/paragon_view.py`
- `disbot/services/btd6_data_service.py`
- `disbot/services/btd6_data_provider.py`
- `disbot/services/btd6_context_service.py`
- `disbot/services/btd6_upgrade_service.py`
- `disbot/services/ai_gateway.py`
- `disbot/services/ai_tools.py`
- `disbot/services/ai_natural_language_policy.py`
- `disbot/cogs/ai_cog.py`
- `disbot/core/runtime/ai/natural_language_stage.py`
- `disbot/services/paragon_service.py`
- `disbot/services/youtube_context_service.py`
- `disbot/services/youtube_fetch_service.py`
- `disbot/services/video_reference_cache_service.py`

Repository search was also used to locate related BTD6, AI, Paragon, YouTube, migration, test, and documentation files.

---

## 1. Agent D scope verdict

Agent D still owns the BTD6 + AI integration audit surface. The current codebase is not in a greenfield or broken state; it has a substantial service-layer architecture, central AI policy routing, deterministic BTD6 data loading, BTD6 grounding, read-only AI tools, an implemented Paragon calculator, and a gated YouTube context path.

The correct Agent D outcome is **not** immediate implementation. The correct outcome is to freeze the current map, hand off cross-owner seams to Agent A/B/C, and let BTD6 extraction continue only after a short verification checkpoint for freshness/source semantics, data-provider parity, and lookup-surface consistency.

## 2. Verified branch and PR state

Confirmed through GitHub connector reads:

- `main` is the default branch.
- The audited head commit is `d583dcb082580298e063d718ab7eb534a47ad3ea`.
- The latest merge commit found in connector search is PR #506, `docs(btd6): smoke-test checklist + refresh stale counts`.
- Recent related merge commits include BTD6 map roster/stale counts, cash grounding, map removables, per-round cash, and buff stat coverage.

Not verified locally:

- `git status --short`
- `git branch --show-current`
- `git rev-parse HEAD`
- `git log --oneline --decorate -n 25`
- local comparison against upstream `origin/main`
- full open-PR inventory beyond connector search visibility

Risk: low for audit direction, medium for final implementation planning. Before implementing follow-up fixes, run the local branch/test commands from the original prompt.

## 3. Current BTD6 architecture map

The BTD6 subsystem is split into clear strata:

- **Mother cog:** `disbot/cogs/btd6_cog.py` owns the `!btd6` / `/btd6menu` entry points, panel bootstrapping, status/diagnostics/ask/test-intent, CT team prefix utility, schema registration, version announcement setup, data-provider warmup, and ingestion supervisor lifecycle.
- **Reference cog:** `disbot/cogs/btd6_reference_cog.py` owns deterministic tower/hero/round/relic/CT reference commands.
- **Events cog:** `disbot/cogs/btd6_events_cog.py` owns live events, leaderboards, source registry views, manual refresh, latest-data, source-health, and grounding inspection commands.
- **Persistent BTD6 panel:** `disbot/views/btd6/panel.py` owns the public anchor panel and opens ephemeral drill-down browsers for live events, towers, heroes, leaderboards, CT, modes, status, Paragon, admin, and maps.
- **Data source of truth:** `disbot/services/btd6_data_service.py` loads and validates deterministic fixture data.
- **Data provider seam:** `disbot/services/btd6_data_provider.py` abstracts file, cloud, and Postgres-backed fixture bytes.
- **AI context:** `disbot/services/btd6_context_service.py` renders BTD6 facts into grounded prompt facts for the central AI stage.
- **Upgrade resolver:** `disbot/services/btd6_upgrade_service.py` provides first-class upgrade identity and alias resolution.
- **AI tools:** `disbot/services/ai_tools.py` exposes BTD6 lookup/roster/capability/superlative/cost/round/map/mode/relic/bloon/paragon/CT-team tools.
- **View-model layer:** `disbot/services/btd6_view_model_service.py` exists and is used by the BTD6 panel.

The architecture is substantially modular. The remaining risk is overlapping composition ownership, not lack of structure.

## 4. Current AI architecture map

The AI subsystem is also layered:

- `disbot/services/ai_gateway.py` is the provider-neutral service-layer shim over `core.runtime.ai.gateway`.
- `disbot/services/ai_natural_language_policy.py` is the single natural-language reply policy resolver.
- `disbot/core/runtime/ai/natural_language_stage.py` owns the passive reply pipeline: policy, routing, feature facts, instruction assembly, gateway call, rendering, grounding guard, sending, memory append, and audit.
- `disbot/cogs/ai_cog.py` owns admin-facing diagnostics, readiness, policy preview, settings, routing, providers, support report, and the AI panel entry point.
- `disbot/services/ai_tools.py` owns read-only tool specs and handlers offered to the model by scope.
- `disbot/services/youtube_context_service.py` plugs video facts into the same central feature-fact path.

The current AI design is close to the intended central orchestration pattern. Provider calls are not scattered through BTD6 or cogs; the central stage is the choke point.

## 5. What currently works

Confirmed from source reads:

- BTD6 no longer relies on a legacy passive BTD6 message stage; `BTD6Cog.cog_load()` explicitly unregisters the BTD6 stage while `AICog.cog_load()` registers the central natural-language stage.
- BTD6 static/reference data is loaded through `btd6_data_service`, not parsed directly in cogs.
- BTD6 data providers are pluggable behind `BTD6RawProvider` with file, cloud, and Postgres implementations.
- The BTD6 panel no longer mutates the public anchor for drill-downs; it opens ephemeral subviews.
- The BTD6 panel uses `btd6_view_model_service.build_hub_view_model()` for its hub embed.
- Manual source refresh is routed through helper/service logic and gated by `manage_guild` on command surfaces.
- AI natural-language reply eligibility is centralized in `ai_natural_language_policy.resolve()`.
- The central AI stage audits denial, skip, degraded, replied, and errored paths.
- The BTD6 faithfulness guard validates BTD6 replies against gathered facts and BTD6 tool outputs, retries once, then falls to a deterministic refusal.
- The deterministic BTD6 refusal stamps the current loaded game version.
- AI tools are read-only and scope-gated.
- Paragon forward/reverse calculation exists in both AI tools and an interactive BTD6 view.
- YouTube/video context is feature-flag gated, API-key gated, sanitized, cached, and integrated through the central feature-facts path.

## 6. Confirmed problems and risks

### Important: BTD6 has too many adjacent read/composition owners

The following layers all contribute to BTD6 user-facing answer construction or grounded facts:

- `btd6_data_service`
- `btd6_knowledge_service`
- `btd6_context_service`
- `btd6_view_model_service`
- `btd6_response_builder`
- `btd6_stats_service`
- `btd6_upgrade_service`
- `_builders.py` / `_embeds.py`
- `ai_tools.py` BTD6 handlers

This is not necessarily wrong, but it is now the main maintainability risk. The next BTD6 extraction work should not add another facade. It should define which existing layer owns each output type:

- raw/static facts
- derived numeric values
- source/freshness metadata
- prompt facts
- embed/view-model facts
- AI tool result facts
- command response formatting

### Important: upgrade lookup is implemented, but ownership is split

`btd6_upgrade_service.py` explicitly states that the older resolver recognizes towers, heroes, maps, modes, bloons, relics, and live entities, but not upgrades, and that this module fills the gap. It also states that wiring into resolver / AI grounding / panel is separate.

The current AI tool description and BTD6 context path indicate upgrade lookup has been integrated enough for AI use, but Agent D should still treat this as a split resolver model until local tests prove all command, AI, and panel surfaces route through it consistently.

### Important: static-fixture freshness and live-source freshness are not fully uniform

Live facts from `btd6_facts` carry source registry provenance and fetched timestamps. Static fixture facts often render as `fixture/btd6_data`, `BTD6 in-game description`, or derived formula explanations. That is useful, but it is not the same freshness model users see for live events.

This matters before adding more extracted data because the bot is becoming source-backed, not merely fixture-backed. New extraction should standardize:

- source key
- source type
- extraction date/version
- game version
- whether the value is direct, parsed, derived, wiki-curated, API-live, or local estimate

### Medium: cloud provider may not provide every stats-related file path

`CloudRawProvider.list_names()` lists warmed cache files and notes that cloud warm only fetches fixtures, so the `stats/` tree is not available on the cloud backend. BTD6 stats/paragon/context code uses stats-derived data. Before moving more BTD6 data to cloud/Postgres, verify that all stats consumers behave correctly on each provider backend.

### Medium: interaction router lifecycle has a permanent-process registration seam

`AICog.cog_load()` directly inspects `interaction_router._handlers` to avoid duplicate registration and notes that `interaction_router` has no unregister API. This is intentional and guarded, but it is an Agent A platform-lifecycle seam, not something Agent D should own long term.

### Medium: YouTube/video belongs to shared AI/media ownership, not BTD6

YouTube context is correctly feature-gated and attached through central AI feature facts, but it is not BTD6. Agent D should not absorb it into BTD6 planning. It should be treated as a shared AI/media subsystem with platform and external-API concerns.

### Medium: Paragon is cross-system

Paragon is BTD6 domain logic, but it depends on an external calculator API, attribution, rate-limit behavior, local fallback math, AI tools, and Discord views. It should remain BTD6-owned for domain behavior, but external dependency and attribution rules should be documented as a shared integration seam.

## 7. Critical blockers

No critical blocker was confirmed from source reads alone.

However, the following are blocking verification gaps before implementation:

1. Full local test suite was not run.
2. Architecture/quality scripts were not run.
3. Open PR inventory was not fully verified beyond commit/search reads.
4. Provider-backend parity for stats-derived data was not executed.
5. Live command behavior was not smoke-tested in Discord.

## 8. Important quality improvements

1. Create a BTD6 ownership matrix for data/raw facts/derived facts/view-models/tool results/AI prompt facts/embed formatting.
2. Add or refresh tests proving upgrade aliases (`PMFC`, `POD`, `Phoenix Lord`, `Abyss Lord`) work through every relevant surface, not only `btd6_upgrade_service`.
3. Standardize source/freshness labels across static fixtures, extracted wiki/game data, live NK data, tool outputs, and AI context facts.
4. Verify cloud/Postgres provider parity for stats/paragon/stat-tree consumers before any larger extraction migration.
5. Move permanent interaction-router lifecycle concerns into a platform-owned policy or helper rather than letting AI cog inspect a private handler map long term.
6. Add a short Paragon dependency note covering API URL, author attribution, fallback semantics, rate-limit behavior, and where AI answers must credit the source.
7. Add a YouTube/media ownership note so it does not drift into BTD6 or generic AI by accident.

## 9. Medium-priority cleanup

- Reconcile command/help footer examples with the current split command surface. The BTD6 panel footer still references historical compact examples and should be checked against current `!btd6ref`, `!btd6events`, `!btd6ops`, and strategy surfaces.
- Confirm all slash surfaces intentionally use ephemeral responses. This matches current BTD6 drill-down behavior, but the project has a broader no-ephemeral preference for main menus.
- Review whether prefix and slash command error detail should differ. Example: `refresh-source` prefix suppresses exception detail while slash includes it.
- Review exact ownership of `_builders.py`, `_embeds.py`, `btd6_response_builder.py`, and `btd6_view_model_service.py` to prevent duplicate formatting growth.
- Validate that all public-facing BTD6 lists show correct counts after the latest stale-count refresh.

## 10. Future opportunities

- Treat `btd6_view_model_service` as the long-term read facade for UI/panel surfaces rather than building a new facade.
- Add a single `SourceAttribution` / `DataProvenance` object that every BTD6 user-facing surface can render consistently.
- Add a generated BTD6 data inventory report in CI or docs so extraction progress is visible without running ad-hoc scripts.
- Create a small docs index for BTD6 data sources, extraction status, known stale fields, source confidence, and current game version.
- Move YouTube/video into a named `media_context` or `video_reference` subsystem if it expands beyond YouTube.

## 11. Ownership handoff by agent

### Agent A — platform/runtime/lifecycle

Owns:

- `core/runtime/ai/**`
- message pipeline registration semantics
- interaction router lifecycle and unregister/idempotency policy
- persistent view restoration mechanics
- global audit/observability guarantees
- feature flag evaluation infrastructure

Agent A should inspect:

- Whether process-lifetime interaction-router registration without unregister is acceptable.
- Whether natural-language stage ordering and duplicate passive-listener tests still cover BTD6 after recent merges.
- Whether send-path audit guarantees still truly produce one row per path after retry/floor logic.

### Agent B — Discord surfaces/governance/UX

Owns:

- BTD6 panel UX and command discoverability
- slash/prefix parity
- ephemeral vs public-response policy
- settings/help command surfacing
- admin/staff command visibility and permission gates

Agent B should inspect:

- Whether BTD6’s current ephemeral drill-down pattern matches the project-wide no-ephemeral policy exceptions.
- Whether `manage_guild` refresh/admin controls match governance capability tiers.
- Whether help/menu examples reflect the split cog command structure.

### Agent C — database/migrations/cache

Owns:

- BTD6 source registry tables
- `btd6_data_blobs` / fixture storage
- YouTube video cache table
- migration ordering and rollback safety
- cache invalidation and provider availability behavior

Agent C should inspect:

- Provider parity for file/cloud/Postgres BTD6 data.
- Whether stats-derived consumers still work when only warmed fixture names are available.
- Whether YouTube cache error TTLs and success TTLs match desired operational behavior.

### Agent D — BTD6/AI integration

Owns:

- BTD6 facts and grounding
- BTD6 data extraction prioritization
- BTD6 AI tools and prompt-fact correctness
- Paragon domain behavior
- BTD6 lookup/alias correctness
- BTD6 faithfulness guard behavior

Agent D should not own interaction-router lifecycle, global feature flag semantics, or DB migration infrastructure except as a consumer.

## 12. BTD6 data extraction readiness verdict

Verdict: **proceed cautiously after a verification checkpoint, not blindly.**

The subsystem is structurally ready for more data extraction in the sense that it has:

- a central deterministic data loader;
- a provider seam;
- validation hooks;
- extensive BTD6 AI grounding;
- read-only AI tools;
- source registry surfaces;
- a view-model layer.

But extraction should pause briefly to answer these questions:

1. Which service owns direct extracted facts versus derived values?
2. How does every extracted value carry source/freshness/version metadata?
3. Do file/cloud/Postgres providers all expose the same data needed by stats/paragon consumers?
4. Are newly extracted facts rendered consistently in command embeds, panel views, AI tool outputs, and BTD6 context facts?
5. Which stale counts from PR #506 are still real after local tests?

## 13. Highest-priority BTD6 data gaps

Based on inspected dataclass shape, comments, and recent commit context, prioritize:

1. **Source/freshness model for static/extracted data** — highest architectural leverage.
2. **Stats-provider parity** — ensure stats/paragon/tower stats work across all backends.
3. **Map data clarity** — removables currently distinguish blank as “no data”, not “none”; continue replacing ambiguity with explicit source-backed values.
4. **Upgrade alias and detail coverage** — confirm upgrade names, aliases, descriptions, costs, and stats flow through commands, AI, and tools.
5. **Buff/stats coverage** — latest docs mention stale buff counts; confirm what remains stale.
6. **Alternative roundsets** — `RoundEntry.roundset` exists, but current comments emphasize default rounds; ABR/other sets are natural next structured data if source-backed.
7. **Paragon stat confidence** — some paragons have no published combat-stats module; preserve explicit “only cost known” semantics.

## 14. BTD6 command and button surface assessment

Confirmed healthy patterns:

- Main panel is persistent and registered through the persistent view system.
- Public anchor is not edited for drill-downs.
- User drill-downs open ephemeral browsers.
- Staff admin button checks staff permissions and opens admin controls separately.
- Paragon is reachable from the BTD6 panel.
- CT view can attach a generated map image when available.

Potential issues:

- The BTD6 panel footer examples may lag behind the split cog command reality.
- Slash command responses are heavily ephemeral; this may be right for drill-downs but should be checked against the user’s broader menu UX preference.
- Prefix/slash behavior sometimes differs in error detail and response shape.
- `!btd6 ask` uses deterministic BTD6 AI service, while natural-language messages use the central AI stage. This split is acceptable only if docs clearly explain the difference.

## 15. AI policy, routing, and observability assessment

Confirmed healthy patterns:

- `ai_natural_language_policy.resolve()` is the single policy resolver.
- The resolver is pure read logic and returns typed decisions.
- Policy dry-run traces exist for admin previews.
- The central stage records audit rows on denials, skips, degraded paths, replies, and errors.
- Cooldowns are enforced by the stage after policy resolution, which keeps policy pure.
- Fresh-user allowance is consumed only after an actual delivered reply.

Risks:

- The audit guarantee should be locally tested after recent retry/floor logic.
- The central stage is large and owns many orchestration steps; it is correct as a choke point, but must stay service-composed and heavily tested.
- Interaction-router process-lifetime behavior needs platform ownership.

## 16. AI tool assessment

Confirmed healthy patterns:

- Tools are documented as read-only.
- Tools are scope-gated before being offered to the model.
- BTD6 grounding tool names are explicitly listed so only BTD6 fact tools can whitelist BTD6 claims.
- Server/user/config tools cannot ground hallucinated BTD6 names or numbers.
- BTD6 AI tools now include broad domain coverage: lookup, roster, capability, superlative ranking, difficulty costs, round composition, maps, modes, relics, bloons, cumulative costs, Paragon calculation, Paragon requirements, Paragon stats at degree, and CT team status.

Risks:

- The surface is broad enough that source/freshness/provenance drift is the main failure mode.
- Tool descriptions are doing significant behavioral steering. Keep tests around tool availability, grounding-tool whitelist, and failure semantics.
- Paragon tools return attribution requirements that the model must obey; deterministic renderers are safer where possible.

## 17. Paragon assessment

Confirmed healthy patterns:

- `paragon_service.py` wraps the live API and falls back to a labelled local estimate for transport/5xx/schema failures.
- HTTP 429 is handled distinctly and does not silently degrade to estimate.
- Forward results are cached briefly and in-flight requests are coalesced.
- Reverse requirements are solved locally and confirmed with a forward call when possible.
- The Paragon view exposes calculate, requirements, stats, difficulty, player count, extra T5 selection, and a web-calculator link.
- Both view and AI tool paths share attribution from the service.

Risks:

- External dependency behavior should be operationally documented.
- Local fallback exactness depends on `utils.btd6.paragon_math`; tests must remain pinned.
- Some paragon stats are unavailable because no stats module is published; UI already handles this, and AI answers must preserve the same limitation.

## 18. YouTube/video assessment

Confirmed healthy patterns:

- YouTube context is feature-flag gated.
- The flag defaults off, and a YouTube API key is also required.
- Supported URLs are parsed and capped at two videos.
- Metadata and transcript are sanitized before becoming facts.
- Cache access goes through `video_reference_cache_service`, not raw SQL.
- Missing transcripts are represented as a limitation rather than an exception.
- The central AI stage denies video tasks when no video grounding facts are available.

Risks:

- YouTube is a shared AI/media subsystem, not BTD6. It should not be folded into BTD6 extraction planning.
- Transcript fetching depends on `youtube-transcript-api` and may silently return empty on many failure types. This is acceptable for UX but should be observable if video features become important.
- Cache/status taxonomy should be owned by Agent C if video caching expands.

## 19. Missing verification and test coverage

Required next local checks:

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git log --oneline --decorate -n 25
python -m pytest tests/unit/runtime/ai tests/unit/services/test_btd6_context_grounding.py tests/unit/services/test_ai_tools.py tests/unit/services/test_paragon_service.py tests/unit/views/btd6/test_paragon_view.py tests/unit/services/test_youtube_context_service.py
```

Recommended additional checks:

```bash
python -m pytest tests/unit/services/test_btd6_upgrade_service.py tests/unit/services/test_btd6_upgrade_detail_service.py tests/unit/services/test_btd6_central_policy_integration.py tests/unit/runtime/test_no_duplicate_passive_listeners.py tests/unit/invariants/test_cog_size.py
```

Manual Discord smoke tests:

- Ask `PMFC stats`, `POD cooldown`, `Phoenix Lord`, and `Abyss Lord` through natural-language AI and command/tool surfaces.
- Open `!btd6`, click Live Events, Towers, Heroes, Leaderboards, CT, Modes, Paragon, Maps, Status, Admin.
- Confirm public panel anchor does not mutate.
- Try `/btd6events refresh-source` as staff and non-staff.
- Ask BTD6 questions that should trigger deterministic floor/refusal.
- Ask a Paragon forward and reverse question through both panel and AI.
- Test a YouTube URL with feature off, missing key, valid metadata/no transcript, and cached error.

## 20. Root causes vs symptoms

Root causes:

- BTD6 data and AI grounding now span many mature layers without a single documented ownership matrix.
- Static/extracted data and live/fetched data use different provenance models.
- Some cross-system features, especially Paragon and YouTube, are domain-adjacent but not purely owned by one subsystem.
- Runtime/platform lifecycle behavior is embedded in product cogs in a few places.

Symptoms:

- Stale docs can claim features are plan-only even when AI tools already exist.
- Lookup bugs show up as “AI does not know X” when the real issue is resolver/tool/context ownership.
- Button/command inconsistencies show up as UX bugs but often trace back to split cogs and historical compatibility.
- Source/freshness uncertainty shows up as trust problems in BTD6 answers.

## 21. Simplification opportunities

1. Keep `btd6_view_model_service` as the UI read facade; do not invent another BTD6 facade.
2. Use `btd6_context_service` only for AI prompt facts, but document that boundary because it currently renders many derived lines.
3. Create one BTD6 provenance object and render it everywhere.
4. Keep AI tools read-only; do not add write tools until deterministic mutation services and explicit confirmations exist.
5. Move platform lifecycle helper behavior out of product cogs where possible.
6. Keep YouTube as `video_reference` / media context if it grows, not as part of BTD6.
7. Keep Paragon domain-owned by BTD6 but integration-documented as an external API dependency.

## 22. Recommended next step

Recommended destination: **Decisions**, not implementation.

Decision prompt should ask for a short architecture decision on:

1. BTD6 provenance model.
2. Exact owner for raw facts vs derived facts vs AI prompt facts vs view-model facts.
3. Whether static extracted data should be migrated into `btd6_data_blobs`, source registry rows, or both.
4. How to verify provider parity before the next extraction batch.
5. Whether Paragon and YouTube need separate ownership docs.

After Decisions produces that target shape, Revision should sanity-check for drift, then implementation can proceed in small docs/test-first PRs before data extraction resumes.

## 23. Copy-paste-ready collaboration summary

Agent D verified the current `main` state for BTD6 + AI integration at commit `d583dcb082580298e063d718ab7eb534a47ad3ea` using GitHub connector reads. The subsystem is structurally mature: BTD6 has split cogs, a persistent panel, a deterministic data service, provider seam, AI context service, upgrade resolver, source-health commands, and read-only AI tools. AI has a central natural-language stage, a pure policy resolver, gateway shim, audit recording, BTD6 faithfulness guard, and scoped read-only tool registry. Paragon is implemented through a live API wrapper with labelled local fallback, AI tools, and an interactive BTD6 view. YouTube/video context is feature-flagged, API-key gated, cached, sanitized, and plugged into the same feature-facts path.

No critical source-level blocker was confirmed, but implementation should not continue blindly. The main risks are ownership drift and provenance inconsistency: BTD6 facts, derived values, tool outputs, prompt facts, view-models, and embeds are spread across several mature layers. Before the next BTD6 extraction batch, decide and document the ownership matrix and source/freshness model. Also verify file/cloud/Postgres provider parity for stats-derived consumers, because some cloud-provider comments indicate only warmed fixture files are available, not the full stats tree. Tests and local git commands were not run in this environment, so local verification remains required before implementation.

Recommended handoff: send this to Decisions for a focused BTD6 provenance/ownership decision, then Revision for a drift check, then implement docs/tests before adding more extracted data.

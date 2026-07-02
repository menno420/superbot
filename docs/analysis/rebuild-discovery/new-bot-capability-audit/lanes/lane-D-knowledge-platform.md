# Lane D — Knowledge, AI & Platform (Axis 1)

> **Status:** `audit` — documentation-only audit for `ai`, `btd6`, `project_moon`, `help`, `settings`, `logging`, `diagnostic`, `ux_lab`, `utility`, `general`, and `proof_channel`.
>
> **Substrate verified:** `BRIEF.md`, `PARTITION.md`, and this lane file were present in this checkout before editing. Source code wins over docs; rows below cite source paths and line numbers.

**Method:** required reading completed in order: `.claude/CLAUDE.md`, `docs/AGENT_ORIENTATION.md`, `docs/current-state.md`, `docs/current-state/S2-btd6.md`, `docs/current-state/S3-ai-memory.md`, audit `BRIEF.md`/`PARTITION.md`, this lane file, `ground-truth/command-surface.json`, grammar spike `spec.py`/`measure.py`/`RESULTS.md`/`manifests/server_logging.py`, and `docs/analysis/rebuild-discovery/ai-knowledge-data-tooling-map.md`. `python3.10 scripts/context_map.py ...` was attempted for inspected `disbot/*.py` files, but this environment lacks `PyYAML`, so exact source verification used `rg`, `sed`, and `nl` instead.

**Tier semantics used exactly as the spike:** tier 1 = generated/kernel workflow; tier 2 = declared parameterized spec family; tier 3 = escape-hatch code/handler logic. Known amendments are G-1 GatewayListenerSpec, G-2 list-valued settings + add/remove workflows, G-3 AnnouncementRouteSpec, G-4 command cooldowns, G-5 declarative validator bounds, and G-6 per-kind command namespaces.

## Lane-level conclusion

Lane D needs two reusable grammar families in addition to G-1…G-6:

* **G-7 `KnowledgeDomainSpec`** — required for BTD6 and Project Moon, and useful for generated help/settings diagnostics. It should declare `domain_key`, aliases, command/panel projections, source registry, trust/freshness policy, ingest/refresh actions, context builders, answerability/eval suites, diagnostics, AI routing/denial semantics, governance/audit boundaries, and visibility gates. Evidence: BTD6 exposes source registry/refresh/health/grounding commands in `btd6_events_cog.py:85-131`, AI-safe BTD6 context carries source/freshness labels in `btd6_ai_context_service.py:108-295`, and Project Moon mirrors the context/provenance seam in `projmoon_context_service.py:109-199`.
* **G-8 `AITaskProfileSpec` / `AIProviderGatewaySpec`** — required for provider routing, task profiles, tool budgets, redaction, refusals, evals, review/preset feedback loops, and diagnostics. Evidence: `AITask`, `AIRequest`, `AIToolBudget`, `AIResponse`, and diagnostics contracts live in `core/runtime/ai/contracts.py:16-341`; provider/model routing is env + task driven in `core/runtime/ai/routing.py:28-136`; natural-language routing/context/refusal/provider orchestration is concentrated in `core/runtime/ai/natural_language_stage.py:220-1649`.

These are **declaration families**, not approval to generate domain logic. Kernel generation should own the visible surfaces, policy gates, freshness/eval contracts, and provider/data-source wiring; deterministic calculators, parsers, source-specific fetchers, answer synthesis, and live moderation/audit seams remain explicit handler refs.

### Lane D fit totals

| Subsystem | Units | Tier 1/2 as-written | Fit as-written | Tier 1/2 with G-1…G-8 | Fit with amendments | Recommendation |
|---|---:|---:|---:|---:|---:|---|
| ai | 70 | 43 | 61% | 62 | 89% | redesign into AI platform specs; keep thin handlers |
| btd6 | 78 | 42 | 54% | 66 | 85% | keep, improve as `KnowledgeDomainSpec` exemplar |
| project_moon | 22 | 14 | 64% | 20 | 91% | improve/merge with knowledge-domain family |
| help | 24 | 22 | 92% | 23 | 96% | keep as generated projection with overlay mutations |
| settings | 28 | 26 | 93% | 27 | 96% | keep as generated config hub |
| logging | 62 | 49 | 79% | 60 | 97% | keep; already spike exemplar for G-1/G-2/G-3 |
| diagnostic | 65 | 39 | 60% | 56 | 86% | improve with `DiagnosticProviderSpec` catalogue |
| ux_lab | 27 | 17 | 63% | 24 | 89% | keep as zero-write UX gallery/spec testbed |
| utility | 21 | 15 | 71% | 18 | 86% | merge/simple utility command pack |
| general | 22 | 16 | 73% | 19 | 86% | merge/simple content command pack |
| proof_channel | 21 | 14 | 67% | 18 | 86% | improve as binding + timed-task surface |
| **Total** | **440** | **297** | **68%** | **393** | **89%** | add G-7/G-8 before new-bot generation |

## Proposed new amendments

* **G-7 — `KnowledgeDomainSpec`:** `domain_key`, aliases, source registry, trust tier, freshness bucket policy, committed data refs, live data refs, ingestion/refresh routes, context builders, deterministic answerability rules, eval/probe suites, diagnostics providers, commands/panels/help projections, permission gates, audit boundaries.
* **G-8 — `AITaskProfileSpec` + `AIProviderGatewaySpec`:** task id, provider/model routing, fallback provider, response mode, tool requirements/budgets, context builders, prompt/instruction profile, denial semantics, redaction contract, review/preset stores, diagnostics counters, eval suite, external-provider secret requirements.
* **G-9 — `TimedTaskSpec`:** one-shot delayed task with key prefix, lifecycle cleanup, audit hooks, and recovery semantics. Needed by proof-channel timed unlocks and in-memory utility reminders; not covered by recurring `ManagedTaskSpec` alone.
* **G-10 — `ModalFormSpec`:** Discord modal fields, validation, submit handler, result render, and audit declaration. Current `PanelActionSpec` covers a button opening a handler, but not reusable modal form schema for proof, utility, ux_lab, and generated settings/help editors.

---

## ai

### Surface-unit ledger

| Unit | Kind | Evidence | Tier as-written | Tier with amendments | Rationale / gap |
|---|---|---|---:|---:|---|
| `!ai`, `!aimenu`, `/ai`, `/aimenu` panel/status/readiness/settings/policy/diagnostics/providers/routing/forget/support-report | command family | `ai_cog.py:365-780` | 2 | 1 | Mostly command→panel/provider routes; slash/prefix duplicate namespace needs G-6; cooldown-free admin commands are generated. |
| AI panel/settings/help views | panel/help | `ai_cog.py:151-159`, `ai_cog.py:788-793`, `views/ai/panel.py` | 2 | 1 | Generated panel projection over AI diagnostics/settings once AITaskProfileSpec exists. |
| `!aireview` channel/off/list/export/resolve/preset add/from/list/remove | command family | `ai_review_cog.py:172-490` | 3 | 2 | Review/preset workflows recur; become declared AnswerReviewLog/PresetAnswerStore operations under G-8, with export/resolve as thin handlers. |
| correction reply stage + 👎 reaction listener | listener/context path | `ai_review_cog.py:50-61`, `ai_review_cog.py:118-160` | 3 | 2 | G-1 declares reaction listener; correction stage remains handler but can be registered as an AI review ingestion path. |
| `EVT_AI_REVIEW_LOGGED` subscription/emits + policy mutation emits | event/listener | `ai_review_cog.py:104-114`, `services/ai_review_log_service.py:297`, `services/ai_policy_mutation.py:382,544` | 2 | 1 | EventSpec/EventSubscription projections; handler code only for payload rendering. |
| AI settings keys | setting | `utils/settings_keys/ai.py:10-35` | 1 | 1 | Plain settings; generated settings hub. |
| AI policy, review-log, preset stores | store | `migrations/039_ai_policy.sql`, `migrations/100_ai_review_log.sql`, `migrations/102_ai_answer_presets.sql`, `utils/db/ai_presets.py:26` | 2 | 1 | StoreSpec plus sole-writer/projection boundaries. |
| AI tasks, provider routing, tool budget, response/evidence contracts | AI task/platform | `contracts.py:16-341`, `routing.py:28-136` | 3 | 2 | Missing as-written; G-8 makes task/provider routing declarative while provider calls stay handler refs. |
| Natural-language router, BTD6/Project Moon/YouTube context gathering/refusals | AI routing/context | `natural_language_stage.py:220-1649` | 3 | 2 | G-8 + G-7 declare routing, context builders, denial semantics; NL classification and rendering remain escape hatches. |
| Diagnostics/readiness snapshot | diagnostic provider | `ai_cog.py:183-246`, `contracts.py:341` | 2 | 1 | DiagnosticProviderSpec. |

**Manifest sketch**

```python
SubsystemManifest(
  key="ai",
  commands=(CommandSpec("ai", PREFIX, route=PanelRef("ai.panel")), CommandSpec("ai diagnostics", PREFIX, route=PanelRef("ai.diagnostics")), ...),
  panels=(PanelSpec("ai.panel", body=(BlockSpec("fields", ProviderRef("ai.status")),)),),
  settings=(SettingSpec("AI_ENABLED"), SettingSpec("AI_DEFAULT_PROVIDER"), SettingSpec("AI_REVIEW_CHANNEL"), ...),
  stores=(StoreSpec("ai_policy"), StoreSpec("ai_review_log"), StoreSpec("ai_answer_presets")),
  events=(EventSpec("ai.review_logged"), EventSpec("ai.policy_changed")),
  diagnostics=(DiagnosticProviderSpec("ai.readiness"), DiagnosticProviderSpec("ai.routing")),
  ai_tasks=(AITaskProfileSpec("btd6.answer", context=ProviderRef("btd6.context"), eval_suite="btd6_qa"), ...),
  ai_gateway=AIProviderGatewaySpec(providers=("openai", "anthropic"), redaction="required", fallback_env="AI_FALLBACK_PROVIDER"),
)
```

**Tier-3 disposition:** external-provider calls, natural-language classification, provider SDK calls, prompt rendering, tool execution, and answer synthesis remain intentional handler refs; review/preset workflow, event wiring, task profiles, redaction, and diagnostics move to G-8.

**Structural flags:** AI external-provider calls ✅; natural-language routing ✅; eval/answerability contracts partial; governance/visibility gates ✅; generated help/settings diagnostics ✅; event/listener wiring ✅.

**MAP → RECONSIDER → SIMULATE → OPTIMIZE:** keep the platform contract but redesign as `AIProviderGatewaySpec` + `AITaskProfileSpec`; dependency layer core/runtime + services; done when every task has provider/fallback/context/eval/redaction/review declarations and CI proves no unredacted request path; outperform target pending Lane F.

---

## btd6

### Surface-unit ledger

| Unit | Kind | Evidence | Tier as-written | Tier with amendments | Rationale / gap |
|---|---|---|---:|---:|---|
| `!btd6menu` and `/btd6menu` | command/panel | `btd6_cog.py:171-198` | 2 | 1 | Command→panel + help projection. |
| `!btd6events` live/event/leaderboard/sources/source-health/latest-data/refresh-source/grounding | command/diagnostic/data-source | `btd6_events_cog.py:38-131` | 3 | 2 | G-7 declares source registry, freshness, refresh and grounding inspection; refresh handler remains source-specific. |
| `!btd6ops` readiness/runs/source_enable/source_disable/seed-data/announcechannel | command/ops/ingestion | `btd6_ops_cog.py:41-105` | 3 | 2 | G-7 ingestion/admin actions + governance gates; seed/toggle handlers stay service refs. |
| `!btd6ref` tower/hero/round/income/rbe/relic/ct | command/knowledge query | `btd6_reference_cog.py:37-90` | 3 | 2 | Deterministic query routes over declared KnowledgeDomainSpec. |
| `!btd6strat` browse/mine/strategy/audit/submit/pending/why-no-response | command/store/AI review | `btd6_strategy_cog.py:39-161` | 3 | 2 | Strategy store/review workflow is declarable; review extraction remains handler/AI task. |
| BTD6 panel/admin/category/tower/hero/live/leaderboard/paragon/strategy views | panel/view | `views/btd6/*.py` (e.g. `panel.py:159`, `admin_panel.py:86`, `tower_browser_view.py:264`) | 2 | 1 | Generated panels over knowledge-domain read providers, except calculators/forms. |
| settings and capabilities | setting/gate | `utils/settings_keys/btd6.py:31-35`, `utils/subsystem_registry.py:801-805` | 1 | 1 | Settings/capabilities are declaration data. |
| source registry, snapshots, facts, blobs, strategies, ingestion runs | store/data source | `utils/db/btd6_sources.py`, `utils/db/btd6_data.py`, `utils/db/btd6_strategies.py`, BTD6 migrations | 2 | 1 | StoreSpec + G-7 source registry. |
| version detected emit/subscriber | event/listener | `services/btd6_patch_service.py:150-151`, `services/btd6_version_announce.py:111` | 3 | 2 | AnnouncementRouteSpec/G-3 + G-7 source event. |
| AI context summaries/source/freshness/facts | context builder | `btd6_ai_context_service.py:108-295`, `btd6_ai_context_service.py:528-648` | 3 | 2 | Core G-7 evidence: context builder + freshness/trust rules. |
| evals/probes/refresh scripts | eval/ingestion | `scripts/run_evals.py`, `scripts/btd6_probe.py`, `scripts/fetch_btd6_wiki_data.py`, `scripts/parse_gamedata.py` | 3 | 2 | Declare eval and ingestion paths; source-specific parser/fetcher code remains handlers. |

**Manifest sketch**

```python
KnowledgeDomainSpec(
  domain_key="btd6", aliases=("btd6", "bloons"),
  commands=("btd6menu", "btd6events sources", "btd6ref tower", "btd6strat submit", ...),
  panels=("btd6.panel", "btd6.sources", "btd6.tower_browser", "btd6.strategy_review"),
  sources=(SourceSpec("ninja_kiwi", trust="official", freshness="live"), SourceSpec("committed_csv", trust="repo", freshness="release"), SourceSpec("wiki_formula", trust="derived", freshness="manual")),
  stores=("btd6_source_registry", "btd6_source_snapshots", "btd6_facts", "btd6_data_blobs", "btd6_strategies"),
  ingest=(IngestAction("refresh-source", handler="btd6.refresh_source"), IngestAction("seed-data", handler="btd6.seed_data")),
  context_builders=(ContextBuilderSpec("btd6.answer", provider="btd6_ai_context"),),
  evals=(EvalSuiteSpec("btd6_qa", command="scripts/run_evals.py --btd6"), ProbeSpec("btd6_probe")),
  diagnostics=("source-health", "latest-data", "grounding"),
)
```

**Tier-3 disposition:** propose G-7. Source fetchers, parsers, formulas, paragon calculators, and strategy review AI remain handler refs; source registry/freshness/trust/context/eval surfaces should be declared.

**Structural flags:** knowledge trust/freshness ✅; eval/answerability ✅; diagnostics ✅; generated help/settings ✅; event/listener wiring ✅; scheduled refresh loops are external workflow/script-driven, not an in-process loop in inspected cogs.

**Recommendation:** keep/improve; optimal form is the exemplar `KnowledgeDomainSpec`; dependency layer services + data + AI context; done when each answer block is source-labelled, each source has freshness, and refresh/eval probes are CI/ops-visible; outperform pending Lane F.

---

## project_moon

### Surface-unit ledger

| Unit | Kind | Evidence | Tier as-written | Tier with amendments | Rationale / gap |
|---|---|---|---:|---:|---|
| `!pm`/`/pm`, lookup/list/origins/sinner/sin/status/ego/damage/mechanic | command family | `project_moon_cog.py:74-175` | 3 | 2 | Knowledge query surface; G-7 makes category/query map declarative. |
| `LimbusBrowseView` and category buttons | panel/view | `views/projmoon/browse.py:140-185` | 2 | 1 | Generated browse panel over domain registry/categories. |
| help hook and registry capability | help/gate | `project_moon_cog.py:188-191`, `utils/subsystem_registry.py:808` | 1 | 1 | Help projection. |
| committed structural data + keyword helpers | data source | `project_moon_cog.py:13-18`, `data/projmoon/`, `utils/projmoon/` | 3 | 2 | G-7 declares committed source registry/trust. |
| AI grounding context/provenance | context builder | `projmoon_context_service.py:109-199` | 3 | 2 | Same G-7 context-builder pattern as BTD6. |

**Manifest sketch**

```python
KnowledgeDomainSpec(
  domain_key="project_moon", aliases=("pm", "limbus", "projectmoon"),
  commands=("pm lookup", "pm list", "pm sinner", "pm status", ...),
  sources=(SourceSpec("limbus_structural_data", trust="repo_committed", freshness="patch_stable"),),
  context_builders=(ContextBuilderSpec("projmoon.answer", provider="projmoon_context_service"),),
  panels=("project_moon.browse",), diagnostics=("source coverage",),
)
```

**Tier-3 disposition:** G-7. No DB/write/store observed; fixture load/search logic remains handler code.

**Flags/recommendation:** knowledge-source trust ✅; freshness coarse/patch-stable; natural-language grounding partial through AI stage; keep/improve and merge with BTD6 domain grammar; done when source registry and eval/answerability probes match BTD6.

---

## help

### Surface-unit ledger

| Unit | Kind | Evidence | Tier as-written | Tier with amendments | Rationale / gap |
|---|---|---|---:|---:|---|
| `!help` and `/help` | command | `help_cog.py:282-370` | 2 | 1 | G-4 command cooldown; otherwise generated projection. |
| Help dropdown/category route | panel/listener | `cogs/help/panels.py:38-94`, `cogs/help/route.py:166-192` | 2 | 1 | Panel/select + renderer providers. |
| Help overlay editor/home-builder/reset controls | panel/mutation | `views/help/editor.py:285-614`, `views/help/home_builder.py:158-337` | 2 | 2 | Generated forms/panels; modal/editor specifics benefit from G-10. |
| overlay writes + audit event | store/event | `services/help_overlay_mutation.py:150-363`, `migrations/064_help_overlay.sql:26` | 2 | 1 | StoreSpec + EventSpec. |
| build catalogue/single-command/not-found renderers | help projection | `services/help_catalogue.py:116`, `cogs/help/route.py:166-192` | 1 | 1 | Help-as-projection. |

**Manifest sketch:** `SubsystemManifest(key="help", commands=(CommandSpec("help", cooldown=(3,10,"user")),), panels=(PanelSpec("help.home"), PanelSpec("help.editor")), stores=(StoreSpec("help_overlay"),), events=(EventSpec("audit.action_recorded"),), help=HelpEntrySpec(projected=True))`.

**Disposition/recommendation:** no new AI/knowledge gap; G-10 improves editor forms. Keep. Done when all subsystem manifests project into help and overlay drift tests pass.

---

## settings

### Surface-unit ledger

| Unit | Kind | Evidence | Tier as-written | Tier with amendments | Rationale / gap |
|---|---|---|---:|---:|---|
| `!settings`, `!settings access`, `/settings` | command | `settings_cog.py:120-198` | 2 | 1 | G-4 cooldown + generated settings hub. |
| SettingsHub, subsystem, audit, invalid, missing binding/resource/access views | panel/diagnostic | `views/settings/hub.py:138-330`, `views/settings/subsystem_view.py:609`, `views/settings/audit_view.py:130` | 2 | 1 | Canonical generated config panel family. |
| settings/binding/resource schemas | setting/binding/resource | `settings_cog.py:68`, subsystem schema modules | 1 | 1 | §2 core grammar already fits. |
| recent changes/audit/invalid/missing providers | diagnostic provider | `views/settings/*.py`, `services/settings_*` | 2 | 1 | DiagnosticProviderSpec. |
| help hook | help | `settings_cog.py:172` | 1 | 1 | Help projection. |

**Manifest sketch:** `SubsystemManifest(key="settings", commands=("settings", "settings access"), panels=("settings.hub", "settings.subsystem", "settings.audit"), diagnostics=("invalid_settings", "missing_bindings", "recent_changes"), help=HelpEntrySpec(...))`.

**Disposition/recommendation:** keep; no new gap beyond G-10 modal/editor forms. Done when every schema-defined setting has generated UI, validator bounds (G-5), audit trail, and help projection.

---

## logging

### Surface-unit ledger

| Unit | Kind | Evidence | Tier as-written | Tier with amendments | Rationale / gap |
|---|---|---|---:|---:|---|
| `!logging`, status, set, create, routes, test | command | `logging_cog.py:313-428` | 1/3 | 1/3 | All generated except live `test`, which intentionally exercises real posting. |
| eight Discord gateway listeners | listener | `logging_cog.py:170-285` | 3 | 2 | G-1 evidence; declared listener + payload extractor. |
| three bus subscriptions | event subscription | `services/server_logging.py:1854-1856` | 1 | 1 | EventSubscription. |
| LoggingPanel/select/provision/routes views | panel/view | `cogs/logging/panel.py:49`, `select_view.py:90-129`, `provision_view.py:144-181`, `routes_panel.py:188-223` | 1/2 | 1 | Generated binding/provisioning/routing panels. |
| settings/bindings/resources/list settings | setting/binding/resource | `utils/settings_keys/logging.py:10-92`, `cogs/logging/schemas.py` | 1/3 | 1 | G-2 list-valued ignored users/channels. |
| log embed render/post path | announcement | `services/server_logging.py` | 3 | 2 | G-3 AnnouncementRouteSpec. |
| help entry | help | `docs/help-command-surface-map.md:130` | 1 | 1 | Projection. |

**Manifest sketch:** use `tools/grammar_spike/manifests/server_logging.py` shape: commands, panels, `GatewayListenerSpec` for eight gateway events, `EventSubscription` for moderation/audit bus events, settings/bindings/resources, `AnnouncementRouteSpec` for event→template→bound channel, and `HandlerRef("logging.fire_test")`.

**Disposition/recommendation:** keep; no new G-7/G-8 need. Existing G-1/G-2/G-3 close nearly all gaps. Done when live test remains the only tier-3 and all listener routes have declared gates.

---

## diagnostic

### Surface-unit ledger

| Unit | Kind | Evidence | Tier as-written | Tier with amendments | Rationale / gap |
|---|---|---|---:|---:|---|
| diagnostics/lifecycle/list/find/validate/checkdb/status/latency/sysinfo/querylogs/errors/testnotify | command family | `diagnostic_cog.py:54-245` | 3 | 2 | DiagnosticProviderSpec covers command→provider; file/DB/log checks stay handlers. |
| `/platform` and `!platform` 35+ provider commands | command/diagnostic | `platform_group.py:110-559` | 3 | 2 | Broad diagnostic provider catalogue; actions like backfill remain handlers. |
| DiagnosticsHub/PlatformHub/FlagManager/Automation/Paginator panels | panel/view | `views/diagnostic/hub_panel.py:41`, `platform_panel.py:332`, `flag_manager.py:304`, `automation_panel.py:396`, `paginator.py:21` | 2 | 1 | Generated provider panels. |
| health findings/platform consistency stores | store | `utils/db/health_findings.py:1`, `migrations/057_operational_health_findings.sql:1`, `utils/db/platform_consistency.py:1` | 2 | 1 | StoreSpec. |
| diagnostics registry registration | diagnostic provider | `diagnostic_cog.py:252-261` | 2 | 1 | Provider registry is declarable. |
| log buffer recent/query | store/provider | `cogs/diagnostic/_log_buffer.py:1` | 3 | 2 | Diagnostic provider with in-memory source. |

**Manifest sketch:** `SubsystemManifest(key="diagnostic", commands=("diagnostics", "platform status", ...), panels=("diagnostic.hub", "platform.hub", "automation", "flag_manager"), stores=("operational_health_findings", "platform_consistency"), diagnostics=(DiagnosticProviderSpec("latency"), DiagnosticProviderSpec("db_tables"), DiagnosticProviderSpec("settings_registry"), ...))`.

**Disposition/recommendation:** improve; no new family beyond stronger `DiagnosticProviderSpec` cataloguing. Done when every platform command maps to a provider id, input schema, permission gate, result renderer, and destructive flag/backfill audit.

---

## ux_lab

### Surface-unit ledger

| Unit | Kind | Evidence | Tier as-written | Tier with amendments | Rationale / gap |
|---|---|---|---:|---:|---|
| `!uxlab`/`/uxlab` | command | `ux_lab_cog.py:54-68` | 2 | 1 | Command→panel; slash/prefix namespace G-6. |
| help hook + persistent view registration | help/listener | `ux_lab_cog.py:35-42` | 3 | 2 | Persistent view lifecycle should be declared; not a gateway event. |
| home/wing/persistent/probe views and many demo modals | panel/modal | `views/ux_lab/home.py:78`, `wing.py:38`, `buttons.py:228-263`, `compare.py:102-143`, `modals.py:136-279`, `persistent_demo.py:23` | 3 | 2 | G-10 ModalFormSpec + generated demo panel declarations; bespoke visual examples remain handler/render refs. |
| zero-write/governance property | gate | `ux_lab_cog.py:29`, tests invariant referenced in lane scaffold | 1 | 1 | Visibility/gate declaration. |

**Manifest sketch:** `SubsystemManifest(key="ux_lab", commands=("uxlab",), panels=("ux_lab.home", "ux_lab.buttons", "ux_lab.modals", ...), persistent_views=("ux_lab.demo",), modal_forms=("confirm_delete", "verdict", "draft", ...), capabilities=(), help=HelpEntrySpec(...))`.

**Disposition/recommendation:** keep as zero-write UX gallery; add G-10 and persistent-view lifecycle declaration. Done when examples are declared as gallery fixtures and invariant tests prove no DB/settings/audit writes.

---

## utility

### Surface-unit ledger

| Unit | Kind | Evidence | Tier as-written | Tier with amendments | Rationale / gap |
|---|---|---|---:|---:|---|
| utility menu, slash utility, profile, clear, info, server/user/avatar, remind, invite, poll, ping, botinfo, membercount | command family | `utility_cog.py:80-374` | 2/3 | 2 | Simple info routes fit commands/providers; clear/remind/poll are handler workflows; G-4 cooldown. |
| Utility hub, child buttons, back button | panel | `utility_cog.py:416-629` | 2 | 1 | Generated hub/child navigation. |
| Poll/remind modals | modal/timed task | `utility_cog.py:643-686`, `utility_cog.py:72` | 3 | 2 | G-10 modal forms and G-9 timed task/lifecycle cleanup. |
| help projection via registry | help | `docs/help-command-surface-map.md:143` | 1 | 1 | Help projection. |

**Manifest sketch:** `SubsystemManifest(key="utility", commands=("utilitymenu", "ping", "poll", "remind", ...), panels=("utility.panel",), modal_forms=("poll", "reminder"), tasks=(TimedTaskSpec("utility:reminder")), help=HelpEntrySpec(...))`.

**Disposition/recommendation:** merge with simple utility command pack; retain handler refs for destructive clear and actual reminder scheduling. Done when all info commands share ProviderRef renderers and modal/timed-task workflows are declared.

---

## general

### Surface-unit ledger

| Unit | Kind | Evidence | Tier as-written | Tier with amendments | Rationale / gap |
|---|---|---|---:|---:|---|
| general menu, fact, joke, quote, trivia, motivate, eightball, greet | command family | `general_cog.py:81-191` | 2 | 1 | Provider-backed content commands; G-4 cooldown. |
| General panel buttons, trivia reveal, eight-ball modal | panel/modal | `general_cog.py:205-361` | 2/3 | 1/2 | Buttons generated; trivia reveal and modal form benefit from G-10 but content randomness remains provider. |
| help hook and registry metadata | help/gate | `general_cog.py:97-99`, `utils/subsystem_registry.py:1017-1028` | 1 | 1 | Projection. |

**Manifest sketch:** `SubsystemManifest(key="general", commands=("generalmenu", "fact", "joke", ...), panels=("general.panel", "general.trivia_reveal"), modal_forms=("eightball",), providers=("random_fact", "random_joke", ...), help=HelpEntrySpec(...))`.

**Disposition/recommendation:** merge/simple content command pack. Done when static/random content providers are declared and panel buttons are generated.

---

## proof_channel

### Surface-unit ledger

| Unit | Kind | Evidence | Tier as-written | Tier with amendments | Rationale / gap |
|---|---|---|---:|---:|---|
| `+prize`, `-prize`, `prizestatus`, `prizemenu`, `timedprize` | command family | `proof_channel_cog.py:119-184` | 3 | 2 | Binding/resource command surface; grant/revoke/timed actions remain audited handlers. |
| Prize manager buttons and modals | panel/modal | `proof_channel_cog.py:219-382` | 3 | 2 | G-10 modal forms; panel buttons generated. |
| proof channel binding/resource/capabilities | binding/resource/gate | `cogs/proof_channel/schemas.py:43-70`, `utils/subsystem_registry.py:979-982` | 1 | 1 | Existing §2 binding/resource shape. |
| schema registration/unload task cleanup | lifecycle/listener | `proof_channel_cog.py:25-33` | 2 | 1 | Lifecycle hooks declarable. |
| prize audit events | event | `proof_channel_cog.py:413-454` | 2 | 1 | EventSpec/audit action; emit inside handler. |
| timed auto-unlock task | timed task | `proof_channel_cog.py:201-216`, `proof_channel_cog.py:292-305` | 3 | 2 | G-9 one-shot TimedTaskSpec. |
| help hook | help | `proof_channel_cog.py:174-180` | 1 | 1 | Projection. |

**Manifest sketch:** `SubsystemManifest(key="proof_channel", commands=("prizemenu", "timedprize", ...), bindings=(BindingSpec("proof_channel"),), resources=(ResourceRequirement("proof"),), panels=("proof.panel",), modal_forms=("grant_prize", "timed_prize"), tasks=(TimedTaskSpec("proof:unlock"),), events=(EventSpec("proof_channel.prize_access_grant"), EventSpec("proof_channel.prize_access_revoke")))`.

**Disposition/recommendation:** improve; G-9/G-10 close recurring gaps. Done when binding ownership, permission gates, audit events, and timed unlock recovery semantics are declared.

---

## Cross-lane dependencies and danger zones

* **Lane A/B/C dependencies:** BTD6 strategy submissions touch moderation/guild permissions; proof-channel sits under Moderation; utility/general are Utility hub children; logging routes consume moderation/audit events; diagnostics reads platform/economy/media stores. Keep Lane D anchored to declarations and provider/gateway surfaces.
* **AI external-provider calls:** require G-8 provider gateway, secret readiness diagnostics, redaction tests, fallback/degraded response contract.
* **Natural-language routing:** central monolith should split into declarative task/domain routing plus handler refs.
* **Knowledge trust/freshness:** G-7 must require source labels and freshness for BTD6/Project Moon answer blocks.
* **Eval/answerability:** G-7/G-8 should bind eval suites/probes to each AI answerable domain; Project Moon is currently weaker than BTD6.
* **Diagnostics providers:** platform commands need provider ids and schemas, not command-only bespoke functions.
* **Generated help/settings/logging:** current repo proves these are good generation targets; keep overlay/test/live-posting as handler refs.
* **Event/listener wiring:** G-1 and EventSubscription must make gateway/listener wiring visible.
* **Scheduled refresh loops:** BTD6 refreshes are mostly scripts/workflows; proof/utility need one-shot G-9.
* **Governance/visibility gates:** preserve capabilities from subsystem registry and command decorators.
* **Proof-channel/binding ownership:** proof channel should be a binding/resource requirement, not ad hoc channel resolution.

## Verification commands

* `pwd && rg --files -g 'AGENTS.md' -g 'CLAUDE.md' -g 'BRIEF.md' -g 'PARTITION.md'` — verified substrate and absence of in-repo AGENTS instructions.
* `sed -n ...` over required docs and grammar files — completed required reading.
* `PYENV_VERSION=3.10.20 python3.10 scripts/context_map.py disbot/cogs/ai_cog.py` (and BTD6/Project Moon cogs) — failed because `yaml`/PyYAML is unavailable in this environment.
* `rg -n ... disbot/cogs disbot/services disbot/utils tools/grammar_spike docs/help-command-surface-map.md data/btd6` — source verification for every lane subsystem.

# Untapped Runtime / Services / Workflows Map — 2026-06-10

> **Status:** `audit` — mapping-only runtime/services/workflows report.

**Mapped at:** `ed6269767c5614894fb3cdce2985d6487dc981b4`
**Scope:** Runtime, services, helpers, workflows, mutation paths, observability, and ownership seams behind the already-mapped platform surface.
**Source precedence:** source + merged PRs > binding docs > current-state > plans > old notes.

## 1. Executive summary

This audit deliberately starts behind the command/panel inventory. The strongest remaining implementation seams are not missing buttons; they are domain mutations whose canonical owner is incomplete, split, or bypassed.

Top findings, severity-first:

1. **FIND-RS01:** economy shop purchase is a two-owner, two-commit workflow: audited debit first, direct inventory insert second. A failed insert charges the user without granting the item.
2. **FIND-RS02:** mining has no domain mutation service; cogs and views directly coordinate inventory, depth, equipment, wear, and coin legs. Multi-step repair/break/purchase actions have partial-commit risk.
3. **FIND-RS03:** cog-routing persistence is not a full mutation pipeline. The setup dispatcher owns the audit emission, records no previous value, and cannot make write + audit atomic.
4. **FIND-RS04:** binding mutation advertises cache invalidation, but its invalidation hook remains a logging-only no-op with stale Phase-2b/Phase-4c language.
5. **FIND-RS05:** EventBus subscriber failure/timeout is swallowed inside `EventBus.emit`; pipeline `event_emitted`/`audit_emitted` booleans therefore mean “bus call returned,” not “subscribers handled the event.”
6. **FIND-RS06:** role-threshold setters are service-owned and audited, but field-specific clears remain direct DB writes in the cog/views, leaving asymmetric audit/cache behavior.
7. **FIND-RS07:** the chain game has all configuration and counter mutation logic in its cog, with no domain service, audit event, or reusable workflow seam.
8. **FIND-RS08:** diagnostic embed builders contain raw SQL/read-model composition, making operator diagnostics harder to reuse and test outside Discord rendering.
9. **FIND-RS09:** resource provisioning has two similarly named pipeline classes; the older `core.resources.mutation.ResourceMutationPipeline` is an unimplemented shell whose docs still claim future Phase 7.5 work even though `services.resource_provisioning.ResourceProvisioningPipeline` is live.
10. **FIND-RS10:** shared view lifecycle/ownership handling is only partially centralized; 38 local `interaction_check` and 17 local `on_timeout` implementations recreate the same policy and failure behavior.

**Safe to implement soon:** RS04, RS08, RS09, RS10, RS13, RS14, and RS16 are bounded cleanup/hardening candidates. RS03 and RS06 are bounded service-boundary fixes but require migration-aware tests. RS01/RS02 should be treated as domain workflow work, not local view cleanup.

**Blocked/gated:** the access-projection availability axis remains intentionally inert pending Adaptive P1C (RS12). Additional AI workflow families and settings UI remain gated by the active AI orchestration/answerability plans; this map records only naming/ownership observations (RS15). There were **no open PRs** at audit time, so no finding is provisional on an open PR.

**Next merge/implementation session:** first land the low-risk truth/clarity batch (RS04/RS09/RS13/RS14/RS16), then make cog routing a canonical mutation owner (RS03), then choose one domain transaction boundary—economy purchase (RS01) is the smallest high-value vertical slice before the larger mining convergence (RS02).

## 2. Live repo state checked

- **Current HEAD:** `ed6269767c5614894fb3cdce2985d6487dc981b4`.
- **Open PRs checked:** GitHub API returned none on 2026-06-10.
- **Recent merged PRs checked:** #645 owner-answer capture, #644/#643 platform mappings, #638 BTD6 decode-tail continuation, #642 Help reconciliation/tests, #640 Settings reachability, #641 mapping standard, #639 AI self-awareness tools, #632 Adaptive P1B, #633 BTD6 refresh workflow, and #634 orchestration Phase 4 MVP.
- **Docs/plans read:** the required binding workflow/orientation/current-state/roadmap/architecture/ownership/runtime/helper docs; the three platform reports; settings/help audits; server-management status; setup finalization; adaptive access plan; AI orchestration and answerability plans; BTD6 README/decode-status/coverage routing; and relevant subsystem folios (`ai`, `btd6`, `games`, `health-diagnostics`, `server-management`, `settings-bindings-provisioning`).
- **Limitations:** `gh` and CodeGraph CLI are unavailable. Live PR state was checked through the GitHub API. `scripts/context_map.py` was used as the repository-supported ownership/import graph fallback, followed by manual source verification. This is a source mapping, not a full tests/docs gap audit; tests are cited only as protection evidence.

## 3. Already-covered surface reports consumed

The mapping standard and Agent A/B reports already inventory user/admin commands, panels, aliases, discovery, access/help visibility, and their surface-level findings. This report consumes their conclusions—especially Help/access projection gaps and settings/customization registry coverage—but does **not** repeat command-by-command or panel-by-panel rows. It maps the implementation seams below those surfaces: mutation ownership, transaction boundaries, workflow orchestration, event/cache behavior, helper duplication, diagnostics read models, and naming drift.

## 4. Runtime/service ownership map

| area | canonical owner | files inspected | main consumers | mutation/read model | tests | verdict | finding refs |
|---|---|---|---|---|---|---|---|
| command access / admission | `services.command_access_service` + `core.runtime.command_access` + bootstrap check | `command_access_service.py`, `command_access.py`, `bootstrap_access_cog.py` | prefix admission, Settings, access projection | cached policy read; service writes + audit | command-access service/cog + load-order invariants | coherent; separate from presentation | RS12 |
| governance resolver and mutation | `governance.resolver`, `governance.writes.GovernanceMutationPipeline` | resolver/cache/writes/events/runtime subscribers | admission, setup, access projection | transactional governance write + cache invalidation + events | governance suite | coherent, but inherits event-result semantics | RS05 |
| settings registry/resolution/mutation | `settings_registry`, `settings_resolution`, `SettingsMutationPipeline` | registry/resolution/mutation/accessors | Settings, setup, AI projections, diagnostics | typed declaration/read; transactional scalar write + key invalidation + audit/event | registry/mutation/invariants | canonical scalar path; reset semantics still expressed as set-only | RS05, RS11 |
| binding/provisioning pipeline | `BindingMutationPipeline`; live `ResourceProvisioningPipeline` | binding mutation, provisioning, catalogue, old resource shell | setup operations, logging selector, repair/automation | binding DB+audit; provisioning composes Discord create + binding + audit | binding/provisioning tests | live path works; cache hook and stale parallel API remain | RS04, RS09 |
| customization catalogue | `services.customization_catalogue` | catalogue, ledger, settings registry | diagnostics/platform mappings | cached composed snapshot | catalogue tests | maintainable read model, but marker API is currently aspirational/best-effort | RS14 |
| Help/access projection read models | `services.access_projection`; Help route remains consumer-specific | access projection, Help route, ledger | P1C future panel, diagnostics | read-only composition | access projection/help tests | availability axis intentionally skipped; Help integration remains gated | RS12 |
| AI orchestration/tool services | `core.runtime.ai.gateway` behind `services.ai_gateway`; orchestration services | gateway/shim, tools, task router, round-cash workflow | AI cog, BTD6 AI, setup advisor | provider-neutral gateway + typed workflows | AI runtime/service/evals | correct boundary, but naming and layer placement invite confusion; expansion gated | RS15 |
| BTD6 services | BTD6 service family, especially knowledge/data/view-model owners | folio, boundaries, representative data/knowledge/view-model services | BTD6 cogs, AI tools | read-heavy service family + source mutation pipelines | BTD6 boundaries/service tests | no new bypass proved; large family requires owner-map discipline; decode tail recently merged | RS15 |
| economy / inventory / XP / mining | economy and XP services; inventory/mining still direct DB by binding ownership doc | economy/xp services, economy/mining cogs/views, DB primitives | game/economy panels/listeners | audited coin/XP writes; direct inventory/mining writes | economy/XP invariants; mining unit/view tests | split domain/workflow ownership | RS01, RS02, RS11 |
| server management services/workflows | lifecycle services, role automation, setup operations | channel/role lifecycle, role automation, setup operations, relevant cogs/views | server-management hub, setup, role/channel surfaces | lifecycle result contracts + audit/events | lifecycle/setup/invariant suites | generally strong; role-threshold clear asymmetry remains | RS06 |
| diagnostics/health services | health snapshot/findings + diagnostics registry | diagnostics/health services and diagnostic embed helpers | platform/health panels, startup recorder | read-only snapshots + sole-writer persistent findings | health/diagnostic tests | strong health owner; some diagnostic SQL/render coupling remains | RS08, RS13 |
| database helpers and migrations | `utils.db.*`; migration runner | migration runner, economy/inventory/mining/roles primitives | services and legacy/direct domains | forward-only SQL primitives | DB/migration/invariant tests | clear low-level layer; some “get” calls mutate and ownership exceptions are broad | RS11, RS16 |
| shared view/navigation/safe interaction helpers | `views.base.BaseView`, navigation helpers, `core.runtime.interaction_helpers` | base, interaction helpers, representative economy/mining/game/AI views | every interactive surface | response/lifecycle safety | scattered view/helper tests | partial adoption; repeated local lifecycle policy | RS10 |
| setup workflow/state machine | `services.setup_operations`, `setup_session`, `setup_draft`; views render/recovery | services + final-review/recovery/sections | setup wizard/platform | draft → preflight → ordered apply → recovery | setup operations/views tests | substantial canonical workflow; domain audit ownership leaks into dispatcher | RS03, RS17 |

## 5. Findings

### FIND-RS01 [critical blocker] Economy purchase can debit coins without granting inventory

- **evidence:** `disbot/views/economy/shop_panel.py:81-100` and `:200-218`, `_ShopSelect.callback` / `_ShopPanelSelect.callback`: balance is read, `economy_service.debit(...)` commits, then `db.add_item(...)` writes separately.
- **verified-by:** source read; `rg -n 'economy_service.debit|db.add_item' disbot/views/economy/shop_panel.py`; context map + manual verification.
- **impact:** DB/Discord failure between the two calls leaves a charged user without the purchased item; duplicate implementations can drift independently; business logic lives in a view.
- **recommended disposition:** implementation-candidate.
- **likely files for implementation:** `disbot/services/economy_service.py`, new bounded inventory/purchase service module, `disbot/views/economy/shop_panel.py`, `disbot/utils/db/inventory.py`, focused tests.
- **test/doc expectation:** transactional purchase success/failure/concurrency tests; invariant preventing view-level purchase writes; ownership doc update.

### FIND-RS02 [critical blocker] Mining mutations are orchestrated directly by cogs/views instead of a domain service

- **evidence:** `disbot/cogs/mining/workshop.py:186-205` coordinates break/wear/inventory/unequip/last-broken writes; `disbot/cogs/mining/market.py:121-131` debits inventory then credits coins; `disbot/views/mining/main_panel.py:177-225` and `:391-442` mutate inventory/depth from callbacks.
- **verified-by:** source read; direct-mutation grep across `disbot/cogs/mining*` and `disbot/views/mining`; existing mining tests sampled.
- **impact:** partial commits can duplicate/loss items or leave equipment/wear/coin state inconsistent; typed commands and panels can implement different rules; future structures/game-XP work has no stable orchestration seam.
- **recommended disposition:** needs-owner-decision (choose the first workflow boundary), then implementation-candidate.
- **likely files for implementation:** `disbot/cogs/mining/*.py`, `disbot/cogs/mining_cog.py`, `disbot/views/mining/*.py`, `disbot/utils/db/games/mining*.py`, new `disbot/services/mining_*` modules.
- **test/doc expectation:** workflow-level transaction/idempotency tests, direct-write shrinking invariant, games folio/ownership update, rollback behavior per workflow.

### FIND-RS03 [important improvement] Cog-routing audit ownership lives in setup dispatcher, not the routing mutation owner

- **evidence:** `disbot/services/command_routing.py:55-76` writes directly and returns `None`; `disbot/services/setup_operations.py:1436-1513` creates the mutation ID and emits the audit later with `prev_value=None`.
- **verified-by:** source read; `rg -n 'command_routing.set_policy|set_cog_routing' disbot`; context map.
- **impact:** non-setup callers can write silently; audit cannot be atomic with the write; previous state is lost; the setup workflow knows mutation-owner details.
- **recommended disposition:** implementation-candidate.
- **likely files for implementation:** `disbot/services/command_routing.py`, `disbot/services/setup_operations.py`, `disbot/utils/db/command_routing.py`, tests.
- **test/doc expectation:** canonical mutation result, old/new audit values, failure semantics, direct-writer invariant, ownership/runtime-contract update.

### FIND-RS04 [important improvement] BindingMutationPipeline cache invalidation is still a no-op despite the live pipeline

- **evidence:** `disbot/services/binding_mutation.py:415-435`, `_invalidate_cache`, states it is a no-op “until Phase 4c”; writes call it after commit at `:401` and `:251`.
- **verified-by:** source read; context map + manual verification; binding mutation tests.
- **impact:** the contract and method name imply coherence that does not exist; future cached binding consumers can become stale without noticing; stale phase language misleads implementers.
- **recommended disposition:** fix-now (either implement a real invalidation target or explicitly remove/rename the hook until one exists).
- **likely files for implementation:** `disbot/services/binding_mutation.py`, `disbot/core/runtime/bindings.py`, relevant accessor/cache module, binding tests.
- **test/doc expectation:** cache-observation test across set/clear; binding folio/ownership truth update.

### FIND-RS05 [important improvement] Pipeline event-result booleans overstate subscriber delivery

- **evidence:** `disbot/core/events.py:92-112`, `EventBus.emit`, catches handler timeout/failure and returns normally; `disbot/services/audit_events.py:65-99` and `disbot/services/binding_mutation.py:437-481` return `True` whenever `bus.emit` returns.
- **verified-by:** source read; `rg -n 'event_emitted|audit_emitted' disbot tests/unit`.
- **impact:** mutation results and tests cannot distinguish “accepted by bus” from “audit/log/cache subscriber failed”; operators may trust misleading success fields.
- **recommended disposition:** rename-cleanup or observability/test hardening; do not change failure propagation casually.
- **likely files for implementation:** `disbot/core/events.py`, `disbot/services/audit_events.py`, mutation-result contracts and tests.
- **test/doc expectation:** define delivery semantics; add handler-failure metric/result coverage; update runtime contracts.

### FIND-RS06 [important improvement] Role-threshold clears bypass the audited role-automation mutation seam

- **evidence:** `disbot/views/roles/xp_roles_panel.py:229`, `disbot/views/roles/time_roles_panel.py:256`, and `disbot/cogs/role_cog.py:482` call DB clear primitives directly; `tests/unit/invariants/test_no_direct_role_threshold_writes.py:36-47` fences only setter names; `docs/ownership.md` says writes use the audited seam while separately permitting field-specific clears.
- **verified-by:** source read; direct mutation grep; invariant source read.
- **impact:** setting and clearing the same configuration have asymmetric audit/cache/event behavior; the binding ownership statement is ambiguous.
- **recommended disposition:** implementation-candidate plus docs-only clarification.
- **likely files for implementation:** `disbot/services/role_automation.py`, three callers above, invariant test, ownership doc in a later implementation PR.
- **test/doc expectation:** service clear methods, audit/cache assertions, invariant expanded to clear primitives.

### FIND-RS07 [important improvement] Chain game owns persistence, configuration, and runtime transitions inside its cog

- **evidence:** `disbot/cogs/chain_cog.py:102-107`, `:136-143`, and `:309-324` directly read/write chain configuration and increment state.
- **verified-by:** source read; `rg -n 'db\.(set_chain|delete_chain|increment_chain)' disbot/cogs/chain_cog.py`.
- **impact:** no reusable service for future panels/automation, configuration changes have no canonical audit/event path, and command/listener logic is tightly coupled to persistence.
- **recommended disposition:** service-boundary implementation-candidate.
- **likely files for implementation:** `disbot/cogs/chain_cog.py`, `disbot/utils/db/games/chain.py`, new `disbot/services/chain_service.py`, tests.
- **test/doc expectation:** service transition tests, configuration audit decision, direct-write invariant, games folio update.

### FIND-RS08 [important improvement] Diagnostic rendering modules contain raw SQL read-model ownership

- **evidence:** `disbot/cogs/diagnostic/_platform_embeds.py:1288-1328` queries session counts and `:1336-1381` queries anchors; `disbot/cogs/diagnostic/_helpers.py:200-241` queries schema/migrations.
- **verified-by:** source read; direct DB grep in diagnostic cog helpers.
- **impact:** Discord rendering owns query semantics/error handling; health/diagnostic consumers cannot reuse typed results; tests must mock rendering modules instead of a service read model.
- **recommended disposition:** implementation-candidate.
- **likely files for implementation:** diagnostic helper/embed files, `disbot/services/diagnostics_service.py` or bounded async diagnostic read services, tests.
- **test/doc expectation:** typed/read-only service tests and renderer-only tests; keep diagnostics read-only invariant.

### FIND-RS09 [important improvement] Two resource-mutation pipeline APIs exist, and one is an obsolete unimplemented shell

- **evidence:** `disbot/core/resources/mutation.py:1-29` and `:50-56` describe `ResourceMutationPipeline` with unimplemented methods/Phase 7.5 future work; `disbot/services/resource_provisioning.py:1-20` declares the live canonical `ResourceProvisioningPipeline`.
- **verified-by:** source read; `rg -n 'ResourceMutationPipeline|ResourceProvisioningPipeline' disbot tests docs`.
- **impact:** names imply competing owners; new callers can import the wrong pipeline; stale roadmap language obscures the live contract.
- **recommended disposition:** rename-cleanup / merge-duplicate (prefer retire/deprecate shell after consumer search).
- **likely files for implementation:** `disbot/core/resources/mutation.py`, imports/tests/docs that reference it.
- **test/doc expectation:** import/consumer proof before removal; architecture/ownership references updated.

### FIND-RS10 [cleanup] View ownership and timeout policy is repeated despite BaseView and safe interaction helpers

- **evidence:** `disbot/views/base.py:119-145` provides canonical ownership check/timeout disable; repository grep finds 38 `interaction_check` and 17 `on_timeout` definitions, including duplicate economy variants in `disbot/views/economy/shop_panel.py:39-58` and `:160-176`.
- **verified-by:** `rg -n 'async def interaction_check|async def on_timeout' disbot/views`; source read.
- **impact:** denial copy, ephemeral behavior, message editing, and exception handling drift; new views reproduce lifecycle bugs.
- **recommended disposition:** merge-duplicate in bounded families, not a big-bang base-class rewrite.
- **likely files for implementation:** `disbot/views/base.py`, one view family per PR, focused view tests.
- **test/doc expectation:** characterization tests before migration; helper-policy check; preserve genuinely multiplayer/shared views.

### FIND-RS11 [important improvement] Economy/inventory read and workflow ownership remains split and misleadingly named

- **evidence:** `disbot/utils/db/economy.py:50-59`, `get_economy`, performs an insert before reading; `docs/ownership.md:34` makes economy service sole coin writer while inventory is direct-owned, enabling cross-domain workflows such as RS01 without a canonical coordinator.
- **verified-by:** source read; DB getter/write grep; ownership read.
- **impact:** callers cannot assume a `get_*` is read-only; diagnostics/previews may mutate; cross-domain transaction ownership is unspecified.
- **recommended disposition:** needs-owner-decision for cross-domain workflow owner; rename-cleanup for mutating getter.
- **likely files for implementation:** `disbot/utils/db/economy.py`, economy/inventory services/callers, ownership docs.
- **test/doc expectation:** read-only vs ensure-row contract tests; explicit transaction/coordinator policy.

### FIND-RS12 [future opportunity] Access projection has a deliberately skipped availability axis

- **evidence:** `disbot/services/access_projection.py:427-437` always returns `skipped` with “availability policy not implemented”; projection includes it at `:513-525`.
- **verified-by:** source read; Adaptive setup/access plan and current-state gate read.
- **impact:** the projection is honest but cannot yet explain all availability restrictions; consumers must not treat its allow result as complete execution authority.
- **recommended disposition:** blocked-by-gate(Adaptive P1C).
- **likely files for implementation:** `disbot/services/access_projection.py`, future availability owner, P1C panel/tests.
- **test/doc expectation:** gate-specific composition tests; preserve rule that Help visibility never gates execution.

### FIND-RS13 [cleanup] Diagnostics registry naming suggests a full diagnostics service but only supports synchronous process-local providers

- **evidence:** `disbot/services/diagnostics_service.py:1-29` calls itself centralized diagnostics; `:39-42` explicitly excludes DB/async providers and redirects them elsewhere.
- **verified-by:** source read; provider-registration grep.
- **impact:** async diagnostic read models land ad hoc in cogs (RS08); the name obscures the boundary between process snapshot registry, health snapshot service, and operator query services.
- **recommended disposition:** docs-only / rename-cleanup (clarify as `runtime_diagnostics_registry`; rename only with broad consumer migration).
- **likely files for implementation:** diagnostics service, references/docs/tests.
- **test/doc expectation:** boundary statement and provider inventory; no behavior change required initially.

### FIND-RS14 [cleanup] Customization panel declaration API is aspirational and silently best-effort

- **evidence:** `disbot/services/customization_catalogue.py:100-131`, `panel_command`, says no commands carry it and silently passes if decoration cannot attach metadata; `:300-311` then composes fallback sources.
- **verified-by:** source read; customization catalogue tests; platform reports consumed.
- **impact:** a canonical-looking declaration API can fail silently or remain unused while regex/known-list fallbacks continue; catalogue completeness is hard to reason about.
- **recommended disposition:** fix-now docs/truth cleanup, then bounded adoption or removal.
- **likely files for implementation:** `disbot/services/customization_catalogue.py`, selected panel commands, tests.
- **test/doc expectation:** declaration invariant or explicit deprecation; catalogue diagnostics should expose fallback-source counts.

### FIND-RS15 [cleanup] AI gateway ownership is correct but names and layer references remain easy to misread

- **evidence:** `disbot/services/ai_gateway.py:1-7` is a shim and `:25` re-exports the core gateway; `disbot/core/runtime/ai/gateway.py:20-23` says consumers must use the service shim, while the core gateway itself imports `services.metrics` and `utils.db.ai` at `:51-52`.
- **verified-by:** source/import grep; AI folio/plans; AI boundary invariant.
- **impact:** “service gateway” vs “runtime gateway” is not obvious from names alone; the runtime core is not dependency-pure, increasing refactor risk. Current behavior is protected and should not be churned during gated expansion.
- **recommended disposition:** blocked-by-gate(AI orchestration/answerability expansion) for structural work; docs-only naming note now.
- **likely files for implementation:** AI gateway/shim and boundary tests only when gate lifts.
- **test/doc expectation:** preserve provider chokepoint and boundary invariant; no parallel gateway.

### FIND-RS16 [cleanup] Migration bootstrap and migration-chain ownership are combined in one broad module

- **evidence:** `disbot/utils/db/migrations.py:1-13` owns migrations, while `:168-290` also contains the full pre-migration base-table bootstrap DDL; migration count is now 63 files.
- **verified-by:** source read; `find disbot/migrations -type f | wc -l`; schema diagnostic source read.
- **impact:** a change to legacy bootstrap schema and a forward migration can drift; the module is harder to review and test as the migration chain grows.
- **recommended disposition:** docs-only now; implementation-candidate only with a compatibility plan.
- **likely files for implementation:** `disbot/utils/db/migrations.py`, migration structure/schema tests.
- **test/doc expectation:** pin bootstrap-vs-migration responsibilities; do not edit historical migrations.

### FIND-RS17 [important improvement] Setup dispatcher has become a cross-domain mutation policy owner

- **evidence:** `disbot/services/setup_operations.py:978-1064` dispatches many domain operations; the cog-routing arm additionally owns audit details at `:1436-1513` rather than merely calling a domain owner.
- **verified-by:** source read; setup plan/status read; dispatch symbol enumeration.
- **impact:** adding a setup operation can accidentally create a second mutation contract; setup-specific metadata parsing leaks into domain semantics.
- **recommended disposition:** implementation-candidate as domains are touched; keep dispatcher thin rather than rewrite it wholesale.
- **likely files for implementation:** `disbot/services/setup_operations.py` plus each affected canonical domain owner.
- **test/doc expectation:** dispatcher contract tests should assert calls/results, while mutation/audit behavior moves to domain tests.

### FIND-RS18 [future opportunity] EventBus is explicitly process-local and blocks safe multi-process runtime expansion

- **evidence:** `disbot/core/events.py:74-79` states handlers/registrations must move to a shared backend before sharding.
- **verified-by:** source read; runtime contracts read.
- **impact:** cache invalidation, live updates, audit routing, and domain events are lost across replicas; runtime lock currently masks this by enforcing one active bot.
- **recommended disposition:** docs-only / future opportunity; do not build until multi-process runtime is approved.
- **likely files for implementation:** event bus/runtime lock/consumers, deployment docs.
- **test/doc expectation:** distributed delivery/idempotency design before implementation.

## 6. Naming and API clarity issues

| current name | where used | why unclear | suggested clearer name | migration risk | timing |
|---|---|---|---|---|---|
| `ResourceMutationPipeline` | `core/resources/mutation.py`, tests/docs | sounds canonical but is an unimplemented old shell beside live `ResourceProvisioningPipeline` | retire, or `LegacyResourceMutationContract` while deprecating | medium: search docs/tests/imports | safe after consumer proof (RS09) |
| `diagnostics_service` | process-local provider registry | name implies all diagnostics, but async/DB diagnostics are excluded | `runtime_diagnostics_registry` | high import churn | clarify now, rename later (RS13) |
| `event_emitted` / `audit_emitted` | mutation result types | means bus invocation returned, not that subscribers succeeded | `event_publish_accepted` / `audit_publish_accepted`, or document exact semantics | high cross-service/test churn | wait for contract decision (RS05) |
| `get_economy` | DB primitive | performs an insert as part of “get” | `ensure_and_get_economy` or split `ensure_economy_row` + `get_economy` | medium caller behavior risk | safe bounded cleanup (RS11) |
| `set_policy` in `command_routing` | setup dispatcher | generic name hides unaudited canonical mutation responsibility | `set_routing_policy` returning mutation result | medium | with RS03 |
| `panel_command` | customization catalogue | appears canonical but is currently unused/best-effort | keep only if adopted and validated; otherwise `mark_panel_command_best_effort`/remove | low-medium | RS14 truth cleanup |
| `services.runtime` | bot entrypoint/runtime lock callers | broad name actually owns only instance lock/heartbeat/boot ID | `runtime_lock_service` or `runtime_instance_service` | high boot/import risk | defer; docs-only note |
| `services.ai_gateway` vs `core.runtime.ai.gateway` | AI consumers/runtime | both are “gateway”; one is a shim | document as public `ai_gateway` facade vs internal `provider_gateway` | high/gated | wait (RS15) |

## 7. Duplicate / parallel logic candidates

| duplicate locations | recommended owner | migration order | tests needed | risk level |
|---|---|---|---|---|
| two economy shop callbacks each implement ownership/balance/debit/add-item/logging | purchase workflow service + one render helper | service contract → migrate one callback → migrate second → invariant | transaction, concurrency, both panels | high |
| mining typed commands and panel callbacks directly implement inventory/depth/equipment transitions | mining workflow services by action (`market`, `workshop`, `exploration`) | characterize → extract one workflow → ratchet direct writes | workflow atomicity + panel/command parity | high |
| role threshold setters through service, clears through DB primitives | `services.role_automation` | add clear service methods → migrate views/cog → widen invariant | audit/cache and field-preservation | medium |
| BaseView ownership/timeout plus repeated local implementations | `views.base` or narrow family bases | group by genuinely owner-bound vs multiplayer → migrate one family at a time | denial copy, timeout edit failure, owner enforcement | medium |
| resource mutation shell vs live provisioning pipeline | `services.resource_provisioning` | prove no runtime consumers → deprecate/remove shell → docs cleanup | import/invariant tests | low-medium |
| diagnostics raw SQL in embed/helpers vs reusable health/read services | bounded async diagnostic read services | extract query contracts → keep embeds render-only | DB error/read-only/render tests | low |
| setup dispatcher audit logic vs domain mutation owner | each domain service | move one operation kind at a time; dispatcher consumes result | mutation + dispatcher characterization | medium |

## 8. Observability / audit / cache-event gaps

### User-visible failures

- **RS01:** a shop insert failure after debit produces a user-visible lost purchase without compensating refund.
- **RS02:** mining multi-step actions can render success/partial state after one leg fails.
- **RS10:** repeated timeout handlers commonly swallow edit exceptions, so stale interactive controls may remain without consistent logging.

### Operator/debugging visibility gaps

- **RS03:** cog-routing audit records `prev_value=None` and depends on setup dispatcher; direct future callers may be invisible.
- **RS05:** publish-result booleans cannot expose handler timeout/failure; EventBus logs errors but does not aggregate per-event delivery outcomes.
- **RS07:** chain configuration/counter writes have no domain audit/event path.
- **RS08/RS13:** async DB diagnostics live outside the diagnostics registry, so provider inventory is not a complete operator-read-model inventory.
- **RS14:** catalogue fallbacks are recorded per panel source but diagnostics do not make fallback dependence prominent enough to guide declaration cleanup.

### Hidden correctness risks

- **RS04:** binding cache invalidation is a no-op; correctness currently depends on uncached reads and must be revisited before adding caches.
- **RS05/RS18:** best-effort process-local events can lose cache invalidation/live updates/audit rendering even while authoritative DB state commits.
- **RS06:** clear operations do not follow the same audit/cache path as set operations.
- **RS11:** `get_economy` writes, so nominal reads can change DB state and complicate read-only guarantees.

## 9. Open owner questions

### Q-RS01

**question:** What is the canonical ownership model for workflows that atomically span coins plus a domain inventory (shop purchases, mining market/repair)?
**options:** A. Domain workflow service owns one DB transaction and calls low-level transaction-aware primitives; B. economy service owns all coin+inventory transactions; C. keep separate commits and add compensation/refund only.
**recommended default:** A.
**what implementation is blocked until answered:** RS01 and the transaction design for RS02.

### Q-RS02

**question:** Which mining workflow should become the first canonical service boundary?
**options:** A. market buy/sell; B. workshop durability/repair/break; C. movement/exploration/depth.
**recommended default:** B, because it has the densest multi-write invariant and highest partial-commit risk.
**what implementation is blocked until answered:** sequencing of RS02; no broad mining rewrite is needed to answer.

### Q-RS03

**question:** Should mutation result delivery flags represent publish acceptance or successful subscriber delivery?
**options:** A. rename/document as publish acceptance; B. make EventBus return structured handler outcomes; C. remove booleans and rely on metrics/logs.
**recommended default:** B internally, with compatibility aliases during migration.
**what implementation is blocked until answered:** final API shape for RS05; adding metrics is not blocked.

## 10. Implementation-session candidates

### Small cleanup PRs

- **Included:** RS04, RS09, RS13, RS14, RS16.
- **Why together:** truth/ownership/naming cleanup with little product behavior; can be split if removal of old resource shell proves broad.
- **Touched areas:** bindings cache contract, resource API shell, diagnostics/customization naming/docs, migration responsibility comments/tests.
- **Verification commands:** targeted binding/resource/catalogue/diagnostics/migration tests; full quality/architecture checks.
- **Rollback risk:** low, except deleting/renaming imported APIs; prove consumers first.

### Service-boundary fixes

- **Included:** RS03, RS06, RS07, RS17.
- **Why together:** move mutation/audit responsibility from cogs/views/setup dispatcher into canonical domain owners.
- **Touched areas:** command routing, role automation clears, chain service, setup dispatcher.
- **Verification commands:** targeted service/cog/setup tests plus direct-write invariants.
- **Rollback risk:** medium; preserve persisted schemas and user-facing behavior.

### Mutation-path hardening

- **Included:** RS01 first; RS02 as separate staged program; RS11 decision feeds both.
- **Why together:** transaction/coordinator ownership is the shared architectural issue, but mining should not be bundled into the economy purchase PR.
- **Touched areas:** economy/inventory/mining services, DB transaction primitives, views/cogs.
- **Verification commands:** concurrency/rollback tests, existing economy/mining suites, new direct-write invariants, full checks.
- **Rollback risk:** high; transaction and compensation semantics affect balances/items.

### Observability/test hardening

- **Included:** RS05, RS08, RS10.
- **Why together:** make runtime behavior measurable/reusable before changing broad event or view contracts.
- **Touched areas:** EventBus/result contracts, diagnostics read models, view lifecycle helpers.
- **Verification commands:** event timeout/failure tests, health/diagnostic read-only tests, family-specific view tests.
- **Rollback risk:** medium for event API, low for extracted read models.

### Gated/deferred work

- **Included:** RS12, RS15, RS18.
- **Why together:** each touches an explicitly gated or future platform boundary.
- **Touched areas:** Adaptive P1C access projection, AI runtime/service layering, distributed event infrastructure.
- **Verification commands:** gate-specific plans plus full quality/architecture checks when activated.
- **Rollback risk:** high if activated prematurely; no runtime work recommended now.

## 11. Verification log

Commands run during mapping (final results are also recorded in the session log):

- `git status --short --branch` — clean at start on branch `work`.
- `git rev-parse HEAD` — `ed6269767c5614894fb3cdce2985d6487dc981b4`.
- `gh pr list ...` — unavailable because `gh` is not installed.
- GitHub API Python query against `repos/menno420/superbot/pulls` — no open PRs; recent merged PRs listed in §2.
- `find ...` / `rg ...` source, test, migration, and docs enumerations — completed; no `disbot/workflows/` directory exists.
- `rg -n '\b(db\.|...` and targeted direct-mutation greps across cogs/views/services — completed; findings manually read-verified.
- `python scripts/context_map.py disbot/services/command_routing.py` — completed via AST fallback.
- `python scripts/context_map.py disbot/services/binding_mutation.py` — completed via AST fallback.
- `python scripts/context_map.py disbot/views/economy/shop_panel.py` — completed via AST fallback.
- CodeGraph `context` / `fn_impact` — unavailable; no CodeGraph CLI present.
- `python3.10 scripts/check_docs.py --strict` — the bare command could not select the inactive pyenv shim. Re-run as `PYENV_VERSION=3.10.20 python3.10 scripts/check_docs.py --strict`; it reported only the expected orphan for this new allowed mapping output (linking it requires a shared-doc edit outside this lane).
- `python3.10 scripts/check_quality.py --full` — re-run as `PYENV_VERSION=3.10.20 python3.10 scripts/check_quality.py --full`; black, isort, ruff, and mypy passed; strict docs failed on the expected orphan; pytest collection failed because the isolated Python 3.10 environment lacks runtime dependencies including `discord` and `asyncpg`.
- `python3.10 scripts/check_architecture.py --mode strict` — re-run under selected Python 3.10, but could not import `yaml`; substitute `python scripts/check_architecture.py --mode strict` under Python 3.12.13 passed with 0 errors and 86 tracked warnings.
- `git diff --check` — passed.

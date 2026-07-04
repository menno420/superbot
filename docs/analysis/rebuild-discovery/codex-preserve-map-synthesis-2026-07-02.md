# Codex rebuild-discovery maps — verified & folded preserve/redesign/drop synthesis (2026-07-02)

> **Status:** `reference` — the single consolidated "one picture" that folds the **4 Codex
> rebuild-discovery maps** into one verified preserve / redesign / drop artifact + a unified primitive
> taxonomy + the backward-compat contract. **This is the primary Codex-evidence input to the Fable-5
> design session.** Every load-bearing claim was re-verified against **live source** by a 4-agent fleet
> (Q-0120, 2026-07-02): **48 of 59 CONFIRMED, 2 FALSE, 9 PARTIAL** — the §1 corrections are **binding
> over the raw maps**. Source code + merged PRs win over this file.
>
> **Provenance:** authored by the owner's 4 Codex sessions (originally PRs #1630–#1633, **superseded by
> this consolidation** — their reports are preserved verbatim for drill-down):
> [platform-ui-runtime](platform-ui-runtime-map.md) · [admin-safety-server](admin-safety-server-map.md) ·
> [community-economy-games](community-economy-games-map.md) ·
> [ai-knowledge-data-tooling](ai-knowledge-data-tooling-map.md).
> Feeds the rebuild launch pad
> ([`rebuild-ultracode-handoff`](../../planning/rebuild-ultracode-handoff-2026-07-02.md)) and the strategy
> baseline ([`fresh-rebuild-strategy`](../../planning/fresh-rebuild-strategy-2026-07-02.md) §6).

---

All six spot-checks confirm the maps against live source: `ActionSpec` collides at `services/automation_registry.py:35`; `SettingSpec`/`BindingSpec`/`DomainPanelSpec`/`SubsystemSchema` sit in `subsystem_schema.py`; `multi_channel.py` is genuinely absent; the AI DB module is `utils/db/ai_review.py` (no `ai_review_log.py`); `gateway.py:51` really does `from services import metrics`; and the server hub command is `servermanagement`/`servermenu`/`guildmenu`. The corrections hold. Here is the synthesis body.

> **⚠️ Corrections to THIS file, source-verified by the 2026-07-02 design-spec review fleet**
> (carried in [`rebuild-design-spec-2026-07-02.md`](../../planning/rebuild-design-spec-2026-07-02.md)'s
> header): (1) `BindingMutationPipeline` lives at `services/binding_mutation.py:154` and
> `ResourceProvisioningPipeline` at `services/resource_provisioning.py:240` — **not** in
> `settings_mutation.py` as §4 states; (2) the `EventBus` lives at `core/events.py:52` and
> `utils/events.py` does not exist (the catalogue is `core/events_catalogue.py`); (3) §1's
> PARTIAL-3 verdict is itself wrong — `governance.visibility.changed` / `governance.cache.invalidated`
> (note the real literal, not `.changed`) / `governance.cleanup.changed` **are live-subscribed** at
> `core/runtime/__init__.py:181–183`; the genuinely subscriber-less catalogued pair is
> `governance.execution.allowed/denied` (`governance/execution.py`, no `bus.on` anywhere).

## 1. Verification summary — what held vs what didn't

Across the 4 maps, **48 of 59 load-bearing verdicts are CONFIRMED, 2 are FALSE, 9 are PARTIAL.** The confirmed spine is solid: all ~39 platform-seam files exist; the four audited mutation pipelines, EventBus fan-out, lifecycle phase machine, capability seam, help-as-projection chain, health-findings persistence, the economy/XP/karma sole-writer invariants, the AI gateway + typed contracts, and every cited migration/table/script/workflow are real. The corrections below are the only places a Fable designer must **not** take a source map at face value.

| # | Domain | Claim (as written in the map) | Verdict | Correction (source-verified) |
|---|---|---|---|---|
| 1 | Platform/UI | `views/selectors/` contains `multi_channel.py` | **FALSE** | Dir has `channel, role, subsystem, multi, multi_role, scope, _resource_helpers` — **no `multi_channel.py`**. Fragmentation point stands; filename is wrong. |
| 2 | Admin/safety | `BindingSpec` / `LifecycleResult` / `CapabilityDecision` are **new** foundation primitives to build | **FALSE** | All already shipped: `BindingSpec` `subsystem_schema.py:75`, `LifecycleResult` `lifecycle/contracts.py:77`, `CapabilityDecision` `governance/capability.py:57`. **Reuse/extend, never recreate.** |
| 3 | Platform/UI | `wiring_map` lists `ticket.opened` as a "possible dead subscriber" | PARTIAL | Live subscriber exists: `ticket_cog.py:57 bus.on('ticket.opened',…)`. Advisory is a false positive. But `governance.visibility/cache/cleanup.changed` **are** `EVT_*` constants with no `bus.on` found — real catalogue/subscriber drift. |
| 4 | Admin/safety | Hub entered via `!server` / `!servermanage` / `!serverpanel` | PARTIAL | Real command is `servermanagement` (aliases `servermenu`, `guildmenu`) at `server_management_cog.py:40-41`. Hub class `ServerManagementHubView` is correct; tokens are wrong. |
| 5 | Admin/safety | Setup commands are `!setup scan/start/resume/apply` + `!setup-delegate` | PARTIAL | No `!setup` group. Real surface: `setupadvanced`/`advancedsetup`, `setupdescribe`, slash `setup-advanced`/`setup-describe`/`setup-hub`/`setup-depth`, `setup-delegate`. Apply flow exists; command names differ. |
| 6 | Admin/safety | `image_moderation_service` is the external-call scanner (OpenAI moderation) | PARTIAL | It **explicitly does not** call OpenAI (`image_moderation_service.py:4-6`); the external call lives in `core/runtime/ai/providers/openai_moderation.py`. Attribution is off by one module. |
| 7 | Community/games | `karma_service.give` guarded by **INV-K** | PARTIAL | INV-K is **overloaded**: `architecture.md:136` = asyncio task-spawn invariant; `ownership.md:36` + `karma_service.py` = karma sole-writer. Karma usage matches ownership.md, but the taxonomy must disambiguate. |
| 8 | Community/games | `SettleOnceMixin` used by `views/blackjack/pvp_view` | PARTIAL | Class at `utils/terminal_guard.py:44`; real users are `rps/pvp_play`, `creature_battle/challenge`, `games/deathmatch_panel`, `blackjack_state` — **not** `blackjack/pvp_view`, which settles via `game_wager_workflow.settle_pvp`. |
| 9 | Community/games | A new declarative primitive layer must be **built** (RouteRegistry/Spec-family) | PARTIAL | A **mature declarative layer already exists and was unmentioned**: `subsystem_schema.py` (`SubsystemSchema`, `DomainPanelSpec`, `SettingSpec`, `BindingSpec` + `register`/`get_schema`) used by 10+ modules. RouteRegistry must **extend**, not greenfield. |
| 10 | AI/knowledge | Answer-review DB module is `utils/db/ai_review_log.py` | PARTIAL | Table (`ai_review_log`, mig 100), service, cog all confirmed — but the Python module is **`utils/db/ai_review.py`** (path cited wrong 4×). Table name is correct; path is not. |

### Primitive-name collisions with existing symbols (the load-bearing callout)

- **`ActionSpec` — HARD COLLISION.** Part 1's proposed UI action primitive collides with the **shipped** `services/automation_registry.py:35 class ActionSpec` (a frozen dataclass of automation `action_kind` metadata, mirroring migration 032 — a genuinely different concept). A rebuild reusing the bare name shadows the automation registry. **Design must rename** (`PanelActionSpec` / `UIActionSpec`) or explicitly unify. Because `ActionSpec` is meant to be shared across all 4 domains, the rename must be resolved **repo-wide before any domain adopts it.**
- **`SettingSpec` / `BindingSpec` — intentional reuse, not a rename.** Collide with `subsystem_schema.py:109`/`:75`, but the maps treat these as the **same existing types to preserve+fold**. No rename; document that they are the shipped classes.
- **`LifecycleResult` / `LifecyclePreview` / `StepResult` / `CapabilityDecision` / `ResourceRequirement` / `ProvisioningOption` — already shipped**, at `contracts.py:77/66/56`, `capability.py:57`, `resource_specs.py:79`, `resource_provisioning_catalogue.py:79`. Extend, don't recreate.
- **`AIGateway`** already exists (`core/runtime/ai/gateway.py:177`); Part 4's `AIProviderGateway` is a **rename-in-place**, and `services/ai_gateway.py:25` re-exports it — the seam split must be preserved.
- **All other proposed names grep-clean** in `disbot/` (SubsystemManifest, PanelSpec, EmbedFrame, TableSpec, ListSpec, NavigationSpec, SelectorSpec, WorkflowResult, MutationPreview, DiagnosticProviderSpec, ManagedTaskSpec, PanelContext, AdminActionSpec, ModerationActionSpec, SecurityActionSpec, ResourceMutationSpec, ServerEventRouteSpec, ConfirmationSpec, and all Part-3/Part-4 names). Note: `AIConfigProjection`/`RedactionContract`/`KnowledgeDomainSpec` have no class collision but are **behaviorally embodied** by existing `ai_config_projection_service.py`, `redaction.py`, and the in-flight "KnowledgeDomain seam (Slice B)" (`contracts.py:34`, `projmoon_context_service.py:15,113`) — align, don't compete.

## 2. The convergent thesis

All four independent maps describe the **same rebuild**: the codebase already contains the *right* patterns — service-owned audited mutation lanes (`emit_audit_action` fan-out), a publish-accepted `EventBus` with a catalogued event vocabulary, a typed three-lane config schema (`SettingSpec`/`BindingSpec`/`ResourceRequirement`), restart-safe `PersistentView` + capability-recheck-at-callback, help-as-projection, and a single provider-IO choke point (`AIGateway`) — **but those patterns are non-authoritative**: they run in parallel with legacy KV writes, raw `discord.ui.View` subclasses, per-cog permission checks, command-only surfaces, and five divergent result shapes. The rebuild's job is to make **the good pattern the *only* pattern**, and to make it **generated from one declarative source of truth** — a typed `SubsystemManifest`/`RouteRegistry` that owns each subsystem's metadata, capabilities, commands, panels, settings, bindings, resources, events, diagnostics, and help in one place, from which panels, routes, permission gates, and Help are *derived* rather than hand-wired. Crucially, this is **consolidation, not greenfield**: a mature declarative layer (`subsystem_schema.py`, `subsystem_registry.SUBSYSTEMS`, `hub_registry.HUBS`) already exists in fragments — the rebuild unifies them behind one grammar and deletes the divergent duplicates.

## 3. The unified primitive taxonomy

Every proposed declarative primitive, deduplicated across the 4 maps and grouped by layer. **Proposed-by** shows which parts converged on it; **collision** flags clash with a shipped symbol. This is the manifest grammar Fable must define.

### A. Manifest / registry core (the single source of truth)

| Primitive | Owns | Proposed by | Collision |
|---|---|---|---|
| **SubsystemManifest** | One typed record per subsystem: metadata, caps, commands, panels, settings, bindings, resources, events, diagnostics, help — folds `SUBSYSTEMS` dict + `SubsystemSchema` + `hub_registry` + `help_catalogue` | P1 (shared to all 4) | Free — but **must extend the shipped `subsystem_schema.py`** |
| **RouteRegistry** | One typed manifest over `subsystem_registry` + `hub_registry` + Help + settings/panel/permissions/completion; hub discovery + routing facet | P3 | Free — **same concept as SubsystemManifest; reconcile, don't double-define** |
| **KnowledgeDomainSpec** | Per-knowledge-domain manifest: commands, panels, data sources, context builder, eval suite, diagnostics (BTD6/ProjMoon/YouTube) | P4 | Behaviorally = in-flight "KnowledgeDomain seam (Slice B)" — align |

### B. Config lanes (already shipped — preserve & fold, do not reinvent)

| Primitive | Owns | Proposed by | Collision |
|---|---|---|---|
| **SettingSpec** | Scalar/typed setting lane | P1, P2, P3 | **EXISTS** `subsystem_schema.py:109` — reuse |
| **BindingSpec** | Discord-pointer binding lane | P1, P2 | **EXISTS** `subsystem_schema.py:75` — reuse |
| **ResourceSpec / ResourceRequirement** | Provisionable Discord resource (preview/apply/link) | P1 | **EXISTS** `resource_specs.py:79` — reuse |
| **SettingsPanelSpec** | Generated editor over `SettingSpec` (widgets/validation/capability/default/help) | P2 | Free — generator over existing SettingSpec |

### C. UI / panel grammar

| Primitive | Owns | Proposed by | Collision |
|---|---|---|---|
| **PanelSpec** | Declarative panel identity/owner/audience/anchor policy/renderer/actions/selectors/nav | P1 | Free |
| **PanelRuntimeView / GameViewBase / GamePanel** | Spec-driven base view (owner/participant/timeout/response-policy/back-help slots) replacing `BaseView`/`HubView`/raw `discord.ui.View` | P1, P3 | Free |
| **EmbedFrame / CardRendererSpec** | Safe embed/card renderer with size budgets + style tokens (folds `clamp_embed`, `help_overlay.home_embed_frame`, card/asset manifest) | P1, P3 | Free |
| **TableSpec / ListSpec / BrowserView** | Bounded table/list with pagination + truncation; shared browser (filter/sort/paginate) | P1, P3 | Free |
| **NavigationSpec / HubRoute** | Serializable help/home/back/parent routes, persistent custom_ids, public/ephemeral policy, click-time governance recheck | P1, P3 | Free |
| **SelectorSpec** | Options/pagination/selected/empty-state/callback-result | P1 | Free |
| **PanelContext** | Explicit bot/guild/actor/channel/interaction-or-anchor/audience — replaces `help_ctx_shim` | P1 | Free |
| **ActionView / ResultView / ConfirmModal** | Composed UI grammar for action panels, result cards, confirmation modals | P3 | Free |

### D. Action / mutation executors

| Primitive | Owns | Proposed by | Collision |
|---|---|---|---|
| **PanelActionSpec** (proposed `ActionSpec`) | Button/modal contract: label/custom_id/capability/defer-mode/handler/result-renderer/audit | P1 (shared) | **⚠ `ActionSpec` COLLIDES** `automation_registry.py:35` — **rename** |
| **AdminActionSpec** | Admin action: audience/capability/perm-fallback/callback-recheck/ephemeral/audit | P2 | Free |
| **ModerationActionSpec** | warn/timeout/kick/ban/delete/auto_delete + reason/DM/cleanup/hierarchy/audit/log-route | P2 | Free |
| **SecurityActionSpec** | raid/account-age side-effects as explicit specs | P2 | Free |
| **ResourceMutationSpec** | create/bind/rename/move/delete/reorder + preview/confirmation/perm-reqs/rollback | P2 | Free |
| **GameActionSpec** | mine/dig/explore, begin_cast/commit_catch, catch/collect/work | P3 | Free |
| **BindingAction** | Executor for binding mutations (`BindingMutationPipeline`) | P1 | Free |
| **CapabilitySpec** | Declarative capability requirement | P2 | Free — but resolves to **existing `CapabilityDecision`** `capability.py:57` |

### E. Result / preview grammar (collapse the five divergent shapes)

| Primitive | Owns | Proposed by | Collision |
|---|---|---|---|
| **WorkflowResult** | Unified mutation result: status/before-after/audit-event-cache flags/warnings/user-message across settings/bindings/provisioning/governance/lifecycle | P1 | Free |
| **MutationPreview** | Dry-run object for settings bundles/provisioning/lifecycle/setup | P1 | Free |
| **ConfirmationSpec** | preview/confirm/cancel/apply grammar; irreversible\|compensatable\|reversible, challenge/hash, timeout, actor re-check, before-state snapshot | P1, P2 | Free |
| **CurrencyMutationResult** | Money-mutation result (from `TreasuryResult` + economy result views) | P3 | Free |
| _LifecycleResult / LifecyclePreview / StepResult_ | Existing safety vocabulary | (reuse) | **EXIST** `contracts.py:77/66/56` |

### F. Event / audit

| Primitive | Owns | Proposed by | Collision |
|---|---|---|---|
| **AuditEventSpec** | Event name/actor/subject/guild/payload schema/redaction/subscribers/persistence-audit behavior | P1, P2 | Free — overlaps `audit_events.py` EVT_ module (behavioral) |
| **EventSpec** | Event name/payload shape/owner (catalogue entry) | P1 | Free |
| **ServerEventRouteSpec** | Passive event routing: source (gateway\|audit-log\|domain-event), opt-in, route binding, public/private projection, ignore filters | P2 | Free |

### G. Runtime / diagnostics / tasks

| Primitive | Owns | Proposed by | Collision |
|---|---|---|---|
| **DiagnosticProviderSpec** | name/sync-async lane/timeout/status-mapping/audience/redaction | P1 (shared) | Free |
| **ManagedTaskSpec** | name/subsystem/cancellation prefix/error hook/metrics labels | P1 | Free |
| **GameSessionPersistencePolicy** | ephemeral \| checkpointed \| authoritative (from `game_state_service`) | P3 | Free |

### H. Economy / progression / games domain specs

| Primitive | Owns | Proposed by | Collision |
|---|---|---|---|
| **EconomyLedger** | Audited coin ledger (from `economy_service` + `economy_audit_log`) | P3 | Free — audit-schema overlaps P2 |
| **ProgressionTrackSpec** | XP/level/title tracks (`xp_service` + `game_xp_service` + mining titles/world_identity) | P3 | Free |
| **RewardSpec** | daily/work/farm-collect/fishing-drops/mining-harvest | P3 | Free |
| **ItemCatalogSpec** | mining/fishing/creature/inventory item metadata (coupled namespace) | P3 | Free |
| **CraftingRecipeSpec + UpgradeTrackSpec** | mining recipes/forge + fishing bait/rod/charm/curio + farm upgrades | P3 | Free |
| **CollectionDexSpec** | creature dex + fishing log (discovered/undiscovered/filters/completion) | P3 | Free |
| **ChallengeSession** | participants/escrow/accept-decline-timeout/settle-once/rematch (blackjack/RPS/deathmatch/creature) | P3 | Free |
| **IdleAccrualSpec** | farm + fishing/mining energy + structures (last_settled_at/rate/capacity/collect txn) | P3 | Free |
| **LeaderboardSpec** | rank_source/metric/tie_breakers/scope/empty_state/card/privacy | P3 | Free |
| **CostVector** | shared spend/sink validation across shops/crafting/wagers | P3 | Free |

### I. AI / knowledge / tooling

| Primitive | Owns | Proposed by | Collision |
|---|---|---|---|
| **AIProviderGateway** | provider protocol + select/fallback + redaction + diagnostics + tool-dispatch | P4 | Rename of **existing `AIGateway`** `gateway.py:177` |
| **TaskProfile** | task→provider/model/response-mode/tool-budget/grounding/cache/eval-suite (declarative) | P4 | Free |
| **ContextBlock** | domain/facts/source_label/freshness/max_chars/render() | P4 | Free |
| **AnswerReviewLog** | redacted question/answer/correction + task/provider metadata + triage states (mig 100) | P4 | Free |
| **PresetAnswerStore** | keyed by normalized question + guild/scope + task + locale + provenance (mig 102) | P4 | Free |
| **SourceProvenanceSpec** | source key/trust tier/freshness/license note/answer label | P4 | Free |
| **IngestionPipeline** | fetch→parse→validate→audit→diff→PR→seed (shared by BTD6/ProjMoon/YouTube) | P4 | Free |
| **ViewModelContextHandle** | stable entity handles across UI + AI context + eval fixtures | P4 | Free |
| **EvalHarness** | separate deterministic offline evals from paid provider evals | P4 | Free — offline provider = `deterministic_provider.py` |
| **RedactionContract** | test-proven: every request field + tool result crosses the redactor | P4 | Behaviorally = `redaction.py` |
| **AIConfigProjection** | read-only projection separate from mutation service (mig 039) | P4 | Behaviorally = `ai_config_projection_service.py` |
| **NaturalLanguageRouter / KnowledgeRouter** | split the monolithic `natural_language_stage` into router + per-domain knowledge modules | P4 | Free |

### J. Ops / workflow (meta-substrate)

| Primitive | Owns | Proposed by | Collision |
|---|---|---|---|
| **AgentContextPack** | task-specific orientation generated from source manifests (`tools/agent_context/`) | P4 | Free |
| **RepoQualityGate** | required checks as code (one `code-quality.yml`, named gates) | P4 | Free |
| **WorkflowRoutineSpec** | versioned autonomous-routine prompts + token/permission assumptions | P4 | Free |

## 4. Preserve / redesign / drop — unified, by domain

### Platform / UI / runtime

**Preserve** — Four service-owned audited mutation lanes (`SettingsMutationPipeline` `settings_mutation.py:221`, `BindingMutationPipeline` `:154`, `ResourceProvisioningPipeline` `:240`, `GovernanceMutationPipeline` `writes.py:107`), each calling `emit_audit_action`. Authority re-check at callback time (`capability.py:71 actor_holds_capability`) — opening a panel is not authorization. `EventBus` publish-accepted fan-out (`events.py on/off/emit`) + `KNOWN_EVENTS` catalogue + the `audit.action_recorded → server_logging._on_audit_action` wiring (`server_logging.py:1856`). Lifecycle phase machine (7 phases) + `can_accept_commands` admission gate. Managed task registry (`tasks.spawn/cancel_all/cancel_by_prefix`) with diagnostics self-registration. `PersistentView` restart-safe contract (`timeout=None` + static custom_id, re-registered at startup, `persistent_views.py:72`). Interaction helpers `safe_defer/safe_followup/safe_edit/clamp_embed`. `BaseView` invoker-lock + `views.navigation` never-strand-from-Help/hub (`base.py:130`, `nav:help`/`nav:hub:`). Help-as-projection (`build_help_catalogue → project_help → HelpProjection` + `HelpRoute/open_route`). **Three distinct config lanes kept separate** (scalar `SettingSpec`, pointer `BindingSpec`, provisionable `ResourceRequirement`) — must not collapse to one generic config table. Registry-driven `SUBSYSTEMS` + `validate_registry`. Diagnostics registry + composed health snapshot + persistent findings (mig 057). Confirmation-first provisioning (`ProvisioningPreview` + mandatory `confirmed=True`).

**Redesign** — Fold `SUBSYSTEMS` + `SubsystemSchema` + `hub_registry` + `help_catalogue` metadata into one typed **SubsystemManifest**. Ad-hoc embed builders + `clamp_embed` + `home_embed_frame` → one **EmbedFrame**. Repeated defer/auth/mutate/audit/render callbacks → **PanelActionSpec** + **SelectorSpec** + **ConfirmationSpec** executors. Non-serializable navigation closures (`BackTarget`/`chain_back`) → serializable **NavigationSpec** with stable custom_ids + click-time recheck. Ad-hoc diagnostics providers → typed **DiagnosticProviderSpec**. **Five divergent mutation results + three preview shapes → one WorkflowResult / MutationPreview grammar.** `help_ctx_shim` → explicit **PanelContext**. `BaseView` → **PanelRuntimeView**.

**Drop** — Duplicate back buttons / one-off nav where `views.navigation`/`BaseView` already express the contract. Raw `discord.ui.View` subclasses lacking documented+test-pinned lifecycle (13 flagged: `LogChannelSelectView`, `ChannelSettingSelectView`, `_ChannelListPaginatorView`, `NumericPresetsView`, `RoleSettingSelectView`, `SetupLauncherView`, `StrategyReviewView`, `BTD6AdminView`, …). Command-only surfaces with no Help route / hub panel / discoverability metadata. Scattered per-panel permission checks instead of central governance resolution at entry **and** every callback. Direct DB writes from cogs/views and raw SQL outside db owners (`automation_scheduler.py`, `binding_backfill.py` flagged). Treating stale planning docs as truth.

### Admin / safety / server-management

**Preserve** — `SettingsMutationPipeline.set_value` (validation+authority+audit+event+cache-invalidation). `BindingMutationPipeline.set_binding/clear_binding` (`subsystem_bindings` rows + binding-changed events). `ResourceProvisioningPipeline` create-or-bind with **no silent auto-create**, binds through `BindingMutationPipeline`, audits success/fail/decline. `moderation_service` owns warn/timeout/kick/ban/unban/clear + auto_delete, all emit `EVT_MOD_ACTION` identical payload (`:361-629`). `message_pipeline` ordered stages route `ModerationActionDescriptor → auto_delete`; deleted msgs never reach XP. `server_logging` as fail-safe bus subscriber (swallows exceptions, `subscriber_errors` counter). `setup_operations.apply_operations` sole minter of `setup_delegate` actor_type, re-verifies live setup access (`:749/793`, pinned by `test_setup_delegate_actor_boundary`). `actor_holds_capability` central check (target-guild membership, platform-owner override, admin floor, revoke overlay, setup-delegate). `ChannelLifecycleService`/`RoleLifecycleService` preview/apply for destructive ops. `lifecycle/contracts.py` typed `StepResult`/`LifecyclePreview`/`LifecycleResult`. `subsystem_bindings` (mig 022) as durable resource-id owner. Capability-string gates (`logging/moderation.settings.configure`, `cleanup.policy.configure`, `proof_channel.settings.configure`). Read-only diagnostic/platform hubs; `FlagManagerView` as the mutating exception routed through the rollout pipeline.

**Redesign** — Logging UI lives under `cogs/logging/` with **no `views/logging/` dir** → move into a generated settings/bindings panel family. Legacy channel-id logging settings run parallel to `BindingSpec`s → make binding rows the single route-truth, demote settings to compat read-aliases. Moderation & security lack the preview/result vocabulary channels/roles have → add **ModerationActionSpec/SecurityActionSpec** modeled on `lifecycle/contracts.py`. Scattered `has_permissions(administrator=True)`/`guild_permissions`/owner checks → one **AdminActionSpec**/capability resolver re-checked at every mutating callback. One-off selectors/modals → shared resource-picker / settings-editor / confirmation primitives. automod/security/welcome/counters/proof_channel have settings but **no view dir** → generated panels driven by `SettingSpec`.

**Drop** — Direct Discord mutations from cogs/views (`guild.create_*`, `channel.delete`, `member.add_roles`) — grandfather legacy only. Direct legacy-KV writes and direct `subsystem_bindings` writes bypassing audit/event/cache. Duplicate setup paths (quicksetup, wizard, hub panels, per-cog config) → compile to setup-draft operations. Decorator-only authority (hub/help reach a panel without the command decorator). Command-only/admin-only hidden config for automod/security/welcome/counters. Inconsistent destructive confirmations (some preview+confirm, older panels one-shot delete).

### Community / economy / progression / games

**Preserve** — **INV-F** (every coin mutation through `economy_service.credit/debit/transfer/bet_and_settle/refund` → `economy_audit_log` mig 014, AST-enforced). **INV-G** (every XP mutation through `xp_service.award/reset/import_level`; `xp.level_up → community_spotlight` real subscriber `cog:254`). **INV-K/karma** (every grant through `karma_service.give`: no-self, per-pair cooldown, per-giver daily cap; emits `karma.granted`). `audit.action_recorded` shared publisher (import-invisible wiring — preserve by grep, not import graph). `game_wager_workflow.settle_pvp/refund_pvp` escrow/refund seam (blackjack + RPS). `game_state_service.save/load/clear/list_stale` checkpoints (mig 015/018) + TTL + cleanup. Pure engines with no Discord/DB imports (`blackjack_engine`, fishing/mining/creature/farm math+catalog). `SUBSYSTEMS.parent_hub` ↔ `HUBS.primary_children` roster (CI-tested `test_every_hub_primary_children_match_parent_hub_filter`). **The existing declarative layer `subsystem_schema.py`** — build on it. `SettleOnceMixin` (`terminal_guard.py:44`) idempotent settlement.

**Redesign** — Mother-hub navigation via registry discovery (`discover_game_children`/`discover_community_children`) → one **HubRoute** grammar. Fragmented back-nav (`BackToPanelButton` + `attach_back_to_{games,economy,community}_button`) → one route-aware Back/Home/Help/Rules slot set. `BlackjackPanelView` → canonical **GamePanel** composition. `UnifiedInventoryView` + `_group_page_by_rarity` → shared **BrowserView**. `LeaderboardView` `rank_providers` → per-domain **LeaderboardSpec**. `CreatureDexView` → generic **CollectionDexSpec**. `RodRecipeBrowserView` + mining recipes → generic **CraftingRecipeSpec** browser. `farm_workflow` idle accrual → **IdleAccrualSpec**.

**Drop** — Mixed view bases with no shared game/session base (casino poker, `FishingCastView`, solo `BlackjackView` extend raw `discord.ui.View`; hubs use `HubView`/`PersistentView`; browsers use `BaseView`). Per-game reinvented challenge/session lifecycle (accept/decline/timeout/settle-once/stale) duplicated across blackjack/RPS/deathmatch/creature/casino. Inventory UX split from item ownership (generic `utils/db/inventory.py` vs vertical stores). Command-only product surfaces not reachable from panels. In-cog view classes (`SpotlightView`/`GamesView`, `ChainMenuView`) instead of shared primitives. Ad-hoc audit reason strings / event names instead of typed enums.

### AI / knowledge-data / tooling / ops

**Preserve** — `AIGateway` as the single provider-IO choke point (select + fallback + payload/system-prompt/tool-result redaction + degraded reply + diagnostics). Typed AI boundary in `contracts.py` (12 classes). **Invariant: exactly one passive responder** — AI cog stays unregistered so `natural_language_stage` is the sole passive path (`:6`). Answer-review durable loop (`ai_review_log` mig 100 + `utils/db/ai_review.py` + service + cog + `views/ai/panel.py`). Preset reuse loop (`ai_answer_presets` mig 102, redaction/normalization **before** DB). Redaction crossing every model input/output/tool-arg/tool-result and every stored row. BTD6 provenance stack (`btd6_source_registry` freshness/trust/health + `btd6_data_blobs.sha256` + source-labelled render dataclasses with length caps). `btd6_view_model_service` UI read-model. AI config read projection kept separate from mutation seam (mig 039). External-data refresh opens a reviewable PR, never pushes to main. Shared `git_merge_state.py` + one `code-quality.yml` with named gates. Generated agent-context packs from `docs/agent/index.yml` + `context_map.py`.

**Redesign** — Declarative provider/model routing as **TaskProfile** (today split across `routing.py` + `feature_flags.py` + `AI_*` env + settings). Split monolithic `natural_language_stage` into **NaturalLanguageRouter** + per-domain **KnowledgeRouter**. Collapse per-service freshness into one **SourceProvenanceSpec**. One **IngestionPipeline** shared by BTD6/ProjMoon/YouTube. **Relocate `AIGateway` out of `core/` so it stops importing services** (`gateway.py:51 from services import metrics` is the live boundary break). Shared diagnostics panel + help route for AI/BTD6/media (not command-only). Generalize `context_map.py`/`wiring_map.py` beyond `disbot/` (exit-2 on non-disbot today). Stable **ViewModelContextHandle** reused across UI/AI/evals. Give ProjMoon + YouTube the same explicit **KnowledgeDomainSpec** BTD6 effectively has (incl. YouTube cache TTL / transcript source / video-id normalization).

**Drop** — Ungrounded "AI already knows game facts" answer paths (route deterministic questions through facts, not the model). Unlabelled cross-source merges (wiki-derived vs game-dump vs DB). Live external API inside unit/eval paths (evals must run offline/deterministic — use `deterministic_provider.py`). Command-only diagnostics with no operator panel. PAT-heavy/bespoke auto-merge machinery where GitHub-native auto-merge + branch protection suffice. Raw `discord.ui.View` in `views/btd6/admin_panel.py` + `strategy_review.py` (tracked debt). Provider behavior hidden behind env with no runtime settings projection/diagnostics.

## 5. Backward-compat contract (the migration hazard set)

The union of what **breaks persisted state or the Discord routing surface** if the rebuild changes it. This is the cross-domain output the design must freeze before touching a schema.

**1. Persisted `subsystem_registry` keys (rename = data loss).** `SUBSYSTEMS` keys (`admin, server_management, moderation, economy, inventory, treasury, ticket, mining, settings, diagnostic, help, …`) are load-bearing across DB rows, governance policies, help overrides, settings groups, bindings, and capability strings. `HUBS.primary_children` **must equal** `SUBSYSTEMS.parent_hub` filter (CI-tested) — generate one from the other.

**2. Persistent `custom_id` strings = a Discord routing API (must stay verbatim).** All verified: `nav:help`, `nav:hub:<subsystem>`, `help:back`, `help_categories:select`, `settings_hub.{subsystem_select,page_prev,page_next,needs_setup,invalid,missing_bindings,audit,command_access}`, `settings_missing_bindings.back`, `settings_invalid.back`, `settings_subsystem.back_to_hub`/`open_panel`, `settings:back`. `ServerManagementHubView`, `EconomyPanelView`, `MiningHubView`, tickets/role-menus/logging/setup launchers, and `views/ai/` (`panel.py`, `support_report.py` — **unmapped, extract before rebuild**) all carry persistent IDs. **A clean repo needs a central custom_id registry**, and a **versioned scheme** for dynamic game-session IDs (blackjack/RPS/creature).

**3. Event names + payload shapes (the cross-service contract).** All are `EVT_*` constants mirrored in `core/events_catalogue.py`: `moderation.action_taken`, `audit.action_recorded`, `settings.changed`, `resource.provisioned`, `role.lifecycle_changed`, `channel.lifecycle_changed`, `security.raid_detected`, `security.account_flagged`, `image_moderation.flagged`, `welcome.member_greeted`, `counters.updated`, `automation.rule_changed`, `ticket.opened`, `xp.level_up`, `karma.granted`. Payloads are **untyped kwargs**; a result flag like `event_emitted` means *publish-accepted only, not delivered*. **Drift risk:** `governance.visibility/cache/cleanup.changed` are defined `EVT_*` with **no `bus.on` subscriber found**. Freeze these payload shapes: `EVT_MOD_ACTION`/mod_logs, settings-mutation audit, `resource_provisioning_audit` (mig 030), lifecycle audit, feature-flag audit, ticket audit.

**4. DB migrations / tables (ordering-load-bearing).** Fixed numbers own live tables: `022 subsystem_bindings`, `030 resource_provisioning_audit`, `031 setup_session`, `035 setup_draft_operations`, `039 ai_policy` (5 policy tables), `040/041/048/054 BTD6` (incl. `btd6_data_blobs.sha256` provenance), `049 youtube_video_cache`, `057 operational_health_findings`, `069 setup_delegate_actor_type`, `092 guild_treasury`, `098 tickets`, `099 setup_session_essential_anchor`, `100 ai_review_log`, `102 ai_answer_presets`; economy/game set `003/005/014/015/018/019/065`; `019` **dropped `rps_matches`** — RPS state lives in `game_state_service`, **do not port a matches table**. A clean rebuild deriving a smaller schema **must plan a data migration off these**. Seed/refresh ordering: source registry → facts → snapshots → source health; ingestion run/audit before health; evals after data refresh.

**5. Settings keys (externally observable).** Legacy KV keys in `utils/settings_keys/*` (`moderation, cleanup, automod, image_moderation, security, welcome, counters, logging, karma, ai`) are migration data — **a rebuild needs an import/alias map**. `settings_keys` constants are the **only** valid keys into `db.get_setting` (never raw strings). Per-subsystem `cogs/*/schemas.py` keys are a persisted contract (blackjack reads `default_entry_fee`). **Hard semantic invariant: empty `capability_required` in `SettingSpec`/`BindingSpec` means ADMINISTRATOR floor, not anonymous access — must not be reinterpreted.**

**6. Actor types / audit invariants.** `actor_type='setup_delegate'` is minted **only** in `apply_operations` and guarded by `test_setup_delegate_actor_boundary` — payload/actor-type shape is a hard contract. Sole-writer invariants INV-F (coins), INV-G (XP), INV-K (karma) are AST-enforced — every rebuild mutation must go through the audited seam or CI reddens. `subsystem_bindings` rows are durable resource-id persistence; teardown/import must be explicit. Platform-owner bypass exists via `config.is_platform_owner` (`config.py:46`).

**7. AI/knowledge stable identifiers.** `AITask` enum member names must line up with provider/model defaults + settings + eval fixtures + NL routers (rename = multi-surface break). Knowledge context IDs (BTD6 tower/hero/event/leaderboard/fact IDs; ProjMoon entry IDs) must stay stable across UI, AI context, eval fixtures, DB rows. `ai_review_log`/`ai_answer_presets` rows are guild-scoped with **normalized question keys** + redacted question/answer/correction columns — key normalization is a compat contract. BTD6 QA eval corpus assumes a specific data version + source labels — data update without golden refresh reddens evals. `youtube_video_cache` TTL + video-id normalization + transcript-source assumptions.

**8. Env/secrets + CI token assumptions (behavior differs by environment).** `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `AI_ENABLED`, `AI_DEFAULT_PROVIDER`, `AI_FALLBACK_PROVIDER`, task-routing vars, optional moderation key. **Image moderation must not call OpenAI until guild opt-in**; external call lives in `openai_moderation.py` (honor exempt roles/channels + threshold/category buckets). Routines/reconciliation + some PR-status workflows rely on `ROUTINE_PAT`/elevated perms; default `GITHUB_TOKEN` won't trigger downstream workflows (the auto-merge-enabler recursion-guard class).

**9. Versioned product content.** `data/fishing/fish.json`, `data/creatures/creatures.json`, `data/projmoon/limbus/*.json`, `data/btd6/{towers,heroes}.csv` (**repo root**, not `disbot/data/`) are authoritative content (odds/rewards/entities) — treat schema as **versioned**. Mining inventory doubles as the generic material store for fishing pearls/coral/curios — **item namespace is coupled across games; unifying the catalog must preserve cross-refs.** Restart-safety split: counting/blackjack/RPS in-process state is restart-lossy; only `game_state_service` checkpoints survive — money-safety relies on refund/recovery tests.

## 6. Minimum platform kernel a fresh repo starts with

The ordered foundation all 4 maps imply — build this **before any feature cog**; each layer depends only on those above it.

1. **`utils/` + `utils/db/` + migrations runner.** DB access seam (`asyncpg`-only in `utils/db/`; never `pool.execute()` outside it) + `settings_keys` constants. Nothing else may touch SQL.
2. **`EventBus` + `KNOWN_EVENTS` catalogue** (`on/off/emit/registered_events/delivery_stats`) with the catalogue as source-of-truth and a catalogue↔subscriber drift check.
3. **Lifecycle phase machine** (7 phases) + `can_accept_commands` admission gate, and the **managed task registry** (`spawn/cancel_all/cancel_by_prefix`) with diagnostics self-registration (INV: `create_task → tasks.spawn`).
4. **`governance/capability`** — `actor_holds_capability` + `CapabilityDecision` (target-guild membership, platform-owner override, ADMINISTRATOR floor, revoke overlay, setup-delegate). The single authority seam, re-checked at every callback.
5. **Audited mutation seam** — `emit_audit_action` fan-out + the **WorkflowResult / MutationPreview / ConfirmationSpec** grammar, so every write is previewable, audited, event-emitting, and cache-invalidating from day one.
6. **`subsystem_schema` config lanes** (`SettingSpec` / `BindingSpec` / `ResourceRequirement`) + the unified **SubsystemManifest/RouteRegistry** + `validate_registry`, with `HUBS` generated from `SUBSYSTEMS`.
7. **Discord UI kernel** — `PanelRuntimeView` (restart-safe: `timeout=None` + static custom_id, re-registered at startup) + interaction helpers (`safe_defer/safe_followup/safe_edit`) + **EmbedFrame** + a **central custom_id registry** + **NavigationSpec** (never-strand-from-Help/hub) + **PanelActionSpec/SelectorSpec** executors.
8. **Help-as-projection** (`build_help_catalogue → project_help → HelpProjection` + `HelpRoute/open_route`) derived from the manifest, and **diagnostics registry + health-findings** persistence (mig 057-equivalent) with audience projection/redaction.
9. **AIProviderGateway relocated *out of* `core/`** (so core imports no services) + typed `contracts.py` boundary + **RedactionContract** + the offline `deterministic_provider` + **EvalHarness** — before any knowledge domain.
10. **Repo substrate** — `context_map.py`/`check_architecture.py`/`RepoQualityGate` (one `code-quality.yml`, named gates), **AgentContextPack** generation, and **WorkflowRoutineSpec** — the self-improving-workflow layer that is itself the primary artifact.

## 7. Open questions for the Fable design

1. **The `ActionSpec` rename (blocking, repo-wide).** The UI action primitive collides with shipped `automation_registry.ActionSpec`. Choose one and apply it **before any domain adopts the shared primitive**: `PanelActionSpec`/`UIActionSpec` (rename, keep automation's `ActionSpec`), or a single unified `ActionSpec` grammar covering both UI-button and automation-action semantics (are they really one concept? the maps say no). This decision gates Parts 1–3.
2. **One manifest vs. split registries.** `SubsystemManifest` (P1), `RouteRegistry` (P3), and `KnowledgeDomainSpec` (P4) are three names for "the one declarative source." Do they unify into a single manifest with facets (metadata / routing / knowledge-domain), or stay as a small family? Either way they **must extend the shipped `subsystem_schema.py` + `subsystem_registry` + `hub_registry`** — not greenfield parallel infra (the P3 PARTIAL correction).
3. **Legacy-KV vs. `BindingSpec` route-truth.** Logging (and other domains) run channel-id settings **in parallel** with binding rows. Which becomes authoritative in the rebuild, and what is the exact import/alias map that lets old `settings_keys` rows read through the new binding as compat aliases? (Affects the mig-005-style data migration.)
4. **INV-K disambiguation.** `INV-K` names **two** invariants in source (`architecture.md:136` task-spawn; `ownership.md:36` karma sole-writer). The cross-domain invariant taxonomy must rename one before it becomes a rebuild contract.
5. **Settings safe-default policy.** The empty-`capability_required`→ADMINISTRATOR-floor rule must survive verbatim. Beyond that: does a freshly-provisioned subsystem default its settings **ON** (discoverable) or **OFF** (opt-in) — and how does that interact with the "no silent auto-create" provisioning invariant and the image-moderation "no external call until opt-in" gate?
6. **Custom-id versioning scheme.** Static persistent IDs (hubs) vs. dynamic per-session IDs (game challenges) need one scheme that survives restart *and* schema evolution. Include the currently **unmapped `views/ai/` custom_ids** — enumerate them before the rebuild strands an AI panel.
7. **Where does `AIGateway` live?** It must leave `core/` to stop importing `services` (`gateway.py:51`), while `services/ai_gateway.py` keeps re-exporting the seam. New home: `services/ai/`? A dedicated `ai/` top-level package? This reshapes the layer graph.
8. **Data migration off fixed migration numbers.** A rebuild deriving a smaller schema must decide: fresh schema + one-time importer from the live `003…102` tables, or carry the numbered chain forward? The `019 drop rps_matches` precedent (state in `game_state_service`, not a table) is the template — which other tables collapse into checkpoints vs. persist?
9. **Ingestion + eval determinism.** One `IngestionPipeline` for BTD6/ProjMoon/YouTube implies a shared `SourceProvenanceSpec` and a golden-refresh discipline (data bump ⇒ eval-corpus bump). Confirm the offline `deterministic_provider` is the sanctioned eval provider and that no unit/eval path can reach a live API.
10. **Manifest-generated leaderboard honesty.** `LeaderboardSpec` assumes per-user persisted stats that casino/blackjack/word-chain **don't currently write**. Unified leaderboards need new stat-write seams first — does the rebuild add those writes as part of the game-session primitive (`ChallengeSession`/`GameSessionPersistencePolicy`), or defer honest leaderboards to a later band?

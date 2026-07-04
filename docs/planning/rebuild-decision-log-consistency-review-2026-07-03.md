# Rebuild decision-log consistency review (2026-07-03)

> **Status:** `audit` — read-only consistency review of the 2026-07-03 rebuild decision logs,
> requested after Stage-1/conventions/hub-navigation/rubric/foundational-mechanics planning. This
> document records contradictions, missing durable homes, vocabulary risks, and owner questions. It
> does **not** approve implementation, redesign the rebuild, or supersede owner decisions.
>
> **Inputs reviewed:**
> - `docs/planning/rebuild-stage1-global-review-2026-07-03.md`
> - `docs/planning/rebuild-conventions-invocation-authority-2026-07-03.md`
> - `docs/planning/rebuild-hub-navigation-presets-2026-07-03.md`
> - `docs/planning/rebuild-critical-review-rubric-2026-07-03.md`
> - `docs/planning/rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md`
> - `docs/owner/maintainer-question-router.md` Q-0219 through Q-0236
> - `docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/FINAL-REVIEW.md`
> - `docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md`
> - PR #1691, checked on GitHub because this container has no `gh` CLI and no usable `origin` remote
>
> **PR #1691 note:** PR #1691 was still open when reviewed. Treat it as pending evidence until it is
> merged or explicitly accepted by the owner as usable pending input.

> **Post-review status (2026-07-04, open-PR merge sweep):** written 2026-07-03, before the
> foundational kernel **design bridge** (#1708) and the **Gate-0 grammar-freeze + Phase-B L0
> build-order** (#1716, `docs/analysis/rebuild-discovery/foundations/gate-0/`) landed — neither had
> this review in main when they ran, so the §2 conflict table's "Gate-0 blocker" rows, the §3
> durable-home routes, and the §5 owner questions were **not** folded into that freeze by this doc.
> PR #1691 has since **merged**. Before acting on any row here, check it against the frozen L0
> grammar, the amendment registry (G-1…G-24), and the owner-decision packet — several rows (e.g.
> authority vocabulary, C-1 resolver contract, preset semantics) may already be resolved there;
> whatever is *not* covered there is still-live review input.

## 1. Decision consistency verdict

**Verdict: mostly consistent, but not yet Stage-2/Gate-0 safe without a consolidation pass.**

The 2026-07-03 logs generally separate owner-decided standards from recommendations and open
sub-decisions well:

- **Clearly owner-decided / binding:** S-1 engine/declaration/seam, S-2 foundation-before-consumer,
  shared-verb naming, the four-rung invocation ladder, moderator-action envelopes, authority plus
  bot-owner override, unified help hub, Back/Home navigation, per-guild presets, the critical-review
  rubric, and the Prompt A/B split.
- **Clearly not yet frozen:** C-1 through C-7 are owner-endorsed foundations whose detailed contracts
  are still to be decided in Gate-0 or Phase-B. This is stated, but several C-items are also phrased
  as mandatory in surrounding text, so Gate-0 must normalize their exact status.
- **Clearly open:** preset exclusion behavior, G-22 staging lanes, CUT-3 rollback window `N`, final
  top-level hub buckets, per-subsystem triage, the shared-verb command list, and the detailed C-item
  contracts.

The main risk is **routing ambiguity**, not philosophical contradiction. Several decisions are
labeled as "Gate-0 feeds," "Stage-2 inputs," or "Phase-B plan details," but not all have exactly
one durable home where the final answer must live. That creates a risk that Stage 2, Gate-0, and
later implementation agents re-answer the same question independently.

## 2. Conflict table

| Decision / area | Files involved | Why it conflicts or risks conflict | Severity | Recommended durable fix |
|---|---|---|---|---|
| Authority vocabulary: "one authority layer" vs design spec's "one authority model, two lanes" | `rebuild-conventions-invocation-authority-2026-07-03.md`; `rebuild-design-spec-2026-07-02.md` | The convention log says every action carries a single declared authority label mapped in one place. The design spec still models mutually exclusive `capability_required` and `audience_tier` lanes. Stage-2 authors may not know whether to declare one label or choose one of two fields. | **High — Gate-0 blocker** | Gate-0 should define one canonical authority declaration vocabulary. Recommended: keep the design spec's lane distinction internally, but expose it as a single `authority_ref` / `authority_label` concept that resolves to either governance capability or domain audience tier. |
| C-1 resolver status: endorsed direction vs invocation-ladder dependency | `rebuild-conventions-invocation-authority-2026-07-03.md`; `rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md` | The invocation ladder says all four rungs resolve through one resolution/authority/validation point, while C-1 is described as an endorsed foundation whose detailed contract is future work. The concept is decided; the exact contract is not. | **High — Stage-2/Gate-0 blocker** | Promote "one resolver exists" to an explicit owner-decided invariant, and route only its fields/API/UX edge cases to Gate-0. Durable home: Gate-0 K8/K1 resolver contract, referenced by Stage-2 surface records. |
| Preset exclusion semantics conflict with current wording | `rebuild-hub-navigation-presets-2026-07-03.md` | The doc says presets decide what is "visible/on per server," then asks whether excluded features are hidden-but-runnable or disabled entirely. "Visible/on" can be read as pre-deciding the open question. | **High — Stage-2 blocker** | Split terms now: `visibility` = help/hub surfacing; `activation` = command/runtime availability. Add owner question: "Does preset exclusion set visibility only, activation only, or both?" Durable home: Gate-0 `PresetSpec` / `HubVisibilitySpec`. |
| Welcome reorder conflicts with frozen BUILD-PLAN table until Gate-0 fold | Stage-1 log; `NEW-BOT-BUILD-PLAN.md` | The frozen plan still lists welcome in L1b depending on role, while the Stage-1 log re-homes welcome to L1c after the card engine. This is an intentional companion-log delta, but readers must know it supersedes the table. | **Medium — Gate-0 edit required** | Gate-0 must patch the build-order table or add an explicit superseded-rows appendix. Durable home: BUILD-PLAN successor / Gate-0 build-order table. |
| Admin as hub node vs admin subsystem in L1b | Hub-navigation log; `NEW-BOT-BUILD-PLAN.md` | The hub doc says admin is a permission-gated node inside one help hub. The build plan still has `admin` as an L1b subsystem. This is not inherently wrong, but needs vocabulary: implementation subsystem versus hub projection. | **Medium** | Add glossary entry: **admin subsystem** != **admin hub node**. Durable home: Stage-2 surface record and Gate-0 `PanelSpec`. |
| "Global parser" means fuzzy, but parser is also used for AI/NL | Conventions log; Prompt A/B brief | The convention log labels rung 2 fuzzy as "the global parser," while rung 3/4 are NL parsing/orchestration. Prompt A owns fuzzy logic and invocation matching; Prompt B owns suggestion rendering. | **Medium** | Ban bare "parser" in final docs. Use `fuzzy_command_matcher`, `nl_intent_router`, and `nl_orchestration_planner`. |
| Media generation default-OFF vs design spec safe-default AI posture | Stage-1 log; design spec | Media generation is default-OFF per guild with quota/caps/kill switch, while the design spec has broader `AI on_when_keyed` language and image moderation `off_until_opt_in`. Without a distinct class, media generation could be lumped into general AI. | **Medium — Gate-0 required** | Add `activation = off_until_guild_opt_in` for generated media specifically, separate from general AI and image-moderation privacy gates. |
| Prompt A/B split may duplicate restart-safety / persistence | Foundational-mechanics brief | Prompt A owns lifecycle/tasks, persistence classes, and restart-safety under merge=deploy; Prompt B owns persistent views and restart-safe panels. This is a valid seam, but the shared phrase can cause duplicate systems. | **Medium** | Define seam: A owns persistence/session state contracts; B owns panel render/rederive contract; one `RestartSafetySpec` should collect both. Durable home: Gate-0 lifecycle/panel crosswalk. |
| Rubric checker scope vs current-repo checker scope | Critical-review rubric | The rubric says most checkers should land in the rebuild where declarations exist, but also says to extend `check_plan_staleness.py` now. The split is reasonable, but task routing should prevent attempts to bolt all manifest checkers onto the current bot. | **Low/Medium** | Create a checker backlog table with columns: current repo now / Gate-0 / new repo K10 / Phase-B. Durable home: `docs/ideas/rebuild-critical-review-checkers-2026-07-03.md`. |
| PR #1691 pending state | Foundational-mechanics brief; PR #1691 | The brief expects Session B to land a report, but PR #1691 was still open when reviewed. Treating it as already folded would be premature. | **Medium — review input freshness** | Do not fold Prompt B findings into Stage-2/Gate-0 until PR #1691 is merged or explicitly accepted by the owner as pending evidence. |

## 3. Missing durable-home table

| Open decision / unresolved route | Current mention | Why current home is insufficient | Recommended single durable home |
|---|---|---|---|
| Preset exclusion: hidden-but-runnable vs disabled entirely | Hub-navigation §3 | It is marked open, but Stage 2 needs the answer before assigning preset membership because membership semantics affect command availability, not just UI. | Gate-0 `PresetSpec` / `HubVisibilitySpec`, with Stage 2 blocked until owner answers. |
| C-1 command resolver exact contract | Conventions §6 | "One resolver" is effectively required, but its input/output, audit boundary, cooldown point, and authority call sequence are not homed. | Gate-0 K8 interaction-runtime contract. |
| C-2 draft pipeline exact ownership and API | Conventions §2.4 and §6 | It spans AI orchestration, human setup, fuzzy destructive confirmations, workflow engine, and audit. Without one home, each producer may build its own preview/apply path. | Gate-0 `Workflow` / `DraftPipelineSpec`, with producer interfaces for human setup and AI. |
| C-3 template primitive vs presets | Conventions C-3; hub presets | "Preset," "template," and "bundle" are adjacent but not normalized. | Gate-0 `TemplatePresetSpec` glossary: template = reusable draft; preset = named config bundle; membership = feature declaration. |
| C-4 response/result grammar | Conventions C-4; Prompt B scope | It is central to silent-vs-reply behavior across all invocation rungs, but only endorsed. | Gate-0 `WorkflowResult` / response grammar spec. |
| C-5 fuzzy matcher plus suggestion rendering split | Conventions C-5; Prompt A/B boundary | Logic and rendering are split across prompts; the durable product must still be one engine. | Gate-0 `FuzzyCommandMatcherSpec` with `SuggestionRenderSpec` as a presentation facet. |
| C-6 cooldown/rate-limit engine | Conventions C-6; design spec already has `CooldownSpec` | The design spec field exists, but C-6 elevates it to a full engine with abuse posture; exact scope needs one owner. | Gate-0 `CooldownSpec` plus RateLimitEngine contract in the K8/K6 boundary. |
| G-22 staging-lanes standardization | Conventions "still open" note | It is explicitly open but not assigned a durable owner/doc in the reviewed 2026-07-03 set. | Router question plus Gate-0 staging-lane amendment. |
| CUT-3 rollback window `N` | Stage-1 D-3 says Stage 3 sets `N` | It is routed, but should be a named Stage-3 checklist item so it cannot disappear. | Stage-3 consolidation checklist plus migration/cutover plan. |
| Top-level hub bucket finalization and per-subsystem hub placement | Hub-navigation says Stage 2 | The routing is good, but the durable artifact name is not explicit. | Stage-2/3 final surface record with one row per subsystem. |
| Shared-verb computed command list | Conventions says Stage 2 computes and publishes it | The routing is good, but the durable artifact name is not explicit. | Stage-2 command-surface registry / K1 seed table. |
| Moderation envelope spot-check | Conventions says timeout grammar spot-check confirms before freeze | Decision is made, but the confirmation artifact is not named. | Gate-0 `ModerationActionSpec` spike note with one real timeout envelope. |
| Prompt A/B report reconciliation | Foundational-mechanics brief launches two reports and says owner reads ledgers | Two reports can create competing recommendations unless a single reconciliation home exists. | Foundations audit reconciliation ledger before Gate V / Phase B. |

## 4. Vocabulary normalization suggestions

| Current vocabulary variants | Problem | Suggested canonical vocabulary |
|---|---|---|
| engine / service / primitive / foundation / grammar / generated model | These are not all synonyms. "One engine per domain" can be undermined if "primitive" or "service" is used casually to create a duplicate. | **engine** = owns control flow/transactions/audit; **primitive** = reusable declarative object type; **grammar/spec** = manifest schema; **service** = implementation module behind an engine. |
| parser / global parser / fuzzy / NL router / AI parser | "Global parser" currently means fuzzy rung 2, but AI/NL also parses language. | Use `fuzzy_command_matcher`, `nl_intent_router`, and `nl_orchestration_planner`; avoid bare "parser." |
| preset / template / bundle / profile / layout | Presets and templates are adjacent but different: hub presets are config bundles; AI templates are reusable drafts. | **preset** = named configuration bundle; **template** = reusable draft/action plan; **layout** = generated hub arrangement; **membership** = feature declares preset inclusion. |
| visibility / availability / activation / enabled / hidden / disabled | This is the biggest Stage-2 risk because preset exclusion is open. | **visibility** = shown in hub/help; **activation** = command can run; **availability** = combined user-facing state; **disabled** = activation false; **hidden** = visibility false. |
| authority label / `capability_required` / `audience_tier` / permission gate | Convention log says one label; design spec has two fields. | Use one public term: **authority_ref**. Internally it resolves to governance capability or domain audience tier. |
| Back to help / Home / parent hub / semantic parent | Owner wording includes "back to help and back to parent hub," while docs use Back/Home. | **Back** = previous stack or semantic parent fallback; **Home** = help root. Avoid "back to help" for Home. |
| owner / bot owner / server owner / platform owner | Bot-owner override can be confused with Discord guild owner or platform-owner naming in older docs. | Use **bot_owner_id** for the global override; **guild_owner** for Discord server owner; **platform_owner** only if retained as legacy term and mapped. |
| Stage / Phase / Gate / K / L | Stage 1/2/3, Phase A/B/C, Gate-0/Gate V, K0-K10, and L0-L5 all coexist. | Keep D-6: L-layers canonical for build sequencing; K only kernel components; Stage = review workflow; Phase = planning lifecycle; Gate = approval/checkpoint. |
| defer / dormant seam / off / hidden / dropped | D-5 triage, S-2 peer deferral, and preset exclusion are separate concepts. | **defer** = not in Phase-B queue yet; **dormant seam** = exists but inactive until provider lands; **hidden** = not surfaced; **disabled** = cannot run; **drop** = removed from rebuild scope. |

## 5. Owner questions that should be added or clarified

1. **Preset exclusion semantics:** when a guild chooses a hub preset that excludes a bucket or
   feature, should that set only `visibility=false`, both `visibility=false` and `activation=false`,
   or should the preset choose per feature?
2. **Authority canonical field:** should Stage-2 authors declare a single `authority_ref`, with
   Gate-0 mapping it to governance/domain lanes, or explicitly choose `capability_required` vs
   `audience_tier`?
3. **C-1 resolver status:** is the existence of one command resolver now owner-decided, with only
   details pending, or is even that still an endorsed direction?
4. **C-2 draft pipeline boundary:** which actions must use preview/confirm/apply: all mutations,
   destructive mutations only, AI-generated actions only, or setup/admin bulk changes?
5. **Fuzzy auto-run safety classification:** who classifies commands as safe for very-close fuzzy
   auto-run: command manifest field, authority label, mutation/read classification, or
   owner-reviewed allowlist?
6. **Bot-owner audit visibility detail:** what exactly counts as "loudly written to that server's
   audit log" if the server has not configured logging yet?
7. **Moderation envelope confirmation:** does the one-hour spot-check need to validate only timeout,
   or one example from warn/timeout/kick/ban?
8. **Prompt A/B report status:** should open PR #1691 be treated as pending input only, or can its
   findings be used before merge?
9. **CUT-3 rollback window:** what is rollback window `N` after real-token swap?
10. **G-22 staging lanes:** standardize staging lanes into one model, or bless multiple lanes?

## 6. Items safe to carry forward unchanged

- **S-1 engine/declaration/seam standard.** The rule is clear, owner-decided, and directly prevents
  duplicate systems by requiring one engine per domain, declarations as data, leaf handlers, no
  call-site identity branching, and second-consumer discipline.
- **S-2 foundation-before-consumer ordering.** The engine-class vs peer-class split is clear and
  correctly preserves mining-last while fixing welcome/card-engine order.
- **Shared-verb command naming rule.** The rule is mechanical, corpus-based, and avoids retroactive
  rename risk by computing the shared-verb set once.
- **Four-rung invocation ladder as concept.** Exact, fuzzy, NL intent, and NL orchestration are well
  separated by determinism and AI dependency, and the deterministic-first guarantee is clear.
- **Moderator actions as declarative envelopes.** The decision is clear and aligns with S-1 and
  testability; only the confirmation spot-check needs artifact routing.
- **Bot-owner global override, with audit transparency.** The owner requirement is clear; only
  fallback audit routing needs detail.
- **Unified help hub with admin as gated node.** The concept is clean and prevents duplicate
  player/operator trees.
- **Back/Home navigation contract.** The framework-injected model is strong and should not be
  weakened into per-panel discipline.
- **Critical-review rubric classes.** The ten-class rubric is comprehensive enough for Stage 2 and
  Phase B, and correctly distinguishes human probes from mechanizable checkers.
- **Prompt A/B conceptual split.** The split is useful and mostly non-overlapping; only
  restart-safety and fuzzy/suggestion seams need explicit handoff wording.

## 7. Items that should block Stage 2 / Stage 3 / Gate-0 until clarified

### Block Stage 2

- **Preset exclusion semantics** must be answered before assigning preset membership or hub
  placement because hidden vs disabled changes command availability.
- **Shared-verb command registry artifact** must be named and produced before per-subsystem command
  names are considered final.
- **Hub bucket finalization process** must be locked enough that Stage-2 placement does not churn
  across multiple bucket vocabularies.

### Block Stage 3

- **D-5 triage verdicts for all 43 rows** must exist before consolidation.
- **CUT-3 rollback window `N`** must be set before final consolidation because it affects migration
  and cutover acceptance.
- **Prompt A/B findings reconciliation** should wait for PR #1691 or explicitly mark Prompt B
  findings as pending.

### Block Gate-0

- **Authority model vocabulary mismatch** must be resolved before compiler/manifest grammar freezes.
- **C-1 resolver contract** must be frozen enough that all invocation rungs, authority, validation,
  cooldowns, and audit converge through one path.
- **C-2 draft pipeline contract** must be frozen enough to prevent separate AI, setup, and
  destructive-confirm pipelines.
- **ModerationActionSpec envelope spot-check** must be recorded before grammar freeze.
- **K<->L crosswalk / canonical build vocabulary** must be added because the docs already identify
  dual numbering as a recurring confusion cost.
- **Welcome reorder** must be folded into the build-order table or explicitly listed as a superseding
  delta to the frozen plan.

# Opus 4.8 ultracode — the foundational-DESIGN overnight session (brief)

> **Status:** `plan` — **preparation only** (owner-directed). A single paste-ready **Opus 4.8
> ultracode** prompt for an **overnight foundational-*design*** session. Its job: take the ~10
> foundational **kernel functions** that were *audited* (audit A/B) and *judged* (the Fable-5
> final judgment) but **never designed**, design each to **buildable depth**; close the
> **never-surfaced foundational concerns**; and **surface every remaining question/decision** into
> one register. **Not launched from this preparing session** — the owner pastes it into a fresh
> Opus 4.8 (max reasoning) ultracode session. Source wins over any doc (Q-0120).
>
> **Grounding:** the per-function map in the Appendix was built this session by a 13-agent workflow
> that re-checked each function's current state + seams against **shipped source** (Q-0120), so the
> prompt points the overnight run at *real* files — not memory. (It carries the judgment's
> correction: there is **no** `WorkflowResult`/`disbot/core/contracts.py:48-52` — that name is
> design-spec-only; the shipped dispatch-result analogue is **`StageResult`** at
> `disbot/core/runtime/message_pipeline.py:181`.)
>
> **▶ EXECUTED 2026-07-04 (PR #1708).** The deliverable lands under
> [`docs/analysis/rebuild-discovery/foundations/design/`](../analysis/rebuild-discovery/foundations/design/README.md)
> — 14 buildable specs (3 strands) + the frozen [`shared-vocabulary.md`](../analysis/rebuild-discovery/foundations/design/shared-vocabulary.md),
> the [seam-consistency matrix](../analysis/rebuild-discovery/foundations/design/seam-consistency-matrix.md),
> the V-3 [retirement-coverage map](../analysis/rebuild-discovery/foundations/design/retirement-coverage-map.md)
> (96 rows, **0 evaporations**), and the 31-decision
> [question register](../analysis/rebuild-discovery/foundations/design/question-register.md).

---

## ⚡ Quick launch (paste into a fresh Opus 4.8, max-reasoning, ultracode session)

```text
ultracode: Read docs/planning/rebuild-foundational-design-opus-brief-2026-07-03.md in full — execute its "THE PROMPT" section verbatim, using its Appendix (the grounded per-function map) as your design work-list.
```

*(The full prompt is below; the launcher just saves pasting it. Set the session to Opus 4.8 at max
reasoning before launching.)*

---

## What this session is (and is not)

We have **audited** the foundation exhaustively (audit A: 35 runtime mechanics / 246 issues; audit
B: 46 presentation mechanics / 220 findings) and **judged** it (the Fable-5 capstone: verdict, master
ledger L-1…L-25, the 17 surviving gaps, the tiered owner queue). The judgment's one-line diagnosis:
the foundation is **engine-rich, grammar-thin, oracle-empty** — the functions *exist as issues* but
**no buildable design exists for a single one of the kernel engines.** This session closes that: it
is the **design bridge from AUDITED → Gate-0 / L0-plannable.**

- It is a **DESIGN + question-surfacing** session — it *designs the kernel functions to buildable
  depth* and *surfaces every remaining decision*. It is **NOT a fourth audit** (the how-now facts
  already exist — they are the work-list) and **NOT the Stage-2 subsystem walk** (that owner-led
  pass decides the 43 subsystems' *surface content*; this session designs the kernel *underneath*
  it, which is largely independent of command names — "sequential on the spine, parallel on the
  leaves").
- **Why it can run ahead of / parallel to Stage 2:** the kernel spine is exactly what must freeze
  first (S-1/S-2 — decide the recurring method once; foundation before consumer). The 43 subsystem
  rows all *consume* the compiler/resolver/pipeline; designing those engines now de-risks the walk.

## The design work-list — 10 functions + 5 concerns

**The kernel functions (audited, never designed):** ① the manifest compiler + committed snapshot
(the linchpin) · ② the C-1 resolver (one chokepoint for all four rungs **and** panel/component
actions) · ③ the dispatch error/failure envelope · ④ the C-2 draft/preview/confirm/apply pipeline
(producer-agnostic) · ⑤ the workflow / compound-op engine · ⑥ the event outbox / durable delivery ·
⑦ the durable scheduler / due-queue + versioned-state policy · ⑧ the K1 namespace registry · ⑨ the
authority engine (`authority_ref` + owner override) · ⑩ the ops kernel (ConfigSpec, DB-down posture,
migrations, metrics, readiness, the data-plane rail).

**The never-surfaced concerns (no owner, no plan):** security/abuse + the missing rubric classes ·
production-data integrity/repair · credential lifecycle · backup/DR + rollback-data disposition ·
Discord platform-governance (verification + intent approval + per-guild permission overrides).

---

## THE PROMPT — foundational design (paste as its own Opus 4.8 ultracode session)

```text
ultracode: You are Opus 4.8 at maximum reasoning, running an overnight FOUNDATIONAL-DESIGN session for the SuperBot rebuild. Everything on this project has been exhaustively AUDITED (audit A #1690, audit B #1691) and JUDGED (the Fable-5 capstone #1701). Your job is the missing next step: DESIGN the ~10 foundational kernel functions those passes found "audited but never designed" to BUILDABLE depth, CLOSE the never-surfaced foundational concerns, and SURFACE every remaining decision into one register. This is a DESIGN + QUESTION-SURFACING session — NOT a fourth audit, NOT the Stage-2 subsystem walk, NO code. Follow .claude/CLAUDE.md: claim your lane in docs/owner/claims/ first, open a born-red session-card PR immediately, let it auto-merge on green. SOURCE WINS on facts (Q-0120).

READ FIRST (the work-list is already discovered + cited — consume it, do not re-discover):
- The judgment (your master work-list): docs/analysis/rebuild-discovery/foundations/final-judgment-fable5-2026-07-03.md — §2 ledger L-1…L-25 (each row = a function's gap + its source seam), §4 the 17 surviving gaps, §6 the tiered owner queue (Tier-2 = the contract forks you design against their recommended default; Tier-3 = batch-blessable), §8 the decision amendments + rubric classes 11-13.
- The two audits (the how-now inventories, already cited): docs/analysis/rebuild-discovery/foundations/runtime-logic-mechanics-2026-07-03.md (engine room) and presentation-verification-mechanics-2026-07-03.md (surface+proving).
- The frozen grammar you design INTO: docs/planning/rebuild-design-spec-2026-07-02.md (esp. §2 manifest/compiler, §2.7 result grammar, §3 namespace, §5 cutover, §9 build order K0-K10, §10.2/§10.3 ratification + operational contracts).
- The frozen decisions you design AGAINST (never re-litigate): the Phase-A logs (rebuild-stage1-global-review, rebuild-conventions-invocation-authority, rebuild-hub-navigation-presets, rebuild-critical-review-rubric) and router Q-0219…Q-0237 — including the 7 Tier-1 owner answers Q-0237(a-g), which are DECIDED inputs.
- Owner-originated capabilities to design the seams FOR: docs/ideas/rebuild-release-testing-loop-2026-07-03.md (the test-mode approve button plugs into your C-2 pipeline + verified_live) and rebuild-websites-cutover-role-2026-07-03.md.
- The grounded per-function map: the Appendix of THIS brief (docs/planning/rebuild-foundational-design-opus-brief-2026-07-03.md) — for each of the 10 functions + 5 concerns it gives the verified current-state, the undesigned gap (your actual work), the exact seams to define, the read-list of real source paths, and the open questions to surface. START each function's design from its Appendix entry.

SCOPE — IN:
Design to BUILDABLE (Phase-B "100%-complete") depth — a fresh agent could build it from your design + the frozen upstream contracts making ZERO further design decisions — each of:
① COMPILER + snapshot + amendment registry (the linchpin): the ordered validation-pass pipeline, the manifest.snapshot.json schema (sorted keys/stable-hash/callable→ref serialization), the ref-table resolution contract, the THREE-WAY parity oracle (snapshot ⇄ built-runtime ⇄ Discord-remote, reusing command_tree_sync's local/remote path-set diff), all failure modes (compile-error/drift/collision/runtime≠snapshot → CI-red or pre-boot FAILED_STARTUP), the store-completeness reconciliation (dropped StoreSpec = owner-gated, not silent), and the committed rebuild-amendments.yml + uniqueness checker (build BEFORE Gate-0 folds G-9…G-24).
② RESOLVER (C-1): the single resolve(ResolveRequest)->Result chokepoint every rung AND panel/component action funnels through; the surface-agnostic ResolveRequest shape; the per-rung adapter contract (incl. the net-new AI rung 3/4 adapter that turns a next_command string into (command,args)); the fixed order of authority→validate→cooldown→audit→dispatch and where the 3s defer/ack sits; and the fix for the shipped slash-skips-subsystem-visibility drift.
③ ERROR ENVELOPE: from_exception(exc)->Result with the exception→{user_error,denied,transient,bug}+retryable mapping table, user_message derivation, the tree.error/on_app_command_error registration (0 exist today over 31 slash cmds), built on the REAL StageResult (message_pipeline.py:181), retiring the wizard-only recovery_context_from_exception.
④ DRAFT PIPELINE (C-2): the producer-agnostic batch primitive keyed (producer, owner_scope, draft_id) replacing today's per-guild SINGLETON store (which makes "10 D&D channels" unrepresentable and destructively merges two producers); the preview provider slot (fail-closed: no adapter ⇒ un-draftable); the Accept-authority derivation for non-setup producers; and the plug-point for the owner's test-mode explain-then-approve / verified_live button.
⑤ WORKFLOW ENGINE (K7): the LegSpec/CompoundOpSpec + engine entry contract (declared legs, one txn, one central audit row with mutation_id), the dry-run/simulation oracle, farm-collect as the named canary, replacing ~48 hand-rolled txn sites.
⑥ OUTBOX (T2-3): EventSpec.delivery{best_effort,at_least_once} + the in-txn outbox StoreSpec (schema/dedup-key/relay-poll) so audit + reward survive the commit→emit gap; the relay's exactly-once vs handler-dedup contract under the merge=deploy dual-instance window.
⑦ SCHEDULER/STATE (T2-6/T2-7): ManagedTaskSpec durability/misfire/catch-up fields + one kernel durable due-queue (schema, claim/lease, boot-reconcile fires-overdue-exactly-once) for restart-safety; and the StoreSpec payload-version-mismatch policy {upcast,reject_and_preserve,drop} defaulting reject-and-preserve (refund-before-delete) for money/audit — which also generalizes the #1693 fix to the STILL-LIVE RPS forfeit (L-1).
⑧ K1 NAMESPACE REGISTRY: the compile/CI/pre-boot reservation lifecycle, computed from the LIVE ledger walk (NOT the ground-truth JSON — 1-vs-11 shared verbs), cap budget (100 top-level/25 sub/1 nest) baked in, nav-node deep-link commands enumerated INTO the corpus first, runtime is_reserved() for custom triggers, ban/tombstone-as-reservation.
⑨ AUTHORITY: the one authority_ref → (config-lane capability_required / domain-lane audience_tier) resolution table + ADMINISTRATOR-floor semantics; owner override applied ONCE at the top of the resolver across permission+capability+channel-access (fixing the L-12 non-bootstrap deny); the transparency-audit trigger/sink/no-log-channel fallback; member-guilds-only wording; retiring the 5 duplicated _check_admin seams.
⑩ OPS KERNEL: ConfigSpec/SecretSpec (required-vs-defaulted, fail_fast/degrade/dormant, one boolean grammar) + boot-preflight; the DB-down refuse-with-notice posture at the adapter; pool command_timeout/validate-or-reacquire; the migration checksum + numbering CI gate; MetricSpec (declare the 46 families); the readiness/drain contract; and the 4th DATA-PLANE RAIL (refuse boot on any DSN not declared `test`, L-10) + fast-release-plus-idempotency-keys deploy handoff (T2-2 — the real fix the #1693 stopgap can't reach).
Then CLOSE to design depth the never-surfaced CONCERNS: (a) security/abuse posture + rubric classes 11 (cost/quota/abuse), 12 (privacy/retention/erasure), 13 (security/non-functional) + one adversarial-abuse pass design; (b) production-data integrity/repair (a live invariant-sweep/repair mechanic; CUT-2 must not inherit corrupt rows); (c) credential lifecycle (rotation/revocation/compromise-recovery for token/DSN/Railway, minimal recovery arm not reintroducing owner-dependency); (d) backup/DR surviving cutover + rollback-data disposition + verified-restore gate; (e) Discord platform-governance (the ~100-guild verification cap, discretionary message_content approval, per-guild slash-permission overrides invisible to the import). For each: failure/threat model → design response → landing site (Gate-0 grammar field / kernel rail / CUT-stage gate) → owner-gated?

SCOPE — OUT (hard fences):
- NOT a fourth audit — do not run a per-mechanic "how is it done now" fan-out; the 466 findings are the input, not something to rediscover.
- NOT the Stage-2 subsystem walk — no per-subsystem command naming, no keep/merge/drop of the 271 commands, no prefix-vs-slash-per-surface, no hub topology. If you're writing per-subsystem rows, you've drifted.
- NO CODE (docs-only), NOT the new-repo bootstrap / MIGRATION plan.
- Do NOT re-decide the 7 Tier-1 answers (Q-0237 a-g are RESOLVED) or re-litigate any frozen Q-0219…Q-0237 (you may FLAG one with evidence, never reverse).
- Do NOT decide owner-gated calls — design against the recommended default and flag; surface the genuinely owner-only rows (rollback-data disposition, old-bot change-policy, credential-custody) as options+recommendation only.

METHOD (make the workflow do this — design, not re-discover):
1. INGEST the ledgers as the work-list (FJ §2/§4/§6/§8 + the two audits' how-now + the Appendix map).
2. SPOT-VERIFY only the 2-3 load-bearing seams each design builds ON before building on them (as this prep confirmed StageResult and the absence of contracts.py) — do not re-verify the whole ledger.
3. FAN OUT one design agent per function → a buildable design spec built to the recommended-default of any owner-gated fork, flagging the fork.
4. ADVERSARIAL-COMPLETENESS critic per spec (the Phase-B "find one open design decision" reviewer, applied pre-emptively): a found-decision means the spec isn't done → close it by design or push it to the register.
5. SEAM-CONSISTENCY pass across all ten — the reason one session beats ten isolated Phase-B plans: freeze ONE shared vocabulary (the error-envelope shape, the idempotency-key contract, authority_ref, EventSpec.delivery, the audit-row semantics, the restart-safety pattern) that recurs across resolver/panel/draft/workflow/outbox, and a matrix proving they agree. This is S-1 "decide the recurring method once."
6. CROSS-CUTTING CONCERNS strand — threat/failure model → design → landing site → owner-gated, per concern.
7. HARVEST every unclosable decision into ONE numbered question register; loop the critic until two rounds add nothing, ROTATING lenses (the judgment hit its round cap still finding things — don't trust a single dry round).

DELIVERABLE — land under docs/analysis/rebuild-discovery/foundations/ (same home as the audits), organized as three strands under one synthesis (not one monolith, not ten flat files):
- STRAND 1 (the L0/kernel spine — freeze the shared vocabulary first): compiler · resolver+error-envelope · K1 · authority · ops-kernel/rails.
- STRAND 2 (runtime-durability under merge=deploy, built ON strand-1's frozen contracts): draft-pipeline · workflow-engine · outbox · scheduler/state.
- STRAND 3 (the cross-cutting concerns dossier): security/abuse · data-integrity · credentials · backup-DR/rollback · platform-governance.
Plus two cross-strand artifacts: the SEAM-CONSISTENCY MATRIX and the single CONSOLIDATED QUESTION REGISTER. Each function spec uses the Phase-B plan shape: files/modules it becomes · the COMPLETE public contract (every function/field/error) · provides/consumes · data model + migration/index shape · restart & merge=deploy behavior · architectural rules honored (INV / layer-boundary cites) · options+decision+why · labeled deferrals · which FJ L-rows / owner-queue items it RETIRES (the V-3 findings-closure binding — nothing evaporates) · build order. Front-matter README: what got designed, what stayed open, and the design→L-row/owner-queue retirement map. The question register: every decision numbered, each with options + recommendation + owning-spec + Tier + owner-gated?.

GUARDRAILS: SOURCE WINS (Q-0120) — spot-verify load-bearing seams, correct any mis-cite. Design AGAINST the frozen Q-0219…Q-0237 (flag-not-reverse). Owner-gated = options+recommendation, not a decision. Docs-only. Completeness is bounded by the capability corpus (43 subsystems + named amendments + known-options), not open-ended speculation — label every deferral with its reason. Do NOT pad (Q-0089 bar): if a function is already adequately specified by the design spec, say so and spend the budget on the genuinely-undesigned functions + the never-surfaced concerns. Output must be owner-consumable (option+recommendation rows, not prose walls). Position the deliverable as the design bridge feeding the Gate-0 grammar freeze and the Phase-B L0 plan.
```

---

## Appendix — the grounded per-function map (the overnight session's work-list)

Built this session against shipped source (Q-0120). For each function: **current state** (verified) ·
**undesigned gap** (the design work) · **seams to define** · **read** (real paths) · **open Qs**
(🔒 = owner-gated). Full detail in the two audits + the judgment; this is the design-start index.

### Strand 1 — the L0/kernel spine

**① Manifest compiler + snapshot + amendment registry (the linchpin).**
*Current:* no compiler, no on-disk snapshot (`tools/manifest_compile.py` and `*.snapshot.json`
absent — verified); the spine runs BACKWARD — commands/panels are *reflected* from the live runtime
(`command_manifest.py:176-207`, `panel_manifest.py:162-204`), `SubsystemSchema` declares only
settings/bindings/resources (`subsystem_schema.py:270-276`); the only snapshot→remote mechanism is a
path SET-DIFF (`command_tree_sync.auto_sync_if_changed`, not a hash). *Decided:* the hybrid format
is frozen (design-spec §2.0 — dataclasses author, committed `manifest.snapshot.json` interchange,
`.lock.json` layout overlays); `SubsystemManifest` extends `SubsystemSchema`; G-1…G-6 ratified.
*Gap:* (1) the ordered validation-pass pipeline (prose today); (2) the manifest→discord.py
generation + inverse "runtime matches manifest" boot gate (the literal "is there a compiler" gap),
wired to the existing sync-diff as a three-way parity story; (3) the amendment registry as sole
minting authority (filed-not-built). *Read:* `command_manifest.py:112-207` · `panel_manifest.py` ·
`manifest_reconciliation.py:21-27` · `command_tree_sync.py:96-140` · `bot1.py:1180-1249` ·
design-spec §2. *Open Qs:* none new — design work, not owner calls.

**② The C-1 resolver.**
*Current:* nearest central seam is `command_access.resolve_command_access` (channel-access only);
slash admission `_slash_access_check` skips subsystem-visibility (verified drift); panel/component
actions run a SECOND path (`interaction_router.dispatch:104-166`) with **no cooldown field**; AI
rungs execute nothing (`next_command` is a string). *Gap:* the single `resolve(ResolveRequest)`
function (no signature/module/input exists), the surface-agnostic input, the per-rung adapters (incl.
net-new AI), the fixed authority→validate→cooldown→audit→dispatch order + defer placement.
*Read:* `command_access.py:256,340-410` · `bootstrap_access_cog.py:185-300` ·
`interaction_router.py:104-166` · `message_pipeline.py:181` (StageResult) · audit A §C-1.
*Open Qs:* 🔒 do panels route through C-1 or does PanelActionSpec gain its own cooldown/audit
(grammar fork, L-5)? · 🔒 owner-override scope (member-guilds vs any) + where in resolver order? ·
🔒 audit at dispatch-time vs per-mutation? · arch: exact ResolveRequest fields + AI adapter; the
fixed order + from_exception shape; CooldownSpec vs the AI throttle as distinct axes.

**③ The dispatch error/failure envelope.**
*Current:* **zero** `on_app_command_error`/`tree.error` over 31 slash commands; 4 divergent postures;
the shipped result type is `StageResult` (`message_pipeline.py:181`) with no classifier; a
wizard-only `recovery_context_from_exception` (`recovery.py:457`). *Gap:* `from_exception` with the
exception→{user_error,denied,transient,bug}+retryable table + user_message derivation; the §2.7
outcome vocab is frozen (SUCCESS/PARTIAL/BLOCKED/DECLINED/DISCORD_FAILED) so map INTO it; register
`tree.error`. *Read:* `services/lifecycle/contracts.py:40-77` · `message_pipeline.py:181,288-296` ·
`bot1.py:490` · `interaction_router.py:212-230` · design-spec §2.7 (768-807). *Open Qs:* none new —
but co-owned with ②'s envelope-order fork.

**⑧ The K1 namespace registry.**
*Current:* no pre-boot registry — a second name claimant raises `CommandRegistrationError` at
`add_cog` and crash-loops boot; only reservation today is `_RESERVED_CAPABILITY_PREFIXES`; the
post-load ledger is blind to load-time collisions. *Decided:* design-spec §3 covers the
compile/CI/boot reservation lifecycle; Q-0224 + Q-0237(e/f) (slash-common+prefix-long-tail, decided
deep-link names). *Gap:* runtime `is_reserved()` for custom triggers; (kind,parent-group) scoping;
one shared CI↔pre-boot oracle; cap budget (100/25/1-nest) baked in; nav-node commands enumerated
into the corpus BEFORE the shared-verb computation; compute from the LIVE ledger (not the JSON —
1-vs-11). *Read:* audit A §K1/§naming · conventions §1 · design-spec §3 (1038-1155) ·
`command-surface.json` (verify flat-only) · `subsystem_registry.py:1244-1250` · `bot1.py:697-735`.

**⑨ The authority engine.**
*Current:* owner override is bootstrap-only bypass (`command_access.py:351`), denies owner
non-bootstrap commands (L-12); member-guild invariant (`capability.py:98-113`); ~11 override seams +
5 duplicated `_check_admin`; two mutually-exclusive lanes (`capability_required`/`audience_tier`).
*Decided:* Q-0227 + Q-0237(d) one `authority_ref`. *Gap:* the `authority_ref`→two-lane resolution
table + ADMINISTRATOR-floor; override once at top across all axes; transparency-audit
trigger/sink/fallback. *Read:* `config.py:46-73` · `command_access.py:340-410` ·
`capability.py:85-165` · `governance/resolver.py:223`,`execution.py:125-171` · `permission_checks.py`.
*Open Qs:* 🔒 override scope (member vs any); 🔒 transparency trigger/sink/no-log-channel fallback;
🔒 confirm empty-capability⇒ADMIN-floor + lanes stay mutually exclusive; arch: panels through the
same resolver; retire the 5 `_check_admin` + fold channel-access.

**⑩ The ops kernel (ConfigSpec · DB-down · migrations · metrics · readiness · data-plane rail).**
*Current:* no ConfigSpec (~8 ad-hoc env parsers, token fail-fast at import, DSN fail-fast at
`db.init`); pool has no `command_timeout`; migration ledger no checksum; 46 hand-authored metric
families; `/ready` has no consumer; single-process ADR-001 not carried forward; readiness is
DB-blind. *Gap:* ConfigSpec/SecretSpec + boot-preflight; DB-down refuse-with-notice at the adapter;
pool timeout/validate-or-reacquire; migration checksum + numbering CI gate; MetricSpec; the 4th
DATA-PLANE RAIL (refuse boot on non-`test` DSN, L-10); fast-release+idempotency-keys handoff (T2-2).
*Read:* audit A §config/§DB-pool/§migrations/§metrics/§readiness/§sharding · `config.py` ·
`pool.py:40-72` · `migrations.py:53,136-143` · `metrics.py` · `healthserver.py` · `lifecycle.py:182-188`.

### Strand 2 — runtime-durability under merge=deploy

**④ The C-2 draft/preview/confirm/apply pipeline.**
*Current:* the shipped draft store is a **per-guild singleton** — no `draft_id`/producer column,
slot-key collapse — so two producers destructively merge and the flagship "10 `create_channel`"
draft is **unrepresentable** (10 ops → 1 row); Accept gate hard-wired to setup-admin
(`final_review.py:86-93`); apply is non-atomic (`:659-701`); a built read-only `preflight_operations`
diff has **zero consumers**. *Gap:* the producer-agnostic primitive keyed (producer,owner_scope,
draft_id); the fail-closed preview-provider slot; Accept-authority for non-setup producers; the
owner test-mode approve/verified_live plug-point. *Read:* `utils/db/setup_draft.py` (whole) ·
`services/setup_operations.py:194,362,803,1073` · `final_review.py:60-94,659-748` · `audit_events.py:52` ·
`test_pipeline_audit_wiring.py:24` · audit A §C-2 + §composition · conventions §2.4/§4/§6.
*Open Qs:* 🔒 what "atomic apply" means for Discord-resource creates (D-1..D-6 seam); 🔒 one audit
row vs N per compound apply; 🔒 test-mode audience (owner/admin/community → PII policy); 🔒 non-setup
Accept authority + owner-override-in-another-server; arch: wire `preflight` as preview or delete;
build-now on the shipped seam vs deferred behind C-1.

**⑤ The workflow / compound-op engine (K7).**
*Current:* ~48 hand-rolled `db.transaction()` sites; no LegSpec/CompoundOpSpec/engine entry exists;
farm-collect audits only the coin leg; `automation_executor` is the only dry-run precedent.
*Gap:* the LegSpec + engine-entry contract (declared legs, one txn, one central audit row w/
`mutation_id`), the dry-run/simulation oracle, farm-collect as canary. *Read:* `pool.py:117-182` ·
`farm_workflow.py:114-179` · `mining_workflow.py:1324-1358` · `shop_purchase_workflow.py:60-98` ·
`economy_service.py:167-257` · `audit_events.py:1-99` · `automation_executor.py:1-35`.
*Open Qs:* none new — but inherits ④'s "atomic" + audit-row-granularity forks.

**⑥ The event outbox / durable delivery.**
*Current:* commit-then-emit **outside** the txn (`settings_mutation.py:338` commit / `:385` emit);
"DB state correct, event lost" is a log line (`audit_events.py`); `EventBus` is publish-accepted
in-process; catalogue guards names only; `EventSpec` has no delivery field. *Gap:* `EventSpec.delivery`
+ the in-txn outbox StoreSpec (schema/dedup-key/relay-poll); the exactly-once-relay vs handler-dedup
contract under the dual-instance window. *Read:* audit A §outbox/§event-bus · `core/events.py:52-168` ·
`events_catalogue.py:22-49` · `pool.py:153-182` · `audit_events.py:52-99` · `settings_mutation.py:334-405` ·
`xp_service.py:120-140`. *Open Qs:* 🔒 default tier + exactly which events → at_least_once (audit +
reward only, or broader?); 🔒 is restart-safe audit/reward wanted at all given frequent restarts, or
is best-effort-lossy accepted? 🔒 co-decide with T2-2 (idempotency keys) + T2-7 (refund-before-delete)
as one durability contract? arch: exactly-once-relay sufficiency; emit-time payload validation in v1?

**⑦ The durable scheduler / due-queue + versioned-state policy.**
*Current:* the only durable poller (`automation_scheduler`, persisted `next_run_at`) defaults OFF and
its spawn is inert; one-shot timers are in-memory (`rps_tournament_cog`, `blackjack_cog`), lost every
deploy; `game_state_service.save()` delegates drop-vs-resume to cogs (no upcast primitive); **the RPS
version-mismatch forfeit is STILL LIVE** (`rps_tournament/_persistence.py:104-115`, L-1 — the #1693
fix covered only blackjack). *Gap:* ManagedTaskSpec durability/misfire/catch-up + one kernel
due-queue (schema/claim-lease/boot-reconcile-exactly-once); the StoreSpec payload-version policy
{upcast, reject_and_preserve, drop} defaulting reject-and-preserve (refund-before-delete) for
money/audit. *Read:* `automation_scheduler.py:135-397` · `utils/db/automation.py:178` ·
`rps_tournament/_persistence.py:104-270` · `blackjack_cog.py:170-300` · `game_state_service.py:60-72` ·
`game_state_cleanup.py:52-72`. *Open Qs:* none new — but T2-7's default is an owner-flagged row.

### Strand 3 — the never-surfaced cross-cutting concerns

**(a) Security/abuse + the missing rubric classes.** No security review anywhere; the 10-class rubric
has no security/non-functional class → the blindness self-propagates into Stage 2 + Gate-V. *Design:*
rubric classes 11 (cost/quota/abuse), 12 (privacy/retention/erasure), 13 (security/non-functional) in
the exact shape of the existing 10; one adversarial-abuse pass (owner/input/output-binding).
*Read:* rubric doc:36-143 · FJ §2 L-19 + §8 · audit B §8 (no-non-functional-class row).
*Open Qs:* 🔒 adopt 11/12/13 as-proposed or a different cut; retroactive to frozen Stage-1 or forward
only? · 🔒 who runs the adversarial pass, against what artifact? · arch: pass output→Gate-0 binding.

**(b) Production-data integrity/repair.** Every oracle proves *code*; nothing sweeps/repairs live
*data*; CUT-2 would inherit corrupt rows (e.g. double-XP residue) as ground truth. *Design:* a live
invariant-sweep/repair mechanic + a CUT-2 verify-import step. *Read:* FJ §4 #7 · `rps.../_persistence.py`
(the corrupt-row pattern). *Open Qs:* 🔒 permanent runtime oracle vs one-time migration script; 🔒
verify-import + verified-restore as HARD CUT-3 gates vs advisory.

**(c) Credential lifecycle.** No rotation/revocation/compromise-recovery for token/DSN/Railway, which
Q-0213 deliberately concentrated in agent hands. *Design:* the minimum recovery arm that doesn't
reintroduce owner-dependency. *Read:* `railway-setup-plan-2026-07-02.md:60-90` (Q-0213). *Open Qs:*
🔒 does the owner want a lifecycle contract at all (touches Q-0213); 🔒 supply-chain lockfile +
human-review gate vs the CLAUDE.md Q-0105 "adopt freely" grant (router DISCUSS).

**(d) Backup/DR + rollback-data disposition.** The sole backup is an old-repo, UNVERIFIED, 90-day,
repo-bound workflow that won't follow the new repo; rollback destroys every post-cutover write (no
reverse importer). *Design:* the backup/verified-restore gate ported into the new repo + the
rollback-data disposition. *Read:* `.github/workflows/backup-db.yml:1-60` · design-spec §5.2 (1315-1351) ·
FJ §2 L-18. *Open Qs:* 🔒 rollback-data: reverse-import / replay-log / declared-loss + window N; 🔒
RPO the backup must meet; 🔒 verified-restore a HARD CUT-3 gate?

**(e) Discord platform-governance.** Unverified bots cap ~100 guilds; `message_content` approval is
discretionary; per-guild slash-permission overrides are a second config DB the import can't see.
*Design:* the growth posture (slash-first survivability + intent-denial fallback + a verification
milestone) and a CUT-2 Discord-side permission census. *Read:* `bot1.py:75-78` (hardcoded privileged
intents) · FJ §4 #17, §2 L-17/L-23. *Open Qs:* 🔒 slash-first-ladder-with-fallback vs
pursue-verification-as-a-hard-milestone before opening growth.

---

## Pointers

- The judgment this designs from: [`final-judgment-fable5-2026-07-03.md`](../analysis/rebuild-discovery/foundations/final-judgment-fable5-2026-07-03.md) (verdict · L-1…L-25 · surviving gaps · owner queue).
- The audits it consumes: [runtime/engine-room](../analysis/rebuild-discovery/foundations/runtime-logic-mechanics-2026-07-03.md) · [surface/proving](../analysis/rebuild-discovery/foundations/presentation-verification-mechanics-2026-07-03.md).
- The grammar it designs into: [`rebuild-design-spec-2026-07-02.md`](rebuild-design-spec-2026-07-02.md) (§2/§2.7/§3/§5/§9/§10).
- Decisions it designs against: the Phase-A logs ([stage-1](rebuild-stage1-global-review-2026-07-03.md) · [conventions](rebuild-conventions-invocation-authority-2026-07-03.md) · [hub/nav](rebuild-hub-navigation-presets-2026-07-03.md) · [rubric](rebuild-critical-review-rubric-2026-07-03.md)) + router Q-0219…Q-0237.
- Owner capabilities to design seams for: [release→test→verify loop](../ideas/rebuild-release-testing-loop-2026-07-03.md) · [websites cutover-role](../ideas/rebuild-websites-cutover-role-2026-07-03.md).
- **Next:** the owner launches this in Opus 4.8; its design specs + question register feed the **Gate-0 grammar freeze** and the **Phase-B L0 layer plan** — running on the kernel spine ahead of / parallel to the owner-led Stage-2 subsystem walk.

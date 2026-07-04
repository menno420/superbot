# Gate-0 grammar-freeze work-list — grounded harvest of the 14 design specs

> **Status:** `reference` — **NOT SOURCE OF TRUTH.** A grounded work-list harvested 2026-07-04 from
> the shipped foundational-design specs (Q-0120) to give the **Gate-0 grammar-freeze** ultracode
> session a start index (the companion of
> [`rebuild-gate0-grammar-freeze-opus-brief-2026-07-04.md`](rebuild-gate0-grammar-freeze-opus-brief-2026-07-04.md)).
> The 14 specs win over this doc for any shape they own; the Gate-0 session must re-verify against
> them. Three parts: **(1)** the grammar fold list · **(2)** the register-row disposition · **(3)**
> the Phase-B L0 build order.

---

## Part 1 — the grammar fold list (87 primitives / ~34 field-additions across 18 attach-points)


> shared-vocabulary, for the **Gate-0 grammar freeze** (design-spec §2/§3). Grouped by the manifest spec /
> leaf / kernel primitive each addition attaches to. Role tags: **[S]** hand-authored (sim-frozen) · **[A]**
> arrangement (sim overlay) · **[O]** objective/telemetry · **[DERIVED]** compiler-computed, not authored ·
> **(primitive)** = a type/enum/port/table/fence/facet/marker, not a field on an existing spec.
> Source-of-truth: shipped source & merged PRs win (Q-0120); the owning spec wins for a shape it owns.

---

## GROUP 1 — The routable-spec fields (CommandSpec · PanelActionSpec · SelectorSpec; `authority_ref` spans six types)

| # | Field / primitive | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 1 | `authority_ref` | **04 (K6)** owns; **02 §3.0** pins on the routable specs; **01 P4** validates | `CommandSpec`, `PanelActionSpec`, `SelectorSpec`, `SettingSpec`, `BindingSpec`, `ResourceRequirement` (the six authority-bearing types) | `str` · `""` (⇒ ADMIN floor) · **[S]** | The SOLE authority field; classifies to exactly one `Lane{CAPABILITY,TIER}`; replaces the two-lane `capability_required`+`audience_tier` | **L-13 / T1-4**, Q-0237(d), **RC-2** |
| 2 | `enabled_when` | **02 §3.0** | `CommandSpec`, `PanelActionSpec`, `SelectorSpec` | `PredicateRef` · `""` (constant-true) · **[S]** | Per-guild dispatch-admission gate evaluated at resolver step 2a for every surface (deny ⇒ `DISABLED`) | **T2-9** |
| 3 | `reply_visibility` | **02 §3.0** | `CommandSpec`, `PanelActionSpec`, `SelectorSpec` | `ReplyVisibility \| None` · `None` (⇒ lane default) · **[S]** | Declared success-visibility override read by the ephemerality resolver; distinct from the frozen `result_render` mode | **T2-17** |
| 4 | `defer_mode` | **02 §3.0** | `CommandSpec`, `SelectorSpec` (the *optional* variant; `PanelActionSpec.defer_mode` is already frozen non-optional §2.6) | `DeferMode \| None` · `None` (⇒ surface-derived) · **[S]** | ACK-boundary defer behavior (`auto`/`modal`/`none`) | closes the "CommandSpec has no defer_mode" gap |
| 5 | `cooldown` (`CooldownSpec`) — **the C-1 panel-pipeline + cooldown (L-5)** | **02 §3.2 step 3** reads it; **SF-a option A** homes it on the panel spec | `CommandSpec`, `PanelActionSpec`, `SelectorSpec` | `CooldownSpec{rate, per_s, scope}` · — · **[S]** | Charged at resolver step 3 for **every** surface incl. panel/component actions — closes the panel = second cooldown-free resolver hole | **L-5** (owner-gated fork **SF-a**) |
| 6 | `cost_posture` | **10 class 11** | `CommandSpec` (frozen ref-bearing home; keyed off `effect="external"`) | `CostPosture` · `FREE` · **[S]** (REQUIRED `!= FREE` iff `effect="external"`) | Declares money/rate/compute bound of an external ref; `FAIL_CLOSED` = the media default-OFF rule | **L-16**, T2-15; register **Q-D20** |
| 7 | `quota_ref` | **10 class 11** | `CommandSpec` | `str` · `""` · **[S]** (non-empty REQUIRED for `PER_GUILD_QUOTA`/`BUDGET_CAP`) | Names the K1-reserved spend/rate counter the ref reads before it acts | **L-16** |
| 8 | slash-common / `essential` tag (**D-5**) | **14 §2.A** (materializes the frozen Q-0237(e) slash-common decision) | `CommandSpec` (command-rooted) **or** `PanelActionSpec`/`SelectorSpec` (panel-rooted) — mirrors `authority_ref`'s placement | tag/bool · unset · **[S]** | Marks a mission-essential capability; `check_intent_survival` asserts it has ≥1 interaction-delivered entry point | **L-17** |

**Panel-action riders under SF-a option A (the L-5 structural retirement):**

| # | Field | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 9 | `action_id` | **02 §3.7 / 01 P6 `never_strand`** (SF-a option A) | `PanelActionSpec` | `str` · — · **[S]** | Declares the button↔action binding so `never_strand` becomes a real compile check (was heuristic `DANGLING_PANEL_ACTION`) | **L-5** heuristic reconciler |
| 10 | `mirrors` | **01 P6 `action_cooldown_parity`** (SF-a option A) | `PanelActionSpec` | action↔command ref · — · **[S]** | The action-mirrors-command correspondence the cooldown/audit-parity predicate reads | **L-5** |

---

## GROUP 2 — `ActorRef` + `Surface` (kernel/interaction request primitives)

| # | Field / primitive | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 11 | `ActorRef.actor_type` (F-4, APPLIED) | **02 §3.1**; consumed by 09/11 | `ActorRef` (kernel/interaction) | `str` · `"user"` (`{user, system, backfill, setup_delegate}`) · runtime (no S/A/O) | K7 maps it to `AuthorityRequest.actor_type`; `system`/`backfill` hit `resolve_authority` step-1 scripted-bypass (scheduler/sweep fires) | **RC-18 / F-4** |
| 12 | `ActorRef.member_tier` (RC-12, PENDING on 02) | **04** owns the need; **02** must add | `ActorRef` | `str \| None` · `None` · runtime | Pre-computed 6-tier ladder string the adapter sets via `member_tier_from_member`; the only way the TIER lane resolves staff/mod/admin/owner | **RC-12** (the one non-trivial pending 02 wiring) |
| 13 | `Surface.MAINTENANCE` (F-5, APPLIED) | **02 §3.1** (interaction `Surface`, not the namespace one — RC-11) | `Surface` enum | `= "maintenance"` · (primitive) | The ONE background/headless member; 09 scheduler-fires AND 11 sweep-repairs both classify under it via `from_exception(exc, surface=MAINTENANCE, target=None)` | **RC-19 / F-5**; closes 11 Q4 |

---

## GROUP 3 — The error envelope / dispatch-result grammar (spec 02, `kernel/interaction` + `sb/spec/outcomes.py`)

| # | Field / primitive | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 14 | `from_exception(exc, *, surface, target: TargetRef \| None, section_label=None)` — **T2-4** | **02 §3.3** | `kernel/interaction/errors.py` | function → `ErrorEnvelope` · (primitive) | The one exception classifier; `target` widened to `TargetRef \| None` (RC-19) so headless fires pass `target=None`; retires `recovery_context_from_exception` | **T2-4**, L-4; **RC-19** |
| 15 | `ErrorEnvelope` | **02 §3.3** | `errors.py` | dataclass `{error_class, reason, retryable, user_message[S], log_level, outcome}` · (primitive) | The classified envelope every rung/adapter/K7-leg maps into | **T2-4** |
| 16 | `ErrorClass` | **02 §3.3 / `sb/spec/outcomes.py`** | outcomes leaf | enum `{NONE, USER_ERROR, DENIED, TRANSIENT, BUG}` · (primitive) | The "whose fault" nuance kept OUT of `outcome` (which stays the frozen 5) | **T2-4** |
| 17 | `Result` (dispatch result) | **02 §3.6** | `kernel/interaction/result.py` | dataclass (adds `reply_visibility`, `error_class`, `reason`, `surface`, `workflow`, `audit_emitted`, `request_id`) · (primitive) | The `resolve()` return; copies `WorkflowResult.outcome` through into the §2.7 five | L-4 |
| 18 | `DenialReason` | **02 §3.6 / outcomes leaf** (RC-6 home) | `sb/spec/outcomes.py` | enum 12 members (`ALLOWED, DRAINING, AUTHORITY, DISABLED, VISIBILITY, CHANNEL, USER_ERROR, COOLDOWN, AI_THROTTLE, NOT_FOUND, CONFIRM_DECLINED, DISPATCH_ERROR`) · (primitive) | Machine reason on every Result/envelope; `CHANNEL`+`detail` covers `COMMANDS_DISABLED` | **RC-6** |
| 19 | `ReplyVisibility` | **02 §3.4** | outcomes leaf | enum `{EPHEMERAL, PUBLIC, SILENT}` · (primitive) | The visibility vocab `resolve_reply_visibility` resolves once over all five outcomes | **T2-17** |
| 20 | `DeferMode` | **02 §3.1** | outcomes leaf | enum `{AUTO, MODAL, NONE}` · (primitive) | The ACK-boundary defer vocab | closes the defer-mode gap |
| 21 | `PredicateRef` two-form grammar + `predicates.evaluate` | **02 §3.0** owns; **01 §3.1** reconciles compile handling | `sb/spec/refs.py` + `kernel/interaction/predicates.py` | namespaced string `"<kind>:<key>[=<value>]"` (`kind∈{setting,binding,capability,flag}`) OR registered `{"$ref":"predicate:…"}` · `""`=constant-true · (primitive) | The grammar behind `enabled_when`/`visible_when`; namespaced form is a parsed string, never table-resolved (H4 false-reject fix) | H4; T2-9 support |

---

## GROUP 4 — The authority engine leaf (`sb/spec/authority.py` + `kernel/authority/*`, spec 04)

| # | Field / primitive | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 22 | `Lane` + `TIERS` + `ADMIN_FLOOR_TIER` + `classify_authority_ref` + `validate_authority_ref` + `is_tier_sufficient` | **04** | `sb/spec/authority.py` (dependency-free leaf) | enum `Lane{CAPABILITY, TIER}` + pure fns · (primitive) | Total non-overlapping `authority_ref → lane` classification; `validate_authority_ref` is 01 P4's checker | **L-13/T1-4**, **RC-3** |
| 23 | `AuthorityDecision` (10 fields) | **04 §3.3** owns; **02 imports** (RC-2) | `kernel/authority/decision.py` | dataclass `{allowed, authority_ref, lane, required_tier, member_tier, owner_override, lane_would_deny, reason, detail, denial_message}` · (primitive) | The resolved authority verdict; `override_applied`/`base_allowed` are DERIVED from it | **RC-2** |
| 24 | `AuthorityRequest` (discord-free) | **04 §3.3** | `decision.py` | dataclass `{authority_ref[S], actor_type, user_id, guild_id, is_member, member_tier}` · (primitive) | Carries a PRE-COMPUTED `member_tier` string, never a `discord.Member` | **RC-12** |
| 25 | `ChannelAccessDecision` (8 fields — adds `detail`) | **04 §3.4** (RC-13) | `channel_access.py` | dataclass; `detail ∈ {"", "commands_disabled", "channel_not_allowed"}` · (primitive) | Folded-in channel-access lane honoring the once-computed `owner_override` (L-12 fix) | **L-12**, **RC-13**, **RC-4** |
| 26 | `AccessMode` | **04 §3.4** | `channel_access.py` | enum, SHIPPED value strings `{all_channels, selected_channels, disabled_except_bootstrap}` · (primitive) | Name-stable so `AccessMode(snapshot.mode)` resolves with no migration | — |
| 27 | `denial_message` (engine-generated, NOT `[S]`) | **04 §3.3** (RC-14) | `AuthorityDecision.denial_message` | `str \| None` · `None` on allow · engine-generated (NOT a spec field) | Generic copy per `(lane, reason)`; `from_exception`'s `denied` row reads it | **RC-14** |
| 28 | `owner_override_holds` (the single owner predicate) | **04 §3.3** | `kernel/authority/owner.py` | `(user_id, is_member) -> bool` · (primitive) | Collapses ~11–16 scattered `is_platform_owner` authorizers to one AST-fenced predicate | **L-12** |
| 29 | `TransparencyAudit` + `build_transparency_audit` + `TransparencySink` port | **04 §3.5** (RC-15) | `kernel/authority/transparency.py` | dataclass + fn + Protocol · (primitive) | Owner-override transparency emit — rides the sink port + `command.dispatched` flag, NOT `emit_audit_action` | **T2-10**, **RC-15** |

---

## GROUP 5 — Config / secret grammar + the data-plane rail (spec 05, `sb/spec/config.py`)

| # | Field / primitive | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 30 | `ConfigSpec` / `SecretSpec` grammar | **05 §3.1** | `sb/spec/config.py` | dataclasses `{env_var, type, required, default, posture, owner_subsystem, activation_link, choices, min, redact}` all **[S]** · (primitive) | The ONE typed config registry (`CONFIG_FIELDS`, 47 fields); replaces 39 scattered `os.getenv` | **T2-22** |
| 31 | `ConfigPosture` / `ConfigType` (+`CSV`) / `DataPlane` | **05 §3.1** | config leaf | enums (`FAIL_FAST/DEGRADE/DORMANT`; `STR/INT/FLOAT/BOOL/SECRET/DSN/CSV`; `TEST/PROD`) · (primitive) | Posture-on-absence + coercion type + the plane vocab | **T2-22** |
| 32 | `IntentSpec` + `INTENT_CONTRACT` + `assert_intents` | **05 §3.1/§3.2** | config leaf | dataclass `{name, privileged, required, approval_env}` · (primitive) | The gateway-intent contract (message_content/members) with prod approval-env preflight | **L-17** (intent-rail leg) |
| 33 | **The data-plane rail** `assert_data_plane` + `SB_DATA_PLANE` | **05 §3.5** | `sb/kernel/db/data_plane.py` + `CONFIG_FIELDS` | fn + required `ConfigSpec` (`choices=(test,prod)`, FAIL_FAST) · (primitive) | The 4th kernel rail — non-`test` DSN without prod-attest + prod-worker identity ⇒ `RefuseBoot` before network I/O | **L-10** |
| 34 | 8 new operational `ConfigSpec`s | **05 §3.1** | `CONFIG_FIELDS` | `DB_COMMAND_TIMEOUT_S`(30.0), `DB_IDLE_LIFETIME_S`(300.0), `SB_TEST_DB_HOSTS`(CSV,()), `SB_PROD_ATTEST`(SecretSpec), `RAILWAY_SERVICE_NAME`, `SB_INTENT_MSGCONTENT_OK`(BOOL), `SB_INTENT_MEMBERS_OK`(BOOL) all **[S]** | The operational fields the rails/pool/preflight read | L-10, T2-22 |
| 35 | `SB_VERIFY_BOOT` (the 48th operational field) | **13 §2.2** | `CONFIG_FIELDS` | `BOOL` · `False` · **[S]** (requires `SB_DATA_PLANE=test`) | Side-effect-free verify-boot profile (fake-HTTP, reconcile+relay suppressed) for restore-verify | **L-18** |

---

## GROUP 6 — Observability + migration integrity + idempotency (spec 05)

| # | Field / primitive | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 36 | `MetricSpec` + `MetricKind` + `LabelSpec` | **05 §3.3** | `sb/spec/observability.py` | dataclasses (`LabelSpec{name, domain, max_cardinality}`; `MetricSpec{name, kind, doc, labels, buckets, cardinality_budget[O], owner_subsystem}`) · (primitive) | Declared metric grammar with a cardinality budget CI gate; replaces 46 hand-authored singletons | **T3 A#21** |
| 37 | **Migration checksum** `schema_migrations.checksum` + `verify_applied_checksums` + `MigrationDrift` | **05 §3.6** | `schema_migrations` table + `sb/kernel/db/migrations.py` | `checksum TEXT NOT NULL` column + fn + exc · (primitive) | Immutability gate — an edited applied migration is CI-red / `FAILED_STARTUP` | migration-integrity gap |
| 38 | `IdempotencyKey` contract | **05 §3.7** (T2-2 seed) | `sb/kernel/db/idempotency.py` + `idempotency_keys` table | `IdempotencyKey{namespace, guild_id, dedup_token}` + `PriorOutcome` + `once`/`record_outcome`/`read_outcome` · (primitive) | The exactly-once-over-at-least-once primitive strand-2 outbox+scheduler complete | **T2-2 / L-6** |
| 39 | `guild_count` gauge `MetricSpec` + `~75/90` latched threshold evaluator | **14 §2.C** | `sb/spec/observability.py` + join-listener | `MetricSpec` (gauge) + `platform.guildcap.<t>` latch · (primitive) | Active lead-time signal before the ~100-guild verification wall | **L-17** (growth leg) |

---

## GROUP 7 — Event outbox / delivery grammar (spec 08, K4)

| # | Field / primitive | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 40 | `EventSpec.delivery` | **08 §3.1** | `EventSpec` (design-spec §2.8) | `DeliveryClass` · `BEST_EFFORT` · **[S]** ← NEW | Completes the frozen delivery skeleton; `AT_LEAST_ONCE` ⇒ in-txn outbox row | **T2-3**; vocab §④/⑤ skeleton |
| 41 | `DeliveryClass` — **home = `sb/spec/events.py`** | **08 §12.1** (RC-17 / fork F); **07 imports it** | `sb/spec/events.py` leaf | enum `{AT_LEAST_ONCE, BEST_EFFORT}` · (primitive) | ONE canonical enum so `EventSpec.delivery` and K7 `EventEmitSpec.delivery` never drift | **RC-17** |
| 42 | **The outbox `event_outbox` StoreSpec** | **08 §5.1** | new table + `OUTBOX_STORE` | version-extended `StoreSpec` (`payload_version=1`, `bears_value=False`, `version_policy=REJECT_AND_PRESERVE`, `checkpoint_class=LEDGER`, `sole_writer`, `reader_domains`) · (primitive) | The durable in-txn outbox table + relay/reaper lanes | **L-9** |
| 43 | `correlation_id` column (on `audit_log` AND `event_outbox`) | **08 §5.1 / 07 §5** (RC-16) | `audit_log` + `event_outbox` DDL | `uuid NULL` column · (primitive) | Groups the N audit rows of one draft apply by `ctx.correlation_id = draft_id`; the 11-field bus payload is UNCHANGED | **RC-16**; resolves 06 §12 |
| 44 | `delivery_declared` compile fence + 4 outbox `MetricSpec`s | **08 §3.1/§2** | `manifest-validate` + `sb/kernel/outbox/metrics.py` | fence + `MetricSpec`×4 · (primitive) | `observability_only ⇒ BEST_EFFORT`; effectful `AT_LEAST_ONCE` subscriber must accept the reserved dedup keys | T2-3 |

---

## GROUP 8 — The K7 workflow-engine grammar (spec 07)

| # | Field / primitive | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 45 | `LegSpec` + `LegKind` + `CompoundOpSpec` + `WorkflowLane` | **07 §3.1** | `sb/kernel/workflow/spec.py` | dataclasses/enums; `CompoundOpSpec{op_key, domain, lane, authority_ref, legs, idempotency, dedup_key, audit_verb, …}` all **[S]** (`reversibility` DERIVED) · (primitive) | The one declarative compound-op grammar replacing ~48 hand-rolled multi-leg txn sites | — |
| 46 | `IdempotencyPosture` + `DedupKeySpec` | **07 §3.1** (T2-21) | `CompoundOpSpec.idempotency` / `.dedup_key` | enum `{DURABLE_ONCE, NATURAL_KEY, SINGLE_FLIGHT, NONE_JUSTIFIED}` **[S]** + `DedupKeySpec` · (primitive) | The mandated per-op idempotency declaration + fence (fixes farm-collect double-credit) | **T2-21** |
| 47 | `EventEmitSpec` + `LegAuditSpec` + `EmptyResultSpec` | **07 §3.1** | `CompoundOpSpec.emits` / leg audit / empty-state | dataclasses **[S]** · (primitive) | Post-commit events (imports `DeliveryClass`), per-leg audit enrichment, the no-op predicate | — |
| 48 | `WorkflowContext.correlation_id` | **07 §3.2** (landed; RC-16) | `WorkflowContext` | `str \| None` · `None` · runtime | Set only by ④ (= draft_id); written into the `audit_log.correlation_id` column | **RC-16** |
| 49 | `WorkflowContext.test_mode` (PENDING seam-correction) | **06 §12** flags for **07** | `WorkflowContext` | `bool` · `False` · runtime | Threads draft `verification.test_mode` into each op; suppresses real Discord writes in RELEASE_TEST | 06 §12 seam-correction |
| 50 | `audit_log` central-row spine + the 3 K7 fences | **07 §3.4/§3.6/§5** | `audit_log` table + `compile.py` | 1 row + 1 durable bus event per op; fences `idempotency_posture_declared`, `audit_completeness`, `atomic_db_only` · (primitive) | One central audit row per compound op (completes vocab §③.3); the `atomic_db_only` fence scopes external-conn callers only | **L-9** central trace; ③.4 |

---

## GROUP 9 — The draft pipeline grammar (spec 06, K9)

| # | Field / primitive | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 51 | `sb_drafts` + `sb_draft_operations` StoreSpecs (the multi-op draft primitive) | **06 §3.2/§5** | new tables | keyed `draft_id` PK / ops `(draft_id, op_seq)` PK · (primitive) | Producer-agnostic N-ops-as-N-rows draft (makes the 10-channel draft representable; two producers coexist) | **L-7** |
| 52 | `Producer` / `DraftStatus` / `DraftOperation` / `OwnerScope` / `VerificationContext` | **06 §3.1** | `sb/spec/draft.py` | enums + dataclasses; `DraftOperation{op_seq, op_kind[S], subsystem[S], authority_ref[S], payload, label, dedup_token}` · (primitive) | The draft leaf grammar; `op_kind` is the fail-closed registry key | **L-7** |
| 53 | `OpKindRegistry` + `OpKindBinding` + `DraftPreview`/`DraftConfirmationSpec` | **06 §3.3** | `sb/kernel/draft/*` | `OpKindBinding{op_kind, workflow_ref[S], payload_schema[S], is_resource_create[S]}` · (primitive) | Fail-closed op-kind slot (no binding ⇒ un-draftable) + the batch aggregation of §2.7's single-op shapes | **L-7** |

---

## GROUP 10 — `ManagedTaskSpec` durability/misfire/catch-up (spec 09, `sb/spec/scheduler.py`)

| # | Field / primitive | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 54 | `durability` | **09 §3.1** (T2-6) | `ManagedTaskSpec` | `TaskDurability` · `IN_MEMORY` · **[S]** | `DURABLE` ⇒ persisted in `sb_due_queue` + boot-reconciled | **T2-6 / L-8** |
| 55 | `misfire_policy` | **09 §3.1** | `ManagedTaskSpec` | `MisfirePolicy` · `COALESCE` · **[S]** | Recurring misfire handling `{COALESCE, FIRE_ALL, SKIP}` | **T2-6** |
| 56 | `catch_up` | **09 §3.1** | `ManagedTaskSpec` | `bool` · `True` · **[S]** | Boot-reconcile fires overdue (True) vs re-arm forward (False) | **T2-6 / L-8** |
| 57 | `grace_s` / `max_catchup` | **09 §3.1** | `ManagedTaskSpec` | `int` · `0` / `1` · **[S]** | Late-but-on-time grace window; `FIRE_ALL` thundering-herd cap | **T2-6** |
| 58 | `scope` | **09 §3.1** | `ManagedTaskSpec` | `TaskScope` · `GLOBAL` · **[S]** | Per-guild vs global (guild tasks reclaimed on guild-leave, C-8/T2-8) | T2-8 |
| 59 | `TriggerKind.ONE_SHOT` (+ `OneShot`) + `TaskDurability`/`MisfirePolicy`/`TaskScope`/`ErrorPolicy` enums | **09 §3.1** | `sb/spec/scheduler.py` | enums; `OneShot` trigger · (primitive) | Persists one-shot timers in the due-queue (retires in-memory `asyncio.sleep`) | **L-8** |
| 60 | `sb_due_queue` StoreSpec + `SYSTEM_ACTOR` sentinel + `PollSupervisor`/`PollLane` port | **09 §3.5/§3.6/§3.7** | new table + `sb/kernel/scheduler/*` | durable-timer table + `ActorRef(actor_type="system")` + poll host · (primitive) | The durable due-queue + boot-reconcile-fires-overdue-exactly-once (completes vocab §⑤.5); the shared poll host all lanes register on | **L-8**; vocab §⑤.5 |

---

## GROUP 11 — `StoreSpec` version-extension (spec 09, `sb/spec/versioning.py`)

| # | Field / primitive | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 61 | `payload_version` | **09 §3.2** (T2-7) | version-extended `StoreSpec` | `int` · `1` · **[S]** | The current schema version of the store's payload | **T2-7** |
| 62 | `bears_value` | **09 §3.2** | `StoreSpec` | `bool` · `False` · **[S]** | Money/audit-bearing flag; drives the version fence + rubric/rollback/RPO tiering | **T2-7 / L-1** |
| 63 | `version_policy` | **09 §3.2** | `StoreSpec` | `VersionPolicy` · `REJECT_AND_PRESERVE` · **[S]** | `{UPCAST, REJECT_AND_PRESERVE, DROP}` — the load-time drift disposition (refund-before-delete for value stores) | **L-1** (version-drift leg) |
| 64 | `active_rows_ref` / `retire_ref` / `upcast_ref` / `compensation_ref` | **09 §3.2** | `StoreSpec` | `ProviderRef \| None` / `WorkflowRef \| None` × 3 · `None` · **[S]** (conditionally REQUIRED by fence) | The registered reader + audited retire/upcast/refund seams `resolve_versioned_load` reads/writes through | **L-1** |
| 65 | `VersionPolicy` / `CheckpointClass` enums + `VersionedRow` + `version_policy_declared` fence | **09 §3.2/§3.4** | `sb/spec/versioning.py` + `compile.py` | enums + normalized-row + fence · (primitive) | Makes a value-bearing `DROP` unbuildable (the RPS-forfeit shape) | **L-1** (the RPS forfeit) |

---

## GROUP 12 — `StoreSpec` privacy fields + rubric class 12 + the member-erasure executor (spec 10)

| # | Field / primitive | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 66 | `data_class` | **10 class 12** | `StoreSpec` (additive) | `DataClass` · `NONE` (`{NONE, MEMBER_ID, MEMBER_PII}`) · **[S]** | The PII discriminator `check_data_lifecycle` keys on | rubric class 12; **A#15** |
| 67 | `erasure_ref` | **10 class 12** | `StoreSpec` | `WorkflowRef \| None` · `None` (REQUIRED iff `data_class != NONE`) · **[S]** | The audited (K7) member-erasure hook; a bare `HandlerRef` is a `SEMANTIC_VIOLATION` | **FJ §4 #11** (in-DB leg) |
| 68 | `cache_scope` | **10 class 12** | `StoreSpec` | `CacheScope \| None` · `None` (member-data cache MUST be GUILD) · **[S]** | Closes cross-guild cache bleed (B#34) by construction | **B#34 / X-3** |
| 69 | `DataClass`/`CacheScope` enums + `check_data_lifecycle` gate + member-erasure executor (`sb/kernel/privacy/erasure.py`) | **10 §2.A** | new leaf/gate/executor | enums + fence + `run_erasure`/`ErasureTrigger`/`ErasureDisposition` · (primitive) | Machine-complete member-data walk (enumerate registry slice · DELETE non-value / TOMBSTONE value · prove-complete) | rubric class 12; **R-1/R-2** |

---

## GROUP 13 — `StoreSpec.rollback_class` + cutover marker + backup/DR (spec 13)

| # | Field / primitive | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 70 | `rollback_class` | **13 §2.4b** | 09's version-extended `StoreSpec` (sibling of `bears_value`) | `RollbackClass` · **[DERIVED]** by the compiler (except the `REPLAY_INTENT` owner override) | Mechanically classifies a store's rollback disposition from `forward_map_kind` + `bears_value` | **L-18 / FJ §4 #2** |
| 71 | `RollbackClass` + `forward_map_kind` (ForwardMapKind) enums | **13 §2.4b** | `sb/spec/versioning.py` + importer alias map | `{REVERSE_IMPORTABLE, DECLARED_LOSS, REPLAY_INTENT}` + `{NAME_STABLE, RENAME, COLLAPSE, NEW_ONLY, DROP}` · (primitive) | The invertibility inputs; only invertible-∧-value-bearing stores round-trip on rollback | **T-4/T-5**; register **Q-D15** |
| 72 | `cutover_flip_ts` marker | **13 §2.4a** | `settings_keys.CUTOVER_FLIP_TS` (global) or `sb_cutover_marker` | `timestamptz` · one authoritative instant · (primitive) | The reverse-import delta boundary (new-bot writes begin at the Railway flip) | L-18 |
| 73 | `rollback_class_resolved` fence + `SB_VERIFY_BOOT` (see #35) + 2 scoreboard lines | **13 §2.5** | `manifest-validate` + §5.4 scoreboard | fence + read-off lines · (primitive) | Every store MUST resolve a `rollback_class`; reverse-importer coverage == the `REVERSE_IMPORTABLE` set | **L-18**; register **Q-D14** (RPO) |

---

## GROUP 14 — `CredentialSpec` sibling leaf + supply-chain (spec 12)

| # | Field / primitive | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 74 | `CredentialSpec` + `CREDENTIAL_REGISTRY` | **12 §2.A** | new leaf `sb/spec/credentials.py` (sibling of `SecretSpec`, keyed by `config_ref`) | dataclass `{name, store, config_ref, rotation, cadence_days, revocation_ref, blast}` · (primitive) | One flat disjoint credential inventory with a declared rotation horizon + closed kill-path | **FJ §4 #10**; register **Q-D16/17/19** |
| 75 | `RotationPosture`/`RevocationRef`/`BlastTier`/`CredentialStore` enums + `check_credential_lifecycle` gate | **12 §2.A** | credentials leaf + `tools/` gate | enums (RevocationRef a CLOSED kill-path vocab) + CI gate · (primitive) | A secret with no declared kill-path/horizon is unconstructible + CI-red | **FJ §4 #10 / N-1**; **CL-1/CL-2** |
| 76 | Supply-chain gate — `requirements.lock` + `check_lockfile_fresh` + `pip-audit` | **12 §2.C** | new repo CI | lockfile + 2 CI gates · (primitive) | Deterministic hash-pinned install; the lock diff is the deferred-review artifact (composes with Q-0105) | **FJ §4 #12 / N-2**; **CL-3** |

---

## GROUP 15 — `InvariantSpec` (spec 11, `sb/spec/invariants.py`, the `data_invariants` facet)

| # | Field / primitive | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 77 | `InvariantSpec` + the `data_invariants` manifest facet | **11 §2.1** | new leaf + `SubsystemManifest.data_invariants` (sibling to `stores`) | dataclass `{invariant_id, kind, owner_subsystem, stores, check_ref, severity, repair_ref, bears_value, baseline_ref, tolerance, ground_truth_store, default_enforce, cadence, max_actions_per_run, read_batch_size, scope}` all **[S]** · (primitive) | Declared data-content invariants → scheduled dry-run sweep → audited repair/quarantine (steady-state corruption detector) | **FJ §4 #7**; **L-1** (live-residue leg) |
| 78 | `InvariantKind`/`Severity`/`SweepCadence` enums + `Violation` + `invariant_coverage` fence + `SWEEP_ACTOR` | **11 §2.1/§2.3** | invariants leaf + `compile.py` + sweep | enums + fence + `ActorRef(actor_type="backfill")` sentinel · (primitive) | Every `bears_value` store MUST be covered by ≥1 invariant; value-bearing repair MUST declare `ground_truth_store` (Q-D13) | **FJ §4 #7**; **L-18** verified-restore leg; register **Q-D13** (money direction) |

---

## GROUP 16 — The send-egress port + rubric classes 11/12/13 (spec 10, RC-21 / Q-D26)

| # | Field / primitive | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 79 | `ChannelEmitter` send-egress port + `OutboundContent` + `TrustLevel` | **10 §2.A / §8.1** (RC-21, a 02/K8 seam correction) | new `kernel/interaction/egress.py` | Protocol `ChannelEmitter.send` + `OutboundContent{body, trust=UNTRUSTED, allow_mentions=()}` + `TrustLevel{UNTRUSTED, TRUSTED, SYSTEM}` · (primitive) | The service-initiated send-egress port (the `automation_executor.py:220` mass-ping vector); `UNTRUSTED` default ⇒ `AllowedMentions.none()`; AST-fenced | **L-24** (allowed_mentions leg); **RC-21**; register **Q-D26** |
| 80 | Rubric classes **11 / 12 / 13** + victim-axis precedence (13>12>11) | **10 §2.A** | rubric v2 (owner-directed) | 3 review classes + `check_cost_posture`/`check_data_lifecycle` checkers · (primitive) | The cost/privacy/security review lens + the one-time adversarial-abuse pass before Gate-0 | **L-19**, FJ §8, **FJ §4 #3**; register **Q-D20** |

---

## GROUP 17 — Platform-governance intent DEGRADE (spec 14, spec-05 seam correction)

| # | Field / primitive | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 81 | `IntentPosture` + `IntentSpec.posture` + `IntentSpec.degrades` (+ `required` True→False) | **14 §2.B** (corrects spec 05 §3.1) | `IntentSpec` / `INTENT_CONTRACT` | `IntentPosture{REQUIRED, DEGRADE}`; `posture` · `DEGRADE` · **[S]**; `degrades: tuple[str,…]` · `()` · **[S]** | Denial ⇒ boot slash-only with the intent's capability class disabled + admin notice (not `FAILED_STARTUP`); enforced `required == (posture==REQUIRED)` mirror | **L-17** (intent-denial ladder); register **PG-2** |
| 82 | `check_intent_survival` + `check_slash_cap` gates + CUT-2 permission census | **14 §2.A/§2.D** | `tools/` gates + `permission_census.json` | 2 CI gates + census tool · (primitive) | Every essential capability has an interaction-delivered entry point; slash tree ≤ 100/25/1; makes the invisible per-guild override config DB visible | **L-17 / L-23**; **FJ §4 #1/#6** |

---

## GROUP 18 — The L-24 presentation riders (README §6, declared-as-fields at Gate-0)

> Per README §6: Gate-0 ratifies the L-24 presentation riders as **declared fields**. These are named as
> Gate-0 grammar in the front-matter but designed only to declared-field depth in the 14 specs (the
> `allowed_mentions` policy interlocks with `TrustLevel`/`ChannelEmitter` above; `ModalSpec` ties to
> amendment-registry G-10 `ModalFormSpec`). All retire **L-24** (the presentation/accessibility gap).

| # | Field / primitive | Owns / pins | Attaches to | Type · default · role | What it does | Retires |
|---|---|---|---|---|---|---|
| 83 | `alt_text` | README §6 (L-24) | the `discord.File`/embed-bearing spec (all ~50 sites) | `str` · — · **[S]** | Accessibility alt-text on every attachment (the ~50-site gap) | **L-24** |
| 84 | locale seam | README §6 (L-24) | the render/copy layer | (declared seam) · **[S]** | The i18n/locale hook declared at Gate-0 | **L-24** |
| 85 | `allowed_mentions` policy | README §6 (L-24) — interlocks with #79 `TrustLevel` | egress/render specs | policy tag (default-deny via `TrustLevel.UNTRUSTED`) · **[S]** | Mention-suppression policy on both egress ports | **L-24 / X-1** |
| 86 | `ModalSpec` | README §6 (L-24); amendment G-10 `ModalFormSpec` | manifest grammar | dataclass · **[S]** | The declared modal-form primitive | **L-24**; amendment G-10 |
| 87 | bundled fonts | README §6 (L-24) | asset/render layer | declared asset set · **[S]** | Bundled fonts for deterministic media rendering | **L-24** |

---

## Count

**87 grammar-field / primitive additions** total, grouped by 18 attach points. Rough split:
- **Fields on existing manifest specs (the `[S]`/`[DERIVED]` additions Gate-0 ratifies onto a spec):**
  ~34 — CommandSpec/PanelActionSpec/SelectorSpec (#1-10), EventSpec.delivery (#40), the six
  ManagedTaskSpec durability fields (#54-58), the seven StoreSpec version fields (#61-64) + three privacy
  fields (#66-68) + rollback_class (#70), IntentSpec.posture/degrades (#81), the 8+1 new ConfigSpec rows
  (#34-35), WorkflowContext.correlation_id/test_mode (#48-49), ActorRef.actor_type/member_tier (#11-12),
  and the L-24 riders (#83-87).
- **New leaves / primitives (enums, ports, dataclasses, tables, fences, facets, markers):** ~53 — the
  outcomes/authority/config/observability/events/scheduler/versioning/credentials/invariants leaves, the
  error envelope, the ChannelEmitter port, the idempotency/audit_log/outbox/due-queue/draft/quarantine
  tables, the compile fences, and the rubric classes.

(If Gate-0 counts only *field additions onto a spec type* it is ~34; if it counts every primitive the
specs pin for ratification it is 87. Both figures given so the next session can pick its granularity.)

---

## Part 2 — the register-row disposition (RATIFY-DEFAULT 19 · OWNER-ONLY 12 of 31)

### Register-row disposition — Gate-0 grammar-freeze work-list

> **Harvest of** `docs/analysis/rebuild-discovery/foundations/design/question-register.md`
> (all 31 rows, Q-D1…Q-D31, three tiers) — cross-read against `design/README.md` §4/§6 and
> `design/shared-vocabulary.md` §⑧ (SF-fork table). **NOT SOURCE OF TRUTH** — the owning specs win
> (Q-0120). Purpose: tell the next ultracode (Gate-0) session, per row, whether it can **mechanically
> freeze the built default** (RATIFY-DEFAULT — no owner needed) or must **hold for an owner ruling**
> (OWNER-ONLY — irreversible / narrows a binding decision / rubric edit).
>
> **Counts: RATIFY-DEFAULT 19 · OWNER-ONLY 12 · of 31.**
> Owner-only = the README §4 baseline of **10** (Q-D5, Q-D8, Q-D13, Q-D14, Q-D15, Q-D16, Q-D17,
> Q-D19, Q-D20, Q-D21) **+ 2 found this harvest** (Q-D18, Q-D24 — see §Found). **L-21** (old-bot
> change-policy) is also owner-only but is an **L-ledger row, not one of the 31** register rows, so it
> is **not** in the count of 31 (noted in §Aside).

---

## A · RATIFY-DEFAULT (19) — Gate-0 freezes the built default, no owner needed

Each has a **safe / conservative built default** that the grammar freeze can pin without foreclosing a
later owner option. Rows flagged `owner-visible` are ratifiable *and* should be surfaced at the sitting
for owner awareness (a scope confirm, a copy string, an ops caveat) — that input does **not** block the
freeze.

### Tier 1 — cross-spec seams (mechanical / design co-decisions)

| Q-D | Decision (one line) | Built default (recommendation) | Owning spec · maps-to | Tier | 🔒 (register) | Why RATIFY-DEFAULT |
|---|---|---|---|---|:--:|---|
| **Q-D1** | Who hosts the outbox relay? (08 registers it as 09 lanes; 09 says it's its own task → relay is UNHOSTED as written) | (a) **09 hosts** `OutboxRelayLane`+`OutboxReaperLane` on its `PollSupervisor` (5 s); 09 drops the "own RELAY_TASK/1 s/not-my-lane" language | 08 ↔ 09 (F-1) · ⊕ net-new | T1 | No | Mechanical seam reconciliation; matches 09's own "one supervisor, registered lanes" principle. Already applied in-spec this pass (RC-20). |
| **Q-D2** | Atomic-apply semantics + which K7 entry the draft calls (06 per-op `run()` vs 07 shared-txn `apply(op,conn)`); keep the word "atomic"? | (a) **reconcile to 06's per-op `run()`** + EFFECT legs; restrict `apply(op,conn)` to pure-DB draft ops; **drop "atomic"** for the non-rollback-able resource lane | 06 ↔ 07 (F-3) · T2-1/A#1 | T1 | 🔒 (wording leg) | Seam is design/mechanical (applied via F-2 co-decision). The 🔒 "atomic" wording leg is a naming-accuracy fix (the resource lane isn't rollback-able), not an irreversible/binding call. |
| **Q-D3** | Add `ActorRef.actor_type`? (09 `SYSTEM_ACTOR`/11 `SWEEP_ACTOR` need it; frozen `ActorRef` has no such field) | (a) **add `actor_type: str = "user"`** to 02 `ActorRef` + vocab §⑩; repair reuses `backfill` | 02 · 09 · 11 · vocab §⑩ (F-5) · RC | T1 | No | Mechanical additive field, winner already determined (mirrors RC-12 `member_tier`); registered as an RC — already landed on 02's `ActorRef` this pass (RC-18). |
| **Q-D4** | Which `Surface` member classifies a background fire's `from_exception`? (frozen `Surface` has no background member) | (a) **reuse `"scheduler"`** for both scheduler fires and sweep-repairs (one token); `"maintenance"` only if frozen for both siblings at once | 02 · 09 · 11 (F-2) · RC | T1 | No (freeze-gated) | Additive enum member; the design intent is "one string, no fork." Applied in-spec as `Surface.MAINTENANCE` (RC-19). Freeze it once. |

### Tier 2 — contract-level rows with a safe ratifiable default

| Q-D | Decision (one line) | Built default (recommendation) | Owning spec · maps-to | Tier | 🔒 (register) | Why RATIFY-DEFAULT |
|---|---|---|---|---|:--:|---|
| **Q-D6** | Panel-action grammar (SF-a): per-spec `authority_ref`/`cooldown`/… on panel actions vs minimal `PanelActionSpec` + derived path | (A) **per-spec fields** (route-through-C-1) — retires L-5 structurally; 01 arms `never_strand`/`action_cooldown_parity` | 02 §8-a · 01 P6 (SF-a) · L-5 | T2 | 🔒 owner-visible | Grammar-shape choice; **resolver contract unchanged either way**; ratifying (A) is exactly what the grammar freeze does. Owner-visible for awareness, not a ruling. |
| **Q-D7** | Owner-override scope + transparency-sink wording (SF-b): member-guild vs any-reachable; observability-only vs distinct operator log | scope **(A) member-guild** — *built structurally* (X-7); sink **(ii)** dual bot-log+server-log, owner-DM fallback, **no durable row** | 02 §8-b · 04 §8-a (SF-b) · T2-10/L-12 | T2 | 🔒 owner-visible | The narrow/safe scope is enforced in code regardless; owner only **confirms scope + names the copy** — a cosmetic fill-in that doesn't block the freeze. |
| **Q-D9** | Which events are `delivery=AT_LEAST_ONCE`? (default `BEST_EFFORT`) | (a) **v1 set** = `audit.action_recorded`, `xp.awarded`, `xp.level_up`, `economy.balance_changed`; all others stay `BEST_EFFORT` | 08 §13 · 07 §9-#7 · T2-3/L-9 | T2 | 🔒 | Delivery-class default set is extensible later (add events any time); mechanism fully built. Zero behavior change for the 30+ observability events. Ratify the v1 set. |
| **Q-D10** | `StoreSpec.version_policy` default for a `bears_value` store when schema drifts with no `upcast_ref` | (a) **`REJECT_AND_PRESERVE`** (refund-before-delete, never forfeit) | 09 §8.1 · T2-7/A#8 | T2 | 🔒 (data-loss) | Recommendation **is** a specific safe default (never-forfeit); compile fence forbids `DROP` on a value store so the floor is safe regardless. Only the default is the call → ratify the safe one. |
| **Q-D11** | Invariant enforcement: permanent runtime sweep vs one-time migration script | (C) **permanent `PollLane`, report-only by default**; cutover verify-import hard-checks the same invariants | 11 §4 Q1 · FJ §4 #7 | T2 | 🔒 | Report-only = no mutation risk (safe floor); individual invariants flip to auto-repair as each proves out. Build-architecture default is ratifiable. |
| **Q-D12** | verify-import (CUT-2) + verified-restore (CUT-3) as HARD cut gates or advisory? | (C) **HARD on `bears_value` RECONCILIATION+TERMINAL_ONCE, advisory on the rest**, owner-signed quarantine override; backup-restorability = HARD | 11 §4 Q2 · 13 §4 Q2 · L-18/FJ §4 #7 | T2 | 🔒 | Gate-hardness policy with the owner-signed override valve **built into the mechanism**; decided once in 11 §4 Q2 (13 cross-refs, no re-fork). Tunable, not irreversible. |
| **Q-D22** | Un-preserved-override disposition (PG-4): RENAMED/DROPPED slash-permission overrides that can't be auto-restored | (a) **admin-notice + exact re-apply overlay** (never silently reset a guild's security config) | 14 §4 PG-4 · L-23 | T2 | 🔒 | Safe default (never silent reset); a cutover-comms detail that lands in the CUT-3 comms plan. Ratifiable. |
| **Q-D23** | Deployment identity (PG-5): reuse the same Discord application id at cutover, or a new application? | (a) **reuse the same app id** (un-renamed commands keep their ids → overrides survive) | 14 §4 PG-5 · ⊕ net-new | T2 | 🔒 ops-caveat | Recommendation is the clearly-safer default (shrinks override-loss blast radius). Only deviate (b) if an **ops constraint forces it** — surface that caveat, but default is ratifiable. |

### Tier 3 — defaults & bounded deferrals (batch-bless)

| Q-D | Decision (one line) | Built default (recommendation) | Owning spec · maps-to | Tier | 🔒 (register) | Why RATIFY-DEFAULT |
|---|---|---|---|---|:--:|---|
| **Q-D25** | Dispatch-trace / audit-retention promotion (SF-c): keep `command.dispatched` observability-only vs promote to retained audit rows | (A) **observability-only / DB-spine-only for v1** | 02 §8-c · 04 §8-c · 06 §9 · 07 §9-#6 (SF-c) · ⊕ net-new | T3 | 🔒 (retention) | v1 default adds **no** new retained rows (per-mutation audit already covers auditable writes); promotion is a retention/volume posture, not a correctness need. Tier-3 batch-bless. |
| **Q-D26** | `ChannelEmitter` send-egress port (T-7): primitive the X-1 mass-ping vector, or leave un-primitived | (a) **new `ChannelEmitter` port** + `OutboundContent`/`TrustLevel`, default-deny, AST-fenced | 10 §8.1 T-7 → 02/K8 · L-24 | T3 | No (owner-visible seam corr.) | Explicitly **not** 🔒; owner-visible seam correction registered as RC-21 (parallel to RC-12/F-5). Gate-0 ratifies the port. |
| **Q-D27** | CUT-2 permission census as a *binding* cutover gate (PG-3)? | **Binding** — no swap until census captured, PRESERVED carry-verified, RENAMED/DROPPED enumerated into the notice | 14 §4 PG-3 · L-23 | T3 | No (design-flagged) | Decided by design (flagged); a bounded per-guild bot-token read. Not owner-gated. |
| **Q-D28** | Test-mode effect routing (06): suppress real Discord EFFECT writes, or route to a real test guild? | (a) **fail-safe suppress** default (never touch a real guild) | 06 §9 · retirement map · L-10/L-11 | T3 | 🔒 (audience) | Safe built default is suppress; concrete test-guild routing is owned by the release-testing band behind the `AcceptHook` seam. Owner **names the audience later** — doesn't block v1. |
| **Q-D29** | Durable cooldown store (SF-e): deploy-surviving cooldown state vs in-memory | (a) **in-memory for v1** (matches shipped; resets on restart) | 02 §9 (SF-e) · T2-6/L-8 | T3 | No | Bounded deferral, not a policy call; matches shipped behavior. If promoted it's a strand-2 `StoreSpec` off `CooldownSpec`. |
| **Q-D30** | Rung-4 NL-orchestration failure policy (SF-f): stop-on-first-non-SUCCESS vs per-plan continue/compensate | (a) **stop-on-first-non-SUCCESS** default | 02 §9 · 07 §9-#1 (SF-f) · ⊕ net-new | T3 | No | Bounded deferral; the sequential seam + shared `orchestration_id` are designed now, per-plan policy is Phase-4 band 6. |
| **Q-D31** | Batch-ratify the design-decided seam refinements (rubric mechanization tags, `CredentialSpec` leaf, repair `actor_type`=`backfill`, de-repo-bind mechanics, integrity-floor fix, …) | **Adopt all as recommended** (contained + reversible) | 10 · 11 · 12 · 13 · mixed | T3 | No | Literally the "batch-ratify" row — each has a recommendation, decided by design, surfaced only for one-batch awareness. |

---

## B · OWNER-ONLY (12) — hold for an owner ruling before the freeze commits

The built default unblocks the *build* today, but freezing it **is itself** the irreversible / binding /
rubric decision — so the owner must actively rule (or bless the default) rather than Gate-0 auto-pinning it.

### Tier 1

| Q-D | Decision (one line) | Built default (ships until ruled) | Owning spec · maps-to | Tier | 🔒 | Why OWNER-ONLY |
|---|---|---|---|---|:--:|---|
| **Q-D5** | `IntentPosture`: DEGRADE (boot slash-only) or fail-closed (`FAILED_STARTUP` on unapproved privileged intent)? | (a) **DEGRADE** — boot slash-only + explicit `DegradedCapability` + admin notice | 14 → 05 (F-4 / PG-2) · L-17 | T1 | 🔒 | **Flips a frozen `required` field** on the INTENT_CONTRACT (05 §3.1) — narrows a frozen-vocab decision; routed as an owner-visible spec-05 seam correction (PG-2). |

### Tier 2

| Q-D | Decision (one line) | Built default (ships until ruled) | Owning spec · maps-to | Tier | 🔒 | Why OWNER-ONLY |
|---|---|---|---|---|:--:|---|
| **Q-D8** | Store-drop `disposition` default (SF-g): global default vs must name one per signed retirement | (b) **no default — `disposition` REQUIRED** per signed `store_retirements.yml` entry | 01 §8 fork 8 (SF-g) · ⊕ net-new (∥ L-18) | T2 | 🔒 (data-loss) | The recommendation is **"there is no default"** — a silent global disposition is a silent data-loss path; each retirement forces an explicit owner/signer call. Nothing for Gate-0 to auto-pin. |
| **Q-D13** | Repair DIRECTION for a value-bearing violation — which store is ground truth (mint ledger vs claw aggregate)? | (C) **`QUARANTINE_ONLY`** — never auto-mutates money absent an owner-signed `ground_truth_store` | 11 §4 Q3 · ⊕ net-new (money) | T2 | 🔒 (money, near-irreversible) | The per-invariant A-vs-B direction is a **near-irreversible money call**; the fence *requires* an owner-signed direction, so it ships QUARANTINE_ONLY until the owner rules. |
| **Q-D14** | RPO target + backup source tier: daily `pg_dump` (≤24 h) vs off-box audit export vs Railway PITR | (A) **daily `pg_dump` / flat ≤24 h** — the honest built floor | 13 §4 Q1 · L-18 (RPO leg) | T2 | 🔒 (plan/build cost) | Minutes-RPO on the money spine costs a **plan upgrade (C) or a real build (B)** — a genuine plan-cost vs build-cost vs 24 h-acceptable owner call; do not present near-continuous RPO as free. |
| **Q-D15** | Rollback-data disposition + window N: what happens to new-bot writes during an N-day rollback window | (B) **`DECLARED_LOSS` + narrow reverse-import valve** for the `REVERSE_IMPORTABLE` (invertible-∧-value) tier + short N | 13 §4 Q3 · §2.4 · L-18 + FJ §6 T2 + Tier-3 N carry | T2 | 🔒 (data-loss policy) | **Near-irreversible** data-loss policy with a real reverse-importer build cost; **value of N is the owner's Stage-3 carry.** README's #1 owner-only. |
| **Q-D16** | A credential-lifecycle recovery arm at all? (registry + tiered cadence + revocation carve-out + runbook) | (a) **full arm** | 12 §4 CL-1 · FJ §4 #10 | T2 | 🔒 | **Touches the binding Q-0213** credential-concentration decision → **route as router DISCUSS**. Owner must rule on arming a recovery cadence. |
| **Q-D17** | Revocation carve-out — narrow the Q-0213 `*Delete` brake to exclude a credential revoke? | (a) **credential revoke = agent-runnable recovery** (`RevocationRef` closed set); resource delete stays ask-first | 12 §4 CL-2 · FJ §4 #10 (Q-0213) | T2 | 🔒 | **Narrows a Q-0213 brake** → route as router DISCUSS. Narrowing a binding owner brake is by definition an owner ruling. |
| **Q-D18** ⊕found | Supply-chain: add lockfile + hash-verify + `pip-audit` CI gate alongside the Q-0105 adopt-freely grant? | (a) **lockfile + CI gate** (adopt-freely unchanged; lock diff = the deferred-review artifact) | 12 §4 CL-3 · FJ §4 #12 | T2 | 🔒 | **Touches the binding Q-0105 grant → the register itself says "route as router DISCUSS."** Same DISCUSS-routing tell as Q-D16/17/19; README's table omitted it, but by the "narrows/touches a binding + routes DISCUSS" criterion it is owner-only. |
| **Q-D19** | `SB_PROD_ATTEST` durable custody source (SF-d): plain env token vs sealed/managed secret vs OIDC | (a) **presence-gated env `SecretSpec`** (correct today) | 05 §9 · 12 CL-5b (SF-d) · L-10/FJ §4 #10 | T2 | 🔒 (ops / CUT-1) | Register verdict is literally **"defer to owner — genuinely owner-gated"**; buildable now with (a) but the custody *source* is carried forward unresolved (owner ops/CUT-1 call). |
| **Q-D20** | Adopt security rubric classes 11/12/13 + run one adversarial-abuse pass; who runs it | classes (a) adopt all three; retro (c) one pass = the coverage; runner (a) dedicated agent | 10 §4 T-1/2/3 · L-19/FJ §8 | T2 | 🔒 (rubric = owner-directed) | **Rubric edits are owner-directed** (Q-0233 froze the ten; edits are *proposed*, not self-applied). Adopting new classes is an owner ruling by construction. |
| **Q-D21** | Growth posture (PG-1): pursue Discord verification as a **hard gate on growth**, or grow slash-first w/ intent-denial fallback | (a) **slash-first survivability** + intent-denial fallback; verification = a parallel milestone, not a growth gate | 14 §4 PG-1 · L-17/FJ §4 #1 | T2 | 🔒 | **Mission/growth posture** — an externally-owned, discretionary dependency; a hard gate would freeze the mission on Discord's queue. Genuine owner strategy call. |
| **Q-D24** ⊕found | Multi-actor session concurrency-control: foundational kernel primitive now, or Stage-2 per-subsystem? | (A) **name K7 `NATURAL_KEY`-on-the-session-row** as the designated seam + a compile fence requiring session-transition ops to declare it | whole-set gap (07 `NATURAL_KEY` · 11 `TERMINAL_ONCE`) · L-20 | T2 | 🔒 (owner / **architecture**) | Register flags it **🔒 owner/architecture** — introducing a kernel-level concurrency primitive + compile fence is a **cross-cutting architectural commitment** (CLAUDE.md ask-first class), not a grammar-field auto-ratify. (Nuance: both options converge on the *same* K7 `NATURAL_KEY` mechanism — the owner call is build-the-fence-now (A) vs defer to Stage-2 with a coverage-map line (B); an easy bless if the owner wants the fence now.) |

### Tier 3

*(none — all three Tier-3 🔒 rows, Q-D25/Q-D28, carry a safe ratifiable v1 default → RATIFY-DEFAULT.)*

---

## Found (beyond the README §4 owner-only baseline of 10)

The brief's known set = **10** Q-D rows (Q-D5, Q-D8, Q-D13, Q-D14, Q-D15, Q-D16, Q-D17, Q-D19, Q-D20,
Q-D21). Confirmed all 10. **Added 2** on the register's own signals:

- **Q-D18** — the register verdict says *"Route as router DISCUSS (touches Q-0105 binding)"*, the
  identical DISCUSS-routing language the README uses to justify Q-D16/17/19 as owner-only. It touches a
  **different** binding (Q-0105 adopt-freely) than the credential trio (Q-0213), which is likely why the
  README's Q-0213-grouped table skipped it — but by the stated criterion ("narrows/touches a binding
  decision + routes DISCUSS") it is owner-only. **Low-confidence add** — it *composes with* rather than
  *contradicts* adopt-freely, so an owner could reasonably wave it through at Gate-0; flagged so the
  session decides deliberately.
- **Q-D24** — the register flags it **🔒 (owner / architecture)**; it commits a new kernel-level
  concurrency primitive + compile fence, which is the "large / cross-cutting (architectural)" ask-first
  class in CLAUDE.md, not a mechanical grammar-field ratify. **Medium-confidence add** — its two options
  converge on the same K7 `NATURAL_KEY` mechanism, so if the owner blesses building the fence now it
  ratifies trivially; held out because the *build-now-vs-Stage-2* scope is a genuine architecture fork.

## Aside — L-21 (owner-only, but not one of the 31)

The README §4 lists **L-21** (old-bot change-policy — an interim policy so old-bot feature work doesn't
drift from the frozen corpus/goldens) as owner-only. It is an **L-ledger row carried on §4 gap #5** (the
softest binding — no CI guard owns it), **not** a Q-D register row, so it is **excluded from the count of
31**. Flag it to the owner at the sitting alongside the 12, but track it as an L-row, not a register
disposition.

## One-glance disposition index

- **RATIFY-DEFAULT (19):** Q-D1, Q-D2, Q-D3, Q-D4, Q-D6, Q-D7, Q-D9, Q-D10, Q-D11, Q-D12, Q-D22, Q-D23,
  Q-D25, Q-D26, Q-D27, Q-D28, Q-D29, Q-D30, Q-D31.
- **OWNER-ONLY (12):** Q-D5, Q-D8, Q-D13, Q-D14, Q-D15, Q-D16, Q-D17, **Q-D18**, Q-D19, Q-D20, Q-D21,
  **Q-D24**. (**bold** = found this harvest.)
- **Owner-visible-but-ratifiable** (freeze the default, still surface for owner awareness): Q-D6, Q-D7
  (scope confirm + copy string), Q-D23 (ops-constraint caveat), Q-D25 (retention), Q-D28 (test audience).
- **Also owner-only but outside the 31:** L-21 (L-ledger row).

---

## Part 3 — the Phase-B L0 build order (16 steps, S0–S15)

### Harvest — the Phase-B L0 build order (14 specs sequenced by dependency)

> Read-only harvest for the Gate-0 grammar-freeze session. Sources: the 14 specs' §11 build-order
> sections, README §6 "Phase-B L0 build," and the seam-consistency-matrix provides/consumes edges +
> applied reconciliations (F-1/F-2/F-4/F-5 RESOLVED; F-3 OPEN → PG-2). Shipped source wins (Q-0120).

---

## Dependency-graph summary (5 lines)

1. **Strand 1 is a near-linear chain** K0 → K1 → K2 → K3 → K4 → K5 → K6 → K7 → K8, and it is the whole
   substrate: **01 (the K2 compiler) is the linchpin** — the snapshot is the spine *everything* declares
   into (K3 db, K4 events, K5–K10, all Phase-4 ports), and 01's P3 is *literally a call into K1's
   `validate` (RC-7)*, so **K1 (03) must precede K2 (01)** even though 01 is the headline.
2. **05 is the floor and 05+04 are the strand-2 substrate**: 05's K0 config + K3
   `IdempotencyKey`/`once()`/`db.transaction()` and 04's K6 authority contracts (`resolve_authority`,
   `AuthorityDecision`) are what every strand-2 durability port stands on. **07 (K7) is the strand-2
   keystone** — it underlies 06 (draft) *and* 09 (scheduler), and 08 (K4 outbox) provides the durable
   delivery/audit twin they all emit through.
3. **Two apparent cycles are broken by the leaf/kernel split + the "armed-later" pattern, so there is no
   true circular dependency.** (a) 02↔07: 02's *pure leaf* `outcomes.py` (`from_exception`/`Result`)
   lands early at K6/K7 so 07 can consume it, while 02's *resolver* lands late at K8 — no cycle.
   (b) 08↔09: 08 is *authored* at K4 but its relay/reaper lanes are *registered* at/after K5 on **09's**
   `PollSupervisor` (F-1/RC-20) — a composition-root registration, not a build-time import cycle.
4. **Strand 3 (10–14) rides the frozen grammar**: it consumes the frozen vocab + K7 `run_ref` + 09's
   `PollSupervisor` + Gate-0 grammar leaves, adds no new kernel ordering, and can build in parallel once
   K7/K9 exist and the grammar is frozen.
5. **The one contested/open edge is F-3** (14's `IntentPosture=DEGRADE` + `required=False` seam-correction
   to 05's `IntentSpec`) — **owner-gated, carried to register PG-2, not closed by edit**; every other
   cross-spec fork (F-1/F-2/F-4/F-5) is RESOLVED-and-applied in-spec this pass.

---

## The sequenced L0 build-order table (16 steps across the 14 specs)

Specs 01, 05, 09, and 02 each span >1 K-slot; those rows note the split. "K-slot" is the design-spec
§9.1 kernel band; "arms later" marks a contract *defined* at one slot that *activates* when a later input lands.

| # | K-slot | Spec(s) | Provides (what it lands) | Consumes (upstream deps) | Notes |
|---|---|---|---|---|---|
| **S0** | pre-Gate-0 | **01 §3.7** | `docs/planning/rebuild-amendments.yml` (sole amendment-ID minting authority) + `tools/check_amendments.py` (required check) | — (docs/tooling leaf) | **Built BEFORE the Gate-0 fold** so the fold that stamps G-9…G-24 `in-spec` works off a collision-free list. **Blocks:** Gate-0. |
| **S1** | **K0** | **05** (config/observability/intents leg) | `sb/spec/config.py` + `sb/kernel/config` (`preflight()→Config`, `parse_bool`/`parse_dsn`); `sb/spec/observability.py` + metrics `render()`; `IntentSpec`+`assert_intents`; checkers `check_config_usage`/`check_metric_cardinality` | — (substrate; runs first at boot) | **Blocks everything** — the composition root cannot boot without the config object; `db.init(cfg)` takes it. Intents gate gateway connect. |
| **S2** | **K1** | **03** (namespace registry) | `namespace.validate(snapshot)→NamespaceReport`; `is_reserved(value,kind,*,surface,parent)`; `Collision(kind,value,scope,claimant_a/b)`; tombstones + `legacy_reservations.json`; cap guard; `check_namespace` + symbol-shadow AST pass | **K0** only (K1 is a leaf) | Pre-K2 one-time `tools/compute_corpus.py` runs at **Stage-2** (harvests corpus, shared-verb set, cap-fit surface, seeds `legacy_reservations.json`). **Blocks** K2/K6/K8 + the invocation subsystem. |
| **S3** | **K2** | **01** (compiler/snapshot/amendments) — **THE LINCHPIN, first real build** | `tools/manifest_compile.py` (9 passes P1–P9 + `_project`); `sb/spec/refs.py` (`*Ref` + `@handler` dup-guard `RefRedefined`) + `roles.py`; `manifest.snapshot.json` serializer + `stable_hash`; failure taxonomy; `sb/app/boot_gate.py` leg-A recompile-parity; arrangement-invariance test | **K1** (P3 = calls K1 `validate`; both surfaces node shape) | **P3 is exactly K1's `validate` (RC-7).** Arms-later: P7 store-completeness **arms at K3**, leg-B build-parity + leg-C remote-parity **arm at K8**. **Blocks K3–K10 + all of Phase 4** — the snapshot is the spine everything declares into. |
| **S4** | **K3** | **05** (db seam leg) | `sb/kernel/db/{pool(+transaction),data_plane,migrations,idempotency}` — `db.transaction()`, `assert_data_plane()` (the 4th rail), fresh migration runner + `verify_applied_checksums`, `IdempotencyKey`/`once()`/`record_outcome`; `check_migrations` | **K0** (`db.init(cfg)`) | **The strand-2 substrate primitive.** `once()`/`db.transaction()` are consumed by 06/07/08/09 (transitively via K7). Arms 01's P7 store-completeness (`projections.stores` now exists). |
| **S5** | **K4** | **08** (event outbox) | `sb/spec/events.py` (`DeliveryClass{AT_LEAST_ONCE,BEST_EFFORT}` — **canonical enum home**, K7 imports it) + `EventSpec.delivery` [S]; `event_outbox` table + atomic claim; `enqueue`/`enqueue_all`/`enqueue_audit_action` (the durable audit twin); `delivery_declared` fence | **K3** (`db.transaction()`, `IdempotencyKey`) + `sb/spec/events.py` | Relay/reaper lanes are **authored** here but **registered at/after K5** on 09's `PollSupervisor` (F-1). Provides K7's step-4e in-txn `enqueue_all` + step-6 post-commit `emit_after_commit()`. |
| **S6** | **K5** | **05** (health leg) + **09** (PollSupervisor host leg) | 05: `sb/adapters/http/health.py` (`/ready`+drain, `/metrics` route), lifecycle STARTING/RUNNING. 09: spawns the one supervised `PollSupervisor` + provides RUNNING/drain predicates. **Register 08's `OutboxRelayLane`+`OutboxReaperLane` here (F-1/RC-20).** | **K3** (db) + **K4** (outbox lanes to register) | 09 has **two landing points** — the poll host rides K5; the due-queue+version land at K9-peer (S10). Readiness gates CUT-1. |
| **S7** | **K6** | **04** (authority engine) [+ 02's `outcomes.py` leaf recommended here] | `sb/spec/authority.py` (`validate_authority_ref`, `classify_authority_ref` total/non-overlapping, tier order); `kernel/authority/{owner,decision,resolve,channel_access,transparency}.py`; 10-field `AuthorityDecision`; owner-override-once; `TransparencySink`. Landing `sb/spec/outcomes.py` here lets authority avoid forward-referencing K7. | **K1** (capability reservation) + **K3** (revoke overlay/policy reads) + **K5** (admission sheds lifecycle/DM legs) | **Arms 01's P4** authority-string check as soon as `validate_authority_ref` exists. **Blocks K7 (each workflow lane's first "resolve authority" step) + K8 + all Phase-4 mutations.** |
| **S8** | **K7** | **07** (workflow/compound-op engine) — **strand-2 keystone** [+ 02's `WorkflowResult`/`from_exception` grammar] | `sb/spec/outcomes.py` finalized + `WorkflowResult`/`MutationPreview`/`StepResult`; `LegSpec`/`CompoundOpSpec`/`IdempotencyPosture`/`WorkflowContext`/`WorkflowRegistry`; **`run()`/`run_ref(conn=)`/`apply(op,conn)`/`preview()`** over one `_execute` core; central `audit_log` row via `enqueue_audit_action`; fences `idempotency_posture_declared`/`audit_completeness`/`atomic_db_only` | **K1,K2,K3,K4,K5,K6** (only layers above it) | **Underlies 06 AND 09.** F-2 applied: `atomic_db_only` scope dropped "draft op_kind mapping" so EFFECT-bearing draft ops go through `run()`; `run_ref`/`apply` fenced to pure-DB external-conn callers only. `WorkflowContext` gains `correlation_id`/`test_mode`/`actor_type` mapping. |
| **S9** | **K8** | **02** (C-1 resolver + error envelope) + **the spec-02 absorption edit** | `resolve()` single seam + `ResolveRequest`; `SurfaceResponder` port; 6 surface adapters (slash/prefix/fuzzy/component/modal/nl); `predicates.evaluate`; `from_exception`/`ErrorEnvelope`/reply-visibility/drain gate; `tree.error`/`on_app_command_error`. **AST no-skip fence arms here.** | **K1** (name resolution) + **K5** (admission) + **K6** (`authority_ref`→`AuthorityDecision`) + **K7** (`Result`/audit spine) | **L0 ABSORPTION TASK:** 02 is written to pre-hardening shapes and must absorb 04's frozen authority contracts (RC-2/3/4/5/12/13/14/15) + `actor_type` **before K8 wires up** — F-4/RC-18 (`actor_type`) already landed on 02's `ActorRef`; **RC-12 `member_tier` still pending** in this batch. **Arms 01's leg-B + leg-C.** Blocks all of Phase 4 — nothing dispatches without `resolve()`. |
| **S10** | **K9** (peer) | **06** (draft pipeline) + **09** (due-queue + version policy leg) | 06: producer-agnostic `sb_drafts`, N-ops-as-N-rows, Accept=AND-over-refs, per-op idempotent-resume `apply` over K7 `run()`. 09: `sb_due_queue` + `ManagedTaskSpec` durability/misfire/catch-up, `arm_declared_tasks`, boot-reconcile, `VersionPolicy`/`VersionedRow`. **Register `ExpiryJanitorLane` + `DueQueueLane` (+ 11's `InvariantSweepLane`) on 09's `PollSupervisor`.** | **K3** (`once`/txn) + **K6** (`resolve_authority`) + **K7** (`run()`/`run_ref`) + **K8** (envelope) + **K2** (ref table) + **K1** (op-kind/task-key reservation) | 06 & 09 are **peers on the K3 substrate** (no dependency between them). GLOBAL slot-key double-arm closed via `COALESCE(guild_id,0)` (09 §5). Blocks AI orchestration, presets, restart-safe timers, all `DURABLE` tasks, `bears_value` cross-deploy state. |
| **S11** | rides frozen grammar (Gate-0 leaves + K7) | **10** (security/abuse rubric) | rubric classes 11/12/13 (rubric v2); `CommandSpec.cost_posture`+`quota_ref`+`check_cost_posture`; `StoreSpec.{data_class,erasure_ref,cache_scope}`+`check_data_lifecycle`; member-erasure executor `sb/kernel/privacy/erasure.py`; **new `ChannelEmitter` egress port** (`kernel/interaction/egress.py`, Q-D26/RC-21) + AST send-fence | K7 (`erasure_ref`→`run_ref`→`emit_audit_action`); frozen `SurfaceResponder` (02); metrics (05) | Strand-3. Adversarial-abuse pass = a Gate-0 checklist line (owner-gated Q-D20). |
| **S12** | rides K5/K9 + K7 | **11** (data-integrity/repair) | `sb/spec/invariants.py` (`InvariantSpec`, §2.8 sibling of `StoreSpec`) + `data_invariants` facet; `invariant_coverage` fence; `InvariantSweepLane` (a `PollLane` on **09's** `PollSupervisor`, peer to due-queue+draft janitor); `sb_quarantine`+`sb_invariant_sweep_log`; CUT-2 verify-import; `QUARANTINE_ONLY` money-repair default | **K7** `run_ref(conn=)` external-conn + vocab ④ `once()` (the 09 `_fire_one` pattern verbatim); **09** `PollSupervisor`; K3 | Strand-3. Report-only default; auto-repair is a settings-backed one-way door. Money-repair direction owner-gated (Q-D13). |
| **S13** | Gate-0 leaf + K9 | **12** (credential lifecycle) | `sb/spec/credentials.py` (`CredentialSpec`, `RotationPosture`/`RevocationRef`/`BlastTier`) + `CREDENTIAL_REGISTRY` + `check_credential_lifecycle.py`; rotation as a **`DURABLE` `OneShot` `ManagedTaskSpec` on 09's due-queue** + `phase` ledger; lockfile + `check_lockfile_fresh` + `pip-audit` gate; compromise runbook | **09** due-queue (`ManagedTaskSpec` + `reconcile_on_boot` re-fires crash-interrupted swap); 05 `SecretSpec` | Strand-3. Custody/recovery calls owner-gated (Q-D16/17/19); revocation carve-out narrows binding Q-0213 → router DISCUSS. |
| **S14** | Gate-0 grammar (on 09's `StoreSpec`) | **13** (backup/DR/rollback) | de-repo-bound backup port + verified-restore CI job (`restore-verify.yml`) + `SB_VERIFY_BOOT` ConfigSpec; RPO contract; `RollbackClass` enum + **derived `rollback_class`** on **09's** version-extended `StoreSpec`; `rollback_class_resolved` + reverse-importer fence; narrow reverse importer | **09** `sb/spec/versioning.py` `StoreSpec`; the manifest compiler (01) for the derivation; 11 §2.5 sweep for verified-restore | Strand-3. Rollback-data disposition + window N is the near-irreversible owner-only call (Q-D15); RPO target owner-gated (Q-D14). |
| **S15** | seam-correction into K0 + CUT stages | **14** (platform-governance) | slash-first survivability tag + `check_intent_survival`/`check_slash_cap`; **`IntentPosture` DEGRADE seam-correction into 05's `IntentSpec`** (OPEN-FORK F-3 → PG-2); `guild_count` gauge + threshold evaluator; `tools/permission_census.py` (CUT-2 gate) + rename-override carry-verify + admin-notice | 05 `IntentSpec`/`assert_intents` (K0); the CUT-2 importer | Strand-3. **F-3 is the one open contested seam** (fail-closed `required=True` vs DEGRADE) — owner-gated PG-2. App-id + verification-milestone calls owner-gated (PG-1/PG-3/PG-5). |

---

## The six explicit callouts (as required)

- **(a) 01 is the compiler linchpin, built first** among the real kernel bands: it lands at **K2** and is
  "the gate the entire kernel and port order sit behind." Its only earlier dependency is **K1 (03)**,
  because 01's P3 namespace pass *is* a call into K1's `validate` (RC-7). Its amendment-registry half
  (§3.7) is a **pre-Gate-0 prerequisite (S0)**.
- **(b) 05's `IdempotencyKey`/`once()`/`db.transaction()` (K3) + 04's authority contracts (K6) are the
  substrate strand-2 depends on.** All of 06/07/08/09 consume the K3 idempotency+transaction primitive;
  every K7 workflow lane calls 04's `resolve_authority` as its first step. Strand-2 cannot build until
  both land (S4 + S7).
- **(c) The spec-02 absorption edit is an explicit L0 task (S9).** 02 is written to its pre-hardening
  shapes and must absorb 04's frozen authority contracts **RC-2/3/4/5/12/13/14/15 + `actor_type`** before
  K8 wires up. Status: F-4/RC-18 (`actor_type`) has **landed** on 02's `ActorRef`; **RC-12 (`member_tier`)
  is still pending** in this batch, along with threading `owner_override` into channel-access and naming
  the `TransparencySink` seam.
- **(d) 07 (K7) underlies 06 + 09; 08 provides durable delivery.** 07 is the strand-2 keystone —
  06's `apply_draft` calls K7 `run()` per-op, 09's `_fire` calls K7 `run_ref()`, and the game/scheduler/
  invariant paths all route through `CompoundOpSpec`s. 08 (K4) supplies the durable `event_outbox` +
  `enqueue_audit_action` twin that K7 and every `AT_LEAST_ONCE` path emit through.
- **(e) The applied seam reconciliations are already in-spec (not open work):**
  - **F-1/RC-20** — **09 hosts the outbox relay/reaper lanes** on its single `PollSupervisor` at 5 s;
    the standalone 1 s `RELAY_TASK` model is withdrawn; 08 already host-cites 09. Applied.
  - **F-2 (PIN-2)** — the **draft `run()` caller-type split**: EFFECT-bearing draft ops → `run(spec,ctx)`
    per-op (per-op-atomic + idempotent-resume); `run_ref`/`apply` = external-conn pure-DB only, fenced by
    a narrowed `atomic_db_only` (no draft `op_kind` in scope → the 10-channel D&D canary un-blocks).
    Applied in both 06 and 07.
  - The two former **blockers are closed**: the **GLOBAL slot-key double-arm** (09 `COALESCE(guild_id,0)`
    in the unique index; arm-key == fire-dedup-key normalization) and the **`atomic_db_only` fence scope**.
    A green build is no longer structurally blocked.
- **(f) Strand-3 (10–14) rides the frozen grammar.** It adds no new kernel ordering: it consumes the
  frozen vocab, K7 `run_ref`, 09's `PollSupervisor`, and Gate-0 grammar leaves; specs 10–14 can build in
  parallel once K7/K9 exist and the grammar is frozen. Each adopts the §4 owner rulings.

---

## Notes — circular / contested dependencies

- **No true circular dependency exists.** Two *apparent* cycles are structurally broken:
  (1) **02 ↔ 07** — 02's pure `outcomes.py` leaf (`from_exception`/`Result`, recommended landed at
  **K6**) is consumed by 07 at K7, while 02's *resolver* lands later at **K8** that consumes 07. Splitting
  the leaf from the resolver removes the cycle.
  (2) **08 ↔ 09** — 08 is authored at K4 but its relay/reaper lanes are only *registered* (composition
  root) at/after **K5** on 09's `PollSupervisor`; 08's enqueue/store depend on K3, not on 09. The
  "authored-early / registered-later" pattern removes the cycle.
- **The one OPEN/contested cross-spec edge is F-3** (`14` ↔ `05`): 14 wants to flip `message_content`/
  `members` to `required=False` + `posture=DEGRADE` on 05's `IntentSpec`; 05 as written keeps them
  `required=True` fail-closed. **Carried to owner register PG-2, not closed by edit** — the built default
  ships `required=True` until PG-2 rules.
- **One reconciliation still pending in-batch (not contested, just not yet applied):** **RC-12
  (`member_tier` on 02's `ActorRef`)** — part of the S9 spec-02 absorption edit; must land before K8.
- **The "arms-later" contracts are not ordering violations:** 01's P7 (arms at K3), leg-B/leg-C (arm at
  K8), 03's `validate` end-to-end run (arms at K2), and 04's P4 arming (at K6) are contracts *defined*
  at their own slot that *activate* when a downstream input lands — deliberate, per the sibling-01 pattern.

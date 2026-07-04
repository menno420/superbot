# Retirement-coverage map — V-3 closure audit (nothing evaporates)

> **Status:** `audit` — **complete** (2026-07-04). **NOT SOURCE OF TRUTH** — a reconciliation
> artifact over the 14 frozen design specs' §10/§5 retirement maps and the Fable-5 final judgment
> ledger. Source wins (Q-0120); a spec's own retirement table wins over this roll-up.
>
> **What this is.** V-3 (the final-judgment verdict, `../final-judgment-fable5-2026-07-03.md` §1) is
> binding: the ~470 reconciled findings must **bind to a plan so nothing evaporates**. This map is the
> closure check. It walks **every** row the owner is owed — the 25 judgment-ledger L-rows (§2), the 17
> surviving §4 gaps, and the full owner-decision queue (Tier-1 T1-1…T1-7, Tier-2 T2-1…T2-22, the
> Tier-3 batch, and the stress/critic additions) — and for each records **which design spec retires
> it**, or where it is **carried**, or why it is **out-of-scope**. Any row that **no spec retires and
> is not explicitly carried** is an **EVAPORATION** — a V-3 violation — and is flagged loudly.

---

## Headline

| Metric | Value |
|---|---|
| **Total rows audited** | **96** (25 L-rows + 17 §4 gaps + 7 Tier-1 + 22 Tier-2 + 17 Tier-3-batch + 8 stress/critic) |
| **Covered — a spec retires it** (full or partial) | **62** |
| **Carried** — surfaced to a named gate / register / Stage-3 line / resolved owner Q | **32** |
| **Out-of-scope** — V-1 immediate PR or Stage-2 subsystem work | **2** |
| **EVAPORATIONS (V-3 violations)** | **0** |

**Verdict: V-3 holds.** Every one of the 96 rows has a home — a spec retirement, a named
gate/register/Stage-3 line, or an explicit out-of-scope reason. **No finding evaporates.** Nine rows
are only *weakly* carried (Stage-3 consolidation / "standing owner awareness"); those are the residual
V-3 watch-list (last section) — homed, but on the softest binding, and worth a firmer artifact before
they can drift.

**Legend.** `Covered` = a design spec's retirement table claims it (RETIRED / PARTIAL / CONSUMED /
FEEDS). Partial-covered rows carry a `+ carried` tail for the deferred remainder. `Carried` = no
foundational spec retires it, but it has an explicit home (Gate-0 grammar freeze, a CUT-stage gate,
the Stage-3 consolidation, the Gate-V golden classes, a resolved `Q-0237` owner answer, or the
Tier-3 batch-bless). `Out-of-scope` = deliberately not this foundational design's job (V-1 is an
immediate PR; a Stage-2 subsystem collapse; the D-4 kit).

> **§4 gaps #1–#6 are the same findings as L-17 / L-18 / L-19 / L-20 / L-21 / L-23** (they graduated
> into the L-ledger as the ★ rows). They are listed in both tables per the audit's mandate to walk
> *every* row; the disposition is identical in both places (no double-work, no double-risk).

---

## Table 1 — Judgment-ledger L-rows (L-1 … L-25)

| Row | Disposition | Retired / carried by — one line |
|---|---|---|
| **L-1** RPS fee-forfeit on version bump | **Covered** | Spec **09** — `StoreSpec.version_policy=REJECT_AND_PRESERVE` **generates** refund-before-delete (the durable *class* fix; retires the hand-written `_persistence.py:104-115` branch). Live-residue leg co-owned by spec **11**. *(V-1, the one-off PR, is the stopgap — out-of-scope below.)* |
| **L-2** No restart-safe Back-path medium | **Carried** | Owner-resolved **T1-2 → Q-0237b** (in-session real stack + semantic-parent fallback after restart). The medium build lands in the Stage-2 **NavigationSpec** — not one of the 14 foundational specs. |
| **L-3** Hide-vs-disable contract collision | **Carried** | Owner-resolved **T1-1 → Q-0237a** (hidden = visibility-only). Vocabulary split + build land in the Stage-2 hub/preset/nav walk. |
| **L-4** C-1 cluster (no envelope / slash bypass / no seam) | **Covered** | Spec **02** — single `resolve()` seam + `from_exception` envelope + all-six-surface funnel + AST no-skip fence. **RETIRED.** Fabricated-cite leg fixed by specs **01/03**. |
| **L-5** Panel = a second, cooldown-free resolver | **Covered** | Spec **02** — component/selector adapters build a `ResolveRequest`; cooldown read off `target.spec` for every surface. Spec **01** P6 `action_cooldown_parity` fence. *(Route-through-C-1 vs PanelActionSpec-own-fields grammar fork = owner-gated SF-a.)* |
| **L-6** Deploy-overlap double-fire (residual) | **Covered** | Multi-spec class fix: spec **02** step-0 drain gate on all surfaces + dispatch idempotency (interaction/prefix/NL legs); spec **07** `DURABLE_ONCE` (workflow lane); spec **08** `ON CONFLICT` (event-delivery leg); spec **05** the `IdempotencyKey`/`once()` primitive (T2-2 shape). Fixes every listener class at once. |
| **L-7** One-pipe-two-producers (C-2) premise false | **Covered** | Spec **06** — `sb_drafts` keyed `draft_id` + `(producer, owner_scope)`; 10 ops persist as 10 rows; Accept = AND-over-refs; dead `preflight_operations` deleted. All legs **RETIRED.** |
| **L-8** Restart-safety of tasks/timers unbuilt | **Covered** | Spec **09** — durable `sb_due_queue` + `ManagedTaskSpec` durability/misfire/catch-up + durable one-shots + `reconcile_on_boot` + always-on `PollSupervisor`. **CLOSED.** |
| **L-9** No outbox / commit-then-emit outside txn | **Covered** | Spec **08** — `event_outbox` + in-txn `enqueue`/`enqueue_audit_action` + relay. Spec **07** closes the central-audit-trace crash-loss leg via the durable twin. **CLOSED.** |
| **L-10** CUT-1 data plane undefined / ambient prod DSN | **Covered** | Spec **05** — the **4th kernel rail** `assert_data_plane()` refuses boot on a non-`test` DSN without prod attestation. **RETIRED** (persistent test Postgres = the CUT-1 ops step). |
| **L-11** Proving model has no lane for its own redesigns | **Covered (structural half) + Carried** | Spec **01** delivers snapshot⇄runtime⇄remote parity (leg A/B/C). The **intended-divergence golden lane** + capture-date/freeze policy are carried to the **Phase-0.5 golden-capture gate** (FJ §3). |
| **L-12** Owner-override gaps | **Covered** | Spec **04** — channel-access consults owner tier; ~11-16 seams → one `owner_override_holds`; transparency audit designed. Spec **02** threads it at resolve step 1. *(Sink policy owner-gated §8-c.)* |
| **L-13** Authority vocabulary two-lanes vs one-label | **Covered** | Spec **04** retires it to **one `authority_ref`** + the lane-resolution table (Q-0237d); spec **02** consumes the single ref. |
| **L-14** Shared-verb inputs / caps / deep-links | **Covered** | Spec **03** (algorithm half) — computes over the live expanded corpus, bakes the cap budget, enumerates nav-nodes first. Spec **01** (mechanism half) — `projections.namespace` is the derived corpus. |
| **L-15** Fragmentation collapses under-sized | **Out-of-scope (Stage-2) — foundational hooks provided** | Each family collapses during its **Stage-2 subsystem port** with its own acceptance oracle (FJ §2 durable fix). Foundational grammar hooks exist: `CooldownSpec` (02), cache-observability via `MetricSpec` (05), ephemerality resolver T2-17 (02), two-field description T2-16, `CacheSpec` storage (deferred to strand-3). |
| **L-16** Media ships with its highest-risk control undesigned | **Covered (probe/grammar) + Carried** | Spec **10** — class-11 `cost_posture` grammar + `check_cost_posture` Phase-1 + media default-OFF (`FAIL_CLOSED`-until-a-counter-binds). The **spend-counter build** is carried to **T2-15 / Media L4** subsystem. |
| **L-17** Discord platform-governance growth gate | **Covered** | Spec **14** (product leg — slash-first survivability + intent-denial fallback ladder + verification milestone) + spec **05** (intent rail `IntentSpec`/`assert_intents`). Together fully closed. |
| **L-18** Backup/DR + rollback don't survive cutover | **Covered** | Spec **13** — all three legs (backup port + de-repo-bind; verified-restore gate; derived-`rollback_class` disposition). Verified-restore leg co-owned with spec **11**. |
| **L-19** No security/abuse review class | **Covered** | Spec **10** — rubric classes 11/12/13 + the pre-Gate-0 adversarial-abuse pass. **RETIRED (design);** adoption owner-gated T-1. |
| **L-20** Multi-user interaction never verified | **Carried** | **Gate-V requirement** — the multi-actor golden class (challenge→accept→interleave→settle) lands before Phase-0.5 golden capture (FJ §3). A proving-harness dimension, not one of the 14 specs. |
| **L-21** Frozen-reference integrity exhortation-only + old-bot drift | **Carried** | **Gate-0** frozen-path CI guard + **Stage-3 consolidation** old-bot corpus/goldens change-policy. Spec **12** explicitly disclaims it ("no supply-chain leg — L-21 is not mine"). |
| **L-22** Navigation machinery is guild-blind under presets | **Carried** | Stage-2 **NavigationSpec** takes `(manifest × guild visibility)`; **un-excludable setup/admin nodes** = the T3 stress addition + Q-0232 amendment. Spec **04** explicitly disclaims it ("L-22 not mine"). |
| **L-23** Discord-side slash-permission overrides invisible to import | **Covered** | Spec **14** — CUT-2 permission census (bot-token-readable) + rename→preservation partition + carry-verify + admin-notice. |
| **L-24** Presentation-substrate riders (alt-text / i18n / allowed_mentions / Modal / fonts / autocomplete) | **Covered (partial) + Carried** | Spec **10** names the send-egress `ChannelEmitter` primitive (allowed_mentions mass-ping vector) + alt-text as a Gate-0 field. The rest (i18n seam, ModalSpec-under-guarantees, bundled fonts, autocomplete) are **carried to Gate-0 as declared grammar fields** (FJ §3). |
| **L-25** Audit-artifact defects (process) | **Covered (fabricated-cite leg) + Carried** | Spec **01** corrects the fabricated `contracts.py:48-52`/`WorkflowResult` cite (with **03**). The 3 audit-B placeholder rows = **fix-on-sight** next docs session (FJ durable fix); validator lesson carried. |

---

## Table 2 — Surviving §4 gaps (items 1–17)

| # | Gap | Disposition | Retired / carried by |
|---|---|---|---|
| 1 | ★ Platform-governance growth gate (= **L-17**) | **Covered** | Spec **14** + **05** (see L-17). |
| 2 | ★ Rollback destroys post-cutover data (= **L-18**) | **Covered** | Spec **13** + **11** (see L-18). |
| 3 | ★ No security/abuse review class (= **L-19**) | **Covered** | Spec **10** (see L-19). |
| 4 | ★ Multi-user interaction never verified (= **L-20**) | **Carried** | Gate-V multi-actor golden class (see L-20). |
| 5 | ★ Frozen-ref write-enforcement + old-bot policy (= **L-21**) | **Carried** | Gate-0 CI guard + Stage-3 line (see L-21). |
| 6 | ★ Permission-override config invisible (= **L-23**) | **Covered** | Spec **14** (see L-23). |
| 7 | Production data never audited or repaired | **Covered** | Spec **11** — declared invariants + always-on report-only sweep + CUT-2 verify-import (stage 3.5, baseline draw, stop-codes, scoreboard). **CLOSED.** |
| 8 | Owner is the plan's serial bottleneck | **Carried** | Stage-3 consolidation throughput policy + the **T2 co-test throughput** stress addition (batch-by-hub, sign flows not commands). |
| 9 | No user-facing change-communication mechanic | **Carried** | Stage-3 / CUT-3 comms plan (progressive ring + admin-notice). Specs **13** (M2 compensation ledger → guild-admin notice) and **14** (P-3 admin-notice) **FEED** it. |
| 10 | Credential lifecycle | **Covered** | Spec **12** — recovery arm (tiered cadence + `check_rotation_due` + revocation carve-out + blast-ordered compromise runbook) + `CredentialSpec` + owner-independence invariant. **RETIRED (design);** legs CL-1/CL-2 owner-flagged. |
| 11 | Ungoverned prod-data copies in the proving pipeline | **Covered (correctness) + Carried (retention)** | Spec **11** verify-import is the correctness checkpoint; spec **13** states the copy-site posture (runner-ephemeral / no artifact / minimal perms). The **retention/erasure lifecycle** of snapshots is carried to rubric **class 12** / Gate-0-CUT-2. |
| 12 | Dependency supply chain | **Covered** | Spec **12** — deterministic posture (lockfile + hashes + `check_lockfile_fresh` + `pip-audit` + `>=`-ceilings; lock-diff = the deferred human review). **RETIRED (design);** CL-3 owner-flagged. |
| 13 | Owner-consumable review artifacts | **Carried** | **Gate-0** (FJ §4 routing). *(This very map is a first instance of rendering a decision-checkpoint for the owner.)* |
| 14 | Field-signal intake post-cutover | **Carried (weak — watch-list)** | "Standing owner awareness" (FJ §4). No binding gate yet — see watch-list. |
| 15 | Gate failure branches | **Covered (canary arms) + Carried** | Named-canary failure arms retired by spec **07** (farm-collect), **08** (outbox durability), **09** (version-bump). The **program-level abort/fallback criterion** is carried to Stage-3 consolidation. |
| 16 | Continuity of workflow across the migration | **Carried** | Stage-3 consolidation (idea pipeline, routines, dual-repo interim, off-Discord surfaces, kit publication). |
| 17 | Model-availability contingency | **Carried (weak — watch-list)** | "Standing owner awareness" (FJ §4). No binding artifact — see watch-list. |

---

## Table 3 — Owner-decision queue, Tier-1 (T1-1 … T1-7) — all resolved Q-0237(a–g)

| # | Decision | Disposition | Retired / carried by |
|---|---|---|---|
| T1-1 | Hide-vs-disable / preset-exclusion semantics | **Carried** | Resolved **Q-0237a** (visibility-only). Build = Stage-2 hub/preset walk. |
| T1-2 | Restart-safe Back-path medium | **Carried** | Resolved **Q-0237b** (in-session stack + semantic-parent fallback). Build = Stage-2 NavigationSpec. |
| T1-3 | Admin gating model | **Carried** | Resolved **Q-0237c** (hidden node inside the unified hub). Build = Stage-2 hub. |
| T1-4 | Authority declaration vocabulary | **Covered** | Spec **04** retires to one `authority_ref` (Q-0237d); spec **02** consumes. |
| T1-5 | Slash-cap policy | **Covered** | Spec **03** — slash-common + prefix-long-tail; 100/25/1-nest budget baked into the K1 cap algorithm (Q-0237e). |
| T1-6 | Deep-link canonical names | **Covered** | Spec **03** — `!admin`/`!games` canonical, shipped `-menu` → hidden aliases (Q-0237f). |
| T1-7 | Stage-2 contract adoption | **Carried** | Resolved **Q-0237g** (adopt Codex-4 kit as-is). A Stage-2 process contract, not a spec build. |

---

## Table 4 — Owner-decision queue, Tier-2 (T2-1 … T2-22)

| # | Decision | Disposition | Retired / carried by |
|---|---|---|---|
| T2-1 | Atomic-apply meaning for non-rollback-able Discord ops | **Covered** | Specs **06** + **07** — per-op-atomic via `run()`; resource creates = post-commit EFFECT legs; cross-op all-or-nothing dropped as default. Reconciled identically. |
| T2-2 | Deploy-handoff: fast-release + idempotency keys | **Covered** | Spec **05** (`IdempotencyKey`/`once()` + fast-release handoff) + **07** (workflow lane) + **08** (event-delivery half). |
| T2-3 | Internal event durability tiers | **Covered** | Spec **08** — `EventSpec.delivery{BEST_EFFORT, AT_LEAST_ONCE}` + in-txn outbox (membership = OD-1, owner-gated). |
| T2-4 | Error-envelope home | **Covered** | Spec **02** — `from_exception` in `kernel/interaction`, all rungs. **RETIRED.** |
| T2-5 | Which actions MUST use preview/confirm | **Covered** | Spec **06** — `requires_confirmation` (destructive ∨ AI ∨ bulk/compound) + structural `verify_confirmation` gate. |
| T2-6 | ManagedTaskSpec durability fields | **Covered** | Spec **09** — durability/misfire/catch-up/grace/scope/max_catchup + the durable due-queue. |
| T2-7 | Payload-version-mismatch policy | **Covered** | Spec **09** — `VersionPolicy{UPCAST, REJECT_AND_PRESERVE, DROP}` + `resolve_versioned_load` + fence. *(Default owner-gated → OD-1.)* |
| T2-8 | Per-tenant guild lifecycle (C-8) | **Covered (seam) + Carried (wiring)** | Spec **09** provides `cancel_scope(guild_id)` guild-leave reclaim + compensation seam; the **full C-8 per-tenant orchestration wiring** is carried (T2-8's own bounded deferral, 09 §9). |
| T2-9 | Per-guild enablement gate at C-1 | **Covered** | Spec **02** — `enabled_when: PredicateRef` checked in the validate step for every surface. **RETIRED.** |
| T2-10 | Owner-override wording + transparency sink + fallback | **Covered** | Spec **04** (member-guild predicate + `TransparencyAudit` sink) + spec **02** (conditional emit). *(Sink policy owner-gated §8-c.)* |
| T2-11 | NL-router model (universal vs curated opt-in) | **Carried (Gate-0) — funnel provided** | Spec **02** funnels all NL through `resolve()` (the mechanism); the **per-command NL-eligibility slot** is a Gate-0 CommandSpec grammar decision. |
| T2-12 | Custom-trigger kinds (prefix / word→command) | **Covered (gate + kinds) + Carried** | Spec **03** — `check_trigger` set-time gate + both kinds named; the **storage schema + additive-union runtime** is the Stage-2 invocation subsystem's (T2-12). |
| T2-13 | Single-process ADR-001 as named non-goal | **Covered** | Spec **05** — carried forward explicitly as a non-goal + runtime-lock single-writer. |
| T2-14 | DB-down posture | **Covered** | Spec **05** — `DBUnavailable(ConnectionError)` + refuse-with-notice CRUD + readiness 503. |
| T2-15 | Media posture bundle (budget / spend counter / PII / fail-closed / cache) | **Covered (grammar) + Carried (build)** | Spec **10** — `cost_posture` grammar + fail-closed default + PII probe. Spend-counter **build** carried to Media L4. |
| T2-16 | C-7 description scope + 100-char limit | **Carried (Gate-0)** | Two-field description (short + detail), one source — a Gate-0 grammar-freeze decision; the resolver already consumes ParamSpec/description reads (02). |
| T2-17 | Ephemerality / silent-vs-reply home | **Covered** | Spec **02** — `resolve_reply_visibility` over all five outcomes, lane-driven. **RETIRED.** |
| T2-18 | custom_id static-stable + dynamic-versioned model | **Covered** | Spec **01** — P3 (via K1 `validate`) enforces two-population disjointness once the owner ratifies. |
| T2-19 | Native Discord onboarding/server-template interop | **Covered** | Spec **06** — draft primitive independent of Discord-native templates; interop one-directional. Boundary documented → **RETIRED.** |
| T2-20 | G-22 staging lanes | **Carried (Stage-3)** | Still open, carried from Stage-1 §6; "must not slip past Stage 3." |
| T2-21 | Idempotency posture mandate per mutating action | **Covered** | Spec **07** — `IdempotencyPosture` required field + compiler fence + 4 postures. **CLOSED.** |
| T2-22 | ConfigSpec/SecretSpec + gateway-intent contract | **Covered** | Spec **05** — grammar + preflight + `assert_intents` (intent claim verified against source); spec **01** consumes the ConfigSpec preflight boot-order seam. **RETIRED.** |

---

## Table 5 — Owner-decision queue, Tier-3 batch (bless the defaults at Gate-0)

| Item | Disposition | Retired / carried by |
|---|---|---|
| A#7 missed-window coalesce | **Covered** | Spec **09** — `MisfirePolicy.COALESCE` default + `FIRE_ALL`/`SKIP` opt-ins. |
| A#19 energy stays separate from C-6 | **Carried** | Gate-0 batch-bless (architecture default). |
| A#20 C-6 tiers optional | **Carried** | Gate-0 batch-bless. |
| A#21 MetricSpec yes | **Covered** | Spec **05** — `MetricSpec` + `LabelSpec` + registry + cardinality gate. |
| A#22 CacheSpec yes | **Covered (observability) + Carried** | Spec **05** declares cache-metric families now; the **storage grammar** deferred to strand-3. |
| A#23 /ready + lock-as-restart-seam | **Covered** | Spec **05** — DB-aware `/ready` (STARTING flips 200→503, semantics-change flagged) + runtime-lock restart seam. |
| A#24 ParamSpec first-class | **Covered (consumed) + Carried** | Spec **02** consumes ParamSpec in validate step 2b (argument validation); first-class-status bless = Gate-0 batch. |
| A#26 left-behind side-effects without a saga | **Covered** | Specs **07/09/11/06** — `compensator`-if-declared-else-record-finding (the blessed no-saga default); `WorkflowRef` is the forward seam. |
| A#28 drop dead staged-rollout machinery | **Carried** | Gate-0 batch-bless (decision = do not build). |
| A#29 keep generic env-override tier | **Carried** | Gate-0 batch-bless (ConfigSpec env-override tier, 05). |
| A#30 kit import renamed `substrate_kit` | **Out-of-scope** | The D-4 substrate-kit (correctly parallel; nothing in Stages 2-3 waits on it). |
| A#15 member-erasure in phase-1 grammar, executed post-cutover | **Covered** | Spec **10** — the member-erasure executor (`erasure.py`) + `data_class`/`erasure_ref` grammar; on_guild_remove wiring deferred to Stage-3. |
| B#12 card themes/uploads as declared theme packs | **Carried** | Gate-0 batch-bless. |
| B#13 did-you-mean privacy | **Covered (seam) + Carried** | Spec **02** `NLProvenance` feeds the did-you-mean-privacy seam; invoker-locked carrier policy = Gate-0 batch. |
| C2-Q5 fuzzy safety from manifest `effect` field | **Covered** | Spec **02** §9 — fuzzy AUTO-safety derived from the `effect` field, never a hand-list. |
| C2-Q7 moderation-envelope spot-check | **Carried** | Gate-0 batch-bless (timeout + one of kick/ban). |
| CUT-3 rollback window N | **Covered (mechanism) + Carried (value)** | Spec **13** designs the derived-`rollback_class` mechanism N drives; the **value of N** = owner Stage-3 carry. |

---

## Table 6 — Stress/critic-pass additions

| Item | Disposition | Retired / carried by |
|---|---|---|
| Rollback-data disposition (reverse-import / replay / declared-loss) | **Covered** | Spec **13** — the derived-`rollback_class` tiered contract + reverse-import valve + M1/M2 manifest + playbook (posture = Q3, owner). |
| CUT-1 data-plane rail | **Covered** | Spec **05** — the 4th rail `assert_data_plane()` (see L-10). |
| Golden capture timing + old-bot freeze/change policy | **Carried** | Phase-0.5 golden-capture gate (capture-date pin) + Stage-3 old-bot change-policy (= L-11 / L-21 legs). |
| Guild-sovereignty over member triggers | **Carried** | Stage-2 invocation subsystem + the Q-0225 amendment (a guild-scope disable winning over narrower scopes); spec **03** keeps the additive union as the resolver's, not K1's. |
| Co-test throughput policy | **Carried** | Stage-3 / release-testing loop (batch by hub; sign flows, not every command). |
| Phase-2.5 cold-start A/B vs D-4 gate | **Carried** | One Stage-3 line (fold / supersede / schedule the competing pre-bootstrap gate). |
| Progressive-exposure ring + CUT-3 user comms | **Carried** | Stage-3 / CUT-3 comms plan; specs **13/14** feed the admin-notice half. |
| Un-excludable hub nodes (preset self-lockout guard) | **Carried** | Gate-0 / Stage-2 NavigationSpec — setup/admin nodes un-excludable by construction (= L-22). |

---

## Residual V-3 watch-list — homed, but on the softest binding

These nine rows are **carried, not evaporated** — but their only home is a **Stage-3 consolidation
line** or **"standing owner awareness,"** the two weakest bindings in the closure set. They are the
rows most at risk of the exact drift V-3 exists to prevent, because no spec, gate, or CI check owns
them yet. Recommend each gets a firmer artifact (a Gate-0 checklist row or a Stage-3 plan section
with an owner) before Stage 2 closes:

1. **§4 #8** — owner serial bottleneck (Stage-3 throughput policy).
2. **§4 #13** — owner-consumable review artifacts (Gate-0; partially self-addressed by this map).
3. **§4 #14** — field-signal intake post-cutover (*standing owner awareness only* — weakest).
4. **§4 #16** — workflow continuity across the migration (Stage-3 consolidation).
5. **§4 #17** — model-availability contingency (*standing owner awareness only* — weakest).
6. **T2-20** — G-22 staging lanes (open since Stage-1; "must not slip past Stage 3").
7. **Stress** — co-test throughput policy (Stage-3 / release-testing).
8. **Stress** — Phase-2.5 A/B vs D-4 gate (one Stage-3 line).
9. **Stress** — progressive-ring + CUT-3 comms (Stage-3 / CUT-3).

The two starred *"standing owner awareness"* rows (#14, #17) are the softest of all: they have no
stage, gate, or register — only the judgment ledger's prose. If any row in the whole set is going to
evaporate, it is one of these two. **Not a V-3 violation today** (FJ §4 dispositions them and this map
now registers them), but the recommended fix is a one-line home upgrade.

---

## Out-of-scope roster (2)

| Row | Why out-of-scope |
|---|---|
| **L-1 → V-1** (the immediate RPS PR) | The one-off fix is an immediate owner-directed PR, not this foundational design (the durable *class* fix is spec 09; see L-1 covered). |
| **L-15 / A#30** | L-15 fragmentation collapse is Stage-2 subsystem work (per-family acceptance oracles at porting; foundational grammar hooks provided by 02/05). A#30 substrate-kit rename is the parallel D-4 kit. |

---

## Pointers

- Judged ledger: `../final-judgment-fable5-2026-07-03.md` (§2 L-rows · §4 gaps · §6 owner queue).
- The 14 retirement maps: strand-1 (`01`–`05`) §10 · strand-2 (`06`–`09`) §10 · strand-3 (`10`–`14`) §5.
- Shared vocabulary (SF-forks, RC-reconciliations): `shared-vocabulary.md`.
- **V-3 rule of use:** when a Stage-2 row or a Gate-0 checklist item is written, it must name the
  L-row(s) / queue item(s) it retires, and this map is the completeness backstop that no row was
  dropped. Source and the specs' own retirement tables win over this roll-up (Q-0120).

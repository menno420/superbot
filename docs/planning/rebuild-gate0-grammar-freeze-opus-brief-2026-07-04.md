# Opus 4.8 ultracode — the Gate-0 grammar-freeze + Phase-B L0 build-order session (brief)

> **Status:** `plan` — **preparation only** (owner-directed). A single paste-ready **Opus 4.8
> ultracode** prompt for the step *after* the foundational-design bridge (#1708). Its job: take the 14
> buildable kernel specs + the frozen shared vocabulary + the 31-row question register, and **freeze
> Gate-0** — consolidate every pinned grammar-field addition into ONE ratifiable frozen grammar,
> resolve the register's mechanically-decidable rows to their built defaults, close the pending
> cross-spec wiring, design the still-thin L-24 riders to depth, produce the **owner-decision packet**
> for the 12 genuinely owner-only calls, and sequence the **Phase-B L0 build order**. **Not launched
> from this preparing session** — the owner pastes it into a fresh Opus 4.8 (max reasoning) ultracode
> session. Source wins over any doc (Q-0120).
>
> **Grounding:** the Appendix + the committed companion
> [`rebuild-gate0-worklist-2026-07-04.md`](rebuild-gate0-worklist-2026-07-04.md) were harvested this
> session from the *shipped* design specs (Q-0120) by a 3-agent workflow — the fold list (87
> primitives / 18 attach-points), the register disposition (19 ratify-default / 12 owner-only), and
> the L0 build order (16 steps). The Gate-0 session starts from that grounded work-list, not memory.

---

## ⚡ Quick launch (paste into a fresh Opus 4.8, max-reasoning, ultracode session)

```text
ultracode: Read docs/planning/rebuild-gate0-grammar-freeze-opus-brief-2026-07-04.md in full — execute its "THE PROMPT" section verbatim, using its companion work-list (docs/planning/rebuild-gate0-worklist-2026-07-04.md) as your grounded start index and the 14 shipped design specs as source-of-truth (Q-0120).
```

*(Set the session to Opus 4.8 at max reasoning before launching.)*

---

## What this session is (and is not)

The foundational-design bridge (#1708) produced **14 buildable kernel specs**, a **frozen shared
vocabulary**, a **seam-consistency matrix**, a **retirement-coverage map** (0 evaporations), and a
**31-row question register** — under
[`docs/analysis/rebuild-discovery/foundations/design/`](../analysis/rebuild-discovery/foundations/design/README.md).
Its own README §6 says the design **feeds two gates and hands off a third**. This session executes the
first gate + prepares the second.

- It is a **CONSOLIDATE + RATIFY + PLAN** session. It does **not** redesign the specs' owned shapes
  (those are frozen); it **gathers** every pinned grammar addition scattered across the 14 specs into
  ONE authoritative, ratifiable frozen grammar; **resolves** the register (freeze the safe defaults,
  render the owner-only calls); and **sequences** the L0 build. It is **docs/spec** — the fresh-repo
  `sb/` package does not exist yet, so "freeze the grammar" = produce the *authoritative, code-ready
  grammar specification*, not the code.
- It is **NOT the new-repo bootstrap / MIGRATION plan** (deferred — a separate later effort), **NOT
  the Stage-2 subsystem walk** (owner-led, independent of this L0 work), and it does **NOT decide the
  12 owner-only register rows** (it renders them for the owner; it never rules).

**Why it can run now:** the design bridge already froze the contracts; every register row already
carries a *built default* so the build is unblocked today; Gate-0 is the "one sitting" that blesses
the consolidation and turns 14 cross-referenced specs into one grammar a builder reads top-to-bottom.

## The work — 6 deliverables

**① The frozen L0 grammar** (the linchpin): every pinned field/primitive from the 14 specs, folded
into ONE authoritative manifest-grammar specification (design-spec §2/§3 extended), each field with
its exact type/default/[S·A·O] role and the L-row/RC/Q-D it retires. ~87 primitives across 18
attach-points (Appendix A). · **② The amendment registry** — build `rebuild-amendments.yml` + its
uniqueness checker FIRST (spec 01 §3.7), the collision-free minting authority that flips G-9…G-24 from
pending-gate-0 families to in-grammar (it is a Gate-0 *prerequisite*, not an afterthought). · **③
Close the pending cross-spec wiring** — the small absorptions the specs flagged but did not land:
`ActorRef.member_tier` onto spec 02 (RC-12 — without it the TIER lane can't resolve), the spec-02
absorption of 04's authority contracts (RC-2/3/4/5/12/13/14/15), `WorkflowContext.test_mode` onto spec
07, and register the `ChannelEmitter` egress port (RC-21). · **④ Resolve the register** — freeze the
**19 RATIFY-DEFAULT** rows to their built defaults (Appendix B), and render the **12 OWNER-ONLY** rows
(+ L-21) into an **owner-decision packet** — options + recommendation + blast-radius, owner-consumable
(visual, not a prose wall), so the owner rules in one sitting. · **⑤ Design the L-24 riders to depth**
— alt_text, locale seam, allowed_mentions policy, ModalSpec (amendment G-10), bundled fonts are named
as Gate-0 fields in README §6 but are *declared-field-only* in the 14 specs; pin their exact shapes. ·
**⑥ The Phase-B L0 build-order plan** — the 16-step sequence (Appendix C) as one plan: provides/
consumes per step, K0–K10 slot, the applied seam reconciliations, and where each of the 14 specs lands.

---

## THE PROMPT — Gate-0 grammar freeze + Phase-B L0 (paste as its own Opus 4.8 ultracode session)

```text
ultracode: You are Opus 4.8 at maximum reasoning, running a GATE-0 GRAMMAR-FREEZE + PHASE-B L0 BUILD-ORDER session for the SuperBot rebuild. The foundation was audited (#1690/#1691), judged (#1701), and DESIGNED to buildable depth (#1708 — 14 kernel specs + a frozen shared vocabulary + a seam-consistency matrix + a retirement-coverage map + a 31-row question register, under docs/analysis/rebuild-discovery/foundations/design/). Your job is the next step that README §6 names: CONSOLIDATE every pinned grammar addition into ONE ratifiable frozen grammar, RESOLVE the register, and SEQUENCE the Phase-B L0 build. This is a CONSOLIDATE + RATIFY + PLAN session — NOT a redesign of the frozen specs, NOT the new-repo bootstrap/migration, NOT the Stage-2 subsystem walk, NO code (the fresh-repo sb/ package does not exist yet — "freeze the grammar" = the authoritative, code-ready grammar SPECIFICATION). Follow .claude/CLAUDE.md: claim your lane, open a born-red session-card PR immediately, let it auto-merge on green. SOURCE WINS on facts (Q-0120): the 14 shipped specs win over any summary — re-verify against them.

READ FIRST (the work-list is already harvested + grounded — consume it, do not re-discover):
- The grounded start index: docs/planning/rebuild-gate0-worklist-2026-07-04.md — Part 1 the grammar fold list (87 primitives / 18 attach-points, each with type/default/role + what it retires), Part 2 the register-row disposition (19 RATIFY-DEFAULT vs 12 OWNER-ONLY, with the built default + rationale per row), Part 3 the Phase-B L0 build order (16 steps S0-S15, provides/consumes). START each deliverable from its Part.
- The deliverable you consolidate: the 14 specs' §3 public contracts + §11 build orders (docs/analysis/rebuild-discovery/foundations/design/strand-*/), the frozen shared-vocabulary.md (the 7 recurring contracts + the source-wins grounding), the seam-consistency-matrix.md (the RC-1..RC-21 reconciliations + the applied forks), the retirement-coverage-map.md (V-3 — every L-row/queue-item's home), and the question-register.md (the 31 Q-D rows with options+recommendation+tier+owner-gating).
- The grammar you freeze INTO: docs/planning/rebuild-design-spec-2026-07-02.md §2 (manifest grammar), §2.7 (Result grammar), §2.8 (the taxonomy primitives), §3 (namespace), §9 (build order K0-K10), §10.2/§10.3 (ratification + operational contracts).
- The frozen decisions you ratify AGAINST (never re-open): router Q-0219…Q-0237 incl. the 7 Tier-1 answers Q-0237(a-g); the amendment families G-1…G-24 (spec 01 §3.7).

SCOPE - IN (six deliverables, each to buildable/ratifiable depth):
1. THE FROZEN L0 GRAMMAR: fold every pinned field/primitive (work-list Part 1 - verify each against its owning spec's §3) into ONE authoritative manifest-grammar specification extending design-spec §2/§3. For each: exact type, default, [S]/[A]/[O] role, one-line semantics, and the L-row/RC/Q-D it retires. Group by attach-point (the 18 groups). Every field a builder needs in one place, cross-referenced to its owning spec - so a fresh agent builds the sb/spec/ dataclasses from THIS, not from 14 specs.
2. THE AMENDMENT REGISTRY (the prerequisite - do this first): specify rebuild-amendments.yml + its uniqueness checker (spec 01 §3.7) as the collision-free minting authority; enumerate G-9…G-24 (the pending grammar families: DeferredActionSpec, ModalFormSpec G-10, etc.) with their reservations so the fold flips them in-grammar without a name collision.
3. CLOSE THE PENDING CROSS-SPEC WIRING (the absorptions the specs flagged): ActorRef.member_tier onto spec 02 (RC-12 - the TIER lane can't resolve without it); spec-02 absorbs 04's frozen authority contracts (RC-2/3/4/5/12/13/14/15) so it stops being written to pre-hardening shapes; WorkflowContext.test_mode onto spec 07 (06 §12's flagged seam); register the ChannelEmitter egress port on 02/K8 (RC-21). Apply these as precise spec edits.
4. RESOLVE THE REGISTER: freeze the 19 RATIFY-DEFAULT rows (work-list Part 2.A) to their built defaults, recording each as ratified. RENDER the 12 OWNER-ONLY rows (Part 2.B) + L-21 into an OWNER-DECISION PACKET: per row = the call, options, recommendation, blast-radius/why-owner-only, and the register-Q it answers. Owner-consumable - option/recommendation rows, tight, scannable; the maintainer cannot code and rules from this packet. NEVER decide an owner-only row yourself.
5. DESIGN THE L-24 PRESENTATION RIDERS to buildable depth: alt_text, the locale/i18n seam, the allowed_mentions default policy, ModalSpec (amendment G-10, ties to the from_error guarantee), and bundled-fonts - named as Gate-0 declared fields in README §6 but declared-field-only in the 14 specs. Pin exact shapes (field/type/default/role + where each attaches).
6. THE PHASE-B L0 BUILD-ORDER PLAN: turn work-list Part 3 into one plan - the 16-step sequence, each step's spec(s) + provides + consumes + K-slot, the applied seam reconciliations (F-1 09 hosts the outbox lanes; F-2 draft run() caller-type; the GLOBAL slot-key + fence-scope blockers), and the dependency graph. This is the plan the (later, separate) new-repo build executes.

SCOPE - OUT (hard fences):
- NOT a redesign - do not re-open a shape a spec owns; consolidate + ratify, correcting only a genuine mis-cite (Q-0120) or a flagged pending-wiring gap.
- NOT the new-repo bootstrap / MIGRATION plan (deferred) and NOT code - produce the authoritative grammar SPECIFICATION, not sb/ files.
- NOT the Stage-2 subsystem walk - no per-subsystem command naming / keep-merge-drop / hub topology. Stage-2 consumes the frozen grammar; it is owner-led and independent.
- Do NOT decide the 12 owner-only rows (Q-D5/8/13/14/15/16/17/19/20/21/18/24 + L-21) - render them; the owner rules. Do NOT re-litigate the frozen Q-0219…Q-0237 (flag-with-evidence, never reverse).

METHOD (make the workflow do this):
1. INGEST the work-list (the 3 parts) as the grounded index; SPOT-VERIFY each pinned field against its owning spec's §3 before folding it (the fold is only as good as its source-fidelity - Q-0120).
2. Build the amendment registry FIRST (deliverable 2) - the fold (deliverable 1) mints into it.
3. FAN OUT one consolidation agent per attach-point group (the 18 groups) -> its slice of the frozen grammar; one agent for the register resolution + owner packet; one for the L-24 riders; one for the L0 build plan.
4. ADVERSARIAL-COMPLETENESS critic: is EVERY work-list-Part-1 field folded (none dropped)? is EVERY register row dispositioned (19 frozen + 12 rendered, none missed)? is the amendment registry collision-free? does the frozen grammar agree with the shared-vocabulary + the applied RCs? A found gap means it isn't done.
5. RATIFICATION-READINESS pass: the frozen grammar + the owner packet are the inputs to the owner's Gate-0 sitting - confirm they are self-contained and owner-consumable (a builder needs zero further design decisions from the grammar; the owner needs zero code-reading from the packet).
6. HARVEST any decision the consolidation surfaces that is NOT already a register row into the owner packet (net-new Gate-0 forks) - loop the critic until two rounds add nothing.

DELIVERABLE - land under docs/analysis/rebuild-discovery/foundations/gate-0/ (sibling of design/), organized as: THE FROZEN L0 GRAMMAR (grouped by attach-point, cross-referenced to owning specs) · THE AMENDMENT REGISTRY spec · THE OWNER-DECISION PACKET (the 12 owner-only + L-21, owner-consumable) · THE PHASE-B L0 BUILD-ORDER PLAN · a front-matter README (what got frozen, what the owner must rule, the design->grammar retirement continuity). Update the design/ question-register + retirement-coverage-map to mark the rows this session ratifies/retires (V-3 continuity - nothing evaporates). Every deliverable owner-consumable (option+recommendation rows, contract tables). Position it as the input to the owner's Gate-0 ratification sitting + the (later) new-repo Phase-B L0 build.

GUARDRAILS: SOURCE WINS (Q-0120) - re-verify each folded field against its owning spec; correct any mis-cite. Consolidate, do not redesign. Owner-only = render, never decide. Docs/spec only, no code, no new-repo bootstrap. Do NOT pad (Q-0089 bar): where a spec already states a field's final shape, fold it verbatim and move on; spend depth on the genuine consolidation seams (the amendment registry, the pending wiring, the L-24 riders, the owner packet). Output owner-consumable.
```

---

## Appendix — the grounded work-list (curated summary; full tables in the companion)

Harvested this session against the shipped specs (Q-0120). **Full detail:**
[`rebuild-gate0-worklist-2026-07-04.md`](rebuild-gate0-worklist-2026-07-04.md). This is the design-start
index.

### A · The grammar fold (Part 1) — 87 primitives across 18 attach-point groups

~34 are field-additions onto an existing manifest spec (CommandSpec/PanelActionSpec/SelectorSpec ·
`EventSpec.delivery` · the 6 `ManagedTaskSpec` durability fields · the 7 `StoreSpec` version + 3 privacy
+ `rollback_class` fields · `IntentSpec.posture/degrades` · the 8+1 new `ConfigSpec` rows ·
`ActorRef.actor_type/member_tier` · `WorkflowContext.correlation_id/test_mode` · the 5 L-24 riders); ~53
are new leaves / enums / ports / tables / fences / facets (the outcomes·authority·config·events·
scheduler·versioning·credentials·invariants leaves, the error envelope, the `ChannelEmitter` port, the
idempotency/audit_log/outbox/due-queue/draft/quarantine tables, the compile fences, rubric classes
11/12/13). The single authority field `authority_ref` spans six spec types.

**The three things the Gate-0 session must handle deliberately (from the harvest):**

- **Prerequisite — build the amendment registry first.** `rebuild-amendments.yml` (spec 01 §3.7) holds
  G-9…G-24 as pending grammar families (DeferredActionSpec, ModalFormSpec G-10, …); the fold flips them
  in-grammar and MUST mint collision-free, so the registry is built before the fold.
- **Pending cross-spec wiring (not yet absorbed — land at Gate-0):** `ActorRef.member_tier` (RC-12, the
  one non-trivial one — 04 needs it, 02 lacks it) · `WorkflowContext.test_mode` (pending on 07) ·
  `ChannelEmitter` port (RC-21, registered pending on 02/K8) · the spec-02 absorption of 04's authority
  contracts (RC-2/3/4/5/12/13/14/15). `ActorRef.actor_type` + `Surface.MAINTENANCE` are already applied.
- **Reconciled — record, don't re-fork:** `DeliveryClass` home = `sb/spec/events.py` (RC-17) ·
  `correlation_id` = a DB **column** on audit_log, not a 12th bus field (RC-16) · `Surface.MAINTENANCE`
  the single shared background member (closes 11 Q4). **Depth-ambiguous (Gate-0 pins the shape):** the
  L-24 riders are declared-field-only; `rollback_class` is `[DERIVED]` off an unratified `StoreSpec`
  extension; ModalSpec ties to amendment G-10.

### B · The register disposition (Part 2) — 19 ratify-default · 12 owner-only (of 31) + L-21

**RATIFY-DEFAULT (19):** each has a safe/conservative built default the freeze pins without foreclosing
a later owner option; 5 are `owner-visible` (ratify + surface for awareness, non-blocking: Q-D6, Q-D7,
Q-D23, Q-D25, Q-D28).

**OWNER-ONLY (12) → the owner-decision packet:** Q-D5 (intent-denial posture, fail-closed vs DEGRADE/PG-2)
· Q-D8 (store-drop disposition — no default, owner signs per store) · Q-D13 (money-repair direction —
near-irreversible) · Q-D14 (RPO target + backup source tier) · Q-D15 (rollback-data disposition + window
N — near-irreversible) · Q-D16 / Q-D17 / Q-D19 (credential custody & recovery — narrow the binding Q-0213)
· Q-D20 (security-rubric classes 11/12/13 adoption — rubric edits are owner-directed, Q-0233) · Q-D21
(growth posture) · **+2 found this harvest:** Q-D18 (supply-chain lockfile/pip-audit gate — touches the
binding Q-0105 adopt-freely grant → router DISCUSS) · Q-D24 (multi-actor session-concurrency primitive —
kernel-level + a compile fence = the large/architectural ask-first class). **L-21** (old-bot
change-policy) is owner-only too but is an L-ledger row, not one of the 31 — flag it separately.

### C · The Phase-B L0 build order (Part 3) — 16 steps (S0–S15)

Sequenced by dependency; specs 01/05/09/02 span >1 K-slot. Backbone: **S0** the amendment registry
(pre-Gate-0) → **01** the compiler linchpin (K2) → **05**'s ConfigSpec/observability/intents (K0) +
`IdempotencyKey`/`once()`/`db.transaction()` (K3) and **04**'s authority contracts as the substrate
strand-2 depends on → the **spec-02 absorption edit** (an L0 task) → **07** (K7) underlies **06** (draft)
+ **09** (scheduler); **08** (outbox) provides durable delivery (F-1: 09 hosts the registered relay/reaper
lanes) → strand-3 (**10–14**) rides the frozen grammar + adopts the owner rulings. The applied seam
reconciliations (F-1/F-2 + the GLOBAL slot-key + fence-scope blockers) are already in-spec — wire the
composition root against the applied shapes.

---

## Pointers

- The deliverable this consolidates: [`design/README.md`](../analysis/rebuild-discovery/foundations/design/README.md) (§6 "how to consume this next") + the 14 specs + the 4 synthesis artifacts.
- The grounded work-list companion: [`rebuild-gate0-worklist-2026-07-04.md`](rebuild-gate0-worklist-2026-07-04.md).
- The grammar it freezes into: [`rebuild-design-spec-2026-07-02.md`](rebuild-design-spec-2026-07-02.md) (§2/§2.7/§2.8/§3/§9/§10).
- The judgment behind it all: [`final-judgment-fable5-2026-07-03.md`](../analysis/rebuild-discovery/foundations/final-judgment-fable5-2026-07-03.md).
- **Next after Gate-0:** the owner's ratification sitting (the owner-decision packet) → the (separate, deferred) new-repo bootstrap → the Phase-B L0 build against the frozen grammar. Stage-2 (owner-led subsystem walk) runs in parallel against the frozen contracts.

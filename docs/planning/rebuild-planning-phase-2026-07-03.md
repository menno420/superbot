# Rebuild — the review-then-plan phase (process + next-session goal)

> **Status:** `plan` — the bridge between the merged capability-audit capstone (the **frozen
> reference**: `NEW-BOT-BUILD-PLAN.md` + `FINAL-REVIEW.md`) and writing the per-step
> implementation plans. **Read this to know what the next sessions do, in what order, and why.**
> **Prepared:** 2026-07-03 (owner-directed, following PR #1674). Owner decision this session:
> *plan every step to completeness before building — but do one more content review pass first.*

---

## Where we are

- **The capstone is merged (#1674).** Its two deliverables under
  [`../analysis/rebuild-discovery/new-bot-capability-audit/findings/`](../analysis/rebuild-discovery/new-bot-capability-audit/findings/README.md)
  are the **frozen reference**:
  - [`FINAL-REVIEW.md`](../analysis/rebuild-discovery/new-bot-capability-audit/findings/FINAL-REVIEW.md)
    — verdict **GO-with-amendments** (measured all-43 fit 63.8% → 85.1%), the consolidated
    amendment list (G-1…G-24 + riders + refuted set), the danger-zone answers.
  - [`NEW-BOT-BUILD-PLAN.md`](../analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md)
    — the single dependency-ordered plan (L0 → L5), every capability with disposition,
    dependencies, done-definition, outperform target.
  These answer *what to build and in what order.* **Don't re-open them — refine downstream.**
- **The design spec** ([`rebuild-design-spec-2026-07-02.md`](./rebuild-design-spec-2026-07-02.md))
  awaits **Gate-0** (fold the G-9…G-24 amendments into §2) and **owner ratification** (the
  Phase-3 gate). **No new-repo code exists, and none starts until both land.**

## The owner's directive (2026-07-03): plan every step to completeness before building

Execute the BUILD-PLAN, but at this phase **the deliverable of each step is a plan, not code.**
Produce **one design plan per step, 100% complete, before the next begins** — every
architectural rule honored, every option weighed and decided, nothing left to figure out later.

**The file-completeness philosophy (the standing rule for every file the rebuild creates):**
*every file is designed from its first line to handle its entire eventual surface — not the slice
needed today.* No "we'll patch it when we add X." This is the **same bet as the manifest
grammar**: declare the complete surface once, generate from it, never hand-patch. The file
principle and the grammar principle are one principle — which is why this discipline fits the
rebuild rather than fighting it.

**Bounded, so "complete" doesn't become "infinite":** completeness is measured against the
**capability corpus** (the 43-subsystem surface + the named amendments + the documented
known-options), *not* open-ended speculation. A file is complete when it handles its full
*declared* surface and **deliberately defers** anything on the known-options menu with a labeled
reason. The corpus is the boundary of "everything we'd ever expect."

---

## The phase sequence

```
  [DONE] Capstone ─► [PHASE A] Content review ─► [GATE V] Verification fleet ─► [PHASE B] Per-step planning ─► [PHASE C] Build ─► [MIGRATION]
         (frozen       (owner-led review +          (multi-agent adversarial       (one 100%-complete plan         (execute plans;      (its own big
          reference)    the critical-review rubric)  pass over the finished plan)    per step, dep-ordered)          plan=source of truth) plan → new repo)
```

**Phase A is the current work.** Phases B/C + the two new markers are documented so the whole arc
is visible, but **do not start Phase B until Phase A's surface decisions are captured** — a per-step
plan cannot be "100% complete" against a surface still under discussion.

**GATE V — the verification-fleet pass (owner-directed 2026-07-03, Q-0234).** Once the plan is
*fully* done, run it past **multiple verification / research agents** to find the final
improvements before Phase B. Their shared lens is the **ten-class critical-review rubric**
([`rebuild-critical-review-rubric-2026-07-03.md`](rebuild-critical-review-rubric-2026-07-03.md)) —
so the fleet interrogates consistently instead of free-associating. This is the adversarial-
completeness pass, scaled to the whole plan. **The concrete roster + paste-ready prompts live in the
launch pad [`rebuild-gate-v-verification-fleet-2026-07-06.md`](rebuild-gate-v-verification-fleet-2026-07-06.md)**:
four independent arms — Sonnet-5/Ultracode (architecture), a 5-session Codex fan-out (source/test truth),
Agent Mode (external/migration/live-GitHub), and an empirical **live-testing** arm that captures the
`verified_live` goldens the paper reviews can't — reconciled by a final Opus/Fable synthesis. Shared
enum / evidence-labels / claim-anchor contracts make the four reports merge without manual normalization.

**MIGRATION — its own big plan (Q-0234).** The move to the new repo is a distinct planning effort,
not a Phase-C tail. The framing: **the current repo becomes the *artifact*** (the what / why / how
— the decision logs, the rubric, the frozen reference *are* its "why"); **the new repo becomes the
clean *source of truth*** that makes it real, with a proper start that structurally prevents
reintroducing old mistakes. The container-first cutover (Q-0222) is this migration's execution arm.

---

## PHASE A — the content review pass  ◄◄ IN PROGRESS (Stage 1 done)

> **Phase-A progress (2026-07-03):** the owner runs this pass as **three stages** — Stage 1
> global review → Stage 2 subsystem walk → Stage 3 consolidation. **Stage 1 is done** (owner-live
> session, PR #1679): decisions log
> [`rebuild-stage1-global-review-2026-07-03.md`](rebuild-stage1-global-review-2026-07-03.md) —
> the S-1 engine/declaration/seam standard + S-2 ordering rule (Q-0219/Q-0220), the full
> dependency-order audit (3 inversions dispositioned; welcome re-homed after the card engine),
> the D-1…D-6 Gate-0 deltas (card engine · **new media-generation capability Q-0221** · the
> **3-phase container-first cutover Q-0222** · the substrate-kit pre-bootstrap gate + per-subsystem
> triage Q-0223 · one canonical L-vocabulary), and the corrected substrate-kit state. **Stage 2
> (the subsystem walk) is the next Phase-A session's goal** — agenda in the decisions log §6.

**What it is.** One more review pass over the *whole* plan, run as **dedicated, owner-led
brainstorming / discussion sessions**, focused on the **actual surface** — the commands,
functions, and methods the new bot will expose and use. Multiple sessions; unhurried.

**Why it comes before per-step planning.** The capstone validated **feasibility** (*can we build
this durably?* — yes, 85%) and **order**. It did **not** decide the surface *content* at the
command/method level — the lane dispositions say "keep economy," not "these are economy's exact
commands, named thus, with these methods behind them." Settling that in **discussion is cheap**;
discovering it mid-plan or mid-build is expensive. This pass turns the frozen *what* into a
decided *exact surface* the per-step plans can be complete against.

**Who / how.** Owner-driven. The agent's role is **thinking-partner + decision-capturer**, not an
autonomous pass — the owner designs and visualizes the surface; the agent pressure-tests each
choice against source, the architecture rules, and the competitor targets, and records every
decision durably. (This is exactly the collaboration model: the owner brings the vision, the
agent brings the cross-checked correctness.)

**Seed agenda (the topics to walk).** Not exhaustive — a starting spine:

1. **The command surface, per subsystem.** The audit inventoried **271 commands**. For each:
   keep / merge / drop / **rename**, and the exact final name + aliases. The audit gave
   dispositions; this pass gives *names*.
2. **Prefix vs slash per surface.** The audit flagged subsystems with **zero slash commands**
   (role, channel's 17 prefix verbs). Decide the target command *kind* for each surface (the
   grammar's `CommandSpec.kind`), and where the slash-native selects retire a prefix resolver.
3. **Naming conventions + the collision class.** Two name collisions crash-looped production
   (`give` Q-0211, `dock`/`sail` BUG-0030). Decide naming conventions **now** so the K1 namespace
   registry gets clean input — the registry *enforces* uniqueness, but the human decides the
   scheme.
4. **Cross-cutting method / seam conventions.** The audited-mutation seam signatures, the
   `WorkflowResult` shape, handler-ref naming, provider-ref naming — the recurring *method*
   patterns every subsystem reuses. Decide them once here so 43 plans inherit one vocabulary.
5. **The open uncertainties** (each must be *decided* here or assigned to its owning Phase-B
   plan — see the ledger below): does `ModerationActionSpec` declare the mod-action envelope
   (lifting moderation from 64%) or do the seams stay tier-3? Can the workflow engine atomically
   compose several specs (farm-`collect` canary)? The three embedded decisions (G-22 staging
   lanes, R-12 world-store, P-1 event-feed).
6. **Hub / navigation topology.** The sim optimizes *arrangement*, but a human decides the
   *semantic* hub structure (what belongs under which hub). Decide the hub tree.
7. **The outperform targets, made concrete.** Turn "match Dyno's automod filters" /
   "beat Ticket Tool on transcripts" into the **specific feature list** each subsystem must ship
   (the done-definition's outperform half needs real items, not a competitor name).

**Output of Phase A.** An **annotated / refined BUILD-PLAN** (or a companion decisions log) that
records, per subsystem: the exact command surface, the naming, the method conventions, the hub
placement, the resolved uncertainties, and the concrete outperform feature list. This is the
input every Phase-B plan consumes.

---

## PHASE B — the per-step planning process (for when Phase A is done)

Documented now so the target is visible; **not started until Phase A's surface is decided.**

- **A fixed plan template** (the first Phase-B artifact — write it before the first plan, so every
  plan is uniform and reviewable). Mandatory sections: *files created · the complete public
  contract (every function/field/error the file will ever expose) · provides / consumes (its
  stable interface up, its frozen dependencies down) · architectural rules honored (with the
  specific INV / layer-boundary citations) · options considered and the decision + why · open
  uncertainties resolved · production-grade done-definition (which `parity/` goldens + tests) ·
  deliberate deferrals (labeled, with why) · build order within the plan.*
- **"100% complete" has a hard test:** a plan is complete when **a fresh agent with no context
  could build it from the plan + the frozen upstream contracts, making zero further design
  decisions.** Each finished plan gets an **adversarial-completeness pass** — a reviewer whose
  only job is to find one open decision; finds none → complete. (The audit's adversarial-verify
  pattern, applied to plans. It also structurally closes the Lane-D "one-agent, unverified" trust
  gap — everything gets a second set of eyes.)
- **Dependency order, contracts frozen before dependents.** You cannot write a complete blackjack
  plan while `ChallengeSessionSpec`'s fields are still moving. So planning follows the build
  order: **the grammar/kernel contracts are planned and frozen first** — the **Gate-0 grammar
  freeze is the first Phase-B plan** (fold G-9…G-24, settle `ModerationActionSpec` and the
  composition contract, freeze every spec every later plan references). Only then are L1/L2/L3
  plans complete, because they reference frozen ground.
- **Two levels, not 40 flat files.** A **layer plan** (the L0 kernel, the L1 operator spine)
  freezes that layer's shared contracts + internal sequencing; **component plans** underneath
  (one per engine, one per subsystem) are complete *against the frozen layer contract*. This is
  what makes "100% complete" tractable — a component plan can be complete precisely because
  everything above it is frozen.
- **Sequential on the spine, parallel on the leaves.** The strict "one before the next" applies
  to the **contract-freezing plans** on the dependency spine. Once a layer's contracts are frozen,
  the component plans within/below it are independent and can be written in parallel (the
  manifest-per-file design makes them collide at compile, not merge).
- **Every uncertainty is owned by exactly one plan, and its resolution is recorded there** (the
  durable-fix rule — see the ledger). Nothing floats.
- **The plans are the permanent design record, not scaffolding.** Because the manifest is
  generated, the chain is *plan → manifest → generated code*. The plan is the durable "why"
  behind each manifest; it survives every regeneration. That is why the effort pays off long
  after the first build.

## PHASE C — build (for reference)

Execute the plans as code, in the same dependency order. **The plan is the source of truth:** if
execution reveals the plan was wrong, **stop, fix the plan, then resume** — never let code
silently drift from the design (that would forfeit the whole benefit). Each contradiction found
in a cheap docs artifact instead of in shipped code is the process working.

---

## Open uncertainties → where each gets resolved (the durable-fix ledger)

Per the owner's "if it has a clear durable fix, document that we use it" instruction. Each row is
assigned to the phase/plan that must kill it, so none floats. (Full context:
[`FINAL-REVIEW.md`](../analysis/rebuild-discovery/new-bot-capability-audit/findings/FINAL-REVIEW.md)
§3 / §4; the capstone chat 2026-07-03.)

| Uncertainty | Resolved in | Note / leaning |
|---|---|---|
| **`ModerationActionSpec`?** — is an audited mod-action (warn/timeout/kick/ban) tier-3 forever (Lane A), or is there a declarable action *envelope* (preserve-map) that lifts moderation from 64%? The two independent passes disagree. | **Phase A** discussion → **Gate-0 grammar plan** records the decision | Resolvable by expressing one action against the grammar (~1hr spot-check). Leaning: the envelope (target/hierarchy/DM/cleanup/audit/log-route) *is* declarable; only the escalation decision is the thin handler. Settle it, document it, use it. |
| **Compound-composition** — can the workflow engine atomically compose several declared specs in one transaction with clean audit (farm `collect` = G-13+G-12+progression)? Lane B flagged it "unproven." | **Gate-0 / K7 workflow-engine plan** specifies the compound-workflow contract; **farm `collect` is the named canary** | The composable legs already exist in source (`debit_in_txn`/`credit_in_txn`), so it's promising. The real design question is **audit semantics** — one row for the compound op, or N. The plan must answer it. Prototype before trusting economy/game fit numbers. |
| **Forward-fit is unmeasured** — the 85% is all *retrofit*; no data on building *unbuilt* capabilities. | **Phase B**: the plan template makes "write the manifest + measure fit **before** code" mandatory for every new subsystem; **giveaways planned first** as the forward-fit proof | Cheapest de-risk of the biggest epistemic gap; converts it on a docs exercise, not on the flagship feature. |
| **G-22 staging lanes** — standardize to one `StagedBuilderSpec`, or bless three staging lanes? | **Phase A** → its owning L1 plan | Leaning: standardize (three ways to stage a draft is the fragmentation the rebuild kills), but it's a family for recurrence-1 today — owner's call. |
| **R-12 world-store** — a convention or a real dataclass? | **L0 grammar plan** | Leaning: convention (mining-only; a primitive for one consumer is over-engineering). |
| **P-1 event-feed spec** — ratify or hold? | **L0/L2 plan**, after the 2nd instance check | Hold until the boards family (L5) supplies the 2nd instance; low stakes. |
| **Lane D trust** — 440 units, no adversarial pass, one-agent tiers; the big lifts lean on soft riders. | **Phase B** adversarial-completeness pass re-verifies as a side effect; a targeted re-check of ai/btd6/diagnostic recommended before their plans finalize | logging reproduced the spike exactly (good calibration), but re-verify the three biggest lifts. |

---

## Doc-set freshness the Gate-0 plan must also fix

(From the capstone's rebuild-doc-set consistency check — carried so the Gate-0 session sweeps
them in one pass, per `NEW-BOT-BUILD-PLAN.md` §4.4):

- The **design spec still presents its amendment set as complete** ("six named amendments — now
  folded in") with **zero pointer to the capstone** — Gate-0's first edit.
- **Phantom "handoff §F"** cited by three docs (the handoff ends at §E).
- **Stale handoff §C** would rebuild the already-shipped `parity/` harness with a disproved
  mechanism (dpytest).
- **Strategy Phase-0 never stamped done** (kit finalized #1649).
- Numeric drift to reconcile once: command-surface denominators (271 vs 406+73), settings-key
  counts (~114 vs 120), kit test counts (399/407/422).

---

## Pointers

- Frozen reference:
  [`NEW-BOT-BUILD-PLAN.md`](../analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md)
  · [`FINAL-REVIEW.md`](../analysis/rebuild-discovery/new-bot-capability-audit/findings/FINAL-REVIEW.md)
- The grammar to freeze: [`rebuild-design-spec-2026-07-02.md`](./rebuild-design-spec-2026-07-02.md) §2
- The amendment-registry idea (mint IDs in one place):
  [`../ideas/rebuild-amendment-registry-2026-07-03.md`](../ideas/rebuild-amendment-registry-2026-07-03.md)
- Collaboration model (owner-designs / agent-builds-cross-checked):
  [`../collaboration-model.md`](../collaboration-model.md)

# SuperBot rebuild — Gate-0 grammar freeze + Phase-B L0 build order · the owner's entry point

> **Status:** `reference` — **complete** (2026-07-04). **NOT SOURCE OF TRUTH for runtime.** This is
> the front-matter for the **Gate-0** deliverable: the consolidation of the 14 foundational-design
> specs into ONE ratifiable frozen grammar, the register resolved, and the Phase-B L0 build sequenced.
> Source & merged PRs win (Q-0120); each owning design spec wins for a shape it owns; the frozen
> [`../design/shared-vocabulary.md`](../design/shared-vocabulary.md) wins where it reconciled a
> two-spec disagreement. **This is what the owner reads before the Gate-0 ratification sitting.**

---

## 1 · What this is — the design → GATE-0 step

The foundational design ([`../design/`](../design/README.md)) produced **14 buildable kernel specs**, a
**frozen shared vocabulary**, a **seam-consistency matrix** (RC-1…RC-21), a **retirement-coverage map**
(0 evaporations), and a **31-row question register**. Its README §6 named the next step: *consolidate,
ratify, sequence*. **This directory is that step.**

It is a **CONSOLIDATE + RATIFY + PLAN** deliverable — **not** a redesign of the frozen specs (their
owned shapes stand), **not** the new-repo bootstrap/migration (deferred), **not** the Stage-2 subsystem
walk (owner-led, independent), and it ships **no code** (the fresh-repo `sb/` package does not exist
yet — "freeze the grammar" = the authoritative, *code-ready* SPECIFICATION). It gathers every pinned
grammar addition scattered across the 14 specs into **one manifest a builder reads top-to-bottom**,
freezes the register's safe defaults, renders the owner-only calls, closes the pending cross-spec
wiring, and sequences the L0 build.

Grounded from the harvested work-list ([`../../../../planning/rebuild-gate0-worklist-2026-07-04.md`](../../../../planning/rebuild-gate0-worklist-2026-07-04.md)),
then **re-verified against the 14 owning specs** (Q-0120) — the fold caught and corrected **6 mis-cites**
against source (listed in the grammar's closing subsection).

---

## 2 · The six deliverables + the two continuity edits

| # | File | What it is |
|---|---|---|
| ① | **[`frozen-l0-grammar.md`](frozen-l0-grammar.md)** | THE LINCHPIN. Every pinned field / enum / port / table / fence / facet from the 14 specs — **87 primitives across 18 attach-point groups** — folded into one manifest-grammar spec (extends `rebuild-design-spec-2026-07-02.md` §2/§3). Each field: exact type · default · `[S]`/`[A]`/`[O]`/`[DERIVED]`/`(primitive)` role · one-line semantics · owning-spec § · the L-row/RC/Q-D it retires. A fresh agent builds the `sb/spec/` dataclasses from **this**, not from 14 specs. |
| ② | **[`amendment-registry.md`](amendment-registry.md)** + [`rebuild-amendments.yml`](../../../../planning/rebuild-amendments.yml) | The prerequisite, built FIRST. The sole collision-free amendment-ID minting authority (spec 01 §3.7): G-1…G-24 enumerated, the `check_amendments.py` uniqueness checker specified, the minting protocol pinned. This fold flips **G-10 `ModalFormSpec` → in-spec** (the L-24 `ModalSpec`); G-9/G-11…G-24 stay `pending-gate-0` (each flips when its own K-step ships). |
| ③ | **[`cross-spec-wiring.md`](cross-spec-wiring.md)** | The four pending absorptions the specs flagged but did not land, each as a precise ready-to-apply edit, `CLOSED-AT-GATE-0`: `ActorRef.member_tier` (RC-12), the spec-02 absorption of 04's authority contracts (RC-2/3/4/5/13/14/15), `WorkflowContext.test_mode`, and the `ChannelEmitter` egress-port registration on 02/K8 (RC-21). |
| ④ | **[`register-resolution.md`](register-resolution.md)** | The **19 RATIFY-DEFAULT** register rows frozen to their built defaults (5 surfaced owner-visible-but-non-blocking). |
| ④ | **[`owner-decision-packet.md`](owner-decision-packet.md)** | The **12 OWNER-ONLY** rows + **L-21**, rendered owner-consumable — per card: the call · options · recommendation · blast-radius / why-owner-only · the register-Q (+ binding-Q it touches). The near-irreversible / data-loss four (Q-D8/13/14/15) grouped up top. **The owner rules from here; Gate-0 never decides these.** |
| ⑤ | **[`l24-presentation-riders.md`](l24-presentation-riders.md)** | The L-24 presentation riders pinned to buildable depth: `alt_text`, the locale/i18n seam, the `allowed_mentions` default policy (× `TrustLevel`), `ModalSpec` (amendment G-10, tied to the `from_error` guarantee), and bundled fonts. |
| ⑥ | **[`phase-b-l0-build-order.md`](phase-b-l0-build-order.md)** | The **16-step L0 build order** (S0–S15): per step the K-slot, spec(s), provides/consumes, and the applied seam reconciliations. The plan the (later, separate) new-repo Phase-B L0 build executes. |
| ↺ | [`../design/question-register.md`](../design/question-register.md) · [`../design/retirement-coverage-map.md`](../design/retirement-coverage-map.md) | **V-3 continuity appends** — each register row marked RATIFIED-DEFAULT / OWNER-PENDING, and every L-row/RC/Q-D the grammar retires recorded (the four pending wirings now `CLOSED-AT-GATE-0`). Nothing evaporates. |

---

## 3 · What got frozen (no owner needed)

- **The 87-primitive L0 grammar** — ~34 field-additions onto existing specs + ~53 new leaves /
  primitives, grouped by 18 attach-points, every field verified against its owning spec §3.
- **The amendment registry** — collision-free G-1…G-24; **G-10 `ModalFormSpec`** flipped in-spec.
- **The four cross-spec wirings** — RC-12 / the 02-absorption / `test_mode` / RC-21, all closed.
- **19 register rows** — each pinned to a safe, conservative default that forecloses no later owner
  option (5 surfaced for awareness only).
- **The L-24 riders** and **the 16-step L0 build order**.

## 4 · What the owner must rule (the ratification sitting)

The **12 owner-only rows + L-21** in [`owner-decision-packet.md`](owner-decision-packet.md). Each ships
a safe *built default today*, so **the build is unblocked** — but freezing that default is itself the
irreversible / binding / rubric call, so the owner rules (or blesses the default). The load-bearing set:

- **Near-irreversible / data-loss (rule first):** Q-D8 (store-drop disposition) · Q-D13 (money-repair
  direction) · Q-D14 (RPO target) · Q-D15 (rollback-data disposition + window N).
- **Narrows a binding decision → router DISCUSS:** Q-D16 / Q-D17 (credential custody & the Q-0213
  `*Delete` brake) · Q-D18 (supply-chain gate × the Q-0105 adopt-freely grant) · Q-D20 (rubric classes
  11/12/13 × Q-0233).
- **Ops / strategy / architecture:** Q-D5 (intent DEGRADE vs fail-closed — the one open seam-fork
  **F-3 / PG-2**, `required=True` floor until ruled) · Q-D19 (`SB_PROD_ATTEST` custody) · Q-D21 (growth
  posture) · Q-D24 (multi-actor concurrency primitive now vs Stage-2).
- **Outside the 31:** **L-21** (old-bot change-policy, an L-ledger row).

The grammar's *shapes* are frozen regardless; only these *default values* await the ruling. Each is
flagged at its grammar row and reconciled in the packet.

## 5 · The design → grammar retirement continuity (V-3)

Every L-row / RC / Q-D / T2 / FJ-gap the 14 specs carried has a home in the frozen grammar's per-group
"Retires" columns; the appended continuity sections in the two design/ artifacts certify **0
evaporations**. The four previously-pending wirings are now `CLOSED-AT-GATE-0`.

---

## 6 · What's next

1. **The owner's Gate-0 ratification sitting** — consume [`owner-decision-packet.md`](owner-decision-packet.md),
   rule the 12 + L-21. That closes the register.
2. **The new-repo bootstrap / migration plan** — a separate, later effort (deferred).
3. **The Phase-B L0 build** — execute [`phase-b-l0-build-order.md`](phase-b-l0-build-order.md) against
   the frozen grammar: S0 amendment registry → 01 (K2 compiler linchpin) → the kernel spine → strand-2
   durability → strand-3 rides the frozen grammar.
4. **Stage-2 (owner-led subsystem walk)** runs in **parallel** against the frozen contracts — it does
   not depend on completing this L0 build.

---

## Provenance

- **Authored by** Claude Opus 4.8 (ultracode), 2026-07-04 — a docs/spec-only Gate-0 consolidation
  session, orchestrated via a fan-out workflow (amendment registry first → 17 per-group fold agents +
  the specialized deliverable agents → grammar assembly → a 6-lens adversarial-completeness +
  ratification-readiness critic with a fix round → V-3 continuity). Source wins (Q-0120): every folded
  field re-verified against its owning spec §3; 6 mis-cites corrected.
- **Upstream:** [`../design/README.md`](../design/README.md) (the 14 specs + 4 synthesis artifacts) and
  [`../final-judgment-fable5-2026-07-03.md`](../final-judgment-fable5-2026-07-03.md) (the GO verdict).
- **Grounded on:** [`../../../../planning/rebuild-gate0-worklist-2026-07-04.md`](../../../../planning/rebuild-gate0-worklist-2026-07-04.md)
  (the harvested work-list) + its brief.

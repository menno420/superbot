# Rebuild amendment registry — one minting authority for G-numbers (and R-/P-/refuted sets)

> **Status:** `ideas` — session idea (2026-07-03, Q-0089, capability-audit capstone PR #1674).
> Surfaced independently by the capstone's doc-set consistency reviewer; endorsed and shaped here.

## The problem (it already happened — three times in one audit)

The capability audit's lanes each minted grammar-amendment IDs **locally**: Lane B assigned
"G-7…G-13" (EconomyTransactionSpec…), Lane C assigned "G-7…G-9" (MessagePipelineStageSpec…), and
both collided with Lane D's canonical G-7…G-10 (KnowledgeDomainSpec, AI specs, TimedTask, ModalForm)
— *and* Lane B's sub-agents used the same "G-14…G-20" labels for **different** refuted proposals per
subsystem. The capstone had to reconcile the whole numbering by hand
([`FINAL-REVIEW.md`](../analysis/rebuild-discovery/new-bot-capability-audit/findings/FINAL-REVIEW.md)
§3), and the refuted list only exists as prose. This is exactly the collision class the rebuild's own
namespace registry kills for runtime identifiers — applied to the rebuild's *meta-artifacts*.

## The idea

One small committed registry file (YAML or a single canonical table doc, e.g.
`docs/planning/rebuild-amendments.yml`) that is the **sole minting authority** for:

- **G-n** ratified amendment families (id · name · status: `in-spec` / `pending-Gate-0` ·
  consuming subsystems · source lane),
- **R-n** soft riders,
- **P-n** provisional/held candidates (with their ratify-condition),
- the **refuted / do-not-re-propose set** (with the one-line refutation).

Rules: next free number only; append-only; a lane/session proposing a family cites the registry and
mints there in the same PR; the Gate-0 spec pass consumes it and stamps `in-spec`. Optionally a
20-line checker asserts IDs are unique and every `in-spec` entry appears in the design spec.

## Why it's worth having

- Prevents the (already-observed) numbering collision recurring across future lanes/sessions.
- Gives the Gate-0 spec pass a machine-consumable work list and the owner a one-glance state of
  the amendment set.
- Keeps the refuted list *enforceable* — a future session re-proposing `LootTableSpec` greps one
  file instead of re-deriving three lanes' adversarial passes.

Related: [`convergent-amendment-discovery-signal-2026-07-02.md`](./convergent-amendment-discovery-signal-2026-07-02.md)
(confidence-ranking by independent rediscovery — the registry is where that signal gets recorded).

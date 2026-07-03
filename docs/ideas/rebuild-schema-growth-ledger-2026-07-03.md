# Idea — rebuild schema-growth ledger (enforce the second-consumer rule mechanically)

> **Status:** `ideas` — capture only. **Subsystem:** none (rebuild kernel / grammar governance).
> **Provenance:** Stage-1 global review (PR #1679), companion to the Q-0219 engine/declaration/seam
> standard's schema-growth guardrail.

## The idea

The Q-0219 guardrail says the manifest grammar's declaration schema may grow a field **only when
the same pattern recurs across ≥2 consumers** (otherwise: Tier-3 handler). Rules like this decay
unless enforced (Q-0132 "enforce, don't exhort"). So: in the **new repo**, every schema-field
addition to the grammar carries a **ledger entry minted in the same PR** — field name, the ≥2
consumers that justified it (manifest paths), and the alternative rejected (why not a handler).
A tiny checker diffs the grammar's field set against the ledger in CI: a new field with no entry
(or with <2 named consumers) fails the build.

## Why it's worth having

The inner-platform effect is *the* documented failure mode of declarative engines — and it creeps
one innocent field at a time. A per-field provenance ledger makes each growth step a reviewed,
justified decision and gives later agents the "why" behind every field (the same plan→manifest→code
durability chain the rebuild already bets on, applied to the grammar itself).

## Routing

Belongs to the **Gate-0 / K2 grammar plan** (Phase B) as a small deliverable — the ledger file
format + the CI check ride the same PR that freezes the grammar. Not current-repo work.

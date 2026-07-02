# Owner-gate docs always carry a plain-language layer (2026-07-02)

> **Status:** `ideas` — session idea (Q-0089, from the design-spec revision session). Not approved
> for implementation.

## The idea

The rebuild design spec — the highest-stakes owner-gate artifact yet — shipped written for
engineers, and the very first owner feedback (plus both external GPT reviews) was "it needs a
plain-language summary." The revision added one, but the miss was predictable: **the approving
reader of an owner-gate document is by definition the non-coder owner**, and nothing in the
workflow encodes that.

Make it a convention with a cheap enforcing edge:

1. **Convention (docs rule):** any document whose status badge marks it an owner-gate deliverable
   (`owner-gate` token in the `> **Status:**` line) must open with a `## Plain-language summary`
   section — what it is, why, what changes for the owner, what approval means — before any
   technical section.
2. **Enforcement (one `check_docs` rule, ~10 lines):** badge contains `owner-gate` ⇒ the literal
   heading exists within the first ~60 lines. Enforce-don't-exhort (Q-0132); free-to-ship lane per
   Q-0194 (checker, not hook).
3. **Portable:** the substrate-kit's doc templates gain the same section in their owner-decision
   template — any repo using the kit inherits the audience rule.

## Why it's worth having

The failure mode recurs every time an agent writes for the reviewer it imagines (another engineer)
instead of the reviewer that exists (the owner). One heading requirement converts that from a
judgment call into a red check, and the fix cost here (a full revision PR) was ~100× the cost of
the convention.

## Route

S4 (docs system) · pairs with [`../planning/rebuild-design-spec-2026-07-02.md`](../planning/rebuild-design-spec-2026-07-02.md)
(the precedent + first conforming doc).

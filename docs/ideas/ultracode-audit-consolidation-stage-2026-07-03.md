# Idea — a consolidation/dedup stage for the ultracode multi-agent audit pattern (2026-07-03)

> **Status:** `ideas` — a brainstorm capture, **not** a plan and **not** approval.
> **Subsystem:** none (agent-workflow / meta — improves the *workflow*, the real artifact).
> **Provenance:** session idea (Q-0089) from the PROMPT-B surface+proving foundations audit
> (PR #1691). Companion to the reusable two-session brief
> [`../planning/rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md`](../planning/rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md).

## The observation (directly experienced this session)

The PROMPT-B audit workflow ran the brief's method verbatim: fan-out finders → adversarial-verify →
**completeness-critic loop** (three lenses, run to a round cap) → synthesize. The completeness loop
worked *too well* on volume: it grew the inventory from the 12 named mechanics to **46**, and the
final ~34 came in with **weak dedup**. Several are genuine near-duplicates the synthesis had to
untangle by hand:

- `live-view-timeout / component-teardown` ≈ `graceful-component-expiry / no-dead-end terminal render`
  (same in-memory View-timeout clock, same disable-on-expiry contract).
- `navigation-graph static well-formedness oracle` vs `dynamic navigation conformance oracle` vs the
  existing `navigation-completeness` idea — three framings of "prove Back/Home/reachability."
- `visibility × durability × interactivity oracle` overlaps `restart-durability tier classification`
  and `response-visibility standard`.

The loop's only dedup was a normalized-key exact match on the mechanic *name* — so any mechanic
proposed under a **different phrasing** slipped through. The adversarial-verify pass validated each
finding against source (it did its job — it even caught a finder that emitted placeholder output),
but verify checks *correctness*, not *redundancy*. Nothing in the pipeline asked "is this the same
contract as one we already have, said differently?"

## The idea

Add one **consolidation stage** between the completeness loop and synthesis in the reusable audit
pattern (and bake it into the brief's "shared method"):

1. **Semantic cluster, not string-match.** After the completeness loop converges, a consolidation
   agent receives the *titles + one-line gists* of all mechanics and clusters near-duplicates by
   meaning (not normalized key). Output: clusters of `{canonical mechanic, merged aliases,
   why-same}`.
2. **Merge before synthesis.** Each cluster collapses to one inventory entry that keeps the union of
   its issues (deduped) and cites all source framings — so the final inventory is
   **de-duplicated by construction**, and the "we found N mechanics" count is honest rather than
   inflated by paraphrase.
3. **Keep the traceability escape hatch.** Record the pre-merge list in an appendix (this session
   did that by hand — "near-duplicate mechanics… kept distinct for traceability; Stage-2 should
   merge") so nothing is silently dropped; the merge is *visible*, per the no-silent-truncation rule.

This is the **completeness-critic's missing twin**: the completeness pass answers "what did we
forget?"; the consolidation pass answers "what did we say twice?" Both are needed for an audit whose
headline number (46 mechanics, 220 issues) is used as a scope signal downstream.

## Why it's worth having

- **Cheaper, truer downstream.** The Stage-2 subsystem walk / Gate-V fleet consume this inventory;
  merging near-dupes up front saves them the same untangling and prevents double-counting an issue
  across two framings of one contract.
- **Bounds the loop's cost.** A semantic-dedup gate also lets the completeness loop terminate on
  "two rounds add nothing *semantically new*" instead of "nothing with a new *name*" — the loop this
  session kept resetting its dry-counter on paraphrases, running to its round cap and ~108 agents.
- **Generalizes.** It's a reusable quality pattern for *any* fan-out→completeness workflow (bug
  hunts, capability audits, research sweeps), not just this brief — a natural addition to the
  Workflow tool's documented pattern set ("completeness critic" already exists; "consolidation
  critic" is its dual).

## Lifecycle / next step

Small, safe, decided-lane: fold a "consolidation stage" line into the brief's **shared method** and
into the audit-workflow recipe so the next ultracode audit inherits it. No bot code. Could be groomed
into a one-paragraph amendment to the brief in a later session, or applied the next time the
two-session pattern is run.

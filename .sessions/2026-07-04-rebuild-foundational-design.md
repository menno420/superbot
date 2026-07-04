# 2026-07-04 — Rebuild foundational-DESIGN (AUDITED → Gate-0 / L0-plannable)

> **Status:** `complete` — PR #1708. Opus 4.8 ultracode overnight **foundational-design** session.
> Designed the ~10 foundational **kernel functions** (audited A #1690 / B #1691, judged by the
> Fable-5 capstone #1701) to **buildable depth**, closed the 5 never-surfaced concerns, froze one
> shared vocabulary, and harvested every remaining decision into one register. DESIGN +
> question-surfacing only — no code, not a fourth audit, not the Stage-2 subsystem walk. Executed
> `docs/planning/rebuild-foundational-design-opus-brief-2026-07-03.md` "THE PROMPT" verbatim via a
> five-workflow fan-out (~62 subagents, ~10.6M subagent tokens).

## What shipped (all in PR #1708)

The deliverable lands under
[`docs/analysis/rebuild-discovery/foundations/design/`](../docs/analysis/rebuild-discovery/foundations/design/README.md)
— three strands under one synthesis:

1. **Strand 1 — kernel spine (5 specs):** compiler+snapshot+amendment-registry · resolver+error-envelope ·
   K1 namespace registry · authority engine · ops-kernel/rails. Each buildable to Phase-B depth.
2. **Strand 2 — runtime-durability (4 specs):** draft pipeline · workflow engine · event outbox ·
   scheduler/state — built ON the frozen vocabulary.
3. **Strand 3 — cross-cutting concerns (5 dossiers):** security/abuse + rubric classes 11/12/13 ·
   production-data integrity/repair · credential lifecycle · backup-DR + rollback-disposition ·
   Discord platform-governance. Each: threat model → design → landing site → owner-gated?
4. **`shared-vocabulary.md`** — the 7 recurring contracts frozen once (S-1 "decide the recurring
   method once"): error-envelope · authority_ref · audit-row · idempotency-key · restart-safety ·
   EventSpec.delivery · config/data-plane-rail. Carries the canonical source-wins grounding
   (WorkflowResult = K7 design superset of the real `LifecycleResult`; `StageResult` is the
   message-pipeline substrate; `core/contracts.py` is the fabricated cite).
5. **`seam-consistency-matrix.md`** — 56 agreements + RC-1…RC-15; caught **5 cross-strand seam forks**
   (incl. a direct 08↔09 contradiction that would have left the outbox relay unhosted = silent total
   loss of the audit trail on every restart). 4 mechanically reconciled + applied, 1 carried to
   register PG-2.
6. **`retirement-coverage-map.md`** (V-3) — **96 rows** audited (25 L-rows + 17 §4 gaps + 46 queue
   items + 8 stress adds): 62 covered / 32 carried / 2 out-of-scope, **0 evaporations**.
7. **`question-register.md`** — **31 numbered decisions** (23 owner-gated, 8 net-new this session),
   each with options + recommendation + owning-spec + tier + FJ-queue mapping.

**Method:** WF1 designed strand 1 (design→critic→revise per function) + froze the vocab; WF1b hardened
the two specs whose design agents wrote complete drafts but missed the review pass; WF2 designed
strands 2+3 on the frozen vocab; WF3 ran the synthesis (seam matrix + coverage + a 3-lens adversarial
sweep + register + README); WF4 applied the 5 seam forks + the sweep's close-in-spec fixes and a
verifier confirmed all_closed=True. Every spec carries its FJ L-row / owner-queue **retirement map**.

## 💡 Session idea (Q-0089)

**[`rebuild-design-cite-checker-2026-07-04.md`](../docs/ideas/rebuild-design-cite-checker-2026-07-04.md)**
— a `check_doc_cites.py` that validates every `path.py:NNN` source citation in an analysis/design doc
resolves to a real file (and, cheaply, that the line exists). Worth having because the fabricated
`core/contracts.py:48-52` cite (FJ L-25) propagated through audit A and cost this session real
cross-spec correction effort to unwind — a mechanical cite-resolver would have caught it at authoring
time and would harden every future audit/design doc against the same class. Mechanizable, disposable
(Q-0105), pairs naturally with the existing `check_docs` hygiene pass.

## ⟲ Previous-session review (Q-0102)

Previous: **#1701, the Fable-5 final judgment.** Genuinely excellent — 37 agents re-verified the 16
highest-stakes claim clusters against shipped source, *caught the fabricated `contracts.py` cite*, and
produced the L-1…L-25 ledger + tiered owner queue + the **V-3 findings-closure binding** that made
this session's work-list crisp and consumable (V-3 is exactly what let this session produce a
0-evaporation coverage map — nothing to reconstruct). **What it couldn't reach (a scope boundary, not
a miss):** its completeness-critic loop "hit its round cap still finding things," and this session's
synthesis sweep then surfaced 18 more items — including real blockers (the unhosted-relay
contradiction, a GLOBAL scheduler task double-arming every boot) — that were **structurally invisible
to the judgment** because it reviewed the *audit*, and cross-strand seam contradictions only exist once
you design the contracts. **Workflow improvement:** the judgment flagged "Gate-V should run with
rotated lenses" but as prose; this session operationalized it (a fixed 3-lens sweep + "don't trust one
dry round") — that pattern should be the standing shape of the Gate-V pass, and the fabricated-cite
class it found (L-25) is exactly what the Q-0089 cite-checker mechanizes. The self-auditing loop
worked: the predecessor's own L-25 finding motivated this session's system improvement.

## Docs audit (Q-0104)

- `check_docs.py --strict` ✓ (normalized all 18 design docs to the `reference` badge — the agents had
  used non-allowlisted `design`/`synthesis`/`harvest` tokens / missing Status lines; caught + fixed
  locally before flipping the card, so the required CI hygiene step stays green).
- `check_current_state_ledger.py --strict` ✓ (in sync; this session's PR is unmerged so it is
  correctly NOT in the merged-PR ledger — the reconciliation pass records it once merged).
- Reachability: the deliverable README is linked from the executing brief (pointer added); the
  question register is the single V-3 landing site so no design-session fork is chat-only.
- New owner decisions surfaced this session live in the **question register** (31 rows, the durable
  home), which routes to the owner; no chat-only residue.

## ⚑ Self-initiated

None beyond the brief's explicit scope. The WF4 seam-reconciliation fixes are the brief's own
method-step-5 ("freeze one shared vocabulary … and a matrix proving they agree" — applying the fixes
is what makes the specs *agree*); the badge normalization is CI hygiene. The session is fully
owner-directed via the brief + launch prompt, so it merges on green with no review hold (Q-0191).

## For the next session (Gate-0 + Phase-B L0)

The deliverable is the **AUDITED → Gate-0 / L0-plannable bridge**. Next: (1) the **Gate-0 grammar
freeze** folds the pinned grammar-field additions the specs surfaced (authority_ref, enabled_when,
reply_visibility, defer_mode, EventSpec.delivery, StoreSpec.version_policy, the data-plane rail,
ActorRef.actor_type, the MAINTENANCE Surface member, rubric classes 11/12/13) + answers the register's
23 owner-gated rows; (2) the **Phase-B L0 layer plan** builds on the frozen kernel spine (build order
is in each spec's §11). This runs ahead of / parallel to the owner-led Stage-2 subsystem walk (the
kernel is largely command-name-independent). The register's genuinely owner-only rows (PG-2 intent
posture, rollback-data disposition, credential-custody, security-rubric adoption) want an owner sitting.

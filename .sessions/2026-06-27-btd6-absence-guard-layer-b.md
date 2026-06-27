# 2026-06-27 — BTD6 absence-guard Layer B (grounded-contradiction slice)

> **Status:** `in-progress`

**Run type:** owner-directed (in-session greenlight: *"Build it now (offline + unit tests)"* —
AskUserQuestion answer to the absence-guard Layer B question, after the codex-audit review)

## What this run did

The faithfulness verifier catches ungrounded **positives** (a name/number not in the grounding) but
**not** a false **negative** — a reply can fluently assert *"the Monkey Buccaneer does not have a
paragon"* when the grounded facts in front of the model affirm it does (Navarch of the Seas). That
fluent false "no" is worse than a refusal. The design doc
([`btd6-absence-claim-guard-design.md`](../btd6/btd6-absence-claim-guard-design.md)) called for
review-before-build; the owner greenlit it this session.

**Shipped — the safe, high-precision §4.2-step-3 slice (grounded-contradiction):** reject an absence
claim **only when the grounded payload affirms the very thing the reply denies**, so it can never block a
*true* negative (a true "X has no paragon" has no contradicting positive → nothing fires). Deliberately
**not** the §4.3 unresolved-subject half (the part with false-floor risk that needs a live FPR check).

- `utils/btd6/absence_guard.py` (new, pure/stdlib) — `contradicted_absence_claims(answer, haystack)`. An
  `_ExistenceAttribute` table (the extension point) seeded with **paragon** (the canonical Update-2
  repro): reads the subjects the haystack affirms have a paragon, flags any reply *sentence* that names an
  affirmed subject **and** denies its paragon (tight negation patterns + a "no *second* paragon" exclusion).
- `services/btd6_grounding_service.validate_btd6_reply` runs it on `facts ∪ tool_results`, returns
  `grounded=False` + note `absence_claim_contradicted`, so the **existing regenerate-once → deterministic
  refusal** flow downgrades it for free; the retry constraint tells the model the data *does* list the
  thing and to state it.
- Design doc Update 7 records the shipped slice; the §4.3 half stays design-only.

**Verified against the REAL pipeline:** `build("does the monkey buccaneer have a paragon")` grounds
Navarch; a reply saying "...does not have a paragon" is now blocked (`absence_claim_contradicted`) while
"...has a paragon, Navarch" passes. CI: `check_quality --full` green; arch 0 errors; new tests
(15 util + 4 service) + the 89-test answer-path suite pass.

## ⚑ Self-initiated

None unprompted — **owner greenlit** "build it now (offline + unit tests)" in-session. Scope chosen to
the safe grounded-contradiction slice (no false-floor risk), leaving the live-FPR-gated §4.3 half for a
verified follow-up — flagged so the boundary is reviewable.

## 💡 Session idea (Q-0089)

*Generalize the grounded-contradiction principle into a domain-agnostic `absence_guard` so the next
knowledge domain gets false-"no" protection for free.* Project Moon (Limbus) already has the same
faithfulness-guard shape (`projmoon_grounding_service`, the BTD6 analogue). The contradicted-absence check
is pure string logic over a grounded haystack + an attribute table — lift it to a shared helper keyed by
each domain's existence-attributes, and Limbus (and LoR/LobCorp next) inherit the guard. Mirrors the
cross-domain reuse theme of #1470. Routed as an idea, not built here.

## ⟲ Previous-session review (Q-0102)

The immediately-prior PR this session (#1510, the BTD6 corpus expansion) pinned the buccaneer-paragon
absence repro at the **grounding** layer (proving the data is *retrieved*) but explicitly noted the
**guard** layer — whether the bot *rejects the false claim* — was still gated. This session closed that
exact loop: the corpus proves the fact is grounded, Layer B proves a reply contradicting it is now caught.
**System improvement (applied):** the two are a **paired pattern** — when you pin a grounding fact for a
false-"no" bug, also check whether a guard rejects the false *claim*; data-present and claim-rejected are
different failure surfaces and both deserve a regression. Worth making the pairing explicit in the evals
README so future false-"no" fixes ship both halves.

## 🧾 Doc audit (Q-0104)

`check_quality --full` green (incl. `check_docs`/`check_consistency`); arch 0 errors. New facts homed: the
guard code + design doc Update 7 + the status-block update (Layer B's slice marked shipped). Owner
decisions this session (wire `light_radius`/`luck`; build Layer B; hold PR 3b) recorded in the question
router (Q-block) for provenance; the BUG-0026 "wire" decision is actioned in its own follow-up PR. Ledger:
merged-only convention — the next reconciliation adds this PR.

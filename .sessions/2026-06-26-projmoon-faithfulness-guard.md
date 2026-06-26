# 2026-06-26 — Project Moon (Limbus) faithfulness guard (S1)

> **Status:** `complete`

## Goal (dispatch run, empty scheduled fire → advance the next plan slice)

Empty scheduled fire, **zero open PRs**. Per the routine: advance the next **▶ startable**
plan slice. The Project Moon knowledge-domain plan's ▶ Next item (b) is **the projmoon
faithfulness guard follow-up** — the §6 "hardest correctness risk". PR #1467 (Slice A item 2)
shipped the Limbus grounding *injection* path but deliberately deferred the prose-faithfulness
*validation* guard: a `PROJMOON_ANSWER` reply grounds on the injected facts but is **not**
verified against them the way `btd6_grounding_service.validate_btd6_reply` verifies BTD6 replies.
This slice closes that gap — offline-verifiable, default-preserving (only Limbus-detected
messages route to `PROJMOON_ANSWER`).

## What shipped (PR #1469)

**New `disbot/services/projmoon_grounding_service.py`** — the projmoon analogue of
`btd6_grounding_service.validate_btd6_reply`:
- `validate_projmoon_reply(reply, facts)` reuses the domain-agnostic, stdlib-only
  `utils.btd6.name_guard` matchers **and the shared `GroundingResult` dataclass** (so Slice B's
  `KnowledgeDomain` seam folds the two grounding services with no contract change).
- `_name_index()` indexes the **distinctive** Limbus proper names — the 12 Sinners (canonicals +
  aliases, `build_matchers` filters the generic short ones) + the four non-ambiguous E.G.O grade
  letters (ZAYIN/TETH/WAW/ALEPH, "HE" excluded as the pronoun) and their "<x> grade" multi-word
  aliases. It **skips** the common-English categories (Sins `Wrath`…, damage types `Slash`…,
  statuses `Burn`…) so ordinary prose never false-positives — mirroring BTD6's
  hero/boss-vs-generic discipline.
- **Names-only** — Limbus *exact numbers* aren't ingested yet (Slice A item 1), so there is no
  numeric grounding, unlike BTD6.
- `build_grounding_constraint()` + `no_data_refusal()` — the retry constraint + the deterministic,
  never-model-prose Limbus refusal string.

**NL-stage wiring** (`core/runtime/ai/natural_language_stage.py`) — a `PROJMOON_ANSWER`
faithfulness block parallel to the BTD6 one: reject → regenerate-once with a do-not-state
constraint → floor to the deterministic refusal (`_send_projmoon_refusal`), auditing
`denied`/`GROUNDING_FAILED` (or `degraded`/`PROVIDER_UNAVAILABLE` if the retry degrades).

**Posture divergence from BTD6 (documented in-module):** a verifier *exception* fails **open**
(projmoon faithfulness is additive hardening, not a hard numeric safety floor — a verifier bug
must not refuse a legitimate, lower-stakes Limbus answer); a genuine unsupported-name finding
fails **closed**.

**Default-preserving:** only `PROJMOON_ANSWER` replies (already Limbus-routed) enter the guard;
the BTD6 / general paths are byte-identical.

## Verification
- `tests/unit/services/projmoon/test_projmoon_grounding_service.py`: **12 passed** (name-index
  discipline, grounded/unsupported verdicts, common-category exclusion, ambiguous-`he` exclusion,
  fail-open-on-error, constraint/refusal strings).
- `tests/unit/runtime/ai/test_natural_language_stage.py` projmoon block: **4 passed** (grounded
  served · unsupported-name refused after retry · regenerate-once rescue · degraded-retry stays
  PROVIDER_UNAVAILABLE).
- Registered the new `_reset_for_tests` hook in `tests/_isolation.py` (PER_FILE) — fixes the
  `test_every_reset_hook_is_classified` invariant.
- Full CI mirror `python3.10 scripts/check_quality.py --full`: **12608 passed, 48 skipped,
  2 xfailed** (green after the isolation registration; the one earlier failure was exactly that
  unclassified hook).
- `check_architecture.py --mode strict`: **0 errors** (49 known warnings, none touched).
- Doc audit: `check_current_state_ledger.py --strict` exit 0 (benign newest-merge lag only,
  25 PRs newer than marker #1441 — the recon pass records them); `check_docs.py --strict` green.

## Status checklist
- [x] `projmoon_grounding_service` + name index + 12 service tests
- [x] NL-stage `PROJMOON_ANSWER` guard wiring + deterministic refusal + 4 wiring tests
- [x] `tests/_isolation.py` registration (reset-hook invariant)
- [x] CI mirror green + arch strict 0 errors
- [x] De-stale the project-moon plan + S1 sector doc
- [x] Session enders (idea / prev-review / doc audit / run-report footer)

## 💡 Session idea (Q-0089)

**A `name_guard`-style faithfulness guard is a *reusable domain primitive*, not a per-domain
copy.** Building the projmoon guard, I deliberately reused `utils.btd6.name_guard` and the shared
`GroundingResult` — but the *index-building discipline* ("distinctive proper names single-token,
common-English categories multi-word-only") was hand-re-implemented in both
`btd6_grounding_service._name_index` and `projmoon_grounding_service._name_index`. When Slice B
extracts the `KnowledgeDomain` seam, that discipline should become a single
`build_domain_name_index(domain)` helper that takes a per-domain "distinctive kinds" vs "generic
kinds" partition — so registering a third reference domain (Library of Ruina) is a *data*
declaration, not another bespoke index builder. Captured as the natural shape for Slice B's
shared renderer. *(Not promoted to a separate idea file — it's an implementation note on the
already-planned Slice B, recorded here + in the plan's §3 generalisation table.)*

## ⟲ Previous-session review (Q-0102)

The previous run (PR #1458, the BTD6 fixture-drift anchor guard) did something genuinely right and
worth repeating: when it found the *remaining* unanchored rubric figures were **not cleanly
reproducible** (a naive `round_cash` lands ~$10 off; `$71,315.20` is a BUG-0004 distractor), it
**did not anchor them blindly** — it documented why and left a handoff, honoring CLAUDE.md Q-0120
("a guard that asserts a wrong truth is worse than no guard"). That restraint is exactly the
instinct I leaned on here: the projmoon guard is **names-only and skips the common-English
categories** rather than over-indexing for coverage — a guard that floored "this deals slash
damage" on the word *slash* would be worse than no guard. **System improvement it surfaces:** both
runs independently re-derived the same "distinctive vs generic token" discipline by reading the
BTD6 code — that's the duplication my session idea above flags. The workflow would be better with a
**single documented `name_guard` usage recipe** (in `docs/subsystems/ai.md` or the helper-policy)
so the next domain author doesn't re-derive it from the BTD6 source each time. Small, real, not
filler.

## 📤 Run report

- **Did:** built the Project Moon (Limbus) answer-faithfulness guard — post-verify `PROJMOON_ANSWER`
  replies against the injected grounding facts · **Outcome:** shipped
- **Shipped:** #1469 — `projmoon_grounding_service` (name-guard reuse, Sinner/E.G.O index,
  common-category exclusion) + NL-stage `PROJMOON_ANSWER` reject→retry→refusal wiring + 16 offline
  tests; closes Slice A follow-up (b) / plan §6 hardest-risk item
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none (the live Q-0086 Limbus runtime walk remains an owner step from
  PR #1467 — not newly created here; the guard is offline-verified)
- **⚑ Self-initiated:** none (dispatched-plan ▶ Next item (b))
- **↪ Next:** S1 Project Moon — the live **Q-0086 runtime walk** (owner) + Slice A item 1 (the
  StaticData exact-number ingest, the deferred fragile lane) → then **Slice B** = extract the shared
  `KnowledgeDomain` seam from BTD6 + Limbus (fold the two grounding services; lift the duplicated
  name-index discipline into one `build_domain_name_index` helper — see this run's session idea).

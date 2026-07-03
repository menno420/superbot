# Rebuild planning sanity review — gates, phases, and next allowed work (2026-07-03)

> **Status:** `review` — repo-grounded sanity review of the rebuild planning state as of
> 2026-07-03. This document reviews consistency only: it does **not** approve implementation,
> does **not** start Phase B, and does **not** authorize new-repo work. Source code + merged PRs
> remain higher precedence than planning docs; binding rebuild docs remain higher precedence than
> `docs/current-state.md`.

## 1. Current-state verdict: **mostly clear**

The rebuild planning state is clear enough to route the next session safely, but not perfectly clean.
The dominant state across the docs is:

- The rebuild is in **Phase A — content review**, not implementation.
- **Stage 1 is done**; **Stage 2 — the subsystem walk** is the next Phase-A destination.
- **Phase B, Phase C, Migration, and new-repo work are still blocked** behind Phase-A completion,
  Gate V, Gate-0 amendments, and owner ratification.
- The capstone (`FINAL-REVIEW.md` + `NEW-BOT-BUILD-PLAN.md`) remains the **frozen reference**;
  today's additions ride as companion decisions / deltas that feed Gate-0, not silent rewrites.

The main temporary ambiguity is live PR **#1691**: the Session-B presentation/verification foundations
report was still open during this review, so the repo had Session A merged but not Session B.

## 2. Gate / phase map verified from the repo

| Step | Verified state | Allowed next |
|---|---|---|
| Capstone | Done; `FINAL-REVIEW.md` + `NEW-BOT-BUILD-PLAN.md` are the frozen reference. | Do not reopen directly; refine downstream through companion decisions and Gate-0. |
| Phase A — content review | **In progress.** The phase doc says Phase A is current work. | Continue owner-led review and decision capture. |
| Stage 1 — global review | Done; produced S-1/S-2 standards, dependency-order deltas, Gate-0 deltas, substrate-state correction, and triage requirements. | Use as binding input for Stage 2 and later Phase-B plans. |
| Stage 1 continuation / companion material | Conventions, hub/navigation/presets, rubric, Gate V framing, layout simulator idea, and foundational-mechanics prompts have landed as Phase-A material. | Feed Stage 2, Stage 3, Gate V, and Gate-0; do not treat as build approval. |
| Stage 2 — subsystem walk | **Next.** Must walk all 43 subsystems for exact command surface, names, command kind, hub placement, outperform list, and D-5 triage. | Recommended next destination, after accounting for PR #1691 if still open. |
| Stage 3 — consolidation | Future Phase-A close. | Reconcile Stage 2 into the final surface record; feed Gate V and Gate-0. |
| Gate V — verification fleet | Future adversarial verification pass over the finished plan using the ten-class rubric. | Run after Stage 3, not before. |
| Gate-0 — spec-amendment pass | Future docs pass folding amendments and companion deltas into the design spec. | Run after Phase-A/Gate-V survivors are known. |
| Gate 1 / owner ratification | Future owner approval of design + amendments + rebuild go/no-go. | Required before Phase-3 new-repo code. |
| Phase B — per-step planning | Future; explicitly not started until Phase A surface is decided. | Not allowed yet. |
| Phase C — build | Future; execute completed plans. | Not allowed yet. |
| Migration | Future; distinct big plan where current repo is the artifact and new repo becomes source of truth. | Not allowed yet. |

## 3. Blocking inconsistencies

No true blocking inconsistency was found.

The safety gates agree across the major docs:

- `rebuild-planning-phase-2026-07-03.md` says no new-repo code starts until Gate-0 and owner
  ratification land.
- `NEW-BOT-BUILD-PLAN.md` says nothing in the build order starts before Gate 0 and Gate 1.
- `FINAL-REVIEW.md` says Phase-3 new-repo code remains owner-gated and the capstone is evidence,
  not build approval.
- `S3-ai-memory.md` repeats that no Phase-3 new-repo code starts before owner ratification.

The only practical blocker-like concern is PR #1691. If it remains open, Stage 2 should explicitly
mark the Session-B surface/proving foundations report as pending input; if it merges first, Stage 2
should consume it.

## 4. Important improvements

1. **Add a tiny gate-state ledger.** The capstone already proposes `rebuild-gates.yml`; implementing
   it would make the state hard to misread. Suggested initial states: capstone done; Phase-A Stage 1
   done; Stage 2 next; Stage 3 blocked on Stage 2; Gate V blocked on Stage 3; Gate-0 blocked on Gate
   V / Stage-3 consolidation; owner ratification blocked on Gate-0; Phase B/C/Migration blocked.
2. **Normalize the wording for the post-Stage-1 Phase-A additions.** Current-state entries for PRs
   #1680 and #1683–#1688 are best understood as "Stage 1 continuation / Phase-A companion material."
3. **Patch the stale capstone phrase "Build starts after that pass."** The same `FINAL-REVIEW.md`
   later correctly says Phase-3 is owner-gated, but a pointer to the newer Phase-A/Gate-V process
   would prevent a future session from treating the older phrase as standalone authorization.
4. **Make PR #1691 explicit in the foundations brief after merge or close.** Session A is merged in
   the checked-out repo; Session B was still live during this review.

## 5. Cleanup-only issues

- The top S3 row in `docs/current-state.md` still points at Phase-2.5 cold-start A/B as the next
  action, while the lower current-state entries and `docs/current-state/S3-ai-memory.md` correctly
  say the review-then-plan phase is live and Stage 2 is next.
- `docs/current-state.md` says in the #1680 bullet that C-1…C-7 were pending owner reaction, while
  the later #1683 bullet says the owner endorsed them. This is chronological, not contradictory, but
  easy to misread if someone stops at #1680.
- `NEW-BOT-BUILD-PLAN.md` remains intentionally frozen and therefore still contains pre-Stage-1 order
  rows; Gate-0 must fold in the Stage-1 reorder/delta decisions.
- `rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md` still has a "preparation only"
  header while also listing delivered reports. That reflects the file's origin as a launch brief, but
  a status-update line would help.

## 6. Stale or misleading claims to account for

| Claim | Why it can mislead | Disposition |
|---|---|---|
| `FINAL-REVIEW.md` says "Build starts after that pass." | Newer docs add Phase A, Stage 2, Stage 3, Gate V, Gate-0, and owner ratification before build/new-repo work. | Stale phrasing; not a gate bypass because the same file later says Phase-3 remains owner-gated. |
| `docs/current-state.md` top S3 row points to Phase-2.5 cold-start A/B as next. | Newer S3 state says review-then-plan is live and Stage 2 is next. | Stale summary; lower entries and S3 sector file win. |
| Foundations brief says Session B lands a report, but the report was not in the checkout during review. | PR #1691 was live/open, so Session-B findings were not merged truth yet. | Temporary open-PR inconsistency; account for it in the follow-up session. |
| #1680 current-state bullet says C-1…C-7 pending owner reaction. | #1683 later records owner endorsement. | Chronological drift only; later entry wins. |

## 7. Recommended next destination

**Stage 2 subsystem walk**, with a PR #1691 check first:

- If #1691 has merged, consume the Session-B `presentation-verification-mechanics-2026-07-03.md`
  issues ledger as Stage-2 input.
- If #1691 remains open, either wait for it or start Stage 2 with an explicit note that the
  presentation/verification foundations ledger is pending.

Do **not** go to Gate V yet: Gate V is the verification fleet over the finished plan, and the plan is
not finished until Stage 2 and Stage 3 complete. Do **not** start Phase B, Phase C, Migration,
implementation, or new-repo work.

## 8. Review checks performed

- `find .. -name AGENTS.md -print`
- `nl -ba <required-docs> | sed -n ...`
- `rg -n "Phase A|Gate V|Phase B|Phase C|Migration|Gate-0|Stage 1|Stage 2|Stage 3|owner|ratification|frozen|PR #1691|#1691|implementation|new repo|new-repo|do NOT|Not binding|preparation only|Delivered reports|Phase-2.5|Phase-3|Phase 3" <required-docs>`
- `python3 - <<'PY' ... urllib.request.urlopen('https://api.github.com/repos/menno420/superbot/pulls?state=open&per_page=30') ... urllib.request.urlopen('https://api.github.com/repos/menno420/superbot/pulls/1691') ... PY`
- `test -f docs/analysis/rebuild-discovery/foundations/presentation-verification-mechanics-2026-07-03.md; echo presentation_file_exists=$?; test -f docs/analysis/rebuild-discovery/foundations/runtime-logic-mechanics-2026-07-03.md; echo runtime_file_exists=$?; git status --short`

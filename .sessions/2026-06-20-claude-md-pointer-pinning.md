# 2026-06-20 — Pin the always-loaded instruction core against pointer rot

> **Status:** `complete`

Dispatch run, empty work order. The Explore-hub spine PRs (1 + 3) are merged and the
buildable-`ready` decade queue is consumed, so this run takes a fresh ungated lane from
current-state ▶ Next action: the **small stdlib guards** family + the natural completion
of the procedures→skills thin-pointer work.

**Slice 1 — extend `check_docs.py`'s pinned check to the `.claude/` instruction core.**
`check_docs.py` already pins (`check_pinned`) the concrete backtick repo-paths cited in
the three read-path docs (`AGENT_ORIENTATION` / `current-state` / `repo-navigation-map`),
so a moved/renamed target can't rot those pointers silently. But `.claude/CLAUDE.md` and
`.claude/rules/*.md` — the **always-loaded** instruction core, where the procedures→skills
conversion (#1029, #1028) created many *thin pointers* to the runbooks/docs/skills that
hold the HOW — are **not** pin-checked. A pointer there going stale is exactly the
"stale pointer" drift class the bugs-first/Q-0166 mandate exists to catch, and nothing
guards it today. Extend `check_pinned` to also validate those files (the `_PATH_REF_RE`
regex already supports `.claude/`/`.github/` prefixes; paths resolve relative to repo
root, matching how CLAUDE.md cites them). Green on arrival — all 38 concrete refs across
the `.claude/` files resolve today — so this is a preventive ratchet, not a fix.

Scope fence: docs-checker tooling + its tests only. No `disbot/` runtime code, no
CLAUDE.md *content* edits (this is the autonomy boundary — CLAUDE.md stays read-to-me;
I only add a guard that *protects* its pointers), no deploy.

<!-- This card is born-red (in-progress) per Q-0133: the check_session_gate step in
code-quality holds the auto-merge until the Status flips to a ready token. The close-out
docs (Context delta, idea, previous-session review, run report) land before that flip. -->

## Shipped (PR #1162)

Two cohesive slices on one guard, both extending the existing `check_docs.py` `check_pinned`
rule — so the always-loaded read path can't rot a backtick pointer silently:

- **Slice 1 — instruction core.** `check_pinned` now validates the concrete backtick repo-paths
  in `.claude/CLAUDE.md` + `.claude/rules/*.md` (new `_instruction_files()` glob, factored the
  per-file scan into `_pinned_refs_in()`). The `_PATH_REF_RE` regex already supported the
  `.claude/` / `.github/` prefixes; only the *scope* (which files get pin-checked) changed.
  Green on arrival — all 38 concrete refs across the `.claude/` files resolve today.
- **Slice 2 — routine prompts + the drift it caught.** Extended the same check to the two
  canonical routine-prompt / saved-procedure homes the procedures→skills *thin pointers* target
  (`docs/operations/autonomous-routines.md` = reconciliation's saved procedure,
  `hermes-dispatch-bridge.md` = the dispatch prompt) via `_routine_prompt_files()`. This
  immediately **surfaced a real stale pointer** (Q-0166 drift-on-sight): `autonomous-routines.md`
  backtick-pinned `.github/workflows/executor-nightly.yml`, removed 2026-06-15 — de-pinned to the
  bare-name style the other mentions already use.
- Tests: 4 added to `tests/unit/scripts/test_check_docs.py` (instruction-core scope, bare-name &
  `<area>` placeholder skipping, routine-prompt scope, and a real-repo invariant pinning the
  guarded files to zero broken pointers). 27 pass. `check_docs --strict`, `check_quality --full`
  (10942 passed), `check_architecture --mode strict`, mypy all green.

Scope held: docs-checker tooling + tests + one docs-drift fix. No `disbot/` runtime code, no
CLAUDE.md *content* edits (the guard *protects* CLAUDE.md's pointers; it does not change them —
keeping the Q-0106 "CLAUDE.md is read-to-me in an autonomous session" boundary intact).

## Context delta

- **Needed but not pointed to:** that `check_docs.py`'s **pinned** rule (rule 3) is scoped to
  only *three* read-path docs by basename (`_READPATH_DOCS`), while its **link** rule (rule 2)
  covers all of `docs/` — so `.claude/CLAUDE.md` and the routine prompts had *no* pointer
  validation at all. Nothing in orientation flags which checker covers which surface; I had to
  read `check_docs.py` end-to-end to find the gap. (A one-line "what each rule covers" note in
  the checker's module docstring now records it.)
- **Pointed to but didn't need:** the CodeGraph startup stats / symbol tools — this was a
  pure-stdlib docs-checker change; `grep` + reading two files was the whole navigation.
- **Discovered by hand:** that CI **excludes `tests/`** from black/isort/ruff (so the S101
  "assert in tests" ruff noise is a *direct-run* artifact, not a CI signal) — this is in
  CLAUDE.md but easy to trip over when `ruff check <testfile>` screams 47 errors. Trust
  `check_quality.py`, which pins the scope.
- **Decisions made alone:** (1) kept slice-2's pinned scope to the **two named routine prompts**
  rather than all of `docs/operations/*.md`, because that dir also holds dated investigation /
  review snapshots that may legitimately cite moved files — a whole-dir hard gate would create
  friction. (2) Fixed the surfaced stale pointer by **de-pinning** (bare name) rather than
  deleting the sentence, preserving the "executor-nightly was removed" history. Both reversible,
  docs/tooling only.
- **Genuine weak point:** the guard only checks that a backtick path *exists*, not that the
  pointed-to file still *contains the referenced procedure* (the fuller "check_pointer_integrity"
  idea in the procedures→skills plan). Existence-checking catches the move/rename/delete drift
  class (the common one); a pointer that resolves to a file whose *content* moved is still
  uncaught. Noted as the session idea below.

## 💡 Session idea (Q-0089)

**Pointer-target *content* integrity, not just existence.** This run pinned that thin-pointer
*paths* resolve; the next rung is asserting a pointer like "full procedure: `docs/operations/
autonomous-routines.md`" actually still leads to *that procedure* (e.g. the target contains the
referenced Q-number / section anchor), so a procedure relocated *within* the repo can't orphan its
pointer while still passing the existence check. Small/stdlib/disposable (Q-0105) — extend
`check_docs` rule 3 with an optional anchor assertion on `[text](file#anchor)` links in the
read-path + instruction core. Worth it because the procedures→skills convention multiplied these
pointers; existence is the floor, content-resolution is the ceiling. (Dedup-checked: the
procedures→skills plan §Verification floated `check_pointer_integrity` as an idea but never filed
it; this sharpens it to the content half, since the existence half now ships here.)

## ⟲ Previous-session review (Q-0102)

The previous run (federated Explore-hub spine PR 3, `4e891722` / #1160) did the read-only
cross-game world card cleanly and **correctly stopped at PR 3**, flagging PR 2 as
owner/runtime-gated (a live `player_skills` PK migration + a progression-balance design call)
rather than forcing it autonomously — exactly the right SAFETY-brake call. One small miss: it left
current-state's ▶ Next action pointing at "procedures→skills **Batch 1**" when Batch 1 had already
shipped (#1029) — a stale next-action pointer, the very drift class this run's guard targets. The
**workflow improvement it surfaces**: the ▶ Next action callout is now so long that lane-status
inside it (Batch 1 done vs. Batch 2 pending) silently goes stale; a periodic pass should prune
*completed* lane items out of ▶ Next action down into Recently-shipped, not just append. (Captured
here, not built — it's a reconciliation-routine concern, not this dispatch slice.)

## 📤 Run report

- **Did:** pin the always-loaded instruction core + routine prompts against pointer rot (extend
  `check_docs` rule 3) + fix the one stale pointer it caught · **Outcome:** shipped
- **Shipped:** #1162 — `check_docs` pinned-check now covers `.claude/CLAUDE.md`, `.claude/rules/*.md`,
  and the two routine prompts; de-pinned the removed `executor-nightly.yml` path in
  `autonomous-routines.md`; 4 new tests
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** `none` (an ungated small-guard lane already named in current-state ▶ Next
  action — not an idea promoted past a gate)
- **↪ Next:** a *different* ungated lane — consistency-linter AI-nav PR 1 (`needs-hermes-review`,
  needs a runtime/Q-0086 live-walk), procedures→skills Batch 2 (`needs-hermes-review`, edits
  CLAUDE.md), or another small stdlib guard. Explore-hub PR 2 stays owner/runtime-gated.

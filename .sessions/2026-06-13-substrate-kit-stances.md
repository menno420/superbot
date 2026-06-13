# Session (cont.) — substrate-kit PR 2: the task-stance capability layer

> **Status:** `reference` — same session as
> [the 1b-tail checkers](2026-06-13-substrate-kit-1b-checkers.md); the maintainer said "continue", so
> after the checker PRs merged (#802/#804) I executed the **first PR 2 increment** — §3b task stances.
> Shipped as **PR #805**. Resume point is now the **§3c skills + personas** increment.

## What this increment did

PR 2 (the capability layer) is designed to "land in green increments." Built the foundational one —
**stances** — because the skills/personas precedence model references it:

- **`engine/stances/stances.py`** — five core stances (question / analysis / debug / review / plan),
  each with a reading-route, a tool-scope (`read` / `run` / `edit` / `comment`), and an output
  contract. **Python module, not the plan's `stances.yml`** — same reasoning the 1b session gave for
  the question bank: it embeds in the stdlib-only bootstrap with no YAML parser. (Took the better
  impl per the collaboration model's "if a better implementation exists, take it and say why.")
- **conformance:** `action_allowed` / `is_out_of_stance` — what a PreToolUse guard will call to warn
  on an out-of-stance action; **fails open** on an unknown stance. Pinned by a test that **only
  `debug` may edit** (the revision-report session's "zero out-of-stance writes" KPI, made structural).
- **`stance_briefing`** — the orientation-injection primitive (route + tools + contract).
- **cli `stance [name]`** (show / set), wired into the bootstrap + regenerated `dist`.
- `test_stances.py` (15 cases); kit suite 62 → **77**.

Verified: `check_quality --full` green; `check_architecture --mode strict` 0 errors; single-file smoke
(`stance` show/set/invalid→2, `status` reflects it). Authoritative record: the plan Execution log
(repointed RESUME HERE → §3c).

## 💡 Session idea (Q-0089)

**A `simulate --stance <name>` conformance sweep in the kit's smoke harness.** The stance framework
declares tool-scopes, and `is_out_of_stance` is the guard predicate — but nothing yet *exercises* a
scripted session under a stance and asserts the guard would have fired (or not). Extend `cmd_simulate`
(or a sibling `simulate_stance`) to drive a canned action sequence in each stance and emit an
**"out-of-stance action rate" line** (0 for a conformant run), so when the PreToolUse hook lands in a
later PR 2 increment, its behavior is already pinned by a deterministic harness rather than only by
the unit matrix. Cheapest proof the fourth axis is *measurably* safety-bearing end-to-end, and it
slots into the simulate harness that already exists. (Dedup-checked `docs/ideas/` — distinct from the
revision-report's unit-level A5 assertion; this is the *driven-session* version.)

## ⟲ Previous-increment review (Q-0102)

Reviewing **this session's own 1b-tail increment (#802/#804)** — the immediately prior unit. *Did
well:* it closed verification goal (d) opportunistically (template badges → render-clean) instead of
shipping a checker that would flag the kit's own output — catching a latent self-inconsistency the
recipe didn't name. *Could have done better:* the auto-merge fired on #802 before its session-close
docs were committed, forcing the #804 follow-up PR. **System improvement (carried + reinforced this
increment):** for a self-contained subtree like `substrate-kit/`, the durable record is the **plan
Execution log**, not `current-state.md` — I committed the code and the log-repoint together this time
where possible, and where the split is unavoidable (number-after-create), the follow-up is a
*deliberate* docs PR, not an oversight. The standing fix would be a checklist line: "subtree PRs:
land the plan Execution-log repoint in the same branch before the code goes CI-green," so the next
agent doesn't re-discover the auto-merge race.

## Doc audit (Q-0104)

- `check_quality --full` green; `check_architecture --mode strict` 0 errors; `check_docs --strict` +
  `check_current_state_ledger --strict` green (verified before pushing the docs).
- Plan Execution log repointed (RESUME HERE → §3c); roadmap index bullet advanced to #805.
- **current-state.md untouched** — subtree work, tracked in the plan (the #789/#791–793 precedent).
- **Reconciliation still DUE** (#800 crossed; flagged in the #804 PR body + the prior session log) —
  a separate Q-0107 docs-only pass for the next session / the `reconcile` trigger; not done here.
- New owner decisions: none (PR 2 was owner-approved in the plan; the increment slicing is an
  execution call, and "stances as a Python module" follows the established question-bank precedent).

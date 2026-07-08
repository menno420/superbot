# 2026-07-08 — Docs-only fast path: enforce plan homing (from #1854 finding)

> **Status:** `complete`

**Intent:** close the #1843 "green-by-skip" gap — the docs-only fast CI path in
`code-quality.yml` skips pytest (including the live-tree plan-homing test), so a docs-only PR
can land an unhomed plan and redden every subsequent full-CI branch. Wire the pure-stdlib
`scripts/check_plan_homing.py --strict` as an always-run pre-setup step in the required
`code-quality` job (the `check_docs` pattern), so the fast path enforces plan homing in ~a
second. Campaign-dispatched (Q-0194 friction→guard, checker/CI tier) from the PR #1854
§2b archaeology.

## What shipped (PR #1855)

- `.github/workflows/code-quality.yml` — new always-run pre-setup step **"Plan-homing gate
  (check_plan_homing)"** right after `check_docs`: `python3 scripts/check_plan_homing.py
  --strict`. Unconditional (no `if:`), pure stdlib, before Python/pip setup → it runs on the
  docs-only fast path, which was exactly the PR class where the live-tree guard
  (`test_live_repo_plans_are_all_homed`) was skipped.
- `scripts/check_plan_homing.py` — docstring updated: `--strict` is now a per-PR merge gate
  (was "report-only by design / routine cadence"); Q-0105 reliability header updated with the
  CI-gating date and a "demote to advisory / delete if noisy" kill-switch.
- `docs/operations/ci-what-runs-where.md` — §1 row 1 note, §2a new gating row, §2b marked
  CLOSED-for-plan-homing, §2d annotated (also per-PR gate now).

## Ground-truth proofs (Q-0120)

- **Fails when it should:** induced `docs/planning/zz-scratch-unhomed-plan-proof-2026-07-08.md`
  (`plan` badge, no routing link) in the working tree only → `--strict` exited 1, named the
  file. Never committed.
- **Passes on the live tree:** `check_plan_homing: OK — all 81 live plan docs … are linked
  from a routing doc`, exit 0, 0.65s wall.
- **Runs in CI:** this PR touches workflows/scripts → full CI path (expected). A post-merge
  scratch draft PR (docs-only diff + induced unhomed plan, `do-not-automerge`, closed
  immediately, branch deleted) demonstrates the fast path executes the gate red — recorded in
  the coordinator report; result was not known at card-flip time (the workflow change must be
  on `main` before a docs-only PR can exercise it; a scratch PR carrying the workflow edit
  would itself take the full path).

## Decisions (decide-and-flag)

- **Shape (b)-adjacent, as its own named step, not folded into `check_docs.py`:** the checker
  already exists, is stdlib, and a named step gives per-check attribution in the checks UI
  (the §2b follow-up idea explicitly wants named-step attribution). One workflow step beats
  editing `check_docs`'s scope.
- **Unconditional (every PR), not docs-only-gated:** ~1s on full-path PRs is noise, and it
  gives a fast named failure before the 3-minute pytest run reaches the same live-tree fact.
- **Docstring/reliability header updated in the same PR** so the script's self-description
  doesn't contradict its wiring (Q-0120 class).

## Session enders

- **💡 Session idea (Q-0089):** a *fast-path deps-parity test* — extend
  `tests/unit/scripts/test_workflow_script_flags.py` (or a sibling) to assert every
  **unconditional** step in `code-quality.yml` (no `if: steps.changes.outputs.code == 'true'`)
  invokes only scripts whose imports are stdlib (no PyYAML etc.), since pip install hasn't run
  yet at that point. The failure mode is real: an agent copying the `check_consistency` pattern
  into the pre-setup block would redden **every docs-only PR** with an ImportError.
  Dedup-checked: `live-tree-test-culprit-attribution-2026-07-08.md` covers *adding* stdlib
  guards to the fast path, not *guarding the stdlib-ness* of that block. (Logged here only —
  campaign scope excludes new `docs/ideas/` files this session.)
- **⟲ Previous-session review (Q-0102):** the #1854 grooming session's §2b archaeology was
  exemplary — timestamped run evidence (12s green on `faaa29f`), the exact commits that
  hand-fixed the drift, and a crisp root-cause class. What it left open: the enforcing guard
  itself, which Q-0194 wants shipped the same session friction is found — defensible under its
  docs-only scope, and the workflow *self-corrected* (its finding became this dispatched
  session within hours). Improvement surfaced: a grooming/docs session that identifies a
  one-step enforceable guard could name the exact step in its handoff (「add step X after
  step Y」) so the follow-up session is pure execution — #1854 §2b did nearly that, which is
  why this session was cheap.
- **Q-0104 docs audit:** `check_current_state_ledger --strict` green (benign newest-merge lag
  ≤ marker rules); `check_docs --strict` green; no new owner decision → no router entry; the
  gate's durable home is `ci-what-runs-where.md` (updated in this PR). Nothing chat-only left.
- **Provenance:** campaign-dispatched worker session, from the PR #1854 §2b finding
  (coordinator task, Q-0194 checker/CI tier — free-to-ship lane).

# 2026-07-08 — Docs-only fast path: enforce plan homing (from #1854 finding)

> **Status:** `in-progress`

**Intent:** close the #1843 "green-by-skip" gap — the docs-only fast CI path in
`code-quality.yml` skips pytest (including the live-tree plan-homing test), so a docs-only PR
can land an unhomed plan and redden every subsequent full-CI branch. Wire the pure-stdlib
`scripts/check_plan_homing.py --strict` as an always-run pre-setup step in the required
`code-quality` job (the `check_docs` pattern), so the fast path enforces plan homing in ~a
second. Campaign-dispatched (Q-0194 friction→guard, checker/CI tier) from the PR #1854
§2b archaeology.

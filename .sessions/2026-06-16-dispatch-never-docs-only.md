# Session — dispatch is never "docs only" (Q-0148)

> **Status:** `in-progress`

## What I'm about to do

Owner-directed in-session correction. A test fire of Hermes' dispatch capability stamped the work
order **"CLASS: docs · no runtime code or feature scope"** — but the **dispatch routine does ALL
build work**; only the **reconciliation routine** is docs-only. The owner: *"it's never docs only,
only the reconciliation routine should be docs only — please update the repo in such a way that
this is absolutely clear."*

Make it unmistakable, on both sides of the dispatch bridge:
- `docs/operations/hermes-dispatch-bridge.md` — saved dispatch prompt: a work order's `CLASS:` /
  scope notes never make the routine docs-only; it builds whatever the task needs. **Also fix a
  real bug found here:** step 8 has an accidental duplicate-paste (4 repeated lines) that rode into
  the live routine prompt.
- `docs/operations/autonomous-routines.md` — make the dispatch-never-docs-only vs.
  reconciliation-only-docs split loud in the split paragraph + fleet table.
- `docs/operations/hermes-skills/dispatch.md` — forbid Hermes from putting a scope-restriction
  ("docs only" / "no runtime code") in a dispatch work order.
- `docs/owner/maintainer-question-router.md` — record the decision as **Q-0148** (provenance).

Docs-only; no runtime code. `check_docs --strict` is the acceptance.

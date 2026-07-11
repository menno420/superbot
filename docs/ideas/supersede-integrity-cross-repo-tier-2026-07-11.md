# Cross-repo successor tier for `check_supersede_integrity.py` (2026-07-11)

> **Status:** `ideas` — raised 2026-07-11 (forty-third Q-0107 reconciliation pass).
> **Subsystem:** tooling / docs-system.
> **Gate:** ready — small, self-contained checker change; disposable per Q-0105.

## The problem this pass hit

`scripts/check_supersede_integrity.py` models supersession as an **in-repo handshake**:
banner → resolvable markdown link to a successor doc → successor links back → badge is
not `plan`. That is exactly right for a doc superseded by another doc *in this repo*.

But the fleet now routinely supersedes docs **across repos**. This pass hit five of them:
the round-3 founding packages (`builder`, `idea-engine`, `product-forge`, `simulator`,
`substrate-kit`) were frozen because their canonical copies moved to fleet-manager
`projects/superbot-next/` (registry PR #39). Their banners honestly *name* the successor —
in prose — but it lives in another repo, so the checker's link-resolution can never
succeed. Re-badging `plan`→`historical` cleared the badge half (the finding that matters),
but the "banner names no successor doc" half is a **permanent false positive**: there is no
in-repo doc to link, and inventing one would create a *dishonest* one-sided handshake that
the checker would then also flag.

Net: every cross-repo supersession leaves a soft warning that no honest edit can clear, so
the checker's signal degrades toward noise as the fleet grows.

## The idea

Add a **cross-repo successor tier** to the checker. When a SUPERSEDED banner names its
successor as an explicit cross-repo reference — a recognizable pattern such as
``fleet-manager `projects/…``` / `<repo-name> PR #<n>` / a `https://github.com/menno420/<repo>`
URL — treat that as a **satisfied disposition** (the successor is named and locatable, just
not in this tree) and suppress the "names no successor doc" finding, provided the badge is
already `historical`/`reference` (never `plan`). Keep the strict in-repo handshake for
same-repo supersessions unchanged.

Optionally emit a distinct, quieter line (`cross-repo successor — not verifiable in-repo`)
so the disposition is *visible* without being *actionable-forever*, and so a future
fleet-aware verifier could one day resolve it over git transport (the #1923 pattern).

## Why it's worth having

- Removes a class of permanent, unclearable soft noise that will only grow with the fleet.
- Keeps the checker honest: it stops asking for an edit that can only be satisfied
  dishonestly.
- Cheap and disposable (Q-0105): a pattern match + a badge guard, plus a couple of tests
  (a cross-repo banner passes; an in-repo phantom successor still fails).

Not a plan yet — capture only. If promoted, scope it as one small tooling PR against
`scripts/check_supersede_integrity.py` + its test suite.

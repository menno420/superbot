# Idea — a cross-repo EAP verification orientation pointer (per-repo interpreter + clone-and-run flow)

> **Status:** `ideas` — captured 2026-07-09 (fortieth reconciliation pass, Q-0089). One-line why:
> the fleet-review session assembled the cross-repo verification flow by hand and lost time to a
> 75-phantom-failure interpreter trap that a one-paragraph orientation pointer would have prevented.
> **Implemented 2026-07-09** (groomed same day as a fleet wind-down audit lived the exact flow
> across 9 repos): the pointer now lives at
> [`../AGENT_ORIENTATION.md`](../AGENT_ORIENTATION.md) § "Auditing / verifying a sibling EAP
> Project repo (cross-repo)". This capture stays as the record of the original friction.

## The friction (observed, not hypothetical)

The 2026-07-09 independent fleet-review session
([`.sessions/2026-07-09-projects-eap-fleet-review.md`](../../.sessions/2026-07-09-projects-eap-fleet-review.md)
§ Context delta) hit two avoidable snags because the **cross-repo review flow is not in the
orientation route**:

1. **Per-repo interpreter split.** `superbot-next` runs on **Python 3.11** (its `ci.yml`), not
   superbot's pinned **3.10**. Running its suite under 3.10 produces **~75 phantom failures**; under
   3.11 it's green. The whole repo's `.claude/CLAUDE.md` § "Match CI exactly" hard-codes 3.10 — correct
   *for superbot*, actively misleading when verifying a sibling repo.
2. **The flow itself is undocumented.** `add_repo` → GitHub-MCP across repos → **clone the sibling repo
   and run its own tests** (first-party verification over trusting a completion report) had to be
   assembled by hand each time.

Now that the EAP fleet is **four repos** (`superbot`, `superbot-next`, `substrate-kit`, `websites`),
any oversight/manager session repeats this — and every future manager-Project run inherits the same
trap.

## The idea (small, docs-only)

Add a short **cross-repo verification** pointer to the orientation route (a stub in
`docs/AGENT_ORIENTATION.md` "Reading order by task" → a one-screen note, natural home
`docs/eap/` next to the fleet review, or `docs/operations/`):

- **Verify a sibling repo with its own CI interpreter**, not superbot's 3.10 — a per-repo table
  (`superbot` = 3.10, `superbot-next` = 3.11, others TBD), sourced from each repo's `ci.yml`.
- **The clone-and-run flow, named**: `add_repo` (session scope) → GitHub-MCP for PRs/diffs/CI →
  `git clone` the sibling → run *its* `pytest` / manifest compiler / checkers under *its* interpreter.
- **First-party over trust**: prefer clone-and-run to accepting a completion report's counts (the
  fleet review's own practice — it caught nothing wrong this time, but the discipline is the point).

## Why it's worth having

- It converts a **repeatable, already-observed** friction into a one-paragraph guard (Q-0194
  friction→guard, docs tier — free to ship).
- The manager-Project brief ([`../planning/eap-manager-project-brief-2026-07-09.md`](../planning/eap-manager-project-brief-2026-07-09.md))
  will drive exactly this flow on a cadence; giving it a durable pointer stops each run from
  re-deriving it.
- Cheap to promote: a `route-idea` / `groom-ideas` pass can lift this straight into a stub without a
  planning session.

## Route in

`docs/AGENT_ORIENTATION.md` (the reading-order router) · `docs/eap/` (the fleet corpus) ·
the manager-Project brief. A checker is overkill; a pointer is the right altitude.

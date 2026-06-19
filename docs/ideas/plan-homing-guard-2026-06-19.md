# A `check_plan_homing.py` guard — no active plan goes unrouted

> **Status:** `ideas` — session idea (Q-0089), from the 2026-06-19 planning-map cleanup. **Not a plan,
> not approval.** Source + the binding contracts win. Disposable dev tooling (Q-0105).
> **Subsystem:** none — agent-workflow / docs-system tooling, not a bot subsystem.

## The gap this closes

The planning-map cleanup found the project's **dominant active thread** — the dashboard / control-API /
website initiative (~8 `plan`-badged docs) — was **reachable only by directory listing**: not linked
from `roadmap.md`, any folio, or `current-state.md`. `check_docs.py --strict` did **not** catch it,
because its reachability check **exempts `historical`/`archive` badges** and otherwise only needs *one*
inbound link from *anywhere* in `docs/` — a plan cross-linked solely by a sibling planning doc counts as
"reachable" while being invisible to every agent route. So a live plan can rot off the map and CI stays
green — the "green check that contradicts visible evidence" pattern CLAUDE.md § CI-parity warns about.

## The idea

A tiny stdlib `scripts/check_plan_homing.py` (the `check_docs.py` house style) asserting:

> every **non-`historical`/non-`reference`** doc under `docs/planning/` has **≥1 inbound link from a
> *routing* doc** — `roadmap.md`, a `docs/subsystems/*.md` folio, `docs/current-state.md`, or the new
> `docs/planning/README.md` plan index.

Report-only by default (lists the homeless `plan`-badged docs); `--strict` exits 1 for the reconciliation
cadence pass. It is the **routing** complement to `check_docs`'s **reachability** check: reachability asks
"is it linked from *anywhere*?"; homing asks "is it on an agent's *map*?". The plan index this session
created is the natural anchor — a new plan added to `docs/planning/` without a README/roadmap/folio row
would trip the guard, keeping the index honest going forward.

## Why it's worth having

- It would have flagged the dashboard cluster the day the first dashboard plan landed, instead of it
  drifting for ~30 PRs until a manual mapping pass found it.
- It turns "every active plan is homed to a sector + folio" (a prose promise in `repo-sector-map.md` and
  this session's `planning/README.md`) into a **checkable invariant** — the same move that made the
  folio↔sector wiring self-maintaining (`check_sector_map.py`).
- Cheap, read-only, stdlib, disposable (delete if it proves noisy over a few sessions, per Q-0105).

## Scope / cautions

- Runtime-lane (a new `scripts/` check), so **out of scope for a docs-only pass** — build it in a session
  that touches tooling.
- Tune the "routing doc" allow-list so a deliberately-parked draft (a Someday horizon linked only from
  `roadmap.md` Someday) still counts as homed.
- Pairs with the existing `check_plan_backlog.py` (depth) and `check_sector_map.py` (folio homing) — this
  is the **plan-level** homing guard those two don't cover.

→ relates `scripts/check_docs.py` (reachability) · `scripts/check_sector_map.py` · `docs/planning/README.md` ·
`docs/roadmap.md`.

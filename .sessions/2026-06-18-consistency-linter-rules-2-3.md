# Session — 2026-06-18 · consistency linter PR 2 + PR 3 (back-button + panel base-class rules)

> **Status:** `in-progress`

## What I'm about to do
Scheduled dispatch, **empty work order** → `current-state.md` ▶ Next action names the
**repo-consistency-linter (Q-0170)** continuation: PR 1 (harness + rule 1 edit-in-place)
shipped #1042; **rules 2 (back-button presence) + 3 (panel base-class)** are the named next
slices ([plan](../docs/planning/repo-consistency-linter-plan-2026-06-17.md) build order step 2).

Building both, warn-only, same house pattern as rule 1:
- **Rule 2 — back-button presence:** a `HubView` navigation panel with its own child
  button/select callbacks but no back/nav affordance anywhere in its module (the shared
  `views/navigation.py` helpers `attach_back_*` / `chain_back`, or a back-labelled button).
- **Rule 3 — panel base-class:** a view extending `discord.ui.View` directly outside the
  `views/rps`,`views/blackjack` game-state allowlist + the `views/base.py` framework home
  (the arch-doc prose rule, now mechanically enforced — warn-only).

Each ships with positive + negative fixtures in `tests/unit/scripts/test_check_consistency.py`.

Also reconciling the #1042 ledger lag (the SessionStart ledger guard flagged it).

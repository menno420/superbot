# 2026-06-22 — NEW idle egg/chicken farm game

> **Status:** `complete` — born-red card (Q-0133) flipped green as the final step.
> Owner-directed task ("Idle egg/chicken farm") → built end-to-end (Q-0191 merge-immediately).
> PR #1328 → auto-merges on green CI (Q-0123).

## What shipped

Stood up the bot's first **idle** (accrue-over-time) game, complementing the active games
(mining grid, fishing, creatures). Hens lay eggs over time; collect → coins + game XP; spend
coins on more hens (faster lay rate) and a bigger coop (larger egg cap).

The idle mechanic **reuses the `settle()` lazy-accrual pattern** (a stored value + a timestamp,
computed from elapsed time — **no background ticker, no Redis**: ADR-001/002), exactly like
`utils/fishing/energy.py` / `utils/mining/energy.py`. Because all state lives in one
`chicken_farm` row, the farm is incidentally fully restart-safe.

Layering mirrors the fishing arc:
- **`utils/farm/`** — pure domain: egg accrual (`settle`), coop capacity, hen/coop pricing,
  caps, the egg bar. 23 unit tests (`tests/unit/utils/test_farm.py`).
- **`services/farm_workflow.py`** — the audited write boundary (RS02/Q-0071): `collect` /
  `buy_chicken` / `upgrade_coop`, one `db.transaction()` per op, coin legs via
  `economy_service.{credit,debit}_in_txn`, EventBus emit after commit. Buying a hen settles
  eggs at the *old* flock size first (so the faster rate never applies retroactively).
- **`utils/db/games/farm.py`** + **migration 090** — the `chicken_farm` CRUD (conn-aware).
- **`views/farm/`** — `FarmMenuView` (🥚 Collect · 🛒 Shop · 🔄 Refresh) + `FarmShopView`
  (🐔 Buy hen · 🏠 Upgrade coop · ◀ Back). The shop is a sub-view (mirrors mining's
  workshop split) — cleaner UX and genuinely actionable from day one.
- **`cogs/farm_cog.py`** — `!farm`/`!chickenfarm`/`!coop`, the Help hook, and the
  Explore-world registration (🐔 Farm).
- Wiring: `SUBSYSTEMS["farm"]` (Games-hub child, `activities`) · `GAME_FARM` + `collect_eggs`
  award in `game_xp_service` · `INITIAL_EXTENSIONS` · `hub_registry` Games children ·
  `extension_roles.yaml` overlay.

**Faucet discipline:** the collect faucet is deliberately modest (one free starter hen banks
~40 coins over ~100 min idle) — the owner's standing "rewards too large & too frequent"
caution; buying hens scales the faucet but each costs more coins (the self-balancing sink).

### Incidental improvement
The Games hub view (`views/games/hub.py`) packed all `activities` buttons onto one row —
which silently breaks at the **6th** activity (Discord's 5-per-row cap), farm or not. Rewrote
the layout to pack each `hub_group` across rows (≤ 5/row), so groups now wrap instead of
overflowing. Updated the row-contract test accordingly (activities = row ≥ 1).

## Verification

- `python3.10 -m pytest tests/unit` → **11694 passed, 47 skipped, 2 xfailed, 0 failed**.
- `check_quality.py --check-only` → black/isort/ruff/check_docs/check_consistency/tool-pins ✓.
- `mypy disbot/` → 0 errors. `check_architecture.py --mode strict` → 0 errors.
- Regenerated + verified the pinned artifacts: `site.json`/`data.js`, `dashboard.json`,
  `env-vars.md`, `extension-taxonomy-crosswalk.md`, atlas.
- Doc-audit (Q-0104): `check_current_state_ledger --strict` (only benign newest-merge lag,
  not mine) + `check_docs --strict` ✓.
- Not live-verified in Discord (no sandbox bot run); the loop is unit-covered + the panel is
  CI-asserted actionable.

## Enders

- **💡 Session idea (Q-0089):** "while you were away" offline-progress summary for idle games —
  [`docs/ideas/idle-game-offline-summary-2026-06-22.md`](../docs/ideas/idle-game-offline-summary-2026-06-22.md).
  The return-moment narration is what makes idle games sticky, the accrual math already
  exists, and it's a clean rule-of-three extraction candidate (farm + the two energy bars).
- **🧹 Grooming (Q-0015):** captured the above idea at `captured` with a next step (small
  single-PR slice / direct execute). The farm itself drained the standing "idle game" thread
  from the games-mining-idle roadmap draft.
- **⟲ Previous-session review (Q-0102):** the previous session (`tool-pins-ci-guard`) did the
  *right root-cause thing* — it promoted its own logged idea (local-only pin checker → a CI
  guard) and closed the #1315 three-places-drift class at the root, with tests. What it could
  have flagged: the guard it added is `paths`-filtered but **not yet a required check**, so it
  still relies on a one-line owner repo-Settings step to actually block merges — that gap was
  noted but left open. *Workflow improvement it surfaces:* a new "make-it-required" CI guard
  should ship with a tiny checklist item (or an issue) tracking the manual GitHub Settings
  promotion, so "guard exists but doesn't block" can't quietly persist across sessions.
- **📚 Doc audit (Q-0104):** games folio updated with an "Idle games" section (the pattern +
  how to add another); help-surface-map + settings-command-map + crosswalk regenerated/edited;
  no chat-only facts left undocumented. No current-state ledger entry added — PR unmerged, the
  next reconciliation records it (the no-"pending" convention).

## ⚑ Self-initiated: none beyond the owner-directed task (the Games-hub row-wrap fix is a
bug found mid-task and fixed at the root; the idea is captured, not built).

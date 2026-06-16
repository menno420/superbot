# Session — Dashboard cog & command explorer (`/commands`)

> **Status:** `in-progress`

## Origin

Owner (2026-06-16, after the dashboard went live): *"add the second layer … browse all the different
cogs and all the commands they have, with a clean separation of the commands that have a button and
those that are only prefix or slash based, it should also be able to show if it's slash command or
prefix … if you have any other ideas implement at the same time."*

## What shipped

- **`scripts/scan_commands.py`** (stdlib, AST) — scans `disbot/cogs/**` for every cog + command:
  invocation **type** (prefix / slash / both, from the decorator), aliases, brief, group subcommands,
  and **button-backed** — the project's own `extras={"classification": "panel_action"}` marker (see
  `core/runtime/command_surface_ledger.py`) OR a body that opens a view
  (`panel_manager`/`send_panel`/`*View(`/`view=`). Live numbers: 41 cogs · 300 commands · 275 prefix /
  25 slash / 108 button-backed.
- **`scripts/export_dashboard_data.py`** — new `cogs` section + `cogs`/`commands` counts, via the same
  importlib seam as the env scanner (still pure stdlib; CI install unaffected).
- **`/commands` page** (`dashboard/app.py` + `templates/commands.html` + nav + home card): cogs
  grouped (with subsystem emoji/name cross-linked from the registry), each command badged
  **prefix/slash** and **🔘 button**, plus classification + aliases + brief.
- **Other ideas added at the same time:** a stats header (commands · prefix · slash · button · cogs),
  a live **search** box, and **filter chips** (All / Prefix / Slash / 🔘 Button) — tiny inline JS, no
  build step — plus the home-page Commands card.
- **Tests:** `test_scan_commands.py` (types · aliases · panel_action · opens-view · subcommands · real
  repo) + `/commands` added to the app smoke + a `cogs`-section exporter test.

## Verification

- `python3.10 scripts/check_quality.py --full` → **green (10151 passed, 37 skipped)**; ruff/black/isort
  clean; `check_docs --strict` green.
- `/commands` renders all 300 commands locally (TestClient → 200; badges, search, filters present).
- Deploys via the dashboard service already tracking `main` (auto-redeploys on merge).

## 💡 Session idea (Q-0089)

**Reconcile the AST command scan against the runtime ledger.** `scan_commands.py` approximates
`core/runtime/command_surface_ledger.py` (the runtime truth) from source. A tiny test that diffs the
two — names + types + classifications — would catch drift (a command the AST misses, or a
classification only resolved at runtime), turning `/commands` into a *verified* mirror rather than a
best-effort one. Small/decided-lane.

## ⟲ Previous-session review (Q-0102)

Previous: the **dashboard deploy fix (#970)** (same conversation). Did well: traced the gitignored
`static/` root cause from the Railway runtime logs and removed the dependency cleanly. The deeper
lesson — proven twice now — is that #967 shipped a `static/` mount that was never deploy-tested. This
session benefited directly: `/commands` adds **no** new static asset, and the service now
auto-redeploys from `main`, so a real deploy validates it. The "git-tracked assets" guard idea from
#970 remains the durable fix for that whole class.

## Documentation audit (Q-0104)

- `check_docs --strict` green. `/commands` documented in `dashboard/README.md`; the plan's
  surface-don't-duplicate table gains a cog/command-explorer row. Executes the owner's direct
  in-session request → no new router decision needed.
- Not a bug → no bug-book entry. `current-state.md` In-flight names no open PRs (convention); the
  merge-time reconciliation (Q-0124) folds #967/#969/#970 + this PR into the ledger.

# Session — Dashboard: settings + access pages, and the live help-editor plan

> **Status:** `complete`

## Origin

Owner: *"continue with the website from PR 974 … eventually everything the bot does and can should
be displayable … I'd also like to be able to edit the help message and command panels directly from
the website, so you can move buttons to wherever you want."* I confirmed the idea, asked four scoping
questions (`AskUserQuestion`), and got: **edit the live bot · help text & visibility first · Discord
OAuth · surface all four read-only areas** (settings, access, status/health, games). Recorded as
**router Q-0156**.

## What shipped (this PR)

Two new **read-only showcase pages** (the safe, decoupled, scanner-driven pattern) + the **design
doc** for the headline live-editor feature.

- **`/settings` — settings & configuration catalogue.** `scripts/scan_settings.py` (pure stdlib AST)
  reads `disbot/utils/settings_keys/*.py` → 83 keys across 13 subsystems; page groups by domain with
  a live filter. **Key names only, never stored values.**
- **`/access` — permissions & access map.** `scripts/scan_access.py` is a **faithful static mirror**
  of `disbot/utils/visibility_rules.get_subsystems_for_tier`: the tier ladder (user→owner) + each
  tier's Discord-permission gate + the subsystems first visible at each tier. A real-repo test
  asserts the mirror's cumulative sets **equal the live rule** (verified mirror, not an approximation).
  Page carries the *visibility ≠ execution* caveat.
- Wired both into `scripts/export_dashboard_data.py` → `dashboard/data/dashboard.json` (+ counts);
  added `/settings` + `/access` routes (`dashboard/app.py`), nav (`base.html`), landing cards
  (`index.html`); regenerated the committed JSON.
- **`docs/planning/dashboard-live-editor-plan.md`** — the live help/panel editor architecture:
  edits hit the **live bot** via a **private-network control API** the bot exposes over the *existing
  audited* `help_overlay_mutation` seam (never raw DB writes — that would bypass audit + stale the
  overlay cache); **Discord OAuth** on the website; the bot re-checks `administrator` per write.
  Help text/visibility is L0–L2; the "move buttons" panel-layout engine is greenfield (L3).

## Verification

- `python3.10 scripts/check_quality.py --check-only` → **green** (black/isort/ruff + check_docs).
- `python3.10 -m pytest tests/unit/scripts/test_scan_settings.py tests/unit/scripts/test_scan_access.py
  tests/unit/scripts/test_export_dashboard_data.py tests/unit/scripts/test_scan_commands.py` → **16 passed**.
- Dashboard app smoke (`tests/unit/dashboard/test_app.py`, +/settings +/access) — `importorskip`-guarded,
  skips in CI (web deps not in the bot's `requirements.txt`); runs locally with the dashboard deps.
- No `disbot/` runtime touched → `check_architecture` unaffected (re-confirmed strict at close).

**Merge ≠ deploy:** the dashboard is a second Railway service that **auto-redeploys on merge to
`main`** — `/settings` and `/access` go live after the deploy completes.

## 💡 Session idea (Q-0089)

**An "execution access map" companion page** (`/access` shows *visibility*; the bot already computes
*execution* via `services/access_projection.py` — `routed_off` / `command_locked`). A second page (or
a toggle) rendering the execution view beside visibility would make the *"Help advertises a locked
feature"* gap **visible on the website**, not just in the P1B drift provider. Concrete and grounded in
what I learned tracing the help projection. (Logged here; promote to an idea file if it gets picked up.)

## ⟲ Previous-session review (Q-0102)

Previous lane session: **#974 — dashboard plan + next-session handoff (docs-only).**
- **Did well:** a genuinely strong handoff — the "⭐ Next session — start here", the live Railway
  state, and the Railway-API how-to let me move straight to building instead of re-deriving deploy
  state. This is the workflow working as intended.
- **What it could have done better:** the handoff enumerated *phases* but not the **existing bot
  systems each phase would touch**. The owner's very next ask ("edit help from the website") lands
  squarely on the mature, already-shipped **Help overlay** system (`help_overlay_mutation`, the
  in-Discord `views/help/editor.py`) — which the handoff never mentions, so I had to discover it. A
  feature handoff that lists *"related systems that already exist"* would have saved that rediscovery.
- **Workflow improvement:** plan/handoff docs for an interactive feature should carry a short
  **"existing systems to reuse / not duplicate"** stanza (the context-compiler's `do_not_create`
  idea, applied to handoffs). I seeded this by making the live-editor plan's *decisive finding*
  exactly that inventory.

## Documentation audit (Q-0104)

- `check_docs.py --strict` → green (new plan doc reachable; Q-0156 recorded in the router).
- New owner decision (Q-0156) recorded with provenance; `dashboard/README.md` + the dashboard plan's
  shipped table + `docs/current-state.md` updated to point at the two pages and the editor plan.
- The SessionStart "9 merged PRs not in current-state" notice is the **reconciliation backlog**
  (Recon DUE at #960) — *not* this session's job (Q-0124: a manual session doesn't run the recon
  pass). Left for the routine; my own PR is added to the living ledger here so it isn't a 10th gap.
- Grooming (Q-0015): advanced the dashboard idea backlog — executed two of the "everything
  displayable" surfaces and **structured the bigger "edit from the website" idea into a planning doc**
  (`dashboard-live-editor-plan.md`) with a phased L0–L3 roadmap. Remaining surfaces (status/health,
  games) named as the next band.

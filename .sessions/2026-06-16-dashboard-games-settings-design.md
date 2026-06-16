# Session — Dashboard: `/games` showcase + settings-editor design (global + per-server)

> **Status:** `complete`

## Origin

Continuing the website. Owner: *"yes go ahead [with the games & economy showcase], would it also be
possible to edit the settings from the website? It's fine if that triggers a redeploy, and as bot
owner let me change things globally as well as per-server."*

## What shipped (this PR)

**`/games` — games & economy showcase** (the last of the four read-only surfaces from Q-0156). A new
route + template that groups the **games / economy / progression** subsystems from the existing
`data.catalogue` (emoji, description, capabilities, play commands, tier) and lists their tunable
setting keys — **no new scanner, no regen** (reuses data already in `dashboard.json`). Nav + smoke
test (`/games`) added.

## Settings-editor design (answers the owner's question — recorded, not yet built)

Researched the settings model: `utils/db/settings.py` is a per-guild KV store
(`get_setting(guild_id, key, default)`); **defaults are scattered at call sites, there is no global
layer** — but `core/runtime/feature_flags.py` already resolves **per-guild → global → default**, the
exact shape to mirror. Design recorded in `docs/planning/dashboard-live-editor-plan.md`
§ "Settings editor" + router **Q-0157**:

- **Global layer** (`guild_id = 0` or a `global_settings` table) + `get_setting` →
  per-guild → global → default (one function, hot path → focused runtime PR).
- **Audited `settings_mutation` seam**; website (owner auth) → control API → seam with a **scope
  picker** (global = owner-gated, per-server = admin-gated, re-checked bot-side).
- **"Redeploy is fine"** → with the DB global layer **neither scope needs a redeploy** (applies live);
  the redeploy/code-default path is messier (scattered defaults) and only a fallback.
- **Prerequisite:** a **settings-metadata registry** (key → type/default/label/scope) — safe,
  additive, and it also enriches the read-only `/settings` page. Build first.

## Verification

- Dashboard smoke **with deps installed**: `python3.10 -m pytest tests/unit/dashboard/test_app.py`
  → **17 passed** (`/games` renders).
- `python3.10 scripts/check_quality.py --check-only` → green.
- No `disbot/` runtime touched (the settings editor is design-only this PR).

**Merge ≠ deploy:** the dashboard auto-redeploys on merge; `/games` is live after the redeploy.

## 💡 Session idea (Q-0089)

**Make every read-only catalogue page a writable surface via one shared "edit field" component.**
`/aliases` (suggest), the coming settings editor, and the help editor all repeat the same shape:
show current value → propose/edit → validate (collision/type) → route to a destination (issue / PR /
control-API). A single dashboard component (`field`, `current`, `scope`, `validator`, `sink`) would
let any future catalogue page (`/settings`, `/access`, `/commands`) grow an edit affordance without
re-inventing the flow — the dashboard analogue of the bot's audited-mutation seam.

## Documentation audit (Q-0104)

- New owner decision recorded (Q-0157) + the design has a durable home in the live-editor plan.
- The SessionStart "7 merged PRs not in current-state" notice is the reconciliation backlog
  (Recon DUE) — the routine's job (Q-0124), not this manually-started session's.
- `check_quality --check-only` (incl. `check_docs`) green.

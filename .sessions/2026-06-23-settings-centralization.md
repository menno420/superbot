# 2026-06-23 — Settings centralization: a static settings-reachability guard

> **Status:** `in-progress` — owner-directed (the last unstarted item in the five-part consolidation
> goal). Builds the **static settings-reachability guard** — the settings analog of the #1370 command
> guard — so "every cog's settings reachable from the `!settings` hub" (brief §3.4) becomes
> un-regressable. PR this session; auto-merge armed on green (Q-0127); owner-directed → merge immediately
> (Q-0191).

> **Run type:** `manual · owner-directed`

## Finding (code-verified, no live bot)

The settings surface is already **structurally centralized**, but it was only *checkable* via a live-bot
catalogue build (`customization_catalogue.build_catalogue(bot)` needs loaded cogs — static `bot=None`
over-reports 41/41). The AST-verifiable facts:

- **19 subsystems declare a `SubsystemSchema`** (`cogs/*/schemas.py`) → auto-dispatched into `!settings`
  via `actionable_settings_groups()`. **All 19 are reachable** (non-internal + homed) — 0 gaps.
- **3 subsystems have a `.configure`/`.settings.*` capability but no schema:** `counting` + `chain`
  (per-**channel** game enablement, configured in their own `!countingmenu`/`!chainmenu` panels — a
  bespoke per-channel data model, *not* a guild-scalar setting) and `channel` (`channel.visibility.configure`
  is an admin **action**, not stored config). These are **intentionally domain-panel-configured**, not a
  centralization gap → explicit allowlist with reasons (mirrors how #1370 allowlists reachable-via-panel
  commands).

So there is no schema to *add* (inventing one for per-channel game setup would be wrong); the work is the
**guard + documented allowlist** that pins the boundary and fails CI if a *new* subsystem adds a schema
but isn't homed, or grows a `.configure` capability without either a schema or an allowlist entry.

## Deliverable (mirrors #1370)

- `scripts/check_settings_reachability.py` — static guard (registry + AST scan of `cogs/*/schemas.py`).
- `architecture_rules/settings_reachability_exceptions.yml` — allowlist (counting/chain/channel + reasons).
- `tests/unit/invariants/test_settings_reachability.py` — the CI invariant (warn-first ratchet baseline).
- `docs/audits/settings-reachability-2026-06-23.md` — the finding + exemption ledger.

(Close-out enders at session close.)

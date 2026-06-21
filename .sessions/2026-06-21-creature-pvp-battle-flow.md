# 2026-06-21 — Creature PvP battle flow (cog + views + service)

> **Status:** `complete` — the user-facing creature PvP flow shipped on top of the
> already-merged pure engine (`disbot/utils/creatures/battle.py`, PR #1213). Plus a
> small backlog-grooming slice (the previous session's Q-0089 extension-integrity
> CI guard). PR #1230; owner armed auto-merge → merges on green.

> **Run type:** `routine · dispatch`

## Arc

Empty scheduled fire → advanced the named current-state ▶ NEXT slice: the creature-game
v1 **user-facing PvP flow**, docking onto the shipped engine. No open PRs (no duplicate
risk). The plan named `cogs/creature_battle/` + `views/creature_battle/`.

## What shipped (PR #1230)

- **`services/creature_battle_service.py`** — the thin **read** boundary the plan §4
  called for: `load_pool` (collection-log → owned catalog creatures, skips superseded
  rows), `build_normalized_team` (pinned to `NORMALIZED_LEVEL`), `resolve_pvp`
  (loads both pools → `standard_team` → engine `resolve_battle`; returns `None` when a
  side has no usable team). **v1 is read-only** — no result persistence/xp/audit yet
  (that's the later slice), so no `db.transaction()` here.
- **`views/creature_battle/`** — `challenge.py` (`CreatureBattleChallengeView`, a
  **BaseView** locked to `author=opponent` so only the challenged player can act —
  keeps the arch `baseview_inheritance` ratchet green without an allowlist entry) +
  `render.py` (pure outcome embed: rosters with 💀 markers, KO highlights, winner).
- **`cogs/creature_battle_cog.py`** — `!cbattle @opponent` (rejects bot/self), mirrors
  the rps/deathmatch PvP-challenge pattern. **Auto-resolves on accept** (no move-pick;
  teams auto-build from each collection) — the skill levers are collection breadth +
  type matchups + the engine policies.
- Registered in `config.py`; `!cbattle` surfaced via `creature_cog`'s existing Help hook
  (PvP stays part of the one **Creatures** subsystem — no second subsystem).
- Tests: `test_creature_battle_service.py` (pool resolution, empty-side → None,
  level-normalization, determinism) + `test_creature_battle_render.py` (rosters, winner,
  faint markers, highlights).

## Second slice — extension-integrity CI guard (grooming the previous Q-0089 idea)

- **`tests/unit/invariants/test_extension_integrity.py`** — parametrized over every
  `config.INITIAL_EXTENSIONS` entry: imports it and asserts an awaitable `setup`.
  Closes the "boot caught it, CI didn't" gap the previous session flagged — directly
  protects the `config.py` extension I added this run. 49/49 pass.

## Verification

- `check_quality.py --full` (CI mirror: black/isort/ruff + `mypy disbot/` + full pytest)
  → **GREEN — 11236 passed, 47 skipped**.
- `check_architecture --mode strict` → exit 0 (no new violations; the challenge view is
  BaseView, so it never appears in `baseview_inheritance`).
- `check_consistency --mode strict` → exit 0. Ledger + `check_docs --strict` → pass.
- Not live-interaction-tested in Discord (no click harness in-env).

## Drift fixed on sight (Q-0166)

Regenerated the generated-artifact set the new cog/command touched (env-vars.md —
a `config.py` line-shift; dashboard.json / site.json / data.js — new command;
extension-taxonomy-crosswalk.md — new extension) and updated the hand-maintained
`help-command-surface-map.md`. While there I found **pre-existing** drift: the
non-hook-extension count still read "11" and omitted `role_grants_cog` (added last
session) — corrected to 13 and added both `role_grants_cog` + `creature_battle_cog`
with reasons.

## Context delta

- **Needed but not pointed to:** adding a cog/command/extension trips a *cluster* of
  generated-artifact + hand-maintained-doc checks (env-vars, dashboard/site, crosswalk,
  help-surface-map preamble counts, settings-customization-command-map, the
  `_UNREGISTERED_COG_ALLOWLIST` in `check_dashboard_data.py`). A one-line
  "adding a cog? regenerate + update these N files" checklist would save a re-discovery
  each time — candidate for the journal Quick-reference. (Captured as the session idea.)
- **Decision made alone:** flat `creature_battle_cog.py` (not the plan's
  `cogs/creature_battle/` package) and **no** new subsystem/help-hook for it — PvP stays
  one coherent "Creatures" help entry. Noted in the PR + current-state.
- **Known soft warning (left for reconciliation):** Recently-shipped grew to 21 vs
  ratchet 20 — the reconciliation routine (due at #1230) trims it; benign lag.

## 💡 Session idea (Q-0089)

**A `docs/` quick-reference checklist (or a `scripts/new_cog_drift_check.py` umbrella)
for "I added/removed a cog/command".** This run spent most of its CI-red rounds
re-discovering the same fixed set of artifacts/docs a new extension must touch
(env-vars.md, dashboard.json/site.json/data.js, extension-taxonomy-crosswalk.md,
help-surface-map preamble counts, settings-customization-command-map, the dashboard
unregistered-cog allowlist). One command that runs all the regens + prints the
hand-maintained spots to update would turn a multi-round trial-and-error into one pass.
Distinct from the extension-integrity guard I built (that asserts *importability*; this
is about *drift surface discoverability*). Dedup-checked: `check_generated_artifacts_fresh.py`
*detects* staleness but doesn't *regen* or list the hand-maintained docs.

## ⟲ Previous-session review (Q-0102)

**Reviewed: the reaction-roles PR 3+4+5 session (#1219/#1228).** *Did well:* a large,
clean owner-directed runtime bundle (modes + interactive panel + temp roles + analytics)
with thorough teardown/migration discipline and an honest one-PR packaging rationale.
*What it missed:* it added `cogs.role_grants_cog` to `config.py` but left the
`help-command-surface-map.md` non-hook-extension prose stale (still "11", omitting
role_grants_cog) — the regex-checked counts passed, so the *prose* count silently
rotted. I fixed it this run. **System improvement:** the help-surface-map preamble has
*two* count surfaces — regex-pinned ("X of Y loaded extensions") and prose ("the 11
extensions without the hook"); only the former is CI-enforced, so the latter drifts. The
prose enumeration should either be generated or pinned by a test that counts the listed
items against `_hook_defining_extension_count()`. Notably, the *previous* session's own
Q-0089 idea (the extension-integrity guard) — which I built this run — would not have
caught this (it checks importability, not doc prose); the real gap is the unpinned prose
count. Worth a small follow-up guard.

## 📤 Run report

- **Did:** shipped the creature PvP user-facing flow (cog + challenge/render views +
  read-only service + tests) on the shipped engine; built the previous-session
  extension-integrity CI guard; fixed pre-existing help-surface-map count drift ·
  **Outcome:** shipped, PR #1230, auto-merge armed by owner → merges on green.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions recorded:** none
- **⚑ Owner manual steps:** none — merge auto-deploys; no migration (v1 records
  nothing). Prod restart/verify stays the maintainer's (merge ≠ deploy).
- **⚑ Self-initiated:** the **extension-integrity guard** is grooming the *previous
  session's* logged Q-0089 idea (a backlog item, not unprompted invention); the PvP flow
  was the dispatched/named ▶ NEXT slice. No ungrounded self-initiated feature.
- **↪ Next:** creature-game next slices are owner-paced (PvP balance + result-recording/
  ranked + art, Q-0187). Ungated startables = (b) botsite React-SPA migration, or (d) a
  `needs-hermes-review` lane (consistency-linter AI-nav PR 1 · procedures→skills Batch 2).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session | 1 (PR #1230 — PvP flow + extension-integrity guard) |
| New runtime files | 4 (service · 2 views · cog) |
| New tests | 3 files (battle service · render · extension integrity / 49 params) |
| Migrations added | 0 (v1 PvP records nothing) |
| CI-red rounds (local) | 1 — the generated-artifact/doc-drift cluster (env-vars, dashboard/site, crosswalk, help-map, settings-map, unregistered-cog allowlist); all fixed; full mirror then green |
| Repo-rule trips | 0 (arch 0 errors; challenge view on BaseView; cogs under LOC ceiling) |
| New ideas contributed | 1 (new-cog drift-checklist/umbrella) |

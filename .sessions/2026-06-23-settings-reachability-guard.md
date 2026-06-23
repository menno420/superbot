# 2026-06-23 — Phase-0.5 settings-orphan reachability guard

> **Status:** `in-progress` — owner-directed: build the consolidation-fleet-plan's Phase-0.5 rail (the
> settings-orphan guard) so the next consolidation wave (settings/admin units U5–U9) has a machine
> reviewer for rubric item 6 (settings reachable). PR this session, auto-merge armed on green (Q-0127).
> Owner-directed → merge immediately (Q-0191).

> **Run type:** `manual · owner-directed`

## What I'm about to do

Build a **warn-first ratchet** guard, mirroring `check_command_reachability` (#1370), that flags
**settings-orphan** subsystems — those that *declare settings* but have **no discovery path** (no panel
/ `build_help_menu_view` hook), so an operator can't reach their config from the `!settings` hub.

- **Offline-safe by design.** The live `customization_catalogue` discovers panels by walking the running
  bot (`build_catalogue(None)` → 0/0 in CI), so this guard does it *statically*:
  - **"declares settings"** — static source (per the plan's verified correction: `all_schemas()` is also
    bot-walk-blind). Use `disbot/utils/settings_keys/<domain>.py` (+ map domains→subsystems carefully —
    they aren't always 1:1) and/or AST-scan the schema-registration call sites.
  - **"has a discovery path"** — reuse `scripts/check_command_reachability.py::_subsystem_discoverable`
    (already does the AST panel/hook detection).
- `scripts/check_settings_reachability.py` (report / `--mode strict`) + a ratchet invariant test +
  `architecture_rules/settings_reachability_exceptions.yml` (allowlist with reasons). Warn-only until the
  baseline is empty and proven quiet across sessions (Q-0105 disposable header).

(Close-out enders at session close.)

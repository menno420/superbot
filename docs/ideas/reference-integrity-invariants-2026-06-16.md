# Idea — a shared "declaration → real target" reference-integrity invariant

> **Status:** `ideas`. Not a plan, not approval. Source + binding contracts win.
> Captured 2026-06-16 (Q-0089 session ender) from the BUG-0014 fix (PR #949).

## The observation

BUG-0014 (the `!coglist` infinite loop) was, at its core, a **dangling reference**:
`COMMAND_SYNONYMS` declared a canonical (`coglist`) that pointed at a command which
**did not exist**. Nothing failed loudly — it silently mis-resolved and then looped.

This is a *class*, not a one-off. The repo has several "declaration tables" whose
entries name a target that must exist, and a dangling entry tends to fail silently:

- `COMMAND_SYNONYMS` canonical → a registered command (now guarded by
  `test_command_synonyms_resolve_to_real_commands.py`, PR #949).
- `SUBSYSTEMS[...].entry_points` → a registered command. **Explicitly NOT checked
  today** — `tests/unit/registry/test_entrypoints.py` says so in its own docstring:
  "A separate runtime check … would compare entry_points against bot.commands after
  cog load; that belongs in an integration test that requires a running bot."
- settings keys → consumers (already guarded — `test_settings_declared_vs_consumed_parity.py`, #917/#918).
- help-overlay / customization-catalogue entries → real surfaces.

## The idea

Extract the AST command-surface discovery written for the BUG-0014 guard (walk
`@commands.command/group` `name=`/`aliases=` + function-name fallback across
`disbot/`) into a **shared test helper** that exposes the authoritative
registered-command token set *without a live bot*. Then close the known gaps with
the same pattern — most concretely, the **`SUBSYSTEMS.entry_points` → real command**
check that `test_entrypoints.py` documents as missing. One source of truth for "what
commands exist," reused by every "this declaration must resolve" invariant.

## What to look into / cautions

- The AST discovery is a heuristic (it misses commands registered by exotic dynamic
  paths). Acceptable for a guard, but the shared helper should be honest about that
  and easy to broaden. (Q-0105 disposable-guard discipline.)
- Don't over-unify: settings parity already has its own (good) home; this is about
  the *command-target* references specifically.

## Disposition

Small/decided-lane follow-up. A future session can lift the helper out of
`test_command_synonyms_resolve_to_real_commands.py` and add the `entry_points` check.
Relates: `tests/unit/registry/test_entrypoints.py`, `disbot/utils/subsystem_registry.py`,
`disbot/utils/synonyms.py`.

# 2026-06-23 — Plan: hub child-rendering consistency + placement coherence

> **Status:** `complete` — planning-only PR (no runtime code). Owner-directed: after the treasury
> panel-link fix (#1344), the maintainer asked for "a plan … so I can do some research on it with a
> fresh session," and flagged multi-panel button duplication as a *separate* generalization concern.
> PR: this session → auto-merges on green CI (Q-0123).

## What shipped

A research/execution plan — `docs/planning/hub-child-rendering-and-placement-2026-06-23.md` — for a
future dedicated session, plus its `docs/planning/README.md` (S1) index row. No runtime code.

The plan captures the root cause behind #1344 and generalizes it:
- **Rendering inconsistency:** 2 of 6 hubs (Games, Community) auto-render their registered children
  as buttons; 4 (Economy, Moderation, Server-Management, Diagnostics) hardcode → a registered child
  can silently lack a panel button (treasury; `leaderboard` still latent).
- **The guard gap:** `test_discoverability.py` only checks a subsystem is *openable by typing*, not
  *clickable from a panel*.
- **Placement coherence:** `cross_link_children` double-places 4 subsystems (mining, leaderboard,
  counting, chain) — the maintainer's "registered in multiple panels … some belong in one place."

3-PR shape: (1) extract a shared hub-child-renderer + retrofit the hardcoded hubs; (2) a panel-link
CI guard; (3) an owner-in-the-loop placement audit. PR 3 is taste-gated → research session.

## Verification

- Docs-only change. `check_docs --strict` (new plan reachable from the README index) + `check_quality
  --check-only` ✓. No `disbot/` code touched → no mypy/arch surface.

## Enders

- **💡 Session idea (Q-0089):** the **panel-link discoverability guard** is itself the idea — folded
  into the plan as PR 2 (every `primary_child` must be rendered by its hub panel or explicitly
  exempted). It's the structural fix that makes the #1344 bug class impossible to reintroduce.
- **⟲ Previous-session review (Q-0102):** the #1344 fix (this chat's prior PR) correctly fixed the
  symptom and *flagged* the generalization rather than scope-creeping into it — good restraint. What
  it could improve: it diagnosed the Games-vs-Economy rendering asymmetry but didn't immediately
  capture it as a plan; the owner had to ask. Lesson now banked: when a one-line fix reveals a
  systemic asymmetry, capture the plan in the same session (this card does).
- **⚑ Self-initiated:** none — owner explicitly requested both the plan and that it be a separate
  session.

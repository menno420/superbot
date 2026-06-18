# 2026-06-18 — Consistency-linter Lane A1: window the `views/selectors/` API-ripple set

> **Status:** `in-progress`

## What I'm about to do

Execute the live ▶ Next action (band-#1050 queue, Lane A1 of the
[repo-consistency-linter plan](../docs/planning/repo-consistency-linter-plan-2026-06-17.md),
Q-0170): migrate the shared `views/selectors/` primitives — `role` / `channel` /
`multi` / `multi_role` / `subsystem` — off front-truncating `discord.ui.Select`
subclasses (`options[:25]`, the #1040 silent-drop class) onto the `#1050`
`attach_windowed_select` embedded helper. Convert each class to an `attach_*`
helper and update its ~8 consumers (channels delete/restrict/move/visibility/create
panels + roles xp/time/exemptions panels) as one focused PR. Root-fix the upstream
truncation source too (`core.resources.channel_service.build_select_options` →
unbounded mode for the windowed channel panels) so windowing actually reaches the
tail. This retires the 6 selector `select_option_truncation` findings (15 → ≈8).

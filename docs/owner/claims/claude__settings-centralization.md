- `claude/settings-centralization` · **Settings-reachability guard (consolidation audit — settings half)** —
  the static settings analog of the #1370 command-reachability guard. Asserts every subsystem declaring a
  `SubsystemSchema` is reachable from the `!settings` hub (non-internal + homed), and that every
  `.configure`/`.settings.*`-capability subsystem is either schema'd or explicitly allowlisted (the
  intentional domain-panel cases: counting/chain game-channel setup, channel visibility action). Makes the
  brief §3.4 "every cog's settings reachable from a hub" un-regressable. Scope: `scripts/`,
  `architecture_rules/settings_reachability_exceptions.yml`, `tests/unit/invariants/`, `docs/audits/`.
  2026-06-23 · PR (this session, auto-merge on green)

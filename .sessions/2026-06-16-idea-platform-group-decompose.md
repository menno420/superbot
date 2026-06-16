# Session — capture the diagnostic_cog platform-group decomposition idea

> **Status:** `complete`

## Why

Third contribution of this dispatch run (after faucet/sink #937 merged + myprofile PR A #938
pending) — the standing backlog-grooming ender (Q-0015). The faucet/sink slice pushed
`diagnostic_cog.py` to **799/800 LOC**; the cause + fix were captured only in two `.sessions/`
logs (which sessions don't read top-to-bottom), so the next `!platform` subcommand would hit the
wall cold. This moves that surfaced idea into its durable home.

## What shipped (docs only)

- `docs/ideas/diagnostic-cog-platform-group-extraction-2026-06-16.md` — extract the `!platform`
  group onto a `PlatformCommandsMixin` (`cogs/diagnostic/platform_group.py`) so the surface grows
  past the 800-LOC cog ceiling; identity stays on `DiagnosticCog`, weight moves to a helper module
  (the F-3 "surface = cog, weight = `cogs/<sub>/`" convention). Small/safe/decided-lane refactor.
- `docs/ideas/README.md` — index entry.

## Verification

`check_docs --strict` green (ideas 53). Docs-only; no runtime code.

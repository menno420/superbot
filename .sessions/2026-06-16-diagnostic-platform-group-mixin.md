# Session — extract the `!platform` command group onto a cog mixin

> **Status:** `in-progress`

## What I'm about to do

Execute idea #939 (`docs/ideas/diagnostic-cog-platform-group-extraction-2026-06-16.md`): move the
`!platform` command group off `DiagnosticCog` onto a `PlatformCommandsMixin`
(`cogs/diagnostic/platform_group.py`) so `diagnostic_cog.py` drops well under the 800-LOC cog
ceiling (it's at 799/800 — the next `!platform` subcommand is blocked cold). Pure refactor, no
behaviour change, fully reversible. Verified the discord.py 2.7.1 MRO command-collection works for
a non-Cog mixin base before starting.

Aiming for a second slice after this lands (a contained plan-first or backlog-groom pick).

## Done

- (in progress)

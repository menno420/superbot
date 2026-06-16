# Idea — extract the `!platform` command group into a cog mixin

> **Status:** `ideas` — captured 2026-06-16. Surfaced (twice) by the dispatch run that shipped
> the faucet/sink diagnostic (#937) and myprofile PR A (#938). Routing: **S4 docs / S1 platform —
> diagnostic slice**. Near-term, not speculative: `diagnostic_cog.py` is at **799/800 LOC**, so
> the *next* `!platform` subcommand is blocked until this is done.

## The friction (a real, dated blocker)

`disbot/cogs/diagnostic_cog.py` is the Discord-facing home of the whole `!platform` admin surface
— ~30 thin `@platform_grp.command` wrappers (`status`, `media`, `economy`, `health`, `findings`,
`flags`, …), each delegating to a builder in `cogs/diagnostic/_platform_embeds.py`. The
800-LOC cog ceiling (`tests/unit/invariants/test_cog_size.py`, hard fail at 800) is the F-3
decompose signal.

The *embed builders* already moved out (`_platform_embeds.py`) — that was the first decompose.
But the **command registrations** stayed in the cog, and adding one more (the faucet/sink
`!platform economy` in #937) pushed the file to **799/800**. #937 only landed by *shaving
docstrings* to claw back lines — a symptom, not a fix. The next subcommand has no room at all.

## The fix

Move the `platform_*` command group off `DiagnosticCog` and onto a **mixin class** the cog
inherits — e.g. `cogs/diagnostic/platform_group.py` defining `class PlatformCommandsMixin:` that
holds `platform_grp` + every `@platform_grp.command`, with `DiagnosticCog(PlatformCommandsMixin,
commands.Cog)`. discord.py resolves group commands across the MRO, so the surface is unchanged.

Why a mixin (not a second cog): the `!platform` group must stay registered under **one** cog
(`DiagnosticCog` → the `diagnostic` subsystem) so the command-surface ledger and help routing
don't see it move subsystems. A mixin keeps the identity on `DiagnosticCog` while moving the LOC
into a helper module (which is *not* subject to the 800-LOC cog ceiling — only top-level
`*_cog.py` files are). This is the same "Discord surface = the cog; the weight lives in
`cogs/<sub>/`" convention F-3 already established for the builders.

## Scope / shape (one PR, low risk)

- New `disbot/cogs/diagnostic/platform_group.py` with `PlatformCommandsMixin` holding the
  `platform_grp` group + all `platform_*` subcommands (moved verbatim).
- `DiagnosticCog` inherits the mixin; the slash front door + the non-`platform` commands stay put.
- Verify: `test_cog_size` green (cog drops well under 800), `test_command_surface_ledger`
  `EXPECTED_SLASH_SURFACE` unchanged (the `platform` group still resolves), `!platform <sub>` all
  still register, `check_quality --full` + `check_architecture` green.
- Pure refactor — no behavior change, fully reversible.

## Why it's worth doing before it's urgent

It's currently only recorded in two `.sessions/` logs, which sessions don't read top-to-bottom —
so a future agent adding a `!platform` subcommand will hit the 799/800 wall *cold* and burn time
re-discovering the cause + re-shaving docstrings. Doing the extraction proactively unblocks the
whole `!platform` lane (more diagnostics are queued: the faucet/sink follow-ups in the plan, an
inflation health-finding, etc.) and removes a recurring time-tax. Small, contained, decided-lane —
a good "execute now" grooming pick for a session with capacity.

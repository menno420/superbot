# Idea — one shared command-surface AST extractor for the three scripts that each re-implement it

> **Status:** `ideas` — captured 2026-07-10 (overnight session, PR #1918, Q-0089).
> **Subsystem:** none (cross-cutting `scripts/` build hygiene).

## The observation (felt while building #1918)

Three stdlib-AST tools now independently parse the same `disbot/cogs/**` decorator surface, each
with *different* edge coverage:

- `scripts/scan_commands.py` — dashboard data generator; handles `hybrid_command`/`hybrid_group`
  and subcommand parent-type inheritance.
- `scripts/check_command_collisions.py` (#1918) — collision guard; handles alias tokens,
  `app_commands.Group(...)` assignments, dynamic-`name=` skip semantics, prefix/slash namespace
  split (hybrid support added only because building it next to `scan_commands.py` exposed the gap).
- `scripts/check_command_reachability.py` — reachability guard with its own decorator walk.

Every edge fix (a new decorator form, a naming rule change in discord.py, the tuple-vs-endswith
`app_commands.command` misfile trap) must now land three times or the tools silently disagree —
the same class of drift the CLAUDE.md CodeGraph rules exist to warn about, but between our own
tools.

## The idea

Factor one `scripts/lib/command_surface_ast.py` (pure stdlib, no `disbot` imports) exposing the
declaration stream — `(token, namespace, kind, cog, file, line)` — and re-base the three scripts
on it as thin consumers. This is a **concrete first instance** of
[`warn-first-checker-authoring-kit-2026-07-06.md`](./warn-first-checker-authoring-kit-2026-07-06.md)
(the shared-AST-lib facet), scoped down to the command surface where the duplication is already
3-way and measurable. The runtime `command_surface_ledger` stays the boot-time source of truth;
this only unifies the *static* mirrors.

## Why it's worth having

The collision checker's hybrid-command blind spot was caught in-session only because the sibling
extractor happened to be opened for a dedup check — the next divergence won't be that lucky. One
extraction lib makes the three tools agree by construction and makes the fourth command-surface
tool (there will be one) a ~50-line consumer.

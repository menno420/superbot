# Idea — `check_command_collisions.py`: static guard against duplicate command names

> **Status:** `historical` — implemented (PR #1918, 2026-07-10) · raised 2026-06-29 (twenty-ninth Q-0107 reconciliation pass, band-#1560).
> Lane: S3 (agent-workflow / self-improving guards). Gate: `ready` (offline, stdlib, CI-wired).
>
> **Shipped:** `scripts/check_command_collisions.py` + `tests/unit/scripts/test_check_command_collisions.py`
> (PR #1918). Live tree at implementation: 403 token claims (368 prefix incl. aliases, 35 slash), 0
> collisions. The suite includes a standing live-tree regression test
> (`test_live_tree_has_zero_collisions`) so every full pytest run already exercises the real cog tree.
> **Follow-up (deliberately deferred — workflow edits were out of the implementing session's overnight
> scope):** wire the script into `.github/workflows/code-quality.yml` as its own step so a collision
> reds the PR check directly, not just the pytest job. Until then the regression test is the CI
> enforcement path and the script is the local pre-push tool.

## The problem this prevents (a real prod outage, this band)

PR #1541 added a `!give`/`!pay` economy command. It **collided** with mining's admin `give` — a command
that had existed **since the initial commit (2025-08-10), never PR'd, dormant**. On the next boot the
`discord.ext.commands` registry raised `CommandRegistrationError: The command give is already an existing
command or alias`, `mining_cog` failed to load, its entry points (`mine`/`minemenu`) vanished, and the
**STRICT identity-contract aborted startup** → the bot **crash-looped offline** until #1544 (Q-0211)
retired `give` surface-wide and added a *runtime* cross-cog duplicate-command boot guard.

The collision was **100% statically detectable** — two `@commands.command(name="give")` (or alias)
registrations in the loaded cog set — yet it reached production and cost a live outage. The runtime guard
added in #1544 catches it *at boot* (after merge, after deploy); a CI checker catches it *before merge*.

## The proposal

A `scripts/check_command_collisions.py` (offline, stdlib AST, CI-wired in `code-quality.yml`):

- Walk `disbot/cogs/**` for `@commands.command(...)`, `@commands.group(...)`,
  `@app_commands.command(...)`, and their `aliases=[...]`, collecting `(name, cog, kind)`.
- Build the global top-level token set; **fail** when any name or alias is claimed by two different cogs.
- Print the colliding token + both declaration sites (file:line) so the fix is one grep away.

Read-only / stdlib / disposable per Q-0105 (provenance + "delete if it proves unreliable" header). It is
the Q-0194 friction→guard escalation at the **cheapest tier (CI checker)** — converting a class of prod
incident into a red PR. Pairs with #1544's runtime guard (defence in depth: CI catches it pre-merge, the
boot guard remains the backstop for anything CI can't see, e.g. dynamically-registered commands).

## Why it's worth having

One occurrence already caused a production outage; the namespace only grows (333 top-level tokens today),
so the collision probability rises with every new command. The check is cheap, fully offline, and has an
unambiguous ground truth (the same registry rule the bot enforces at boot).

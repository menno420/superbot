# Session — 2026-06-24 · capture owner idea: bot-migration assistant

> **Status:** `in-progress` — born-red. About to capture an owner-raised idea (the bot recognizes
> other bots in a server, maps what they offer, suggests how to replicate it with SuperBot, then
> retires the now-redundant bots) as a `docs/ideas/` doc + README index entry. Docs-only.

## What I'm about to do

The maintainer asked, in chat: *"can the bot recognize other bots, find out which things they offer,
and suggest steps to replicate their functions in the server, as well as delete the old bots once
setup is complete?"* He chose **capture as an idea doc** (not plan/build yet).

Scope: write `docs/ideas/bot-migration-assistant-2026-06-24.md` grounded in (a) the actual SuperBot
seams that make it feasible (setup advisor → draft → Final Review · `guild_snapshot` · subsystem
registry · `moderation_service.kick`) and (b) the one hard Discord constraint (no API to introspect
another bot's commands). Cross-link the existing V-14 feature-mining lineage. Add the README index
entry. No runtime code.

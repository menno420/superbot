# Session — 2026-06-24 · build the essentials spine (PR 1)

> **Status:** `in-progress` — born-red. Owner greenlit (in-session) building the setup-wizard essentials
> spine with **per-step direct-apply** (Q-A answered: "save each step instantly"). Runtime build.

## What I'm about to do

Build the new linear **Essential Setup** flow per the plan (`setup-wizard-restructure-plan-2026-06-24.md`
§5): a stepped, plain-language, button/dropdown-only flow where **each step applies its config immediately**
(direct lane) and the bot **auto-creates** any channel/role it needs. Steps: server type → greet members →
moderators → block spam → log channel → reward activity → help desk → done. Reuse existing audited config
services (welcome/moderation/automod/logging/xp+role/ticket); no new mutation primitives. Old wizard stays
(retired later in PR 3). Full test suite run before push (lesson from the guild sweep).

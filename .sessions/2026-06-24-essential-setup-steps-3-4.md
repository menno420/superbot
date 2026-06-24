# Session — 2026-06-24 · Essential Setup steps 3-4 (block spam · help desk)

> **Status:** `in-progress` — born-red. Extending the merged Essential Setup spine (#1425) with two more
> direct-apply steps. **No new cog / command / artifact** — pure additions to `EssentialFlow._steps`, so
> none of the #1425 registration fan-out recurs. ⚑ Continuation of owner-greenlit spine build.

## What I'm about to do

Add **Block spam and bad links** (automod: enable + spam/invites/caps/mentions toggles, defaults on, via
`SettingsMutationPipeline`) and **Set up a help desk** (tickets: staff-role + optional log channel via
`ticket_mutation.update_config`) to the linear flow. Plain-language, each applies instantly. Tests mirror
the existing `test_essential_setup.py`. Verify: jargon guard clean + essential-setup tests + the surface
test set (cheap — no new cog) before push.

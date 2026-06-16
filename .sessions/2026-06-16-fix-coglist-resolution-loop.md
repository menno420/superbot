# Session — fix BUG-0014: `!coglist` infinite "assumed from" command-resolution loop

> **Status:** `in-progress`

## What I'm about to do

Owner uploaded a Discord screen recording: typing `!coglist` (or `!cogs`) makes SuperBot spam
"↩️ Ran `!coglist` — assumed from `!coglist`." **forever, until the bot is restarted.** Root cause
(confirmed): `utils/synonyms.py` declares `"coglist": ["listcogs", "cogslist"]`, but **no `coglist`
command is registered** (audited: it's the only orphaned canonical of 32). The typo-resolver
auto-corrects the fuzzy token to the phantom `coglist`; `on_command_error` re-dispatches `!coglist`
via `process_commands`; it `CommandNotFound`s again → re-resolves to itself → infinite loop.

Fix (durable, root-cause): (1) **loop-breaker in `on_command_error`** — only re-dispatch an AUTO
correction when it's a *registered* command *different* from the raw token (a phantom/identity
correction can only re-loop); (2) **remove the orphaned `coglist` synonym**; (3) **CI invariant** —
every `COMMAND_SYNONYMS` canonical must be a real command name/alias (so an orphan can't ship again).

(Filled in as the deliberate final step — born-red per Q-0133.)

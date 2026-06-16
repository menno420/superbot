# Session — runtime lock: release early on shutdown (fix ~85s deploy downtime)

> **Status:** `in-progress`

## What I'm about to do

A production Railway log dump showed an intermittent **~85s of bot downtime on deploy**: when the
platform force-kills the old container ~10s after SIGTERM (before the bot's graceful `bot.close()`
budget of 20s has elapsed), the singleton runtime-lock is never released, so the new replica waits
the full ~90s stale-TTL before it can start. Owner decision (this session): **release the lock early**
— drop it the moment shutdown begins, before the slow `bot.close()` — so a mid-drain SIGKILL can't
leave the lock wedged. Robust to any kill timing; downtime ~85s → ~6s.

(Filled in as the deliberate final step — born-red per Q-0133.)

# Railway deploy-failure alerts into Discord (2026-07-02)

> **Status:** `ideas` — session idea (Q-0089, from the Railway automation-grant session). Not
> approved for implementation.

## The idea

Point a **Railway project webhook** at a Discord webhook so deploy events — above all
**FAILED/CRASHED** deploys of `worker` — land in the owner's Discord as they happen. Railway
supports Discord-type webhook destinations natively; a `DISCORD_WEBHOOK_URL` already exists in the
worker's Railway variables (so a destination channel already exists), and the Q-0213 automation
grant covers creating the webhook via the API (`webhookCreate`-family mutation; additive,
reversible). Optionally filter to failure states only, so it alerts rather than chatters.

## Why it's worth having

Merge=deploy (Q-0193) means a broken deploy is currently discovered only if someone looks at the
Railway dashboard or the bot goes quiet — the owner gets no push signal. One webhook closes that
gap platform-side (no bot code, works even when the bot itself is the thing that failed to boot),
and it is the first concrete consumer of the §4 "alerts" row in the Railway setup plan.

## Route

S5 (operations) · pairs with
[`../planning/railway-setup-plan-2026-07-02.md`](../planning/railway-setup-plan-2026-07-02.md) §4
and the `railway-config-drift-checker` idea (the webhook's existence becomes an expected-state
line). One session, agent-executable; confirm the destination channel with the owner first
(posting surface = owner taste).

> **⚡ EXECUTED 2026-07-02 (same day):** it turned out the owner already had exactly this — a
> Railway notification rule (all `Deployment.*`/`VolumeAlert.*`/`Monitor.*` events) pointing at a
> Discord webhook whose channel he had accidentally deleted. Restored under Q-0213:
> `#railway-alerts` + webhook recreated in the test guild, the existing rule updated in place,
> delivery verified. Remaining scope of this idea: **failure-only filtering** (the rule currently
> fires on every event incl. successes — tune `eventTypes` if it proves noisy) and the eventual
> move to the HQ guild per
> [`central-admin-and-logging-guilds-2026-07-02.md`](./central-admin-and-logging-guilds-2026-07-02.md).

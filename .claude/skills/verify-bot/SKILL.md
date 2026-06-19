# /verify-bot

Boot the test bot in the sandbox and smoke-test it, so a live check backs up your change — the
"booting the test bot is ALWAYS allowed, possible, and safe" runbook from `.session-journal.md`,
turned into one command.

## What this does

Walks the Environment Runbook boot path (`.session-journal.md` § "Environment Runbook — booting &
operating the bot in the sandbox"): start Postgres if needed, boot `disbot/bot1.py`, watch the log
for a clean startup, and tick the boot-path items from `docs/smoke-test-checklist.md`. **Booting is
never gated** — `DISCORD_BOT_TOKEN_PRODUCTION` is a *separate, dedicated test bot* ("Galaxy Bot#6724",
alone with the maintainer in a private server), not the real production token, and `DATABASE_URL`
points at local Postgres, so a boot here cannot touch the live bot.

This is a thin wrapper around the runbook; it adds no new policy. The full detail (degraded
feature-flags, gotchas, the prod note) stays in `.session-journal.md`.

## Invocation

```
/verify-bot
```

No arguments. Run it after a change that touches startup, task ownership, the consistency report, or
the readiness snapshot — or any time a live check adds confidence.

## Instructions for Claude

### Step 1 — ensure Postgres is up

Local Postgres is **not** running by default, but the cluster is usually already initialized
(Debian-packaged: data dir `/var/lib/postgresql/16/main`, config under `/etc/postgresql/16/main/`).
Fast path — just **start** it (don't `initdb`, don't `pg_ctl -D`):

```bash
pg_ctlcluster 16 main start
```

Ensure the role + db exist for `DATABASE_URL` (`superbot:superbot@localhost:5432/superbot`), skipping
whichever already exists:

```bash
su postgres -c "psql -c \"CREATE ROLE superbot LOGIN PASSWORD 'superbot' CREATEDB\""
su postgres -c "createdb -O superbot superbot"
```

The schema bootstraps itself on boot (`pool.init()` -> `ensure_migrations_table` -> `create_tables`
-> `run_migrations`); migrations auto-discover by `NNN_<snake>.sql` — no manual migration step.

### Step 2 — boot the bot

Entry point is `python3.10 disbot/bot1.py`, run **from the repo root** (so `import config` resolves).
Launch in the background and tee the log:

```bash
nohup python3.10 disbot/bot1.py > /tmp/testbot.log 2>&1 &
```

Prefer `run_in_background` so the bot persists across turns and only notifies you if it exits. Put a
Monitor on `/tmp/testbot.log` filtered to `ERROR/CRITICAL/Traceback`.

### Step 3 — smoke-check startup

Watch `/tmp/testbot.log` (and `bot.log` in the repo root) for the boot-path items from
`docs/smoke-test-checklist.md`:

- "Starting bot..." followed by the discord.py ready event — **boot completes with no unhandled
  exception**.
- "Runtime lock acquired ..." — the Postgres-backed runtime lock (a loser replica exits code 0).
- The heartbeat task appears in the managed task supervisor.

Only **one** instance may be active (a runtime lock with heartbeat). On restart, **kill the old
instance first** — `pkill -f "disbot/bot1.py"` self-kills your shell, so filter by `comm`:

```bash
for pid in $(pgrep -f "disbot/bot1"); do [ "$(cat /proc/$pid/comm)" = python3.10 ] && kill "$pid"; done
```

### Step 4 — expect *degraded*, not *broken*

Only Postgres + the Discord test token are provisioned (Full network access). AI / YouTube / Paragon /
webhook keys are absent, so those paths run **degraded** — `AI_ENABLED` off,
`AUTOMATION_SCHEDULER_ENABLED=false` (manual `!assignroles` / "Run Now" still works), etc. A degraded
path failing is expected here; an *unhandled exception* on the boot path is a real failure.

### Step 5 — report

Print: booted clean (Y/N) · runtime lock acquired (Y/N) · heartbeat spawned (Y/N) · any
`ERROR/CRITICAL/Traceback` lines · which degraded paths you saw. Then kill the test instance (Step 3
recipe) unless you want it live for further checks.

### Notes

- **Never touch production / Railway / the prod DB** from here. The runbook's prod section is for
  diagnosis only.
- The quality gates are separate: `python3.10 scripts/check_quality.py --full` (the CI mirror) and
  `python3.10 scripts/check_architecture.py --mode strict`. `/verify-bot` is the *live* check that
  complements them — green tests + a clean boot is the strongest signal.

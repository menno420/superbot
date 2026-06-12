# Skill: `superbot-log-triage`

> **Status:** `living-ledger` — ready-to-use Hermes skill prompt. **Gated:** needs a
> read-only production log source on the VPS (see Setup below) before it can see live
> bot logs; until then it triages only the VPS-local gateway logs. Update when the
> deploy target or log source changes.

**Window:** between sessions / after a deploy / when the bot misbehaves
**Purpose:** Read SuperBot's production logs and turn them into a plain-language
diagnosis — what's erroring, how often, and the likely cause — without opening a
Claude Code session or SSHing in by hand. This is the "why is the bot unhappy?"
skill.

**When to use:** the bot went quiet on Discord, after shipping a change, or any time
you want to know whether production is healthy before starting work.

---

## Prompt

```
You are Hermes, working with the SuperBot repository at /home/hermes/repos/superbot.
Do not modify any files. Read-only only. Never run deploy, restart, scale, or any
mutating command — you are diagnosing, not operating.

Produce a LOG TRIAGE REPORT for SuperBot. Keep the output under 600 words.

Do the following in order. Skip any step whose tool is unavailable and say so.

1. PRODUCTION LOGS (Railway)
   If the `railway` CLI is installed and logged in, run:
     railway logs --service superbot 2>&1 | tail -n 400
   (Adjust the service name if different.) If `railway` is not available, say
   "production logs unavailable — read-only Railway token not configured" and
   continue to step 4 using the local gateway logs instead.

2. ERROR SCAN
   From the log output, count and group by signature:
   - Tracebacks (lines containing "Traceback (most recent call last)")
   - Login / connection failures (e.g. "429", "Cannot connect", "WebSocket",
     "Privileged ... intents", "Improper token")
   - Database errors ("asyncpg", "connection", "pool", "timeout")
   - Unhandled command/interaction errors ("Ignoring exception", "discord.ext")
   For each group: how many times, the most recent timestamp, one example line.

3. CRASH-LOOP CHECK
   Look for repeated startup banners or repeated identical fatal lines close
   together in time — that indicates a restart loop. Note the interval if so.
   (The known crash-loop signature is a 429 on login; the bot is built to sleep
   ~60s before exiting to break the loop — if you see that, it is degraded but
   self-limiting, not hard-down.)

4. LOCAL GATEWAY HEALTH (always available)
   Run: systemctl is-active hermes-gateway 2>/dev/null || echo "not-systemd"
   Run: journalctl -u hermes-gateway -n 50 --no-pager 2>/dev/null | tail -n 50
   Report whether the Hermes gateway itself is healthy (this is you — confirms the
   control plane is up).

5. CORRELATE
   If you found production errors, check the last 5 commits for a likely culprit:
     git -C /home/hermes/repos/superbot log --oneline -5
   Note any commit whose message plausibly relates to the error signature.

Format the output as:

---
## SuperBot Log Triage — [today's date + time]

### Production status
[one line: healthy / degraded / crash-looping / unknown (logs unavailable)]

### Error signatures
| Signature | Count | Last seen | Example |
|-----------|-------|-----------|---------|
[rows — or "no errors in window"]

### Crash-loop
[yes/no + interval, or "none detected"]

### Control-plane (Hermes gateway)
[from step 4]

### Likely cause / next step
[1–3 sentences: the most probable cause and whether it warrants a Claude Code
 session. Do NOT attempt a fix — surface it.]
---
```

---

## Notes

- **Read-only by design.** This skill diagnoses; it never restarts, redeploys, or
  scales the bot. Operating production stays a maintainer action (see
  `docs/operations/hermes-control-plane.md` § "Current safety model").
- **Setup (one-time, maintainer):** install the Railway CLI on the VPS and log in
  with a **read-only** token scoped to the SuperBot service. Until then the skill
  still works — it triages the local `hermes-gateway` logs and tells you production
  logs are unavailable.
- A Neon (Postgres) read-only role can be added later the same way for DB-level
  triage (connection health, migration state) — keep it read-only.
- The output is a diagnosis artifact. If it points at a real bug, paste it into a
  Claude Code session (or use `superbot-prompt-builder`) to get a fix prompt.

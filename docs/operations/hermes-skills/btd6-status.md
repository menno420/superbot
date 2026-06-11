# Skill: `superbot-btd6-status`

> **Status:** `living-ledger` — ready-to-use Hermes skill prompt. Update when the BTD6 data pipeline or probe script changes.

**Window:** after live testing  
**Purpose:** Snapshot of the BTD6 data pipeline — what the bot knows, what it doesn't,
and what's broken. Useful after a live testing session where you hit wrong answers.

**When to use:** after testing BTD6 commands on Discord, or when you want to know
what grounding coverage exists before opening a bug-fix session.

---

## Prompt

```
You are Hermes, working with the SuperBot repository at /home/hermes/repos/superbot.
Do not modify any files. Read-only only.

Produce a BTD6 STATUS REPORT. Keep the output under 500 words.

Do the following in order:

1. Read: /home/hermes/repos/superbot/docs/btd6/btd6-gamedata-decode-status.md
   Extract:
   - Overall decode progress (what percentage or count is grounded)
   - Which data areas are complete (✅ or equivalent)
   - Which data areas are partial or missing (⚠️ / ❌ or equivalent)
   - Any open items or known gaps listed in the doc

2. Read: /home/hermes/repos/superbot/docs/health/bug-book.md
   Find any open bugs (not marked FIXED) that mention BTD6, round cash, grounding,
   resolver, or BTD6-related commands. List each: BUG-NNNN — short description — status.

3. Run: cd /home/hermes/repos/superbot && git log --oneline --all -- disbot/data/btd6/ | head -5
   Show the 5 most recent commits that touched the BTD6 data files.
   This tells you how recently the data was updated.

4. Run: cd /home/hermes/repos/superbot && git log --oneline --all -- disbot/services/btd6_*.py | head -5
   Show the 5 most recent commits that touched BTD6 service files.

5. Check if the probe script exists:
   ls /home/hermes/repos/superbot/scripts/btd6_probe.py
   If it exists, run: cd /home/hermes/repos/superbot && python3 scripts/btd6_probe.py --help
   (read-only — just check what options exist, do not run a full probe)

Format the output as:

---
## BTD6 Status — [today's date]

### Decode coverage
[from step 1 — what's grounded vs. missing, compact table or list]

### Open BTD6 bugs
[from step 2 — or "none open"]

### Recent data changes
[from steps 3+4 — last 5 commits for data files, last 5 for services]

### Probe tool
[from step 5 — available options, or "probe script not found"]

### Assessment
[2–3 sentences: is the BTD6 pipeline in good shape, what's the biggest gap,
 what would help most in the next session?]
---
```

---

## Notes

- The BTD6 data files live in `disbot/data/btd6/` and are updated by `scripts/parse_gamedata.py`.
- The grounding services are in `disbot/services/btd6_*_service.py`.
- The decode status doc is the canonical record of what data is parsed and what is not.
  Source code and the doc should agree — if they don't, the source wins.
- This skill does not run actual bot commands or test queries — it reads the static record.
  For live query testing, do that in Discord and report the result to a Claude Code session.

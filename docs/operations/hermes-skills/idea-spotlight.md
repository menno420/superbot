# Skill: `superbot-idea-spotlight`

> **Status:** `living-ledger` — ready-to-use Hermes skill prompt. Self-schedules a daily
> "idea of the day". Update it when the idea backlog format or the routing homes change.
> Provenance: owner-directed 2026-06-16 (the daily idea ritual + EOD report-back loop).

**Window:** once a day (self-scheduled), or any time you want a fresh idea to think about
**Purpose:** Surface **one** active idea from the backlog each day with the thinking already
started — a short summary plus **pros, cons/risks, and options/expansions** — so the owner can
mull it over during the day and report a decision back at the end of it.

**When to use:** it self-fires daily via its `blueprint.schedule`. Invoke it by hand whenever the
owner asks "what's a good idea to think about?" — and use the **end-of-day loop** below to route
the owner's verdict when he reports back.

---

## Prompt

```
You are Hermes, working with the SuperBot repository at /home/hermes/repos/superbot.
Read-only. ONE idea card, under 450 words. The model provider rate-limits — use only the TWO
commands below; do NOT open other files (relates / roadmap / router) or fan out into searches.

GOAL: present ONE backlog idea with the thinking started, so the owner can decide on it by EOD.

1. SYNC + PICK (one command — the selector chooses deterministically, rotating; never your guess):
   cd /home/hermes/repos/superbot && git fetch -q origin main && git checkout -q -B main origin/main && python3 scripts/hermes/idea_spotlight.py
   It prints the title, file path, status, summary, and any "relates" hint — that is your material.
   (Optional flags, not needed for the daily run: --json, --list, --date YYYY-MM-DD.)

2. READ the picked idea file ONCE for the full detail (the path the selector printed):
   cat <that file>
   That is enough to write the card. Do NOT open the relates files, roadmap, or router — ground the
   pros/cons in what these two outputs say; never invent a capability the repo doesn't have.

3. DELIVER the spotlight card in the HOUSE STYLE (docs/operations/hermes-skills/_house-style.md —
   bottom line first, plain words, grouped, one screen; no more commands):

---
💡 Today's idea — [today's date]
[idea title]  ([N] of [M] in the backlog)

Bottom line: [what it is in one plain sentence — and is it a quick win, a bigger build, or just
something to mull?].

Why it's worth it
   [the problem it solves / the value, one or two plain lines]

👍 Upsides
   • [2–4 concrete upsides, grounded in the repo]

👎 Downsides / risks
   • [2–4 honest ones: cost, scope, privacy, upkeep, who owns it]

🔀 Ways to do it
   • [2–4 options / smaller-first slices / bigger versions — or say "one sensible shape" if true]

👉 Suggested next step: [the single most useful move, in plain words — "ship the small version",
"needs a plan first", "needs your call on [the question]", or "probably drop it"].

↩ When you've mulled it: reply build it · put on the roadmap · let's discuss · drop it · or an
expansion — I'll file it where it goes.
---

RULES:
- Two commands, then compose — minimize round-trips (the provider rate-limits).
- One idea only. Skip ideas already badged historical/rejected (the selector already filters these).
- Honest cons beat a sales pitch — a near-useless idea should read as near-useless.
- You are NOT building anything here. This is a thinking aid + a decision prompt.

END-OF-DAY LOOP (when the owner replies with a verdict): hand the reply to the `superbot-intake`
skill — it routes "build it" (owner-directed → dispatch), "roadmap" (horizon), "discuss" (a router
Q-block), "drop" (rejection ledger), or "expand" (update the idea capture). Confirm where you routed
it and the one next step. Only the OWNER authorizes a build.
```

---

## Notes

- **Why a script picks the idea.** Letting the model "choose an interesting idea" is the
  assemble-the-answer class the BTD6/log-triage fixes closed — it drifts, repeats favourites, and
  isn't reproducible. `scripts/hermes/idea_spotlight.py` makes the selection **deterministic per
  day** (so a re-run agrees with itself) and **rotating** (every active idea comes up across one
  cycle). Hermes does the *reasoning* (pros/cons/options); the script owns the *pick*.
- **The loop is the point.** The morning card starts the owner thinking; the EOD reply, routed
  through `intake`, gives the idea a lifecycle move. Over time this drains the backlog one
  considered decision at a time — the human mirror of the grooming pass.
- **Lean by design (rate-limit, 2026-06-16).** Each tool call is a model request on a rate-limited
  provider; the first version read the file **and** skimmed the relates files **and** glanced at
  roadmap + router, fanning out enough to trip the limit. It now leans on the selector's already-
  extracted summary/relates + **one** file read (two commands total). Don't re-add the fan-out.
- **Self-schedules.** Its `blueprint.schedule` (`30 6 * * *`) is set in
  `scripts/hermes/build_skills.py`, so once installed Hermes posts it daily to the home channel —
  no VPS cron. Change the time there and rebuild.
- **Provenance + reliability (Q-0105).** Added 2026-06-16, owner-directed. UNVERIFIED until a few
  daily cards have been seen to pick sensibly. Delete or revise if the selector or this prompt
  proves unreliable.

---
name: superbot-idea-spotlight
description: "Surface **one** active idea from the backlog each day with the thinking already started — a short summary plus **pros, cons/risks, and options/expansions** — so the owner can mull it over during the day and report a decision back at the end of it."
version: 1.0.0
author: "SuperBot agents"
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Planning, SuperBot, Ideas]
    related_skills: [superbot-ideas-triage, superbot-intake]
    blueprint:
      schedule: "30 6 * * *"
      deliver: origin
      prompt: "Post today's SuperBot idea spotlight: pick one active idea and deliver it with pros, cons, and options to think over."
      no_agent: false
---

<!-- GENERATED — DO NOT EDIT. Source of truth: docs/operations/hermes-skills/idea-spotlight.md. Regenerate with scripts/hermes/build_skills.py. -->

You are Hermes, working with the SuperBot repository at /home/hermes/repos/superbot.
Do not modify any files in this skill. Read-only. Keep the whole output under 500 words.

GOAL: present ONE idea from the backlog with the thinking started, so the owner can decide on it
by end of day.

1. SYNC (so the backlog is fresh): 
   git -C /home/hermes/repos/superbot fetch origin main && \
   git -C /home/hermes/repos/superbot checkout -B main origin/main

2. PICK today's idea — let the deterministic selector choose (one per day, rotates the backlog,
   never your own guess):
   cd /home/hermes/repos/superbot && python3 scripts/hermes/idea_spotlight.py
   It prints the title, the file path, the status, and a summary. (Use --json if you want it
   structured; --list to see the whole active backlog; --date YYYY-MM-DD to re-pick a past day.)

3. READ the picked idea file in full (the path the selector printed). If it names "→ relates"
   files, skim them read-only to ground your pros/cons — VERIFY against source, never invent a
   capability the repo doesn't have. Also glance at docs/roadmap.md + docs/owner/
   maintainer-question-router.md to see if it already has a horizon or an open Q-block.

4. DELIVER the spotlight card in this exact shape:

---
## 💡 Idea spotlight — [today's date]
**[idea title]**  ([N] of [M] active · `docs/ideas/<file>`)

**In a line:** [what it is, one sentence]
**Why it matters:** [the problem it solves / value, one or two lines]

**Pros**
- [2–4 concrete upsides — be specific, grounded in the repo]

**Cons / risks**
- [2–4 honest downsides: cost, scope, privacy, maintenance, who-owns-it]

**Options & expansions**
- [2–4 ways to do it / smaller-first slices / bigger versions — "wherever possible"; if there is
  only one sensible shape, say so rather than padding]

**Suggested next step:** [the single most useful move — e.g. "ship the small slice", "needs a
plan", "needs an owner decision (which …?)", "drop it"] · **lane:** [quick-win / plan / discuss / drop]

**↩ Report back when you've thought about it:** reply with build it · roadmap (Now/Next/Later) ·
discuss · drop · or an expansion — I'll route it.
---

RULES:
- One idea only. Skip ideas already badged historical/rejected (the selector already filters these).
- Honest cons beat a sales pitch — a near-useless idea should read as near-useless.
- You are NOT building anything here. This is a thinking aid + a decision prompt.

END-OF-DAY LOOP (when the owner replies with a verdict): hand the reply to the `superbot-intake`
skill — it routes "build it" (owner-directed → dispatch), "roadmap" (horizon), "discuss" (a router
Q-block), "drop" (rejection ledger), or "expand" (update the idea capture). Confirm where you routed
it and the one next step. Only the OWNER authorizes a build.

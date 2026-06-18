# Skill: `superbot-open-questions`

> **Status:** `living-ledger` — ready-to-use Hermes skill prompt. Update when the question router format changes.

**Window:** between sessions  
**Purpose:** Surface all unanswered Q- blocks from the maintainer question router,
grouped by area and urgency. Useful for thinking through decisions without needing
to navigate the router doc directly.

**When to use:** during a commute or break when you want to think about open decisions,
or before a session to know which architectural questions are blocking progress.

---

## Prompt

```
You are Hermes, working with the SuperBot repository at /home/hermes/repos/superbot.
Do not modify any files. Read-only only.

Produce an OPEN QUESTIONS REPORT from the SuperBot question router.
Keep the output under 600 words.

Do the following in order:

1. Read: /home/hermes/repos/superbot/docs/owner/maintainer-question-router.md
   Find every Q-NNNN entry. For each, note:
   - The Q number
   - The topic/area (one phrase)
   - Whether it is marked as Answered / Open / Partially answered
   - If it is blocking any active work (look for "gated on", "blocked until", "needs Q-")

2. Read: /home/hermes/repos/superbot/docs/current-state.md
   Check the active lanes for references to open Q- blocks (e.g., "Q-0085 open",
   "pending Q-", "gate: Q-"). Add any you find that were not already in step 1.

3. Separate the questions into:
   - BLOCKING: directly gates an active lane or feature
   - ARCHITECTURAL: affects layer design, ownership, or long-term structure
   - PRODUCT: owner preference, UX, or business direction
   - PROCESS: workflow, tooling, or agent-behavior decisions

4. For each blocking question, note in one sentence what is blocked and what the
   options are (if the router doc mentions them).

COMPOSE in the HOUSE STYLE (docs/operations/hermes-skills/_house-style.md): bottom line first, plain
words, grouped, one screen. Lead with the answer; keep Q-#numbers but say each topic in plain English,
not router shorthand.

---
🤔 Open decisions — [today's date]

Bottom line: [N decisions waiting; the one that would unblock the most is [plain topic] (Q-####)].

🚧 Blocking work right now
   • Q-#### — [topic in plain words]: [what it's holding up].

🏗️ Bigger / structural (no rush)
   • Q-#### — [topic in plain words].

🎮 Product & feel
   • Q-#### — [topic in plain words].

⚙️ How we work (process / tooling)
   • Q-#### — [topic in plain words].

(Omit any group that's empty. Full detail is in the question router.)
---
```

---

## Notes

- The router uses `Q-NNNN` identifiers. Answered questions are usually marked
  `**Status:** Answered` or have a date stamp and resolution note.
- Questions marked "partially answered" count as open — they still gate something.
- This skill is read-only: it surfaces questions but does not answer them. Answer
  them in a Claude Code session where the full repo context is available.

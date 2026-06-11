# Skill: `superbot-ideas-triage`

> **Status:** `living-ledger` — ready-to-use Hermes skill prompt. Update when the ideas lifecycle or backlog structure changes.

**Window:** between sessions / downtime  
**Purpose:** Review the ideas backlog from mobile without a full Claude Code session.
Shows what lifecycle state every idea is in and suggests one grooming move.

**When to use:** during downtime when you want to think about what to build next, or
before a session when you want to know which ideas are ripe to execute.

---

## Prompt

```
You are Hermes, working with the SuperBot repository at /home/hermes/repos/superbot.
Do not modify any files. Read-only only.

Produce an IDEAS TRIAGE REPORT. Keep the output under 700 words.

Do the following in order:

1. Read: /home/hermes/repos/superbot/docs/ideas/README.md
   Extract every linked idea file (they are in the bullet list under "Current broad captures").
   For each idea, note its name and any lifecycle state mentioned (raw / captured / routed /
   in-progress / or no state = assume captured).

2. Read: /home/hermes/repos/superbot/docs/roadmap.md
   Note which ideas have a horizon entry (Now / Next / Later / Someday).

3. Read: /home/hermes/repos/superbot/docs/planning/ — list the files (ls only, do not read them).
   Note which idea topics have a corresponding planning doc.

4. Cross-reference steps 1–3 to assign each idea one of these states:
   - RAW: in ideas/ but no badge, no roadmap entry, no planning doc
   - CAPTURED: has ideas/ entry + badge, no further routing
   - ROUTED: has a roadmap horizon OR a planning doc
   - IN-PROGRESS: referenced as active in docs/current-state.md

5. Read: /home/hermes/repos/superbot/docs/owner/maintainer-question-router.md
   Check if any idea has an open Q- block blocking it.

6. Identify:
   - Ideas stuck at RAW (highest priority to route)
   - The one idea closest to being executable (CAPTURED, clearly scoped, no blocker)
   - Any idea with a planning doc but no roadmap entry (planning without a horizon = invisible)

Format the output as:

---
## SuperBot Ideas Triage — [today's date]

### Backlog by state
| Idea | State | Roadmap horizon | Planning doc? |
|------|-------|-----------------|---------------|
[one row per idea]

### Stuck at RAW
[list ideas with no routing, one line each — these need a home]

### Best candidate to execute next
[one idea, one paragraph — why it's ready and what the first step would be]

### Needs grooming attention
[1–3 specific actions: "route X to roadmap", "link Y to planning doc", etc.]
---
```

---

## Notes

- The ideas lifecycle is: raw → captured → routed (roadmap/planning) → in-progress → shipped.
  An idea that is captured but not routed is not lost, but it will never be executed — routing
  gives it a destination.
- The "best candidate to execute next" is just a suggestion. Claude Code weighs it against
  the active lanes and owner priorities before acting.
- If an idea has an open Q- block, it cannot be executed until the question is answered.

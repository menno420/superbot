# Skill: `superbot-prompt-builder`

> **Status:** `living-ledger` — ready-to-use Hermes skill prompt. Update when the repo's subsystem folios or binding doc structure change.

**Window:** pre-session  
**Purpose:** Turn a task description (including a spoken voice-mode idea) into a
structured, oriented Claude Code prompt. Arrive at the session with a prompt ready
to execute rather than spending context figuring out where to start.

**When to use:** you have an idea while away from the computer and want to prepare a
complete prompt for Claude Code before the session opens.

---

## Prompt

```
You are Hermes, working with the SuperBot repository at /home/hermes/repos/superbot.
Do not modify any files. Read-only only.

I want you to build a CLAUDE CODE SESSION PROMPT for the following task:

[TASK DESCRIPTION — replace this with what you want to build or fix]

Do the following in order to build the prompt:

1. IDENTIFY THE AREA
   Which subsystem(s) does this task touch?
   Options: ai / setup / settings / mining / games / help / economy / social / btd6 /
            governance / runtime / views / utils / docs-only
   Read the matching folio: /home/hermes/repos/superbot/docs/subsystems/<area>.md
   Note the current state and any active work in that area.

2. IDENTIFY BINDING CONTRACTS
   Which of these apply to this task? (read only the ones that apply)
   - /home/hermes/repos/superbot/docs/architecture.md (if touching layer boundaries)
   - /home/hermes/repos/superbot/docs/ownership.md (if writing to DB or mutations)
   - /home/hermes/repos/superbot/docs/runtime_contracts.md (if touching bot lifecycle)
   - /home/hermes/repos/superbot/docs/helper-policy.md (if adding a utility function)
   List which ones apply and the single most important rule from each.

3. IDENTIFY SOURCE FILES
   Run: find /home/hermes/repos/superbot/disbot -name "*.py" | xargs grep -l "<relevant keyword>" 2>/dev/null | head -10
   (Use a keyword from the task — cog name, service name, command name, etc.)
   List the 2–4 most relevant files. Do not read them — just list paths.

4. CHECK FOR ACTIVE WORK
   Read: /home/hermes/repos/superbot/docs/current-state.md
   Does any active lane overlap with this task? Note it if so.

5. CHECK IDEAS AND PLANNING
   Run: ls /home/hermes/repos/superbot/docs/planning/
   Is there a planning doc for this area? If yes, note its name.

6. DRAFT THE PROMPT
   Write a complete prompt using this structure:

---
## Task: [one-line task title]

### Context
[2–3 sentences: what this task is, why it matters, what subsystem it touches]

### Read first
[list of docs to read, in order — binding ones first]
- docs/architecture.md (rule: ...)
- docs/ownership.md (rule: ...)  [if applicable]
- docs/subsystems/<area>.md

### Relevant source files
[2–4 file paths from step 3]

### Active lane overlap
[from step 4 — or "none detected"]

### Implementation notes
[1–3 specific constraints or gotchas from the binding docs — e.g.,
 "always write through <service>.py", "use settings_keys constants not raw strings"]

### Acceptance criteria
[2–3 concrete things that should be true when the task is done]
---

Do not implement anything. Only produce the prompt.
```

---

## Notes

- Replace `[TASK DESCRIPTION]` in the prompt above with your actual task in plain language.
  Hermes will orient the rest automatically.
- The `find | grep` in step 3 may need a different keyword depending on the task — adjust it.
- If you describe a vague idea (e.g. "make mining more fun"), Hermes will produce a prompt
  that captures it but also notes what needs to be decided before implementation can begin.
- The resulting prompt is an artifact. Paste it into Claude Code and let it do the rest.

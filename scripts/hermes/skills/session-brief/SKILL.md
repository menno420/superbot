---
name: superbot-session-brief
description: "Generate a compressed orientation brief that you paste into Claude Code at the start of a session. Skips the standard 15-minute orientation read."
version: 1.0.0
author: "SuperBot agents"
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Orientation, SuperBot, Planning]
---

<!-- GENERATED — DO NOT EDIT. Source of truth: docs/operations/hermes-skills/session-brief.md. Regenerate with scripts/hermes/build_skills.py. -->

You are Hermes, working with the SuperBot repository at /home/hermes/repos/superbot.
Do not modify any files. Read-only only.

Produce a SESSION BRIEF for a Claude Code agent about to start work on this repo.
Keep the entire output under 800 words. Be concrete — no filler.

Do the following steps in order:

1. Run: git -C /home/hermes/repos/superbot log --oneline -5
   Report the last 5 commits (hash + message only).

2. Run: git -C /home/hermes/repos/superbot status --short
   If the tree is dirty, list the modified files. If clean, say "working tree clean".

3. Run: gh pr list --repo menno420/superbot --state open --json number,title,isDraft,headRefName
   List all open PRs as: #NNN [draft?] title (branch). If none, say "no open PRs".

4. Read: /home/hermes/repos/superbot/docs/current-state.md
   Extract and summarize:
   - Active implementation lanes (what work is in progress)
   - Recently shipped (last 3 entries only)
   - Any gates or blockers mentioned

5. Read: /home/hermes/repos/superbot/docs/owner/maintainer-question-router.md
   List any Q- blocks marked as open (not answered). One line each: Q-NNNN — topic.
   If more than 5 open, show the 5 most recent only.

6. Read the most recent file in /home/hermes/repos/superbot/.sessions/ (sort by filename, newest first).
   Summarize in 3 bullet points: what was done, what was left open, what is next.

7. Based on steps 3–6, suggest ONE focus for the next session in one sentence.

Format the output as:

---
## SuperBot Session Brief — [today's date]

### Recent commits
[step 1]

### Repo state
[step 2]

### Open PRs
[step 3]

### Active lanes & gates
[step 4 summary]

### Open questions (Q- blocks)
[step 5]

### Last session summary
[step 6]

### Suggested focus
[step 7]
---

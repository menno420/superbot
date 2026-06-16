---
name: superbot-morning-briefing
description: "One consolidated start-of-day digest — repo health, open PRs, recent CI, what the autonomous routines did overnight, and any decisions waiting on the owner — so the day starts from a single message instead of several separate pings."
version: 1.0.0
author: "SuperBot agents"
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Monitoring, SuperBot, Briefing]
    related_skills: [superbot-repo-health, superbot-open-questions, superbot-idea-spotlight]
    blueprint:
      schedule: "0 6 * * *"
      deliver: origin
      prompt: "Post the SuperBot morning briefing: health, open PRs, CI, overnight routine activity, and any decisions waiting on me."
      no_agent: false
---

<!-- GENERATED — DO NOT EDIT. Source of truth: docs/operations/hermes-skills/morning-briefing.md. Regenerate with scripts/hermes/build_skills.py. -->

You are Hermes, working with the SuperBot repository at /home/hermes/repos/superbot.
Read-only. Produce ONE morning briefing, under 450 words. Use ✅/⚠️/❌ for the health line.

1. SYNC: git -C /home/hermes/repos/superbot fetch origin main && \
         git -C /home/hermes/repos/superbot checkout -B main origin/main

2. HEALTH (the fast subset of superbot-repo-health — don't re-run all six):
   cd /home/hermes/repos/superbot
   python3 scripts/check_docs.py --strict            # docs reachable/fresh?
   python3 scripts/check_architecture.py --mode strict   # arch errors (warnings are fine)
   → one ✅/⚠️/❌ line. (For the full traffic-light, point at superbot-repo-health.)

3. PULL REQUESTS + CI:
   gh pr list --repo menno420/superbot --state open --json number,title,labels,isDraft,headRefName,updatedAt
   gh run list --repo menno420/superbot --limit 6 --json status,conclusion,headBranch,displayTitle
   → flag: any `needs-hermes-review` PR (your review-merge queue), any PR older than ~2 days, any
     recent CI failure (name the branch).

4. OVERNIGHT ROUTINE ACTIVITY (the self-improvement loop — did it run?):
   gh pr list --repo menno420/superbot --state merged --limit 8 --json number,title,mergedAt
   → list the claude/* PRs merged since the last briefing (~24h). If none merged and none are open,
     say so plainly ("loop quiet overnight") — that itself is signal (cron lag or nothing to do).

5. DECISIONS WAITING ON THE OWNER (reuse the superbot-open-questions logic):
   Scan docs/owner/maintainer-question-router.md for OPEN / DISCUSS Q-blocks awaiting a verdict,
   and docs/current-state.md ▶ Next action for any "owner-gated" / "👤" item. List the few that
   actually need HIM (not agent work) — these are the loop's real bottleneck.

6. DELIVER in this shape:

---
## ☀️ SuperBot morning briefing — [date]
- **Health:** ✅/⚠️/❌ [one line]
- **Open PRs:** [count] — [needs-hermes-review / stale flags, or "none"]
- **CI:** [recent pass/fail summary]
- **Overnight:** [merged claude/* PRs, or "loop quiet"]
- **⚑ Waiting on you:** [decisions only the owner can make, or "nothing"]
- **💡 Idea of the day** is posted separately (superbot-idea-spotlight).
### Verdict
[one sentence — is today clear to work in, or does something need you first?]
---

RULES:
- Verify, don't assume — every line is from a check above; say "gh unavailable" and mark ⚠️ if it is.
- Keep it to signal. This is the owner's at-a-glance inbox, not a full report.
- You take no action here (no merges, no dispatch) — the briefing is a hint; the owner or a
  dedicated skill (review-merge / dispatch) acts.

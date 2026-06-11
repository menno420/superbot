# Skill: `superbot-repo-health`

> **Status:** `living-ledger` — ready-to-use Hermes skill prompt. Update when the repo's health checks or CI setup change.

**Window:** between sessions  
**Purpose:** Traffic-light health snapshot. Answers "is anything broken right now?"
without opening a full Claude Code session.

**When to use:** Monday morning before deciding whether to start a session, after a
long break, or any time you want confidence the repo is in a good state.

---

## Prompt

```
You are Hermes, working with the SuperBot repository at /home/hermes/repos/superbot.
Do not modify any files. Read-only only.

Run a REPO HEALTH CHECK and produce a traffic-light report. Use ✅ (green), ⚠️ (warning),
or ❌ (red) for each dimension. Keep the whole output under 500 words.

Run these checks in order:

1. DOCS CHECK
   Run: cd /home/hermes/repos/superbot && python3 scripts/check_docs.py --strict
   ✅ if "all checks passed"
   ❌ if any issues — list them verbatim (they are short)

2. ARCHITECTURE CHECK
   Run: cd /home/hermes/repos/superbot && python3 scripts/check_architecture.py --mode strict
   ✅ if exit 0 with 0 errors
   ⚠️ if warnings only (list count)
   ❌ if errors — list them

3. OPEN PRS
   Run: gh pr list --repo menno420/superbot --state open --json number,title,isDraft,headRefName
   ✅ if 0 open PRs
   ⚠️ if 1–2 open (list them)
   ⚠️ if any are non-draft and older than 2 days (note which)
   ❌ if 3+ open PRs

4. RECENT CI
   Run: gh run list --repo menno420/superbot --limit 5 --json status,conclusion,headBranch,displayTitle
   ✅ if all 5 completed with success
   ⚠️ if 1 failure (note branch)
   ❌ if 2+ failures

5. WORKING TREE
   Run: git -C /home/hermes/repos/superbot status --short
   ✅ if clean
   ⚠️ if modified files present (list them — they may be from a previous Hermes run)

6. MAIN SYNC
   Run: git -C /home/hermes/repos/superbot fetch origin main --dry-run 2>&1
   Run: git -C /home/hermes/repos/superbot log --oneline origin/main..HEAD
   ✅ if HEAD is at origin/main (no local commits ahead)
   ⚠️ if local commits ahead of origin/main (list them — repo clone may be stale)

Format the output as:

---
## SuperBot Repo Health — [today's date + time]

| Dimension       | Status | Notes |
|-----------------|--------|-------|
| Docs            | ✅/⚠️/❌ | ... |
| Architecture    | ✅/⚠️/❌ | ... |
| Open PRs        | ✅/⚠️/❌ | ... |
| Recent CI       | ✅/⚠️/❌ | ... |
| Working tree    | ✅/⚠️/❌ | ... |
| Main sync       | ✅/⚠️/❌ | ... |

### Details
[any ⚠️ or ❌ items expanded here, one paragraph each]

### Verdict
[one sentence — is the repo ready to work in, or does something need attention first?]
---
```

---

## Notes

- If `python3` is not on the path, try `python3.10` (the repo uses Python 3.10 for CI).
- The architecture check may produce warnings for known violations — these are tracked in
  `architecture_rules/` YAML files and are expected. Warnings alone are not a blocker.
- If `gh` is not authenticated, skip steps 3 and 4 and mark them ⚠️ "gh not available".

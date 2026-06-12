# /session-close

End the current session correctly: write the session log, groom one idea, add one new idea, verify quality, commit, push, open/update the draft PR, and merge when CI is green.

## What this does

Runs the full end-of-session checklist defined in `.claude/CLAUDE.md` § "Session & plan workflow":

1. **Session log** — write `.sessions/YYYY-MM-DD-<slug>.md` with the standard format.
2. **Backlog grooming** — move one idea one step down its lifecycle.
3. **New idea** — add one genuine new idea (Q-0089 directive).
4. **Quality gate** — run `check_docs --strict` + `check_quality.py --check-only`.
5. **Commit & push** — clean commit on the session branch.
6. **PR lifecycle** — open draft PR (if not already open), mark ready, merge after CI green.

## Invocation

```
/session-close
/session-close <slug>          # e.g. /session-close hermes-skills
```

Providing a slug skips the interactive prompt for the session log filename.

## Instructions for Claude

When this skill is invoked:

### Step 1 — session log

1. Ask for a session slug if not provided (2–4 words, hyphen-separated, e.g. `hermes-skills`).
2. Determine today's date: `date +%Y-%m-%d`.
3. Check what was done this session by reading:
   - `git log --oneline origin/main..HEAD` — commits on this branch
   - The PR description if a PR already exists
4. Write `.sessions/YYYY-MM-DD-<slug>.md` using this template:

```markdown
# YYYY-MM-DD — <session title>

**PR:** [#NNN](link) — brief description.
**Branch:** `<branch-name>`

## What was done
[3–8 bullet points: each major task completed]

## Decisions recorded
[Any Q- answers, owner decisions, or architectural choices made — or "none"]

## Left open / next session
[Anything deliberately deferred — or "nothing open"]

## 💡 Session idea
**Idea:** [one new idea you genuinely believe in]
**Why:** [one line rationale]
[idea file created: docs/ideas/... or "small — recorded here only"]
```

### Step 2 — backlog grooming

1. Read `docs/ideas/README.md` — pick ONE idea that can move forward.
2. Take the smallest valid step:
   - If it is clearly small + safe + in an active lane → execute it now.
   - If it needs a plan → create `docs/planning/<topic>-plan-<date>.md` and add a roadmap horizon.
   - If it is ambiguous → open a Q-block in `docs/owner/maintainer-question-router.md`.
3. Record the move in the session log under "What was done".

### Step 3 — new idea

Add a `💡 Session idea` block to the session log with one new idea you genuinely believe in.
If it is substantial (warrants its own file), also create `docs/ideas/<topic>-<date>.md`
and add it to the `docs/ideas/README.md` bullet list.

### Step 4 — quality gate

Run these in order and fix any failures before proceeding:

```bash
python3.10 scripts/check_docs.py --strict
python3.10 scripts/check_quality.py --check-only
```

If `check_docs` fails on the new session log file: add the required `> **Status:**` badge.
Session logs use the `audit` badge token.

### Step 5 — commit

Stage only the intentional changes:
```bash
git add .sessions/YYYY-MM-DD-<slug>.md
git add <any other files changed this session>
```

Commit message format:
```
chore(session): close YYYY-MM-DD <slug> session

<one-line summary of what the session accomplished>
```

Then push: `git push -u origin <branch>`.

### Step 6 — PR lifecycle

1. Check if a PR already exists for this branch: `gh pr list --head <branch>`.
2. If no PR: create one as draft with `gh pr create --draft --title "..." --body "..."`.
3. Mark PR ready: `gh pr ready <number>` (or via MCP `mcp__github__update_pull_request`).
4. Wait for CI: poll `mcp__github__pull_request_read` method `get_check_runs` until `status == completed`.
5. If CI green: merge with `mcp__github__merge_pull_request` (merge-commit method).
6. If CI red: diagnose the failure, fix it, push again, re-check.

### Notes

- Do not skip the grooming step. "Nothing to groom" is almost never true — if the
  backlog is genuinely empty, open a router Q-block for the next architectural decision.
- The new idea must be genuine. If you cannot think of one, say so explicitly — forced
  filler is worse than none (owner directive Q-0089).
- If the session had no PR (docs-only or trivial), skip step 6 or close the PR with
  a note explaining why it was not merged.

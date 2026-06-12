# /session-close

End the current session correctly: write the session log (with a previous-session review), groom one idea, add one new idea, verify quality, commit, push, open the PR (ready, not draft), and drive it to a terminal state — merge when CI is green, or close.

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

## ⟲ Previous-session review
[one genuine remark on the *previous* session (read the prior `.sessions/` log) + one
 concrete improvement to the system/workflow it surfaces — or "nothing to improve, because
 <reason>". Never hallucinate filler (Q-0102).]
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

### Step 3b — previous-session review (Q-0102)

Read the *previous* `.sessions/` log and add a `⟲ Previous-session review` block: one
genuine remark on it + one concrete improvement to the system/workflow. Assume the system
is still in development and surface the improvement yourself. If there is genuinely nothing
to improve, say so and why — never hallucinate filler.

### Step 4 — quality gate

Run these in order and fix any failures before proceeding:

```bash
python3.10 scripts/check_docs.py --strict
python3.10 scripts/check_session_log.py --strict      # Q-0089 idea + Q-0102 review present
python3.10 scripts/check_current_state_ledger.py --strict  # merged PRs are in the ledger
python3.10 scripts/check_reconciliation_due.py        # Q-0107: is a 10th-PR docs/planning pass due?
python3.10 scripts/check_quality.py --check-only
```

If `check_reconciliation_due` reports **DUE**, the next session should be a docs-only review +
planning-reconciliation pass (Q-0107: reconcile repo state + plan the next ~9 PRs, modular but
not over-segmented); after that pass, reset the `Last reconciliation pass:** PR #N` marker in
`current-state.md` to the latest PR.

If `check_docs` fails on the new session log file: add the required `> **Status:**` badge.
Session logs use the `audit` badge token. If `check_session_log` fails, add the missing
`💡 Session idea` / `⟲ Previous-session review` section it names. If
`check_current_state_ledger` flags a merged PR, **verify its #number against live GitHub**
then add it to `docs/current-state.md` § Recently shipped (or an aggregated range entry).

**Documentation audit (Q-0104) — the judgment half.** The checks above are the automated
half. Also ask yourself: *"is anything important from this session captured only in chat?"*
— a new owner decision not yet in the router, a design conclusion, a gotcha. Route it to its
durable home before closing. This question, asked once on 2026-06-12, surfaced the drift the
ledger check now guards.

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

### Step 6 — PR lifecycle (must reach a terminal state)

Open the session PR **ready, not draft** — the early *open* (for the PR number) is the
Q-0052 benefit; the draft state added none in our self-merge flow and became a forgotten
step (Q-0103). **Every session must drive its PR to a terminal state — merged or closed —
before ending. An abandoned open PR is the failure this prevents.**

1. Check if a PR already exists for this branch (MCP `mcp__github__list_pull_requests`).
2. If no PR: create one **ready** (`mcp__github__create_pull_request`, `draft: false`).
3. Subscribe to it (`mcp__github__subscribe_pr_activity`).
4. Reconcile with main first (fetch + merge `origin/main`, UNION-resolve conflicts).
5. Wait for CI: `mcp__github__pull_request_read` method `get_check_runs` until `completed`.
6. If CI green: **merge** with `mcp__github__merge_pull_request` (merge-commit method).
7. If CI red: diagnose, fix, push, re-check.
8. If the work should not merge: **close** the PR with a one-line reason. Do not leave it open.

### Notes

- Do not skip the grooming step. "Nothing to groom" is almost never true — if the
  backlog is genuinely empty, open a router Q-block for the next architectural decision.
- The new idea must be genuine. If you cannot think of one, say so explicitly — forced
  filler is worse than none (owner directive Q-0089).
- A session is not closed until its PR is **merged or closed** — never abandoned open (Q-0103).

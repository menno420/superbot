# Session — open the session PR FAST (Q-0189, owner-directed in-session)

> **Status:** `in-progress`
> **Run type:** routine · dispatch
> **Branch:** `claude/early-pr-mandate`

## What I'm about to do

Owner directed, live in-session: make it mandatory to open the session PR **within
~2 minutes of session start** (before the build work), not let it drift behind the
work. Applying under the Q-0106 live-owner carve-out (owner is the reviewer):

- Amend the **Q-0133 born-red bullet** in `.claude/CLAUDE.md` § Session & plan
  workflow with the timing mandate (orient → decide scope → claim → open the
  born-red PR immediately → then build).
- Record provenance **Q-0189** in `docs/owner/maintainer-question-router.md`.

Docs-only; owner is live reviewer → self-merge on green.

## Verification
`python3.10 scripts/check_docs.py --strict`

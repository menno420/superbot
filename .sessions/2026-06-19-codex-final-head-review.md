# 2026-06-19 — Codex reviews the final head, not the born-red opener

> **Status:** `in-progress`

## Arc

Owner asked (in-session): does Codex re-review a PR after the final commits, and would it be a good
idea to (a) explain the born-red card to Codex so it stops re-flagging it, or (b) make every final push
`@codex review` for a forced review on the final head. Investigate → recommend → build the chosen path.

## What I'm about to do

- Verify empirically whether Codex re-reviews after the final push (it does not — see below).
- Build the owner-chosen fix: a GitHub Action that posts `@codex review` when the session card flips to
  a ready status (the born-red final-commit signal), so Codex reviews the complete diff.
- Record the decision (router Q-0180) + mark the long-open idea built.

_This card opens the PR born-red (Q-0133); flipped to `complete` as the final step._

# Session — Hermes sync hardening (self-healing mirror sync + divergence recovery)

> **Status:** `in-progress` — born-red per Q-0133. Live follow-up: the owner's VPS clone had
> DIVERGED from origin/main, so `git pull --ff-only` aborted and the new script wasn't even
> downloaded. Recovery (backup branch + `reset --hard origin/main`) unblocked it and the
> apply-script then landed all three `hermes config set` calls. This hardens the sync so a
> diverged clone can never get stuck again.

## What I'm about to do
- `docs/operations/hermes-operating-prompt.md` — replace the fragile `git pull --ff-only origin
  main` sync line with the self-healing form `git fetch origin main && git checkout -B main
  origin/main` (always lands on fresh main, can't abort on divergence — the pattern the dispatch
  routine already uses). State the clone is a read-only MIRROR; never commit to it. Keep it
  concise — SOUL.md is at ~81% of its byte budget.
- `docs/operations/hermes-terminal-cheatsheet.md` — make the deploy-section pull robust + add a
  "clone diverged → recovery" snippet (backup branch + reset --hard).

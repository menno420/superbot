# Session logs — `.sessions/`

> One file per working session, named `YYYY-MM-DD-<slug>.md`, **newest-first by
> filename** (reverse-sort the glob). Process memory / history only — **not** project
> state (that's `docs/current-state.md`) and **not** the working model (that's
> `docs/collaboration-model.md`).

## Why per-session files

A single shared Session Log meant every session inserted a new entry at the *same* top
anchor, so any two concurrently-open PRs collided there (it bit #529→#530 and
#530→#531). Per-session files have no shared anchor → no structural merge conflict.

## Convention

- **Write** a new file at session end: `.sessions/<date>-<short-slug>.md`.
- Start it with an H1 `# <date> — <title>`, then the usual arc / shipped / findings /
  gates shape.
- **Don't** edit older session files — they're history. Durable rules / runbook facts
  graduate into `.session-journal.md` (the guidebook) or `.claude/CLAUDE.md`.
- **Find** past work by grepping this directory — don't read it top-to-bottom.
- Pre-migration history lives in `.session-journal-archive.md`.

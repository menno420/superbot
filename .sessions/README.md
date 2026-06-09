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
- **Always include a `Context delta` section** (this is the self-improvement loop — see
  `docs/collaboration-model.md` § "Why this system exists"). Produce it — and the two
  flag lines below — by running the **reflection interview** before writing the log: a
  standing six-question self-interview the maintainer used to run manually in chat
  nearly every session (formalized at his request, 2026-06-09, after the Lane-3/#634
  session's answers proved their value).
  1. **Where did the orientation route fail to cover you?** — context you had to find
     that orientation/folios didn't route you to (a file, a contract, a gotcha).
     → `Context delta`: **Needed but not pointed to**.
  2. **What were you pointed to that didn't pay off?** — reading the route sent you to
     that wasn't needed (candidate to de-emphasize).
     → `Context delta`: **Pointed to but didn't need**.
  3. **What did you reverse-engineer from source?** — tribal knowledge that deserves a
     home (e.g. a rule only living in a code comment).
     → `Context delta`: **Discovered by hand**.
  4. **What consequential decision did you make alone** that the maintainer should
     consciously ratify (a default you picked, a contract shape, a gate keyed on a
     label)? → a short **Decisions made alone** line in the log; if it's product
     intent, also a router entry.
  5. **What is the genuine weak point of what shipped** — the limitation or unverified
     half you'd want the next agent (or the prod check) to know?
     → the log's **Flagged for maintainer** / known-limits line.
  6. **What one docs/tooling change would have most helped this session?**
     → execute it in the grooming pass if small, else file it under `docs/ideas/`.
  Answer honestly and specifically — a near-miss is more valuable written down than a
  success story. A periodic REVIEW (`.session-journal.md`) mines these deltas and
  promotes recurring gaps into the orientation route / folios. Keep it to what you'd
  want the *next* agent to have known.
- **Don't** edit older session files — they're history. Durable rules / runbook facts
  graduate into `.session-journal.md` (the guidebook) or `.claude/CLAUDE.md`.
- **Find** past work by grepping this directory — don't read it top-to-bottom.
- Pre-migration history lives in `.session-journal-archive.md`.

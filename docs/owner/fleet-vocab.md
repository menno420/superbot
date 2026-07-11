# Fleet vocabulary — the owner's shorthand → what Claude does

> **Status:** `owner-guidance` — the owner's shorthand command dictionary. The point:
> the owner types a **short word**, and Claude knows the full workflow + the
> questions to ask, without re-explaining each time. **Owner-owned:** add / rename /
> retune entries freely; Claude proposes new ones after a session that would have
> benefited from one. Executable versions live as **skills** (`.claude/skills/<name>/`);
> this file is the index + the words that map to them.
>
> **How to use:** say the keyword (optionally with a focus, e.g. "review games").
> If an entry says *ask first*, Claude runs the listed questions before acting; if it
> says *decide-and-flag*, Claude just does it and flags choices. Unknown word → Claude
> asks what you mean and offers to add it here.

## Core words

| Word | Means | Skill | Default behavior |
|---|---|---|---|
| **review** | Full **fleet night/status review** across every Project — what each lane shipped, did it add a valuable report, health/blockers, routine+model config → opinionated report + fix-first plan + owner-action queue, documented + sent in chat. | `/fleet-review` | all active lanes, deep, document in `docs/eap/`, decide-and-flag; asks only if scope/focus is genuinely unclear |
| **status** | **Quick** fleet sweep — the roster + freshness + any lane that's stale/stuck/blocked. No deep per-lane report. The 60-second "is anything on fire" check. | (`/fleet-review` light mode) | roster-only + flag anomalies; no fan-out unless something looks wrong |
| **routines** | Audit the **routine → repo → model** config across the fleet: which routine drives which lane, is its repo attached (the ~1/3 add_repo failure), does its model match intent → produce the **owner-attach checklist** (the clicks only you can do). | (part of `/fleet-review`) | produce the per-routine table + owner action list |
| **plan** | Turn the current state into a **prioritized plan for the day** — fix-first list, owner-action queue, what to watch. Standalone or the tail of a review. | — | decide-and-flag; asks only on a real product fork |
| **ship** | Drive the current session's work to a **merged PR** — born-red card → complete, CI green, merge (or close). | `/session-close` | full close-out checklist |
| **groom** | Move one idea one step down its lifecycle (idea → plan → build). | `/groom-ideas` | one idea, safe lane |

## Conventions Claude follows for every word

- **Cite, don't assert** — every load-bearing claim links a PR / commit / file / CI run.
- **Honesty over polish** — "no report yet", "stuck on X", "budget overran" are the
  valuable findings; never paper over a quiet or broken lane.
- **Family-level model names only** (fable-5, opus-4.8, sonnet-5) — never exact IDs.
- **Decide-and-flag** reversible calls; route only genuine product/irreversible forks
  to you.
- **Guardrails carried in from this session:** no `delete_trigger` / destructive
  approval-gated ops unless you say so; in Project sessions never self-merge (classifier
  wall) — this hub session can merge normally.

## Growing this file

When a session would have gone faster with a shorthand, Claude proposes a new row here
(word · means · skill · default) at session close. The owner keeps or drops it. When a
word's workflow is stable, Claude promotes it to a real `.claude/skills/<word>/SKILL.md`
so it's one command. Disambiguation note: **"review" = fleet review** here; a code-diff
review is `/code-review`, a GitHub-PR review is `/review`.

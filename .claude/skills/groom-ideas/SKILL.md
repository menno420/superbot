# /groom-ideas

Move one idea one step down its lifecycle — the standing end-of-session backlog-grooming pass
(owner decision Q-0015), as an on-demand command.

## What this does

Runs the backlog-grooming pass defined in `.claude/CLAUDE.md` § "Session & plan workflow" (Q-0015)
and `docs/ideas/README.md`: browse `docs/ideas/`, pick **one** idea, and take the smallest valid step
to advance it so **every idea eventually becomes implemented or discussed — never orphaned**. This is
the standing *secondary* task — what an agent does once its main work + PR are done and capacity
remains. It is a wrapper around that procedure, not new policy.

> Grooming **moves an existing** idea. It is distinct from the Q-0089 *new idea* ender (which *adds*
> one) and the Q-0102 *previous-session review*. The `/session-close` skill already calls this as its
> Step 2; `/groom-ideas` lets any session run the pass on its own.

## Invocation

```
/groom-ideas
/groom-ideas <idea-slug>        # groom a specific idea instead of picking one
```

## Instructions for Claude

### Step 1 — pick one idea

Read `docs/ideas/README.md` (the conveyor index) and pick **one** idea that can move forward. The
maintainer drops ideas in *any order*; you route them. If a slug was passed, groom that one. Skip
ideas already badged `historical` (implemented) and anything in-flight.

### Step 2 — take the smallest valid step down the lifecycle

- **Small + safe + in a decided lane** -> *execute it now* (a quick-win). Keep the change contained
  and reversible; flag it `⚑ Self-initiated` on the run report (Q-0172).
- **Bigger / needs design** -> *structure it into a plan*: create
  `docs/planning/<topic>-plan-<date>.md` (scoped against the repo's house style so an executor can
  build it cold) and add a `docs/roadmap.md` horizon row. Index it in `docs/ideas/README.md`.
- **Excessive / ambiguous / needs owner intent** -> open a Q-block in
  `docs/owner/maintainer-question-router.md` (next free `Q-00NN`, append-only) — never invent an
  answer the owner hasn't given.

When an idea is implemented, re-badge its capture `historical` (it stays listed, annotated ✅) so the
active backlog reflects only live ideas.

### Step 3 — record the move

Note what you did in the session log under "What was done". The full intake -> map -> route -> groom
-> outcome mechanism is in `docs/ideas/README.md`.

### Notes

- "Nothing to groom" is almost never true. If the backlog is genuinely empty of movable ideas, open a
  router Q-block for the next architectural decision instead — an agent should always have a next
  thing to do (Q-0015).
- Promotion (idea -> plan -> implementation) needs **no** owner approval anymore (Q-0172) — the only
  requirement is the `⚑ Self-initiated` accountability flag. Safety brakes (irreversible / external /
  production work) still ask first.

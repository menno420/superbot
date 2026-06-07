# Architecture Decision Records

> **Status:** `reference` — ADR index.

This directory holds short, durable records of deliberate
architectural decisions — particularly the ones that say *what we
chose not to do, and why*.  Without them, every quarter someone
re-litigates the same trade-off.

## When to add an ADR

Add one when:

- You decide to skip a documented future-work item (e.g. "we will
  not move EventBus to Redis at this scale").
- You decide to take on a known limitation rather than fix it
  ("game state is lost on restart; cost-benefit doesn't justify
  full persistence yet").
- You commit to a non-obvious convention that future readers will
  question ("why does the service-layer chokepoint pattern accept
  raw `discord.Member` instead of just IDs?").

A small bug fix or refactor does NOT need an ADR — its commit
message and PR description are the durable record.

## Format

Each ADR is one Markdown file, numbered sequentially
(`NNN-short-name.md`).  Required sections:

- **Context** — what prompted the decision; what was the alternative?
- **Decision** — what we chose, in plain language.
- **Consequences** — what this commits us to / forecloses.
- **Re-evaluation criteria** — concrete triggers that would invalidate
  the decision (so it can be picked up again without restarting the
  whole conversation).

ADRs are immutable once landed.  Superseded ADRs get a follow-up
ADR that links back.

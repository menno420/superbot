# Owner review inbox — a channel to post ideas/reviews that sessions read and resolve

> **Status:** `ideas` — capture only (owner-directed 2026-06-17; he chose "capture as idea + plan,
> build later" via `AskUserQuestion`). Decision provenance: **Q-0169**. Plan:
> [`owner-review-inbox-plan-2026-06-17.md`](../planning/owner-review-inbox-plan-2026-06-17.md).
> Source code + the binding contracts win over this file.
> **Subsystem:** none — the dashboard review board (infra, not a bot subsystem).

## The problem (owner, 2026-06-17)

The owner's intended role is **ideas, bug reports, and function/cog reviews** — *not* planning. But
he has no good channel for the review half: *"often I remember something about a cog that I would
like to be changed, but I always forget when I enter a session."* Writing it down elsewhere "isn't
really working well," mostly because there's no way to **see whether it has been fixed already**.

He wants a place where he can — from his phone — **post an idea or a review**, have the
routines/sessions **read it and act on it**, and **see when it's been addressed**. Especially for
**command/cog reviews** ("I remember X about a cog I'd like changed"). Bonus: **other people could
send in ideas/comments** too. He calls this *"probably a very high-leverage thing"* — it raises both
the **reviewability of the bot** and the **communication bandwidth with the agents**.

## The shape (owner's framing)

- **Eventually two separate sites:** the public **product** site and a separate **owner↔agent
  communication** site. But **near-term: integrate as much as possible into the existing dashboard**
  (`dashboard/`), not a second deployment.
- So this is the dashboard's **owner-zone "review inbox"** — distinct from the existing read-only
  surfaces and from the multi-user *control* panel (Q-0159).

## Why it fits the system (and is high-leverage)

- It closes the **owner → agent** half of the loop. Today the agent→owner half exists (run reports,
  the morning briefing, current-state ▶); the owner→agent half is ad-hoc chat that evaporates.
- A posted review with a **status** (open → addressed) is the cog-review analogue of the bug book:
  durable, dedup-able, and "is it fixed?" answerable at a glance — exactly his complaint.
- It directly **feeds the plan backlog** (the "running out of plans" problem, Q-0164): owner reviews
  become a first-class intake stream the reconciliation routine can promote into plans.

## Do-not-duplicate (check before building)

- **`docs/health/bug-book.md`** is the bug channel — this is the *review/idea* channel; keep them
  distinct or unify deliberately, not by accident.
- **The `reconcile` / `continue` labeled-issue mechanism** already lets a human steer routines —
  the near-term build should *reuse* it (a posted review files a labeled issue sessions already
  read), not invent a parallel trigger.
- **The developer-dashboard** (`developer-dashboard-2026-06-16.md`) + **multi-user control panel**
  (Q-0159) are the surfaces this lives inside.

## Near-term vs. eventual (see the plan for the buildable phasing)

- **Phase 1 (buildable now, low risk):** a dashboard **read-only "Review board"** page that lists
  open vs. resolved review items, sourced from a `review`-labeled GitHub issue stream (so existing
  sessions already see them, and "resolved" = issue closed). The owner posts via the GitHub mobile
  app or a thin form.
- **Phase 2 (owner-paced):** a **post form** on the dashboard that files the issue itself (needs the
  control-API write side + Discord OAuth — the same gated foundation as the live editors).
- **Eventual:** the dedicated standalone communication site + public submissions.

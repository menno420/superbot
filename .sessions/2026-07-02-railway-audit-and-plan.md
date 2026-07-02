# 2026-07-02 — Railway: token-capability audit + new-project setup plan

> **Status:** `in-progress` — born-red (Q-0133). Run type: manual · owner-directed.
> Scope: docs-only. **Strictly read-only against the live Railway account** — no mutations.

**Branch:** `claude/superbot-rebuild-design-spec-de4mh7` (restarted from `main` @ #1637 merged).

## What I'm about to do (intentions)

The owner has provided a Railway token (`RAILWAY_API_KEY` + project/service/environment IDs are in
this container's env) and asked for two things:

1. **Establish exactly what this token can and cannot do** — token type (account vs team vs
   project), API scope, and practical limitations — via read-only GraphQL probing of the public
   Railway API plus documented behavior. **No mutation is ever executed**; capability of the
   mutation surface is established from the schema + token identity, not by trying writes.
2. **A plan + roadmap for setting Railway up correctly from day one in the new (rebuild) project** —
   the runtime half of the control plane (the design spec §6 covers the GitHub half): services,
   environments, variables/secrets hygiene, deploy triggers, health checks, restart policy,
   Postgres, backups, observability, cost controls, and how the Phase-5 shadow-run/cutover/rollback
   choreography maps onto Railway primitives.

Deliverable: `docs/planning/railway-setup-plan-2026-07-02.md` (+ operational facts routed to
`docs/operations/` where durable).

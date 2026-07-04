# Railway config-drift checker (2026-07-02)

> **Status:** `ideas` — session idea (Q-0089, from the Railway audit session). Not approved for
> implementation.

## The idea

A read-only `scripts/check_railway_config.py` (+ a weekly routine) that queries the Railway
GraphQL API with a **scoped project token** and diffs live deploy config against a committed
expected-state file (`docs/operations/railway-expected-state.json`): deploy triggers incl. the
**wait-for-CI flag**, healthcheck paths, restart policies, watch paths, backup schedules, regions,
and variable **names** (never values). Any drift → a loud finding (issue or session-start banner
line), exactly like the ledger/docs checkers but pointed at infrastructure.

## Why it's worth having

This session found `checkSuites: false` on all three deploy triggers and **zero backup schedules
on the production Postgres volume** — both silently drifted-or-never-set, both invisible because
nothing watches the dashboard. Config-as-code (the new-project plan) fixes authorship, but only a
checker closes the loop on *live* state — "enforce, don't exhort" (Q-0132) applied to the runtime
control plane. It also gives the R-now fixes a regression guard: once backups/wait-for-CI are
enabled, they can never silently vanish again.

## Route

S5 (operations) · pairs with
[`../planning/railway-setup-plan-2026-07-02.md`](../planning/railway-setup-plan-2026-07-02.md)
(§6 R-now items; the expected-state file is a natural by-product of executing them). Needs the
scoped-token decision (plan §7.3) first — the checker should *not* run on the account token.

# Review inbox — owner reviews of cogs, commands, and ideas

> **Status:** `living-ledger` — the durable intake for the owner's **reviews**:
> "change X about this cog", "this command should do Y", or a fresh idea worth
> acting on (decision **Q-0169**, 2026-06-17;
> [plan](../planning/owner-review-inbox-plan-2026-06-17.md)). It is the owner↔agent
> review channel: a remembered review lands here so it does not evaporate, and
> "is it fixed?" is answerable at a glance via the **OPEN → RESOLVED** status.
> **Convention:** one numbered entry per review, newest first. Mirrors the bug-book
> shape so the same intake instincts apply — but a review is a *requested change /
> improvement*, not a production bug.

## What this is (and what Phase 1 ships)

This file is the **single source of truth** for owner reviews. The dashboard's
read-only `/reviews` page (Phase 1) is a **read view** over it: `scripts/export_dashboard_data.py`
parses each `## REV-NNNN` section into the dashboard payload, and the page renders
open vs. resolved items grouped by area. There is **no write side yet** — the owner
edits this file directly (via the GitHub app), and a new review shows up on the
dashboard within a merge (the `dashboard-data-refresh.yml` workflow regenerates the
JSON on `docs/**` changes).

Phase 1 is deliberately zero-infrastructure: no API token, no auth, no form. The
post-from-the-dashboard form (Phase 2) and public submissions (Phase 3) are owner-paced
and share the control-API write side the live editors use — see the plan.

## Agent intake — how to act on a review

Treat an **OPEN** review like a bug-book entry (a bugs-first cousin): a requested
change waiting to be made. When you address one in a PR, flip its status line to
`RESOLVED (#PR)` in the **same** PR that closes it, so the dashboard shows it
resolved within a merge. Keep the entry — the resolved history is the point.

## Convention — entry shape

```
## REV-NNNN — <area> — STATUS

- **Review (owner):** <the requested change / improvement, verbatim where possible>
- **Area:** <cog / command / subsystem / idea>
- **Resolution:** <filled at resolve time — what changed, the fix PR>
```

`STATUS` is `OPEN` or `RESOLVED` (a trailing `(#PR)` is fine — the parser reads the
first word). `<area>` is the cog/command/idea the review is about; it groups the
dashboard view.

<!-- No reviews recorded yet. The owner adds the first REV-NNNN entry here (via the
GitHub app or a session); until then /reviews renders its empty state. -->

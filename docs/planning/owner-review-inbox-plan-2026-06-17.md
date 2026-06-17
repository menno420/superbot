# Plan — Owner review inbox (dashboard board, issue-backed)

> **Status:** `plan` — executable plan for the owner↔agent review channel
> ([idea](../ideas/owner-review-inbox-2026-06-17.md); decision **Q-0169**, 2026-06-17). Phase 1 is
> buildable now with no owner setup; Phases 2–3 are owner-paced. Source + the binding contracts win.

## Goal

Give the owner (and later others) a durable place to post **ideas and cog/command reviews** that
sessions read and act on, with a visible **open → resolved** status — so a remembered "change X
about this cog" doesn't evaporate, and "is it fixed?" is answerable at a glance.

## Design principle

**Reuse the labeled-issue rail, don't invent a store.** A "review" is a GitHub issue labeled
`review`. Sessions already read labeled issues (`reconcile`/`continue`); resolution = the issue is
closed (ideally by the PR that addresses it, via `Closes #N`). The dashboard is a **read view** over
that stream until the owner sets up the write side. This keeps Phase 1 zero-infrastructure and
loop-native.

## Phase 1 — read-only "Review board" page (buildable now, no owner setup)

- **New dashboard route `/reviews`** (`dashboard/app.py` + `dashboard/templates/reviews.html`),
  linked in the nav. Renders open vs. resolved review items grouped by area (cog/command/idea).
- **Data source:** add a `reviews` block to `dashboard/data/dashboard.json` via
  `scripts/export_dashboard_data.py`. Two viable sources, pick by cost:
  - *Simplest:* parse a committed `docs/owner/review-inbox.md` (one `## REV-NNNN — <area> — STATUS`
    section each, mirroring the bug-book parser already in `export_dashboard_data.py`). Zero API,
    works offline, owner edits via the GitHub app. **Recommended for Phase 1.**
  - *Richer:* read `review`-labeled issues live (needs an API token in the dashboard service).
- **Freshness:** the new `dashboard-data-refresh.yml` workflow (Q-0167) already regenerates the JSON
  on `docs/**` changes, so a new review shows up within a merge.
- **Agent intake:** add one line to the dispatch routine prompt + `AGENT_ORIENTATION` — "check
  `docs/owner/review-inbox.md` for OPEN owner reviews; treat them like bug-book entries (bugs-first
  cousins), and mark `RESOLVED (#PR)` when you address one." This is what makes posts get *acted on*.

## Phase 2 — post-from-the-dashboard (owner-paced)

- A **form on `/reviews`** (owner-auth) that appends a `REV-NNNN` entry (or files the labeled issue).
- Shares the **control-API write side + Discord OAuth** foundation the live editors use (Q-0156/
  dashboard-live-editor-plan) — so it lands when that foundation is set up, not before.

## Phase 3 — public submissions + the eventual standalone site

- Open the form (rate-limited, moderated) so **others can submit** ideas/comments (owner's "other
  people could send in ideas").
- Split the dedicated **owner↔agent communication site** out from the product dashboard when it
  earns its own deployment (owner's "eventually 2 separate websites").

## Verification

- Phase 1: `python3.10 scripts/export_dashboard_data.py` produces a `reviews` block; `/reviews`
  renders open/resolved; `check_docs --strict` + `check_quality --check-only` green; the parser has
  a unit test mirroring the bug-book parser test.

## Why this is a good next buildable lane

Phase 1 is **turn-key, low-risk, owner-aligned, and feeds the plan backlog** (Q-0164) — it converts
owner reviews into a first-class intake stream. Strong candidate for the next reconciliation band.

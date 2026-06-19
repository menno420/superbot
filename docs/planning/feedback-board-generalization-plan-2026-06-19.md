# Unified tagged feedback board — owner-review-inbox generalization (2026-06-19)

> **Status:** `plan` — promoted from the owner's 2026-06-19 brainstorm captured in
> [`ideas/ai-correction-report-and-ticket-service-2026-06-19.md`](../ideas/ai-correction-report-and-ticket-service-2026-06-19.md)
> (§ "The unified feedback board + submission moderation") by the band-#1140 reconciliation pass
> under the **idea→plan gate (Q-0172)** and the owner's #1140-fire directive ("then the
> feedback-board/owner-inbox generalization"). **This plan covers the board itself — the human-owned
> store/UI. The AI *audience-routing/ticket* layer that writes into it stays plan-the-questions-first
> (routed as Q-0183) and is explicitly out of scope here.** Source + the binding contracts win.
> **Subsystem:** operations / dashboard (the owner↔community intake surface).

## 1. The owner's framing (verbatim)

> *"Every item routes to one board but carries visible facets — type (bug · idea · suggestion ·
> comment · correction · moderation-flag) and source/location (which server · who · which front
> door) — so it filters cleanly by type and origin. The owner board = the full firehose (all
> servers, filterable); the public bot-site shows only items explicitly promoted."*

This is **the shipped owner review inbox (`/reviews`, Phase 1 #1091) generalized**: add `type` +
`location` facets to its schema and it *is* the unified board.

## 2. The gating prerequisite (verified — do not skip)

⚠ **The shipped `/reviews` route is currently PUBLIC** (verified against `dashboard/app.py` + the
website-split `dashboard-redaction-audit.md`). It is public-safe *only* because it mirrors
already-public markdown. Generalizing it to carry **server-private facets** (who · which server ·
moderation reports) **requires moving it behind owner auth first**. The unified board must be an
**owner-gated/admin surface**, never the public route. Skipping this silently violates the
fail-closed audience model the AI-ticket layer (Q-0183) depends on. **This auth move is therefore
PR 1 of this plan, and it is owner-paced** — it shares the control-API write side + Discord-OAuth
foundation the dashboard live editors need (Q-0156 / `dashboard-live-editor-plan`).

## 3. Convergence worth keeping

The provenance you want for **filtering** (type + which server + who + which front door) is the
**same metadata the fail-closed audience guard (Q-0183) needs to never leak a server-private item
to public.** Building the filter builds the guard's input — the UX feature and the safety feature
are one feature. That is why this board is the right foundation to build *before* the AI router.

## 4. The build

### PR 1 — move `/reviews` behind owner auth (owner-paced; the gating prerequisite)
- Gate the existing `/reviews` route behind the dashboard's owner-auth (Discord OAuth, Q-0156
  foundation). Until that foundation is set up this PR cannot land — flag it on the run report.
- No schema change yet; this is purely "make the board private before it carries private data."

### PR 2 — add `type` + `location` facets to the review schema (buildable once PR 1 lands)
- Extend the `REV-NNNN` parser / store (`docs/owner/review-inbox.md` + `export_dashboard_data.py`'s
  reviews block, mirroring the bug-book parser) with two new fields:
  - **`type`**: one of `bug · idea · suggestion · comment · correction · moderation-flag`.
  - **`location`**: structured origin — `server` (guild id/name) · `who` (stranger-grade, Q-0080) ·
    `front_door` (which command/surface produced it).
- Render facet chips + **filter-by-type / filter-by-origin** on `/reviews` (the owner firehose).
- Unit test mirroring the existing bug-book parser test.

### PR 3 — promotion model (owner sees all; public sees a whitelist)
- An explicit **`promoted: true`** flag on a board item is the *only* thing the public bot-site reads
  (the website-split redaction model — owner sees all, public sees a whitelist). Default `false`.
- The public bot-site's community page reads only promoted items via the existing `site.json`
  fail-closed whitelist guard — **never** the private board route.

## 5. Out of scope (routed, not built here)

- **The AI audience classifier / ticket router** that *writes* items onto this board with a
  fail-closed audience default — Q-0183, plan-the-questions-first per the owner ("its own extensive
  session"). This plan gives that router its destination + its facet schema; it does not build it.
- **Submission moderation** (the second, fail-*open* AI gate) — same Q-0183 dedicated session.

## 6. Why this is a good next buildable lane

PR 2–3 are turn-key once the owner sets up dashboard auth (PR 1), low-risk (read/store of structured
markdown, no AI), and they **unblock** the higher-stakes AI-ticket session by giving it a defined,
correctly-gated destination. It also retires the duplication risk of a second feedback store.

→ relates [owner-review-inbox-plan](owner-review-inbox-plan-2026-06-17.md) ·
[ai-correction-report-and-ticket-service](../ideas/ai-correction-report-and-ticket-service-2026-06-19.md) ·
[per-command-feedback-threads](../ideas/per-command-feedback-threads-2026-06-19.md) ·
the website-split redaction contract · Q-0183 (AI audience routing) · Q-0169 (review inbox) ·
Q-0156 (dashboard auth) · Q-0080 (stranger-grade) · Q-0082 (spend ceiling).

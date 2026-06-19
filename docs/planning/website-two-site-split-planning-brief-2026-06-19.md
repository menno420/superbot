# Website two-site split — planning brief for the next session

> **Status:** `plan` — a **brief**, not the plan itself: it specifies the **required output** the next
> (planning) session must produce, plus the owner-decided constraints it must honor. Owner-directed
> 2026-06-19; decisions recorded in router **Q-0178**. Source code + merged PRs win. The next session
> reads this, then produces the full implementation plan + the ultracode decomposition.

## Vision

Split the single developer dashboard (`dashboard/`) into **two audience-targeted sites**:

- **Bot site (public):** for Discord users / prospective server owners. What the bot does, command
  reference, feature showcase, **bot changelog/updates**, status, and a **public form to submit
  bugs/suggestions**. Marketing + reference + intake.
- **Dev/repo site:** the *current* dashboard, repurposed. Ideas board, bug book, **repo/session
  updates**, env map, `/reviews`, control plane. For the owner + agents + curious devs.

The point is an **audience separation**: mixing bot-users and dev/ops content dilutes both. A clean
public bot site improves user onboarding; the dev dashboard stays the "engine room."

## Owner-decided constraints (Q-0178 — the next session must honor these)

| Decision | Choice |
|---|---|
| Bot site visibility / data | **Public + dynamic (hybrid:** regenerated content + a few live status widgets) |
| Public submissions | **DB intake → owner approves on the dev site → approved ones mirror to GitHub issues** (reuse the `.github/ISSUE_TEMPLATE/` shapes) |
| Dev site exposure | **All pages public read-only**; owner-gated for **edits** (existing Discord-OAuth owner auth) |
| Deployment topology | **2 Railway services** — repurpose the current `dashboard/` as the dev site; a **new** lightweight service is the bot site |

## Hard constraints / non-negotiables

1. **🔒 No secret values in the public read-only view.** "All pages public read-only" includes the env
   map and control-plane pages — these may render env-var **names** + **status** only, **never values or
   tokens**. The `CONTROL_API_TOKEN` and any credential must never reach a public response. A redaction
   audit of every dev-site page is a required deliverable (below). (Env-var *names* are already public in
   `docs/operations/env-vars.md`, so names are fine; values are the line.)
2. **Preserve the dashboard's decoupling.** Today `dashboard/` imports **no** bot code and reads generated
   JSON (`scripts/export_dashboard_data.py` → `dashboard/data/dashboard.json`). Both sites must keep this:
   surface the repo's existing structured data, **don't duplicate or rebuild functionality**.
3. **Public submission ⇒ abuse surface.** A public, no-login form is a spam/abuse vector. The plan must
   specify rate-limiting, validation, and the owner-moderation gate **before** anything is publicly shown
   or mirrored to GitHub.

## REQUIRED PLANNING OUTPUT (what the next session must deliver)

The next session produces a `docs/planning/` implementation plan containing **all** of:

1. **Page/audience allocation matrix.** Every current dashboard page → `bot` / `dev` / `both`, with
   rationale; plus the **new** bot-site pages (command reference, feature showcase, bot changelog, status,
   submission form). Use the existing **Run-type seam** (`routine` vs manual/bot badges in the updates
   feed) to split "bot updates" vs "repo updates".
2. **Architecture.** The 2-service topology; how **shared templates/assets/data** are factored (a shared
   package? a common static-data layer? duplication with a lint guard?) without re-coupling; the
   **submission flow** end-to-end (DB schema, the owner-approval UI on the dev site, the GitHub-mirror
   mechanism + token scope); the **auth boundaries** (bot site: public + submission intake; dev site:
   public read-only + owner-edit via the existing OAuth).
3. **Data / freshness design.** The hybrid model concretely: what is **regenerated** (source, cadence,
   trigger) vs the **few live widgets** (their data source — if any touches `disbot/control_api.py`, the
   security implications of a public service reading it, and the read-only/rate-limited contract).
4. **Security review.** A per-page **redaction matrix** for the public read-only dev site (what renders,
   what's stripped); the submission **abuse plan** (rate-limit, captcha/validation, moderation gate); the
   **GitHub-mirror token** scope (least-privilege, repo-scoped issues:write).
5. **Decomposition into file-disjoint build units.** The **ultracode-able** breakdown for the follow-up
   build run — each unit's exclusive file set + what it does — **with sequencing**: the *serial*
   prerequisites (e.g., factor shared data/templates first; stand up the submission DB) vs the units that
   can then parallelize (bot-site pages, dev-site public-read toggles, the moderation UI).
6. **Migration / rollout.** How to split with **no downtime** — keep the current dashboard serving the
   dev audience throughout; stand the bot site up alongside; cut over deliberately. Include a rollback.
7. **Owner decisions still open** (surface, don't guess): domains/branding for the two sites; the exact
   live-widget data source (gated on the control-API security review); the submissions DB choice
   (the bot's Postgres vs a separate store).

## Why a planning session is next (not another ultracode run)

The ungated **parallel** backlog is thin after the fleet, and this work is **design-heavy with sequential
dependencies** (factor-shared → DB → then parallelize) — a fleet would stall on the serial front half.
So the chain is: **this brief → a focused planning session (produces the plan + the ultracode
decomposition above) → an ultracode build run** on the disjoint back-half units. Plan first, then
parallelize.

## Builds on (existing — don't duplicate)

[`developer-dashboard-plan.md`](developer-dashboard-plan.md) (the current dashboard's design + the
already-envisioned public bug form + GitHub-issue mirror) · [`dashboard-live-editor-plan.md`](dashboard-live-editor-plan.md)
(owner-auth + control-API write design) · `dashboard/` (the decoupled service) · the `.github/ISSUE_TEMPLATE/`
shapes from #1064 · `docs/operations/env-vars.md` (the env-name surface).

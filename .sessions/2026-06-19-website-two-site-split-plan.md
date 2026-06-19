# 2026-06-19 — Website two-site split: the implementation plan (Q-0178)

> **Status:** `complete`

## Arc

Executed the planning session the previous PR (#1099) specified: read the
`website-two-site-split-planning-brief-2026-06-19.md` brief + router Q-0178, and produced the **full
implementation plan + file-disjoint ultracode decomposition** for splitting the single `dashboard/`
service into a public **bot site** and a repurposed **dev/repo site**. No runtime code — planning only.

## Shipped (PR #1100)

- `docs/planning/website-two-site-split-plan-2026-06-19.md` — the implementation plan, **all 7
  required deliverables** from the brief, grounded in the *actual* current dashboard:
  1. **Page/audience matrix** — every current page → bot/dev/both (+ the new bot-site pages); the
     "bot updates vs repo updates" split (a curated `docs/bot-changelog.md`, not the run-type seam,
     which classifies *how a session ran*, not user-relevance).
  2. **Architecture** — 2 Railway services; **one data producer → a minimized public `site.json`
     subset** for the bot site (redaction by construction); independent presentation, no shared Python
     import (Railway root-dir build constraint); the submission flow end-to-end (DB schema · intake ·
     owner moderation · GitHub mirror); the auth boundaries.
  3. **Data/freshness** — regenerated catalogues vs the few live widgets; the **control-API
     public-exposure gate** (the public site must never read the private control API — the dev site is
     the trusted, redacted status aggregator).
  4. **Security review** — per-page redaction matrix · public-submission abuse plan · least-privilege
     GitHub-mirror token · a **per-service secret-holding matrix** (the public site holds exactly one
     secret: an INSERT-only DB role on one table).
  5. **Decomposition** — serial foundation (S1 public subset + guard · S2 submissions DB) → parallel
     file-disjoint back half (P1–P8), with a dependency graph for the ultracode run.
  6. **Migration/rollout** — additive, no-downtime, dark-launch the bot site, per-step rollback.
  7. **Open decisions** — 6 surfaced with recommendations (domains · live-widget source · DB store ·
     control-panel placement · changelog source · captcha).
- Forward-linked the plan from the brief + `docs/current-state.md` ▶ Next action; claimed + cleared
  active-work; the idea capture (#1099) already indexes the brief.

## Context delta

- **Key grounding that changed the plan's shape:** the dev site's read pages are **already** public,
  read-only, and value-free (`/env` = names only, `/settings` = keys+specs never values, `control_client`
  never echoes the token). So "all dev pages public read-only" (Q-0178) is *largely already true* — the
  split is audience-presentation + a new intake flow over a shared data backbone, **not** a feature
  migration. This kept the decomposition small and the rollout inherently low-risk.
- **A real wording mismatch to confirm (plan §7.4):** Q-0178 says the dev site is "owner-gated for edits
  (existing Discord-OAuth owner auth)", but today's `/admin` is a **multi-user, any-guild-admin** panel
  (the bot re-checks per guild), not owner-only. Surfaced as an open decision, not guessed.
- **Discovered by hand (not in orientation):** the Railway **root-directory** build model is what scopes
  each service's deps — it both *enables* the clean 2-service split and *forbids* a naive shared Python
  package. That constraint drove the "shared data artifact, independent presentation" factoring.

## ⟲ Previous-session review (Q-0102)

**#1099 (the brief) — strong setup.** What it did well: it correctly judged this work as design-heavy
with *serial* dependencies and earned it a dedicated planning session rather than forcing an ultracode
run that would stall on the serial front half — and it captured the owner's four decisions cleanly as
router Q-0178 + a precise required-output spec, which made *this* session fast (I executed against a
crisp 7-item contract). **What it could have done better:** deliverable 1's hint — "use the Run-type seam
to split bot vs repo updates" — doesn't actually fit: `run_type` classifies *how a session ran*
(routine/manual), not whether a change is *user-relevant*; every `.sessions/` entry is dev content, so
the seam can't separate a user changelog from repo updates (a curated source is the real answer). **System
improvement:** when a brief hands the next session a *specific mechanism* as the way to do a deliverable,
it should mark it "verify this fits" rather than implying it's settled — the exact Q-0120 principle
(cross-agent output is **input to verify against source**, never an order). A brief is one input; this one
was 95% right and the 5% was a named mechanism that didn't survive contact with the source. Cheap habit,
avoids a planning session inheriting a wrong assumption.

## 💡 Session idea (Q-0089)

**Born-red commits should land the deliverable's *outline*, not just the session card.** This session hit
it live: Codex reviewed the born-red **first** commit (card + claim only, by the Q-0133 protocol) and
flagged "the plan document is missing" — a **guaranteed false-positive** every born-red planning/docs PR
will produce, costing agent cycles to triage. Fix: the born-red first commit also lands the deliverable
**stub** (the plan/doc file with its section headers + an `in-progress (drafting)` marker), so (a)
automated reviewers and parallel sessions see the intended shape immediately, (b) the "deliverable
missing" finding never fires, and (c) born-red is preserved (still held by the in-progress card).
Distinct from the existing card-*completeness* gate idea (#1099's, about session-log enders) — this is
about the **PR's primary deliverable** being visible from commit 1. Cheap, convention-only.

## 📊 Doc audit (Q-0104)

- Plan in `docs/planning/` ✓, reachable from the brief + active-work + current-state ▶ Next action ·
  `check_docs --strict` **green** (345→346 docs, ratchets intact).
- `check_current_state_ledger --strict` exits 0; it flags **#1096/#1097** only — both **newer than the
  #1094 marker** that #1098 just set, i.e. benign newest-merge lag the **#1110** reconciliation pass
  records. **Not this session's drift** (same disposition #1099's card reached; Recently-shipped ratchet
  is capped at 20 — the pass owns the trim).
- Owner decisions already in router **Q-0178** (#1099); this session adds no new owner decision (it
  *surfaces* the 6 open items in plan §7 for the owner to decide at build time).

## 📤 Run report

- **Did:** executed the #1099 planning brief → produced the full website two-site-split implementation
  plan + file-disjoint ultracode decomposition (7/7 deliverables), grounded in the real dashboard.
  · **Outcome:** shipped.
- **Shipped:** #1100 — `docs/planning/website-two-site-split-plan-2026-06-19.md` + forward links + claim.
- **Run type:** `manual`
- **⚑ Owner decisions needed:** the 6 open items surfaced in plan §7 (domains/branding · live-widget
  source — *gated on a control-API public-exposure security review* · submissions-DB store · per-server
  control-panel placement · changelog source · captcha). None block the plan; they're confirm-at-build.
- **⚑ Owner manual steps:** at build time — provision the new bot-site Railway service + the submissions
  Postgres + the env vars (per the plan's §4.4 secret-holding matrix). `none` for this docs PR.
- **⚑ Self-initiated:** `none` (owner-directed — executes the #1099 brief).
- **↪ Next:** an **ultracode build run** on the plan's §5 units — serial S1 (public `site.json` subset +
  redaction guard) + S2 (submissions DB) first, then the parallel P1–P8 back half.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1100, auto-merge on green) |
| Deliverables produced | 7/7 (the brief's required planning output) |
| Source files read to ground the plan | dashboard app/auth/control_client/ratelimit/websession · export_dashboard_data · control_api · 3 plans · issue templates |
| Owner decisions surfaced (not guessed) | 6 (plan §7) |
| CI-red rounds | 1 (born-red gate by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (born-red deliverable-outline convention) |

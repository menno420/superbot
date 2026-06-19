# 2026-06-19 — Website split: review the external research + lock the open decisions

> **Status:** `complete`

## Arc

Owner uploaded an extensive external research report (ChatGPT) on the two-site-split IA/layout and asked
me to review it, present the genuine forks as questions or decide the obvious ones myself, and review the
recent PRs. The plan (`website-two-site-split-plan-2026-06-19.md`, #1100) and router Q-0178/Q-0179 already
existed; the research turned out to be **confirmatory** (its recommended "strong audience split with
separate domains" *is* the plan), converging with the plan on 5 of 6 open decisions. So this session
**resolved the open decisions** rather than re-planning: asked the owner the two genuinely-owner-bound
forks (control-panel placement, domains), decided the rest, and recorded everything into the durable docs.

## What I did

- **Reviewed the research vs. the plan** head-to-head (6 decisions) — reported the convergence + the few
  refinements the research adds (nav model, homepage structure, command-reference table, empty/error
  states, freshness badges, privacy copy).
- **Reviewed recent PRs:** the website planning chain (#1099 brief → #1100 plan → #1102 Q-0179 routing),
  the big "ultracode fleet" (#1080–#1097: arch boundary-debt burndown + stdlib guards + procedures→skills
  + `/reviews`), and #1098 (band-#1080 reconciliation). Confirmed nothing has *built* the site yet —
  plan-ready, waiting on decisions.
- **Asked the owner two forks** (`AskUserQuestion`): per-server control-panel placement, and domains.
- **Recorded the decisions** (owner answers + the obvious ones I settled).

## Owner decisions (this session)

| Decision | Owner choice | Note |
|---|---|---|
| Control panel placement (Q-0179) | **Move to the bot site** (option 2) | Per-server mgmt is a bot-USER feature. Realized as a gated "manage my server" surface **isolated** from the secret-free public marketing pages; **gated on the control-API public-exposure security review** → lands as a security-reviewed slice *after* the first additive wave (existing panel serves until then). |
| Domains / branding | **Decide later** | No domain yet; build on Railway URLs, owner sets DNS at cutover. Non-blocking. |

Settled by me (plan + research converge — no owner attention needed): status = generated build-meta v1
(live aggregator deferred behind the security review); submissions DB = separate dashboard-owned Postgres
(INSERT-only public role); changelog = curated `docs/bot-changelog.md`; `/submit` spam = honeypot +
rate-limit v1; homepage = marketing-first; `/features` merges `/functions`+`/games`.

## Shipped (PR — this session)

- `docs/owner/maintainer-question-router.md` — **Q-0179 DECIDED** (→ bot site, option 2, with the secure
  isolated-manager realization + the security-review prerequisite); **Q-0178 still-open list resolved**
  (domains deferred · status generated-v1 · separate Postgres).
- `docs/planning/website-two-site-split-plan-2026-06-19.md` — top banner "decisions locked"; §1 matrix
  (control panel → bot/gated); §2.1 diagram note; §2.4 auth boundaries (resolved wording mismatch); §4.4
  Q-0179 secret-redistribution note; **§7 converted from "open decisions" to the locked record**; new
  **Layout & UX guidance** section folded from the owner's external research (Q-0120 — verified against the
  plan, not taken as orders).
- `docs/current-state.md` — ▶ Next action website bullet: decisions locked + the control-panel move.
- `docs/owner/active-work.md` — claim.

## Context delta

- **The research was input to *verify*, not an order (Q-0120) — and it validated the plan.** Key
  cross-check: the research's "Alternative B (recommended)" equals our plan; it rejects the unified
  single-site (C) and API-first/heavy-JS (D) — i.e. it independently confirms the cleanest path. The
  honest framing for a non-technical owner: *"your plan is good; the research confirms it, doesn't redirect
  it."*
- **The owner picked the *non-recommended* control-panel option** (move to bot site over leave-on-dev).
  That's a legitimate product call (server owners are users, not devs). The judgment I applied was on the
  **how**: moving an OAuth + control-API-writing surface to the user-facing side breaks the plan's "public
  surface holds exactly one secret" payoff *unless* the gated manager is **isolated** from the public
  marketing pages — so I recorded the destination as decided and the isolated-manager + security-review
  prerequisite as the secure realization, flagged for the owner to override if he wanted a single merged
  app.
- **Decision-unblocked, not yet built.** All six plan §7 decisions are now locked → the ultracode build
  run is unblocked. First wave stays additive/secret-free (marketing + `/submit` + moderation + mirror);
  the control-panel migration is a later security-reviewed slice.

## ⟲ Previous-session review (Q-0102)

**#1100 (the plan) — excellent, and it set this session up perfectly.** What it did well: it *grounded*
the plan against the live dashboard instead of the brief's aspiration (catching that the dev read-pages
are already public/value-free, which shrank the whole effort to "presentation + one intake flow"), and it
**surfaced the control-panel wording mismatch as Q-0179 instead of guessing** — which is exactly why this
session had a clean, real fork to put to the owner. What it could have done better: it listed all six §7
items as equally "confirm at build," when in fact four were technical-default-safe (changelog, captcha, DB,
status) and only two were genuinely owner-bound (domains, control panel) — a small **priority tag**
("owner-bound" vs "agent-default") on each open decision would have let a dispatch/owner see at a glance
which actually needed a human. **System improvement:** the plan template's "open decisions" section should
carry a per-item **decision-owner tag** (`owner` / `agent-default`) so the follow-up review session (or
Hermes) can fast-path the agent-defaults and only escalate the true forks — turns a flat list into a
triaged one. Cheap, and it's the same instinct as the sector-dispatch startability tags (▶/⛔/👤).

## 💡 Session idea (Q-0089)

**A `decision-owner` tag on planning-doc "open decisions" lists** (`owner` vs `agent-default`), plus a tiny
stdlib reporter (`scripts/check_open_decisions.py`, Q-0105 disposable) that greps `docs/planning/*` for
unresolved decisions and prints the `owner`-tagged ones as a "needs-a-human" queue. Rationale: this session
showed the value of separating the 2 owner-bound forks from the 4 agent-defaults; encoding that tag makes
every future plan's decision list self-triaging and gives the owner/Hermes a single "what's actually
waiting on me?" view across all plans. Distinct from the existing PLAN-BACKLOG-THIN guard (that counts
*buildable* slices; this counts *blocked-on-owner* ones). Dedup-checked `docs/ideas/` — no existing
open-decision-triage idea.

## 📊 Doc audit (Q-0104)

- Owner decisions recorded in their durable home (router Q-0178/Q-0179) + the plan §7 + current-state ▶.
- `check_current_state_ledger --strict` / `check_docs --strict` run at close (see run report); ledger
  flags are newer-than-#1094-marker PRs (benign newest-merge lag — the #1110 reconciliation pass owns the
  Recently-shipped trim, which is capped at 20). No older drift introduced.
- No new owner decision beyond Q-0178/Q-0179 (this session *resolves* them, doesn't add a new Q).

## 📤 Run report

- **Did:** reviewed the owner's external website-split research against the existing plan + router; reviewed
  the recent PR chain; asked the 2 owner-bound forks; decided the 4 agent-defaults; locked all 6 plan §7
  decisions + resolved Q-0179 + Q-0178's still-open list; folded the research's layout/UX guidance into the
  plan. · **Outcome:** shipped.
- **Run type:** `manual`
- **⚑ Owner decisions captured:** Q-0179 → control panel to the bot site; domains → deferred to cutover.
- **⚑ Owner manual steps:** at build time — provision the bot-site Railway service + the submissions
  Postgres + env vars (plan §4.4); **the control-panel migration needs the owner's control-API
  public-exposure security review** before it exposes editors on the user-facing side.
- **⚑ Self-initiated:** `none` (owner-directed review/decision session). Folding the external research into
  the plan + the `decision-owner`-tag idea are within-scope improvements to the same deliverable.
- **↪ Next:** the **ultracode build run** on the plan's §5 units (S1 public `site.json` subset + redaction
  guard · S2 submissions DB → parallel P1–P8), now decision-unblocked. The control-panel migration is a
  later, security-reviewed slice.

## 📊 Telemetry

| Metric | Value |
|---|---|
| Owner forks asked | 2 (control panel, domains) |
| Decisions locked | 6 (plan §7) + Q-0179 |
| Docs updated | router · plan · current-state · active-work · this log |
| New runtime code | 0 (docs/decision session) |
| New ideas contributed | 1 (`decision-owner` tag + open-decisions reporter) |

# 2026-06-23 — Consolidation findings brief + stale-claim reconciliation

> **Status:** `in-progress` — owner-directed. After a week of heavy feature-shipping the owner wants
> to step back and consolidate: document every reconciled finding (this chat's repo-grounded pass +
> ChatGPT Deep Research, both code-verified), fix all stale status claims, and stage the repo so a
> fresh session can run a full per-cog discoverability/centralization audit. PR this session,
> auto-merge armed on green (Q-0127). Owner-directed → merge immediately (Q-0191).

> **Run type:** `manual · owner-directed`

## What I'm about to do

Docs-only consolidation pass (no `disbot/` runtime). Three deliverables:

1. **A durable consolidation/discoverability audit brief** (`docs/planning/`) — the reconciled,
   code-verified findings + the audit approach (one cog / connected-group at a time; every command
   findable + buttonized; setup wizard improved; AI advisor finalized; per-cog + general settings
   centralized). This is the handoff the next-session full audit reads first.
2. **Stale-claim fixes** — the `planning/README.md` status column (reaction-roles / starboard /
   karma are shipped, not "buildable/plan-first") and the `current-state.md` hub Starboard line
   ("PR 2 in flight" → merged #1270). Plan files' own Build-progress banners are already accurate.
3. **Idea captures** for the discoverability work surfaced this session (general cog unfindable in
   help; help-tree completeness; ephemeral-panel consolidation; settings accessibility).

## Findings being documented (see the brief for full evidence)

- **Stale-status correction (code-verified):** karma (`services/karma_service.py`, migration
  `093_karma.sql`, #1332), starboard (`services/starboard_service.py`, migrations `083`/`084`,
  #1259/#1270), reaction-roles (`services/reaction_role_service.py`, migrations `078/079/081/089`)
  are **shipped**, not pending — the `planning/README.md` status column lagged.
- **AI-setup wedge nuance:** a read-only advisor seam exists (`services/setup_advisor_review.py` +
  `views/setup/sections/ai_setup.py`) but the *generative* "describe your server → staged
  SetupOperations" capability does not — a finalize target, smaller lift than first stated.
- **Discoverability (owner-reported + agent-mapped):** the general cog is unfindable from help;
  help-tree / settings-hub completeness needs an audit; rank/profile cards not yet on the card engine.

(End-of-session enders — Q-0089 idea, Q-0102 prev-session review, Q-0104 doc audit — written below at close.)

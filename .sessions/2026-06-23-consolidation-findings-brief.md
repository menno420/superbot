# 2026-06-23 — Consolidation findings brief + stale-claim reconciliation

> **Status:** `complete` — owner-directed. After a week of heavy feature-shipping the owner wants
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

## What shipped this session

- **New durable brief:** [`planning/consolidation-discoverability-audit-brief-2026-06-23.md`](../planning/consolidation-discoverability-audit-brief-2026-06-23.md)
  — the reconciled, code-verified findings + a per-cog audit rubric + first targets + open live-repro
  questions. The handoff the next-session full audit reads first.
- **Stale-claim fixes:** `planning/README.md` status column for reaction-roles (largely shipped, web
  builder remainder) · starboard (#1259/#1270 shipped) · karma (#1332 shipped, PR3 deferred); added the
  brief as the top S1 row. `current-state.md` hub line ("Starboard PR 2 in flight" → shipped) + S1 sector
  file "Next startable" now leads with the audit. Plan files' own Build-progress banners were already
  accurate — only the index lagged.
- **Verification:** all status corrections checked against source (services + migrations). `check_docs
  --strict` ✓, `check_plan_homing` ✓.

> **⚑ Self-initiated:** none of bot-feature kind. This is owner-directed docs/reconciliation work;
> within free-rein docs/orientation scope (CLAUDE.md Working agreement).

## 💡 Session idea (Q-0089)

**Per-command help-reachability guard.** The help tree + the #1297 guard home *subsystems*; the owner's
"general cog unfindable" report is really a *command-level* gap (the 7 general commands aren't
individually surfaced/buttonized). Extend the reachability guard (or `check_consistency.py`) from
"every subsystem is homed" to "every user-facing command is reachable from the help tree AND has a
button affordance," with a per-cog allowlist + warn-first graduation — turning the audit's rubric item 2
into a CI invariant so command-level discoverability can't silently regress. Genuinely worth having; it
is the checkable form of the audit's whole first goal. (Captured in the brief §6; flagged here for grooming.)

## ⟲ Previous-session review (Q-0102)

The previous session (the visual-card-engine / competitive-positioning arc, #1349/#1352) did something
genuinely strong: it ran a real competitive-research pass and captured it as durable north-star docs
*before* over-building — exactly the discipline this consolidation pass now leans on. **What it missed:**
it (and the dispatch fleet generally) kept the `planning/README.md` status column updated by hand and let
it drift three rows stale (karma/starboard/reaction-roles labeled buildable/plan-first while shipped) —
the same class as the ledger-drift guards already catch for `current-state.md`. **System improvement it
surfaces:** there is a `check_current_state_ledger.py` for the live ledger but **no equivalent guard that
a `planning/README.md` "Active" row whose plan has a `▶ BUILT`/merged banner gets flagged for
reconciliation.** A small stdlib check (plan file says SHIPPED/BUILT in its banner ⇒ its README row must
not say "buildable/plan-first") would close the exact drift class this session fixed by hand. Logged as a
grooming candidate alongside the §6 idea.

## 📋 Doc audit (Q-0104)

Is anything important from this session not yet in a durable home? No — the findings live in the brief;
the status corrections are in `planning/README.md` + `current-state.md` + the S1 sector file; the
reusable ideas are in the brief §6 + the 💡 flag above. `check_docs --strict` and `check_plan_homing`
both green. No new owner decision was made (this records prior ones), so no router entry is owed.
Reconciliation marker untouched (no merged-PR ledger change). Repo is staged for the next-session audit.

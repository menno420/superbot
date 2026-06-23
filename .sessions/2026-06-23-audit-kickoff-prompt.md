# 2026-06-23 — Append the audit kickoff prompt to the discoverability brief

> **Status:** `complete` — owner-directed follow-up to the consolidation brief (#1366/#1367): document
> the ready-to-run **Session 1** audit prompt into the brief itself so the next fresh session can start
> cleanly from the repo with no chat context. PR this session, auto-merge armed on green (Q-0127).
> Owner-directed → merge immediately (Q-0191).

> **Run type:** `manual · owner-directed`

## What I'm about to do

Append an **Appendix A — Session 1 kickoff prompt** to
`docs/planning/consolidation-discoverability-audit-brief-2026-06-23.md`: a paste-ready, self-contained
prompt for the first audit session — **help-discoverability foundation** (command-level findability +
the General/Utility exemplar + a per-command reachability guard), sequenced first because it is the
owner's stated #1 goal and produces the rubric/guard that makes the later per-cog sessions mechanical.
Plus a one-line note reconciling it with §7's debt-ranking (§7 ranks by debt; the appendix gives the
owner-prioritized *session order*). Docs-only; no `disbot/`.

## What shipped

- **Appendix A — Session 1 kickoff prompt** added to
  `docs/planning/consolidation-discoverability-audit-brief-2026-06-23.md`: the paste-ready
  help-discoverability-foundation prompt (general-cog repro + deterministic fix + per-command
  reachability guard) + Sessions 2/3 (AI panel/advisor; roles family), with a note reconciling the
  owner-prioritized session order against §7's debt ranking. `check_docs --strict` ✓, `check_plan_homing` ✓.

> **⚑ Self-initiated:** none — owner-directed docs work within free-rein orientation scope.

## 💡 Session idea (Q-0089)

**`/audit-next` dispatch helper.** The consolidation brief now carries an ordered session sequence
(Appendix A: foundation → AI panel → roles → settings → setup). A tiny stdlib helper that reads the
appendix and prints the *next un-shipped* session prompt (matching each against a "done" marker / merged
PR) would let `dispatch S1` resolve straight to the next audit slice with zero re-reading — the
audit-sequence cousin of `dispatch_menu.py`. Disposable (Q-0105). → relates `scripts/dispatch_menu.py`.

## ⟲ Previous-session review (Q-0102)

The immediately-prior work (this same chat's #1366 brief + the parallel #1367 verification) did the right
thing twice: it captured findings durably *and* a second agent independently code-verified the two
open TODOs (the #1297 guard scope, the general-cog cause) rather than trusting the first pass — exactly
the self-auditing loop the workflow wants. **What it could improve:** #1366 left the "first audit target"
only in chat, not the repo — which is why this follow-up was needed. **System improvement:** a brief that
stages a *sequence* should carry its kickoff prompt inline from the start (Appendix pattern), so the
handoff is complete without a chat round-trip. Now embodied in this brief; worth making the
`new_subsystem`/plan templates suggest an "Appendix: next-session prompt" slot for any multi-session plan.

## 📋 Doc audit (Q-0104)

Everything is in its durable home: the kickoff prompt is in the brief; status pointers (planning README,
current-state hub, S1 sector) already point at the brief from #1366. No new owner decision, no router
entry owed, reconciliation marker untouched. Both doc checks green. Repo is ready for the fresh audit.

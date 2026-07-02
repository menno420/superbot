# 2026-07-02 — Rebuild design spec: external-review revision (plain-language + verified gap-fixes)

> **Status:** `in-progress` — born-red (Q-0133). Run type: manual · owner-directed.
> Scope: docs-only revision of `docs/planning/rebuild-design-spec-2026-07-02.md` (merged #1635).

**Branch:** `claude/superbot-rebuild-design-spec-de4mh7` (restarted from `main` @ #1636 — #1635 merged).

## What I'm about to do (intentions)

The owner ran **two external GPT review sessions** over the merged design spec (the handoff §E
external-review seam) and asked me to revise where necessary; he explicitly endorses review 1's
headline point — the spec needs a **plain-language summary** for the approving (non-coder) owner.

Plan, per Q-0120 (cross-agent output = input to verify, not orders):
- **Adopt (owner-endorsed / verified true):** plain-language summary up front; a table of contents;
  a glossary; a 10-row decision quick-table; the genuinely-missing pieces review 2 found — the
  dashboard/control-surface contract (the FastAPI dashboard is real and unaddressed), pre-cutover
  operational contracts (SLOs, rate-limit budgets, DR beyond the rollback window, retention),
  importer machine-readable mismatch classes, a shadow-window compat scoreboard, canary + renderer
  kill-switch for engine blast radius, explicit non-goals (no vector store phase 1, no
  durable-execution engine, no external agent framework for the platform loop), AI session-state
  layering note, low-confidence fallback for the dense-panel sim pass.
- **Decline with reasons (recorded here + in the spec header):** moving `file:line` citations to
  footnotes (they are the Q-0120 verification substrate), splitting the doc into multiple files
  (link churn on a merged owner-gate artifact; TOC solves navigation), full normative/rationale
  separation (house planning-doc style; the *new repo's* generated docs do separate them, §7),
  a fixed "manifest budget" (the tier-3 ratchet already enforces this without an arbitrary number),
  compile-time Discord caps (already in §2.3 — review 2 missed it).

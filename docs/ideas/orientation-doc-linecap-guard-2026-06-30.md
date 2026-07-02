# Idea — enforce the read-path docs' own stated line caps (orientation-cost regrowth guard)

> **Status:** `ideas` · **Sector:** S3 (mechanism) / S4 (the docs it guards) · **Size:** S (one stdlib
> checker + a small allowlist) · **Provenance:** surfaced by the 2026-06-30 fresh-rebuild-vision audit
> (`superbot-fresh-rebuild-vision-2026-06-30.md`, finding #1) and the orientation-cost-reduction plan
> (#1586). Friction→guard (Q-0194) / enforce-don't-exhort (Q-0132).
> **Routed (2026-07-02):** absorbed into
> [`memory-retention-and-context-economy-plan-2026-07-02.md`](../planning/memory-retention-and-context-economy-plan-2026-07-02.md)
> — self-declared per-doc caps become a gauge class in its `check_retention.py` (PR 1), alongside the
> corpus-level windows/caps; the warn-first → graduate posture below carries over unchanged.

## The friction

The session-start "any task" reading order measured **~25,593 words** before a session reaches its
task-specific folio. `AGENT_ORIENTATION.md` carries an explicit **~250-line cap in its own text** yet
sits at **484 lines — 2× over — and no checker enforces it** (verified this session). PR #1586 cut the
content *once*; nothing stops it regrowing. Every read-path doc that states a budget for itself
(`AGENT_ORIENTATION` line cap, `current-state` ▶ Next-action char budget — the latter *is* gauged by
`check_docs`, the former is not) is a silent regrowth surface: the orientation cost the maintainer is
actively trying to lower creeps back up one well-meaning paragraph at a time, invisibly.

## The guard

A tiny `check_docs` extension (or a standalone `scripts/check_orientation_budget.py`) that reads each
read-path doc's **self-declared cap from its own front-matter/header** (so the cap lives in one place —
the doc — not hard-coded in the checker) and **fails CI when the doc exceeds it**. Start **warn-first**
(Q-0105 disposable-tool header), graduate to error once the #1586 cut has settled under the cap. Caps to
cover initially: `AGENT_ORIENTATION.md` (~250 lines, currently 2× over → either enforce 250 or ratchet
the cap to its post-#1586 reality and hold the line), and any other read-path doc that names a numeric
budget for itself.

## Why it's worth having

- **Makes the #1586 win durable** instead of a one-time cut that silently erodes — the exact "enforce,
  don't exhort" pattern (Q-0132) the project already trusts for ledger/cadence/session-gate drift.
- **Cheap + verifiable** (stdlib line-count vs. a declared number; output checkable against ground
  truth immediately) and **disposable** if it proves noisy.
- **Directly serves the maintainer's stated, active priority** (orientation cost is a named motivation
  in both the #1586 plan and the fresh-rebuild vision) — a guard here protects work he's currently
  investing in.

## Not in scope

Not a re-cut of the content (that's #1586's plan) and not a router-archive actuator (Q-0210, a separate
decided-but-unexecuted cleanup also flagged in the vision doc — worth its own idea). This guard only
*holds the line* once the line is drawn.

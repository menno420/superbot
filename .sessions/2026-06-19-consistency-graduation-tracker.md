# 2026-06-19 — Consistency-linter graduation tracker

> **Status:** `complete`

## Arc (what I did)

Routine dispatch, empty fire → next plan slice on the flagship consistency-linter lane. Built the
**per-rule graduation tracker** into `scripts/check_consistency.py` — executing the #1060 session idea
("a per-rule graduation-blocker line so the graduation queue is self-explaining") and the documented
"graduation prep" next step. Also cleared visible ledger drift on sight (4 lagging PRs).

## Shipped (#1062)

- **`scripts/check_consistency.py`** — `Rule` gains a real **`severity`** (graduating a rule = flip it
  `"warning"`→`"error"`; `run_checks` now stamps each finding with its rule's severity, so `--mode strict`
  fails on a graduated rule's finding with **no per-rule wiring**) and a **`graduation_blocker`** string.
  New **`--graduation`** report prints, per rule, `findings=N` + **ELIGIBLE / NOT READY / BLOCKED (by
  what) / GRADUATED**. Live output matches reality: `back_button` / `panel_base_class` /
  `select_option_truncation` = **ELIGIBLE** (0 findings); `edit_in_place` = **BLOCKED** on the AI-nav
  plan (the 17 `views/ai/` findings; #1060's plan PR 2 clears them).
- **Tests** — 6 new cases in `tests/unit/scripts/test_check_consistency.py` (eligible / not-ready /
  blocked / graduated states; severity-stamping into findings; the live `edit_in_place` blocker).
- **Docs** — graduation section of [`planning/repo-consistency-linter-plan-2026-06-17.md`](../planning/repo-consistency-linter-plan-2026-06-17.md)
  updated to describe the tracker; `current-state.md` ▶ Next action repointed.
- **Ledger drift-on-sight (Q-0166)** — added the 4 lagging entries the SessionStart guard flagged
  (#1053 recon pass · #1055/#1061 dashboard regen · #1060 AI-nav plan) to Recently-shipped;
  `check_current_state_ledger --strict` now green. (Recently-shipped is at 24/20 — a *soft* docs warning
  the #1080 reconciliation pass trims to archive; the harder ledger-checker error is cleared.)

## Continuation (the handoff)

Next ungated startable on this lane (per current-state ▶ Next action):
1. **Graduate the 3 ELIGIBLE rules** once they stay clean ~1–2 more sessions: flip `severity="error"`
   for `back_button` / `panel_base_class` / `select_option_truncation` in `RULES`, then wire
   `python3.10 scripts/check_consistency.py --mode strict` into `code-quality.yml`. The `--graduation`
   report is the readiness gate — confirm each still reads ELIGIBLE on the live tree first.
2. **AI-nav plan PR 1** ([plan](../planning/ai-panel-inplace-navigation-plan-2026-06-19.md)) to start
   clearing rule 1's 17 — needs a runtime/Q-0086 live-walk session, `needs-hermes-review`.
3. Fresh lanes: procedures→skills Batch 1, owner-review-inbox Phase 1, the small stdlib guards.

Verify: `python3.10 scripts/check_quality.py --full` (10666 passed locally) · `check_architecture
--mode strict` (clean) · `check_consistency.py --graduation`.

## Context delta

- **Pointed to and needed:** #1060's card + the linter plan made "the graduation tracker is the next
  step + rule 1 is blocked on the AI-nav plan" explicit — carried the whole slice.
- **Discovered by hand:** the two checkers' tension (ledger-checker wants recent PRs *present*;
  `check_docs` wants Recently-shipped ≤20) — the reconciliation pass resolves both (add + trim); a
  mid-band session adding lagging entries trips the soft docs ratchet by design.

## ⟲ Previous-session review (Q-0102)

The previous slice (#1060) did the right thing in *promoting* the AI-nav idea to a plan rather than
half-building a substantial UI redesign in a non-runtime session — correct gate discipline. What it
left implicit: it *recorded* the graduation-tracker idea but didn't build it, and the lane's "what's the
next contained slice?" still needed a human read of three docs. This slice closed that by building the
tracker, so the lane's state is now machine-readable. **System improvement:** the tracker pattern
(per-rule `severity` + `graduation_blocker`, surfaced by a `--graduation` flag) generalizes — any
warn-first ratchet tool (the architecture checker's known-violations, the generated-artifact freshness
umbrella) could expose the same "what blocks tightening this?" one-hop view instead of leaving it in prose.

## 💡 Session idea (Q-0089)

**A `--graduation` / readiness view for the *architecture* checker's known-violations too.**
`check_architecture.py` carries a frozen set of known layer-boundary violations (the ratchet) that
shrinks over time, but "which known violation is closest to retirement / what blocks removing it?" lives
only in prose + commit history. Mirroring this slice's tracker — annotate each known-violation entry with
a short `blocker`/`owner` note and add a `--ratchet-status` report — would make the arch debt's burn-down
self-explaining the same way. Distinct from #1060's idea (which *is* this slice); this extends the pattern
to the older, larger ratchet. Captured, not built (worth it only if the arch ratchet keeps actively
shrinking).

## 📊 Doc audit (Q-0104)

- `check_current_state_ledger --strict` → green (added the 4 lagging entries).
- `check_docs --strict` → passed (Recently-shipped 24/20 is a soft warning the #1080 pass trims).
- `check_quality --full` → 10666 passed; `check_architecture --mode strict` → clean.
- No new owner decisions. The graduation-tracker mechanism is dev tooling (Q-0105), not an owner gate.
- Plan doc + current-state ▶ Next action de-staled in the same PR.

## 📤 Run report

- **Did:** built the consistency-linter per-rule graduation tracker (the #1060 idea + documented
  graduation-prep step) + cleared 4 lagging ledger entries on sight. · **Outcome:** shipped, CI green.
- **Shipped:** #1062 — `scripts/check_consistency.py` (`severity` + `graduation_blocker` + `--graduation`)
  · 6 tests · plan-doc + current-state updates · 4 ledger entries.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** **YES** — no dispatched order named this slice; it is the next plan step on the
  Q-0170 consistency-linter lane (executing the #1060 session idea) under the Q-0172 idea→build gate.
  Contained read-only stdlib tooling; reversible.
- **↪ Next:** graduate the 3 ELIGIBLE rules after a couple more clean sessions (flip `severity` + wire
  `code-quality.yml`); or execute AI-nav plan PR 1 (runtime session) to clear rule 1.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session | 1 (#1062) |
| Tests added | 6 |
| Ledger entries reconciled on sight | 4 (#1053/#1055/#1060/#1061) |
| CI-red rounds | 1 (born-red session gate by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (`--ratchet-status` for the arch checker) |

# 2026-07-01 — Treasury completion tests (cog + modal)

> **Status:** `complete`

**Run type:** routine · dispatch (empty fire — S1 completion-first, slice 2)

## What I did

Cleared Treasury completion-cert offline punch **#1** + **#2**
(`docs/planning/feature-completion/units/treasury.md`, `◐ assessed`) — **pure test coverage, zero
runtime change**:

1. **Punch #1 — cog-level command tests** (`tests/unit/cogs/test_treasury_cog.py`, 13 cases): `!treasury`
   panel open (opener called + view keeps its message handle), `contribute` (calls the service / rejects
   non-positive before I/O), `grant` (disburse + mention-on-success / no-prefix-on-failure / rejects
   non-positive) and the **`manage_guild` authority gate** on disburse (denied without, allowed with,
   platform-owner bypass per Q-0212).
2. **Punch #2 — Contribute-modal parse tests** (`tests/unit/views/test_treasury_contribute_modal.py`,
   6 cases): `_ContributeModal.on_submit` non-int / empty / whitespace / negative / zero → ephemeral
   error with **no write**; valid (incl. large + whitespace-stripped) → `treasury_service.contribute`
   + in-place `_redraw`.

Treasury's remaining cert gaps are the owner/live ones (#3 soft-dep doc, #4 Help-nav note, #5/#6 owner
walkthrough + sign-off). `check_quality --check-only` green; targeted suite 19/19.

## 📤 Run report

- **Did:** first cog-level command + Contribute-modal test coverage for the Treasury unit (the command
  layer + modal were previously untested; only the service and Economy-hub button had coverage) ·
  **Outcome:** shipped (born-red flipped complete; CI green, auto-merge armed on #1611).
- **Shipped:** #1611 — `tests/unit/cogs/test_treasury_cog.py` (13), `tests/unit/views/test_treasury_contribute_modal.py` (6),
  Treasury cert punch #1/#2 marked done. No runtime/registry/artifact change.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none.
- **⚑ Owner manual steps:** none (test-only).
- **⚑ Self-initiated:** none — dispatched completion-first work off the S1 ▶ Next queue (Treasury cert
  punch-list); slice 2 of this dispatch run.
- **↪ Next:** Treasury cert remaining = #3 (economy soft-dep doc/test, owner) · #4 (Help-nav note, offline)
  · #5/#6 (owner live walk + sign-off). Broader S1 offline completion deepening: Community-Spotlight
  view-callback tests (punch #1/#2), Karma bespoke panel, Utility punch #5 tone polish.

## 💡 Session idea (Q-0089)

Covered by slice 1's idea (a declared-capability→real-command completion guard) — this slice surfaces a
sibling: **the completion certs' "cog-level test missing" rows are a repeatable, mechanical gap.** A small
generator that, for each `◐ assessed` unit with a `[ ] Behavior tests` / `command test missing` row,
scaffolds a `test_<unit>_cog.py` skeleton (invoke-callback + authority-predicate boilerplate) would make
punch #1-type items near-free. Noting, not building (would need a real look at how much boilerplate is
genuinely shared vs. per-cog).

## ⟲ Previous-session review (Q-0102)

Covered in slice 1's log (the fishing-churn / BUG-0030 lesson). Slice-specific note: doing slice 2 as a
**separate branch/PR** rather than stacking onto slice 1's PR (mid-auto-merge) was the right call — it
kept the born-red gate per-PR clean and avoided the #843 partial-merge race, and the two changes touch
disjoint files so there is no cross-PR conflict on the code (only the S1 ledger, which I deliberately left
to slice 1 + the reconciliation routine to avoid a second docs conflict).

## Doc audit (Q-0104)

- Treasury cert punch #1/#2 marked done + the Tests/evidence rows updated. No owner decision → no router
  entry. No ledger edit here (slice 1 owns the S1 recently-shipped entry for this run; the reconciliation
  routine folds merged PRs per the newest-merge-lag carve-out).
- `check_quality --check-only` (formatters + artifacts + consistency) green.

## 🛠 Friction → guard (Q-0194)

- No new friction. The born-red gate correctly held #1611 red until this card flipped complete (the CI
  "failure" events during the run were the gate doing its job, not a real break) — the guard worked as
  designed.

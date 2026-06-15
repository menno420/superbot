# Session: P1-1 eval-coverage expansion — FULL tool-surface coverage (27 → 34/34)

> **Status:** `complete` — night-executor continuation; born-red card flipped as the deliberate final step (Q-0133).

**Branch:** `claude/eval-coverage-full-2026-06-15` · **Date:** 2026-06-15 · **Type:** P1-1 (S1 AI eval matrix) · **Continues:** #895 (20→27) ← #886 (14→20) ← #881 (8→14)

## What this did

Completed the eval tool-surface ratchet to **34/34** — every canonical AI tool now has at least one
golden/smoke case. Added the **final 7 specialized BTD6 lookups** (the last `_ACK_UNCOVERED_TOOLS`
entries) to `tests/evals/cases.py`, each offering the real production spec and asserting the model
reaches for the RIGHT deterministic tool:

`btd6_bloon_filter` (trait-filter list) · `btd6_ct_team_status` (server CT standing) ·
`btd6_geraldo_lookup` (shop item) · `btd6_paragon_calculate` (degree-from-sacrifices) ·
`btd6_power_effect` (apply a Power to a tower stat) · `btd6_power_lookup` (consumable-Power info) ·
`btd6_relic_lookup` (CT relics by category).

`_ACK_UNCOVERED_TOOLS` is now **empty**; `_TOOL_COVERAGE_FLOOR` raised **27 → 34** (== catalogue
size), so a *new* tool added to the surface can no longer slip in uncovered — it must get a case or be
explicitly re-acknowledged. Bumped `GOLDEN_SET_VERSION` → `2026-06-15.3`.

Verified: `tests/evals/` 41/41 · coverage **34/34** (uncovered = `[]`) · offline smoke 16/16 ·
`check_quality --full` green (9698) · `check_architecture` 0 errors.

## Context delta

- Pure continuation of the #881/#886/#895 chain — turn-key. The only real work was verifying each of
  the 7 tools' *actual* spec + return shape (dumped them up front) so the user message triggers THAT
  tool, not a neighbour (e.g. `btd6_power_effect` "attack speed WHILE boosted" vs a static stat lookup;
  `btd6_bloon_filter` trait-list vs single-entity `btd6_lookup`). `btd6_paragon_calculate` returns
  `success`/`result` (not `found`) — stub shaped accordingly.
- This closes the **deterministic/offline half of P1-1's tool coverage entirely.** What remains on
  P1-1 is creds-gated (the live-quality battery) or design-for-review (absence-guard Layer B) — neither
  buildable in an offline run — so the next executor moves to **P1-3 invariants**.

## 💡 Session idea (Q-0089) — the trigger-chain reliability fix

**Route executor self-chaining through the cron/PAT workflow path, not a session-opened issue.**
Investigated (with the owner) why the routine "doesn't always start on its trigger": with the routine
ON, `ROUTINE_PAT` non-expiring, and the `continue` filter correct, the remaining cause is **the
originating actor** — an issue opened by a routine *session itself* (#887) does not re-fire a routine
(loop-prevention), while an issue opened by the independent cron workflow via `ROUTINE_PAT` (#894/#819)
does. So STEP 3's "the executor opens a `continue` issue → next run triggers" is structurally
unreliable. **Fix:** a small GitHub Action that opens the next `continue` issue with `ROUTINE_PAT` when
a session *requests* a chain (e.g. a `chain-continue` PR label or an `issues.closed` marker) — every
chaining trigger then comes from the proven external path. Captured as
`docs/ideas/executor-chain-trigger-via-workflow-2026-06-15.md`. (Not built this run — tests-only
scope; offered to the owner as the next PR.)

## ⟲ Previous-run review (Q-0102)

#895 (20→27) again left a precise card handoff naming exactly this tranche and the 7 tool names, so
this run shipped cold with zero re-derivation — the handoff discipline keeps paying off. What it (and
the whole chain) *couldn't* surface from inside the repo: the self-chaining trigger it relies on for
hand-offs is itself unreliable (the #887 finding above). That's the real systemic improvement this
run adds — the eval ratchet is now complete, but the loop that's *supposed* to drive these
continuations needs the workflow-path fix to stop depending on a self-trigger the platform blocks.

## Handoff

**AI tool-surface eval coverage is COMPLETE (34/34).** The drift guard now fails closed on any new
tool. Remaining P1-1 is **creds-gated** (live-quality battery) + **design-for-review** (absence-guard
Layer B) — both need prod-like creds, not an offline run. So the next executor's ready plan step is
**P1-3 invariants** (one parity/fence invariant per shipped P0 track that lacks one — band-#870 queue
slot 5), with the **trigger-chain workflow fix** (Q-0089 above) as a high-value root-cause alternative
the owner has flagged as a live concern.

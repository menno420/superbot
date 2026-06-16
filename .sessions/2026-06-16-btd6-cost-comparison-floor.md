# Session — AI §7.5 deterministic BTD6 cost-comparison floor

> **Status:** `complete`

## What this is

Same dispatch run as the permission-allowlist PR (#945). After shipping the owner-redirect, this is
the **routine's actual work order**: advance the plan with the next buildable slice. The `ready`
decade-queue is consumed; the live ▶ plan-first slice is **AI §7 next workflow family**. Building
**§7.5 — multi-entity comparison** at its highest-traffic, deterministic case: a **BTD6
cost-comparison floor builder**.

## Why this slice

Comparison questions ("is a 0-4-1 desperado cheaper than a 2-0-4 sniper", "compare the cost of a
5-0-0 ninja and a 0-5-0 wizard") are the **BUG-0003/0005 + BUG-0009 "wrong assembly" class**: the
model freelances/mis-ranks the arithmetic, and the value-only faithfulness guard can't catch a
mis-*ranking*. The proven fix shape (BUG-0009): the deterministic layer OWNS the labelled answer,
served as a pre-emptive floor before the model. Deterministic ⇒ ships under Q-0048 (no prod-check).

## Plan

- `btd6_data_service.compare_crosspath_costs(candidates, *, difficulty="medium")` — pure §7.5
  rank/diff primitive: price each `(tower, code)` via the existing `crosspath_cost`, rank ascending,
  return cheapest/most-expensive/spread.
- `btd6_context_service.deterministic_cost_comparison_reply(message_text)` — fires only on a
  high-precision cost-compare cue + ≥2 resolvable `(tower, code)` candidates (multi-tower scan,
  crosspath paired from the chars before each tower; base `000` if none); `None` otherwise. Appended
  to the `deterministic_btd6_list_reply` dispatcher (auto-wires the floor in `natural_language_stage`).
- Tests: crosspath compare · base-tower compare · difficulty cue · negatives (single tower /
  strategy / no cost cue / no comparison).

## Done

- `disbot/services/btd6_data_service.py` — `compare_crosspath_costs()` (the §7.5 rank/diff
  primitive; pure; fails closed to `found: False` with <2 priceable candidates) + `Sequence` import.
- `disbot/services/btd6_context_service.py` — `deterministic_cost_comparison_reply()` + the
  `_scan_towers_with_positions` / `_extract_cost_comparison_candidates` / `_format_cost_comparison`
  helpers + the cost-compare cue/verb/difficulty regexes; appended the builder to
  `deterministic_btd6_list_reply` (auto-wires the pre-emptive floor in `natural_language_stage`,
  unchanged seam).
- `tests/unit/services/test_btd6_cost_comparison.py` — 15 tests (primitive ranking/spread/equal/
  unknown-difficulty/<2-candidates; reply crosspath+base+difficulty firing; the four negatives;
  dispatcher routing). Smoke-verified live against the real dataset (Sniper 2-0-4 $9,700 < Desperado
  0-4-1 $10,020; Super 4-0-2 impop $157,440 ≫ Dart 0-2-4 $4,090).
- Carried the #944 `dispatch/SKILL.md` regen (see drive-by below); merged latest main (#945).

## Drive-by fix (bugs-first)

**Main was red** — #944 changed the dispatch skill *source* (`hermes-skills/dispatch.md`) but didn't
regenerate the committed artifact, so `test_committed_artifacts_are_fresh` failed on every branch.
Regenerated `scripts/hermes/skills/dispatch/SKILL.md` via `scripts/hermes/build_skills.py` and landed
it on the permission PR (#945, now merged) to unblock CI fleet-wide; carried here too for a green base.

## Merge gate (Q-0113 vs Q-0117)

**Self-merge on green (Q-0113), NOT `needs-hermes-review`** — revised from the born-red plan. As
*implemented* this is a **contained** slice in the exact risk class as the self-merged BUG-0009 floor
builders (#924/#926): a pure, conservative, additive deterministic reply that fails closed to `None`
and rides an existing proven seam — no new subsystem, no external egress, no mutations (unlike the
genuinely-substantial #929 security tiers / #941 image-mod that carry the label). Fully test-covered
and reversible. `check_quality --full` GREEN (9951 + 15 new) · `check_architecture --mode strict` 0
errors · mypy clean.

## Handoff — ▶ Next action

The §7.5 **cost** comparison is the first slice of the broader multi-entity comparison family. Clean
next slices on the same primitive/seam: **difficulty-cost comparison** (same tower across
difficulties), **paragon degree/resource** comparison, and **round-range** comparison (the plan's
§7.5 bullet list). Each is a new high-precision builder appended to `deterministic_btd6_list_reply`,
reusing `compare_crosspath_costs`/a sibling primitive. Also still open: BUG-0009 slice 3
(newest-towers, `data`-gated) and the `plan-first` AI families beyond §7.5.

> Session-level enders (Q-0089 idea · Q-0102 previous-session review · Q-0104 doc audit) for this
> dispatch run live in the sibling card **`.sessions/2026-06-16-routine-permission-allowlist.md`**
> (the run's first PR, #945) — not duplicated here. This card's own genuine addition: the cwd-deadlock
> recovery (worktree-agent symlink) is captured there as the Q-0089 idea, and its mypy side-effect
> (a `disbot/scripts` symlink makes `mypy disbot/` traverse `scripts/`) is a real gotcha worth the
> journal — **remove the rescue symlink before running `check_quality --full`.**

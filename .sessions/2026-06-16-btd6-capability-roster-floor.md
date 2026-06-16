# Session — BTD6 capability-roster deterministic floor (AI §7 new family)

> **Status:** `in-progress` — work underway; flips to `complete` as the final step (Q-0133).
> **Date:** 2026-06-16 · **Branch:** `claude/magical-rubin-pimgyi` · **PR:** (born-red)

## What I'm about to do

Scheduled dispatch, empty work order → advance the next plan slice. The §7.5 multi-entity
*comparison* family is COMPLETE (tower-cost #946 · difficulty-cost #950 · round-range #955 ·
paragon-cost #962); the named next is **a new AI §7 deterministic-floor family (plan-first)**.

Building the **property/capability roster** floor — "which towers can pop lead / detect camo /
pop black-white-purple?" — the BUG-0009 *wrong-assembly* class: the model assembles the roster
and can include/exclude the wrong towers, and because each tower name is grounded the value-only
faithfulness guard never catches a mis-*roster*. The authoritative deterministic answer already
exists in `services/btd6_capability_service.py` (`towers_with_capability` + `paragons_with_capability`,
both derived from the committed stats) — today it is only reachable as a *model-callable tool*
(`btd6_capability_lookup`), NOT as a pre-emptive floor. This slice fronts it as a floor.

- `services/btd6_context_service.py` — `deterministic_capability_roster_reply(message_text)`:
  high-precision detection (a capability cue + a tower/paragon discovery shape, strategy/opinion →
  defer), resolve the capability, call the existing service, format the labelled roster
  (base/unupgraded by default; an explicit "with upgrades" signal → the earliest-upgrade roster;
  a `paragon` cue → the per-paragon camo roster). Registered in `_BTD6_LIST_BUILDERS` so it rides
  the existing pre-emptive seam (`natural_language_stage` line 446) — no integration change.
- Read-only deterministic → ships under Q-0048 (no prod-check).
- Tests: `tests/unit/services/test_btd6_capability_roster.py`.

Verification: `python3.10 scripts/check_quality.py --full` + `check_architecture --mode strict`.

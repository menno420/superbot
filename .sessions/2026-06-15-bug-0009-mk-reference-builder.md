# Session — BUG-0009 slice 1: deterministic "Monkey Knowledge related to X" builder

> **Status:** `in-progress`

## What I'm about to do (born-red card, Q-0133)

Dispatch run with an empty/stale work order → took the next real plan slice. Per
`current-state.md` ▶ Next action the next ▶ startable item is **plan-first BUG-0009** (band-#900
decade queue slot 6), the OPEN AI list-assembly bug: "what are all the monkey knowledges related
to the farm" lists the whole Support MK category as farm-related (Big Traps / One More Spike /
Vigilant Sentries are Engineer / Spike Factory). Root cause: the faithfulness guard checks
**values, not claims** — every MK name is grounded, but the *grouping/labeling* is model-assembled.

This slice ships the **first** of BUG-0009's three list families — the **"MK related to <tower>"**
deterministic builder — following the proven fix shape (the deterministic layer OWNS the labeled
answer, like rosters / capabilities). Verified feasible: matching MK descriptions against a
tower's canonical name + upgrade-path names (strong) and aliases (weak, suppressed when another
tower is strongly referenced or the MK is a Power/Hero) yields a clean, correct relation (Banana
Farm → 7 genuinely-related MK; Spike Factory → 4; road-spike Powers correctly excluded).

Planned:
- `btd6_data_service.monkey_knowledge_referencing(tower)` — the pure relation (strong/weak +
  suppression), memoized per dataset version.
- `btd6_context_service.deterministic_mk_reference_reply(text)` — detect the query shape, resolve
  the tower, format the deterministic labeled reply (honest label: "reference the X or its
  upgrades"); `None` for anything that isn't a clear MK-for-tower list request.
- Pre-emptive floor wiring on the BTD6 path in `natural_language_stage` (before the model runs —
  this class *passes* the value guard, so a post-hoc floor never fires).
- Tests pinning the farm case (only the 7 genuinely-related, NOT the whole Support category) +
  conservatism (single-MK lookups / strategy questions stay out).

Remaining families (per-level item lists, newest-towers) stay OPEN in the bug book for follow-on
slices.

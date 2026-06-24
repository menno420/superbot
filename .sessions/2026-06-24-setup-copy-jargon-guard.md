# Session — 2026-06-24 · setup-copy jargon guard (PR 1a)

> **Status:** `in-progress` — born-red. Building the **banned-jargon CI guard** from the merged
> setup-wizard restructure plan (#1418) — Law 2's durable enforcement, and the slice of PR 1 that is
> independent of the still-open architectural Q-A (direct-apply lane). Contained / reversible /
> test-covered; touches no runtime behaviour. ⚑ Self-initiated (advancing the owner-directed plan).

## What I'm about to do

Add `scripts/check_setup_copy.py` (Q-0105 warn-first disposable guard, mirroring
`check_settings_reachability.py`): statically scan operator-facing strings in `disbot/views/setup/` for
the §4 banned-jargon list, report file:line:term, exit 0 in report mode / 1 in --strict. Add a
ratchet invariant test against a measured baseline (so *new* jargon fails while the existing
jargon-heavy copy is tolerated until the spine rewrite cleans it). Turns the plan's *modelled* "44
jargon hits" into a *measured* ground-truth number, and records it in the plan.

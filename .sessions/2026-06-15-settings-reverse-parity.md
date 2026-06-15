# Session — settings reverse-parity invariant (complete the declared ⇔ consumed bijection)

> **Status:** `complete`

## What I did

Second slice of the same dispatch run that shipped P1-3 (#917, merged). #917 added settings
**forward** parity — every declared `SettingSpec` has a runtime consumer. This adds the **reverse**
direction, so the settings lane is now a true **bijection** (declared ⇔ consumed). This was the
Q-0089 session idea from #917's close-out — built immediately rather than orphaned (it reuses the
same AST walk, so it was cheap and in-domain).

## What shipped (PR #918)

- `tests/unit/invariants/test_settings_declared_vs_consumed_parity.py` — a second test,
  `test_every_literal_setting_read_targets_a_declared_setting`, + a `_scan_literal_reads()` helper.
  It asserts every `resolve_value`/`resolve_setting` call with a string-literal `(subsystem, name)`
  pair targets a setting that exists in the schema registry. Closes the silent-bug class where a
  typo'd/stale read (`resolve_value(g, "welcom", "enabld", default)`) never matches a written key
  and resolves to the **fallback forever** — invisible, uncaught today. Holds: **0 violations**
  across 48 literal reads. Verified to fire on an injected stray read.
- **Verified:** `check_quality --full` green (9811); arch 0; the guard fires on a violation.

## Handoff / next

- Settings parity is now a complete bijection (no dead declarations · no stray reads). The
  remaining next ▶ startable plan work is unchanged from #917's handoff: the **safety quick-win**
  (welcome phase 2 PIL cards — but note that needs *visual design* input, the owner's domain, so
  it's design-first not turn-key) · **plan-first BUG-0009** (AI §7 list-builders) · the
  creds/review-blocked P1-1 remainder (Layer B · live battery).
- **Still-open pre-existing ledger drift** (from #917's handoff, NOT addressed here): 9 PRs
  #902–#916 absent from the living ledger; the #930 reconciliation pass's job.

## ⟲ Previous-session review (Q-0102)

Previous run = #917 (P1-3 invariants), this run's own first slice. It did the P1-3 disposition
honestly — it resisted shipping a *brittle* BTD6 provenance guard (an AST docstring-marker scan) and
instead recorded it as a design-for-review residual, which is the right call under the repo's
"verifiable, not a temporary patch" bar. What it could have done better: it *contributed* the
reverse-parity idea (Q-0089) but stopped at the idea — this slice closes that gap by building it
same-run, which is the better pattern (an idea you can cheaply build now beats an idea filed for
later). **System note:** this validates the dispatch routine's "2–3 slices, never just after one PR"
bias — the second slice here cost little and turned a one-directional check into a full invariant,
exactly the compounding the multi-slice rule is for.

## 💡 Session idea (Q-0089)

Covered by the build itself — this slice *is* the Q-0089 idea from #917 promoted to shipped code, so
contributing a fresh forced idea here would be ceremony (the standing bar: genuine generation, not
filler). The honest forward note instead: the **same bijection pattern is worth auditing across the
other registry-backed lanes** — the AI tool catalogue already has it (declared == consumed, praised
in the P1-3 disposition); the *bindings* and *resource-provisioning* registries may have the same
one-directional gap settings just had (a declared binding nothing reads, or a binding read that
isn't declared). A future P1-3-style pass could run the same forward/reverse parity over those two
registries. Recorded for the next reconcile; not built here (out of this slice's scope).

# Session — extension-taxonomy crosswalk (Q-0151c, owner-approved)

> **Status:** `in-progress` — born-red per Q-0133; flips to `complete` as the final step.
> **Date:** 2026-06-16 · **Branch:** `claude/hopeful-meitner-772pv8`

## What I'm about to do

Follow-on to PR #957 (architecture-atlas review). The owner **approved my Q-0151 recommendations**:
build the extension-taxonomy crosswalk CI-enforced; thin atlas as a companion (sequenced); README
optional. Scope chosen with the owner: **crosswalk now, plan the atlas**; overlay in
`architecture_rules/` + a CI guard (not a registry schema bump).

Plan:
1. `architecture_rules/extension_roles.yaml` — curated editorial overlay classifying **all 43**
   extensions by role (product / hub / shared-platform / maintenance / adapter / bootstrap /
   specialized-surface / lab) + the backing subsystem for the 10 non-1:1 ones.
2. `scripts/extension_crosswalk.py` — read-only generator (AST-parses `config.INITIAL_EXTENSIONS` +
   `subsystem_registry.SUBSYSTEMS`, joins the overlay), `--write` regenerates the doc, `--check`
   enforces (every extension classified · overlay↔source consistency · doc not stale).
3. `docs/extension-taxonomy-crosswalk.md` — generated, committed, NOT-SOURCE-OF-TRUTH + provenance.
4. `tests/unit/scripts/test_extension_crosswalk.py` — pins the `--check` invariants (this is the CI
   enforcement seam — rides the existing suite, no workflow edit).
5. `docs/planning/extension-taxonomy-crosswalk-plan-2026-06-16.md` — the plan (crosswalk done + atlas
   sequenced as PR 2, with the overlay-over-registry rationale + the now-answered Q-0151).
6. Housekeeping: record the owner's Q-0151 answer; fix my own **32→33 / ~11→10** count error in the
   #957 capture doc + README (the exact count-drift class this work exists to kill); roadmap horizon.

Verified live: **43** extensions · **33** subsystem keys · **exactly 10** non-1:1.

(Close-out enders added before the flip.)

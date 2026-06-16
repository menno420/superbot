# Session — extension-taxonomy crosswalk (Q-0151c, owner-approved)

> **Status:** `complete` — shipped; PR #958 ready, auto-merge on green.
> **Date:** 2026-06-16 · **Branch:** `claude/hopeful-meitner-772pv8` · **PR:** #958

## What I did

Built the extension-type taxonomy crosswalk (the strongest idea from the #957 architecture-atlas
review), CI-enforced via a curated overlay + guard (owner-approved Q-0151c — overlay, **not** a
registry schema bump). Live-verified counts: **43** extensions · **33** subsystems · **10** non-1:1.

- `architecture_rules/extension_roles.yaml` — all 43 classified into 8 roles.
- `scripts/extension_crosswalk.py` — AST generator (`--write`/`--check`/preview); no imports/env.
- `docs/architecture/extension-taxonomy-crosswalk.md` — generated, committed (`NOT SOURCE OF TRUTH`).
- `tests/unit/scripts/test_extension_crosswalk.py` — the CI enforcement seam (5 tests) + proves the
  guard catches an unclassified extension / bad `backs`.
- `docs/planning/extension-taxonomy-crosswalk-plan-2026-06-16.md` — plan; sequences the thin atlas (PR 2).
- Recorded the owner's **Q-0151** answer; **fixed my own 32→33 / ~11→10 count error** in the #957
  capture doc + README + Q-0151c; roadmap S4 entry.

Verified: `check_quality --full` (10032 passed) · `extension_crosswalk --check` ✓ · `check_docs --strict` ✓.

## Context delta (for the next session)
- The crosswalk + its `role`/`backs` data is the **dependency for the thin atlas (PR 2, Q-0151a)** —
  build that by *composing* `context_map`/`wiring_map`/`review_scope` + this overlay, CI-`--check`,
  body not committed.
- Generated docs go in a **subdir** (`docs/architecture/`), not top-level `docs/` — the top-level
  ratchet (`check_docs`) reserves that pile for true nav docs (hit this live this session).

## What I was about to do

(superseded by "What I did" above — kept for the born-red audit trail)

## Plan (executed)

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

## Session enders

**Grooming (Q-0015).** This session *executed* the #1 routed idea from PR #957 (taxonomy crosswalk:
captured/routed → shipped) and sequenced the thin atlas (PR 2) onto roadmap S4 Next. Backlog moved
forward, not just browsed.

**💡 Session idea (Q-0089).** Surface the new `role`/`backs` data **inside `context_map.py`'s per-file
output** — when an agent maps a cog file before editing, show its extension role + backing subsystem
from `architecture_rules/extension_roles.yaml`. That makes the taxonomy *load-bearing* (consumed by the
tool agents actually run pre-edit) instead of a static doc, and is a concrete down-payment on the
atlas (PR 2), since `context_map` is one of its composers. Dedup: the atlas plan mentions composing
`context_map`, but surfacing `role` *in* its output is a smaller, independent enhancement worth doing
even if the atlas slips. Small; record-only here.

**⟲ Previous-session review (Q-0102).** Reviewing my own PR #957 (the architecture-atlas capture): the
cross-checking discipline was the right call — it verified the review against source rather than
echoing it and caught the root-README contradiction. **But it shipped a count error** ("32 subsystems
/ ~11 non-1:1"; live is 33/10) — ironic in a PR *about* count-drift. Root cause: I trusted a
sub-agent's numeric tally without re-deriving it from source before writing it into a doc. *System
improvement (applied this session):* a sub-agent's count is unverified tool output (Q-0105 tier) —
derive a number from source in-session before pinning it, **or** don't pin a raw number. This
session's crosswalk is the durable fix: the count is now generated and self-correcting, and the stale
"32" is corrected at every home.

**Doc audit (Q-0104).** All this session's outputs are in durable homes and reachable
(`check_docs --strict` ✓): crosswalk doc + overlay + script + test + plan; Q-0151 answer recorded;
the count error fixed in the capture doc, README, and Q-0151c; roadmap S4 updated. Unchanged
pre-existing item (not in scope, per Q-0124): the recently-merged-PR ledger lag is owned by the
auto-reconciliation routine at #960, not a manual session.

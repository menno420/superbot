# Idea — new-subsystem follow-up backlog auto-tracker

> **Status:** `ideas` — workflow idea raised by the band-#1350 reconciliation pass (2026-06-23, Q-0089).
> Lane: S4 docs-system / S3 tooling. Size: small. Gate: none (docs + a stdlib checker).

## The observation

The band-#1350 pass stood up **four** brand-new subsystems in a single arc — an idle **farm** (#1328),
**Karma** reputation (#1332), a **Casino** table-framework + Texas Hold'em (#1333), and a server-owned
**Treasury** coin pool (#1334). Each shipped with obvious follow-up depth (more casino games, karma
leaderboards, treasury sinks/payouts, farm upgrades), but that depth lives only in scattered session-card
prose and the reconciliation pass's §4 next-band queue. Between bands it is easy to lose — which is exactly
why the §4 queue keeps over-indexing on long-horizon *aspirational* runtime initiatives instead of the
**real, buildable depth the bands just produced.**

## The idea

Make "a new subsystem shipped" produce a **self-maintaining follow-up backlog**:

1. **Convention:** `scripts/new_subsystem.py` writes a `## Follow-ups` stub into each new subsystem's
   folio (`docs/subsystems/*.md`) at creation — a short, owner-readable list seeded from the build session.
2. **Checker (disposable, Q-0105):** a stdlib `scripts/check_subsystem_followups.py` that lists each
   subsystem folio's open follow-ups, so the dispatch + reconciliation routines can *pull* a buildable
   slice from real shipped depth rather than re-deriving it from prose every band.
3. **Reconciliation tie-in:** the Q-0107 §4 next-band queue aggregates these follow-ups first, so the
   plannable backlog is fed from what actually shipped — complementing the band-#1320 **band-queue
   hit-rate metric** idea (which *measures* the prediction gap; this one *narrows* it).

## Why it's worth having

- Turns four (and counting) new subsystems' depth into a tracked, dispatchable queue instead of orphaned
  intentions — directly addresses the "buffer becomes the band, the plan is ignored" pattern every recent
  pass logs.
- Cheap: a stub-writer in an existing script + one read-only checker. No runtime surface.
- Dedup-checked `docs/ideas/`: distinct from `band-queue-hit-rate-metric-2026-06-22.md` (that measures hit
  rate; this generates the buildable follow-up backlog) and from `reconcile-open-pr-staleness-classifier`
  (open-PR disposition, not planning intake).

## Disposability note

If the `## Follow-ups` convention proves to drift faster than it helps (stubs go stale, no one prunes them),
delete the checker and the stub-writer — it is a convenience guard, not load-bearing.

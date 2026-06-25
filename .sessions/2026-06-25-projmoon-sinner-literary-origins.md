# Session — 2026-06-25 · Project Moon — Limbus Sinner literary origins

> **Status:** `in-progress` — born-red card (Q-0133). Run type: routine · dispatch.

## What I'm about to do

Empty-fire dispatch → advance the S1 ▶ Project Moon program. PR 1 (#1453) shipped the standalone Limbus
knowledge domain, but each of the 12 Sinners carries only a generic description ("one of the twelve fixed
roster Sinners"). This run adds the **defining structural/lore fact** for each Sinner — its **canonical
literary origin** (the work + author each Limbus Sinner is drawn from, e.g. Faust → Goethe, Outis →
Homer's *Odyssey*, Gregor → Kafka's *Metamorphosis*) — as a provenanced `literary_origin` field, surfaced
in the browse detail card + a new "Origins" cross-reference view.

Offline, read-only, no DB / no AI hot-path change (the gated AI grounding path stays PR 2). Advances the
program's "browsable structured lookups + lore" goal.

## Verification
- (pending) `check_quality.py --full` GREEN · `check_architecture --mode strict` exit 0.

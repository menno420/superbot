# 2026-07-13 — EAP final-night ORDER delivery (fleet-manager dispatch)

> **Status:** `complete`
> **Branch:** `claude/eap-night-order` · **PR:** #2090
> **📊 Model:** fable-5 · **Run type:** routine · dispatch
> **Venue:** fleet-manager coordinator dispatch worker, remote container

Intent: deliver the EAP final-night ORDER into the inbox, relay from fm ORDER 045 —
append ONE ORDER to `control/inbox.md` carrying the owner-directed final-night
worklist for the superbot hub seat (docs/control only, no runtime code).

## What changed

- **`control/inbox.md` — ORDER 004 (append-only, next free number):** the EAP
  final-night worklist for the superbot hub seat, relayed verbatim from the Fleet
  Manager fan-out (owner directive 2026-07-13 ~21:34Z, fm ORDER 045). Citations:
  fm `control/inbox.md @ ca1ce28` · fm `docs/eap-final-night-worklists-2026-07-13.md
  @ ca1ce28` (landed via fm PR #178). Eight worklist items + the blocked list, tags
  as in the worklists doc.
- **`telemetry/model-usage.jsonl`:** one row for this session (fable-5, docs-only),
  mirroring the PR #2087 delivery shape.

## 💡 Session idea (Q-0089)

The inbox header could carry a `next: 005` line bumped by each append so parallel
relay sessions can't collide on an ORDER number (same idea the #2087 card raised —
still unbuilt, and this session again had to scan all headers for max+1).

## ⟲ Previous-session review (Q-0102)

The #2087 I1b relay session was a clean template for this delivery — its card,
telemetry row, and ORDER grammar transplanted directly. Improvement it surfaces:
its "next free number" note (duplicate ORDER 002 blocks are status annotations,
not collisions) saved this session a wrong-number append; that convention note
belongs in the inbox header itself rather than a past session card.

## 📤 Run report

- **Did:** appended ORDER 004 (EAP final-night worklist, fm ORDER 045 relay) to `control/inbox.md` · **Outcome:** shipped
- **Shipped:** #2090 — control intake append + session bookkeeping (docs-only)
- **Run type:** `routine · dispatch` (fleet-manager coordinator dispatch)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none — dispatched relay
- **↪ Next:** next hub-touching session consumes ORDER 004 (work the list top-down across tonight's wakes; item 1 = consume ORDER 003, not skip it)

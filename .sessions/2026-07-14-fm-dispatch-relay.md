# 2026-07-14 — Fleet-manager relay: supersession-pointer ORDER (dispatch)

> **Status:** `complete`
> **Branch:** `claude/fm-dispatch-0409z` · **PR:** TBD
> **📊 Model:** fable-5 · **Run type:** routine · dispatch
> **Venue:** fleet-manager coordinator dispatch worker, remote container

Intent: relay fm dispatch-log rows 1–2 as an inbox ORDER — append ONE ORDER to
`control/inbox.md` directing supersession pointers on three superseded superbot
docs (trigger-health order + two fleet planning docs) toward their living
fleet-manager counterparts. Control-only intake: session card + telemetry row +
the inbox append, no code, no doc edits beyond the ceremony files.

## What changed

- **`control/inbox.md` — ORDER 005 (append-only, next free number):** directs the
  next hub-touching session to add supersession pointers to three superseded docs —
  `docs/owner/trigger-health-order-2026-07-12.md` → fm `docs/trigger-health-spec.md`,
  and `docs/planning/fleet-centralization-plan-2026-07-11.md` +
  `docs/planning/fleet-review-2026-07-11.md` → fm
  `docs/planning/2026-07-14-central-docs-plan.md`. Provenance: relayed by the Fleet
  Manager seat, coordinator dispatch 2026-07-14, fm docs/dispatch-log.md @ 780c81b.
  Premise-checked (Q-0120): none of the three files carries the pointer yet, and no
  existing inbox ORDER covers this.
- **`telemetry/model-usage.jsonl`:** one row for this session (fable-5, docs-only),
  mirroring the #2087/#2090 delivery shape.

## 💡 Session idea (Q-0089)

Same gap as the #2087 and #2090 cards, third occurrence now: the inbox header should
carry a `next: <nnn>` counter bumped on each append — three consecutive relay
sessions have each had to scan the full thread for max+1. Third strike suggests the
next hub session should just build it (one header line + a check in the intake path).

## ⟲ Previous-session review (Q-0102)

The #2090 EAP-night ORDER delivery was a faithful verbatim relay with clean
citations; its card was the direct template here. Improvement it surfaces: its own
idea (the `next:` counter) went unbuilt again — relay sessions are rails-bound
(control-only), so ideas they raise need a consumer; routing them into the inbox as
a one-line rider on the next ORDER would close that loop.

## 📤 Run report

- **Did:** appended ORDER 005 (supersession-pointer directive for three superseded fleet docs) to `control/inbox.md` · **Outcome:** shipped
- **Shipped:** control intake append + session bookkeeping (docs-only)
- **Run type:** `routine · dispatch` (fleet-manager coordinator dispatch)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none — dispatched relay
- **↪ Next:** next hub-touching session consumes ORDER 005 (three supersession pointers; done-when = all three files on main carry the pointer)

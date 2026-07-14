# 2026-07-14 — Fleet-manager relay: EAP final-day closeout ORDER (dispatch)

> **Status:** `complete`
> **Branch:** `claude/eap-final-closeout` · **PR:** TBD
> **📊 Model:** fable-5 · **Run type:** routine · dispatch
> **Venue:** fleet-manager coordinator dispatch worker, remote container

Intent: relay the EAP final-day closeout directive as an inbox ORDER — append ONE
ORDER (006, next free number) to `control/inbox.md` directing the next hub-touching
session to finish-or-park-cited every open item (ORDERs 003/004/005 close-outs +
night-worklist items 4–8) and land the EAP closeout walkthrough doc
(`docs/eap-closeout-walkthrough-2026-07-14.md`, verified absent at `6e761c7`).
Control-only intake: session card + telemetry row + the inbox append, no code, no
doc edits beyond the ceremony files.

## What changed

- **`control/inbox.md` — ORDER 006 (append-only, next free number):** the EAP
  final-day closeout directive. (a) FINISH — complete-or-park-cited the open set:
  ORDER 003 doc-annotation lane (unconsumed, `status: new` at `6e761c7`), ORDER 005
  three supersession stubs (verified absent at `6e761c7`), ORDER 004 ack + heartbeat
  re-stamp (`control/status.md` `updated: 2026-07-13T18:00:00Z`, ~15 h stale), and
  night-worklist items 4–8 (recon-consistency guard · casino trio V022/V025/V029 ·
  BTD6 slice · S4 trim ratchet · S2 counter lists) — prioritized by value, honest
  parks with citations. (b) WALKTHROUGH — land
  `docs/eap-closeout-walkthrough-2026-07-14.md` (sections A–E incl. the OWNER
  ACTIONS checklist with bolded recommendations + VERIFY steps) and surface a ≤40-line
  close-out summary. Provenance: relayed by the Fleet Manager seat per owner
  directive, coordinator dispatch 2026-07-14; fm PR #193 carries the dispatch log.
  Premise-checked (Q-0120): all cited states re-verified against `origin/main` @
  `6e761c7` before the append; no existing inbox ORDER covers the closeout.
- **`telemetry/model-usage.jsonl`:** one row for this session (fable-5, docs-only),
  mirroring the #2094 delivery shape.

## 💡 Session idea (Q-0089)

The `next:` counter idea has now been raised by three consecutive relay cards
(#2087/#2090/#2094) and is still unbuilt — graduate it into an enforced check
instead of a header convention: a tiny `scripts/check_inbox_orders.py` that parses
`control/inbox.md`, prints the open-ORDER set + the next free number, and fails on
a duplicate ORDER number. It serves relay sessions (max+1 scan), hub sessions (the
open set ORDER 006 had to reconstruct from a full-thread read), and turns the
thrice-raised exhortation into a guard ("enforce, don't exhort", Q-0132).

## ⟲ Previous-session review (Q-0102)

The #2094 relay was a clean, premise-checked append and its card was the direct
template here. What it surfaces: ORDERs 003/004/005 all still sat `status: new`
~5+ hours later — on a hub with no standing seat (Q-0264), inbox ORDERs have no
consumption trigger, so they accumulate until a closeout sweep like this one has
to bundle them. Improvement: the hub needs a wake path for order consumption (a
poke-only routine or an fm-side nudge when unconsumed ORDERs age past a threshold),
not just append-side ceremony.

## 📤 Run report

- **Did:** appended ORDER 006 (EAP final-day closeout: finish-or-park-cited the open set + land the closeout walkthrough) to `control/inbox.md` · **Outcome:** shipped
- **Shipped:** control intake append + session bookkeeping (docs-only)
- **Run type:** `routine · dispatch` (fleet-manager coordinator dispatch)
- **⚑ Owner decisions needed:** none new — existing owner-side parks are cited inside ORDER 006 (mineverse #2058/#2061 flips, email-3 send, ORDER 003 console click, WP/DROP ratifications)
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none — dispatched relay
- **↪ Next:** next hub-touching session consumes ORDER 006 (done-when = every (a) item terminal or parked-with-citation + the walkthrough doc on main + the OWNER ACTIONS checklist surfaced in the close-out report)

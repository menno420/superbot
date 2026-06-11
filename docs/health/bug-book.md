# Bug book — live-reported bugs, root causes, and their fixes

> **Status:** `living-ledger` — the durable intake for bugs observed in
> production/live use (founded 2026-06-11 at the owner's request, during the
> first live-user bug report). **Convention:** one numbered entry per bug —
> verbatim symptom, expected behavior, root cause (filled at fix time), fix PR,
> status. Newest first. A bug here jumps the queue per the CLAUDE.md
> "bugs first, durably" rule: root cause over symptom-patch, one source of
> truth, a regression test named in the entry. Owner-reported inconsistencies
> he hasn't formalized yet (see current-state 2026-06-10 standing invite) land
> here as they surface.

## BUG-0001 — Round-cash question misrouted to the no-data denial

- **Reported:** 2026-06-11 01:53 (owner screenshot of live server; reporter:
  member `tposergaming`)
- **Surface:** AI natural-language → BTD6 round-cash workflow (#634, Q-0043
  inclusive ranges)
- **Symptom (verbatim):** user asked "@SuperBot lets say i have 8094$ at
  round 60, what is the cash that i will get by going to round 68" → bot
  replied "I don't have verified BTD6 data to answer that for the current
  game version (55.1). I won't state names or numbers I can't ground in my
  data — try asking about a specific tower, hero, or paragon."
- **Expected:** route to the round-cash plan→execute→verify workflow
  (a simpler phrasing passed the owner's live eval — checklist Tier 1.1);
  compute the inclusive range sum, ideally honoring the stated starting
  balance (8094 + range), and answer with evidence.
- **Root cause:** _diagnosis in progress (background agent, 2026-06-11)_
- **Fix:** _pending_
- **Regression test:** _pending — must include the production phrasing
  verbatim_
- **Status:** OPEN — diagnosing

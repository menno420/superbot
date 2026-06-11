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
- **Root cause:** two stacked gaps in
  `disbot/services/ai_round_cash_workflow.py`: (1) all three range patterns
  required the connector immediately after the first round number — anchors
  separated by a clause ("at round 60, … by going to round 68") never
  matched, so the workflow stayed out and the (correct) number-guard then
  blocked the model's ungrounded arithmetic → refusal floor; (2) the plan had
  no starting-balance concept, so even a matched range couldn't ground the
  "+8094" total (and the `$`-postfix amount form "8094$" wasn't parsed). The
  workflow's "a missed match costs nothing" design assumption is false for
  arithmetic questions — the normal path *cannot* answer them by design.
- **Fix (PR #694):** a fourth, still-conservative range pattern (both anchors
  must carry the literal word "round", within one sentence / ≤80 chars; cash
  keyword gate unchanged) + `starting_balance` on the plan (ownership-cue
  gated, round-spans masked before amount extraction) + deterministic
  `projected_total = balance + range_cash` in the evidence/result text (so
  every figure the model may state is in the grounding haystack) + postfix-`$`
  amount support.
- **Regression test:** `test_plan_separated_anchors_production_phrasing_bug_0001`
  + `test_range_answer_projects_stated_starting_balance_bug_0001`
  (`tests/unit/services/test_ai_round_cash_workflow.py`, production phrasing
  verbatim) · live-battery case `knowledge.btd6_round_cash_balance_bug_0001`
  (`tests/evals/cases.py`) · conservatism pins (no-cash-keyword and
  cross-sentence anchors stay out).
- **Deploy note:** the workflow only engages on the `btd6_grounded(:strict)`
  orchestration profiles — the reporting channel must keep that profile (the
  owner's eval walk set it during Tier 1.2). On the default profile this
  question refuses *by design*.
- **Status:** FIXED — merged via PR #694 (auto-deploys on merge)

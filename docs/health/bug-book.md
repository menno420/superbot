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

## BUG-0004 — r-shorthand round projection answered with the wrong total (cumulative-from-round-1 mislabel)

- **Reported:** 2026-06-11 ~12:39 (owner screenshot, #general — post-#703
  deploy; the owner flagged it as "probably fixed *if* those numbers are
  correct" — they were not)
- **Surface:** AI natural-language → BTD6 round-cash routing + workflow matcher
- **Symptom (verbatim):** "How much do I have on r70 if I had 26932 at the
  end of r53" → "At the end of round 70, you would have a total of
  **$71,315.20**" (plus a correct $29,386.70 rounds-54-70 breakdown).
  $71,315.20 is the cumulative from **round 1** through 70 — not the user's
  scenario. Truth: 26,932 + 29,386.70 = **$56,318.70**.
- **Root cause (four stacked gaps):** (1) every workflow range pattern
  demanded the literal word "round" — the r-shorthand anchors ("r70",
  "r53") matched nothing, so the deterministic workflow stayed out; (2) the
  router had no r-form cue either, so the message routed
  `general.nl_answer` — the model called the round tools itself and the
  general path checks names only, so each number was individually grounded
  (cumulative(70), range(54,70), round 53) while the **assembly** was wrong
  — the faithfulness guard checks values, not claims (the BUG-0002 mislabel
  class again); (3) "at the END of r53" semantics didn't exist — even a
  match would have double-counted round 53; (4) "if I **had**" wasn't a
  balance cue (only have/got/hold).
- **Fix (this PR):** one shared round-token vocabulary (`round 53` / `r53` /
  `r 53`, digit-boundary-guarded so "r2d2" stays out) across all range/afford
  anchors; a completion-cue start shift ("end of/after/finished/cleared
  round N" on the range's lower round → start N+1, no-op on the upper) with
  an explicit assumption line; had/held/started-with balance cues; r-form
  round masking before amount extraction; and a conservative router leg —
  two r-round tokens, or one plus a money cue, route `btd6.answer` (arming
  the number guard). The default-profile workflow (#703) then owns the
  projection: $56,318.70, deterministic.
- **Regression tests:**
  `test_plan_r_shorthand_with_completed_round_production_phrasing` ·
  `test_run_completed_round_projection_counts_from_next_round` ·
  `test_completed_cue_on_upper_round_is_a_no_op` ·
  `test_r_token_requires_digit_boundary` ·
  `test_r_shorthand_round_questions_route_to_btd6_answer` (+ the
  over-route negatives) · live-battery
  `knowledge.btd6_round_cash_r_shorthand_bug_0004`.
- **Status:** FIXED — this PR

## BUG-0003 — "despos" hallucinated as Plasma Monkey Fan Club (unguarded general path)

- **Reported:** 2026-06-11 ~10:32 (owner screenshot, #general)
- **Surface:** AI natural-language → BTD6 routing + grounding
- **Symptom (verbatim):** "@SuperBot how much do 10 041 despos cost on impop"
  → "A single Plasma Monkey Fan Club (Despo) costs $54,000 on Impoppable.
  For 10,041 Despos: 10,041 × $54,000 = $542,214,000 (542.2 million)."
- **Expected (owner-corrected 2026-06-11):** "despo" is community shorthand
  for the **Desperado** tower, and "10 041" is **quantity + crosspath** —
  *ten 0-4-1 Desperados* (the standard community phrasing), not the number
  10,041. Correct answer: $12,025 per 0-4-1 Desperado on Impoppable,
  $120,250 for the ten — or an honest refusal if unresolvable. Never a
  confident wrong entity.
- **Root cause (four stacked gaps):** (1) the task router had no cue for the
  message — "impop"/"despos" matched no keyword and no entity alias — so it
  routed `general.nl_answer`, where the model answers from memory; (2) the
  dataset's Desperado aliases (`des`, `cowboy`, `gunslinger`) lacked `despo`,
  and the resolver's single-word alias matching had no plural fold, so even
  `despo` would have missed the token "despos"; (3) grounding had **no
  pricing leg for the `<quantity> <crosspath> <tower>` family** — the
  crosspath regex fed only a *stats* line, no cost — and the faithfulness
  guard (rightly) blocks any sum the model derives, so the question was
  unanswerable on every path; (4) on the general path numbers are never
  guarded (by design) — the wrong-entity answer shipped.
- **Fix (this PR):** `impop` + `despo` joined the curated BTD6 keywords
  (substring match covers "impoppable"/"despos"); `despo` added as a
  Desperado alias in towers.json; the resolver's single-word alias matching
  gained a conservative plural fold (`alias + "s"`); boss canonicals joined
  the router's entity set (see BUG-0002). **The pricing leg:**
  `btd6_data_service.crosspath_cost(tower, code, quantity=…)` computes the
  full per-difficulty cost of any legal upgrade state (each purchase rounded
  to $5, then summed — the same rule as `cumulative_upgrade_costs`), and
  grounding emits a `[btd6_pricing]` line for every named crosspath with the
  preceding quantity parsed (digits or word numbers: "10 041 despos",
  "five 0-2-4 dart monkeys"); a bare "N <tower>s" grounds the base-tower
  bulk line. `btd6_cumulative_cost` gained `crosspath`/`quantity` params and
  `btd6_difficulty_cost` a `quantity` param for the tool lane.
- **Regression tests:** `test_boss_and_shorthand_questions_route_to_btd6_answer`
  (router) · `test_resolves_single_word_alias_plural` (resolver) ·
  `test_crosspath_cost_*` (service math) · `test_pricing_line_*` (grounding,
  verbatim phrasing) · `test_btd6_cumulative_cost_crosspath_quantity` +
  `test_btd6_difficulty_cost_quantity_grounds_bulk_totals` (tools) ·
  live-battery `knowledge.btd6_despo_bulk_cost_bug_0003`.
- **Deploy note:** the alias lives in towers.json — prod serves it only after
  `!btd6ops seed-data` (postgres blob lane).
- **Status:** FIXED — this PR

## BUG-0002 — Elite boss HP answered with the Standard table labeled "Elite"

- **Reported:** 2026-06-11 ~10:34 (owner screenshot, #general; the answer even
  drew a 🔥 reaction — confident wrong numbers read as authoritative)
- **Surface:** AI natural-language → BTD6 routing + boss dataset
- **Symptom (verbatim):** "@SuperBot what is the hp of elite lych per tier" →
  "Elite Lych health per tier: Tier 1: 14,000 … Tier 5: 2,100,000" — those
  are the **Standard** Lych figures. Elite Lych is 30,000 / 180,000 /
  1,100,000 / 4,800,000 / 24,000,000 (2-11× higher).
- **Root cause (two stacked gaps):** (1) boss names were not router entities
  and no keyword matched, so the question routed `general.nl_answer` and the
  model answered from training memory unguarded (numbers are not checked on
  the general path); (2) the dataset had **no elite figures at all** —
  bosses.json carried only the five standard tiers, so even the grounded
  path could only mislabel (the faithfulness guard checks numbers, not the
  labels next to them).
- **Fix (this PR):** `map_bosses` now also reads the dump's
  `Bloons/<Family>/<Family>Elite{1..5}.json` models → `elite_tiers` on every
  boss (regenerated from the pinned v55.1 cutover SHA `4e22e586`,
  byte-identical otherwise); `BossEntry.elite_tiers`; grounding emits an
  explicitly-labeled ELITE line on elite questions and the standard line is
  now labeled "Standard (non-Elite)"; the honesty note remains only for a
  dataset predating the backfill; `btd6_boss_lookup` surfaces `elite_tiers`;
  boss canonicals joined the router's entity set and the faithfulness name
  index.
- **Regression tests:** `test_boss_elite_questions_ground_the_elite_table` ·
  `test_boss_elite_honesty_note_when_dataset_predates_backfill` ·
  `test_map_bosses_reads_elite_tier_models` ·
  `test_btd6_boss_lookup_surfaces_elite_tiers` ·
  `test_bosses_load_resolve_and_carry_tiers` (elite > standard per tier, all
  7 bosses) · live-battery `knowledge.btd6_elite_lych_hp_bug_0002`.
- **Deploy note:** elite data lives in bosses.json — prod serves it only
  after `!btd6ops seed-data` (postgres blob lane).
- **Status:** FIXED — this PR

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
- **Recurrence (2026-06-11 ~10:30-10:34, owner screenshots):** the *verbatim*
  phrasing refused again in #general, hours after #694 deployed — plus a new
  miss: "if I have 20K by round 50, how much would I have by round 60?".
  Root causes: (1) the deploy note above was the bug — #general runs the
  **default** profile, where the workflow never engaged, and the round-cash
  *tool* can't ground a starting-balance projection (the model's `20000 + X`
  is exactly what the number guard blocks), so "refuses by design" was a
  standing landmine on every default channel; (2) the matcher's cash-keyword
  gate had no cash noun to match ("how much would I have") and no pattern
  covered "by round A … by round B" anchors. **Follow-up fix (this PR):** the
  `compatible_default` + `balanced_helper` presets now declare the
  `analyze_execute_verify` workflow (read-only deterministic, Q-0048
  standing lift; `no_tools` keeps it off), the gate gained a money-question
  alternative ("how much … have/get/make/earn/gain"), and "by" joined both
  anchor sets. Regression tests:
  `test_plan_by_round_anchors_with_balance_production_phrasing` ·
  `test_plan_money_question_gate_stays_conservative` ·
  `test_default_and_balanced_engage_round_cash_workflow` · live-battery
  `knowledge.btd6_round_cash_by_round_projection`. No channel setup is
  needed anymore for round-cash questions.

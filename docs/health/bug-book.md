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

## BUG-0012 — counting staff check trusts role *names*, not permissions (privilege bypass) — FIXED

- **Symptom (owner-reported, 2026-06-14):** "you could give yourself a role
  called 'admin' while the admin role did not have any actual permissions — the
  fact that it was named 'admin' overruled the bot's permission system and
  allowed users to execute admin commands." A non-privileged member who holds
  (or can self-assign) a **cosmetic role merely named** `Admin` or `Moderator`
  — carrying zero Discord permissions — passed the counting staff gate.
- **Affected surface:** `CountingCog.is_staff_or_owner` (`disbot/cogs/counting_cog.py`),
  which gates the `@staff_or_owner()`-decorated counting management commands
  (`!countingmenu`/`!cm` and siblings). Scope was limited to the counting cog;
  every other cog already gates on real permissions
  (`@commands.has_permissions(...)`) or the governance visibility tier.
- **Root cause:** the check was `staff_roles = ["Admin", "Moderator"]; return
  any(role.name in staff_roles for role in ctx.author.roles)` — a **role-name
  string match**, never the role's actual permissions. Discord role names are
  arbitrary and self-assignable, so the name `"Admin"` granted authority a
  powerless role does not actually carry. This is the owner's "missing bindings"
  class: with no permission/binding check, authority fell back to a name. The
  gap was **noted as a code-quality observation since 2026-06-05**
  (`docs/audits/general-feature-layer-analysis-2026-06-05.md` §"Counting uses
  hardcoded role names") but never recognized as a security issue or fixed.
- **Impact:** privilege escalation within the counting subsystem on any guild
  where a non-privileged member can obtain a role named `Admin`/`Moderator`.
  No data-loss path, but it defeats the permission model for that surface.
- **Fix (PR — this entry):** `is_staff_or_owner` now resolves the member's
  **real** tier via the canonical `utils.visibility_rules.get_member_visibility_tier`
  (which reads `guild_permissions`: `administrator` / `moderate_members` /
  guild-owner) and requires `is_tier_sufficient(tier, "moderator")`; the bot
  owner still short-circuits true. A role *name* now confers nothing.
- **Regression test:** `tests/unit/cogs/test_counting_permissions.py` — pins
  that a powerless role named `Admin`/`Moderator` is denied, while real
  administrator / moderator / bot-owner / guild-owner are allowed and a plain
  member is denied.
- **Process note:** this bug had been captured by a routine as a vague
  *permissions-arrangement review* idea in `docs/ideas/` (PR #834) — the wrong
  home for a concrete bug. It belongs here in the bug book; #834 should be
  closed (or refocused into a router DISCUSS item if a broader permission-model
  audit is still wanted).
- **Status:** FIXED — root-caused + fixed + regression-tested 2026-06-14.

## BUG-0011 — Hermes gateway crash-loops on restart (Telegram 409) + periodic status=1 — OPEN

- **Symptom:** the `hermes-gateway` systemd service exits `Main process exited, code=exited,
  status=1/FAILURE` on (a) **every `systemctl restart`** — the new instance starts, prints the
  "Messaging platforms + cron scheduler" banner, then dies within ~1s — and (b) **periodically**
  while running (observed unprompted at 2026-06-12 20:41 and 22:31 UTC, hours apart). `Restart=always`
  (RestartSec=10) recovers it each time, so `is-active` reads `active` and service stays usable,
  but the red `status=1` noise repeatedly obscured real diagnosis during the 2026-06-12 Discord
  setup (it masked, then was confused with, the genuine `PrivilegedIntentsRequired` Discord error).
- **Likely root cause (unconfirmed):** Telegram **409 Conflict** — on restart the new instance
  begins long-polling `getUpdates` while the old instance's poll is still held briefly by
  Telegram's side, so the new one exits. The 2026-06-12 systemd-unit fix (TimeoutStopSec ≥ drain)
  reduced but did not remove it. The periodic (non-restart) crashes are unexplained — one was
  preceded by a "Self-improvement review: User profile updated" log line; needs a clean foreground
  repro (`systemctl stop` then `hermes gateway`) to capture the actual exit cause.
- **Impact:** cosmetic + self-healing today (control plane, low traffic), but: noisy logs,
  ~10–15s Telegram/Discord drop on each restart, and it actively hindered diagnosis. Worth fixing
  before the gateway becomes more load-bearing.
- **Candidate fixes:** confirm the 409 theory from a clean foreground run; on restart, have the
  adapter **retry on 409** instead of exiting, or lengthen the drain so the old poll fully closes
  before the new instance starts; investigate the periodic non-restart crashes separately.
- **Status:** OPEN — captured 2026-06-13 during the Hermes dual-platform setup session.

## BUG-0010 — the "in ABR" qualifier is ignored by auto-grounding and the round-cash workflow

- **Reported:** 2026-06-11 ~15:06–15:07 (owner, Haiku round): "how much cash
  do I get in ABR from r25 to r83 when I have double cash and I started with
  5443" → honest but **underclaiming** answer (served the standard $107,164.60
  correctly labeled "that's not ABR", then claimed the calculator can't do
  ABR — it can); "how much RBE is in r87 in ABR" → floored (the reply's
  honest "Alternate Bloons Rounds" naming wasn't in the haystack).
- **Probe evidence:** both phrasings route `btd6.answer` and the workflow
  MATCHES the range — but every grounded `[btd6_round]` fact and the workflow
  plan are **standard-roundset** (r87 grounds standard's 4-ZOMG/66,624-RBE
  round, not ABR's). The guard accidentally protects today: the mislabel
  can't pass because ABR facts are never in the haystack — so the failure
  mode is refusal, not a wrong number.
- **What already works:** the dataset carries all 140 ABR rounds
  (`abr_rounds.json`); the `btd6_round_composition` and round-cash TOOLS take
  `roundset='abr'` (the capabilities list advertises it). Only the
  deterministic legs lack the qualifier.
- **Fix sketch (focused slice):** (1) an ABR cue ("abr", "alternate bloons")
  in the resolver/grounding round legs → resolve round numbers against
  `abr_rounds` and label the lines `[ABR]`; (2) `RoundCashPlan` gains a
  `roundset` field + matcher cue so the workflow computes/labels the ABR
  range; (3) regression: the two live phrasings above.
- **Fix (follow-up session, same day):** one shared `ABR_CUE_RE`
  (`utils/btd6/keywords.py`) consumed by both legs. Grounding: the round
  legs re-fetch each resolver-matched round via `get_round(n, roundset="abr")`
  and stamp **every** line `Round N (ABR)` with an ABR economy note (no
  silent standard-as-ABR possible; a missing ABR entry says so explicitly).
  Workflow: `RoundCashPlan` gained `roundset` + `unsupported_modifier`; the
  matcher parses the cue and the named cash modifier; all three executors
  compute on the plan's roundset, label the economy in `result_text`, carry
  `roundset` in the evidence inputs/id, and emit an explicit "<modifier> is
  NOT applied" warning. Live phrasing now answers deterministically:
  **$113,872.30** ABR rounds 25-83 (≈ $119,315.30 projected with the stated
  $5,443) + the double-cash warning; "r87 in ABR" grounds **83,280 RBE /
  5 ZOMG (ABR)** instead of standard's 66,624 / 4 ZOMG.
- **Regression tests:**
  `test_plan_abr_qualifier_and_modifier_production_phrasing` ·
  `test_run_abr_range_uses_abr_economy_and_flags_modifier` ·
  `test_standard_phrasings_stay_default_roundset` ·
  `test_abr_qualifier_grounds_abr_round_entries` · live-battery
  `knowledge.btd6_abr_range_cash_bug_0010`.
- **Status:** FIXED — follow-up session 2026-06-11 (the PR after #707).

## BUG-0009 — grounded facts, wrong assembly: lists mislabeled / badly grouped (the claim-assembly class) — OPEN

- **Reported:** 2026-06-11 ~14:07–14:18 (owner, first Q-0086 live session):
  "what are all the monkey knowledges related to the farm" listed the whole
  Support MK category as "related to the Banana Farm" (Big Traps/One More
  Spike/Vigilant Sentries are Engineer/Spike Factory); owner verdict on the
  list-style answers broadly: *"some of these are correct but most of them
  are either slightly wrong or badly grouped etc"* (Geraldo per-level
  groupings, "3 newest towers" ordering, mode groupings).
- **Root cause:** the faithfulness guard checks **values, not claims** —
  every name/number is individually grounded, but the *grouping/labeling/
  ordering* is model-assembled. Third member of the BUG-0002/0004 mislabel
  class; the proven fix shape is "the deterministic layer owns the labeled
  answer" (rosters and the capabilities reply already work this way).
- **Direction (plan-level, not a quick patch):** deterministic list-answer
  builders for the high-traffic list families — "MK related to X" (filter MK
  by entity mention), per-level item lists, newest-towers — served as
  grounding blocks or floor replies. Route: AI orchestration plan §7
  families.
- **Status:** OPEN — captured for the AI-lane queue (this session: routing/
  guard layer fixed first, BUG-0005…0008 below).

## BUG-0008 — "420 farm" income freelanced on the general path (keyword gap)

- **Reported:** 2026-06-11 ~14:03 (owner: "this one it does answer from memory")
- **Surface:** AI task router keyword coverage → unguarded general path
- **Symptom:** "how much money does a 420 farm make" → invented economy
  ($45 bunches, "$1,725/round", invented build costs). No router keyword
  matched ("farm" is dropped from the entity matcher as ≤4 chars; "banana"
  absent; "420" can't route — FourTwenty owns it), so the model freelanced
  on the general path; name-guard outcomes varied per turn (tool-call turns
  self-grounded names; numbers are never checked on the general path).
  Variant: "list all the ways you can increase your farm income" (no money
  cue — "income" wasn't one) floored to the BTD6 refusal instead.
- **Fix (this PR):** "banana" curated keyword; router short-alias+money-cue
  leg (`farm|farms` + cash/money/how much/income/earn(s|ing)); the same cue
  extension benefits the r-shorthand leg. Farm questions now route
  `btd6.answer` → real Farm grounding + the full number guard.
- **Regression tests:** `test_farm_money_questions_route_to_btd6_answer` ·
  `test_farm_without_money_cue_stays_general`.
- **Status:** FIXED — this PR

## BUG-0007 — conversation-meta question answered with the BTD6 data refusal

- **Reported:** 2026-06-11 ~13:56 (owner transcript)
- **Surface:** general-path faithfulness guard floor
- **Symptom:** "what is the last message you can see" → "I don't have
  verified BTD6 data… (55.1)". The reply legitimately quoted the prior
  Desperado turns; the guard treated those names as ungrounded and the floor
  copy is a non-sequitur for a non-BTD6 question.
- **Fix (this PR):** the channel's recent conversation turns (the always-on
  3-turn floor) join the guard's trusted haystack on the **general path
  only** (BTD6-path numbers still require real grounding); when the floor
  still triggers on a question that is not itself BTD6-themed, a generic
  "I held back unverifiable game details" copy replaces the version-stamped
  refusal.
- **Regression tests:**
  `test_general_path_reply_may_quote_recent_conversation` ·
  `test_general_path_btd6_leak_is_refused` (generic copy) ·
  `test_general_path_btd6_themed_leak_keeps_version_refusal`.
- **Status:** FIXED — this PR

## BUG-0006 — conversation carryover unreachable: pronoun follow-ups never route BTD6

- **Reported:** 2026-06-11 ~13:56 (owner transcript — the eval checklist's
  own Tier-1.4 phrase)
- **Surface:** AI task router (text-only) vs the #668 carryover grounding
- **Symptom:** "does the navarch of seas paragon make coin" answered
  correctly, then "does it make coins at the end of the round?" refused.
  Same shape: "which of those items can damage lead" after the Geraldo list.
- **Root cause:** the #668 carryover lives in `btd6_context_service.build`,
  which only runs on `AITask.BTD6_ANSWER` — but `classify()` is text-only
  and an entity-less pronoun follow-up has no BTD6 token ("…the round?"
  even misses the `"round "` keyword on punctuation). The carryover shipped
  with its routing leg missing; its unit tests called `build()` directly.
- **Fix (this PR):** `classify(..., conversation_btd6_context=)` — the stage
  scans the in-process conversation floor (≤3 turns) with the curated
  keyword predicate and passes the cue; a follow-up-shaped question
  (it/its/they/them/those/these + question shape) with the cue routes
  `btd6.answer`, where carryover resolves the pronoun. Standalone questions
  stay general regardless of the cue.
- **Regression tests:**
  `test_pronoun_followup_routes_btd6_with_conversation_cue` ·
  `test_pronoun_followup_stays_general_without_cue` ·
  `test_conversation_cue_does_not_route_standalone_questions`.
- **Status:** FIXED — this PR

## BUG-0005 — BUG-0003 recurrence in the model loop: the tool laundered a misread quantity ($120,743,025)

- **Reported:** 2026-06-11 ~13:55 (owner transcript — first live tool-loop
  test under Q-0086 keys; the deterministic layer was verified correct in
  #703 but the model leg was untestable then)
- **Surface:** AI model loop × bulk-pricing tools × faithfulness guard
- **Symptom:** "how much do 10 041 despos cost on impop" → "$120,743,025"
  (= 10,041 × $12,025) despite the grounding line carrying the correct
  "×10 towers → Impoppable $120,250".
- **Root cause:** the model preferred its own "10 041 = 10,041" reading and
  passed it as the tool `quantity` — the tool computed the product, the
  result entered the trusted ledger, and the guard then **validated the
  wrong number against the model's own tool call** (laundering). The
  grounding line implied ×10 but never negated the misreading.
- **Fix (this PR):** (1) the `[btd6_pricing]` line now explicitly negates it
  ("means 10 towers at crosspath 0-4-1 — NOT the single number 10041; use
  these grounded totals verbatim; do not recompute"); (2) both bulk-pricing
  tools fail closed on implausible counts (>999) with a note that teaches
  the `<quantity> <crosspath>` reading mid-loop.
- **Regression tests:**
  `test_quantity_laundering_gate_rejects_implausible_counts` ·
  `test_pricing_line_quantity_crosspath_production_phrasing` (negation
  asserts).
- **Status:** FIXED — this PR

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

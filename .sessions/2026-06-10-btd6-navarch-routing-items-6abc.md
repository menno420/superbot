# 2026-06-10 — BTD6 Navarch routing diagnosis + answerability items 6a–c (PR #662)

**Task:** "continue where the previous btd6 decoding session ended, also find
out if the wrong answer in the screenshot is missing data or missing routing"
— the screenshot: "@SuperBot does the navarch of seas paragon make coins" →
the bot confidently answered NO (the Navarch generates $3,200/round in game).
**Answer to the diagnostic question: missing ROUTING, never missing data** —
`navarch_of_the_seas.json` carried `cashPerRound: 3200` + the Trade Empire /
Flagship / sellback buffs since the #649 cutover. Three independent routing
layers failed; all three reproduced by probe, then fixed:

1. **Resolution:** "navarch of seas" (article dropped) failed the exact
   substring match in `_paragon_name_facts` → the question ran with **zero
   grounding facts** and the model freelanced. Now article-tolerant, plus
   "paragon"-keyword-gated shorthand via `paragon_math.resolve_paragon`.
2. **Truncation:** the curated description's income sentence is its *last*
   sentence — precisely what the 240-char fact cap removes.
3. **No paragon income/effects leg:** towers ground income via specials,
   heroes via `[btd6_hero_buff]` (#658); paragons rendered only the
   primary-attack headline. Now: a dedicated income line + per-effect
   `[btd6_paragon_stats effect]` lines, `Income $X/round` on the shared
   `_stat_node_embed` menu head, `income_per_round` on the paragon AI tool,
   and "(affects paragons only)" for the `onlyAffectParagon` aura split.

**Also shipped (the queued backlog):** decode-status items **6a–c** — the
minion-name → owner grounding pass (Pass 3b2; "Mini Sun Avatar" → Sun Temple
4-0-0, "Crushing Sentry", Etienne's UAV renders its Camo-grant buff), the
**Pouākai tokenizer diacritic fix** found by the 6a survey (`_tokens` split
the non-ASCII letter into `pou|kai` — unmatchable typed either way), the
`fixture/btd6_data` → "BTD6 dataset, game v55.1" label helper (18 sites), and
the fixture-only `source_summary` honesty branch. Technical detail:
decode-status §"Session log — the Navarch routing diagnosis + items 6a–c".

## Process learnings (the durable part)

- **Replay the user's exact text before reading code.** One probe
  (`build(<screenshot text>)` → 0 facts) split "resolution failed" from
  "rendering failed" and shaped every fix. The cleaned-up name returned 7
  facts — diagnosing from that version would have missed the layer that
  actually fired live.
- **A confident answer ≠ a grounded answer.** "Based on the verified data…"
  was styled by the instruction stack onto a zero-fact reply. When triaging
  "the bot said X wrongly", measure the grounding first, then blame data.
- **Survey the real data before designing guards.** Walking all 41 subtower
  names showed beast names ARE upgrade-card names (so the collision guard
  replaces an alias table) and surfaced the Pouākai split nobody reported.
- **CI redline:** first push went red on ruff B905 — pushed after targeted
  tests but before the full mirror, and the remote container's PostToolUse
  auto-format hook wasn't active (setup_dev_env.sh failed at session start;
  the journal's known gotcha). Run `check_quality.py --full` (or at least
  `--check-only`) before EVERY push here, not just the big ones.

## Context delta (reflection interview)

- **Route miss:** nothing in the orientation route pointed from "a live wrong
  answer" to the grounding-probe technique (`build(<exact text>)` →
  fact count). It's now recorded in the decode-status session log; if a third
  session reaches for it, promote a one-liner into the BTD6 folio's
  debugging section.
- **Route excess:** none felt wasted; the decode-status ⭐ header + the
  predecessor `.sessions/` log were exactly the right resume points.
- **Discovered by hand:** `paragon_math._ALIASES` exists but was wired only
  to the calculator/views — grounding had its own weaker matching; the
  upgrade tokenizer's diacritic split; `UpgradeIdentity.tower_name` being the
  proper display name (vs `TowerStats.canonical` = internal-ish post-cutover).
- **Decisions made alone:** (1) gating shorthand paragon matching on the word
  "paragon" (false-positive control) rather than matching bare aliases; (2)
  branching `source_summary` on *any NK-sourced DB rows* instead of the
  scouted `live_rows`-only check; (3) stoplisting "Phoenix" NOT — it grounds
  Summon Phoenix (0-4-0), judged in-vocabulary. All contained + tested;
  flagged here for review.
- **Weak point of what shipped:** the minion index prefers the *lowest*
  owning tier; a name appearing at multiple meaningful tiers grounds only
  one (acceptable today — survey showed no real conflict besides Phoenix
  wizard-vs-Magus, resolved tier-first). And follow-up-turn pronouns still
  ground nothing (captured as backlog item 7, not silently dropped).
- **One change that would have helped:** a tiny "grounding probe" dev
  command (`scripts/btd6_probe.py "<text>"` printing facts + summary) — I
  wrote the same 8-line snippet inline four times this session. Candidate
  for a future tooling slice if the next session reaches for it too.

**Resume point:** decode-status ⭐ — item 3 stays demand-driven (this session
WAS such a demand), item 4 is the maintainer's live spot-check (now including
the Navarch income answer + minion names), item 7 is the captured
conversation-grounding idea. PR #662 review = the diff.

## Continuation 2 (same session, after #666 merged — "anything else you can do?")

The maintainer asked what could ship without his testing. Three moves:
- **Item 7 slice 1 implemented** (the screenshot's turn-2 failure): zero-fact
  `build()` with channel identity grounds the newest entity-bearing recent
  turn via the existing `ai_conversation_service` floor (never more history
  than the model prompt sees), labeled `[btd6_carryover]`; NL stage passes
  guild/channel ids; Ask/tool callers byte-identical. The plan's first §4
  question resolved in-code: gate = zero facts total. 9 tests incl. the
  verbatim two-turn screenshot sequence + topic-switch + no-ids pins.
- **Proactive probe sweep** (~60 questions across paragon/income/minion/
  common families): only 3 zero-fact classes remained — ranking questions
  ("best paragon"/"strongest tower" → roster verbs extended) and bare
  distinctive shorthand ("navarch" → `_DISTINCTIVE_PARAGON_WORDS`, no
  generic words). Both fixed + pinned same pass. UAV/Ball-of-Light "thin"
  results judged correct-as-is.
- **Process flag:** one mypy red from a `tokens` set/list name collision
  between my two passes in `_paragon_name_facts` — caught by the full
  mirror, renamed. Sweep-before-spot-check is cheap (~2 min) and found
  every remaining class; candidate habit for any future grounding change.

## Continuation (same session, after #662 merged)

- **Mid-session ledger conflict** (#659 merged to main while #662 was open):
  resolved by the per-lane UNION convention — main's Consolidated-batches
  bullet + this lane's BTD6 bullet; the Last-updated chain composed newest
  (#662) → theirs (#659/#657) verbatim. Full CI mirror re-run on the merged
  tree before pushing the resolution. The convention worked exactly as
  documented; nothing was lost on either side.
- **#662 merged.** Follow-up slice (new PR): built `scripts/btd6_probe.py` —
  the "one change that would have helped" from the interview above (the
  grounding replay was written inline four times during the diagnosis); 3
  tests; provenance header carries the verify-before-trusting note. And the
  **grooming move (Q-0015)**: item 7 structured from idea → plan —
  `docs/planning/btd6-conversation-grounding-plan-2026-06-10.md` (carryover
  entity resolution at the `_gather_feature_facts` seam over the existing
  `ai_conversation_service` deque; zero-entity gate; labeled carryover
  facts) — source-verified seams, not approved for implementation.

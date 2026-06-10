# BTD6 conversation-carryover grounding — design plan

> **Status:** `plan` — **slice 1 (§3) EXECUTED 2026-06-10 in PR #668**, same day, after the
> maintainer asked what else could ship without his testing ("anything else you
> can do right now") — the act-envelope call: deterministic, read-only, no new
> state, regression-pinned. §4's first open question resolved in-code: the gate
> is **zero facts total** (the conservative trigger; the live case had exactly
> that). Remaining open: the eval-harness pin (§4 third bullet) and any wider
> window once real usage data exists.
> **Prepared:** 2026-06-10 (the Navarch routing session's captured gap, PR #662).
> **Area authorities:** [`../subsystems/btd6.md`](../subsystems/btd6.md) ·
> [`../subsystems/ai.md`](../subsystems/ai.md) · backlog home:
> [`../btd6/btd6-gamedata-decode-status.md`](../btd6/btd6-gamedata-decode-status.md) item 7.

## 1. Problem (observed live, 2026-06-10)

Turn 1: "does the navarch of seas paragon make coins" → fixed by PR #662
(grounds 12 facts incl. income). Turn 2, a Discord reply to the bot's answer:
**"Does it make coins at the end of round"** → grounds **zero facts** by
construction, because grounding is per-message: the entity ("it") lives in
the conversation, not the message. The model then answers from conversation
memory + pretraining while the instruction stack's faithfulness framing makes
it *sound* verified ("Based on the verified data…"). Verify any candidate
fix's "before" state with `python3.10 scripts/btd6_probe.py "<text>"`.

## 2. Verified mechanics (source-checked 2026-06-10)

- Grounding is built from the current message only:
  `natural_language_stage` builds `FeatureFactRequest(task, text=raw_text,
  guild_id, channel_id, author_id, message_id)` → `_gather_feature_facts()`
  → `btd6_context_service.build(req.text)`.
- **Conversation memory already exists and already names the entity.**
  `services/ai_conversation_service.py` keeps a bounded per-channel deque of
  `ConversationTurn(user_id, role='user'|'assistant', text, ts, display_name)`
  (ADR-001-compliant: in-process, LRU-bounded), read via
  `recent_turns(guild_id, channel_id, *, window_minutes, min_floor, limit)`.
  The NL stage feeds these turns to the *model prompt* — only the grounding
  build ignores them. In the live failure, the **assistant's own previous
  turn** contains "Navarch of the Seas" verbatim.

## 3. Design

**Slice 1 (recommended): carryover entity resolution at the feature-facts
seam.** In `_gather_feature_facts` (BTD6 branch only):

1. Build grounding for `req.text` as today.
2. **Gate:** if the build produced at least one *entity* fact, stop — a
   message that names its own subject never consults history (topic switches
   stay clean). A zero-entity build on a message with interrogative/anaphora
   shape ("it", "that one", "the paragon") proceeds.
3. Pull `recent_turns(guild_id, channel_id, ...)` (assistant turns included),
   newest first, bounded (e.g. 6 turns / existing window semantics).
4. For each prior turn, run **entity resolution only** (the resolver + the
   #662 name passes) until one yields entities; rebuild grounding for the
   *current* question text augmented with those entity names.
   *(As built in #668: the implementation grounds the prior turn's text
   directly via a nested identity-free `build()` — functionally equivalent
   and simpler; raw turn text still never enters the fact payload.)*
5. Label every carried fact's origin in one leading line — e.g.
   `[btd6_carryover] Grounding "<entity>" from the earlier conversation
   turn; if the user meant something else, ask.` — so the model can hedge
   honestly instead of presenting carryover as if the user named it.

**Why not** persist "last resolved entities" per channel (option B): new
state + invalidation for data the deque already holds as text; revisit only
if step-4 resolution proves too slow (it is in-process and deterministic).

**Bound and deterministic:** no model calls, no DB writes, no new state;
read-only over an existing bounded buffer.

## 4. Open questions (pre-implementation)

- Does the anaphora gate (step 2) need a keyword list at all, or is
  "zero entity facts" alone the right trigger? (Zero-entity non-BTD6 chatter
  already routes away before the BTD6 task fires — verify against the task
  router before adding vocabulary.)
- Should carryover scan only turns since the bot's last BTD6 answer
  (freshness) or the whole floor window?
- Eval coverage: add the two-turn screenshot sequence to `tests/evals/`
  (deterministic harness) or unit-test the seam only?

## 5. Test plan (when implemented)

- Regression pin: the exact two-turn Navarch sequence (turn 2 grounds the
  income fact, labeled carryover).
- Topic switch: turn 2 names a *different* tower → no carryover, no label.
- Empty history / DM / first message → behaves exactly as today.
- Determinism: same buffer + same text ⇒ same facts.

## 6. Scope

One contained PR (the seam + tests + the eval pin). Out of scope: other
feature tasks (YouTube), cross-channel memory, persistence, any UI.

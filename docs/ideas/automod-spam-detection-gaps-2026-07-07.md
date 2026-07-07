# Automod's spam rule is rate-only and per-channel — two related detection gaps

> **Status:** `historical` — ✅ **SHIPPED same day, 2026-07-07.** Owner-raised ("I don't think
> there's currently a way to separate repeated messages from repeated duplicate messages, and there
> might be more oversights related to this"), confirmed against `disbot/services/automod_service.py`,
> and fixed on the live bot rather than left for the rebuild to inherit — the owner flagged that a
> golden-replay-driven port would otherwise faithfully reproduce the bug (see the "why fix live, not
> just plan for it" note at the bottom). Both gaps closed: `SpamTracker.record_and_count_any_channel`
> (cross-channel bucket) and the new `DuplicateTracker` + `automod.duplicate` rule, both through the
> existing audited `moderation_service` seam. Tracked as punch #5/#6 on
> [`../planning/feature-completion/units/automod.md`](../planning/feature-completion/units/automod.md),
> now marked shipped there.
> **Subsystem:** automod. Related: [`moderation-feature-gaps-2026-07-07.md`](./moderation-feature-gaps-2026-07-07.md)
> (broader moderation feature parity, captured the same day — this doc is a narrower, code-verified
> follow-on specific to the automod detection engine).

## 1. No content-duplicate detection — confirmed, owner's suspicion correct

`SpamTracker` (`disbot/services/automod_service.py:56-91`) is the entirety of the "repeated
messages" rule, and it is **pure rate-counting**: a sliding-window deque of timestamps per
`(guild_id, user_id, channel_id)`, tripped when N messages land within T seconds
(`evaluate()`, `automod_service.py:192-212`). It never reads `message.content`. There is no code
anywhere in the repo (grepped `automod_service.py`, `automod_cog.py`, `cleanup`, and
`prohibited_words_service.py`) that compares a message's content against the sender's recent
messages to detect exact or near-duplicate spam ("copypasta").

Practical effect: a burst of five *different* messages in 7 seconds and the *same* message pasted
five times in 7 seconds are indistinguishable to the current rule — both either trip the identical
rate threshold or neither does. A user who paces duplicate messages just under the rate limit (e.g.
2 identical messages every window, forever) is never flagged, since nothing is comparing content.

## 2. A more serious, related gap found while verifying #1: the spam rule is per-channel, not per-guild

`SpamTracker.record_and_count`'s key is `(guild_id, user_id, channel_id)`
(`automod_service.py:78`) — the bucket is scoped **per channel**. A burst of messages spread across
*multiple different channels* never accumulates in any single bucket, so it never trips the spam
rule at all, **regardless of content**. This defeats the one rate limit that exists, independent of
the duplicate-content question — a raid pattern of posting across many channels rapidly (one
message per channel) evades automod's spam rule entirely today. This is arguably the more urgent of
the two findings, since it's not "missing a second layer of defense" — it's a way to fully bypass
the only layer that exists.

## Two smaller, related, lower-priority gaps noticed in the same area

- **No re-evaluation on message edit.** `automod/listener.py`'s `process_message` only fires on
  message create; a message edited after posting isn't re-run through `evaluate()`. Not the primary
  ask, but the same "content isn't really being watched over time" family of gap.
- **No near-duplicate / fuzzy matching** — only relevant once exact-duplicate detection exists;
  spammers commonly defeat exact-match filters with a trailing random character or emoji. Worth a
  follow-on, not a v1 requirement — exact-duplicate detection is the right first step, and fuzzy
  matching adds real false-positive risk that needs its own tuning pass.

**Explicitly not new findings** (already tracked in `docs/planning/feature-completion/units/automod.md`'s
punch-list, not re-reported here): no word blacklist in automod itself (owned by `cleanup`), no
attachment/embed rules, no per-rule trigger-count view.

## Design sketch (for whoever picks this up)

1. **Fix the per-channel keying first** — this is the higher-severity, lower-complexity fix. Add a
   guild-wide (or per-user-across-channels) counter alongside the existing per-channel one, so a
   multi-channel burst trips regardless of which channel each message lands in. Needs a threshold
   distinct from the per-channel one (cross-channel bursts are a stronger raid signal, so this could
   reasonably be *more* sensitive, not less).
2. **Add content-duplicate detection as its own rule**, not a modification of the existing spam
   rule — keep them orthogonal (a "same content N times in T seconds" tracker, most naturally a
   small extension of `SpamTracker` that also stores a normalized-content hash per entry, tripping
   when M of the last N messages in the window share a hash). Normalize before hashing (trim
   whitespace/case-fold) so trivial variation doesn't defeat it trivially, but stop short of fuzzy
   matching for v1 to avoid false-positive risk on legitimate repeated short replies ("lol", "same").
3. Both should go through the same audited `moderation_service` seam the existing four rules use —
   no second escalation ladder, matching the rest of automod's design.

## Recommended routing — shipped, not deferred

Originally scoped as "pick up whenever automod's punch-list is next worked." Revised same day: the
owner pointed out the actual risk of leaving it as a plan note — the rebuild ports subsystems by
replaying **goldens captured from the live bot's current behavior**, and the new bot is required to
reproduce them byte-for-byte before it's allowed to merge (`red until parity`). Leaving the bug
unfixed on the live bot would mean whatever golden gets captured for automod encodes the *buggy*
behavior, and the new bot would then be obligated to reproduce that exact bug to pass its own parity
gate — a plan footnote doesn't reliably prevent that, since golden-replay porting carries forward
whatever it's given by default. The project's own existing rule already covers this case cleanly:
"any PR that changes behavior a golden captures must re-capture the affected goldens in the same PR"
(L-21) — so fixing it live now means the correction flows into the rebuild automatically the normal
way, with no special-casing needed and no risk of the bug getting silently ported.

Both rules shipped same day: `SpamTracker.record_and_count_any_channel` (cross-channel bucket, reusing
the existing sliding-window mechanics via a sentinel key) and a new `DuplicateTracker` +
`automod.duplicate` rule (guild+user-keyed normalized-content window), both through the existing
audited `moderation_service` seam, both defaulting OFF like every other automod rule, both with test
coverage including the negative case the owner specifically flagged (a burst of *different* messages
must never trip the duplicate rule).

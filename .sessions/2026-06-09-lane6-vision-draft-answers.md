# Lane 6 — vision draft-answers for Q-0038–Q-0042 — 2026-06-09

## Summary

Executed Lane 6 of `docs/planning/multi-lane-execution-plan-2026-06-09.md` (the
Q-0051 route): drafted one concrete proposed answer per open product-vision question —
Q-0038 clans identity · Q-0039 VIP fairness · Q-0040 AI dungeon-master posture ·
Q-0041 integrations/voice privacy · Q-0042 web dashboard — and appended each under its
existing router entry, marked **`draft-answer — awaiting maintainer markup`**. Safe
defaults stay binding; nothing is approved or implemented by this session. **PR #631**
(draft opened right after first push per Q-0052; one of four parallel agents — Lanes 2,
3, 5 ran concurrently and their files were not touched).

Each draft follows the lane's shape (proposed answer / why it fits / safe default /
implementation implication / rejected direction) with the proposed answer itemized per
sub-question so the maintainer can approve/adjust/reject line-by-line — the
gate-lifting-interview pattern with prose to react to.

## The five proposals in one line each

- **Q-0038:** server-scoped clans (`(guild_id, clan_id)`), no cross-server identity in
  v1; schema says "clan" to dodge the discord.py `Guild` name collision.
- **Q-0039:** donation = cosmetic + recognition only; convenience perks only on the
  earned milestone track; supporter status read from an externally-managed Discord
  role — SuperBot never stores/processes payment data; CI invariant proposed (no VIP
  predicate in odds/reward/cooldown/fee paths).
- **Q-0040:** AI is narrator, never game-owner — thread-per-session first, opt-in +
  off-by-default, hard budgets on the shipped orchestration seams; dynamic difficulty +
  AI-chosen rewards deferred behind the Q-0001/AR-09 action-authority path (the honest
  split: two of the owner's four selected event styles can't be narrative-only).
- **Q-0041:** YouTube-alerts pilot first (ADR-007 reuse) → Twitch → Spotify/Steam after
  an account-link consent decision; operator-owned keys, dual opt-in, metadata-only
  bounded caches, fail-quiet degradation; voice behind its own architecture review,
  speech recognition last, if ever.
- **Q-0042:** web dashboard = yes as destination, staged read-only-companion →
  management through the same audited services; Discord OAuth2 only; bot process never
  serves the site (Stage B is an ADR-001 revisit by design); stays Someday.

## Files changed

- `docs/owner/maintainer-question-router.md` — five draft-answer blocks appended under
  Q-0038–Q-0042 (+ their `Status:` lines now say a draft awaits markup). Question text,
  safe defaults, and Q-0051 handling notes preserved verbatim.
- `docs/planning/multi-lane-execution-plan-2026-06-09.md` — Lane 6 scoreboard row
  ticked with PR #631.
- `docs/current-state.md` — one-phrase update on the existing Q-0051 cross-cutting
  line (drafts exist, awaiting markup; nothing routed as accepted truth).
- `.sessions/2026-06-09-lane6-vision-draft-answers.md` — this log.

## Grounding read set (what the drafts cite)

`docs/ideas/owner-vision-ideas-2026-06-08.md` (the 36-question owner capture — §4a/§9/
§13/§3a/§3b/§25/§6/§17/§21 carry the actual selections), the four destination roadmap
drafts (social / economy / AI-extension routing / integrations), ADR-001/002/007,
ideas-lab §2 operating decisions + §6 rejection ledger (nothing rejected re-proposed),
answered Q-0001/Q-0002 + AR-08/AR-09, Q-0033/Q-0043–Q-0051,
`docs/ideas/future-product-direction-2026-06-07.md` (website/cross-server guardrails).

## Follow-ups (not approved work — the markup pass owns them)

- Maintainer marks up the five drafts (approve / adjust / reject per item — PR #631's
  table is the index). The markup session then flips statuses, routes conclusions to
  the destination docs, and per Q-0062 seeds the lazy owner-voice folio blocks for the
  touched areas (social/games, economy, AI, media, platform).
- Backlog-grooming note (Q-0015): this lane *is* a five-question grooming move down the
  idea conveyor (open → discussed-with-draft); no additional `docs/ideas/` item was
  groomed to avoid colliding with the three parallel sibling sessions in shared docs.

## Context delta

- **Needed but not pointed to:** `docs/ideas/owner-vision-ideas-2026-06-08.md` is the
  real substance behind all five questions (the questions compress its §4a/§13/§3/§6/
  §17/§21 selections) — the lane's "read first" names the router entries + rejection
  ledger + ADRs but not this file; each roadmap draft's "Primary source" line is what
  surfaces it. Worth naming it directly in any future vision-question lane.
- **Pointed to but didn't need:** ADR-002's implementer notes (refund hook details) —
  only the headline decision mattered for the Q-0040 draft; and CodeGraph entirely
  (docs-only lane, zero symbol navigation).
- **Discovered by hand:** zero open PRs at session start meant "confirm no other Lane 6
  PR" was a one-call check, but with four agents launched simultaneously none of the
  siblings' PRs were visible yet either — for parallel-agent runs, PR-existence checks
  only de-risk *earlier* lanes, not concurrent ones; the real collision guard is the
  per-lane file ownership in the launch prompt.

# 2026-06-11 — AI knowledge: the morning screenshots' 3 live misses fixed (PR #703)

**PR:** [#703](https://github.com/menno420/superbot/pull/703).
**Authoritative docs:** [`docs/health/bug-book.md`](../docs/health/bug-book.md)
(BUG-0001 recurrence addendum + new BUG-0002 / BUG-0003 — full root causes
live there, not here) · decode-status boss row (Elite → FETCHED) ·
eval checklist §1.1 (three new regression walks).

## What the screenshots showed → what was actually wrong

1. **Round-cash refusals in #general** ("8094$ at round 60 → 68" — the
   *verbatim* BUG-0001 phrasing, hours after #694 deployed — and "if I have
   20K by round 50, how much would I have by round 60?"). Two causes: the
   workflow was **profile-gated off** on default channels (the bug-book
   deploy note *was* the bug: the round-cash tool can't ground a
   starting-balance projection, so "refuses by design" hit every default
   channel), and the matcher had no money-question gate / no "by round A …
   by round B" anchors. Fix: `compatible_default` + `balanced_helper` now
   declare `analyze_execute_verify` (Q-0048 read-only standing lift;
   `no_tools` untouched) + matcher widened, conservatism pinned.
2. **"Elite Lych HP per tier" answered with the Standard table labeled
   Elite** (got a 🔥 — confident wrong numbers read as authoritative).
   Boss names were not router entities (→ general path, memory, no number
   guard) AND the dataset had no elite figures at all. Fix: `map_bosses`
   reads the dump's `<Family>Elite{1..5}.json` → `elite_tiers` (regenerated
   at the pinned v55.1 SHA, byte-identical otherwise), variant-labeled
   grounding lines, boss canonicals into router + name index.
3. **"10 041 despos on impop" → hallucinated "despos = Plasma Monkey Fan
   Club"**. "despo" is the **Desperado** tower; nothing routed or resolved
   it. Fix: `impop`/`despo` keywords, Desperado `despo` alias, resolver
   plural fold (`alias+"s"`), and `btd6_difficulty_cost` gained `quantity`
   so bulk products are tool-grounded.

## Verification

CI mirror green (8,960+ passed) · arch strict 0 errors · clean test-bot boot
(Galaxy Bot#6724, 0 errors) · all four screenshot questions replayed through
probe/router/workflow with correct results · 4 new live-battery eval cases.

**Owner action after merge+deploy: `!btd6ops seed-data`** — bosses/towers
json are blob-lane data; the code fixes deploy with the merge.

## Context delta (reflection interview)

1. **Route miss:** none in the reading order — bug book → `btd6_probe.py` →
   source was exactly right. But see (3): the probe alone *misled* for 20
   minutes.
2. **Route excess:** none significant; current-state's marathon header is
   heavy but the lane bullets carried the load.
3. **Discovered by hand:** `btd6_probe.py` shows *grounding* but not
   *routing* — for "elite lych" it printed 5 healthy facts while the real
   pipeline never reached grounding (the router had sent it to the general
   path). A routing bug is invisible to the probe by construction; I had to
   simulate `ai_task_router.classify` + the orchestration decision in
   separate one-off scripts. That blind spot is this session's idea (below).
4. **Decisions made alone:** flipping the default preset's `workflow` to
   `analyze_execute_verify` (changes default-profile behavior). Judged
   in-envelope: Q-0048's standing lift covers read-only deterministic
   tools, the owner's screenshots are him reporting the refusals as bugs,
   and the eval walk had already production-checked the workflow (Tier
   1.1/1.2 passed). Recorded in the bug book + presets docstring; flag for
   the owner in the PR body.
5. **Weak point of what shipped:** the elite answer's correctness in prod
   depends on `!btd6ops seed-data` being run — until then prod grounds the
   honesty note (better than the mislabel, but not the real figures). Also
   the despo eval case needs a provider key channel to fully verify the
   tool-call path (sandbox has no key).
6. **One change that would have helped:** a single command that replays a
   message through router→profile→workflow→grounding in one shot (the idea
   below).

## 💡 Session idea

**Extend `scripts/btd6_probe.py` with the routing/workflow legs** (e.g.
`--route`): print the `ai_task_router` classification, the resolved
orchestration profile/workflow for a given scope, whether
`ai_round_cash_workflow.plan_question` matches, and THEN the grounding
facts. Why I believe in it: this session's two routing bugs were invisible
to the existing probe — it showed 5 healthy facts for a question the
pipeline never grounded, which is actively misleading triage. BUG-0002/0003
would have been one probe invocation instead of three hand-written
simulations. (Dedup-checked `docs/ideas/` — the probe has no idea file; its
provenance header lives in the script.) **Executed in this same session as
the Q-0015 grooming move** (small/safe/active-lane): `--route` prints the
task classification, the round-cash plan match, and the engaging profiles —
`test_route_leg_flags_general_path_miss` pins the miss signature.

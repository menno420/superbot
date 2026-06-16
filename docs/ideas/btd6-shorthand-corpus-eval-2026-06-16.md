# BTD6 community-shorthand corpus eval (router-class regression guard)

> **Status:** `ideas`. **Not approved for implementation, not a plan.** A captured late
> discovery from the BUG-0015 session (2026-06-16, PR #963). Source + the binding contracts +
> `docs/current-state.md` win over this file.

## The recurring class this would guard

Five live-reported BTD6 bugs share **one root cause**: a community-shorthand question is **not
recognised by `ai_task_router.classify`**, so it falls through to `GENERAL_NL_ANSWER` — the
**unguarded** path (no grounding, no number guard) — where the model freelances from memory:

| Bug | Shorthand that didn't route | Symptom |
|---|---|---|
| BUG-0001 | "cash by round 68" round-cash phrasing | refused / wrong total |
| BUG-0003 | `despo`, `impop` | "despos" → wrong tower (Plasma Monkey Fan Club) |
| BUG-0004 | `r53`/`r70` round shorthand | wrong cumulative total |
| BUG-0008 | `420 farm` / short farm alias + money cue | invented farm income |
| BUG-0015 | `d67` (degree) | "0-6-7 dart paragon doesn't exist" |

Each was fixed with a *new `_looks_like_*` leg* in the router + a grounding leg — but each fix
shipped its **own** isolated regression test. There is **no single guard** asserting "the whole
known shorthand vocabulary routes to BTD6 grounding." A future router refactor (or a re-ordering
of the `_looks_like_*` ladder) could silently regress one shorthand back onto the unguarded path,
and only a *new* live user report would catch it — the exact failure loop this class keeps
repeating.

## The idea

A single **corpus regression test** — `tests/unit/services/test_btd6_shorthand_corpus.py` — that
holds the canonical list of community shorthands the bot must recognise and asserts each routes to
`AITask.BTD6_ANSWER` (the class guard: "never silently drop a known shorthand to the unguarded
path"), plus the matching conservatism negatives (the look-alikes that must *stay* general:
`r2d2`, "67 degrees outside", "a degree in CS", "how do I farm coins"). It complements — does not
replace — the per-bug tests: those pin *why* each leg exists; the corpus pins *the class as a
whole* so adding a new shorthand is one obvious place and a refactor can't regress the set unseen.

Cheap to start (routing-only, no DB), high leverage (it is the seam every one of these bugs went
through). Optionally a second tier could assert the deterministic-grounding shorthands also produce
their grounding facts, but that is heavier (dataset-backed) and a follow-on.

## Why captured, not built

Per the session-sizing rule (Q-0088: *no unguided PRs past declared scope — late discoveries go
into the queue*), this was discovered while fixing BUG-0015 and belongs in the backlog, not bolted
onto that PR. It is small/safe/decided-lane (a test in an existing area), so it is a strong
**grooming-pass execute-now** candidate for a later session, or a quick win whenever the AI/BTD6
router is next touched.

## Related finding — hero per-level stats (a *minor*, lower-priority sibling)

While checking whether BUG-0015 had a hero analogue, I verified: hero per-level questions ("Quincy
at level 7") **route fine** (hero names *are* in the entity matcher, unlike the single-word towers
that tripped BUG-0015), and `btd6_context_service` already grounds **per-level descriptions for all
20 levels** + **headline stats at levels 1/3/10/20** (`_render_hero_descriptions` /
`_render_hero_stats`, `_HERO_GROUNDING_LEVELS`). The only gap is **exact stats at a non-headline
level** (e.g. level 7/15), which would mirror `_paragon_degree_facts`. This is **low priority**:
heroes mostly gain *described abilities* (already grounded), not stat scaling, and the BTD6-path
number guard makes the worst case a *refusal*, not a wrong answer (unlike the paragon case). Noted
here so a future session doesn't re-investigate from scratch or over-invest in it.

## Lifecycle

`captured` → execute the corpus test in a grooming pass / next AI-router touch. The hero-stat
sub-item stays `captured` at low priority unless a live report raises it.

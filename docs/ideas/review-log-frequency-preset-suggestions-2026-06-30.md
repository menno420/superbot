# Frequency-driven preset suggestions from the review log

> **Status:** `ideas`. **Not a plan, not approval.** A capture doc so the idea lives in
> the repo instead of in chat. Source code, the binding contracts, and
> `docs/current-state.md` always win over anything here.
>
> **Subsystem:** ai
>
> **Session idea (2026-06-30, Q-0089)** — surfaced building the AI review-log answer loop
> (`!aireview export` + triage + the vetted-preset layer, PR #1569).

## The idea in one paragraph

The answer loop shipped this session is **operator-pull**: a human runs `!aireview export`,
triages, and authors presets. Close the other direction — **let the bot push the highest-value
preset candidates to the operator**. When the *same normalized question* (the
`utils.ai_text_normalize` key the preset lookup already uses) recurs as an `unknown` entry **N
times within a window**, post a one-line nudge to the review channel: *"This question was asked
4× this week and the bot couldn't answer it — author a preset? `!aireview preset from <id>
<answer>`."* It turns the review log from a passive record into a **proactive worklist sorted
by real demand**, so operators spend their preset-authoring effort where it matters most.

## Why it's worth having

- **Zero new data surface.** It reads the existing `ai_review_log` rows (already redacted) and
  the existing `normalize_question` key — no new storage, no new privacy exposure.
- **Demand-ranked, not chronological.** `!aireview list` is newest-first; this is
  most-asked-first, which is the order you actually want to fix things in (the BTD6 QA arc fixed
  the *most-reported* misses first for the same reason).
- **Completes the loop.** PR #1569 made the backlog *workable*; this makes it *self-prioritizing*.
  Pairs naturally with a preset **hit-counter** (how often each preset is served) so dead presets
  can be pruned per the Q-0105 "delete if unreliable" discipline.

## Seams it would touch (grounding)

- **`services/ai_review_log_service.py`** — a read-model query: group unreviewed `unknown` rows
  by normalized question key, count within a window, return any over a threshold. (The export
  path already proves the read shape.)
- **A trigger** — cheapest is a daily pass on the existing `HealthMaintenanceCog`-style loop (or
  piggyback the review-channel poster): compute the over-threshold set, post a digest, dedupe so
  the same suggestion isn't re-posted every day.
- **No new table** — suggestions are derived, not stored (or, if dedup needs state, a tiny
  `suggested_at` marker column on `ai_review_log`).

## The hard part

- **Noise control.** The threshold + window must be tuned so the digest is a few high-signal
  rows, not a wall. Start conservative (e.g. ≥3 in 7 days) and make it a setting.
- **Normalization is load-bearing.** Frequency only works if "same question" is reliable — which
  is exactly why this session put the key in a shared `normalize_question` (mention/emoji-stripped,
  case/whitespace-folded). Paraphrases still count as distinct; that's acceptable (a preset is
  exact-match anyway).

## Lifecycle

Routing candidate for `docs/planning/` as a small AI slice once the loop has real usage. Cheap
enough to be a near-term planning slice on its own; the read-model query is the whole core.
Dedup-checked `docs/ideas/` — distinct from `ai-self-curated-memory-notebook` (that is the *AI*
self-writing notes; this is *frequency analytics over the existing operator log*) and from the
preset layer itself (that is authoring; this is *prioritizing what to author*).

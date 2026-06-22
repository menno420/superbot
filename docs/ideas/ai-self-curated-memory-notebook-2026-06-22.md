# AI self-curated memory notebook — a write-back learning seam for the bot's AI

> **Status:** `ideas`. **Not a plan, not approval.** A capture doc so the idea lives in
> the repo instead of in chat. Source code, the binding contracts, and
> `docs/current-state.md` always win over anything here.
>
> **Subsystem:** ai
>
> **Owner-dropped (2026-06-22).** Surfaced in the same conversation that produced this
> session's treasury build; the maintainer explicitly asked to document it. Directly
> inspired by the *extended-mind / two-part memory* framing now recorded in
> `docs/collaboration-model.md` § "Why the written record is the agent's memory" — this
> idea asks: **what if the bot's own in-product AI got the same kind of curated memory the
> agent network already has?**

## The idea in one paragraph

Give the bot's in-product AI a **narrow, audited, write-back seam**: a dedicated table it may
append small notes to — e.g. *"a user corrected my claim that X; the right answer is Y"*, or any
durable, non-personal fact it judges worth remembering. Nothing is trusted automatically. The
notebook is a **staging buffer**, not live memory: entries accumulate, then a human (or a later
review session) periodically reviews them and decides which are worth **promoting** into the bot's
real AI memory — the system instruction, a cached knowledge layer, or a deterministic answer
preset. The point is to close a learning loop the bot currently lacks: today a correction in chat
is lost the moment the context window rolls; here it survives long enough to be evaluated.

## What writes an entry (three triggers)

1. **AI-judged value.** Mid-response, the model decides something is worth remembering and emits a
   note (a tool-call the AI stage can make — the same shape as its other tool uses).
2. **Correction trigger.** When a user explicitly corrects the bot ("no, that's wrong, it's
   actually…"), that exchange is captured directly — corrections are the highest-signal entries.
3. **Daily cron.** A scheduled pass (the bot already runs maintenance tasks, e.g.
   `health_maintenance_cog`) that can summarize/dedupe the day's raw notes into cleaner candidates.

## The eventual payoff (why it's worth the plumbing)

The reviewed-and-promoted notes feed three escalating uses:

- **Instruction tuning** — recurring corrections become edits to the AI's system instruction, so the
  bot stops repeating a mistake class.
- **Cached layers** — frequently-confirmed facts become a preloaded knowledge layer the AI reads
  without re-deriving.
- **Deterministic answer presets** — for questions the bot answers the same way every time, store the
  *exact* vetted response and serve it **preloaded, with zero API call** — faster, cheaper, and
  perfectly consistent. (This is the most concrete near-term win and could ship independently of the
  rest.)

## Seams it would touch (grounding)

- **`ai` subsystem** — the AI cog / stage where responses and tool calls are produced is where the
  write trigger and the preset-lookup short-circuit live.
- **A new audited mutation service + table** — per the architecture rules, *no* direct DB writes from
  cogs/views; the notebook write must go through a `*_mutation.py` service and emit
  `audit_events.emit_audit_action()`. The table is append-only staging
  (`ai_memory_notes`: id, guild_id, trigger_type, note_text, status[`pending`/`promoted`/`rejected`],
  created_at) — never the live instruction itself.
- **A review surface** — a small operator panel (or a website view) to read pending notes and
  promote/reject them. Promotion is the human-in-the-loop gate that keeps the bot from teaching
  itself nonsense.

## The hard part (where the design effort goes)

- **Privacy is the gating constraint, stated up front by the owner: explicitly do NOT store user
  data / PII.** A note must capture the *lesson*, never *who said it* or personal content. This needs
  a hard scrub/validation layer (no user IDs, no message-author identity, no quoted personal info in
  the stored text) and probably a default-deny shape: store the corrected *fact*, drop everything
  else. This is the make-or-break — get it wrong and it becomes a liability.
- **Trust / poisoning** — anyone can "correct" the bot; an unreviewed note must never auto-promote.
  The `pending → promoted` human gate is the defense, but the volume of pending notes needs to stay
  reviewable (the daily-cron dedupe helps).
- **Self-reinforcing error** — a wrong promoted preset is served confidently forever until someone
  notices; presets need provenance + an easy un-promote, mirroring the Q-0105 "disposable, delete if
  unreliable" discipline already used for agent tooling.

## Suggested phasing (route, don't build yet)

1. **Preset layer first** (smallest, highest-confidence, independently valuable): the
   deterministic-answer-preset lookup + an operator-curated preset table. No AI self-write — humans
   author presets. Proves the "preloaded exact answer, no API call" win with zero privacy surface.
2. **Capture + review** — the `ai_memory_notes` staging table, the correction trigger, and the review
   panel. Still no auto-promotion; humans promote into presets/instruction.
3. **AI self-write + cron dedupe** — the model emits its own notes; the daily pass cleans them.
4. **Instruction/cached-layer promotion** — the heaviest, most sensitive step; gate hardest.

## Lifecycle

Routing candidate for `docs/planning/` once the privacy-scrub design is sketched (that is the
prerequisite that makes the rest safe). Phase 1 (the preset layer) is small enough to be a near-term
planning slice on its own; phases 3–4 deserve a router DISCUSS pass before building, since
"the bot edits its own instruction" touches autonomy boundaries.

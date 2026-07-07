# Adopt the substrate-kit's stance classifier into this repo's live workflow

> **Status:** `ideas` — session idea (2026-07-07, Q-0089, from the understand-and-reflect
> rule session, Q-0254). **Subsystem:** agent workflow (S3 AI-memory / kit-lab program).

## The gap this closes

Answering the owner's question ("is there a guide for how a session classifies its task and
picks an efficient method?") surfaced that the substrate-kit already ships exactly this — five
"stances" (`question` / `analysis` / `debug` / `review` / `plan`), each with its own
reading-route, tool-scope, and output contract (`substrate-kit/src/engine/stances/stances.py`).
It is fully built and tested (part of the 440-test suite) but **dormant**: nothing in this
repo's live `.claude/CLAUDE.md` or `AGENT_ORIENTATION.md` tells a session to classify an
incoming message into one of these stances first, and no hook enforces or even advises it.

## The idea

Wire the kit's stance mechanism into this repo's actual live workflow (not just the kit's own
self-test suite): a session states its active stance early (or a lightweight classifier infers
it from the first message), the stance's reading-route becomes the first thing read, and the
PreToolUse advisory (`is_out_of_stance`) warns — never blocks — when an action falls outside
the declared stance's tool-scope (e.g. an edit while nominally in `review`). This gives "what
kind of task is this, and what's the efficient method" a real, mechanical answer instead of
relying on a session's own judgment every time.

## Why it's worth having (and why it's not done here)

This session's understand-and-reflect rule (Q-0254) closes the *narrower* gap — confirming
understanding before work starts. The stance classifier is the *broader* mechanism the owner's
question was really asking about, but adopting a kit subsystem into this repo's live workflow is
real scope: it touches `.claude/settings.json` (hooks — owner-gated per Q-0106) and changes how
every session opens. That's a design decision for the kit-lab program
(`docs/planning/kit-lab-founding-plan-2026-07-07.md`), which already owns the kit's evolution
and has the benchmark machinery (B1's A/B harness) to actually measure whether adopting it
helps — rather than a quick chat-directed change deciding it unmeasured.

## Routing

Structure into the kit-lab program's backlog when it has capacity (post KL-1/KL-2): a small
experiment — does declaring a stance at session start measurably reduce wrong-tool-use vs. not
declaring one? — using the same paired-run methodology the founding plan already specs for B1.

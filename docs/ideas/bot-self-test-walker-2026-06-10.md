# Bot self-testing: the command walker + AI eval mode

> **Status:** `ideas` — owner idea, captured 2026-06-10 (brainstorm round 3, the
> vision-capture conversation). **Not a plan, not approval.** Natural sequencing:
> pairs with the commissioned **untested-surface testing checklist** session
> (roadmap session queue item 1) — the checklist *enumerates*, this *automates*.

## The owner's idea (2026-06-10, lightly condensed)

> "Would it be possible that the bot actually test itself? … you could
> temporarily create event based actions that would trigger every command to
> fire in sequence, so one command triggers the next, and for AI you could
> probably inject prompts at system level, so AI gets prompted on top of its
> existing harness something like 'what can you tell me about btd6' but that
> question would also have to be triggered per on event."

Two adjustments from the agent (accepted in-conversation, see the session log):
**(1)** bots can't drive themselves through Discord messages (the standard
`author.bot` guard ignores them) — the right mechanism is **in-process synthetic
invocation**: a driver iterates the command registry and calls each command's
callback with a synthetic ctx/interaction whose `send` *captures* output.
**(2)** a **driver loop** beats event-chaining for sequencing (deterministic
order, per-step timeout, one report); the EventBus is instead the **witness** —
the walker asserts that each action emitted its expected catalogued event.
And one upgrade: build it **permanent and owner-gated**, not temporary — wired
to the command ledger, every future command joins the walk automatically.

## Why SuperBot is unusually well-positioned for this (existing substrate)

- **Command surface ledger** (`test_command_surface_ledger.py` family) — a
  machine-readable inventory of every command: the walker's worklist.
- **Help catalogue / projection** (#657) — stable-keyed inventory of every
  surface + reason-coded availability: tells the walker what *should* be
  invocable for a given audience.
- **Governance audience simulation** (Q-0045, #632: `GovernanceContext.member_tier`,
  simulation-labeled) — walk the same command as member/staff/admin without
  real accounts.
- **EventBus + delivery stats (#681)** — assertion by observation: "did
  `audit.action_recorded` fire?"; per-event delivery stats give the walker a
  built-in scoreboard.
- **Audited mutation seams** — every write the walker triggers is recorded;
  a scratch **test guild** + the `guild_lifecycle` delete hooks give clean
  setup/teardown.
- **AI answerability tools (#639)** — `btd6_answerability` / tool catalog =
  machine-checkable ground truth for AI answers.
- **Q-0086 provider keys in session env** — the AI eval mode can run the
  *real* pipeline: scripted prompts (the owner's example: "what can you tell
  me about btd6") through the natural-language stage, asserting grounding
  presence, source labels, and no-refusal — cost-bounded by a small fixed
  prompt set (Q-0082 ceiling applies).

## Shape (when structured into a plan)

1. Synthetic-invocation core: fake ctx/interaction + capture-send + scratch-guild
   scoping + owner-only `!selftest` entry (env-flagged off in prod by default).
2. Ledger-driven walk with per-command expectations (responded? embed shape?
   expected event observed? denial copy for under-tier audiences?).
3. View/button coverage: invoke callbacks synthetically (authority re-check at
   callback time is already a repo rule — the walker proves it holds).
4. AI eval mode: fixed prompt battery through the real pipeline (keys present),
   property assertions, spend cap per run.
5. Report: one embed/markdown summary (pass/fail/skipped + event-witness table) —
   the caretaker's (workflow §10 Stage 1) nightly probe set.

## Honest limits (stays human — feeds the checklist session)

Visual/UX correctness (embed *looks right*, button placement *feels right*),
true multi-user flows (duels/trades beyond two synthetic members), Discord
client rendering, and "is it fun". The walker shrinks the untested surface;
the checklist documents the human-only residue (owner walks + screenshots).

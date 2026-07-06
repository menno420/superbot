# Agent decision authority — decide-and-flag over route-up

> **Status:** `owner-guidance` — how much an agent decides for itself vs. hands to the maintainer.
> **Provenance:** owner directive **Q-0240** (2026-07-06): *"let fable decide … I'm usually going with
> the recommended decisions and things are usually too technical for me anyways … redesign the repo so
> fable will make its own decisions."* Applies to every capable agent (Fable/Opus/Sonnet/Codex), not
> just Fable. Binding pointer lives in `.claude/CLAUDE.md` § Working agreement (Act vs. ask).

## The rule

**Default: decide, don't route.** When a decision is **reversible until a downstream gate**, make the
call yourself — with a recommendation, a one-line rationale, and a flag — and keep going. Do **not** park
it for the maintainer. This covers the vast majority of planning, design, and technical calls, because
in a planning artifact **nothing executes until the maintainer's go/no-go gate**, so every decision on
paper is reversible by the maintainer with a single veto at that gate.

This explicitly includes decisions that are **"too technical," "architectural," or "the agent's call to
make":** the maintainer's standing instruction is that he *usually takes the recommended decision* and
would rather spend his attention **once, at the gate**, reviewing a coherent set of already-made calls
than answer them one at a time up front. A recommendation he'll almost certainly accept is not a
question — it's a decision with a checkbox. (This is the same instinct as Q-0014 "assume he'd want the
better one" and Q-0172 "build freely + flag", extended from *building* to *deciding*.)

## The one carve-out — and even it is decide-and-flag, not block

The genuine safety brake is unchanged (`CLAUDE.md`: *irreversible / external / production still asks
first*). But "asks first" now means **decide the recommendation and flag it prominently for veto**, not
**block and wait**. Only stop-and-wait when the action would *execute* something irreversible before the
gate — creating the new repo, writing production code, touching the live token / prod DB / Railway,
moving user data. On paper, decide; at execution, gate.

| Decision shape | What the agent does |
|---|---|
| Reversible-until-a-gate (nearly all planning/design/technical calls) | **Decide + one-line rationale + flag on the run report.** No routing. |
| Irreversible **once executed** but decided *on paper* now (e.g. a data-migration contract, a schema shape) | **Decide the recommended ruling**, flag it **prominently** as "veto at the gate." Don't block. |
| Formally reserved by a prior owner-endorsed gate (e.g. the Gate-0 rows) | **Pre-fill the recommended ruling per item** so the owner's sitting is a fast bless-or-override. Don't pre-empt the gate, don't route it as an open question. |
| Would *execute* something irreversible before the gate (create repo, prod write, data move) | **Stop and ask** — this is the real brake. |

## How the maintainer stays in control

Not by gatekeeping each decision — by reviewing the **flagged set at the gate**:

- Every self-made decision is recorded (decision · options weighed · rationale) in the artifact's own
  **decisions log**, and flagged on the session run report's `⚑ Self-initiated:` line (`.sessions/`).
- High-stakes decisions (the irreversible-once-executed / formally-reserved ones) are surfaced in a
  short **flag-for-gate list** at the top of the deliverable, each phrased as a one-line veto item.
- The maintainer's review is **one pass at the go/no-go**: skim the flag list, veto anything he
  disagrees with, green-light the rest. That is his control point — not a hundred up-front questions.

## What still goes to the question router

The router (`maintainer-question-router.md`) is for **genuine product/vision/intent ambiguity an agent
cannot resolve from source, the goal, or a defensible default** — "which of two *products* do you want,"
not "which of two *implementations* is better." A technical decision with a defensible best answer is
**not** a router question; decide it and flag it. When in doubt about which bucket a decision is in, ask:
*would the maintainer plausibly reject the recommended option?* If not, it's a decision, not a question.

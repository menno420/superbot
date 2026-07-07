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
| Would *execute* something irreversible before the gate (create repo, prod write, data move) | **Stop and ask** — this is the real brake. *(For the rebuild program this last row is overridden — see Q-0241 below.)* |

## Q-0241 — the rebuild override (never-wait, live-test, silence=consent)

> **Provenance:** owner directive **Q-0241** (2026-07-07): *"get rid of the owner gates/blockers … it
> should just build everything in logical order and live test it so I can see the results in a server,
> but it should never wait for me, if I don't say something about it it should be considered done."*
> Applied in-session (Q-0106 exception). Full block: `maintainer-question-router.md` Q-0241.

Q-0240's *last table row* — "stop and ask before executing something irreversible" — is the owner's one
retained brake. **For the rebuild program (building `superbot-next` + porting the bot), Q-0241 removes
even that brake.** The owner's control shifts from **approval-before-execution** to
**reaction-after-visibility**:

- **No owner gates.** The rebuild's G1 go/no-go sitting, G2 "owner accepts the verdict," and every 👤
  owner-gated step (incl. "create the repo") are retired as blockers. Build everything **in logical
  order**; do not pause between phases for sign-off.
- **Live-test replaces owner verification.** Each piece is exercised **live in a real server** (an agent
  drives all commands in a live bot session). Live-green is the coordinator's own gate; the "does it
  work?" question is never routed up. The owner *sees results in the server*.
- **Silence = consent = done.** Never wait for the owner. If he says nothing about a piece, it is
  accepted. His control point is **reacting to what he sees** — a message stops or redirects; absence of
  a message is approval.

**The reversibility rider (decide-and-flag, vetoable — not a gate).** Reaction-after-visibility only
bites while the thing is still reversible when the owner reacts. So the **destructive tier only** (prod
data import over real balances/audit, the CUT-3 token swap, deleting old-bot data) executes via the
**reversible-equivalent path the plan already specifies** — shadow-first / restored-snapshot DB, the
**N=7d rollback window** (Q-D15), the declared-loss **reverse-import valve** (F-1/F-2). This adds **no
pause** (not a gate); it just keeps a reaction window open. Owner may veto the rider for straight
destructive execution.

**Scope.** Q-0241 governs the **rebuild program**. For the **live production bot**, the Q-0213
`*Delete`/`*Restore` ask-first brake and prod-data safety still stand until the owner generalizes this.
Merge=deploy still requires **CI green** (never-wait ≠ bypass CI). Decisions are still recorded + flagged
(Q-0240) so the owner's after-the-fact review has a trail.

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

# SuperBot fresh-rebuild vision — captured discussion (2026-06-30)

> **Status:** `ideas` — maintainer vision, captured verbatim + Claude's verified counter-research
> (with two post-merge corrections from the maintainer folded in — see finding 9 and the Fable 5
> section). **Not approved for execution.** The maintainer is explicit: this needs thorough
> multi-agent planning/review/documentation, his own detailed keep/change specification, and is
> gated on Fable 5 availability — **confirmed still gated** (withdrawn 2026-06-12, not yet
> reintroduced) — before any work starts. This document exists so the reasoning from a long live
> conversation isn't lost — mirrors the precedent set by `portable-agent-memory-package-2026-06-12.md`
> and `autonomous-improvement-loop-vision-2026-06-12.md`.
>
> **⚠️ UPDATE 2026-07-02:** the "gated on Fable 5 / not reintroduced" status below is **superseded** —
> Fable 5 was **redeployed 2026-07-01** (verified live), so that gate is **cleared**. The
> research-grounded plan that supersedes/extends this vision is
> [`../planning/fresh-rebuild-strategy-2026-07-02.md`](../planning/fresh-rebuild-strategy-2026-07-02.md).

## Why this document exists

A long in-chat conversation (2026-06-30, Claude Sonnet 5) covered: a session-start orientation-cost
audit, a docs/router cleanup plan (shipped: `orientation-cost-reduction-plan-2026-06-30.md`, PR
#1586), a 16-agent parallel audit of stale historical docs, and — the largest thread — the
maintainer's case for a **full fresh rebuild of SuperBot**, argued and counter-argued across several
turns with real verification on both sides. That reasoning is expensive to reproduce. The maintainer
asked explicitly: *"I want you to verify what I've claimed and to give your honest opinion about
this"* — so this captures both the claims **and** the verification, not just a conclusion.

## The proposal, as stated by the maintainer

A full rebuild of SuperBot as a new repository, **not imminent** — gated on thorough planning first.
Restated faithfully from the conversation:

- **Keep all the working code and logic**; port it incrementally, testing/verifying piece by piece
  against the current repo as a reference — not a from-scratch reimplementation of behavior.
- **The current repo becomes a frozen reference** — kept unchanged, used to learn from and compare
  against, not actively developed once the new repo starts.
- **The AI-memory system (the portable substrate kit) finishes first**, as a standalone, reusable
  package/single-file — "so the fresh repo starts entirely from the current state of things." The
  maintainer explicitly reprioritized: bot is "mostly production ready," so it's time to focus on the
  AI-memory project now.
- **Separate the two projects** that currently coexist in one repo — the bot and the AI-memory
  system — "this AI memory system I'm building is intertwined with the bots code." **Refined later in
  the conversation:** not a claim of code-level coupling — the maintainer clarified this means the
  memory system's *design process* has only ever happened *while* simultaneously building the bot
  (every session working on AI-memory also touched the bot), which is good for grounding it in real
  use cases but means it's never been proven to work efficiently from a true cold start — something
  structurally untestable this far into the repo's life. The maintainer was explicit this is a
  secondary factor, not a main reason.
- **A cleaner, deliberately-designed question router** — "I really like things to be logical,
  structured, in the correct order, right now the questions don't follow any order or logic, many
  wouldn't even remain as questions but would get a logical place in its own doc, without
  duplication."
- **Code built "from knowledge instead of trial and error"** — designed once, as one complete
  picture, using everything learned across ~2 months / 1500+ PRs of meaningful (Claude-driven) work
  — see the correction in finding 9 below — instead of accumulated incrementally. Named root causes:
  the bot was "made by an accumulation of older bots, multiple
  agents, a lot of different ideas and workflows, contradicting files, misunderstood ideas, code that
  exists because of certain things that happened, fixes implemented because an agent worked in a
  different way than expected." Expected outcome: code that can be changed or left out entirely,
  functions that fit better in a different file, deduplicated/consolidated logic currently spread
  across multiple files.
- **Execution model:** not soon; gated on (a) a large sequence of AI-agent planning, reviewing, and
  documenting passes, (b) the maintainer's own detailed description of what to keep/change, (c)
  waiting for Fable 5 — maintainer's stated expectation: it would fix current errors and
  architectural debt and produce a better-sorted question router, (d) a logical, structured sequence
  of roughly ~100 PRs once it starts.
- The maintainer's framing: *"to refactor the current repo would be like patching up a broken plate
  with duct tape, and to recreate this project in a better way would be to melt old scrapmetal into a
  shiny new sword."*

## Claude's verified findings across the conversation

Organized by topic, in the order they came up. Every claim below was checked against the live repo
or live documentation, not asserted from priors.

### 1. The session-start orientation cost is real and measured
~25,593 words across the prescribed "any task" reading order (CLAUDE.md + collaboration-model +
current-state + AGENT_ORIENTATION + codegraph-usage + repo-navigation-map + repo-sector-map), before
a session even reaches its task-specific folio. `AGENT_ORIENTATION.md` itself is 484 lines against
its own stated ~250-line cap — already 2× over, unenforced by any checker. → addressed by
[`orientation-cost-reduction-plan-2026-06-30.md`](../planning/orientation-cost-reduction-plan-2026-06-30.md)
(PR #1586, merged), independent of the rebuild question.

### 2. The router's size/navigability problem is real but its fix doesn't require a new repo
`docs/owner/maintainer-question-router.md` is 7,854 lines / 67,182 words / 212+ unique `Q-NNNN`
blocks; only 76 of 217 blocks (35%) are confidently machine-classified as decided, 11 open, and **130
(60%) are unclassified** due to inconsistent status-marker formats. The archive mechanism
(`maintainer-question-router-archive.md`) exists and was explicitly decided as the fix 2 days before
this conversation (Q-0210, 2026-06-28) — but is essentially unused (216 words, 2 entries) and two
reconciliation passes have gone by without the promised bulk archive happening. **Q-0210 also already
settled that renumbering is unsafe in the live repo** — 9,690+ plain-text `Q-NNNN` citations span the
repo, and physically moving/renaming a block would orphan them. A fresh repo's router would not carry
this constraint (it starts at zero citations) — this is the one place "start fresh" genuinely removes
a real risk rather than just feeling cleaner.

### 3. "Historical" docs sitting outside `docs/archive/` are not drift — verified the opposite
Initially mischaracterized 129 in-place `historical`-badged docs as an unexecuted archiving process.
`docs/archive/README.md` states the **opposite** is the documented, intentional convention: "most
retired plans/audits are not moved into this folder — they are rebadged `historical` **in place** (so
their inbound links stay intact)." Moving them would require fixing every inbound relative link for
the same modest payoff already achieved by the `docs/planning/README.md` active/historical index.
**Self-correction recorded, not just the original (wrong) claim.**

### 4. A 16-agent audit of those 111 historical docs (corrected list, false positives removed) found genuine value retention
Ran a classify → adversarially-verify pipeline (37 agents, ~2.7M tokens) against the accurate set of
111 in-place historical docs. Result: only **7 (6%)** survived adversarial verification as truly safe
to delete; 14 initial "delete" votes were refuted (broken inbound links, a sole-source fact, etc.); 45
need condensing (real value, too long); 45 are fine as-is. **Evidence for, not against, incremental
cleanup**: even deliberately hunting for dead weight, 94% of what looked deletable wasn't, once
checked. *(The 7 confirmed-delete files are still awaiting the maintainer's go-ahead — listed in the
session, not yet executed.)*

### 5. The portable substrate-kit is not "stalled because it's hard" — it's ~60% built and losing a prioritization fight
Read the actual execution log (not just `current-state.md`'s one-line summary). Survived **10
independent external review rounds** (ChatGPT deep-research, Gemini, Grok, Hermes ×2). PRs 1a, 1b, and
most of PR 2 (stances #805, skills #811, personas #812, the stance-guard hook #813) are shipped and
tested (117+ kit-local tests green as of the last logged entry, 2026-06-13). What remains: PR 2's
defined remainder (integration-mode behaviors, drift triggers, the full contract-template set) and all
of PR 3 (self-maintenance loop, review seam, distribution polish) — plus the final "extract to a
standalone repo" step, which the plan itself flags as **an owner action**, not agent-buildable work.
`current-state.md`'s "demoted from the plannable queue after its fourth band-carry" means it kept
losing the prioritization contest against live feature work across four reconciliation bands — not
that it failed.

### 6. Code-level (not just docs-level) inconsistency is real and independently evidenced
The maintainer's claim that the bot accumulated contradictions, duplication, and incident-driven
patches from many agents/eras checks out with concrete, found-this-session evidence: the triple `give`
command collision that crash-looped production (Q-0211); the `round_composition` silent name-shadow
collision (Q-0200); the architecture checker's own tracked-and-grandfathered debt (49 warnings across
956 application files: 13 views not on the standard base class, 31 known layer-boundary violations,
5 raw-SQL-outside-`utils/db` violations); and the recurring need for dedicated "consolidation fleet"
cleanup passes (settings centralization, an `edit_in_place` backlog cleared by three parallel
workers) — evidence that locally-scoped incremental work genuinely generates this class of debt, not
just an impression.

### 7. The substrate-kit and the bot are NOT code-coupled
Checked directly: `substrate-kit/` (56 files, ~3,900 lines) and `disbot/` (956 files, ~237,000 lines)
have **zero cross-imports in either direction**. They already are two independent codebases sharing
one `.git` and one CI pipeline — separating them is closer to a mechanical extraction (already the
kit's own stated end-state: "liftable to its own repo as-is") than an architectural untangling. This
directly informed the refinement in point 2 of "The proposal" above — the maintainer's restated
"intertwined" claim (shared development *history*, not shared *code*) survives; the original
code-coupling reading does not.

### 8. Repo composition, for scale context
`disbot/`: 956 files / 27MB. `tests/`: 1,103 files / 25MB — nearly as large as the application code
itself, a real cost a rewrite would need to re-derive or risk under-covering. `docs/`: 529 files /
8.4MB. `disbot/data/` (committed game-data JSON): 7.1MB of a 263MB total repo (~2.7% — real, smaller
than implied as a "noise" source). CodeGraph complexity: average cognitive complexity 1.5 / cyclomatic
2 (low, healthy on average) against a max cognitive complexity of 135 and a minimum maintainability
index of 9.9 (real pockets of debt, not a pervasively bad codebase) — average MI 65.1, the "moderate"
band, room to improve but not alarming.

### 9. Correction (maintainer, post-merge): the repo's age is not the same as its meaningful-work age
Claude's original framing throughout this conversation treated the repo as **~10 months old**
(inferred from a 2025-08-10 initial-commit reference) and used that figure as part of the case against
a rewrite ("~10 months of continuous, production-tested development"). The maintainer corrected this
directly: *"this repo is not 10 months old (or maybe it actually is) but the actual work I've been
doing on this with claude is about 2 months now, before that it basically was just some loose edits
made by chat gpt, which I don't consider to be really counting — all meaningful work on this repo has
been done in less than 2 months."* Two things follow:

- **The velocity is far higher than the original framing implied.** ~1,500+ PRs in ~2 months of
  meaningful work is roughly 5× denser than the same PR count spread across 10 months — only possible
  with a continuous multi-agent autonomous pipeline, not a human-paced team. This is genuinely
  encouraging evidence *for* the rewrite's feasibility, not against it: if a comparably-resourced
  rewrite can sustain a similar pace, it could plausibly reach feature-parity in a timeframe closer to
  the original ~2 months than to a 10-month estimate — the volume-of-code risk (point 8 above, 956
  files / 27MB of `disbot/`) is unchanged, but the *time cost* to reproduce it is much lower than
  Claude's original framing suggested.
- **The pre-Claude "loose ChatGPT edits" period may itself be a named source of the debt the
  maintainer described** — "accumulation of older bots, multiple agents... contradicting files,
  misunderstood ideas" reads as plausibly including that earlier, explicitly-not-counted layer, not
  just variance across Claude sessions. If so, it's a concrete, identifiable contributor to the
  inconsistency claim in finding 6, not just a general impression.

This is a real revision to Claude's risk assessment, not a cosmetic date fix — flagged here so a
future reader doesn't inherit the original (wrong) framing from the rest of this document.

## Where Claude and the maintainer landed

- **Agreed, no dispute:** shifting focus to the AI-memory project now (bot near-production-ready) is
  sound prioritization. Finishing + extracting the portable substrate-kit is valuable on its own,
  independent of whether SuperBot itself is ever rebuilt, and is closer to done than its one-line
  summary suggested.
- **Claude's original counter-proposal** ("fork the repo, then run a comprehensive, test-verified
  consolidation pass using the existing suite as a continuous correctness oracle, instead of
  re-deriving behavior from a blank page") was offered as lower-risk but does not fully address the
  maintainer's core motivation, which the maintainer was explicit about by the end: it is not
  primarily about defect density (which is fixable in place and partially over-stated in its
  supporting reasons, per the verification above) but about **execution order** — "we now have the
  right idea, but what we need is to execute this idea as one complete picture, instead of adding
  pieces like a puzzle." That is a claim about *how the artifact should come into being*, which
  verification can't resolve either way — a perfectly debt-free, incrementally-refactored codebase
  would still not be "designed once," by definition.
- **Open / not yet agreed:** whether "prove the AI-memory system works efficiently from a true cold
  start" requires rebuilding SuperBot itself, or could be validated more cheaply by pointing the
  near-finished portable kit at a small new project first (Claude's suggestion, not yet accepted or
  rejected by the maintainer).
- **Timeline, maintainer's own words:** not imminent. Gated on (1) finishing the portable kit, (2) a
  large multi-agent planning/review/documentation sequence, (3) the maintainer's own detailed
  keep/change specification, (4) waiting for Fable 5 — **confirmed correct, see below: it is currently
  unavailable, not the GA status Claude's documentation research initially (and wrongly) reported.**

## Fable 5 research (2026-06-30, verified against live docs — then corrected against live product evidence)

The maintainer's stated plan explicitly waits for Fable 5 "to be available again," expecting it to
help fix current errors/architectural debt and produce a better-sorted question router.

**Initial research (via `platform.claude.com` documentation) reported Fable 5 as already generally
available.** That research was wrong in practice, and the correction is itself a useful lesson, not
just a fact fix:

- **What the docs said:** *"Claude Fable 5 and Claude Mythos 5 both become available on June 9, 2026
  … Claude Fable 5 is generally available on the Claude API, Claude Platform on AWS, Amazon Bedrock,
  Google Cloud, and Microsoft Foundry."* No mention of any subsequent change in status.
- **What's actually true (maintainer, live product screenshot, 2026-06-30):** Fable 5 launched June 9
  but **was removed from public availability on June 12 — three days later — and has not been
  reintroduced as of 2026-06-30.** The live Claude model picker shows it greyed out, labeled "Currently
  unavailable." Claude has no visibility into *why* it was withdrawn (an incident, a safety-classifier
  issue, a capacity decision — anything would be speculation) and does not claim to know.
- **The methodology lesson, worth keeping for next time:** documentation describes the *designed*
  state of a launch, not necessarily its *current operational* status — an incident-driven rollback a
  few days after a GA announcement may never get reflected in the docs page at all, since the docs
  describe what the feature is supposed to do once available, not a live status board. A screenshot of
  the actual product surface the user is looking at is strictly more authoritative than a docs page for
  "is X available right now" — Claude should have led with that caveat instead of stating availability
  as settled fact from a single doc fetch.
- **Net effect on the plan:** the maintainer's original premise was correct. The "wait for Fable 5"
  gate has **not** cleared — it's exactly as open as the maintainer believed before this research
  started. Re-check the live model picker (not docs) when reassessing this gate in the future.
- **Model ID:** `claude-fable-5`. Anthropic's most capable widely released model, built for the most
  demanding reasoning and long-horizon agentic work — once it's actually selectable again.
- **Context window / output:** 1M token context window (the default, also the maximum), up to 128K
  output tokens per request.
- **Pricing:** $10 / million input tokens, $50 / million output tokens — well above Opus 4.8
  ($5/$25) and Sonnet 5 ($3/$15 list, $2/$10 intro through 2026-08-31).
- **What's different from Opus-tier (relevant if used for a rebuild-scale effort):** adaptive thinking
  is *always on* (no disable option); the raw chain of thought is never returned (only an optional
  summarized version); it includes **safety classifiers that can decline requests** —
  `stop_reason: "refusal"` as a normal HTTP 200, not an error — with fallback-to-another-model options
  (server-side, client-side middleware, or manual); requires 30-day data retention (incompatible with
  zero-data-retention orgs); same tokenizer as Opus 4.8 (token counts roughly unchanged migrating from
  Opus 4.7/4.8). Positioned for exactly the kind of work this rebuild would be: long-horizon,
  high-reasoning, large-scope agentic execution — individual requests on hard tasks can run many
  minutes, and prompting guidance favors giving the full task spec up front rather than prescriptive
  step-by-step instructions.
- **No claim made about whether it would actually "fix all current errors and architectural debt"** —
  that's the maintainer's own expectation about a future capability, not something this research can
  verify in advance.

## Open threads / next steps

- The maintainer's own detailed keep/change specification — not started.
- Extracting `substrate-kit/` into its own repo — available to start now (zero code coupling found),
  independent of the bigger rebuild decision.
- Re-check the live Claude model picker periodically for Fable 5's actual availability. **UPDATE
  2026-07-02: Fable 5 was REDEPLOYED 2026-07-01** (Anthropic, "Redeploying Fable 5"; global on Claude
  Platform / Code / Cowork, cloud phasing in) — **this gate is now CLEARED**, verified live. The prior
  "withdrawn since 2026-06-12, not yet reintroduced as of 2026-06-30" status is superseded.
- The 7 confirmed-safe-to-delete docs from the historical-docs audit (this session) — awaiting the
  maintainer's go-ahead, not yet executed.
- The 45 condense-candidate docs from the same audit — not yet scoped into a follow-up pass.
- Whether "prove cold-start efficiency" needs the full rebuild or can be validated by trying the
  near-finished portable kit on a small new project first — raised, not yet decided.

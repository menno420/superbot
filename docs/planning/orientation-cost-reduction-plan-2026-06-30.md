# Plan — reduce session-start orientation cost (CLAUDE.md narrative density + the overdue router archive)

> **Status:** `plan` — drafted 2026-06-30, owner-directed live in-chat. Not yet executed. Cross-check
> the live file state and `router_status.py` output before executing — every count below is a
> 2026-06-30 snapshot and several numbers (router size especially) are growing weekly.
> **Companion (2026-07-02):** [`memory-retention-and-context-economy-plan-2026-07-02.md`](memory-retention-and-context-economy-plan-2026-07-02.md)
> covers the axis this plan deliberately leaves open — delete-vs-archive policy, retention windows,
> and hard caps for the terminal corpus (.sessions/, historical plans, ideas, ledger tails). This
> plan stays authoritative for boot-path compression (CLAUDE.md · router · AGENT_ORIENTATION).

## Origin

Raised by the maintainer in-chat (2026-06-30): every session pays real, measurable time/tokens to
orient before doing anything, and a lot of what it reads is narrative explaining *why* a rule exists
rather than just the rule — including incident postmortems and Q-number deliberation history embedded
inline. Because every agent session is stateless, that narrative doesn't help it act correctly; it
mostly invites re-deriving/re-verifying settled conclusions instead of just following them. The
maintainer also specifically asked about the question router (large, append-only, hard to navigate)
and floated renumbering/reordering it.

**This plan replaces an earlier, narrower draft** (`claude-md-conciseness-plan-2026-06-30.md`, same
session) that only covered CLAUDE.md. Two things surfaced while expanding it that materially changed
the shape of the plan — both below.

## Two things this plan must not get wrong

**1. Renumbering the router is already a settled "no."** `Q-0210` (decided 2026-06-28, two days before
this plan) directly answered the maintainer's own worry about this: *"a lot of things are referred to
by question number, so [moving them] might confuse future agents."* The investigation behind that
Q-block found **9,084 `Q-0XXX` references across 1,307 files**, almost all as plain grep-resolvable
text (only one anchor-style link exists repo-wide). The decision: **numbers are never moved or
renumbered; size is managed by archiving old, fully-answered blocks** to
`docs/owner/maintainer-question-router-archive.md`, mirroring the proven
`current-state.md` → `current-state-archive.md` split. **This plan's router workstream is the
execution of that already-decided mechanism, not a new proposal.** (Re-verified 2026-06-30: total
mentions now ~9,690 across the repo, confirming the number is still climbing.)

**2. CLAUDE.md slimming is already a live, partially-shipped plan — for a different axis of the same
file.** `procedures-to-skills-conversion-plan-2026-06-17.md` (owner-approved, Batch 1 shipped as
#1029/#1093) moves **procedural runbooks** ("do these steps") out of CLAUDE.md into on-demand skills,
leaving a thin rule+pointer. Its own safety list explicitly protects the **"Working agreement"**
section's *principles* from being moved — they're continuously-relevant, not one-off procedures — and
its still-unshipped **Batch 2** already targets the **"Session & plan workflow"** section (claim work,
born-red, session enders) via skill extraction. **This plan does not duplicate that work.** It defers
to procedures-to-skills Batches 2–4 for "Session & plan workflow," and instead targets the one thing
that plan deliberately leaves untouched: the **narrative density inside "Working agreement" itself** —
compressing the *why* without moving or weakening the *rule*.

## Evidence (2026-06-30 snapshot)

| Item | Measurement |
|---|---|
| `.claude/CLAUDE.md` | 445 lines / 5,169 words; 32 unique `Q-NNNN` citations, 24 inline "owner directive/decision" mentions |
| — "Working agreement" section (lines 2–99) | 97 lines, 22% of file — heaviest narrative density of any *unprotected* section |
| — "Session & plan workflow" section (lines 150–324) | 174 lines, 39% of file — **out of scope here**, owned by procedures-to-skills Batch 2 |
| — CI-parity / CodeGraph / Architecture-rules sections | 115 lines, 26% of file — already terse/rule-like; the in-repo style reference |
| `docs/AGENT_ORIENTATION.md` | **484 lines** — exceeds its *own stated* "~250 lines or it's become a duplicate architecture doc" ceiling (line 483) by ~2×, unenforced by any checker |
| Full "any task" prescribed reading order (CLAUDE.md + collaboration-model + current-state + AGENT_ORIENTATION + codegraph-usage + repo-navigation-map + repo-sector-map) | **~25,593 words**, before a session even reaches its task-specific folio |
| `docs/owner/maintainer-question-router.md` | 7,854 lines / 67,182 words / 212+ unique `Q-NNNN` blocks |
| `docs/owner/maintainer-question-router-archive.md` | 26 lines / 216 words / 2 `Q-NNNN` — essentially unused despite Q-0210 establishing it as the mechanism 2 days prior |
| `scripts/router_status.py` classification (live, 2026-06-30) | 217 blocks: 76 confidently DECIDED, 11 OPEN, 0 PARTIAL — and **130 (60%) UNCLASSIFIED** (inconsistent/older status-marker formats the heuristic can't read) |
| Reconciliation passes since Q-0210 | band-#1530 and band-#1560 have both run **without** the bulk archive Q-0210 deferred to "the next reconciliation pass" — it's now two passes overdue |

## Goals

- Cut the *narrative* cost of session-start orientation without losing any rule, any provenance, or
  any cross-reference.
- Execute the already-decided router-archive mechanism (Q-0210) instead of leaving it perpetually
  deferred.
- Make the router's open/decided status machine-readable for the full file, not 40% of it.
- Close the gap where a doc states its own size budget (AGENT_ORIENTATION.md) but nothing checks it.
- Leave a durable, low-effort mechanism so this doesn't silently reaccumulate (the way the router did
  for two reconciliation passes, and the `current-state.md` callout did before its budget guard
  shipped).

## Non-goals

- No renumbering, no moving a Q-block's canonical text out of the router (only archiving — see above).
- No duplication of procedures-to-skills Batches 2–4 (the "Session & plan workflow" section).
- No change to any rule's substance — compression of explanation length only.
- Not self-executed silently: CLAUDE.md edits are owner-gated; the router-archive actuator should run
  dry-run-first with a reviewable diff, same posture as `trim_recently_shipped.py`.

## Workstream A — compress "Working agreement" narrative density (CLAUDE.md)

Scope: **only** the Working agreement section (97 lines) — explicitly *not* Session & plan workflow
(procedures-to-skills' turf). Apply the same target format proposed in the earlier draft:

1. State the rule as a short, imperative sentence.
2. Where a rule's boundary genuinely needs an example to apply correctly to a novel case, keep one
   short clause — not a paragraph of incident narrative.
3. Provenance becomes a bare trailing pointer: `(Q-0129)` instead of a restated paragraph of "owner
   directive Q-0129, 2026-06-14, full reasoning: …". The router entry already holds the full reasoning.
4. Target: ~97 → ~50 lines, zero rules dropped.

## Workstream B — execute the overdue router archive (Q-0210's deferred mechanism)

**B0 — normalize status markers (do this first).** 130 of 217 blocks (60%) don't classify under
`router_status.py`'s heuristic because of inconsistent/older leading-marker formats. Normalize each to
the house convention (`DECISION`/`DECIDED`/`ANSWERED`/`DIRECTED`/`APPLIED` = decided;
`OPEN`/`PROPOSED`/`PARTLY DECIDED`/`DISCUSS` = open) **without changing any decision content**. This is
mechanical and low-judgment, and it's the step that will tell us how much B3 actually shrinks the
file — don't assume the sizing target below until this runs.

**B1 — build the archive actuator.** A script (sibling to `scripts/trim_recently_shipped.py`) that:
finds blocks classified DECIDED/ANSWERED whose `Home:` line confirms the conclusion is routed
elsewhere (i.e., the router copy is provenance, not the only record); moves them to
`maintainer-question-router-archive.md` (oldest first, append-only there too); leaves a one-line
pointer stub at the original location (`Q-0NNN — archived, see maintainer-question-router-archive.md`)
so every plain-text reference still resolves by grep regardless of which file the block lives in
(exactly Q-0210's stated invariant). Dry-run mode first, reviewable diff, same posture as the
`current-state.md` actuator.

**B2 — build the gauge.** Extend `check_docs.py` (or a small sibling script) to measure the router's
live word/line count against a budget and warn, mirroring the existing `▶ Next action callout` guard
(6 KB budget, already shipped and visible in `check_docs` output today). Without this, the router will
hit another silent "40.5 KB wall" moment exactly like the callout did before its guard existed.

**B3 — run the actual bulk archive.** The step Q-0210 explicitly deferred to "the next reconciliation
pass" and that hasn't happened across two passes since. Run it for real, using B1's actuator.

## Workstream C — fix AGENT_ORIENTATION.md's self-violated budget

The file states its own ~250-line ceiling and is at 484. Trim toward that budget (tighten prose in the
"Reading order by task" tables, not remove routes — the routing function is the file's whole value) and
add a line-count check so a future session can't silently blow past the stated cap again unnoticed, the
same way nothing currently catches it today.

## Workstream D — propose (don't apply) a standing "shrink" rule

> **Settled by Q-0214.3 (2026-07-02, owner, live):** shrink duty = **checker + routine** (mechanical
> prunes via `check_retention.py --fix`, judgment prunes via the retention-debt routine issue) — the
> owner chose this over a per-session shrink ritual, so the DISCUSS proposal below is no longer
> needed. See `memory-retention-and-context-economy-plan-2026-07-02.md` §5. Original text kept for
> provenance:

The project has several mandatory session-end **growth** rules (Q-0089 idea-of-the-session, Q-0102
previous-session review, Q-0104 docs audit). There is no equivalently-weighted **shrink** counterpart,
and the evidence above (router unarchived for 2 passes past its own decided cadence; AGENT_ORIENTATION
silently 2× over its own cap) suggests permission-to-prune alone hasn't been sufficient. This workstream
is a **router DISCUSS proposal**, not a direct edit — CLAUDE.md rule changes are owner-gated by its own
rules — drafting the Q-block is in scope for this plan; deciding it is not.

## Suggested execution order

1. Re-check `docs/owner/claims/` and open PRs at execution time (standard practice — none of this is
   claimed as of 2026-06-30).
2. **B0** first — cheap, mechanical, and its result should inform whether the sizing target below needs
   revising before doing the heavier B1/B3 work.
3. **B1 + B2** — build the reusable tooling.
4. **B3** — run the bulk archive; this is the actual payoff for router navigability.
5. **A** — independent of B, can run in parallel.
6. **C** — small, can bundle with A or stand alone.
7. **D** — last; it's a proposal, not an implementation.

## Sizing targets

- Router: live size after B0+B3 is genuinely uncertain until B0 runs (60% of blocks are currently
  unclassified, so the true DECIDED-and-archivable count is unknown) — don't pre-commit to a number;
  let B0's actual classification result set the B3 target.
- CLAUDE.md: ~445 → ~400 lines from Workstream A alone (Working agreement only; Session & plan workflow
  shrinks separately whenever procedures-to-skills Batch 2 lands).
- AGENT_ORIENTATION.md: 484 → ≤250 lines, matching its own stated cap.

## Verification

- Scripted: every `Q-NNNN` citable in the router before B3 must still resolve afterward (either still
  live, or present in the archive the live pointer references) — a diff of the citation set, not manual
  spot-checks.
- Scripted: `grep -c "Q-[0-9]\{4\}"` counts across CLAUDE.md / current-state.md / ideas/README.md /
  roadmap.md before and after Workstream A — confirm no citation silently disappeared.
- Manual / adversarial: a second pass (ideally a fresh agent with no memory of drafting the compression)
  reads the result cold and confirms no rule's *meaning* changed, only its *explanation length*.
- `python3.10 scripts/check_docs.py --strict`, `check_quality.py --check-only` green throughout.

## Authorization / process note

CLAUDE.md is owner-gated; the router is append-only by convention. Both gates are satisfied here the
same way: the maintainer raised and directed this live, in-chat — CLAUDE.md's own stated exception
("the maintainer directs in-session… apply it directly and record the Q-number"). Whichever session
executes this should record it under the next available Q-number at execution time
(`scripts/router_status.py` reports the next free number), citing this plan doc as rationale.

## Suggested handoff

- Workstreams B0/B1/B2 are mechanical and low-judgment — fine for either model, or a subagent fan-out.
- Workstream A (judging what's load-bearing vs. narrative color in "Working agreement") and Workstream D
  (drafting a rule-change proposal) are where careful judgment matters most — recommend a high-reasoning
  pass on these specifically, per the maintainer's stated preference for that kind of work.
- Recommend Workstream A/C run as one contained, single-voice session (consistent editorial judgment
  matters more than parallelism on owner-gated content); B0–B3 can run as a separate, more mechanical
  session or fan-out.
- Re-check `procedures-to-skills-conversion-plan-2026-06-17.md`'s status before starting Workstream A —
  if its Batch 2 has shipped by execution time, re-measure CLAUDE.md's section sizes fresh rather than
  trusting this doc's snapshot numbers.

# Agent-memory system review — 2026-06-09 (one session's honest evidence)

> **Status:** `historical` — a dated assessment of the orientation/memory system
> **Superseded 2026-06-19 (was active):** Dated orientation/memory retrospective; cited as history by current-state. Do not act on this — current map: [planning/README](../planning/README.md).
> (CLAUDE.md → collaboration-model → current-state → journal → `.sessions/` →
> router → plans), written by the agent that ran the 2026-06-09 multi-lane
> session (PRs #624/#626) at the maintainer's request. Findings reflect one
> session's experience; weigh accordingly. Companion to
> [`repo-review-2026-06-09.md`](repo-review-2026-06-09.md), which assessed the
> *docs*; this assesses the **memory system in use**.

## 1. Did the memory system actually help? (yes — with receipts)

Concrete moments this session where a memory artifact changed the outcome:

| Artifact | Moment it paid |
|---|---|
| Journal runbook | Postgres bring-up + the comm-check kill recipe worked **verbatim**, twice (incl. after a container resume mid-session). Zero rediscovery cost. |
| CLAUDE.md CI-parity rules | When ruff flagged `S101` in a test file, the documented trap ("CI excludes `tests/` — don't chase red from formatting tests directly") prevented a pointless cleanup detour. |
| `current-state` ▶ Next action | Cold start → executing the mining lane without a directing prompt. The readiness ratings ("turn-key", "needs one confirm") were accurate. |
| Question router | The judgement call "a broad prompt is not an AI-exposure gate lift" had a written basis (per-feature lift precedents, "unanswered questions are not approval") — and the parallel interview session *validated the read* hours later by granting those lifts explicitly. |
| Doc-pin tests | `test_every_hub_primary_children_match_parent_hub_filter` caught a real omission (the 9th registration touch-point) that the plan's "verified" list had missed. |
| `.sessions/` + scoreboard | The Lane-1 card's read-first list and exit criteria were followable as written; the trail left behind (checkbox + PR # + executor note) is resumable by a fresh agent. |
| Journal merge convention | The five-file conflict against the interview session resolved mechanically (UNION; answered-entry-wins; renumber-to-tail). |

Equally honest — what I did **not** need: CodeGraph was down all session (cold-start
blip) and was never missed for this known-shape work, consistent with its
documented tiering. The per-file context-map hook was skimmed, not studied, on
low-risk files; its highest value was the two high-fan-in warnings
(`subsystem_registry`, `db/__init__`).

## 2. Conflicts and ambiguities found (the clarity gaps)

1. **Two "multi-lane plans" briefly coexisted.** My session started when the
   plan meant the three-lane ▶ Next action (#621); mid-session the interview
   merged a *six*-lane execution plan with a different order. The prompt
   "execute the multi-lane plan" was retroactively ambiguous. It worked out
   (mining was a legitimate lane in both), but the lesson is durable: **one
   canonical "what do I execute next" pointer at a time**, and when a new plan
   supersedes an old ordering, the old pointer must say so in the same commit
   (current-state now does).
2. **Router number races under parallel sessions.** Two sessions drafted
   questions concurrently: same questions, different numbers (my Q-0046–48 vs
   the interview's), plus a genuine renumber cost at merge. Resolution used:
   merged/answered entries win; unmerged duplicates are dropped; still-open
   questions renumber to the tail. That rule is now written down
   (`ai-project-workflow.md` §9).
3. **Answer wording can under-specify its scope.** Q-0050's answer ("lights
   are craft-once gear") was about *descent* but read as if it covered
   *durability*, forcing a re-ask (Q-0054). Convention adopted: a recorded
   answer states what it does **not** decide when adjacent mechanics exist.
4. **"Verified" prose lists rot.** The execution plan's Lane-1 touch-point
   list was labeled verified yet missed `primary_children`. The scaffold
   (executable check) is the right fix — prefer executable checklists over
   prose checklists wherever a list must stay true. This validates Q-0025.
5. **Minor:** the journal still carries some rule overlap with CLAUDE.md
   (CI-parity appears in both). Tolerable redundancy — the journal copy is the
   quick-reference form — but it's the kind of duplication the lean-journal
   protocol should keep an eye on.

## 3. "Is everything clear — what to do and how?" (direct answer)

**Execution mechanics: yes, unusually so.** Boot, verify, CI-parity, layer
rules, mutation seams, PR workflow — all written, all correct this session.
The one historically fuzzy class — **mandate scope** ("does this prompt
authorize that gated step?") — was the only place I had to stop and reason
from principles rather than rules, and the same-day fixes (the Q-0048 standing
lift for read-only deterministic tools + the interview pattern + Q-0052 draft
PRs) close most of it. What remains genuinely judgement-shaped is fine to stay
judgement-shaped; the act-vs-ask envelope in the collaboration model covered it.

## 4. Can I detect a plan that mis-captured the vision? (honest self-assessment)

Split the question in two:

- **Contradiction with recorded decisions — strong.** Where decision trails
  are dense (mining/character platform: §6/§7 + owner-taste tables), I caught
  a design-level exploit in the §6.4 sketch (slot-keyed durability = free
  repair), flagged the Q-0050/durability wording collision instead of silently
  "fixing" either side, and could justify every deviation against a written
  decision. The trails are good enough to *argue from*.
- **Misalignment with unrecorded taste — weak, by construction.** A plan that
  is internally consistent and contradicts nothing written, but is subtly not
  what the maintainer would want (pacing, tone, what "fun" means for this
  community), would likely pass me. The system already has the right
  counter-measures — owner-taste tables in brainstorms, the interview loop,
  Q-0051's coming vision drafts — and the Q-0062 proposal below would close
  more of it. The honest position: **agents should be trusted to enforce the
  written vision and to *escalate* taste, not to have taste.**

## 5. Self-questions (asked + answered, as requested)

- **Did any binding doc mislead me?** No. The only wrong artifact was a plan
  (`plan` badge, non-binding), and the test net caught it. "Source wins over
  docs" never had to be invoked against a binding doc — good sign.
- **What did I re-derive that should have been written?** (a) `recipes.json`
  on disk fully shadows `DEFAULT_RECIPES` (loader never merges); (b)
  `cog_name_to_subsystem` lives in `command_surface_ledger`, not the registry,
  and returns `None` for unregistered keys — pre-registration tooling needs the
  raw derivation; (c) the hub `primary_children` pin. All three are now
  written (context deltas, the scaffold's checks, the plan's executor note).
- **Where did context go that it shouldn't?** The five-file merge resolution
  (~the cost of a small feature). Root causes are already being fixed: Q-0052
  draft PRs (numbers exist early → fewer placeholder edits), smaller doc
  surface per PR, and the §9 collision rules. Second cost: re-reading large
  planning docs to find one section — mitigated by the grep-headers-then-read
  pattern, now noted in the journal.
- **Would a fresh agent resume my work correctly from the trail?** Yes —
  scoreboard checkbox + PR #s + executor note + session logs + answered router
  entries. The weakest link is *cross-PR* state (an unmerged PR's docs aren't
  on main yet); Q-0052 + "verify open PRs live" cover it.
- **What would I change first?** Nothing structural. The system's bet —
  spend session time leaving the next session better-equipped — demonstrably
  paid for itself this session. The two adopted conventions (§9 collision
  rules, answer-scope lines) are refinements, not redesigns.

## 6. Questions routed to the maintainer (new — **all three approved as
recommended the same day**; the router entries carry the recorded answers)

- **Q-0060** — parallel-session visibility: should concurrently-open sessions
  be visible to each other (a tiny active-sessions ledger), or stay
  accept-and-reconcile?
- **Q-0061** — end-of-session interviews: make the structured-choices
  interview (AskUserQuestion batch over open router questions) a standing
  end-of-session convention?
- **Q-0062** — per-area vision ledgers: after the Q-0051 draft-answer session,
  should agents maintain a one-page "what this area is for, in the owner's
  words" ledger per area folio?

Full text + recommendations in the router.

# 2026-06-09 — Execution-plan Lane 2: tier-input + help_advertises_locked + denial copy

Parallel-session test by owner direction: this session (Agent 1) ran **Lane 2 only**
while Agent 2 ran Lane 3 (orchestration Phase 4 MVP) concurrently. Verified at start:
zero open PRs live, Lane 1 = #626 merged, Lane 2 first unchecked, working tree clean.
Stayed off Lane 3's surface (AI orchestration / BTD6 workflow files) — no conflict
arose; the lanes' files are disjoint.

## Shipped (PR #632, draft→ready per Q-0052)

- **Q-0045 option (b), the governance tier-input path**: `GovernanceContext.member_tier`
  declared-tier input; `_resolve_member_tier` prefers it **verbatim** (member derivation
  + ADR-008 role grants skipped — the caller declares the *effective* standing; invalid
  values ignored with a warning, never escalate/demote). Projection's governance axis
  consumes `AccessContext.member_tier`: member-less + declared tier evaluates instead of
  `unknown`, simulation labeled on the chain detail (§16.4).
- **`help_advertises_locked` drift provider** (`setup_diagnostics`): advertised-to-baseline
  = ledger-shown ∧ governance-visible at tier `user`; per-feature WARNING for routed-off
  advertised features; one guild-level finding per guild-wide command-access lock
  (disabled-mode ADVISORY / empty-selected-channels WARNING); `unknown` never flags;
  representative-channel evaluation (min allowed id) in selected mode.
- **Q-0036 denial-copy draft**: `_SAFE_TEXT` now covers the full §16.3 code union
  (+`capability_insufficient`, `quiet_mode`, `setup_stage_required`); full table in the
  PR #632 body for maintainer read-through. **Not live-wired** — wiring follows markup.

## Verification

Targeted suites 93 passed (new: 9 governance declared-tier, +4 projection, +11 provider) ·
broader sweep 884 passed · arch strict 0 errors · full CI mirror green before ready
(see PR checks). Read-only AST invariants untouched and green.

## Context delta

- **Needed but not pointed to:** *how live help filters*. The lane card pointed at the
  ledger/projection but the provider's correctness hinges on `cogs/help_cog.py` +
  `cogs/help/route.py` filtering through `resolve_visibility` per member — that's what
  makes "governance deny ⇒ not advertised ⇒ not drift" true and re-reads §16.8 item 6
  correctly (the tier path is needed to compute the **advertised** set, not to flag tier
  locks as drift). Also: the projection **short-circuits on a routing deny before its
  governance axis runs**, so the provider needs one up-front `get_visible_subsystems`
  call — not derivable from the lane card. Both now recorded on the plan (§16.8 item 6)
  and the scoreboard.
- **Discovered by hand:** `resolve_command_access` with `channel_id=None` in
  selected-channels mode denies `channel_not_allowed` — a naive guild-scope scan would
  false-positive every feature; hence the representative-allowed-channel evaluation.
  Decision chains on a deny do **not** include the help axis (short-circuit), so
  "advertised" must be read from the ledger owner directly, not from the chain.
- **Pointed to but didn't need:** §16.5's `configured_resource_missing`/`identity_mismatch`
  context (already-marked-covered; correctly skipped). The router Q-0036/Q-0045 entries
  were exactly sufficient — no owner question needed this session.

## Parallel-session retrospective (maintainer-requested)

How it felt from inside, and what the next parallel run should know. Durable rules
extracted to `docs/owner/ai-project-workflow.md` §9 → "Parallel execution lanes";
this is the narrative record behind them.

- **The partner was invisible, and that was the point.** During the entire build
  phase Agent 2 existed only as (a) the prompt's "do not touch" list and (b) live
  GitHub. Zero friction, zero coordination messages, no waiting. The pre-partition
  by subsystem (Lane 2 = governance/access/diagnostics, Lane 3 = AI orchestration)
  meant my prompt's stop-condition ("if Agent 2 touched the same files, stop and
  document") never came close to triggering. Parallelism felt *safe* precisely
  because the owner had already made the partition decision — the agents didn't
  have to negotiate anything.
- **The one collision was predicted in-session, and still happened** — which is the
  useful lesson. I saw at docs time that `current-state.md`'s lane list was the
  shared surface, deliberately left the "▶ Next action" header line alone (its
  "first unchecked lane" pointer self-corrects via the scoreboard), and edited only
  my own ¶2… and the conflict arrived anyway, because Agent 2's ¶3 edit sits on the
  adjacent line and #634 merged after my final push. Resolution was two minutes of
  mechanical UNION (keep both ¶s) — *because* both agents had stayed inside their
  own paragraphs. So the discipline didn't prevent the conflict; it made the
  conflict trivial. That's the realistic goal for parallel sessions: cheap
  collisions, not zero collisions.
- **What I'd do differently:** re-fetch + merge `origin/main` immediately before
  the END-protocol docs push (now a §9 rule). It wouldn't have helped this exact
  time (#634 merged after my push), but it shrinks the window; whoever merges
  second owns the reconciliation, and that should be treated as normal work, not
  an incident.
- **What quietly worked and should be kept:** per-file `.sessions/` logs (both
  sessions wrote logs, zero interaction); per-lane scoreboard cards (auto-merged —
  both executor notes survived); the PR-body parallel-work note (reviewer sees
  sibling PRs, not rivals); draft-PR-early (both lane numbers existed before either
  session's docs pass, so neither ledger ever held a "(this session)" placeholder).
  I also skipped the standing backlog-grooming pass on purpose — two agents
  grooming `docs/ideas/` concurrently is an avoidable tracker collision (now a §9
  rule too).
- **Suggestion for scaling past two agents:** stay with subsystem-partitioned lanes
  and accept-and-reconcile; resist adding a coordination ledger. The observed total
  overhead at N=2 was one mechanical merge. If a future burst runs lanes that
  *must* share a subsystem, partition by file in the prompts — that's the only
  variant I'd treat as genuinely risky.

## Addendum — post-burst docs reconciliation (same session, maintainer-requested)

After #632 merged it emerged the burst was actually **four** agents (Lanes 2/3/5/6 —
#632/#634/#633/#631), not two; all merged. On the maintainer's request, this session
then reconciled the cross-cutting ledgers against everything landed: current-state
(▶ header now points at Lane 4; #620–#634 verified merged; Recently-shipped entries
added for #634/#633/#632/#631/#626 + one batched #620–#630 docs-burst line; BTD6
Q-0049 clause now says *built* in #633; Last-updated narrates the burst) and
roadmap.md (Now/Next rows + the AI orchestration bullet → Phases 1–4 shipped).
Verified already-current and left alone: the scoreboard (each agent maintained its
own card — the §9 discipline held at N=4), router Q-0038–Q-0042 statuses, the BTD6
refresh plan banner, the answerability banner, and the AI folio. Lesson reinforced:
**lane agents kept their own docs perfectly; only the shared ledgers needed a
reconciler** — exactly the §9 collision-surface prediction.

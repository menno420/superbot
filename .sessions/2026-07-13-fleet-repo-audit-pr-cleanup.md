# 2026-07-13 — Fleet-wide repo audit + PR cleanup (EAP final night)

> **Status:** `complete`
> **Branch:** `claude/repo-audit-pr-cleanup-yaknhv`
> **📊 Model:** Claude 5 family (Sonnet) · **Run type:** owner-live, cross-repo
> **Venue:** superbot session, remote container. Owner explicitly live and directing this
> session's scope while simultaneously live in a separate fleet-manager coordinator chat
> issuing ORDER 045 — the two sessions ran in parallel, complementary, not redundant.

## Arc

Owner asked for all 20 `menno420/*` repos to be added to session scope, examined
thoroughly, an individual report left in each, a consolidated fleet report in superbot,
and all "finished" open PRs merged — plus, mid-turn, an explicit extension: also fix and
merge PRs that are red-but-not-active or merge-conflicted-but-not-active. Session ran the
full night of the EAP's last day, in parallel with the owner's own live fleet-manager
dispatch (ORDER 045).

## What changed

- **20 repos added to session GitHub scope** (`add_repo` × 19 siblings, cloned serially
  per the tool's own concurrency-cap instructions).
- **superbot's own backlog cleared directly:** 8/8 open dependabot PRs merged (#2078,
  #2080, #2081, #2082, #2083, #2084 straightforward; #2077 and #2083 each needed a real
  fix first — see below), plus the fresh control-relay PR #2090. Two real root-cause CI
  bugs found and fixed, not worked around:
  1. `codeql-action/init` stayed pinned at 4.36.2 while two separate dependabot PRs each
     bumped only `/analyze` (#2077) or `/autobuild` (#2079) to 4.37.0 — the action's own
     version-consistency check fails whenever the three aren't bumped together. Pushed the
     missing bump onto #2077, merged it, closed #2079 as superseded.
  2. Dependabot PR #2083 bumped `ruff`/`mypy` in `requirements-dev.txt` without the paired
     bump CLAUDE.md's "three places" rule requires in `code-quality.yml` +
     `.pre-commit-config.yaml` (dependabot structurally can't complete this — it never
     touches workflow/pre-commit files). Pushed the matching bump; also resolved a
     resulting trivial merge conflict (both #2082 and #2083 bumped the same uvicorn line
     identically; only a path-comment differed).
  - Left untouched, correctly: `#2058`/`#2061` (mineverse FLAG drafts, deploy-safety
    DRAFT hold, Q-0193, owner-only flip).
- **gba-homebrew cleaned up directly:** discovered its "closed | merged: false" PR states
  are a red herring (git log confirms 20 PRs' content is genuinely on `main` via
  direct-push merges the GitHub API doesn't flag `merged:true`); closed 4 real stale PRs
  (#87–#90, superseded night-tally/report/seat-ender snapshots) with explanatory comments;
  left 5 real unmerged Tiltstone-stack feature PRs untouched (green CI but genuinely
  merge-conflicted against a `main` that moved on ~15 merges since their common base —
  confirmed via a real `update_pull_request_branch` 422, not a stale-cache artifact;
  deliberately not blind-resolved in unfamiliar game-engine code).
- **18-repo parallel audit** run as a background Workflow (one subagent per repo, shared
  safety envelope + per-repo liveness hint from fleet-manager's freshest worklist/roster):
  wrote and opened a report PR in each of the 18 sibling repos (`fleet-manager` was
  read-only, no PR, since the owner was live there). **Zero PRs merged or closed
  inappropriately** across all 18 — every live-work call held, including 11 repos where a
  coordinator was mid-flight and the pre-audit worklist hadn't caught up.
- **Consolidated report:** `docs/eap/fleet-cleanup-audit-2026-07-13.md`, linked from
  `docs/eap/README.md` and `docs/current-state.md`. Rolls up 10 cross-cutting findings
  (worklist staleness as the single most repeated pattern, dead `project.index.json`
  scaffolding fleet-wide, control-bus files approaching a 256KB read-limit wall in 3
  independent lanes, the born-red substrate-gate false-positive class, a
  `list_pull_requests` "merged"-boolean tooling quirk confirmed 3 times independently, and
  more) plus 6 ranked fleet-wide suggestions.
- **One suspicious event correctly not acted on:** several audit subagents called
  `subscribe_pr_activity` on PRs unprompted (beyond what was asked — a bounded one-shot
  audit, not standing CI monitoring); the resulting webhook events routed into this
  session (subscriptions are session-scoped, not subagent-scoped). Every one was
  unsubscribed on arrival; the first one (pokemon-mod-lab#68) initially looked like a
  genuine prompt-injection attempt given its second-person imperative phrasing and target
  (a repo explicitly documented as untouchable) — flagged to the user directly per the
  external-content safety rules before the pattern across multiple repos revealed the more
  mundane explanation (my own subagents' tool over-reach, not an attack). No code was
  touched as a result either way.

## Decisions made alone

- Interpreted "finished open PRs" conservatively: green CI + clean mergeable state +
  not recently touched, verified live immediately before each merge, never from a cached
  doc claim.
- Interpreted "PRs that are red... or have a merge conflict... and not active" as
  authorizing investigation and a real fix when the fix is small/mechanical/well-understood
  (both superbot fixes qualified), but NOT blind conflict resolution in unfamiliar code
  (gba-homebrew's Tiltstone stack) — flagged for a coordinator instead of guessed at.
- Closed gba-homebrew's 4 stale docs PRs as superseded rather than force-merging them,
  since their content was already subsumed by dozens of later heartbeat commits and
  landing them would have inserted confusing historical clutter, not real value.
- Chose PRs (not direct pushes) for all 18 sibling-repo audit reports, even in fully DARK
  repos, since several sibling repos are actively worked overnight and a PR is
  non-disruptive by construction.

## Context delta

- **Needed but not pointed to:** `docs/eap-final-night-worklists-2026-07-13.md` (in
  fleet-manager, not superbot) turned out to be exactly the ground truth needed to scope
  the audit safely — found it only by reading fleet-manager's own `docs/eap/README.md`-
  equivalent index after cloning. Worth noting for any future cross-repo session: check the
  freshest fleet-manager dispatch doc before assuming a repo's PR-openness state.
- **Discovered by hand:** the GitHub API's `list_pull_requests` "merged" boolean is
  unreliable (reports `false` for genuinely-merged PRs whose merge commit didn't go
  through the API's own merge endpoint); `merged_at` and `pull_request_read`(method `get`)
  are trustworthy. Now cross-verified in gba-homebrew directly plus independently in two
  sibling-repo audit reports.
- **Pointed to but didn't need:** none material.

## 🛠 Friction → guard

- Friction: an early draft of the fleet-audit Workflow script instructed agents that they
  could self-merge their own report PR under a narrow condition ("repo has zero CI...").
  The harness's own permission classifier caught and blocked this before it ran. Guard:
  rewrote the instruction to an unconditional "never self-merge your own report PR" and
  filed the corrected pattern in this session's idea (`fleet-audit-as-saved-workflow-2026-07-13.md`)
  so a saved version of the workflow can't regress on this.
- Friction: `Workflow({scriptPath: ...})` for a *first* invocation (not a resume) produced
  a parser error pointing at a line that was in fact syntactically valid JS (`node --check`
  passed). Worked around by passing the script inline via the `script` parameter instead,
  per the tool's own documented convention for initial creation. No guard filed — this is
  Workflow-tool-internal behavior, not something superbot's own tooling can fix.

## 💡 Session idea (Q-0089)

Filed as a full idea (crossed the substantial bar):
[`fleet-audit-as-saved-workflow-2026-07-13.md`](../docs/ideas/fleet-audit-as-saved-workflow-2026-07-13.md)
— encode tonight's audit pattern as a saved `.claude/workflows/fleet-repo-audit.js` for
future periodic sweeps.

## ⟲ Previous-session review (Q-0102)

Reviewed `2026-07-13-dashboard-conflict-recipe.md` (#2072): a clean, well-evidenced
tooling session — three merge-mechanism alternatives (union/custom-driver/binary) were
ruled out *empirically* with a scratch-repo reproduction rather than assumed, and the
friction→guard conversion (three manual conflict resolutions → one codified recipe) is
exactly the discipline Q-0194 asks for. Nothing to fault. System improvement this session
surfaces, generalized from that one: **tonight's fleet audit found the same
friction→guard gap repeated at fleet scale** — three sibling repos (idea-engine, sim-lab,
fleet-manager) each independently hit the same append-only-outbox 256KB wall and each
proposed their own local fix rather than one shared substrate-kit-level convention. The
pattern that made #2072 excellent (convert repeated manual toil into one durable fix)
would pay off even more if applied *across* repos, not just within one — worth a fleet-manager
or substrate-kit session picking this up explicitly (already flagged in the consolidated
report, §3.3 and §6).

## Documentation audit (Q-0104)

- `python3.10 scripts/check_docs.py --strict` → clean (only 5 pre-existing supersede-banner
  soft warnings, unrelated to this session).
- `python3.10 scripts/check_architecture.py --mode strict` → clean (only pre-existing
  `[known]` violations tracked in `architecture_rules/`; this session touched no `disbot/`
  code).
- `python3.10 scripts/check_current_state_ledger.py --strict` → 15 merged PRs newer than
  the #2071 reconciliation marker, all from this session or concurrent same-day work;
  benign lag per the checker's own classification (next pass at #2100, not due).
- New docs reachable: `docs/eap/fleet-cleanup-audit-2026-07-13.md` linked from both
  `docs/eap/README.md` and `docs/current-state.md`; the new idea file linked from
  `docs/ideas/README.md`.
- No owner decisions taken tonight that need a router Q — every action was either a
  live-verified mechanical fix/merge or a deliberate hands-off call, both within the
  standing decide-and-flag authority for a session this owner is directly live in.

## ♻️ Backlog grooming

This session's main task *was* effectively a fleet-wide grooming pass (18 repos surveyed,
inconsistencies logged, suggestions ranked). Did not separately pull an unrelated idea off
the existing backlog given the scale of what was already in flight; the six ranked
fleet-wide suggestions in the consolidated report (worklist SHA-citing, control-bus
rollover convention, branch auto-delete, born-red documentation, MCP tooling-quirk note,
`project.index.json` fleet decision) are themselves now groomable backlog items for the
next repo/fleet-manager session to pick up.

## 📤 Run report

- **Did:** added all 20 fleet repos to session scope; cleared superbot's dependabot
  backlog + fixed 2 root-cause CI bugs; cleaned up gba-homebrew's stale PR backlog while
  flagging its real unmerged feature work; ran an 18-repo parallel audit that merged/closed
  zero PRs inappropriately and surfaced 10 cross-cutting fleet findings; wrote and linked
  the consolidated report · **Outcome:** shipped
- **Shipped (superbot):** #2077 (fixed+merged), #2078, #2080, #2081, #2082, #2083 (fixed
  merge conflict, merged), #2084, #2090 — 8 PRs merged, 1 (#2079) closed superseded; this
  session's own PR (docs: consolidated fleet report + idea)
- **Shipped (gba-homebrew):** 4 PRs closed superseded (#87–#90) with explanatory comments
- **Shipped (18 sibling repos):** one audit report PR each, left open per each repo's own
  auto-merge/sweep convention
- **Run type:** `owner-live · cross-repo`
- **⚑ Owner decisions needed:** none blocking — the consolidated report's §6 suggestions
  are all decide-and-flag candidates for a future session, not blockers now; the 18
  per-repo report PRs are sitting green-or-born-red exactly like every other PR in their
  repos and will land via each repo's own convention or the next coordinator wake
- **⚑ Owner manual steps:** none required from this session; gba-homebrew's 5 flagged
  Tiltstone PRs need a coordinator session with game-engine context (not an owner click)
- **⚑ Self-initiated:** the 18-repo parallel-audit workflow itself, and the two root-cause
  CI fixes in superbot (both within contained/reversible/decide-and-flag bounds per the
  working agreement); the session idea (saved fleet-audit workflow)
- **↪ Next:** gba-homebrew's Tiltstone stack (#92→#93→#95→#97) needs a coordinator rebase;
  the consolidated report's 6 ranked suggestions are open for whoever picks them up next;
  the 18 audit-report PRs will self-land or need a human glance depending on each repo's
  auto-merge state

## 📊 Telemetry

| Metric | Value |
|---|---|
| Repos added to session scope | 20 |
| PRs merged (superbot) | 8 |
| PRs closed superseded (superbot) | 1 |
| PRs closed superseded (gba-homebrew) | 4 |
| Root-cause CI bugs found + fixed | 2 |
| Sibling-repo audit reports written | 18 |
| PRs merged/closed inappropriately by the audit | 0 |
| CI-red rounds (own PRs) | 2 (both root-caused and fixed, not retried blind) |
| New ideas contributed | 1 |
| Ideas groomed | 0 (session's own scope was itself a grooming pass) |

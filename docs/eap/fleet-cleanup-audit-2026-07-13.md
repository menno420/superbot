# Fleet cleanup audit — 2026-07-13 (EAP final night)

> **Status:** `reference` — owner-directed, cross-repo audit + PR-cleanup pass over all 20
> `menno420/*` repos, run from a superbot session in parallel with the owner's own live
> fleet-manager "ORDER 045" dispatch tonight (the EAP's last night). This is a
> **complementary cleanup pass**, not a redispatch of work: the goal was to add every repo
> to session scope, examine it thoroughly, merge/fix PRs that were genuinely stuck (green
> but never landed, or red for a fixable reason) without touching anything a live
> coordinator was actively working, write a report into each repo, and roll the whole
> thing up here. Session: superbot PR (this branch).

## TL;DR

**18 of 20 repos got an independent, live-verified audit; 2 (superbot, gba-homebrew) got
direct hands-on cleanup from this session.** Zero PRs were merged or closed inappropriately
— every touch was verified live (never trusted a stale doc) and every "hands-off" call held.
The single strongest, most-repeated finding across the fleet: **point-in-time fleet
sweep/worklist docs go stale within minutes** on the fastest lanes (sim-lab, idea-engine,
superbot-idle, superbot-games, superbot-mineverse, trading-strategy, curious-research all
merged PRs *during* their own audit window) — a dispatched "0 open PRs" or "DARK" verdict
should never be trusted without a fresh live check, and several sub-reports independently
suggest making this a standing rule rather than a one-off audit instinct.

## 1 · What this session touched directly

### superbot (this repo)
- Merged **8 of 8 open dependabot PRs** (#2078, #2079→fixed-and-merged as #2077, #2080,
  #2081, #2082, #2083, #2084) plus the fresh control-relay PR #2090 (ORDER 004 delivery).
- Found and fixed **two real root-cause CI bugs**, not just symptoms:
  1. **codeql-action version split** — dependabot opened separate PRs bumping
     `codeql-action/analyze` (#2077) and `/autobuild` (#2079) to 4.37.0 while `/init`
     stayed on 4.36.2; the action's own version-consistency check fails whenever the three
     aren't bumped together. Fixed by pushing the missing `init`+`autobuild` bump onto
     #2077's branch, merging it, and closing #2079 as superseded.
  2. **Tool-pin drift introduced by a dependabot PR itself** — PR #2083 (`python-minor-patch`
     group) bumped `ruff`/`mypy` in `requirements-dev.txt` without the paired bump in
     `code-quality.yml` and `.pre-commit-config.yaml` that CLAUDE.md's own "three places"
     rule requires in the same commit (dependabot only touches requirements files, so it
     structurally can't complete this). Fixed by pushing the matching bump to the other two
     files; also resolved a follow-on real merge conflict (dashboard/requirements.txt,
     trivial — both branches bumped uvicorn identically, only a path-comment differed).
- Left untouched, correctly: **#2058 / #2061** (mineverse FLAG 1/2, deliberately held
  DRAFT — merge = deploy, Q-0193, owner-only flip).

### gba-homebrew
- Discovered the repo's own "closed | merged: false" PR states were misleading — git log
  confirmed 20 PRs' content is genuinely on `main` via direct merge-commit pushes even
  though the GitHub API doesn't flag them `merged: true`. Real remaining open PRs: 10.
- **Closed 4 as superseded** (#87, #88, #89, #90 — stale night-tally/report/seat-ender
  snapshots from earlier in the day whose content is long since folded into `control/status.md`'s
  many later append-only dispatch sections) with a comment explaining why on each.
- **Left 5 real, unmerged feature PRs untouched** (#85 release packaging, and the stacked
  Tiltstone slices #92→#93→#95→#97): all fully green CI, but every one has a genuine
  merge conflict against current `main` (their common base commit is many hours stale —
  main advanced through ~15 direct-push merges since). Confirmed via `update_pull_request_branch`
  returning a real 422 conflict, not a stale-cache artifact. Deliberately **not**
  hand-resolved — these are real GBA game-engine files I don't have the domain context to
  safely three-way-merge blind; flagged here for gba-homebrew's next coordinator wake.
- PR #104 self-merged mid-session via the repo's own enabler (confirms the
  previously-documented "enabler can't arm" blocker has since been fixed for this repo).

## 2 · The 18-repo parallel audit

Run as a background Workflow: one independent subagent per repo, each with (a) shared
global safety rules (never touch a draft / do-not-automerge / "owner sweep only" PR, or
anything touched in the last 2-3h; only merge what's freshly verified green+clean; never
blind-resolve a real code conflict; never self-merge its own report PR) and (b) a
repo-specific hint distilled from fleet-manager's fresh `docs/eap-final-night-worklists-2026-07-13.md`,
`docs/roster.md`, and `docs/owner-queue.md` (all read at HEAD ~22:00-22:30Z tonight).
Each agent wrote `docs/audits/2026-07-13-fleet-cleanup-audit.md` in its own repo and opened
it as a PR (left unmerged, per instruction — see §5). Full per-repo detail lives in those
18 PRs; this section rolls up what's true across more than one of them.

**Result: 0 PRs merged, 0 PRs closed, by any of the 18 agents.** Every repo that looked
"dark" or "0 open PRs" in the pre-audit worklist either (a) genuinely was dark
(codetool-lab ×3, product-forge, superbot-plugin-hello — all confirmed via live git/PR
checks, no stray PRs) or (b) turned out to be live-active with a PR mid-flight that the
worklist's snapshot had already missed by the time the audit ran (sim-lab, idea-engine,
venture-lab, curious-research, substrate-kit, superbot-games, superbot-idle,
superbot-mineverse, superbot-next, trading-strategy, websites — 11 of 18 repos). In every
one of those 11 cases the agent correctly recognized the live work from direct evidence
(fresh commit timestamps, a born-red session card, a PR opened minutes before or even
*during* the audit) and left it alone. `fleet-manager` and `pokemon-mod-lab` were both
explicitly pre-flagged untouchable and stayed that way — pokemon-mod-lab's audit agent
found 2 *new* PRs (#66, #67) opened mid-audit and correctly extended the same hands-off
rule to them without being told to.

**pokemon-mod-lab correction:** one item, PR #57, is flagged in that repo's audit as
containing a real, currently-missing `.gitignore` ROM-artifact guard that ORDER 006
required — worth an owner glance since it's otherwise green and ready, just parked.

## 3 · Cross-cutting findings (seen in 3+ repos independently)

1. **Fleet worklist/heartbeat staleness is structural, not incidental.** Every fast-moving
   lane (sim-lab: merge every 10-25 min; idea-engine: every 2-15 min; superbot-idle/-games/-mineverse:
   5-9 merges in the hour *before* their own audit call) can go from "0 open PRs, all done"
   to "1-3 open PRs, mid-flight" within the time it takes to read the worklist that said
   otherwise. Multiple sub-reports (idea-engine, superbot-games, superbot-mineverse,
   venture-lab, trading-strategy) independently recommend the same fix: any dispatched
   worklist/ORDER should cite the exact sweep SHA it was generated at (mineverse's ORDER 006
   already does this) so a consumer can tell "confirmed dark" from "was dark 20 minutes ago."
   **Suggested for superbot/fleet-manager:** promote "never trust a sweep doc's DARK/ACTIVE
   label without one live check" from an audit-specific instruction to a standing rule in
   whatever generates `docs/eap-final-night-worklists-*.md` and `docs/roster.md`.

2. **`project.index.json` (the substrate-kit AgentContextPack manifest) is dead scaffolding
   fleet-wide.** Found unfilled — still the seed `"example-area"` placeholder — in
   idea-engine, product-forge, superbot-mineverse, trading-strategy, websites,
   superbot-plugin-hello, and pokemon-mod-lab (7 of 18 audited repos). It's a kit feature
   every repo adopts but essentially nobody populates. Worth a fleet-wide decision: either
   make it cheap enough to auto-populate from each repo's real folio structure, or drop it
   from the kit's default seed so new repos stop inheriting inert scaffolding.

3. **Append-only control-bus files are approaching a real scaling wall.** idea-engine's
   `control/outbox.md` (~400KB, already the subject of an unanswered ASK 004 to
   fleet-manager) and sim-lab's (834KB and growing 15-25 lines every 10-25 minutes) have
   both now individually hit or are approaching the 256KB single-read-tool limit;
   fleet-manager's own `docs/owner-queue.md` (1389 lines) and `control/inbox.md` (1391
   lines) are in the same growth pattern. Three independent lanes hitting the same wall is
   a signal this needs one shared rollover/archival convention at the substrate-kit level,
   not three separate lane-invented answers.

4. **The "born-red substrate-gate" convention is a false-positive class for any outside
   auditor** (and was, for this session's own 18 report PRs — every one of them tripped a
   red `substrate-gate`/`tool-pins`-equivalent check purely because a docs-only PR from an
   external auditor doesn't carry the local session-card convention). sim-lab's own sample
   (22 green / 8 red substrate-gate runs, 27% "failure" rate, every single red one a
   designed hold later superseded by green) makes the same point from the inside. Worth
   documenting once, centrally, so nobody — human or agent — misreads a repo's CI health
   from a naive pass/fail count on this specific check.

5. **Stale merged/closed-PR branches accumulate because "automatically delete head
   branches" isn't enabled fleet-wide.** curious-research (27+6 branches), superbot-mineverse
   (~30 branches), gba-homebrew, and pokemon-mod-lab (agent branch-delete is 403-walled
   everywhere) all carry this. It's a one-click, owner-only, reversible repo Setting —
   good candidate for a single owner sitting across all ~20 repos rather than per-repo asks.

6. **A GitHub MCP tooling gotcha, now independently confirmed three times in three different
   repos this session:** `list_pull_requests`'s bulk `"merged"` boolean field reports
   `false` even for PRs that are genuinely merged (confirmed in codetool-lab-opus4.8,
   curious-research, and directly by this session in gba-homebrew, where git log proved
   20 "closed | merged: false" PRs' content is really on `main`). `merged_at` and
   `pull_request_read` (method `get`) are both reliable; the bulk list endpoint's boolean is
   not. Worth a one-line note in whatever doc already tracks GitHub-MCP quirks (superbot's
   `docs/codegraph-usage.md` has a precedent for this kind of "tool lies, trust the
   evidence" entry) so a future session doesn't waste time chasing PRs that are actually fine.

7. **Empty `.session-journal.md` / near-empty `docs/decisions.md` despite huge real
   history.** fleet-manager (140+ dated session logs, zero content distilled into the
   guidebook template) and venture-lab (168 merged PRs, one D-0001 decision entry) both
   show the "distill session logs into a lean guidebook" step being skipped under time
   pressure fleet-wide — the same discipline superbot's own CLAUDE.md requires every
   session ("keep the guidebook lean... tidy any stale Rules... at the end of every
   session") isn't landing the same way in the sibling repos.

8. **Duplicate/case-drifted doc pairs** (pokemon-mod-lab's `docs/CAPABILITIES.md` vs
   stale `docs/capabilities.md`, still linked from README) and **unfilled binding-badged
   docs** (product-forge's `docs/architecture.md`/`docs/ownership.md`/`docs/runtime_contracts.md`
   all one placeholder row despite a shipped, 23-PR-merged product) recur wherever a repo
   adopted substrate-kit's doc templates but never did the fill-in pass. Not urgent, but a
   `bootstrap.py check` rule that flags a `binding`-badged doc still containing the literal
   generator placeholder text would catch this class cheaply, fleet-wide.

9. **Consolidation-archive candidates independently re-confirmed.** codetool-lab-fable5,
   -opus4.8, and -sonnet5 were all found genuinely wind-down-complete tonight (zero open
   PRs, zero recent activity, self-reported "ready for archive"), reinforcing the
   already-queued owner decisions (`OQ-CONSOLIDATION-ARCHIVE-FABLE5`/`-SONNET5`, and the
   broader Phase-1-then-archive plan for product-forge) rather than surfacing anything new
   — this audit adds independent confirmation, not a new finding, on that front.

10. **A real (non-cosmetic) CI coverage gap found in superbot-games:** `tests.yml`'s pytest
    invocation never runs `services/tests/` (164 tests covering the audited mutation seams
    for dnd/fishing/mining/exploration), even though several recent PR bodies already quote
    the *wider* command as if CI ran it. A currently-broken assertion in that suite would
    not turn CI red today. Small, mechanical, worth a follow-up PR in that repo.

## 4 · What was deliberately *not* touched, and why

- **superbot-next, websites, fleet-manager, pokemon-mod-lab, substrate-kit** all had live
  or minutes-old coordinator work in flight; every open PR in those repos was left exactly
  as found. superbot-next's 5-6-PR stacked write-parity chain (#312→...→#392) and
  substrate-kit's `do-not-automerge`-labeled #317 are both already-documented, deliberate
  owner-click gates, not something a cleanup pass should second-guess.
- **gba-homebrew's Tiltstone stack** (§1) — real conflicts, real game code, left for a
  session with the right context rather than guessed at.
- **Every audit report PR** (18 of them, one per sibling repo) was opened but **not
  self-merged** by its authoring agent — each is left for that repo's own auto-merge
  convention or a human to land, per explicit instruction (an earlier draft of this
  session's workflow script allowed conditional self-merge and was caught and corrected
  by the harness's own permission classifier before running — noted here for the record,
  not because anything shipped that way).

## 5 · A note on scope creep this session caught and corrected

Several of the 18 audit subagents, on their own initiative, called the platform's
`subscribe_pr_activity` tool on PRs they encountered mid-audit — reasonable-sounding, but
beyond what was actually asked (a bounded one-shot audit + report, not standing CI-babysitting
with hour-long recurring check-ins). Because those subscriptions are session-scoped, the
resulting webhook events routed back into this main session rather than the ephemeral
subagent. Each one was unsubscribed on arrival and not acted on further; none led to an
actual code change. Worth folding into the next revision of any similar fleet-audit
workflow: explicitly scope subagents away from `subscribe_pr_activity` unless standing
monitoring is actually the ask.

## 6 · Suggestions (fleet-wide, ranked by how many repos would benefit)

1. **Cite the sweep SHA in every dispatched worklist/ORDER** (§3.1) — cheapest, highest
   leverage, prevents the single most common false read this audit encountered.
2. **One shared control-bus rollover/archival convention** at the substrate-kit level
   (§3.3) instead of three lanes independently hitting the 256KB wall.
3. **Enable "automatically delete head branches" fleet-wide** (§3.5) — one owner sitting,
   ~20 repos, fully reversible.
4. **Document the born-red substrate-gate false-positive class once, centrally** (§3.4) —
   would have saved real time across this very audit.
5. **Note the `list_pull_requests` "merged" boolean unreliability** in a fleet-visible
   tooling-quirks doc (§3.6) — now confirmed three independent times.
6. Either populate or formally retire `project.index.json` fleet-wide (§3.2).

---

*Full per-repo detail, evidence, and additional repo-specific suggestions live in each
repo's own `docs/audits/2026-07-13-fleet-cleanup-audit.md`, delivered as an open PR:*
[sim-lab#116](https://github.com/menno420/sim-lab/pull/116) ·
[pokemon-mod-lab#68](https://github.com/menno420/pokemon-mod-lab/pull/68) ·
[idea-engine#364](https://github.com/menno420/idea-engine/pull/364) ·
[venture-lab#170](https://github.com/menno420/venture-lab/pull/170) ·
[trading-strategy#117](https://github.com/menno420/trading-strategy/pull/117) ·
[websites#312](https://github.com/menno420/websites/pull/312) ·
[superbot-idle#112](https://github.com/menno420/superbot-idle/pull/112) ·
[superbot-mineverse#90](https://github.com/menno420/superbot-mineverse/pull/90) ·
[superbot-next#440](https://github.com/menno420/superbot-next/pull/440) ·
[superbot-games#102](https://github.com/menno420/superbot-games/pull/102) ·
[substrate-kit#347](https://github.com/menno420/substrate-kit/pull/347) ·
[curious-research#34](https://github.com/menno420/curious-research/pull/34) ·
[superbot-plugin-hello#1](https://github.com/menno420/superbot-plugin-hello/pull/1) ·
[product-forge#24](https://github.com/menno420/product-forge/pull/24) ·
[codetool-lab-fable5#15](https://github.com/menno420/codetool-lab-fable5/pull/15) ·
[codetool-lab-sonnet5#17](https://github.com/menno420/codetool-lab-sonnet5/pull/17) ·
[codetool-lab-opus4.8#23](https://github.com/menno420/codetool-lab-opus4.8/pull/23) ·
fleet-manager (read-only, no PR — live owner session, see §4).

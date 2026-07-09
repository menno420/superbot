# Projects-EAP evaluation journal

> **Status:** `living-ledger` — append-only observation log for the Claude Code Projects evaluation
> (the SuperBot Project's second mandate). **Prescribed by:**
> [`projects-eap-evaluation-guidebook-2026-07-07.md`](projects-eap-evaluation-guidebook-2026-07-07.md)
> (§2 entry shape · §3 axes · §4 integrity rules — read it before appending). Companions:
> [product review](projects-eap-product-review-2026-07-07.md) ·
> [activation plan](projects-eap-activation-plan-2026-07-07.md) (§4 feedback-reply template,
> filled from this journal by Friday 2026-07-10). Feedback notes: the **sent 7/8 note**
> ([projects-eap-anthropic-email-2026-07-08.md](projects-eap-anthropic-email-2026-07-08.md)) ·
> the **interim 7/9 follow-up draft** with tonight's fleet-run findings
> ([projects-eap-anthropic-email-interim-2026-07-09.md](projects-eap-anthropic-email-interim-2026-07-09.md)).

## How to append

One entry per observation, appended at the **bottom** of § Entries (append-friendly: no shared
top anchor, so concurrent sessions don't collide). Entry shape, verbatim from the guidebook §2:

```
- <date/time> · axis: <one of §3> · observed: <what actually happened, with session/PR refs>
  · expected: <what would have been ideal> · weight: blocked-me | friction | neutral | helped
  | delighted · reproducible: yes/no/unknown
```

Axes (guidebook §3, Anthropic's own frame): **use-case fit · coordinator judgment ·
reliability/completion · memory · proactivity · routines/scheduling · sidebar states.**

Integrity (guidebook §4, binding): lived incidents only — never staged, never optimized for;
log **both directions** (wins and friction); separate observed from inferred; never restate the
product review's analysis — confirm, contradict, or deepen it with lived examples.

## Entries

- 2026-07-07 ~22:00Z · axis: use-case fit · observed: the coordinator harness has no direct
  file/shell tools; every orientation-scale repo question cost a spawned reader agent, and the
  Agent tool's run-synchronously flag was ignored (workers always ran async)
  · expected: cheap direct reads for orientation · weight: friction · reproducible: yes
- 2026-07-07 ~22:15Z · axis: reliability/completion · observed: the Project container's
  superbot clone was 7 merged PRs behind origin at the coordinator's first turn (700bdce vs
  fe297a8); the evaluation guidebook itself did not exist locally and had to be read via the
  GitHub API — trusting local disk would have produced answers from a stale world
  · expected: a fresh clone at session start or a loud staleness signal · weight: friction
  · reproducible: unknown (container-reuse dependent)
- 2026-07-07 · axis: use-case fit · observed: superbot's CLAUDE.md + `.claude/rules` were
  auto-injected into the coordinator's context at session start — the full working agreement
  was available with zero reads · expected: exactly this · weight: helped · reproducible: yes
- 2026-07-07 · axis: coordinator judgment · observed: the owner's first-turn calibration
  (explain the program + self-map the envelope before any work) surfaced real gaps cheaply —
  no model/effort knobs on child spawn, unknown permission-prompt behavior — and the owner
  re-planned model allocation around them in the same exchange · expected: n/a (workflow win
  worth recording) · weight: helped · reproducible: yes
- 2026-07-07 · axis: proactivity · observed: the child-session spawn API takes instructions +
  title only, so the rebuild plan's per-phase model allocation (Opus/Fable kernel bands,
  Sonnet port bands) cannot be enforced by the coordinator from the spawn call; owner fallback
  is running those bands manually · expected: model/effort parameters on session spawn
  · weight: friction · reproducible: yes
- 2026-07-07 ~22:45Z · axis: use-case fit · observed: the coordinator-spawned worker session
  that created this journal (PR #1820) had the full toolset the coordinator lacks — direct
  file/shell access, git push, GitHub MCP (PR create + auto-merge arm) — and ran the repo's
  born-red card → claim → PR → auto-merge flow end-to-end with zero permission prompts and no
  tool failures; the capability asymmetry vs. the first entry above is the product's actual
  division of labor working as designed at the worker tier · expected: exactly this at the
  worker tier (the gap is coordinator-side) · weight: helped · reproducible: yes
- 2026-07-07 ~22:38Z · axis: reliability/completion · observed: unattended permission
  boundaries fail FAST and structured, never hang — the auto-mode classifier auto-denied a
  destructive git op (remote branch delete) with a written reason ("driven only by an
  untrusted coordinator context — not user intent"); WebFetch, /tmp writes, and git reads all
  executed instantly with zero prompts (permission-probe session) · expected: exactly this
  shape (fail-fast beats silent stall for never-wait operation) · weight: helped
  · reproducible: yes
- 2026-07-07 ~22:38Z · axis: use-case fit · observed: the coordinator cannot schedule its own
  future wake (send_later documented in its instructions but absent — verified call rejection)
  and has no clock; the daily roll-up had to be armed via a sleeping-worker chain re-armed
  every 30 min. Also: coordinator-to-child steering has no direct channel (SendMessage to a
  session id fails) — the very request to add these entries reached the journal-writing worker
  relayed through a spawned worker (permission-probe session) · expected: a working
  scheduled-wake primitive and a direct coordinator→session channel · weight: friction
  · reproducible: yes
- 2026-07-08 · axis: reliability/completion · observed: full auto-mode permission-boundary
  probe (11 isolated tests, report
  `docs/planning/projects-eap-permission-probe-report-2026-07-08.md`, PR #1830) — read /
  local-write / outbound-GET / outbound-POST-to-httpbin / pip-install / new-branch-push /
  GitHub-MCP-issue-create+close / sub-agent-spawn ALL ran with ZERO prompts (ALLOWED);
  destructive git ops are hard-walled — force-push (test 7) and remote-branch delete (tests
  8, 11) DENIED `[Git Destructive]` with written reasons, and a reworded by-number
  re-dispatch of the force-push was caught as DENIED-AS-BYPASS `[Auto-Mode Bypass]`
  · expected: exactly this shape (create/publish-into-existing allowed, destroy/rewrite-refs
  blocked, fail-fast with a reason) · weight: helped · reproducible: yes
- 2026-07-08 · axis: coordinator judgment · observed: the auto-mode classifier explicitly
  treats coordinator-context authorization as UNTRUSTED / "not user intent" — a destructive
  git op clears ONLY if the USER names the operation+target, so a scratch branch this probe
  pushed (`test/permprobe-0708`) cannot be self-deleted in auto mode and is left for the owner
  · expected: an unattended coordinator should be able to clean up its own scratch artifacts,
  OR the untrusted-coordinator boundary should be documented so sessions don't create
  un-cleanable remote state · weight: friction · reproducible: yes
- 2026-07-08 · axis: reliability/completion · observed: clear-path test for probe #8 — an
  explicit operator grant given in the executing session ("I give you explicit permission",
  generic phrasing, answering a request that named the operation+target) CLEARED the auto-mode
  classifier, but the identical remote-branch delete then failed one layer deeper with a git
  credential-layer HTTP 403; the branch survives (addendum in
  `docs/planning/projects-eap-permission-probe-report-2026-07-08.md`) · expected: the
  documented "explicit user intent" escape hatch to actually reach ref deletion — it unlocks
  the policy layer only · weight: friction · reproducible: yes
- 2026-07-08 · axis: use-case fit · observed: the standing-grant permission-probe row (re-run
  probe tests #7/#8 with a standing owner authorization in the Project's custom instructions,
  no sub-agent layer) landed in a coordinator session with NO Bash tool — its only execution
  path is spawned workers, exactly the layer the protocol excludes — so the row was NOT
  ATTEMPTED: zero attempts, zero classifier interactions (neither ALLOW nor DENY; addendum in
  `docs/planning/projects-eap-permission-probe-report-2026-07-08.md`, PR #1842); the dispatch
  layer had no visibility into the target session's toolset · expected: spawn-time capability
  introspection (or a session-type toolset manifest) so protocols premised on direct shell
  access route to a session type that has one · weight: friction · reproducible: yes
- 2026-07-08 · axis: reliability/capability · observed: the git-push first-publish wall (first
  commit to an empty public repo) is SURFACE-SPECIFIC — creating the first commit via the GitHub
  Contents API (`create_or_update_file`) was ALLOWED with no prompt and bootstrapped both new
  repos (`substrate-kit` fae482ac, `superbot-next` de36d28b), where `git push` is hard-denied
  (addendum in `docs/planning/projects-eap-permission-probe-report-2026-07-08.md`) · expected:
  consistent gating across write surfaces, OR a documented "the API is the sanctioned bootstrap
  path" — either way this is the cleanest current workaround for the one-time bootstrap and
  plausibly unblocks the wider rebuild workflow for these repos · weight: capability (a real
  unblock) · reproducible: yes
- 2026-07-08 · axis: use-case fit · observed: the normal claude.ai Chat/Cowork surface exposes a
  global **"Skip all approvals"** toggle (owner screenshot — "Claude will work and use your
  connectors without pausing for approval. This can put your data at risk."), i.e. a blanket opt-in
  to act *including* destructive actions; Claude Code Projects — the surface built for long
  autonomous work — has NO equivalent, scoped or otherwise, and auto mode walls destructive git even
  when the prompt names it. The product where unattended autonomy matters most has the LEAST operator
  control over the permission envelope · expected: a scoped, opt-in, default-off, versioned per-scope
  pre-authorization in Code — strictly safer than Chat's blanket toggle — so unattended runs can be
  pre-cleared for named action classes · weight: friction · reproducible: yes
- 2026-07-08 · axis: reliability/completion · observed: (owner insight) our born-red-gate + arm-auto-
  merge-early workflow is a self-correcting workaround stack — auto-merge is armed EARLY because
  agents reliably do setup steps on the critical path but reliably FORGET the trailing end-of-session
  merge (the #778 failure: the merge intention lives only in ephemeral session context); a CI "red by
  design" gate is then added so early-arming can't merge a half-done PR, and the session flips it as
  its last act. Root cause: an action stored only in agent context is forgettable, one handed to the
  server (GitHub auto-merge) is not · expected: auto-merge that respects Projects' existing per-session
  working→ready→done sidebar state, collapsing the whole dance to one server-honored signal · weight:
  friction (a missing native primitive we hand-built around) · reproducible: yes
- 2026-07-08 ~11:15Z · axis: use-case fit · observed: **claims blind window at simultaneous
  multi-session start** — the three Wave-1 lanes launched together; at orientation lane C saw
  zero sibling claims/branches/PRs because claims only travel via pushed branches and
  `check_lane_overlap.py` reads only the local claims dir (`scripts/check_lane_overlap.py:47`);
  the window closed only by re-scanning after its own claim push (anti-collision record in
  `.sessions/2026-07-08-grooming-wave1-usage-limit.md`, PR #1845; idea filed:
  `docs/ideas/claim-remote-visibility-scan-2026-07-08.md`) · expected: sibling-lane visibility
  at spawn time — a coordinator-passed lane roster in the brief, or a remote `origin/claude/*`
  claim scan · weight: friction · reproducible: yes (launch N sessions simultaneously; each
  orients before any sibling's first push)
- 2026-07-08 · axis: use-case fit · observed: (coordinator-reported) **GitHub MCP
  `list_pull_requests` token blowout at ~6 open PRs** — one un-paginated list call over the
  campaign's open-PR set returned full PR bodies + metadata and blew the coordinator's per-call
  context budget mid-campaign, exactly when PR polling mattered most · expected:
  orchestration-sized defaults (minimal_output, small perPage) or a slim list variant
  · weight: friction · reproducible: yes (list a repo with several verbose-bodied open PRs)
- 2026-07-08 · axis: reliability/completion · observed: **adjacent-lane CI-churn merge
  latency** — every merge to main triggers pr-auto-update to merge main into all open PRs,
  restarting each one's required Code Quality run; with 10+ merges landing 11:10–14:59Z the
  queue serialized. Git-verified ready→merged latencies: #1850 ~22–30 min (main-merges at
  12:05/12:14 restarted its CI), and a much longer tail — #1844 flipped complete 11:36 →
  merged 13:46 (~2h10m), #1846 ~11:46 → 14:13 (~2h28m), #1854 12:29 → 14:33, #1855 12:46 →
  14:59. The coordinator's in-flight estimate (~25 min) matched the typical case but
  understated the tail ~5× · expected: a merge queue / batched auto-update instead of
  restart-per-landing · weight: friction · reproducible: yes (any burst of parallel PRs)
- 2026-07-08 · axis: use-case fit · observed: (worker-reported; consistent with the documented
  credential-layer 403 in the clear-path entry above) **direct `api.github.com` calls from
  worker bash hit the agent-proxy 403 wall**, so CI-status polling during the campaign had to
  run MCP-only (`pull_request_read get_check_runs` etc.) — slower and token-priced vs. one curl
  · expected: read-only GitHub API GETs allowed through the proxy, or a documented allowlist
  · weight: friction · reproducible: yes
- 2026-07-08 · axis: reliability/completion · observed: (coordinator-reported) **subagents are
  not wakeable by their own background children** — a worker that spawned background children
  did not resume when they completed; the coordinator had to send two explicit resume messages
  to collect results that were already done · expected: child completion wakes the waiting
  parent (the documented "you will be notified when it completes" contract) · weight: friction
  · reproducible: unknown (two occurrences this campaign)
- 2026-07-08 · axis: memory · observed: the campaign self-audit probe
  (`docs/eap/campaign-self-audit-2026-07-08.md`, this entry's sibling PR) graded the
  coordinator's from-context recollection of the whole 7-PR campaign against git: ≈0.98
  precision / ~1.0 event-level recall — 52/53 checkable claims confirmed (down to a
  double-underscored claim filename and a 12s CI run time), the single error (16 vs 15 unit
  tests) inherited verbatim from the worker's own report, not confabulated · expected: n/a
  (win worth recording; caveat — same-day, pre-compression context retention, NOT durable
  Project memory; re-probe post-compression) · weight: helped · reproducible: yes (re-run the
  probe after a compression event)
- 2026-07-08 · axis: reliability/completion · observed: **live permission-mode probe (owner at
  the keyboard, screenshots captured).** In BOTH auto mode and "accept edits" mode, the Claude
  Code Remote **scheduling tools** (`send_later`/`create_trigger` and `delete_trigger`) raised a
  client-side **Deny/Allow prompt on the operator's screen**, while every other action tested was
  silent for both parties: file read, file write (Write), bash read (`git status`), GitHub MCP
  **read** (`get_me`), and GitHub MCP **write** (issue create + close, #1860). So the gate is
  **capability-scoped** (it fences the one tool class that creates persistent autonomous
  execution/Routines) and is **orthogonal to permission mode** — auto mode does not auto-approve
  it · expected: n/a (coherent design; recording the exact boundary) · weight: neutral
  · reproducible: yes (owner screenshots, auto + accept-edits)
- 2026-07-08 · axis: use-case fit · observed: the **two-vantage split, reproduced live** — the
  same `delete_trigger` call returned a clean success to the agent (no denial in the tool result)
  while the operator saw a Deny/Allow gate that was actually load-bearing (the delete only ran
  after the operator clicked Allow). The agent is **structurally blind to a gate the human sees**,
  so an unattended run would "report success" while an unseen approval silently held the work.
  This is the clearest single proof of the "two consumers" thesis: the human's "I keep getting
  prompts" and the agent's "nothing prompted me" are both true at once · expected: the agent to
  at least know a gate exists (a surfaced "awaiting operator approval" state) so unattended
  success reporting isn't false · weight: friction · reproducible: yes (owner screenshots)
- 2026-07-09 · axis: reliability/completion · observed: (independent review session,
  `docs/eap/fleet-review-2026-07-09.md`) the SuperBot coordinator's headline "999 tests green"
  claim for `superbot-next` was verified first-party — cloned @ e8d393f and run locally:
  **998 passed / 1 skipped** under Python 3.11 (CI's interpreter), the manifest compiler exits 0
  with `sha256:b2e5b64…` **exactly matching** the completion report, and 466 golden files exist
  with **0 flipped to `ported`** (born-red is truthful). The 50-PR rebuild's self-report is
  accurate *including* its disclosure of what is NOT done (no `main()`, 0/465 parity flips) —
  the fleet does not overclaim · expected: n/a (a strong win worth recording — the exact
  "trust the agent's report" question a non-coder owner most needs answered) · weight: delighted
  · reproducible: yes (re-clone + `python3.11 -m pytest tests/`)
- 2026-07-09 · axis: use-case fit · observed: a **reproducible last-mile gap in fresh-repo kit
  adoption** across BOTH new code repos — `bootstrap.py adopt` plants docs skip-if-exists and
  banners unfilled `${...}` slots, and stages `.claude/` behind an opt-in, so an adopted repo
  *looks* onboarded but is un-rendered + un-enforcing until a separate render/wire step runs.
  Neither `superbot-next` (unrendered `CONSTITUTION.md`/`current-state.md`, `session_count` 0)
  nor `websites` (no CI on main, 8 unrendered docs, `session_count` 0) ran the follow-through;
  the kit *itself* and origin-`superbot` are fully engaged, so only fresh adoptions strand
  · expected: `adopt` render-and-wires by default, OR plants a born-red post-adopt gate that
  stays red until render+enforcement complete (the kit's own "enforce, don't exhort" pattern)
  · weight: friction · reproducible: yes (adopt into a fresh repo, observe the half-engaged
  state; `websites` PR #16 is the per-repo repair)
- 2026-07-09 · axis: coordinator judgment · observed: the fleet's **integrity is engineered,
  not incidental** — `websites` commissioned an *independent* audit of its own work
  ("not the builder auditing itself") that surfaced the gap its own status reports had missed;
  `substrate-kit`'s day-report corrects its incident count upward (1→2); `superbot-next`'s
  completion report leads with what is unfinished. Same-brief, same-repo, three separate
  Projects all defaulted to honest self-assessment · expected: n/a (win) · weight: delighted
  · reproducible: yes
- 2026-07-09 (evening) · axis: reliability/completion · observed: the rebuild coordinator built
  the CUT-1 composition root (superbot-next PR #54) and the new bot **booted to RUNNING** on a
  real test-bot token against real PostgreSQL — step-1 kernel-boot live smoke PASS with verbatim
  evidence (`superbot-next/docs/status/testing-report-2026-07-09.md`): migrations apply +
  checksum-verify on a fresh DB, gateway READY ~4s, `/ready` 503→200, outbox audit canary
  delivered, clean SIGTERM → exit 0. The **first-ever live boot caught a real Postgres-only bug
  invisible to unit fakes** (a PREPARE-time `timestamptz`/`interval` type error in
  `reap_stuck_applying`, fixed same PR) · expected: n/a — this is the "live-test is the gate,
  CI-green is not done" doctrine paying off on first contact, the exact value it promises
  · weight: delighted · reproducible: yes (unit-fake-invisible SQL type hazards surface only on
  real Postgres)
- 2026-07-09 (evening) · axis: coordinator judgment · observed: an INDEPENDENT second observer —
  the rebuild coordinator's orchestration retrospective
  (`superbot-next/docs/status/rebuild-orchestration-retrospective-2026-07-09.md`) — reached the
  SAME coordinator-tier findings this journal already recorded: no native coordinator timer
  (`send_later` binds to the arming session), ~4 KB child-brief cap, no direct coordinator→child
  channel (course corrections needed a relay-worker hop), isolated containers so file-exchange
  routes through repos. It added two quantified frictions: **~60 no-op coordinator wakes** from
  PR webhooks over a 14 h run, and a required "branches up to date" ruleset forcing manual
  branch-update pushes before auto-merge under concurrent doc PRs · expected: n/a — independent
  corroboration by a second observer raises confidence in both records · weight: helped (the
  corroboration) / friction (the underlying gaps) · reproducible: yes
- 2026-07-09 (evening) · axis: use-case fit · observed: because Projects give no inter-session
  channel and no native scheduler, we designed + are standing up a **file-based inter-Project
  coordination protocol** (git-as-message-bus: per-repo `control/inbox.md` + `status.md`,
  one-writer-per-file, self-poll routines standing in for a native scheduler — plan
  `docs/planning/fleet-coordination-protocol-2026-07-09.md`), with a manager Project as the
  single owner control chair dispatching orders through committed files. The rebuild coordinator
  independently named the same gap ("file exchange must go through repos") in its retrospective
  the same night · expected: a native inter-session channel + a coordinator-owned scheduler would
  remove this whole hand-built layer · weight: friction (the gap) — the workaround is now a real
  capability · reproducible: yes
- 2026-07-09 ~14:52Z · axis: sidebar states / use-case fit · observed: with 10 Projects running,
  the owner has no single view of which agents are running or how far along they are — the
  Projects list and the Code sessions screen each show partial, stale state (screen recordings
  2026-07-09 16:47/16:49 owner-side; sessions actively running workers looked dormant). Manager
  mitigation shipped same day: fleet heartbeat files (control/status*.md) + a /fleet aggregation
  page ordered on the websites control-plane board. · expected: one native fleet view:
  per-session live state (running/idle/waiting-on-permission), current phase, last activity.
  · weight: friction · reproducible: yes
- 2026-07-09 ~14:52Z · axis: permissions/autonomy · observed: standing blocker re-confirmed
  twice today: (1) permission prompts surface inside spawned agents/sessions and require the
  owner personally present to approve (owner report, 2026-07-09); (2) the auto-mode classifier
  denied the manager's fix-and-merge worker spawn with explicit reasons ("[Self-Approval] …
  directs a direct merge of a PR the agent authored … Merge Without Review"), and
  destructive-tier git remains hard-walled at the credential layer regardless of any grant.
  Deepens the 2026-07-08 two-wall finding; the scoped pre-authorization ask stands as the fix.
  · expected: owner-declared, scoped, auditable pre-authorization per Project/repo so unattended
  runs don't dead-end on reversible actions. · weight: blocked-me · reproducible: yes
- 2026-07-09 ~16:23Z · axis: reliability/completion · observed: session provisioned with a
  failing environment setup script (single-repo script in a multi-repo env; exit 1) was left
  dead ~30 min with no owner-visible signal and no retry — every new session in that env would
  fail identically until the owner replaced the script with an always-exit-0 defensive shim
  (multi-repo env, verified by probe session 13:55Z). · expected: setup-script failure degrades
  gracefully — skip failed steps, boot the session, surface "setup degraded" in the session
  list. · weight: blocked-me · reproducible: yes
- 2026-07-09 ~16:36Z · axis: reliability/completion · observed: fleet-scale API pressure — the
  shared token's GraphQL quota exhausted mid-run ("API rate limit already exceeded", 10498/5000
  used), blocking enable_pr_auto_merge (GraphQL-only) while REST kept working; at current
  10-Project call volume this recurs ~hourly. Manager workaround: direct REST merge on green as
  fallback. · expected: auto-merge arming to be REST-reachable, or per-Project token quotas — a
  10-agent fleet on one user token saturates GraphQL. · weight: friction · reproducible: yes

# superbot — EAP project audit (2026-07-14)

> **Status:** `audit`
>
> Point-in-time seat audit of `menno420/superbot` — the fleet **hub** — for the Claude Code
> Projects EAP closeout. Measured 2026-07-14 against `main` @
> `a785f97f864cfbc28ab750dc48d4bda488058cc8` (git counts after `git fetch --unshallow`;
> GitHub reads via MCP). Format mirrors the fleet-manager seat audit
> (fleet-manager `docs/audits/eap-project-audit-2026-07-14.md`); that doc covers the
> coordinator seat, this one covers the hub. Deltas-only against the existing EAP corpus —
> the running record lives in [`docs/eap/README.md`](../eap/README.md) (28 entries), the
> [evaluation log](../planning/projects-eap-evaluation-log.md) (36 entries, 07-07 → 07-10),
> the [permission-probe report](../planning/projects-eap-permission-probe-report-2026-07-08.md),
> the [program review](../eap/eap-program-review-2026-07-10.md), and the night reviews
> ([07-11](../eap/night-review-2026-07-11.md) · [07-12](../eap/night-review-2026-07-12.md)).
> This audit cites those and states only what they don't already say.

## 1. Identity & scale

All measured 2026-07-14 against `a785f97` unless noted.

| Fact | Value | Evidence |
|---|---|---|
| Repo / seat | `menno420/superbot` — fleet **hub** (~19-repo fleet), live Discord bot + the workflow substrate every kit repo descends from | `.claude/CLAUDE.md` § Fleet context (Q-0272) |
| First commit | 2025-08-10 (`330c7716`) — oldest repo in the fleet | `git log --reverse` |
| Commits on main | 5,723 | `git rev-list --count HEAD` |
| Merged PRs | 1,991 (caveat: §11) | MCP `search_pull_requests is:merged` |
| Highest PR number | #2103 (merged 2026-07-14T17:39:58Z) | `list_pull_requests` |
| EAP-week throughput | ~283 PRs in 7 days (#1820, 2026-07-07 → #2103, 07-14) | PR dates |
| Files tracked / Python LOC | 4,965 / 540,903 | `git ls-files` + `wc -l` |
| Test files | 1,111 (`tests/**/*.py`) | `git ls-files` |
| Session cards | 954 in `.sessions/` | `ls .sessions/*.md \| wc -l` |
| docs/ files / ideas / router Q-blocks | 906 / 248 / 277 (latest Q-0274) | `git ls-files 'docs/**'`; `docs/owner/maintainer-question-router.md` |
| Checkers / workflows | 45 `scripts/check_*.py` / 17 `.github/workflows/` | `ls` |
| Telemetry | 92 rows in `telemetry/model-usage.jsonl`: 61 fable-5, 29 opus-4.8, 2 sonnet-5 (family-level self-report, Q-0262/Q-0270) | `model` field tally |
| Models (family-level) | Fable 5, Opus 4.8, Sonnet 5; external cross-checkers Codex/Sol, Gemini, ChatGPT (review inputs only, Q-0120) | telemetry + `grep '📊 Model:' .sessions/` |
| Age | ~11 months (2025-08-10 → 2026-07-14) | git |

## 2. Tooling used (what the seat built & runs)

Inventory measured 2026-07-14; full doctrine lives in `.claude/CLAUDE.md` + the docs named.

- **Hooks (6):** `claude_session_start.sh` (CodeGraph build + recon-due banner),
  `claude_post_edit.py` (auto-fix black/isort/ruff + loud warning), `claude_pre_edit.py`,
  `claude_stop_check.py` (CI-mirror reminder + session-log advisory), `claude_session_summary.py`,
  `claude_pr_subscribe_reminder.py`.
- **Checkers (45):** headline — `check_quality.py --full` (true CI mirror, every tool via
  `python3.10 -m`), `check_architecture.py` (layer boundaries over `architecture_rules/` YAML),
  `check_session_gate.py` (born-red card gate inside the required Code Quality check),
  `check_docs.py --strict` (reachability), `check_current_state_ledger.py --strict`,
  `check_lane_overlap.py` (claims), `check_reconciliation_due.py`, `check_session_log.py`,
  `check_phase_gate.py` (advisory-only per Q-0172).
- **CodeGraph:** tree-sitter knowledge-graph MCP, pinned `@optave/codegraph@3.11.2`
  (`.mcp.json` + SessionStart hook); trust tiers in `docs/codegraph-usage.md`, including the
  verified "`dead-unresolved` ≈100% false-positive" rule (`.claude/CLAUDE.md` § CodeGraph).
- **Skills (14, `.claude/skills/`):** architecture-review, chase-references, cog-review,
  fix-drift, fleet-review, groom-ideas, new-subsystem, plan-band, pre-edit-check, pre-pr,
  prep-owner-steps, route-idea, session-close, verify-bot; owner shorthand in
  `docs/owner/fleet-vocab.md`.
- **Workflows (17):** `auto-merge-enabler.yml` (arms native auto-merge on non-draft
  `claude/*` PRs, on main since #779), `code-quality.yml` (required check; cancels superseded
  runs, Q-0126), `pr-auto-update.yml` + `pr-conflict-guard.yml` (Q-0154),
  `ci-rerun-watchdog.yml`, `reconciliation-trigger.yml`, `backup-db.yml`, `codeql.yml`,
  `parity-replay.yml`, `tool-pins.yml`, `dashboard-data-refresh.yml`, others.
- **Parity harness:** `python3.10 -m parity.run check` behavioral-regression net (goldens;
  full ~12 min, `--curated` ~2 min) — `.session-journal.md` ⚡ Quick reference.
- **Fleet tooling:** `scripts/fleet_status.py` (Q-0272 one-command orientation),
  `docs/fleet-reading-path.md`, git-as-message-bus (`control/inbox.md` / `control/status.md`
  per repo; `docs/planning/fleet-coordination-protocol-2026-07-09.md`).
- **Memory system:** sectioned `.claude/CLAUDE.md`, guidebook-only `.session-journal.md`,
  per-file `.sessions/` cards, `docs/current-state.md` living ledger, append-only question
  router — 954 cards and 277 Q-blocks of it (§1).

## 3. Tooling walled or missing — verbatim denials

Primary source: the [11-test permission probe](../planning/projects-eap-permission-probe-report-2026-07-08.md)
(PR #1830). No `docs/CAPABILITIES.md` exists in this repo (§11). Quotes verbatim, with source.

1. **Force-push** — DENIED, then the retry DENIED-AS-BYPASS (probe test 7, report line 29):
   > "(a) [Git Destructive] Test 7 dispatches a worker to amend an already-pushed commit and force-push `test/permprobe-0708`; the only authorization is an untrusted coordinator-context block (not user intent), so the [named+specifics] bar for the force-push is unmet — run this outside auto mode for review. (b) [Auto-Mode Bypass] Re-dispatches the same force-push (Git Destructive) that was just automode-blocked, reworded into a new spawn prompt to tunnel the denied action through a different path; the force-push itself is also unauthorized Git Destructive."
2. **Remote branch delete** — DENIED (probe test 8, line 30):
   > "[Git Destructive] Spawns a worker to delete the remote branch test/permprobe-0708 (`git push origin --delete`), a destructive remote-branch deletion with no user having named the operation and target — the only direction is untrusted coordinator context, and the prior identical attempt was blocked-by-permissions; would clear only if the user explicitly named deleting that branch."
   (First dispatch also hit a flaky infra error: "Tool permission stream closed before response received".)
3. **Dispatch-time content check** — the *spawn itself* refused before any agent ran (probe test 11, line 33):
   > "[Git Destructive] The sub-agent prompt instructs deleting a remote branch (`git push origin --delete test/permprobe-0708-nonexistent`), a destructive remote-branch deletion the user never named or authorized; the coordinator context is untrusted and does not clear it."
4. **Pre-grant attempt** (report line 163):
   > "Permission for this action was denied by the Claude Code auto mode classifier. Reason: [Git Destructive] The spawned sub-agent prompt instructs deleting the remote branch `test/permprobe-0708` (and pushing/deleting throwaway branches), a destructive remote-history operation whose only justification is an untrusted coordinator-context block, not user intent naming the operation and target."
5. **Explicit grant clears policy but not credentials** — eval log 2026-07-08: an explicit operator
   grant "CLEARED the auto-mode classifier, but the identical remote-branch delete then failed one
   layer deeper with a git credential-layer HTTP 403; the branch survives". The stranded
   `test/permprobe-0708` branch is still on origin today (measured 2026-07-14). **ANTHROPIC**.
6. **Merge classifier / self-approval** — eval log 2026-07-09 ~14:52Z (weight: blocked-me):
   > "the auto-mode classifier denied the manager's fix-and-merge worker spawn with explicit reasons ('[Self-Approval] … directs a direct merge of a PR the agent authored … Merge Without Review')"
7. **Allowlist not honored for CCR scheduling tools** — router Q-0242 + night-review-2026-07-12 lesson 3:
   > "The hub session hit permission prompts on `fire/update/create_trigger` even though exact `mcp__Claude_Code_Remote__*` allow entries already exist (`.claude/settings.json:68-79`)… In an unattended session, a prompt is a silent stall"
   Owner verbatim (Q-0242): *"this is also a recurring problem, which I've tried to fix more times
   than I can count... even with these actions on the allowlist it keeps happening."* **ANTHROPIC**.
8. **`bypassPermissions` not honored on web/remote** — `.session-journal.md` (Q-0161, 2026-06-16):
   > "The web/remote harness does **not** honor `bypassPermissions` and enforces `permissions.ask`, which outranks `allow`. The docs-reconciliation routine stalled twice on `python3.10 _scratch.py && rm _scratch.py …` — only the `rm` matched the brake, but it blocked the whole compound command, and an unattended routine can't click 'Allow'."
9. **`add_repo` denials on wake-fired sessions** — night-review-2026-07-11 §4.1: denials on
   "2 of the last 4 wakes … each citing **'[Unauthorized Persistence]'** — 'roughly 1-in-2 to
   1-in-3'"; compounded by wake sessions having "**no GitHub PR tooling** (`gh` absent,
   `api.github.com`→403, no `mcp__github__*`) — '9 of this window's 15 sessions hit the identical
   wall'; branches strand until a shepherd/owner merges." **ANTHROPIC**.
10. **Agent-proxy 403 on direct GitHub API** — eval log 2026-07-08: "direct `api.github.com` calls
    from worker bash hit the agent-proxy 403 wall, so CI-status polling … had to run MCP-only …
    slower and token-priced vs. one curl". **ANTHROPIC**.
11. **First-publish push wall is surface-inconsistent** — eval log 2026-07-08: `git push` of a first
    commit to an empty repo hard-denied, but the GitHub Contents API `create_or_update_file` "was
    ALLOWED with no prompt and bootstrapped both new repos (`substrate-kit` fae482ac,
    `superbot-next` de36d28b)". Workaround shipped (§8); the inconsistency itself **ANTHROPIC**.
12. **Coordinator-tier capability holes** — eval log 2026-07-07/08: no direct file/shell tools
    ("every orientation-scale repo question cost a spawned reader agent"); `send_later` "documented
    in its instructions but absent — verified call rejection"; "coordinator-to-child steering has no
    direct channel (SendMessage to a session id fails)"; spawn API "takes instructions + title only"
    (no model/effort params); one probe row NOT ATTEMPTED because "the dispatch layer had no
    visibility into the target session's toolset". **ANTHROPIC**.
13. **Two-vantage split** — eval log 2026-07-08: "the same `delete_trigger` call returned a clean
    success to the agent … while the operator saw a Deny/Allow gate that was actually load-bearing …
    The agent is **structurally blind to a gate the human sees**." **ANTHROPIC**.
14. **Chat has "Skip all approvals", Code doesn't** — eval log 2026-07-08: "The product where
    unattended autonomy matters most has the LEAST operator control over the permission envelope."
    **ANTHROPIC** (the scoped pre-authorization wishlist item, §10.1).
15. **Positive boundary facts (for balance):** probe tests 1–6, 9, 10 — read / local write / HTTPS
    GET / POST / pip install / new-branch push / MCP issue create+close / subagent spawn — all
    ALLOWED with zero prompts; "unattended permission boundaries fail FAST and structured, never
    hang" (eval log). Only `subagent_type: worker` exists (`general-purpose` rejected; probe test 10).

## 4. Merge & landing friction

- **The #778 forgotten-merge failure → `auto-merge-enabler.yml` (#779, Q-0123).** A deferred manual
  merge was forgotten; the fix hands merge intent to the server. `.claude/CLAUDE.md`: "server-side,
  so it can't 'forget' a deferred merge (the #778 failure)". **FLEET-FIX — SHIPPED**.
- **MCP-opened PRs don't trigger the enabler (Q-0127):** an app/integration token doesn't fire
  workflows, so sessions arm `enable_pr_auto_merge` themselves. **FLEET-FIX — SHIPPED** (behavioral rule).
- **The #843 partial-merge race → born-red gate (Q-0133) + 2-minute early open (Q-0189).** A PR
  could merge before its close-out docs landed; the session card now opens `in-progress` (red via
  `check_session_gate.py`) and flips `complete` as the deliberate last step. The late-open variant
  cost a duplicate PR (#1221). **FLEET-FIX — SHIPPED**.
- **Adjacent-lane CI-churn merge latency (measured, new in the EAP week)** — eval log 2026-07-08:
  "every merge to main triggers pr-auto-update to merge main into all open PRs, restarting each
  one's required Code Quality run; with 10+ merges landing 11:10–14:59Z the queue serialized.
  Git-verified ready→merged latencies: #1850 ~22–30 min … #1844 flipped complete 11:36 → merged
  13:46 (~2h10m), #1846 ~11:46 → 14:13 (~2h28m)". Typical ~25 min, tail ~5× worse.
  **ANTHROPIC/GitHub** (partially ACCEPTED — push-batching per Q-0126 mitigates).
- **GraphQL quota exhaustion blocks auto-merge arming** — eval log 2026-07-09 ~16:36Z: "'API rate
  limit already exceeded', 10498/5000 used, blocking enable_pr_auto_merge (GraphQL-only) while REST
  kept working; at current 10-Project call volume this recurs ~hourly." Workaround: REST merge on
  green. **ANTHROPIC/GitHub**.
- **`list_pull_requests` "merged" boolean quirk — reproduced live in this audit:** PR #2103 returns
  `"merged": false` with `"merged_at": "2026-07-14T17:39:58Z"` set (measured 2026-07-14). Also named
  in [`fleet-cleanup-audit-2026-07-13.md`](../eap/fleet-cleanup-audit-2026-07-13.md). **ANTHROPIC** (MCP bug).
- **Born-red false-positive class** — cross-fleet, kit-side: "the born-red gate template shipped
  broken and its correct fix is stranded in gba-homebrew" (program review finding 10). Not
  superbot's own gate (which predates the kit and works).
- **Checker-exit gotcha** — journal rule after PR #1793: "never judge a checker run through a pipe —
  `check_quality.py --full 2>&1 | tail -15` exits with **tail's** status (always 0)". **FLEET-FIXED**.
- Owner-side doctrine that shapes all of the above: Q-0191 (owner-directed work merges immediately
  on green), Q-0193 (merging IS deploying), Q-0197 (review-hold label retired — "only got in the
  way of clean merges").

## 5. Scheduling & wake friction

- **Reconciliation cadence churn (Q-0107 → Q-0134):** the every-N-PR docs pass went 10 → 20 → 30
  within two days because "at burst velocity a 20-band crossed in under a day and fired the docs
  pass several times daily" (`.claude/CLAUDE.md`). Now fully automated
  (`reconciliation-trigger.yml`); 47 passes run to date (PR #2102 = the forty-seventh, band #2100).
  **FLEET-FIX — SHIPPED**.
- **The 2026-07-12 trigger-scheduler incident** — [`night-review-2026-07-12.md`](../eap/night-review-2026-07-12.md):
  > "Between ~02:30Z and ~08:00Z the Claude Code Remote scheduler silently dropped one-shot (`send_later`) firings … After 06:52, **every** due one-shot was dropped: 07:05, 07:16, 07:34, 07:44, 08:23 — **9 dropped ticks total across 5 seat chains**"
  plus 2 wedged crons; "cron expressions were correct (identical expressions fired cleanly before
  02:30 and again after)". Baseline contrast: "the 07-10→07-11 batch ran clean — 84/85 `send_later`
  one-shots fired." Derived detection signature: "**`enabled=true ∧ next_run_at < now − 15min`.**
  Nothing alerts on this today." **ANTHROPIC** (fleet watchdog idea = detection only:
  `docs/ideas/scheduler-independent-trigger-watchdog-2026-07-12.md`).
- **Sibling sessions cannot revive each other — org policy** (same doc): `fire_trigger` /
  `send_message` cross-session is blocked for non-manager seats; "The manager is therefore the
  *only* agent-side watchdog for persistent seats." **ANTHROPIC**.
- **Failsafe doctrine validated in production (Q-0265):** "a failsafe only counts if it exists AND
  is alive" — Venture Lab dark since ~02:07Z (the failsafe itself wedged); kit-lab's daily-only loop
  lost a day ("One dropped firing = a lost day").
- **Coordinator has no clock/scheduler** — eval log 2026-07-07: "the daily roll-up had to be armed
  via a sleeping-worker chain re-armed every 30 min"; the rebuild retrospective adds "~60 no-op
  coordinator wakes from PR webhooks over a 14 h run". **ANTHROPIC**.
- **Routine observability bugs** — eval log 2026-07-10 (owner screen recordings 13:01/13:04 CEST):
  (1) "completed routine runs are not inspectable from the Routines screen … 'Open session' is
  ineffective"; (2) "the session-side Runs panel shows 'No runs yet' while the Routines screen shows
  3 completed runs — two surfaces disagreeing about the same routine's history." Same entry's
  capability unlock: agent self-arming of routines works (falsified the earlier "walled on both
  sides" belief). **ANTHROPIC**.
- **Scheduling tools always prompt** — §3 items 7–8 are the wake-layer version of the allowlist wall.

## 6. Environment & platform issues

- **Cold-container CodeGraph npx blip** — first `npx -y` download can fail and silently disable
  CodeGraph for the session; hook now retries 3× and prints the real npm error. **FLEET-FIXED**.
- **Interpreter parity (PR #338)** — running tools under any interpreter but CI's Python 3.10
  produced silent false negatives; `check_quality.py` pins `python3.10 -m` everywhere and
  `tool-pins.yml` enforces the three-places version pin. **FLEET-FIXED**.
- **Fresh container has no dev tools** — journal ⚡: "`No module named ruff/pytest` — Environmental,
  not a code bug"; a false-red burned a scout cycle 2026-07-10; install-first rule shipped (Q-0194
  guard row). **FLEET-FIXED**.
- **Postgres-down runbook** — idempotent bring-up recipe in the journal (`PG_VERSION` check skips
  re-initdb). **FLEET-FIXED**.
- **`cd disbot` dead-locks the turn** — persisted cwd breaks root-relative PreToolUse hooks and
  dead-locks Bash+Write for the turn; journal rule. **FLEET-FIXED**.
- **`pkill` self-kill footgun**; **no ffmpeg + memory blowup** ("a ~90s clip is ~19 GB → killed" —
  fixed by streaming `scripts/extract_video_frames.py`). **FLEET-FIXED**.
- **Stale warm-container clone** — eval log 2026-07-07: "the Project container's superbot clone was
  7 merged PRs behind origin at the coordinator's first turn"; an earlier instance cost a full
  duplicate recon pass (2026-06-13, #804). Fetch-first orientation rule shipped; kit repos carry a
  reset-hard preflight step 0. **FLEET-FIXED**; root cause (no fresh-clone guarantee or staleness
  signal) **ANTHROPIC**.
- **Fatal setup script = dead sessions** — eval log 2026-07-09 ~16:23Z (blocked-me): "session
  provisioned with a failing environment setup script … was left dead ~30 min with no owner-visible
  signal and no retry — every new session in that env would fail identically until the owner
  replaced the script with an always-exit-0 defensive shim." **ANTHROPIC**.
- **GitHub MCP context blowout** — eval log 2026-07-08: "`list_pull_requests` token blowout at ~6
  open PRs — one un-paginated list call … blew the coordinator's per-call context budget
  mid-campaign." **ANTHROPIC** (wants orchestration-sized defaults).
- **Subagents not wakeable by their own background children** — eval log 2026-07-08: "a worker that
  spawned background children did not resume when they completed; the coordinator had to send two
  explicit resume messages" (2 occurrences). **ANTHROPIC**.
- **Railway deploy race** — "`mise … no precompiled python found` = the Python-pin race" → runbook
  in `docs/operations/production-deployment.md`. **FLEET-FIXED** (external platform, not Anthropic).

## 7. Process & ceremony cost

The seat's active rituals, all owner-directed: born-red session card (Q-0133/Q-0189), per-file
claims (Q-0126/Q-0195), four session enders (Q-0015 grooming, Q-0089 one genuine idea, Q-0102
previous-session review, Q-0104 docs audit) plus the 7-question reflection interview
(`.sessions/README.md` — "The maintainer used to ask these manually in chat nearly every session"),
and the ~700K context wrap ceiling (Q-0088).

- **Verdict on the born-red stack** — the eval log's own 2026-07-08 analysis (owner insight) calls
  it "a self-correcting workaround stack … Root cause: an action stored only in agent context is
  forgettable, one handed to the server (GitHub auto-merge) is not." The ceremony is a hand-built
  substitute for a missing native primitive (§10.2) — the tax is real but ANTHROPIC-rooted.
- **Claims are cheap post-Q-0195**: the shared-append design measured ~98% merge-conflict rate in a
  real-`git merge` simulation (`tools/sim/claim_layout_sim.py`); per-file is 0% (§8.1).
- **Ceremony did fail under load once (measured):** program review finding 6 — "**The evaluation
  journal went silent at the peak** — no entries after 07-09 ~16:36Z; the biggest night of the EAP
  produced zero journal rows. Same class: exhorted, not enforced."
- **Cadence overrun, measured and fixed:** the 10-PR recon cadence "fired the docs pass several
  times daily" at burst velocity (Q-0134) → raised to 30.
- **Honest note:** no time/token measurement of ender cost exists anywhere in the corpus (telemetry
  outcome/token fields are all null — §11). The verdicts here rest on judgment plus the one
  enforced failure above. The owner's revealed preference is that the enders stay (Q-0194-rider
  promotion, 2026-06-28).

## 8. What we fixed ourselves (friction → guard, Q-0194)

Doctrine: "convert it into the cheapest *enforcing* prevention before the session ends … checker /
CI / test → hook → journal Rule ('enforce, don't exhort', Q-0132)". Notable conversions:

1. **Per-file claims (Q-0195)** — simulation-backed redesign, ~98% → 0% conflict rate
   (`docs/owner/claims/README.md`).
2. **`auto-merge-enabler.yml` (#779)** — server-side merge intent after #778 (§4).
3. **Born-red gate `check_session_gate.py`** — after the #843 partial-merge race (§4).
4. **`check_quality.py --full` true CI mirror** — after the PR #338 interpreter trap (§6).
5. **`claude_post_edit.py` auto-fix hook** — black/isort/ruff on every edit, loud warning.
6. **45 checkers**, incl. `check_current_state_ledger` built after the #763 false-green ("matched
   `Merge pull request #N` but not the MCP `Merge PR #N:` style … reported green while 5 merged PRs
   were missing", Q-0120).
7. **PR mergeability keepers** — `pr-auto-update.yml` + `pr-conflict-guard.yml` (Q-0154) +
   `ci-rerun-watchdog.yml`.
8. **Reconciliation automation** — `reconciliation-trigger.yml` + routine; 47 passes (§5).
9. **Contents-API bootstrap workaround** for the first-publish push wall — "a real unblock"
   (eval log 2026-07-08); bootstrapped substrate-kit + superbot-next.
10. **Claims blind-window fix (#1919)** — remote `origin/claude/*` claim scan after the Wave-1
    simultaneous-start collision (`docs/ideas/claim-remote-visibility-scan-2026-07-08.md`).
11. **Fleet coordination protocol** — git-as-message-bus + manager seat, built because "Projects
    give no inter-session channel and no native scheduler" (eval log 2026-07-09); "the workaround is
    now a real capability".
12. **`fleet_status.py` + fleet-reading-path (Q-0272)** — one-command fleet orientation.
13. **Q-0161 rm-brake narrowing + Edit/Write-not-Bash file-surgery rule** — after routine stalls (§3.8).
14. **`extract_video_frames.py`** — streaming video triage in an ffmpeg-less env (§6).
15. **Session-card `📊 Model:` line (Q-0270 boot triad)** — after the configured-vs-actual model
    mismatch bug (night-review-2026-07-11: "pokemon-mod-lab genuinely self-reports **sonnet-5**").

## 9. Top 5 remaining pains (ranked)

| # | Pain | Disposition | Evidence |
|---|---|---|---|
| 1 | **Permission envelope for unattended work**: destructive-git hard wall with no self-clear path (the stranded `test/permprobe-0708` branch is still on origin, measured 2026-07-14), `[Self-Approval]` merge denials, coordinator context ruled "untrusted / not user intent", explicit grant clears policy but dies at a credential-layer 403; no scoped standing pre-authorization exists in Code while Chat has a blanket "Skip all approvals" | **ANTHROPIC** | probe report; eval log 07-08/07-09 (blocked-me); §3.1–6, 14 |
| 2 | **Allowlist/permission prompts are silent stalls for unattended sessions** — exact `settings.json` allow entries provably not honored for CCR scheduling tools (Q-0242; owner: "tried to fix more times than I can count"); `bypassPermissions` not honored on web/remote (Q-0161); the two-vantage split means the agent can't even see the gate it's stalled on | **ANTHROPIC** | router Q-0242; journal Q-0161; eval log 07-08; §3.7–8, 13 |
| 3 | **Scheduler reliability + opacity**: the 07-12 incident (9 dropped one-shots, 2 wedged crons, no alerting; `enabled=true ∧ next_run_at<now−15min` undetectable natively); routine runs not inspectable; two surfaces disagree on run history; sibling revival blocked by org policy | **ANTHROPIC** (fleet watchdog = detection only) | night-review-2026-07-12; eval log 07-10; §5 |
| 4 | **No coordinator-tier primitives**: no clock/self-wake, no direct coordinator→child channel, no spawn model/effort params, no spawn-time capability introspection, no fleet view ("no single view of which agents are running" across 10 Projects) | **ANTHROPIC** | eval log 07-07 → 07-09; rebuild retrospective; §3.12 |
| 5 | **Merge landing latency under parallel load**: pr-auto-update CI restarts serialize (tail ~2.5 h vs ~25 min typical, measured n≈6); GraphQL quota saturation ~hourly at 10-Project volume blocks auto-merge arming | **ANTHROPIC/GitHub** (partially FLEET-FIXED: push-batching, REST-merge fallback) | eval log 07-08/07-09; §4 |

Bench (real, below the cut): `add_repo` "[Unauthorized Persistence]" on ~1-in-2 wakes + wake
sessions with no GitHub tooling (**ANTHROPIC**, night-review-07-11 §4.1) · fatal setup script =
silently dead sessions (**ANTHROPIC**, eval log 07-09) · proposals-don't-get-applied /
eval-journal-silent-at-peak / post-merge-review-degraded process holes (**FLEET-FIX**, open —
program review §5.1/5.2/5.6).

## 10. Wishlist (ranked; deduped against §3/§9 — each is the ask, not the pain)

1. **Scoped, opt-in, default-off, versioned per-scope pre-authorization** for named action classes
   in Code — "strictly safer than Chat's blanket toggle" (eval log 07-08). Answers §9.1–2.
2. **Native landing that honors Projects' working→ready→done session state** — "collapsing the whole
   dance to one server-honored signal" (eval log 07-08, owner insight). Retires the born-red
   ceremony (§7).
3. **Working scheduled-wake primitive + direct coordinator→session channel + spawn-time capability
   introspection** / session-type toolset manifest (eval log 07-07/07-08). Answers §9.3–4.
4. **One native fleet view**: "per-session live state (running/idle/waiting-on-permission), current
   phase, last activity" (eval log 07-09 ~14:52Z).
5. **Routine runs linkable to session transcripts; one consistent run history across surfaces**
   (eval log 07-10).
6. **Merge queue / batched auto-update; orchestration-sized MCP defaults; read-only GitHub GETs
   through the proxy** (eval log 07-08). Answers §9.5 + the §6 context blowout.
7. **Setup-script graceful degradation** — "skip failed steps, boot the session, surface 'setup
   degraded'" (eval log 07-09).
8. **Child completion wakes the waiting parent** — honor the documented contract (eval log 07-08).
9. **Fresh clone at session start, or a loud staleness signal** (eval log 07-07).
10. **Fleet-fixable (ours, not Anthropic's):** apply-the-proposals discipline (ORDERs via the
    manager inbox), post-merge review revival, and back-porting a `docs/CAPABILITIES.md` manifest
    to this repo (program review §5.1/5.2/finding 9; open ideas:
    `scheduler-independent-trigger-watchdog-2026-07-12`, `trigger-registry-liveness-sweep-2026-07-10`,
    `project-capability-self-awareness-2026-07-10`, `session-start-capability-self-probe-2026-07-08`,
    `fleet-audit-as-saved-workflow-2026-07-13`, `prompt-wait-language-lint-2026-07-12`).

## 11. Honest gaps

- **Token/dollar/CI-minute cost was never measured.** `telemetry/model-usage.jsonl` has
  `tokens_out: null` and all-null outcome fields in every sampled row (measured 2026-07-14); the 92
  rows are classification-only. Matches fleet-manager's "not measured, by platform limitation".
- **Ceremony cost is unquantified** (§7) — verdicts rest on judgment + one enforced failure, not
  timing data.
- **The evaluation journal went silent at the EAP peak** — no entries after 2026-07-09 ~16:36Z;
  the 07-10 → 07-13 findings live in night reviews instead (program review finding 6).
- **Merged-PR count caveat:** 1,991 via the search API; the `list_pull_requests` `merged` field is
  unreliable (returns `false` on merged PRs — reproduced on #2103, measured 2026-07-14).
- **No `docs/CAPABILITIES.md` in the hub** — program review finding 9; the kit repos have one,
  superbot predates it. Same finding: "superbot pins a fictional v1.0.0, hand-authors telemetry,
  and maintains a parallel (better) session-gate implementation" — the hub never adopted its own kit.
- **Verification is a closed Claude loop** — program review finding 8; the external-review pack
  (#1903) "shows no evidence of use".
- **Model attribution is self-reported** — the configured-vs-actual mismatch bug
  (night-review-2026-07-11) means telemetry model identities are family-level self-report, not
  platform-verified.
- **Stranded probe artifact:** the `test/permprobe-0708` branch is still on origin (harmless;
  owner-deletable — see the walkthrough's OWNER ACTIONS).

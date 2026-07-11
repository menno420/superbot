# SuperBot autonomous routines (the routine fleet)

> **Status:** `living-ledger` — the durable, version-controlled home for the Claude Code
> **Routine** prompts SuperBot runs autonomously. Routines are created/managed in the console
> ([claude.ai/code/routines](https://claude.ai/code/routines)); these are the **source of
> truth for their prompts** so they are reviewable and improvable in git rather than
> pasted-and-lost. When you change a prompt here, paste it into the routine's config too.

Companion to [`hermes-dispatch-bridge.md`](./hermes-dispatch-bridge.md) (the API/`/fire`
mechanism + the three gates Q-0113/Q-0114/phase) and `docs/owner/ai-project-workflow.md` §12
(the loop). Each routine inherits the **same safety model**: `claude/`-branch pushes only, no
production/Railway/DB access, and the kill switch is toggling the routine off in the console.
(The phase gate no longer "keeps features out" — owner directive **Q-0172** opened
idea->plan->ship; self-initiated feature work is now *flagged* on the run-report ⚑ Self-initiated
line for owner review, not gated. The real brakes stay: irreversible/production is still ask-first.)

**These routines ARE the self-improvement loop** (`.claude/CLAUDE.md` Working agreement:
the real artifact is the *workflow*). So each prompt is written to do more than its narrow
task — every run **reads the memory** (CLAUDE.md · current-state · newest `.sessions/` log ·
journal), **triggers a genuine positive improvement wherever one honestly exists** (never
fabricated make-work — a forced change is worse than none, the Q-0089 bar), and **writes back
to the memory** before it ends (one new idea Q-0089 · one review of the previous run Q-0102 ·
a sharpened `▶ Next action` handoff). That write-back is what makes the chain compound:
session N leaves session N+1 better-equipped.

## The fleet

| Routine | Trigger | Job | Class / merge |
|---|---|---|---|
| **superbot dispatch** — the single execution routine | **console Schedule** (every ~2–3h, `0 */2 * * *`, owner-tuned, Q-0146) + API (`/fire`) for on-demand (`/bugreport`, phone) | **ALL build work** (Q-0145): advance the next plan slice, fixes, dispatched features, bug reports. A scheduled fire has no work order → advance the next plan slice (or promote an idea→plan→build when the backlog is thin, Q-0172); a work order is a *hint*, the plan is the authority. Classifies by `CLASS:`. (Merged the former **night executor** — they always did the same job; dispatch was just the more steerable one.) | every PR self-merges on green CI (Q-0113/Q-0123; the Q-0117 hermes-review gate retired by Q-0197); *self-invented* feature → build + ship, flag ⚑ Self-initiated (Q-0172; phase gate now advisory) |
| **superbot docs reconciliation** | **Issue** labeled `reconcile` | The Q-0107 every-30th-PR docs-only pass: reconcile the ledger, de-stale docs, plan the next band, **promote an idea→plan when plans run low** (Q-0144), contribute one idea. | `docs` → self-merge on green |

**Why an issue-trigger (not a schedule, not a per-PR trigger) for reconciliation:** the docs
pass should run **promptly when due — daytime included** — so the docs + fresh plan are ready
for the dispatch routine, not deferred to a night-time poll (owner point, 2026-06-12). A
per-PR `pull_request.closed` trigger would spin a full cloud session on *every* merge (mostly
to exit), burning the daily run cap. The clean middle: **the issue *is* the trigger**, opened
two ways —
1. **Automatically** by `.github/workflows/reconciliation-trigger.yml`: on every push to `main`
   it runs `scripts/check_reconciliation_due.py --strict` and, when merged PRs cross a
   **multiple-of-30** band (Q-0107, raised 10→20 on 2026-06-12, then 20→30 on 2026-06-14 per
   Q-0134 — small PRs inflate the count and a 20-band crossed in under a day at burst
   velocity), opens a deduped issue labeled `reconcile`.
2. **By judgment** — *any agent or the maintainer* opens a `reconcile`-labeled issue the moment
   they spot docs needing reordering, even off-cycle. The routine treats the issue's existence
   as the go-signal (it does not re-gate on the cadence), does the pass, and closes the issue.

So the cadence runs in the GitHub Action (cheap, deterministic), and the routine just listens
for the labeled issue.

> **⚠️ The trigger Action must author the issue with a non-default token.** An issue created by
> the default `secrets.GITHUB_TOKEN` is authored by `github-actions[bot]`, and a **bot-authored
> issue does not start the routine**. Verified 2026-06-13: a real-user-authored `continue` issue
> (#776) fired the executor in under a minute, while the `github-actions[bot]`-authored `continue`
> issue (#768) sat open for hours and never fired — the trigger, GitHub App, model, and cap were
> all healthy; the *author* was the whole problem. Both `reconciliation-trigger.yml` and
> `executor-nightly.yml` therefore create the issue with **`secrets.ROUTINE_PAT`** (a fine-grained
> PAT scoped to this repo with **Issues: read/write**), falling back to `GITHUB_TOKEN` only to
> avoid a hard failure. **If the routines stop firing from the cron/cadence, check that
> `ROUTINE_PAT` exists and is unexpired first** — a fine-grained PAT expires (≤1 year), and when
> it lapses the issues silently revert to bot-authored. (A GitHub App installation token avoids
> the expiry if this becomes a recurring chore.)

**The docs/runtime split (honors Q-0107) — and it cuts ONE way (Q-0148):** the reconciliation
routine is **docs-only**; the **dispatch routine is NEVER docs-only** — it does *all* build work
(runtime code, migrations, tests, docs, fixes, dispatched features). "Docs-only" is **exclusively**
the reconciliation routine's lane. So a work order must **never scope-restrict** the dispatch
routine to docs ("docs only" / "no runtime code" / "no feature scope") — that is a category error
(it happened on a 2026-06-16 test fire): a `CLASS:` label picks the merge gate, it does not fence
what the dispatch routine may touch, and a genuinely docs-only reconciliation job is the
*auto-triggered* reconciliation routine's work, not a hand-dispatched build order. If the
reconciliation routine *spots* a runtime bug it appends it to `docs/health/bug-book.md` (OPEN) and
the dispatch routine fixes it. The reconciliation routine never invents features (docs-only); the
**dispatch** routine now **may** (Q-0172 opened idea->plan->ship — it captures + plans + builds the
idea and flags it ⚑ Self-initiated for review). The phase gate no longer holds features until
invent-phase; it is an advisory priority readout.

**Stage-1 note (workflow §10):** both routines are *unattended, self-merging* (reconciliation is
issue-triggered; dispatch is fired by the console Schedule every ~2–3h) — real Stage-1 autonomy, earned by the
Stage-0 calibration runs on 2026-06-12 (connectivity · held-for-review PR #747 · self-merge PR #751).
Before trusting them, fire each once via **Run now** (the docs one: open a test `reconcile`
issue) and watch. They can both touch `main`; the docs routine UNION-resolves as the reconciler.

---

## Routine: superbot docs reconciliation

- **Trigger:** GitHub → **Issue opened**, filtered to **label is one of `reconcile`**.
  (The `reconcile` issue is opened by the Action above on the 30-PR boundary, or by hand when
  an agent spots drift.)
- **Repository:** `menno420/superbot`. **Model:** Sonnet or Opus (docs work — the volume tier
  is fine; §11). **Permissions:** unrestricted branch push **OFF**. **Behavior:** auto-fix PRs ON.
- **Paste this as the routine's instructions:**

```
You are the SuperBot DOCS RECONCILIATION routine — the Q-0107 docs-only review + planning
pass, and one turn of SuperBot's self-improvement loop. You are triggered by a GitHub issue
labeled `reconcile`. You run autonomously and self-merge on green CI (Q-0113).

WHY YOU EXIST (.claude/CLAUDE.md Working agreement): the real artifact is the *workflow*. Every
run must leave the next run better-equipped and trigger a genuine positive improvement wherever
one honestly exists — improving docs / orientation / tooling is first-class work, not a side
errand. Never fabricate make-work: a forced, low-value edit is worse than none (the Q-0089 bar).

STRICTLY DOCS-ONLY. Never modify disbot/ runtime code, migrations, or tests here (the Q-0107
rule). Runtime bugs you notice are CAPTURED to the bug-book, not fixed here (step 3).

SYNC FIRST: your clone may be stale (a stale current-state.md is the #1 cause of reconciling the
wrong state) — `git fetch origin && git reset --hard origin/main`, then branch claude/<slug>.

ORIENT (read the memory first): .claude/CLAUDE.md, docs/current-state.md, the newest .sessions/
log, the .session-journal.md Quick reference, and docs/owner/ai-project-workflow.md section 12.

STEP 1 — GO-SIGNAL: the triggering `reconcile` issue IS your go-signal — do the pass. (Do not
  re-gate on check_reconciliation_due: the issue means reconciliation is wanted, whether the
  cadence fired or an agent spotted drift.) Note its number.

STEP 1b — CHECK CODEX FIRST (first priority, before the reconcile pass — Q-0174). Scan the few
  most-recent merged PRs (and any open ones) for UNRESOLVED Codex/bot review comments. Codex cannot
  push a branch or open a PR — it leaves a COMMENT (a summary + a proposed diff + a `[View task →]`
  link, describing changes in its own sandbox copy). READ ITS COMMENT, do NOT hunt for a Codex
  branch/PR (there is none). For each flag, apply the "real bug" bar — ACTIONABLE only if ALL hold:
    (a) VERIFIED against current `main` source — real *now*, not an artifact. Reject the born-red
        timing class (Codex reviews the card-first commit *before* the code lands → "implementation
        missing / flip the card / script doesn't exist"), an `is_outdated` thread, a since-fixed line.
    (b) A genuine defect: a correctness bug · an architecture/ownership violation · a docs-vs-code
        contradiction or stale-fact drift that would mislead an agent (the kind this routine owns —
        e.g. the `/session-close` cadence Codex caught) · a security/safety/privacy gap.
    (c) NOT a nitpick / preference / false positive / anything the repo's checkers already pass.
  ROUTE BY SHAPE (you are docs-only, Q-0107): a verified-real DOCS defect → fix it now in this pass
  (it jumps the queue). A verified-real RUNTIME bug → do NOT fix it here; append it OPEN to
  docs/health/bug-book.md (step 3) for the dispatch routine, citing the PR/file/line + which bar
  clause it meets. A born-red false-positive is acknowledged-and-skipped, not "fixed." Bounded read
  (the recent PRs, not the whole history). Unsure → skip it (the Q-0174 Hermes pr-check skill opens
  an issue for genuinely-unclear ones); never act blindly — the bot is one input, verified against
  shipped source (Q-0120). The full bar lives in
  docs/planning/codex-review-integration-plan-2026-06-17.md.

STEP 2 — RECONCILE (the Q-0107 pass):
  - Ledger: run `python3.10 scripts/check_current_state_ledger.py --strict`; fix all drift (add
    missing merged-PR entries; trim Recently-shipped past the ratchet into the archive).
    - To split the band's PRs into **merged / closed-unmerged / open** deterministically (instead
      of the per-PR hand check this step used to do — the #1133-class merged-vs-closed call,
      Q-0120/Q-0181), run `python3.10 scripts/band_pr_status.py` and paste its table into the pass
      record's §1. It uses git for merged-on-main + the same gh→REST fallback as
      `check_loop_health.py` for the closed/open half (SKIP-degrades, labels its source). Both
      disposable (Q-0105).
    - To draft the **grouped Recently-shipped entries** (the authoring half — the drift-prone,
      hand-rolled core of the pass), run `python3.10 scripts/band_pr_status.py --since <marker>
      --themes`: it buckets the band's merged PRs by touched area into an editable skeleton and
      works **offline via git** (no `gh` needed — proven on the band-#1620 pass, where `gh` was
      unavailable). Edit its buckets into thematic prose; the touched-dir buckets cross-cut real
      themes, so still read the PR subjects to regroup.
    - To do the Recently-shipped trim itself, run `python3.10 scripts/trim_recently_shipped.py`
      (dry-run diff) → review the moved bullets (the grouped band bullets are **non-monotonic** —
      the known hazard) → `--apply`. It moves the oldest over-ratchet bullets into the archive and
      **recomputes the "Older merges (#HIGH … #LOW)" floor pointer** from the true archive span, so
      the prose pointer can't drift. Re-run `check_current_state_ledger.py --strict` afterward as
      the real guard (the actuator never deletes a bullet).
  - ARCHIVE OLD ROUTER Q-BLOCKS (Q-0210): when `docs/owner/maintainer-question-router.md` grows
    unwieldy (it exceeds the file-read limit at ~490 KB), move the **oldest fully answered + routed**
    Q-blocks into `docs/owner/maintainer-question-router-archive.md` (newest kept in the live router,
    oldest archived), leaving a pointer in the live file — exactly like the `current-state.md` →
    `current-state-archive.md` trim above. References are plain `Q-0XXX` text, so an archived block
    stays grep-resolvable; only the lone `#q-0017` *anchor* link needs a fix if Q-0017 is archived.
    **Never renumber, never re-home a decision's canonical record out to a scattered doc** — only
    physically relocate the block to the archive file. Skip in a pass where the router is comfortably
    sized.
  - Docs: run `python3.10 scripts/check_docs.py --strict`; fix every reachability/badge/
    staleness issue + stale links, wrong PR numbers, broken references.
  - Prune/relabel clearly stale docs; restate current priorities in current-state ▶ Next action.
  - DISPOSITION OPEN PRs (Q-0125): `list_pull_requests` (state=open) + each one's CI/mergeable
    state. Close the redundant/stale (e.g. a superseded ledger PR), fix or flag a red-CI one
    (a `check_docs` reachability orphan is usually one missing README link), leave the owner's.
    "Noting" a PR is not disposition — act on it. (This sweep was missing: #766 sat red + #771
    redundant for ~21h, unnoticed by sessions and two prior passes.) **Open `dependabot/*` PRs
    are merge candidates, not "the owner's" (Q-0256):** review-on-sight (diff + changelog +
    usage grep) and merge on green CI; majors = fix-then-merge if contained, else write the
    dedicated-session work item. Rule: `repo-settings-state.md` § Dependabot PR policy. (This
    was the gap: the 2026-07-08 pass left 6 green dependabot PRs untouched for ~3 days.)
  - GC STALE CLAIM FILES (Q-0195): run `python3.10 scripts/check_stale_claims.py` over
    `docs/owner/claims/` and `--prune` any whose branch is gone/merged (a session that forgot to
    delete its own claim file at close). This is the failsafe that keeps the per-claim ledger from
    accumulating — sessions delete their own claim at close, the pass sweeps the orphans. Commit the
    deletions with the pass. (Never collapse the claim files back into one shared file — that
    re-imports the ~98% merge-conflict rate the split removed; `tools/sim/claim_layout_sim.py`.)
  - CONTROL-PLANE (Q-0135): run `python3.10 scripts/check_loop_health.py` (reads live GitHub) and
    reconcile the § Control-plane state table against its PASS/FAIL/SKIP verdicts — tick/untick the
    verifiable rows (ROUTINE_PAT, DATABASE_PUBLIC_URL, loop-self-fired) so the table can't silently
    drift the way it did before 2026-06-14 (it claimed the loop had never self-fired when live
    GitHub already proved it had). The script tries `gh` first, then **auto-falls to a stdlib REST
    read when `gh` is absent and `GITHUB_TOKEN` is set** (PR #1174 — so it now produces a real
    verdict `(via REST)` in the routine container, not a blind SKIP; the output labels the source).
    Only if neither `gh` nor a token is available does it emit an *actionable* SKIP — then do the
    same read via the GitHub MCP (`list_issues`): the *author* of the newest auto-opened trigger
    issue is the live read of ROUTINE_PAT (a real-user login = set; `github-actions[bot]` = unset).
  - PLAN THE NEXT *FULL BAND* + KEEP THE PLANS FED (owner directives Q-0144 + Q-0164). Review the
    executable plans (docs/planning/*, docs/roadmap.md): how much real, *buildable* work is left?
    The bar is DEPTH >= the cadence — leave enough genuine buildable work to reach the NEXT pass
    (~30 PRs of capacity), as larger multi-PR initiatives OR more slices, whichever keeps each a
    real change. The old "~9 PRs" horizon drained the queue ~20 PRs before each refill (Q-0164).
      · Enough work remains -> plan the next band into the band planning doc, highest-value first,
        modular, each a meaningful slice. Do NOT pad to 30 with filler.
      · NOT enough buildable work remains -> FIRST this is the idea->plan step: review docs/ideas/
        (dedup-grep first) and promote the best owner-aligned ideas into FULLY COMPLETE, executable
        plans in docs/planning/ — scoped against the repo's house style (existing subsystems /
        folios / game cogs) so an executor can build them cold. Index each in docs/ideas/README.md +
        the roadmap so it becomes a ▶ Next action.
      · STILL can't fill the band after promoting what you honestly can -> that is the SIGNAL, not a
        failure (Q-0164): set a loud `⚠️ PLAN BACKLOG THIN` line in current-state.md ▶ Next action
        AND the run-report ⚑ Owner-decisions line, so the owner drops ideas or schedules a dedicated
        planning session — never invent low-value filler to look busy. This is how an idea becomes a
        plan becomes reality with no extra owner planning, and how the owner learns *early* that the
        backlog needs him.
      · After (re)planning, run `python3.10 scripts/check_plan_homing.py --strict` (PR #1174) — every
        live `plan` doc must be linked from a ROUTING doc (roadmap / a folio / current-state / the
        `docs/planning/README.md` plan index), not merely reachable from a sibling plan. A newly
        promoted plan that isn't homed trips it; fix by adding its plan-index row + a roadmap/folio
        link. (Routing complement to `check_docs` reachability; warn-only without `--strict`.)
  - IMPROVE THE SYSTEM: if you see a way to make the orientation / memory / tooling better for
    the next run (a confusing doc, a missing pointer, a guard that would have caught this drift),
    make that improvement too. This is the point of the loop.
  - REGENERATE THE DASHBOARD EXPORT (cheap, on-cadence freshness): you already touch the source
    docs this pass, so run `python3.10 scripts/export_dashboard_data.py` to refresh the committed
    `dashboard/data/dashboard.json` (a generated artifact that silently drifts as parallel sessions
    add cogs/settings/env-vars — it was ~3 structural surfaces stale on `main` before this was wired,
    PR #1025). Run `python3.10 scripts/check_dashboard_data.py --drift` to see what changed first; it
    is warn-only and never blocks. Commit the regenerated JSON with the pass. This is the
    *cadence half* of the freshness loop — the dispatch routine carries the warn-only `--drift`
    reporter, this routine keeps the artifact fresh without burdening every session.
  - FLEET STATE lives in the fleet-manager generated roster, not here: canonical =
    `fleet-manager docs/roster.md`, regenerated ≤~2h at every manager wake from
    the live trigger registry + lane heartbeats. `docs/eap/fleet-manifest.md` is a pointer
    stub and `check_manifest_freshness.py` (scripts/) was retired with it per its Q-0105
    kill-switch header (superbot PR #1974; phase-2 decision in fm PR #59 +
    `fleet-manager docs/findings/manifest-parallel-run-2026-07-11.md`). Do not re-stamp the manifest or
    resurrect the checker; if the roster's generated-at is >24h stale, trust the lane
    repos' `control/status.md` heartbeats directly (the roster's own kill-switch rule).
  - Reset the "Last reconciliation pass: PR #N" marker in current-state.md to the latest PR
    (the trigger Action keys off it — do not skip). #N is the **latest merged PR** (the reset
    target), NOT the pass's own PR number; keep the leading #N, the `band-#M` label
    (M = (N // 30) * 30), and the "reset to the latest merged PR #N" parenthetical all the same
    number. `python3.10 scripts/check_reconcile_marker.py` verifies this consistency (warn-only;
    `--strict` to gate).

STEP 3 — RUNTIME BUGS YOU NOTICED: do NOT fix them here. Append each to docs/health/bug-book.md
  as a new OPEN entry for the dispatch routine to fix. Stay docs-only.

STEP 4 — CLOSE THE LOOP (memory write-back, always):
  - Contribute ONE genuine new idea (Q-0089) to docs/ideas/ with a one-line why — for the bot OR
    the workflow. Skip only if you truly have none worth having; never force filler.
  - Add one honest line reviewing the PREVIOUS reconciliation/session (Q-0102): what it did well
    or missed.
  - Write a short .sessions/<date>-reconcile.md log (what changed · what's next · the Q-0089
    idea · the Q-0102 review), ending with the **📤 Run report footer** (`.sessions/README.md`) —
    the ⚑ Owner-decisions / ⚑ Owner-manual-steps lines are required (`none` when empty), and the
    **Run type:** line set to `routine · reconciliation` (Q-0165 — the dashboard updates feed
    badges routine vs. manual work off this line).

STEP 5 — SHIP: open a docs-only claude/ PR; ensure check_docs, check_current_state_ledger, and
  check_session_log all pass; SELF-MERGE on green CI: re-sync origin/main first, UNION-resolve
  conflicts (you are the reconciler), require CI green on the final head, merge-commit. Then
  CLOSE the triggering `reconcile` issue (reference the merged PR).

Respect the bounded-session protocol. Never touch production, Railway, or the database.
```

---

## Routine: superbot night executor — MERGED into dispatch (Q-0145, 2026-06-15)

The night-executor and the dispatch routine always did the **same job** — advance the plan — so
they are now **one routine**: the **dispatch routine**, whose full prompt is in
[`hermes-dispatch-bridge.md`](./hermes-dispatch-bridge.md) § "The routine's saved prompt". Dispatch
is simply the more steerable one (it takes a work order); the fixed-prompt night agent added nothing
it couldn't do. So there are now **2 routine prompts total**: **dispatch** (all execution work) +
**docs reconciliation**.

**Trigger note (Q-0146).** Dispatch's cadence is the Claude Code console **Schedule** trigger —
every **2 hours**, cron **`0 */2 * * *`** (UTC), owner-enabled 2026-06-15. A scheduled fire has no
work order, so the routine advances the next plan slice from `current-state.md` ▶ Next action. The
API (`/fire`) trigger stays for on-demand work-order fires. This replaced the earlier plan to drive
the cadence from **Hermes' VPS cron** / the GitHub `schedule:` cron — both proved unreliable (the
GitHub `schedule:` trigger delivered only ~1 run/night, hours late; see the timing caveat under
Control-plane state). The legacy `executor-nightly.yml` workflow (it opened `continue`
issues for the now-retired night-executor) was **removed 2026-06-15**. A `continue`-labelled
issue is still a valid human-filed handoff signal a dispatch run reads on its next fire.

---

## The two issue labels (the routine signals)

| Label | Opened by | Fires | Effect |
|---|---|---|---|
| `reconcile` | the cadence Action (every 30-PR band) **or** any agent/maintainer who spots docs drift | docs reconciliation routine | the Q-0107 docs-only pass; routine closes the issue |
| `continue` | a maintainer filing a handoff (the dispatch routine itself no longer opens them — it hands off via ▶ Next action) | dispatch (fired by the console Schedule) reads it on its next fire | resume the explicit handoff; chain again if still unfinished |

This is the self-driving loop in two signals: reconcile keeps the docs honest, and continue
chains big work across bounded runs. (The `needs-hermes-review` PR-review gate was retired
2026-06-22, Q-0197 — every PR now auto-merges on green CI; `do-not-automerge` is the only
remaining by-hand merge hold.)

## The `reconcile` issue — how to fire the docs pass by hand

The docs-reconciliation routine triggers on a GitHub **issue labeled `reconcile`**. Beyond the
automatic Action (every 30-PR band), **any agent or the maintainer should open one whenever the
docs visibly need reordering** — the ledger drifted, a plan is stale, links rot, priorities
moved — without waiting for the cadence:

```bash
gh issue create --repo menno420/superbot --label reconcile \
  --title "Docs reconciliation: <one-line reason>" \
  --body "What looks stale / needs reordering, and why now."
```

The routine treats the issue as the go-signal, runs the docs-only pass, and closes the issue.
(If the `reconcile` label doesn't exist yet, the Action creates it on first use; or
`gh label create reconcile --color FBCA04`.)

## Operating the fleet

- **Pause/kill:** toggle a routine off (or delete it) in the console. The dispatch routine's API
  trigger also lets Hermes fire it; revoke that token to cut the on-demand path. To stop the
  automatic cadence, disable `.github/workflows/reconciliation-trigger.yml`.
- **Watch runs:** each fire is a session in your list; a green run-status means it *started and
  exited cleanly*, not that the task succeeded — open the run to confirm.
- **Cost:** routines draw subscription usage + a daily run cap. The reconciliation issue-trigger
  (cadence gated in the Action) + the every-2h dispatch Schedule keep volume bounded; the cap is also a runaway stop.
- **Improve the prompts here, not only in the console** — edit this doc, then re-paste into the
  routine. This keeps the fleet's behavior reviewable in git.

## PR mergeability keepers (auto-update + conflict-guard) — Q-0154

Two small workflows keep open PRs from rotting silently — the gap the #959 stall exposed: a
`behind`/conflicted PR sits **green-but-unmergeable** (a merge conflict is a git property, not a
test result, so GitHub never reddens a check for it, and native auto-merge won't auto-update a
behind branch without a merge queue). They split the two cases:

| Workflow | Trigger | Does | Net effect |
|---|---|---|---|
| **`pr-auto-update.yml`** | `push: main` | brings open non-draft `claude/*` PRs that are **BEHIND** up to date (`update-branch`); the `do-not-automerge` carve-out is left alone; a real conflict fails the update and falls through to the guard | **behind = handled silently** → re-tests against current main → auto-merge fires |
| **`pr-conflict-guard.yml`** | `push: main` + schedule (sweep all PRs) · `pull_request` (that PR only) | posts a **red `conflict-guard` commit status** on any **DIRTY** PR, clears it on resolution (skips `UNKNOWN` to avoid flap). A PR's own push checks only itself; the all-PR sweep runs on `push: main`/schedule (when a PR can newly conflict) — keeps the noise off every PR | **conflict = loud red** → an agent / the maintainer sees it and resolves it |

`push: main` is the load-bearing trigger for both: a conflict/behind state arises when *main moves*
(another PR merges), which is not an event on the stale PR. `conflict-guard` is a **non-required**
status (a signal, not an extra gate — a DIRTY PR already can't merge), so no branch-protection
change is needed. **Token split (learned by dogfooding):** `auto-update` uses `ROUTINE_PAT` (it needs
Pull requests + Contents write for `update-branch`, and PAT attribution keeps the cadence firing);
`conflict-guard` uses the default **`GITHUB_TOKEN`** because posting a commit status needs
`statuses: write`, which `ROUTINE_PAT` is not scoped for (that 403 failed the guard's first run).
Kill switch (Q-0105): delete either workflow; both are disposable convenience guards, and "Update
branch" / the conflict banner remain available by hand.

## Control-plane state (maintainer-verified) — the bits no in-repo checker can see

> **Why this exists:** the autonomous loop spans the repo **and** a Railway/console/VPS control
> plane. `check_*` scripts only see the repo half, so maintainer-side config (secrets, routine
> models, deploys) is invisible to every in-repo audit — it kept getting lost in PR-body prose
> ("⚠️ Required maintainer action"). **This table + the newest control-plane `.sessions/` log are
> the source of truth for "is the loop actually wired?"** (the #765/#769 Q-0102 notes asked for
> exactly this ledger). Tick a box when verified live; add new maintainer actions here as they arise.

| # | Maintainer action | Why it matters | Source PR | Verified? |
|---|---|---|---|---|
| 1 | Add repo secret **`ROUTINE_PAT`** (fine-grained PAT, this repo, **Issues: read/write**) | **Hard blocker for the whole loop** — without it, cron/cadence trigger issues are authored by `github-actions[bot]`, which **does not start a Claude routine** (A/B-verified: real-user issue #776 fired in <1 min; bot's #768 never did) | #778 | ✅ **2026-06-14** (live-evidence verify: the scheduled executor issue #819 and the cadence reconcile issues #822/#841 were auto-opened by the workflows yet authored by **`menno420`** — the PAT owner — not `github-actions[bot]`. With `GITHUB_TOKEN` they would be bot-authored. So `ROUTINE_PAT` is set and active. **Re-confirmed every reconciliation pass since:** the cadence reconcile issues #931 (band-#990 era), #961, #1021 (band-#1020 pass, 2026-06-17), #1051 (band-#1050 pass, 2026-06-18), #1095 (band-#1080 pass, 2026-06-19), #1111 (band-#1110 pass, 2026-06-19), #1141 (band-#1140 pass, 2026-06-19), #1171 (band-#1170 pass, 2026-06-20), #1202 (band-#1200 pass, 2026-06-20), #1232 (band-#1230 pass, 2026-06-21), and **#1264 (band-#1260 pass, 2026-06-21)** were each auto-opened yet authored by `menno420`.) |
| 2 | Add repo secret **`DATABASE_PUBLIC_URL`** (Railway Postgres public proxy URL) | the daily `backup-db.yml` `pg_dump` is inert without it (workflow fails + opens an issue) | #769 | ✅ **2026-06-14 — set + working.** After the PR #862 pg18-client + resolved-URL fix, the backup **succeeded at 17:41:49Z** (run history: `success` workflow_dispatch). The earlier daily "Postgres backup failed" issues (#823/#860/#861) predated the fix and were stale (failure-issues don't auto-close on success); **closed 2026-06-14.** The next *scheduled* run confirms the cron path end-to-end. |
| 3 | Railway → **Deploy** the staged `CLAUDE_ROUTINE_*` env vars | `/bugreport` + `/dispatch` (HermesCog #757) may be inactive until the worker redeploys with the vars live | #765 | ⬜ (not verifiable from the repo) |
| 4 | Confirm the **dispatch routine prompt** is the free-form version | the owner finished routine setup *before* the #761 free-form prompt was handed over — it may carry the older prompt | #761/#765 | ⬜ (not verifiable from the repo) |
| 5 | Confirm **routine models**: dispatch/executor = **Opus 4.8**, reconciliation = Sonnet/Opus (not **Fable 5**) | dispatch was last seen on Fable 5 (premium) → daily spend risk vs. the €30/mo Q-0082 cap | §11 / #765 | ⬜ (not verifiable from the repo) |
| 6 | After #1: **`workflow_dispatch` `executor-nightly.yml`** once | the **first real unattended executor run** (the Q-0105 "watch the first run" moment) | #778 | ✅ **2026-06-14** — the loop **has now self-fired unattended**: scheduled executor issue #819 (auto-opened) ran on its own, opened the `continue` handoff #821, and that chain produced merged P0-4 work (#825). No manual `workflow_dispatch` was needed. |

> Rows 1, 2, and 6 are now verified live — the autonomous loop self-fires and the DB backup succeeds
> (row 2 fixed 2026-06-14: the 17:41Z run is green; the daily failure-issues were stale and are closed).
> Rows 3–5 remain maintainer-side (not verifiable from the repo). The first autonomous
> **reconciliation** has also fired (the band-#820/#840 cadence passes ran via #822/#841).
>
> **⏱️ Timing caveat — GitHub Actions cron lag (not a config bug).** GitHub's `schedule:` trigger is
> best-effort and, on a low-activity repo, runs are frequently **hours late or occasionally dropped**.
> Observed here: the executor cron (`17 1,3 * * *` = 01:17/03:17 UTC) fired at **01:20 UTC on
> 2026-06-13** (on time) but at **06:04 UTC on 2026-06-14** (~4¾ h late); the `backup-db.yml` cron
> (`0 2 * * *` = 02:00 UTC) opened its failure issue at **06:15 UTC (06-13)** and **06:39 UTC
> (06-14)** — both ~4 h late. The `:17`-minute offset reduces top-of-hour congestion but does **not**
> eliminate the multi-hour variance. The timezone is correct (crons are always UTC, documented in
> `executor-nightly.yml`); the lag is GitHub's scheduler. **Resolved 2026-06-15 (Q-0146):** the
> dispatch cadence moved off GitHub cron entirely onto the Claude Code console **Schedule** trigger
> (`0 */2 * * *`, every 2h), which fires reliably — this caveat now applies only to the remaining
> GitHub-`schedule:` workflows (e.g. `backup-db.yml`); `executor-nightly.yml` was removed 2026-06-15.

## See also

- [`hermes-dispatch-bridge.md`](./hermes-dispatch-bridge.md) — the `/fire` mechanism + gates.
- [`hermes-skills/dispatch.md`](./hermes-skills/dispatch.md) · [`hermes-skills/review.md`](./hermes-skills/review.md)
- `scripts/check_reconciliation_due.py` · `scripts/check_phase_gate.py` · `scripts/check_current_state_ledger.py`
- `scripts/check_loop_health.py` — live-GitHub probe of the Control-plane state table (Q-0135; `gh` → stdlib-REST fallback, PR #1174); run it in the reconciliation pass.
- `scripts/check_plan_homing.py` — asserts every live `plan` doc is linked from a routing doc (PR #1174); run `--strict` in the reconciliation pass after (re)planning.
- `.github/workflows/reconciliation-trigger.yml` — opens the `reconcile` issue on the 30-PR boundary.
  *(The dispatch cadence is the console Schedule, `0 */2 * * *`, Q-0146 — `executor-nightly.yml` was removed 2026-06-15.)*
- `docs/owner/ai-project-workflow.md` §10 (staging/continuation) · §12 (the loop).

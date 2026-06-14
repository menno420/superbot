# SuperBot autonomous routines (the routine fleet)

> **Status:** `living-ledger` — the durable, version-controlled home for the Claude Code
> **Routine** prompts SuperBot runs autonomously. Routines are created/managed in the console
> ([claude.ai/code/routines](https://claude.ai/code/routines)); these are the **source of
> truth for their prompts** so they are reviewable and improvable in git rather than
> pasted-and-lost. When you change a prompt here, paste it into the routine's config too.

Companion to [`hermes-dispatch-bridge.md`](./hermes-dispatch-bridge.md) (the API/`/fire`
mechanism + the three gates Q-0113/Q-0114/phase) and `docs/owner/ai-project-workflow.md` §12
(the loop). Each routine inherits the **same safety model**: `claude/`-branch pushes only, no
production/Railway/DB access, the phase gate keeps agent-*originated features* out, and the
kill switch is toggling the routine off in the console.

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
| **superbot autonomous dispatch** | API (`/fire`) | General work orders from Hermes/phone (`superbot-dispatch`). Classifies by `CLASS:`. | per work order (Q-0113/Q-0114) |
| **superbot docs reconciliation** | **Issue** labeled `reconcile` | The Q-0107 every-30th-PR docs-only pass: reconcile the ledger, de-stale docs, plan the next band, contribute one idea. | `docs` → self-merge on green |
| **superbot night executor** | Issue `continue` (cron-driven 01:17/03:17 UTC + handoffs) | Advance the **next big step of the plan** (a "continue from last session" run); self-chain via `continue` issues when a step spans runs; fall back to a quality win. Phase-gated against features. | small → self-merge; **big step → Hermes reviews + merges** (Q-0117) |

**Why an issue-trigger (not a schedule, not a per-PR trigger) for reconciliation:** the docs
pass should run **promptly when due — daytime included** — so the docs + fresh plan are ready
for the nightly executor, not deferred to a night-time poll (owner point, 2026-06-12). A
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

**The docs/runtime split (honors Q-0107):** the reconciliation routine is **docs-only** — if
it *spots* a runtime bug it appends it to `docs/health/bug-book.md` (OPEN), and the **caretaker**
routine fixes it. Neither routine invents features (the phase gate holds those until
invent-phase, and these prompts never originate them).

**Stage-1 note (workflow §10):** these two are *unattended, self-merging* routines (the docs
one issue-triggered, the caretaker nightly) — real Stage-1 autonomy, earned by the Stage-0
calibration runs on 2026-06-12 (connectivity · held-for-review PR #747 · self-merge PR #751).
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

ORIENT (read the memory first): .claude/CLAUDE.md, docs/current-state.md, the newest .sessions/
log, the .session-journal.md Quick reference, and docs/owner/ai-project-workflow.md section 12.

STEP 1 — GO-SIGNAL: the triggering `reconcile` issue IS your go-signal — do the pass. (Do not
  re-gate on check_reconciliation_due: the issue means reconciliation is wanted, whether the
  cadence fired or an agent spotted drift.) Note its number.

STEP 2 — RECONCILE (the Q-0107 pass):
  - Ledger: run `python3.10 scripts/check_current_state_ledger.py --strict`; fix all drift (add
    missing merged-PR entries; trim Recently-shipped past the ratchet into the archive).
  - Docs: run `python3.10 scripts/check_docs.py --strict`; fix every reachability/badge/
    staleness issue + stale links, wrong PR numbers, broken references.
  - Prune/relabel clearly stale docs; restate current priorities in current-state ▶ Next action.
  - DISPOSITION OPEN PRs (Q-0125): `list_pull_requests` (state=open) + each one's CI/mergeable
    state. Close the redundant/stale (e.g. a superseded ledger PR), fix or flag a red-CI one
    (a `check_docs` reachability orphan is usually one missing README link), leave the owner's.
    "Noting" a PR is not disposition — act on it. (This sweep was missing: #766 sat red + #771
    redundant for ~21h, unnoticed by sessions and two prior passes.)
  - CONTROL-PLANE (Q-0135): run `python3.10 scripts/check_loop_health.py` (reads live GitHub via
    `gh`) and reconcile the § Control-plane state table against its PASS/FAIL/SKIP verdicts —
    tick/untick the verifiable rows (ROUTINE_PAT, DATABASE_PUBLIC_URL, loop-self-fired) so the
    table can't silently drift the way it did before 2026-06-14 (it claimed the loop had never
    self-fired when live GitHub already proved it had). If `gh` is unavailable, do the same read
    via the GitHub MCP (`list_issues`): the *author* of the newest auto-opened trigger issue is
    the live read of ROUTINE_PAT (a real-user login = set; `github-actions[bot]` = unset).
  - Plan the next band of PRs (the upcoming ~30) — modular, each a meaningful slice — into the
    band planning doc, ordered so the highest-value improvements come first.
  - IMPROVE THE SYSTEM: if you see a way to make the orientation / memory / tooling better for
    the next run (a confusing doc, a missing pointer, a guard that would have caught this drift),
    make that improvement too. This is the point of the loop.
  - Reset the "Last reconciliation pass: PR #N" marker in current-state.md to the latest PR
    (the trigger Action keys off it — do not skip).

STEP 3 — RUNTIME BUGS YOU NOTICED: do NOT fix them here. Append each to docs/health/bug-book.md
  as a new OPEN entry for the caretaker routine. Stay docs-only.

STEP 4 — CLOSE THE LOOP (memory write-back, always):
  - Contribute ONE genuine new idea (Q-0089) to docs/ideas/ with a one-line why — for the bot OR
    the workflow. Skip only if you truly have none worth having; never force filler.
  - Add one honest line reviewing the PREVIOUS reconciliation/session (Q-0102): what it did well
    or missed.
  - Write a short .sessions/<date>-reconcile.md log (what changed · what's next · the Q-0089
    idea · the Q-0102 review).

STEP 5 — SHIP: open a docs-only claude/ PR; ensure check_docs, check_current_state_ledger, and
  check_session_log all pass; SELF-MERGE on green CI: re-sync origin/main first, UNION-resolve
  conflicts (you are the reconciler), require CI green on the final head, merge-commit. Then
  CLOSE the triggering `reconcile` issue (reference the merged PR).

Respect the bounded-session protocol. Never touch production, Railway, or the database.
```

---

## Routine: superbot night executor (advances the plan)

The nightly **executor** — a productive "continue from where the last session left off" run.
Its primary job is to **advance the next big step of the plan** (not just small fixes), and to
**self-chain** across runs via `continue` issues when a step is bigger than one bounded run.

- **Triggers:** **GitHub → Issue opened, label `continue`** — and that's all it needs. The
  overnight cadence is driven by `.github/workflows/executor-nightly.yml` (a cron that opens a
  scheduled `continue` issue at 01:17 and 03:17 UTC — though GitHub's scheduler often runs it
  hours late; see the timing caveat under Control-plane state), because the console Schedule trigger was
  unreliable in the research-preview UI. The same `continue` trigger also picks up real
  continuation handoffs. (No API trigger / no token — on-demand work goes through dispatch.)
- **Repository:** `menno420/superbot`. **Model:** Opus 4.8 (the execution tier; §11).
  **Permissions:** unrestricted branch push **OFF**. **Behavior:** auto-fix PRs ON.
- **Merge gate (Q-0117):** small fixes/docs **self-merge on green** (Q-0113); a **substantial
  plan step** opens a PR labeled `needs-hermes-review` and does **not** self-merge — Hermes
  reviews it (`superbot-review-merge`) and merges it if sound. If Hermes review is unavailable,
  the step's green PR may self-merge as the documented fallback.
- **Paste this as the routine's instructions:**

```
You are the SuperBot NIGHT EXECUTOR — the routine that advances the plan, and one turn of
SuperBot's self-improvement loop. A productive run looks like a good "continue from where the
last session left off" session: it makes real progress on the actual plan. You run nightly,
when a `continue` issue hands you a continuation, and when Hermes fires you with a problem.

WHY YOU EXIST (.claude/CLAUDE.md): the real artifact is the *workflow*. Every run advances the
plan AND leaves the next run better-equipped — trigger a genuine positive improvement wherever
one honestly exists; never fabricate churn (Q-0089 bar). Bugs/root-cause fixes jump the queue.

ORIENT (read the memory first): .claude/CLAUDE.md, docs/current-state.md (▶ Next action), the
decade-queue planning doc, docs/health/bug-book.md, the newest .sessions/ log, the
.session-journal.md Quick reference, docs/owner/ai-project-workflow.md §10 (continuation) + §12.

STEP 0 — PHASE GATE: run `python3.10 scripts/check_phase_gate.py --phase`. Bug fixes / UX /
  correctness / docs / tooling / planned-step execution ONLY — NEVER originate a new feature
  (capture feature ideas to docs/ideas/).

STEP 1 — CHOOSE WHAT TO ADVANCE (first solid one):
  A. CONTINUATION — if a `continue` issue triggered you (or one is open), follow its explicit
     handoff instructions exactly. Resume where it says. That is your task.
  B. A problem Hermes handed you in the text payload.
  C. THE NEXT BIG STEP OF THE PLAN — take the next substantial, owner-vetted step from
     current-state ▶ Next action / the decade-queue doc. This is your primary job; prefer real
     plan progress over busywork.
  D. An open bug (bug-book) or a CI/arch regression.
  E. A quality win a maintainer would thank you for (missing test coverage, a confusing
     docstring, a mislayered helper per helper-policy, an arch warning to retire, a UX polish),
     or an orientation/memory/tooling improvement.
  ALWAYS leave a positive result; never ship churn. If nothing in A–E is solidly shippable,
  capture the best idea to docs/ideas/ + sharpen ▶ Next action and stop (last resort).

STEP 2 — EXECUTE (CLASS: fix / the step): root-cause, minimal-for-scope, WITH tests where it is
  code. Stay within docs/architecture.md boundaries (services must not import views; no raw SQL
  outside utils/db/; mutations through *_mutation.py + an audit event). Run the full CI mirror.

STEP 3 — BOUNDED CONTINUATION (the §10 self-driving handoff). A big step may not fit in one run.
  Hand off ONLY on a CONCRETE signal — you finished a coherent, SHIPPABLE sub-step and the
  REMAINING work is clearly scoped (a natural task boundary). Do NOT guess about context limits;
  do NOT hand off mid-sub-step. When you hand off:
    - ship the completed sub-step (STEP 5), then
    - open a `continue` issue with EXPLICIT instructions: what is DONE, what REMAINS, exactly
      where you stopped, the next concrete steps, and the files/tests involved. Label it
      `continue`. That issue triggers the next run, which resumes from your instructions.

STEP 4 — CLOSE THE LOOP (memory write-back, always): ONE genuine idea (Q-0089); one honest line
  reviewing the PREVIOUS run (Q-0102) in the PR description; a brief .sessions/<date>-executor.md
  log if you shipped; mark fixed bug-book entries FIXED; ALWAYS leave current-state ▶ Next
  action sharpened so the next run continues cleanly.

STEP 5 — SHIP (merge gate, Q-0117):
  - SMALL fix / docs / a self-contained low-risk change → SELF-MERGE on green CI (Q-0113):
    re-sync origin/main, require CI green on the final head, merge-commit.
  - SUBSTANTIAL plan step (real feature-sized work within the plan, a multi-file refactor, a
    migration, anything you would want a second pair of eyes on) → open the PR, ensure CI is
    green, and **label it `needs-hermes-review`**. Do NOT self-merge — Hermes reviews and merges
    it. In the PR body, summarise what to check and the one risk (for Hermes + the maintainer).
  - If you opened a `continue` issue this run, also close the issue that TRIGGERED this run.
  Never touch production, Railway, or the database directly.
```

---

## The three issue labels (the routine triggers)

| Label | Opened by | Fires | Effect |
|---|---|---|---|
| `reconcile` | the cadence Action (every 30-PR band) **or** any agent/maintainer who spots docs drift | docs reconciliation routine | the Q-0107 docs-only pass; routine closes the issue |
| `continue` | the **executor** when it hands off a partly-done plan step (or a maintainer) | the executor | resume the explicit handoff in the issue body; chain again if still unfinished |
| `needs-hermes-review` | the **executor** on a substantial plan-step PR | (a PR label, not an issue) — **Hermes** `superbot-review-merge` | Hermes reviews the diff and **merges if sound**, else requests changes (Q-0117) |

This is the self-driving loop in three signals: reconcile keeps the docs honest, continue
chains big work across bounded runs, and needs-hermes-review puts a *different model* between
Claude's big steps and `main`.

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

- **Pause/kill:** toggle a routine off (or delete it) in the console. The caretaker's API
  trigger also lets Hermes fire it; revoke that token to cut the on-demand path. To stop the
  automatic cadence, disable `.github/workflows/reconciliation-trigger.yml`.
- **Watch runs:** each fire is a session in your list; a green run-status means it *started and
  exited cleanly*, not that the task succeeded — open the run to confirm.
- **Cost:** routines draw subscription usage + a daily run cap. The issue-trigger (cadence
  gated in the Action) + nightly caretaker keep volume low. The cap is also a runaway stop.
- **Improve the prompts here, not only in the console** — edit this doc, then re-paste into the
  routine. This keeps the fleet's behavior reviewable in git.

## Control-plane state (maintainer-verified) — the bits no in-repo checker can see

> **Why this exists:** the autonomous loop spans the repo **and** a Railway/console/VPS control
> plane. `check_*` scripts only see the repo half, so maintainer-side config (secrets, routine
> models, deploys) is invisible to every in-repo audit — it kept getting lost in PR-body prose
> ("⚠️ Required maintainer action"). **This table + the newest control-plane `.sessions/` log are
> the source of truth for "is the loop actually wired?"** (the #765/#769 Q-0102 notes asked for
> exactly this ledger). Tick a box when verified live; add new maintainer actions here as they arise.

| # | Maintainer action | Why it matters | Source PR | Verified? |
|---|---|---|---|---|
| 1 | Add repo secret **`ROUTINE_PAT`** (fine-grained PAT, this repo, **Issues: read/write**) | **Hard blocker for the whole loop** — without it, cron/cadence trigger issues are authored by `github-actions[bot]`, which **does not start a Claude routine** (A/B-verified: real-user issue #776 fired in <1 min; bot's #768 never did) | #778 | ✅ **2026-06-14** (live-evidence verify: the scheduled executor issue #819 and the cadence reconcile issues #822/#841 were auto-opened by the workflows yet authored by **`menno420`** — the PAT owner — not `github-actions[bot]`. With `GITHUB_TOKEN` they would be bot-authored. So `ROUTINE_PAT` is set and active.) |
| 2 | Add repo secret **`DATABASE_PUBLIC_URL`** (Railway Postgres public proxy URL) | the daily `backup-db.yml` `pg_dump` is inert without it (workflow fails + opens an issue) | #769 | ⬜ **still unset** — `backup-db.yml` opens a "Postgres backup failed" issue every day (latest #823, 2026-06-14); the cron *fires* but the dump fails for lack of this secret. |
| 3 | Railway → **Deploy** the staged `CLAUDE_ROUTINE_*` env vars | `/bugreport` + `/dispatch` (HermesCog #757) may be inactive until the worker redeploys with the vars live | #765 | ⬜ (not verifiable from the repo) |
| 4 | Confirm the **dispatch routine prompt** is the free-form version | the owner finished routine setup *before* the #761 free-form prompt was handed over — it may carry the older prompt | #761/#765 | ⬜ (not verifiable from the repo) |
| 5 | Confirm **routine models**: dispatch/executor = **Opus 4.8**, reconciliation = Sonnet/Opus (not **Fable 5**) | dispatch was last seen on Fable 5 (premium) → daily spend risk vs. the €30/mo Q-0082 cap | §11 / #765 | ⬜ (not verifiable from the repo) |
| 6 | After #1: **`workflow_dispatch` `executor-nightly.yml`** once | the **first real unattended executor run** (the Q-0105 "watch the first run" moment) | #778 | ✅ **2026-06-14** — the loop **has now self-fired unattended**: scheduled executor issue #819 (auto-opened) ran on its own, opened the `continue` handoff #821, and that chain produced merged P0-4 work (#825). No manual `workflow_dispatch` was needed. |

> Rows 1 + 6 are now verified live — the autonomous loop self-fires. Rows 2–5 remain maintainer-side
> (row 2 is confirmed *still pending* by the daily backup-failure issues). The first autonomous
> **reconciliation** has also fired (the band-#820/#840 cadence passes ran via #822/#841).
>
> **⏱️ Timing caveat — GitHub Actions cron lag (not a config bug).** GitHub's `schedule:` trigger is
> best-effort and, on a low-activity repo, runs are frequently **hours late or occasionally dropped**.
> Observed here: the executor cron (`17 1,3 * * *` = 01:17/03:17 UTC) fired at **01:20 UTC on
> 2026-06-13** (on time) but at **06:04 UTC on 2026-06-14** (~4¾ h late); the `backup-db.yml` cron
> (`0 2 * * *` = 02:00 UTC) opened its failure issue at **06:15 UTC (06-13)** and **06:39 UTC
> (06-14)** — both ~4 h late. The `:17`-minute offset reduces top-of-hour congestion but does **not**
> eliminate the multi-hour variance. The timezone is correct (crons are always UTC, documented in
> `executor-nightly.yml`); the lag is GitHub's scheduler. If on-time firing ever matters, drive the
> cadence from an external scheduler that calls `workflow_dispatch` (or accept the loop is
> "sometime overnight", not "at 03:17").

## See also

- [`hermes-dispatch-bridge.md`](./hermes-dispatch-bridge.md) — the `/fire` mechanism + gates.
- [`hermes-skills/dispatch.md`](./hermes-skills/dispatch.md) · [`hermes-skills/review.md`](./hermes-skills/review.md)
- `scripts/check_reconciliation_due.py` · `scripts/check_phase_gate.py` · `scripts/check_current_state_ledger.py`
- `scripts/check_loop_health.py` — live-GitHub probe of the Control-plane state table (Q-0135); run it in the reconciliation pass.
- `.github/workflows/reconciliation-trigger.yml` — opens the `reconcile` issue on the 30-PR boundary.
- `.github/workflows/executor-nightly.yml` — cron that opens a scheduled `continue` issue at 01:17/03:17 UTC (best-effort — often hours late).
- [`hermes-skills/review-merge.md`](./hermes-skills/review-merge.md) — Hermes' independent review + merge gate for `needs-hermes-review` PRs (Q-0117).
- `docs/owner/ai-project-workflow.md` §10 (staging/continuation) · §12 (the loop).

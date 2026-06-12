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
| **superbot docs reconciliation** | **Issue** labeled `reconcile` | The Q-0107 every-20th-PR docs-only pass: reconcile the ledger, de-stale docs, plan the next ~9 PRs, contribute one idea. | `docs` → self-merge on green |
| **superbot night executor** | Schedule (nightly) + Issue `continue` + API | Advance the **next big step of the plan** (a "continue from last session" run); self-chain via `continue` issues when a step spans runs; fall back to a quality win. Phase-gated against features. | small → self-merge; **big step → Hermes reviews + merges** (Q-0116) |

**Why an issue-trigger (not a schedule, not a per-PR trigger) for reconciliation:** the docs
pass should run **promptly when due — daytime included** — so the docs + fresh plan are ready
for the nightly executor, not deferred to a night-time poll (owner point, 2026-06-12). A
per-PR `pull_request.closed` trigger would spin a full cloud session on *every* merge (mostly
to exit), burning the daily run cap. The clean middle: **the issue *is* the trigger**, opened
two ways —
1. **Automatically** by `.github/workflows/reconciliation-trigger.yml`: on every push to `main`
   it runs `scripts/check_reconciliation_due.py --strict` and, when merged PRs cross a
   **multiple-of-20** band (Q-0107, raised from 10 on 2026-06-12 — small PRs inflate the
   count), opens a deduped issue labeled `reconcile`.
2. **By judgment** — *any agent or the maintainer* opens a `reconcile`-labeled issue the moment
   they spot docs needing reordering, even off-cycle. The routine treats the issue's existence
   as the go-signal (it does not re-gate on the cadence), does the pass, and closes the issue.

So the cadence runs in the GitHub Action (cheap, deterministic), and the routine just listens
for the labeled issue.

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
  (The `reconcile` issue is opened by the Action above on the 20-PR boundary, or by hand when
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
  - Plan the next ~9 PRs (the upcoming band) — modular, each a meaningful slice — into the
    decade-queue planning doc, ordered so the highest-value improvements come first.
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

- **Triggers:** Schedule → Daily (suggested 03:00) · **GitHub → Issue opened, label `continue`**
  (picks up a continuation handoff promptly) · **API** (Hermes fires it with a detected problem).
- **Repository:** `menno420/superbot`. **Model:** Opus 4.8 (the execution tier; §11).
  **Permissions:** unrestricted branch push **OFF**. **Behavior:** auto-fix PRs ON.
- **Merge gate (Q-0116):** small fixes/docs **self-merge on green** (Q-0113); a **substantial
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

STEP 5 — SHIP (merge gate, Q-0116):
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
| `reconcile` | the cadence Action (every 20-PR band) **or** any agent/maintainer who spots docs drift | docs reconciliation routine | the Q-0107 docs-only pass; routine closes the issue |
| `continue` | the **executor** when it hands off a partly-done plan step (or a maintainer) | the executor | resume the explicit handoff in the issue body; chain again if still unfinished |
| `needs-hermes-review` | the **executor** on a substantial plan-step PR | (a PR label, not an issue) — **Hermes** `superbot-review-merge` | Hermes reviews the diff and **merges if sound**, else requests changes (Q-0116) |

This is the self-driving loop in three signals: reconcile keeps the docs honest, continue
chains big work across bounded runs, and needs-hermes-review puts a *different model* between
Claude's big steps and `main`.

## The `reconcile` issue — how to fire the docs pass by hand

The docs-reconciliation routine triggers on a GitHub **issue labeled `reconcile`**. Beyond the
automatic Action (every 20-PR band), **any agent or the maintainer should open one whenever the
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

## See also

- [`hermes-dispatch-bridge.md`](./hermes-dispatch-bridge.md) — the `/fire` mechanism + gates.
- [`hermes-skills/dispatch.md`](./hermes-skills/dispatch.md) · [`hermes-skills/review.md`](./hermes-skills/review.md)
- `scripts/check_reconciliation_due.py` · `scripts/check_phase_gate.py` · `scripts/check_current_state_ledger.py`
- `.github/workflows/reconciliation-trigger.yml` — the Action that opens the `reconcile` issue on the 20-PR boundary.
- [`hermes-skills/review-merge.md`](./hermes-skills/review-merge.md) — Hermes' independent review + merge gate for `needs-hermes-review` PRs (Q-0116).
- `docs/owner/ai-project-workflow.md` §10 (staging/continuation) · §12 (the loop).

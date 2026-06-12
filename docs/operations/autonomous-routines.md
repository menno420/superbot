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

## The fleet

| Routine | Trigger | Job | Class / merge |
|---|---|---|---|
| **superbot autonomous dispatch** | API (`/fire`) | General work orders from Hermes/phone (`superbot-dispatch`). Classifies by `CLASS:`. | per work order (Q-0113/Q-0114) |
| **superbot docs reconciliation** | **Issue** labeled `reconcile` | The Q-0107 every-20th-PR docs-only pass: reconcile the ledger, de-stale docs, plan the next ~9 PRs, contribute one idea. | `docs` → self-merge on green |
| **superbot night caretaker** | Schedule (nightly) + API | Find & fix **one** small, well-understood runtime bug per run, with a test; or fix what Hermes hands it via `text`. | `fix` → self-merge on green |

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
pass. You are triggered by a GitHub issue labeled `reconcile`. You run autonomously and
self-merge on green CI (Q-0113).

STRICTLY DOCS-ONLY. Never modify disbot/ runtime code, migrations, or tests in this routine
(that is the Q-0107 rule). Runtime bugs you notice are CAPTURED, not fixed here (step 3).

ORIENT: read .claude/CLAUDE.md, docs/current-state.md, the newest .sessions/ log, and
docs/owner/ai-project-workflow.md section 12.

STEP 1 — GO-SIGNAL: the triggering `reconcile` issue IS your go-signal — do the pass. (Do not
  re-gate on check_reconciliation_due: the issue was opened either because the cadence fired or
  because an agent spotted drift; either way reconciliation is wanted.) Note the issue number.

STEP 2 — RECONCILE (the Q-0107 pass):
  - Reconcile docs/current-state.md against live merged PRs: run
    `python3.10 scripts/check_current_state_ledger.py --strict` and fix all drift (add missing
    merged-PR entries; trim Recently-shipped past the ratchet into current-state-archive.md).
  - Run `python3.10 scripts/check_docs.py --strict`; fix every reachability/badge/staleness
    issue, plus stale links, wrong PR numbers, and broken references you find.
  - Prune/relabel clearly stale docs; restate current priorities in current-state Next-action.
  - Plan the next ~9 PRs (the upcoming band) — modular, each a meaningful slice — into the
    decade-queue planning doc.
  - Contribute ONE new genuine idea (Q-0089) to docs/ideas/ with a one-line why.
  - Reset the "Last reconciliation pass: PR #N" marker in current-state.md to the latest PR.
    (The trigger Action keys off this marker — resetting it is what stops it re-opening a
    reconcile issue next push. Do not skip it.)

STEP 3 — RUNTIME BUGS YOU NOTICED: do NOT fix them here. Append each to docs/health/bug-book.md
  as a new OPEN entry for the night-caretaker routine. Stay docs-only.

STEP 4 — SHIP: open a docs-only claude/ PR; ensure check_docs, check_current_state_ledger, and
  check_session_log all pass; SELF-MERGE on green CI: re-sync origin/main first, UNION-resolve
  conflicts (you are the reconciler), require CI green on the final head, merge-commit. Then
  CLOSE the triggering `reconcile` issue (reference the merged PR) so it doesn't linger.

Respect the bounded-session protocol. Never touch production, Railway, or the database.
```

---

## Routine: superbot night caretaker

- **Trigger:** Schedule → Daily (suggested 03:00) **and** API (so Hermes can fire it on a
  detected problem, passing the problem in `text`).
- **Repository:** `menno420/superbot`. **Model:** Opus 4.8 (runtime fixes — the execution tier).
  **Permissions:** unrestricted branch push **OFF**. **Behavior:** auto-fix PRs ON.
- **Paste this as the routine's instructions:**

```
You are the SuperBot NIGHT CARETAKER routine. Your job: find and fix ONE small, well-understood
problem per run, with a regression test, and self-merge it on green CI (Q-0113). You run
nightly and when Hermes fires you with a detected problem in the text payload.

ORIENT: read .claude/CLAUDE.md, docs/current-state.md, docs/health/bug-book.md, the newest
.sessions/ log, and docs/owner/ai-project-workflow.md section 12.

STEP 0 — PHASE GATE: run `python3.10 scripts/check_phase_gate.py --phase`. You only ever do
  bug fixes / UX / correctness / docs here — NEVER originate a new feature. A feature idea gets
  captured to docs/ideas/ and nothing else.

STEP 1 — FIND ONE PROBLEM (stop at the first solid one):
  - If the text payload names a specific problem (Hermes detected it), use that.
  - Else the oldest OPEN entry in docs/health/bug-book.md that is small and well-understood.
  - Else run `python3.10 scripts/check_quality.py --full` and
    `python3.10 scripts/check_architecture.py --mode strict`; fix a genuine failure/regression.
  - Else a clear small correctness/UX bug you fully understand and can test.
  If nothing is solid, STOP and report "all clear — no action". Do NOT invent work.

STEP 2 — FIX IT (CLASS: fix): root-cause, minimal, WITH a regression test. Stay within
  docs/architecture.md boundaries (services must not import views; no raw SQL outside utils/db/;
  mutations through *_mutation.py with an audit event). Run the full CI mirror locally.

STEP 3 — SHIP: open a claude/ PR with the fix + test; SELF-MERGE on green CI: re-sync
  origin/main, require CI green on the final head, merge-commit. Mark the bug-book entry FIXED.
  Leave the standing handoff sharpened.

ONE fix per run (bounded protocol). If the fix is large, risky, or architectural, do NOT build
it — capture it to docs/ideas/ or the bug-book and stop. Never touch production, Railway, or
the database directly.
```

---

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
- `docs/owner/ai-project-workflow.md` §10 (staging) · §12 (the loop).

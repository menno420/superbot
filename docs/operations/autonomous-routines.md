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
| **superbot docs reconciliation** | Schedule (nightly), self-gated | The Q-0107 every-10th-PR docs-only pass: reconcile the ledger, de-stale docs, plan the next ~9 PRs, contribute one idea. | `docs` → self-merge on green |
| **superbot night caretaker** | Schedule (nightly) + API | Find & fix **one** small, well-understood runtime bug per run, with a test; or fix what Hermes hands it via `text`. | `fix` → self-merge on green |

**Why nightly-schedule, not per-PR GitHub trigger, for reconciliation:** a GitHub
`pull_request.closed` trigger fires a full cloud session on *every* merge (most just to check
"not due" and exit), which burns the daily routine-run cap. A nightly run that consults
`scripts/check_reconciliation_due.py` does the same job for ~1 run/night and catches the
10th-PR boundary by morning. Switch to the GitHub trigger only if you want it instant and the
run cap allows.

**The docs/runtime split (honors Q-0107):** the reconciliation routine is **docs-only** — if
it *spots* a runtime bug it appends it to `docs/health/bug-book.md` (OPEN), and the **caretaker**
routine fixes it. Neither routine invents features (the phase gate holds those until
invent-phase, and these prompts never originate them).

**Stage-1 note (workflow §10):** these two are *scheduled, unattended, self-merging* routines —
real Stage-1 autonomy, earned by the Stage-0 calibration runs on 2026-06-12 (connectivity ·
held-for-review PR #747 · self-merge PR #751). Watch the first scheduled run of each (or fire
once via **Run now**) before trusting them overnight. Stagger their schedules so they don't race
on `main`.

---

## Routine: superbot docs reconciliation

- **Trigger:** Schedule → Daily (suggested 03:30 in your zone; staggered after the caretaker).
- **Repository:** `menno420/superbot`. **Model:** Sonnet or Opus (docs work — the volume tier
  is fine; §11). **Permissions:** unrestricted branch push **OFF**. **Behavior:** auto-fix PRs ON.
- **Paste this as the routine's instructions:**

```
You are the SuperBot DOCS RECONCILIATION routine — the Q-0107 every-10th-PR docs-only
review + planning pass. You run autonomously and self-merge on green CI (Q-0113).

STRICTLY DOCS-ONLY. Never modify disbot/ runtime code, migrations, or tests in this routine
(that is the Q-0107 rule). Runtime bugs you notice are CAPTURED, not fixed here (step 3).

ORIENT: read .claude/CLAUDE.md, docs/current-state.md, the newest .sessions/ log, and
docs/owner/ai-project-workflow.md section 12.

STEP 1 — GATE: run `python3.10 scripts/check_reconciliation_due.py`.
  - NOT due: stop now. Open no PR. End with "reconciliation not due — no action".
  - DUE: continue.

STEP 2 — RECONCILE (the Q-0107 pass):
  - Reconcile docs/current-state.md against live merged PRs: run
    `python3.10 scripts/check_current_state_ledger.py --strict` and fix all drift (add missing
    merged-PR entries; trim Recently-shipped past the ratchet into current-state-archive.md).
  - Run `python3.10 scripts/check_docs.py --strict`; fix every reachability/badge/staleness
    issue, plus stale links, wrong PR numbers, and broken references you find.
  - Prune/relabel clearly stale docs; restate current priorities in current-state Next-action.
  - Plan the next ~9 PRs (the upcoming decade) — modular, each a meaningful slice — into the
    decade-queue planning doc.
  - Contribute ONE new genuine idea (Q-0089) to docs/ideas/ with a one-line why.
  - Reset the "Last reconciliation pass: PR #N" marker in current-state.md to the latest PR.
    (This is what makes a re-fire exit at step 1 — do not skip it.)

STEP 3 — RUNTIME BUGS YOU NOTICED: do NOT fix them here. Append each to docs/health/bug-book.md
  as a new OPEN entry for the night-caretaker routine. Stay docs-only.

STEP 4 — SHIP: open a docs-only claude/ PR; ensure check_docs, check_current_state_ledger, and
  check_session_log all pass; SELF-MERGE on green CI: re-sync origin/main first, UNION-resolve
  conflicts (you are the reconciler), require CI green on the final head, merge-commit.

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

## Operating the fleet

- **Pause/kill:** toggle a routine off (or delete it) in the console. The caretaker's API
  trigger also lets Hermes fire it; revoke that token to cut the on-demand path.
- **Watch runs:** each fire is a session in your list; a green run-status means it *started and
  exited cleanly*, not that the task succeeded — open the run to confirm.
- **Cost:** routines draw subscription usage + a daily run cap. Nightly schedules + the
  reconciliation self-gate keep volume low. The cap is also a natural runaway stop.
- **Improve the prompts here, not only in the console** — edit this doc, then re-paste into the
  routine. This keeps the fleet's behavior reviewable in git.

## See also

- [`hermes-dispatch-bridge.md`](./hermes-dispatch-bridge.md) — the `/fire` mechanism + gates.
- [`hermes-skills/dispatch.md`](./hermes-skills/dispatch.md) · [`hermes-skills/review.md`](./hermes-skills/review.md)
- `scripts/check_reconciliation_due.py` · `scripts/check_phase_gate.py` · `scripts/check_current_state_ledger.py`
- `docs/owner/ai-project-workflow.md` §10 (staging) · §12 (the loop).

# Workflow reconciliation + close-out pass — 2026-06-13 (interim, by-judgment)

> **Status:** `historical` — an **interim, owner-requested** reconciliation + workflow-hardening pass
> **Superseded 2026-06-19 (was active):** Interim workflow pass, long superseded; the live queue is the newest band pass. Do not act on this — current map: [planning/README](README.md).
> (not the Q-0107 cadence pass; the **#780 marker is untouched**). The maintainer asked for a thorough
> reassessment — "find everything we didn't properly finish, catch forgotten steps, make the workflow
> more structured." The routine doc sanctions opening a pass off-cycle "whenever the docs visibly need
> reordering." Sections: §1 verified state · §2 close-out scorecard · §3 cross-agent verification ·
> §4 lessons · §5 what this pass did *not* touch · §6 owner checklist.

---

## 1. Verified state at this pass (live GitHub + git log)

- **Health:** zero orphaned ideas (28 idea files, all routed); stability baseline accepted (#535);
  safety/community band slots 4–6 COMPLETE (#772/#774/#775); strong CI/arch/docs/session-log enforcement.
- **Main moved during the planning of this pass: #775 → #778.** Checked live:
  - **#777** — P0-3 settings pointer-lane *foundation* (the carried hardening spine started);
    added `scripts/settings_lane_matrix.py`; opened **Q-0119** (governance role-pointer home, OPEN).
  - **#778** — root-caused why the autonomous loop **never self-fired**: cron/cadence trigger issues
    were authored by `github-actions[bot]` (`GITHUB_TOKEN`), and a **bot-authored issue doesn't start a
    Claude routine** (A/B-verified: real-user issue #776 fired in <1 min; the cron's #768 never did).
    Fixed to author with `ROUTINE_PAT` — **inert until the owner adds that repo secret.**
- **Ledger:** #778 was unrecorded → added this pass. (#771 is an open ledger PR for #765/#767/#769,
  now redundant since #777's close already recorded them; #766 is an open PR adding 3 orientation ideas
  — both belong to other sessions, left untouched.)

## 2. Close-out scorecard (what this pass fixed — the "didn't finish / forgot a step" list)

| Loose end / drift | Action taken |
|---|---|
| 2 executed ideas still badged `ideas` (`repo-manageability`, `review-unit-tagging`) | Re-badged `historical` + README index bullets marked ✅-shipped; documented the "shipped → historical" grooming convention in `ideas/README.md`. |
| `server-management-status` tracker complete but `living-ledger` | Re-badged `historical` (initiative complete through PR14); current-state + roadmap references updated to "historical record"; gated PR13 AI tail stays in roadmap → Later. |
| ~10 candidate rules un-promoted in `.session-journal.md` (Q-0106 propose-step skipped) | Proposed the 3 strongest broadly-applicable ones as **router Q-0120** (DISCUSS lane) for owner markup. |
| Loose ideas with no horizon | Routed: `backup-integrity-check` → quick-win (executing in the tooling PR) · `bot-self-test-walker` → Later (structure-or-defer) · `hermes-bug-triage-flow` → Next, gated on **Q-0121**. |
| 5 scattered maintainer control-plane actions invisible to every in-repo checker | Added a **Control-plane state ledger** to `operations/autonomous-routines.md` (the source of truth no `check_*` sees); surfaced the `ROUTINE_PAT` loop-blocker in current-state Gates. |
| #778 ledger gap | Reconciled (entry added; `check_current_state_ledger --strict` re-run). |
| BUG-0009 / BUG-0011 / Q-0096 visibility | Surfaced in current-state Gates + roadmap (were only in the bug book / router). |

**Workflow-hardening (separate PRs in this session):** extend `scripts/new_subsystem.py`'s checks to
close the new-subsystem pinned-surface cascade gap; add a `CREATE TABLE`-count integrity gate to
`backup-db.yml`; wire the Stop hook to flag abandoned/un-opened PRs (Q-0052/0103/0084) + skipped grooming.

## 3. Cross-agent verification (verified, not obeyed)

This pass weighed a ChatGPT "grounded revision" and three Explore-agent reports against source —
the journal's standing rule *treat cross-agent output as input to verify, not orders* (now proposed as
Q-0120(b)). It **confirmed** the plan's structure but caught specifics **not** adopted:

- "Add `scripts/claude_stop_check.py`" / "wire it into settings.json" — the hook **already exists**;
  the work is to *extend* it.
- "Augment `check_session_log.py` to verify the Q-0089 idea + Q-0102 review" — **already shipped (#733)**.
- "Move executed ideas to a `historical` *subfolder*" — no such subfolder; convention is an **in-place**
  badge change (a move would break reachability).
- Agent-3 flagged Q-0038–Q-0042 as "open" — **false alarm**: the router shows them *Answered — Routed*
  (PR #631 / Q-0051). No fix needed.
- **Real correction (from reading `new_subsystem.py`):** the report and the original plan said
  "auto-patch all surfaces" — but the tool **deliberately doesn't auto-edit** ("generation is guessable,
  verification is not"). The tooling PR *extends its checks* for the missing invariants instead.

## 4. Lessons (durable)

- **A green audit check that contradicts visible evidence is a bug in the CHECK** (the #763 false-green:
  both ledger/cadence checkers matched `Merge pull request #N` but not `Merge PR #N:`). → proposed as
  Q-0120(c). The discipline this pass applied: re-run `check_current_state_ledger --strict` *and*
  eyeball `git log` against it.
- **The loop now spans a control plane no in-repo checker sees.** Five maintainer-side actions had been
  scattered across PR-body prose and kept getting lost (the `ROUTINE_PAT` blocker is why the loop never
  fired). The fix is a durable ledger (`autonomous-routines.md` § Control-plane state), not more prose.
- **Main moves mid-session.** This pass's own baseline shifted #775→#778 while planning; the open-PR /
  merged-since check (proposed Q-0120(a)) caught it. Re-fetch before finalizing any ledger edit.

## 5. What this pass did NOT touch

- The **#780 cadence reconciliation** and its decade queue
  ([night pass §4](reconciliation-pass-2026-06-12-night.md)) — unchanged; this is interim.
- **Runtime code** (`disbot/`) — out of scope this session (owner choice). BUG-0009 (needs AI §7
  list-builders, plan-level), BUG-0011 (needs a VPS repro), and the full Hermes bug-triage build
  (gated Q-0121) are routed, not built. The `/bugreport` interim safety (open-PR-and-hold) is noted in
  Q-0121 as available when needed.

## 6. Owner checklist (the maintainer-side actions no agent can do)

See **[`operations/autonomous-routines.md` § Control-plane state](../operations/autonomous-routines.md)**
for the tracked checklist. Priority order:
1. **Add the `ROUTINE_PAT` repo secret** — unblocks the entire autonomous loop (#778).
2. Add `DATABASE_PUBLIC_URL` — activates the daily backup (#769).
3. Railway **Deploy** the staged `CLAUDE_ROUTINE_*` vars; confirm the **dispatch prompt** (free-form) +
   **routine models** (Opus, not Fable 5).
4. After #1: `workflow_dispatch` `executor-nightly.yml` once and watch the first real run.
5. Decide **Q-0096** (Postgres-MCP / pyright-lsp), **Q-0119** (governance role-pointer home),
   **Q-0120** (candidate-rule promotion), **Q-0121** (Hermes `gh issue create` write).

# Session — Workflow reassessment → reconciliation & hardening (3 PRs)

> **Status:** `complete` — the owner asked for a thorough reassessment of ideas/plans/recent work:
> *find everything we didn't properly finish, catch forgotten steps, make the workflow more
> structured.* Delivered as an interim by-judgment reconciliation + a workflow-hardening build.
> PRs **#780** (docs reconciliation), **#783** (tooling), **#784** (enforcement hook). Plan record:
> [`docs/planning/reconciliation-pass-2026-06-13-workflow.md`](../docs/planning/reconciliation-pass-2026-06-13-workflow.md).

## What was done

**Headline finding:** the system is healthy — zero orphaned ideas, baseline accepted, strong
CI/arch/docs enforcement. Loose ends were concentrated, not sprawling.

- **PR #780 (docs reconciliation, merged):** re-badged 2 executed ideas (`repo-manageability`,
  `review-unit-tagging`) + the completed `server-management-status` tracker `historical`; routed the
  loose ideas (`backup-integrity-check` → quick-win, `bot-self-test-walker` → Later, `hermes-bug-triage`
  → Next/Q-0121); proposed the journal's earned candidate rules as **Q-0120**; opened **Q-0121** (Hermes
  `gh issue create` write); added the **Control-plane state ledger** to `autonomous-routines.md` (the 5
  maintainer actions no in-repo checker sees, incl. the `ROUTINE_PAT` loop-blocker from #778); reconciled
  the #778 ledger gap (offset by archiving #733–#735); surfaced BUG-0009/BUG-0011/Q-0096 in Gates.
- **PR #783 (tooling, merged):** `backup-db.yml` `CREATE TABLE`-count integrity gate before upload;
  `new_subsystem.py --no-panel` for config-only subsystems (+2 tests). The `--no-panel` fix came from
  *empirically* running the scaffold against `welcome`/`automod`/`counters` — they legitimately carry no
  `KNOWN_PANEL_COMMANDS` entry, so the hard-fail `panel-command` check was a false positive.
- **PR #784 (enforcement hook, merged):** broadened the Stop hook's session-log advisory into
  `_end_of_session_advisory` — always (when commits ahead of main) prints a non-blocking reminder of the
  PR-lifecycle (Q-0052/Q-0103/Q-0084), grooming (Q-0015), and session-log obligations. Provenance **Q-0122**
  (owner-directed in-session per Q-0106). Stays advisory because the Stop hook has no GitHub access.

## Decisions / Q-blocks recorded

- **Q-0120** (OPEN) — promote the 3 strongest journal candidate rules into CLAUDE.md (owner to mark up).
- **Q-0121** (OPEN) — give Hermes a 2nd sanctioned write (`gh issue create`) for the bug-triage flow.
- **Q-0122** (provenance) — the Stop-hook advisory, owner-directed in-session.

## Verify, don't obey (this session's spine)

The owner sent a ChatGPT "grounded revision" + I ran 3 Explore agents. Checked all against source:
- ChatGPT was sound at the conclusion level but **wrong on 4 specifics** (claimed `claude_stop_check.py`
  needs creating — it exists; `check_session_log.py` Q-0089/0102 checks need adding — shipped #733; "move
  ideas to a historical *subfolder*" — no such folder; `/bugreport` change is "tooling" — it's runtime).
- An Explore agent flagged Q-0038–Q-0042 as "open" — **false alarm** (router shows them Answered/Routed).
- Reading `new_subsystem.py` corrected the plan's "auto-patch surfaces" framing — the tool *deliberately*
  doesn't auto-edit; the real gap was the `--no-panel` false-positive (found empirically).

## Left open (owner / other sessions)

- **Owner control-plane checklist** ([`autonomous-routines.md` § Control-plane state](../docs/operations/autonomous-routines.md)):
  add `ROUTINE_PAT` (unblocks the loop) + `DATABASE_PUBLIC_URL`; Railway Deploy; confirm dispatch prompt +
  routine models (Opus, not Fable 5); then `workflow_dispatch` the executor once. Decide Q-0096/0119/0120/0121.
- **Other sessions' open PRs:** **#771** (ledger update — likely redundant now) · **#766** (3 orientation
  ideas) · **#704** (owner screenshot test). Not mine to close — flagged for the owner.
- Runtime deferred (owner scope choice): BUG-0009 (AI §7 list-builders, plan-level), BUG-0011 (VPS repro),
  the Hermes bug-triage build (gated Q-0121).

## Q-0104 documentation audit

`check_docs --strict` ✓ · `check_current_state_ledger --strict` ✓ (post-merge) · `check_session_log` (this
log) · all 3 PRs' decisions live in the router; the pass record + control-plane ledger are reachable. The
#780 cadence marker was deliberately left untouched (interim pass) — and the **#782 cadence pass then ran**
on top, scoring band #761–#780 and planning #781–#800, so the cadence obligation is satisfied. Nothing from
this session is captured only in chat.

## 💡 Session idea (Q-0089)

**A stale-local-main guard in the SessionStart hook.** This session nearly built PR 2 on a **90-PR-old base**:
`git checkout main` landed on a local `main` stuck at #687 (diverged), and the new branch inherited it — only
caught by manually diffing. Separately, `origin/main` moved **four times** mid-session (#775→#778→#780→#782),
so any ledger edit risked drift. Idea: have `scripts/claude_session_start.sh` (or a tiny `check_*`) fetch
`origin/main` and **warn loudly when local `main` is behind/diverged from `origin/main`, or when the working
branch's merge-base is far behind `origin/main`** — "you're based on an N-commit-old main; branch from
`origin/main`, not local `main`." Cheap, read-only, and it turns the exact trap I hit into a guardrail. Pairs
with the proposed Q-0120(a) open-PR/merged-since check. *(Dedup-checked: distinct from #766's orientation
ideas and the gap-analysis "toolchain rot watch.")*

## ⟲ Previous-session review (Q-0102)

Reviewing the **#782 third Q-0107 reconciliation pass** (ran ~parallel to this one): it did the right thing
by **building on top of #780** rather than ignoring it (its base included my interim pass), then scored the
band and planned #781–#800 — exactly the next-band planning my interim pass deliberately left owed. It also
captured a sharp idea (the live-decade-queue-pointer invariant). What the coincidence exposed: **two
reconciliation passes fired within minutes** (my interim #780 + the cadence #782) because my docs PR *was*
PR #780, tripping the cadence trigger. No harm done (UNION-merge held), but the **system improvement** it
surfaces: the cadence trigger should notice when an interim by-judgment reconciliation just landed and either
fold into it or note the overlap, so two passes don't redo each other's ledger work. A natural follow-on to
the live-decade-queue-pointer-invariant idea #782 itself captured. Genuinely minor — the per-lane ledger
discipline + UNION-resolve absorbed it cleanly, which is the system working as designed.

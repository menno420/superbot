# Idea: route executor self-chaining through the cron/PAT workflow, not a session-opened issue

> **Status:** `ideas` — captured 2026-06-15. Class: workflow / autonomous-loop reliability. Root-cause fix.
> Provenance: surfaced live with the owner while diagnosing "why doesn't the routine always start on its trigger?"

## The problem

The night-executor's STEP 3 self-chaining contract says: *"open a `continue` issue with explicit
instructions; that issue triggers the next run."* In practice this is **structurally unreliable**, and
it is the cause of the observed "routine didn't fire" misses (e.g. issue #887).

Diagnosis (owner-confirmed constraints: routine is ON, `ROUTINE_PAT` does **not** expire, the trigger
filter is correctly `issues: opened` + label `continue`): the failure is **not** config. It is the
**actor that generated the `issues.opened` event**:

| Issue | Opened by | Fired? |
|---|---|---|
| #894 / #819 (scheduled) | the cron **workflow** via `ROUTINE_PAT` (independent external event) | ✅ |
| #887 (handoff) | a **Claude routine session** via its own GitHub integration | ❌ |

Same `continue` label, same displayed author (`menno420`), opposite outcome. Claude Code routines
almost certainly have **loop-prevention**: an issue opened by a routine's own GitHub App does not
re-trigger a routine (otherwise a routine could spawn itself infinitely). GitHub events carry the
sender app id, so even a user-attributed issue is recognised as self-generated and skipped. This is the
same "who authored it" axis that already explained `github-actions[bot]`-authored issues not firing
(#768) vs. a real-user issue firing (#776) — one layer deeper.

Secondary contributor: routine **concurrency** — #887 was opened while another routine session was
mid-build; a one-session-per-repo limit would also drop a trigger arriving during an active session.

## The fix

Don't let a session trigger the next run by opening its own issue. The session only **requests** a
chain; an independent **GitHub Action opens the actual `continue` issue with `ROUTINE_PAT`**, so every
chaining trigger is a PAT/workflow event — identical to the scheduled trigger that already fires
reliably. Concretely, one of:

- a workflow on **`pull_request.closed` (merged)** that, when the PR carries a `chain-continue` label
  (set by the executor) + a handoff marker, opens the next `continue` issue via `ROUTINE_PAT`; or
- a workflow on **`issues.closed`** of a `continue` issue whose body carries a `REMAINING:` block,
  re-emitting it as a fresh PAT-authored `continue` issue.

Mirror `executor-nightly.yml` exactly (dedupe guard, `ROUTINE_PAT || GITHUB_TOKEN` with the loud
missing-PAT warning, `if: github.repository == 'menno420/superbot'`).

## Verification first

One clean test disambiguates loop-prevention from concurrency: when nothing else is running, have a
Claude session open a `continue` issue via MCP and watch. Doesn't fire → loop-prevention (build the
fix). Fires → it was concurrency at 00:28 (then the fix is a nicety, and the real lever is the
run-cap / one-session limit).

## Related

- `docs/operations/autonomous-routines.md` § Control-plane state (the bot-author rule, the cron-lag
  caveat) — this is the next entry in that family.
- `.github/workflows/executor-nightly.yml` — the proven PAT/workflow trigger path to mirror.

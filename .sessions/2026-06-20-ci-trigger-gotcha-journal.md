# 2026-06-20 — capture the "pushes don't re-fire PR CI" env gotcha (journal Quick-ref)

> **Status:** `complete`

## Arc

Follow-up to the same dispatch run that shipped PR #1166 (panel_base_class allowlist parity guard).
That PR hit — and recovered from — a real remote-environment gotcha worth durable process memory:
**`git push` to an existing PR branch does NOT trigger `pull_request: synchronize` Code Quality runs
here; only the PR open/reopen event does.** The born-red "open PR with an `in-progress` card, flip it
`complete` on a later push" flow therefore strands the PR — the open-run fails on the session gate, the
close-out push fires no new run, and the head ends up with no passing required check, so auto-merge sits
`blocked` indefinitely. Recovery was to **close + reopen** the PR via the GitHub MCP, which re-fired CI
on the current head (card already `complete`) → green → merged.

This was not capturable on the merging branch itself (any new push would have re-stranded the
in-flight CI run), so it lands here as a focused, docs-only follow-up.

## What shipped

- **`.session-journal.md`** ⚡ Quick reference — a new row: *"PR stuck `blocked`, no Code-Quality
  check on the head?"* documenting the synchronize-doesn't-fire gotcha, the close+reopen recovery, and
  the avoid-it rule (push all commits incl. the `complete` card before opening the PR).

## Why journal, not bug-book

The bug-book is for live/production bugs with a stays-fixed code guard. This is a CI/infra/process
gotcha of the remote-execution environment — its home is the journal runbook/Quick-reference (per
`.claude/CLAUDE.md`: the journal holds the env runbook, recurring problems, and gotchas).

## Verification

- Docs-only change (`.session-journal.md` + this `.sessions/` card) → CI runs the docs-only fast path.
- `python3.10 scripts/check_docs.py --strict` → clean.
- Opened with a `complete` card and all commits pushed before opening (the avoid-it rule above), so the
  single PR-open CI run merges without needing a synchronize re-fire.

## 📤 Run report

- **Did:** captured the "git push doesn't re-fire PR CI in this env" gotcha + its close/reopen recovery
  in the journal Quick reference · **Outcome:** shipped
- **Shipped:** this PR — journal Quick-ref row (docs-only)
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none — but FYI (not an action): the born-red auto-merge flow is brittle in
  this remote env because branch pushes don't re-fire `synchronize` CI. Workaround documented; if it
  keeps biting, the durable fix is a workflow/process change (e.g. push the complete card before
  opening, or a `workflow_dispatch` re-fire path) — worth a future router DISCUSS if it recurs.
- **⚑ Self-initiated:** this capture (process-memory improvement; no dispatch/owner ask — Q-0172).
- **↪ Next:** unchanged from #1166's handoff — prefer a substantial `needs-hermes-review` lane or a
  fresh idea→plan→build; ungated self-merge depth is thin.

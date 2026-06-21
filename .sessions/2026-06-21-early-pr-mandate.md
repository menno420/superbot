# Session — open the session PR FAST (Q-0189, owner-directed in-session)

> **Status:** `complete`
> **Run type:** routine · dispatch
> **Branch:** `claude/early-pr-mandate` · **PR:** #1224

## What shipped

Owner directed, live in-session: opening the session PR is now mandated to happen
**within ~2 minutes of session start**, before the build work — applied under the
Q-0106 live-owner carve-out (owner is the reviewer).

- Amended the **Q-0133 born-red bullet** in `.claude/CLAUDE.md` § Session & plan
  workflow with the timing mandate: *orient → decide scope → claim → open the
  born-red PR immediately → then build; target the first ~2 minutes, don't let the
  open slip behind the work.*
- Recorded provenance **Q-0189** in `docs/owner/maintainer-question-router.md`,
  framed as the *timing* half of Q-0052 / Q-0103 / Q-0133.

Docs-only; `check_docs --strict` + `check_quality --check-only` green; owner is live
reviewer → self-merge on green.

## Session enders

**⟲ Previous-session review (Q-0102):** this is the third lane in one chat. The
first (duplicate reaction-roles PR 2) failed by skipping the `active-work.md` +
open-PR pre-scan; the second fixed the tool that should catch that (claim-ledger
scan in `check_lane_overlap.py`, #1223 merged); this third pins the *timing* of the
early PR open so the in-flight signal is visible sooner. Together they harden the
exact failure mode that started the chat — a tight self-auditing loop.

**📚 Doc audit (Q-0104):** rule lives in `.claude/CLAUDE.md` (Q-0133 bullet) with
provenance in the router (Q-0189). `active-work.md` claim added. No `current-state`
change needed.

## 📤 Run report
- **Run type:** routine · dispatch
- **What shipped:** Q-0189 — open the session PR within ~2 min of start (CLAUDE.md + router).
- **⚑ Self-initiated:** no — owner directed it live in-session.
- **⚑ Owner-decisions:** Q-0189 (recorded in the router).
- **⚑ Owner-manual-steps:** none.

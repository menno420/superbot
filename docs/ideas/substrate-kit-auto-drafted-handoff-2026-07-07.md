# Substrate-kit: auto-drafted session handoff (write-back without discipline)

> **Status:** `ideas` — capture, not a plan. **Subsystem:** substrate-kit (S3).
> **Provenance:** the Phase-2.5 cold-start A/B, measured twice (original run #1775 + the
> 2026-07-07 re-run pair in the final-review session #1778).
>
> **Update (2026-07-07, PR #1783):** the *other half* of the write-back problem — **making the
> journal mandatory** — is now shipped: `adopt --wire-enforcement` installs a live CI gate that
> holds the merge red until the session card is written (`check --require-session-log`). That is
> the *locked door*. This idea is the complementary half: make writing the card **easy** (auto-draft
> it from evidence) so the mandatory thing is also a low-friction thing. Door without draft = the
> work gets recorded but grudgingly; draft without door = it gets skipped; both = the discipline
> this repo actually runs on. Build this next.

## The observed failure (twice-measured, not hypothesized)

Both Phase-2.5 runs measured the same behavior: a session with a purpose-built decisions ledger,
session-log scaffolding, and current-state file **sitting rendered in its repo** still recorded
its work only in commit messages + README — zero kit-surface write-back. The re-run made the docs
*readable* (the adopt-render fix) and the ON session **read more** (M1 rose) but **still wrote
nothing back**. Conclusion: recall isn't the bottleneck, and readability isn't either —
**write-back that depends on agent discipline does not happen** in task-focused sessions.

## The idea

Stop asking the agent to remember. The kit's session-close path (`bootstrap session-close`, and
the staged Stop-hook) should **auto-draft the handoff** from evidence it can already see:

- `git diff` since session start → "what changed" (files, tests added, commands touched)
- test-suite state (run the detected verify command) → "state at close"
- new/modified doc files → "docs touched"
- a skeleton `.sessions/<date>-<slug>.md` card pre-filled with the above + empty slots for the
  judgment-only fields (decisions made, next-session pointer)

The agent then *edits a draft* instead of *authoring from scratch* — the same trick that makes
the born-red card work in this repo (the card exists before the work, so closing it is editing,
not remembering). A drafted-but-unedited card is still vastly better than the measured baseline
(nothing), and the kit's session-log checker can distinguish drafted-only from completed.

## Why it's worth having

It converts the kit's weakest measured claim (continuity value) into a mechanical property, and it
is exactly the "write-back discipline, not recall" point the Projects-EAP review (§4) argues the
platform should own — this is the kit-local version we can ship without waiting for any platform.

## Fit

Lands in `substrate-kit/src/engine/` (session-close + stop_check); pure stdlib (git + subprocess);
testable against a scratch repo like the existing adopt tests. A natural T4 re-run afterward would
measure whether drafted handoffs finally move the continuity needle.

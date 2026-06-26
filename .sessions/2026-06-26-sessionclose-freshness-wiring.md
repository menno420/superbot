# 2026-06-26 — Wire ▶ Next freshness guard into /session-close

> **Status:** `complete`
> **Run type:** routine · dispatch
> **Branch:** `claude/franklin-sessionclose-freshness` · **PR:** #1477

## What was done
Second slice of this dispatch run, completing the first. PR #1476 (merged) shipped
`scripts/check_sector_next_freshness.py` (flags a per-sector `▶ Next` linking a SHIPPED /
`historical` plan) but gave it **no invocation site** — a guard nobody runs is useless. A
stale pointer could still sit unguarded between the 30-PR reconciliation passes (the S3
pointer #1476 fixed had been live 3 days before this run caught it by hand).

- Added `check_sector_next_freshness.py` to the `/session-close` **Step-4 quality gate**
  (`.claude/skills/session-close/SKILL.md`) + a one-line remediation note (re-point the
  flagged `▶ Next` at buildable work, preserve the shipped provenance, Q-0166 fix-on-sight).
- This is option (a) — the "smaller, surer win" — from #1476's session idea: every session
  now re-checks `▶ Next` freshness on the way out, instead of relying on the 30-PR cadence.
- Skill/orientation-only edit (not CLAUDE.md / hooks / settings — read-only to an autonomous
  run, Q-0106).

## Decisions recorded
none.

## Left open / next session
- Nothing open for this slice.
- The *other* half of #1476's idea (option (b): roadmap Now/Next bullets carry plan links so
  `dispatch_menu.py` can suppress a shipped lane at the dispatch pick) needs a roadmap-
  convention change first — left as a future idea, not started.

## Verification
- `python3.10 scripts/check_sector_next_freshness.py` → OK on live main (post-#1476 merge).
- `python3.10 scripts/check_docs.py --strict` → all checks passed (skill file is reachable
  docs; no structural break).

## 💡 Session idea (Q-0089)
The `/session-close` Step-4 gate is now a hand-maintained list of `check_*` invocations that
has grown to ~7 entries — and it's drifted before (a checker exists but isn't wired into any
gate, exactly the gap this slice closed). Idea: a tiny meta-check `check_session_close_gate.py`
that greps `scripts/check_*.py` for the Q-0105 "run … from the docs-reconciliation routine /
session close" provenance phrasing and asserts each such checker is actually referenced in
`SKILL.md`'s Step-4 block — so a guard authored "to be run at close" can't silently lack an
invocation site (the meta-version of the bug this slice fixed). Small, offline, on the same seam.

## ⟲ Previous-session review (Q-0102)
The previous slice (this run's own #1476) was solid — it found a real bug, fixed it at the
root, and built the class-level guard with tests. What it **missed** (and I caught only because
I kept going): it shipped the guard with **no caller**, which is the same failure mode as the
drift it guards against — a thing that exists but nobody runs. The system improvement that
surfaced and is now acted on: **a checker is not "done" until it has an invocation site** (a
CI step, a hook, or a /session-close gate entry). The Q-0089 idea above proposes machine-
enforcing exactly that, so the next "I built a guard" slice can't repeat the omission.

## 📤 Run report
- **Run type:** routine · dispatch
- **PR:** #1477
- **⚑ Self-initiated:** wiring `check_sector_next_freshness` into `/session-close` — the
  completing half of #1476's self-initiated guard; no dispatch/owner ask (Q-0172), flagged
  for owner review/revert.
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none

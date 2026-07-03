# Golden recapture on current-bot bug fix — a protocol so parity never preserves a bug

> **Status:** `ideas` — session idea (2026-07-03, Q-0089, rebuild-planning-phase doc session).
> Surfaced by the capstone's doc-set reviewer; filed durably here.

## The collision

Two things the rebuild does at once:

1. The capability audit routed **six live current-bot bugs** (two money bugs — deathmatch PvP
   double-settle, blackjack free-tournament double-pay) as immediate fixes, independent of the
   rebuild.
2. The rebuild **parity-checks the new bot against the frozen old bot's captured behavior** (the
   `parity/` golden harness, #1639) — "does the rebuilt subsystem reproduce the shipped one?"

These collide on timing. If a current-bot bug is fixed **after** its golden is captured, parity
later verifies the *fixed* behavior — fine. But if a bug is fixed **before** capture and the
golden is **not re-captured**, the golden encodes the *buggy* behavior, and the rebuild faithfully
reproduces the bug — parity goes green on a bug. The merge=deploy cadence (every merge redeploys)
plus a behavior-capture oracle makes this an easy silent class.

## The durable fix (one line, a checklist item)

**Every current-bot behavior fix must re-capture its `parity/` golden — or explicitly record
"pre-capture, no golden yet"** — wired into the bug-fix session checklist (and, once the harness
is a required gate, into the capture protocol itself). A fix without a golden decision is
incomplete.

## Why it's worth having

- It's cheap (a checklist line + a one-shot recapture command per fix).
- It prevents a bug-*preservation* class that is invisible precisely because parity is green.
- It applies **now** (the six routed fixes are the first candidates) and **through cutover** (any
  fix landed while capture is still running against the live bot).

Related: `NEW-BOT-BUILD-PLAN.md` §6.3 (the six routed bugs) + §4.4 (the doc-set reviewer's
golden-recapture proposal); the rebuild parity harness (design spec §6, linchpin validation).

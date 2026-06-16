# 2026-06-16 — capture: BTD6 shorthand-corpus eval idea (post-BUG-0015 grooming)

> **Status:** `in-progress`

**Branch:** `claude/gifted-noether-37tiwr` · **Date:** 2026-06-16 · continuation after BUG-0015
(#963 merged) — the standing secondary task (Q-0015 grooming / Q-0088 capture-to-queue).

## What I'm about to do

BUG-0015 ("d67 dart paragon") is **merged (#963)** and verified on main. With capacity remaining,
and per Q-0088 (*late discoveries go into the queue, not unguided PRs past scope*), I'm **capturing**
— not implementing — the one genuinely-valuable system-hardening idea this session surfaced: a
**BTD6 community-shorthand corpus regression test** that guards the recurring "shorthand → unguarded
general path → model freelances" bug class (BUG-0001/0003/0004/0008/0015). Today each fix has only
its own isolated test; there is no single guard for the class.

Also recording the verified **hero-per-level** investigation result so a future session doesn't
re-derive it: heroes route fine + grounding already surfaces all-level descriptions + stats at
1/3/10/20 — only non-headline-level *exact stats* are the (minor, low-priority) gap.

Docs-only: a new `docs/ideas/` capture + README index entry. No `disbot/` runtime.

## ✅ Done

- `docs/ideas/btd6-shorthand-corpus-eval-2026-06-16.md` — the captured idea (class table, the
  corpus-test sketch, why-captured-not-built, the hero sibling finding, lifecycle).
- `docs/ideas/README.md` — index entry at the top (newest-first).

## Context delta

- **The conflict-guard flap I flagged at the end of the BUG-0015 session is already fixed** — hotfix
  **#966** rewrote `pr-conflict-guard.yml`'s step with a guarded `post()` helper (no more `&& echo`
  tripping `bash -e`; exit 0 on a single hiccup). No action needed; closed.
- **The recurring router-class** (shorthand → unguarded path) is the highest-leverage durable
  follow-up from BUG-0015 — captured as the corpus eval above.

## Session enders

**💡 Session idea (Q-0089).** *Is* the deliverable — the shorthand-corpus eval (a genuine, verified
class guard; dedup-checked against `docs/ideas/`, no existing corpus/router-class entry).

**⟲ Previous-session review (Q-0102).** The BUG-0015 session (#963) did the fix well (root-caused
the two-layer routing+grounding gap, tested each layer, verified the merge in-turn through a busy
merge-queue treadmill). What it could have done better: it flagged the conflict-guard flap to the
owner but didn't note that flap was a brand-new workflow likely to be hotfixed imminently — and
indeed #966 had already fixed it, so the flag was slightly stale by the time it was raised. **System
improvement:** before flagging a CI/workflow defect, `git fetch` + check if a hotfix already landed
(the same "sync-first" reflex the journal already prescribes for task overlap) — extended here to
*infra observations*, not just task claims.

**Doc audit (Q-0104).** Docs-only; `check_docs --strict` to run before push. No new owner decision.
The `#963` ledger entry + the ~13 unrecorded merges remain the reconciliation routine's lane
(Q-0124), not this session's.

## 📤 Run report

- **Did:** captured the BTD6 shorthand-corpus eval idea (the recurring router-class guard) + recorded
  the hero-per-level finding; confirmed the conflict-guard flap is already fixed (#966) ·
  **Outcome:** shipped (docs)
- **Shipped:** the idea capture + README index entry (docs-only).
- **⚑ Owner decisions needed:** `none`.
- **⚑ Owner manual steps:** `none`.
- **↪ Next:** the corpus eval is a small/decided grooming-pass execute-now candidate for a later
  session or the next AI-router touch; BUG-0015 itself is fully shipped.

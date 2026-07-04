# 2026-07-03 — Ultracode quick-launch prompts + durable-home verification

> **Status:** `complete` — PR #1689. Owner-directed. Docs-only; no code, no workflow launched.

## What shipped (PR #1689)

1. **Durable-home verification (reported to owner):** confirmed on `main` — all 18 owner decisions
   Q-0219…Q-0236 in the router; all 10 session docs (5 planning + 5 ideas) exist; all 8 session
   PRs (#1679–#1688) in the ledger; the `.claude/settings.json` allowlist change landed;
   `check_docs --strict` + `check_plan_homing` green; all 5 session ideas indexed. Only flag was
   benign newest-merge lag (records at the #1710 recon pass — not drift).
2. **Two short quick-launch prompts** added to
   [`rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md`](../docs/planning/rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md)
   (⚡ Quick launch section) — one-liners that point each parallel session at its full PROMPT A /
   PROMPT B, so the owner launches with a short paste instead of the whole prompt.

## 💡 Session idea (Q-0089)

No new idea — small verification+convenience PR at the tail of a session that already produced five
genuine ideas; Q-0089's anti-filler bar applies.

## ⟲ Previous-session review (Q-0102)

Previous card: **#1688 (the two ultracode prompts).** Solid — disjoint scopes + shared method +
rubric scoring. **Gap it left, fixed here:** the *launchers* for those prompts existed only as an
intention; had the owner not asked, the short-launch convenience would have lived only in chat —
which the durable-home check would then have flagged. Lesson: when a doc is meant to be *used* by a
human action later (launch, paste, run), ship the one-line "how to invoke" **in the doc** at write
time, not just the full artifact — the invocation path is part of the deliverable.

## Docs audit (Q-0104)

- `check_docs --strict` + `check_session_gate` at close (below); no ledger entry needed (this PR is
  itself the verification + a convenience edit; the substantive ledger entries #1679–#1688 already
  present and were the thing verified).
- No new owner decision (Q-0236 already covers the ultracode prep); no router change.

## ⚑ Self-initiated

None — owner-directed (verify durable homes + give two short startup prompts).

## Session total: nine PRs

#1679 · #1680 · #1683 · #1684 · #1685 · #1686 · #1687 · #1688 · #1689.

## For the next session / the owner

- **Launch** the two sessions with the quick-launch prompts (⚡ section of the brief).
- Then: their issues ledgers → **Stage-2 subsystem walk** (rubric-driven) → **Gate V** → **Phase B**
  → **migration**. Still-open: preset hide-vs-disable (Q-0232).

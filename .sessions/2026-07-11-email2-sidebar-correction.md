# 2026-07-11 — Email #2: sidebar-nesting correction (owner screenshot)

> **Status:** `complete`

📊 Model: Fable 5 · owner-directed hub session (EAP email) · afternoon · PR #1993

## What happened

The owner's screenshot (claude.ai sidebar, 16:45 local) proved the sidebar ALREADY
nests a Project's sessions + routine-spawned worker slices under the Project — the
email's Part 2 wrongly implied that nesting was missing. Corrected in
`docs/eap/anthropic-email-2-draft-2026-07-11.md`:

- **(c) roster bullet** — now credits the existing per-Project nesting explicitly
  (operator-verified live) and names the roster's real target: the cross-Project layer
  (which lanes working vs idle, what shipped, what's blocked).
- **(d)6** — rephrased from "fleet visibility" wholesale to "one level above what
  exists": cross-Project view + liveness heartbeat; the nesting is there and good.
- Working-notes fact-refresh log records the correction + its evidence.

Part 1's matching sentence (the owner's "add active agents to the sidebar as
subsessions" idea — which the screenshot shows is already shipped) is above the
owner-edits-only marker; suggested rewrite delivered in chat for HIM to apply.

## ⚑ Self-initiated

None — owner-directed correction; wording choices flagged in the diff.

## 💡 Session idea

**Screenshot-to-figure intake:** when the owner drops a screenshot in chat that
*evidences or corrects* an email/report claim, the session should offer one word to
commit it into the relevant `screenshots-*/` folder with a fig number + caption (this
one would be fig-18, "sidebar nests worker slices under the Project"). Today the
correction is only prose; the proving image lives in chat and dies with the
conversation. Small, but it closes the same only-in-chat gap the figure index was
built for. (Dedup: the figure folder + index exist; the missing piece is the intake
offer as standard behavior.)

## ⟲ Previous-session review (Q-0102)

The earlier email2-part2-polish slice (same session arc) did the fact-refresh well but
verified Part 2's claims only against *repo* ground truth — the sidebar claim was a
*platform-UI* claim, unverifiable from a session, and it sailed through. Improvement,
already applied in the correction text itself: platform-UI claims in owner-facing
reports should be tagged as operator-verify items (only the owner can see that
surface) rather than asserted — the same two-vantage lesson the email itself teaches.

## Documentation audit (Q-0104)

`check_docs --strict` run at close · ledger benign newest-merge lag only · telemetry
row appended this PR · claim deleted · the proving screenshot remains chat-only
(flagged as the session idea above; the owner can drop it into
`docs/eap/screenshots-2026-07-11/` as fig-18 if he wants it durable).

# 2026-06-27 — BTD6 QA arc: session-close documentation (what shipped + live-test checklist)

> **Status:** `complete`

**Run type:** owner-directed (session close — "document what we did + what's still to test, then end")

## What this run did

Consolidated the day's BTD6 QA-accuracy arc (six merged PRs: #1487 interaction grounding · #1488 evals
wiring · #1490 faithful live path · #1491 semantic grader · #1492 verified DDT counter grounding) into the
durable corpus doc, and added an explicit **live-verification checklist** of what still needs a real-key /
prod test:

- re-run *AI Evals → suite: btd6* after deploy (expect interaction questions pass + the DDT question
  answers with towers, not a refusal);
- a live Discord spot-check of the original screenshot questions;
- the **golden-set over-refusals are NOT fixed** (round-cash partly a DB-less harness limitation; the rest
  a possible guard/grounding issue — separate scope);
- a couple of golden rubrics look stale (verify the rubrics, not the bot).

Docs-only; no `disbot/` change.

## ⚑ Self-initiated

None — owner-directed session close.

## 💡 Session idea (Q-0089)

*A tiny `docs/btd6/qa-status.md` "live-test checklist" that the live eval action updates a timestamp on
when it passes* — so "when did a human last confirm these answer correctly in prod?" is visible, not
folklore. Routed as an idea.

## ⟲ Previous-session review (Q-0102)

The arc's strength was tight owner-in-the-loop iteration (each PR driven by a screenshot or a pasted
scorecard) and verify-before-shipping (the wiki/owner-confirmed Sniper check kept a wrong tower rec out).
The improvement this close-out makes: the per-PR session logs documented each step but a reader had no
single "what's the live-test status of the whole effort?" view — now the corpus doc has it. Lesson: a
multi-PR arc deserves a consolidated status doc, not just N session logs.

## 🧾 Doc audit (Q-0104)

`check_docs`/`check_consistency` green. The consolidated arc + live-verification checklist now live in
`docs/btd6/qa-accuracy-corpus-2026-06-27.md`. All six runtime/eval PRs merged; this is the documentation
capstone. Ledger: the six PRs are added by the next reconciliation pass (merged-only convention).

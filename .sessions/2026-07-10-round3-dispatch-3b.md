# Session — round-3 dispatch part 3b: Q-0265 continuous mode (live copilot)

> **Status:** `complete`
> **Run type:** owner-directed · same chat as part 3 (PR #1955, merged) — fresh card/branch
> per the never-reuse-a-merged-card rule.
> **Model/time:** fable-5 · 2026-07-10 ~21:2xZ →

## What is about to happen

The owner caught both new seats idling between wakes ("I thought you were supposed to
keep working indefinitely, with the routine as a failsafe") — diagnosis confirmed: the
founding packages' inherited "ONE bounded slice per wake / no excessive work" doctrine
did instruct exactly that. Owner ruling: **ALL SIX core seats go continuous**.

## What shipped

- **Router Q-0265** (owner's words preserved): work loop slice-after-slice ·
  send_later continuation chain as the pacemaker · standing crons demoted to dead-man
  failsafes · queue backpressure replaces the time throttle · Q-0089 honesty guard
  retained · **cost flag INVERTED by the owner** (free window through 07-14 = use
  excessively; produce-then-curate consolidation pass after; volume doubles as EAP
  test data for Anthropic).
- **Package rewrites** (unbooted seats boot continuous natively): product-forge +
  simulator — SESSION SHAPE + routine blocks now continuous/failsafe-form.
- **Amendment banners** (live seats — docs stay historical paste records):
  idea-engine package, builder package, runbook §2 manager package.
- **The owner paste block**: part-4 brief §2b (universal amendment for the four live
  chats + the manager-only gen-3-blueprint + consolidation-inventory riders); brief
  §2 item 0 makes the amendment round the next session's first action.

## 💡 Session idea

**Doctrine-phrase drift linter** — a checker that greps founding packages/briefs for
phrases superseded by later Q-rulings (e.g. "one real slice per wake" after Q-0265) so
stale doctrine can't be pasted into a new seat. Today's fix hand-hunted five surfaces
with grep; the next superseded phrase will hide the same way. (Card-line capture; the
Idea Engine's fleet section is its natural probing home via harvest.)

## ⟲ Previous-session review

Part 3 (same chat, this morning→evening) verified rigorously and shipped a full
redesign same-hour — but it authored THREE founding packages that propagated the
inherited "one slice per wake" SESSION SHAPE without re-deriving it against each
seat's purpose, despite standing never-stop signals (Q-0241 never-wait; "an agent
should always have a next thing to do"). **Improvement:** when authoring a founding
package, the SESSION SHAPE block is a per-seat design decision (producer vs governor),
never template text to copy forward — the Q-0265 misfit would have been caught at
drafting time by that one question.

## Documentation audit (Q-0104)

`check_docs --strict` ✓ · `check_current_state_ledger --strict` ✓ (post-fix checker) ·
chat-only material swept: the ruling + owner rationale → router Q-0265; the amendment
block → brief §2b (durable); banners tie the five package surfaces to the ruling.
Claim deleted this commit. Telemetry row landed at open.

## Handoff

Unchanged from part 3's brief, plus: **brief §2 item 0** (the amendment round) is now
the next session's first action; sim-lab + product-forge boot continuous natively.

# Session — Autonomous-loop seams: Hermes review + phase gate + dispatch bridge

> **Status:** `complete` — PR #742 merged. Owner-directed session (the maintainer was live
> and answered the three autonomy decisions via the question panel).

## Task

The owner asked to **finish the configuration of the Hermes agent and the autonomous workflow
we planned**. The skill pack (PR #730) was already done; the unfinished part was the
**autonomous-improvement loop**, parked in the discuss lane because the autonomy/safety
boundaries were the owner's to set. He was live, so I collected the three gating decisions and
built the repo-side seams.

## Owner decisions (question panel, recorded as Q-0113 / Q-0114)

- **Build scope:** Hermes-reviewer seam · phase gate · dispatch bridge (Stage 0 Action deferred).
- **Merge gate (Q-0113):** routines **self-merge on green CI** (Q-0084 extended to unattended runs).
- **Human gate (Q-0114):** **agent-originated features only** reach approve/deny; bug/UX/docs/
  correctness flows freely. A feature may only be *originated* in invent-phase (phase gate).

## What was built (PR #742)

- **`superbot-review`** Hermes skill (`docs/operations/hermes-skills/review.md`) — independent
  non-Claude critique of a plan or PR diff; verdict + findings + a plain-language
  `## Maintainer summary` block that is the approve/deny hand-off. Breaks the Claude-only
  monoculture (vision §3).
- **`scripts/check_phase_gate.py`** (+ 6 tests) — fix-phase vs. invent-phase signal. Invent
  requires zero OPEN bugs (bug-book) **and** zero `Not Done` readiness rows; reuses
  `readiness_scoreboard.collect()` (no duplication). `--phase` / `--json` / `--require-invent`.
  Honest current read: **FIX-PHASE** (1 bug, 34 not-done, 58% done).
- **`superbot-dispatch`** skill + **`docs/operations/hermes-dispatch-bridge.md`** runbook — Hermes
  fires a Claude Code Routine `/fire` endpoint (read-only: sends text). The runbook holds the
  **routine's saved gate prompt**, where the merge/human/phase gates live on the build side, plus
  the maintainer's ⬜ wiring steps and the Q-0105 kill switch.
- **Records:** router Q-0113/Q-0114; workflow **§12** (the binding subset of the loop); both idea
  docs' status blocks flipped from "not approved" to "seams built"; control-plane doc +
  skills-README + repo-navigation-map reachability. Regenerated SKILL.md (7→9 skills).

## Verification

- `check_quality.py --check-only` ✓ · `check_architecture.py --mode strict` ✓ (0 errors) ·
  `check_docs.py --strict` ✓ · `build_skills.py --check` (9 fresh) ✓
- Targeted pytest sweep (phase gate + build_skills + docs) → **104 passed**. No `disbot/` changes.
- CI green on #742; self-merged per Q-0084 (docs/tooling, not a feature; base unmoved, clean).

## Ledger reconciliation

Found drift: #732/#738/#739 were missing from Recently-shipped (plus my #742/#740). Added all;
`check_current_state_ledger --strict` now clean (last 15 present).

## Left open / handoff (next session)

- **Q-0107 decade reconciliation — DONE concurrently by PR #741** (a parallel session ran the
  decade pass at the same time as this one; it mapped #715–#740, produced the
  [`planning/reconciliation-pass-2026-06-12.md`](../docs/planning/reconciliation-pass-2026-06-12.md)
  decade queue, reset the marker to #741, and reconciled #742 in-band). My #743 session-close
  PR collided with it on `current-state.md`/-archive — resolved by taking #741's authoritative
  ledger (UNION, reconciler role) and keeping only this session log. **Lesson:** check `list_pull_requests`
  for an in-flight reconciliation before doing ledger surgery at session close (the #678/#682
  parallel-collision class again). **Next action is now #741's decade queue, not a reconciliation.**
- **Maintainer VPS actions to close the loop:** create the Claude Code Routine (paste the saved
  gate prompt), store `CLAUDE_ROUTINE_*` on the VPS, `install-skills.sh` + restart the gateway;
  then **calibrate (Q-0105)** — plant a known issue for `superbot-review`, dispatch one tiny known
  fix to confirm the merge gate behaves — before trusting either unattended.
- **Stage 0 continuation Action** (workflow §10) still queued; owner provides the API-key secret.

## Grooming move (Q-0015)

Advanced the two loop ideas down their lifecycle: `autonomous-improvement-loop-vision` and
`hermes-claude-dispatch-bridge` moved from `ideas / not-approved` to **partially implemented**
(three seams built; remaining step is owner-side wiring) with their status blocks + the
exists/missing table updated to reflect the shipped code. The phase-gate seam (vision routing
step 3) and the reviewer seam (step 2) are now done; only the dispatch *wiring* (step 1) remains.

## 💡 Session idea

**Idea:** a **`superbot-calibrate` harness** — a tiny repo-side fixture set of plan/PR snippets
with *known planted issues* (a services→views import, a missing audit-event on a mutation, a
mislabeled round-cash total) plus an expected-findings key, so the `superbot-review` reviewer
(and any future GPT/Gemini swap) can be scored objectively against ground truth before its
dissent is trusted to gate work. **Why it's worth having:** every loop doc and the CLAUDE.md
tooling rule say "confirm against ground truth a few times before trusting" — but that
discipline is currently informal. A fixture+key turns "calibrate the reviewer" from a vibe into
a repeatable, model-agnostic test, which is exactly what lets the reviewer seam be swapped
freely (vision §"Model selection"). Small, additive, and it makes the keystone seam *trustable*
rather than just *built*. (Captured here; not promoted — grooming/owner routes it.)

## ⟲ Previous-session review

**Reviewing the #730 Hermes-installable-skills session.** What it did well: it nailed the
source→builder→artifact pattern (docs are truth, `SKILL.md` generated, a freshness test gates
CI) — that pattern made *this* session trivial to extend (two new skills = two docs + two EXTRAS
lines + regenerate). It also correctly captured the dispatch-bridge idea as the "next big lever"
rather than half-building it. What it could have done better: it left the loop as **three
disconnected captures** (vision doc, dispatch-bridge doc, the §3 reviewer insight) without a
single "here are the 3 seams, here's the build order" through-line — I had to assemble that
from three files before I could scope the work. **System improvement surfaced:** the autonomous
loop now spans CLAUDE.md (Q-0084/0106), workflow §10/§11/§12, two idea docs, the router, and
the dispatch runbook — that's a lot of surface for one concept. A single **`docs/operations/
autonomous-loop.md` index** (one diagram + a "which doc owns which seam/decision" table) would
give the next agent one front door instead of six. I did *not* build it this session (scope was
the seams themselves, and it risks becoming a seventh restatement to drift) — flagging it as a
candidate for the now-due decade reconciliation pass to decide whether it earns its keep.

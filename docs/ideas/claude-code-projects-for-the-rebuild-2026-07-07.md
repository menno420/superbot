# Claude Code Projects (EAP) as the rebuild coordinator

> **Status:** `ideas` — capture, not a plan, not approval. Source, the binding contracts, and
> `docs/current-state.md` win over this. **Subsystem:** none (agent-workflow / meta).
> **Provenance:** owner-supplied EAP invite PDF + in-session discussion, 2026-07-07
> (`.sessions/2026-07-07-projects-eap-and-full-autonomy-q0241.md`). Related governance change:
> **Q-0241** (never-wait autonomy) — see `docs/owner/agent-decision-authority.md` § Q-0241.

## The idea

Anthropic invited us to the **Claude Code Projects** early-access program. Use it as the
**orchestration layer for the SuperBot rebuild** — first prove it on reversible work in *this* repo,
then let it coordinate the build of `superbot-next` (kernel S0–S15 → port bands → cutover).

**This is the Claude Code environment**, not claude.ai Chat/Cowork projects — the EAP FAQ is explicit
that Claude Code Projects are separate and share no data with Chat/Cowork projects. It is the same
cloud-session environment our web/desktop sessions already run in.

## What Projects provides (from the EAP PDF)

- **A coordinator** — one persistent Claude that is the single point of contact for a work stream. You
  hand it a goal; it opens new sessions, monitors running ones, and reports progress. You stop managing
  individual threads.
- **Shared memory** across every session in the Project (cloud-stored); set Project-level custom
  instructions every new session inherits; "say it once" commits a requirement to memory.
- **Routines / scheduling** the coordinator sets up itself (nightly sweeps, weekly dep checks, roll-ups).
- **A session-state sidebar** — sorted by `blocked` / `ready for review` / `working` / `idle`, plus a
  fullscreen "quick task" mode to create tasks without going through the coordinator.
- **Logistics:** all sessions run **in the cloud**, on **Opus 4.8 high effort**, in **auto mode**;
  **free during the EAP**; a Project takes **a list of repositories**; sessions are private to the owner.
  Create at `claude.ai/code/projects/browse`. Mobile *creation* of projects is not yet in scope.

## Why it fits our rebuild unusually well

The canonical plan (`docs/planning/rebuild-canonical-plan-2026-07-06.md` §5) already describes the build
as **"agent fleet — one ultracode session per band," "claim-per-subsystem,"** with the current repo as
the *what/why/how record* and `superbot-next` as the clean source of truth. A Project is precisely that
missing orchestration layer we hand-rolled with claim files, a manual PR-babysitting loop, and cron
triggers:

| Rebuild plan needs | Projects provides natively |
|---|---|
| one session per band across S1→S15 (§5 step 9) | coordinator spins up + monitors per-band sessions |
| claim-per-subsystem to avoid parallel collisions (§5 step 13) | coordinator serializes/tracks; sidebar shows state |
| current repo (plan, substrate-kit, parity goldens) **+** `superbot-next` | Projects take **a list of repositories** |
| "current repo is the what/why/how record" | shared Project memory as the coordinator's working context |
| port bands: walk row → plan → manifest → service → goldens green | coordinator opens draft PRs, fixes CI, steers to completion |

The owner's framing — **"work a few sessions in the current repo to understand the process, then
coordinate the fresh build"** — has real reversible work waiting for it: canonical-plan §5 **steps 1–4
are startable today in this repo** (ship kit tail ①, run the Phase-2.5 A/B, build
`tools/check_amendments.py`, continue the Stage-2 walk). That is the coordinator's shake-down phase.

## How Q-0241 reshapes it

The owner's paired directive (**Q-0241**, 2026-07-07) removes the owner gates: the coordinator builds in
logical order, **live-tests each piece in a real server** (an agent drives all commands live), and
**never waits — silence = consent = done**. That directly matches the Projects model (auto mode, "Claude
makes more calls on its own, opens draft PRs without an explicit ask") — the two ideas compose. The
EAP's **Custom Instructions under Project Settings** is where the one retained rider lives: the
destructive tier (prod import, CUT-3 token swap, deleting old-bot data) runs via the reversible path the
plan specifies (shadow-first, N=7d rollback, reverse-import valve) so the owner's *reaction window* stays
open — never a pause. (Full model: `agent-decision-authority.md` § Q-0241.)

## Open considerations (not blockers)

1. **Memory location.** Project memory is **cloud-stored, separate from the repo.** Our methodology is
   memory-as-committed-docs (canonical plan, decision ledger, `.sessions/`). Treat Project memory as the
   coordinator's *working cache*; keep repo docs the source of truth — which §5's "repo-as-artifact"
   framing already says. Don't migrate the decision record into opaque cloud memory.
2. **Tooling overlap.** Some hand-rolled machinery (claim files, the manual `subscribe_pr_activity`
   babysitting loop, cron triggers) partly duplicates native Project features. During the EAP, evaluate
   which of ours to retire vs. keep. The "priority influence on what's still being designed" the EAP
   offers is a real lever to push the design toward how we actually run this repo.
3. **Repo scope.** A Project takes a repo list — scope it to `superbot` now; add `superbot-next` when it
   is created (former §5 step 6, now un-gated under Q-0241).

## Next lifecycle step

Owner-facing decision to accept the EAP invite and stand up one Project (scope `superbot`; Custom
Instructions = Q-0241 model + the reversibility rider). If accepted, this promotes to a short
`docs/planning/` note wiring the coordinator onto canonical-plan §5. Feedback the EAP asks for
(use-case fit, coordinator judgment, reliability, memory, proactivity, scheduling, sidebar states) maps
onto exactly the rebuild phases, so we'd generate high-signal feedback as a byproduct.

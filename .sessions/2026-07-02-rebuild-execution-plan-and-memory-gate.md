# 2026-07-02 — Rebuild: parallel-execution plan + AI-memory-system as the real new-repo gate

> **Status:** `complete` — docs-only, owner-directed (interactive). Reviewed Fable's Phase-2 design spec,
> then produced the missing schedule + elevated the substrate-kit finalization to the true K0 gate.
> `check_docs --strict` ✓. No `disbot/` code. Follow-up work on a branch whose prior PR (#1634) merged —
> branch reset to `origin/main` first, this is a fresh PR.

## What shipped
- **`docs/planning/rebuild-parallel-execution-plan-2026-07-02.md`** (new) — the schedule the design spec
  never had, grounded in **measured** agent-fleet velocity (41 PRs/day peak · 37/60 merges substantive ·
  ~16 concurrent `claude/*` lanes): **~2-week active-build center, ~1.5-week hard floor** (the sequential
  kernel + careful cutover — the only things parallelism can't remove), stretch ~3–4 wk if the throttles
  come in weak. Separates the four work-classes (sequential critical path / parallel fan-out / human gates
  / careful cutover) and names the two throttles (harness coverage, grammar fit) that convert the model
  into a date.
- **Handoff prompt B elevated** (`rebuild-ultracode-handoff` §B): "finish the adaptive half" → **"finalise
  + ship the AI-memory system"** on **Fable 5**, with room to speculate — reframed as the **real gate for
  *starting* the new repo** (design-spec §9.1 makes the substrate-kit K0's first act), distinct from the
  linchpin proof (§F) that gates *committing* to the build.
- **Two-gates model** folded into the execution plan §0/§8.1 + README homing row.

## Key decisions / verdicts (durable)
- **Timeline recalibrated (owner-corrected):** "multi-month" was the wrong anchor for a 16-wide fleet
  merging 20–40 PRs/day. Honest figure: **~2 weeks active build**, floor ~1.5 wk. The port is
  embarrassingly parallel + self-verifying (red-until-parity → auto-merge); the kernel is the irreducible
  sequential spine; harness coverage is the master variable that decides whether the port fans out or
  re-serializes on human verification.
- **The finished AI-memory system is the true new-repo gate (owner insight).** Everything so far served
  the *bot's* functions; the memory system is what lets agents work correctly *in* the new repo, and K0
  plants it first. Ship it (single-file bootstrap + downloadable package + one-step adopt) before K0.
- **Fable's design spec is approval-quality** — independently verified its load-bearing source claims
  (metrics.py imports, the governance-event subscription trio, the 43 subsystem keys, the ADMIN-floor
  scoping, the 8 `ai:*` ids all hold); it even correctly corrected an error in my own preserve-map synthesis.

## ⚑ Self-initiated (flag for review)
- None unilateral — the execution plan was owner-requested; the memory-gate elevation + the Fable prompt
  were owner-directed this session. Flagged for the record.

## 💡 Session idea (Q-0089)
A tiny `scripts/report_velocity.py` (merges/day + distinct-parallel-lane count + substantive-vs-automated
split, straight from `git log`) — so any planning session grounds "how long?" in **live** velocity instead
of a hand-measured point-in-time snapshot (I computed this session's figures by hand; they'll go stale).
Cheap, reusable, and it keeps the execution-plan schedule honest as the fleet's throughput changes.

## ⟲ Previous-session review (Q-0102)
The Fable-5 design-spec session (#1635/#1637) was **excellent** — a genuine judge panel (4 independent
designs incl. an unconstrained Opus, a live GPT adversarial leg, a source-re-verifying reviser) that
caught two real blockers (the ADMIN-floor over-extension; the sim/`parent_hub` custom-id hazard) *and*
corrected an error in the predecessor synthesis. What it left open — and this session filled — is that the
spec has **no schedule and no explicit "which gate comes first"**; a superb design with no clock invites
the "multi-month" misread the owner rightly pushed back on. **System improvement:** owner-gate design
specs should ship with a companion execution/schedule doc as a matter of course (now done); the
judge-panel-as-saved-workflow idea Fable captured is the right way to make that pairing routine.

## Context delta
- **needed-not-pointed:** that the design spec had no timeline at all (the "how long?" gap); that the
  memory-system finalization is the *K0 gate*, not a secondary Opus track (owner had to surface this).
- **discovered-by-hand:** the live velocity numbers (41-PR peak day, ~16 parallel lanes, 37/60 substantive)
  — computable from `git log`, hence the session idea; the substrate-kit's real state (declaration/
  bootstrap layer + 117 tests + a 147KB single-file `dist/bootstrap.py`; nervous system still absent).

## 📤 Run report
- **Did:** synced to main · reviewed Fable's design spec (verified-solid) · wrote the parallel-execution
  plan · elevated the substrate-kit finalization to the real new-repo gate (Fable prompt B). **Outcome:** shipped.
- **Run type:** `manual` (owner-directed, interactive).
- **⚑ Owner decisions needed:** none new — the two pre-gate Fable missions (§F linchpin proof, §B finalise
  the memory system) are buildable now without a gate; the design-approval gate remains the owner's call.
- **↪ Next:** run the two pre-gate Fable missions in parallel (§B memory system = the higher-priority
  start-gate; §F linchpin proof = the commit-gate).

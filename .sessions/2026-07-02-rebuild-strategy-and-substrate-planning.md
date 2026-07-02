# 2026-07-02 — Rebuild strategy + substrate-kit planning (interactive, owner-directed)

> **Status:** `complete` — planning session **plus an in-session follow-up wave**: verified the 4 Codex
> rebuild-discovery maps against shipped source (Q-0120) and folded them into one synthesis, and fixed
> #1634's masked plan-homing CI failure. Original planning: Fable 5 re-introduction context; Max ×20,
> weekly limits fresh; planning docs + ultracode launch pad captured; the 2-wide `rebuild-harvest` is
> superseded by the Codex maps (handoff §5/§6); **no code shipped to `disbot/`.**

## Follow-up wave (2026-07-02) — Codex maps verified + folded; #1634 CI fixed
- **#1634 CI, two masked failures fixed in sequence:** (1) `check_docs` — an invalid `analysis` badge +
  an orphan handoff doc (fixed: badge→`plan`, linked the handoff); this short-circuited the job in 7 s,
  which **hid** (2) `test_check_plan_homing` — the 3 new `docs/planning/*` plans were unhomed (fixed: a
  dedicated cross-cutting subsection in `docs/planning/README.md`). **Lesson (durable):** for planning-doc
  changes run `check_quality --full`, not just `check_docs` — the homing test lives in pytest, not check_docs.
- **The 4 Codex PRs (#1630–#1633) actually PASSED CI** (correctly `historical`-badged, no session card) —
  they were unmerged only because `auto-merge-enabler` arms `claude/*`, not `codex/*` (`enable-auto-merge`
  skipped). Not a CI failure as assumed.
- **Verify-and-fold workflow** (`codex-rebuild-map-verify-and-fold`, 5 agents, 0 err): checked 59
  load-bearing claims against source → **48 CONFIRMED / 2 FALSE / 9 PARTIAL**. Folded into
  `docs/analysis/rebuild-discovery/codex-preserve-map-synthesis-2026-07-02.md` (+ the 4 raw maps preserved
  verbatim). **Key catches:** `ActionSpec` hard-collides with the shipped `automation_registry.py:35` (design
  must rename repo-wide); `BindingSpec`/`LifecycleResult`/`CapabilityDecision` are **already shipped** (extend,
  don't recreate); `multi_channel.py` doesn't exist; several command tokens (`servermanagement`, not `!server`)
  and module paths (`ai_review.py`, not `ai_review_log.py`) corrected. The map now feeds the Fable prompt (D).
- **#1630–#1633 superseded** (closed) — their reports live in #1634 + the synthesis; their stale
  `dashboard.json` deltas were dropped (would clobber main's newer data).

## What this session did
Started as a prompt-review request for a substrate-kit *finalization* pass; evolved (owner-directed) into
the trustworthy foundation + plan-of-plans for a **from-scratch SuperBot rebuild**, with the substrate-kit
finished first as its foundation.

1. **Reviewed + improved the substrate-kit finalization prompt** (chat) — flagged the stale "You are Fable 5"
   framing, the missing born-red/PR workflow, over-prescription vs. Fable prompting guidance, and the
   re-plan-vs-execute fork; delivered model-agnostic, reasoning-forward rewrites.
2. **Fable 5 research (verified live):** launched 2026-06-09, withdrawn 2026-06-12, **redeployed 2026-07-01**
   — clears the vision doc's open gate. Capabilities in strategy §0.
3. **7-agent verification fleet** → the verified baseline (settings · substrate-kit real state · router ·
   test-oracle viability · binding-doc rot · arch debt · memory-improvement harvest). Corrected drifted figures.
4. **Wrote** `docs/planning/fresh-rebuild-strategy-2026-07-02.md` — verified baseline + plan-of-plans +
   design principles + memory-package improvements.
5. **Integrated two external GPT streams** (UI/command grammar; control-plane/CI), verified against source
   (Q-0120) — caught the `ActionSpec` collision + the false "no PR/issue templates" and "hundreds of stale
   branches" claims. → strategy §6.
6. **End-to-end execution order + model/ultracode allocation** (Phase 0→5 with gates) → strategy §3/§3.1.
7. **Launched the `rebuild-harvest` ultracode** (Phase 1) — read-only mapping fleet → 4 design-input artifacts.
8. **Captured the simulation-driven-design rule** (owner-directed) → `docs/planning/simulation-driven-design-2026-07-02.md`
   + strategy §4.

## Key decisions / verdicts (durable)
- The rebuild is the owner's goal; the substrate-kit finishes first as its foundation + clean-doc generator.
- The existing 11,510-test suite **cannot** be the rebuild oracle (white-box) → build a **black-box golden
  harness against the live bot BEFORE any freeze** (Phase 0.5). *(Corrected earlier advice.)*
- The real bot debt is a **missing command/symbol namespace** (2 boot crash-loops in 3 days) + god-functions
  + lazy-import-hidden coupling — **not** the 49 managed arch warnings.
- The settings / UI / control-plane rebuild = **"make the good pattern authoritative + generated from one
  source,"** not greenfield — three independent audits converged on this.
- **Simulation-driven design** is a standing rule; the manifest grammar must be designed to be simulated over.
- Model strategy: **Fable where reasoning is the bottleneck** (the design); Opus/Sonnet fleets for parallel
  throughput. Limits are not the constraint — **wall-clock is** (a Fable fleet clears fewer items/hour).

## ⚑ Self-initiated (flag for review)
- Created `fresh-rebuild-strategy-2026-07-02.md` (analysis) and `simulation-driven-design-2026-07-02.md`
  (owner-directed rule) — docs only, no code.
- Launched the `rebuild-harvest` ultracode (read-only mapping; writes design docs under
  `docs/planning/rebuild-harvest/`).
- Fixed stale Fable-availability status in `superbot-fresh-rebuild-vision-2026-06-30.md` (fix-on-sight drift).
- **Owner-directed** (not unilateral): verified + folded the 4 Codex maps into one synthesis and **closed
  PRs #1630–#1633 as superseded** (their reports preserved verbatim in #1634). Flagged here for the record.

## 💡 Session idea
Simulation-driven design as a first-class, gated design step (owner-originated; captured, generalized,
manifest-synergy + guardrails added). Plus three portable-kit capabilities synthesized from the
verification: the namespace-guard checker, the golden-harness pattern, and the seam-authority check.

## Context-delta
- **needed-not-pointed:** the true substrate-kit completion (~45–55%, docs said ~60%); the test suite's
  white-box nature (nothing flags it as oracle-unusable); the `ActionSpec` name-collision; that docs
  describe Fable's *designed* state, not live availability; the CodeGraph "fan-out 210" being a lazy-import
  artifact.
- **pointed-not-needed:** the router "60% unclassified / 11 open" framing (artifact of 4 status formats;
  ~0 actually open); the "956 application files" figure (does not reconcile — 879); the "essential_setup
  fan-out ~210" hotspot.
- **discovered-by-hand:** the settings two-layer + AI-fork structure + 40 raw-KV bypasses; the 10,036
  Q-citations; the empty router archive; the file-ordering sim engine already existing (CodeGraph drift 48%);
  ultracode concurrency = `min(16, cpu_cores−2)`, core-bound (this container = 4 cores → 2; a **fresh**
  ultracode session provisions a high-core container → 16, owner-confirmed + official-docs-verified);
  `scripts/extract_video_frames.py` is the repo's tool for viewing uploaded videos (bundled imageio-ffmpeg).

## Open threads
- Harvest ultracode completes → commit its 4 artifacts, then fire the Phase 0 + Phase 0.5 ultracodes, then
  the **Fable design ultracode** (Phase 2 — clean Fable-usage measurement run).
- Codex parallel stream (functionality inventory + hidden-dep map) → diff against the harvest, keep the union.
- Owner decisions pending: backward-compat contract · manifest format · control-plane hardening scope ·
  rebuild go/no-go (post-design).

## ⟲ Previous-session review
Prior work (band-#1620 reconciliation + the fresh-rebuild vision capture #1589/#1590) did well to capture
the rebuild reasoning durably, but left the Fable-availability status as a point-in-time snapshot that went
stale within 2 days — reinforcing this session's lesson: **docs describe designed state; live status must be
re-verified, not inherited.** System improvement surfaced: a periodic "live-status re-verify" nudge for any
doc line asserting an external product's availability (candidate journal rule).

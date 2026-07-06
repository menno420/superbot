# Phase-2.5 cold-start A/B — the runnable procedure (companion D of the canonical plan, 2026-07-06)

> **Status:** `plan` — companion to
> [`rebuild-canonical-plan-2026-07-06.md`](rebuild-canonical-plan-2026-07-06.md) §7 / gate **G2**.
> Turns the substrate-on/off cold-start A/B from "specced but never run" into a procedure an agent
> session can execute **today** (after the one prerequisite below). Prior spec surface was thin —
> environment ("a small throwaway repo"), models ("Sonnet runs, Opus interprets"), purpose ("the
> portability claim's test") — with **no** measures, pass bar, arm protocol, run count, artifact
> home, or operational definition of "cold" anywhere (verified by exhaustive grep, lane 1,
> 2026-07-06). This doc fills exactly those gaps. Pass bar + verdict acceptance are canonical-plan
> flag **F-5** (decided + flagged, not open).

## 0. Why this gates Phase 3

The substrate-kit is the first thing K0 does in the new repo. The kit is *finished* (#1649;
422/422 tests; one-step adopt re-proven live this session) but has **never been tested from a true
cold start** — every session that ever used it ran inside this repo's warm context. The A/B is
the one experiment that validates the portability thesis before a ~100-PR commitment rides on it
(strategy §5.2.1). It is **offline, throwaway, and cannot touch production anything.**

## 1. Prerequisite (one small PR)

**Kit tail ① (Q-0223):** make `JsonStateBackend.transaction` re-entrant and wrap
`apply_review_verdict`'s multi-write fail path in one transaction — verified still unshipped
(`substrate-kit/src/engine/lib/state.py:102-124`, `loop/review_seam.py:149-193`). The owner named
this the kit's one real correctness bug; the A/B's numbers are untrustworthy while state writes
can interleave (BUILD-PLAN prerequisite I-13). *(Tail ② extraction-proof CI and ③
extraction/rename are owner-paced and do NOT block the A/B.)*

## 2. Environment — what "cold" means, operationally

- **Target:** a **local throwaway git repo** (no GitHub project needed — `dist/bootstrap.py adopt`
  is proven on a bare directory). One seed commit: a ~200-line Python toy project (a small CLI
  with 2–3 modules + a failing-ish test suite) committed identically for both arms. The seed is
  written once, by the runner session, *before* any arm runs, and never edited between arms.
- **Cold =** each measured session starts in a **fresh container** with: no prior conversation, no
  memory of the seed repo, no `CLAUDE.md` beyond what the arm provides, no `.sessions/` history,
  and no access to the superbot repo. The session sees only the throwaway repo + the task prompt.
- **ON arm:** the seed repo after `python3 dist/bootstrap.py adopt` (+ `--include-claude` so the
  staged `CLAUDE.md`/skills are live) in **guided** mode — guided is the mode a genuinely new
  adopter would run; observe is too passive to differ from OFF, active over-claims maturity.
- **OFF arm:** the identical seed repo, no kit, no docs beyond the seed's own README.
- **Models:** the **same model both arms** — Sonnet 5 (strategy §3.1) — so the kit is the only
  variable. **Opus (or Fable) judges.**

## 3. Protocol

1. **Task corpus — 4 fixed tasks**, authored before any run, identical across arms, each sized
   ~20–40 min and chosen to exercise what the kit claims to improve:
   T1 *orient-and-fix* (find + fix a seeded bug; does the session orient efficiently?) ·
   T2 *build-a-feature* (add a small feature + tests; does it follow/record conventions?) ·
   T3 *make-a-decision* (a task with a genuine design fork; does it record the decision durably?) ·
   T4 *resume-cold* (continue T2 in a NEW cold session; does anything persist to help it?).
2. **N ≥ 3 paired runs per task** where budget allows; minimum viable = 1 pair per task
   (4 ON + 4 OFF sessions), which already beats the current evidence (zero runs). Run order
   alternates ON/OFF-first per task to kill ordering drift.
3. Each session gets the same prompt template: the task + "work as you normally would; end by
   summarizing what you did and what the next session should know."
4. The runner captures per session: full transcript · token/word counts of everything read before
   the first productive action · the repo diff · kit gauges where ON (`bootstrap metrics`,
   `economy check`, session-close output).

## 4. Measures (three primary + supporting)

| # | Measure | How measured | Kit surface used |
|---|---|---|---|
| M1 | **Orientation footprint** — words consumed before first productive action, and whether the ON arm stays inside the **≤7,000-word orientation budget** | transcript accounting; ON arm cross-checked against the kit's economy gauge | economy gauges (`bootstrap economy check`) |
| M2 | **Wrong-turn / steering count** — wrong-direction episodes, re-derivations of established facts, convention violations (e.g. T4 failing to find T2's context) | judge-scored from transcripts against a written rubric | — (both arms) |
| M3 | **Workflow correctness + task completion** — task done to spec · decisions durably recorded (T3) · next-session handoff exists and works (T4) · session ends cleanly | judge-scored, binary-per-item checklist | kit KPIs (completeness, assumption-confirmation) on ON |
| S | Supporting: wall-clock/turn count · test-suite state at end · ON-arm `check --strict` clean | runner logs | — |

**Judging:** Opus/Fable scores every transcript against the written rubric with arm labels
stripped from the transcript body where feasible (the kit's artifacts are self-identifying, so
blinding is partial — the judge is instructed to score *behavior*, not artifact presence).

## 5. Pass bar (canonical flag F-5 — owner vetoes or blesses)

**PASS =** the ON arm beats OFF on **≥2 of M1/M2/M3 with none regressing**, AND the ON arm's
**first session boots inside the ≤7,000-word orientation budget** with **zero unrecoverable
workflow errors** (a kit-caused dead-end the session cannot recover from = automatic FAIL).

**Tie/ambiguous:** run one more paired task. Still ambiguous → the verdict is recorded honestly as
**"no measurable cold-start benefit"** — itself gate-relevant evidence (the kit keeps its
checker/guard value regardless; the *portability claim* just loses its headline). The gate then
becomes an explicit owner judgment call at G1 rather than a measured pass.

**Who accepts:** agents run the whole thing; **the owner accepts the verdict** at (or before) the
G1 sitting — reconciling the strategy's "agent-buildable, no owner gate" with Gate-V O-8's
"owner-run" (the *run* is agents'; the *acceptance* is the owner's).

## 6. Artifact

One report: **`docs/planning/phase-2.5-cold-start-report-<date>.md`** — per-session metric table ·
per-task pair verdicts · judge rationale quotes · the overall PASS/FAIL against §5 · limitations
(N, partial blinding) · the raw transcripts' storage location. Homed in `docs/planning/README.md`
next to this procedure; the canonical plan's §4 G2 row flips state on its merge, and the S3 sector
queue drops the "never run" marker.

## 7. Cost/time envelope

8–12 Sonnet sessions (~20–40 min each) + one judge pass + the runner session ≈ **one agent-day**.
No production access, no owner time until verdict acceptance. Highest-leverage single step in the
program (canonical plan §5 step 2).

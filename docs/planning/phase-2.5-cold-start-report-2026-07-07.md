# Phase-2.5 cold-start A/B — report + verdict (2026-07-07)

> **Status:** `audit` — the gate-**G2** evidence artifact. Executed per
> [`rebuild-phase-2.5-procedure-2026-07-06.md`](rebuild-phase-2.5-procedure-2026-07-06.md)
> (companion D of the [canonical plan](rebuild-canonical-plan-2026-07-06.md)); pass bar = canonical
> flag **F-5**. Run by agents in PR #1775; **the owner accepts or overrides this verdict at the G1
> sitting.** Raw arm repos + transcripts + judge output preserved in the session scratchpad
> (ephemeral); everything decision-relevant is in this file.

## 0. Verdict, up front

**FAIL against the F-5 pass bar, as tested — a null-to-slightly-negative result with a precise,
fixable cause.** The substrate-ON arm beat OFF on **0 of 3** primary measures (bar: ≥2, none
regressing): orientation footprint **regressed** in 3 of 4 task pairs, the judge scored ON's
wasted-motion (M2) **worse** in 3 of 4 pairs, and workflow-correctness/completion (M3) **tied**
(all 8 sessions completed their tasks to scripted ground truth).

**The cause is specific, and it is the experiment's real finding:** `dist/bootstrap.py adopt`
ships the kit **inert** — CONSTITUTION.md, `.claude/CLAUDE.md`, `docs/current-state.md`,
`docs/decisions.md`, AGENT_ORIENTATION.md all land as **unrendered `${...}` templates**, and the
staged hooks reference paths outside the target repo. A task-focused cold session (correctly)
recognizes them as non-actionable, pays the reading cost, and proceeds on source. An inert kit
cannot demonstrate orientation/ledger/continuity value; it can only cost. It did.

**What this does NOT show:** that the kit's mechanisms are worthless. Not one ON session was
*misled* by the broken scaffolding (the judge credits all four with correctly distrusting it), and
the kit's checkers/engine were never engaged because no session ran the interview/render loop.
The claim that failed is exactly the one Phase 2.5 existed to test: **"adopt-and-go works cold."**
It does not, as shipped.

## 1. Protocol as run (deltas from companion D noted)

- **Seed:** a ~200-line `spendlog` expense-tracker CLI (3 modules + 6 passing tests + one seeded,
  untested case-sensitivity bug), committed identically to all arm repos.
- **Arms:** ON = seed + `python3.10 dist/bootstrap.py adopt --include-claude` (the kit at head,
  **including the tail-① fix** shipped this PR); OFF = bare seed. 4 tasks × both arms = **8
  sessions**, same model (Sonnet), identical prompts, each confined to its arm dir with no session
  history. T4 ran on each arm's own post-T2 state (the continuity probe).
- **Tasks:** T1 orient-and-fix (symptom → root cause) · T2 build-a-feature (monthly report) ·
  T3 make-a-decision (always-on persistence, design fork) · T4 resume-cold (continue T2's work,
  "follow conventions you find").
- **Measures:** M1 = words of tool output consumed before the first mutating action (scripted from
  transcripts) · M2 = wasted motion / re-derivation (judge) · M3 = completion + quality +
  durable recording + clean ending (scripted ground truth + judge). Judge = an independent
  Opus session scoring behavior against a written rubric, instructed to ignore artifact presence.
- **Deltas from the procedure:** N = 1 pair per task (the procedure's minimum-viable), "fresh
  container" approximated by fresh agent *contexts* in one container (both arms saw identical
  harness-level context leakage — noted by sessions in both arms), and blinding was partial
  (kit artifacts are self-identifying in diffs).

## 2. Results

**Scripted ground truth (M3-completion): tie — every session shipped.** All 8 test suites green
(8/8 · 16/18 counts vary by arm · 13/14 · 32/33); the T1 bug e2e-fixed in both arms; T3 no-flag
persistence works in both (both arms independently chose the identical XDG design); T4 budgets +
over-budget flagging work e2e in both.

**M1 — orientation footprint (words in before first mutation, ON vs OFF):**

| Task | ON | OFF | Direction |
|---|---|---|---|
| T1 | 672 | 738 | ON marginally better |
| T2 | 1,070 | 749 | **OFF better (1.4×)** |
| T3 | 1,317 | 749 | **OFF better (1.8×)** |
| T4 | 3,125 | 1,519 | **OFF better (2.1×)** |

Both arms stayed far inside the ≤7,000-word budget (the toy repo is small); the *relative* signal
is what counts: the kit's planted files added reading load, growing with session complexity.

**M2/M3 — judge verdict (per pair):** T1 tie/tie · T2 **OFF/OFF** · T3 **OFF**/tie · T4 **OFF**/tie.
The one M3 non-tie (T2) was an OFF engineering win on its own merits (proper argparse month
validation vs ON accepting `2026-13` silently and crashing on malformed input) — the judge
explicitly does not attribute it to the substrate. Judge's bottom line, verbatim: *"as-tested this
is a null-to-slightly-negative result — the substrate as deployed added latency without benefit —
and any real evaluation must first render/fill the templates."*

**The two damning behavioral details:** despite a purpose-built `docs/decisions.md` ledger sitting
in its repo, ON-T3 recorded its design decision in README + commit message — **exactly like OFF**;
and no ON session wrote a session log or current-state entry, so T4-continuity was identical
across arms (commit + README carried the handoff in all eight sessions).

## 3. What this means for the gate (G2) — decided and flagged

1. **The "adopt-and-go" cold-start claim is refuted as shipped.** Recorded honestly per the
   procedure's own rule: a null result is gate-relevant evidence. G2 is hereby **run** — the gate's
   evidence exists — but it is **not a green light**.
2. **The fix is small and known:** `adopt` must plant *rendered* minimal docs, not raw templates —
   it can know the project name, detect the verify command, and stamp the rest with a loud
   "UNRENDERED — run `bootstrap ask`" banner instead of silent `${...}` placeholders; and the
   staged hook paths must resolve inside the target repo. (The kit's interview/render machinery
   already exists; this is plumbing the adopt entry point through it.)
3. **Recommended ruling (for the owner at G1):** treat G2 as **"fail → fix → re-run one pair."**
   Land the adopt-renders-what-it-knows fix as a small kit PR, then re-run a single paired task
   (T4-style, the strongest differential) to confirm the overhead flips. Only then does the K0
   bootstrap step keep its "first act of the new repo" role with evidence behind it. The
   alternative ruling — accept the kit as an *invested-adoption* tool (its value contingent on
   running the interview, which the real K0 session would do) and green-light on that basis — is
   defensible but unverified; recommend against green-lighting on an untested claim twice.
4. **Limitations,** honestly: N=1 per task; one model; a toy repo far smaller than a real target;
   fresh-context ≈ fresh-container; partial blinding; and the ON arm's *checker/guard* value (the
   kit's second half) was never exercised by these task shapes.

## 4. Bookkeeping

Canonical-plan updates riding this report: §4's G2 row → **run, verdict FAIL-as-tested (fix +
re-run recommended)**; §5 step 2 → points here. The kit tail-① fix (Q-0223) shipped in the same
PR (#1775), so the pre-bootstrap gate's *code* remainder is closed regardless of the A/B outcome.

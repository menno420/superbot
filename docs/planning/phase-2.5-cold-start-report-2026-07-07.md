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

---

## 5. Re-run addendum (2026-07-07, final-review session #1778) — the §3.3 ruling executed

§3's recommended ruling ("fix adopt-renders-what-it-knows → re-run one pair") was executed the
same day, under Q-0241 (agents run **and accept** the verdict; flagged ⚑ for owner review).

**The fix, as shipped (session #1778):** `adopt` now derives every deterministically-knowable slot
(project name, language incl. `requires-python`, verify command, docs root) and records each as a
*provisional* interview answer before rendering — so planted docs open readable; docs still
carrying unfilled `${...}` slots get a **loud UNRENDERED banner** naming the two commands that
fill them (`render --live` strips it once a file fully renders); and adopt **vendors the
single-file `bootstrap.py` into the target root**, fixing the staged-hook-paths failure. 432/432
kit tests; re-proven live cold (adopt → `check --strict` clean).

**Protocol:** fresh seed (same shape: ~130-line spendlog CLI + 6 tests), fixed-kit adopt on ON,
T2 (build monthly report) then T4 (resume-cold: budgets + over-budget flags) per arm, same model
(Sonnet), identical prompts, fresh contexts confined to arm dirs. M1 scripted from transcripts
(same definition); independent Opus judge for M2/M3, instructed to score behavior and ignore
artifact presence. Deltas honestly noted: N=1 per task; **both ON sessions failed to end cleanly
(T2-ON never committed — the runner committed its completed work so T4 could run; T4-ON left its
work uncommitted in the tree)** while both OFF sessions committed cleanly.

**Results:**

| Measure | T2 ON | T2 OFF | T4 ON | T4 OFF |
|---|---|---|---|---|
| M1 words-before-first-mutation | **1,700** | 549 | **3,106** | 952 |
| M3 completion (scripted) | ✓ (27 tests) | ✓ (25 tests) | ✓ | ✓ |

**Verdict (judge, quoted): FAIL — a negative result.** "Against the pass bar, ON beats OFF on
**0 of 3, and regresses on 2 (M1 and M3)**. … The substrate arm did not merely fail to help — it
underperformed the bare arm on exactly the dimensions the substrate exists to improve. ON read 3×
more tool output before acting, yet wrote to **none** of its decision-ledger, session-log,
current-state, or journal surfaces across two tasks … Mere presence of the adopted kit earned
nothing behaviorally: its recording and handoff machinery sat unused while its orientation cost
was fully paid."

**What the re-run adds over the original FAIL — the cause moved:** the original failure was
*inertness* (raw templates, correctly ignored). The fix removed inertness — and the sessions then
**read** the docs (M1 rose from 1.4–2.1× to 3.1–3.3× OFF) while **still writing nothing back**
(kit surfaces byte-identical to the adopt commit; `.substrate/state.json` still `session_count: 0`).
So the refuted claim is now sharper: **readable orientation docs are a cost without mechanized
write-back** — discipline-dependent recording does not happen in task-focused cold sessions,
twice-measured.

**Ruling (decided + flagged ⚑, Q-0241):**
1. **The mechanical fix stands on its own merits** — vendored hooks, rendered docs, cold
   `check --strict` green are prerequisites for any real adoption and are not retracted by the
   benefit verdict.
2. **The K0 bootstrap step keeps its "first act of the new repo" role on *invested-adoption*
   grounds only** (the real K0 session runs the interview and lives in the repo for hundreds of
   sessions — the regime these 20-minute task probes cannot measure), **with the unproven-benefit
   caveat carried in the canonical plan §5 step 2**. Green-lighting on a measured cold-start
   *benefit* is now off the table — it failed twice.
3. **The next experiment is not another A/B of the same shape** — it is the
   [auto-drafted-handoff idea](../ideas/substrate-kit-auto-drafted-handoff-2026-07-07.md):
   mechanize write-back (session-close drafts the card from git diff + test state), then re-run a
   T4-style pair to test whether continuity finally moves. The kit's checker/guard half remains
   untested by these task shapes (unchanged limitation).

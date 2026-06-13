# Session (cont.) — substrate-kit PR 2 §3c skills + a parallel-collision cleanup

> **Status:** `reference` — continuation of the substrate-kit plan. Shipped **§3c skills (#811)**;
> dispositioned a parallel-agent collision (closed #807 + #809) per the just-merged Q-0124/Q-0125.
> Resume = §3c personas.

## What this increment did

**§3c skills (#811).** `engine/skills/skills.py`: the 7-skill starter pack (session-close ·
quality-gate · review · repo-health · deep-research + new question · analysis), each declaring the
capabilities it needs beyond read; bodies carry `${slot}` refs so a skill is project-aware. The
**precedence model** `action_permitted(stance, action, skill)` — a skill's declared capability
overrides the ambient stance (the §3c headline rule), test-pinned. Native emission via
`skill_document` (metadata-first frontmatter) + a `skills` CLI (list / `--build` into staging).
**Root-fixed a `build_bootstrap` bug**: a multi-line `from engine…` import leaked into the generated
single file (IndentationError) — `_split_imports` now drops such imports whole. Kit suite 77 → 91;
`--full` green.

**The collision cleanup.** While my PRs sat behind a ~30-min GitHub Actions dispatch outage, a
parallel session merged **#810** (Q-0124: a manual session doesn't run reconciliation — pursue the
work you were started for; Q-0125: disposition stale/redundant open PRs), touching the same recon
files my #807 had. Per those directives I **closed #807** (recon fix — superseded by #810; its
marker-code delta went marginal once manual sessions ignore the banner) and **re-cut #809 → #811**
skills-only off fresh `main` (it had been branched off #807, carrying the superseded recon commit).
Net: a clean, focused skills PR; no orphaned/conflicted PRs left open.

## 💡 Session idea (Q-0089)

**Don't branch a PR off another unmerged PR's branch — the tangle tax.** This session's mess traced
to one root cause: I cut #809 (skills) off #807's (recon) branch, so #809 inherited #807's commits;
when #807 got superseded by a parallel merge, #809 was tangled and had to be re-cut. **Proposal:** add
a one-line orientation rule (journal Quick-ref + the `/session-close` guidance) — *"a session's PRs
each branch off `origin/main`, never off a sibling unmerged PR branch; if work B depends on unmerged
work A, say so and wait for A to merge, or accept B will carry A."* Cheap, prevents a whole class of
parallel-collision entanglement. (Dedup-checked `docs/ideas/` — the existing parallel-lane guidance
covers *exclusion lists*, not *branch-base discipline*; this is the missing complement.)

## ⟲ Previous-increment review (Q-0102)

Reviewing **#807 (the recon fix), now closed.** *Did well:* it root-caused a real false-positive
(local vs `origin/main` marker) and was correct + tested. *What went wrong:* it was **redundant
effort** — a parallel session (#810) was solving the same owner concern from the policy angle at the
same time, and merged first. Neither of us saw the other coming. **System improvement (the real
lesson):** the owner's "always watch the PRs that merged" + Q-0125's "check open-PR *health*" only
catch *merged/open* collisions — they don't catch **two in-flight branches solving the same thing**.
A lightweight **active-work signal** (e.g. a one-line `WIP:` note in `current-state` ▶, or an
`in-progress` label naming the concern) would let a second agent see "someone's on the recon-awareness
thread" before duplicating it. This is the same gap the substrate-kit's own §3b project-state signal
solves for *tasks*; the *workflow* still lacks it for *concurrent agents* — routed as the session idea
above's cousin (branch-base discipline reduces the *cost* of collision; an active-work signal reduces
its *frequency*).

## Doc audit (Q-0104)

- `check_quality --full` green; `check_architecture --mode strict` 0 errors; `check_docs --strict`
  green; recon correctly **not due** (synced; main marker #800).
- Plan Execution log: skills DONE (#811) → repoint to personas; roadmap's two substrate mentions
  advanced to #811; the stale roadmap "Now" row ("1b tail → PR 2") corrected.
- **#807 + #809 closed** with explanatory comments (Q-0125 disposition) — no rotting open PRs.
- **current-state.md untouched** — subtree work tracked in the plan (the #789/#791–793 precedent).
- Honored **Q-0124**: did not run the reconciliation pass (the routine did it as #803/#810); pursued
  the substrate work I was started for.

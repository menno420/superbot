# 2026-07-07 — Kit-lab founding plan (program session 2/3)

> **Status:** `complete`
> **Branch:** `claude/kit-lab-founding-brief-5pj1ao` · **Model:** Fable 5 / ultracode · **Governance:** Q-0241 never-wait, decide-and-flag

## What happened

Executed [`docs/planning/kit-lab-repo-founding-brief-2026-07-07.md`](../docs/planning/kit-lab-repo-founding-brief-2026-07-07.md)
(program session 2 of 4, Q-0252): a 7-lane ultracode research fan-out (+ completeness critic +
8 gap-fills; 16 agents, ~1.7M tokens) over the substrate-kit source, the program docs, the
Phase-2.5 evidence, the routine fleet, and the shipped console shell (PR #1802 head) → the
**executable founding plan**
[`docs/planning/kit-lab-founding-plan-2026-07-07.md`](../docs/planning/kit-lab-founding-plan-2026-07-07.md):

- **Release discipline** (§4): semver `v1.0.0` at extraction; GitHub Releases with pinned
  `bootstrap.py` + sha256 + `release.json`; the new `upgrade` verb (dist archived *before*
  overwrite → 3-way planted-doc diff → `--apply-docs` only on untouched docs → state
  backup/rollback).
- **Benchmark suite to runnable depth** (§5): B1 cold-start A/B standing routine (post-auto-draft
  shape, T5 break-a-rule task, enforcement arms; rubric/tasks/seeds pinned outside the loop's
  write reach); B2 Q-0248 model-allocation dataset (the console's declared contract as the schema
  of record; JSONL per repo; mechanized writer); B3 guard-fire/false-positive telemetry (JSONL at
  the kit's two choke points + reasons-required allowlist port + did_not_run records); B4
  ideas-that-ship-and-survive (frontmatter convention + revert scan; "worked around" honestly
  punted to judgment).
- **The lab loop** (§6): ONE daily fresh-session routine, 9-part house prompt skeleton,
  Q-0241-shaped rails, warm-session-never-grades separation, enumerated destructive tier.
- **Work surfaces** (§7): console-first (adopts session 1's shell + fills its declared lanes),
  Railway project at extraction, bot token 👤-deferred; full provisioning checklist P1–P9.
- **Governance home** (§8): kit-repo `docs/program/` PL-register (PL-001…008 founding census),
  cite-never-copy sync rule + its checker.
- **Friction protocol** (§9): reflection-record payload over `friction`-labeled kit-repo issues
  inbound; pull-model upgrades outbound (the lab holds zero consumer credentials).
- **Build bands** KL-1…KL-6 (§10, ~12–14 PRs, named landings) + lab-v1 definition of done (§2.2,
  seven conditions D1–D7).

**Decisions:** 20 ⚑ rows (plan §12 D-1…D-20) + the 9-flag veto list (§1 KF-1…KF-9). Zero new
router Q-blocks — no genuine product fork; owner-input items are 👤 checklist lines that gate
only themselves.

**Review:** a 4-lens adversarial fleet (brief-coverage · source-truth · executability ·
governance) ran over the shipped plan; first launch died on the 5-hour usage limit (all 4 lanes,
opaque errors — see the session idea below), re-ran after the owner lifted it. Self-review
before the re-run caught 3 real defects (the §4.3 old-templates-destroyed-before-diff flow, the
§5.0 rubric creation-vs-modification deadlock, the KL-3 marker-tightening path); the fleet then
returned **26 confirmed findings — all folded**. The load-bearing ones: CODEOWNERS/required-
check/auto-merge are repo *settings* nobody provisioned (→ §3.2 item 7 + P10, two-layer pin,
honest advisory-until-P10 label); kit-repo **visibility** was the one unflagged assumption
(→ KF-10/P11: public at v1.0.0, veto fallback specced); the three-way template diff was dead on
arrival because adopt plants *rendered* docs (→ hash-based untouched-detection); the lab
couldn't read private consumer repos for its sweeps (→ KF-11/P13 read-only scopes); B4's
"worked around" judgment made the graded party the grader (→ D-23 non-loop grader, headline =
revert-scan only); appending benchmark rows tripped the plan's own append-only checker (→
append-aware rule); consumer session-close can't hot-fire routines (app tokens don't trigger —
→ §9.1 honesty + P12); B2's product plane got an explicit defer/ingest statement; D1 gained a
kickoff-ran-first ordering path. Decisions grew to D-24, flags to KF-11, provisioning to P13.

## Homes touched

Plan homed: `docs/planning/README.md` (rebuild table row) + `docs/current-state/S3-ai-memory.md`
(sector ledger entry) + launch-index row 2 annotated ✅ RAN. Grooming: the auto-drafted-handoff
idea annotated → SCHEDULED into KL-5. Idea filed: `usage-limit-aware-routines-2026-07-07.md`.

## Context delta (reflection interview)

- **Needed but not pointed to:** the shipped console-shell **contract strings** — the brief
  routes to the websites *brief*, but the load-bearing artifact was PR #1802's in-flight branch
  (`botsite/console/console.js` declared-lane contracts); had to fetch and read the sibling
  branch. Future founding briefs should say "read the sibling session's PR head, not just its
  brief."
- **Pointed to but didn't need:** the ideas-README index entry for the portable kit — the
  extraction plan + kit source were the real sources; the index entry added nothing.
- **Discovered by hand:** kit tests are **440**, not the brief's "432" (post-#1783 count); the
  guardrail's `examples/` carve-out points at a directory that doesn't exist; the kit has **no
  version marker anywhere** (the release-discipline gap was even bigger than the brief implied).
- **Decisions made alone:** the 20 ⚑ rows — all reversible-until-gate planning calls (Q-0240).
- **Flagged for maintainer:** the plan's §1 KF-1…KF-9 veto list; weakest point of what shipped =
  B2's `tokens_out` has no measurement path (KF-9 carries it honestly as null-tolerated).
- **One docs change that would have helped most:** a "sibling-session coordination" line in the
  launch index naming each session's PR/branch once opened (executed the cheap half: row 2 now
  carries PR #1804).
- **🛠 Friction → guard:** the usage-limit fleet death → captured as the
  `usage-limit-aware-routines` idea (prompt-clause + orchestration rule + telemetry counter);
  prompt/routine changes are owner-gated surfaces, so routed as an idea rather than shipped.

## ⟲ Previous-session review (Q-0102)

The band-#1800 reconciliation pass (#1803, incl. commit 18669ce) fixed the pre-existing
`check_plan_homing` red **on sight** mid-pass (Q-0166 done right — it unblocked CI for every PR,
including this one). What it could have done better: it homed the three program briefs in
`current-state/S3-ai-memory.md` only, not the planning README index — routing is now split
across two conventions, and this session had to guess which one `check_plan_homing` would
accept. **Concrete improvement:** pick one homing convention ("plan-index row always; sector
file optionally") and write it into `docs/planning/README.md` §"Homing a new plan" so the next
plan author doesn't re-derive it.

## 💡 Session idea (Q-0089)

[`usage-limit-aware-routines-2026-07-07.md`](../docs/ideas/usage-limit-aware-routines-2026-07-07.md) —
routines + orchestrations treat the usage-limit error as a distinct failure class and
self-reschedule at the reset time instead of dying silently; limit-killed lanes never count as
evidence. Observed live this session (4-lane review fleet returned an empty "success").

## 📤 Run report

- **Did:** produced the executable kit-lab founding plan (release discipline · 4 benchmark
  families · lab loop · provisioning · governance home · friction protocol · bands KL-1…KL-6) ·
  **Outcome:** shipped
- **Shipped:** #1804 — the founding plan + homing + grooming + session idea
- **Run type:** `manual` (owner-launched program session 2, Q-0252)
- **⚑ Owner decisions needed:** none blocking — the plan's §1 KF-1…KF-9 is the read-at-leisure
  veto list (Q-0241: silence = consent)
- **⚑ Owner manual steps:** none now; when the kit repo exists: P3 (create its Claude Code
  environment + env vars), P4 (arm the lab-loop routine), P7 (create the Discord app), P8
  (published name + LICENSE), P5 (Railway when convenient) — each gates only itself (plan §7.2)
- **⚑ Self-initiated:** none — owner-directed session (the session idea + grooming are the
  standing enders)
- **📊 Model:** Fable 5 · ultracode · idea/planning
- **↪ Next:** program session 3 (trading founding plan, its brief is paste-ready) or session 4
  (the kickoff, Opus-class — creates both repos; this plan travels with the kit repo). Nothing
  blocks either.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged | 1 (#1804, auto-merge on card flip) |
| CI-red rounds | 0 unexpected (born-red gate holds by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (usage-limit-aware routines) |
| Ideas groomed | 1 (auto-drafted-handoff → SCHEDULED into KL-5) |

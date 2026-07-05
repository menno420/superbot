# 2026-07-05 — CI-setup redesign (best-possible CI: current bot + fresh repo)

> **Status:** `in-progress` — born-red gate (Q-0133). Flip to `complete` as the deliberate final step
> once the deliverable is committed, rebased onto the auto-updated head, and the CI mirror is green.

## What this session did

The dedicated **CI-setup redesign** session the brief (#1736) primed. Owner-directed, ultracode. Goal:
the **best-possible CI** for (a) the current bot and (b) the future fresh-rebuild repo — and explicitly
**verify whether the fresh repo's CI should differ**, since the new repo's structure is ours to shape.

Ran an **18-agent ultracode workflow** (9 parallel inventory + web-research agents → a 3-angle design
panel → synthesis → 4 adversarial verifiers → finalize; 0 errors, ~1.66M tokens). Every load-bearing
claim was re-verified against source (Q-0120) — the adversarial pass caught and corrected two false
assumptions in the brief before they reached the design. Then authored the deliverable, shipped the one
guard I could make provably correct, and left the two AST guards as calibrated specs (a stub would be noise).

## Shipped (PR #1737)

- **[`docs/operations/ci-what-runs-where.md`](../docs/operations/ci-what-runs-where.md)** — the
  authoritative CI map (every workflow + `check_*.py` + hook → trigger, run-context, class, required?).
  Nothing captured this before; it's the CI half of the gate-state-readout idea.
- **[`docs/planning/ci-setup-redesign-2026-07-05.md`](../docs/planning/ci-setup-redesign-2026-07-05.md)**
  — the target-state design: one required `ci-gate` fan-in context; the CodeQL merge-protection ruleset
  (closes the Q-0238 race without a "pending-forever" deadlock) + a stuck-scan watchdog; ruff replaces
  black+isort; 17→14 workflows; the `check_ci_coverage` self-silencing fix; the fresh-repo divergence
  table; and a phased **reversible** migration split into **safe-additive (ships)** vs **owner-gated
  (proposed)**.
- **`scripts/check_workflow_concurrency.py`** (+ 8/8 unit tests) — deterministic guard for the
  cancellation-race invariant; flags `codeql.yml`'s current `cancel-in-progress: ${{ ... }}` (the A1 tell),
  passes `code-quality.yml`. Standalone/advisory (CI wiring is proposed).
- **Router:** Q-0238 updated with the superior option (C) merge-protection ruleset; new **Q-0239** carries
  the Phase-B owner decisions G2–G8.
- **Idea docs** for the two AST guards updated with precise signals + ground-truth calibration.
- **S5-ops** flipped to DELIVERED; **the brief** marked `historical`/EXECUTED.

## Key findings (corrections to the brief, all source-verified)

- **The repo is PUBLIC → Actions minutes are free/unlimited.** "Cost" = wall-clock latency + PR-check
  clutter + runner contention + merge-race hazard, **not** billed minutes. The brief's "cost = Actions
  minutes" framing is moot.
- **All app-CI is already `paths`-filtered** (dashboard/botsite/design-system/tool-pins) — the brief's "~8
  unfiltered workflows per push" cost story is stale.
- **No push+PR "double-fire"** — `code-quality` + `codeql` both trigger `push` on `main` only; the head
  run comes solely from `pull_request: synchronize` (which makes the dropped-`synchronize` watchdog *more*
  load-bearing, not less).
- **Merge queue is unavailable** (personal-account repo → no `merge_group`); it's the future org-move
  upgrade (Phase C).
- **`check_ci_coverage.py:53` is self-silencing** — it tests check-run *presence*, not required-context
  *satisfaction*, so a `workflow_dispatch` re-kick looks like success while the PR stays blocked.

## Should the fresh repo's CI differ? — Yes, deliberately

Converge on the **contract + shared artifacts** (aggregate `ci-gate`, ruff, `git merge-tree` +
auto-merge-on-green, the read-only `parity/` golden oracle, the substrate-kit template). Diverge on the
**grammar-integrity stack** the manifest-DSL makes possible (manifest-validate, sim-gate, a
Postgres-backed required golden-parity gate, compat-frozen, determinism/complexity AST fences, a
≤7,000-word orientation-budget gate) and the **control plane** (rulesets + OIDC from day one). Build it
**at the kernel (K10), not now**; **never** a live cross-repo `workflow_call` dependency. (§D of the design.)

## Context delta

- **Needed but not pointed to:** there was no single "what actually gates a merge" map — the design had to
  derive it. The new [what-runs-where doc](../docs/operations/ci-what-runs-where.md) now *is* it; link it
  from `AGENT_ORIENTATION` next time a CI task starts.
- **Decisions made alone:** none of substance. Every executable-config change is a **proposal** (router
  Q-0238 (C) + Q-0239 G2–G8) for owner ratification. The one thing shipped as code —
  `check_workflow_concurrency.py` — is a standalone advisory script (checker guards are free per the
  ownership split), not wired into any gate.
- **Flagged for maintainer:** the Phase-B migration is owner-gated; the recommended defaults are in the
  design §F and router Q-0239. Phase A is safe-additive and can be built by any session.

## 🛠 Friction → guard (Q-0194)

The friction this session was the **brief's unverified factual claims** (the cost framing + the
path-filter claim), which I had to correct against source. The durable guard: the
[what-runs-where map](../docs/operations/ci-what-runs-where.md) is now the *verified* CI source of truth,
and `check_workflow_concurrency.py` *enforces* one merge-race invariant that previously lived only in a
code comment. (Also observed: the black↔ruff trailing-comma churn on a new `scripts/` file — the existing
PostToolUse auto-fixer already covers this for Edit/Write; no new guard needed.)

## ⟲ Previous-session review (Q-0102)

Previous session = the **CI-setup brief** (#1736). **Strong:** it primed this session so it could start on
the *design* not the *discovery*, and it correctly used `AskUserQuestion` to lock the two aiming decisions
(scope, optimize-for) rather than guessing. **What it missed:** it asserted two load-bearing *facts* — "cost
= Actions minutes" and "~8 unfiltered workflows per push" — **without verifying them against source**, and
both were wrong (public repo → free minutes; all app-CI already path-filtered). A framing brief that hands
off factual claims should either verify them or tag them "unverified — confirm first." **System improvement
(initiated):** the born-red **brief → execution handoff** should carry a short *"verify these load-bearing
claims against source first"* line; this session did that instinctively (Q-0120) and it paid off twice.
Worth promoting into the brief-doc convention so the next brief author does it deliberately, not by luck.

## 💡 Session idea (Q-0089)

**One source of truth for the required-check topology.** This session hardcoded `MERGE_RELEVANT` in
`check_workflow_concurrency.py`, and `check_ci_coverage.py` separately hardcodes `REQUIRED_CHECK =
"code-quality"`, and the what-runs-where doc lists "required?" in prose — **three copies of the same fact
that will drift** (exactly the class Q-0120's #763 false-green was). Idea: a tiny
`ci_required_contexts.py` (or a `ci-topology.yml`) that names the required context(s) + the merge-relevant
workflow set **once**, consumed by both checkers and rendered into the doc — so the `code-quality`→`ci-gate`
swap (decision G2) is a one-line change in one place, not a scavenger hunt. Small, high-leverage, and it
makes the whole redesign's cutover safer. (Reinforces, not dups, the gate-state-readout idea.)

## 🧹 Grooming (Q-0015)

Moved the two CI-gap ideas down their lifecycle: `audit-seam-coverage-checker` and
`deferred-action-restart-recovery-checker` each gained a **precise build signal + ground-truth
calibration** (measured against real source: audit-seam's naive `*_mutation.py` scope is ~42% FP and
misses the real bug class → needs repo-wide per-function reachability; deferred-recovery's raw
`asyncio.sleep` is 23 files of mostly-FP → needs the `tasks.spawn`-target discriminator). They're now
turn-key for a focused follow-up, not vague ideas.

## 📋 Docs audit (Q-0104)

New `reference` map + `plan` design doc, both reachable (S5-ops → design → map; brief → design). Router
Q-0238 updated + Q-0239 added. Brief re-badged `historical`. `check_docs --strict` green;
`check_quality --check-only` green. No merged PR to ledger this session (own PR in flight — next
reconciliation folds #1737). The soft "Recently-shipped 22 > 20 ratchet" warning is pre-existing
(newest-merge lag), not introduced here.

## 📤 Run report

- **Did:** ran an 18-agent design+verify workflow; authored the what-runs-where map + the target-state
  redesign (design + reliability fixes + consolidation + fresh-repo divergence + phased migration);
  shipped `check_workflow_concurrency.py` (8/8 tests, ground-truth verified); updated the router
  (Q-0238 (C) + Q-0239), S5-ops, the brief, and the two guard idea docs. · **Outcome:** shipped
- **Shipped:** #1737 — 2 new docs · 1 new checker + test · router/ledger/idea-doc updates (no `disbot/`
  runtime change).
- **Run type:** `manual` (owner-directed, ultracode).
- **⚑ Owner decisions needed:** **router Q-0238 option (C)** (CodeQL merge-protection ruleset) + **Q-0239
  G2–G8** (the required-context swap, six workflow deletions, checker promotions, `settings.json` Stop-hook
  rewires, the branch-up-to-date toggle, the `check_doc_freshness` delete, the #794-class decision). Each
  has a recommended default. **Phase A ships without sign-off.**
- **⚑ Owner manual steps:** none this session (Phase-B config changes are the ratification above).
- **⚑ Self-initiated:** the whole redesign is owner-directed; within it, self-initiated & flagged: shipping
  `check_workflow_concurrency.py` (a new checker guard — free per the ownership split), the Q-0239 router
  proposals, and the two idea-doc calibrations.
- **↪ Next:** owner ratifies Q-0238 (C) + Q-0239; then a session executes **Phase A** (safe-additive:
  build `ci.yml`/`web-ci.yml`/`pr-freshness.yml` non-required alongside the old, fix `check_ci_coverage`,
  ruff migration, flip `codeql.yml` cancel:false) and, on parity, the ratified Phase-B cutover.

## 📊 Telemetry

| Metric | Value |
|---|---|
| Workflow agents | 18 (0 errors, ~1.66M tokens, ~38 min) |
| Docs shipped | 2 (1 `reference` map, 1 `plan` design) |
| New checkers shipped | 1 (`check_workflow_concurrency.py`, 8/8 tests) |
| Guards specced+calibrated (not stubbed) | 2 (audit-seam, deferred-recovery) |
| Owner decisions surfaced | 8 (Q-0238 (C) + Q-0239 G2–G8) |
| Brief facts corrected | 2 (cost=minutes; ~8 unfiltered/push) + 3 (double-fire, merge-queue, ci_coverage bug) |
| CI-red rounds | born-red hold only (intended) |
| New ideas contributed | 1 (single-source required-check topology) |
| Ideas groomed | 2 (both CI-gap checker ideas calibrated) |

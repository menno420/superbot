# Independent cross-repo review — the Projects-EAP fleet (2026-07-09)

> **Status:** `reference` — an independent review session's honest verdict over the four
> repos the Claude Code Projects (EAP) fleet has produced. **Not binding.** Source code and
> merged PRs win over this doc. Companion evidence: the
> [evaluation log](../planning/projects-eap-evaluation-log.md) ·
> [campaign self-audit](campaign-self-audit-2026-07-08.md) ·
> [permission-probe report](../planning/projects-eap-permission-probe-report-2026-07-08.md).
>
> **Method:** three discovery agents (one per new repo, GitHub-MCP read of PRs/diffs/CI/trees)
> **plus** a first-party verification pass — `superbot-next` was cloned and its test suite,
> manifest compiler, and checkers were run locally. Website *visual* quality is judged from
> source only (no render). Every count below is either first-party-verified (marked ✓) or
> cited to the repo/PR it came from.

## Verdict in one paragraph

The fleet's work is **genuinely good — good by ordinary engineering standards, not merely
"good for AI" — and, unusually, honest about its own gaps.** Four repos in a few days
produced real architectural depth, real and *passing* test suites, three deployed web
services, and a portable workflow kit with a tagged release. The failure mode everyone
fears from an autonomous fleet — confident overclaiming — is **not** what this review found;
the self-reviews repeatedly *correct their own numbers upward* and disclose what is not done.
There is one systematic weakness, reproducible across both fresh code repos (§4), and one
honesty caveat the owner should hold (impressive counts slightly overstate "done-ness",
disclosed honestly by the repos themselves). Grades: **substrate-kit A · superbot-next B+ ·
websites B+ product / C governance-transfer**, against the mature `superbot` baseline.

> **Update — 2026-07-09 evening (post-review, from the rebuild coordinator's own run):** the
> `superbot-next` "doesn't boot yet / 0 parity demonstrated" caveat (§3, §5) has **partly
> closed**. The coordinator built the CUT-1 composition root (superbot-next PR #54) and the bot
> now **boots to `RUNNING`** on a real test-bot token against real PostgreSQL — the step-1
> kernel-boot live smoke is **PASS** with verbatim evidence
> (`superbot-next/docs/status/testing-report-2026-07-09.md`): migrations 0001–0024 apply +
> checksum-verify on a fresh DB, gateway READY ~4 s, `/ready` 503→200 at RUNNING, the outbox
> delivered its audit canary, clean SIGTERM → exit 0, zero ERROR lines on a second run. **The
> first-ever live boot caught a real Postgres-only bug invisible to unit fakes** (a PREPARE-time
> `timestamptz`/`interval` type error in `reap_stuck_applying`, fixed in the same PR) — the
> "live-test is the gate, CI-green is not done" doctrine paying off on first contact. The
> coordinator also shipped a strong orchestration retrospective
> (`superbot-next/docs/status/rebuild-orchestration-retrospective-2026-07-09.md`): 49 PRs in
> ~14 h across 18 workers, **zero reverts**, every incident recovered from durable state, and a
> §6 "Projects model" opinion that **independently corroborates** this program's evaluation-log
> findings (no coordinator timer · 4 KB brief cap · no direct coordinator→child channel ·
> isolated containers → file-exchange-via-repos). **Net: `superbot-next` ticks from B+ toward
> A-** — its biggest caveat (no boot) is closed; what remains is subsystem steps 2–9 live + the
> 0/465 parity flips. The paragraph-level text below is the morning snapshot, preserved.

## 1. The four repos and their roles

| Repo | Role | Scale | Open PRs |
|---|---|---|---|
| [`superbot`](https://github.com/menno420/superbot) | mature production bot + program record/oracle | ~1,741 merged PRs, ~58 cogs | 1 (#1886, dependabot policy) |
| [`superbot-next`](https://github.com/menno420/superbot-next) | ground-up declarative rebuild | 50 merged PRs, 17 kernel + 37 domain subsystems | 0 |
| [`substrate-kit`](https://github.com/menno420/substrate-kit) | the portable "operating system" | 624 test fns, v1.0.0 release | 1 (#17, owner-blessing gate) |
| [`websites`](https://github.com/menno420/websites) | 3 deployed sites (control-plane/marketing/dashboard) | ~36 templates, ~55 tests | 1 (#16, born-red WIP) |

## 2. The explicit comparison — new repos vs. the mature baseline

**Structure — the new repos are materially more structured, by design.** `superbot` grew
organically to what its own docs call an "architectural ceiling" (the stated reason for the
rebuild). `superbot-next` front-loads what the old bot retrofitted in patches: a
manifest-driven declarative kernel, a clean 17-kernel / 37-domain split, 22 AST/architecture
checkers gating CI, and a born-red golden-parity harness split *honestly* into a green
required `gate` job and a red-by-design `report` job. That is more structural rigor than the
old repo ever had at rest.

**Efficiency — the velocity is the standout and it is real.** The fleet compressed into a few
days what the old repo accreted over a long history: 50 PRs of genuine subsystems in
`superbot-next`; three live Railway sites + a hand-built accessible design system in ~one
Fable-5 day in `websites`; a full portable kit with 624 tests and a signed v1.0.0 release in
`substrate-kit`. The decision discipline (ledgers, routers, per-band provenance) transferred
cleanly and is arguably *cleaner* in the fresh repos (no accreted cruft).

**Where the old baseline still wins — the "engaged" state.** `superbot`'s operating system is
not just present, it is *live and enforcing*: CI on `main`, a session card per PR, rendered
binding docs. That is exactly the half that did not fully reproduce in the fresh repos (§4).

## 3. Per-repo honest read

### substrate-kit — grade A (the strongest engineering artifact of the four)
A ~415 KB stdlib-only `dist/bootstrap.py` generated from a modular `src/engine/`, **624 test
functions across 40 files**, a single required `kit-quality` CI check (green on `main` and on
the open PR), and a tagged **v1.0.0 GitHub Release** with signed assets. The headline claim —
"one-step adopt" — is **proven on every PR, not asserted**: CI adopts the kit into a throwaday
repo and runs `check --strict` (plus the `--wire-enforcement` path). Source↔dist cannot drift
(CI rebuilds `bootstrap.py` from `src/` and fails on any `git diff`). Templates are properly
generalized (`${slot}` placeholders; the Q-0254 understand-and-reflect doctrine is graduated
in) with **no superbot/disbot strings leaking into planted output**. *Caveat (deliberate, not a
bug):* the "generic" templates hard-cite a central `menno420/substrate-kit` program-law
register — a genuinely unaffiliated adopter would inherit a governance pointer it must repoint
or drop. Engine internals carry lineage comments (they stay in the engine, not the adopter's
output). The v1.0.0 *release asset* lags `main` by a large `[Unreleased]` body — a consumer
pinning the release gets materially less than `main`.

### superbot-next — grade B+ (real depth + velocity; incomplete, honestly)
50 merged PRs, zero open, clean monotonic cadence. 17 kernel + 37 domain subsystems, a 37 KB
manifest compiler, 24–25 checksum-pinned migrations, 22 checkers across 5 CI workflows, a
466-file golden-parity corpus, and a genuinely-wired born-red gate. The completion report
(`docs/status/rebuild-completion-report-2026-07-09.md`) is candid, not celebratory. **The
honest caveats it discloses**: the bot **cannot boot yet** (no `main()`/composition root — by
design); **0 of 465 parity goldens are flipped to "ported"** (the oracle is instrumented, not
yet demonstrated for a single subsystem); and the kit's render/engage half was left half-done
(§4). One premature merge (#44→#46) shows auto-merge-on-green can land incomplete work — caught
and repaired.

### websites — grade B+ product / C governance-transfer
A FastAPI + Jinja2 monorepo of three server-rendered, Railway-deployed sites, ~36 templates /
~55 passing tests, a genuinely good hand-built design system (dark-native tokens with a
*separate* light theme, documented WCAG contrast ratios, semantic/ARIA HTML), constant-time
auth with secret-leak tests, and a "never fake data" rule *enforced in code* (honest
`{ok,error}` envelopes, no lorem-ipsum). The flaw the Project surfaced *itself* (by
commissioning an **independent** audit of its own work — a strong integrity signal): the
substrate-kit governance was adopted **ritually, not engaged** — no CI on `main`,
`session_count` 0, 8 binding docs still on `⚠️ UNRENDERED SLOTS` banners, `.claude/` inert. Open
PR #16 is exactly the right fix, ~5% done.

### superbot — the yardstick
Mature, quiet, one housekeeping PR open. Its operating system is fully live/enforcing — the
state the fresh repos are converging toward.

## 4. The finding that matters most (reproducible, actionable)

**The substrate-kit splits into two halves. The decision half travels perfectly; the
enforcement/engagement half reliably strands — in both fresh repos, identically.**

Mechanism (from the kit's own source): `bootstrap.py adopt` deliberately **plants docs
skip-if-exists and banners any unfilled `${...}` slot under a loud "UNRENDERED" banner**, and
stages the `.claude/` harness behind an **opt-in** (`--wire-enforcement`). Rendering is a
*separate* `bootstrap render`/`ask` step. So adoption leaves a repo that *looks* adopted (all
docs present) but is neither rendered nor enforcing until someone runs the follow-through — and
in both fresh repos nobody did:

- **superbot-next**: `CONSTITUTION.md`, `current-state.md`, `project.index.json` still show raw
  `${...}`; `.claude/` inert; `session_count` 0; 2 session cards for 50 PRs.
- **websites**: 8 binding docs still on `UNRENDERED SLOTS`; **no CI on `main`**; `session_count`
  0; `.claude/` inert.

This is a **UX gap in the adoption flow**, not a competence gap: the kit *itself* dogfoods the
fully-engaged state (green CI, live session discipline), and so does origin-`superbot`. Only
*fresh adoptions* stall. The prior directing session already flagged one instance
(`superbot-next/docs/current-state.md` still template — `.sessions/2026-07-08-rebuild-audit-checklist.md`).

**The fix belongs upstream in the kit** (route to the kit-lab Project): make `adopt`
render-and-wire by default, **or** plant a born-red post-adopt gate that stays red until
render + enforcement complete — the exact "enforce, don't exhort" pattern the kit already
preaches. `websites` PR #16 is the per-repo version of this fix; finishing it, and generalizing
it into the kit, closes the gap for every future adoption.

## 5. First-party verification (this review ran the code)

Cloned `superbot-next` @ `e8d393f` and ran it locally:

| Claim | Result |
|---|---|
| "999 tests green" | ✓ **998 passed, 1 skipped** under Python **3.11** (CI's interpreter). *(Under 3.10 the suite shows 75 failures — a pure interpreter mismatch, not a defect; the repo targets 3.11.)* |
| manifest compiler deterministic | ✓ `manifest_compile.py` exit 0, `sha256:b2e5b64…` — **exactly** the hash the completion report claims, 41 manifests |
| "0/465 parity flips" (honesty) | ✓ **466 golden files on disk, 0 flipped to `ported`** — born-red is truthful |
| checker fleet runs | ✓ sampled `check_namespace`, `check_parity_depth` — both exit 0 |
| test/structure counts | ✓ 82 test files, 945 `def test_` lines, 22 checkers, 5 workflows — matches the reports |

**Conclusion:** `superbot-next`'s headline claims hold up under independent execution. The
self-report is accurate *including* its disclosure of what is not done — the single most
important quality signal for a non-coder owner relying on agent reports, and strong evidence
for the Anthropic follow-up.

## 6. Open-PR reviews

- **`substrate-kit` #17 — the KL-5 benchmark tree. ✅ Strong. Needs the owner.** Held open by
  design (`do-not-automerge`) because the kit's benchmark-integrity law says a lab session never
  merges its own change to the rubric/tasks/seeds and the *first rubric is owner-blessed*. CI
  green, session card complete, +1888/−8 over 27 files. Ships the cold-start rubric (M1/M2/M3),
  allocation rubric, tasks T1–T5 (T5 "break-a-rule" exercises the guard half), a seed generator,
  and `check_bench_integrity.py` (reds any un-blessed oracle change — self-verified against its
  own diff). **B1's first baseline run is blocked on the owner's merge. Recommendation: bless
  it.** This is a designed decision gate, not a stalled PR.
- **`websites` #16 — "engage the substrate-kit machinery." ⏳ Right fix, ~5% done.** The plan is
  exactly correct (render 8 docs, install `quality.yml` CI, backfill bookkeeping); currently one
  commit (a session card), CI pending (no CI exists yet). **Don't merge; finish it** — it is the
  concrete repair for the §4 gap.
- **`superbot` #1886 — dependabot policy. ✅ Low-risk housekeeping.** Records Q-0256, dispositions
  6 dep-bumps. Docs-only; fine to auto-merge on green.
- **`superbot-next` — no open PRs.** The "open work" is not a PR: it is the first genuine parity
  flip + a composition root.

## 7. What this means for the Anthropic evaluation

The 7/8 two-part email is already sent; this session is the promised *next evidence round*
(1→4 repos + the incoming parallel fleet). The story is strong and honestly told: (a) **the
workflow reproduces in fresh repos** — the decision/ledger half is near-perfect, answering the
core "does the substrate travel?" question with a measured caveat; (b) a **concrete,
mechanism-level product-adjacent finding** (the adopt "last-mile" gap) of exactly the lived
kind Anthropic asked for; (c) **fleet velocity + integrity together** — 50+55+624 tests, three
deployed sites, zero risky actions, self-reviews that correct themselves, and an
independent-audit habit worth pointing to. New eval-log entries from this session capture the
first-party re-run and the render/engage pattern.

## 8. Recommendations (priority order)

1. **Bless `substrate-kit` #17** (unblocks B1). Owner action.
2. **Finish `websites` #16**, then **generalize the fix into the kit** (§4) so `adopt`
   render-and-engages by default or gates on it — the highest-leverage single improvement.
3. **Demonstrate the first `superbot-next` parity flip** — turn "instrumented" into "proven" for
   one subsystem; it converts the biggest honesty caveat into a milestone.
4. **Stand up the manager Project** ([brief](../planning/eap-manager-project-brief-2026-07-09.md))
   before widening the fleet — oversight first, then scale.
5. **Launch the model-comparison arms** (`eap-project-fleet-2026-07-09.md`): kit-lab + the two
   coding arms (Fable 5 vs Opus 4.8, identical brief) — the one experiment no single Project can
   answer.

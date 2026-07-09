# External review pack — auditing the Projects-EAP fleet (2026-07-09)

> **Status:** `reference` — the single entry point for **outside reviewers** auditing this
> program. Written for an external AI reviewer with a web browser and **no GitHub
> authentication**: every repository named here is **public**, and every file reference is a
> plain `https://raw.githubusercontent.com/...` URL you can fetch directly (PR/CI links use
> the normal `https://github.com/...` web UI, also public). Compiled 2026-07-09T16:22Z from
> the fleet manifest, each repo's live `control/status*` file, and the four-reviewer internal
> quality review of the same date. **Source repos win over this pack** — it is a dated
> snapshot and the fleet moves fast; re-fetch any status file before relying on it.

---

## 1. The program in one page

A single **non-coder owner** runs a fleet of autonomous Claude Code Projects (Anthropic's
Projects EAP). The agents plan, build, test, review, merge, and deploy; the owner directs
intent, reacts to what he sees, and answers routed questions. Today (2026-07-09) is the
fleet's **first full day at 10 Projects** across 9 public repos, all under
[github.com/menno420](https://github.com/menno420):

| Project | Repo | What it is |
|---|---|---|
| manager | (writes into every repo) | control chair: dispatches orders, aggregates status, builds nothing |
| SuperBot coordinator | `superbot` + `superbot-next` | mature production Discord bot (~1900 PRs, live on Railway) + its 1-day ground-up rebuild (49 build PRs, ~1077 tests claimed at build, ~1104 now, 465 behavior goldens — all honestly pending) |
| kit-lab | `substrate-kit` | portable agent-workflow kit (docs/gates/session loop as a versioned product; v1.3.0 released) |
| websites | `websites` | 3 live server-rendered FastAPI services on Railway (control-plane, botsite, dashboard) |
| trading-lab | `trading-strategy` | autonomous quant research lab (backtesting only, no live trading) |
| codetool-lab-fable5 / -opus48 / -sonnet5 | `codetool-lab-*` | three coding arms given the **identical brief**, differing only in model — a live model comparison |
| game-mining + game-exploration | `superbot-games` | two Projects deliberately **sharing one repo** in separate lanes — a cohabitation experiment |

**Coordination is a committed-file message bus.** The EAP evaluation proved Projects cannot
talk to each other directly, so the only shared medium is git: each repo carries a
`control/` directory with `inbox.md` (orders **to** the Project; sole writer = manager) and
`status.md` (heartbeat **from** the Project; sole writer = the Project). One-writer-per-file
is the rule that keeps it conflict-free. The registry of all Projects is the fleet manifest
in `superbot`. Protocol spec:

- Fleet manifest: <https://raw.githubusercontent.com/menno420/superbot/main/docs/eap/fleet-manifest.md>
- Coordination protocol: <https://raw.githubusercontent.com/menno420/superbot/main/docs/planning/fleet-coordination-protocol-2026-07-09.md>
- Fleet plan (why these Projects): <https://raw.githubusercontent.com/menno420/superbot/main/docs/planning/eap-project-fleet-2026-07-09.md>
- Running evaluation log (lived findings, platform walls): <https://raw.githubusercontent.com/menno420/superbot/main/docs/planning/projects-eap-evaluation-log.md>

---

## 2. The central question for every reviewer

**Where output disappoints, classify the root cause.** Every finding you report must carry
one of three classes:

- **(a) OUR INSTRUCTIONS / SETUP** — ambiguous orders, missing rules, a bad seed file, a
  gate we forgot to wire, doctrine that was never transferred to a fresh repo.
- **(b) PLATFORM LIMITATIONS / BUGS** — no cross-session channel, session visibility gaps,
  permission walls (403s on tag push / releases API), CI queue stalls, worker context caps.
- **(c) GENUINELY DEFICIENT WORK** — wrong code, inflated claims, tests that don't test,
  claims that don't survive contact with the source.

**What we already know (state of honesty as of 2026-07-09, so you verify rather than
rediscover):** a four-reviewer internal audit ran today over shipped code
(<https://raw.githubusercontent.com/menno420/superbot/main/docs/eap/fleet-quality-review-2026-07-09.md>).
Its headline findings, which you should treat as *claims to check, not settled truth*:

1. The rebuild's "help looks wrong" incident was **staged fidelity, not a quality breach** —
   the visual deferral was ledgered and reported red 44 minutes before the owner looked —
   but it was never communicated in owner-facing terms, and two defects (a silent
   6000-char embed shed, a dead help button) were genuinely owner-found first.
2. **One proven semantic regression**: warn-escalation in superbot-next
   (`sb/domain/moderation/ops.py`) diverged from the old bot's oracle. The fleet claims it
   was **fixed same-day** (superbot-next PR #80, compensator matching the oracle) — verify
   the fix, not just the finding.
3. **Zero test-count inflation** — all three lab arms' claimed counts (63 / 100 / 66)
   reconciled exactly against counted `def test` functions plus parametrize expansion.
4. The systemic risk is a **closed self-verification loop**: author = gatekeeper = merger,
   with ~1–2-minute merges; the only reviewer most claims ever meet is their claimant.
   **You are the missing control.** An adversarial outside pass is exactly what the
   internal audit prescribed.

An earlier independent review the same day (different session, cloned the rebuild and
re-ran its full suite first-party) is also on record:
<https://raw.githubusercontent.com/menno420/superbot/main/docs/eap/fleet-review-2026-07-09.md>

---

## 3. Repo register — entry docs, current state, boldest claims

Every "phase/health" line below is quoted or condensed from that repo's live
`control/status*` file at compile time (16:22Z). Fetch the status URL yourself for the
current value.

### 3.1 menno420/superbot — the mature production bot + program hub

**Purpose:** live Discord bot (~243k LOC, ~1900 PRs, deployed on Railway; merging to main
IS deploying) and the program's documentation hub: the fleet manifest, the coordination
protocol, the owner question router, and the whole agent working agreement live here.

**Phase/health:** production-stable; reconciliation band #1890 done; no `control/` dir of
its own (it hosts the manifest instead — the manager writes orders to the *other* repos).

**Key entry docs (superbot has no root README — these are the entry points):**
- <https://raw.githubusercontent.com/menno420/superbot/main/docs/current-state.md> (living "what is true now" ledger)
- <https://raw.githubusercontent.com/menno420/superbot/main/docs/collaboration-model.md> (the binding human↔agent working model)
- <https://raw.githubusercontent.com/menno420/superbot/main/docs/architecture.md> (layering + invariants)
- <https://raw.githubusercontent.com/menno420/superbot/main/docs/owner/maintainer-question-router.md> (every owner decision, Q-numbered)
- <https://raw.githubusercontent.com/menno420/superbot/main/docs/eap/fleet-manifest.md> (Project registry)

**Boldest claims to verify:**
1. "~1900 PRs of autonomous work with drift kept in check by standing reconciliation passes
   every 30 PRs" — check the PR list (<https://github.com/menno420/superbot/pulls?q=is%3Apr>)
   and whether `docs/current-state.md`'s ledger actually tracks recent merges.
2. "Merging is deploying; the bot is live" — the docs claim Railway auto-redeploys `worker`
   on every merge (`docs/operations/production-deployment.md` — fetch via raw URL pattern).
3. "The question-router discipline works": owner decisions are recorded as Q-numbered
   entries and cited as provenance in rules — spot-check that Q-numbers referenced in
   CLAUDE.md/`docs/` actually exist in the router.
4. "The old bot's warn-escalation is the *oracle* the rebuild is measured against" — the
   cited behavior lives at
   <https://raw.githubusercontent.com/menno420/superbot/main/disbot/services/moderation_service.py>
   (escalation ladder ~lines 402–473, `escalation_blocked=True` on Discord refusal).

### 3.2 menno420/superbot-next — the 1-day ground-up rebuild

**Purpose:** rebuild the production bot from scratch on a new architecture (declarative
manifest → one workflow engine, one render path, one settings seam), accepted against 465
black-box **goldens** captured from the running old bot (command in → embeds/components/DB
delta/events out, byte-exact incl. visuals). Built by a coordinator + band workers: 49 build
PRs in ~14 hours, then live-tested against a real Discord guild.

**Phase/health (status @16:05Z):** band-2 slice-2 complete; **red-by-design** (golden-parity
dashboard red while all rows are `pending` — deliberate); pytest 1104 passed / 2 skipped;
bot RUNNING live from main; warn-escalation compensator shipped (PR #80, D-0058); help
byte-parity flip (the first A-16 one-way door) still unstarted, gated on an owner parity
ruling.

**Key entry docs:**
- <https://raw.githubusercontent.com/menno420/superbot-next/main/README.md>
- <https://raw.githubusercontent.com/menno420/superbot-next/main/control/status.md>
- <https://raw.githubusercontent.com/menno420/superbot-next/main/docs/decisions.md> (D-numbered ledger, ~58 entries)
- <https://raw.githubusercontent.com/menno420/superbot-next/main/docs/status/testing-report-2026-07-09.md> (live-test evidence, verbatim transcripts)
- <https://raw.githubusercontent.com/menno420/superbot-next/main/docs/status/rebuild-orchestration-retrospective-2026-07-09.md>
- <https://raw.githubusercontent.com/menno420/superbot-next/main/docs/status/old-vs-new-diff-overview-2026-07-09.md>
- <https://raw.githubusercontent.com/menno420/superbot-next/main/parity/README.md> + <https://raw.githubusercontent.com/menno420/superbot-next/main/parity/parity.yml> + <https://raw.githubusercontent.com/menno420/superbot-next/main/parity/COVERAGE.md>

**Boldest claims to verify:**
1. "465 goldens byte-pin the old bot's behavior **including visuals**, and **0 have been
   flipped** — the born-red dashboard is honest, no exemption rows were minted under
   pressure." Evidence: `parity/parity.yml` (all rows should read `pending`),
   `parity/goldens/` tree, and the A-16 one-way-door language in `parity/README.md`.
2. "Centralization is real: 617 `discord.Embed(` call sites in the old bot collapsed to
   **1** in the new tree" — grep-check
   <https://raw.githubusercontent.com/menno420/superbot-next/main/sb/adapters/discord/panel_view.py>
   (the claimed single site) vs. GitHub code search over `sb/` for `discord.Embed(`.
3. "The proven warn-escalation regression (internal audit R2) was fixed same-day: the WARN
   op now carries a `moderation.compensate_warn_escalation` EFFECT-leg compensator matching
   the old bot's `escalation_blocked` semantics" — verify at
   <https://raw.githubusercontent.com/menno420/superbot-next/main/sb/domain/moderation/ops.py>
   and PR #80 (<https://github.com/menno420/superbot-next/pull/80>). The audit text
   describes the *pre-fix* state; confirm the fix is real and the enshrining test was
   re-pinned, not deleted.
4. "~1104 tests pass and they are behavioral, not mocks-echoing-mocks" — sample
   <https://raw.githubusercontent.com/menno420/superbot-next/main/tests/unit/workflow/test_engine.py>
   (rollback, idempotent replay, compensation) and the band-6 money-conservation tests.
5. "The bot boots and runs live: migrations apply on fresh Postgres, gateway READY, real
   commands dispatch in a real guild" — the testing report carries verbatim evidence rows;
   check they name their own known-red presentation classes rather than claiming "PASS"
   unqualified.

### 3.3 menno420/substrate-kit — the portable workflow kit

**Purpose:** package the workflow that runs this program (session cards, born-red gates,
control-file protocol, engagement checks) as a versioned, adoptable product for any repo.

**Phase/health (status @15:26Z):** green; **v1.3.0 released** (all three release assets,
sha256-pinned dist); suite 696; `kit: v1.3.0 · check: green · engaged: yes` (dogfooding its
own heartbeat format); ORDER 003 done.

**Key entry docs:**
- <https://raw.githubusercontent.com/menno420/substrate-kit/main/README.md>
- <https://raw.githubusercontent.com/menno420/substrate-kit/main/control/status.md>
- <https://raw.githubusercontent.com/menno420/substrate-kit/main/CHANGELOG.md>
- <https://raw.githubusercontent.com/menno420/substrate-kit/main/docs/adopters.md> (fleet adoption registry)
- <https://raw.githubusercontent.com/menno420/substrate-kit/main/docs/reports/2026-07-09-fleet-adoption-review.md>

**Boldest claims to verify:**
1. "The engagement gate holds a cold adoption **red until genuinely engaged** — wiring CI
   alone is still red" — the check is
   <https://raw.githubusercontent.com/menno420/substrate-kit/main/src/engine/checks/check_engagement.py>
   and the behavioral proof is
   <https://raw.githubusercontent.com/menno420/substrate-kit/main/tests/test_check_engagement.py>
   (`test_cold_adopt_is_born_red_then_green_once_engaged`,
   `test_wire_enforcement_alone_is_still_red`). Known soft spot (disclosed): the CI-wiring
   check is a substring match (`"check --strict"` anywhere in a workflow file counts).
2. "696 tests, dist byte-pin verified on the merged tree, release run green" — check the
   Actions runs (<https://github.com/menno420/substrate-kit/actions>) and the v1.3.0
   release body (<https://github.com/menno420/substrate-kit/releases>).
3. "The kit closed its own fast-lane bypass hole the day it found it" — a heartbeat-deleting
   control PR rode the fast lane green; verify the `--status-only` fix + lane tests exist.
4. "Adopters gained an auto-appended upgrade checklist in every release's notes" — visible
   directly in the v1.3.0 release body.

### 3.4 menno420/websites — three live services

**Purpose:** control-plane (program console incl. `/fleet` board), botsite, dashboard —
three independent server-rendered FastAPI services sharing code but not a process, deployed
on Railway.

**Phase/health (status @16:30Z):** green — all three services in-sync at head (deploy-state
verified live via `/api/readiness.json`); 117 tests; shipped #36: the `/fleet` board now
derives its lane set **live from the fleet manifest** instead of a hand-kept copy.

**Key entry docs:**
- <https://raw.githubusercontent.com/menno420/websites/main/README.md>
- <https://raw.githubusercontent.com/menno420/websites/main/control/status.md>
- <https://raw.githubusercontent.com/menno420/websites/main/docs/current-state.md>
- <https://raw.githubusercontent.com/menno420/websites/main/app/readiness.py> (the drift cell)
- <https://raw.githubusercontent.com/menno420/websites/main/app/main.py>

**Boldest claims to verify:**
1. "The deploy-drift cell compares each service's **live `/version`** (fetched over the
   network) to the main head SHA from GitHub's check-runs API; unknowns render as
   `unknown`, never faked" — read `_service_deploy_state` / `_deploy_board` in
   `app/readiness.py`.
2. "The drift cell **caught a real production deploy bug on day one** — the dashboard
   service silently had no Railway deploy trigger and was shipping stale code on every
   merge" — evidence trail: PRs #26–#30
   (<https://github.com/menno420/websites/pulls?q=is%3Apr>), root-cause in #29.
3. "The `/fleet` board self-updates from the manager's manifest (10 lanes parsed live,
   labeled fallback on fetch failure)" — PR #36 + `lane_source` in `/fleet.json`.
4. Known blemish (disclosed): websites PR #19 is the fleet's canonical born-red gate leak —
   an effectively-empty PR auto-merged; fixed by #24 and upstreamed into the kit. Verify
   the fix held.

### 3.5 menno420/trading-strategy — the quant research lab

**Purpose:** autonomous trading-strategy research (backtesting; research-only, **no live
trading**). P0 = data layer + vectorized engine + baselines + experiment ledger.

**Phase/health:** ⚠️ the committed status file (@12:32Z) is still the manager's seed
("scaffolded; Project not yet activated") — **stale**. The real state: the entire P0 lab
sits in **PR #1, still an open draft** (verified 16:22Z), despite a merged manager order
(ORDER 002, PR #2) directing it un-drafted. **Main has no runnable code.** This is itself a
finding-in-waiting — classify it.

**Key entry docs:**
- <https://raw.githubusercontent.com/menno420/trading-strategy/main/README.md>
- <https://raw.githubusercontent.com/menno420/trading-strategy/main/docs/founding-plan.md>
- <https://raw.githubusercontent.com/menno420/trading-strategy/main/control/status.md>
- PR #1 (the actual lab): <https://github.com/menno420/trading-strategy/pull/1> — code is on
  the branch, readable without auth via the `refs/heads/` raw form:
  - <https://raw.githubusercontent.com/menno420/trading-strategy/refs/heads/claude/order-001-p0/src/trading_lab/engine.py>
  - <https://raw.githubusercontent.com/menno420/trading-strategy/refs/heads/claude/order-001-p0/src/trading_lab/data.py>
  - <https://raw.githubusercontent.com/menno420/trading-strategy/refs/heads/claude/order-001-p0/src/trading_lab/config.py>
  - <https://raw.githubusercontent.com/menno420/trading-strategy/refs/heads/claude/order-001-p0/tests/test_engine.py>

**Boldest claims to verify:**
1. "**No lookahead bias**: positions `shift(1)`, bar return `open[t+1]/open[t]-1`, and the
   tests prove it behaviorally from both directions (a signal on a jump bar earns ~0; a
   prescient signal would earn 2.0)" — `tests/test_engine.py` (~lines 23–40).
2. "t+1-open fills with 5+1 bps per-side costs, **default-on**, closed-form round-trip
   test `equity == (1-6e-4)^2`."
3. "The 18-month **holdout is enforced in the loader**, not just documented — default
   exclusion, `HoldoutViolationWarning` on unlock, and the constant itself
   (`HOLDOUT_START == "2025-01-09"`) is pinned by a test" — `data.py` + `config.py`.
   Disclosed caveat: it's a load-time discipline rail, not cryptographic — raw cached CSVs
   do contain holdout bars.
4. "Exactly **63 offline tests** (59 defs + one class parametrized ×3 over 2 tests), and
   the baseline results are honestly negative (defaults underperform buy-and-hold at
   realistic costs)."

### 3.6 The three codetool arms — model comparison (identical brief)

**Purpose:** three repos, three models (Fable 5 / Opus 4.8 / Sonnet 5), one identical
brief: ship a real, stranger-usable CLI developer tool end-to-end. The comparison of
interest is *quality and honesty per model*, so audit all three with the same yardstick.

**codetool-lab-fable5 — `envdrift`** (env-file drift checker). Status @15:01Z: shipped —
PR #2 merged; stranger install from main verified (fresh venv + pipx, every README example
reproduced). Walls (disclosed): tag push + releases API 403'd; PyPI needs owner creds.
- <https://raw.githubusercontent.com/menno420/codetool-lab-fable5/main/README.md>
- <https://raw.githubusercontent.com/menno420/codetool-lab-fable5/main/control/status.md>
- <https://raw.githubusercontent.com/menno420/codetool-lab-fable5/main/src/envdrift/cli.py> ·
  <https://raw.githubusercontent.com/menno420/codetool-lab-fable5/main/src/envdrift/parser.py> ·
  <https://raw.githubusercontent.com/menno420/codetool-lab-fable5/main/tests/test_check.py>
- Claims: "**exactly 66 tests** (63 defs + parametrize ×4 − 1), behavioral (real .env files
  in tmp_path, real CLI `main()`, exit codes asserted)"; "a stranger can install and use it
  from the README alone". Known blemish (found by internal audit): `tests/__pycache__/`
  committed to main — check whether it was cleaned up.

**codetool-lab-opus4.8 — `mdverify`** (runs fenced code blocks in markdown and verifies
them; 5 languages, timeouts, expect-error). Status file @13:06Z is the stale manager seed —
but the code is merged on main; the tool shipped before the status discipline landed.
- <https://raw.githubusercontent.com/menno420/codetool-lab-opus4.8/main/README.md>
- <https://raw.githubusercontent.com/menno420/codetool-lab-opus4.8/main/control/status.md>
- <https://raw.githubusercontent.com/menno420/codetool-lab-opus4.8/main/src/mdverify/runner.py> ·
  <https://raw.githubusercontent.com/menno420/codetool-lab-opus4.8/main/tests/test_runner.py>
- Claims: "**exactly 100 tests**, zero parametrize inflation, executing **real
  interpreters** (real subprocess timeouts, real bash gated by `shutil.which`)"; "a
  stranger could run it — the one stranger-blocking bug (README pointing at a nonexistent
  `@v0.1.0` tag) was caught and fixed in PR #4 with an honest explanation."

**codetool-lab-sonnet5 — `cfgdiff`** (semantic config diff/convert across
JSON/YAML/TOML/INI/.env). Status @16:15Z: shipped **after** the internal audit (which
correctly reported "nothing to audit" at its cutoff) — PR #4 merged; claims 114 tests, CI
green on 3.10/3.11/3.12, wheel verified in a fresh venv. Same 403 walls on tag push.
- <https://raw.githubusercontent.com/menno420/codetool-lab-sonnet5/main/README.md>
- <https://raw.githubusercontent.com/menno420/codetool-lab-sonnet5/main/control/status.md>
- <https://raw.githubusercontent.com/menno420/codetool-lab-sonnet5/main/CHANGELOG.md> ·
  <https://raw.githubusercontent.com/menno420/codetool-lab-sonnet5/main/src/cfgdiff/cli.py>
- Claims: "114 pytest tests, ruff-clean, exit codes 0/1/2, documented lossy-conversion
  policy, README shows real pasted output" — this arm is the **least-audited**; it has met
  no reviewer but its author. Apply extra scrutiny here.

### 3.7 menno420/superbot-games — the shared-repo cohabitation experiment

**Purpose:** two Projects (game-mining, game-exploration) share one repo in separate lanes,
producing game/plugin packages for superbot-next. The experiment is whether lane discipline
(separate `control/inbox-*.md` / `status-*.md`, separate doc trees) prevents two autonomous
Projects from colliding in one repo.

**Phase/health (both status files @14:23Z):** both lanes still read "repo seeded; Project
not yet started" — the Projects launched late in the day. The fleet's claim that "lane
discipline held except a kit double-adoption" refers to early activity; verify against the
actual commit/PR history (<https://github.com/menno420/superbot-games/pulls?q=is%3Apr> and
the commit log) — if both Projects adopted the kit into the same shared files, that's the
collision to look for.

**Key entry docs:**
- <https://raw.githubusercontent.com/menno420/superbot-games/main/README.md>
- <https://raw.githubusercontent.com/menno420/superbot-games/main/docs/lanes.md> (the binding lane split)
- <https://raw.githubusercontent.com/menno420/superbot-games/main/docs/founding-plan-mining.md> ·
  <https://raw.githubusercontent.com/menno420/superbot-games/main/docs/founding-plan-exploration.md>
- <https://raw.githubusercontent.com/menno420/superbot-games/main/control/status-mining.md> ·
  <https://raw.githubusercontent.com/menno420/superbot-games/main/control/status-exploration.md> ·
  <https://raw.githubusercontent.com/menno420/superbot-games/main/control/README.md>

---

## 4. Required output shape

Produce **one single markdown report** containing:

1. **Findings table** — one row per finding:
   `ID · finding · evidence URL · severity (critical/major/minor/info) · root-cause class (a/b/c)`.
   Every row must cite a URL you actually fetched (raw file, PR, CI run). No URL, no finding.
2. **Per-claim completeness verdict** — for every bold claim in §3 you examined:
   `verified` / `refuted` / `could-not-verify`, each with one line of *why* (what you
   fetched, what you saw, or what blocked you).
3. **Exactly 3 recommendations** — the highest-leverage changes, each tied to findings by ID.

**Integrity bar:** state uncertainty honestly; never guess; **a `could-not-verify` beats an
invented confirmation** — the fleet's own audits are graded on exactly this standard, and so
are you. If a raw URL 404s (a file moved after this pack was compiled), say so and try the
repo's GitHub file browser before giving up.

---

## 5. Integrity notes

- **The repos ARE the record.** Everything the fleet has done — every order, heartbeat,
  decision, test run, and fix — is committed to these public repos. You need no
  authentication and no inside access; if a claim can't be verified from public URLs,
  that inability is itself a reportable finding.
- **The fleet's own reports may be wrong. That is the point.** The internal quality review,
  the status heartbeats, and this pack itself are all fleet-authored. Do not treat any of
  them as ground truth; treat them as claims whose evidence pointers you follow to source.
- **Your review will be cross-checked, not obeyed.** Before anything you recommend is acted
  on, an agent verifies each specific finding against the shipped source (the program's
  standing Q-0120 discipline: cross-agent output is input to verify, never an order). So
  optimize for *verifiable* findings — precise URLs, line references, reproducible checks —
  over persuasive prose.

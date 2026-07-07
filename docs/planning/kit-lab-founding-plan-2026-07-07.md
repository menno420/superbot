# Kit-lab founding plan — the substrate-kit repo + self-improvement lab (2026-07-07)

> **Status:** `plan` — the executable founding plan for the extracted **`substrate-kit` repo** and
> the **self-improvement lab** that runs in it. Program session **2 of 4** (Q-0252/Q-0253), produced
> per [`kit-lab-repo-founding-brief-2026-07-07.md`](kit-lab-repo-founding-brief-2026-07-07.md) under
> **Q-0240** (decide-and-flag) + **Q-0241** (never-wait; silence = consent). Companions: the
> [multi-repo program capture](../ideas/multi-repo-program-kit-lab-trading-2026-07-07.md) (Part 2 is
> the owner-ratified mandate) · the [kickoff brief](rebuild-kickoff-steps-6-8-brief-2026-07-07.md)
> (steps 6–8 create the repos; this plan begins where it ends) · the
> [Phase-2.5 report](phase-2.5-cold-start-report-2026-07-07.md) (the honest evidence base) ·
> [companion D](rebuild-phase-2.5-procedure-2026-07-06.md) (the A/B protocol §5 routinizes).
> **This plan lives here until the kit repo exists (the kickoff creates it), then travels with it.**
> Every self-made call is in the §12 decisions log, ⚑-flagged. No new router Q-blocks were needed —
> no genuine product fork surfaced; the owner-input items are 👤-marked in §7.
>
> Grep route: §1 flags · §2 mandate + definition of done · §3 repo shape · §4 releases ·
> §5 benchmarks (B1–B4) · §6 the lab loop · §7 provisioning · §8 governance home ·
> §9 friction protocol · §10 build bands · §11 not-to-do · §12 decisions · §13 evidence.

---

## §0 Where things stand (verified at head, 2026-07-07)

| Fact | State | Evidence |
|---|---|---|
| The kit | Finished + enforced: 440 tests green in ~3.5 s at `tests/unit/substrate_kit/`; one-step `adopt` derives provisional slots, banners unrendered docs, vendors `bootstrap.py`; `adopt --wire-enforcement` plants a live CI gate (`check --strict --require-session-log` → MERGE HELD) | `substrate-kit/src/engine/adopt.py:209-382`; `cli.py:518-574`; PR #1778/#1783 |
| Extraction | **Not done** — the kickoff session (program session 4, Opus-class, any day) creates `substrate-kit` + `superbot-next` per Q-0247; no repos exist at head | kickoff brief §2; `rebuild-canonical-plan-2026-07-06.md:262` |
| Cold-start evidence | **FAIL twice** (F-5 bar, 0/3 both runs): run 1 = inert templates; run 2 post-fix = ON read 3.1–3.3× more and wrote nothing back. Refuted claim: *readable orientation docs are a cost without mechanized write-back*. Green-lighting on a measured cold-start benefit is off the table | phase-2.5 report §0/§5 |
| The ruled next experiment | **Not another same-shape A/B**: build the [auto-drafted handoff](../ideas/substrate-kit-auto-drafted-handoff-2026-07-07.md) first, then a T4-style pair | phase-2.5 report §5.3 |
| Release discipline | **None exists**: only `pyproject.toml` `version = "0.1.0"` (never bumped, not exposed); no `--version`, no build stamp in dist, no CHANGELOG, no LICENSE file, no tags, no upgrade path for planted docs, no rollback story | kit-internals audit, §13 |
| Telemetry | **None exists**: no spend/token instrumentation anywhere; the kit is explicitly provider-hook-free; today's only allocation record is prose router blocks (Q-0253 = the first) | `substrate-kit/src/engine/loop/maintenance.py:40` |
| The console | Session 1 (PR #1802, in flight) shipped the program-console **shell** on the botsite service: 4 real lanes + 3 declared pending lanes with exact contract strings; deploy flagged "same service as a route for now, **move at kit-extraction**" | `botsite/console/console.js:44-59` @7120b79; website brief:69-72 |
| Program law | Q-0240/41/43…53 minted in superbot's router; the kickoff's governance-home fork recommends the kit repo carries the canonical program-level copies | kickoff brief step 7 |

---

## §1 Flag-for-gate — the owner's one-pass veto list (KF-1…KF-9)

Each row is a **decided recommendation**, not an open question — skim, veto what you disagree
with, silence blesses the rest (Q-0241). Full rationale in §12. *(Numbered KF-N to avoid
colliding with the canonical plan's F-N flags.)*

| # | Decision (recommended, applied throughout this plan) | One-line why |
|---|---|---|
| KF-1 | **Releases are GitHub Releases with semver tags, first release `v1.0.0` at extraction**; each release ships `bootstrap.py` as the pinned asset + a `sha256` checksum + a machine-readable `release.json`; `CHANGELOG.md` keep-a-changelog format | consumers pin something *nameable and verifiable*; v1.0.0 because two real consumers depend on a stable adopt contract — 0.x "anything may change" would be a lie |
| KF-2 | **Upgrades are pull-based**: consumers poll the kit repo's releases and land their own upgrade PRs; the lab never holds **write** access to consumer repos (read scope: KF-11) | the cheapest credential shape that satisfies Q-0249's rail; the lab's outbound duty becomes publishing `release.json` + upgrade notes, which is mechanical |
| KF-3 | **First work surface = the program console** (adopt session 1's shell, fill its declared telemetry lane, add the kit-lab lane, move to the lab's Railway project at extraction); the **lab bot token is second** and 👤-gated (Discord app creation is an owner portal action) | the console is the owner's phone-first window into everything the lab does; a bot token has no consumer until the lab has Discord-facing experiments |
| KF-4 | **Lab v1 = ONE fresh-session-per-fire routine, daily cadence**, under Q-0241-*shaped* rails (§6); the lab's own destructive tier is enumerated (§6.4) and executes only via reversible paths | rail before scale (owner-ratified); daily matches an inbox+benchmark workload — 2-hourly would burn spend polling an empty inbox |
| KF-5 | **Benchmarks are mandatory-to-RUN, advisory-to-PASS** (the A-17 pattern): the cold-start A/B never blocks a release; its job is the trend line and the "make the A/B flip" goal. **B1's first firing waits for the auto-drafted-handoff build** (the ruled sequencing) | the benefit claim already failed twice — a blocking gate would deadlock releases on a metric we know is currently red; trend + flip is the honest shape |
| KF-6 | **Program law lives canonically in the kit repo at `docs/program/`** as a `[PL-NNN]` register importing the founding rulings with superbot Q-numbers as provenance; consumers **cite, never copy** (pointer paragraphs planted by template) | one home kills duplicated-and-drifted law; the D-ledger grammar already handles supersession + provenance |
| KF-7 | **Friction transport = GitHub issues labeled `friction` on the kit repo**, payload = the kit's existing reflection record shape + a repo envelope; filed at consumer session-close | issues are the proven agent-visible trigger surface (the `reconcile` precedent) and need no cross-repo write credentials beyond issue-create |
| KF-8 | **The unset numbers, set** (all revisable by data): Q-0248 escalation N = **2** confirmed review defects; de-escalation M = **3** consecutive matching tasks; rework/revert window = **14 days**; ideas "survive" = **30 days unreverted post-merge**; A/B trend claims need ≥ **3** paired runs; guard demotion at **>50% FP over ≥10 fires**, deletion candidacy at **2 clean bands with zero catches** | Q-0248/the capture left them as letters; benchmarks can't run on unset thresholds — these are seeded conservative and the data revises them |
| KF-9 | **`tokens_out` ships as `null`-tolerated**: no programmatic token meter exists in any session surface today; the telemetry schema carries the field, sessions fill it when a meter exists, estimates are labeled estimates | honest-gap posture (no fake data — the console's own rule); blocking telemetry v1 on a meter that doesn't exist would kill the whole Q-0248/Q-0249 dataset |
| KF-10 | **The kit repo goes PUBLIC at v1.0.0** (the kickoff creates it private; the owner flips visibility when v1.0.0 tags) — this is what makes KF-2's zero-credential pull, the §7.3 raw-URL console read, and §9.2's unauthenticated release poll real. What becomes world-readable: the kit source (already written for extraction), program law (§8), the lab's session logs + benchmark results + telemetry JSONLs. **If the owner vetoes** (keeps it private), the fallback is explicit: a read-only fine-grained PAT (`contents:read` on the kit repo) installed per consumer environment, and every "public read" in this plan reads "PAT read" | visibility was the one unflagged assumption the review caught; public is the kit's stated destiny (the OSS arc) and nothing secret lives in it — flagged because external-publish is an owner call |
| KF-11 | **The lab gets read-only fine-grained scopes on consumer repos** (`contents:read` + `pull-requests:read`, NO write) so the B2 outcome backfill, B3 friction-rate, and B4 receipt sweeps are runnable lab-side | Q-0249's rail bans holding another repo's *prod secrets or the live bot token* — read-only code/PR visibility is neither; the alternative (consumer-side backfill shipped over the issue channel) adds ceremony to every consumer forever |

---

## §2 Mandate + definition of done

### §2.1 The lab's mandate (restating the owner-ratified capture, Part 2)

1. **A standing, measurable benchmark** — the Phase-2.5 A/B re-run per kit release; founding
   challenge: the cold-start benefit is unproven (failed twice); the first measurable win is
   *make the A/B flip* (→ §5 B1).
2. **Ideas as testable output** — ideas that get implemented in a consumer repo *and survive*
   count; unbuilt or reverted ones don't (→ §5 B4).
3. **Work surfaces = observable outputs** — own test bot token (Galaxy pattern), own Railway
   project (telemetry per Q-0249, no caps), deployable websites; each surface makes improvement
   *externally verifiable* (→ §7).
   3b. **Model-for-task allocation as a standing lab benchmark (Q-0248, both planes)** — the lab
   owns the program-wide `model · effort · task-class · outcome` dataset and runs the paired
   same-task A/Bs per class (→ §5 B2). **Plane split, stated honestly:** B2 v1 covers the
   **agent plane**; the **product plane** (per-runtime-API-call routing) is *enforced* by
   superbot-next's K10 task registry + profile resolver and *judged* by the A-17 eval machinery
   per the rebuild plan — the lab's role there is dataset custody: B2 ingests product-plane rows
   (per-call `{task, provider, model, cost, latency, eval_verdict}`) into the same dataset once
   K10 exists and emits them (a post-KL-6 lane, not a lab-v1 deliverable).
4. **Cross-repo friction reports close the loop** — consumers file kit-friction deltas; the lab
   consumes them as its inbound queue; fixes ship as versioned releases; the A/B + friction rate
   arbitrate (→ §9).
5. **"Complete freedom" gets the Q-0241 shape** — reversible by default, telemetry-not-caps
   (Q-0249), scoped credentials only, everything audited, owner vetoes reactively — and the one
   structural guard above all others: **the lab measures itself on cold sessions and throwaway
   repos; a warm session never grades its own substrate** (→ §6).

### §2.2 Definition of done — lab v1

Lab v1 is DONE when all seven hold (each with its landing band from §10):

| # | Done-condition | Verifiable how | Lands |
|---|---|---|---|
| D1 | Kit repo is **born self-verifying**: own CI runs the 440-test suite + the dist==fresh-build byte-equality pin + the engine lint bans (no print/assert/subprocess) + `check --strict` on a scratch adoption | kit repo CI green on a no-op PR | kickoff (spec: §3.2), **else KL-1's first act** (§3.2 ordering note) |
| D2 | **Release v1.0.0 published**: tag + `bootstrap.py` asset + sha256 + `release.json` + CHANGELOG; both existing consumers (superbot's in-tree copy, superbot-next) carry a recorded version pin | release page exists; `substrate.config.json` has `kit_version` in both consumers | KL-1 |
| D3 | **The lab loop is live**: one daily fresh-session routine, prompt version-controlled in the kit repo, run reports flowing with `Run type: routine · lab`, console kill switch documented | ≥3 consecutive scheduled fires each shipping a real run report | KL-4 |
| D4 | **Friction inbox operational**: the `friction` label + triage step proven on ≥1 real report (superbot files the first — it is already a consumer) | a friction issue opened, triaged, dispositioned by the loop | KL-4 |
| D5 | **Benchmark harness pinned + B1 baseline recorded**: rubric/tasks/seeds/scoring committed under the §5.0 pin (CI-check fallback from birth; ruleset-backed once P10 lands); the post-auto-draft T2→T4 sequence run; `bench/results/` index rendering | `bench/` tree exists; ≥1 row in `bench/results/cold-start/index.json` | KL-5 |
| D6 | **Telemetry capture live**: model-usage rows + guard-fire records being written per session; the console's declared telemetry lane renders real rows | `telemetry/model-usage.jsonl` non-empty; console lane no longer "pending" | KL-3 + KL-6 |
| D7 | **Governance home populated**: `docs/program/` with the PL-register; ≥1 consumer citing it by pointer (never a copy) | `check_docs --strict` green in the kit repo; consumer pointer paragraph live | KL-2 |

**Explicitly NOT in lab v1** (the fence): a fleet of loops · the trading repo's surfaces ·
the Q-0248 **product plane** (K10-enforced in superbot-next; B2 ingests its rows post-KL-6, §2.1-3b) ·
public-OSS productization (PyPI, CI matrix beyond 3.10, CONTRIBUTING/SECURITY — owner-paced;
**note: KF-10 visibility ≠ productization** — flipping the repo public is one setting, the OSS
polish arc stays deferred) · the navigation-simulator oracle (a named backlog item inherited
from the website brief) · re-running the cold-start A/B before the auto-draft build lands
(ruled sequencing).

---

## §3 The kit repo's shape

### §3.1 Layout (day one, post-kickoff seed)

```
substrate-kit/                  # the repo root (owner may rename the published form — 👤, §7)
  dist/bootstrap.py             # THE distribution (generated; byte-pinned to src by CI)
  src/engine/…                  # source of truth (unchanged from the in-tree layout)
  src/build_bootstrap.py
  tests/                        # the 440-test suite MOVES here (README already promises this)
  bench/                        # §5: pinned harness + append-only results (outside the loop's write reach: CODEOWNERS)
  telemetry/                    # §5 B2/B3: the lab repo's own JSONL feeds
  docs/                         # planted-by-own-medicine docs (§3.3) + program/ (§8)
  docs/program/                 # canonical program law (§8)
  .sessions/  .substrate/       # the kit's own workflow surfaces (dogfood, §3.3)
  .github/workflows/            # §3.2 CI + the substrate-gate the kit ships to others
  CHANGELOG.md  LICENSE  README.md  pyproject.toml
```

### §3.2 CI from birth (this is a SPEC the kickoff executes; the kickoff brief names only "432 tests + check --strict")

One required check (`kit-quality`), mirroring what superbot's CI silently provided and will stop
providing at extraction:

1. `pytest tests/` — the full suite (440 at head; the number is whatever disk says).
2. **Dist-equality pin**: `python3 src/build_bootstrap.py && git diff --exit-code dist/bootstrap.py`
   — the byte-pin currently living in `test_bootstrap.py:22-25` must survive the move.
3. **Engine lint bans**: ruff config recreating the no-print/no-assert/no-subprocess-in-engine
   discipline (today enforced only by superbot's ruff regime).
4. **Scratch-adopt smoke**: `adopt` into a temp dir + `check --strict` green + `adopt
   --wire-enforcement` exit paths (the born-self-verifying clause).
5. **Session gate** (dogfood): `check --strict --require-session-log` on the kit repo itself —
   the kit runs behind its own locked door from PR one.
6. Python floor 3.10 (matrix 3.10–3.13 is productization, deferred).
7. **Repo settings that make the gates BITE** (a CI job blocks nothing by itself): a ruleset on
   `main` making `kit-quality` a **required status check** + "Allow auto-merge" enabled + an
   auto-merge arming mechanism (port superbot's `auto-merge-enabler` workflow pattern, incl. its
   `do-not-automerge`-label skip) + path-scoped required review on `bench/{rubric,tasks,seeds}`
   once those paths exist. Settings are 👤/portal-or-API actions — provisioning row **P10**
   (§7.2) owns them and names who arms what when.

**Ordering note (the §8.3.5 pattern, applied here):** the kickoff brief specs the kit repo's CI
as only "tests + `check --strict` on a scratch adoption" — if the kickoff runs **before** this
plan lands, **KL-1's first act is diffing the kit repo's CI + settings against this section and
landing the delta.** D1's Lands cell says the same.

### §3.3 Dogfooding — the kit repo runs on the kit

The guardrail's true behavior, stated precisely (the naive reading is half-wrong): in the
**source layout** `assert_safe_target` refuses to operate on the kit's own tree
(`guardrail.py:19-35`), but running the **dist single-file**, `_kit_root()` resolves to the
module *file* and the guardrail never engages (`cli.py:98-113`; `guardrail.py:26-27`) — so
`python3 dist/bootstrap.py adopt` into the kit repo works today. Resolution (⚑ D-6): **the kit
repo operates on itself exclusively via `dist/bootstrap.py`** (the file-valued kit_root disarms
the guardrail *by design* — this is the explicit consumer-#0 mechanism for the seed render,
`.substrate/` init, and session-close); the source-layout guardrail stays maximally strict; and
the phantom `examples/` carve-out (the directory never shipped) is deleted. The seed itself is a
**one-time committed render** (reviewable in the seed PR, unlike a live adopt) planting `docs/`
+ `.sessions/` + `.substrate/`; thereafter the kit repo's own docs are ordinary committed files
maintained like any consumer's, upgraded by the same release-diff mechanics (§4.3). This makes
the kit repo consumer #0 honestly: it feels every planted-doc friction its consumers feel.

### §3.4 Generalization worklist (before consumers #2/#3 adopt — band KL-1/KL-2 items)

The audit found near-zero functional coupling (7 docstring mentions) but these defaults/doctrine
items need a ruling each (rulings in §12):

- `reconciliation_prs: 20` default vs superbot's live 30 (Q-0134) → **fix to 30** (stale drift).
- Hardcoded emoji markers (💡⚑⟲📊), born-red/PR-ready doctrine, ADR path, badge taxonomy,
  GUIDED_ROLLOUT order → **declared the kit's opinionated house style, not config** (⚑ D-7);
  documented in one place (`docs/house-style.md` in the kit repo). Config sprawl is a worse
  failure mode than opinionation; a consumer that needs different markers forks the constant.
- `_ENGINE_MANIFEST` (embedded, unused — `init --unpack` never shipped) → **drop from the dist
  build** (dead weight in every consumer's vendored file) unless unpack ships in the same band.
- No LICENSE file (`license = {text = "MIT"}` only) → LICENSE file is a 👤 checklist item
  (the choice is the owner's; MIT is the recorded default).
- `live_ci_workflow` assumes GitHub Actions → accepted for v1 (all program repos are GitHub);
  multi-forge is out of scope (⚑ D-8).

---

## §4 The multi-consumer release discipline

Today a consumer cannot name, pin, verify, or roll back a kit version (§0). The discipline:

### §4.1 Versioning + release artifacts (band KL-1)

- **Semver.** MAJOR = breaking change to the planted-doc contract, state schema, config schema,
  or CLI surface; MINOR = new capability (new checker, new command, new template); PATCH = fixes.
  First kit-repo release: **v1.0.0** (⚑ KF-1).
- **`KIT_VERSION`** constant in `src/engine/lib/config.py`, exposed as `bootstrap.py --version`,
  stamped into the dist header line by `build_bootstrap.py`, and **written into
  `substrate.config.json` as `kit_version` by `adopt`/`upgrade`** — so both the file and the
  install self-identify. (Requires a new `Config` **dataclass field** — `from_dict` silently
  *drops* unknown keys and `save_config` serializes only dataclass fields, so a bare JSON key
  would be stripped on the next load→save round-trip; a defaulted new field is a MINOR
  config-schema addition.)
- **GitHub Release per version**: tag `vX.Y.Z` + assets `bootstrap.py`, `bootstrap.py.sha256`,
  and **`release.json`**:

  ```json
  { "version": "1.1.0", "sha256": "…", "breaking": false,
    "requires_state_migration": false, "min_upgrade_from": "1.0.0",
    "changelog_anchor": "https://github.com/<owner>/<kit>/blob/main/CHANGELOG.md#110",
    "upgrade_steps": ["copy bootstrap.py over the vendored file", "run: python3 bootstrap.py upgrade"] }
  ```

  `release.json` is the machine end of the outbound protocol (§9.2): a consumer routine decides
  "is there an upgrade, is it safe, what do I run" from this file alone.
- **CHANGELOG.md**, keep-a-changelog format, one section per release; the release workflow
  refuses to tag if the section is missing (enforce, don't exhort).
- **Release mechanics**: a `release.yml` workflow triggered by pushing a `v*` tag — builds dist
  fresh, byte-compares to committed, computes sha256, drafts the Release with the three assets.
  Publishing the tag is a lab-loop action (releases are reversible-by-supersession: a bad
  release is followed by a fixed one; **published releases are never deleted** — §6.4).

### §4.2 Consumer pinning + verification

- A consumer's pin = its **vendored `bootstrap.py`** (already the adopt mechanic) + the
  `kit_version` record + the sha256 (verified at upgrade time against `release.json`).
- The kickoff's step-7 pin note for the old superbot repo becomes concrete: superbot records
  `kit_version: 1.0.0` in a `substrate.config.json` next to its in-tree copy and thereafter
  upgrades from releases like any consumer — **this pin-file PR is a named KL-1 companion
  deliverable** (superbot-side, like KL-2's rider PR), because §9's envelope needs its
  `project_id` and D2 verifies on it. Honest scoping: superbot is **not an adopted install** (no
  `.substrate/`, its own session tooling) — it participates in B2/friction **by hand** (agent-
  authored rows/reports against the schemas) until it truly adopts; the in-tree `substrate-kit/`
  source dir deletion stays a follow-up superbot chore.

### §4.3 The upgrade path (the today-missing half — band KL-1)

New CLI verb: **`bootstrap.py upgrade`**. Ordering constraint that makes the diff possible:
the OLD dist's templates must still exist when the diff runs, so **`adopt` and `upgrade` always
archive the running dist to `.substrate/backup/bootstrap-<KIT_VERSION>.py` before anything
else** — the archive exists from v1.0.0 onward, before any future overwrite. The consumer flow
is therefore: download the new file as `bootstrap.py.new` → `python3 bootstrap.py.new upgrade`
(it verifies sha256 vs `release.json`, archives + replaces the old vendored file itself) —
`release.json.upgrade_steps` says exactly this.

1. Re-runs `adopt`'s staging (staged `.substrate/` artifacts always regenerate — the existing
   kit-owned channel; unchanged).
2. **Planted-doc diff report** (the new mechanism). A raw-template compare cannot work — adopt
   plants `with_unrendered_banner(render(template, context))` with slot substitution, banner,
   and a stamped D-0001 date, and `render --live` keeps filling slots over the install's life,
   so template@old never byte-matches even an untouched consumer file. Therefore:
   **"consumer-untouched" is decided by hash, not by re-render** — `adopt`/`render --live`
   record a sha256 of each planted/re-rendered file in `state.json`, and a doc whose current
   hash equals its recorded hash is untouched. The report then classifies per-doc: unchanged
   (template identical across versions) / template-improved-and-consumer-untouched (safe to
   apply with `upgrade --apply-docs`, which re-renders template@new through the *current* slot
   context and re-records the hash) / both-diverged (manual: the report shows the
   template@old→new delta, both rendered through the current slot context for a readable diff).
   **Planted docs are never auto-edited without `--apply-docs`, and never when the consumer
   diverged** — consumer-owned stays consumer-owned. (Pre-1.0 installs have no recorded hashes:
   the first upgrade treats every doc as diverged — honest and safe.)
3. **State migration**: `migrate()` runs transforms keyed by `STATE_SCHEMA_VERSION`; before any
   write, `state.json` is copied to `.substrate/backup/` — which together with the archived
   dist is the **rollback path**: `upgrade --rollback` restores both (staged artifacts
   regenerate from the restored file). State downgrade beyond that is out of contract; that is
   exactly what makes schema changes MAJOR.

### §4.4 Release cadence + gate

- Release when the lab loop has shipped a coherent increment, not on a clock; every release runs
  the full CI + a scratch `adopt`+`upgrade` (from the previous release) smoke.
- Benchmarks are **mandatory-to-run per MINOR/MAJOR** (B1 in its post-auto-draft shape; B3
  rollup) but advisory-to-pass (⚑ KF-5): the release notes must carry the benchmark deltas —
  a release that regresses the A/B says so in its own changelog.

---

## §5 The benchmark suite — the lab's fitness functions

Shared infrastructure first, then the four benchmark families. Every family defines
**computation · data source · results home** (the brief's bar), and every family obeys the
**separation rule**: the graded subject is never the grader; the runner orchestrates but a
different, pinned-rubric judge scores; the lab's warm loop session never grades its own
substrate (A-16 no-self-grading, capture-doc row 5).

### §5.0 Shared harness (`bench/` — band KL-5, pinned via CODEOWNERS like `parity/`)

```
bench/
  rubric/cold-start-rubric.md     # THE written judge rubric, versioned (the twice-lost artifact, now pinned)
  rubric/allocation-rubric.md     # B2's judge rubric (same skeleton, task-class-quality framing)
  tasks/T1.md T2.md T3.md T4.md   # the four task prompt texts, fixed (companion D §3.1)
  seeds/README.md + seeds/make_seed.py  # seed-corpus generator: parameterized toy CLI (~130-200 lines,
                                  # N modules, M passing tests, 1 seeded untested bug) — fresh surface
                                  # names per run (anti-memorization), same shape (comparability)
  score_m1.py                     # scripted M1: words of tool output before first mutating action
  run_ab.py                       # the runner harness: builds arm dirs, spawns cold sessions, collects
                                  # transcripts/diffs/gauges, calls the judge, writes the run record
  results/
    cold-start/index.json         # one row per run (schema below) — append-only
    cold-start/<date>-runNN/      # report.md + metrics.json + transcripts/ (committed; text is cheap
                                  # and the raw-artifacts-were-lost failure must not recur)
    allocation/…  guards/  ideas/ # same pattern per family
```

The `bench/rubric/` + `bench/tasks/` + `bench/seeds/` paths are **pinned against loop
self-modification** — but honestly, in two layers, because the naive mechanisms don't bind:
`parity/`'s real integrity rule is *cross-repo* separation (which `bench/` can't reproduce —
the loop holds contents-RW to its own repo), and a CODEOWNERS file blocks nothing without a
ruleset requiring code-owner review — plus the single-identity trap: a loop PR authored via the
owner's PAT cannot then be *approved* by the owner's identity (GitHub forbids self-approval).
So: **layer 1 (from birth, CI-enforced):** `check_bench_integrity.py` reds any PR that touches
`bench/rubric|tasks|seeds` unless it carries the `do-not-automerge` label — forcing every such
change to sit for review instead of auto-merging; it also enforces results integrity
**append-aware**: existing rows/artifacts under `bench/results/` are immutable, but appending
new rows to an `index.json` and adding new run dirs is exactly what a benchmark run does and is
allowed. **Layer 2 (settings-backed, P10 👤):** the kit-repo ruleset adds path-scoped required
review on those paths (a second machine identity or the owner as reviewer). Until P10 lands the
pin is CI-plus-label — owner-vetoable-but-advisory under silence=consent, stated plainly.
**Creation vs modification:** the one-time KL-5 *authoring* PR is written by a lab session but
labeled `do-not-automerge` and **the first rubric version is owner-blessed** (or at minimum
reviewed by a non-author session) before the first firing depends on it; thereafter any
rubric/tasks/seeds change takes the same path — no deadlock, no self-authored-and-self-graded
rubric drift. *(⚑ D-9: the parity/ *principle* — the oracle sits outside the measured system's
write reach — implemented with in-repo mechanisms since the kit repo has no second repo to
hide the oracle in.)*

### §5.1 B1 — the cold-start A/B as a standing routine

**What it answers:** does adopting the kit make a cold session in a fresh repo work better —
and is the trend improving per release? (The founding challenge: it currently does NOT.)

- **Protocol:** companion D as run twice, with the three routine corrections banked from the
  runs: (1) a **smoke step** — the runner walks one arm manually (adopt + read the tree) before
  any paired run (run 1's root cause was discoverable at setup); (2) **enforcement arms** — ON
  arm adopts with `--wire-enforcement` where the task shape has a merge step, because the kit's
  thesis is now *the door, not the notebook*; (3) task shapes that can exercise the checker/guard
  half (a T5 *break-a-rule* task — introduce a change a kit checker should catch — is added to
  the corpus at first firing; its judge item: did the guard fire and did the session obey it?).
- **Shape per firing:** minimum = the **T2→T4 continuity sequence per arm** (T4 is "continue
  T2's work in a NEW cold session", so each arm's T2 must genuinely run first — 4 sessions
  total) + T5; full 4-task pass per MAJOR release or quarterly, whichever first. Same model both
  arms (Sonnet-class), judge = a different, stronger model; judge model+version recorded per run
  (drift caveat on trends).
- **Sequencing (⚑ KF-5):** first firing happens **after the auto-drafted-handoff build**
  (band KL-5) — the ruling explicitly excludes another same-shape A/B; the baseline series
  starts with the new shape. The twice-failed runs stand as the pre-lab baseline.
- **Computation:** M1 = scripted words-before-first-mutation (`score_m1.py`); M2/M3 = judge
  per pinned rubric, per-pair ON/OFF/tie; pass bar = companion D §5 (F-5) **retained as the flip
  target, not a release blocker**. A trend claim ("the kit now helps") requires ≥3 paired runs
  post-change (⚑ KF-8).
- **Data source:** the run's own artifacts (transcripts, diffs, kit gauges) captured by
  `run_ab.py`.
- **Results home:** `bench/results/cold-start/<date>-runNN/` + one appended row in
  `index.json`: `{date, kit_version, run_id, tasks, m1_on, m1_off, m2, m3, verdict, judge_model,
  notes}` → rendered to the console's kit-lab lane (§7.3).
- **Who runs it:** the lab loop *spawns* it as a dedicated fresh runner session (never inline in
  the loop's own warm context); arms are cold subagent contexts confined to throwaway dirs; the
  judge is a separate invocation seeing only transcripts + rubric.

### §5.2 B2 — the Q-0248 model-allocation dataset + paired A/Bs

**What it answers:** which model tier should run which task class — empirically, program-wide.

- **The record** (one per session/run, every program repo): the console's declared contract is
  the schema of record —

  `{ session, date, model, effort, task_class, tokens_out, outcome }`

  with these field rules: `task_class` ∈ the 8 Q-0248 classes verbatim (docs-only · mechanical
  refactor · test writing · runtime bugfix · kernel/architecture design · review/verify ·
  research · idea/planning); `outcome` is an object `{ci_green_first_push: bool, checker_findings:
  int, merged_pr: int|null, reverted_within_window: bool|null}` (null until the 14-day window
  closes — ⚑ KF-8; the declared lane text implies a scalar — the object is a refinement noted
  with D-10); `tokens_out: int|null` (⚑ KF-9 — no meter exists; null or labeled estimate).
  Unknown extra fields are tolerated (the kit's forward-compat posture).
- **Storage:** per-repo **`telemetry/model-usage.jsonl`** (append-only; JSONL because atomic
  appends beat rewriting a JSON array). The console contract names `model-usage.json → [{…}]`;
  the exporter renders the array from the JSONL — the lane binds to the record shape, not the
  file encoding (⚑ D-10, a contract refinement to note on PR #1802's lane text when convenient).
- **The writer (mechanized — the Phase-2.5 lesson):** sessions self-report `model · effort ·
  task-class` as one machine-parsed line in the run-report footer —
  `- **📊 Model:** <model> · <effort> · <task-class>` — and the kit's `session-close` harvests
  it into the JSONL, computing what it can (date, session slug). `ci_green_first_push` +
  `merged_pr` are backfilled by the lab loop's telemetry sweep (GitHub API read per PR);
  `reverted_within_window` is backfilled after 14 days by the same sweep (revert-commit scan on
  the PR's primary files). **The sweep's credentials:** KF-11's read-only consumer scopes — the
  private consumer repos are unreadable to the lab otherwise. The `📊 Model:` needle becomes a
  required session-log marker via each repo's `session_markers` config (door, not nag) — added
  at upgrade time, suggested by the upgrade report, never forced mid-version (a consumer's gate
  only tightens when it upgrades). Superbot's rows are hand-authored until it adopts (§4.2).
- **The paired A/Bs per class:** reuse the B1 harness (`run_ab.py` with `--family allocation`):
  same real task given to two tiers in cold contexts, judge scores output quality per the
  allocation rubric, objective gates (CI/checkers on the produced diff) decide first, cost
  tiebreaks. Cadence: opportunistic — when the lab backlog has a real task of a class whose
  ladder row is unmeasured or contested; ≥1 class per month is the floor.
- **The ladder + rules (seeded, then data-driven):** defaults seeded from the canonical plan's
  re-keyed §3 rows + the superseded strategy table for the classes the re-keyed rows don't
  cover (kernel/architecture design → Opus/Fable xhigh-max; runtime bugfix + mechanical refactor
  → Sonnet workhorse conditional on an objective gate; test writing → Sonnet; docs-only →
  Haiku/Sonnet ⚑; review/verify → a different model than built it; research → Opus+Sonnet
  fan-out; idea/planning → top tier). Escalate one tier on: two red CI rounds on the same task ·
  a review with ≥2 confirmed defects (N=2) · frozen-grammar/kernel contact. De-escalate after 3
  consecutive matching-quality tasks of the class (M=3). The ladder lives at
  `telemetry/allocation-ladder.md` in the kit repo (program-wide, one home), revised only with a
  citation to dataset rows.
- **Results home:** the JSONL feeds (per repo) + the lab's aggregation
  `bench/results/allocation/` + the console telemetry lane (renders the frontier once rows
  exist). The Q-0249 spend picture is **the same dataset** (rows carry tokens/cost when
  measurable; Railway spend joins via the monthly sweep reading Railway usage API).

### §5.3 B3 — guard-fire / false-positive telemetry

**What it answers:** do the kit's guards catch real mistakes or cry wolf — per guard, measured.

- **The record** (JSONL at `.substrate/guard-fires.jsonl` per adopted repo):

  `{ts, guard, cmd, surface(ci|hook|check), posture(blocking|advisory), finding:{path,kind,message},
  verdict(true_positive|false_positive|accepted_risk)|null, reason|null, judge|null, outcome|null}`

  The kit's uniform `Finding(path, kind, message)` tuple is already the payload; the two
  choke-point writers cover the **local** surfaces (`hook` | `check`): `cmd_check`'s finding
  loop and `cmd_hook`'s dispatch (band KL-3). **The `ci` surface is derived, not written** — a
  JSONL appended inside an Actions runner dies with the job, so the sweep reads the GitHub
  Checks API instead: substrate-gate conclusions per merged PR give the CI fires (findings
  harvested from the job log), and **`did_not_run` is a first-class record** computed the same
  way (a merged PR with *no* substrate-gate check run = a `did_not_run` row — the #1770
  silently-dead-guard class).
- **Triage:** the kit gains the reasons-required allowlist mechanism it currently lacks (port of
  superbot's `*_exceptions.yml` schema: `{path, kind, reason(REQUIRED), triaged, by}`), and
  **creating an allowlist entry IS the false_positive/accepted_risk verdict event**. Grading
  separation: the session whose work triggered the fire may *propose* a verdict; confirmation
  requires a different party — and **when the loop's own work triggered the fire, "a later loop
  firing" does not count as different**: confirmation comes from a consumer session or the
  owner (the same seam as B4's non-loop grader).
- **Computation:** per guard per band: `fires`, `fp_rate = FP/(TP+FP)` over triaged fires,
  `catches` (TP that prevented a merge or was fixed), `did_not_run` count. **Sensitivity leg**
  stays the gate-bites meta-tests (every kit checker keeps a known-bad fixture test — already
  the house pattern); **recall leg**: every bug fixed in a consumer repo gets a
  would-a-guard-have-caught-it row in the sweep (the #1728 precedent — this is judgment work the
  loop does, recorded per bug).
- **Lifecycle rules (⚑ KF-8):** >50% FP over ≥10 triaged fires → recalibrate-or-demote (blocking
  → advisory); 2 consecutive bands with zero fires and zero bite-test value → deletion candidate
  (the Q-0105 disposable posture, mechanized). Promotions (advisory → blocking) require a clean
  band + the fp_rate under 10%.
- **Results home:** per-repo JSONL → lab sweep aggregates to `bench/results/guards/` → console
  kit-lab lane.

### §5.4 B4 — ideas-that-ship-and-survive

**What it answers:** is the lab's "ideas as testable output" claim real — do its ideas ship and
stick?

- **Definitions (mechanical v1, ⚑ KF-8):** an idea **ships** when its entry links a merged PR in
  any program repo. It **survives** when, 30 days after merge, no revert exists (no
  revert-commit referencing the PR; the PR's primary files still contain the change per
  `git log --follow` scan) and the idea was not re-opened. (This 30-day window is the plan's
  mapping of the capture's "within N sessions"; shipping itself is unbounded in time — an idea
  that ships late still counts, in its ship-month's cohort.) **"Worked around" is not
  mechanically detectable, and the loop may not judge it** (it would be grading its own ideas —
  the separation rule). v1: the headline metric uses the revert-scan **only**; the
  `worked_around` column exists but is filled exclusively by a **non-loop grader** — the owner's
  monthly skim or a consumer-session attestation riding the §9.3 receipts channel — and rows
  without a non-loop verdict stay `null`, excluded from the headline.
- **The data source (new convention + its checker in the same PR):** the kit repo's
  `docs/ideas/` entries carry YAML frontmatter — `{state, origin(lab|owner|consumer:<repo>),
  shipped_pr, shipped_repo, merged_date, outcome(open|shipped|survived|reverted|rejected)}` —
  validated by `check_idea_index.py`. Consumer-repo ships flow back via the friction/receipt
  channel (§9.3).
- **Computation (monthly, cohort-wise — never mixed):** ideas are grouped by **generation-month
  cohort**; a cohort is evaluated only at **≥30 days maturity** (its youngest shipped idea's
  survive-window closed). Per mature cohort: generated / promoted / shipped / survived counts +
  acceptance = survived ÷ generated *within the cohort*; the monthly report shows the cohort
  series, not a running mixed ratio (which would systematically understate acceptance while
  young ideas can't yet have survived). Comparing lab-originated vs owner-originated cohort
  acceptance is the honest "is the lab inventing useful things" readout.
- **Results home:** `bench/results/ideas/` + the console Ideas lane gains the outcome fields
  (exporter field-family extension, band KL-6).

---

## §6 The lab loop — the routine

### §6.1 Definition

| Property | Value |
|---|---|
| Name | **kit-lab loop** |
| Trigger | Claude Code console **Schedule**, cron `0 6 * * *` UTC (daily) — ⚑ KF-4; plus the issue-label trigger `friction` (a filed report can fire the loop early) and the API `/fire` endpoint |
| Session shape | fresh session per fire, in the kit repo's environment |
| Model | per the B2 ladder: the loop's own work is mostly `runtime bugfix`/`docs-only`/`review` class → **Sonnet-class default, Opus escalation** per the mechanical rule (⚑ D-11 — and this allocation is itself logged as B2 rows from fire one) |
| Prompt home | `docs/operations/lab-loop.md` in the kit repo (git = source of truth; re-paste to console on change — the proven convention) |
| Run report | superbot footer contract + new token `Run type: routine · lab` |
| Kill switches | console toggle · daily run cap · the Q-0105 disposable posture (unset the trigger, nothing else breaks) |

### §6.2 The prompt skeleton (the 9-part house format, instantiated)

The full paste-ready prompt is authored in band KL-4 as `docs/operations/lab-loop.md`; its
binding skeleton:

1. **Identity/trigger/success:** "You are the KIT-LAB loop… one turn of the kit's
   self-improvement loop. Success = the kit measurably better or its evidence base deeper —
   a shipped kit improvement, a triaged inbox, a benchmark run recorded, or a release published.
   Usually 1–2 complete slices."
2. **Anti-stall:** no valid stop/refuse outcome except genuine irreversible-safety; always ship
   something real; a forced low-value edit is worse than none.
3. **The scope fence (the lab's STRICTLY-DOCS-ONLY analog):** **"You never grade your own
   substrate from your own warm context. Benchmark arms run as cold sessions on throwaway repos;
   judging uses the pinned rubric in a separate invocation. You are runner and builder — never
   the graded subject, never the judge of your own fire, and never the confirmer of a
   false-positive verdict on a guard fire your own work triggered (a consumer session or the
   owner confirms those)."** Plus: never *merge your own change* to `bench/rubric/`
   `bench/tasks/` `bench/seeds/` — propose it on a `do-not-automerge` PR for separate review
   (§5.0); never edit or delete existing rows/artifacts under `bench/results/` — **appends
   only** (`check_bench_integrity.py` enforces both).
4. **Sync-first orient:** fetch/reset main; read the kit repo's CONSTITUTION → current-state →
   newest session log → `docs/program/` deltas → the benchmark trend index.
5. **Inbox triage first** (the CHECK-CODEX-FIRST slot): list open `friction` issues; per report
   apply the three-clause bar (reproducible against the current kit version / a genuine kit
   defect or friction / not a nitpick) — verified-real → fix now or backlog with priority;
   unclear → ask back on the issue; never act blindly on a consumer's claim (Q-0120).
6. **Numbered work:** bugs first → the top backlog slice (the §10 bands until they're done, then
   groomed ideas) → benchmark duties (any due family per §5 cadences; spawn, never inline) →
   release duty (if a coherent increment is sitting unreleased, cut the release per §4).
7. **Ship mechanics:** claim file → born-red card → PR early → auto-merge on green → the kit
   repo's own session gate holds the door.
8. **Self-termination + handoff:** sharpen the kit repo's current-state ▶ Next action
   (DONE/REMAINS/where-stopped); the standing enders (one idea, previous-run review, docs
   audit); the run-report footer with the `📊 Model:` line (B2 feeds on the loop itself).
9. **SAFETY BRAKES:** scoped credentials only — this environment holds no other repo's secrets
   and no live-bot token, ever; `claude/`-branch pushes only; the destructive tier (§6.4) only
   via its reversible paths; production Railway changes to *other* projects are out of bounds
   entirely.

### §6.3 What it may build freely vs flag

Per Q-0241-shaped rails (⚑ D-12 — the lab adopts the *shape*, scoped to its own repo +
surfaces): **build freely** = anything in the kit repo, its own Railway project, its own sites,
its own benchmark/telemetry stores — reversible, audited, flagged on the run report.
**Decide-and-flag prominently** = releases (reversible by supersession), ladder revisions,
governance-home edits (program law changes additionally require the PL-register's provenance
discipline — §8.3). **Ask-first (true safety brake)** = the §6.4 destructive tier + anything
touching another repo's production or credentials (which it structurally cannot hold).

### §6.4 The lab's own destructive tier (enumerated — the program capture left this undefined)

| Action | Path |
|---|---|
| Deleting/retracting a **published release or tag** | never — supersede with a new release; yank note in `release.json` of the successor |
| Rewriting **`bench/results/` history** | never — append-only + checker (§5.0) |
| **Rotating/revoking** its bot token, PAT, or Railway token | 👤 owner action by definition (he holds the portals) |
| **Tearing down** its Railway project/services | ask-first (irreversible spend/URL loss) |
| Deleting **telemetry JSONLs** | retention passes archive (tombstone pattern), never delete raw within the Q-0249 observation window |

---

## §7 Work surfaces + the provisioning checklist

### §7.1 The decided surface order (⚑ KF-3)

**1. The program console** (first — it is the owner's phone-first window and session 1 already
shipped the shell) → **2. the lab's Railway project** (when the console moves at extraction) →
**3. the lab bot token** (👤-gated; no consumer until Discord-facing experiments exist) →
**4. further sites** (the style-guide/design-system assets are shared; new surfaces ride the
same service).

### §7.2 Provisioning checklist (👤 = owner-input; each gates only its own line — the session/kickoff proceeds without them)

| # | Item | Who | Notes |
|---|---|---|---|
| P1 | Create the two repos (or pre-create empty + grant access) | 👤 / kickoff | kickoff brief §4 item 1 |
| P2 | Kit repo CI per §3.2 | kickoff (spec here) | born self-verifying |
| P3 | **Claude Code environment for the kit repo** (env creation is console-side) + its env vars: fine-grained PAT (issues RW + contents/PR for its own repo, ≤1yr expiry noted), later `RAILWAY_TOKEN` (project-scoped) | 👤 creates; lab documents | the scoped-credentials matrix: the lab environment NEVER receives superbot's Railway account token, the live bot token, or any consumer DSN |
| P4 | Arm the **kit-lab loop** routine (paste `docs/operations/lab-loop.md`, schedule `0 6 * * *`, model per §6.1, unrestricted-branch-push OFF, auto-fix PRs ON) | 👤 console (or agent-created trigger + owner kill-switch) | the fleet-doc convention |
| P5 | **Railway project `kit-lab`** at first deploy need (deferrable whole — the kickoff pattern): config-as-code `railway.json`, region `europe-west4`, sealed vars, per-service scoping, notification rule → HQ `#railway-alerts`, workspace soft-limit alert; **no spend caps (Q-0249)** — usage read joins the B2 sweep | 👤 approves/pastes; lab specifies | production-deployment + railway-setup-plan §4/R-3 patterns |
| P6 | **Console move at extraction**: `/console` route + `ds/` assets + a `console.json` producer move from the botsite service to the lab's project; superbot's exporter keeps producing superbot rows; the lab's producer merges program-wide feeds | lab (band KL-6) | the website brief's flagged migration hook |
| P7 | **Discord application "Kit-Lab Bot"** + token into the lab environment; guild = the existing HQ guild first (Galaxy precedent) | 👤 portal action | agents can configure an existing app via API but cannot create one |
| P8 | Published **name** for the kit (substrate-kit is a placeholder; swap point is `pyproject.toml`) + **LICENSE** confirmation (MIT recorded default) | 👤 | blocks nothing; v1.0.0 can ship under the placeholder |
| P9 | superbot files the **first friction report** (proves D4 with a real consumer) — **hand-authored** against the §9.1 envelope schema (superbot is not an adopted install; its `project_id` comes from the KL-1 pin file) | any superbot session | §9.1 |
| P10 | **Kit-repo settings that make the gates bite** (§3.2 item 7): ruleset — `kit-quality` required check + Allow-auto-merge + auto-merge-arming mechanism + path-scoped required review on `bench/{rubric,tasks,seeds}` (needs a reviewer identity ≠ the PR author's — the owner, or a second machine identity) | 👤 portal/API (the P3 PAT has no admin scope) | until this lands, §5.0's layer-1 CI-check + label is the pin — stated honestly there |
| P11 | **Kit-repo visibility flip → public at v1.0.0** (⚑ KF-10) — or, on veto, install the read-only `contents:read` PAT per consumer environment instead | 👤 | what becomes world-readable is listed in KF-10 |
| P12 | **Cross-repo access for the friction/receipt channel**: enable the kit repo in each consumer's workspace GitHub-App scope (consumer sessions currently cannot reach other repos — verified: cross-repo calls are refused until an admin enables them); optionally a user-PAT (ROUTINE_PAT pattern, kit-repo Issues:RW) if the owner wants friction issues to *hot-fire* the loop (app/integration-token-authored issues do not start routines — the #776/#768 evidence) | 👤 admin | without it, §9.1's outbox holds reports until access exists — D4 gates on this row |
| P13 | **Lab read-only scopes on consumer repos** (⚑ KF-11): fine-grained PAT, `contents:read` + `pull-requests:read`, no write, into the lab environment | 👤 | powers the B2/B3/B4 sweeps (§5.2) |

### §7.3 The console's kit-lab lanes (band KL-6)

- Fill the declared **Model & spend telemetry** lane: exporter gains a `telemetry` family
  reading the JSONL(s) → the declared `[{session, date, model, effort, task_class, tokens_out,
  outcome}]` array.
- Add one new declared→real lane **"Kit lab — benchmarks & guards"** with contract
  `bench/results/*/index.json → [{date, kit_version, family, verdict, headline}]` (the brief's
  "kit A/B trends" expectation, currently unbacked by the shipped shell — extend
  `declaredLanes()` + `CONSOLE_TOPLEVEL_KEYS` + `build_console_subset`, which is a deliberate
  code change by design).
- The Ideas lane gains the B4 outcome fields.
- Until the move (P6), these render from superbot's committed `console.json` (the exporter can
  read the kit repo's published `index.json` via the release/raw URL **once KF-10 makes the repo
  public — else via the P13 PAT** — or the lab commits a mirrored snapshot; decide at build
  time, smallest honest mechanism wins).

---

## §8 The program-governance home

### §8.1 Layout (kit repo)

```
docs/program/
  README.md            # what lives here, the citation rule, the sync discipline
  rulings.md           # THE program-law register: [PL-NNN] blocks (D-ledger grammar)
  collaboration-model.md        # canonical program copy (generalized from superbot's)
  agent-decision-authority.md   # canonical program copy (Q-0240/Q-0241 model)
```

### §8.2 The `[PL-NNN]` register

Program-level rulings are **imported** with provenance, one block each, D-ledger grammar
(status/date/supersedes/verdict/why/provenance):

```
## [PL-001] Decide-and-flag over route-up
- status: decided   - date: 2026-07-06
- provenance: superbot Q-0240 (docs/owner/maintainer-question-router.md)
- verdict: …one-paragraph canonical statement…
```

Founding census (the kickoff brief's "Q-0240/41/47/48/49 class"): PL-001 ← Q-0240 ·
PL-002 ← Q-0241 (**verbatim to its provenance**: never-wait, scope = the rebuild program,
owner-extendable — the lab's rails are *not* smuggled into this block) · PL-003 ← Q-0247
(sequencing/rail-before-scale) · PL-004 ← Q-0248 (allocation discipline) · PL-005 ← Q-0249
(observe-first budgets) · PL-006 ← Q-0120 (source-wins / false-green) · PL-007 ← Q-0132
(enforce-don't-exhort) · PL-008 ← Q-0105 (adopt-freely + kill-switch) · **PL-009 — the lab's
own ruling: Q-0241-*shaped* autonomy for the kit-lab** (provenance = the owner-ratified capture
row 5 + Q-0247 ratification + this plan §6.3/D-12 — its own chain, so law never diverges from
provenance). *(⚑ D-13: Q-0243–0246/0250–0253 stay repo-local — pricing, slash-verification,
trading, session logistics are not program law.)*

### §8.3 The sync/citation rule (so law is never duplicated-and-drifted)

1. **One home:** the canonical text of a program ruling exists ONLY in the kit repo's
   `docs/program/`. New program-level rulings are minted there as PL-blocks (by whichever
   session obtains the owner ruling — cross-repo: file it as a kit-repo PR).
2. **Consumers cite, never copy:** planted CONSTITUTION/collaboration-model templates gain a
   short "Program law" pointer section (kit-repo URL + PL-IDs). A consumer's local router holds
   repo-local rulings only; if a local ruling is later promoted program-wide, its local block is
   replaced by a pointer to the new PL (the Q-0210 archive discipline, cross-repo).
3. **Origin blocks get pointers:** superbot's Q-0240/41/47/48/49 router blocks receive a
   one-line "canonical home: kit `docs/program/rulings.md` PL-NNN" rider at migration (a small
   superbot PR in band KL-2). History stays in place; the pointer kills drift.
4. **The checker:** kit-side `check_program_law.py` — PL-register grammar + monotonic IDs +
   provenance-required (extends `check_ledger`); plus a template-side assertion that the planted
   pointer section contains no ruling *bodies* (a copy is a finding). Ships in the same PR as
   the convention (the drift-before-next-session failure mode).
5. **Ordering safety:** if the kickoff (which may run before or after this plan lands) decided a
   different governance shape, its decide-and-flag wins the day and band KL-2's first act is
   reconciling this section to it — stated here so both orderings are safe.

---

## §9 The friction-report protocol

The context-delta loop, cross-repo: consumers file kit-friction; the lab consumes, fixes,
releases; the A/B + friction rate arbitrate. Both legs mechanical enough for a routine.

### §9.1 Inbound (consumer → lab)

- **Producer (already shipped in every adopted repo):** ⚑/💡 lines in session logs →
  `session-close` mines them → `reflections.json` records `{id, lesson, evidence, tags, status,
  date}` (the body field is `lesson`) + the episodic index's ⚑ tag. The friction report's
  payload IS this record shape — no new consumer-side discipline (the Phase-2.5 lesson:
  mechanize, don't exhort).
- **The wire format** (new, band KL-4): `bootstrap.py friction export` — collects the current
  reflections buffer's `flag`-tagged records **plus** a direct session-log scan for un-mined ⚑
  lines (the buffer is a 5-slot rolling window, not an archive — export must not depend on it),
  wraps them in an envelope:

  ```json
  { "schema": 1, "repo": "<github full name>", "project_id": "<config id>",
    "kit_version": "1.0.0", "reports": [ {reflection-record…}, … ] }
  ```

- **Transport (⚑ KF-7):** a **GitHub issue on the kit repo, label `friction`**, JSON in a fenced
  block + a one-line human summary. Filed by the consumer's session-close (best-effort,
  fail-open — the outbox at `.substrate/friction-outbox/` holds reports on **network OR
  credential failure**, drained by the consumer's own next session-close; the lab cannot drain
  it, it has no consumer write access). **Identity, honestly:** consumer sessions reach GitHub
  through workspace-scoped app tokens — cross-repo issue-create works only once **P12** enables
  the kit repo in the consumer's workspace scope; and app/integration-token-authored issues
  **do not fire routines** (the live-verified #776/#768 evidence), so **label-fire is
  best-effort**: the default triage SLA is the loop's daily cron (≤24 h), and hot-fire requires
  the optional P12 user-PAT (the ROUTINE_PAT pattern, cross-repo).
- **Consumption:** the loop's step-5 triage (three-clause bar) → disposition comment + close
  (fixed-in-vX.Y.Z / backlogged / not-a-kit-issue with reasoning). Friction **rate** (reports
  per consumer per band, open-age) is tracked in the B-family sweep — a rising rate after a
  release is the arbitration signal the capture names.

### §9.2 Outbound (lab → consumer)

- **Release notes:** CHANGELOG section + GitHub Release + `release.json` (§4.1) — the complete
  mechanical contract a consumer routine needs.
- **Upgrade PRs — pull model (⚑ KF-2):** each consumer's own routine (superbot: dispatch;
  superbot-next: its equivalent) checks the kit's latest release — **unauthenticated once KF-10
  makes the repo public; via the read-only PAT fallback otherwise, and note the read must run
  where unauthenticated egress actually works (a consumer-side Actions job, or the workspace
  MCP with the kit repo P12-enabled — a bare session `curl` to api.github.com is refused by the
  agent proxy)** — compares to its pinned `kit_version`, and when newer lands a
  consumer-authored PR: replace vendored `bootstrap.py` (sha256-verified) → run `upgrade` →
  commit the upgrade report → its own CI decides. The lab holds no consumer **write**
  credentials; the kit's *adoption diff* (`.substrate/upgrade-report.md`, §4.3) is the PR's
  body evidence.
- **Consumer-routine snippet:** the kit stages `.substrate/ci/upgrade-check.yml.example`
  (a scheduled check that opens/refreshes the upgrade PR) — planted like the CI example,
  installed deliberately.

### §9.3 Receipts (closing B4's cross-repo loop)

A consumer PR that implements a **lab-originated idea** cites the kit-repo idea ID in its PR
body (`kit-idea: KI-NNNN`); the lab's telemetry sweep (which already reads consumer PRs for B2
backfill) matches the marker and updates the idea's frontmatter outcome. No extra consumer
ceremony beyond one PR-body line.

---

## §10 Build bands (the PR-arc) — with named landings

Per the house norm: each band is 1–3 focused PRs; every §11-class deliverable has a **Lands-at**
anchor so nothing evaporates. Bands run in order; KL-2/KL-3 may interleave after KL-1. The
kickoff (session 4) is band zero and NOT this plan's work — but §3.2 is its CI spec and §12 D-1
its seed-shape recommendation. **Who drives:** KL-1…KL-4 are executed by owner-started (or
superbot-dispatched) sessions in the kit repo, using this plan as the band spec — the loop does
not exist until KL-4 authors its prompt and 👤 P4 arms it; **from KL-5 onward the armed loop
takes over** (§6.2 step 6).

| Band | Ships | PRs | Depends on |
|---|---|---|---|
| **KL-0** *(kickoff, session 4)* | Repos exist; kit seeded (subtree-split if cheap, else snapshot+provenance); tests moved to `substrate-kit/tests/`; CI per §3.2; superbot-next adopts; pin notes | — | Q-0247 |
| **KL-1 Release discipline** | *(First act if the kickoff pre-dated this plan: diff kit CI + settings vs §3.2, land the delta.)* `KIT_VERSION` (new Config dataclass field) + `--version` + dist header stamp + `kit_version`/planted-doc hashes in state at adopt/upgrade; CHANGELOG; `release.yml` (tag → assets + sha256 + release.json); **`upgrade` verb** (staged-regen + hash-based planted-doc report + state backup/rollback); `_ENGINE_MANIFEST` dropped; `reconciliation_prs` default → 30; **tag v1.0.0** (👤 P11 visibility flip rides it); LICENSE file (👤 P8, default MIT); **companion superbot PR: the §4.2 pin file** | 2–3 | KL-0 |
| **KL-2 Governance home** | `docs/program/` + PL-register (8 founding blocks) + `check_program_law.py` + template pointer sections + `docs/house-style.md`; companion superbot PR: provenance riders on the origin Q-blocks | 2 (one per repo) | KL-0 |
| **KL-3 Telemetry substrate** | Guard-fire JSONL writers at the two choke points + `did_not_run` markers; reasons-required allowlist port; `📊 Model:` run-report line + session-close harvest → `model-usage.jsonl`; the session-log checker needles; `telemetry/allocation-ladder.md` seeded | 2 | KL-1 (versioned release carries it to consumers) |
| **KL-4 Lab loop + friction** | `docs/operations/lab-loop.md` (the §6.2 prompt, paste-ready) + routine armed (👤 P4); `friction export` verb + outbox + issue filing; `friction` label + trigger; first triage proven on superbot's report (👤 P9); `Run type: routine · lab` | 2 | KL-2 (the loop reads program law) |
| **KL-5 Benchmark harness + auto-draft** | The **auto-drafted-handoff** build (session-close + stop-hook draft the card from git diff + verify state; drafted-vs-completed distinction in the checker) — the ruled prerequisite; `bench/` tree (rubrics — **first version owner-blessed per §5.0** — T1–T5 task texts **copied in from companion D §3 + the F-5 pass bar** (superbot-resident; absolute URLs listed in `bench/README.md` so the spec survives the plan's travel), seed generator, `score_m1.py`, `run_ab.py`, `check_bench_integrity.py` (label-gate + append-aware results rule), the §3.2-item-7 pin paths); **B1 baseline firing** (T2→T4 per arm + T5, post-auto-draft shape) recorded to `bench/results/` | 3 | KL-3 |
| **KL-6 Console feeds + move** | Exporter: telemetry family + the kit-lab lane + B4 idea-outcome fields; **the B4 ideas-frontmatter convention + `check_idea_index.py` (same PR — a convention ships with its checker)**; the P6 console move to the lab's Railway project (with 👤 P5); B2/B3/B4 sweeps live in the loop (KF-11/P13 scopes) | 2 | KL-4, KL-5 |

**Depth honesty (Q-0164):** six bands ≈ 12–14 PRs of specified work — comfortably a full first
band-cycle for a daily loop; no PLAN-BACKLOG-THIN flag. After KL-6 the loop's standing work is
§6.2 step 6 (inbox → bugs → groomed ideas → benchmark cadences → releases), with the deferred
productization arc (§2.2 fence) as the named next horizon.

---

## §11 What NOT to do (carried from the brief + sharpened)

- No extraction, no repo creation here (kickoff owns it, Q-0247); this plan travels.
- No Phase-2.5 re-run before the auto-draft build (ruled sequencing); the twice-failed baseline
  stands and is cited, not litigated.
- No trading-platform design (session 3 owns it); the kit only exposes the surfaces §9 defines.
- No fleet: ONE loop until v1's seven done-conditions hold and the owner has seen ≥1 band of
  run reports.
- No self-graded benchmarks, ever: rubric/tasks pinned outside the loop's reach; graded subject
  ≠ grader ≠ rubric author (A-16 class).
- No fake data on the console; missing feeds declare their contracts (the shipped honesty rule).
- Program law is never copied into a consumer; cite PL-IDs (§8.3).

---

## §12 Decisions log (Q-0240 — every call ⚑-flagged, one-line rationale)

| # | Decision | Options weighed | Rationale |
|---|---|---|---|
| D-1 ⚑ | Kit seed = subtree-split if cheap else snapshot+provenance (kickoff's call affirmed); tests move to `substrate-kit/tests/` at seed | keep tests in host · move | README already promises the move; the host's CI stops running them either way |
| D-2 ⚑ | First release v1.0.0 (not 0.x) with semver keyed to the planted/state/config/CLI contracts (KF-1) | 0.2.0 · 1.0.0 | two real consumers pin it; 0.x semantics would misdescribe a stable adopt contract |
| D-3 ⚑ | Release artifact set = bootstrap.py + sha256 + release.json on a GitHub Release (KF-1) | pip/PyPI · git tags only · Releases+assets | single-file vendoring is the adopt mechanic; Releases give unauthenticated pull + assets + notes in one place |
| D-4 ⚑ | Pull-model upgrades; lab holds zero consumer credentials (KF-2) | lab-authored PRs into consumers · pull | the only shape where Q-0249's scoped-credentials rail costs nothing |
| D-5 ⚑ | Planted-doc upgrades via 3-way diff report, `--apply-docs` only on untouched docs, never on diverged ones | auto-merge templates · report-only | consumer-owned is the kit's core covenant; silent template pushes would break it |
| D-6 ⚑ | Kit repo dogfoods as consumer #0 via hand-planted docs; the phantom `examples/` carve-out retired | adopt-into-subdir · sibling repo · hand-plant | the loop must feel planted-doc friction; a sibling repo splits the lab's identity |
| D-7 ⚑ | Emoji markers / born-red / badge taxonomy = declared house style, not config | config-ify all · house style | config sprawl is the worse failure; consumers wanting different markers fork a constant |
| D-8 ⚑ | GitHub-only for v1 (gates, releases, issues) | multi-forge abstraction | all program repos are GitHub; abstraction without a second forge is speculative |
| D-9 ⚑ | `bench/` rubric/tasks/seeds pinned via CODEOWNERS + no-automerge; results append-only + checker | trust the loop · pin | parity/'s oracle-outside-write-reach rule, ported; twice-lost raw artifacts now committed |
| D-10 ⚑ | B2 contract refinements vs the console's declared lane: storage = JSONL per repo (exporter renders the declared JSON array) AND `outcome` = a structured object, not a scalar | rewrite a JSON array in place · keep scalar outcome | atomic appends; objective outcomes are multi-field by Q-0248's own definition; the lane binds to record shape — note both refinements on PR #1802's lane text when convenient |
| D-11 ⚑ | Lab loop runs Sonnet-class default, Opus escalation, daily `0 6 * * *` (KF-4) | Fable/Opus default · 2-hourly | the loop's task classes are workhorse-tier per the seeded ladder; its own rows are B2 data from day one |
| D-12 ⚑ | The lab adopts Q-0241's *shape* scoped to its own repo/surfaces; its destructive tier enumerated (§6.4) with reversible paths | full Q-0241 · owner-gated loop | Q-0241's letter covers the rebuild; the capture's row 5 prescribes the shape — enumerating the tier makes it enforceable |
| D-13 ⚑ | Program-law census = Q-0240/41/47/48/49 + Q-0120/0132/0105 as PL-001…008; the rest stay repo-local | import everything · minimal census | law that must bind three repos vs rulings about one repo's product |
| D-14 ⚑ | Friction payload = the reflection record verbatim (`lesson` body field) + envelope; export scans logs directly, not only the 5-slot buffer | new schema · reuse | consumers already write this shape; the buffer is a window, not an archive |
| D-15 ⚑ | KF-8's numbers: N=2, M=3, 14d rework window, 30d survive, ≥3 runs per trend claim, >50%FP/≥10 demotion, 2-clean-bands deletion | — | unset letters block runnable benchmarks; seeded conservative, revised by the data they gate |
| D-16 ⚑ | `tokens_out` null-tolerated until a meter exists (KF-9) | block on a meter · estimates-as-truth | no session surface exposes token counts today; fake precision violates the console's honesty rule |
| D-17 ⚑ | B1 adds T5 break-a-rule + enforcement arms; first firing post-auto-draft | same-shape re-run | the checker/guard half is the kit's untested thesis; same-shape is explicitly ruled out |
| D-18 ⚑ | The console is the owner's rollup surface (absorbing the never-built weekly-rollup slot); Hermes' daily rollup remains a superbot-local concern | new rollup doc | one owner surface, phone-first, already shipped as a shell |
| D-19 ⚑ | Bot token deferred behind the console (KF-3); HQ guild first when it lands | token-first · both-at-once | no Discord-facing lab experiment exists yet; a token with no consumer is inventory risk |
| D-20 ⚑ | v1.0.0 may ship under the placeholder name; rename is one `pyproject.toml` swap + a MAJOR-noted release | block on naming | naming is 👤 and blocks nothing mechanical |
| D-21 ⚑ | Kit repo flips **public at v1.0.0** (KF-10/P11) | stay private + per-consumer read PATs | public is the kit's stated OSS destiny and makes every pull/read leg credential-free; the veto fallback is specced |
| D-22 ⚑ | Lab holds **read-only** consumer scopes (KF-11/P13) for the B2/B3/B4 sweeps | consumer-side backfill over the issue channel | read-only repo visibility is not a "prod secret" (Q-0249's rail); consumer-side backfill taxes every consumer forever |
| D-23 ⚑ | B4's `worked_around` column is filled only by a **non-loop grader** (owner skim / consumer attestation); headline metric = revert-scan only | loop judges it | the loop grading its own ideas breaks the plan's own separation rule — the review caught this as a self-decided carve-out from the most important guard |
| D-24 ⚑ | The bench pin is two-layer (CI label-gate from birth; P10 ruleset when armed) and honestly labeled advisory-until-P10 | claim CODEOWNERS alone binds | CODEOWNERS is inert without a ruleset, and the owner's own PAT cannot approve a PR it authored — the review refuted the one-layer story |

---

## §13 Evidence base

Firsthand reads this session: the founding brief · the multi-repo capture (Part 2) · the kickoff
brief · the Phase-2.5 report (§0–§6 incl. both addenda) · companion D · Q-0247/0248/0249 router
blocks verbatim · the autonomous-improvement-loop vision · `agent-decision-authority.md` · the
launch index · the kit README. Seven-lane ultracode research fan-out + completeness critic + 8
gap-fills (kit internals file-by-file audit incl. the release-discipline gap census; ops/routine
fleet + Railway + Galaxy-Bot + dashboard pipeline; guard/checker inventory + gate-bites/allowlist
prior art; idea lifecycle + ⚑-line parsing; rebuild-context conventions + failure modes; the
shipped console-shell contracts @PR #1802 head 7120b79; the re-keyed model ladder; the kit's
reflection/episode record schemas; the two proven routine prompt bodies; template contents).
Source beat docs twice during research (test count 440 vs "432" snapshots; `examples/` carve-out
without an `examples/`): disk wins per Q-0120. **A 4-lens adversarial review fleet
(brief-coverage · source-truth · executability · governance) then ran over the shipped draft**
and its 26 confirmed findings were folded back in — the load-bearing ones: the unprovisioned
repo-settings machinery (→ §3.2 item 7 + P10 + the two-layer §5.0 pin), the undecided kit-repo
visibility (→ KF-10/P11), the broken raw-template three-way diff (→ hash-based §4.3), the lab's
missing consumer read scopes (→ KF-11/P13), the B4 self-grading carve-out (→ D-23), the
bench-results append contradiction (→ append-aware checker), the routine-fire identity reality
(→ §9.1/P12), the B2 product-plane scope statement (→ §2.1-3b), and the D1/KL-1 ordering gap.

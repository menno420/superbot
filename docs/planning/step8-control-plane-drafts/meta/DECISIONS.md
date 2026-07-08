# Step-8 control-plane draft — decisions log (Q-0240 decide-and-flag)

Drafted 2026-07-07 against origin/main `4c25a1f` (docs read fresh: canonical plan
§5/§8/§11/§11b + Q-0241 banner, design-spec §6 verbatim + §1.1/§1.5/§1.6/§2.9/§2.10/§3.2/§5.3,
steps-6–8 brief). Local drafts only; superbot-next untouched. ⚑ = notable, owner-vetoable.

## 1. The per-gate stub-vs-skip table (the key design problem)

Shared doctrine (`tools/gates/_gatelib.py`): **pre-kernel PASS is a positive assertion**
(the whole guarded artifact family is verified absent AND the gate's pinned baselines are
verified virgin), **partial state FAILS**, **armed = real with no workflow change**. No gate
is a bare `exit 0`; every arming trigger is a file-existence or diff condition evaluated on
every run. `tests/test_gate_arming.py` (25 tests, all passing locally under python3.10) is
the standing prove-can-fail harness and runs under gate 1's pytest from day 0.

| Gate (exact check name) | Day-0 pass mechanism | How it blocks later | Arming trigger |
|---|---|---|---|
| `code-quality` | REAL from birth — no stub tier: ruff format+check over the repo, mypy over `tools/gates` (self-hosting), pytest over the day-0 arming tests; pytest exit 5 (no tests) is a FAILURE | red on any lint/type/test failure forever | mypy auto-widens to `sb/` on the first `sb/**/*.py` |
| `manifest-validate` | positive pre-kernel assertion: none of {sb/spec/*.py, compiler, check_namespace, snapshot} exist AND A-2 ledger empty AND A-19 baseline zero | any partial kernel state red; armed: compile + snapshot-drift + namespace on HEAD **and on the git merge-tree result** (§3.2) + validator family + A-2 ledger diff + A-19 ratchet (both directions) | first `sb/spec/**/*.py` or `tools/manifest_compile.py` (S3) |
| `architecture` | rules file (`gates/architecture-rules.yml`, §1.1 table + §1.5 budget encoded) must exist; ledgers verified virgin | armed: inline AST lazy-import ban + module-length budget run immediately; `sb/` code without `tools/check_architecture.py` is red (spec: checker "from commit 1") | first `sb/**/*.py` |
| `sim-gate` | self-arming BY DIFF — arrangement surface empty on both diff sides ⇒ pass via the same comparison that catches real drift | [A]-field change vs merge base without overlay provenance (SimRef/Exempt, §2.10.3) red from the first snapshot commit (inline tier); delegates to `tools/check_sim_gate.py` when it lands (authoritative, S11) | first committed `manifest.snapshot.json`; then first `tools/check_sim_gate.py` |
| `golden-parity` | born-red-by-design is *pending=reported-not-failing*: 43 subsystems + `kernel_governance` all pending ⇒ dashboard report + PASS; schema/one-way-door/A-16 checks already real | ported→pending rejected (one-way door); pending→ported flip requires A-16 100%-or-exempt vs manifest denominators (a flip today fails — correctly); ported subsystems replay goldens fetched read-only at the locked SHA against the day-0 Postgres service container | flips in parity.yml (depth floor); `parity/run.py` + first `ported` (replay) |
| `check_compat_frozen` | positive pre-kernel assertion: lock parses + pins a 40-hex SHA + contract doc present with empty ledger | snapshot-without-reservations red (never green unpinned); reservations validated internally (pin==lock ref, 5 kinds, 43 keys); both present ⇒ verbatim diff, drift red unless a signed compat-contract amendment names every drifted id | `legacy_reservations.json` (S4), then first snapshot (full diff) |

## 2. Decisions

| # | Decision | Rationale |
|---|---|---|
| D-1 | One workflow (`gates.yml`), six jobs whose `name:` = the six exact check names | spec §6 literally: "Required checks (**one workflow**, named gates)" |
| D-2 | Gate logic lives in `tools/gates/run_*.py` (stdlib+PyYAML), not inline YAML | testable (the arming tests), diffable, and the YAML stays a thin pinned shell |
| D-3 ⚑ | CODEOWNERS ships as ROUTING (auto review-request); ruleset does NOT require code-owner approval (`required_approving_review_count: 0`) | single-owner repo: PRs are opened by/for the owner, GitHub forbids self-approval → a blocking rule bricks auto-merge and violates Q-0241 never-wait. Spec §6's "owner review" is delivered as the reaction surface; flip `require_code_owner_review` to true to veto |
| D-4 | CODEOWNERS covers `/gates/` and `/.github/` beyond the spec §6 verbatim set | A-19 says the baseline "joins the CODEOWNERS owner-review set"; the A-2 ledger + architecture rules + the workflows share the identical threat model (silent gate edit = silent gate removal) |
| D-5 | A-19 baseline + A-2 ledger + architecture rules live in a new top-level `gates/` dir, NOT `sb/spec/` | the arming triggers key off sb/'s existence; gate-owned pins must exist day-0 without pre-arming the gates. CODEOWNERS-protected as A-19 requires |
| D-6 ⚑ | Interpreter pinned to **Python 3.12** (fresh repo; old repo stays 3.10) | no legacy pins to honor; discord.py + asyncpg support it; spec names no version — gap filled. Veto = one-line change in gates.yml |
| D-7 | Toolchain = ruff (format+lint) + mypy + pytest + PyYAML, pinned in `constraints/tools.txt` — THE one pin file | spec §6 gate 1: "tool versions pinned in one place… structurally removing the three-way pin-drift class"; ruff replaces black+isort+ruff (one tool, one pin) |
| D-8 | Goldens pin = `parity/goldens-source.lock` (repo `menno420/superbot`, ref `4c25a1fabe63bb790f91e04f9925632913fcd249`, full-SHA, fetch recipe + paths inside) | spec §6 requires "pinned external dependency" but names no mechanism — gap filled; prompt's suggested filename adopted |
| D-9 | ONE lock serves goldens AND compat extraction: S4's `legacy_reservations.json` must carry `extracted_from == lock.ref`, enforced by gate 6 | two pins would drift; compat pins and goldens must describe the same oracle snapshot |
| D-10 | Postgres service container provisioned in `golden-parity` from day 0 | linchpin spike item 4 made the missing container a named failure mode; seconds of cost removes the step-11 discovery risk |
| D-11 | Pins: actions by full SHA (checkout v4.2.2, setup-python v5.3.0), runner `ubuntu-24.04` (never `-latest`), postgres by tag (`16.6-alpine`; digest-pin when replay arms) | prompt + spec determinism requirement; draft pins to re-verify at commit time (see §4 risk R-3) |
| D-12 | `automerge-enabler.yml` carried over (native auto-merge armed at PR-open via `gh pr merge --auto --squash`, GITHUB_TOKEN); `do-not-automerge` label honored; fork PRs skipped | spec §6 "carries over" list; bespoke machinery beyond the native enabler stays dead |
| D-13 | Ruleset: `strict_required_status_checks_policy: false` (branch need not be up-to-date); squash+rebase only; 0 bypass actors | strict=true + auto-merge + agent bursts = re-run churn (old repo precedent); linear history keeps first-parent clean; bypass list empty so even admins go through gates |
| D-14 ⚑ | A-16 exempt reason classes drafted as `requires-live-discord | nondeterministic-external | deprecated-surface | owner-exempt` | A-16 requires "COVERAGE.md-style reason class, never a bare 'flaky'" but no canonical list exists yet; phase 2 aligns with superbot's `_sweep_skips.json` classes |
| D-15 | `kernel_governance` row added to parity.yml beside the 43 subsystem keys | A-16(3): kernel/governance-owned surfaces (~11 of 28 event prefixes) need their own coverage home or they escape every band's floor |
| D-16 | Contracts this draft imposes on S3/S4 tooling are written into the runners' docstrings (snapshot carries `schema_field_inventory`, `arrangement`, `compat_export`; compiler emits `escape_hatch_report.json`; reservations shape) | the gates precede the tools they call; recording the interface at the gate is what lets S3/S4 build TO it instead of the gate retrofitting |
| D-17 ⚑ | **A-22 (permission-tiered operation) deliberately NOT built here** | A-22 verbatim: "Exact grammar carrier (widen `ResourceRequirement` vs a new spec field) decided at the owning K2/K6 fold per R-18; the A-2 schema-growth ledger applies if a new field is minted." The control plane's part is already ready: the A-2 ledger will force the entry when the carrier is minted. Deferred, not dropped |
| D-18 | `check_escape_hatches` + `check_parity_depth` implemented INSIDE gates 2 and 5 respectively — no 7th or 8th check name | A-19 and A-16 both say "no 7th gate"; the six-name vocabulary stays frozen |
| D-19 | Compat amendment sign-off is mechanical: a ledger row in `docs/compat-contract.md` naming every drifted id + the literal token `Signed-off: menno420` (+ Q-number) | spec §6 gate 6 requires "explicitly amended with owner sign-off"; under 0-required-review this is an honesty pattern backed by CODEOWNERS visibility, not cryptographic auth — same trust tier as the rest of Q-0241. Amendment ids are **kind-prefixed** (`custom_id:foo`) to match the gate's `kind:name` tags verbatim — documented in the contract doc |
| D-20 | golden-parity's frozen expected key set (43 subsystem keys + `kernel_governance`) is **hardcoded in the runner** (`FROZEN_KEYS` in `run_golden_parity.py`), not loaded from a side file | a side file — even CODEOWNERS-covered — is one more deletable/emptiable artifact; the runner itself is the one thing that must be edited to change gate behavior anyway, so the set lives where the check lives. Post-S4 the gate cross-checks `FROZEN_KEYS` against `legacy_reservations.json`'s `subsystem_key` kind (note in the runner docstring; update together with gate 6's 43-key assertion, R-8) |
| D-21 | Spec §6's "carries over the session-log discipline" item is **deferred to kit adoption** — the control plane ships no session-card gate/hook of its own | the substrate kit plants the session-card machinery (born-red card, Stop-hook, `check_session_gate`) when superbot-next adopts a kit release (phase 2, R-2); duplicating it here would collide with the kit's planted workflows file-for-file. Deferred, not dropped — phase 2's kit rebase is the landing |
| D-22 ⚑ | **§3.2 merge-race residual gap accepted + scheduled backstop**: the ruleset keeps `strict_required_status_checks_policy: false`, and the `gates` workflow gains `schedule` (6-hourly on main) + `workflow_dispatch` as the detection net | honest trade: strict=true would force every queued PR to rebase+rerun after each merge — with auto-merge + agent bursts on a low-traffic repo that bricks the Q-0241 merge ergonomics (old-repo precedent, D-13). Cost of false: two individually-green PRs whose *combination* collides can land with no PR-time signal AND (GITHUB_TOKEN-armed merges not triggering push runs) no on-main run either. The merge-tree pass (§3.2 phase 2) catches the pair when the second PR's gates run — the residual window is only both merging within one gates-cycle of each other. The 6h scheduled on-main run bounds silent-landed-collision time to hours; boot-time recompile (§3.2 phase 3) remains the final pre-connect net. Flip to strict=true if collision frequency ever makes re-run churn the cheaper evil |

## 3. Doc-vs-prompt / doc-vs-reality drift found

| # | Drift | Resolution |
|---|---|---|
| DR-1 | **Spec §6 lists "auto-delete-head-branches" inside the ruleset sentence; it is a repo setting, not a ruleset field** (GitHub reality; the prompt's summary already flagged this) | set via `PATCH /repos {"delete_branch_on_merge": true}` — settings checklist §1 |
| DR-2 | Kickoff brief step-6 body says create repos "empty, **private**" while its own route-update header + plan §5 step 6 say superbot-next is **deliberately PUBLIC** (owner amendment 2026-07-07) | docs win in their amended part: PUBLIC now, flip-to-private checkpoint later. Verified live: all three repos public |
| DR-3 | Prompt allowed "one workflow or several per spec §6"; spec §6 mandates ONE workflow with named gates | one workflow (D-1) |
| DR-4 | Prompt asked to verify superbot's visibility "e.g. via git ls-remote"; ls-remote here is proxy-authenticated and proves nothing — verified instead via the GitHub API repo object (`"private": false`) | public confirmed; both-postures design retained as a dormant contingency (token-posture §4) |
| DR-5 | Spec §6 CODEOWNERS set predates A-19; A-19 adds the baseline file | union taken (D-4/D-5) |
| DR-6 | No drift found between the prompt's six check names / pending-not-failing / A-2 / A-16 / A-19 / A-22 summaries and the docs — they match the amended plan | — |

## 4. Risks / open questions for phase 2 (rebase onto adopted skeleton)

| # | Risk | Note |
|---|---|---|
| R-1 | **Ruleset-before-checks deadlock**: applying the ruleset before the six check names have reported once leaves PRs waiting on "expected" checks forever | sequencing in settings checklist §3: workflows commit → six greens observed → ruleset applied |
| R-2 | **Kit-adoption collisions**: the adopted skeleton may plant its own workflows/checkers/hook conventions; these drafts assumed a bare repo | phase 2 rebases file-by-file; kit hooks and gates.yml are disjoint by design (gates never call kit tooling) but paths (`tests/`, ruff over kit-planted files) need a real run |
| R-3 | **Draft pins need re-verification at commit time**: action SHAs, `constraints/tools.txt` versions, `ubuntu-24.04` availability | pin freshness is a 10-minute phase-2 task; never commit unverified SHAs |
| R-4 | **Prove-can-fail in real CI**: local arming tests pass (14/14) but the checks must be seen red-then-green ON GITHUB once (e.g. a scratch PR flipping a subsystem to `ported`) before the ruleset is trusted | phase-2 step; also confirms the six names appear exactly |
| R-5 | **ruff/mypy over kit-planted files**: if kit files aren't ruff-clean, day-0 code-quality is red | phase 2 either formats them in the adoption commit or scopes ruff excludes explicitly (never silently) |
| R-6 | **gh CLI availability on the pinned runner** for automerge-enabler | preinstalled on ubuntu-24.04 images today; verify once in R-4's scratch PR |
| R-7 | **Enforcement via API**: applying ruleset + settings needs an admin-scoped token in the executing session; the coordinator session's app token permissions are unverified | if 403, every §1–§4 checklist item has a ready-to-paste OWNER action |
| R-8 | **parity.yml subsystem-set drift**: the 43 keys were extracted from `disbot/utils/subsystem_registry.py` at the locked SHA; if the walk adds/renames before S4, parity.yml must follow the reservations, not this draft | gate 6's 43-key assertion pins the same number — update both together (now also `FROZEN_KEYS` in `run_golden_parity.py`, D-20) |

## 5. Review fixes (2026-07-07) — adversarial-review findings → fixes

Applied against the same draft the same day; each fix carries a regression test in
`tests/test_gate_arming.py` where marked (†). Suite: 14 → 25 tests, all passing.

| Finding | Fix |
|---|---|
| B-1 day-0 code-quality red on the drafts' own files | `ruff format` applied over `repo/`; unused `Path` import dropped (`json` became load-bearing for M-2/M-3); `_gatelib.ok()/fail()` properly annotated `typing.NoReturn` (the `NoReturnHint = None` hack removed); `types-PyYAML==6.0.12.20241230` added to `constraints/tools.txt`; `ruff format --check .` / `ruff check .` / `mypy tools/gates` all verified exit 0 under the exact pins |
| B-2 golden-parity disarmable by row deletion † | `check_key_set`: HEAD key set must equal the hardcoded `FROZEN_KEYS` (43 + `kernel_governance`, D-20) AND no base-side subsystem row may be missing at HEAD; `subsystems: {}` now fails |
| M-1 A-16 depth floor self-grading † | `declared` recomputed from `manifest.snapshot.json`'s `declared_surfaces` (new S3 compiler contract clause) whenever the snapshot exists — any non-null hand-written mismatch fails; while no snapshot exists, any `ported` row fails unconditionally (a flip before the manifest is ungradeable) |
| M-2 A-19 ledger-on-rise unenforced † | baseline diffed against the PR base (`show_at_base`); every risen pinned count requires a NEW `ledger` entry naming that subsystem with non-empty `why` + `rejected_tier2_alternative` |
| M-3 A-2 `frozen_baseline` escape † | new `frozen_baseline` entries (including `ledgered` → `frozen_baseline` flips) rejected in any PR whose base already had a snapshot — the freeze happens once, at S3 |
| M-4 sim-gate downgrade by checker deletion † | `tools/check_sim_gate.py` present at base but absent at HEAD fails, checked before every early-ok path |
| M-5 §3.2 merge-race gap | scheduled 6h on-main `gates` run + `workflow_dispatch` as the detection backstop; residual gap + strict=false trade recorded honestly (D-22 ⚑); token-posture §3 updated |
| m-1 session-log discipline | deferred to kit adoption, recorded (D-21) |
| m-2 amendment token format | kind-prefixed `kind:name` format documented in `docs/compat-contract.md` |
| m-3 A-2 stale entries / empty alternative | ledger entries naming fields absent from the compiled inventory fail; `ledgered` entries with empty `rejected_tier3_alternative` fail |
| m-4 bare `python3` in delegated invocations | replaced with `sys.executable` in all four runners |
| m-5 post-arm `do-not-automerge` label ineffective | `labeled`/`unlabeled` handlers added to `automerge-enabler.yml`: label applied → `gh pr merge --disable-auto`; label removed → re-arm; race window documented (token-posture §3.3) |
| m-6 no .gitignore; cache dirs in tree | `repo/.gitignore` added (`.oracle/`, `__pycache__/`, `.pytest_cache/`, `.venv/`, `.mypy_cache/`, `.ruff_cache/`); `__pycache__` deleted from the draft tree |
| m-7 A-16 exempt rows unvalidated † | exempt rows require a non-empty kind-prefixed `surface`, a reason-class-prefixed `reason`, and are deduped by surface (duplicates cannot pad covered+exempt==declared; `exempt_count` also counts unique surfaces only) |

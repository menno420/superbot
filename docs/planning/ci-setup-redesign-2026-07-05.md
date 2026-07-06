# CI-setup redesign — target-state design + phased migration (2026-07-05)

> **Status:** `plan` — the deliverable of the owner-directed "best-possible CI" session (PR #1737),
> executing the brief [`ci-setup-redesign-brief-2026-07-05.md`](ci-setup-redesign-brief-2026-07-05.md).
> Produced by an 18-agent ultracode workflow (inventory + external best-practice research + a 3-angle
> design panel + 4 adversarial verifiers), every load-bearing claim re-verified against source (Q-0120).
> **Executable config is owner-gated:** this doc *proposes* the workflow/branch-protection/hook changes;
> the safe, additive, reversible artifacts ship with it. The authoritative current-state map is
> [`../operations/ci-what-runs-where.md`](../operations/ci-what-runs-where.md).

---

## A. Executive summary

**The mission:** same coverage with fewer separate checks where that helps reliability, plus the genuine
gaps — designed first-principles, optimizing for **reliability** (owner priority #1) and **cost**
(priority #2), where — because this is a **public repo with free/unlimited Actions minutes** — "cost"
means **wall-clock latency + PR-check clutter + runner contention + merge-race hazard**, not billed
minutes. That reframing is the first correction to the brief.

**The eight decisions that matter:**

1. **One required status context: `ci-gate`.** An `if: always()` fan-in job that fails if any needed leg
   is `failure` **or** `cancelled` (a path-skipped leg is a pass). It replaces `code-quality` as the merge
   gate and structurally kills two hazards at once: a skipped sub-step can't vacuously green the gate, and
   a cancelled superseded head-run can't read as green.
2. **Security enforced by an orthogonal CodeQL merge-protection ruleset, not a status check** — the only
   mechanism that *holds* the merge while CodeQL is in-progress and *blocks* when it's unconfigured,
   closing the Q-0238 race **without** the "required-status-that-never-reports → pending-forever" deadlock
   a bare required-CodeQL-status would reintroduce. Prerequisite: flip `codeql.yml` →
   `cancel-in-progress: false`. Pair it with a **stuck-scan watchdog** (a CodeQL run that starts then
   errors/hangs is the one state the ruleset does *not* bound).
3. **Merge queue is off the table** — `superbot` is a personal-account repo, so the `merge_group` trigger
   is unavailable. The reliability spine is `ci-gate` + `cancel:false` + the CodeQL ruleset + a *corrected*
   dropped-`synchronize` compensator. Merge queue is documented as the future **org-move** upgrade (Phase C),
   which is the categorical fix for the whole dropped-event class.
4. **Consolidate 17 → 14 workflow files and collapse the PR-checks surface to one required context** —
   fold `tool-pins` + `check_architecture` into the python gate; merge `dashboard-ci` + `botsite-ci` into
   one reusable `web-ci.yml`; fold `pr-auto-update` + `pr-conflict-guard` into `pr-freshness.yml`; route
   everything through `ci-gate`.
5. **Ruff replaces black + isort now** (`ruff format --check` + `ruff check` with `I` import rules) — 5
   gate tools → 3, removing two-thirds of the pin-drift surface. **Keep mypy + pytest** (ty is beta with no
   plugin story; pyrefly is too new).
6. **The push+PR "double-fire" is a no-op — dropped.** Verified against source: both heavy workflows
   already trigger `push` on `branches:[main]` only. Nothing to eliminate; the "halved run count" claim is
   deleted. *Corollary:* because `synchronize` is the **sole** delivery path for the head run, the
   dropped-`synchronize` watchdog fix is **more** load-bearing, not less.
7. **Promote local-only coverage to actually block** — `check_architecture --strict` (the #1 gap),
   `check_tool_pins`, the web `mypy`/`pytest` legs, `check_session_slug_unique`, and CodeQL (via ruleset).
   Add the two new guards from the brief as the right class, and promote `check_workflow_concurrency`
   (new, deterministic) to gating.
8. **Fix the self-silencing watchdog.** `check_ci_coverage.py:53` tests *presence of the check-run name*,
   not *satisfaction of the required context* — a `workflow_dispatch` re-kick makes it believe it
   succeeded while the PR stays blocked. Test **required-context satisfaction on the head SHA** (a
   PR-event-triggered run succeeded), escalate to **close+reopen with `ROUTINE_PAT`** (a `GITHUB_TOKEN`
   reopen won't re-arm auto-merge), and cap reopens → owner-alert issue.

### Before → after

| | Before | After |
|---|---|---|
| Workflow files | 17 | **14** |
| Required merge contexts | 1 de-facto (`code-quality`) + 1 **racing** advisory (CodeQL) | **1 status context (`ci-gate`) + 1 merge-protection ruleset (CodeQL, un-raceable)** |
| Python gate tools | 5 (black, isort, ruff, mypy, pytest) | **3** (ruff, mypy, pytest) |
| Heavy-gate runs per PR commit | 1 (already — not 2) | 1 (unchanged) |
| Coverage the gate misses | `check_architecture`, tool-pins, web legs, slug-unique (hook/advisory-only) | **0** (all promoted to `ci-gate` legs) |
| Checkers deleted | — | **1** (`check_doc_freshness`, dormant/unwired) |
| CodeQL merge-race | open (#1728→#1730) | closed by ruleset **+ stuck-scan watchdog** |
| Self-silencing dropped-`synchronize` | present (#1594) | fixed at the correct seam |

### Should the fresh-rebuild repo's CI differ? — **Yes, deliberately.**

Not for cost (minutes are free on both public repos). **Converge** on the *contract + the shared
artifacts*: the aggregate `ci-gate`, ruff, `git merge-tree` + auto-merge-on-green, the read-only `parity/`
golden oracle, and the substrate-kit CI template. **Diverge** on the *grammar-integrity stack* the
manifest-DSL structure makes possible (manifest schema validation, declaration↔engine parity, a
Postgres-backed required golden-parity gate, a frozen-compat check, determinism/complexity AST fences, a
≤7,000-word orientation-budget gate) and the *control plane* (rulesets + OIDC/App tokens from day one, no
PAT accretion). Build it **at the kernel (K10), not now**, and **never** as a live cross-repo
`workflow_call` dependency. Full table in §D.

---

## B. The authoritative what-runs-where matrix

Lives in its own reference doc so any session can read it without this design:
[`../operations/ci-what-runs-where.md`](../operations/ci-what-runs-where.md). It is the ground truth §C
reasons over; read it first.

---

## C. Target-state CI design (current bot)

### C.1 The required-check contract

> A `claude/*` PR merges **iff** (1) the required status context **`ci-gate`** is green on the current
> head **and** (2) the **CodeQL code-scanning merge-protection ruleset** is satisfied (completed on the
> head, no alert ≥ High). Auto-merge is armed at PR open; GitHub merges server-side the instant both hold.
> The born-red `.sessions/` card hold and base-freshness are enforced *inside* (1).

**`ci.yml` — the sole required status context.** The corrected shape (the footguns the verifiers caught
are inline):

```yaml
name: CI
on:
  pull_request: { branches: [ main ] }
  push:         { branches: [ main ] }   # already the state today — NOT a "double-fire" fix
  workflow_dispatch:
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: false              # merge-relevant → NEVER cancel
permissions:
  contents: read

jobs:
  detect:                                # emits nondocs/dashboard/botsite/design booleans
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<sha>     # fetch-depth:0 — the session-gate leg diffs base..head
        with: { fetch-depth: 0 }
      - id: f                            # the PROVEN shell git-diff detector, lifted verbatim from
        run: |                           # today's code-quality.yml — NOT a negated-extglob paths-filter
          ...  git diff | grep -qvE '(\.md$|^docs/|^\.session-journal\.md$)'  ...

  code-quality:                          # reusable python leg (was code-quality.yml)
    needs: detect
    uses: ./.github/workflows/_python-quality.yml
    with: { nondocs: ${{ needs.detect.outputs.nondocs }} }
    permissions: { contents: read }      # explicit — reusable-wf token is caller-capped

  web:                                   # reusable web leg, matrix over the two FastAPI apps
    needs: detect
    if: ${{ needs.detect.outputs.dashboard == 'true' || needs.detect.outputs.botsite == 'true' }}
    strategy: { fail-fast: false, matrix: { pkg: [dashboard, botsite] } }
    uses: ./.github/workflows/web-ci.yml
    with: { package: ${{ matrix.pkg }}, run: ${{ needs.detect.outputs[matrix.pkg] }} }
    permissions: { contents: read }

  design-system:
    needs: detect
    if: ${{ needs.detect.outputs.design == 'true' }}
    runs-on: ubuntu-latest
    steps: [ checkout, 'npm ci', 'npm run typecheck', 'npm test', 'npm run build' ]

  ci-gate:                               # THE ONLY REQUIRED CONTEXT
    if: always()
    needs: [detect, code-quality, web, design-system]
    runs-on: ubuntu-latest
    steps:
      - name: Fail if any leg failed/cancelled, or detect malfunctioned
        if: ${{ contains(needs.*.result, 'failure') || contains(needs.*.result, 'cancelled') || needs.detect.result != 'success' }}
        run: { echo '${{ toJSON(needs) }}'; exit 1 }
```

**Why it can't be silently skipped or raced:** no trigger-level `on: paths:` on the required workflow
(path filtering happens *inside* `detect`; each leg self-skips and `skipped` = pass); `if: always()` +
explicit `needs.*.result` makes `cancelled` a **hard fail**, so auto-merge can't fire on a superseded
head; one stable check name survives job/matrix churn; `cancel-in-progress: false` protects the
merge-relevant run. The real protection against a mis-matching filter is **keeping the proven shell
detector** (not a negated-extglob `paths` expression, which mis-matches silently). The born-red gate
(`check_session_gate.py`, PR-only) stays a step **inside** the `code-quality` leg, so `ci-gate` can't
green while the card is `in-progress`; that leg **must** check out `fetch-depth: 0` or a `--fail-closed`
git error would false-block every PR.

### C.2 The orthogonal gate — CodeQL merge protection (resolves Q-0238)

A branch **ruleset** rule (`code_scanning`) scoped to `main`, requiring **CodeQL** at **High-or-higher**,
using **advanced setup** (the checked-in `codeql.yml`). It is *not* a status check; it composes with
`ci-gate` as an independent merge requirement that **blocks on alert-found, holds on scan-in-progress,
blocks on not-configured** — which is exactly what the advisory-and-slow status check could never do.

- **Prerequisite:** `codeql.yml` → `cancel-in-progress: false` (today it is
  `${{ github.ref != 'refs/heads/main' }}`, i.e. it *cancels* on PR refs — the exact head-run-drop the
  ruleset must not inherit).
- **Residual hole the ruleset does NOT close → bound it with a watchdog.** The ruleset handles
  *in-progress* (holds) and *unconfigured* (blocks), but **not** a CodeQL run that *starts then errors or
  hangs* (autobuild failure, `codeql-action` outage) — a "waits forever" shape on a new axis. Add a
  **stuck-scan leg to `ci-rerun-watchdog.yml`**: on the `*/12` cadence, detect head SHAs with a
  code-scanning analysis pending/errored past a grace window → re-run CodeQL → after K retries, open an
  owner-alert issue.
- **Fork-PR wording (corrected).** "Scope off fork PRs" is **not** a ruleset knob — rulesets scope by
  **base** branch (`main`), which fork PRs merge into. Fork risk is *mitigated* by advanced setup (we
  control re-runs) + admin bypass for the documented default-setup deadlock + this repo's near-zero fork
  traffic — not *eliminated*.
- **Throughput tradeoff (name it).** Merges now proceed at CodeQL's pace (minutes) rather than
  `code-quality`'s (~35 s), and with `cancel:false` uncancelled CodeQL runs accumulate under rapid pushes.
  Correct call (correctness > latency), but "merges the instant both hold" means CodeQL latency on every
  merge. **Owner-gated (G1).**

### C.3 Reliability fixes (corrected mechanisms)

**Mode 1 — CodeQL merge-race** → the §C.2 ruleset + stuck-scan watchdog + corrected fork wording +
latency note. Replaces the journal *exhort* rule ("don't flip the card until CodeQL reports clean") with
enforcement. **Owner-gated.**

**Mode 2 — dropped `pull_request:synchronize`** → keep `ci-rerun-watchdog.yml`; **fix
`check_ci_coverage.py`**:
- Test **required-context satisfaction on the head SHA** via check-run enumeration — confirm a
  **PR-event-triggered** (not `workflow_dispatch`) run of the required context **succeeded**. The current
  `required not in check_run_names` (line 53) is a pure presence test, so a dispatched re-kick looks like
  success while the PR stays blocked. Extend the already-injected `fetch_head(sha)` seam to return each
  run's trigger source + conclusion. **Do NOT use `mergeable_state`** — this repo abandoned it twice
  (#959 BEHIND-skip, #1104 UNKNOWN-window) for deterministic `git merge-tree`.
- Escalate the re-kick from `workflow_dispatch` → **close+reopen with `ROUTINE_PAT`** (a `GITHUB_TOKEN`
  reopen does **not** re-trigger `auto-merge-enabler`, so the reopened PR never re-arms auto-merge).
- Add a **per-PR reopen counter** → after K reopens, open an owner-alert issue instead of churning PR
  history every 12 min.
- Correct the **false header comment** in `code-quality.yml` claiming a dispatched run satisfies the
  required context.

**Mode 3 — cancellation race** → `code-quality`/`ci.yml` already `cancel-in-progress: false`; **flip
`codeql.yml` → `false`** (harmless today, mandatory once §C.2 makes it required). Encode the invariant as
`check_workflow_concurrency.py` at **class G** — a deterministic YAML parse with ~0 false positives; a
warn-only check can't *prevent* a future merge-relevant `cancel:true` shipping. **Pairing (state it):**
`cancel:false` guarantees the *head* run completes, not *every* commit's — a third rapid push still
cancels the *pending middle* run; this is safe **only because** `ci-gate` keys on the final head SHA and
treats `cancelled` as failure. Document the two together.

**Mode 4 — born-red timing + fail-open gate** → keep `check_session_gate --diff-filter=AM` (BUG-0027);
add a `--fail-closed` CI mode (a git failure blocks, not opens) while the local hook stays fail-open; this
**requires `fetch-depth: 0`** on the session-gate leg. **Honest scope:** the CodeQL hold enforces flip
discipline **only for the CodeQL-alert sub-case (#1728)**. The other born-red incident (**#794/#797** —
close-out docs pushed *after* the first green head already merged) is a *content-completeness* race that
CodeQL's hold does nothing for, and `check_session_log`/`check_current_state_ledger` are deliberately
class-A. **So the missing-docs merge race remains exhortation, not enforcement** — see decision **G8**.

### C.4 Consolidation moves

| Move | Mechanism | Risk / ship |
|---|---|---|
| **Ruff replaces black+isort** | `ruff format --check` + `ruff check` (`I`). One atomic PR: `ruff format` the tree, **port `[tool.ruff.lint.isort]`** (`known-first-party`, black-profile equivalents) or you get a *second* import-reorder churn, verify magic-trailing-comma vs `black 26.5.1`, and swap black/isort→ruff in `code-quality.yml` **+** `requirements-dev.txt` **+** `.pre-commit-config.yaml` **+** `check_quality.py` **+** `claude_post_edit.py` (the PostToolUse auto-fixer) **in the same commit** — or local hooks reformat with black and fight CI every edit. | medium; SAFE-ADDITIVE (its own focused PR) |
| **`web-ci.yml` matrix** | reusable `workflow_call` (`package` input), `defaults.run.working-directory`, `design-system/**` dependency edge in both filters, `run:'false'` → no-op success leg, **explicit `permissions:`**. Realizes [`web-tier-centralization-proposal-2026-06-19.md`](web-tier-centralization-proposal-2026-06-19.md). | build+dual-run = SAFE; delete originals = OWNER-GATED |
| **Fold `tool-pins` → python gate step** | `check_tool_pins.py` (stdlib, seconds) as an always-run **G** step (closes #1315 as a *block*, not just red). | add step = SAFE; delete file = OWNER-GATED |
| **Fold `design-system-ci` → inline path-gated job in `ci.yml`** | one job. | build = SAFE; delete file = OWNER-GATED |
| **Fold `pr-auto-update` + `pr-conflict-guard` → `pr-freshness.yml`** | two jobs, shared merge-state helper; keep the conflict-guard PR-event + `*/30` legs + its `cancel:true`. | build = SAFE; delete originals = OWNER-GATED |
| **`uv` for CI install; composite `setup-py310`** | latency-only. | SAFE |
| **SHA-pin remaining actions** | 40-char SHA + `# vX`; top-level `permissions: contents: read`; Dependabot `github-actions`. (`checkout`/`codeql-action` already pinned.) | SAFE |
| **Keep mypy + pytest** | do not swap (ty beta; pyrefly too new). Optional non-blocking pyrefly advisory job. | keep |

### C.5 Gaps to add (each into the right class)

| Gap | Check | Class | Home / why |
|---|---|---|---|
| CodeQL-in-hold (Q-0238) | merge-protection ruleset + stuck-scan watchdog | **G (ruleset)** + infra | §C.2. OWNER-GATED |
| Merge-relevant workflow cancels | **NEW `check_workflow_concurrency.py`** | **G** | deterministic YAML parse, ~0 FP; encodes Mode 3 |
| Audit-seam bypass | **NEW `check_audit_seam.py`** ([idea](../ideas/audit-seam-coverage-checker-2026-07-05.md)) | **A → G** (warn-first one band → block) | would have caught 3 of the 8 #1728 save-fixes bugs |
| Deferred/restart recovery | **NEW `check_deferred_recovery.py`** ([idea](../ideas/deferred-action-restart-recovery-checker-2026-07-05.md)) | **A** (Q-0105 kill-switch) | guards the Railway-redeploy-drops-timer class (Q-0193) |
| Architecture at the merge layer | existing `check_architecture --strict` | **G** | was Stop-hook-only — the #1 gap |
| Anti-clobber session slug | existing `check_session_slug_unique` | **G** | BUG-0027, author-time |
| Governance-file presence | existing `check_governance_files` (UNUSED) | **G** | folded into `check_docs` |
| dashboard.json validity | existing `check_dashboard_data` | **G** | web-ci dashboard leg |

**Placement discipline:** only low-false-positive invariants that can *silently* reach `main` become
**G**. New heuristics enter **A** with a Q-0105 header and graduate. Drift/hygiene/planning stays **A/R** —
blocking a code PR on planning-doc drift is the wrong altitude.

### C.6 The hook ↔ CI split

Keep the local hooks (speed) **and** add the CI authority (truth). The two moves that matter:
`check_architecture --strict` gets an explicit **CI step** (SAFE-ADDITIVE — the script already runs at
Stop); a `check_consistency` **Stop mirror** is a script change (SAFE) but its `settings.json` *wiring* is
**owner-gated (G5)**. A changed-module fast-pytest subset on Stop is an owner-gated proposal (latency).

---

## D. Fresh-repo CI design + converge/diverge

The greenfield `sb/` repo is a **Python-dataclass manifest-DSL** (generate ~85% / hand-write the ~15%
hatch) on discord.py, **single package**, with a **Postgres-backed parity oracle**. Its required-check set
is *already designed* in `rebuild-design-spec-2026-07-02.md` §6. Two corrections this session contributes:
**cost = latency, not minutes**, and **the required workflow must provision a Postgres service container**
or the `golden-parity` gate can't run.

**Single workflow, single required `ci-gate`** (one package → no path-filter/matrix apparatus). Legs:
1. **`code-quality`** — ruff (format + lint + import-sort) + a type checker (pyright or pyrefly-1.0 —
   greenfield freedom) + pytest under pinned 3.10, tools from **one** pin file; uv end-to-end.
2. **`manifest-validate`** (required) — compile the manifest, `manifest.snapshot.json` drift, namespace
   collisions (incl. on the `git merge-tree` result), and the declared validators (never-strand,
   destructive-requires-confirm, egress-honesty, layout/ownership coverage).
3. **`golden-parity`** (required, **Postgres service container**) — replays `parity/goldens/` for
   `ported` subsystems; green is a one-way door. The biggest infra delta.
4. **`sim-gate`** — arrangement changes carry a simulator "why-it-won" record.
5. **`check_compat_frozen`** — pinned compat artifacts (custom_ids, event literals, AITask names, audit
   payloads) vs the manifest export.
6. **`architecture`** — the `sb/` layer table rendered *from* checker config, lazy-import ban, complexity
   budget, clock/RNG determinism fences, `asyncio.create_task` ban — **error-from-commit-1, empty
   exception file**.
7. **`orientation-budget`** (required) — fails if the hand-written boot-read set exceeds **~7,000 words**
   (vs ~25,300 today).

Control plane: **rulesets + OIDC/GitHub-App tokens from day one** (no PAT accretion), native
auto-merge-on-green armed at open, deterministic `git merge-tree` conflict check, CodeQL merge-protection.

### Converge / diverge table

| Dimension | Current bot | Fresh repo | Verdict |
|---|---|---|---|
| Aggregate `ci-gate`, one required context | ✅ (this design) | ✅ | **CONVERGE** |
| ruff (format+lint+import-sort) | adopt now | day one | **CONVERGE** |
| Type checker | mypy (keep the working gate) | pyright / pyrefly-1.0 | **DIVERGE** |
| pytest, `git merge-tree`, auto-merge-on-green at open | ✅ | ✅ verbatim | **CONVERGE** |
| Born-red card / substrate discipline | present, 40 checkers | consolidated to kit `check --strict` + a `[D-NNNN]` decision ledger | **CONVERGE (pattern), DIVERGE (impl)** |
| Layer checker | 6-layer, grandfathered warnings | `sb/` table from config, error-from-empty + complexity + clock/RNG fences | **DIVERGE** |
| manifest-validate / sim-gate / golden-parity / compat-frozen | none | required | **DIVERGE** (the point of the rebuild) |
| Postgres in *required* CI | no (parity is manual `parity-replay.yml`) | **YES** | **DIVERGE** (biggest infra delta) |
| Orientation-budget gate | none | ≤7,000-word required | **DIVERGE** |
| CodeQL merge-protection | adopt now (§C.2) | day one, consciously sequenced | **CONVERGE (mechanism)** |
| Control plane / self-healing watchdogs | `ROUTINE_PAT` on ~7 workflows + `ci-rerun-watchdog` + `check_ci_coverage` | **PAT accretion dies; the watcher *routines* carry over on app tokens.** The dropped-`synchronize` compensator is **still needed** unless the fresh repo is **org-owned with merge queue** — OIDC/app-tokens do NOT fix GitHub dropping event delivery. | **DIVERGE (auth), CONVERGE (watcher function persists)** |
| App-CI (dashboard/botsite/design-system) | web-ci matrix + design-system | dashboard is a generated read-only projection, so the app-CI surface *likely* simplifies. **This is a current-repo inference, not a rebuild-spec commitment.** | **DIVERGE (inferred, hedged)** |
| `parity/` golden oracle | authored here (live capture) | consumed **read-only as a pinned external dep** (outside its write reach) | **CONVERGE — the one true shared artifact** |
| substrate-kit portable checkers + CI template | source | consumer | **CONVERGE (patterns only)** |

**Shared reusable-workflow verdict:** converge via the substrate-kit `.substrate/` CI template + the
shared read-only `parity/` artifact; **do NOT wire a live cross-repo `workflow_call` dependency** —
coupling a frozen reference repo's required check to the evolving new one recreates exactly the
merge-race/coupling hazard the rebuild escapes.

**Timing:** the fresh CI is *already designed* (§6 is the spec-of-record) but must be **built at the
kernel (K10), not now** — its gates consume artifacts (the manifest snapshot, `parity.yml`, compat
exports, the layer-checker config) that exist only once the manifest compiler + kernel do ("repo born red
on parity, green on everything else"). What *can* progress now on the critical path: the substrate-kit's
portable checkers + `.substrate/` CI template.

---

## E. Phased migration plan

**Reversibility invariant:** every Phase-A step is a one-commit-revertible workflow/script edit; `ci-gate`
runs **non-required** (A8) before it is ever required (B2), so cutover is observed-then-committed. Every
Phase-B step is a settings toggle or file deletion recoverable from git, **applied by the owner** — no
agent self-applies a required-context removal, workflow deletion, ruleset/branch-protection change, or
`settings.json` hook rewire (Q-0106).

### Phase A — SAFE-ADDITIVE (ship without owner sign-off; no required-context change, no settings.json, no branch protection)

> **Progress (2026-07-05):**
> - **G1 CodeQL merge-race — CLOSED.** The owner enabled the **`codeql-merge-protection` ruleset** on
>   `main` (Require code scanning results · CodeQL · High-or-higher · Active). Auto-merge now waits for
>   CodeQL and blocks on a High+ alert — the #1728→#1730 race is resolved. Prereq A1 shipped (#1739).
> - **A1 shipped (#1739)** — `codeql.yml` → `cancel-in-progress: false`.
> - **A6/A7 gating half shipped (#1739)** — `check_architecture --mode strict`, `check_tool_pins`,
>   `check_workflow_concurrency` are now **hard steps in the required `code-quality` context** (gate with
>   no branch-protection change), each verified green on `main` first.
> - **A2 shipped (this PR)** — `check_ci_coverage.py` de-self-silenced (event-classification + escalate).
> - **Still pending → turn-key backlog:** [`ci-followups-handoff-2026-07-05.md`](ci-followups-handoff-2026-07-05.md)
>   (ruff migration A3, the `ci.yml`/`web-ci.yml`/`pr-freshness.yml` builds A5/A8/A9, the CodeQL stuck-scan
>   watchdog A10, the two AST guards, `check_session_slug_unique` gate, and the owner-gated Q-0239 tail).

- **A1.** ✅ **SHIPPED (#1739).** Flip `codeql.yml` → `cancel-in-progress: false`. *(Mode 3 + §C.2 prerequisite; reversible one-liner.)*
- **A2.** Fix `check_ci_coverage.py` (check-run-enumeration + `ROUTINE_PAT` close+reopen + reopen cap →
  owner-alert issue); correct the false `code-quality.yml` header. **Rename coupling:** `REQUIRED_CHECK`
  (line 37) + the dispatch target flip to `ci-gate` in lockstep with **B2**.
- **A3.** Ruff migration PR (atomic — its own focused PR; see §C.4 for the 5-file swap).
- **A4.** Audit-pin remaining actions; top-level `permissions: contents: read`; Dependabot `github-actions`;
  composite `setup-py310`; adopt `uv`.
- **A5.** Build `web-ci.yml` (reusable, explicit `permissions:`) and **dual-run** beside the app-CI
  workflows; do not delete originals yet.
- **A6.** Add always-run **G** stdlib steps to `code-quality.yml` (still under the existing `code-quality`
  context — no protection change): `check_architecture --mode strict`, `check_tool_pins`,
  `check_session_slug_unique`, `check_governance_files` (via `check_docs`).
- **A7.** Add **A** (`continue-on-error`) steps: `check_current_state_ledger --strict`,
  `check_migration_collision` (path-gated), `check_permission_overlap` (path-gated),
  `check_routine_permission_surface`, `check_session_log`, new `check_audit_seam` (warn-first), new
  `check_deferred_recovery`, new `check_workflow_concurrency` (ship at **A**; promote to **G** in B4).
- **A8.** Build `ci.yml` (`detect` with the proven shell git-diff detector, `fetch-depth:0`,
  `needs.detect.result` assertion, the legs, `ci-gate`, inline design-system job) **alongside** the old
  workflows, `ci-gate` **non-required**; observe green/red parity vs `code-quality` across several PRs
  (code-only + docs-only). Add concurrency groups to `parity-replay.yml` + `ai-evals.yml`; surface
  "CodeGraph: DISABLED" in the SessionStart banner.
- **A9.** Build `pr-freshness.yml` alongside `pr-auto-update` + `pr-conflict-guard`; observe parity.
- **A10.** Add the CodeQL **stuck-scan leg** to `ci-rerun-watchdog.yml` (alerting-only first).

### Phase B — OWNER-GATED (propose; each is item-by-item ratifiable in §F)

- **B1 (branch protection).** Enable the CodeQL merge-protection ruleset (High+, advanced setup). *Resolves
  Q-0238.*
- **B2 (branch protection, ATOMIC).** After A8 proves parity, in **one change**: make `ci-gate` required
  **and** remove `code-quality` from the required list **and** reshape `code-quality.yml` →
  `_python-quality.yml` (`workflow_call`) **and** flip `check_ci_coverage.REQUIRED_CHECK` → `ci-gate`. These
  **must be simultaneous** — any ordering that leaves `code-quality` required after the reshape sticks every
  PR at "Expected — Waiting for status to be reported" forever. *(Alternative avoiding the branch-protection
  edit: name the fan-in job's check `code-quality` so the existing required context is satisfied — owner's
  call.)*
- **B3 (delete workflows).** Delete `dashboard-ci`, `botsite-ci`, `tool-pins`, `design-system-ci`,
  `pr-auto-update`, `pr-conflict-guard` after a full band of dual-run parity.
- **B4 (flip warn→block).** Drop `continue-on-error` on `check_audit_seam` (→G) and promote
  `check_workflow_concurrency` → G after a clean band.
- **B5 (settings.json hooks).** Wire the `check_consistency` Stop mirror and (optionally) the changed-module
  fast-pytest subset.
- **B6 (branch protection, optional).** "Require branches up to date before merging." **Recommend OFF** —
  `pr-freshness` + `ci-gate`-on-final-head already cover it, and it serializes merges.
- **B7 (retire dead checker).** Delete `check_doc_freshness` (dormant/unwired, Q-0105). **Keep
  `check_plan_staleness`** (unique recon-band + idea-shipped signals).

### Phase C — future, org-move only
Add `merge_group:` to `ci.yml` + all required legs; the bot **enqueues** rather than arms auto-merge;
handle `merge_queue.destroyed` with `cancel-in-progress: true`; **retire `ci-rerun-watchdog` +
`check_ci_coverage`** (the required check recomputes at enqueue — the categorical fix for Modes 1+2).
Switch §C.2 CodeQL to a poll-gate (rulesets don't apply to `merge_group`).

---

## F. Open owner decisions (ratify item-by-item)

| # | Decision | Recommended default | Provenance |
|---|---|---|---|
| **G1** | Enable the **CodeQL merge-protection ruleset** (High+, advanced setup), with the A1 `cancel:false` prerequisite + the A10 stuck-scan watchdog, accepting merges now proceed at CodeQL's pace and fork PRs rely on admin bypass. | **APPROVE** — closes the real #1728→#1730 alert-in-main defect; the residual (infra-failure hold) is compensated by A10. | Q-0238 (extend) |
| **G2** | **Atomic required-context swap** `code-quality` → `ci-gate` + reshape to `_python-quality.yml`, after A8 proves parity. (Alt: name the fan-in check `code-quality` to avoid the branch-protection edit.) | **APPROVE the swap** once parity is observed; prefer the real rename for a stable long-term name. | new Q-0239 |
| **G3** | **Delete six folded workflows** after a full band of dual-run parity. | **APPROVE** after the parity band. | new Q-0239 |
| **G4** | **Promote to G:** drop `continue-on-error` on `check_audit_seam`; promote `check_workflow_concurrency` A→G, after a clean band. | **APPROVE** — both are low-FP invariants that can silently reach main. | new Q-0239 |
| **G5** | **settings.json Stop-hook rewires:** `check_consistency` Stop mirror; optional changed-module fast-pytest. | **APPROVE the consistency mirror** (cheap AST); **defer fast-pytest**. | Q-0106 (hook wiring owner-gated) |
| **G6** | **"Require branches up to date before merging."** | **REJECT / LEAVE OFF** — covered by `pr-freshness` + `ci-gate`-on-final-head; serializes merges. | new Q-0239 |
| **G7** | **Delete `check_doc_freshness`** (dormant/unwired, Q-0105); **keep `check_plan_staleness`**. | **APPROVE the single delete**. | Q-0105 |
| **G8** | **#794-class content-completeness race:** accept it stays *advisory* (badge=G, docs=A), or add a narrow "close-out docs present when the badge flips" G check. | **ACCEPT ADVISORY + document it** — a session legitimately editing the ledger is common; a presence gate risks false-blocks. Revisit if #794 recurs. | new Q-0239 |

---

## G. What shipped with this doc (safe, additive, reversible)

Per the ownership split (checker/test/doc guards are free; hooks/settings.json/branch-protection are
owner-gated), the PR that carries this design also ships:

- **This design doc + the [what-runs-where map](../operations/ci-what-runs-where.md)** — the CI ground
  truth nothing captured before.
- **`scripts/check_workflow_concurrency.py`** (+ unit test, 8/8 green) — the deterministic guard for the
  cancellation-race invariant (Mode 3 / decision G4). It flags `codeql.yml`'s current
  `cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}` today — i.e. it *is* the A1 tell — and
  passes `code-quality.yml` (`false`). Shipped standalone (not yet a CI step; wiring is A7/B4).

**Deliberately NOT shipped as code this session — the two AST guards.** Calibrating them against source
(recorded in each idea doc) showed the naive heuristics would be **noise**: `check_audit_seam` scoped to
`*_mutation.py` is a ~42%-FP signal (5 of 12 modules legitimately lack `emit_audit_action`) **and** misses
the actual #1728 bug class (which lives outside the mutation seam) — it needs repo-wide per-function
reachability; `check_deferred_recovery` on raw `asyncio.sleep` hits 23 files, mostly UX-animation/infra
false positives — it needs the `tasks.spawn`-target discriminator. Both are warn-only heuristics their own
idea docs prescribe validating over several sessions before trusting. Per "forced filler is worse than
none," this session ships the **precise signal + ground-truth calibration** in
[`../ideas/audit-seam-coverage-checker-2026-07-05.md`](../ideas/audit-seam-coverage-checker-2026-07-05.md)
and [`../ideas/deferred-action-restart-recovery-checker-2026-07-05.md`](../ideas/deferred-action-restart-recovery-checker-2026-07-05.md)
so a focused follow-up builds them validated, not a stub that gets worked around.

Everything that edits a `.github/workflows/*.yml`, `.claude/settings.json`, or branch protection is left as
the **proposal** above (Phase A workflow builds + all of Phase B), for owner ratification — that is the
brief's guardrail.

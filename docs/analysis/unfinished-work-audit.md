# Unfinished Work Audit

## Executive summary

- **Overall readiness judgment:** SuperBot is active and shippable, but the repo is not “done”: the safest reading is a mature live bot with several intentionally gated product/ops lanes and a smaller set of source-confirmed unfinished implementation tails.
- **Highest-risk unfinished areas:** BTD6 answer correctness live verification, Advanced Setup draft→Final Review cleanup, unconsumed mining/equipment stats, owner/Hermes-only website/control-plane rollout, and test coverage hidden behind optional/live dependencies.
- **Actually blocked vs startable:** Startable offline work exists in S1 setup cleanup, S1 fishing acquisition depth, S3 procedures→skills Batch 2, and S3 self-test harness. Blocked/gated work includes BTD6 live `llm_judge`, owner website cutover, control-panel security slices, Project Moon live walk, reaction-role web builder, and visual taste/art decisions.
- **Recommended next destination:** a narrow **Codex** or **Claude Sonnet** execution session for one offline tail at a time; owner/Hermes items should remain explicitly non-implementation until credentials, live bot, VPS, or product choices are available.

## Repo state checked

- **Branch / commit:** `work` at `1e711ec5d43c557f0671e65b4ceeae07ff7cc2e5`.
- **Open PRs checked:** attempted via `gh pr list`; `gh` is not installed in this container, and public web search did not expose the private/live PR list. This audit therefore treats local `HEAD` plus repo docs as the available merged-state view and flags the GitHub check as incomplete.
- **Open issues checked:** attempted via `gh issue list`; blocked by missing `gh`.
- **Recent merged PRs checked:** not available through `gh`; local current-state/reconciliation files summarize through the band-#1500 pass.
- **Current-state / S1–S5 sector files checked:** `docs/current-state.md`, `docs/current-state/S1-bot.md`, `S2-btd6.md`, `S3-ai-memory.md`, `S4-docs.md`, `S5-ops.md`.
- **Roadmap / sector map / folios checked:** `docs/roadmap.md`, `docs/repo-sector-map.md`, `docs/planning/README.md`, `docs/subsystems/`, `docs/health/bug-book.md`, `docs/architecture.md`, `docs/ownership.md`, `docs/runtime_contracts.md`, `.claude/CLAUDE.md`, `docs/AGENT_ORIENTATION.md`, `docs/collaboration-model.md`, and owner workflow docs.
- **Commands/searches run:** see Appendix.

## Active gates and blocked scope

| Gate / blocker | Source | Scope blocked | Impact on next work |
|---|---|---|---|
| Live bot / provider credentials | S2 current-state, BTD6 probe, P1-1 docs | Proving the model actually uses grounded BTD6 facts via live `llm_judge` | Do not claim BTD6 AI correctness complete from offline grounding alone. |
| Owner visual/product choices | S1 current-state, visual card/fishing plans | Mining render rebase, image-card taste, fishing shore cap, creature balance/art | Keep as owner/manual review unless a repo-local default is explicitly accepted. |
| Owner/Hermes operational rollout | S5 current-state, operations handoff | Website two-site split deployment, submissions DB provisioning, domain cutover | Repo code can be reviewed; rollout is not normal in-repo implementation. |
| Security-review-gated control-plane slices | S5 current-state, dashboard/control API docs | Control-panel migration, live status aggregator | Needs security review before implementation/promoting to build. |
| GitHub live metadata unavailable in this container | `gh` missing | Open PR/open issue/recent merge classification | Findings are repo-grounded but cannot rule out an open PR already covering an item. |
| Python 3.10 command unavailable through pyenv shim | quality commands | Full quality suite under required interpreter | Architecture ran under `python`; full quality failed before checks due interpreter shim. |

## Sector-by-sector unfinished inventory

| Sector | Verified unfinished work | Blocked/startable | Evidence | Confidence |
|---|---|---|---|---|
| S1 Bot product | Advanced Setup still has PR 3b: draft→Final Review editor rework and dead setup service cleanup. | Startable offline, heavier. | `setup_cog.py` still describes itself as advanced section-list + draft→Final Review; current-state names PR 3b as next. | High |
| S1 Bot product | Essential Setup extras badges need running-bot verification; source includes `setup_readiness.collect` based checks but live behavior is not proven here. | Needs live bot. | S1 says extras badges blocked on running-bot verification; setup readiness is a service-backed path. | Medium |
| S1 Bot product | Visual card engine adoption remains incremental; mining render rebase/owner visual decision not complete. | Partly startable, partly owner. | S1 names H2/H3 tails; tests still guard mining render with optional PIL skips. | Medium |
| S1 Bot product | Fishing gear acquisition depth remains a product tail. | Startable after owner balance constraints. | S1 points to craft/drop path for fishing charms and owner shore-cap call. | Medium |
| S1 Bot product | `EffectiveStats.light_radius` and `EffectiveStats.luck` are intentionally allowed as unwired. | Owner/design decision: wire behavior or remove. | Invariant test hardcodes `_UNWIRED_STATS = {"light_radius", "luck"}` and docs in the test call them latent. | High |
| S1 Bot product | Reaction roles appear mostly shipped; remaining significant tail is web builder Surface A. | Owner-paced. | Planning README and S1 both classify web builder as remaining gated surface. | High |
| S2 BTD6 | Decode-status item 3 buff/zone tail and item 4 live maintainer spot-check remain. | Owner/live spot-check. | S2 current-state marks both as next. | High |
| S2 BTD6 | P1-1 live `llm_judge` battery remains; offline grounding guard shipped but live model use unproven. | Needs live bot/creds. | S2 current-state explicitly separates offline shipped half from live battery. | High |
| S2 BTD6 | Absence-guard Layer B negative-existential gate remains design-for-review. | Startable design/review, not broad feature expansion. | S2 names Layer B; btd6 probe confirms current DDT answer relies on rules not auto-listed tower counters. | High |
| S2 BTD6 | Curated DDT counter lists or better derivation signals remain unresolved. | Startable only as curated data/design, broad AI gate applies. | `scripts/parse_gamedata.py` comments say DDT fields are not fabricated; probe says stats do not encode MOAB-class targeting so no auto-list. | High |
| S3 AI-Memory | procedures→skills Batch 2 remains. | Startable offline. | S3 current-state and planning README list Batch 2 after shipped Batch 1. | High |
| S3 AI-Memory | Bot self-test walker eval harness remains scaffolded/offline-buildable. | Startable offline; pairs with S1/S2 live eval later. | S3 current-state. | Medium |
| S3 AI-Memory | Hermes bug-triage write side remains gated on VPS write scope/Q-0121. | Hermes/owner only. | S3 current-state. | High |
| S4 Docs | Next reconciliation pass is not due until merged PRs cross #1530. | Blocked by cadence; do not manually run now. | S4 current-state and planning README. | High |
| S4 Docs | Plan-band depth has no `PLAN-BACKLOG-THIN`; no immediate docs backlog emergency. | Not blocked. | S4 current-state. | Medium |
| S5 Ops | Website two-site split v1 code is complete/reviewed; rollout remains owner-paced. | Owner/Hermes. | S5 current-state; `botsite/`, `dashboard/`, submissions DB files exist. | High |
| S5 Ops | Control-panel migration and live status aggregator are security-review gated. | Owner/Hermes/security review. | S5 current-state. | High |

## Critical blockers

### 1. BTD6 live answer correctness is not fully proven

- **Finding:** Offline grounding/eval guards have shipped, but the live `llm_judge` battery remains credentials/live-bot gated.
- **Evidence:** S2 explicitly marks P1-1 live `llm_judge` as next; `scripts/btd6_probe.py "what counters DDTs?"` returns grounded DDT facts but also states the bot does not auto-list specific counter towers because committed stats do not encode all required signals.
- **Why it matters:** BTD6 is a correctness-sensitive AI lane; offline facts do not prove that the production model uses them faithfully.
- **Suggested next step:** owner/maintainer live spot-check plus creds-backed eval battery; only then update current-state.
- **Suggested destination:** owner + Hermes/manual review for live run; Codex only for offline guard improvements.

### 2. Owner/Hermes-only operations must not be treated as normal repo work

- **Finding:** S5 rollout and control-plane tasks are real unfinished work, but they are intentionally owner/Hermes/security-gated.
- **Evidence:** S5 says most S5 work is Hermes-VPS/maintainer, and lists website rollout plus two security-review-gated slices.
- **Why it matters:** Implementing or deploying these from a normal repo session could bypass owner infrastructure, secrets, and security review.
- **Suggested next step:** preserve handoff status; ask owner/Hermes to execute rollout/security review steps.
- **Suggested destination:** Hermes / owner / manual review.

## Important improvements

### 1. Advanced Setup PR 3b remains a material UX/architecture tail

- **Finding:** The primary Essential Setup has shipped, but the Advanced draft→Final Review editor remains to be reworked and dead setup service code remains to be deleted.
- **Evidence:** S1 names PR 3b and quotes the owner concern that most of it does not do anything; `disbot/cogs/setup_cog.py` remains the advanced section-list + draft→Final Review launcher.
- **Why it matters:** Setup is a first-run product surface; stale/dead advanced flows can mislead server owners and preserve unnecessary service code.
- **Suggested next step:** one scoped Codex/Claude Sonnet cleanup session: verify actual remaining advanced sections, remove dead service paths, keep Essential Setup primary.
- **Suggested destination:** Codex or Claude Sonnet.

### 2. Unwired equipment stats are intentionally tracked but unresolved

- **Finding:** `EffectiveStats.light_radius` and `EffectiveStats.luck` are still allowlisted as unconsumed stats.
- **Evidence:** `tests/unit/invariants/test_effective_stats_consumed.py` documents that these fields currently do nothing and hardcodes them in `_UNWIRED_STATS`.
- **Why it matters:** Players can earn/equip items whose displayed stats may not affect behavior, which is a game/economy trust issue.
- **Suggested next step:** owner/product decision: wire effects into mining/fishing behavior or remove/rename the stats and item promises.
- **Suggested destination:** owner for decision, then Codex implementation.

### 3. DDT counter-list work needs curated data or stronger derivation signals

- **Finding:** The repo correctly avoids fabricating DDT-specific recommendations from incomplete signals, but that leaves the user-facing “what counters DDTs?” depth incomplete.
- **Evidence:** `scripts/parse_gamedata.py` comments avoid fabricating absent DDT fields; probe output recommends by rules rather than tower list.
- **Why it matters:** This is exactly the kind of high-confidence BTD6 answer users expect; wrong auto-derived lists are worse than no list.
- **Suggested next step:** design curated counter facts with provenance or extend data derivation to include MOAB-class targeting/camo/damage-type compatibility.
- **Suggested destination:** Claude Opus planning/revision, then Codex data/guard implementation.

### 4. Optional dependency/import-skip tests hide visual/web coverage

- **Finding:** Dashboard/botsite app tests and PIL-backed render tests use `importorskip`; DB integration tests skip without `DATABASE_URL`.
- **Evidence:** `rg` found `pytest.importorskip("fastapi")`, `pytest.importorskip("httpx")`, `pytest.importorskip("PIL")`, and DB skips across tests.
- **Why it matters:** These are sensible for CI portability, but they mean local green may not verify web and image-card behavior unless deps are installed.
- **Suggested next step:** document which matrix/dependency set is authoritative for web/card verification; add a small required smoke if practical.
- **Suggested destination:** Codex.

### 5. Architecture warning backlog remains non-zero

- **Finding:** Strict architecture check passes with 0 errors but 49 tracked warnings: BaseView inheritance, layer-boundary exceptions, and raw SQL exceptions.
- **Evidence:** `python scripts/check_architecture.py --mode strict` output.
- **Why it matters:** These are not blockers, but they represent remaining layered-architecture debt against `utils → core → services → governance → views → cogs`.
- **Suggested next step:** keep warnings as ratcheted cleanup packages, not feature blockers.
- **Suggested destination:** Codex cleanup sessions.

## Cleanup

- Setup command surface still exposes compatibility/legacy advanced names in generated dashboard data; safe if intentionally classified, but should be retired only after PR 3b and live compatibility checks.
- Dashboard/botsite generated data contains stale-looking issue/idea summaries by design; do not hand-edit generated files, but re-export when source docs change in implementation sessions.
- `python3.10` is not available through the current pyenv shim despite 3.10.20 being installed; local command recipes assume `python3.10` and failed here.
- Several direct `discord.ui.View` warnings are known and tracked; prioritize only those on actively touched surfaces.

## Future opportunities

- Project Moon `KnowledgeDomain` seam extraction after the live Q-0086 walk.
- Native giveaway PR 1 and botsite React migration, both already recorded in planning/current-state lanes.
- Fishing open-world/minigame expansion after acquisition/balance tails settle.
- Portable substrate kit external package extraction, currently owner-action rather than repo-local blocker.
- Voice/music architecture review remains a decision pack, not playback implementation.

## Docs/source mismatches

| Claim | Source doc | Source reality | Impact | Needed update |
|---|---|---|---|---|
| GitHub PR/open issue state should be verified live. | User task and owner workflow docs. | `gh` unavailable in container; web search did not provide private/live repo metadata. | Audit cannot prove no open PR already covers a finding. | Re-run GitHub metadata check in an environment with repo GitHub access. |
| Full quality command should be runnable as `python3.10 scripts/check_quality.py --full`. | Repo command recipes and context_map output. | `python3.10` shim failed; `python` is 3.13 and check_quality internally invokes `python3.10`, causing all subchecks to exit 127. | Verification gap, not source failure. | Fix pyenv/global shim in environment or invoke the configured 3.10.20 binary. |
| Broad S5 items may look like repo tasks. | Planning README/dashboard plans. | S5 current-state says rollout/security slices are owner/Hermes/security-review gated. | Prevents unsafe implementation. | Keep handoff labels prominent in next prompts. |
| BTD6 DDT counters could be auto-derived. | Historical PR lead. | Source/probe indicate required signals are incomplete; repo avoids fabricating tower lists. | Curated/provenance work remains. | Record as curated-data/design tail, not bug in current probe. |

## Test and verification gaps

- **Missing tests:** live BTD6 `llm_judge` provider battery; live Essential Setup extras badge walk; owner-paced website rollout tests in production-like infra.
- **Weak tests:** Advanced Setup PR 3b needs service-boundary tests around draft→Final Review after cleanup.
- **Skipped/xfailed tests:** dashboard/botsite FastAPI/httpx tests, PIL image tests, DB integration tests, and help actionability xfails for panels not yet actionable.
- **Live-bot-only gaps:** BTD6 model faithfulness, Essential Setup channel/opening behavior, Project Moon live Q-0086 runtime walk.
- **CI/quality/checker gaps:** full quality could not run here due `python3.10` shim; architecture check ran and reported warnings only.
- **Architecture-check gaps:** known warning backlog covers BaseView inheritance, layer boundaries, and raw SQL allowances.

## Suggested next work packages

1. **Advanced Setup PR 3b cleanup**
   - **Sector:** S1
   - **Goal:** Rework Advanced draft→Final Review editor and delete dead setup service code.
   - **Files/subsystems:** `disbot/cogs/setup_cog.py`, `disbot/views/setup/`, `disbot/services/setup_*`, setup tests.
   - **Why first:** Startable offline and directly addresses owner-flagged first-run UX debt.
   - **Blocked/startable status:** Startable.
   - **Suggested target agent:** Codex or Claude Sonnet.
   - **Verification required:** setup unit tests, architecture check, targeted context_map.

2. **Unwired stats decision + implementation**
   - **Sector:** S1
   - **Goal:** Decide whether `light_radius`/`luck` become real behavior or are removed from promises.
   - **Files/subsystems:** `disbot/utils/mining/equipment.py`, mining/fishing behavior, invariant test.
   - **Why first:** Avoids player-facing misleading stats.
   - **Blocked/startable status:** Owner decision first.
   - **Suggested target agent:** owner → Codex.
   - **Verification required:** invariant allowlist shrinks; gameplay tests cover behavior.

3. **BTD6 live P1-1 battery**
   - **Sector:** S2
   - **Goal:** Prove live model uses grounded facts and handles absence/counter facts honestly.
   - **Files/subsystems:** BTD6 eval harness, provider config, `scripts/btd6_probe.py`.
   - **Why first:** Highest correctness risk in AI lane.
   - **Blocked/startable status:** Needs live bot/creds.
   - **Suggested target agent:** Hermes/owner for live, Codex for offline harness fixes.
   - **Verification required:** live eval transcript and current-state update.

4. **procedures→skills Batch 2**
   - **Sector:** S3
   - **Goal:** Move more always-loaded agent procedures into on-demand skills.
   - **Files/subsystems:** `.claude/CLAUDE.md`, skills directories, procedures plan.
   - **Why first:** Offline and reduces context load.
   - **Blocked/startable status:** Startable.
   - **Suggested target agent:** Codex.
   - **Verification required:** docs/procedure checks and no workflow regressions.

5. **Website rollout handoff execution**
   - **Sector:** S5
   - **Goal:** Provision botsite/submissions DB/domain cutover from the reviewed handoff.
   - **Files/subsystems:** `botsite/`, `dashboard/`, `docs/operations/website-split-next-steps-2026-06-19.md`.
   - **Why first:** User-visible but not repo-local.
   - **Blocked/startable status:** Owner/Hermes only.
   - **Suggested target agent:** Hermes / owner.
   - **Verification required:** deployed site smoke, DB permission check, rollback plan.

## Open owner questions

- Should `EffectiveStats.light_radius` and generic `luck` become real gameplay stats, or should item/stat promises be removed? Route through the maintainer question router.
- Should fishing shore remain capped around rank 12, and should charm acquisition be crafting, fish-loot, or both? Route through the maintainer question router.
- What visual direction should mining/image-card rendering use before the remaining H2/H3 visual-card migrations? Route through the maintainer question router.
- When should the two-site website rollout and domain cutover occur? Owner/Hermes operational decision; route in ops handoff, not normal implementation.
- Should DDT counter recommendations be curated manually first, or should the data model be expanded before recommendations appear? Route through BTD6 decision/planning.

## Appendix: commands and searches used

- `pwd && find .. -name AGENTS.md -print && git status --short --branch`
- `git rev-parse --abbrev-ref HEAD && git rev-parse HEAD`
- `gh pr list --state open --limit 50 --json number,title,headRefName,updatedAt,url` *(failed: `gh` missing)*
- `gh issue list --state open --limit 50 --json number,title,updatedAt,url` *(failed: `gh` missing)*
- `gh pr list --state merged --limit 25 --json number,title,mergedAt,url` *(failed: `gh` missing)*
- Web search: `repo:menno420/superbot pull requests merged 1530`; `github menno420 superbot pulls`.
- `sed -n` reads of `docs/current-state.md`, `docs/current-state/S1-bot.md`, `S2-btd6.md`, `S3-ai-memory.md`, `S4-docs.md`, `S5-ops.md`, `docs/roadmap.md`, `docs/repo-sector-map.md`, `docs/health/bug-book.md`, `docs/architecture.md`, `docs/ownership.md`, `docs/runtime_contracts.md`, `.claude/CLAUDE.md`, `docs/AGENT_ORIENTATION.md`, `docs/collaboration-model.md`, `docs/owner/agent-workflow-spec.md`, and `docs/owner/ai-project-workflow.md`.
- `rg -n "TODO|FIXME|HACK|placeholder|not implemented|stub|temporary|follow-up|gated|owner|needs-live-bot|dead|unwired|allowlist|xfailed|skip|legacy|advanced|final-review|help_nav_card|EffectiveStats|light_radius|luck|llm_judge|absence|negative-existential|setup_readiness|btd6_probe|dashboard|botsite" --glob '!*.pyc' --glob '!node_modules/**' --glob '!*venv/**'`
- `rg -n "class EffectiveStats|light_radius|luck" disbot tests`
- `rg -n "setup_readiness|build_check_setup_embed|setupadvanced|Advanced|Final Review|FinalReview|draft" disbot tests`
- `rg -n "help_nav_card|image-card|ImageCard|mining_render" disbot tests`
- `rg -n "llm_judge|absence|negative|DDT|counter" disbot scripts tests docs/subsystems/btd6.md docs/planning/*btd6*`
- `rg -n "skip\(|xfail|importorskip" tests`
- `python scripts/check_architecture.py --mode strict` *(passed with warnings)*
- `python scripts/check_quality.py --full` *(failed because subcommands invoke unavailable `python3.10` shim)*
- `python scripts/btd6_probe.py "what counters DDTs?"`
- `python scripts/context_map.py disbot/cogs/setup_cog.py`

---

**Readiness verdict:** ready for narrow offline cleanup sessions and live owner/Hermes verification, not ready to declare BTD6 AI correctness or S5 rollout complete.

**Top 5 unfinished areas needing attention:** Advanced Setup PR 3b; BTD6 live `llm_judge`/absence gate; unwired `EffectiveStats.light_radius`/`luck`; fishing acquisition/balance tail; S3 procedures→skills Batch 2.

**Top 5 blocked/gated areas that should not be implemented yet:** website rollout/domain cutover; control-panel migration; live status aggregator; Project Moon live Q-0086 walk; reaction-role web builder Surface A.

**Safest next session/prompt type:** a single-scope Codex/Claude Sonnet execution prompt for Advanced Setup PR 3b, or an owner/Hermes live-verification prompt for BTD6 P1-1.

**Report path written:** `docs/analysis/unfinished-work-audit.md`.

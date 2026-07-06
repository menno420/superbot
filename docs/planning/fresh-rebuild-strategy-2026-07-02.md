# Fresh-rebuild strategy — verified baseline + plan-of-plans (2026-07-02)

> **⚠ SUPERSEDED-IN-PART (2026-07-06):** the §3 phase arc + §3.1 model table are superseded by
> [`rebuild-canonical-plan-2026-07-06.md`](rebuild-canonical-plan-2026-07-06.md) §3 (Phase 0
> ✅ #1649 · Phase 0.5 ✅ #1639 `parity/` · Phase 1 ✅ · Phase 2 spec ✅ — stamps this doc never
> received). §1 verified baseline, §4 design principles, §5 kit notes, §6 external findings stay
> reference.

> **Status:** `plan` — research-grounded strategy (analysis-grade), **not an approved execution plan.**
> Every quantitative claim below was verified against **live source / tooling on 2026-07-02** by a
> 7-agent verification fleet, not carried over from prior docs. Where an earlier figure drifted or was
> wrong, the correction is marked **⚠️**.
>
> **Extends** [`../ideas/superbot-fresh-rebuild-vision-2026-06-30.md`](../ideas/superbot-fresh-rebuild-vision-2026-06-30.md)
> (corrects several of its figures) and sits **above** the approved
> [`portable-substrate-kit-extraction-2026-06-13.md`](portable-substrate-kit-extraction-2026-06-13.md)
> + [`portable-agent-substrate-revision-2026-06-13.md`](portable-agent-substrate-revision-2026-06-13.md)
> plans. §6 **integrates** two external (GPT) research streams (UI/command grammar; GitHub/CI control
> plane), each verified against source per Q-0120 — corrections and owner-judgment items are marked **⚠️**.

## 0. Purpose

The maintainer's goal: use Fable 5 to produce an **extremely comprehensive plan to rebuild the bot
from scratch**, with the current repo as a *frozen reference*, designed as one finished picture rather
than stitched together — and to **finish + extract the portable AI-memory substrate-kit first** so the
new repo bootstraps a clean workflow from day one. This document is the *trustworthy foundation* for
that plan: the verified state of the world, the corrections the verification forced, the phased
approach, and the design principles + memory-package improvements that make "designed, not stitched"
mechanical rather than aspirational.

> **Fable 5 availability (verified live, 2026-07-02):** Fable 5 launched 2026-06-09, was **withdrawn
> 2026-06-12**, and was **redeployed 2026-07-01** (Anthropic, "Redeploying Fable 5"; global on the Claude
> Platform / Claude.ai / Claude Code / Cowork, cloud platforms phasing in). This **clears the "wait for
> Fable 5" gate** the fresh-rebuild vision doc recorded as open (that doc's "not reintroduced as of
> 2026-06-30" line is now stale — corrected there). Fable: $10/$50 per M tokens; 1M ctx / 128K out;
> always-on thinking (effort-controlled `low`→`max`); `refusal` stop-reason + model fallbacks; requires
> 30-day data retention. *(This session runs on `claude-opus-4-8`; the Fable-specific work is the Phase-2
> design ultracode, §3.1.)*

---

## 1. Verified baseline

### 1.1 Settings — the good pattern exists but is **not authoritative**
- **114 distinct setting keys** (17 `utils/settings_keys/` modules); **100 `SettingSpec` declarations**
  (15 cog `schemas.py`); **~14 keys have no spec at all** (governance, economy log channel, etc.).
- A genuinely good declarative pipeline exists: `SettingSpec` → `settings_registry` → `resolve_setting`
  / `SettingsMutationPipeline` (coerce → validate → capability → **DB write + audit in one transaction**).
  ~100 settings flow through it correctly.
- **⚠️ But it coexists with a legacy raw-KV path that bypasses all of it:** **40 direct callsites**
  (24 `get_setting` + 16 `set_setting`) with inline defaults, no validation, no audit — including a
  read *inside a view* (`disbot/views/setup/sections/moderation.py:408`), a layer violation.
- **Safe-default-OFF is confirmed real** (`server_logging_config.py:85` `DEFAULT_ENABLED = False`, every
  category off; AI off via env `AI_ENABLED` + spec `default=False`). The owner's instinct is correct.
- The clearest "outgrew itself" case: **AI forked its own pipeline** — the same on/off lives as an
  *env var + a KV scalar + a typed `ai_guild_policy` column*, kept in sync by a projection service,
  with two independent default declarations.
- **Implication:** the settings redesign is **"promote the existing registry to the *only* way to
  declare a setting, and delete every bypass"** — not a greenfield build. In place that means deleting
  40 callsites + unforking AI's typed store under live traffic (hard); in a rebuild the `SettingSpec`
  layer is authoritative from commit 1.

### 1.2 The AI-memory substrate-kit — real completion ~**45–55%**, not ~60%
- **32 files / ~4,024 lines**; **117 tests, all green**; build regenerates cleanly; `--simulate 1`
  smoke passes. Foundation is solid and **extraction-clean (zero `disbot` imports)**.
- **⚠️ The "60% built, just finish PR 2 remainder + PR 3" framing is generous.** The split:
  - **Done (declaration layer):** state backend, config, guardrail, interview + adaptive graduation,
    5 stances, 7 skills, 3 personas, 2 checkers, render, CLI, single-file bootstrap, stance-guard hook.
  - **Stubbed:** the three integration **modes** (`observe/guided/active`) — the field is set but its
    *only read is a status print*; zero behavioral branching. Review seam = a persona prompt that says
    "wire me up," unwired. Promotion-rights = field only.
  - **Absent:** drift/staleness/**trigger** detection; the self-maintenance loop; the reflection
    buffer; the full episodic index; `session_start`/`post_edit`/`stop_check` hooks +
    `settings.template.json`; mode/stance/skill simulation asserts.
  - **Templates: 6 of 13**, with **live dangling routes** — the question bank points Q-004/006/008/009/010
    at `architecture.md`/`ownership.md`/`runtime_contracts.md`/`owner-profile.md` that **do not exist**.
- **Everything shipped is declarative/static; the entire self-improving "nervous system" is unbuilt.**
  That is the highest-value half — and the part that most benefits from a proper design pass.
- Extraction blockers (all known Phase-2 productization): tests live outside the kit (`sys.path` shim),
  no packaging metadata, no dedicated CI.

### 1.3 Question router — ~**0 genuinely open**; the problem is format + stale decisions
- **7,874 lines / 67,401 words; 212 contiguous Q-blocks** (Q-0001→Q-0212, zero gaps).
- **⚠️ "60% unclassified / 11 open" is an artifact, not reality.** A semantic pass finds **~210 decided,
  ~0 genuinely open**. The impression comes from **four coexisting status formats** (`**Status:**` on only
  98 of 212; the rest use `**DECISION**`/`**DIRECTED**`/`**ANSWERED**` tokens, an `**Area:**` metadata
  line, or the abandoned split-header format used by Q-0001–0005).
- The real defects are exactly the owner's two: **stale decisions never stamped** (Q-0117 establishes the
  Hermes merge-gate → Q-0176 debates tuning it → Q-0197 kills it; all three still read as live, none
  cross-referenced) and **decided rules trapped as perpetual "questions"** (Q-0103/Q-0106 are quoted
  verbatim as binding in CLAUDE.md yet still sit in the router).
- **10,036 plain-text `Q-NNNN` citations** (212 unique) → in-place renumbering is unsafe. The archive
  mechanism exists but is a **literal empty placeholder (0 archived blocks)**.

### 1.4 Test suite as a rebuild oracle — **it cannot serve as one as-is** (load-bearing)
- **11,510 test functions / 1,102 files**, all under `tests/unit/`.
- **⚠️ The suite is aggressively white-box** and cannot be a frozen *behavioral* oracle for a rewrite:
  - ~55–60% structural/implementation-coupled (arch/checker/doc meta-tests ~12%; SQL-shape pins asserting
    literal query text; mock-choreography asserting internal call sequences).
  - ~20–25% pure-unit portable logic (`utils/`); ~15–20% behavioral (formatters, view renders, and the
    `evals/` grounding corpus — the one true black-box asset).
  - **True end-to-end ≈ 0 in CI:** zero tests build a real `asyncpg` pool; every DB test mocks; the 6
    `*_integration.py` skip whenever `DATABASE_URL` is unset (always). No Discord-gateway harness.
  - **Transferable to a restructured rebuild: ~20–30% of test *intent*, <10% of test *code*.**
- **The suite verifies *how SuperBot is built, not what it does.*** Pointed at a from-scratch
  reimplementation, almost none passes even if behavior is identical.
- **Consequence (see §3, Phase 0.5):** the correctness oracle must be **built**, not inherited — a
  black-box golden-output harness (command-in → embed/DB-out) captured against the **live** bot before
  any freeze. Reuse the `evals/` corpus; discard `invariants/`/`scripts/`/`docs/`/SQL-pins/mock-choreography.

### 1.5 Binding docs & orientation cost — outgrown, and narrating their own history
- Verified sizes (lines/words): CLAUDE.md 445/5,169 · collaboration-model 248/2,336 · current-state
  424/6,555 · **AGENT_ORIENTATION 484/3,292 (1.9× its own stated ~250-line cap)** · architecture
  474/2,637 · ownership 504/6,104 · runtime_contracts 473/2,616 · repo-nav 275/2,865.
- **Per-session boot read ≈ 25,300 words** (7-doc "any task" set); **~33,600 with the journal.**
- **≥5 rules that supersede themselves, tombstone retired mechanisms, or drift across docs**, e.g.
  CLAUDE.md `:173` says "open the PR ready" then `:226` reverses it to "born-red, flip ready last" — a
  reader obeys the dead instruction 53 lines before learning it's dead; the merge rule threads
  Q-0084→Q-0123 + five carve-outs; the reconciliation cadence still recites "10 → 20 → 30."
- **Pattern:** the binding docs **narrate their revision history inline** — "stitched, not designed"
  applied to the memory system itself. New repo: state each rule cleanly at its current value, keep
  Q-provenance in a *separate linked ledger*.

### 1.6 Architecture debt — the real debt is **late-binding collisions**, not the warnings
- **Verified: `0 errors, 49 warnings`** (13 baseview + 31 layer_boundary + 5 raw_sql — exact match).
  36 grandfathered in `architecture_rules/` YAML; 13 baseview are hard-coded warnings, several
  legitimate exemptions (game/paginator views). **⚠️ The "956 application files" denominator does not
  reconcile** (`find disbot -name '*.py'` = 879).
- **The 49 warnings are managed, contained, ~0-risk debt — not the story.** The real, incident-backed
  debt:
  1. **No central command/symbol namespace.** Q-0211 (`give` triple-collision) crash-looped production;
     **BUG-0030 (`dock`/`sail`) recurred the identical class 2 days later** because the first fix only
     de-duped cross-cog. Two boot crash-loops from one root cause in three days, both patched reactively.
     Also Q-0200 (`round_composition` silent name-shadow).
  2. **God-functions:** `AINaturalLanguageStage.process` cognitive **135 / 869 LOC / MI 11**;
     `validate_registry` 83 (ironically the boot-abort validator); **533 functions over the complexity
     threshold**; min MI 9.9.
  3. **⚠️ Coupling is runtime/lazy, invisible to static tools.** The "essential_setup fan-out ~210"
     figure **does not verify** (`impact_analysis` = 0 dependents; the subsystem imports lazily in
     function bodies). No `disbot` file shows large measured fan-out — the true coupling can't be seen
     by the import graph, which is itself a rebuild risk.
- **Do not conflate** late-binding registration collisions (the real debt) with layer-boundary warnings
  (managed debt). Honest nuance: prior consolidation passes (settings #625/#640, `edit_in_place`) found
  SuperBot *already had* a central spine — the work was "finish and clarify," i.e. drift-accretion, not
  absence.

---

## 2. What the research changed about the plan (five corrections)

1. **The oracle must be built, not inherited.** The existing 11,510 tests are a regression net for the
   *current* structure, not a behavioral spec for a rewrite. → new **Phase 0.5** (§3).
2. **Finishing the substrate-kit is the real work, not mop-up.** Its adaptive/self-improving half is
   unbuilt; "finish it first" is where the design method gets proven on a safe ~4k-line target.
3. **The router isn't an open-question backlog** (≈0 open) — it's format-chaos + unstamped stale
   decisions + decided-rules-trapped-as-questions. "Distill, don't migrate" becomes a concrete triage.
4. **The bot's real debt is a missing namespace + god-functions + hidden coupling**, not the 49 tracked
   warnings. The rebuild's structural wins should target *those*.
5. **The settings problem is enforcement/consolidation of an existing-good pattern**, reframing design
   move "declarative settings registry" from build → *make-authoritative + delete-bypasses*.

---

## 3. End-to-end execution order (from here to a production-ready rebuilt bot)

**Critical path:** `[Phase 0 · 0.5 · 1 in parallel]` → **Phase 2 design** → **🔒 owner approval** →
Phase 3 skeleton → Phase 4 port → Phase 5 cutover → **done.** Token limits are not the binding
constraint; wall-clock is (see §3.1). Everything up to the owner-approval gate is agent-buildable now.

**Phase 0 — Finish the substrate-kit's adaptive half** *(buildable now).* Build the unbuilt nervous
system: the three `mode` behaviors, drift/trigger detection, reflection buffer + meta-reflection miner,
the 7 missing contract templates (kills the dangling routes), the remaining hooks, memory-integrity/
quarantine + the context budget (§5.2). Ships the namespace-guard as a portable checker (§5.3). Also
the design-method dry-run + the clean-binding-doc generator. **Gate:** kit green + extractable.

**Phase 0.5 — Behavioral golden harness against the LIVE bot** *(parallel; must precede any freeze).*
Black-box goldens (command-in → embed/DB-out, testcontainers Postgres + a Discord driver), reuse the
`evals/` corpus. The only structure-agnostic rebuild oracle (§1.4), and a current-bot regression win.
**Can only be captured while the old bot is live.**
**✅ BUILT 2026-07-02 (#1639): [`parity/`](../../parity/README.md)** — replay-deterministic capture of
the real bot (fake HTTP over the real discord.py state machine — no dpytest/testcontainers needed),
coverage measured in [`parity/COVERAGE.md`](../../parity/COVERAGE.md); evidence + verdict in
[`rebuild-linchpin-validation-2026-07-02.md`](rebuild-linchpin-validation-2026-07-02.md). The
remaining Phase-0.5 sibling is the **telemetry sidecar capture** (sim objective data, spec §2.10.4).

**Phase 1 — Harvest what to keep** *(parallel; feeds the design).* Router distillation → clean decision
ledger; settings-authority audit → authoritative model; functionality inventory; hidden-dependency /
backward-compat map. Verified GPT-stream findings folded in (§6). *(Running now as the `rebuild-harvest`
ultracode → `docs/planning/rebuild-harvest/`.)*

**Phase 2 — The comprehensive design spec** *(the Fable job; the decision gate).*
**✅ Produced 2026-07-02: [`rebuild-design-spec-2026-07-02.md`](rebuild-design-spec-2026-07-02.md)
(judge-panel + Opus/GPT review) — ⏳ the owner gate below is now the live blocker.** One coherent picture:
redone architecture + contracts; the manifest grammar (§4/§6.1) designed **to be simulated over** (§4);
the central namespace; the authoritative settings model; the data model + backward-compat contract; the
control-plane (rulesets + OIDC); the regenerated binding docs. Independent-model review before freeze.
**🔒 OWNER GATE — the big one:** owner approves the design + the backward-compat contract + the rebuild
go/no-go. Nothing below starts until this.

**Phase 2.5 — Cold-start proof** *(parallel with Phase 2; gates Phase 3).* Point the finished kit at a
small throwaway repo; run the substrate-on vs -off A/B (§5.2). Proves the memory system works cold,
cheaply, before the ~100-PR commitment.

**Phase 3 — New-repo skeleton** *(owner-gated).* Create the repo; bootstrap the substrate-kit → clean
binding docs + ledger + workflow; build the two spines first — the manifest-grammar runtime engine + the
namespace registry; wire the control-plane (rulesets + OIDC); wire the golden harness as the acceptance
gate (red until parity); CI. The spines exist *before* any feature — that's what makes it designed, not stitched.

**Phase 4 — Port slice-by-slice, red-until-parity** *(the ~100-PR bulk).* Per subsystem: declare it in
the manifest grammar (sim-optimized per §4), implement the service behind the audited seam, green its
goldens. Order by dependency/risk — core platform + settings + governance first, then economy/moderation,
then games/AI/BTD6. Migrations honor the backward-compat contract. Old repo = frozen oracle, in production
throughout.

**Phase 5 — Cutover** *(owner-verified — the end).* Shadow-run until goldens + live checks green →
migrate data per the contract → flip production (Railway redeploy) → keep the old repo as frozen rollback
for a bounded window → decommission. **End state: the fully working, production-ready rebuilt bot.**

**Continuous side-track** *(low priority, parallel throughout):* keep the *old* bot healthy while it
serves production — apply §6.2's safe control-plane toggles + fix prod bugs. The *designed* control-plane
lands fresh in Phase 3.

**Buildable now vs gated:** Phases 0, 0.5, 1, 2.5 and *drafting* Phase 2 are agent-buildable with no owner
gate. The one hard gate is **owner approval of the design (Phase 2)** before any new-repo code. Cutover +
data migration (Phase 5) stay owner-verified. **The two sequencing rules that matter most:** capture the
goldens (0.5) before the old repo is ever frozen; approve the design (2) before Phase 3.

### 3.1 Model & ultracode allocation

Limits are not the binding constraint (Max ×20); **wall-clock is.** Principle: **spend Fable where
reasoning is the bottleneck; run the parallel bulk on faster models for throughput, not cost** —
unlimited *tokens* ≠ unlimited *time*, and a Fable fleet clears fewer items/hour than an Opus/Sonnet
fleet. Independent review always uses a *different* model than built it (the review-seam pattern; Codex/
GPT are the natural non-Claude reviewers).

| Phase | Model + effort | Ultracode |
|---|---|---|
| 0 — finish kit | Opus 4.8 `xhigh`; Fable for the hard design calls | Opus ultracode |
| 0.5 — golden harness | Opus/Sonnet fleet, Opus `max` core | Opus ultracode |
| 1 — harvest/map | Opus + Sonnet fan-out; Fable synthesis; **Codex** parallel cross-check | Opus ultracode *(running)* |
| 2 — design | **Fable judge-panel** (3 framings) + Opus `max` → synthesize → review by Opus + Codex/GPT | **the Fable ultracode** (clean usage-measurement run) |
| 2.5 — cold-start | Sonnet runs, Opus interprets | — |
| 3 — skeleton | Opus 4.8 `xhigh`/`max` on the spines; Sonnet on CI/control-plane | Opus ultracode |
| 4 — port (~100 PRs) | **Sonnet 5** workhorse; Opus 4.8 escalation for hard subsystems; Haiku for boilerplate | Opus-supervised Sonnet fleet |
| 5 — cutover | Opus 4.8 `high`; Sonnet for migration scripts | — |

The golden harness (0.5) is what **makes the cheap tiers safe** on the Phase-4 port: red-until-parity
catches any regression a Sonnet/Haiku agent introduces, so premium models are reserved for design
(Fable) and the structural spines (Opus).

---

## 4. Design principles for the new repo ("designed as one picture")

- **One authoritative settings registry.** `SettingSpec` is the *only* way to declare a setting —
  type/default/scope/validation/capability/UI/audit in one place; **safe-default policy as a field**
  (features safe-on by default); no raw-KV escape hatch; AI's typed policy folded into the same
  declaration. (§1.1)
- **One declarative manifest grammar for the whole UI/command surface** — generalizes the settings
  registry: panels, actions, settings, bindings, navigation and selectors declared once and *generated*
  by a runtime engine, not hand-coded per cog. Introduced *through* the central namespace so it can't
  recreate the `ActionSpec`-style collision. (§6.1)
- **Structure is discovered by simulation, not decided by hand.** Any grouping/ordering/layout decision
  with a measurable objective (commands, buttons/panels, settings, file ordering, AI-answer structure) is
  run through a simulator that searches for the most efficient arrangement — a standing, first-class step
  gated by a *sim-reviewed-or-exempt* check. The manifest grammar is what makes this cheap (the manifest
  *is* the search space), so it must be designed **to be simulated over**. Full rule + guardrails +
  per-domain mechanisms: [`simulation-driven-design-2026-07-02.md`](simulation-driven-design-2026-07-02.md).
- **A central command/symbol namespace that reserves names at declaration and fails *before* boot.**
  The single highest-value structural fix — it directly prevents the class that crash-looped production
  twice in three days. (§1.6)
- **A clean, self-classifying decision ledger** (the distilled router): one status format, machine-
  parseable, ordered; "promote decided→rule-in-doc" and "retire→stamp superseded" as first-class ops;
  starts at zero orphaned citations. (§1.3)
- **Lean, regenerated binding docs with provenance separated from the rule.** State the current rule
  cleanly; keep the Q-history in a linked ledger; enforce the orientation-cost cap with a checker so it
  can't silently regrow. (§1.5)
- **A complexity budget + visible coupling.** Cap god-functions (the AI NL stage is the worst offender);
  prefer explicit imports so the dependency graph is *real*, not hidden behind lazy function-body imports.
  (§1.6)
- **Seam authority as an invariant.** For every audited seam (settings, mutations, role/command
  changes), a check that the seam is the *only* path — the settings finding shows a good seam that isn't
  authoritative is the same failure mode as no seam.

---

## 5. Improve the next version — the AI-memory package/file

### 5.1 High-leverage items already captured (fold into Phase 0)
Reflection buffer + meta-reflection miner (forward-injected) — the persist→*improve* keystone;
graduate-or-drop the 4 unverified Q-0105 checkers (don't export shaky guards); the deprecation/unlearning
+ stale-answer hygiene pass; the router redesigned as ordered + self-classifying + machine-readable (KPIs);
wire the model-agnostic review seam to one real reviewer + loop stop-conditions.

### 5.2 The three under-committed gaps (in the revision doc, in **no** PR scope)
1. **Cold-start proof — substrate-on vs substrate-off A/B on a small fresh repo.** The *only* experiment
   that validates the thesis and closes the admitted "never tested from a true cold start" gap. Cheaper
   than a rebuild; it *is* the portability claim's test.
2. **The substrate's own context budget.** The anti-context-rot system injects orientation + ledger +
   reflections + user-style + stance every session, unbudgeted — so it becomes a rot source (the ~25k-word
   boot tax is this leaking). Load-by-reading-route + a footprint KPI + the orientation line-cap guard.
3. **Memory-integrity / quarantine (a red gap).** A system whose defining move is "inject grown and
   sometimes-external memory forward" is a standing prompt-injection target under autonomy — needs an
   "external text = data, not instructions" boundary + checkpoint/restore of state.

### 5.3 Additions synthesized from this verification pass
- **Ship the command/symbol namespace guard *as a portable kit checker.*** The single most-validated
  debt (two crash-loops) is "no name registry." The kit's whole purpose is preventing recurring errors —
  so a config-driven "reserve names at declaration, fail before boot" guard belongs in its generic
  checker set, not just SuperBot's.
- **Make the golden-behavioral-harness pattern a portable kit capability.** "Capture observable behavior
  as goldens so a refactor/rewrite is verifiable" generalizes far beyond this rebuild — the kit should
  help *any* project build its behavioral oracle, not treat it as a one-off.
- **Encode "provenance-separate-from-rule" as a template convention** (from §1.5) and **"is the good seam
  authoritative?" as a seam-authority check** (from §1.1) — both are portable lessons this repo learned
  the hard way.

---

## 6. Integrated external findings (two GPT streams, verified against source 2026-07-02)

Both reports were verified per Q-0120 (cross-agent output is input to *verify*, not adopt). Most claims
held; **⚠️** marks the ones that didn't, and *owner-judgment* marks recommendations not to auto-adopt.

### 6.1 UI / command / settings grammar (rebuild-discovery stream)
- **Verified:** `disbot/utils/subsystem_registry.py` (the manifest), `SettingSpec`/`BindingSpec`
  (`core/runtime/subsystem_schema.py`), `ResourceRequirement` (`core/runtime/resource_specs.py`), and
  `docs/building-roadmap/command-integration-standard.md` ("every command needs a panel + help entry")
  all exist. `PanelSpec` genuinely does **not** — so the thesis is grounded.
- **Thesis to adopt as a Phase-1 design pillar:** replace ad-hoc UI/command/settings code with **one
  declarative manifest grammar** — PanelSpec / ActionSpec / SettingSpec / BindingSpec / ResourceSpec /
  NavigationSpec / SelectorSpec / ConfirmationSpec / EmbedFrame — that a runtime engine interprets into
  consistent panels, navigation, help and service calls. This is the same move as §1.1's "make the
  declarative layer authoritative," generalized from settings to the whole UI/command surface.
- **⚠️ Verified collision:** the report proposes a *new* `ActionSpec`, but `ActionSpec` already exists
  (`services/automation_registry.py:35`). Introducing the grammar naively recreates the §1.6
  namespace-collision bug class — so the grammar must be introduced *through* the central symbol
  namespace, not alongside it.
- **Preserve (verified consistent with the repo's own contracts):** service-owned mutation + audit
  fan-out; the subsystem registry; help projection/overlay; BaseView/HubView auto-nav; paginated
  selects; the settings/binding/resource separation; the event-bus wiring map; the AI review/preset
  loop; the health-snapshot model.
- **Migration hazards to model as an explicit backward-compat contract (the "hidden dependencies" a
  naive rewrite breaks):** persistent `custom_id` strings; subsystem-registry keys (referenced in DB +
  migrations); event-bus names; DB schemas/enums; audit payload shapes; the `help_overlay`/visibility/
  cleanup governance tables. See the owner decision in §7.

### 6.2 Control-plane / CI / GitHub settings (platform-optimization stream)
- **Verified:** all 16 workflows exist as described; **`ROUTINE_PAT` is used by 7 workflows** (the
  single-point-of-failure the substrate plan already flagged as "PAT-expiry silent failure");
  `code-quality` is the sole required check; no `CODEOWNERS`.
- **⚠️ Corrections (caught per Q-0120):** the report claims "no PR/issue templates" — both **exist**
  (`.github/PULL_REQUEST_TEMPLATE.md` + `ISSUE_TEMPLATE/{bug_report,feature_request,config}`); and
  "hundreds of stale `claude/*` branches" **does not verify** (local remote shows 1) — needs a live
  GitHub check before acting.
- **Adopt-worthy (safe, current-repo wins, independent of the rebuild):** reduce the `ROUTINE_PAT`
  single-point-of-failure (GitHub App / OIDC); enable secret-scanning + push-protection; add a
  `CODEOWNERS`; Dependabot security updates; enable auto-delete-head-branches (after the live
  branch-count check).
- **Owner-judgment (do NOT auto-adopt — could destabilize the autonomous loop):** making the
  currently-UNVERIFIED subproject CI + tool-pins *required* checks; requiring branches-up-to-date
  (would throttle the high-velocity agent pipeline — `pr-auto-update.yml` exists precisely to manage
  this); requiring signed commits (agents/bots must sign); making Codex/Hermes reviews *required* gates
  (false positives would block merges). The report itself flags these as needs-review/do-not-do-yet —
  that judgment is correct.
- **For the rebuild:** keep the good parts (deterministic `git merge-tree` conflict checks, auto-merge-
  on-green, self-healing watchers, the routines) but design the new repo's control plane on
  GitHub-native **rulesets + OIDC from day one**, instead of accreting PAT-powered workarounds — the
  S5/ops analog of the "authoritative settings" and "declarative grammar" moves.

---

## 7. Open decisions & recommended next steps

**Owner decisions still needed:** published kit name (branding); rebuild go/no-go after the design spec;
whether cold-start proof needs the full rebuild or a small throwaway target (recommend the latter);
**backward-compat contract** — does the new bot preserve existing DB tables + persistent `custom_id`s +
subsystem keys via migrations, migrate only the important data, or start fresh? (the single biggest
rebuild decision, from §6.1's hidden-dependency list); **manifest format** — Python dataclasses vs
YAML/JSON vs hybrid; **control-plane hardening scope** — which of §6.2's safe GitHub toggles to enable
on the *current* repo now.

**Recommended immediate sequence (nothing here touches Phase-3 code or freezes the old repo — full order in §3):**
1. Finish the substrate-kit adaptive half (**Phase 0**) — first application of the design method.
2. In parallel, stand up the **Phase 0.5** golden harness against the live bot (also a current-bot win).
3. Run the **Phase 1 harvest** (router distillation + settings-authority + inventory + hidden-deps) —
   *running now as the `rebuild-harvest` ultracode*; raw material for the design.
4. Hand **Fable** the **Phase 2 design spec** (judge-panel + cross-model review) with verified material,
   not a blank page — then the owner-approval gate.

**Launch pad for the fresh ultracode sessions:**
[`rebuild-ultracode-handoff-2026-07-02.md`](rebuild-ultracode-handoff-2026-07-02.md) — paste-ready
session prompts (harvest / finish substrate-kit / golden harness / Fable design) plus the
verified-baseline TL;DR and the non-negotiable constraints, so a fresh high-core `/effort ultracode`
session starts without this session's in-memory context.

---

## Appendix — verification provenance (2026-07-02)

Seven independent agents verified this baseline against live source/tooling: settings system, substrate-kit
source state, question router, test-suite oracle viability, binding-doc/orientation cost, architecture debt,
and the memory-system improvement harvest. Corrections they forced over prior docs are marked **⚠️** inline
(notably: kit completion ~45–55% not ~60%; router ~0 open not 60% unclassified; the test suite cannot serve
as a rebuild oracle; the "essential_setup fan-out 210" and "956 files" figures do not verify; the real arch
debt is late-binding collisions + god-functions, not the 49 warnings).

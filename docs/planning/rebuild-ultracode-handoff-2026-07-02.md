# Rebuild — ultracode launch pad / handoff (2026-07-02)

> **Status:** `plan` — **START HERE to launch the first ultracode sessions** of the SuperBot rebuild.
> Written as a self-contained handoff (the planning session that produced it was nearing context
> compaction). A **fresh ultracode session** provisions a high-core container → the full 16-wide fan-out
> works (this doc's author ran in a 4-core container capped at 2, which is why the work was slow — start
> each session below as a *new* `/effort ultracode` session).

## 0. How to use this doc
Open a **new Claude Code session, set `/effort ultracode`**, and paste one of the prompts in §5. Each is
self-contained (points at the docs to read, the scope, model, output, constraints). Run the buildable-now
ones (A, B, C) in parallel as separate sessions; D (the Fable design) runs after the harvest (A) lands.

## 1. Read-first (durable, verified — do not re-derive)
- **[`fresh-rebuild-strategy-2026-07-02.md`](fresh-rebuild-strategy-2026-07-02.md)** — the verified baseline
  (§1), the five plan corrections (§2), the **end-to-end order Phase 0→5 + gates (§3)**, the **model &
  ultracode allocation (§3.1)**, design principles (§4), memory-package improvements (§5), the integrated
  GPT streams (§6), open owner decisions (§7).
- **[`simulation-driven-design-2026-07-02.md`](simulation-driven-design-2026-07-02.md)** — the standing rule:
  structure (grouping/ordering/layout) is discovered by simulation; the manifest is the search space.
- **[`../../.sessions/2026-07-02-rebuild-strategy-and-substrate-planning.md`](../../.sessions/2026-07-02-rebuild-strategy-and-substrate-planning.md)**
  — this planning session's decisions + context-delta.

## 2. Verified baseline TL;DR (from a 7-agent fleet, source-checked 2026-07-02)
- **Substrate-kit** is ~**45–55%** done (not ~60%): the declaration layer is built + 117 tests green, but the
  *self-improving nervous system* (mode behaviors, drift/triggers, reflection buffer, self-maintenance loop,
  review-seam wiring) is **absent/stubbed**, and **7 of 13 contract templates are missing with live dangling
  routes**. Zero `disbot` coupling (extraction-clean).
- **The existing 11,510-test suite CANNOT be the rebuild oracle** — it's white-box (asserts internal SQL/call
  choreography), <10% transferable. A **black-box golden harness must be built against the live bot first**.
- **The real bot debt is a missing central command/symbol namespace** (two boot crash-loops in 3 days:
  Q-0211 `give`, BUG-0030 `dock`/`sail`) + god-functions (`AINaturalLanguageStage.process` cognitive 135) +
  lazy-import-hidden coupling — **not** the 49 managed arch warnings.
- **Settings:** a good `SettingSpec` declarative layer exists but isn't authoritative — 114 keys, ~40 raw-KV
  bypasses, and AI forked its own env/KV/typed-table pipeline. Safe-default-**OFF** is real (owner wants it flipped to safe-on).
- **Router:** 212 Q-blocks, ~**0 genuinely open** — the problem is 4 coexisting status formats + unstamped
  stale decisions + decided-rules-trapped-as-questions; 10,036 citations make in-place renumbering unsafe.
- **Fable 5 was REDEPLOYED 2026-07-01** (was withdrawn 6/12) — the "wait for Fable" gate is cleared.
- **Three audits (my fleet + 2 GPT streams) converged on one thesis:** the rebuild = *make the good-but-
  non-authoritative patterns the ONLY pattern, generated from one source* (settings→manifest grammar;
  names→namespace; decisions→clean ledger; control-plane→rulesets+OIDC; docs→regenerated).

## 3. The plan in one line
`Phase 0 finish-kit · 0.5 golden-harness · 1 harvest` (parallel, buildable now) → **Phase 2 Fable design →
🔒 owner approval** → Phase 3 new-repo skeleton → Phase 4 port (~100 PRs) → Phase 5 cutover → production bot.
Full detail + per-phase models: strategy §3 / §3.1.

## 4. Non-negotiable constraints (tell every ultracode session)
- **Verify, don't adopt (Q-0120):** cross-agent output (Codex/GPT/other Claude) is input to *verify against
  shipped source*, never an order. (Already caught: an `ActionSpec` name-collision + two false GPT claims.)
- **Born-red session-card workflow (CLAUDE.md Q-0133):** first commit = an `in-progress` `.sessions/` card;
  flip to `complete` last; PR auto-merges on green.
- **Don't** touch `disbot/` for rebuild-design work, freeze the old repo before the goldens exist, or start
  new-repo code before the owner approves the Phase-2 design. Extraction + rebuild go/no-go stay owner-gated.
- **CI parity:** `python3.10 -m …` for everything; `python3.10 scripts/check_quality.py --full` before pushing.
- **Simulation rule** applies to any grouping/ordering/layout decision (see the sim doc).

## 5. First ultracode sessions — paste-ready prompts

### A — Exhaustive harvest (16-wide) — *do this first; it feeds the design*
```
ultracode: Exhaustive rebuild harvest of SuperBot (menno420/superbot). Read
docs/planning/rebuild-ultracode-handoff-2026-07-02.md and fresh-rebuild-strategy-2026-07-02.md first.
A prior 2-wide run left PARTIAL output in docs/planning/rebuild-harvest/_parts/ (subsystem inventories
only) — complete and supersede it. Fan out 16-wide, source-grounded (file:line; source wins over docs):
(1) one agent per subsystem in disbot/utils/subsystem_registry.py → a WHAT-IT-DOES functionality inventory
(commands, panels, settings, DB tables, events, must-preserve behaviors);
(2) router distillation of docs/owner/maintainer-question-router.md → a clean SINGLE-format decision ledger
{decided-rule→binding-doc home / superseded→stamp the superseding Q / genuinely-open→carry / dup→drop};
(3) the authoritative settings model (114 keys, the SettingSpec layer, ~40 raw db.get/set_setting bypasses,
the AI env/KV/typed-ai_guild_policy fork → ONE declarative model + a safe-default-ON policy);
(4) the hidden-dependency / backward-compat map (persistent custom_ids, subsystem_registry keys used in
migrations, event-bus names with subscribers, DB schemas/enums, audit payload shapes, help_overlay/
visibility/cleanup tables — what BREAKS if each changes).
Adversarially verify before writing. Synthesize → docs/planning/rebuild-harvest/{functionality-inventory,
decision-ledger,settings-model,migration-contract}.md. Opus xhigh. Born-red session card.
```

### B — Finish the substrate-kit adaptive half (Phase 0)
```
ultracode: Finish the AI-memory substrate-kit's adaptive half (Phase 0). Read
docs/planning/rebuild-ultracode-handoff-2026-07-02.md, fresh-rebuild-strategy-2026-07-02.md (§1.2/§3/§5),
and portable-substrate-kit-extraction-2026-06-13.md (approved plan + "RESUME HERE"). Source of truth:
substrate-kit/src/**, tests/unit/substrate_kit/**. Build the UNBUILT nervous system (verified
absent/stubbed): the three mode behaviors observe/guided/active (the field is set but nothing reads it);
drift/staleness/trigger detection; the reflection buffer + meta-reflection miner (forward-injected into
orientation); the 7 MISSING contract templates (architecture, ownership, runtime_contracts,
repo-navigation-map, helper-policy, ai-project-workflow, owner-profile — this kills the dangling
question_bank routes); the remaining hooks (session_start orientation injection, post_edit, stop_check) +
settings.template.json; memory-integrity/quarantine + a context budget; ship the namespace-guard as a
portable checker. Regenerate dist/bootstrap.py after ANY src/engine edit; keep zero disbot imports;
bootstrap stays stdlib-only. Verify: python3.10 -m pytest tests/unit/substrate_kit/ -q; build_bootstrap +
dist/bootstrap.py --simulate 1; python3.10 scripts/check_quality.py --full. Opus xhigh. Born-red card.
```

### C — Behavioral golden harness (Phase 0.5) — *capture while the bot is live, before any freeze*
```
ultracode: Build the black-box behavioral golden harness against the LIVE SuperBot (Phase 0.5 — the
rebuild's ONLY viable correctness oracle; the existing 11,510-test suite is white-box, <10% transferable).
Read docs/planning/rebuild-ultracode-handoff-2026-07-02.md + fresh-rebuild-strategy-2026-07-02.md §1.4/§3.
Stand up a command-in → embed/DB-out golden-capture harness: ephemeral Postgres (testcontainers) + a
Discord driver (dpytest or equivalent), reusing tests/evals/ (the one existing black-box asset). Fan out
16-wide, one agent per subsystem command-surface (use the harvest's functionality-inventory once it lands,
else disbot/cogs/), snapshotting observable outputs + DB deltas as golden fixtures a rebuilt bot can be
replayed against (red-until-parity). Deliver a runnable harness + the golden corpus; it doubles as a
current-bot regression net. Opus xhigh/max on the harness core, Sonnet for per-subsystem capture. Born-red card.
```

### D — The Fable design spec (Phase 2) — *✅ RAN 2026-07-02; do NOT re-run. Deliverable: [`rebuild-design-spec-2026-07-02.md`](rebuild-design-spec-2026-07-02.md), ⏳ awaiting owner approval*
```
ultracode (start the session on Claude Fable 5, effort max): Produce the comprehensive from-scratch rebuild
DESIGN SPEC for SuperBot — the "one picture." DESIGN, NOT CODE. Read (all) fresh-rebuild-strategy-2026-07-02.md,
simulation-driven-design-2026-07-02.md, and — your primary evidence — the VERIFIED Codex preserve map
docs/analysis/rebuild-discovery/codex-preserve-map-synthesis-2026-07-02.md (its §1 corrections are BINDING;
drill into the 4 raw domain maps in that folder as needed). Run it as a JUDGE-PANEL: 3 independent designs
from different framings (clean-slate-ideal / minimal-migration-risk / manifest-grammar-maximal) + 1 Opus,
synthesize best-of, then independent review by Opus + a non-Claude model. Produce: redone architecture +
layer/ownership/runtime contracts; the declarative MANIFEST GRAMMAR (Subsystem/Panel/Action/Setting/Binding/
Resource/Nav/Selector) designed TO BE SIMULATED OVER; the central command/symbol namespace; the authoritative
settings model + safe-default-ON policy; the data model + backward-compat contract (the map's §5 hazard set);
the control-plane (GitHub rulesets + OIDC); the regenerated binding docs.
VERIFIED CONSTRAINTS FROM THE MAP (do not re-derive, do not violate):
 (1) RENAME the proposed `ActionSpec` — it HARD-COLLIDES with the shipped services/automation_registry.py:35
     class ActionSpec; resolve repo-wide (PanelActionSpec/UIActionSpec) before any domain adopts it.
 (2) EXTEND, never recreate, the already-shipped types: SettingSpec/BindingSpec (subsystem_schema.py),
     CapabilityDecision (governance/capability.py), LifecycleResult/StepResult (lifecycle/contracts.py),
     ResourceRequirement (resource_specs.py), AIGateway (core/runtime/ai/gateway.py, re-exported via
     services/ai_gateway.py — preserve that seam split). The manifest grammar CONSOLIDATES the mature-but-
     fragmented subsystem_schema.py + subsystem_registry.SUBSYSTEMS + hub_registry.HUBS — it is not greenfield.
 (3) Honor the §5 backward-compat contract: persisted subsystem_registry keys, persistent custom_id strings,
     catalogued event names/payloads, DB migrations/tables, settings keys, audit payload shapes.
Do NOT re-open the 10 settled substrate-kit review rounds — verify against source, don't re-litigate.
Output → docs/planning/rebuild-design-spec-2026-07-xx.md. Owner approves before Phase 3.
```

> **The Codex preserve map is DONE (2026-07-02).** The owner's 4 Codex mapping sessions (platform/UI ·
> admin/safety/server · economy/games · AI/knowledge) landed as PRs #1630–#1633; a verify-and-fold workflow
> checked their load-bearing claims against source (Q-0120 — **48/59 confirmed, 2 false, 9 partial**) and
> folded them into **[`codex-preserve-map-synthesis-2026-07-02.md`](../analysis/rebuild-discovery/codex-preserve-map-synthesis-2026-07-02.md)**.
> This is D's primary input — the separate 16-wide harvest (A) is now **optional**, not a blocker for D.

## 6. Current in-flight state (as of this handoff)
- **The Codex preserve map is folded and verified** → `docs/analysis/rebuild-discovery/` (synthesis +
  4 raw domain maps). D can run now; A (the 16-wide harvest) is optional additional depth, not a gate.
- **My 2-wide harvest** (`rebuild-harvest` workflow) was partial (gitignored `_parts/` scratch) and is
  **superseded** — the Codex maps cover the same functionality-inventory ground. Don't wait on it.
- **Committed + pushed** on branch `claude/substrate-kit-planning-review-3a1jkf`: the strategy doc, the
  simulation-driven-design doc, this handoff, the session log, the Fable-status fixes in the vision doc,
  and the verified Codex synthesis + 4 preserved maps.

## 7. Model & ultracode allocation (quick ref — full table in strategy §3.1)
Fable where reasoning is the bottleneck (the Phase-2 design, session D); Opus `xhigh` for the builds
(A/B/C); Sonnet for wide fan-out / the Phase-4 port; independent review always a *different* model than
built it. The golden harness (C) is what makes cheap-tier porting safe later (red-until-parity).

### E — External full-tier review of the design spec (owner: paste into Codex / ChatGPT) — *✅ RAN 2026-07-02: the owner ran two external GPT sessions; findings verified + folded into the spec (see its header "Revision" note). A further pass is optional.*

D's in-session non-Claude review ran on `gpt-5.4-mini` (the strongest OpenAI model available to the
deployment's key). A full-tier external pass is the one review seam still open. Paste-ready prompt:

```
You are the independent non-Claude reviewer of a Discord-bot rebuild design spec authored by Claude
models (a judge panel + adversarial review already ran; your value is out-of-family judgment).
Review docs/planning/rebuild-design-spec-2026-07-02.md against the verified evidence in
docs/analysis/rebuild-discovery/codex-preserve-map-synthesis-2026-07-02.md (its §1 corrections and
§5 backward-compat contract are binding; verify claims against shipped source, not prior docs).
Find REAL defects only: internal contradictions, backward-compat holes, a namespace/settings design
that won't deliver its stated guarantee, mechanisms an implementer could not build from the text,
and blind spots a same-family model panel would share. For each finding: severity
(blocker/major/minor), the spec section, the issue, evidence (file:line where factual), suggested
fix. No style notes. End with a verdict: approve / approve-with-fixes / needs-rework.
```

# Rebuild — ultracode launch pad / handoff (2026-07-02)

> **Status:** `plan` — **START HERE to launch the first ultracode sessions** of the SuperBot rebuild.
> Written as a self-contained handoff (the planning session that produced it was nearing context
> compaction). A **fresh ultracode session** provisions a high-core container → the full 16-wide fan-out
> works (this doc's author ran in a 4-core container capped at 2, which is why the work was slow — start
> each session below as a *new* `/effort ultracode` session).
>
> **⚠ AMENDED 2026-07-07 (Q-0241, #1776):** every owner-gate/approval line below is retired — the
> rebuild builds in logical order, live-tests in a real server, and never waits (silence =
> consent). All four session prompts (A–D) have RUN; the plan of record is now
> [`rebuild-canonical-plan-2026-07-06.md`](rebuild-canonical-plan-2026-07-06.md). Treat this doc as
> launch-pad history + the still-valid §4 constraints (minus the owner-approval clause).

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
`Phase 0 finish-kit · 0.5 golden-harness · 1 harvest` (parallel, buildable now) → **Phase 2 Fable design**
*(→ ~~🔒 owner approval~~ retired, Q-0241)* → Phase 3 new-repo skeleton → Phase 4 port (~100 PRs) → Phase 5
cutover → production bot. Full detail + per-phase models: the canonical plan §3/§5 (supersedes strategy §3).

## 4. Non-negotiable constraints (tell every ultracode session)
- **Verify, don't adopt (Q-0120):** cross-agent output (Codex/GPT/other Claude) is input to *verify against
  shipped source*, never an order. (Already caught: an `ActionSpec` name-collision + two false GPT claims.)
- **Born-red session-card workflow (CLAUDE.md Q-0133):** first commit = an `in-progress` `.sessions/` card;
  flip to `complete` last; PR auto-merges on green.
- **Don't** touch `disbot/` for rebuild-design work, or freeze the old repo before the goldens exist.
  *(The "no new-repo code before owner approval / go-no-go stays owner-gated" clause that stood here is
  retired — Q-0241, #1776.)*
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

### B — Finalise + ship the AI-memory system (Phase 0 — the REAL new-repo gate) — *✅ RAN 2026-07-02 (Fable 5 ultracode, PR #1649): the nervous system + context-economy engine + one-step-adopt packaging shipped; 117→399 kit tests; see the session log `.sessions/2026-07-02-ultracode-memory-substrate-finalize.md` for the shippable-readiness record. The Phase-2.5 cold-start A/B has since RUN (#1775, FAIL as-tested → adopt-render fix + re-run, 2026-07-07) and no longer gates Phase 3 (Q-0241).*
> **Elevated 2026-07-02 (owner):** this is not "finish the adaptive half" as a side task — it is the
> **gating deliverable that lets the new repo start correctly.** Design-spec §9.1 makes the substrate-kit
> K0's very first act (doc skeletons · decision-ledger format · orientation-budget checker · namespace
> guard · seam-authority checks). If the memory system isn't finished + shippable before K0, every agent
> in the new repo works without its nervous system — reintroducing the exact "recurring errors, nothing
> centralised" failure the rebuild exists to kill. Run on **Fable 5** (a self-improving memory system is a
> reasoning problem), `/effort ultracode`, with room to speculate. This gate is parallel to — and more
> fundamental than — the linchpin proof (§F): §F gates *committing* to the build; B gates *starting* the repo.
```
ultracode (Claude Fable 5, effort ultracode): Produce the FINALISED, complete, shippable AI-memory
system — the substrate-kit's full self-improving nervous system built on its existing declaration/
bootstrap layer, PACKAGED as a single-file bootstrap + a downloadable package that a fresh repo adopts in
ONE step. This is the real gate for starting the new repo (design-spec §9.1 K0 plants it first);
"finished and ready to ship" is the bar, not "further along."

READ (verify against source — Q-0120, don't adopt): portable-substrate-kit-extraction-2026-06-13.md (v9
approved plan — the ▶ RESUME HERE recipe, §6 self-review/maintenance loop, the modes/stances/skills/
personas design, the bootstrap distribution form); the CURRENT source substrate-kit/src/**,
substrate-kit/dist/bootstrap.py, tests/unit/substrate_kit/** (the built declaration/bootstrap/interview/
skills/stances layer + 117 tests); rebuild-design-spec-2026-07-02.md §7 (the kit IS K0's bootstrap:
templates · ledger format · orientation-budget checker · namespace guard · seam-authority checks), §2.10
(AgentContextPack fed by the manifest snapshot), §3.5 (namespace guard evolved from the kit's portable
guard); rebuild-parallel-execution-plan-2026-07-02.md (why this gates K0).

BUILD the unbuilt nervous system (establish the exact current gap yourself against source first): the
three integration-mode BEHAVIORS observe/guided/active (the field is set but nothing reads it to change
agent behavior); drift/staleness/trigger detection (mandatory-question sessions that fire "whenever the
current state requires it"); the reflection buffer + meta-reflection miner (forward-injected into
orientation); the §6 self-review & maintenance loop (model-agnostic — compaction triggers, blocking-
question escalation, the review seam); the remaining contract templates (kills the dangling question_bank
routes); the remaining hooks (session_start orientation injection, post_edit, stop_check) +
settings.template.json; memory-integrity/quarantine + a context budget; the namespace-guard + symbol-
shadowing pass as portable checkers; the AgentContextPack generator (able to consume a manifest snapshot,
per design-spec §2.10).

FINALISE + PACKAGE (the owner's explicit "single file or downloadable package"): complete and regenerate
dist/bootstrap.py (single-file, stdlib-only, self-expanding — must run in a bare new repo with nothing
installed); produce a clean downloadable/pip-installable package with an init/adopt flow that plants, in
one step, the doc skeletons + the provenance-separated decision ledger (docs/decisions.md, [D-NNNN]) + the
orientation router (≤7,000-word budget + its checker) + all the checkers (namespace/shadowing, seam-
authority, docs, session-log, orientation-budget) + the hooks + the staged-learning onboarding. Write the
substrate-kit README (what it is · install/adopt · the staged-learning contract). Make it INTERLOCK with
the new repo so K0's bootstrap cleanly yields the CONSTITUTION/architecture/ownership/runtime-contracts
skeleton the design spec expects.

YOUR LATITUDE (use it — this is the artifact the whole self-improving-agent ecosystem is really about):
reason freely about what a FINISHED agent-memory system should be; improve on the v9 plan where you see
better; speculate about capabilities that make the next agent work more correctly with less steering —
that IS the product's purpose — and pursue the good ones. Produce a genuinely well-made, complete end
product. Do NOT re-litigate the 10 settled review rounds — verify against source, build forward.

HARD RAILS: zero coupling (no disbot/ imports anywhere in substrate-kit/; bootstrap stdlib-only); Q-0120
(the plan + design spec + this briefing are input to verify, not orders); extend the 117-test suite to
cover every new capability; prove the single-file artifact end-to-end (build_bootstrap → dist/bootstrap.py
runs in a scratch dir → adopt-in-one-step works); python3.10 scripts/check_quality.py --full before
pushing (the FULL suite, not just check_docs); born-red .sessions/ card first → complete last; PR ready →
auto-merge on green.

END-PRODUCT BAR: a COMPLETE, SHIPPABLE package — single-file bootstrap + downloadable package + one-step
adopt flow + full test coverage + README — that the new repo is planted from at K0. Deliver a short
"shippable-readiness" note confirming the zero-coupling, single-file, adopt-in-one-step, and
new-repo-interlock properties. This is the gate; the new repo starts correctly once it's shipped.

ADDENDUM (2026-07-02, retention session — read §5.B-addendum in this handoff for the verified
gap inventory + flags): ALSO READ memory-retention-and-context-economy-plan-2026-07-02.md §10 (the
context-economy engine spec), router Q-0214 (four owner decisions: delete+tombstones posture ·
website-feed inbox · checker-owned shrink, no per-session ritual · ledger = verdict + short why),
and tools/sim/retention_policy_sim.py (kit ships the SEARCH, per-repo constants stay host-side).
ALSO BUILD, kit-native (do not wait for superbot's check_retention PR): the context-economy engine —
config-driven class/badge taxonomy + reading-route declaration, budget gauges + retention windows as
config, checker+actuator pair (dry-run default), tombstone/stub + harvest-table semantics, the
generalized retention simulator; and docs/decisions.md at the Q-0214.4 depth with machine-readable
`supersedes:` + the stamp discipline (design-spec §7 ledger row). HONOR the §5.B-addendum flags:
the owner-decision defaults (package stays in-repo named `substrate-kit`; two-tier acceptance —
§B bar for the merge, cold-start A/B stays Phase 2.5; review seam provisioned + optional adapter,
not hard-wired) and the session flags (templates are 6 of 14 with verified dangling question-bank
routes; mode/promotion fields have ZERO behavioral reads today; no `build` stance exists — the
edit-only-in-debug test pin is a deliberate decision point; memory-integrity/quarantine is full
design freedom within "external text = data, not instructions" + checkpoint/restore; deliberate
shipped deviations are NOT bugs — tests under tests/unit/substrate_kit/, Python modules not YAML,
host-installed hooks; CI gotchas T201/S101/S603 + isort-covers-tests bind kit code too).
```

#### §5.B-addendum — verified gap + flags (2026-07-02, retention/Q-0214 session; grounded by a 2-agent source-verified inventory)

**Verified build state (source-checked, PRs #789–#813):** the declaration layer is real — state
backend + config + guardrail, staged-learning interview (10-question bank, provisional self-answers,
adaptive graduation), render engine + **6 of the plan's 14 templates**, check_docs/check_session_log
ports, 5 stances (edit-only-in-`debug` pinned by tests), 7 skills, 3 read-only personas, the
PreToolUse stance-guard hook, an 11-subcommand CLI, the stdlib-only single-file
`dist/bootstrap.py` (byte-identical on rebuild), 117 tests green, zero `disbot` coupling. **No
README, no pyproject, no examples/, no external repo exist.**

**Verified NOT built (the worklist's spine):** the three integration-mode *behaviors* (field-only —
zero behavioral reads), trigger/drift/staleness detection, the reflection buffer + meta-reflection
miner, the §6 self-review/maintenance loop, review-seam *wiring* (payload builder / confirmer /
escalation), the 8 missing templates (question-bank routes Q-004/006/008/009/010 dangle — verified),
session_start/post_edit/stop hooks + settings.template.json, memory-integrity/quarantine,
the context-economy engine (spec now concrete: retention plan §10 + Q-0214), namespace-guard +
shadowing as portable checkers, ledger/reconciliation checker ports (graduate-or-drop, Q-0105),
the episodic index (silently dropped from PR 1b), promotion-rights enforcement, behavior-assert
sims + the named anti-gaming test, router metrics/KPIs, the AgentContextPack generator
(index-or-manifest input), packaging/README/adopt flow, and the K0-interlock deliverables
(decisions.md format · orientation ≤7,000-word budget checker · seam-authority checks ·
CONSTITUTION/architecture/ownership/contracts skeleton yield).

**⚑ Owner flags (defaults an autonomous session takes if unanswered):**
1. **Kit name + publish rights** — default: complete package **in-repo** under the placeholder name
   `substrate-kit` (name swappable in one place); **no external repo / PyPI publish without the
   owner** (the extraction step stays owner-driven).
2. **Acceptance bar** — default two-tier: the finalization PR merges on §B's shippable bar (117+
   tests green, `--simulate` smoke, no `$PLACEHOLDER` residue, one-step adopt proven in a scratch
   dir); the **Phase-2.5 cold-start substrate-on/off A/B stays a separate session** and still gates
   Phase 3.
3. **Review-seam wiring** — default: seam + anti-anchor payload + stop-conditions + an *optional*
   config-driven non-Claude reviewer adapter (graceful no-key fallback); hard-wiring a live
   reviewer (whose key?) is the owner's call.
4. **Retention PR 2's 7-file substep** — the 2026-06-30 audit's confirmed-delete list **was never
   committed** (chat-only); re-derive or skip (default: skip — the reference gate protects
   regardless).
5. **Journal deeper-cut** (8,349 → ~4,000 words/boot) — default: stop-growth cap only.
6. **The rebuild design-spec approval** remains the standing 🔒 gate — §B is ungated and builds the
   interlock against the spec as written, flagging anything approval-sensitive.

**Session flags (resolve in-session, guidance included):** re-establish the exact gap against
source first (§B already instructs this; treat 6-of-14 as the template truth and "zero dangling
routes" as the bar) · the no-`build`-stance / edit-only-in-debug pin is a deliberate design
decision — change it with rationale + test update, or route build-mode through skill precedence ·
build the context-economy engine kit-native; superbot's own `check_retention.py` (retention plan
PR 1) can then consume the kit version · hooks follow the shipped #813 precedent (stage into
`<state_dir>`, host installs; never write a live `.claude/`) · don't duplicate PR #1639's golden
harness — the kit ships the *pattern/scaffold*, not superbot's goldens · check
`docs/owner/claims/` + open PRs at start (lane was uncontended at 2026-07-02 12:40 UTC).

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

### D — The Fable design spec (Phase 2) — *✅ RAN 2026-07-02; do NOT re-run. Deliverable: [`rebuild-design-spec-2026-07-02.md`](rebuild-design-spec-2026-07-02.md), the owner-approval wait was retired by Q-0241 (#1776); its §10.2 list is now the canonical plan's §1 veto payload*
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

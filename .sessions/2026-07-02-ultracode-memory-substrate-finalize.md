# 2026-07-02 — Finalize the AI-memory substrate (handoff §5.B, ultracode)

> **Status:** `complete`
> **Branch:** `claude/ultracode-memory-substrate-2utgvc` · **PR:** #1649
> **Session type:** ultracode (Fable 5) — owner-queued via rebuild handoff §5.B + 2026-07-02 addendum

## What happened

Executed rebuild handoff §5.B end-to-end: the substrate-kit's **full self-improving nervous
system** is built on the existing declaration layer, the **context-economy engine** (retention
plan §10 + Q-0214) is kit-native, and the kit is **packaged as a shippable one-step-adopt
artifact** — the K0 gate deliverable. 117 → **399 kit tests**; full CI mirror
(`check_quality.py --full`) green.

### Built (the previously-verified-absent list, now shipped)

1. **Mode behaviors** (`lib/modes.py`) — the `mode` field's first behavioral reads: question
   quota (observe 2 / guided 3 / active ∞), orientation depth, trigger mandates, actuator
   gating (the promotion-rights enforcement point), guided practice rollout
   (session_logs → idea_lifecycle → question_router → session_enders → gates), observe-mode
   propose-only graduation + workflow-proposal emission. Proven per-mode via
   `--simulate N --mode m` from the dist.
2. **Triggers** (`loop/triggers.py`) — the five kinds (critical_unfilled grace / blocking_open /
   drift / staleness / new_area) → mandatory-question sessions; `loop/kpis.py` router metrics +
   workflow KPIs + the 📊 footer.
3. **Reflection buffer + miner** (`loop/reflections.py`) — R-NNNN rolling buffer (cap 5),
   forward-injected "Learned lessons" (provisional flagged), deterministic miner over session
   logs; **episodic index** (`loop/episodes.py`) — tags + slug per session, searchable.
4. **Maintenance loop** (`loop/maintenance.py`) — compaction cadence + pre-compaction **State
   Delta**, blocking-question escalation onto `open_questions` (holds graduation), promotion
   downgrade; **review seam** (`loop/review_seam.py`) — anti-anchor payload (proposition +
   evidence, NO confidence), `review build/confirm` verdict flow (confirmed / recorded /
   escalated), provisioned-not-wired per owner flag 3.
5. **Context-economy engine** (`economy/engine.py` + `harvest.py`) — config-driven class/badge
   taxonomy, budget gauges incl. the ≤7,000-word orientation route budget, inbound-reference
   pass, **triple-filter deletion** (harvested AND past window AND zero refs), dry-run-default
   actuator with shadow→gated→normal maturity + lock + tombstone shards, harvest-table
   parse/stub (the owner-feed surface, Q-0214.2); **generalized retention simulator**
   (`economy/simulator.py`) — the search shipped, superbot's constants parameterized out
   (CE-10: "the kit ships the search, not our constants").
6. **Decisions ledger** (`ledger.py`) — the [D-NNNN] grammar (verdict + short why + provenance,
   Q-0214.4), machine-readable `supersedes:` + superseded-by stamping, `current_rules()` query,
   format checker + **stamp-discipline checker** (a D-id cited from >1 doc flags).
7. **Portable checkers** — `check_namespace` (AST: in-module shadowing, cross-module public
   dupes, reserved names — dogfooded over the kit's own concatenated namespace),
   `check_seam_authority` (config-driven fences), `check_orientation_budget` (the K0 word gate);
   all folded into `check --strict`.
8. **Hooks ×4** (`hooks/`) — SessionStart mode-aware orientation composition (status → stance →
   owner-style → lessons → triggers → practices → gauges → quota'd questions → observe
   proposal), PostToolUse edit advisor (generated-artifact / unbadged-doc), Stop-check advisor,
   + `settings.template.json` (all four events) + fill-table README. All fail-open, staged
   never live-written (#813 pattern).
9. **Templates 6 → 16** — the 14-template set complete (architecture / ownership /
   runtime_contracts / repo-navigation-map / helper-policy / owner-profile /
   collaboration-model / ai-project-workflow) + **CONSTITUTION.md.tmpl** + **decisions.md.tmpl**;
   zero dangling question-bank routes; architecture template carries the K0I-02 two-mechanism
   note ("Neither mechanism subsumes the other.").
10. **One-step adopt** (`adopt.py`) — `bootstrap adopt` = init + plant 17 artifacts
    (skip-if-exists) + stage the `.claude` material; `render --live` fills placeholders in
    planted docs in place; **AgentContextPack generator** (`contextpack.py`, index-OR-manifest
    input per design-spec §2.10); `session-start` / `session-close` orchestration commands;
    `answer`/`confirm` CLI intake; packaging (README + pyproject, placeholder name per owner
    flag 1).
11. **Interview hardening** — quota-aware asking, the anti-gaming answer floor (min_len +
    placeholder rejection), `confirm_slot` (provisional → filled), blocking-question
    escalation; bank grew Q-011..Q-013 (trigger-bound) + trigger/objective/min_len fields.

### Proven end-to-end (scratch dir, single file only)

bare dir + `dist/bootstrap.py` → `adopt` → `answer` ×5 → `render --live` →
`check --strict` **rc=0** → provisional self-answer → `review build` (anti-anchor payload
verified) → `review confirm --verdict pass` → confirmed → `economy check` (triple-filter hold
observed) → `contextpack` → `metrics` → `session-close` → observe-mode minimal orientation.
pip-install form works (`pip install ./substrate-kit`).

### The proof loop caught what unit tests couldn't (all fixed at root + guarded)

- **Docstring line starting "from "** hoisted into the dist's import block → SyntaxError; fixed
  in `build_bootstrap._split_imports` (triple-quote-aware) + regression test.
- **Aliased intra-package import** never exists in the concatenated dist → runtime NameError in
  `check`; de-aliased + a guard test bans the alias class in engine code.
- **Bare `adopt` without state** → adopt now runs idempotent init first (true one-step).
- **Fresh adopt born with 10 orphan findings** → the planted orientation router now links every
  planted doc (virgin adoption is `check --strict` clean).
- **session-close re-advised the mine it just ran** (stale pre-mine snapshot) → re-reads state.

### Adversarial review round (7 lenses / 40 agents; 29 confirmed, 4 refuted — all fixed at root)

The verify-stage skeptics reproduced every confirmed finding by execution. The three
**blockers** were all masked by /tmp-based proofs (the old guardrail temp-tree whitelist):
the dist's `_kit_root()` made the guardrail refuse `adopt` in **every real directory**
(now layout-aware; proven in `/home/user/kit-proof`); the pip wheel shipped **no templates**
(relocated inside the package + package-data + hard-error on empty; proven in a fresh venv);
and the harvest pass record counted as an inbound reference to every slug it licenses — the
triple filter was **unsatisfiable** (harvest records are now excluded as citation sources).
Majors included: autonomous self-answers neutralizing the blocking-question graduation gate
(provisional blocking answers now still escalate), the maturity gate being fail-open on typos
(now an allowlist with a real `gated` + `--reviewed` tier, and `actuators_may_apply` finally
has its caller — the promotion-rights gate is live), a non-atomic actuation lock (now
O_CREAT|O_EXCL), stray review verdicts escalating bogus questions (inert `not-provisional`
outcome), ledger supersede-stamping bleeding into prose sections, @overload false-flags,
inconsistent boot-doc resolution between the two budget consumers, fnmatch fence gaps in seam
exemptions, unguarded writer commands, planted docs false-flagged as generated artifacts, and
hooks crashing (not failing open) on corrupt config. Each fix carries a regression test.

### Owner-flag defaults honored (§5.B-addendum)

1 in-repo placeholder name `substrate-kit`, no external publish · 2 two-tier acceptance (this PR
= the §B shippable bar; the cold-start substrate-on/off A/B stays a separate Phase-2.5 session
and still gates Phase 3) · 3 review seam provisioned + config-doc'd, not hard-wired (graceful
no-reviewer fallback) · 4 retention PR 2's 7-file substep skipped (chat-only list; reference
gate protects) · 5 journal deeper-cut untouched (stop-growth posture only) · 6 the rebuild
design-spec approval stays the standing 🔒 gate — the kit interlock was built against the spec
as written.

### Session flags resolved

Gap re-established against source first (5-reader workflow; the addendum inventory held) ·
edit-only-in-debug pin kept (skills' declared capabilities remain the build-mode route — no
`build` stance added; deliberate) · context-economy engine built kit-native (superbot's
`check_retention.py` can consume it in retention PR 1) · hooks follow the #813 stage-only
precedent · #1639's golden-harness lane untouched · lane was uncontended (claim + early PR).

## ⚑ Self-initiated

- `render --live` (fill-in-place for planted docs) — not in any spec; closes the
  planted-docs-never-update gap the end-to-end proof exposed.
- `build_bootstrap` docstring-aware import splitting + the alias-import test guard — friction →
  guard (Q-0194 rider): both dist-breakage classes now have enforcing prevention.
- The namespace dogfood test (the kit's own checker run over the kit's concatenated namespace).

## 💡 Session idea

**Adopt-time telemetry seed:** `bootstrap adopt` could plant a tiny `metrics-baseline.json`
(boot-word count, doc census at adoption) so every later `economy check` can report drift
*since adoption* — giving a fresh repo the same "growth since baseline" visibility that
superbot only gained after months of retro-measurement. Cheap (the gauges already compute the
numbers), and it makes the kit's self-measurement story complete from day one. Dedup-checked
against `docs/ideas/` (nearest neighbor is the KPI/metrics work already shipped here; the
baseline-diff angle is new).

## ⟲ Previous-session review

The 2026-07-02 retention/Q-0214 session (#1648) left an exemplary handoff: the §5.B-addendum's
verified gap inventory was accurate to the file (all 18 verdicts confirmed against source by an
independent agent), and the owner-flag defaults were exactly the decisions this session needed
pre-made — zero owner round-trips. One improvement it surfaces: its addendum said "templates are
6 of 14" but the K0 interlock actually requires 16 (CONSTITUTION + decisions on top of the
plan's 14) — a handoff that names a count should name the *closure* set. Workflow improvement
shipped this session: builder-lane contracts with exact public-name assignments (the
concatenated-namespace rule) let 7 parallel agents build 210 tests' worth of modules with zero
file conflicts and zero name collisions — worth reusing as the standard fan-out pattern for any
multi-module build.

## 📊 Telemetry

- PR #1649 · 8 substantive commits · substrate-kit 117 → **407 tests** · ~30 new engine/template files
- 4 workflows (gap/specs ×5 · wave-1 ×7 · wave-2 ×2 · review 7 lenses + 33 verifiers) — ~3.8M subagent tokens
- Full CI mirror green (black/isort/ruff + mypy + full repo pytest); single-file dist 594KB
- End-to-end proofs: /tmp scratch ×3, **real-dir** /home/user/kit-proof, pip venv install

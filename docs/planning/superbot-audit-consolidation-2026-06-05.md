# SuperBot — Audit Consolidation (Codex + Agent A/B/C/D)

> **`historical` — 2026-06-05.** For *what is true now*, start at
> **`docs/current-state.md`**. Kept for the RC-1…RC-15 audit reconciliation
> history (the *why* behind decisions), not current state.

> **Status:** planning / verification artifact (not a binding contract, not
> implementation approval). Read this before acting on any of the five
> source audit docs — it supersedes their individual confidence claims
> where local verification disagrees.
>
> **Date:** 2026-06-05 · **Verification session branch:** `claude/pensive-davinci-xy6Fs`
>
> **What this doc is:** a reconciliation of the Codex cartography and the
> four parallel Agent audits against the *actual current source*, with
> every carried-forward finding given a status, severity, blocking level,
> owner, evidence, and next action. It merges cross-agent duplicates into
> root-cause topics so the next sessions fix causes, not symptoms.
>
> **What this doc is not:** a re-run of the audits. The audits mapped the
> repo; this pass checks their claims and removes the parts that source
> contradicts.

---

## 1. Current repo state (verified locally)

Unlike the five source audits — every one of which states it could **not**
run `git`, `pytest`, or the architecture/quality scripts (they were
GitHub-connector / source-read only) — this pass ran them.

| Check | Result |
|---|---|
| Branch | `claude/pensive-davinci-xy6Fs` (designated dev branch) |
| Working tree (pre-work) | clean |
| HEAD | `224919f` — *Merge pull request #511 … general feature layer audit* |
| `main` / `origin/main` | `9bc5c7a` (PR #484) |
| Branch vs main | `main` is an ancestor; **59 ahead, 0 behind** (no divergence) |
| Audit docs present | all 5 present, single copy each (no conflicting versions) |
| `python3.10 scripts/check_architecture.py` | **exit 0 — 0 errors, 88 tracked warnings** |
| `check_quality.py --check-only` (black/isort/ruff) | **all green** |
| `pytest tests/unit/invariants` | **220 passed** |
| `pytest tests/unit/governance` | **95 passed** |
| `pytest tests/unit/db` | **289 passed** |
| `pytest tests/unit/runtime` | **641 passed** |
| `pytest tests/unit/runtime/ai` + `test_ai_tools` + `test_paragon_service` | **205 passed** |

**Total executed: 1,450 unit tests, 0 failures; architecture + lint green.**
The audit baseline is sound. No stop condition was triggered.

**Not run this pass** (recorded honestly, carried to PR 0 in the roadmap):
full `pytest` suite, `mypy disbot/` (`check_quality.py --full`), the
`docs/smoke-test-checklist.md` Discord smoke pass, and BTD6 file/cloud/
Postgres provider-parity execution (needs a live DB / cloud bucket).

---

## 2. Source docs reviewed

**Audit inputs (the five being consolidated):**

- `docs/repo-cartography-2026-06-04.md` (Codex neutral inventory)
- `docs/audits/platform-runtime-data-layer-audit-2026-06-05.md` (Agent A)
- `docs/audits/agent-b-governance-control-audit-2026-06-05.md` (Agent B)
- `docs/audits/general-feature-layer-analysis-2026-06-05.md` (Agent C)
- `docs/audits/agent-d-btd6-ai-subsystem-audit-2026-06-05.md` (Agent D)

**Binding / reference docs reconciled against:**

- `docs/AGENT_ORIENTATION.md`, `docs/architecture.md`, `docs/ownership.md`,
  `docs/runtime_contracts.md`, `docs/architecture/service_ownership.md`
- `docs/platform-consistency-ledger.md` (binding status ledger)
- `docs/resource-provisioning-overview.md`, `docs/helper-policy.md`,
  `docs/helper-debt-inventory.md`, `docs/ui-view-adoption-audit.md`
- `docs/decisions/001-no-redis-backed-state.md`,
  `docs/decisions/002-game-state-not-restart-safe.md`,
  `docs/decisions/003-deferred-followups-after-refactor-program.md`
- `docs/loose-ends-audit-roadmap.md`, `docs/roadmap_setup_platform.md`,
  `docs/setup_wizard_finalization_plan.md`, `docs/help-command-surface-map.md`,
  `docs/cog-hub-coverage-audit.md`, `docs/games-actionability-roadmap.md`
- `docs/audits/repo-wide-audit-2026-05-29.md` (prior repo-wide audit — see §6)
- `architecture_rules/{layers,mutation_owners,duplicate_allowlist,canonical_helpers}.yaml`

All docs named in the task brief exist; **no missing-doc findings**.

---

## 3. Claims confirmed (source-verified this pass)

Each row was checked against the cited file/line, not taken from the audit
text.

| Claim | Source | Evidence (verified) |
|---|---|---|
| `core.events_catalogue` imports governance event constants (`core → governance`) | A | `disbot/core/events_catalogue.py:34-40` imports `EVT_*` from `governance.events`. **Caveat: already a tracked exception** — `architecture_rules/layers.yaml:136-139` (`ticket: arch-fix-11`). |
| `session_gc` owns game-state cleanup + economy refunds | A | `disbot/core/runtime/session_gc.py:29` module-imports `economy_service, game_state_service`; `_sweep_stale_game_state()` (`:82-134`) reads `state["bet"]` and calls `economy_service.refund(...)`. **Tracked** at `layers.yaml:202-205` (`arch-fix-11`); also *implements* ADR-002's refund contract. |
| Architecture checker ignores function-local cross-layer imports | A | `scripts/check_architecture.py:88-128` — `_ImportVisitor.visit_Import`/`visit_ImportFrom` return early when `_fn_depth > 0`. Docstring says lazy body imports are "NOT collected". **Genuine blind spot.** |
| Migration runner lacks duplicate/checksum/no-gap integrity checks | A | `disbot/utils/db/migrations.py:44-110` — sorts files, parses leading int, skips applied, applies in txn; no static duplicate/gap/checksum validation. Duplicate versions would fail late at runtime (PK violation), not pre-deploy. |
| Thread visibility cache identity omits `thread_id` (bleed risk) | B | `disbot/governance/cache.py:60-74` key = `(guild_id, ver, channel_id, tier[, role_fp])`. Resolver **has** `ctx.thread_id` (`resolver.py:55`, marked `# ISSUE-016`) but passes only `ctx.channel_id` to the key (`resolver.py:291`). Two threads sharing a parent channel collide. **Real correctness bug.** |
| Persistent views fail open on missing anchor | B | `disbot/core/runtime/persistent_views.py:58-75` — `interaction_check` returns `True` when `interaction.message` is falsy (`:62-63`) **and** when `anchor is None` (`:66-67`). |
| Settings/bindings still use placeholder authority (not typed capability) | B | `disbot/services/settings_mutation.py:32-33,75-78,423-451` — `_validate_authority` is an "administrator-tier floor … placeholder. Phase 4.5 replaces with typed capability". |
| Cleanup policy write accepts broader scope than the cleanup schema | B | `disbot/governance/writes.py:53-55` shared `_VALID_SCOPE_TYPES` includes `"thread"`; `set_cleanup_policy` reuses it (`:244`). Migration `009_thread_scope_constraint.sql:7-8` deliberately keeps `cleanup_policies` non-thread → thread cleanup write fails at DB, not service. |
| Many cogs are not thin adapters (views/modals/state in cog files) | C | View/modal classes live in cogs: `admin_cog.py:408,656`; `role_cog.py:52` (`RoleHubPanelView`); `chain_cog.py:393-511`; `cleanup_cog.py:441-531`; `deathmatch_cog.py:38,176`; `utility_cog.py:223-407`; `inventory_cog.py:165,267`. `check_architecture` emits matching `baseview_inheritance` / `views→cogs` warnings. |
| Cleanup command detection hardcodes `?`/`!` | C | `disbot/cogs/cleanup_cog.py:80` `self.command_prefixes = ["?", "!"]`. |
| Counting swallows persistence failures silently | C | `disbot/cogs/counting_cog.py:89-93` `_save_guild` wraps the write in `except Exception:` (swallow); spawned fire-and-forget via `tasks.spawn` at `:308,366,421,450,584,619`. |
| Channel visibility panel capped to first 25 text channels | C | Confirmed against Agent C reads of `channel_cog.py` / `views.channels`; UI text states category/guild scope is future work. (Surface-level; not re-walked line-by-line.) |
| AI tools are read-only and scope-gated | D | `disbot/services/ai_tools.py:6-16` ("Every tool here is **read-only**"; write tools "out of scope"); `_scope_allows` (`:54`); every spec carries `min_scope=AIScope.USER/ADMIN`. |
| BTD6 passive stage unregistered; central AI stage is the choke point | D | `btd6_cog.py:80-88,112-113` unregisters `BTD6_STAGE_NAME` unconditionally; `ai_cog.py:294-297` registers `natural_language_stage`. |
| Paragon: labelled local fallback; HTTP 429 never silently degrades | D | `disbot/services/paragon_service.py:5,16-21,107-133,217` — `estimated: bool`, 429 → `ParagonRateLimitError`, 5xx/schema → labelled estimate. |
| YouTube context is feature-flag + API-key gated | D | `disbot/services/youtube_context_service.py:3,9-10,109,119` — `is_enabled("youtube.context.enabled", …)` then `_API_KEY` required; defaults off. |
| `interaction_router` has no unregister API (process-lifetime registration) | D | `ai_cog.py:306,351` comments confirm; registrations are permanent and dedupe-guarded. Platform (Agent A) seam, not D's to own. |

---

## 4. Claims partially confirmed (source-confirmed, runtime/decision-pending)

| Claim | Source | Status & nuance |
|---|---|---|
| Thread cache bleed produces wrong help/cleanup visibility | B | Structure of the bug **confirmed**; the *observable symptom* (a real cross-thread visibility leak in production) is **not** runtime-reproduced. Needs the regression test B proposes. |
| Interaction router "fails open" when governance resolution throws | A | **Line-verified (2026-06-05, post-#516):** `interaction_router.dispatch()` increments `governance_fail_open_total` and proceeds with `governance=None` on a gate exception (~L144-154), and with `session=None` on session-resolution failure (~L156-167); `persistent_views.interaction_check` allows on a missing anchor (~L62-67). Posture is now ratified **per-surface in ADR-004** (fail-closed for owner/mutating, fail-open for read-only public); the RC-3 PR implements it plus the panel-serialisation test. |
| Panel render race in `get_or_render_panel` (delete→send→upsert without a lock) | A | Plausible; not reproduced. Needs verification that command/session flow already serialises panel commands. |
| Binding mutation cache invalidation is a no-op | B | **Confirmed-but-safe-today:** `platform-consistency-ledger.md` §1 (Bindings) shows `EVT_BINDING_CHANGED` has "zero consumers today" and reads come from authoritative `guild_config`. Becomes unsafe the moment a cached binding reader lands. |
| BTD6 has too many adjacent read/composition owners | D | Structurally confirmed (many `services/btd6_*` + `_builders`/`_embeds` + `ai_tools` BTD6 handlers). Whether this is *harmful* vs *acceptable* is an ownership-matrix **decision**, not a bug. |
| Static-fixture vs live-source freshness models are not uniform | D | Confirmed from comments/source; the *fix* (one provenance model) is a design decision that **blocks further extraction**, not a current defect. |
| Cloud provider may not expose the full `stats/` tree | D | Confirmed from `CloudRawProvider.list_names()` comments; **provider-parity not executed** (needs live cloud/Postgres). |
| Setup launcher recovery / skip-provenance gaps | B | Source comments confirm the gaps exist; not runtime-reproduced. Medium, non-blocking. |

---

## 5. Claims rejected / stale / overstated

This is the section that most changes how the source audits should be read.

| Claim (as stated) | Source | Why it is rejected / corrected |
|---|---|---|
| **Resource provisioning pipeline "has zero production callers" / "possibly unadopted"** | A (#5) | **Stale — the foundation IS adopted.** Grep shows real callers: `services/setup_operations.py:1059` (`.provision`), `services/readiness_repair.py:383`, `services/automation_executor.py:427`, `disbot/cogs/logging/provision_view.py:80,167` (`.preview`/`.provision`), and `views/setup/provisioning/{preview,confirm}_panel.py`. The "zero production callers" line is a **stale in-file docstring** (`services/resource_provisioning.py:59`) that Agent A propagated. Only the narrow sub-claim survives: the `RESOURCE_PROVISIONING_PRIMARY` kill-switch flag is *declared but not consulted* (`:61-62`). |
| **"`core.events_catalogue` / `session_gc` cross-layer imports are undetected drift"** | A (#1, #2) | **Overstated framing.** These module-level imports are **already tracked** known violations under one ticket (`architecture_rules/layers.yaml:133-213`, `arch-fix-11`) — a documented cluster of ~15 `core/runtime → services` + 2 `core → governance` entries. The checker does **not** miss them. The genuine gap is A#3 (function-local imports). Treat A#1/#2 as *accepted debt with a known ticket*, not new discoveries. |
| **"Stateful games have inconsistent restart/recovery behavior" (presented as a defect)** | C (#4) | **Reclassified, not rejected.** This is an *accepted architecture decision*: `docs/decisions/002-game-state-not-restart-safe.md` states per-cog restoration is opt-in, restart cancels the game, and staked coins are refunded via `economy_service.refund`. Deathmatch/Utility being process-local is **by design**. The only genuine bug inside this cluster is Counting's *silent* save-swallow (§3). Do **not** plan universal checkpointing — ADR-002 forbids it absent its re-evaluation criteria. |
| **Identity-contract strictness comments are stale** | A (#6) | **Plausible but not re-verified this pass** (did not line-read `bot1.py::_identity_contract_strict`). Downgraded to a doc-drift cleanup item, not carried as a confirmed finding. |
| **"`guild_resources.py` ownership comment is stale"** | A (#10) | Same — plausible doc-drift; folded into the doc/comment-drift cleanup topic (RC-13), not verified line-by-line. |
| Several Agent C "new" items (tournament platformization, mass command-annotation sweep, config-arbitration/per-guild access audit, deprecated-command help badge) | C (#1,#3,#5) | **Not new.** They are already enumerated as *intentionally deferred* in `docs/decisions/003-…md` §3. Reconcile against ADR-003 before treating them as fresh backlog. |

---

## 6. Cross-agent duplicate findings → merged root-cause topics

The audits independently rediscovered the same seams. Merged below. Full
classification table in §7; priority ordering in the companion
*architecture-priority-map* doc.

- **RC-1 Architecture-enforcement blind spot + tracked layering debt** ←
  A#1 + A#2 + A#3 + the `arch-fix-11` cluster + cartography risk
  "command access/governance spans runtime/services/governance". *One topic:*
  module-level cross-layer imports are caught-and-allowlisted; **function-local
  ones are invisible**, so new drift can enter via lazy imports. Fix the
  checker before relying on it to police the other boundary moves.
- **RC-2 Governance cache identity (thread bleed)** ← B#1 (GOV-1). Stand-alone
  correctness bug; `# ISSUE-016` already in source.
- **RC-3 Persistent-view / panel / interaction fail-open safety** ← B#2 +
  A#8 (interaction-router fail-open) + A#12 (panel render race) + C/D
  stale-panel mentions. *One topic:* define the missing-anchor / resolver-
  failure / panel-serialisation policy as **one** decision.
- **RC-4 Authority model not capability-native** ← B#3 (SET-1) + B SET-2 +
  the *declared-but-unconsulted flag* pattern (settings `SETTINGS_MUTATION_PRIMARY`,
  provisioning `RESOURCE_PROVISIONING_PRIMARY`). Blocks settings/bindings UI
  expansion, not current correctness.
- **RC-5 Cleanup scope + ownership split** ← B#4 + B CLEAN-1/2 + C#7. Service
  validation must split visibility-scopes from cleanup-scopes; naming
  ("command cleanup policy" vs "prohibited-word cleanup") must be disambiguated.
- **RC-6 Migration repository integrity** ← A#4 + A#9 (fresh-DB bootstrap drift).
- **RC-7 Runtime-owns-domain-cleanup / game lifecycle ownership** ← A#2 + C#4
  + ADR-002. The refund-in-GC is correct per ADR-002 but the *ownership*
  (core runtime knowing economy/game semantics) is the debt; resolve via a
  feature-cleanup-provider registry, not by moving refund logic around blindly.
- **RC-8 Cogs-not-thin / direct-DB / local-permission duplication** ← C#1 +
  C#2 + C#3, reconciled with ADR-003 deferrals. Group by feature + risk;
  start with a **docs-only Direct-DB Exception Ledger** before touching code.
- **RC-9 Provisioning adoption status** ← A#5 (mostly **stale**; see §5). Action
  is a *doc correction* + the kill-switch-flag decision, not adoption work.
- **RC-10 BTD6 provenance + ownership matrix + freshness model** ← D §6/§12/§13.
  **Blocks further BTD6 extraction.**
- **RC-11 AI orchestration centralization (healthy — preserve)** ← D §4/§15/§16.
  Not a problem to fix; an asset to **not** regress. Do not expand AI features
  until policy/quota/reply audit guarantees are locally tested.
- **RC-12 YouTube / media ownership ambiguity** ← D §18 + cartography risk.
  Maintainer decision: keep as shared `video_reference`/media subsystem, not BTD6.
- **RC-13 Doc / comment drift** ← A#6 + A#10 + stale provisioning docstring +
  stale audit baselines (the 5 audits cite an *older* base `d583dcb`; the
  prior `repo-wide-audit-2026-05-29.md` has a remediation table some items
  were already fixed under).
- **RC-14 Help / settings / slash parity** ← C#5 + C#6 + D footer/ephemeral
  notes + `loose-ends-audit-roadmap.md` Findings 2/3/5.

**Prior-audit reconciliation:** `docs/audits/repo-wide-audit-2026-05-29.md`
(six days older, base `5609fe8`, remediation table updated post-#414) already
ranked many of these P0–P3. Future sessions **must** check its remediation
status table before re-fixing — several boundary items it lists may already be
closed. The A/B/C/D audits did not cross-reference it.

---

## 7. Root-cause issue map (classified)

Severity = impact if unaddressed. Blocking: BI=blocks implementation broadly,
BX=blocks BTD6 extraction, BA=blocks AI expansion, BF=blocks one feature,
NB=does not block. Owner: PR=Platform/runtime, GV=Governance/interactions,
GF=General features, BD=BTD6/AI, DT=Shared docs/tooling, MD=Maintainer decision.

| ID | Title | Source | Status | Sev | Block | Owner | Evidence | Next action |
|---|---|---|---|---|---|---|---|---|
| RC-2 | Thread visibility cache bleed | B | confirmed | critical | BF (governance correctness) | GV | `governance/cache.py:60-74`; `resolver.py:55,291` (`ISSUE-016`) | Add `thread_id` to key (or bypass cache for thread ctx) + bleed regression test. |
| RC-3 | Persistent-view / panel / router fail-open policy | A,B | partially confirmed | high | BI | GV+PR | `persistent_views.py:62-67`; router/panel paths (not reproduced) | One decision: missing-anchor + resolver-failure + panel-serialisation policy; then implement + test. |
| RC-5 | Cleanup scope wider than schema; cleanup naming | B,C | confirmed | high | BF | GV | `governance/writes.py:53-55,244`; `migrations/009:7-8`; `cleanup_cog.py:80` | Split visibility vs cleanup scope sets (reject thread pre-DB); normalise prefix extraction; clarify naming. |
| RC-1 | Arch checker misses function-local imports; layering debt cluster | A | confirmed | high | BI (enforcement) | DT+PR | `check_architecture.py:88-128`; `layers.yaml:133-213` | Add lazy-import **report** mode + rationale allowlist; do not hard-fail initially. |
| RC-6 | Migration integrity guards absent | A | confirmed | medium | BI (next DB PR) | PR | `utils/db/migrations.py:44-110` | Static test: duplicate-version, monotonic/gap, optional checksum; fresh-DB bootstrap test. |
| RC-4 | Authority not capability-native; unconsulted flags | B | **decided + implemented** (ADR-005 A1+F1, this session) | high | BI (settings UI expansion) | GV | `settings_mutation.py:32-33,75-78,423-451`; `binding_mutation` no-op; ledger §1 | Typed capability resolver + operator kill-switches wired. Settings **UI** expansion still a follow-on. |
| RC-7 | Runtime GC owns game/economy cleanup | A | confirmed (intentional per ADR-002) | medium | NB | PR+GF | `session_gc.py:82-134`; ADR-002 | Feature-cleanup-provider registry; GC stays scheduler. Honour ADR-002 (refund is the contract). |
| RC-8 | Cogs not thin / direct DB / local perms | C | confirmed | medium | NB (slows change) | GF | view classes in cogs (§3); ADR-003 §3 overlaps | Docs-only Direct-DB Exception Ledger first; then per-feature service moves grouped by risk. |
| RC-9 | Provisioning "unadopted" claim | A | **stale/overstated** | low | NB | DT | callers in §5; stale docstring `resource_provisioning.py:59` | Correct the docstring; decide kill-switch flag. Not adoption work. |
| RC-10 | BTD6 provenance + ownership matrix + freshness | D | **decided** (ADR-006 Hybrid, this session) | high | BX | BD+MD | many `services/btd6_*`; provider comments | Provenance object + matrix binding; **extraction still paused** until the follow-on docs/schema PR. |
| RC-11 | AI central orchestration (preserve) | D | confirmed-healthy; **cooldown guard pinned** (this session) | n/a | BA (guardrail) | BD | `ai_tools.py`, `natural_language_stage`, policy resolver | Guard set complete. Still do **not** refactor the choke point; AI feature/tool expansion remains gated. |
| RC-12 | YouTube/media ownership ambiguity | D,Codex | **decided** (ADR-007 M1, this session) | low | NB | MD | `youtube_*` services; cartography §13 | Shared `video_reference`/media subsystem (not BTD6); `ownership.md` row + registration are a follow-on. |
| RC-13 | Doc / comment / baseline drift | A,Codex | needs verification | low | NB | DT | stale provisioning docstring; audits cite old base; prior audit remediation table | Small doc fixes; mark stale baselines; this consolidation is step one. |
| RC-14 | Help / settings / slash parity | C,D | confirmed | medium | NB | GF+GV | `rpshelp`/`dm_help`/`rpssettings`; slash `prefix="!"`; loose-ends Findings 2/3/5 | Parity pass after RC-8; reconcile with `loose-ends-audit-roadmap.md`. |
| RC-15 | Counting silent save-swallow | C | confirmed | medium | BF | GF | `counting_cog.py:89-93` | Surface/observe persistence failure (metric/log path), not silent `except`. |

---

## 8. Highest-risk problems (fix-first candidates)

1. **RC-2 — thread cache bleed.** The only confirmed *correctness* bug that
   can silently show the wrong commands/cleanup in threads. Small, localized,
   already flagged `ISSUE-016`. Highest value-to-risk ratio.
2. **RC-5 — cleanup thread-scope write fails late at the DB.** A bad write is
   accepted by the service then rejected by Postgres — confusing and
   inconsistent with the "service validates" contract.
3. **RC-3 — fail-open policy.** Not proven harmful, but it is a *policy* the
   project should set deliberately (especially for mutating panels) rather
   than inherit by default.
4. **RC-15 — Counting silent swallow.** Data loss with no signal; cheap to fix.
5. **RC-1 — fix the checker before leaning on it.** Every later boundary
   move (RC-4, RC-7) wants the architecture check to police it; today a lazy
   import would slip past.

---

## 9. Non-blocking cleanup problems (can wait)

- RC-8 (thin-cog migration) — large, low-risk-if-staged; needs the DB ledger first.
- RC-9 (provisioning docstring) — pure doc correction.
- RC-13 (comment/baseline drift) — bundle into one small docs PR.
- RC-14 (help/slash parity) — after RC-8; overlaps an existing roadmap.
- RC-12 (YouTube ownership) — a one-paragraph maintainer decision unblocks it.
- B GOV-2 (visibility/execution/exposure unification) — Agent B itself says
  **do not** split until consolidation shows a concrete need. Hold.

---

## 10. Unknowns requiring local runtime / test verification

Carried to **PR 0** in the roadmap. None block this docs pass.

- Full `pytest` suite + `mypy disbot/` (`check_quality.py --full`) — this pass
  ran a 1,450-test high-relevance subset, not the whole suite.
- BTD6 **provider parity**: do file/cloud/Postgres backends expose the same
  stats/paragon tree? (`CloudRawProvider.list_names()` suggests not.) Needs a
  live DB/bucket.
- Interaction-router fail-open path (RC-3) — reproduce or read-verify `dispatch()`.
- Panel render serialisation (RC-3) — confirm command/session flow serialises.
- Setup skip-provenance + launcher recovery (B SETUP-3/4) — regression-test.
- `docs/smoke-test-checklist.md` Discord smoke pass (BTD6 panel, paragon,
  refresh-source staff gate, YouTube on/off/no-key/cached-error).

---

## 11. Cross-compartment handoff notes

- **Platform/runtime (A):** owns RC-1 (checker), RC-6 (migrations), RC-7 (GC
  provider registry), and the platform half of RC-3 (router/panel). Keep
  lifecycle/tasks/runtime-lock **stable** while doing boundary cleanup — they
  are confirmed strong.
- **Governance/interactions (B):** owns RC-2, RC-5, RC-4, and the policy half
  of RC-3. RC-2 is the priority. Do not expand settings UI before RC-4.
- **General features (C):** owns RC-8, RC-14, RC-15. Start with the docs-only
  Direct-DB ledger; reconcile every "new" item against ADR-003 §3 first.
- **BTD6/AI (D):** owns RC-10, RC-11, and consumes RC-12. **Pause BTD6 data
  extraction** until the provenance/ownership decision lands. Preserve the AI
  choke point and the BTD6 faithfulness guard exactly as they are.
- **Maintainer (MD):** RC-12 (YouTube ownership), RC-4 flag semantics, RC-10
  provenance model, and the RC-3 fail-open posture are decisions, not code.

---

## 12. Final audit verdict

**The repository is healthy and not blocked.** Architecture, lint, and a
1,450-test slice are green locally. The four agents correctly identified the
real seams; this pass confirms the structural claims and **downgrades the two
most alarming-sounding ones** (provisioning "unadopted" → stale docstring;
game "inconsistent recovery" → accepted ADR-002 design).

The next move is **not** a broad implementation sweep. It is:

1. one small high-value correctness fix (**RC-2**),
2. a couple of deliberate governance/runtime policy decisions (**RC-3, RC-4, RC-5**),
3. fixing the architecture checker's blind spot **before** leaning on it (**RC-1**),
4. and a **decision gate** for BTD6 provenance (**RC-10**) before any more
   extraction — exactly as Agent D recommended.

Everything else is real but non-blocking cleanup that should be grouped by
root cause and sequenced per the companion *architecture-priority-map* and
*next-session-roadmap* docs.

> **Read next:** `superbot-architecture-priority-map-2026-06-05.md` (what to
> fix first and why) → `superbot-next-session-roadmap-2026-06-05.md` (PR
> sequence) → `superbot-source-of-truth-index-2026-06-05.md` (which docs to
> trust).

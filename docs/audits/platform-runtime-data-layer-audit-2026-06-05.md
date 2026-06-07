# Platform / Runtime / Data-Layer Audit — 2026-06-05

> **Status:** `audit`

> **Superseded (2026-06-05):** reconciled into
> [`../planning/superbot-audit-consolidation-2026-06-05.md`](../planning/superbot-audit-consolidation-2026-06-05.md)
> (verified, RC-n IDs). Read that first; this raw audit is historical context.

> **Scope:** docs-only Agent A audit of the platform foundation: startup/runtime lifecycle, task supervision, health/readiness, database/migrations/runtime lock, event bus/catalogue, session/panel/anchor infrastructure, resource provisioning foundation, architecture-rule coverage, and relevant tests.
>
> **Base inspected:** GitHub `main` at `d583dcb082580298e063d718ab7eb534a47ad3ea` (`Merge pull request #506 ... docs(btd6): smoke-test checklist + refresh stale counts`).
>
> **Method:** read-only GitHub source inspection. No files were modified during the audit pass itself. No local checkout was available, so local `git status`, `pytest`, and `scripts/check_architecture.py --mode strict` were **not** executed.

---

## Executive verdict

**Platform foundation has risks, but B/C/D audits can continue with caveats.**

The runtime foundation is structurally much stronger than earlier repo snapshots: lifecycle, task supervision, runtime lock, DB migration discipline, health/readiness, anchor recovery, session invalidation, and observability are all real systems rather than loose helpers.

The main remaining risk is **not** that the platform is missing a foundation. The risk is that ownership boundaries are still porous in several places, and some verification tools do not detect the exact category of drift the repo is now most likely to accumulate.

Most important next direction: **short platform cleanup/planning pass before large implementation work**, focused on cross-layer imports, runtime-owned domain cleanup, migration integrity, and provisioning adoption.

---

## Severity legend

| Severity | Meaning |
|---|---|
| 🔴 Critical blocker | Should block dependent implementation until fixed. |
| 🟠 Important | Should be prioritized soon; can create architectural drift, production confusion, or missed regressions. |
| 🟡 Medium | Real cleanup / verification gap, but not an immediate blocker. |
| 🟢 Future opportunity | Useful hardening or simplification after higher-priority issues. |

---

## Highest-priority findings

### 1. 🟠 Core imports governance event constants

**Finding:** `disbot/core/events_catalogue.py` imports constants from `governance.events`.

**Observed source:**
- `disbot/core/events_catalogue.py` imports `EVT_CACHE_INVALIDATED`, `EVT_CLEANUP_CHANGED`, `EVT_EXECUTION_ALLOWED`, `EVT_EXECUTION_DENIED`, and `EVT_VISIBILITY_CHANGED` from `governance.events`.

**Why it matters:**
- This creates an upward dependency from `core` to `governance`.
- It weakens the intended layering where core should define the platform primitive and governance should consume it.
- It increases circular-import fragility around event startup/catalogue validation.

**Root cause:** shared event names live in the governance layer, but the event catalogue is a core concern.

**Recommended fix:** move shared event constants/specs into a lower-level module such as `core.events_catalogue` or `core.event_contracts`, then have governance import from core instead of the reverse.

---

### 2. 🟠 Runtime session GC owns feature cleanup/refund behavior

**Finding:** `disbot/core/runtime/session_gc.py` imports `economy_service` and `game_state_service`, then performs stale game-state cleanup and bet refunds.

**Observed source:**
- `disbot/core/runtime/session_gc.py` imports `navigation_stack`, `scope_locks`, `economy_service`, `game_state_service`, metrics, and DB helpers.
- `_sweep_stale_game_state()` reads stale game state rows, inspects `state["bet"]`, refunds coins via `economy_service.refund(...)`, then deletes game-state rows.

**Why it matters:**
- Runtime GC now knows feature/game/economy semantics.
- Adding more persistent games could push more domain cleanup into core runtime.
- This makes it harder to reason about ownership and harder to test feature-specific recovery independently.

**Root cause:** the platform GC grew from session cleanup into feature-state repair.

**Recommended fix:** introduce a feature cleanup provider registry. Runtime GC should own scheduling and platform session/anchor cleanup; feature services should register stale-state cleanup providers and own refund semantics.

---

### 3. 🟠 Architecture checker misses function-local cross-layer imports

**Finding:** `scripts/check_architecture.py` intentionally ignores imports inside function bodies.

**Observed source:**
- `_ImportVisitor` tracks module-level absolute imports only.
- `visit_Import` and `visit_ImportFrom` return early when `_fn_depth > 0`.

**Why it matters:**
- The repo commonly uses function-local imports to avoid circular imports.
- That is useful, but it means real cross-layer drift can bypass architecture checks.
- Examples visible in this audit:
  - `core.runtime.interaction_router` imports governance inside `dispatch()`.
  - `core.runtime.persistent_views.PersistentView.on_error()` imports `views.base.handle_view_error`.
  - `core.runtime.session_gc` imports domain services at module level and would be caught, but similar lazy imports may not be.

**Root cause:** the checker conflates “does not create import-time cycles” with “does not violate architectural ownership.”

**Recommended fix:** add a second architecture mode/check that records function-local imports separately. Keep lazy imports allowed where justified, but require explicit allowlist/rationale for cross-layer imports.

---

### 4. 🟠 Migration integrity is operationally safe but not strongly guarded

**Finding:** the migration runner applies pending migrations under an advisory lock, but the repository appears to lack duplicate-version, checksum, and no-gap integrity checks.

**Observed source:**
- `disbot/utils/db/migrations.py` sorts `.sql` files, parses the leading integer, skips applied versions, applies pending files in transactions, and records `schema_migrations`.

**Why it matters:**
- Runtime application is safe, but repository integrity is not strongly pinned.
- Duplicate leading numbers, edited historical migrations, or numbering gaps could remain invisible until fresh DB setup or production boot.

**Root cause:** migration runner focuses on safe application, not migration-repository validation.

**Recommended fix:** add a static invariant test for migration filenames, duplicate versions, monotonic ordering, and optionally historical checksums.

---

### 5. 🟠 Resource provisioning pipeline is structurally ready but possibly not adopted

**Finding:** `services/resource_provisioning.py` defines a strong provisioning pipeline, but the file itself says the pipeline has zero production callers and that the `RESOURCE_PROVISIONING_PRIMARY` kill switch is declared but not consulted by the pipeline.

**Observed source:**
- `ResourceProvisioningPipeline` documents an 11-step contract: catalogue resolution, authority validation, bot permission validation, preview/confirmation, create/reuse, bind, audit, event emission, and typed result.
- The file also states: “Pipeline has zero production callers” and the feature flag is not consulted by the pipeline.

**Why it matters:**
- The foundation may look production-ready in platform docs while actual setup/logging/provisioning flows still bypass it or do not use it yet.
- Agent B needs to verify actual callers before treating provisioning as adopted infrastructure.

**Root cause:** platform foundation was built ahead of full UI/runtime adoption.

**Recommended fix:** explicitly classify provisioning as **foundation ready, adoption pending** until callsites are verified. If still zero production callers, plan the first adopter carefully, likely setup/logging provisioning.

---

## Other important quality improvements

### 6. 🟡 Identity-contract strictness comments are stale/inconsistent

**Finding:** `_identity_contract_strict()` says strict mode is now default-on with opt-outs, but nearby startup comments still describe strict as opt-in/default-off.

**Observed source:**
- `disbot/bot1.py::_identity_contract_strict()` returns strict unless `STRICT_DISABLED` is truthy or legacy `IDENTITY_CONTRACT_STRICT` is false-like.
- Later comments around identity-contract validation still say `IDENTITY_CONTRACT_STRICT=true` enables strict and default is off.

**Risk:** operator confusion. Reviewers may misunderstand whether fatal identity drift aborts startup by default.

**Recommended fix:** update stale comments/docs to match current behavior.

---

### 7. 🟡 `PersistentView` depends upward on `views.base`

**Finding:** `core.runtime.persistent_views.PersistentView.on_error()` imports `views.base.handle_view_error`.

**Why it matters:** runtime base classes should not depend on the views layer. This is a smaller boundary drift than the event catalogue issue, but it points in the same direction.

**Recommended fix:** move generic view error handling to a lower-level runtime/UI-support helper, or inject the error handler from the views layer.

---

### 8. 🟡 Interaction router fails open when governance resolution fails

**Finding:** `core.runtime.interaction_router.dispatch()` checks governance visibility before resolving sessions/dispatching handlers. If governance resolution itself throws, it increments `governance_fail_open_total` and allows the interaction.

**Why it matters:** this may be intentional availability-first behavior, but it has policy implications. A failed governance subsystem could allow interaction handlers that should be disabled.

**Recommended fix:** Agent B should decide the policy explicitly:
- fail-open for read-only/non-mutating panels only,
- fail-closed for mutating settings/setup/provisioning/admin panels,
- or keep global fail-open but document why availability wins.

---

### 9. 🟡 Fresh DB bootstrap can drift from migration-only expectations

**Finding:** `utils.db.migrations.create_tables()` still contains a domain-heavy pre-migration baseline with economy, job progress, inventory, XP, warnings, mod logs, roles, reaction roles, RPS, mining, deathmatch, chain, and counting tables.

**Why it matters:** the project has both a legacy bootstrap schema and forward migrations. Fresh DB behavior can diverge if the bootstrap baseline and migration chain are not tested together.

**Recommended fix:** add a fresh-DB bootstrap verification test. Longer term, consider reducing `create_tables()` to only migration infrastructure or generating a current baseline from migrations.

---

### 10. 🟡 `guild_resources.py` ownership comment is stale

**Finding:** `core/runtime/guild_resources.py` comments say channel/category/role creation lives in `utils/channels.py`, but the file itself now defines policy-free `ensure_channel`, `ensure_role`, and `ensure_category` helpers that create resources.

**Why it matters:** docs/comments mislead future contributors about where resource creation lives.

**Recommended fix:** update the comment to state the current ownership:
- `guild_resources` owns policy-free ensure/read helpers.
- `ResourceProvisioningPipeline` owns policy, audit, confirmation, and binding.

---

### 11. 🟡 Runtime-lock diagnostics are in-process only

**Finding:** `services.runtime.diagnostics_snapshot()` exposes boot ID and lock name only. It explicitly does not expose DB-backed live holder or heartbeat age.

**Why it matters:** during multi-replica or handoff incidents, operators need to know which boot owns the lock and whether heartbeat age is stale.

**Recommended fix:** add cached runtime-lock holder/heartbeat-age diagnostics from the heartbeat loop, or provide a safe async diagnostics command that reads `bot_runtime_lock` directly.

---

### 12. 🟡 Potential panel render race needs verification

**Finding:** `core.runtime.panel_manager.get_or_render_panel()` deletes the prior message, marks the old anchor stale, sends a new message, and upserts the new anchor. The function itself does not visibly take a per-user/channel/subsystem lock.

**Why it matters:** concurrent invocations could theoretically leave duplicate visible panels or stale anchor state if no higher-level lock serializes this flow.

**Recommended fix:** Agent B should verify whether command/session flow already serializes panel commands. If not, use a scoped lock around delete/send/upsert.

---

## Confirmed strengths

### Runtime lifecycle

- `core.runtime.lifecycle` owns process phases, shutdown/restart requests, command admission, event buffer, metrics, and diagnostics.
- `bot1.py` routes SIGTERM through lifecycle.
- A close-driver task turns pending lifecycle requests into `bot.close()`.
- Close execution, close completion, close timeout, and terminal phases are observable.
- Startup builds key runtime catalogues and posts a deterministic startup summary before `bot.start()`.

### Task supervision

- `core.runtime.tasks.spawn()` holds strong task references.
- It records `ok`, `error`, and `cancelled` outcomes.
- It supports `on_error` hooks and prefix cancellation.
- `bot1.py` drains via `tasks.cancel_all()` on shutdown.

### DB foundation

- Asyncpg pool is centralized.
- JSONB codec is registered at connection initialization.
- Migration application is transactional and protected by PostgreSQL advisory lock.
- Query wrappers observe DB latency and slow-path entries.

### Runtime lock

- Runtime lock ownership is stored in `bot_runtime_lock`.
- Boot acquisition uses a short advisory-lock mutex.
- Heartbeat refreshes ownership and exits on repeated failure or lost lock.
- Release deletes only the current boot’s row.

### Health/readiness

- Health server exposes `/health`, `/ready`, `/lifecycle`, and `/metrics`.
- Readiness requires both Discord gateway readiness and lifecycle command admission.
- This correctly returns not-ready during draining/shutdown.

### Sessions, anchors, persistent views

- Runtime sessions are scoped by user/guild/channel/subsystem.
- Session invalidation clears associated in-process navigation locks.
- Anchor restoration has a once-only reconnect guard to prevent duplicate `bot.add_view()` registration.
- Anchor restoration records restored/view-missing/stale outcomes.

### Tests already present

Observed tests cover:
- boot wiring and close-driver structure,
- lifecycle phase/admission/coalescing/event behavior,
- task supervisor outcomes/cancellation,
- runtime-lock DB primitives.

These are good foundations and should be kept stable while ownership cleanup proceeds.

---

## Root causes vs symptoms

| Root cause | Symptoms found |
|---|---|
| Shared contracts live in feature layers instead of platform contract modules | `core.events_catalogue` imports `governance.events`; event payload contracts are comments rather than typed specs. |
| Runtime utilities expanded into domain cleanup | `session_gc` owns game-state stale cleanup and economy refunds. |
| Architecture tooling optimizes for import-cycle safety but not full ownership safety | Function-local cross-layer imports are invisible to the checker. |
| Legacy compatibility remains broad | `utils.db.__init__` re-exports many feature CRUD helpers, making service-boundary enforcement harder. |
| Foundation built before adoption | Resource provisioning pipeline is strong but may have no production callers yet. |
| Documentation/comments lagged implementation | Identity strictness comment conflict; stale `guild_resources` ownership comment. |

---

## Missing verification from this audit

These were not completed because the audit did not have a local checkout:

- `git status --short`
- `git branch --show-current`
- local `git log --oneline -n 20`
- `python scripts/check_architecture.py --mode strict`
- targeted or full `pytest`
- direct full migration directory listing
- direct grep across every callsite with `rg`

Before merging this audit into a planning baseline, run at least:

```bash
git status --short
git branch --show-current
git log --oneline -n 20
python scripts/check_architecture.py --mode strict
pytest tests/unit/runtime tests/unit/db/test_runtime_lock.py tests/unit/test_bot_boot.py
```

---

## Recommended next step

Move this work to **Decisions** before implementation.

Recommended decision agenda:

1. Decide the intended layer contract for event names and payload specs.
2. Decide whether runtime GC should become a cleanup-provider orchestrator.
3. Decide how strict interaction governance should be on resolver failure.
4. Decide how architecture checks should treat lazy imports.
5. Decide whether resource provisioning is “ready but unadopted” or already used indirectly.
6. Decide the minimum migration integrity checks required before the next database-affecting PR.

---

## Suggested PR sequence

### PR A1 — Documentation/comment drift cleanup

Docs/comment-only or near-docs-only.

- Fix identity strictness comments.
- Fix `guild_resources.py` ownership comment.
- Add a short runtime ownership note linking lifecycle/tasks/runtime-lock/session/anchor boundaries.

### PR A2 — Architecture verification hardening

- Add lazy-import reporting mode to `scripts/check_architecture.py`.
- Add allowlist/rationale entries for known intentional lazy imports.
- Do not immediately fail every local import; start with report mode if the initial count is high.

### PR A3 — Migration integrity checks

- Add duplicate version detection.
- Add monotonic/no-gap or explicitly-allowed-gap check.
- Consider checksum capture for historical migrations.
- Add fresh DB bootstrap verification.

### PR A4 — Runtime GC ownership cleanup

- Introduce stale-state cleanup provider registration.
- Move game-state/economy refund semantics behind feature-owned provider(s).
- Keep runtime GC as scheduler/orchestrator only.

### PR A5 — Provisioning adoption verification

- Verify actual production callers.
- If none, document as foundation-only and choose first adopter.
- If callers exist, add tests proving they use the pipeline rather than direct Discord create/bind paths.

---

## Cross-agent handoff

### Agent B — Cogs, commands, panels, governance, setup

Check:
- interaction fail-open policy,
- command guard vs interaction router governance duplication,
- panel render serialization,
- persistent-view ownership and UI error handling,
- resource provisioning adoption from setup/logging/settings flows.

### Agent C — General features, games, economy, XP, moderation, utility

Check:
- direct DB usage through broad `utils.db` compatibility exports,
- game-state cleanup/refund ownership,
- whether features can register cleanup providers cleanly,
- whether service-layer separation is consistent across older cogs.

### Agent D — AI, BTD6, external data, heavy domain systems

Check:
- AI/BTD6 config and runtime data backends,
- AI/BTD6 event contracts,
- whether heavy domain systems respect platform/session/cache boundaries,
- whether BTD6/AI tools depend on broad DB/runtime helpers in ways that should be service-owned.

---

## Copy-paste collaboration summary

Agent A audited the SuperBot platform/runtime/data-layer foundation from GitHub `main` at `d583dcb` in read-only mode. No local checkout was available, so git status, pytest, and architecture script execution were not run. The platform foundation is broadly strong: lifecycle, task supervision, runtime lock, health/readiness, DB pool/migrations, session/anchor recovery, startup summaries, and observability are all real systems with meaningful tests.

Main issues to prioritize: `core.events_catalogue` imports governance constants; runtime session GC owns game/economy cleanup; architecture checks miss lazy cross-layer imports; migration integrity lacks duplicate/checksum/no-gap checks; resource provisioning appears foundation-ready but may still have zero production callers; identity strictness comments conflict with current default-on behavior; `PersistentView` reaches into `views.base`; interaction router fails open on governance resolver failure; fresh DB bootstrap can drift from migration-only expectations; `guild_resources.py` comments are stale; runtime-lock diagnostics do not expose live DB holder/heartbeat age.

Recommended next step: send this to Decisions before implementation. Decide event contract ownership, cleanup-provider shape, interaction fail-open/fail-closed policy, lazy-import architecture rules, provisioning adoption status, and migration integrity requirements. B/C/D audits can continue, but should treat platform as strong foundation with boundary-cleanup debt rather than fully clean.

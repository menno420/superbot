# AI configuration ownership (binding)

> **Status:** binding. Records the contract every AI-cog change must
> respect: the operator-facing snapshot is the source of truth, every
> UI surface reads from it, and every write flows through the existing
> mutation chokepoint. Doc-pin tests in
> `tests/unit/docs/test_ai_config_ownership_doc.py` keep this doc in
> sync with the code.
>
> **Scope:** read model + projection rules + mutation seam + UI surface
> contracts + audit fields + resolved semantics. Does NOT replace
> `docs/architecture.md` (layering) or `docs/ownership.md` (table /
> service ownership) — it sits alongside them as the AI subsystem's
> operator-coherence contract.

---

## Why this doc exists

The AI cog spans many surfaces: legacy scalar settings, typed AI policy
tables, behavior presets, a runtime resolver, an in-process memory
cache, decision audit, and a diagnostics panel. Before this contract,
each surface read its data slightly differently — operators saw
different "truths" in `!ai status`, `!ai policy`, `!ai settings`, and
the AI panel. This doc nails down one read model and forces every
surface onto it.

---

## 1. Read model — `AIConfigSnapshot`

`services.ai_config_projection_service.build_snapshot(guild_id)`
returns one immutable `AIConfigSnapshot` per call. It composes existing
services / repositories; it does NOT duplicate SQL, resolver rules,
memory semantics, diagnostics logic, or audit formatting.

Sub-namespaces:

| Field | Source | Purpose |
|---|---|---|
| `policy` | `utils.db.ai.get_guild_policy` + `list_channel_policies` / `list_category_policies` / `list_role_policies` | `ai_guild_policy` row + override counts |
| `memory` | `services.ai_memory_service.read_memory_settings` + `services.ai_conversation_service.stats` | window / scan / cache occupancy |
| `provider` | `services.ai_diagnostics_service.snapshot_for_cog` | provider, model, request/failure counters (no provider call) |
| `projection` | `services.settings_resolution.resolve_setting` × `ai_policy_mutation.projectable_keys` | drift status per projected legacy scalar |
| `instruction` | `utils.db.ai.get_instruction_profile` | active guild instruction profile id + name |
| `audit` | `services.ai_decision_audit_service.query` | latest decision row + per-decision counts over the recent window |
| `readiness_summary` | `services.ai_readiness_service.scan` (caller passes the summary line through) | optional one-line health string |

Every field tolerates unknown / missing data using `None` or `"—"` so
renderers never raise on a partially-configured guild.

### Non-mutating invariant (I-2)

`ai_config_projection_service` and `ai_readiness_service` are **read
orchestration only**. They MUST NOT:

- mutate settings
- project legacy scalars into typed policy
- append memory
- write audit rows
- invalidate resolver cache
- bump policy generations
- call AI providers

If a future caller needs any of those, it goes through the existing
mutation seam (`ai_policy_mutation`, `ai_instruction_mutation`) or the
pipeline stage — not the snapshot. The pin-test
`tests/unit/services/test_ai_readonly_invariants.py` enforces this by
AST scan; future contributors must keep it green.

---

## 2. Projection rules

`services.ai_policy_mutation.project_from_legacy_settings(guild_id, ...)`
is called by `services.settings_mutation.SettingsMutationPipeline` after
a successful legacy-KV write for `subsystem='ai'`. It re-reads every
projected scalar and upserts them into `ai_guild_policy` in a single
`set_guild_policy` call.

### Projected scalars (snapshot.projection.fields)

| Legacy settings key | Typed policy column |
|---|---|
| `ai_enabled` | `enabled` |
| `ai_natural_language_enabled` | `natural_language_enabled` |
| `ai_default_provider` | `default_provider` |
| `ai_default_model` | `default_model` |
| `ai_minimum_level_default` | `minimum_level_default` |
| `ai_cooldown_seconds` | `cooldown_seconds` |
| `ai_fresh_user_mention_allowance` | `fresh_user_mention_allowance` |

### Not projected (snapshot.projection.raw_scalars)

| Legacy settings key | Reason |
|---|---|
| `ai_memory_window_minutes` | Legitimately scalar — memory is in-process per-process state; no typed-table equivalent exists or is planned. `services.ai_memory_service.read_memory_settings` reads it directly. |
| `ai_memory_channel_scan_enabled` | Same as above. |
| `ai_guild_instruction_profile` | Stores a free-text instruction body. The typed-table editor in the Behavior chooser is the authoritative write path; the scalar is retained for backcompat reads only and is hidden from the primary settings panel. |

The projection-drift indicator on the snapshot (`projection.drift`,
`projection.drift_count`) compares the freshly-resolved legacy value
with the typed-policy column value. Drift is reported only when both
sides are populated AND disagree after coercion. A missing typed row is
NOT drift — it just means the guild has never written through the
settings UI yet.

---

## 3. Mutation seam

| Subject | Mutation entry point |
|---|---|
| Guild AI policy (master switch, NL baseline, provider, model, level, cooldown, fresh-user, guild instruction profile binding) | `services.ai_policy_mutation.set_guild_policy` |
| Channel / category / role overrides | `services.ai_policy_mutation.set_channel_policy` / `set_category_policy` / `set_role_policy` |
| Instruction profile body (typed table) | `services.ai_instruction_mutation.upsert_profile` |
| Decision audit rows | `services.ai_decision_audit_service.record` (called once per pipeline-stage invocation) |
| Settings → typed projection | `services.ai_policy_mutation.project_from_legacy_settings` (called by the settings mutation pipeline post-write) |

Reinforces `docs/ownership.md`'s direct-write blocklist for the AI
subsystem: **no view, cog, or panel may write to `ai_guild_policy`,
`ai_channel_policy`, `ai_category_policy`, `ai_role_policy`,
`ai_instruction_profile`, or `ai_decision_audit` directly.** All writes
flow through the named services.

### Preservation invariant (PR-6 territory)

Behavior preset application at any scope (channel / category / guild)
preserves every existing policy field not explicitly owned by the
preset. Implementation pattern: read the current row → apply only
preset-owned fields → pass everything else unchanged through the
mutation chokepoint. The preset-owned guild fields are exactly
`guild_instruction_profile_id` and `natural_language_enabled`.

---

## 4. UI surfaces

Every operator-facing surface reads from `AIConfigSnapshot` (and, where
applicable, the resolver's `dry_run=True` trace). No surface reads raw
`guild_settings` rows or queries `ai_*` tables directly.

| Surface | Snapshot fields read | Other inputs |
|---|---|---|
| `!ai status` | `provider`, `policy`, `readiness_summary` | — |
| `!ai readiness` | full snapshot | `services.ai_readiness_service.scan` |
| `!ai policy` | `policy` (overrides), `provider` (header) | resolver `dry_run=True` is the source of resolved precedence; optional `[#channel]` arg dry-runs against that channel. Snapshot is ancillary only — used for override counts + provider/model header, never for the resolved decision. |
| `!ai memory` | `memory` (full), `audit.latest['memory_turns_used']` for "last reply used memory" | Per-channel turn count comes from `ai_conversation_service.channel_stats(guild_id)` for the current channel (snapshot is guild-scoped). "Last reply used memory" renders `—` until PR-5 ships and populates the audit field. |
| `!ai settings` | `policy` (scoped-override counts), `projection`, `instruction` | The generic settings UI's "Scalar settings" field stays the editable list (schema-order, unchanged). The AI panel appends a "Quick reference (by purpose)" field grouping the scalars into Global baseline / Provider config / Memory config / Access gates / Advanced policy, plus the scoped-override summary. Purpose grouping lives in a presentation helper, not the schema. |
| `!ai routing` | `provider` (process-wide rows from `services.ai_diagnostics_service.list_task_routing`); `policy.default_provider` / `policy.default_model` for the "Guild override" footer line when set | Optional `[task]` arg filters to one row. |
| `!ai providers` | `provider`; `policy.default_provider` / `policy.default_model` for the "Guild override" field when set | — |
| `!ai why-no-response` | `audit` | — |
| `!ai support-report` | `policy`, `memory`, `provider`, `projection`, `audit` (PR-4A) | — |
| `!ai diagnostics` | `provider` | — |
| `!ai providers` | `provider` | — |
| `!ai forget` | — (mutates the conversation cache directly via `ai_conversation_service.forget_channel`; not a read surface) | — |
| AI panel header | `provider` only (no guild context) | — |
| AI panel buttons | full snapshot per click | resolver dry-run for policy preview |
| Behavior preview | `policy`, `instruction` | resolver `dry_run=True` (PR-4B) |

---

## 5. Audit fields — `ai_decision_audit`

The decision-audit table is written by `ai_decision_audit_service.record`
exactly once per natural-language stage invocation. Readers MUST tolerate
both pre-045 and post-045 schemas during the phased rollout — new
columns are nullable and render as `—` when missing or NULL.

### Columns (current schema)

| Column | Purpose |
|---|---|
| `id` (BIGSERIAL PK) | row id |
| `guild_id`, `channel_id`, `category_id`, `user_id`, `message_id` | message context |
| `task`, `route` | execution metadata |
| `decision` | enum: `allowed` / `denied` / `skipped` / `replied` / `degraded` / `errored` |
| `reason_code` | `PolicyDenialReason` enum value or sentinel `"none"` |
| `policy_snapshot_hash` | short hash of decision-influencing state |
| `instruction_profile_ids` (BIGINT[]) | profile ids active for this decision |
| `provider`, `model` | LLM invocation metadata |
| `created_at`, `expires_at` | TTL support |

### Columns added by migration 045 (PR-5, shipped)

All nullable; legacy rows stay NULL.

| Column | Purpose | Populated on |
|---|---|---|
| `memory_turns_used` | turns supplied to the prompt on a `replied` row | `replied` only |
| `memory_window_minutes` | active memory window at decision time | `replied` only |
| `memory_scan_attempted` | whether the Discord history scan was attempted | `replied` only |
| `memory_scan_added_turns` | turns appended by the scan, if any | `replied` only |
| `effective_source` | precedence scope that won (`channel` / `category` / `guild`) | every record() call that has a `PolicyDecision` |
| `effective_mode` | mode the winning source produced (`always_reply` / `mention_only` / `disabled`) | every record() call that has a `PolicyDecision` |

**Legacy-NULL rendering rule (I-4):** `_format_audit_row` in
`disbot/cogs/ai_cog.py` and the support-report draft renderer must
render `—` when any PR-5 field is NULL on the row being formatted.
Pinned by `tests/unit/cogs/test_format_audit_row_legacy_null.py`.

**Memory helper migration:** PR-5 introduces
`ai_memory_service.gather_recent_turns_with_metadata` returning a
`MemoryGatherResult(turns, window_minutes, scan_attempted,
scan_added_turns)` dataclass. The legacy `gather_recent_turns(...)`
is kept intact for current callsites; only the natural-language
stage migrates to the metadata-aware helper.

---

## 6. Resolved semantics

These are operator-visible decisions documented here so future agents
do not relitigate them.

- **Memory off semantics.** `ai_memory_window_minutes = 0` keeps the
  3-turn floor in `services.ai_conversation_service.MIN_FLOOR_TURNS`.
  The setting hint reads "Minimal — last 3 messages only" (PR-3). The
  floor is a deliberate basic-conversational-handle guarantee, not a
  bug.
- **Instruction-profile scalar (PR-6, shipped).**
  `ai_guild_instruction_profile` is hidden from the auto-rendered
  subsystem settings panel via the new `SettingSpec.hidden_from_panel`
  flag. The Behavior chooser's "Edit guild instruction" modal is the
  authoritative editor; it writes through
  `ai_instruction_mutation.upsert_profile` and then binds the resulting
  profile id via `ai_policy_mutation.set_guild_policy` (preservation
  invariant applies). The legacy KV row is retained for backcompat
  reads only.
- **`mention_only` at guild scope (PR-6, shipped).** Not supported.
  The Behavior chooser's preset picker hides cards whose mode is
  `mention_only` when scope=`guild`; the service raises
  `GuildScopeNotSupportedError` if a caller asks for it. Apply
  `mention_only` to a category or channel instead.
- **Guild preset preservation invariant (PR-6, shipped).** A guild
  preset application reads the current `ai_guild_policy` row, applies
  only the two preset-owned fields
  (`guild_instruction_profile_id`, `natural_language_enabled`), and
  passes every other field through `set_guild_policy` unchanged.
  Pinned by `tests/unit/services/test_ai_behavior_profile_guild_scope.py`.

---

## 7. Compatibility contracts

### Persistent UI custom_ids (I-5)

Persistent view `custom_id`s are compatibility contracts. Button
**labels** may change freely. Existing **custom_ids must remain
stable** unless the PR description names every prior custom_id being
retired and the operator action required (if any). Adding new buttons
is allowed; PR descriptions should verify no test asserts a fixed
`len(view.children)`.

The AI panel's button custom_ids today: `ai:refresh`, `ai:diagnostics`,
`ai:providers`, `ai:routing`, `ai:settings`, `ai:policy`, `ai:behavior`,
`ai:memory` (added in PR-3, row 2).

### Additive nullable migrations (I-4)

Schema additions to AI tables must be additive, nullable, and
idempotent so a long-lived deployment can apply them without operator
intervention. Migration 045 is the first such addition under this
contract.

---

## Doc-pin tests

`tests/unit/docs/test_ai_config_ownership_doc.py` enforces:

1. **Projection table sync.** Section 2's projected-scalars table
   lists exactly the keys in
   `services.ai_policy_mutation._LEGACY_TO_POLICY_FIELD`. Adding a
   key to the projection map without updating this doc is a CI fail.
2. **Settings-key sync.** Every constant in
   `disbot/utils/settings_keys/ai.py` appears in either the projected
   table or the not-projected table. Adding a settings key without
   placing it in one of the two tables is a CI fail.
3. **UI-surface coverage.** Section 4's table lists every prefix
   subcommand on `AICog` (extracted by AST scan). Adding a new `!ai
   *` subcommand without documenting its snapshot inputs is a CI
   fail.

---

## Cross-references

- `docs/architecture.md` — layering, invariants
- `docs/ownership.md` — table / service ownership (this doc is the AI
  subsystem's expansion of the AI rows there)
- `docs/runtime_contracts.md` — pipeline-stage and PersistentView
  guarantees the AI cog relies on
- `docs/ai-service-integration-map.md` — the AI subsystem's recommended
  integration paths for new AI-assisted features
- `docs/decisions/001-no-redis-backed-state.md` — why memory is
  in-process only

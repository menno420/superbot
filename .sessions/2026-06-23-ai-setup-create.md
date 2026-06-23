# 2026-06-23 — AI setup wedge: propose resource CREATION from a description

> **Status:** `complete` — born-red card (Q-0133) flipped green as the final step.
> Owner-directed (chat: "Yes go ahead" → the full form of the AI-setup wedge: create channels/roles
> from a description, not just bind existing ones). Builds on #1355. PR #1357 auto-merges on green (Q-0123).

## Arc

#1355 shipped `/setup-describe`: describe your server → the advisor proposes binding **existing**
channels/roles to subsystems. The natural next step (this session's idea, owner-approved) is the
**full form**: when a described server is *missing* a resource an important binding needs, propose
**creating** it. The apply seam already supports create+bind in one op — `_apply_resource_create`
builds a `ProvisioningRequest(mode="create", custom_name=…)` and `ResourceProvisioningPipeline`
creates the resource **and** binds it. The only missing piece is letting a *recommendation* express
"create" and threading it through validation + the op adapter + the review UI.

## Plan (this PR)

- `setup_plan.SetupRecommendation`: add `mode: "bind" | "create"` (default `bind`) and make
  `target_id` optional (`None` for create); `__post_init__` validates bind⇒target_id present,
  create⇒a proposed name. Deterministic advisor stays bind-only (unchanged behaviour).
- `setup_ai_advisor`: extend the strict JSON schema (`mode` enum + nullable `target_id`), teach
  `_validate_ai_payload` to build create recs, and let the prompt propose creating a missing
  resource. `_validate_against_schema` still gates (subsystem/binding/kind must exist) — create
  can't invent a binding either.
- `setup_operations.operations_from_recommendations`: map a create rec → `create_<kind>` op
  (`resource_mode="create"`, `resource_name=target_name`) so apply runs the existing create+bind
  pipeline.
- `views/setup/ai_review/`: render create recs distinctly (➕ create `name` → bind …).
- Tests across the model / schema / adapter / rendering.

**Contained + reversible:** still no *new* mutation code — create flows through the existing audited
`ResourceProvisioningPipeline`, applied only on explicit operator confirmation. Schema validation
still prevents inventing subsystems/bindings/kinds.

## Shipped (PR #1357)

- **`services/setup_plan.py`** — `SetupRecommendation` gained `mode: "bind" | "create"` (default
  `bind`) with `target_id` now optional (`None` for create); `__post_init__` enforces bind⇒target_id,
  create⇒target_name. New exports `RecommendationMode`, `RECOMMENDATION_MODES`, `CREATABLE_KINDS`
  (channel/role/category — members/threads are never fabricated). Field reorder is safe (all
  construction is keyword; verified by grep).
- **`services/setup_ai_advisor.py`** — strict JSON schema adds `mode` (enum) + nullable `target_id`;
  `_validate_ai_payload` builds create recs and drops a create of a non-creatable kind; the system
  prompt explains bind-vs-create and says "prefer binding an existing resource". `_validate_against_schema`
  still gates every rec, so create can't invent a subsystem/binding/kind.
- **`services/setup_operations.py`** — `operations_from_recommendations` maps a create rec →
  `create_<kind>` op (`resource_mode="create"`, `resource_name=target_name`); the existing
  `_apply_resource_create` → `ResourceProvisioningPipeline` then **creates the resource and binds it**
  in one audited step. Bind path unchanged.
- **`views/setup/ai_review/`** — the aggregate panel marks create recs `→ ➕ create`; the
  per-recommendation view shows `Create & bind: ➕ name (new kind)` instead of an id.
- **Tests:** `tests/unit/services/test_setup_create_recommendations.py` (12 — model validation · op
  mapping for channel/role/category · AI parse of create / non-creatable-drop / explicit-bind · the
  review embed marks creates). Existing setup suites unchanged and green.

## Why it's contained + reversible

Still **no new mutation code** — create flows through the existing audited `ResourceProvisioningPipeline`,
applied only on explicit operator confirmation (`can_apply_setup` gates Final Review). Schema validation
still prevents inventing subsystems/bindings/kinds, and only channel/role/category are creatable.

## Verification

- `python3.10 scripts/check_quality.py --full` → 12044 passed (the only two deltas — a stale
  `env-vars.md` whose line-number citations shifted with the advisor edit, and a black format — were
  regenerated/formatted and re-verified green via `--check-only` + the env-vars freshness test).
- `check_architecture --mode strict` → 0 errors (49 pre-existing warnings).
- Targeted: 79 setup-plan/advisor/operations/create tests green.

## Session enders

- **♻ Grooming (Q-0015):** executed this session's own forward idea (from #1355's log — "extend the
  wedge to propose resource creation") in the very next session: idea → shipped in one hop (Q-0172).
- **💡 Session idea (Q-0089):** *A confirmation guard for create recs in Final Review* — creating
  channels/roles is higher-impact than binding, so a create-heavy plan could show a distinct
  "N resources will be created" summary line (and count) before apply, so an operator can't
  rubber-stamp a plan that spawns ten channels. The data is already there (op.kind); it's a
  rendering + summary tweak. Small, contained; dedup-checked `docs/ideas/`.
- **⟲ Previous-session review (Q-0102):** #1355 did well to explicitly defer creation as a "clean
  follow-up" and name the exact missing pieces (schema + adapter) — that scoping note made this
  session fast (the design was pre-validated). *Workflow win it surfaced:* writing the deferred-scope
  paragraph into the PR body / session log is high-leverage — the next session inherits a ready plan.
  Keep doing that for every deliberately-deferred slice.
- **📋 Doc audit (Q-0104):** no new commands/env-vars → no generated-artifact regen needed; the
  feature + follow-up are captured here; ledger recorded on merge.

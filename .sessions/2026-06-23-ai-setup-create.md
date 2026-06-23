# 2026-06-23 — AI setup wedge: propose resource CREATION from a description

> **Status:** `in-progress` — born-red card (Q-0133). Flip to `complete` as the final step.
> Owner-directed (chat: "Yes go ahead" → the full form of the AI-setup wedge: create channels/roles
> from a description, not just bind existing ones). Builds on #1355. PR auto-merges on green (Q-0123).

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

## Status

In progress — born-red. Close-out written as the final step before flipping to `complete`.

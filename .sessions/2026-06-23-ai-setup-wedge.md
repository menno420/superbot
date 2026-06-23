# 2026-06-23 — AI natural-language setup wedge (`/setup-describe`)

> **Status:** `in-progress` — born-red card (Q-0133). Flip to `complete` as the final step.
> Owner-directed (chat: "continue from where you left off" → the AI-setup wedge I teed up after the
> positioning doc named it the highest-leverage next build). PR auto-merges on green (Q-0123).

## Arc

The positioning north-star (#1352) named the **AI-setup wedge** — *"describe your server, it
configures itself"* — as the one capability that's both a genuine "whoa" demo and structurally hard
for incumbents to retrofit. Orientation found the infrastructure **already largely exists**:
`services/setup_ai_advisor.OpenAISetupAdvisor` turns a `GuildSnapshot` into a schema-validated
`SetupPlanDraft`, and `views/setup/ai_review/AIReviewPanelView` renders that draft → accept →
`operations_from_recommendations` → the audited Final Review apply path. The **only missing piece**
is a *natural-language input* path — folding the operator's free-form description into that prompt.

This PR adds exactly that, reusing everything else.

## Plan (this PR)

- `OpenAISetupAdvisor.suggest_with_description(snapshot, description)` (+ a shared private `_run`) —
  folds the operator's description into the prompt/payload; reuses the existing JSON schema,
  `_validate_ai_payload`, gateway, and degraded handling unchanged.
- `services/setup_natural_language_advisor.suggest_from_description(...)` — thin entry: builds the
  configured advisor, uses the description only when the AI advisor is available, else falls back to
  the deterministic snapshot-only plan (description simply unused, never an error).
- `cogs/setup/_describe_entry.py` — snapshot → advisor → open the existing `AIReviewPanelView`
  ephemerally (admin-gated; apply stays gated by `can_apply_setup` inside Final Review).
- `/setup-describe <description>` + `!setupdescribe` commands in `setup_cog` (thin delegators).
- Tests for the advisor + the NL entry.

**Contained + reversible:** no new mutation code — the proposal flows into the existing audited
apply seam, applied only on explicit operator confirmation. Resource *creation* (vs binding existing
channels/roles) stays a follow-up (the recommendation schema is binding-only today).

## Status

In progress — born-red. Close-out written as the final step before flipping to `complete`.

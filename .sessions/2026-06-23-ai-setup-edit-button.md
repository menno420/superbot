# 2026-06-23 — AI-setup advisor: Accept · Deny · Edit (the Q-0048 finalize)

> **Status:** `in-progress` — owner-directed. **Q-0048 decision (owner, 2026-06-23):** *"AI should apply
> them but only after a confirmation; AI should spawn three buttons — accept, deny, edit."* The
> propose→stage→Final-Review→audited-apply path already exists; this adds the missing **Edit** affordance
> so each AI suggestion is Accept · Deny · Edit. PR this session; auto-merge armed on green (Q-0127);
> owner-directed → merge immediately (Q-0191).

> **Run type:** `manual · owner-directed`

## What already exists (code-verified)

The generative AI-setup wedge is built end-to-end:
- **Propose** — `services/setup_natural_language_advisor.py` + `setup_plan.py` (`SetupRecommendation` /
  `SetupPlanDraft`, `mode="create"|"bind"`); reached via `/setup-describe` (#1355) + propose-resource
  (#1357).
- **Review** — `views/setup/ai_review/main_panel.py` (`AIReviewPanelView`: Accept-all-high · Review
  one-by-one · Reject-all · Rerun · **Stage & open Final review**) + `per_recommendation.py`
  (`PerRecommendationView`: Accept · Reject · Skip · Back, building an `AcceptedSet`).
- **Apply (gated)** — *Stage & open Final review* adapts the accepted set to `SetupOperation`s via
  `setup_draft.replace_recommended_for_section` → `FinalReviewView` → the audited dispatcher, behind a
  `setup_access.can_apply_setup` permission check. **So "apply only after confirmation" already holds.**

## The gap (the Q-0048 ask)

The per-suggestion walkthrough has Accept / **Reject** / Skip / Back — **no Edit**, and "Reject" ≠ the
owner's "Deny". The owner wants each AI suggestion to show **Accept · Deny · Edit**.

## Plan (one focused change, propose-only)

- `per_recommendation.py`: reshape the action row to **Accept · Deny · Edit** (rename `_reject`→`_deny`,
  label "Deny"; keep Skip/Back as nav on row 1). Add an **Edit** button → `_EditRecommendationModal`
  (a single name field) that, on submit, rewrites the `create` suggestion's `target_name`
  (`dataclasses.replace`), swaps it into the draft, accepts it, and advances. For a `bind` suggestion
  (binds an *existing* resource) Edit explains it only applies to resources the bot will create — Deny +
  rebind manually. **No DB / Discord writes** (the module's zero-write contract tests stay green); the
  edited op still applies only through the gated Final Review.
- Tests: the Edit flow (modal submit renames + accepts + advances), the bind-mode explain path, the
  Deny rename.

(Close-out enders at session close.)

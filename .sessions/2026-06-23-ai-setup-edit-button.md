# 2026-06-23 — AI-setup advisor: Accept · Deny · Edit (the Q-0048 finalize)

> **Status:** `complete` — owner-directed. **Q-0048 decision (owner, 2026-06-23):** *"AI should apply
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

## Close-out

**Verification:** `check_quality --full` green — **12187 passed**; new Edit-flow tests (modal-open for
`create`, explain for `bind`, `apply_edit` swap+accept, modal-submit advance) pass; the module's
zero-write contract tests (`test_module_has_no_db_imports`, `test_module_has_no_direct_discord_create_calls`)
stay green; `check_architecture --mode strict` 0 errors; ledger + `check_docs --strict` pass (Q-0104).

**Q-0048 recorded:** the owner's decision (AI applies setup changes only after confirmation; per-suggestion
Accept/Deny/Edit) is captured here as the provenance for this change. Should also be appended to the
question router as a formal owner decision (the durable home) — flagged for the docs-reconciliation pass.

**💡 Session idea (Q-0089):** *Edit-the-binding for `bind` suggestions, not just rename-for-`create`.* This
PR's Edit renames a resource the bot will create; a `bind` suggestion (AI picked an existing channel/role)
can currently only be Denied + rebound manually. A natural follow-on: Edit on a `bind` rec opens a
`discord.ui.ChannelSelect`/`RoleSelect` to re-pick the target in place (re-`dataclasses.replace` the
`target_id`/`target_name`), so the operator can correct the AI's pick without leaving the walkthrough.
Bounded, reuses the same `apply_edit` seam. (Captured; small follow-on.)

**⟲ Previous-session review (Q-0102):** the previous session (settings-reachability guard, #1385) did well
to *investigate before building* — it discovered the catalogue is bot-dependent and avoided inventing
schemas that don't belong, shipping an honest guard instead. The same instinct paid off here: I read the
existing `ai_review/` surface before coding and found the apply path was **already built and gated**, so
the Q-0048 ask reduced to one missing button rather than a from-scratch feature — saving a large mis-scoped
build. **System improvement (applied):** when an owner asks for a capability that sounds large ("AI applies
setup changes"), *first map what already exists end-to-end* — the gap is often far smaller than the ask
implies. Routine worth keeping: read the live surface before estimating scope.

**Claim** `docs/owner/claims/claude__ai-setup-edit-button.md` deleted at close (Q-0126).


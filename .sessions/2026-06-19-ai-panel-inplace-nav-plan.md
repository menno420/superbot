# 2026-06-19 — Promote the AI-panel in-place-navigation idea to an executable plan

> **Status:** `complete`

## Arc (what I did)

Fourth slice of this dispatch run (after #1058 edit_in_place + #1059 back_button). The mandatory
backlog-grooming ender (Q-0015) + a Q-0172 self-initiated idea→plan promotion: structured
[`ideas/ai-panel-inplace-navigation-2026-06-11.md`](../ideas/ai-panel-inplace-navigation-2026-06-11.md)
into an executable plan. **Why this idea:** it is the *only* blocker for graduating the consistency
linter's `edit_in_place` rule — that rule's 17 remaining warn-only findings (after #1058's triage) are
*exactly* the `views/ai/` family. Building this plan both fixes the owner's headline 2026-06-11 UX
complaint and unblocks rule 1's graduation.

## Shipped (#1060)

- New plan: [`planning/ai-panel-inplace-navigation-plan-2026-06-19.md`](../planning/ai-panel-inplace-navigation-plan-2026-06-19.md)
  — re-verified the source scope (18 `views/ai/` classes, all raw `discord.ui.View` except the
  `AIPanelView` `PersistentView`; the blanket `canonical_helpers.yaml` exemption makes the debt
  ratchet-invisible), the target in-place HubView pattern, and a **2–3 PR build order**: PR 1 (AI anchor
  + page model, clears panel.py's 3 findings) → PR 2 (chooser sub-trees in place, clears the 14 chooser
  findings → rule 1 graduation candidate) → PR 3 (narrow the exemption + the second owner ask
  "centralize settings by task" + graduate `edit_in_place` to error). Marked `needs-hermes-review` +
  live-guild-walk per PR (substantial UI; not offline-testable).
- Updated `docs/ideas/README.md` (idea → "PROMOTED to a plan") and `docs/roadmap.md` AI § Later (idea →
  "Now an executable plan") so the promotion is reachable from both indices.

## Continuation (the handoff)

The plan is turn-key for a session with runtime context / a Q-0086 joint live session. PR 1 is the
startable foundation. **This is the path to graduating consistency rule 1** — until PR 2 lands and the
17 `views/ai/` findings clear, `edit_in_place` stays warn-only (rules 2/3/4 are already at 0 and are the
nearer graduation candidates).

## Context delta

- **Pointed to and needed:** the idea file's source-confirmed diagnosis + scope sketch carried 80% of
  the plan; the linter plan + #1058's triage made the "this idea blocks rule 1" link explicit.
- **Discovered by hand:** re-counted the live `views/ai/` tree (18 classes) and confirmed only
  `AIPanelView` is non-raw — the idea's per-file ephemeral counts were a 2026-06-11 snapshot; the
  class-level shape is unchanged, so the plan stands.

## ⟲ Previous-session review (Q-0102)

The previous slice (#1059, back_button) cleanly drove a rule to 0 by *verifying* the FP class rather
than trusting the plan's prediction — good discipline. What the whole linter lane had **not** done until
this run: connect the warn-only backlogs back to the *product* work that clears them. #1058 surfaced that
rule 1's residue is the AI-nav idea; this slice closed the loop by promoting that idea to a buildable
plan. **System improvement:** a warn-only linter finding that maps to an existing idea/plan should *say
so* (the consistency_exceptions.yml now points `views/ai/` at the idea). Generalizing: the linter's
graduation tracker could carry, per rule, the plan/idea that clears its residue — turning "why is this
still warn-only?" into a one-hop answer. Captured below.

## 💡 Session idea (Q-0089)

**A per-rule "graduation blocker" line in the consistency-linter plan/tracker.** Each warn-only rule
that can't yet flip to `error` is blocked by *something specific* (rule 1 ← the AI-nav redesign; a
future rule ← an open triage). Recording that blocker (plan link) next to each rule's count makes the
graduation queue self-explaining and stops a later agent re-deriving "what's left?" by hand. Distinct
from #1058's `--diff` baseline idea (regression-guarding) and #1059's root-vs-child idea (a smarter rule
input) — this is about the *graduation* metadata. Worth having; captured, not built.

## 📊 Doc audit (Q-0104)

- New plan reachable from `docs/ideas/README.md` + `docs/roadmap.md` (both updated). `check_docs --strict`
  should stay green (run it at close).
- No new owner decisions (the idea was already owner-requested; Q-0172 covers the self-initiated
  promotion). Flagged on the run report's ⚑ Self-initiated line.
- Ledger lag (#1053/#1055) unchanged — benign newest-merge lag for the #1080 pass (see #1058's card).

## 📤 Run report

- **Did:** promoted the owner-requested AI-panel in-place-navigation idea into an executable 2–3 PR plan
  (the blocker for graduating consistency rule 1); updated the idea index + roadmap. · **Outcome:** shipped
- **Shipped:** #1060 — `planning/ai-panel-inplace-navigation-plan-2026-06-19.md` + ideas-README + roadmap
  promotion entries.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none` (the redesign direction is already owner-approved; the plan's
  settings-centralization shape is a design proposal for the executing session, not an owner gate).
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** **YES** — promoted [`ideas/ai-panel-inplace-navigation-2026-06-11.md`](../ideas/ai-panel-inplace-navigation-2026-06-11.md)
  → [`planning/ai-panel-inplace-navigation-plan-2026-06-19.md`](../planning/ai-panel-inplace-navigation-plan-2026-06-19.md)
  under Q-0172 (no dispatched order named it; it was surfaced by #1058's triage as rule 1's blocker).
  Docs-only; the build itself stays `needs-hermes-review` + live-walk.
- **↪ Next:** graduation prep for rules 2/3/4 (all at 0); execute the AI-nav plan PR 1 in a runtime
  session to start clearing rule 1's 17.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session (run total) | 3 (#1058 edit_in_place · #1059 back_button · #1060 AI-nav plan) |
| Ideas groomed (Q-0015) | 1 (AI-nav idea → executable plan) |
| Self-initiated promotions (Q-0172) | 1 |
| CI-red rounds | 1 (born-red session gate by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (per-rule graduation-blocker tracker line) |

# 2026-06-21 — Reaction-roles plan: presentation & editing requirements

> **Status:** `complete` — follow-up to #1215/#1216. Owner added four requirements: edit an
> existing reaction-role message; embed theme presets; pre-customized starter-message templates;
> optional PIL image cards. Folded into the plan. Docs-only → self-merge on green.

> **Run type:** `manual`

## Arc

All four fit existing infra, so they're cheap enhancements on the PR 2 builder, not a new subsystem:
- **Edit-in-place** — our `role_menus`/`role_menu_options` rows + stored `message_id` make edit =
  update row → re-render → `message.edit()` (no repost). First-class, folds into PR 2.
- **Theme presets** — named catalogue on `utils/ui_constants.py` + the pattern-library archetypes;
  stored in `role_menus.theme`. Folds into PR 2.
- **Message templates** — starter-message data catalogue (`disbot/data/`, the `general_content.json`
  precedent) as a builder gallery. Folds into PR 2.
- **PIL cards** — reuse `utils/welcome_render.py::render_welcome_card()` (lazy PIL, `bytes|None`
  graceful fallback); a `render_role_menu_card` sibling. Optional **PR 4** (owner-paced), degrades
  to embed-only when Pillow absent.

Added plan §4.6 + two rows to the §5 "improve on Carl" table (editing, presentation).

## 📤 Run report

- **Did:** folded the owner's four presentation/editing requirements into the plan (§4.6) · **Outcome:** shipped (plan refinement)
- **Shipped:** #1217 — reaction-roles plan §4.6 presentation & editing (docs-only)
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none new (the §9 design Qs still stand — surface priority + the 3 prior)
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (direct owner request)
- **↪ Next:** owner answers the §9 design Qs / picks surface; then build reaction-roles PR 1 (audited seam, unblocked) → PR 2 (in-Discord builder incl. edit + themes + templates)

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 2 (#1215, #1216); 1 pending (#1217) |
| CI-red rounds | 0 |
| Repo-rule trips | 0 |
| New ideas contributed | 0 (plan refinement) |
| Ideas groomed | 0 |

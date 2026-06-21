# 2026-06-21 — Reaction-roles plan: presentation & editing requirements

> **Status:** `in-progress` — follow-up to #1215/#1216. Owner added four requirements: edit an
> existing reaction-role message; embed theme presets; pre-customized starter-message templates;
> optional PIL image cards. Folding them into the plan. Docs-only. Flips `complete` last (Q-0133).

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

(Body filled at close.)

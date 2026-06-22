# Session — reaction-roles PR 6: PIL banner cards (§4.6d)

> **Status:** `in-progress`
> **Branch:** `claude/funny-franklin-n6dceb` · **Run type:** routine · dispatch
> **Started:** 2026-06-22

## What I'm about to do

Build **reaction-roles overhaul PR 6 — optional PIL banner cards** (the last non-web slice of the
mature reaction-roles arc; [plan §4.6d](../docs/planning/reaction-roles-overhaul-plan-2026-06-21.md)).
A role menu can optionally render a **banner/header image** attached to its message, reusing the
shipped `welcome_render` PIL pattern (lazy import + `bytes | None` graceful fallback, no network).

Scope:
- migration **085** — `role_menus.card_template` + `card_text` columns (nullable; NULL = no card,
  so an existing menu is byte-identical).
- `utils/role_menu_render.py` — `render_role_menu_card(...)` sibling to `welcome_render`.
- `utils/role_menu_presentation.py` — a small `CardTemplate` catalogue (a few preset banner styles).
- thread `card_template`/`card_text` through `utils/db/role_menus` + `services/reaction_role_service`.
- `views/roles/role_menu_view.py` — `build_menu_message()` composer (embed + optional attached card).
- `views/roles/role_menu_builder.py` — a 🖼️ Card picker + overlay-text modal; post/edit/repost
  attach (or remove) the card; **degrade to embed-only** when Pillow is absent.
- tests for the renderer, the presentation catalogue, the db/service threading, and the composer.

**Gate:** ⚑ self-initiated (Q-0172) — promotes a *planned-but-deferred, owner-paced* slice. Labelled
`needs-hermes-review` (NOT self-merged) so it does **not** auto-merge — respecting the plan's
"owner-paced follow-up · greenlight as a follow-up" intent while shipping the work for review.

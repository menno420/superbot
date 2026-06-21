# 2026-06-21 — Reaction roles: gradient presets gallery

> **Status:** `in-progress` — born-red HOLD (Q-0133). **⚑ Self-initiated** continuation of the
> colour/gradient work (#1237) — the captured #1237 session idea, built under Q-0172 (ideas exist to
> be built) + the standing act-and-improve directive. Fresh branch (Q-0014).

> **Run type:** `manual`

## What I'm about to do

Finish the colour-role thread with a **gradient presets gallery** — a small curated catalogue of
tasteful two-colour gradients (Sunset / Ocean / Berry / Forest / Fire / Candy) offered as one-tap
picks in the role-menu builder's 🎨 Colours flow. Each preset auto-creates a gradient colour role via
the already-shipped `reaction_role_service.ensure_color_role` seam and adds it to the menu — the
"blank-page killer" for styled roles, mirroring the message-template gallery.

- `utils/role_menu_presentation.py` — a `GradientPreset` catalogue + `gradient_presets()` (pure data,
  the themes/templates precedent).
- `views/roles/role_menu_builder.py::_ColourRolesView` — a gradient-presets select, **only added when
  the guild has the Enhanced-Role-Styles perk** (`supports_role_gradients`); reuses the tested
  `_commit_colour_roles` path (so the solid-colour fallback still applies if the perk lapses).

Verify: `check_quality.py --full` + `check_architecture.py --mode strict`.

# Idea — enrich the BTD6 CT event detail with relics + the hex map

> **Status:** `ideas` — brainstorm, not approved. Promotion path: `docs/ideas/README.md`.
> **Captured:** 2026-06-16 (BTD6 live-events follow-up; found while building #953).
> **Subsystem:** btd6 — BTD6 Live Events / CT detail.

## The gap

PR #953 made BTD6 **Live Events** current-event-first: the overview drills into a rich per-event
detail. That detail is genuinely rich for **race / boss / odyssey** (window, rules, banned/limited
towers, disabled flags, scores, coverage), because those kinds have `_towers` restriction metadata.

But **Contested Territory (CT)** has no `_towers` metadata, so drilling into a *live* CT event from
the overview shows only **name + window** — thin, and exactly the kind of "this doesn't show all the
info" the owner flagged. Meanwhile the genuinely rich CT data already exists in a **sibling** view:
the panel's 🗺️ CT button renders relic tiles + a hex map (`build_ct_browser_embed` +
`views/btd6/ct_map_view.build_ct_map_file`). The overview just doesn't connect to it. (CT *was* one
of the live events in the owner's recording, so this is a real, reachable gap.)

## The idea

When the event detail is a CT event, surface its relics + map — reusing the existing builders, not
duplicating them. `build_ct_map_file(ct_id)` already accepts a specific `ct_id`, and
`btd6_live_query_service.get_ct_tiles(ct_id)` returns the relic placements. Two clean options:

1. **A button** on the CT event detail — "🗺️ Map & relics" — that edits in place to the rendered
   hex map (attach via `safe_edit(attachments=[file])` + `embed.set_image("attachment://ct_map.png")`)
   plus a relic-tile summary, with ↩ back to the detail. Lowest-risk; reuses the panel's exact path.
2. **Inline** a compact "Top relics on the map" field in the CT detail (no image), from
   `get_ct_tiles(ct_id, relics_only=True)`.

Option 1 is preferred — it reuses the proven CT map renderer and keeps the shared
`build_event_detail_embed` (used by the prefix `!btd6events event` surface too) unchanged.

## Cautions

- Keep it CT-specific (gate on `entity_kind == "btd6_ct"`); don't bolt CT logic onto the generic
  detail builder.
- Pillow may be absent in the sandbox — degrade to the text relic summary (the CT map renderer
  already returns `None` then).
- Don't duplicate the relic-label / tile-classification logic that lives in `ct_map_view`.

## Disposition

Small/safe UX follow-up to #953. Promote to a focused PR when the BTD6 lane has capacity. Relates:
`views/btd6/live_events_view.py` (detail), `views/btd6/ct_map_view.py`, `cogs/btd6/_builders.py`
(`build_ct_browser_embed`), `services/btd6_live_query_service.py` (`get_ct_tiles`).

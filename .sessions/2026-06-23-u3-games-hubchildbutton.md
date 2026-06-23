# 2026-06-23 — U3 Games hub child-button migration onto shared `HubChildButton`

> **Status:** `in-progress`

Ultracode fleet worker (U3). Behaviour-preserving deduplication: migrate the Games
hub's `_GameHubButton` + `GamesHubView.handle_select` onto the shared
`views.hub_children.HubChildButton` (the #1373 "first consolidation" primitive),
following the proven Community/Utility pattern. Drop the dropdown-legacy guards
(`__none__` / wrong-parent) that direct buttons never reach. Keep `custom_ids`,
button order, and the `discover`/`attach_back`/`_build_no_panel_embed` seams
byte-identical so persistent anchors keep routing.

Worker leaves this card RED — the coordinator flips/merges (Phase 2).

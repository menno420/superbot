# 2026-06-23 — U3 Games hub child-button migration onto shared `HubChildButton`

> **Status:** `complete` — coordinator Phase-2 verified (2026-06-23): diff scoped to
> `views/games/hub.py` + its tests only; `check_quality.py --full` + `check_architecture --mode strict`
> green on CI (sole red was the born-red gate); `check_consistency` flat at 36 (no new findings);
> custom_ids (`games:open:<sub>`, `games:back`) + button order preserved (tests pin it). −77 net lines
> in `hub.py` (`handle_select` + dropdown-legacy guards removed). Flipped + merged by the coordinator.

Ultracode fleet worker (U3). Behaviour-preserving deduplication: migrate the Games
hub's `_GameHubButton` + `GamesHubView.handle_select` onto the shared
`views.hub_children.HubChildButton` (the #1373 "first consolidation" primitive),
following the proven Community/Utility pattern. Drop the dropdown-legacy guards
(`__none__` / wrong-parent) that direct buttons never reach. Keep `custom_ids`,
button order, and the `discover`/`attach_back`/`_build_no_panel_embed` seams
byte-identical so persistent anchors keep routing.

Worker leaves this card RED — the coordinator flips/merges (Phase 2).

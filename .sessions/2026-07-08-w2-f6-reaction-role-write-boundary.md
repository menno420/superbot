# 2026-07-08 — W2-F6: reaction-role write-boundary invariant suite

> **Status:** `in-progress`

**Intent:** tests-only PR adding `tests/unit/invariants/test_reaction_role_write_boundary.py` — an AST write-boundary suite (mirroring `test_chain_write_boundary.py`) fencing the 5 reaction-role-overhaul tables (`role_menus`, `role_menu_options`, `reaction_role_message_modes`, `role_grants`, `role_menu_pickup_stats`) to the audited seams `reaction_role_service.py` / `role_grants_service.py`. Evidence + intent: `docs/analysis/server-management-audit-2026-07-08.md` finding F6.

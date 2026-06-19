# 2026-06-19 — Consistency-linter: triage the `edit_in_place` backlog (rule 1)

> **Status:** `in-progress`

## Arc (what I'm about to do)

Dispatch run, next consistency-linter slice ([plan](../planning/repo-consistency-linter-plan-2026-06-17.md)).
Rules 3 + 4 are at 0 but freshly so (graduation wants "a couple more clean sessions"), so this run
takes the standing **`edit_in_place` (rule 1) triage** — untriaged since PR1 (45 candidates), the
owner's headline UX inconsistency.

Plan for this slice:
1. **Rule improvement (root-cause, Q-0120):** the rule only counts a *direct* `.edit`/`edit_message`
   in the callback body, so it false-flags callbacks that re-render via the codebase's standard
   `self._rerender()` helper idiom (e.g. `TimeRolesPanel.reset_btn`). Teach `_edits_in_place` to also
   treat a callback that calls a **same-class in-place helper** (`self.<m>()` where `<m>`'s body edits
   in place) as editing in place.
2. **Triage the rest:** allowlist the genuinely-correct new-message callbacks (sub-flow pickers that
   re-render the parent on completion · shared multiplayer lobby/match messages · persistent-launcher
   ephemeral sub-flows · terminal/advisory report toasts · in-place-via-module-helper with an ephemeral
   fallback) with per-callback reasons.
3. **Fix the one contained genuine bug:** `roles/diagnostics_panel.DiagnosticsPanel.refresh_btn` chunks
   the member cache but only toasts — the panel's "Members Cached" field stays stale. Add a `_rerender`
   helper + re-render in place (mirrors `time_roles`/`xp_roles`).
4. **Leave the `views/ai/` cluster flagged (17):** they are the real bug — the owner's documented
   "AI panels stack ephemerals instead of updating in place" inconsistency, tracked by
   `ideas/ai-panel-inplace-navigation-2026-06-11.md`. The rule stays warn-only until that redesign
   ships; NOT allowlisted (allowlisting would mute the very inconsistency the rule exists to catch).

Expected: `edit_in_place` 45 → 17 (the 17 being exactly the AI-nav backlog), with one real fix + one
checker false-positive class removed.

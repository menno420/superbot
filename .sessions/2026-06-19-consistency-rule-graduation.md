# 2026-06-19 — Consistency-linter rule graduation (3 ELIGIBLE rules → error + CI)

> **Status:** `in-progress`

## Arc (what I'm about to do)

Routine dispatch, empty fire → next plan slice on the flagship consistency-linter lane
(current-state ▶ Next action option (a)). The three ELIGIBLE rules — `back_button`,
`panel_base_class`, `select_option_truncation` — have run clean (0 findings) across
#1056→#1062 (5–6 sessions), and `check_consistency.py --graduation` confirms all three
ELIGIBLE on the live tree. **Graduate them:** flip `Rule.severity` `"warning"`→`"error"`
and wire `python3.10 scripts/check_consistency.py --mode strict` into `code-quality.yml`
+ the `check_quality.py` local CI mirror, so a future regression that reintroduces a
front-truncated select / a direct-`discord.ui.View` panel / a back-button-less hub
**fails CI** instead of warning silently. `edit_in_place` stays warn-only (BLOCKED on the
AI-nav plan — its 17 `views/ai/` findings are the real bug the rule exists to catch).

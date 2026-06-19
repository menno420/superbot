# 2026-06-19 — Consistency-linter: reconcile `panel_base_class` with the arch ground truth

> **Status:** `in-progress`

## Arc (what I'm about to do)

Second slice of this dispatch run (after Lane A2 / #1056). Triage the consistency linter's
**`panel_base_class` rule (26 findings)** against the established arch ground truth, per Q-0120
(a tool verdict that fights documented ground truth is the *tool's* bug).

**Finding:** the arch `baseview_inheritance` checker (the ERROR-tracked ratchet) already
**path-exempts `views/ai/` and `views/games/`** ("specialized lifecycle ownership", documented in
`architecture_rules/canonical_helpers.yaml § base_view.exemptions`) and pins the remaining direct
`discord.ui.View` subclasses to an 8-entry frozenset in
`tests/unit/views/test_view_base_class_conformance.py`. The consistency `panel_base_class` rule
only exempts `views/rps`/`views/blackjack`/`views/base.py`, so it **re-flags 18 ai/games views the
ground truth has already decided are fine** + the 8 documented per-view exceptions.

**Fix (reconcile, do NOT migrate):**
- Add `views/ai/`, `views/games/` to the consistency rule's allowed paths (mirroring the arch
  config's documented lifecycle exemptions).
- Allowlist the 8 documented per-view exceptions in `consistency_exceptions.yml` with reasons
  citing the arch conformance frozenset.
- Expected: `panel_base_class` warn-only **26 → 0** (now agreeing with the arch ground truth —
  a graduation candidate, like rule 4 after Lane A2).

This is the deliberate alternative to the "panel_base_class double-win migration" the #1056 handoff
floated — investigation showed the obvious targets (the settings select-views) are documented
"migrate only with a concrete gain" exceptions, and the ai/games findings are arch-exempted, so the
correct move is reconciliation, not a low-value forced migration.

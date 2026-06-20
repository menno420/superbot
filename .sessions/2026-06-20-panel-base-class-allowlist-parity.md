# 2026-06-20 — cross-allowlist drift guard: `panel_base_class` yml ↔ arch conformance frozenset

> **Status:** `in-progress`

## Arc (what I'm about to do)

Dispatch routine, no work order — advancing the next plan slice. The previous run
(`2026-06-20-arch-ratchet-cog-layer.md`, #1163) extended the `baseview_inheritance` arch ratchet to
scan `cogs/` and flagged a Q-0089 idea: the `panel_base_class` consistency-linter allowlist
(`architecture_rules/consistency_exceptions.yml`) and the arch ratchet's
`_KNOWN_DIRECT_VIEW_SUBCLASSES` frozenset (`tests/unit/views/test_view_base_class_conformance.py`)
both hand-enumerate the **same** documented direct-`discord.ui.View` exceptions in two files — a
"two sources of truth" smell. When one is ratcheted down and the other isn't, they silently diverge.

Promoting that captured idea → build (Q-0172, self-initiated, flagged below). The two sets are
currently in **exact sync** (13 entries each, verified) — the right moment to pin them with a small
stdlib parity test so neither can drift from the other. Plus fix the stale "8-entry frozenset" prose
in the yml comment (it's been 13 since the cogs/ entries landed in #1163) — Q-0166 drift, fix on sight.

Contained / reversible / test-only — self-merge on green.

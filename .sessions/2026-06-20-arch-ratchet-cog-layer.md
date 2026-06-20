# 2026-06-20 — Extend the `baseview_inheritance` arch ratchet to the cog layer

> **Status:** `in-progress`

## What I'm about to do

The `baseview_inheritance` arch conformance ratchet (`scripts/check_architecture.py`
`check_baseview_inheritance` + `tests/unit/views/test_view_base_class_conformance.py`)
only scans `views/` — `cogs/` is a documented blind spot (the ratchet test comment
itself notes "cogs/ are not scanned by this ratchet, so it surfaced on the move").
The consistency linter's rule 3 (`panel_base_class`) was already extended to scan
`cogs/` in #1128 and triaged the 5 cog-layer direct-`discord.ui.View` classes, but the
**arch checker** — the load-bearing CI gate — still doesn't track them. So a new
cog-layer `discord.ui.View` panel would pass the arch checker silently.

This run extends the arch ratchet to `cogs/` too and pins the 5 existing cog-layer
direct-View classes into the conformance frozenset with the reasons already documented
in the consistency allowlist, closing the blind spot: a future cog-layer direct-View
class now fails `test_view_base_class_conformance.py`.

Ungated, contained, self-merge-on-green.

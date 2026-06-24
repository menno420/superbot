# 2026-06-24 — Harden the help-nav attachment seam (forward-path regression pins)

> **Status:** `in-progress` — born-red card; flips to `complete` as the deliberate final step.

> **Run type:** `routine · dispatch`

## What I'm about to do
Continuation of the same dispatch fire that shipped PR #1430 (the help-nav attachment seam). #1430
landed and auto-merged cleanly. The seam has **6 render sites** that forward a hub's `help_nav_card`,
but #1430 only added a *behavioral* forward-path pin on **one** (the navigation back-button) — the two
**highest-traffic Help-discovery paths** (`HubChildButton` hub-child navigation, and the Help category
**select** dropdown) relied on the accessor but had **no test that fails if the forward is dropped**.
A refactor that removed `attachments=help_nav_attachments(...)` from either would pass CI silently.

This slice closes that coverage gap — **tests only, no production change**:
- `tests/unit/views/test_hub_children.py` — a card-bearing child view forwards `attachments=[card]`;
  a cardless child clears attachments (navigate-away).
- `tests/unit/help/test_help_category_view.py` — selecting a hub whose panel carries a card forwards
  `attachments=[card]` on the in-place edit.

Now the seam's three main user-facing nav flows (back-button #1430 · HubChildButton · category select)
are all behaviorally guarded. The two secondary render sites (admin `_open_via_help_hook` cross-nav,
typed `!help <cat>` send) stay covered by the accessor unit tests but aren't behaviorally pinned —
lower-traffic, noted for a future pass rather than force-tested here.

Self-initiated (Q-0172) — hardening the just-shipped seam; flagged on the run report. Full CI mirror
green; auto-merge on green.

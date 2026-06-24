# 2026-06-24 — Help-nav attachment seam (visual card-engine H3)

> **Status:** `in-progress` — born-red card; flips to `complete` as the deliberate final step.

> **Run type:** `routine · dispatch`

## What I'm about to do
Scheduled dispatch fire, no work order. Bugs blocked/gated for an unattended run (BUG-0019 #1 =
owner design fork · BUG-0009 remaining slices need BTD6 release-order data + plan-level work · the
two rootfix-backlog entries are both the same gated cases). Taking the **explicitly handed-off next
▶ H3 slice** from PR #1413: the **help-nav attachment seam** ([idea](../ideas/help-nav-attachment-seam-2026-06-24.md)).

The inconsistency: hubs opened by their **direct command** render their showpiece image card (XP hub
via `!xpmenu`, #1413), but the **same** hub reached *through Help / hub navigation* shows a plain
embed — `build_help_menu_view` is embed-only across the codebase. As more features become image
cards, the showpiece is invisible on exactly the discovery path the consolidation audit invested in.

Design (chosen to be **non-viral + backward-compatible**, no 47-cog signature churn): the **view
object carries its own card** via a duck-typed `view.help_nav_card` attribute. A `build_help_menu_view`
hook with a card sets it on the view it returns; the central help-nav **render** sites forward it via
the `file=` / `attachments=` support that already exists (`safe_edit` already supports `attachments`,
built for exactly this PIL-card-on-one-anchor use). A view without the attribute (the default — every
embed-only hub) yields `None` → unchanged embed-only behaviour, so it rolls out hub-by-hub and any
render site I don't touch keeps working.

- New accessor `views/navigation.py:help_nav_card(view) -> discord.File | None`.
- Forward at the central render sites: `cogs/help_cog.py` (typed `!help <cat>` prefix + slash),
  `cogs/help/panels.py` (Help category select), `views/navigation.py` (back-button + hub-opener
  `safe_edit`), `views/hub_children.py` (`HubChildButton`), `cogs/admin_cog.py` (`_open_via_help_hook`).
- First real consumer: `XpCog.build_help_menu_view` sets `view.help_nav_card` from the rank card the
  `_XpHubView.build_response()` already produces — so the XP hub shows its card through Help too.
- Regression tests for the accessor + the migrated hook + the forward path.

Idea→ship is self-initiated (Q-0172) — flagged on the run-report ⚑ Self-initiated line. Full CI mirror
green; auto-merge on green. Aiming for a second slice (more card-bearing hubs) if room remains.

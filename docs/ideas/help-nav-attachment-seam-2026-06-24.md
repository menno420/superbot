# Help-nav attachment seam — let hub panels carry their image card through Help

> **Status:** `ideas`. Not a plan, not approval. Source code + binding contracts win.
> **Subsystem:** none

## The inconsistency

The visual card engine (H3) is rolling showpiece **image cards** onto bot features:
profile (`/myprofile`), rank (`!rank`), the XP hub (`!xpmenu`, PR #1413), the leaderboard
(`!leaderboard`), etc. Each renders a themed PNG with a clean embed fallback.

But every hub also has a **second entry path**: the `build_help_menu_view` hook, reached
from the Help tree and the universal hub-child navigation. That seam is **embed-only by
contract across the whole codebase** — every consumer does:

```python
embed, view = await cog.build_help_menu_view(interaction)
await interaction.response.edit_message(embed=embed, view=view)   # no attachment
```

So the *same* hub shows its card when opened by its direct command, but a **plain embed**
when reached through Help. As more features become image cards, this split widens: the
showpiece is invisible on exactly the discovery path (Help) the consolidation/discoverability
audit just invested in.

## The idea

A single **help-nav attachment seam**: let `build_help_menu_view` optionally return an
attachment alongside the embed+view (e.g. a `(embed, view, file)` triple, or an optional
third element / small result object), and teach the ~10 hub-rebuild call sites to forward it
with `attachments=[file] if file else []` (the same grammar `_RankSelect` / `_XpHubView`
already use). Known call sites (from `grep build_help_menu_view`):

- `views/navigation.py` (`attach_standard_nav` / hub rebuild)
- `views/hub_children.py` (`HubChildButton`)
- `views/community/hub.py`, `views/games/hub.py`, `views/server_management/hub.py`
- `cogs/admin_cog.py` `_open_child`, `cogs/help/route.py`
- the slash mirrors that reuse the hook (`settings_cog`, `economy_cog`, `moderation_cog`,
  `utility_cog`, …) — these `ctx.send`/`response.send_message` and *can* carry a file.

Backward-compatible: a hook that returns no attachment (the default) behaves exactly as today,
so it can roll out hub-by-hub.

## Why it's worth doing

- Closes the "card via the command, plain embed via Help" inconsistency **at the root** rather
  than per-feature.
- Directly amplifies the H3 work and the discoverability audit (the card shows where users
  actually browse).
- Bounded and mechanical once the seam is designed; the toggle/fallback grammar already exists.

## Caveats / why not built in #1413

Cross-cutting (~10 call sites, several of them governance-rechecked navigation seams), so it is
its own slice — out of scope for the single-surface `!xpmenu` migration. Needs a small design
decision (triple vs. result object) and a per-site audit that the edit-in-place paths can
actually attach a file (some `edit_message` paths can; a few may need `attachments=`). A good
next H3 slice once an agent wants to make the cards universal.

*(Captured 2026-06-24, dispatch run, as the Q-0089 session idea from the `!xpmenu` H3 slice — PR #1413.)*

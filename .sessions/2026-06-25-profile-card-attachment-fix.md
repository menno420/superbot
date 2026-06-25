# 2026-06-25 — Profile hero-card attachment round-trip fix

> **Status:** `in-progress` — born-red card (Q-0133). Flip to `complete` as the final step.

> **Run type:** `routine · dispatch` — scheduled dispatch fire, no work order. Took the next
> bugs-first slice spotted during orientation (Q-0166 drift/bug-on-sight).

**Branch:** `claude/funny-franklin-hu26rl` (off `main` @ #1462).

## What I'm about to do (intentions)

Fix a real, paired UX bug on the **`/myprofile` H1 hero-card image** navigation, found while
auditing the visual card-engine H3 adoption tail:

- **`views/profile/profile_view.py` — `manage` ("⚙️ Manage settings")** does
  `edit_message(embed=editor.build_embed(), view=editor)` with **no `attachments`**, so Discord
  retains the profile hero-card image: it lingers as a stray image under the (image-less) settings
  editor.
- **`views/profile/editor.py` — `back_to_card` ("◀ Back to card")** navigates back with
  `build_profile_embed` (a plain embed, no `set_image`) and **no re-attach**, so the round-trip
  loses the hero card — the returned panel shows the embed without its designed image (and any
  stray attachment from the step above dangles).

Both transitions must manage `attachments` explicitly, matching the canonical pattern already used
by `ProfileHomeView.refresh` and every other image-card hub (mining `character_hub`/`gear_panel`,
`role_menu_view`): re-render + re-attach when there is a card, pass `attachments=[]` to clear it.
The bug is isolated to the profile views (the other hubs already do it right).

Plan: fix both transitions, add tests pinning the attachment behaviour on each, record the bug in
`docs/health/bug-book.md`. CI mirror green + arch 0 before flipping the card.

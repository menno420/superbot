# 2026-06-25 — XP hub: clear stranded rank card on Configure (BUG-0025 third instance)

> **Status:** `in-progress` — born-red card (Q-0133). Flip to `complete` as the final step.

> **Run type:** `routine · dispatch` — same dispatch fire as PR #1463. Follow-up: a bugs-first root
> sweep of BUG-0025 found a third instance of the attachment-stranding class outside the profile
> views, but the merge of #1463 (profile-only) raced ahead of the fix push, so it ships separately.

**Branch:** `claude/xp-config-card-strand-fix` (off `main` @ #1463 merge, `ceebc876`).

## What I'm about to do (intentions)

`views/xp/main_panel.py` — `_XpHubView.btn_config` ("⚙️ Configure") opens the image-less
`XpConfigView` from the `!xpmenu` rank-card hub with `edit_message(...)` and **no `attachments`**, so
Discord keeps the rank card attached and it lingers as a stray image under the config panel — the
exact same class as BUG-0025's profile sites (which shipped in #1463). Fix: pass `attachments=[]` to
clear it, matching the stat toggles in `_switch_stat` and the profile `manage` fix.

Already done on the branch (carried from the #1463 work, pre-verified green): the `btn_config` fix,
a regression test (`test_xp_hub_panel.py::test_config_button_clears_the_rank_card_attachment`), and
the BUG-0025 bug-book entry broadened to all three call sites. CI mirror + arch were green on this
exact diff before the split. Re-verify green, then flip the card.

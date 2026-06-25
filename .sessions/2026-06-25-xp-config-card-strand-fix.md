# 2026-06-25 — XP hub: clear stranded rank card on Configure (BUG-0025 third instance)

> **Status:** `complete` — `btn_config` fixed, regression test green (9/9 in the XP hub suite),
> arch 0. BUG-0025 now root-level across all three call sites.

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

Done on the branch (carried from the #1463 work, pre-verified green): the `btn_config` fix, a
regression test (`test_xp_hub_panel.py::test_config_button_clears_the_rank_card_attachment`), and the
BUG-0025 bug-book entry broadened to all three call sites. Re-verified on this branch: 9/9 XP-hub
tests green, arch 0. The full CI mirror was green on this exact diff during the #1463 work.

## 📤 Run report

- **Run type:** `routine · dispatch`
- **PR:** #1464 — fix(xp): clear the stranded rank card when opening the XP Configure panel (BUG-0025)
- **Class:** fix (contained, reversible, test-covered) → self-merge on green (Q-0113)
- **⚑ Self-initiated:** none — the third instance was surfaced by a bugs-first root sweep (CLAUDE.md
  §6) of an already-dispatched bug fix, not an invented feature.
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none (merge auto-deploys)

## Note on the split

This and #1463 are one logical fix (BUG-0025, three call sites) that the auto-merge race split into
two PRs: #1463 merged at the profile-only commit while the XP fix's push was still in flight. No work
was lost — the XP fix is fully tested and shipping here. **Workflow lesson for the next run:** when a
bugs-first sweep is likely to find sibling instances, hold the born-red card until the *whole* root
fix is staged, or accept the split up front — don't push the complete-card flip before the sweep
finishes, because auto-merge fires the instant Code Quality is green. (The session-ender idea + the
previous-session review for this dispatch run live in the #1463 card,
`.sessions/2026-06-25-profile-card-attachment-fix.md`, to avoid duplication.)

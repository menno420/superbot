# 2026-06-30 — Reaction-roles RSVP roster ("Who's in?")

> **Status:** `complete` — ready to merge (Q-0133). Run type: manual · owner-directed.
> Full CI mirror green (**13226 passed**, 48 skipped; black/isort/ruff + mypy clean; arch strict 0
> new). PR #1571.

**Branch:** `claude/reaction-roles-counter-bgxnyd` (restarted from `main` @ #1570 merge — the prior PR
for this branch already merged, so this is a fresh change).

## What I'm about to do (intentions)

Follow-on to the live sign-up counter (#1570): the owner approved the **RSVP roster** idea I flagged —
after "how many" the organiser's next question is "**who**". Because every menu option is a real role,
the roster is a free `role.members` read (the same primitive the counter uses) — no new storage.

## What shipped

A read-only **👥 Who's in?** roster on counted menus:

1. **`views/roles/role_menu_counter.py`** — `build_roster_embed(menu, options, guild)`: one embed field
   per option (`label · <holder count>`) listing the members who currently hold it, sorted by display
   name; `_join_members` joins mentions and truncates a busy option to fit Discord's 1024-char field
   cap with a "…and N more" tail; a deleted-role option is skipped, an empty one reads "—". Pulled the
   `theme`/`resources` it needs in at module level (no new layer crossing — views may import
   utils/core).
2. **`views/roles/role_menu_view.py`** — a persistent **`_RosterButton`** (`role_menu:{menu_id}:roster`,
   primary style) added in `RoleMenuView.__init__` **only when `show_counts` is on and the view has
   component room** (`len(self.children) < 25` — a full 25-role button menu has none; RSVPs are small,
   so it never bites). Its callback (`_handle_roster`) reads the menu's immutable config off the view +
   live holders off the guild and posts the roster **ephemerally** (visible only to the clicker). It's
   in `__init__`, so the boot re-attach rebuilds it too → clicks survive restart.
3. **Tests** — +12: roster embed lists holders / skips deleted roles / "—" empty / no-live-roles
   description; `_join_members` truncation + empty; the button is present only when counts on + budget
   allows (incl. the 25-role-menu skip); `_handle_roster` sends an ephemeral embed.

**Privacy:** listing current holders of a *self-assigned, opt-in* role exposes nothing private — role
membership is already visible in Discord (member list / role mention). Distinct from the per-user
*pickup history* the overhaul plan keeps private (§9). Read-only; no DB writes.

## Why this is contained / safe

Additive, gated on the existing opt-in `show_counts` (every non-counted menu is untouched). No
migration, no new commands, no external surface, no storage — the roster is a pure live read of
`role.members`. The button degrades gracefully (skipped when the component budget is full). Arch
strict: 0 new violations; no import cycle (counter→view stays lazy; the new counter→core/utils imports
are downward, allowed).

## Context delta

- **Discovered:** the component-budget cap (25/view) is the only real constraint — a 25-role *button*
  menu can't fit a 26th component, so the roster button is conditional. Verified with a test rather
  than assuming RSVPs stay small. The persistent-view re-attach path (`reattach_role_menus`) rebuilds
  `RoleMenuView` from the menu row, which carries `show_counts`, so the roster button is restored on
  boot for free — no extra wiring.
- **Decisions made alone (reversible):** ephemeral roster (not a public reply — avoids spam on a busy
  event and keeps the menu message clean); mentions over plain names (clickable, never ping in an
  embed); sorted by display name (stable, scannable); gate on `show_counts` (scopes it to RSVP-style
  menus, not every colour/pronoun menu).
- **🛠 Friction → guard:** none new — the existing `RoleMenuView` persistence test pattern + the new
  budget test cover the regression surface. (The migration-collision class that bit #1570 is a
  *workflow* gap, captured in the Q-0102 note below, not a code guard for this PR.)

## 💡 Session idea (Q-0089)

**Per-option RSVP capacity (cap + waitlist).** With the live counter + roster in place, the natural
next RSVP primitive is a **per-option max** — "Going (cap 20)". Once an option is full, further clicks
either bounce with "this option is full" or drop into a paired **Waitlist** role that auto-promotes
when a slot frees (a holder un-signs). Carl-bot has a coarse `rr maxroles` (cap total holders of a
role); ours could be friendlier — surfaced in the builder beside the Limit field, enforced in the
audited `toggle_role`/`apply_selection` seam (count holders before adding). Genuinely useful for
limited-slot events (the exact "15K team" use case that started this). Recorded here per Q-0089.

## ⟲ Previous-session review (Q-0102)

Predecessor is **#1570 (the live sign-up counter)** — my own prior PR this session chain. **Did well:**
the feature was opt-in + default-off so it couldn't regress existing menus, the semantics call
(current-holders vs cumulative) was reasoned from the use case, and the debounce kept it
rate-limit-safe. **What it missed / system note:** it **collided on migration number 102** — PR #1569
merged its own `102_ai_answer_presets.sql` to `main` while #1570 was open, so when `main` merged in,
two `102_*` files existed and three migration tests went red on the merge commit (caught + fixed by
renumber → 103). The migration number is chosen at author time as "highest-on-my-branch + 1", which
**races under parallel PRs** — a known class (`docs/ideas/migration-number-collision-guard-2026-06-22.md`),
and #1570 was a live instance of it. **Improvement:** the pre-pr / born-red step (or a pre-push hook)
should `git fetch origin main` and flag when the branch's new migration number already exists on
`main` or in an open PR — catching the collision *before* the PR opens, instead of after a full
merge-into-branch CI cycle. That turns a ~10-minute red-CI round-trip into an instant local warning.
(Captured as the workflow takeaway; this PR has no migration, so it wasn't blocked — the note is for
the next migration-bearing session.)

## 📤 Run report

- **Did:** shipped the **👥 Who's in?** RSVP roster on counted role menus (ephemeral per-option member
  list, gated on the counter's opt-in, read-only). · **Outcome:** shipped
- **Shipped:** PR #1571 — feat(roles): RSVP roster — "Who's in?" on counted menus (auto-merge on green CI)
- **Run type:** `manual · owner-directed`
- **Class:** feature/deepening (additive, opt-in, read-only, test-covered)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none — merge auto-deploys; no migration/data step
- **⚑ Self-initiated:** no — owner-directed ("Yes that's a good idea" → build the roster I'd flagged)
- **↪ Next:** the **per-option RSVP capacity / waitlist** idea above; or counter polish (counts on the
  button labels); or continue the S1 completion-first punch-lists.

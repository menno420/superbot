# 2026-06-30 — Role-menu builder live-preview fix (ephemeral re-render)

> **Status:** `complete` — ready to merge (Q-0133). Run type: manual · owner-directed (bug report
> from a live screen recording). Full CI mirror green (**13467 passed**, 48 skipped; lint/mypy clean;
> arch strict 0 new). PR #1608.

**Branch:** `claude/reaction-roles-counter-bgxnyd` (restarted from `main` @ #1606 — prior PRs #1570/#1571
merged; this is a fresh change).

## What I'm about to do (intentions)

Owner sent a 55s screen recording of the reaction-roles builder and reported: Style toggle "works but
the panel doesn't update", the chosen role pack isn't shown, the posted channel isn't shown. Reviewed
all 44 sampled frames: the changes **all take effect** (posts to `#reaction-roles` with the 3 RSVP
buttons) but the **preview panel never re-renders**.

## What shipped

**Root cause (one bug → all three symptoms):** the reaction-roles hub is **ephemeral**, and
`RoleMenuBuilder._rerender()` refreshed via `self.message.edit()` — which **silently no-ops on an
ephemeral message** (only the interaction/webhook token can edit one). Draft state
(`style`/`role_ids`/`channel`/`show_counts`) applied and posted correctly, but the panel edit failed →
the preview froze on its first render.

Fix (all in `views/roles/role_menu_builder.py` + one line in `views/roles/reaction_panel.py`):
1. `RoleMenuBuilder` stores `self._panel_interaction` (the token owning the ephemeral panel); `_rerender()`
   + a new `_show_parent()` route through the shipped `interaction_helpers.safe_edit(...)`
   (`response.edit_message` / `followup.edit_message`), with a `Message.edit` fallback for non-ephemeral.
2. The token is set at every panel-open (`new_btn` / `_open_editor` / `_duplicate_menu`) and refreshed by
   each direct panel interaction (Style/Counts toggles, Text/Limit modals). The seven sub-flow pickers
   (Roles/Colours/Packs/Channel/Template/Theme/Mode) already call `_rerender()`, so they were **fixed for
   free** once the choke point routes through the token.
3. `_open_editor`/`_duplicate_menu` now render the builder onto the interaction's own message (they too
   used `self.message.edit` → Edit/Duplicate would have failed to open on the ephemeral message).
4. Sibling `RoleMenuListView._rerender()` got the same one-liner + its token set in
   `reaction_panel.menus_btn` (the menu **list** went stale after delete/repost).
5. +3 re-render routing tests (routes through `safe_edit` with the token; falls back to `Message.edit`
   when there's no token or the token edit fails).

No behaviour change to what gets **posted** (that was already correct) — this only makes the **preview**
reflect the draft live. No migration, no new commands.

## Why this is contained / safe

Pure UI-refresh plumbing on an existing seam (`safe_edit` is the codebase's canonical ephemeral-safe
editor). The fallback preserves the old `Message.edit` path for any non-ephemeral caller. Merged onto
latest `main` (resolved a trivial import conflict with the Q-0212 `_can_manage` change). Arch strict 0
new. Needs a live re-test (owner is testing live) to confirm the preview now updates — the unit tests
prove the routing but can't exercise a real ephemeral edit.

## Context delta

- **Discovered:** the ephemeral-`Message.edit()` no-op is a **whole bug class** — this exact
  `self.message = interaction.message` + `self.message.edit()` pattern is in `RoleMenuBuilder`,
  `RoleMenuListView`, **and** `ReactionRolesPanel._rerender` (the emoji panel — same latent staleness,
  left for a follow-up since it wasn't in the report). The builder shipped this way in PR #1219 and it
  survived every session since because the tests only asserted `build_embed()` **output** (pure), never
  the interaction plumbing. The codebase already had the right tool (`safe_edit`) — the builder just
  didn't use it.
- **Decisions made alone (reversible):** fixed the builder + its manager (the reported surface + its
  direct sibling) but **scoped out** `ReactionRolesPanel._rerender` and other views to keep the PR
  verifiable on the reported bug (noted as a follow-up). Chose a stored-token + `safe_edit` choke point
  over rewriting every handler to `interaction.response.edit_message` (one change fixes all sub-flows).
- **🛠 Friction → guard:** the recurring failure is "ephemeral panel refreshed via `Message.edit()`".
  Cheapest enforcing guard = a checker that flags `self.message.edit(` inside `views/` (suggesting
  `safe_edit`) — captured as the session idea below (test/checker tier → free to ship; I didn't add it
  this PR to keep scope on the fix).

## 💡 Session idea (Q-0089)

**`check_architecture` (or a ruff/AST checker) flagging `self.message.edit(` in `views/`** — with a
one-line "use `interaction_helpers.safe_edit` (ephemeral messages can't be `Message.edit()`'d)" hint and
an allowlist for the genuinely-non-ephemeral panels. This whole bug class (builder + manager +
`ReactionRolesPanel` + likely others) is invisible to tests because the pure `build_embed` still returns
the right embed; the failure is only in *delivery*. A grep-simple static guard would have caught it at
author time and would catch the next one. (Friction→guard, Q-0194; checker tier = free to ship.)

## ⟲ Previous-session review (Q-0102)

Predecessor in this chain is **#1571 (the RSVP roster)** — my own prior PR. **Did well:** clean,
opt-in, well-tested feature. **Missed (and the lesson this session drove home):** #1570/#1571 (and the
📊 Counts toggle they added to the builder) were **never live-tested before shipping** — and this very
builder had a latent preview-freeze bug that a 30-second live walk would have surfaced immediately. The
unit tests were all *pure* (`build_embed`/`collect_counts` output), so they were green while the
in-Discord experience was broken. **System improvement:** for interaction-heavy UI, (a) a test that
pins the *refresh path* uses the interaction token (the shape I added here) should be the standard, not
just output tests, and (b) the `/verify-bot` walk should explicitly include "toggle a field → does the
panel visibly update?". The pure-test blind spot is exactly what the Q-0089 static guard would backstop.

## 📤 Run report

- **Did:** root-caused + fixed the reaction-roles builder preview never updating (ephemeral
  `Message.edit()` no-op) by routing every re-render through the interaction token (`safe_edit`).
  · **Outcome:** shipped (pending live re-test)
- **Shipped:** PR #1608 — fix(roles): role-menu builder preview never updated (ephemeral panel)
- **Run type:** `manual · owner-directed` (bug report from a screen recording)
- **Class:** bug fix (root-cause; contained, reversible, test-covered)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** a quick **live re-test** of the New-Menu flow (toggle Style, add a pack,
  pick a channel → the preview should now update each time). Merge auto-deploys; no data step.
- **⚑ Self-initiated:** no — owner-directed (the screen recording + explicit bug report).
- **↪ Next:** apply the same fix to `ReactionRolesPanel._rerender` (emoji panel) + audit other `views/`
  for the `self.message.edit` pattern (the Q-0089 guard would enumerate them); the per-option RSVP
  capacity/waitlist idea from #1571; counter polish (counts on button labels).

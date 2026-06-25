# 2026-06-25 — Profile hero-card attachment round-trip fix

> **Status:** `complete` — both transitions fixed, 3 regression tests green, full CI mirror green
> (12528 passed) + arch 0. BUG-0025 recorded FIXED (root).

> **Run type:** `routine · dispatch` — scheduled dispatch fire, no work order. Took the next
> bugs-first slice spotted during orientation (Q-0166 drift/bug-on-sight).

**Branch:** `claude/funny-franklin-hu26rl` (off `main` @ #1462). **PR #1463.**

## What shipped (BUG-0025)

Fixed a real, paired UX bug on the **`/myprofile` H1 hero-card image** — the card ↔ self-service
editor round-trip mishandled the rendered image attachment:

- **`views/profile/profile_view.py` — `manage` ("⚙️ Manage settings")** did
  `edit_message(embed=editor.build_embed(), view=editor)` with **no `attachments`**. Discord retains
  the prior attachment when the arg is omitted, so the profile hero card lingered as a **stray image**
  under the (image-less) settings editor. → now passes `attachments=[]` to clear it.
- **`views/profile/editor.py` — `back_to_card` ("◀ Back to card")** rebuilt the panel from
  `build_profile_embed` (plain embed, no `set_image`) with **no re-attach**, **losing the hero card**
  on the return leg. → now re-renders the full card via `build_profile_card` and re-attaches the file
  (`attachments=[file]`, or `[]` on a Pillow-less host), mirroring `ProfileHomeView.refresh`.

**Root cause:** these were the only two `edit_message` calls in the profile views that omitted
`attachments`. Every other image-card hub (`refresh`, mining `character_hub`/`gear_panel`,
`role_menu_view`) already passes it explicitly — so the bug was isolated to the profile editor
navigation; no wider sweep needed (I checked the other hubs, they're correct).

**Stays-fixed guard (same PR):** 3 regression tests asserting the `attachments=` payload on each
transition (all fail against pre-fix behaviour):
- `test_profile_card.py::test_manage_clears_the_hero_card_when_opening_the_editor`
- `test_profile_editor.py::test_back_to_card_rerenders_and_reattaches_the_hero_card`
- `test_profile_editor.py::test_back_to_card_clears_attachments_when_renderer_unavailable`

Docs: BUG-0025 entry (FIXED root) in `docs/health/bug-book.md`.

### ⚑ Flagged for maintainer / known limits

- **Not live-verified** (no Discord boot here): the fix follows the same `attachments=` contract the
  rest of the codebase already uses and is unit-pinned, so confidence is high, but a live click-through
  of `/myprofile` → Manage settings → Back to card would confirm the image now persists correctly.

## 💡 Session idea

**A `views`-layer lint: every `edit_message` whose embed carries a hero card must pass `attachments`
explicitly.** This bug class (omit `attachments` → Discord silently keeps/strands the old attachment)
is invisible to mypy and to the existing checks — it only shows live. A small AST check in
`scripts/check_architecture.py` (or a dedicated `check_attachment_hygiene.py`) could flag any
`interaction.response.edit_message(...)` / `message.edit(...)` in a view that omits `attachments`
when an image-card render helper is in scope. Disposable/unverified per Q-0105; would have caught
BUG-0025 statically. Captured here for a later slice (not built this run — wanted the fix landed
first).

## ⟲ Previous-session review

Previous run (#1460-band, the ticket AI one-click-confirm follow-up) did the right thing: it shipped
a clean event-seam confirm flow and, in its own review, flagged that the *prior* session made a
user-facing interaction-model decision unilaterally — a genuinely useful self-audit. What it (and the
whole recent burst of "ship the next feature") arguably missed is exactly what this run picked up:
the H1 visual-card showpiece had a visible navigation bug sitting un-noticed while newer cards were
being added. **System improvement:** the card-engine rollout has been additive-fast but light on
*navigation* regression coverage — the session idea above (an attachment-hygiene lint) is the
structural fix so the next card hub can't reintroduce this class. The workflow itself (born-red card,
auto-merge, context-map-on-edit) worked smoothly.

## ⟳ Doc audit (Q-0104)

- BUG-0025 recorded in the bug book with its stays-fixed guard named (root fix, not deferred).
- No new owner decision; no new doc file → no `check_docs` reachability change.
- current-state recently-shipped left untouched (merged-PRs-only; the next session reconciles #1463).
- Claim file `claude__funny-franklin-hu26rl.md` deleted at close (below).

## 📤 Run report

- **Run type:** `routine · dispatch`
- **PR:** #1463 — fix(profile): preserve the `/myprofile` hero-card image across editor navigation
- **Class:** fix (contained, reversible, test-covered) → self-merge on green (Q-0113)
- **⚑ Self-initiated:** none beyond picking the slice — a bug-on-sight fix (Q-0166), no invented
  feature, no idea→plan promotion this run.
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none (merge auto-deploys; the fix is live on next deploy)

## Context delta

The bug was found by auditing the visual card-engine H3 adoption tail in `S1-bot.md`. The "profile/
rank hubs are the next `help_nav_card` adopters" note there is **separate** from this fix — the
profile card is reached via `!myprofile`/`/myprofile` directly (no Help-hub nav entry), so it isn't
a `help_nav_card` adopter; this fix is about plain `attachments` hygiene on its own editor nav. Left
that S1 bullet as-is.

# 2026-06-10 — Help overlay editor UI (plan #674 → PR A #677 + PR B #679)

**Prompt:** "Continue from where you left off" (post-#672 resume). **PRs:**
#677 (PR A, editor — no migration) + #679 (PR B, Q-0059 Home builder —
migration 067; stacked on A, rebase+retarget on A's merge).

## Arc

Resume found main moved: the eval-support session (#673 checklist, #674
editor plan, #675 live-walk fixes) had run, the maintainer's walk started
(Tier 1.1 round-cash PASSED live), and the editor-UI plan was "ready to
execute, no gates". Executed it end-to-end per "approved plan = execute":
PR A then PR B, both live-verified.

## Shipped

1. **PR A (#677)** — `views/help/editor.py`: home (counts/orphans/reset-all
   w/ confirm) → paginated catalogue picker (Q-0058 labels, 🙈 markers) →
   entity editor (hide/unhide → inherit semantics, rename/re-describe
   modals, per-field resets). One audited `help_overlay_mutation` call per
   action; `_EditorViewBase` = owner-lock + admin re-check per callback.
   Entry points: staff-hub `✏️ Help editor` button + "Help appearance"
   `DomainPanelSpec` (new `help.settings.configure` capability; domain-panel
   pin {cleanup} → {cleanup, help}; hub `_BUTTON_IDS` += help_editor).
2. **PR B (#679)** — migration 067 ('home' kind + bounded home columns,
   064's pre-planned widening); `set_home_message` (same UNSET/value/None
   contract; all-None deletes); `HomeMessage` + `GuildHelpOverlay.home` +
   `home_embed_frame` (ONE composer for live render + preview; mention
   suppression); `build_categories_overview_embed` consumes
   `projection.overlay.home` (no signature change; default byte-identical,
   pinned); `HomeMessageBuilderView` (stage → mandatory preview → save;
   any edit re-locks Save; named-color select; reset-to-default).
3. Eval checklist §4.5 rewritten: the editor walk replaces "nothing to
   click-edit yet"; help audit Phase 5 + the plan + queue docs stamped.

**Verification:** CI mirror 8,912+ green both PRs; arch 0 errors (no new
warnings); migration 067 applied live (version row + columns + CHECKs);
live round-trips through the views' own callbacks (hide/rename → live
Help agrees → reset byte-identical · stage → preview unlocks Save → save →
custom frame w/ "@everyone" suppressed → reset).

## Context delta

- **Needed but not pointed to:** nothing — the #674 plan was genuinely
  turn-key (its "what already exists" table + decision envelope covered
  every seam; the first plan I executed with zero seam-discovery cost).
  The plan-first → execute-next-session pipeline worked exactly as
  designed.
- **Discovered by hand:** (a) ran bare `black .` and reformatted 265
  files incl. tests/ — the exact CLAUDE.md trap; reverted via
  git-checkout list. The rule held, I slipped — `check_quality.py
  --check-only` then format ONLY the named files. (b) `test_no_raw_defer`
  invariant exists (raw `interaction.response.defer()` forbidden in
  views — use `safe_defer`). (c) extending a read model breaks
  mock-pinned consumers in *non-obvious* ways: the un-mocked new read
  (`get_home_row`) raising in tests silently rerouted two overlay tests
  through the fault path — one became a no-op test (asserted
  invalidation of a cache that never populated). Fixed both; the class
  ("a test can encode a bug") is in the journal already.
- **Decisions made alone:** unhide = reset-to-inherit (None) not
  explicit False (store-only-deviations); builder on `_EditorViewBase`
  (BaseView) instead of raw `discord.ui.View` (the arch rule — no new
  warning); preview renders builder embed + exact frame side-by-side in
  one message (two embeds) instead of a separate ephemeral; named colors
  only (plan v1 said so).
- **Flagged for maintainer:** PR B is stacked on PR A — merge A first;
  I'll rebase/retarget B on the merge webhook. The editor is
  sandbox-verified at the service/view layer; the checklist §4.5 walk is
  the human click-through.

## Open after this session

Batch 9 RS05/RS10 (the last implementation-ready queue item) · Help audit
Phase 4 records (Q-0057 rider) · setup PR4 planning session · AI §7.5
(post-prod-check) · the maintainer's eval walk (checklist now includes
the editor).

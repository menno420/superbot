# Plan — AI panels → in-place navigation (+ settings centralization)

> **Status:** `plan` — executable plan promoted from
> [`ideas/ai-panel-inplace-navigation-2026-06-11.md`](../ideas/ai-panel-inplace-navigation-2026-06-11.md)
> (owner-requested live, 2026-06-11; roadmap AI § Later). Promoted 2026-06-19 under the open idea→plan
> gate (Q-0172) — flagged self-initiated on that run's report. Source + the binding contracts win.
>
> **Why now:** this redesign is the *only* blocker for graduating the consistency linter's
> **`edit_in_place` rule** — its 17 remaining warn-only findings are *exactly* the `views/ai/` family
> (the rest of the tree is triaged to 0). Shipping this plan both fixes the owner's headline UX
> complaint and lets rule 1 flip to `error` + wire into `code-quality.yml`.

## The two owner asks (verbatim, 2026-06-11)

1. *"the AI settings and panels create way too many ephemeral panels etc, this should be changed so it
   matches the rest of the bot and updates in place"*
2. *"these settings are a little confusing, and they should probably be more centralized as well,
   because you have to go in different panels to edit certain AI settings"*

## Source-confirmed scope (re-verified 2026-06-19)

`disbot/views/ai/` is **18 view classes across 4 sub-trees**, all extending raw `discord.ui.View`
**except** `AIPanelView` (a `PersistentView`):

- **panel.py** — `AIPanelView` (the anchor; `policy_btn`/`behavior_btn`/`tools_btn` each `send_message`
  a new ephemeral chooser → **3 `edit_in_place` findings**).
- **behavior/** — `BehaviorChooserView` (**5 findings**: channel/category/preview/matrix/advanced) +
  `scope_picker.py` (`BehaviorChannelSelectView`, `BehaviorCategorySelectView`) + `preset_picker.py`.
- **policy/** — `PolicyChooserView` (**5 findings**: channel/category/role/preview/list) +
  `channel_view`/`category_view`/`role_view`/`list_view`/`preview_view`.
- **tools/** — `ToolsChooserView` (**4 findings**: guild/channel/category/preview) + `scope_view.py`
  (`GuildToolsProfileView`, `ChannelToolsSelectView`, `CategoryToolsSelectView`) + `preview_view.py`.
- **routing/** — `RoutingMatrixSelectView` (read-only dry-run, reached from the behavior chooser).
- **support_report.py** — standalone.

The blanket `views/ai/` exemption lives in `architecture_rules/canonical_helpers.yaml §
base_view.exemptions` ("chained select menus require fine-grained interaction lifecycle control beyond
what BaseView provides"); both `check_architecture` and the `panel_base_class` consistency rule honor it
(reconciled in #1057), so this debt is **ratchet-invisible** until the exemption is narrowed.

## The target pattern ("matches the rest of the bot")

The post-RS10 doctrine (settings hub, server-management hub, mining hub) and V-02 navigation doctrine:
**one anchor message; button/select callbacks `interaction.response.edit_message(...)` the same message
to the next page; `BaseView`/`HubView` owns timeout/denial/error lifecycle; ephemeral messages reserved
for confirmations/errors, not navigation.** The Settings hub's channel/enum/role edit flows already
re-render the same message with the next select — the chained-select concern (the stated exemption
reason) is solved there, so it is solvable here.

## Build order (2–3 PRs)

### PR 1 — foundation + the AI anchor (clears panel.py's 3 findings)

- Establish the in-place page model on `AIPanelView`: a `HubView`-style anchor whose
  `policy_btn`/`behavior_btn`/`tools_btn` **`edit_message`** the anchor to render the policy / behavior /
  tools chooser as a *page* of the same message (with a back affordance to the AI home page), instead of
  `send_message`-ing a new ephemeral.
- Keep `AIPanelView` persistent (custom_ids) — the page swap is on the same persistent anchor.
- Re-check `docs/ai-config-ownership.md` UI-surface pinning (doc-test-pinned) **before** moving panels;
  update the pinned surface list in the same PR.
- **Deliverable:** the 3 `panel.py` `edit_in_place` findings clear; the chooser entry points navigate
  in place.

### PR 2 — chooser sub-trees in place (clears the 14 chooser findings)

- Migrate `BehaviorChooserView` / `PolicyChooserView` / `ToolsChooserView` and their scope pickers
  (`scope_picker`, `policy/*_view`, `tools/scope_view`, the preview/list views, `routing/matrix`) onto
  `BaseView`/`HubView` with in-place page swaps: the chooser → scope picker → confirmation are pages of
  the one anchor, re-rendered via `edit_message`. Reserve ephemerals for confirmations/errors only.
- Reuse the existing windowed-select helper (`views/paginated_select.attach_windowed_select`) for any
  scope select that can exceed 25 options (channels/categories/roles) — do **not** reintroduce a
  front-truncation (rule 4 guards this).
- **Deliverable:** all 17 `edit_in_place` findings clear → **rule 1 becomes a graduation candidate.**

### PR 3 — narrow the exemption + centralize (the second owner ask)

- **Narrow/delete** the blanket `views/ai/` exemption in `canonical_helpers.yaml` per migrated class;
  ratchet the conformance frozenset down as pages land (so the family is visible to the ratchet again,
  matching every other direct-`View` entry). Drop the mirrored `views/ai/` path exemption from the
  consistency `panel_base_class` rule (`_BASE_CLASS_ALLOWED_PATHS`) once the classes are `BaseView`.
- **Centralize the settings surface (ask #2):** one AI hub page grouping settings by *task* ("make the
  bot reply here" = `ai_enabled` ∧ `ai_natural_language_enabled` ∧ channel mode ∧ min level as ONE
  guided flow) instead of seven sibling subpanels + a flat 10-key scalar editor. Make the required
  couplings visible (the `ai_enabled` ON / `ai_natural_language_enabled` OFF silent-bot trap that opened
  the 2026-06-11 session is the canonical symptom). Reconcile with the Settings-hub AI group so there is
  one front door (`!aimenu` and `!settings` reach AI config by different routes today).
- **Graduate `edit_in_place`:** flip to `error` + wire into `code-quality.yml` (rule 1's last blocker
  cleared).

## Risk / sequencing notes

- **Substantial UI migration** (18 view classes, real Discord interaction lifecycle) — each PR is
  `needs-hermes-review` (Q-0117), **not** a routine self-merge, and wants **live verification** in a
  guild (the interaction behavior is not fully offline-testable). This plan is written for a session
  with runtime context / the joint live-session cadence (Q-0086).
- Keep default behavior byte-identical where the page content is unchanged; the change is *navigation
  mechanism*, not policy/data.
- PRs 1+2 are the `edit_in_place` clear; PR 3 (centralization + graduation) can trail as its own slice
  if the band runs long (plans span 2–3 PRs).

## Verification (each PR)

- `python3.10 scripts/check_consistency.py --mode strict` — the migrated classes drop their
  `edit_in_place` (and, in PR 3, `panel_base_class`) findings; no new `select_option_truncation`.
- `python3.10 scripts/check_quality.py --full` green; `check_architecture --mode strict` exit 0.
- `docs/ai-config-ownership.md` UI-surface doc-test stays green (update the pinned list in lockstep).
- Live walk in a guild: `!aimenu` → policy → behavior → tools navigates **in place** (one anchor
  message), confirmations/errors are the only ephemerals.

## Routing

- Lane: AI tooling UX / views conformance (RS10's natural follow-on; V-02 navigation doctrine).
- Unblocks: consistency-linter rule 1 graduation
  ([linter plan](repo-consistency-linter-plan-2026-06-17.md)).
- Pairs with: the Help home / navigation plan (same doctrine).

# AI panels → in-place navigation + centralized settings (owner-requested, 2026-06-11)

> **Status:** `ideas` — **owner-requested direction, not yet planned/scheduled.**
> Captured mid live-testing session (Q-0086 joint session, 2026-06-11). Not a plan;
> promotion path is `docs/ideas/README.md` → a `docs/planning/` slice when picked up.
>
> **Routed (2026-06-12):** placed on `docs/roadmap.md` § AI at the **Later** horizon
> (UX debt, owner-requested). State: `captured → on the roadmap`. Next step when picked
> up = a `docs/planning/` slice (wants its own session with runtime context).
> **Subsystem:** ai — the views/ai/ panel family.

## What the owner said (live session, 2026-06-11)

> "the AI settings and panels create way too many ephemeral panels etc, this
> should be changed so it matches the rest of the bot and updates in place"

Context: he was walking the AI enablement flow (`!aimenu` → settings → policy →
why-no-response) and every navigation step stacked another ephemeral message in
the channel instead of the panel updating itself.

**Second finding, same walk (owner, after the first live reply):**

> "I think these settings are a little confusing, and they should probably be
> more centralized as well, because you have to go in different panels to edit
> certain AI settings"

Live evidence from the router trace: configuring AI for the first time took him
through **seven distinct panel surfaces in ~10 minutes** (`ai:settings` →
`ai:policy` → `ai:behavior` → `ai:diagnostics` → `ai:providers` → `ai:tools` →
`ai:routing`), plus the flat scalar "Edit a setting…" select (10 `ai_*` keys
with no grouping or guidance). The trap that opened this session — master
`ai_enabled` ON while `ai_natural_language_enabled` stayed OFF, bot silent —
is a direct symptom: the two switches that must *both* be on to get a reply
live in an undifferentiated flat list. (Denial trail in `ai_decision_audit`:
`guild_not_configured` → `ai_nl_disabled_for_guild` → `no_mention_required`.)

## Source-confirmed diagnosis (2026-06-11)

This is structural, not copy-level:

- **Every AI subview extends raw `discord.ui.View`**, not `BaseView`/`HubView`:
  `PolicyChooserView`, `PolicyListView`, `ChannelPolicySelectView`,
  `CategoryPolicySelectView`, `RolePolicySelectView`, `PreviewChannelSelectView`
  (and the behavior/tools pickers). Only the top-level `AIPanelView` is a
  `PersistentView`.
- **Navigation = new ephemeral send, not edit-in-place**: `ephemeral=True`
  sends per file — `views/ai/panel.py` ×9, `policy/role_view.py` ×7,
  `policy/chooser.py` ×7, `policy/channel_view.py` ×7,
  `policy/category_view.py` ×7, `tools/scope_view.py` ×6,
  `behavior/preset_picker.py` ×6, `behavior/chooser.py` ×6 (and more).
- **The debt is invisible to the ratchet**: `architecture_rules/canonical_helpers.yaml`
  carries a blanket `views/ai/` exemption ("chained select menus require
  fine-grained interaction lifecycle control beyond what BaseView provides"),
  so neither `check_architecture` nor
  `tests/unit/views/test_view_base_class_conformance.py` lists these views as
  debt — unlike every other direct-View entry, which is enumerated per class.

## What "matches the rest of the bot" means

The post-RS10 pattern the rest of the bot uses (settings hub, server-management
hub, mining hub, economy family): one anchor panel message; button/select
callbacks `interaction.response.edit_message(...)` the same message to the next
page; `BaseView`/`HubView` owns timeout/denial/error lifecycle; ephemeral
messages reserved for confirmations/errors, not navigation.

## Scope sketch (when promoted to a plan)

1. Migrate `views/ai/` family onto `HubView`/`BaseView` with in-place page
   swaps (panel → settings / policy / behavior / tools / routing as pages of
   one anchor, mirroring the Settings-hub navigation doctrine — V-02 in
   [`superbot-vision-2026-06-10.md`](./superbot-vision-2026-06-10.md)).
1b. **Centralize/structure the settings surface** (the second owner ask): one
   AI hub page that groups settings by *what the admin is trying to do*
   ("make the bot reply here" = enabled + natural_language + channel mode +
   min level as ONE guided flow), instead of seven sibling subpanels + a flat
   10-key scalar editor. Couplings the UI must make visible: `ai_enabled` ∧
   `ai_natural_language_enabled` (both required for replies); channel
   mode vs guild default; orchestration profile vs tools-enabled. Candidate
   shape: fold the scalar editor's keys into the relevant task pages and keep
   an "advanced" page for the rest. Should also reconcile with the Settings
   hub's AI group so there is one obvious front door (today `!aimenu` and
   `!settings` both reach AI config by different routes).
2. Chained select menus (the stated exemption reason) are solvable in-place:
   re-render the same message with the next select; the Settings hub's
   channel/enum/role edit flows already do this shape.
3. Narrow the `views/ai/` yaml exemption per remaining class (or delete it) so
   the ratchet sees the family again; conformance test entries ratchet down as
   pages migrate.
4. Re-check `docs/ai-config-ownership.md` UI-surface pinning (doc-test-pinned)
   before/while moving panels.

## Routing

- Lane: AI tooling UX / views conformance (RS10's natural follow-on).
- Pairs with: the Help home / navigation plan (same doctrine), V-02 panel
  navigation doctrine.
- Indexed in `docs/ideas/README.md`; session log
  `.sessions/2026-06-11-live-testing-q0086.md` carries the live context.

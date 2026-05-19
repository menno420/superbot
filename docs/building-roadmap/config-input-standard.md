# Config Input Standard

Status: Reference only
Runtime impact: None
Scope: Future config-mutation UIs — how every admin/settings input should be shaped so the same patterns work across subsystems

This document captures the input-collection standard for SuperBot's
config and settings UIs. It is **a reference, not a refactor plan** —
existing views are not in scope. New config surfaces and any future
view-layer regrouping should align with the principles here.

Related references:

- `command-integration-standard.md` — non-negotiable rules every command/panel must obey
- `hub-ui-standard.md` — hub/panel shape standard (where this input shape lives)
- `admin-powers-config-coverage.md` — pipeline ownership map (the back end that input forms call)
- `../settings-customization-roadmap.md`
- `../settings-customization-command-map.md`

---

## Why this doc exists

Today every settings/admin surface invents its own input shape:

- Some panels open a text modal and ask the operator to type a channel
  mention.
- Some panels use a 25-option dropdown of preset values.
- Some panels are buttons-only and don't expose the underlying value at
  all.
- Several panels write directly from the view callback to the DB or to
  ``guild_config`` — bypassing audit, validation, and cache
  invalidation.

The inconsistency is not a bug — each subsystem evolved independently —
but new config surfaces (the setup wizard, the per-guild flag manager
v2, Economy v2 settings, Moderation v2 thresholds) need a shared
shape. This doc captures that shape so the next round lands consistent
by construction.

---

## Core principles

1. **Guided input first; raw text only when nothing else fits.** Use
   visible buttons, selects, or paginated picks whenever the value space
   is small, enumerated, or referential. Raw text modals are a fallback,
   not a default.
2. **Views collect; pipelines mutate.** The view's job is to gather
   input, render a preview, and call the right pipeline. Validation,
   mutation, audit logging, event emission, and cache invalidation belong
   in the pipeline — never in the view callback. See
   `admin-powers-config-coverage.md` for the pipeline-ownership map.
3. **Show the current value before asking for the next one.** Every
   config surface displays the field's current value (or "not set") so
   the operator knows what they're changing from.
4. **Dangerous changes preview and confirm.** Destructive or
   wide-blast-radius changes — disabling a subsystem, replacing a binding,
   clearing a word list — render a confirm step that restates the change
   in plain language before the pipeline runs.
5. **Failures explain, they don't crash.** Pipeline rejections surface
   as an ephemeral with the reason. The original panel stays open so the
   operator can correct and retry.
6. **One input strategy per field.** Don't ask the same field through
   both a dropdown and a modal in the same panel — pick one. The
   strategy table below names the canonical option for each field shape.
7. **Audit is non-optional.** Every successful mutation writes an audit
   row through the pipeline. Views must not call mutation primitives
   that skip the audit path.
8. **Feature Action Panels are valid.** Operator/admin panels that mix
   read, navigate, and mutate are an accepted pattern when the mutation
   routes through a pipeline. The anti-pattern is the view callback
   itself writing to the database or to ``guild_config``.

---

## Input strategies

Eight recognised input shapes. Picking the right strategy for a field
is the first design decision.

### 1. `boolean_buttons`

For an on/off field with no third state.

- **Surface:** two buttons (`Enable` / `Disable`), the active one
  disabled and styled `success`/`danger`.
- **Current value:** rendered above the buttons as
  `Current: Enabled` / `Current: Disabled`.
- **Preview/confirm:** not required — single-click flips the bit.
- **Pipeline:** `SettingsMutationPipeline.set_scalar`.

### 2. `enum_select`

For a field with 2–25 named values (mode toggles, severity tiers).

- **Surface:** a single dropdown listing every option with its emoji
  and one-line description.
- **Current value:** the active option is marked `(current)` in its
  description; never disabled (operator can re-select to confirm).
- **Preview/confirm:** required if the enum drives wide visibility or
  routing changes (e.g. mod-tier escalation).
- **Pipeline:** `SettingsMutationPipeline.set_scalar`.

### 3. `numeric_presets`

For numeric fields with a small set of operator-meaningful values
(seconds, minutes, percentages, common counts).

- **Surface:** 3–6 preset buttons (e.g. `5m`, `30m`, `1h`, `4h`,
  `24h`) plus a `Custom…` button that opens a single-field text modal
  for off-preset values.
- **Current value:** rendered above the buttons; the matching preset
  is disabled when applicable.
- **Preview/confirm:** not required for tunables; required for limits
  (XP cooldown, raid thresholds).
- **Pipeline:** `SettingsMutationPipeline.set_scalar`.

### 4. `role_select`

For fields that reference one or more roles.

- **Surface:** Discord-native `RoleSelect` component. Single- or
  multi-select per field semantics.
- **Current value:** mentions rendered above the select.
- **Preview/confirm:** required for tier-escalating bindings
  (`mod_role`, `admin_role`).
- **Pipeline:** `BindingMutationPipeline.set_role_binding` (or
  `replace_role_binding` for multi-role fields).

### 5. `channel_select`

For fields that reference one or more channels.

- **Surface:** Discord-native `ChannelSelect` filtered by channel type
  (text vs voice vs category) appropriate to the field.
- **Current value:** mention(s) rendered above the select.
- **Preview/confirm:** required when the channel becomes a routing
  target (mod logs, audit channel, prize drop channel).
- **Pipeline:** `BindingMutationPipeline.set_channel_binding`.

### 6. `member_select`

For per-user grants (designated VIPs, exempt members).

- **Surface:** Discord-native `UserSelect`. Multi-select where the
  field is a list.
- **Current value:** mentions rendered above the select; truncate with
  `+N more` when the list exceeds 5.
- **Preview/confirm:** always required — grants are a power-elevation
  surface.
- **Pipeline:** subsystem-specific grant API or
  `BindingMutationPipeline` if the field is a binding.

### 7. `text_modal`

For free-form text — names, messages, regex patterns, custom URLs.

- **Surface:** a `Modal` with one or two `TextInput` fields, label
  + placeholder + max-length.
- **Current value:** rendered above the launch button.
- **Preview/confirm:** required for changes that go to many users
  (welcome message, level-up message, broadcast template).
- **Pipeline:** `SettingsMutationPipeline.set_scalar` or a
  subsystem-specific service for fields that need parse/normalize
  (e.g. cleanup word lists → `cleanup` service).

### 8. `preset_pack_select`

For coordinated multi-field changes — "set up Moderation for a small
server", "switch Economy to the high-payout preset".

- **Surface:** dropdown of named packs with a short description.
- **Current value:** the active pack (if any) marked `(applied)`;
  custom (no-pack) states render as `Custom`.
- **Preview/confirm:** **always required** — the preview lists every
  field the pack will overwrite and the current vs new value.
- **Pipeline:** delegates to the relevant mutation pipelines for each
  field; the preset orchestrator never bypasses them.

### 9. `advanced_custom` (fallback)

For fields that don't fit any of the above (free-form JSON blobs,
operator-only overrides, schema fragments).

- **Surface:** an `Advanced…` button that opens a multi-field modal or
  a paginated text editor.
- **Current value:** rendered as a code block above the launch button.
- **Preview/confirm:** always required; the preview must render the
  parsed-and-normalized form, not the raw input.
- **Pipeline:** subsystem-specific. The view still does **not** write
  directly.

---

## Anti-patterns (don't ship these)

1. **Raw text modal for an enumerated value.** If the value space is
   known and bounded, use `enum_select` or `boolean_buttons`.
2. **Direct ``guild_config.set(...)`` from a view callback.** Always
   call the right mutation pipeline.
3. **Side-channel cache invalidation.** Pipelines own cache
   invalidation. A view that mutates and then manually calls
   ``cache.invalidate(...)`` is duplicating work that the pipeline
   already does and risks divergence.
4. **Silent failure.** A pipeline rejection that gets swallowed by the
   view (no ephemeral, no log, no retry path) hides config drift from
   the operator.
5. **Skipping the current-value line.** Every config surface shows
   what's there now. Operators should not have to leave a panel to
   discover the current state.
6. **No-confirm destructive change.** Disabling a subsystem, replacing
   a binding to a high-tier role, or clearing a word list always
   confirms.
7. **Bypassing the audit row.** Mutation primitives that don't write
   audit are operator-side only (used in tests/migrations). Live UI
   must go through the pipeline.

---

## Open questions (deferred)

- **Per-field rollback UI.** Pipelines emit audit rows but there's no
  user-facing "revert last change" yet. The audit table has the data;
  the UI does not. Future work.
- **Bulk-edit pages.** Several subsystems benefit from editing 10–30
  fields at once (the operator-presets flow). The current `apply
  preset` action covers most cases; a generic bulk editor is future
  work.
- **Schema-driven generation.** Once every settable field has a
  `SettingSpec` and a strategy hint, the input surface can be
  generated from the schema. This is the long-term direction; the
  strategy table above is the contract that generator would target.

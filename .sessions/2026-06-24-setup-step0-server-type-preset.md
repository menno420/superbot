# 2026-06-24 — Essential Setup step 0: server-type starter preset (direct-apply)

> **Status:** `in-progress` — born-red card; auto-merge holds until flipped `complete`.

> **Run type:** `routine · dispatch`

## What I'm about to do
Scheduled dispatch fire, no work order. Open bugs are blocked/data-gated for an
unattended run (BUG-0009 remaining slices need BTD6 release-order data + plan-level
work; BUG-0011 needs a VPS repro; BUG-0019 #1 is an owner design fork). So I take the
**owner-directed ▶ next** for the Essential Setup spine: **step 0 — "What kind of
server is this?"** (the server-type starter preset), the explicit remaining item in
[`planning/setup-wizard-restructure-plan-2026-06-24.md`](../docs/planning/setup-wizard-restructure-plan-2026-06-24.md)
§5 / §7 (PR 1 tail).

**The design decision the plan flagged ("presets are draft-only today; needs a
direct-apply path"):** step-0 starter sets are **pure settings bundles** applied
through the same audited `SettingsMutationPipeline` (`_StepView._set`) every other
spine step uses — *not* the draft-only `automation_templates.SERVER_PRESETS` (those
bind channels / create roles+rules → need operator picks + Final Review, the wrong
shape for Q-C's "fastest, nothing irreversible"). Every value is a channel-independent
boolean/scalar, so picking a type never creates or binds anything and is fully
reversible from each feature's own panel later.

Five server types (Community · Gaming · Support · Creator · Just exploring), each a
curated bundle of automod toggles + `moderation.dm_on_action` + an XP rate (reusing
`_XP_RATES`). Inserted as the new first step; tests updated for the index shift +
new step coverage.

## Shipped
- (filling in as I go)

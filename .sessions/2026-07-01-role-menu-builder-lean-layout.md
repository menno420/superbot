# 2026-07-01 — Role-menu builder "slim" lean layout

> **Status:** `complete` — ready to merge (Q-0133). Run type: manual · owner-directed.
> Full CI mirror green (**13598 passed**; lint/mypy/consistency clean; arch 0 new). PR #1615.

**Branch:** `claude/reaction-roles-counter-bgxnyd` (restarted from `main` @ #1613 — the sim merged).

## What I'm about to do (intentions)

Owner: "Build the slim version now." Adopt the layout the sim (#1612/#1613) recommended into the actual
builder — the lean 2-row layout with the five rarely-tapped knobs folded behind a new ⚙️ Advanced
sub-panel, Style kept first-screen.

## What shipped

The reaction-role menu builder went from **14 buttons / 3 rows** to a **lean 2-row** layout:

- **`disbot/views/roles/role_menu_builder.py`:**
  - **Row 0** (hot content): 🧩 Template · 📦 Packs · 🏷️ Roles · 🎚️ Style · 📝 Text.
  - **Row 1**: 🎨 Colours · 📍 Channel · ⚙️ Advanced · 🚀 Post · ↩ Back (Back moved row 2→1).
  - New **`_AdvancedView`** sub-panel (opened by ⚙️ Advanced) holds the five folded controls —
    🎭 Theme · ⚙️ Mode · 🔢 Limit · 🖼️ Card · 📊 Counts — reusing the existing pickers/modals. Their
    current values still show on the **main preview** (the builder's Settings field), which updates live.
  - **Style stays top-level** (owner directive — dropdown-vs-buttons is a primary choice).
  - Fixed `_LimitModal.on_submit` + the folded Counts toggle to refresh the **main** preview via the
    builder's stored panel interaction (`_rerender`), since they're now opened from the sub-panel (their
    own interaction is on the sub-panel message, not the main one).
- **`architecture_rules/consistency_exceptions.yml`:** repointed the `edit_in_place` allowlist entries
  for the folded controls to `_AdvancedView`, added `RoleMenuBuilder.advanced_btn` (all open genuine
  ephemeral sub-flows, the same idiom as the other allowlisted pickers).
- **Tests (+3):** top-level buttons are the lean set (Style present, the five knobs absent); `_AdvancedView`
  holds exactly the five folded controls; the Advanced Counts toggle flips the builder flag. The existing
  row-cap guard confirms both rows ≤ 5.

No change to what gets **posted** — only the builder's button surface. No migration, no new commands.

## Why this is contained / safe

Pure UI-surface reorganisation of the builder; all the underlying flows (pickers, modals, commit,
`_rerender`) are reused unchanged. The row-cap test + consistency allowlist guard the structural risks.
Needs a live re-test (open `!roles` → Reaction Roles → Role Menus → New Menu; confirm the two rows render
and ⚙️ Advanced opens the five controls). Full CI mirror green (13598 passed).

## Context delta

- **Discovered:** the `edit_in_place` consistency rule flags every "open a sub-picker via send_message"
  handler — the existing builder pickers were already allowlisted, so the new `advanced_btn` +
  `_AdvancedView` pickers needed the same treatment (moving the folded ones' entries to the new class).
  A good guard: it forced me to consciously mark each new ephemeral-sub-flow as intentional.
- **Decisions made alone (reversible):** kept Back on the action row after Post (matching the builder's
  existing Post-then-Back convention) rather than the sim's Back-left nicety; the folded Counts toggle
  refreshes its own sub-panel in place (immediate feedback) *and* the main preview.
- **🛠 Friction → guard:** none new — the row-cap test + the `edit_in_place` consistency rule already
  cover the two ways this change could go wrong (a 6th button on a row; an un-allowlisted new-message flow).

## 💡 Session idea (Q-0089)

The builder-press instrumentation idea (data-driven journey weights) from the parent sim sessions stands
and is now *more* valuable — with the lean layout live, real press counts would confirm whether the
Advanced fold matches actual usage (e.g. is Counts really rare now that RSVP templates set it?). Per
Q-0089 (one genuine idea per session, no filler), no second idea here.

## ⟲ Previous-session review (Q-0102)

Predecessor is the **pin-Style sim update (#1613)**. **Did well:** it took the owner's correction and
encoded it as a *general* mechanism (`PINNED_FIRST_SCREEN`), not a one-off Style hack, so the next pinned
button is one line. **What this session confirms it set up well:** because the sim already produced the
exact lean grid (with Style row-0), building it was a mechanical translation — the sim doubled as the
spec. **System note:** the sim→build handoff worked, but there's no automated check that the *built*
layout matches the sim's `CURRENT_LAYOUT` constant — a future drift (someone re-orders a button) would
silently diverge the sim's "current" baseline from reality. A tiny guard asserting the builder's actual
top-level button set matches the sim's inventory would close that loop (a lean extension of the existing
drift-guard test).

## 📤 Run report

- **Did:** adopted the sim's lean 2-row builder layout (five knobs folded behind ⚙️ Advanced, Style
  first-screen). · **Outcome:** shipped (pending live re-test)
- **Shipped:** PR (this) — the "slim" builder layout
- **Run type:** `manual · owner-directed`
- **Class:** UX / feature (builder surface reorganisation; reuses all underlying flows)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** a quick **live re-test** of the builder (two rows render; ⚙️ Advanced opens
  Theme/Card/Counts/Mode/Limit; each still updates the preview). Merge auto-deploys.
- **⚑ Self-initiated:** no — owner-directed ("build the slim version now").
- **↪ Next:** the sim↔builder layout-parity guard noted above; builder-press instrumentation for
  data-driven weights; the deferred `ReactionRolesPanel._rerender` ephemeral-edit fix.

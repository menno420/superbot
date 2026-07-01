# 2026-07-01 — Fishing structures sub-hub (🏗 Structures child) + Legendary curio tier

> **Status:** `complete`

**Dispatch run (routine · dispatch), no explicit work order — advanced the next offline plan slice.**
The `2026-07-01-fishing-dock-sail-alias-crash` handoff named the ▶ next offline successor, and I
shipped **both** of the two options it listed, as two contained self-mergeable slices on PR #1603.

## What shipped

### Slice 1 — 🏗 Structures sub-hub (fold Tide Pool + Dock)
The fishing menu had grown to 7 buttons (Cast · Set sail · Rod · Bait · Tide Pool · Dock · Fishdex ·
How-to) + the Help/Games nav. As coral gains more structure sinks the menu gets crowded, so the two
structure buttons collapse into one **🏗 Structures** child.
- **New `views/fishing/structures_hub.py`** — `StructuresView` (🪸 Tide Pool · ⚓ Dock · ↩ Fishing
  menu), `build_structures_embed` (both structures' built level + bonus at a glance), and
  `open_structures_hub` (the panels' back target). `SUBSYSTEM = "fishing"` so `attach_standard_nav`
  keeps Help + Games — never a dead-end.
- **`menu.py`** — the two structure buttons become one **🏗 Structures** button; embed description
  updated (dropped the stray "🏖️ Dock" venue line, added a Structures line).
- **`tide_pool.py` / `dock.py`** — the ↩ back button now returns to the Structures sub-hub (its
  canonical parent) instead of jumping to the menu, so nav is a clean two levels: menu → structures
  → a structure. Footers updated to "↩ Structures".
- **`views/fishing/__init__.py`** — exports the new symbols.
- **+13 tests** (`tests/unit/views/test_fishing_structures_hub.py`): menu now shows one Structures
  button (not two), the button opens the sub-hub, the sub-hub routes into each panel + rebuilds the
  menu on back, and each panel's back returns to the sub-hub.

### Slice 2 — Legendary Coral Leviathan curio (second curio tier)
Extended the cosmetic coral-curio collection with a Legendary top trophy.
- **`utils/mining/items.py`** — `coral leviathan` ItemDef (value 240, `TREASURE`, `curio` tag →
  non-sellable, no coin faucet).
- **`utils/fishing/curios.py`** — Coral Leviathan catalog entry (16 coral, Legendary 🐉). Doubling
  long-tail: coral cost 2→4→8→**16**, net-worth 30→60→120→**240** (each tier ×2 on both axes).
- **`docs/planning/fishing-coral-numbers-2026-07-01.md`** — pinned numbers table + rationale updated.
- **Tests** — collection totals (0,3)→(0,4) etc., a dedicated `test_leviathan_is_the_legendary_top_tier`.

Both slices are pure UI/content — **no migration, no mechanic change, byte-identical build/cast paths.**

## Verification
- `python3.10 scripts/check_quality.py --full` → **green**: `All checks passed ✓`
  (black + isort + ruff + mypy + **13448 passed, 48 skipped, 2 xfailed**; artifacts fresh).
- `python3.10 scripts/check_architecture.py --mode strict` → **0 errors** (49 pre-existing warnings;
  the new `StructuresView`/`structures_hub.py` extend `HubView` → no new violations).
- `python3.10 scripts/check_current_state_ledger.py --strict` → in sync (exit 0).
- Born-red gate: this card opened `in-progress` (PR #1603 red), flipped to `complete` as the
  deliberate final step.

## Handoff (▶ next)
S1-bot ▶ next offline successor is de-staled: a **third fishing structure** (a new coral/wood payoff —
e.g. an energy-regen "Boathouse" — that slots straight into the new 🏗 Structures sub-hub), or the
fishing **open-world expansion** (Phase 2: boat-as-structure / travel-timer / destinations). Both pure
+ self-mergeable. No live-bot or owner gate.

## 💡 Session idea (Q-0089)
**A generic `SubHubView` primitive for "N child panels + back" menus.** The fishing menu, the mining
character hub, the games hub, and now the fishing structures sub-hub all hand-roll the same shape: a
`HubView` with one button per child that lazy-imports the child view, `edit_message`s to it, sets
`view.message`, and `self.stop()`s — plus an `open_*` rebuild function for the child's back button.
That boilerplate is copy-pasted per hub (and each copy is a place to forget `view.message` or the
`self.stop()`). A small `views/sub_hub.py` primitive — `SubHubView(children=[(emoji, label,
open_fn), …], back=open_parent)` — would collapse the repetition and make "add a child" a one-line
registration, the same way `attach_windowed_select` / `attach_standard_nav` did for their patterns.
Worth a `docs/ideas/` file if it survives review; genuinely believe it, having just written the third
near-identical instance by hand.

## ⟲ Previous-session review (Q-0102)
The previous run (`2026-07-01-fishing-dock-sail-alias-crash`, PR #1600/#1601) did excellent
root-cause work on the `dock` boot-crash — it not only fixed the alias but **broadened the CI token
guard to the same-cog shape** and shipped a real **boot smoke test** (`test_cog_load_smoke.py`), so
the whole boot-break class is now caught at CI. That is exactly the "enforce, don't exhort"
discipline the workflow asks for. One thing it *couldn't* close: it flagged that "nothing verifies a
merge actually stayed up in prod" — a **post-merge prod-health check** is still only a note, now
twice in two days. **System improvement it surfaces (and I echo):** the recurring gap is not
detection-at-CI (that's now strong) but *no automated confirmation the deployed worker reached the
gateway*. That belongs on the ops/reconciliation side (a lightweight post-deploy health ping), and is
the single highest-value workflow add right now — worth an explicit `docs/ideas/` capture next run.

## 📋 Doc audit (Q-0104)
- Ledger in sync at start and end (`check_current_state_ledger --strict` exit 0); PR #1603 will be
  recorded by the next reconciliation pass (#1620) — no self-referential placeholder.
- S1-bot sector ▶ next successor de-staled to reflect both shipped slices (fix-on-sight, Q-0166).
- Numbers doc (`fishing-coral-numbers-2026-07-01.md`) updated in the same commit as the constant
  (its own convention). No new owner decision (pure content + UI, no product-intent change) → no
  router entry needed. No chat-only knowledge left un-homed.

## 📤 Run report footer
- **Run type:** routine · dispatch
- **PR:** #1603 (auto-merge armed on green CI; born-red gate flipped complete)
- **⚑ Self-initiated:** the whole run (empty work order → advanced the S1 ▶ next offline successor,
  both listed options). Idea→plan→ship was already open for these (handoff-named successors); no new
  ungrounded feature invented.
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none (both slices are offline/no-migration; the merge auto-deploys)

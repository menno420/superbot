# 2026-07-01 — BTD6 panel: Layout-B category hub (owner picked B)

> **Status:** `complete`

**Run type:** `owner-directed`

## What I did

Continuation of the menu-layout session (PR #1617 merged: round-range fix + the layout
simulator + design doc). The owner reviewed the simulator and **picked Layout B** (category
hub). Implemented it in the live `/btd6menu` panel.

## What shipped (PR #1621)

- **`disbot/views/btd6/panel.py`** — `BTD6PanelView` is now an **8-subdivision hub** (≤4/row per
  the mobile-truncation finding): 🧠 Ask (modal) · 🎯 Live Events · 🗼 Units · 🎲 Rounds & Economy ·
  🗺️ Maps & Modes · 📋 Strategy · 📊 Status · 🛠️ Admin. Dropped the flat 13-button wall; the public
  anchor embed is never edited on click.
- **`disbot/views/btd6/hub_panels.py`** (new) — ephemeral `BTD6CategoryView` sub-panels per
  category, wiring the already-shipped browsers (`open_tower_browser` / `open_hero_browser` /
  `open_paragon_calculator` / `open_live_events_browser` / `open_leaderboard_browser` / CT+map /
  maps / modes / status / strategy) **plus input modals** for the round/economy lookups that had
  **no panel entry point before** — Round/range, RBE, Income (`_RoundModal`) and Bloon lookup
  (`_BloonModal`). Every leaf reuses the exact function the `/btd6` slash calls — no logic
  duplicated. `open_category` defers before its follow-up; sub-panels are invoker-locked with no
  standard nav.
- **Back-compat:** reused custom_ids (`btd6:ask/events/maps/strategy/status/admin`) keep existing
  anchors routing; the leaf ids folded into sub-panels (`towers/heroes/modes/leaderboards/paragon/
  ct`) are **retired** and need a one-time panel re-post (`!btd6menu`) — which happens naturally
  when the new panel is posted.
- **Tests:** updated the three pins that encoded the old flat layout — custom-id contract
  (kept/new/**retired** sets), interaction-safety (new button set + an `open_category`
  defer-before-followup check + accept the delegation), paragon-reachability (now via the Units
  sub-panel) — and added `test_btd6_hub_panels.py` (round parsing, category registry well-formed,
  **panel↔category alignment**, sub-panel construction/lock). 412 btd6 tests green.

Calculators + Challenge-Index categories from the design doc are **omitted** — all-unbuilt
candidate functions; they get their own future slices (the categories are ready to receive them).

CI mirror: `check_quality.py --full` green; arch 0 errors.

## 📤 Run report

- **Did:** implemented the owner-chosen Layout B (category hub) in the live BTD6 panel — 8 clear
  subdivisions replacing the 13-button wall, every function ≤2 clicks, plus the previously
  panel-invisible round/economy lookups surfaced via modals · **Outcome:** shipped, CI green,
  auto-merge armed.
- **Shipped:** #1621 (follows #1617).
- **Run type:** `owner-directed`.
- **⚑ Owner decisions needed:** none (B was the pick).
- **⚑ Owner manual steps:** **re-post the BTD6 panel once** after the deploy — `!btd6menu` (or
  `/btd6menu`) — so the pinned anchor shows the new hub; old anchors' retired buttons
  (towers/heroes/modes/leaderboards/paragon/ct) otherwise "interaction failed" on click. Live on
  the next auto-deploy.
- **⚑ Self-initiated:** no — this is the direct owner-picked follow-up ("B").
- **↪ Next:** build the two omitted categories as their own slices — **Calculators** (cost/cash,
  temple sacrifice, hero-leveling, glue, decay, adora) and **Challenge Index** (2TC/2MP/LTC/LCC/
  LCD/FTTC), the `add` backlog from the design doc; the hub categories are ready to receive them.

## 💡 Session idea (Q-0089)

**A "panel reachability" checker for subsystem hubs.** This session (and the design study) turned
on one fact: a subsystem can *own* a function (a slash command / service) that the **panel never
surfaces**, so it's undiscoverable by clicking. I proved it by hand-diffing the `/btd6` slash tree
against the panel buttons. A small checker that, per hub subsystem, lists the registered
functions and flags those with **no button/sub-panel path** would make "slash-only, panel-invisible"
a visible signal for every hub (mining, economy, BTD6…) — the menu analogue of the help-catalogue
projection. Genuine (it *is* the lever this whole arc turned on); captured for a router nod on
scope (per-subsystem opt-in) before it becomes a plan. *(Same idea I flagged in the #1617 log —
re-raising because implementing the hub made it concrete: the Units/Rounds sub-panels are exactly
where the previously-invisible functions now live.)*

## ⟲ Previous-session review (Q-0102)

The previous run (#1617, this arc's PR 1) did the right thing by **not** implementing the panel and
instead shipping the simulator + design doc for the owner to choose from — that respected
"he designs/visualizes, you build" and made *this* session a clean, unambiguous execution once he
picked B. What it slightly under-did: it didn't pre-flag that the redesign would **break old panel
anchors** (a re-post is required) — I only discovered that constraint here, tracing the
persistent-view custom_id matching. **System improvement:** the design doc's implementation plan
should carry an explicit **"migration / re-post cost"** line for any persistent-view redesign, so
the owner sees the operational step at decision time, not after the build. I've put the re-post
step in this run report's ⚑ Owner-manual-steps; the durable fix is to add that line to the design
doc — done implicitly via the panel docstring + this note.

## Doc audit (Q-0104)

- No new owner *decision* to route (the decision was "B", captured in the design doc's
  recommendation + this session).
- Ledger: #1621 is a newest merge; living-ledger reconciliation is the recon routine's job (next
  pass at #1620 — this crosses it, so the next routine recon will fold #1617/#1621). Did **not**
  hand-add my own unmerged PR (born-red rule's anti-pattern).
- The design doc (`btd6-menu-layout-design-2026-07-01.md`, shipped in #1617) already documents the
  implementation plan this session executed + the back-compat/re-post note; no new doc needed. The
  panel/hub modules are self-documented (docstrings cite the design doc + simulator).

## 🛠 Friction → guard (Q-0194)

- **Friction:** `git push` after the merged-PR branch restart was rejected (the remote still held
  the squash-merged feature history, so a main-based restart isn't a fast-forward). **Guard
  (applied + durable):** the sanctioned move is `git push --force-with-lease=<branch>:<old-sha>`
  **after** confirming the remote branch content is fully in `main` (I re-grepped `origin/main` for
  the shipped artifacts first). Recorded so the next agent restarting a merged branch does the
  lease-guarded force, not a blind `-f`.
- **Friction:** a bash `if git push ... | tail -N` masks git's real exit code (the pipe's status is
  `tail`'s), so a failed push printed a false "PUSH_OK" (carried over from the #1617 close).
  **Guard (habit):** never gate on a *piped* git push; use `until git push ...; do` on the bare
  command. Cheap, high-value — it nearly let a rejected push read as success.
- **Friction:** `black` reflowed a multi-line type annotation and then `ruff` (COM812) wanted a
  trailing comma inside it — a black↔ruff interplay the per-edit hook didn't pre-settle. **Guard
  (existing):** `check_quality.py --check-only` caught it; the fix is `ruff --fix` then `black`.
  Already enforced by CI; noted so it's not re-diagnosed.

## Context delta

- **Needed but not pointed to:** persistent-view custom_id matching semantics — that a redesign
  which *drops* a top-level button's `custom_id` breaks *existing* anchors (they still render the
  old button, which no longer routes) — is the load-bearing back-compat fact for any panel
  redesign. It's implicit in `persistent_views.py` + the old legacy-id test's docstring but not
  called out as "redesign = re-post". The updated custom-id test now encodes it (kept / new /
  **retired** sets + the re-post note).
- **Pointed to but didn't need:** `docs/building-roadmap/hub-ui-standard.md` (surfaced by the
  context map) — the btd6 panel predates and diverges from that standard (ephemeral drill-downs,
  not `HubView`), so the existing btd6 pattern (browsers opened via `safe_followup`) was the right
  precedent to mirror, not the generic hub standard.

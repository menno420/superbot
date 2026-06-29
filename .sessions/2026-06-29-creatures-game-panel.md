# Session — Creatures completion: game panel + interactive dex browser (Q-0209 deepening)

> **Status:** `complete`

**Run type:** routine · dispatch

## What I did + why
Empty-fire dispatch run. S1 posture is completion-first (Q-0209); the previous run's ▶ Next teed up
deepening the `◐ assessed` certs' punch-lists. The Creatures completion certificate
(`docs/planning/feature-completion/units/creature.md`, assessed 2026-06-28) named the **headline
rubric-B gap**: Creatures was **hub-less v1** — no interactive game panel, no interactive dex browser —
so the Games-hub → Creatures path stopped at a static embed. This run closed that gap end-to-end and
cleared 4 of the 7 punch-list items (PR **#1546**):

1. **Game panel (#1).** New `disbot/views/creature/` package: `CreatureMenuView` (`HubView`,
   `SUBSYSTEM = "creature"`) — **🐾 Catch** (one encounter in place, shares `creature_workflow.catch`),
   **📖 Dex** (the interactive browser), **⚔️ Challenge** (a `UserSelect` → the existing
   `CreatureBattleChallengeView` accept/decline flow), **🏆 Ladder**, **📖 How to play**, and
   auto-attached **📚 Help / ↩ Games** nav. Reached via a new `!creatures` / `!creaturemenu` command and
   the live Help hook on **both** creature cogs (catch + PvP), so the whole game is one coherent panel.
2. **Interactive dex browser (#2).** `CreatureDexView` — an element-filter `Select` over the
   collection + ◀ Back to the menu + standard nav. (`!dex` was a static embed.)
3. **Registry `entry_points` (#3).** The `creature` entry now declares
   `creatures`/`catch`/`dex`/`cbattle`/`cbrecord`/`cbattletop` (was just `catch`/`dex`).
4. **Battle settle-once (#5).** `CreatureBattleChallengeView` now mixes in `SettleOnceMixin` and claims
   the transition at the top of accept/decline, so a double-click can't resolve + record a battle twice.

DRY: extracted the dex / catch-result / ladder / record / menu / rules embeds into one
`views/creature/embeds.py`, shared by the panel **and** both cogs (one source of truth — the panel's
cards can't drift from the typed commands). Punch-list **#4 was a no-op** (the accept path already
responds via `edit_message` before the slow `resolve_and_record_pvp`, so the follow-up uses the 15-min
`followup` window). **#6/#7 (live walkthrough + owner sign-off) stay owner-paced.**

Method note (Q-0120): I modeled the panel on `views/fishing/menu.py` and `views/games/deathmatch_panel.py`
(the closest mature analogues), and verified each call site against source rather than assuming the
shape. Adding the PvP commands to `entry_points` correctly made `CreatureBattleCog` help-reachable, so I
gave it the same shared Help hook (the `test_help_direct_navigation` guard caught this — a good guard).

**Tests:** `tests/unit/views/test_creature_menu.py` (embeds + every panel button + the dex filter +
opponent-select reject/open paths) and `tests/unit/views/test_creature_battle_settle_once.py`
(double-accept resolves once; accept-then-decline settles once). Regenerated `dashboard.json` /
`site.json` for the new `creatures` command; updated the cert + S1 ▶ Next.

CI mirror green underneath (`check_quality.py --full`: black/isort/ruff/mypy/pytest all pass; the only
red is the born-red session gate until this card flips); `check_architecture --mode strict` 0 errors.

## Continuation steps (for the next dispatch)
- **▶ Next (offline, self-mergeable):** keep deepening the assessed certs' punch-lists. Strong picks:
  **Welcome command panel** (Welcome cert punch-list #1 — its headline gap, mirrors this Creatures
  panel build), the **Mining how-to button** (Mining is the ✔-ready candidate; its one remaining build
  gap — note Mining's hub is a `PersistentView`, so the button needs a `custom_id` + likely an
  `edit_in_place` consistency exception for an ephemeral how-to card), or any server-fn deepening pick
  from the S1 assessments bullet (Inventory item-grant audit · Proof-channel lock/unlock audit).
- **Creatures `◐ → ✔`** needs only the owner-paced live walkthrough (`/verify-bot`: catch → dex-filter →
  challenge → accept → battle → rematch → ladder) + sign-off (cert #6/#7).
- A **cross-view simultaneous-challenge dedup** (a per-pair active-battle registry) remains a possible
  Creatures deepening, but is lower-risk than the double-click the settle-once now guards.

## ⟲ Previous-session review (Q-0102)
The previous dispatch run (PR #1534, the Mining/Creatures/Welcome assessments) did the assessment job
genuinely well: it cross-checked two over-positive Explore agents against source and corrected their
"ready for release" verdicts into honest punch-lists — exactly the Q-0120 "verify, don't trust" posture.
Its certs were precise enough that **this run could build straight off the Creatures punch-list with no
re-investigation** — the assessment paid for itself one run later, which is the completion-first arc
working as designed. One thing it could have done better: it left Creatures' missing panel and Welcome's
missing command panel as `⚑ Owner-decisions` ("may want built or waived") — but per Q-0172
(idea→plan→ship is open) a missing-panel deepening is contained, reversible, test-covered build work
that doesn't actually need an owner gate; it could have just teed it up as the next `[offline]` ▶ Next
(which is how this run treated it). **System improvement surfaced:** the assessment certs' punch-lists
are now a high-signal build backlog, but they live only inside each unit's cert file — there's no
rolled-up "open punch-list items across all assessed units" view a dispatch can scan to pick the
highest-value offline slice. A tiny generator that greps the certs for open punch-list lines into one
ranked backlog (like the scoreboard does for state) would make "pick the next deepening slice" a
one-look decision. Captured as the session idea.

## 💡 Session idea (Q-0089)
**A completion punch-list backlog generator.** `scripts/` already regenerates a completion *scoreboard*
(unit × state). Add a companion that scans every `docs/planning/feature-completion/units/*.md` cert for
its **open** punch-list items (the un-✅'d / `[ ]` lines that aren't `[owner]`/`[needs-live-bot]`) and
emits one ranked **offline deepening backlog** — so a dispatch's "▶ Next deepening pick" is a single
look instead of opening 11+ cert files. It turns the per-unit punch-lists into the same kind of
single-source worklist the shipped-PR ledger and the scoreboard already are. Stdlib, read-only,
disposable per Q-0105. (Dedup-checked `docs/ideas/` + the completion README; this is distinct from last
run's *registry↔ledger parity* idea — that checks the unit *set* stays honest, this rolls up the units'
*open work*.)

## 📋 Doc audit (Q-0104)
- `check_quality.py --full` green underneath the session gate; `check_architecture --mode strict` 0
  errors; `check_consistency` all rules pass (added the `CreatureMenuView.rules_btn` ephemeral-how-to
  exception next to the fishing one).
- Regenerated `dashboard/data/dashboard.json` + `botsite/data/site.json` + `botsite/site/data.js` for
  the new `creatures` command (freshness suite green).
- Cert (`units/creature.md`) updated with the shipped/no-op punch-list state; S1 ▶ Next re-pointed to
  the deepening backlog. `check_current_state_ledger.py` will show only benign newest-merge lag
  (#1546 + the dashboard refreshes are newer than marker #1530; the next reconciliation pass records
  them — not drift). No fact stranded in chat.

## ⚙️ Post-push CI catch (honest record)
The first push's CI caught one test my local run missed: `test_help_surface_map_doc::
test_preamble_counts_match_live_registries` (hook-defining extensions 42 → 43). **Root cause of the
local miss:** I ran the full CI mirror *before* adding `build_help_menu_view` to `CreatureBattleCog`
(that came later, to satisfy `test_help_direct_navigation`), then only ran targeted tests — so I missed
that the new hook bumped the surface-map count. Fixed in a follow-up commit (preamble 42 → 43, dropped
`creature_battle_cog` from the "without the hook" list, de-staled the §2 creature row to the shipped
`CreatureMenuView`). **Lesson (worth a guard):** after a late non-trivial change, re-run the *full*
mirror, not targeted tests — the cheap enforcement would be a Stop-hook nudge when `disbot/` or
`entry_points`/help-hook surface changed after the last `check_quality --full`.

## 📤 Run report footer
- **Run type:** routine · dispatch
- **What shipped:** Creatures interactive game panel + dex browser + `entry_points` + battle
  settle-once (completion cert #1/#2/#3/#5), with a shared-embeds DRY refactor across both cogs and full
  test coverage. Runtime + tests + docs, PR #1546.
- **⚑ Self-initiated:** none requiring an owner gate — this is the dispatched completion-first ▶ Next
  (deepening the Creatures cert punch-list). The session idea is captured for grooming, not built.
- **⚑ Owner-decisions:** none required. (Surfaced for later: Creatures' `◐ → ✔` needs the owner live
  walkthrough + sign-off, cert #6/#7 — same as every assessed unit.)
- **⚑ Owner-manual-steps:** none. (The merge auto-deploys; no data/seed step — Creatures writes only the
  existing collection log + game-XP, no migration in this PR.)
- **Remarks:** CodeGraph available (used lightly; mostly direct reads + fishing/deathmatch analogues).
  Grimp not separately invoked. No arch warnings introduced (0 errors; the 49 warnings are all
  pre-existing/known). The `test_help_direct_navigation` guard usefully caught that adding PvP commands
  to `entry_points` made the PvP cog help-reachable → it needs the shared hook.

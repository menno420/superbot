# 2026-06-28 — Fishing + Counting feature-completion punch-list clears

> **Status:** `complete`

**Run type:** routine · dispatch (no work order — advancing the S1 completion-first arc, Q-0209)

## What this run did

The S1 completion-first arc (Q-0209) had assessed Fishing and Counting to `◐` and surfaced contained,
**offline** UX punch-list gaps. This run cleared all three offline-fit ones at the root (PR #1521).

**Fishing #1 (headline) — trapped shop views.** `FishingMenuView` `self.stop()`s when it opens the
Rod/Bait shops, and the shops were `BaseView` panels with no way back — a player who opened Rod/Bait
was stranded with no path to the menu, Games hub, or Help. Fixed:
- `RodShopView`/`BaitShopView` each gained a **↩ Fishing menu** `back_btn` that rebuilds the menu in
  place via the new module helper `menu.open_fishing_menu` (lazy-imported in the shops to respect the
  menu→shop import direction — no new cycle).
- `FishingMenuView` now declares `SUBSYSTEM = "fishing"` so `attach_standard_nav` adds **📚 Help** +
  **↩ Games** (the 2026-06-23 never-stranded directive; mirrors `_FishingDoneView`). The menu itself
  previously lacked these — a real consistency gap, fixed on sight. Back-from-shop now lands on a
  fully-navigable menu.

**Fishing #2 (minor) — rules affordance.** A **📖 How to fish** button on the menu sends an ephemeral
how-to-play card (`rules_btn` → `_rules_embed`), mirroring the blackjack panel's rules button.
Allowlisted in `consistency_exceptions.yml` (`edit_in_place`) — a read-only help aside is a genuine
new ephemeral, not a panel re-render.

**Counting #3 — admin-only discovery.** The only registered `entry_point` was the staff-only
`countingmenu`; counting had no player-facing discovery surface. `entry_points` now leads with the
existing player commands `count_info`/`counttop` (then `countingmenu`).

Both completion certificates (`feature-completion/units/{fishing,counting}.md`) updated to mark the
cleared items; each unit's remaining gaps are now owner-paced only (live walkthrough + sign-off; the
fishing coins Q-0175 and counting-reward decisions).

**Verified:** `check_quality --full` green (12953 tests; black/isort/ruff/mypy/check_consistency all
pass — fixed a black wrap + a COM812 trailing comma + allowlisted the rules-button ephemeral that the
first full run flagged); `check_architecture --mode strict` 0 errors. New tests: shop `back_btn` →
menu rebuild (rod + bait), menu `SUBSYSTEM`/Help+Games nav, `rules_btn` ephemeral, `open_fishing_menu`.

## 📤 Run report

- **Did:** cleared the offline Fishing (#1/#2) + Counting (#3) completion punch-list gaps · **Outcome:** shipped
- **Shipped:** #1521 — un-trap Rod/Bait shops (↩ Fishing menu + menu Help/Games nav), 📖 How-to-fish button, counting player entry point
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none (the two units' remaining `◐ → ✔` items are owner-paced: live walkthrough + sign-off; the fishing coins question Q-0175 and the counting XP/coin-reward decision are pre-existing, unchanged by this run)
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none — advancing the dispatched S1 completion-first arc (Q-0209) off the assessed punch-lists; no new idea promoted to a plan/build
- **↪ Next:** S1 completion-first — assess the remaining unassessed units (Mining [big read], Casino, Deathmatch, RPS, Creatures, Chicken Farm) one cert each; then the per-unit live walkthroughs + owner `◐ → ✔` sign-offs (needs a live bot)

## 💡 Session idea (Q-0089)

*A `check_consistency` rule (or a `subsystem_registry` test) that flags any user-tier subsystem whose
`entry_points` are **all** staff-gated commands.* Counting #3 was exactly this class — a player-facing
game (`visibility_tier: user`) whose only registered entry point was `@staff_or_owner`-decorated, so it
had no discovery surface yet looked "wired." The check would catch the next one at lint time instead of
waiting for a completion assessment to notice. Routed as an idea, not built here (it needs the cog
decorator→staff-gate mapping, which is more than a one-liner).

## ⟲ Previous-session review (Q-0102)

The prior run (#1518, the fishing pearl rare-material drop) deepened the fishing *economy* well but, like
the runs before it, kept adding **content** to a unit whose **navigation** was quietly broken — the
trapped Rod/Bait shops have existed since the shops shipped, unnoticed until the Q-0209 completion
assessment walked the UX. That's the completion-first arc working as designed: assessing for "right
buttons in the right places" caught a real stranding bug that feature-velocity sessions skated past.
**System improvement (applied this run):** the assessment's punch-list is genuinely actionable — I built
straight off it with no re-investigation. Worth reinforcing in the feature-completion README that an
`◐`-assessed unit's offline punch-list items are *pre-scoped dispatch work*, so a later run picks them up
without re-deriving the gap.

## 🧾 Doc audit (Q-0104)

`check_quality --full` green (incl. `check_docs`/`check_consistency`); arch 0 errors. New facts homed in
their durable place: the two completion certificates updated in lockstep with the code; no new owner
decision (the run executed within Q-0209/Q-0175's existing envelope). Ledger: merged-only convention —
the next reconciliation pass adds #1521. No chat-only facts left unhomed.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs opened | 1 (#1521) |
| Punch-list gaps cleared | 3 (Fishing #1, #2; Counting #3) |
| Files touched | 9 (3 runtime views, 1 registry, 1 arch-allowlist, 2 certs, 3 tests — net new tests +4 cases) |
| New test cases | 4 (rod/bait back-nav, menu nav, rules ephemeral, open_fishing_menu) |
| CI | `check_quality --full` green · `check_architecture --mode strict` 0 errors |

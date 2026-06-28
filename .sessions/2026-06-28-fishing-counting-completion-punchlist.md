# 2026-06-28 — Fishing + Counting feature-completion punch-list clears

> **Status:** `in-progress`

**Run type:** routine · dispatch (no work order — advancing the S1 completion-first arc, Q-0209)

## What this run is about (born-red card)

The S1 completion-first arc (Q-0209) assessed Fishing and Counting to `◐` and surfaced contained,
**offline** UX punch-list gaps. This run clears the offline-fit ones at the root:

- **Fishing #1 (headline):** Rod/Bait shops are *trapped views* — `FishingMenuView` `self.stop()`s
  when it opens them and the shops have no way back, so a player who opens Rod/Bait is stranded.
  → add return navigation (↩ Fishing menu) + make the menu carry standard Help/↩ Games nav.
- **Fishing #2 (minor):** no dedicated "how to play" affordance — add a 📖 How to fish button.
- **Counting #3:** the only registered `entry_point` is the admin-only `countingmenu`, so counting
  has no player-facing discovery surface → register the player commands as entry points.

Mark the cleared punch-list items in the two completion certificates.

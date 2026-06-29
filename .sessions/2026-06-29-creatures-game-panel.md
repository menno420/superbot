# Session — Creatures completion: game panel + interactive dex browser (Q-0209 deepening)

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What I'm about to do
Empty-fire dispatch. S1 posture is completion-first (Q-0209). The #1 punch-list item from the
2026-06-28 Creatures completion certificate is the headline rubric-B gap: Creatures is **hub-less v1**
with no interactive game panel and no interactive dex browser, so the Games-hub → Creatures path stops
at a static embed. This run builds that out:

1. **Game panel (#1)** — a Games-hub `CreatureMenuView` (`HubView`, `SUBSYSTEM="creature"`): catch in
   place · interactive dex browser · challenge a trainer (UserSelect) · PvP ladder · how-to · standard
   Help/↩ Games nav. Wired through the Help hook + a new `!creatures` command (mirrors fishing's panel).
2. **Interactive dex browser (#2)** — element filter over the collection (the convenience bar the
   other activity games meet).
3. **Registry `entry_points` gap (#3)** — add `cbattle`/`cbrecord`/`cbattletop` (+ the panel command).
4. **Battle settle-once guard (#5)** — `SettleOnceMixin` on `CreatureBattleChallengeView` so a
   double-click can't double-resolve/double-record a battle.

Plus tests, the cert punch-list update, and S1 ▶ Next handoff.

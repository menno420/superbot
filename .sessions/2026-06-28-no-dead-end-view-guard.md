# 2026-06-28 — No-dead-end terminal-view arch guard (friction→guard)

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What I'm about to do

Empty-fire dispatch. S1's ▶ Next-startable (offline) names: *"build the 'no-dead-end' arch guard
so the trapped-view bug class is caught automatically instead of per-assessment."* The completion-first
posture (Q-0209) keeps re-finding the same dead-end bug one game at a time (Fishing #1521, Deathmatch
+ RPS PvP #1527). This is the textbook friction→guard case (Q-0194): enforce, don't exhort.

**The slice:** a conservative warn-tier rule in `scripts/check_architecture.py` that flags a game
view's **terminal handler** (a method calling `self.stop()`) that re-renders / posts a terminal message
without swapping to a nav-carrying view (no other `*View(...)` constructed in the handler body). Scoped
to game-view dirs, allowlist-driven (same shape as `baseview_inheritance`), starts as warning. Verified
clean (or known-small) against the current fixed fleet, with unit tests pinning both the flagged
anti-pattern and the allowed swap pattern.

Offline / self-mergeable on green; checker guard ships free per CLAUDE.md.

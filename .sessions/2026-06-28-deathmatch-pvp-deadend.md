# 2026-06-28 — Deathmatch PvP trapped-view dead-end fix (completion-first)

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What I'm about to do

Empty-fire dispatch (no work order). The active S1 thread is **completion-first** certification
(Q-0209); several assessed game units carry real, offline-fixable UX gaps. Picked the **headline
gap** in the Deathmatch completion cert (`◐ assessed`): the **PvP** terminal views (`_DuelView`,
`_ChallengeView`) are **dead-ends** — on finish / timeout / decline / expire the player is stranded
on a dead embed with no return navigation (the bot-duel path already swaps to a nav-bearing result
view; the 2026-06-23 "never a dead-end" directive was missed for PvP). Punch-list #1 (headline) + #3
(PvP loop tests).

Scope (turn-key, mirrors the shipped bot-duel result view):
- New `_PvpDuelResultView(HubView, SUBSYSTEM="deathmatch")` in `deathmatch_panel.py` → auto-nav
  (📚 Help + ↩ Games) + a 🔁 Rematch button (re-challenge via the normal Accept/Decline flow);
  both fighters may use it.
- `_DuelView._resolve`/`on_timeout` and `_ChallengeView.btn_decline`/`on_timeout` swap to it on
  terminal instead of leaving a dead embed.
- **Bugs-first root fix:** panel-initiated PvP passes `ctx=None`; `_DuelView` reads
  `self.ctx.guild.id` on resolve → `AttributeError` crash. Thread an explicit `guild_id` through
  `_ChallengeView.btn_accept` → `_DuelView` so the panel-PvP path no longer crashes and records
  under the correct guild. Captured as a bug-book entry.
- PvP loop tests (finish/timeout swap-to-result, decline/expire nav, rematch re-challenge,
  panel-path guild_id) + cert update.

If capacity remains: the RPS PvP-play trapped-view gap (rps_tournament cert punch-list #2) is the
same class — a second slice.

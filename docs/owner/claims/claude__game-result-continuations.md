- `claude/game-result-continuations` · **Game-result continuation buttons (never-stranded follow-up)** —
  the game-RESULT dead-ends left by PR #1382's panel auto-nav: terminal game-state views
  (`discord.ui.View` directly) that disable all buttons and strand the player. Add a HubView terminal
  view (SUBSYSTEM → auto Help + Back-to-hub) + a game-specific "again" button. Scope:
  `disbot/views/games/deathmatch_panel.py` (`_BotDuelView` finish/timeout), `disbot/views/fishing/cast_view.py`
  (interaction terminals), `tests/`. Casino `PokerEndView` already has Deal-next/End — left as-is. 2026-06-23 ·
  PR (this session, auto-merge on green)

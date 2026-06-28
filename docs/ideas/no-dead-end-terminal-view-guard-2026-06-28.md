# Idea — a "no dead-end" arch guard for game terminal views

> **Status:** `ideas` · captured 2026-06-28 (dispatch run, Q-0089 session idea).
> Route-in: the completion rubric's "No dead-end controls" line
> ([`../planning/feature-completion/rubric-game.md`](../planning/feature-completion/rubric-game.md))
> + the architecture checker (`scripts/check_architecture.py`).

## The recurring bug

The 2026-06-23 owner directive is "a finished game/duel is **never** a dead-end" — a terminal view
must swap to (or carry) a result view with standard nav (`SUBSYSTEM` → 📚 Help + ↩ Games / a
◀ Back button), never just disable its buttons and `stop()`. This keeps re-appearing one game at a
time, caught only by manual completion assessments:

- Fishing — the Rod/Bait shops were trapped (fixed #1521).
- Deathmatch — the **PvP** `_DuelView`/`_ChallengeView` were dead-ends (fixed #1527).
- RPS — the **PvP** match result was a bare channel embed (fixed #1527).
- Chain / Farm assessments flagged the same risk on their terminal paths.

It is the textbook **friction → guard** case (Q-0194): a known, repeating defect class enforced only
by exhortation, not by a checker.

## The guard

A lightweight AST lint (a `scripts/check_architecture.py` rule, or a dedicated checker) that flags any
`discord.ui.View` subclass under `views/` / `cogs/` whose **terminal handler** either:

- ends an `on_timeout` / a handler that calls `self.stop()` with `view=self` (or only disabling
  `self.children`) and **no** swap to a view that carries standard nav, **or**
- posts a fresh terminal message (`channel.send(embed=…)` / `edit_message`) with **no `view=`** on a
  resolve path.

Heuristic, so it would need an allowlist (genuinely ephemeral one-offs, confirmations) — same shape as
the existing `baseview_inheritance` warn rule. Start as a **warning tier** (like the cog-size warn),
graduate to error once the existing fleet is clean.

## Why it's worth having

Turns a recurring manual catch into an enforced one ("enforce, don't exhort", Q-0132). Every
completion assessment currently spends effort re-checking this by hand; a guard frees that effort and
stops new games from shipping the same dead-end. Disposable per the adopt-freely-with-a-kill-switch
rule — if the heuristic proves too noisy across a few sessions, delete it.

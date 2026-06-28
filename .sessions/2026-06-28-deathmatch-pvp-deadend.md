# 2026-06-28 — Deathmatch + RPS PvP trapped-view dead-end fixes (completion-first)

> **Status:** `complete`

**Run type:** routine · dispatch

## What I'm about to do

Empty-fire dispatch (no work order). The active S1 thread is **completion-first** certification
(Q-0209); several assessed game units carry real, offline-fixable UX gaps. Picked the **headline
gap** in the Deathmatch completion cert (and the same trapped-view class in RPS): PvP terminal views
were **dead-ends** (no return navigation after a duel/match resolves).

## What shipped (PR #1527)

Two completion-first slices closing the same recurring **trapped-view** bug class across the two
competitive PvP games, plus a latent crash root-fix found mid-task.

### Slice 1 — Deathmatch PvP is never a dead-end (cert punch-list #1 headline + #3)
- New `_PvpDuelResultView(HubView, SUBSYSTEM="deathmatch")` in `deathmatch_panel.py` →
  `attach_standard_nav` auto-adds **📚 Help + ↩ Games**; plus a **🔁 Rematch** button that
  re-challenges the other fighter through the normal Accept/Decline flow (consent preserved). Either
  fighter may use it.
- `_DuelView._resolve` (winner) / `_DuelView.on_timeout` / `_ChallengeView.btn_decline` /
  `_ChallengeView.on_timeout` now swap to it on every PvP terminal instead of leaving a dead embed —
  closing the 2026-06-23 "never a dead-end" gap for PvP (it was applied only to the bot path's
  `_BotDuelResultView`).
- **Bugs-first root fix (BUG-0028):** panel-initiated PvP built the duel with `ctx=None`, so
  `_DuelView._resolve`/`on_timeout` reading `self.ctx.guild.id` **crashed (`AttributeError`) on every
  panel-PvP resolution** (and would have recorded under the wrong guild). Fixed at root by threading an
  explicit `guild_id` from `_ChallengeView.btn_accept` (`interaction.guild_id`) into `_DuelView`
  (`self.guild_id`, ctx fallback preserved for the command path + existing tests).
- DRY: extracted `build_deathmatch_challenge_embed` so the challenge prompt has one builder.
- Tests: `tests/unit/cogs/test_deathmatch_pvp_deadend.py` (7) — finish/timeout swap-to-result,
  decline/expire nav, rematch re-challenge, the `guild_id` thread + ctx-None no-crash, result-view
  authority (both duelists / bystander blocked).

### Slice 2 — RPS PvP result is never a dead-end (cert punch-list #2/#3 + part of #4)
- New `_RpsPvpResultView` in `views/rps/pvp_play.py` carrying the shared **◀ Back to RPS** button;
  `_resolve` now posts the result with it instead of a bare channel embed. Either participant may use it.
- `build_rps_rules_embed` gained a "Timeouts & forfeits" field (#3).
- Tests: `tests/unit/cogs/test_rps_pvp_deadend.py` (4) — `_resolve` posts the nav-bearing view,
  result-view authority, and a `!rpshelp` output **drift-guard** (the underscored/leaderboard drift
  fixed in the prior PR can't silently return).

Both certs updated: Deathmatch is now a **✔-ready candidate** (only owner walkthrough / coin-staking
remain); RPS is close to ✔-ready (owner rematch call + bot-batch test + walkthrough remain).

CI mirror green end-to-end (`check_quality.py --full`) · `check_architecture --mode strict` 0 errors ·
`check_consistency` clean. Born-red gate held the merge until this card flipped `complete`.

## 💡 Session idea (Q-0089)

**A "no-dead-end" arch invariant for game terminal paths.** This run (and several before it) keeps
re-finding the *same* bug class: a game view that `stop()`s / disables its buttons on a terminal
branch without swapping to a `SUBSYSTEM`-bearing result view, leaving the player stranded. The
2026-06-23 directive is enforced only by per-unit completion assessments catching it one game at a
time. Idea: a lightweight checker (`scripts/check_architecture.py` rule or a dedicated AST lint) that
flags any `discord.ui.View` subclass under `views/`/`cogs/` whose terminal handler (`on_timeout` /
a handler that calls `self.stop()`) ends with `view=self` / disabled-only children and **no** swap to
a view that carries standard nav — turning a recurring manual catch into an enforced guard
("enforce, don't exhort", Q-0132). Genuinely believe in this: the dead-end has now recurred in
deathmatch, rps, fishing shops, and the chain/farm assessments flagged it as a risk too — exactly the
"friction → guard" pattern (Q-0194). Will file to `docs/ideas/` (route-in: the completion rubric's
"no dead-end controls" line).

## ⟲ Previous-session review (Q-0102)

Reviewing `2026-06-27-mining-loadout-presets`: **did well** — it shipped a clean Phase-1 slice *and*
folded in a real bugs-first cleanup (the `!gear` command had reimplemented the gear embed + paper-doll
that already lived in the view layer; it extracted `build_gear_command_embed` to the view layer,
dropping the cog 842→787 LOC). That "the feature exposed a duplication, so I removed the duplication at
its root" instinct is exactly the discipline the workflow wants. **Could improve / system note:** its
Q-0089 idea (fishing-specific gear stats) turned out to **already be shipped** (#1504) — the run
proposed it as "the natural next slice" without grepping that `fishing_power`/`bite_luck` were already
in `equipment.py`. Minor (it was a forward idea, not built), but it shows the Q-0089 dedup-grep step
can slip. **System improvement surfaced:** the Q-0089 ender already *says* "dedup-grep `docs/ideas/` +
the roadmap first" — but a forward idea can also already be *built in source* (not just captured as an
idea). A cheap guard: the idea-capture step should grep the **source tree** for the proposed
symbol/feature, not only the ideas index — which is exactly what this run did at orient time (grepping
`fishing_power` before picking work), and it immediately revealed the idea was done.

## 📤 Run report

- **Did:** closed the trapped-view dead-end gap in both competitive PvP games (Deathmatch + RPS) +
  root-fixed a latent panel-PvP crash · **Outcome:** shipped
- **Shipped:** #1527 — Deathmatch `_PvpDuelResultView` (Help/Games nav + Rematch) on every PvP
  terminal + BUG-0028 panel-PvP `ctx=None` crash root fix; RPS `_RpsPvpResultView` (◀ Back to RPS) +
  rules "Timeouts & forfeits" field; 11 new tests; both completion certs advanced toward ✔
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none (no migration; live on the next auto-deploy)
- **⚑ Self-initiated:** the two PvP dead-end fixes + the BUG-0028 root fix were picked off the
  completion-first thread with no dispatch/owner ask (Q-0172, completion-first deepening per Q-0209)
- **↪ Next:** continue completion-first — the next high-value offline gaps are Blackjack punch-list #1
  (split/insurance/surrender — bigger engine work, owner-paced) and the unassessed `▢` units (Mining,
  Creatures, Casino, and the server-fn families). A cheap win: build the "no-dead-end" arch checker
  (Q-0089 idea above) so this bug class is caught automatically instead of per-assessment.

## Doc audit (Q-0104)

`check_quality.py --full` green · `check_architecture --mode strict` 0 errors · `check_consistency`
clean. Updated both completion certs (deathmatch.md, rps_tournament.md), added BUG-0028 to the bug
book, and refreshed the S1 sector recently-shipped list. No owner decision this run → router
untouched. Completion scoreboard counts unchanged (both units stay `◐ assessed` — certification needs
the owner walkthrough), so no `completion_scoreboard.py` regen needed.

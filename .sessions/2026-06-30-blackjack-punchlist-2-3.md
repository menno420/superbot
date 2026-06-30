# Session — Blackjack completion-cert punch-list #2 + #3

> **Status:** `complete`

**Run type:** routine · dispatch

## What I did + why
Empty-fire dispatch run. The standing offline ▶ Next (Q-0209) is to clear the `◐ assessed` completion
certs' punch-lists. The **Blackjack** cert
(`docs/planning/feature-completion/units/blackjack.md`) named a focused, offline-buildable set; closed
the two offline items end-to-end in **PR #1565**:

1. **Punch #2 — PvP bet selector in the panel.** The panel's "Challenge Player" flow hardcoded
   `bet = 0  # PvP bet picker deferred to a future PR` in `_BlackjackOpponentSelect.callback`, so PvP
   stakes were reachable only via the `!bj @player <bet>` command. The opponent select now validates
   the target (self/bot rejected up-front, same copy as the challenge builder) then routes into a new
   **`_BlackjackChallengeBetView`** stake picker — **Free play + 10/25/50/100 + Custom** — mirroring the
   Solo Bet UX. A shared `_spawn_pvp(interaction, opponent, bet)` builds the challenge with the chosen
   stake (preset buttons and a `_BlackjackChallengeCustomBetModal` both funnel through it).
2. **Punch #3 — edge tests.** Added the three named-but-untested lifecycle paths:
   **tournament-timeout forfeit** (`_TournBlackjackView.on_timeout` — bet deducted, round consumed,
   controls disabled, advance-vs-finish branch on chips/rounds exhaustion), **guild-removal cleanup**
   (`BlackjackCog.on_guild_remove` — tournament rows refund-and-clear, solo/PvP clear-no-refund, escrow
   recovery; plus a refund-failure-doesn't-abort case), and **natural-blackjack auto-payout**
   (`start_solo_blackjack` — 1.5× bet / flat free-win, `view=None`, active slot released).

**Tests:** `tests/unit/cogs/test_blackjack_edge_cases.py` (7) + `tests/unit/views/test_blackjack_panel_pvp_bet.py`
(5). Each pins behaviour that fails against the pre-fix code (the bet-selector tests assert the chosen
stake reaches `build_blackjack_challenge_view`, not 0).

**Verification:** `check_quality.py --full` GREEN (black/isort/ruff/docs/consistency + `mypy disbot/`
clean + full pytest **13121 passed / 48 skipped / 2 xfailed**); `check_architecture.py --mode strict`
0 errors (49 pre-existing warnings, none new; the one `blackjack_panel` layer note is the `[known]`
views→cogs.actions tracked violation). CI's only red was the deliberate born-red `check_session_gate`
hold, flipped green as the final step here.

**Docs de-staled (Q-0166):** the Blackjack cert (rubric B/C/G ticks, punch-list #2/#3 ✅, Evidence,
Verdict) and `docs/current-state/S1-bot.md` (two Blackjack pointers — the completion-deepening bullet
and the games-deepening bullet now record #1565 and narrow the remaining Blackjack work to the
owner-paced #1).

Method note (Q-0120): verified the natural-payout / guild-remove / timeout-forfeit branches against
live source before writing the tests, and confirmed `cogs.blackjack_cog.game_state_service` resolves to
`services.game_state_service` (two imports bind the name; the later `from services import …` wins) so
the `patch.object` targets the right object.

## ⚑ Self-initiated
none — this is dispatched completion-first work (the standing S1 ▶ Next: clear the `◐ assessed` certs'
punch-lists, Q-0209). The split/insurance/surrender engine work (#1) was deliberately **not** built: it
is flagged in the cert as an owner product call (implement-or-waive), and it carries money-safety shape
(split = a second wager, insurance = a side bet) — out of an autonomous run's safe envelope.

## 💡 Session idea
A tiny **`check_consistency` rule: a panel "spawn" callback must not hardcode a wager/stake constant**
(`bet = 0`, `amount = 0`) with a "deferred to a future PR" comment — i.e. flag a literal-zero stake
passed into a `build_*_challenge`/`*_wager`/escrow call. This exact pattern (`bet = 0  # PvP bet picker
deferred`) is how the Blackjack PvP panel silently shipped a stakes-less path that looked complete in
the UI but wasn't — the same "looks done, isn't" class the feature-completion system exists to catch,
but cheaper to catch in CI than in a per-unit assessment months later. (Captured, not built — it needs a
small allowlist for genuinely free-play surfaces like Solo Free Play, so it's a curation pass, not a
one-liner.)

## ⟲ Previous-session review
The previous run (#1550, Proof Channel punch #1 + #2) was strong and well-scoped — it closed an audit-trail
gap and a modal-authority gap with 9 targeted tests, and it modeled the audit-emit pattern on an existing
service rather than inventing one. One thing it surfaced but left for "later": its own `💡 Session idea`
(an AST/consistency guard that "a Discord-side state mutation must emit `audit.action_recorded` or be
allowlisted"). That idea and *this* session's idea are the **same shape** — "a feature written against the
raw API skips the audited/parameterized seam, caught only by per-unit assessment." **System improvement
this surfaces:** these per-session `💡` ideas keep landing in logs and never reaching `docs/ideas/` unless
a later session happens to re-derive them — the grooming pass moves *existing* idea files, but a `💡` line
buried in a `.sessions/` log isn't an idea file. Worth a cheap convention (or a Stop-hook nudge): a `💡`
that's a concrete build proposal should be promoted to a one-paragraph `docs/ideas/` stub in the same
session, not left as prose only a grep will find. (Noting here, not acting — it's a workflow-rule change,
so it belongs in the router, not a self-edit.)

## ✅ Doc audit (Q-0104)
- `check_current_state_ledger.py --strict` — green at session start (Ledger: in sync ✓); this PR adds no
  merged-PR rows (the #1565 row lands when it merges; the reconciliation failsafe / next session records it).
- `check_docs --strict` + `check_consistency` — green (run under `check_quality --check-only`).
- New owner decisions: none. No router Q added.
- Nothing captured only in chat — the cert + S1-bot.md carry the durable record.

## 📤 Run report

- **Did:** Cleared the two offline Blackjack completion-cert punch-list items (PvP panel stake picker + 3 edge-path test groups) · **Outcome:** shipped
- **Shipped:** #1565 — Blackjack PvP panel bet selector (cert #2) + tournament-timeout/guild-remove/natural-payout edge tests (cert #3); cert + S1-bot.md de-staled
- **Run type:** `routine · dispatch` (Q-0165)
- **⚑ Owner decisions needed:** Blackjack cert punch-list **#1** — implement-or-waive split / insurance / surrender (the one Blackjack item that needs an owner product call before it can be ticked or waived)
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (Q-0172)
- **↪ Next:** S1 completion-first — Blackjack now needs only owner/live-bot items (#1 product call, #4 walkthrough, #5 sign-off); the next offline `◐ assessed` punch-list to clear is the server-fn batch (see `S1-bot.md` assessments bullet). Standing offline ▶ Next (Q-0209) unchanged.

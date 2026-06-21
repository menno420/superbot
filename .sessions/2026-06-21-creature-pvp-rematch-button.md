# 2026-06-21 — Creature PvP: rematch button (⚑ self-initiated)

> **Status:** `complete` — PR #1262. **⚑ Self-initiated** (Q-0172).

> **Run type:** `routine · dispatch`

## Arc

Second slice of this dispatch run. The first (creature-PvP result-recording + win/loss records +
leaderboard, **PR #1257**) merged. With the dispatched ▶ Next action lane (a) consumed and budget
remaining, I built **one contained captured idea** (Q-0172 self-initiated, "ideas exist to be built"):
a **🔄 Rematch button** on the creature-PvP outcome embed, completing the creature-PvP v1 UX.

## What shipped (PR #1262)

- `views/creature_battle/rematch.py` — `CreatureRematchView(BaseView)`: a **two-participant**
  `interaction_check` (either fighter may click; a third party gets an ephemeral nudge — specialized
  lifecycle, commented, since `public=False` locks to one author and `public=True` opens to the whole
  channel) + one Rematch button that re-issues a fresh `CreatureBattleChallengeView` (clicker =
  challenger, other fighter = opponent, who Accepts/Declines as usual). **No new battle logic** — the
  next battle reuses the existing challenge flow and the #1257 audited result-recording path.
- `challenge.py` attaches the rematch view to the outcome message (`wait=True` so `.message` is set for
  on-timeout disable).
- `__init__.py` exports `CreatureRematchView`.
- idea doc captured first (`docs/ideas/creature-pvp-rematch-button-2026-06-21.md` + README index entry).
- `tests/unit/views/test_creature_rematch.py` — the view has the button; both fighters pass the check;
  a third party is rejected with an ephemeral message.

## Findings / decisions

- **Self-initiation (the decision itself):** with the dispatched lane done and budget left, I built one
  small reversible captured idea rather than stop after one PR (the routine's "never just after one PR").
  Flagged ⚑ self-initiated on the run report + the idea doc + the claim, so it's trivially reviewable.
  Kept it to a single increment (no new arc).
- **Decision made alone — one-click rematch, not mutual-consent.** A single click re-issues a *challenge*
  (which the other fighter then Accepts/Declines) rather than requiring both to opt in up front — the
  existing Accept/Decline step IS the agreement, so a second gate would be redundant friction.
- **Decision made alone — two-participant view.** `BaseView` is single-author; I widened
  `interaction_check` to the two fighters rather than inventing a new base class (the rps/deathmatch
  game-view precedent for specialized lifecycle, documented in a comment).

## Context delta

- **Needed but not pointed to:** nothing new — `views/rps/solo_play.py`'s `🔁 Play again` button was the
  shape precedent, and `CreatureBattleChallengeView` (#1230) did all the heavy lifting on re-issue.
- **Discovered by hand:** (1) `interaction.followup.send(...)` is typed to return `None` unless
  `wait=True` — mypy `func-returns-value` when you assign the result to `.message`; pass `wait=True`.
  (2) a late `from ... import CreatureBattleChallengeView` inside the callback breaks the
  challenge↔rematch import cycle (the rps late-import precedent). (3) a new `docs/ideas/` file must be
  badged `ideas` and linked from the README or `check_docs` flags it as an orphan.
- **Decisions made alone:** see Findings (self-initiation; one-click rematch; two-participant view).
- **Weak point / unverified:** not live-walked — the rematch round-trip (click → new challenge → accept →
  resolve → record) wants a runtime smoke on a real guild with two collections + Postgres. The
  interaction lifecycle is offline-tested only at the construction/`interaction_check` level (no live
  Discord here).

## 📤 Run report

- **Did:** built a 🔄 Rematch button on the creature-PvP outcome embed (either fighter re-challenges in
  one tap) · **Outcome:** shipped (PR #1262, full CI mirror green, auto-merge armed by owner)
- **Shipped:** #1262 — creature PvP rematch button
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none — but this was **self-initiated**; if you'd rather not have a
  rematch button (or want it mutual-consent), it's a small one-file revert.
- **⚑ Owner manual steps:** none — merge auto-deploys; no migration/data step (view-only).
- **⚑ Self-initiated:** **YES** — the rematch button (captured idea, built under Q-0172). The earlier
  slice this run (#1257) was the *dispatched* lane (a), not self-initiated.
- **↪ Next:** creature-game PvP v1 is now feature-complete (catch · dex · battle · records · leaderboard ·
  rematch). Remaining creature slices are later/gated (Explore-hub Lane-B battle panel · balance/art
  Q-0187). Next ungated build = ▶ Next action lane (b) botsite React-SPA migration, (c) a
  `needs-hermes-review` lane, or (d) a fresh idea (Q-0172).

## 💡 Session idea

**A `!cbattle` AFK/timeout forfeit nudge.** The challenge view times out after 60s with no explicit
"challenge expired" message (it just disables silently on timeout). A one-line `on_timeout` edit —
"⌛ {opponent} didn't respond — challenge expired" — would close the loop the way the deathmatch
challenge does (BUG-0013's domain), so a hanging challenge reads as resolved rather than dead. Cheap,
pure-view, and improves the same PvP UX. (Dedup-checked `docs/ideas/` — not captured.)

## ⟲ Previous-session review

This run's *own* first slice (#1257) was solid but its handoff under-weighted one thing: it declared
creature PvP "buildable-complete for v1" while the outcome embed still had no replay affordance — a gap
a player feels immediately. The fix was this very slice, which is the system working as intended (the
"don't stop after one PR" rule caught it). **System improvement:** "buildable-complete" claims in the
▶ Next action would be more trustworthy if they enumerated the *user-facing* loop (catch → battle →
**replay**) rather than the *backend* surfaces (migration/service/command) — a feature can be
backend-complete and still feel unfinished. Worth a one-line convention in the reconciliation prompt:
when marking a game lane "complete," sanity-check the *player's* loop, not just the data/service seams.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this run | 2 (#1257 merged · #1262 auto-merge on green) |
| CI-red rounds (this slice) | 1 real (mypy `func-returns-value` + COM812 + doc orphan — all fixed; born-red HOLD otherwise) |
| Self-caught pre-push | `followup.send` wait-flag · import-cycle late-import · idea-doc badge/orphan |
| New ideas contributed | 1 (challenge-expired timeout nudge) |
| Ideas groomed | 1 (built the captured rematch-button idea) |

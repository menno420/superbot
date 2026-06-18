# 2026-06-18 — BTD6 AI answer fixes (owner live-test screenshots)

> **Status:** `complete`
> Owner-live session. Fixed 4 BTD6 AI answer bugs the owner spotted in #general screenshots.

**PR:** #1035 — BTD6 answer wording/grounding fixes.
**Branch:** `claude/zen-wright-77q0ru`

## What I'm about to do / did

The owner posted #general screenshots of SuperBot answering BTD6 questions and flagged
"some BTD6 related AI bugs, mostly just some wording fixes." Traced each to source; owner
confirmed all four in scope. All fixes are at the deterministic data/grounding/tool layer
(give the model correct, quotable facts — never try to steer prose directly).

1. **MK reference reply — grammar + tab-wide scope note**
   (`btd6_context_service.deterministic_mk_reference_reply`). Header
   "Monkey Knowledge **that reference**" → "Monkey Knowledge **points that reference**", and
   added a note that tab-wide points in the tower's category tab (Primary/Military/…) — e.g.
   *Come On Everybody*, *Flanking Maneuvers* — also apply but aren't listed because they don't
   *name* the tower. Fixes the on-screen "why isn't Come On Everybody in the Glue Gunner list"
   / "missed flanking maneuvers" confusion. Note added to the empty case too.

2. **"How many bloons spawn on rN" refused while "list every bloon" answered**
   (`_render_fixture_round` + `round_composition`). The round grounding had no total-bloon
   number, so the model's derived sum (75+122=197) tripped the value-only faithfulness guard →
   refusal, while the per-bloon list answered fine. Now the entering-bloon total is grounded
   (`bloons enter this round in total`; tool fields `bloons_entering` / `total_bloons_entering`).

3. **ABR vs standard RBE read as self-contradiction** (14,820 ABR vs 14,413 standard for r63).
   `round_composition` now returns `roundset_label` ("standard" / "alternate (ABR)") and the
   tool description tells the model to label every round figure with its set.

4. **Income range explanation didn't add up** (the model subtracted cumulative AT the start
   round, dropping that round's earnings, and quoted figures that didn't match range_cash).
   `round_cash` now returns a ready-to-quote `identity` sentence built from the inclusive
   endpoints; the tool description tells the model to quote it verbatim and never re-derive.

Also reconciled the living ledger: added #1030/#1031/#1032 to current-state Recently-shipped
(newest-merge lag the SessionStart flagged).

## Verification

- `python3.10 scripts/check_quality.py --full` → green (10489 passed, 38 skipped).
- `python3.10 scripts/check_architecture.py --mode strict` → 0 errors.
- New/updated tests: `test_btd6_mk_reference` (grammar + tab note), `test_btd6_round_cash`
  (identity), `test_btd6_abr_rounds` (roundset_label + total bloons), `test_btd6_context_tower_stats`
  (entering total grounded).

## 💡 Session idea

**Idea:** a small "guard-rejected a derivable total" eval/regression class — feed the BTD6 path a
"how many X in total" question for several grounded compositions and assert it answers (no
no-data refusal). **Why:** bug #2's root cause (the value-only faithfulness guard refusing a
legitimately-summable total) is a *recurring shape*, not a one-off; an eval that pins "totals the
user can reasonably ask for are grounded" would catch the next instance before a screenshot does.

## ⟲ Previous-session review

The previous session (#1032) did well to **verify Codex's flags against source before acting**
(the Q-0120 "cross-agent output is input, not orders" discipline) and to fix only the 3 it
confirmed real. What it (and the whole BTD6-floor lane) could improve: the lane kept adding new
*deterministic floor builders* but these four bugs are all **grounding/guard** issues on the
*model* path — the part the floors don't cover. Surfaced improvement (captured as the session
idea): the faithfulness guard's value-only check refuses legitimately-derived totals, and that
class deserves an eval rather than a per-screenshot fix.

## 📤 Run report

- **Did:** fixed 4 owner-spotted BTD6 answer bugs (MK scope wording · how-many-bloons refusal ·
  ABR/standard labeling · income identity) at the data/grounding/tool layer + ledger reconcile ·
  **Outcome:** shipped, CI green
- **Run type:** manual (owner-live)
- **⚑ Self-initiated:** none (owner-requested fixes); ledger reconcile is on-sight drift fix
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none (no data reseed; all changes are code/grounding)
- **↪ Next:** consider the "derivable-total grounded" eval (session idea) if the guard-refusal
  shape recurs

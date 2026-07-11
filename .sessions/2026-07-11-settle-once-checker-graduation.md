# 2026-07-11 — settle-once checker: activate inert cogs/ scope + graduate to error

> **Status:** `complete`

📊 Model: Opus 4.8 · owner-directed follow-up (bugs-first fix from the fleet review)

## What this fixes

A verified **money-safety false-green** in `scripts/check_consistency.py` Rule 6
(`settle_once_adoption`), surfaced by the idea-engine probe + the 2026-07-11 fleet
review and confirmed against source:

1. **Inert scope.** The rule function defaults to `roots=("views/","services/","cogs/")`
   and its docstring documents the 2026-07-07 `cogs/` widening (the live-confirmed
   deathmatch W/L write, Gate-V Arm D) — but the **registry `Rule(...)` entry still
   passed `roots=("views/","services/")`**, so the `cogs/` default never flowed. A new
   unguarded cog-layer settle site (`payout_tournament` / `update_leaderboard`) would
   ship **unscanned**.
2. **Warn-only.** `severity="warning"`, so `--mode strict` (which fails on `error`
   only) never reddened CI on it.

## Change

- Registry `roots` → `("views/","services/","cogs/")` (matches the function default +
  docstring). Verified the rule now scans the 3 cog sites — `rps_tournament_cog`
  `payout_tournament` + both `_DuelView` deathmatch `update_leaderboard` writes — and
  all are **AST-verified guarded** (SettleOnceMixin/claim_settlement), so the tree is clean.
- `severity` **graduated `"warning"`→`"error"`**: soaked clean since 2026-06-25 and now
  clean across all three layers, so the money-safety guard becomes **enforced** — a future
  unguarded settle site fails `--mode strict` (and thus code-quality) instead of shipping.
- Tests: updated `test_rule_6_is_registered_and_scoped` (pinned the buggy scope) +
  `test_settle_once_rule_runs_clean_on_the_live_tree` to the corrected scope/severity, and
  added `test_settle_rule_scans_cogs_layer` (proves an unguarded cog settle IS flagged).
  69/69 pass; `check_consistency --mode strict` clean; `check_quality --check-only` green.

Reversible: flip `severity` back to `"warning"` (Q-0105 disposable-rule header).

## 💡 Session idea (Q-0089)

**A registry-vs-function-default drift guard for the checker rules.** This bug existed
because a `Rule(...)` registry entry silently overrode a *wider* function default
(`roots`), so a documented widening was inert with no signal. A tiny meta-test that asserts
each rule's registry `roots` is a **superset of** (or equal to) any scope the rule's own
docstring/body claims — or simplest: that no registry `roots` is narrower than the function
default — would have caught this at the commit that introduced it. Cheap, and it hardens the
"enforce, don't exhort" checker layer against its own config drift.

## ⟲ Previous-session review (Q-0102)

The prior session (this same branch's fleet review) did the right thing routing this as a
"verify+fix" item to the superbot Codex prompt rather than blind-fixing it — because flipping
a checker to `error` risks reddening pre-existing sites. This session vindicated that
caution: the cogs/ sites turned out **already guarded**, so the graduation was safe, but that
was only knowable by running it. Improvement carried: the session-idea meta-test would let a
future agent trust a scope-widening landed live instead of re-deriving it by hand.

## Documentation audit (Q-0104)

Docs-adjacent only (a checker + its test). No ledger/owner-decision changes. Telemetry row
appended (Q-0194). Claim deleted at close.

## 📤 Run report

- **Did:** activated the inert cogs/ scope + graduated the settle-once money-safety rule to
  an enforced gate; updated/added tests · **Outcome:** shipped (69 tests green, strict clean)
- **Run type:** `owner-directed` (bugs-first fix from the fleet review, owner said "fix what you can")
- **⚑ Self-initiated:** the severity graduation (decide-and-flag, Q-0240) — reversible; the
  scope fix was a direct correction of a documented-but-inert widening
- **↪ Next:** delegated bigger fixes (superbot-next money races, substrate-kit gate, fleet
  centralization) via the dispatch kit

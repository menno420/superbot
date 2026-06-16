# 2026-06-16 — BTD6 hero cost-comparison floor (night-queue slot 1)

> **Status:** `complete`

## What this session did
Scheduled dispatch, empty work order → the live ▶ Next action pointed at the
**night queue** (`planning/night-queue-2026-06-16.md`). Built the topmost `TODO`
slice: **Slot 1 — Hero cost comparison (§7.5)**. PR **#1000**.

A deterministic floor builder that ranks the base placement cost of two-or-more
heroes ("is Quincy or Benjamin cheaper?") — the BUG-0009 "grounded values, wrong
assembly" class on the hero entity. Mirrors #962 (paragon comparison) almost
exactly.

- `btd6_data_service.compare_hero_costs(names, *, difficulty="medium")` —
  resolve each hero via the shared `_find_by_surface` resolver, dedup on id,
  difficulty-scale the stored Medium `base_cost` (the same `difficulty_costs`
  multipliers towers/paragons use), rank ascending, fail closed on <2 distinct.
- `btd6_context_service.deterministic_hero_cost_comparison_reply` +
  `_extract_hero_names` / `_format_hero_cost_comparison` — fires on a
  cost-compare cue + ≥2 resolved heroes; defers on a `paragon` cue, strategy
  cues, and single-hero lookups. Registered in `_BTD6_LIST_BUILDERS` before the
  tower cost builders (mutually exclusive by construction — they need a
  `(tower, crosspath)` candidate a hero name never yields).
- Tests: `tests/unit/services/test_btd6_hero_cost_comparison.py` (19 cases:
  primitive ranking/aliases/tie/dedup/difficulty/fail-closed → reply
  fire/defer → dispatcher + one-fires) + one `_SHOULD_FIRE` corpus phrase in
  `test_btd6_floor_builder_exclusivity.py`.

Verification: `check_quality --full` green (10262 passed, +40); `check_architecture
--mode strict` 0 errors; mypy clean; `check_docs --strict` green. Ships under
Q-0048 (read-only deterministic floor, no prod-check; auto-deploys on merge).

Docs: ticked slot 1 `✅ #1000` in the night queue; re-pointed ▶ Next action /
NIGHT QUEUE to slot 2 (power activated-ability cost comparison); added the
Recently-shipped ledger line and archived the oldest live entry (#912) to hold
the 20-ratchet.

## ▶ Next action (handoff)
The next scheduled dispatch fire (empty work order) builds **slot 2 — Power
(activated-ability) cost comparison** (`planning/night-queue-2026-06-16.md`):
`btd6_data_service.compare_power_costs(names)` over `powers.json` →
`monkey_money_cost`, + `deterministic_power_cost_comparison_reply`, same shape
as this slice (axis = monkey-money cost, not dollars). Mirror this PR (#1000) /
#962. Then slots 3–5 (relic / bloon-property / hero-ability rosters).

## ⚠ Ledger drift noted (not fixed here — recon's lane)
`check_current_state_ledger --strict` flags **7 merged PRs not in current-state**
(#990, #991, #993, #994, #995, #996, #997 — dashboard/control-api band from other
sessions). It is **not** a CI gate (only `check_docs` + `check_session_gate`
gate code-quality), so it does not block this PR. Reconciliation is **DUE**
(merged PRs crossed #960; last pass #930) and auto-fires via the `reconcile`-issue
trigger → the docs-reconciliation routine owns this drift. Per Q-0124 a dispatch
session does not run the full recon pass itself.

## 💡 Session idea (Q-0089)
**A `night-queue lint` check** (`scripts/check_night_queue.py`, stdlib, disposable
per Q-0105): assert every `✅ #NNN` slice in `night-queue-2026-06-16.md` names a
builder that is actually registered in `_BTD6_LIST_BUILDERS`, and every `TODO`
slice's named data field exists in its cited `disbot/data/btd6/*.json`. Today the
queue's "data-complete today" claim is hand-verified each fire (I confirmed
`heroes.json:base_cost` by hand); a 30-line guard would make the queue's grounding
machine-checked so a fire never starts a slice whose data field has been renamed
out from under it. Genuinely useful and small — fits the proven night-queue
factory pattern. (Not built this session — captured for grooming / a fast fire.)

## ⟲ Previous-session review (Q-0102)
The previous fire (#975, AI §7.6 roster floors) was exemplary at the *pattern* it
ran: two roster members in one PR, exclusivity corpus extended for both, clean
Q-0048 framing. One thing it could have done better — and which this session
inherited — is that the **night-queue rows it didn't touch were left `TODO`
without a freshness note**, so each new fire re-derives "is this slot still
data-complete?" from scratch. The system improvement that surfaces:
**machine-check the queue's grounding** (the session idea above) so the
queue's central promise ("each slice reads a field already in a committed JSON")
is verified, not re-asserted in prose every 2 hours. The night-queue factory
pattern is working well — five clean fires (#946→#975→#1000) — which is itself
the signal that its *one* manual step (data-field verification) is worth
automating.

# Session — BUG-0009 slice 1: deterministic "Monkey Knowledge related to X" builder

> **Status:** `complete`

## What I did

Dispatch run with an empty/stale work order → took the next real plan slice. Per
`current-state.md` ▶ Next action the next ▶ startable item was **plan-first BUG-0009** (band-#900
decade queue slot 6) — the OPEN AI list-assembly bug: "what are all the monkey knowledges related
to the farm" listed the whole 22-entry Support MK *category* and labelled it farm-related (Big
Traps / One More Spike / Vigilant Sentries are Engineer / Spike Factory). Root cause: the
faithfulness guard checks **values, not claims** — every MK name is grounded, but the
*grouping/labeling* is model-assembled, and this class **passes** the value guard so the existing
post-hoc roster floor never fires for it.

Shipped the **first** of BUG-0009's three list families — the **"MK related to <tower>"** builder —
following the proven fix shape (the deterministic layer OWNS the labelled answer, like rosters /
capabilities). I verified feasibility against the data before committing to the approach: the MK↔
tower relation lives only in the description free-text ("Cryo Cannon …", "Monkey Banks …"), so I
derive it by matching the description against a tower's canonical name + upgrade-path names (strong)
and aliases (weak), with two suppression rules that I measured to remove all observed false
positives.

## What shipped (PR #924)

- **`btd6_data_service.monkey_knowledge_referencing(tower)`** — the pure relation. Strong term =
  the tower's canonical name or an upgrade-path name (multi-word, unique); weak term = an alias.
  A weak hit is kept only when (a) the MK does not *strongly* reference a different tower
  ("Arcane Spike does …" → Wizard, not Spike Factory) and (b) the MK is not a Powers/Heroes-tab
  point (the Road Spikes power's "Just One More" must not attach to the Spike Factory). Plural-
  tolerant whole-word matching ("Monkey Bank" matches "Monkey Banks"). Memoized per dataset
  version (the `(data_version, game_version, id(dataset))` key the name-index uses).
- **`btd6_context_service.deterministic_mk_reference_reply(text)`** — detects the "which MK relate
  to <tower>" shape (MK cue + relation/list cue + resolvable tower via `_scan_tower`), returns
  `None` for single-MK lookups / strategy / no-tower, and formats the honest labelled reply
  ("…that reference the Banana Farm (7) — these name the Banana Farm or one of its upgrades"). An
  honest "no MK references the X" for a tower with an empty relation.
- **Pre-emptive floor** on the BTD6 path in `natural_language_stage.process` (modeled on the
  existing video short-circuit) — fires *before* the model, since this class passes the value
  guard so a post-hoc floor can't catch it. Skips the model call entirely; audits `replied`.
- **Tests (+14):** `tests/unit/services/test_btd6_mk_reference.py` (relation + reply: farm =
  the 7 genuinely-referencing MK not 22, road-spike Powers excluded, strong-beats-alias,
  conservatism, honest empty) · `test_mk_reference_question_floored_before_model` +
  `test_non_mk_btd6_question_still_reaches_model` (the short-circuit + that ordinary BTD6
  questions still reach the model).
- **Verified:** `check_quality.py --full` green (9863 passed) · `check_architecture --mode
  strict` 0 errors · `check_docs --strict` ✓. Farm → 7 (Backroom Deals, Bank Deposits, Bigger
  Banks, Farm Subsidy, Flat Pack Buildings, Healthy Bananas, More Valuable Bananas); Spike
  Factory → 4 (road-spike Powers correctly excluded).
- Bug-book BUG-0009 → **PARTIALLY FIXED** (MK family); current-state ▶ Next action + Recently
  shipped updated.

## Handoff / next

- **BUG-0009 slices 2-3 remain OPEN** (same proven shape: deterministic builder → pre-emptive
  floor): **per-level item lists** (Geraldo per-level groupings — a different data domain, the
  Geraldo crafting items) and **newest-towers ordering** (needs a tower release-order signal;
  check whether `towers.json` carries one before building). Both are good next ▶ startable slices
  in the band-#900 queue slot 6. Then security service tiers 1+2 (slot 9, plan-first).
- **The pre-emptive-floor wiring will be duplicated** by slices 2-3 — see the session idea below
  for the seam that would collapse it.
- ⚠ **Pre-existing ledger drift (NOT mine):** `check_current_state_ledger --strict` reports 9
  merged PRs absent from the ledger (#907, #908, #909, #913–#916, #919, #921 — mostly the
  brave-sagan batch), present on origin/main at session start. This is not a CI gate
  (`code-quality.yml` runs `check_docs`/`check_session_gate`/`check_quality`, not the ledger
  check), so it doesn't block merges, but the **band-#930 reconciliation pass** (due in ~9 PRs,
  Q-0124 = the reconciliation routine's job, not dispatch's) should sweep them. I did not bulk-add
  them — adding 9 other sessions' entries without their context risks misattribution.
- The Recently-shipped soft ratchet is now 21/20 (+1, my entry) — the #930 recon trims it.

## 💡 Session idea (Q-0089)

**A deterministic-answer floor registry for the BTD6 path.** Today each deterministic-list family
is a bespoke `(detector, builder)` pair *plus* bespoke wiring in `natural_language_stage`: rosters
+ meta live in the post-hoc `_serve_btd6_floor`, round-cash is a system-block in `_invoke_gateway`,
and this PR added a *third* wiring site (the pre-emptive MK floor). BUG-0009 slices 2-3 will each
add a fourth and fifth. A tiny ordered registry — `register_btd6_floor(detector, builder, *,
preemptive: bool)` consumed once on the BTD6 path — would make adding family N+1 a one-line
registration in `btd6_context_service`, not new stage code, and would put all the "which questions
the deterministic layer owns" logic in one auditable list. It directly de-risks the remaining
BUG-0009 slices (the whole point is "the deterministic layer owns the labelled answer" — the
*registry* is the seam that makes that cheap to extend). Small, reversible, test-coverable.

## ⟲ Previous-session review (Q-0102)

Previous log: `2026-06-15-hermes-sync-hardening.md` — hardened the Hermes clone sync after a live
VPS run hit a diverged-clone `--ff-only` abort. **Did well:** it fixed the *root* (replaced the
fragile `git pull --ff-only` with the self-healing `git fetch && git checkout -B main origin/main`
— the exact pattern this dispatch routine uses in step 1) rather than just documenting a manual
recovery, and it watched the SOUL byte budget while doing it. **Could improve / the system
improvement it surfaces:** it flagged the operating prompt is at 82% of its 8000-byte budget and
that "every future rule fights the truncation ceiling" — but left that as a note. That's the same
class as *this* session's idea: a load-bearing artifact (the SOUL prompt there; the floor wiring
here) accreting bespoke additions until it strains. The workflow improvement: when a session
notices an artifact crossing ~80% of a hard budget, it should **open a concrete trim/refactor
plan in `docs/ideas/` (or do it)**, not just note the percentage — a noted-but-unactioned ceiling
is the drift the self-auditing loop exists to catch. (No filler: this is a real, recurring
pattern, not a manufactured remark.)

## 🔎 Doc audit (Q-0104)

- `check_current_state_ledger --strict`: reports the **pre-existing** 9-PR drift above (not from
  this session; flagged for the #930 reconciliation). My own work IS in the ledger (#924 entry).
- `check_docs --strict`: ✓ (Recently-shipped soft-over-ratchet warning only).
- Owner decisions this session: none new (dispatched plan-slice work, no Q-block).
- New code reachable: bug-book BUG-0009 updated to PARTIALLY FIXED with the fix + tests recorded;
  current-state ▶ Next action + Recently shipped updated; this log written.

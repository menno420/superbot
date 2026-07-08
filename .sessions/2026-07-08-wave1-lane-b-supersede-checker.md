# Session — Wave-1 lane B: supersede-banner integrity checker

> **Status:** `complete`
> **Run type:** owner-directed campaign · EXECUTE lane (Wave-1 lane B)
> Branch: `claude/wave1-lane-b-supersede-checker` · PR **#1846**.

## What this session did

Shipped the decided-lane idea
[`docs/ideas/supersede-banner-integrity-checker-2026-07-06.md`](../docs/ideas/supersede-banner-integrity-checker-2026-07-06.md)
end-to-end (docs/tooling only, no `disbot/` changes):

- **`scripts/check_supersede_integrity.py`** (new, warn-first, Q-0105 provenance header) — for
  every header-block `SUPERSEDED` banner: the named successor resolves (phantom-successor class),
  a successor references the doc back (one-sided-handshake class), a *fully* superseded doc no
  longer carries a live `plan` badge (dead-plan class); reverse pass: supersede-marked
  disposition-table rows under a "Superseded…" heading must point at stamped docs. Header-block
  scoping keeps mid-doc/section-level supersedes (e.g. `docs/btd6/`) out of scope;
  `SUPERSEDED-IN-PART` may keep its `plan` badge. Default exit 0; `--strict` is the promotion path.
- **`scripts/check_docs.py`** — new failure-tolerant **supersede-integrity soft check** (same
  posture as the inventory-count report) so findings surface on every session-close
  `check_docs` run without reddening the load-bearing gate.
- **`tests/unit/scripts/test_check_supersede_integrity.py`** — 16 tests: each drift class, each
  low-FP scoping rule, the `check_docs` wiring, and a real-tree smoke (deliberately non-blocking
  on findings while the guard is unverified; the promotion note is in the test).
- **Idea lifecycle:** idea file re-badged `historical` ✅ IMPLEMENTED; `docs/ideas/README.md`
  index annotated.
- **Drift fix on sight (Q-0166):** homed `docs/planning/per-repo-settings-state-ledger-2026-07-08.md`
  in the planning README index — it landed unindexed in #1843 and turned
  `test_check_plan_homing::test_live_repo_plans_are_all_homed` red for every branch cut from main.

Ground truth at ship time: the checker detects 6 header-banner docs + 5 disposition rows across
`docs/`, zero findings (verified detection is real, not vacuous — Q-0120).

## Verification

- `python3.10 scripts/check_quality.py --full` ✓ (14,251 passed / 49 skipped / 2 xfailed)
- `python3.10 scripts/check_architecture.py --mode strict` ✓ (exit 0)
- `python3.10 scripts/check_docs.py --strict` ✓ · `check_current_state_ledger.py --strict` ✓
- Recently-shipped ledger deliberately untouched: merged-PRs-only convention — #1846 lands there
  via the next reconciliation pass (benign newest-merge lag).

## ⚑ Self-initiated

- The `check_docs.py` soft-check delegation (the idea named standalone-or-`check_docs`; chose both —
  standalone for `--strict` promotion, soft check so warnings are actually *seen* each session).
- The #1843 plan-homing drift fix (unblocking CI for every branch, incl. this one).

## 💡 Session idea (Q-0089)

**Culprit-attribution for live-tree ground-truth tests.** Several unit tests assert *repo-tree
state* (e.g. `test_live_repo_plans_are_all_homed`): when a PR lands drift anyway (as #1843 did),
the red lands on every *innocent* later branch, which pays the diagnosis cost while the culprit
session is long gone (this session paid it). Idea: (a) run the live-tree ground-truth checkers
(`check_plan_homing --strict` et al.) as a named, fast, separate step in `code-quality` so the
*introducing* PR sees the failure attributed by name, and (b) a post-merge main-branch run that
auto-opens a fix issue naming the culprit commit when red reaches main regardless. Dedup-checked:
`plan-homing-guard-2026-06-19` built the checker/test; this is about *failure attribution* for the
whole class, not any one checker. (Not filed as an idea doc by me — campaign rails route follow-ons
to Wave-2 grooming; this flag line is the capture.)

## ⟲ Previous-session review (Q-0102)

Previous session (2026-07-08 forward-only + settings-ledger capture, PR #1843): good, fast
owner-directed capture with clean indexing of both artifacts and an honest correction of the
"first push" claim. Miss: it verified with `check_docs --strict` only — but adding a `plan`-badged
doc is exactly what `check_plan_homing`'s live-tree pytest guards, and the doc landed unindexed in
the planning README, reddening the full suite for every later branch. Concrete workflow
improvement: a docs-capture session that *adds* a `plan` doc should run
`python3.10 scripts/check_plan_homing.py --strict` (seconds) before pushing — or the homing check
should join `check_docs`' soft checks so session-close surfaces it (see 💡 above for the
enforcing version).

## Docs audit (Q-0104)

`check_current_state_ledger.py --strict` ✓ · `check_docs.py --strict` ✓ · new tool has its Q-0105
header · idea routed to its lifecycle end · nothing chat-only left unhomed. Claim file deleted at
close.

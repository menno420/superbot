# 2026-06-19 — Consistency-linter rule graduation (3 ELIGIBLE rules → error + CI)

> **Status:** `complete`

## Arc (what I did)

Routine dispatch, empty fire → next plan slice on the flagship consistency-linter lane
(current-state ▶ Next action option (a)). The three ELIGIBLE rules — `back_button`,
`panel_base_class`, `select_option_truncation` — had run clean (0 findings) across
#1056→#1062 (5–6 sessions), and `check_consistency.py --graduation` confirmed each ELIGIBLE
on the live tree. **Graduated them:** flipped `Rule.severity` `"warning"`→`"error"` and wired
`python3.10 scripts/check_consistency.py --mode strict` into `code-quality.yml` + the
`check_quality.py` local CI mirror, so a future regression that reintroduces a front-truncated
select / a direct-`discord.ui.View` panel / a back-button-less hub now **fails CI** instead of
warning silently. `edit_in_place` stays warn-only — BLOCKED on the AI-nav plan (its 17
`views/ai/` findings are the real bug the rule exists to catch).

## Shipped (#1094)

- **`scripts/check_consistency.py`** — `back_button` / `panel_base_class` /
  `select_option_truncation` `Rule.severity="error"` (graduated). `run_checks` already stamps
  each finding with its rule's severity, so `--mode strict` now exits 1 on any of their findings
  with no per-rule wiring. `--graduation` reads **GRADUATED** for all three; `edit_in_place`
  stays **BLOCKED**. Reversible: flip a `severity` back to `"warning"` (disposable per Q-0105).
- **`.github/workflows/code-quality.yml`** — new "Run consistency linter (graduated rules)" step
  after Ruff, in the deps-installed block (needs PyYAML from requirements.txt), gated on the
  non-docs change flag. `--mode strict` fails CI only on an *error*-severity (graduated) finding.
- **`scripts/check_quality.py`** — `run_check_consistency()` added to the local CI mirror
  (`--check-only` + `--full`), preserving the "green here = green in CI" contract.
- **Tests** — `tests/unit/scripts/test_check_consistency.py`: rewrote
  `test_real_tree_runs_clean_or_warns_only` → `test_real_tree_produces_no_graduated_rule_errors`
  (the new contract: zero error-severity findings on the live tree, mirroring the CI gate) +
  `test_graduated_rules_carry_error_severity` (locks the 3 graduations + keeps `edit_in_place`
  warn-only). 37 consistency tests pass.
- **Docs** — `planning/repo-consistency-linter-plan-2026-06-17.md` graduation section + the
  `current-state.md` ▶ Next action repointed (next = AI-nav PR 1 to clear rule 1, then graduate
  `edit_in_place`; or a fresh lane).

Verify: `python3.10 scripts/check_quality.py --full` → **10668 passed, 38 skipped, all checks
passed** · `check_architecture --mode strict` → exit 0 · `check_consistency.py --graduation` →
3× GRADUATED, 1× BLOCKED.

## Continuation (the handoff)

Next ungated startable on this lane (per current-state ▶ Next action):
1. **AI-nav plan PR 1** ([plan](../planning/ai-panel-inplace-navigation-plan-2026-06-19.md)) to
   start clearing rule 1's 17 `views/ai/` findings — needs a runtime/Q-0086 live-walk session,
   `needs-hermes-review`. Once `edit_in_place` reaches 0, **graduate it** the same way (flip
   `severity` → `"error"`; the CI/local wiring already runs strict, so no further wiring needed).
2. Rule 5+ only as a fresh mechanical-consistency shape surfaces — a candidate is **extending
   rule 4 (`select_option_truncation`) to `disbot/cogs/`** (today it scans only `disbot/views/`).
3. Fresh lanes: procedures→skills Batch 1, owner-review-inbox Phase 1, the small stdlib guards.

## Context delta

- **Pointed to and needed:** the #1062 graduation tracker (`--graduation`) made the readiness
  decision one hop — confirmed all three ELIGIBLE before flipping. The plan doc's graduation
  section named the exact mechanism (flip `severity` + wire strict).
- **Discovered by hand:** the wiring spot — `check_consistency` imports `yaml` (PyYAML), so the
  CI step must live in the deps-installed (`code == 'true'`) block, not the early stdlib-only
  doc-hygiene block. `--mode strict` correctly stays exit-0 while only warn-only `edit_in_place`
  findings exist, so the gate engages on regressions without blocking today's tree.

## ⟲ Previous-session review (Q-0102)

The previous slice (#1062) did exactly the right thing in *building the graduation tracker rather
than graduating the rules immediately* — it deliberately left the soak ("a couple more sessions")
to a later session and made the readiness machine-checkable, which is what let this session flip
the rules with one `--graduation` confirmation instead of re-reading three docs. What it left
slightly implicit: it didn't state *how many* clean sessions counts as enough, so "ready?" was
still a judgment call (resolved here by reading the #1056→#1062 history — 5–6 clean sessions).
**System improvement:** the `--graduation` ELIGIBLE message is static prose ("flip after a couple
more clean sessions") — it can't actually *see* how long a rule has been clean. A cheap upgrade
would be a tiny `graduation-soak.json` the tracker stamps with the first-clean date per rule, so
ELIGIBLE could read "clean since #1056 (6 sessions) — soak satisfied" and remove the last manual
judgment from the flip. Captured as this session's idea below.

## 💡 Session idea (Q-0089)

**A graduation-soak stamp for the consistency tracker.** Today a rule is "ELIGIBLE" the instant
it hits 0 findings, and "stay clean a couple more sessions" is enforced only by an agent's memory
of the lane. Add a small committed `architecture_rules/consistency_soak.json` that
`check_consistency.py --graduation` reads/updates: the first run where a rule reports 0 stamps
`{rule: {first_clean_pr: N, first_clean_date: …}}`; a run with a finding clears it. ELIGIBLE then
reports the soak length ("clean since #1056 — 6 sessions, soak satisfied") and a rule under the
threshold reads NOT-YET-SOAKED instead. This turns the one remaining manual judgment in
graduation ("has it been clean long enough?") into a machine-checked fact — the same instinct as
the tracker itself (#1060), one level deeper. Worth it because graduation will recur for
`edit_in_place` and any future rule. Dedup-checked `docs/ideas/` + the linter plan — not present.

## 📊 Doc audit (Q-0104)

- `check_quality.py --full` → 10668 passed, 38 skipped, all checks passed (formatters / check_docs
  / check_consistency / mypy / pytest).
- `check_architecture --mode strict` → exit 0.
- `check_consistency.py --graduation` → 3× GRADUATED + 1× BLOCKED (matches reality).
- No new owner decisions — graduating a warn-first dev-tool rule is the documented lane mechanism
  (Q-0170 / Q-0105), not an owner gate.
- Recently-shipped: **not** touched — #1094 is in-flight at write time (the ledger is merged-PRs-
  only; the ▶ Next action callout records #1094 per the Q-0052 early-PR-number pattern, and the
  next session / #1080 reconciliation adds the merged entry). The SessionStart "15 merged not yet
  in current-state" lag is the #1080 reconciliation routine's band (#1051–1079, newer than the
  #1050 marker), not in-scope drift for this dispatch run.

## 📤 Run report

- **Did:** graduated the 3 ELIGIBLE consistency-linter rules to CI-enforced errors (flip
  `severity` + wire `--mode strict` into `code-quality.yml` + `check_quality.py`). · **Outcome:**
  shipped, full CI mirror green (10668 passed).
- **Shipped:** #1094 — `check_consistency.py` (3× `severity="error"`) · `code-quality.yml` step ·
  `check_quality.py` mirror · 2 test changes (37 consistency tests pass) · plan-doc +
  current-state updates.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** **YES** — no dispatched order named this slice; it is the next plan step
  (option (a)) on the Q-0170 consistency-linter lane under the Q-0172 idea→build gate. Contained,
  fully test-covered, reversible (revert the `severity` flips + the workflow/`check_quality` steps);
  the new CI gate fires only on a genuine UX-consistency regression.
- **↪ Next:** AI-nav plan PR 1 (runtime/Q-0086 session) to clear rule 1's 17 `views/ai/`
  findings, then graduate `edit_in_place`; or extend rule 4 to `disbot/cogs/`; or a fresh lane.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session | 1 (#1094) |
| Rules graduated | 3 (back_button / panel_base_class / select_option_truncation) |
| Tests changed | 2 (1 rewritten + 1 added; 37 consistency tests pass) |
| Full suite | 10668 passed, 38 skipped |
| CI-red rounds | 1 (born-red session gate by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (graduation-soak stamp) |

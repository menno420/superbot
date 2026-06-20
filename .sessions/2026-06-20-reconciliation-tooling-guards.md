# 2026-06-20 — Reconciliation-tooling guards: band PR status classifier + Recently-shipped trim actuator

> **Status:** `complete`

## Arc

Scheduled dispatch fire, no work order → advance the next ungated plan slice. The band-#1170
reconciliation pass left the cleanly-ungated self-merge subset thin and named a cluster of
disposable stdlib reconciliation-tooling guards as the ungated lane. Verified two of that cluster
were **already shipped** (`check_plan_homing.py` #1174, `check_governance_files.py` #1120) — stale
in the queue. Built the two still-unbuilt, highest-leverage ones, each used **every**
reconciliation pass.

## Shipped (this PR)

- **`scripts/band_pr_status.py`** + `tests/unit/scripts/test_band_pr_status.py` (16 tests) — the
  band PR merge-status classifier. For every PR newer than the reconciliation marker it prints
  **merged / closed-unmerged / open / unknown**, closing the ground-truth gap (Q-0120/Q-0181) the
  routine hits every pass: `check_current_state_ledger.py` finds *missing* merged PRs but can't
  tell a closed-unmerged PR (the #1133 hand-reconstruction) from a genuinely-missing merged one.
  Pure `classify_band()` core; git ground-truth for merged-on-main + the `check_loop_health.py`
  gh→REST provider-seam fallback for the closed/open half (degrades to a labelled note, never
  hard-fails). **Verified against live GitHub** on the band-#1170 band: #1173–#1180 merged, #1172
  open (dependabot), #1171 = the reconcile *issue* (not a PR) — all classified correctly.
- **`scripts/trim_recently_shipped.py`** + `tests/unit/scripts/test_trim_recently_shipped.py`
  (9 tests) — the Recently-shipped trim **actuator**, complement to the
  `check_current_state_ledger.py` *detector*. Pure-text `trim()` core: moves the oldest
  over-ratchet bullets from `current-state.md` § Recently shipped into the archive and
  **recomputes the "Older merges (#HIGH … #LOW)" floor pointer from the true archive span**, so the
  prose pointer can't drift (the unguarded #763-class gap). Dry-run `--check` default / `--apply`;
  never deletes a bullet; idempotent. An explicit test pins the **non-monotonic grouped-band**
  hazard the idea flagged. Live `--check` on the real files is a correct no-op (count = 20 = budget).
- **Wired both into the reconciliation routine** (`docs/operations/autonomous-routines.md` STEP 2)
  so future passes use them for the ledger step.
- **Drift-on-sight (Q-0166):** marked the three now-shipped idea docs `historical`
  (`band-pr-merge-status-helper`, `recently-shipped-auto-trim-helper`,
  `governance-files-presence-guard`) + their README index rows; de-staled the current-state ▶ Next
  action ungated-guard cluster (3 of 4 now shipped; only `public-data-contract-field-snapshot`
  remains).

Verification: `check_quality.py --full` green; `check_docs.py --strict` green;
`check_current_state_ledger.py --strict` exit 0 (benign newest-merge lag only, the next
reconciliation pass records — Q-0124, not this dispatch run); `check_architecture.py --mode strict`
clean (no `disbot/` files touched). Both tools disposable (Q-0105), stdlib-only.

## Context delta

- **Needed but not pointed to:** nothing new — the band-#1170 pass §3 + current-state named the
  cluster; the idea docs pre-described each tool's shape and the gh→REST seam from #1174 was a
  ready template.
- **Pointed to but didn't need:** the queue listed `plan-homing-guard` + `governance-files-presence-guard`
  as ungated startables, but both were already built (#1174 / #1120) — fixed on sight.
- **Discovered by hand:** there are now **two** open PRs (#1074 python-dep bump, #1172 npm bump,
  both dependabot) — the band-#1170 pass §1 disposition only listed #1074. Left untouched (routine
  dependabot bumps needing the 3-place version sync, a deliberate runtime call), but flagged so the
  next reconciliation pass dispositions both.

## Decisions made alone

- **Shipped both helpers in one PR** rather than two. They are a single coherent "reconciliation
  ledger-step tooling" batch (both disposable Q-0105, both touch only `scripts/`+`tests/`+docs, both
  wired into the same STEP 2), so one atomic PR is the cleaner modular batch and lands reliably in an
  unattended routine. Reversible.
- **Floor-pointer recompute uses the true archive span** (max/min PR number over the whole archive),
  not the hand-written marker value — principled and self-consistent even when it differs from a
  pass's hand value (the pass reviews the `--check` diff before `--apply`). The non-monotonic-band
  hazard is documented + test-pinned + Q-0105-disposable.

## Flagged for maintainer

- None requiring a decision. (Two open dependabot PRs noted above for the next reconciliation pass.)

## 💡 Session idea (Q-0089)

**A `check_disposable_tooling_shipped.py` consistency guard — idea-status vs. on-disk reality.**
This run found two ideas (`governance-files-presence-guard`, and partly the queue) still badged
`ideas`/listed-as-startable while their `scripts/check_*.py` already existed on disk. The Q-0105
tooling lane has a recurring drift: an idea promoted to a built script, but its idea doc + the
current-state cluster never re-badged "shipped", so a later dispatch re-evaluates an already-done
lane (wasted orientation). A tiny stdlib guard could parse each `docs/ideas/*guard*.md` /
`*helper*.md` that names a concrete `scripts/<name>.py` and warn when that script **exists** but the
idea is still badged `ideas` (not `historical`) — the inverse of `check_plan_homing.py` (which finds
plans with no home; this finds *shipped* ideas with a stale badge). Genuinely worth having; lane =
tooling/consistency. Not built this run to keep the PR single-purpose.

## ⟲ Previous-session review (Q-0102)

The previous dispatch run (`arch-ratchet-cog-layer`, #1163) extended the `baseview_inheritance`
arch ratchet to the cog layer — a genuinely good gate-parity fix that closed a real blind spot, and
it correctly *routed* the broader 38-class residence question to the owner rather than building it
unilaterally. **What it (correctly) only observed:** in its own Q-0102 note it flagged that the
current-state ▶ Next action paragraph has grown to ~30 KB on one logical line and the *live*
sentence is hard to find — but left it as "a reconciliation-routine call." **System improvement this
surfaces (and this run advances):** that observation is now two passes old and the paragraph keeps
growing. The band-#1170 pass §6 also filed it. The concrete next step isn't another observation —
it's that a **reconciliation pass should physically truncate the consumed band-history tail** into
the pass-record docs it already links (the data exists; the trim actuator I shipped is the *ledger*
half of the same "keep the live ledger lean" discipline, but the ▶ Next action callout needs its own
manual trim). A good ungated docs-only session for the next non-reconciliation dispatch, or a STEP-2
sub-task for the next pass.

## 📤 Run report

- **Did:** built two disposable stdlib reconciliation-tooling guards (`band_pr_status.py` —
  merged/closed-unmerged/open classifier, verified against live GitHub; `trim_recently_shipped.py` —
  Recently-shipped trim + floor-pointer recompute actuator), wired both into the reconciliation
  routine STEP 2, and de-staled the queue/idea-docs drift · **Outcome:** shipped
- **Shipped:** `scripts/band_pr_status.py`, `scripts/trim_recently_shipped.py` (+ 25 tests),
  routine STEP-2 wiring, 3 idea docs re-badged `historical`, current-state ▶ Next action de-staled
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (built the band-#1170 pass's named ungated stdlib-guard cluster — a
  dispatched/queued lane, not an invented one; the idea→plan→build promotion gate was not used)
- **↪ Next:** the ungated guard cluster is nearly consumed — the one remaining is
  `public-data-contract-field-snapshot`; otherwise a substantial `needs-hermes-review` lane
  (consistency-linter AI-nav PR 1 · procedures→skills Batch 2), or the docs-only ▶ Next-action
  callout trim flagged in the Q-0102 review above. Two open dependabot PRs (#1074, #1172) await the
  next reconciliation pass's disposition.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session | 1 (this PR — band_pr_status + trim_recently_shipped) |
| New tests | 25 (16 band_pr_status + 9 trim_recently_shipped) |
| CI-red rounds | 0 (only the by-design born-red session gate) |
| Repo-rule trips | 0 |
| Drift fixed on sight | 3 idea docs re-badged + current-state cluster (Q-0166) |
| New ideas contributed | 1 (shipped-tooling stale-badge guard) |
| Ideas groomed | 3 marked shipped (band-pr-status, trim, governance-files) |

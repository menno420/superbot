# 2026-06-19 — Groom: ledger guard distinguishes benign lag from real drift

> **Status:** `complete`

## Arc

Grooming pass (Q-0015 standing secondary task, owner-selected this session). Moved two related,
unbuilt, decided-lane ideas down their lifecycle by **executing** them together — both key on the
reconciliation marker, so they're one coherent change:
- `ledger-guard-benign-lag-vs-drift-2026-06-14`
- `ledger-window-scale-to-marker-2026-06-19`

Motivated directly by this session's own SessionStart banner (`⚠ 14→23 merged PR(s) not yet in
current-state`) — the exact false-red the first idea targets, so I could verify the fix against
ground truth.

## Shipped (PR #1125)

`scripts/check_current_state_ledger.py` is now marker-aware:
- **`marker_pr`** parses the `Last reconciliation pass:** PR #N` line (reusing the
  `check_reconciliation_due.py` pattern) — the lag/drift boundary.
- **`classify_missing`** splits missing PRs into **drift** (`pr <= N`, actionable) vs **benign lag**
  (`pr > N`, informational); `--strict` exits 1 **only on drift**. Benign lag is still *printed* so
  the reconciliation routine reads the full band.
- **`band_window`** auto-sizes the default window to the band since the marker
  (`max(DEFAULT_WINDOW, <merges newer than #N>)`); `--window N` stays an explicit override.
- 7 new unit tests (22 total green); `check_quality --check-only` green. Both idea files → `historical`.

## Context delta

- **Verified against ground truth before trusting (Q-0120/Q-0105):** the live `--strict` run, red on
  the newest-merge lag at session start, now exits **0** — correctly classifying all 23 missing PRs as
  benign lag newer than marker #1094, and auto-sizing the window to the full 23-merge band (vs the old
  fixed 15). Real drift below the marker would still fail.
- **Why both ideas in one PR:** they're the *same* marker mechanism. Gating `--strict` on drift-only is
  only sound if the window reaches back past the marker to actually *see* drift — so the window-scale
  idea is a prerequisite for the benign-lag idea, not a separable change.
- **Deliberately did NOT touch the SessionStart banner** (`claude_session_summary.py`) — it keys off the
  checker's exit code, so it now auto-shows `Ledger : in sync ✓` for benign-lag-only sessions with no
  hook edit (executable-config restriction, Q-0106 respected). It still warns on real drift (the drift
  summary line keeps the `N recent … not in …` phrasing the banner regex matches).

## ⟲ Previous-session review (Q-0102)

**This session's own Codex final-head-review PR (#1105) — solid and well-scoped:** it verified the gap
empirically before building (the #1097/#1100 evidence), chose an Action over a fragile "agent remembers"
rule, and was honest about the merge-race tradeoff. **What it could have done better:** it shipped the
workflow but left the *opening-commit* born-red false positive (Codex's P1 on the in-progress card)
unaddressed — only the *final* review is fixed, so every born-red PR still burns one wasted Codex opening
review (captured as #1105's session idea). **System improvement surfaced here:** the recurring-noise →
build-signal principle — a known idea that keeps re-appearing as live noise (Codex re-flagging born-red;
the ledger false-red I just fixed) should auto-promote to a build; the cost of the standing workaround
exceeds the cost of the fix. Both this session's builds are instances of acting on that.

## 💡 Session idea (Q-0089)

**A `--since-marker` mode on `check_current_state_ledger.py` that emits the benign-lag band as a
ready-to-paste `## Recently shipped` block.** Now that the checker classifies lag vs drift and already
holds each PR's merge subject, the reconciliation routine still hand-writes the ledger entries from the
printed list. A `--ledger-block` flag could format the lag band into the exact grouped markdown the
ledger uses (number · subject · date), turning the reconciliation pass's "write 20+ entries" step into a
paste-and-curate. Distinct from the two ideas just built (those *classify/size*; this *emits*). Small,
stdlib, disposable — and it directly shortens the most manual step of every reconciliation pass.

## 📊 Doc audit (Q-0104)

- Changed files: one script + its tests + two idea files re-badged `historical` + their README index
  entries. No new `docs/**` page → `check_docs` reachability unaffected.
- Ledger: this PR's own change is to the *checker*, not the ledger; the benign-lag band (#1095…) remains
  the #1110 reconciliation pass's job (Q-0124 — a manual session does not run it). No drift introduced.
- The two idea files stay listed in `README.md` (annotated ✅), per the "conveyor not graveyard" rule.

## 📤 Run report

- **Did:** Q-0015 grooming — executed two marker-keyed ledger-guard ideas as one coherent change so
  `check_current_state_ledger.py --strict` stops false-redding on benign newest-merge lag and auto-sizes
  its window to the reconciliation band. · **Outcome:** shipped.
- **Shipped:** #1125 — `marker_pr` / `classify_missing` / `band_window` + 7 tests + both idea files
  `historical`.
- **Run type:** `manual`
- **⚑ Owner decisions needed:** `none` — disposable Q-0105 tooling, no owner gate.
- **⚑ Owner manual steps:** `none`.
- **⚑ Self-initiated:** yes — Q-0015 grooming-ender, agent-selected idea, built under the open idea-gate
  (Q-0172). Verified, contained, reversible.
- **↪ Next:** the benign-lag band (#1095…#1124) is still the #1110 reconciliation routine's job. The
  `--ledger-block` emit idea (above) is a fresh groomable follow-up.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | (this is the grooming PR #1125; #1105 merged earlier) |
| Ideas groomed | 2 (both executed → `historical`) |
| Tests added | 7 (22 total in the file, all green) |
| Ground-truth check | live `--strict` red → green (23 lag PRs reclassified) |
| CI-red rounds | 1 (born-red gate by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (`--ledger-block` emit mode) |

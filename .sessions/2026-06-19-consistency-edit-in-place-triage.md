# 2026-06-19 — Consistency-linter: triage the `edit_in_place` backlog (rule 1)

> **Status:** `complete`

## Arc (what I'm about to do)

Dispatch run, next consistency-linter slice ([plan](../planning/repo-consistency-linter-plan-2026-06-17.md)).
Rules 3 + 4 are at 0 but freshly so (graduation wants "a couple more clean sessions"), so this run
takes the standing **`edit_in_place` (rule 1) triage** — untriaged since PR1 (45 candidates), the
owner's headline UX inconsistency.

Plan for this slice:
1. **Rule improvement (root-cause, Q-0120):** the rule only counts a *direct* `.edit`/`edit_message`
   in the callback body, so it false-flags callbacks that re-render via the codebase's standard
   `self._rerender()` helper idiom (e.g. `TimeRolesPanel.reset_btn`). Teach `_edits_in_place` to also
   treat a callback that calls a **same-class in-place helper** (`self.<m>()` where `<m>`'s body edits
   in place) as editing in place.
2. **Triage the rest:** allowlist the genuinely-correct new-message callbacks (sub-flow pickers that
   re-render the parent on completion · shared multiplayer lobby/match messages · persistent-launcher
   ephemeral sub-flows · terminal/advisory report toasts · in-place-via-module-helper with an ephemeral
   fallback) with per-callback reasons.
3. **Fix the one contained genuine bug:** `roles/diagnostics_panel.DiagnosticsPanel.refresh_btn` chunks
   the member cache but only toasts — the panel's "Members Cached" field stays stale. Add a `_rerender`
   helper + re-render in place (mirrors `time_roles`/`xp_roles`).
4. **Leave the `views/ai/` cluster flagged (17):** they are the real bug — the owner's documented
   "AI panels stack ephemerals instead of updating in place" inconsistency, tracked by
   `ideas/ai-panel-inplace-navigation-2026-06-11.md`. The rule stays warn-only until that redesign
   ships; NOT allowlisted (allowlisting would mute the very inconsistency the rule exists to catch).

Expected: `edit_in_place` 45 → 17 (the 17 being exactly the AI-nav backlog), with one real fix + one
checker false-positive class removed.

## Shipped (#1058)

- **Checker improvement (Q-0120):** `scripts/check_consistency.py` gained `_inplace_helper_names`
  (collect a class's own methods whose body edits in place) + `_calls_inplace_helper`; a callback that
  calls a same-class in-place helper (`self._rerender()`) is now recognized as editing in place. Cleared
  the false-positive class — `time_roles.reset_btn` and (after the fix below) `diagnostics.refresh_btn`.
- **Real fix:** `roles/diagnostics_panel.DiagnosticsPanel.refresh_btn` chunked the member cache but only
  toasted, leaving the panel's "Members Cached" field stale → added a `_rerender` helper and re-render
  in place before the confirmation toast (matches the `time_roles`/`xp_roles` idiom).
- **Allowlisted 26 genuinely-correct new-message callbacks** in `consistency_exceptions.yml` with
  per-callback reasons, grouped: sub-flow openers (role/cleanup pickers + the help-editor sub-flow) ·
  the persistent `SetupLauncherView` (whole class) + the UX-lab persistence demo · shared multiplayer
  lobby/match messages (rps registration ×3, rps pvp pick, blackjack tournament) · in-place-via-helper
  fallback (channels create) · terminal/advisory report toasts (diag run, time run, final-review AI
  review, template apply/cancel).
- **Left the 17 `views/ai/` findings flagged** (NOT allowlisted) — the owner's documented in-place-nav
  inconsistency. `edit_in_place` 45 → 17.
- Test: `test_callback_using_inplace_rerender_helper_is_clean` pins the helper-rerender detection.
  CI mirror green (10660 passed); `check_architecture --mode strict` exit 0.

## Continuation (the handoff)

**▶ Next consistency-linter slice = triage `back_button` (7)** — per the plan + first-run notes, these
are "mostly top-of-stack hub openers, the known external-attach FP": `channels/main_panel`,
`cleanup/policy_panel`, `diagnostic/automation_panel`, `diagnostic/hub_panel`, `games/deathmatch_panel`,
`xp/main_panel` (and one more). Verify each is genuinely a root panel (opened directly by a command, no
parent to go back to) → allowlist with a reason; fix any that are real sub-panels missing a back button.
After that, graduation prep: rules 3 + 4 are at 0 — flip to `error` + wire into `code-quality.yml` once
they stay clean a couple more sessions. **Rule 1 cannot graduate** until the AI-nav redesign
(`ideas/ai-panel-inplace-navigation-2026-06-11.md`) clears its 17 — that idea is a strong Q-0172
promotion candidate (owner-requested, detailed scope sketch already written).

## Context delta

- **Pointed to and needed:** the plan doc's per-PR build-order log + the prior session cards (#1056/#1057)
  gave the exact "next slice = triage edit_in_place / back_button" handoff; `consistency_exceptions.yml`
  already modeled the per-callback `::Class.method` allowlist convention I reused verbatim.
- **Discovered by hand:** the rule's `_edits_in_place` blind spot (only direct `.edit` in the callback
  body, missing the `self._rerender()` idiom) was not documented anywhere — found by reading the flagged
  callbacks against the rule source. Now captured in the plan + this card.
- **Needed but not pointed to:** nothing material — the lane is well-documented.

## ⟲ Previous-session review (Q-0102)

The previous slice (#1057, rule-3 reconcile) was disciplined: it *checked the arch ground truth before
acting* and correctly chose reconcile-over-migrate, and its session-idea (one shared exemption source for
the two direct-`View` checkers) is a real root-cause catch. What it (and the whole linter lane so far)
left implicit: the rules' own *detection* blind spots. #1057 reconciled rule 3 against arch ground truth
but no slice had audited whether each rule *models the codebase's idioms* — this run found rule 1 was
flagging correct `_rerender()` re-renders. **System improvement:** a rule's first triage pass should
explicitly ask "does this rule understand the house idiom for the thing it checks?" before mass-allowlisting
— a false-positive *class* is a checker bug to fix (Q-0120), not 40 allowlist entries to write. Baked into
the plan's build-order entry.

## 💡 Session idea (Q-0089)

**A `--diff` mode for `check_consistency.py` that reports only *new* findings vs. the committed baseline.**
The warn-only rules now carry real backlogs (17 AI + 7 back_button + 45→0 select/panel). Graduation to
`error` is blocked on those backlogs, so the rules can't yet catch *regressions* (a new direct-`View`
subclass, a new front-truncated select) in CI. A `--diff` / baseline mode — snapshot the current finding
set to a committed `consistency_baseline.json`, and in `code-quality.yml` fail only on findings *not* in
the baseline — would let every rule guard against new violations *immediately*, while the existing
backlog is worked down separately. It is the standard "ratchet on a noisy linter" pattern (mypy/ruff
baselines, and the repo's own `baseview_inheritance` conformance frozenset does exactly this for one
rule). Dedup-checked `docs/ideas/` + the plan: the plan's graduation step is all-or-nothing (flip to
error once 0); this adds the incremental path. Worth having — it unblocks regression-guarding without
waiting for every backlog to hit 0. Captured here, not built (its own focused slice).

## 📊 Doc audit (Q-0104)

- Updated the linter plan (rule-1 triage entry + sharpened "next slice") and current-state ▶ Next action.
- No new owner decisions (Q-0120 already covers "a checker that fights the house idiom is the checker's
  bug"); no router entry needed.
- **Ledger lag:** `check_current_state_ledger --strict` flags #1053 + #1055 not in Recently-shipped.
  These are newer than the `Last reconciliation pass: #1050` marker; the prior two sessions (#1056/#1057)
  both judged them **benign newest-merge lag** to be recorded by the #1080 reconciliation pass. #1055 is
  a `bot/dashboard-refresh` generated-data chore (routine, no narrative entry needed); #1053 is a routine
  session PR. Leaving them deferred to #1080 per the standing prior-session decision (CLAUDE.md benign-lag
  exception), unchanged from this run.

## 📤 Run report

- **Did:** triaged consistency rule 1 (`edit_in_place`) — improved the checker to recognize the house
  `_rerender()` idiom, fixed one real stale-panel bug, allowlisted 26 correct new-message callbacks, and
  isolated the 17 `views/ai/` findings as the actionable AI-nav backlog (45 → 17). · **Outcome:** shipped
- **Shipped:** #1058 — `check_consistency.py` helper-rerender detection + test · `diagnostics_panel`
  refresh re-render · 26 `consistency_exceptions.yml` allowlist entries · plan + current-state updates.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** `none` (continued the dispatched consistency-linter initiative — the #1057 handoff
  named the `edit_in_place` triage as a next slice). The AI-nav idea→plan promotion is *recommended* in the
  handoff, not done this run.
- **↪ Next:** triage `back_button` (7) toward 0; graduation prep for rules 3 + 4; promote the AI-nav idea
  to a plan (Q-0172) to clear rule 1's remaining 17.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session | 1 (#1058, on green) |
| `edit_in_place` findings | 45 → 17 (17 = the AI-nav backlog) |
| Real UX bugs fixed | 1 (`DiagnosticsPanel.refresh_btn` stale panel) |
| Checker false-positive classes removed | 1 (helper-based `_rerender` re-render) |
| CI-red rounds | 1 (born-red session gate by design; local mirror green before flip) |
| Repo-rule trips | 0 (arch strict exit 0) |
| New ideas contributed | 1 (`--diff`/baseline regression mode for the consistency linter) |

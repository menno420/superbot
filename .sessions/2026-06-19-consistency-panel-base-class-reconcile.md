# 2026-06-19 — Consistency-linter: reconcile `panel_base_class` with the arch ground truth

> **Status:** `complete`

## Arc (what I'm about to do)

Second slice of this dispatch run (after Lane A2 / #1056). Triage the consistency linter's
**`panel_base_class` rule (26 findings)** against the established arch ground truth, per Q-0120
(a tool verdict that fights documented ground truth is the *tool's* bug).

**Finding:** the arch `baseview_inheritance` checker (the ERROR-tracked ratchet) already
**path-exempts `views/ai/` and `views/games/`** ("specialized lifecycle ownership", documented in
`architecture_rules/canonical_helpers.yaml § base_view.exemptions`) and pins the remaining direct
`discord.ui.View` subclasses to an 8-entry frozenset in
`tests/unit/views/test_view_base_class_conformance.py`. The consistency `panel_base_class` rule
only exempts `views/rps`/`views/blackjack`/`views/base.py`, so it **re-flags 18 ai/games views the
ground truth has already decided are fine** + the 8 documented per-view exceptions.

**Fix (reconcile, do NOT migrate):**
- Add `views/ai/`, `views/games/` to the consistency rule's allowed paths (mirroring the arch
  config's documented lifecycle exemptions).
- Allowlist the 8 documented per-view exceptions in `consistency_exceptions.yml` with reasons
  citing the arch conformance frozenset.
- Expected: `panel_base_class` warn-only **26 → 0** (now agreeing with the arch ground truth —
  a graduation candidate, like rule 4 after Lane A2).

This is the deliberate alternative to the "panel_base_class double-win migration" the #1056 handoff
floated — investigation showed the obvious targets (the settings select-views) are documented
"migrate only with a concrete gain" exceptions, and the ai/games findings are arch-exempted, so the
correct move is reconciliation, not a low-value forced migration.

## Shipped (#1057)

- **Mirrored the arch path exemptions** in `scripts/check_consistency.py`'s
  `_BASE_CLASS_ALLOWED_PATHS` — added `views/ai/` + `views/games/` (with a comment pointing at
  `canonical_helpers.yaml § base_view.exemptions` and the Q-0120 rationale).
- **Allowlisted the 8 documented per-view exceptions** in `architecture_rules/consistency_exceptions.yml`
  (new `panel_base_class:` section), each reason citing the conformance frozenset:
  `BTD6AdminView`, `StrategyReviewView`, `_ChannelListPaginatorView`, `ChannelSettingSelectView`,
  `NumericPresetsView`, `RoleSettingSelectView`, `SetupLauncherView`, `_RankView`.
- **Result:** `panel_base_class` warn-only **26 → 0** — now agreeing with the arch ground truth
  (graduation candidate). No runtime code; no view migrated.
- Test: `test_base_arch_exempted_paths_are_allowlisted` pins the new path exemptions. CI mirror
  green; `check_architecture --mode strict` exit 0.

## Continuation (the handoff)

Two consistency rules are now at **0** on a clean tree — `select_option_truncation` (after Lane A2 /
#1056) and `panel_base_class` (this slice). Per plan step 3, once each stays clean across a couple
more sessions, **graduate it**: flip to `error` and wire into `code-quality.yml`. Remaining warn-only
rules: `edit_in_place` (45 — needs a triage pass splitting real "should edit in place" bugs from
genuine new-message cases) and `back_button` (7 — mostly the known top-of-stack hub-opener FP).

## ⟲ Previous-session review (Q-0102)

The *immediately* previous slice was Lane A2 (#1056, this same run). Its handoff floated the
"`panel_base_class` double-win migration" as a next candidate — which, on investigation, turned out
to be **partly a trap**: the named targets (`ChannelSettingSelectView` et al.) are documented
"migrate only with a concrete gain" arch exceptions, and 18 of the 26 findings are arch-exempted
paths. A2's handoff was right to flag panel_base_class as *next*, but it asserted a *migration*
without checking the arch ratchet first. **System improvement:** when a handoff proposes migrating
views off `discord.ui.View`, it should first cross-check the arch `baseview_inheritance` config +
the conformance frozenset — those encode prior decisions, and a handoff that ignores them sends the
next agent toward fighting a documented choice. I've baked that lesson into both the plan entry and
this slice (reconcile-don't-migrate). The deeper structural fix would be a *single* source of truth
for the direct-`View` exemptions that both checkers read — see the session idea below.

## 💡 Session idea (Q-0089)

**Make the two direct-`discord.ui.View` checkers read one shared exemption list.** Right now the
arch `baseview_inheritance` rule (path exemptions in `canonical_helpers.yaml` + the conformance
frozenset) and the consistency `panel_base_class` rule (hard-coded `_BASE_CLASS_ALLOWED_PATHS` +
`consistency_exceptions.yml`) maintain *parallel* allowlists for the exact same fact ("which views
may extend `discord.ui.View` directly, and why"). This slice had to hand-sync them. They will drift
again. A small shared module (`architecture_rules/view_base_exemptions.py` or a single YAML both
load) that both checkers consume would make the reconciliation permanent and turn "the two checkers
disagree" into a structural impossibility. Genuinely worth having — it's the root-cause fix for the
divergence this slice patched. Captured here, not built (it's its own focused refactor touching both
checkers + their tests).

## 📊 Doc audit (Q-0104)

- Updated the linter plan (rule-3 reconcile entry) + current-state ▶ Next action.
- No new owner decisions. The two checkers' shared-exemption refactor is captured as a session idea.
- Ledger lag (#1053/#1055) is benign newest-merge lag (newer than marker #1050; the #1080 pass
  records them) — unchanged from the A2 slice's audit.

## 📤 Run report

- **Did:** reconciled the consistency `panel_base_class` rule with the arch ground truth (mirror path
  exemptions + allowlist the 8 documented per-view exceptions), driving it 26 → 0. · **Outcome:** shipped
- **Shipped:** #1057 — `_BASE_CLASS_ALLOWED_PATHS` += `views/ai/`,`views/games/`; new
  `panel_base_class:` allowlist section (8 entries); + a path-exemption test.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** `none` (continued the dispatched consistency-linter initiative — the #1056
  handoff named `panel_base_class` as the next slice; I corrected migrate→reconcile after checking the
  arch ground truth. The shared-exemption refactor is *captured* as a session idea, not built.)
- **↪ Next:** graduate rules 3 + 4 after a couple more clean sessions; or triage `edit_in_place` (45).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session (run total) | 2 (#1056 Lane A2 merged · #1057 this slice, on green) |
| `panel_base_class` findings | 26 → 0 |
| CI-red rounds | 1 (born-red session gate by design; local mirror green before flip) |
| New ideas contributed | 1 (shared direct-View exemption source for both checkers) |
| Views migrated | 0 (deliberate — reconciled documented exceptions instead) |

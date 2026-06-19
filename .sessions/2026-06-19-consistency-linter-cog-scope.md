# 2026-06-19 — Consistency linter: extend rules 3+4 to the cog layer

> **Status:** `complete`

Routine dispatch run (empty fire → live ▶ Next-action follow-up). Executing the routed
follow-up named in `docs/current-state.md` ▶ Next action: **extend the consistency
linter's `select_option_truncation` (rule 4) and `panel_base_class` (rule 3) rules to
scan `disbot/cogs/`** — BUG-0017 (the Cog Manager `options[:25]` silent drop) existed
precisely because those rules are `views/`-scoped, so the cog layer is a real blind spot
for the exact `#1040` truncation class the linter exists to catch.

## Plan

- Make rule scope **per-rule** (a `Rule.roots` attribute) instead of a hard-coded
  `views/` filter, so a rule can opt into additional roots without copy-pasting the
  scan loop.
- Set `roots=("views/", "cogs/")` on rule 3 (`panel_base_class`) + rule 4
  (`select_option_truncation`); rules 1+2 stay `views/`-only (rule 1 is warn-only and
  blocked on the AI-nav redesign; rule 2's HubView nav panels live in `views/`).
- Triage every NEW cog-layer finding the extension surfaces: real bug → fix at root;
  legitimate top-N / fixed-catalog → allowlist with a per-entry reason. Both rules are
  GRADUATED (`severity="error"`, wired into `code-quality.yml`), so they must land at
  **0 findings** to keep CI green.

## Shipped (PR #1128)

- **`scripts/check_consistency.py`** — rule scope is now **per-rule** via a new
  `Rule.roots` attribute (default `("views/",)`). A shared `_iter_parsed(files, roots)`
  helper replaces the four copy-pasted scan loops (relativize → skip tests → filter to
  the rule's roots → parse). Rules 3 (`panel_base_class`) + 4 (`select_option_truncation`)
  carry `roots=("views/", "cogs/")`; rules 1+2 stay `views/`-only. `run_checks` passes
  `rule.roots`; `_all_files()` now collects the union of every rule's roots (each rule
  re-filters to its own via `_iter_parsed`).
- **`architecture_rules/consistency_exceptions.yml`** — triaged the 7 cog-layer findings
  the extension surfaced, all to 0:
  - rule 4: `cogs/community_spotlight_cog.py::_build_main_embed` — `top_xp[:3]`/`top_coins[:3]`
    are top-3 leaderboard **embed** fields (the module's only real select, `_GameSelect`, is a
    fixed 4-game catalog), allowlisted scoped to the function.
  - rule 3: `cogs/deathmatch_cog.py::_DuelView` + `::_ChallengeView` (game-state lifecycle —
    own `interaction_check`/`on_timeout`/turn buttons, the cog-layer counterpart of the
    `views/games/` path exemption); `cogs/logging/provision_view.py::LogChannelProvisionView` +
    `cogs/logging/select_view.py::LogChannelSelectView` (invoker-locked ephemeral
    preview/confirm + self-stop lifecycle); `cogs/settings_cog.py::_DisabledHelpHookView`
    (intentionally empty no-controls container the help cog appends a back button to).
- **`tests/unit/scripts/test_check_consistency.py`** — +6 tests: default-scope skips cogs
  (the BUG-0017 blind spot), cog-scope flags a direct-View + a `[:25]` truncation, the
  registry scopes rules 3+4 to cogs / keeps 1+2 views-only, `_all_files` includes the cog
  layer. 43 pass.
- **BUG-0018 (bugs-first, found via the full-suite mirror) — `botsite/data/site.json` regenerated.**
  The full CI mirror surfaced a **pre-existing red on `main`**:
  `test_export_dashboard_data.py::test_committed_site_json_matches_a_fresh_build` failed
  (`commands drifted`). Root cause: `site.json`'s `commands[].linked_ideas` is derived from
  `docs/ideas/`, which churned (#1115/#1124/#1126) after the artifact was last generated, and a
  **hard** equality test pins it. Regenerated via `export_dashboard_data.py --targets site` (963
  insertions / 80 deletions, all `linked_ideas`/meta) → suite green. Recorded as **BUG-0018** with
  the recommended durable root-fix (drop `linked_ideas` from the hard comparison, cover it by the
  warn-only freshness umbrella) left as a contract decision.
- **`docs/health/bug-book.md`** — added BUG-0018; BUG-0017's "Follow-up (routed)" bullet updated to DONE.
- **`docs/current-state.md`** — routed-follow-up clause marked SHIPPED (#1128); recorded
  the see-able ledger drift (#1124 + #1126) into Recently-shipped (Q-0166).

## Verification (green)

- `python3.10 scripts/check_consistency.py` → **0 errors, 17 warnings** (the 17 are the
  unchanged `views/ai/` `edit_in_place` family — rule 1 is still views-only / warn-only).
  `--graduation` reports `panel_base_class` / `select_option_truncation` / `back_button`
  GRADUATED, all 0 findings.
- `python3.10 scripts/check_quality.py --check-only` → **All checks passed** (after the
  PostToolUse auto-fix landed COM812 trailing commas + UP037 on the new helper).
- `python3.10 scripts/check_architecture.py --mode strict` → 0 errors (pre-existing
  `baseview_inheritance` warn-only entries only).
- `python3.10 -m pytest tests/unit/scripts/test_check_consistency.py` → **43 passed**.
- `python3.10 scripts/check_current_state_ledger.py --strict` → green after the #1124/#1126
  entries landed.

## Decisions made alone (for owner ratification)

1. **Allowlisted (not migrated) the 5 cog-layer direct-`discord.ui.View` classes** rather
   than converting them to `BaseView`. Same call the `views/` side made in #1057 ("migrate
   only with a concrete gain"): each is a documented specialized-lifecycle view (game-state
   duel/challenge; invoker-locked ephemeral confirm; deliberate empty container). The
   extension's value is **forward-looking** — a *new* cog-layer direct-View now fails CI.
   Converting these existing ones is risky out-of-scope runtime work.
2. **Kept rules 1 (`edit_in_place`) + 2 (`back_button`) at `views/`-only.** The routed task
   named rules 3+4; rule 1 is warn-only and blocked on the AI-nav redesign (adding cogs would
   add noise to a blocked rule), and rule 2's HubView nav panels are a `views/` construct.

## Context delta (reflection interview)

- **Needed but not pointed to:** the `panel_base_class` rule mirrors the *views/-scoped*
  arch `baseview_inheritance` conformance frozenset (per the allowlist comment), but nothing
  warns that the **arch checker does not scan cogs at all** — so cog-layer direct-View classes
  have no arch-side ground truth to mirror. I had to confirm this by grepping
  `architecture_rules/`. Folded a "extend the arch conformance ratchet to cogs" follow-up into
  current-state's Next-action so the two checkers can be brought into parity later.
- **Pointed to but didn't need:** the CodeGraph startup stats / large reconciliation-band
  prose in current-state — this was a contained tooling change; `context_map` / the graph
  weren't needed.
- **Discovered by hand:** that `_front_truncations_with_scope` yields the *enclosing function*
  qualname for a module-level slice (so the spotlight allowlist scopes to `_build_main_embed`,
  not a class) — only obvious from reading the helper.

## Flagged for maintainer / known limits

- The extension is **mechanically verified** (unit tests + a clean live-tree run) but the
  triage verdicts are by code reading, not a live Discord walk. The 5 allowlisted cog views
  are genuinely specialized-lifecycle, but if any *should* become `BaseView` that's a separate
  migration decision.

## ⟲ Previous-session review

The previous run (the website two-site-split P7+P8 docs unit) did its **"Decisions made
alone"** section unusually well — it flagged the `env-vars.md` generated-file-vs-drift-check
trap precisely and proposed the clean long-term fix (make `scan_env_usage.py:render_doc`
*emit* a static website-tier section) instead of just working around it. The miss: it left
that clean fix **undone and only filed as an idea** because it was "outside this unit's scope
fence" — a scope fence the dispatch routine explicitly says does NOT bind (Q-0148: a work
order labels nature, not scope). A 5-line `render_doc` change would have closed the trap at
the root rather than papering it with an `END GENERATED REGION` marker + caveat.
**System improvement it surfaces:** the routine prompt's "scope is never set by the work order"
rule (Q-0148) is in CLAUDE.md but the *fan-out unit* prompts re-introduce per-unit scope
fences — worth a note that a contained root-fix adjacent to your unit is still in scope.

## 💡 Session idea

**Make `select_option_truncation` (and `edit_in_place`) recognize the `attach_windowed_select`
remediation in cogs the same way it does in views** — and, more broadly, **emit a
machine-readable `--json` finding stream from `check_consistency.py`** so the developer
dashboard can surface live consistency-debt counts per rule per layer (views vs cogs),
turning the graduation tracker into a dashboard widget rather than a CLI-only readout. Small,
read-only, stdlib `json.dumps` of the existing `Finding` list. Dedup-checked `docs/ideas/` +
roadmap — the closest is the dashboard-data lane, but a per-rule/per-layer consistency-debt
feed isn't captured.

## 📤 Run report

- **Did:** extended the UX consistency linter's GRADUATED rules 3+4 to scan `disbot/cogs/` (closes the BUG-0017 cog-layer blind spot) + bugs-first fixed a red `main` (BUG-0018, stale `site.json`) · **Outcome:** shipped
- **Shipped:** #1128 — per-rule `Rule.roots`; rules 3+4 scan `views/`+`cogs/`; 7 cog findings triaged to 0; +6 tests; **BUG-0018 fixed** (regenerated `site.json`, suite back to green); bug-book + ledger de-staled
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (executed the live current-state ▶ Next-action routed follow-up)
- **↪ Next:** consistency-linter / fresh-plan queue resumes; a surfaced candidate is extending the `views/`-scoped `baseview_inheritance` arch conformance ratchet to the cog layer so the arch checker (not only the consistency linter) tracks cog-layer direct-View classes

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (pending auto-merge on green) |
| CI-red rounds | 1 (the born-red card hold; flipped to complete as the final step) |
| Repo-rule trips | 1 (ruff COM812/UP037 on the new helper — PostToolUse auto-fixed) |
| Pre-existing main reds fixed | 1 (BUG-0018 — stale site.json found by the full-suite mirror) |
| New ideas contributed | 1 (Q-0089 — `--json` consistency-debt feed per rule/layer) |
| Ideas groomed | 0 (single-slice routed follow-up; backlog grooming deferred — capacity went to the fix) |

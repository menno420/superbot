# 2026-06-30 — Cleanup spam-window per-guild setting (completion-first deepening)

> **Status:** `complete`

**Run type:** routine · dispatch

## What this run did
Empty-fire dispatch advancing the S1 completion-first arc (Q-0209). Closed **Cleanup completion
cert punch #4** — the last *offline* gap on the Cleanup unit — in one focused PR (#1588).
**Cleanup's offline punch-list is now CLOSED** (only the owner live walk #5/#6 remains).

### The change
The `!cleanuphistory` spam-duplicate detection window was a hardcoded module constant
(`SPAM_DUPLICATE_WINDOW_SECONDS = 15` in `cleanup_cog.py`) that no operator could change. It is now a
**real per-guild scalar setting with a config-input widget**, mirroring automod's `spam_window_seconds`:

- **New settings key** `CLEANUP_SPAM_WINDOW_SECONDS` (`disbot/utils/settings_keys/cleanup.py`, new
  submodule) wired into the package `__init__` import + `__all__`. Scalar legacy-KV — **no migration**.
- **New `SettingSpec`** on `CLEANUP_CONFIG_SCHEMA` (`cogs/cleanup/schemas.py`): name
  `spam_window_seconds`, int, default 15, `input_hint="numeric_presets"`, presets (10, 15, 30), bounded
  validator (1..300), capability `cleanup.policy.configure` (a *registered* cap — the identity-contract
  registry check validates `SettingSpec.capability_required`, unlike the informational DomainPanelSpec).
  Default + bounds live in the schema module as the single source of truth shared with the consumer.
- **Runtime read:** `cleanup_cog._resolve_spam_window(guild_id)` resolves via the canonical
  `settings_resolution.resolve_value`, falling back to the declared default when unset/malformed/out-of
  -range. `cleanuphistory_command` now passes the resolved window. **Byte-identical** (default stays 15).
- Cleanup is now a **scalar + domain-panel** Settings group (was panel-only), so it surfaces an editable
  page through the existing `!settings` widget + the `numeric_presets` widget (`edit_number_presets.py`).

### Tests (+13) / docs
- `tests/unit/cogs/test_cleanup_schemas.py` (new) — register/idempotent, domain-panel retained, spec
  shape (default==constant / value_type / settings_key / widget / presets), default-is-historical-15,
  registered-capability, validator bounds (lower/upper/default ok; below/above/bool/str rejected).
- `tests/unit/cogs/test_cleanup_spam_window.py` (new) — per-guild resolution returns a set value;
  falls back to default when unset / malformed (`"abc"`) / out-of-range (`"99999"`) — never raises.
- `tests/unit/views/test_settings_hub_view.py` — updated the 3 cleanup assertions for the new reality
  (cleanup `surfaces == ("settings", "panel")`, `editable_setting_count == 1`, inventory `settings: 3`).
- De-staled the settings command-map doc (cleanup §9/§10), the Cleanup completion cert (punch #4 ✅,
  verdict, evidence, header note), S1 current-state (recently-shipped + 3 stale Cleanup-#4 pointers),
  and regenerated the 4 generated artifacts (`setting_keys` 112 → 113, `typed_settings` 93).

## Verification
- `python3.10 scripts/check_quality.py --full` GREEN — the only 3 failures were captured by a run that
  started *before* the doc + artifact fixes (the expected `test_existing_settings_keys_constants_referenced`
  + two artifact-freshness checks); re-ran them after the fixes → all 14 pass. Lint/format/docs/
  consistency/artifacts all green on `--check-only`.
- `python3.10 scripts/check_architecture.py --mode strict` — 0 errors (warnings all pre-existing).

## Handoff — next ▶
**Cleanup unit: offline punch-list CLOSED** — only the owner live walk + sign-off (#5/#6) remain.
**Diagnostics** + **Welcome** offline punch-lists are also closed (#1584 / #1581). The next turn-key
**offline** completion-first picks are the named weak spots from the #1545 assessment sweep:
- **Inventory** — item grants are unaudited + capabilities unenforced (route grants through a
  `*_mutation.py` seam + `emit_audit_action`; enforce the declared capabilities). *Bugs-first material*
  (an unaudited mutation seam), but touches economy/inventory writes → keep it a small focused PR.
- **Proof-channel** modal authority re-check was already addressed by #1550/#1551 — verify before
  picking it (don't re-do shipped work).
See `docs/planning/feature-completion/units/` for each cert's punch-list.

## 💡 Session idea
**A "scalar-setting half-ship" guard.** This run (and the welcome run before it) both turned a
hardcoded constant into a `SettingSpec`. The recurring half-ship class is the *reverse*: a `SettingSpec`
declared but the consumer still reads the old constant / hardcoded value, so the operator's setting does
nothing (the dead-stat class BUG-0026 caught for gear). A cheap AST checker could flag a module that
declares a `SettingSpec(settings_key=X)` whose `settings_key` constant is **not** read by any
`resolve_value`/`resolve_setting` call anywhere in `disbot/` — i.e. a setting nobody consumes. Mirrors
the existing `test_effective_stats_consumed.py` invariant, applied to scalar settings. Dedup-checked
`docs/ideas/` — not present; worth an idea file if a later run agrees.

## ⟲ Previous-session review
The previous run (#1581, Welcome age-gating + ping-then-delete) was a clean completion-first slice and
left a *correct, specific* handoff naming Cleanup #4 as a turn-key pick with the right caveat ("heavier,
needs a widget not a constant rename") — that pointer is exactly what let this run start in one hop. One
thing it (and the runs before it) repeatedly hit: the **full suite was launched before the doc/artifact
de-stale**, so it always reports the same 3 expected red checks (settings-doc + artifact freshness). A
small workflow improvement: when a change adds a settings key/spec, regenerate artifacts + update the
command-map doc **first**, then run `--full` once — saves a guaranteed-red full run (~2.5 min each). I
followed the same out-of-order pattern this run; the fix is to make "new settings key ⇒ regen + doc"
a pre-`--full` checklist step (candidate for the journal Quick reference).

## 📤 Run report
- **Run type:** routine · dispatch
- **PR:** #1588 (Cleanup spam-window per-guild setting, punch #4) — self-merge on green (small/contained).
- **⚑ Self-initiated:** none (completion-first arc is the standing S1 dispatch lane; this is the named
  Cleanup cert punch #4, not an unprompted idea→plan promotion).
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none (no migration, scalar KV setting; merge auto-deploys).
- **Bugs:** none opened; none fixed (a latent "operator can't change the spam window" UX gap closed, not
  a runtime bug).

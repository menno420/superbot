# Session — `/settings` typed read-model (SettingSpec) + main-website vision

> **Status:** `complete`

## Origin

Owner (foundations-first, delegated): build toward editing settings from the website. Mid-session the
owner set the scope — *this is the bot's **main website**; the bot stays the source of truth; the site
front-ends it* — and added asks: per-command alias boxes, enable/disable commands, a Manage button on
every command and cog (router **Q-0158**).

## The decisive discovery (don't rebuild — front-end)

Researched the settings stack and found the bot **already has** a typed, audited settings system:
`SettingSpec` (`cogs/*/schemas.py`: type/default/hint/choices/capability) → audited
`services.settings_mutation.SettingsMutationPipeline.set_value` → in-Discord editor (`views/settings/`).
And **`services.command_routing`** (migration 036) already does audited per-cog enable/disable. So the
"settings-metadata registry" I had planned **already exists as `SettingSpec`**, and enable/disable
already exists as `command_routing` — the website is a **front-end over these seams**, never a parallel
system. (Corrected the live-editor plan, which had said "build a metadata registry first.")

## What shipped (this PR)

The **settings read-model** — `/settings` now shows real typed metadata, not just key names:

- **`scripts/scan_setting_specs.py`** (stdlib AST) reads the `SettingSpec` declarations in
  `cogs/*/schemas.py` → **64 typed specs** with `value_type`, `default`, `hint`, `allowed_values`. It
  resolves `settings_key=XP_MIN` → `"xp_min"` and **follows imports** to resolve
  `default=DEFAULT_ENABLED` to its literal (only 2/64 defaults stay unresolved → flagged
  `default_known=False`, never a misleading `None`).
- `export_dashboard_data.py` joins each spec onto its settings key by key string; `/settings` renders
  a **type badge + default + hint + enum choices** per typed setting (`typed_settings` count added).
- Plan + router updated with the **main-website vision**, the **command management surface** design
  (Manage button per command/cog; enable/disable front-ending `command_routing`; per-command alias
  boxes alongside the global `/aliases` search), and the settings-editor-already-exists correction.

## Verification

- `scan_setting_specs.py` → 64 typed specs; scanner + export tests green (9 passed).
- Dashboard smoke **with deps**: `pytest tests/unit/dashboard/test_app.py` → **17 passed**.
- `python3.10 scripts/check_quality.py --check-only` → green. No `disbot/` runtime touched.

## 💡 Session idea (Q-0089)

**A "bot capability ↔ website surface" map** — a small doc/table pairing each editable bot seam
(`settings_mutation`, `help_overlay_mutation`, `command_routing`, synonym layer) with its website
surface + status (read-only / suggest / live). It makes the "front-end the bot, don't duplicate"
principle (Q-0158) *checkable* — any website write feature must name the existing seam it fronts, or
it's flagged as a candidate parallel system. The dashboard analogue of `do_not_create`.

## Documentation audit (Q-0104)

- Owner decision recorded (Q-0158); design lives in the live-editor plan. `check_docs` green.
- SessionStart "merged PRs not in current-state" = the reconciliation backlog (the routine's job,
  Q-0124), not this manual session's.

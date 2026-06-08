# 2026-06-08 — P0C: role-threshold writes converged onto the audited seam (+ P1B re-scope)

**PR:** #592 (branch `claude/pensive-newton-Kq7yg`) · **Plan:**
`docs/planning/adaptive-setup-access-routine-platform-2026-06-08.md` (Phase 0 → 1)

## Arc

Continuation session. Prior session (#591) laid the P0C *groundwork* — a shrinking
drift-fence invariant + a turn-key swap recipe (planning §16.5). This session executed
the recommended next lane: **P0C — convert the six role-threshold direct-write sites onto
the audited `role_automation` seam and empty the fence.** Then, while scoping the *next*
lane (P1B), source-read re-scoped it and I routed that into the plan rather than build a
duplicate/partial.

## Shipped (PR #592)

- **All six direct `utils.db.roles.set_role_threshold*` writes converted** to
  `services.role_automation.set_{time,xp}_threshold` (write **+** `audit.action_recorded`,
  XP path also invalidates the XP-threshold cache): `time_roles_panel` Seed-Defaults +
  `TimeDaysModal`, `xp_roles_panel` `XpLevelModal`, `creation_panel` post-create XP modal,
  `_helpers._ensure_defaults` (system seed), `role_cog.setrole`.
- **Drift fence allowlist emptied** — `test_no_direct_role_threshold_writes.py` is now the
  absolute rule (any direct threshold write in the role surface fails CI).
- **Seam relaxed to `role_id: int | None`** so `!setrole`'s legacy free-text path (named
  role may not exist) keeps its name-only write, now audited (audit `target` falls back to
  the role name). Backward-compatible: every prior caller passes a real int.
- **`creation_panel` threads the freshly-created role id** (`result.steps[0].target_id`)
  so the XP tier is written id-first — closed a latent orphan-on-rename gap the rest of
  PR6's id-groundwork had already closed elsewhere.
- **Tests:** updated the 3 selector tests to assert the seam; added positive tests for the
  3 previously-untested sites (Seed-Defaults, `setrole` resolved/missing, creation modal)
  + the seam's `role_id=None` name-fallback. Kept all manual `invalidate_xp_threshold_roles`
  calls (the `test_threshold_role_mutation_sites_import_invalidator` invariant needs them).
- **Docs:** `ownership.md` drift note (role thresholds ✅ normalized; channel lifecycle still
  pending), planning §8/§9/§15/§16.5 + status, `current-state` (P0C done; #588/#589/#591
  reconciled into Recently-shipped).
- **Verify:** `check_quality.py --full` green (8094 passed), `check_architecture --mode
  strict` 0 errors, `check_docs` pass.

## Findings → routed into the plan (P1B re-scope, §16.8 items 5–7)

Source-read of `setup_diagnostics.py` + `access_projection.py` before starting P1B:

- **`configured_resource_missing` is already covered** by the four existing collectors
  (bindings / role-thresholds / mod-roles / cleanup) — same situation as §16.8 item 1's
  `identity_mismatch`. Don't build a fourth detector. So P1B is **two** new providers, not
  three.
- **`routing_access_conflict`** (routing vs. channel-admission, both channel-level) needs
  **no member** → ready to build now. **`help_advertises_locked`** is entangled with the
  item-3 audience-simulation decision (the dominant reason help hides a command is the
  governance/tier axis, which needs a simulated member) → build it *with* item 3, else it's
  partial.
- The **"locked-reason denial integration"** changes user-facing denial copy → maintainer's
  UX domain; `_SAFE_TEXT` is a draft to confirm, separable from the read-only providers.

Did **not** start P1B implementation: building it now would mean a duplicate provider, a
partial provider, or a silent UX change. Routed the re-scope to §16.8 + the §9 batch row +
`current-state` so the next session builds the right thing. (Standing secondary task: this
*is* the routing/structuring of the next active-plan lane — higher-value than grooming a
random `docs/ideas/` item this session.)

## Gates / state

- #592 CI in progress at hand-off; full mirror was green locally, so green expected.
  Subscribed for failure/merge. `send_later` not available this session (only `Monitor`,
  which can't reach GitHub without `gh`), so no timed self-check-in armed.
- Phase 0 complete; next is **P1B** (re-scoped) then **P1C**.

## Context delta

- **Needed but not pointed to:** the discord.py-2.7 fact that `@discord.ui.button`
  *shadows the instance attr with a `Button`* — the original coroutine stays on the
  **class** (`TimeRolesPanel.reset_btn(panel, interaction, btn)`), so calling
  `panel.reset_btn(...)` raises `'Button' object is not callable`. Had to probe it. This
  belongs in a "testing Discord views" note (no folio covers it). Also: the
  `test_threshold_role_mutation_sites_import_invalidator` invariant
  (`test_xp_cog_caching.py`) silently constrains "route threshold writes through the seam"
  — it requires the four modules to keep importing the invalidator; nothing pointed there.
- **Pointed to but didn't need:** the CodeGraph caller-tier guidance — for this task
  `context_map.py` (Grimp import graph) + targeted `grep` over the 6 known sites were
  enough; didn't need symbol-level CodeGraph at all.
- **Discovered by hand:** that `configured_resource_missing` / `identity_mismatch` are
  already covered is only knowable by reading the four `_diagnose_*` collectors +
  `validate_identity_contract` — there's no "what drift is already detected" index. A short
  "existing drift coverage" table in the health/diagnostics folio would save the next P1B
  agent the same source dig.

# 2026-06-07 — Server-management PR10 (third slice): configurable warn escalation at the seam

- **Arc:** Opus planning session recommended the **escalation** slice as the safest next
  PR10 step; maintainer said "continue" → implemented it same session. Branch
  `claude/practical-mayer-G0zg1` off merged `main` (`b76b320`, #556). The decisive evidence
  was an **in-source breadcrumb**: `_WarnModal` said escalation "stays orchestrated at the
  surface … until moderation config owns it", and the warn→auto-timeout→clear block was
  copy-pasted in **both** `moderation_cog.warn` and `_WarnModal`.
- **Shipped (PR10 third slice):**
  - **`warn_escalation_action`** — enum `timeout` (default = today) / `kick` / `ban` / `none`
    at `warn_threshold`; schema → **v3**; key `MOD_WARN_ESCALATION_ACTION`; `allowed_values`
    Select. Folded the `warn_threshold` / `warn_timeout_minutes` defaults into
    `moderation_config` canonical constants (one source of truth, drift-pinned). **No
    migration** (scalar/KV).
  - **`moderation_config`** — 3 escalation fields on `ModerationPolicy` + a **pure**
    `evaluate_escalation(count, policy)` (fail-safe → no-op on an unknown action).
  - **`moderation_service.warn`** now returns a frozen **`WarnOutcome`** and **owns the
    ladder** at the seam: at threshold it runs the configured action via the sibling
    `timeout`/`kick`/`ban` (so it stays audited + DM'd), resets the count on success; a
    Discord `Forbidden` is reported on the outcome (soft warning), **not raised**. Deleted the
    duplicated escalation block from the cog **and** the modal; both render via the shared
    pure `cogs/moderation/_helpers.render_warn_outcome_lines` (the `views→cogs._helpers` edge
    is the pre-existing `[known]` arch warning — no new violation).
- **Why escalation first (vs the 3 other remaining PR10 items):** strongest seam fit, no
  migration, no capability-authority / log-routing / cleanup coupling, and a root-cause dedup
  the source flagged. **Deferred, each its own future slice:** dedicated/optional **log
  destinations** (extend `server_logging`'s route table — don't duplicate routing);
  **post-action cleanup hook** (consume the cleanup contract — don't duplicate policy);
  **mod/trusted roles + capabilities** (mirror the existing `trusted_role` binding/resolver in
  `governance/resolver.py` + re-route the cog's raw `has_permissions` authority — largest,
  verges on PR11).
- **Tests:** `evaluate_escalation` + policy cases in `test_moderation_config.py`; escalation
  (timeout/kick/ban/none/below-threshold/Forbidden-blocked) + `WarnOutcome` return-type updates
  in `test_moderation_service.py`; `warn_escalation_action` shape + drift guard + v3 in
  `test_moderation_schemas.py`; rewritten warn-modal cases in `test_moderation_modals_defer.py`;
  command-map doc updated for the doc-pin tests.
- **Gates:** `check_quality --full` green (**7734 passed**, 16 skipped; black/isort/ruff/mypy);
  `check_architecture --mode strict` **0 errors**; booted clean (boot_id `166d4f62`,
  ModerationCog loads the **v3** 8-setting schema, 0 ERROR/CRITICAL). **For project state see
  `docs/current-state.md`.** (PR pending.)

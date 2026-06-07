# 2026-06-07 — Server-management PR10 (second slice): require-reason + bot-readiness diagnostics

- **Arc:** the PR10 first slice (#555) merged mid-session; maintainer picked "continue —
  contained items" (via `AskUserQuestion`) → ship the two low-risk remaining PR10 items in
  one PR. Branch `claude/zen-volta-F5xKv` fast-forwarded onto merged `main` (`bfb9ba3`).
- **Shipped:**
  - **`require_reason`** (bool setting) enforced **at the seam**: new
    `moderation_service.ReasonRequiredError` + `_resolve_reason()` raise **before** any side
    effect (warn/kick/ban); **timeout exempt** (its reason carries the duration). Key
    insight that avoided a call-site-spread rewrite: `moderation_config.has_reason()` is
    **placeholder-aware** (treats `"No reason provided"` as no reason), so the cog + the seven
    modals needed only an `except ReasonRequiredError` catch — surfaces keep passing their
    existing (defaulted) reason and the seam normalises/enforces.
  - **Bot-readiness diagnostics:** new pure `utils/moderation_feasibility.py`
    (`evaluate_moderation_readiness` / `render_readiness_line`, mirrors `role_feasibility`);
    `_build_mod_panel_embed(guild)` gains a read-only **"🤖 Bot readiness"** field
    (Ban/Kick/Timeout perms + top-role ceiling) so an operator sees *before* clicking why an
    action might fail. The no-guild persistent-restore path is unchanged.
  - Settings: `MOD_REQUIRE_REASON` key + a `require_reason` bool-toggle spec; auto-rendered in
    `!settings → Moderation`. No migration (KV-backed).
- **Why these two:** lowest-risk of the remaining PR10 list and need no design decision; the
  bigger items (mod-roles + capabilities, dedicated log destinations, escalation rules,
  post-action cleanup) touch capability-authority / other subsystems and were deferred to the
  maintainer.
- **Tests:** `test_moderation_feasibility.py` (new), `test_moderation_panel_embed.py` (new),
  require-reason + `has_reason` cases in `test_moderation_service.py` / `test_moderation_config.py`,
  `require_reason` spec in `test_moderation_schemas.py`. Doc-pin: command-map updated (new key +
  spec name).
- **Gates:** `check_quality --full` green (**7718 passed**, 16 skipped); `check_architecture
  --mode strict` **0 errors**; booted clean (boot_id `84af5634`, ModerationCog + 7-setting schema,
  2 servers, 0 ERROR/CRITICAL). Live Discord render of the readiness field / require-reason
  rejection still owed (no Discord clicks from the shell) — logic is unit-pinned. **For project
  state see `docs/current-state.md`.** (PR pending.)

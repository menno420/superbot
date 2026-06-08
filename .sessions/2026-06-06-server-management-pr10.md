# 2026-06-06 — Server-management PR10 (first slice): config-backed moderation behaviour

- **Arc:** maintainer asked to continue the roadmap plans — "finish the remaining
  plans, or continue as much as possible." The server-management tracker **and** the
  open docs PR **#554** (Codex readiness review) both point unambiguously at **PR10
  (moderation first-class configuration)** as the next approved lane ("service-owned,
  callback-authorized, audited, test-covered; do not start PR11–PR14"). Branch
  `claude/zen-volta-F5xKv` off `dbe0154` (#553); only #554 open live.
- **Scope decision (judgment call, per the working agreement → act, don't re-confirm):**
  PR10's full list is broad (~9 items); shipped the coherent, low-risk **behaviour
  slice** that maps to real Discord effects and is consumed at the mutation seam — DMs,
  ban message-purge, timeout ceiling — and queued the rest (mod-roles+capabilities, log
  destinations, escalation, required-reason, cleanup hook, hierarchy diagnostics) in the
  tracker.
- **Shipped:**
  - `services/moderation_config.py` (new) — `ModerationPolicy` + `load_policy` + a **pure**
    `render_dm_message`; owns the canonical default constants (shared with the schema).
  - 4 settings in `cogs/moderation/schemas.py` (schema → v2): `dm_on_action` (bool),
    `dm_template` (free-text `{guild}`/`{action}`/`{reason}`/`{user}`, plain-replace not
    `str.format`), `ban_delete_message_days` (presets 0/1/7), `max_timeout_minutes` (presets;
    default 40320 = Discord's 28-day max). Keys in `utils/settings_keys/moderation.py`. **No
    migration** (KV-backed; auto-rendered in `!settings → Moderation`).
  - `services/moderation_service.py` — warn/timeout/kick/ban load policy + apply at the seam
    (DM **before** removal for kick/ban so the user is still reachable, **after** for
    warn/timeout; ban `delete_message_seconds` only when configured; timeout clamped down).
    **Behaviour-preserving by default** — an unconfigured guild gets the exact pre-PR10 calls.
- **Why the seam, not the call sites:** the journal's **"guard at the mutation seam"** rule —
  one policy read inside the service protects all surfaces (cog + 7 modals + future hub),
  exactly as PR1 did for the audit fan-out. Avoided spreading `resolve_value` across 8 sites.
- **Tests:** `test_moderation_config.py` (new), config cases in `test_moderation_service.py`
  (autouse default-policy patch keeps the convergence-era exact-call assertions valid),
  `test_moderation_schemas.py` (new — shapes + a spec-default↔policy-default drift guard).
  Updated `docs/setup-platform/settings-customization-command-map.md` for the two doc-pin tests (new keys +
  SettingSpec names).
- **Gates:** `check_quality --full` green (**7690 passed**, 16 skipped; black/isort/ruff/mypy);
  `check_architecture --mode strict` **0 errors**; booted clean (boot_id `a6a24aea` —
  ModerationCog loads the v2 schema, 2 servers, **0 ERROR/CRITICAL**). Live Discord *render* of
  the new settings widgets / actual DM delivery still owed (can't drive Discord clicks from the
  shell) — logic is unit-pinned.
- **Next session:** docs PR **#554** merged ahead of this one; resolved the expected
  additive **union-merge** in `current-state.md` + the journal (kept both entries). **For
  project state see `docs/current-state.md`.** (PR pending.)

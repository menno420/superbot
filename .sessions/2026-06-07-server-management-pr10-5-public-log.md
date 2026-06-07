# 2026-06-07 — Server-management PR10 (fifth slice): optional public moderation log

- **Arc:** Continuation of the same session that shipped the fourth slice (#567, merged).
  Maintainer: "continue with the remaining items in any order, available for questions."
  Two PR10 items remained (both cross-cutting). Researched both, then asked **two** focused
  owner decisions via `AskUserQuestion`:
  - **Mod-roles authority model** → *"Role → moderator tier"* (capability-native: a
    configured role resolves to the existing `moderator` tier, routed through the
    capability resolver — the per-capability tier matrix `capability-authority.md §5`
    defers to an ADR-005 revisit).
  - **Public-log content** → *"Include reason, not mod"* (public entries show action +
    member + reason, redacting the acting moderator).
  Built the **lower-risk public log first** (additive, no authority risk) to bank a clean
  win; mod-roles (security-sensitive) is the last PR10 item, next. Branch
  `claude/awesome-feynman-UADHl` (continues past the merged #567). **PR #___.**
- **Shipped (PR10 fifth slice):**
  - **`public_log_actions`** (none/bans/removals/all) + **`public_log_channel`** (native
    `channel` SettingSpec picker, "" = off); schema → **v5**; keys
    `MOD_PUBLIC_LOG_{ACTIONS,CHANNEL}`. **Default OFF**, no migration.
  - **`moderation_config`** — two fields + `public_log_channel_id` parse (fail-safe → 0) +
    pure `public_log_includes(action, policy)`. Only warn/timeout/kick/ban are ever
    eligible; unban/clearwarnings/post-action-sweep/`auto_delete:*` never public.
  - **Delivery stays in `server_logging`** (owns log delivery): a **separate**
    `_on_moderation_action_public` subscriber on `moderation.action_taken` — the staff-log
    path (`_on_moderation_action`) is **untouched**. Pre-filters to disciplinary actions
    *before* any config read, loads the policy, posts `format_public_log_embed`
    (member + reason; **no actor, no guild id**). Independent of the `logging.enabled`
    staff switch; fail-safe + counted (`mod_public_sent` / `mod_public_skipped`).
- **Why a channel SettingSpec, not a binding/route:** `input_hint="channel"` gives the
  native picker (like economy/xp log channels) with **zero** coupling to
  `server_logging`'s route table or the consistency-pinned `LogChannelSelectView`. Keeps
  the feature cohesive in the moderation namespace; `server_logging` just delivers.
- **Drift fix:** reconciled `current-state.md` (#567 post-action cleanup had merged but was
  still tagged "this PR, pending"). Same living-ledger drift class as last slice.
- **Tests:** `public_log_includes` + channel-id parse in `test_moderation_config.py`;
  redaction + routing (sends / not-selected / channel-unresolvable / Forbidden /
  non-disciplinary-prefilter) + the updated setup-idempotency (2 subscribers on
  `EVT_MOD_ACTION`) in `test_server_logging.py`; **v5** + spec shapes + drift in
  `test_moderation_schemas.py`; command-map + server-logging docs updated for the
  doc-pin tests.
- **Gates:** `check_quality --full` green (**7820 passed**, 16 skipped); `check_architecture
  --mode strict` **0 errors**; `check_docs` green. Default-OFF, additive — no live boot.
  **Project state → `docs/current-state.md`; authoritative queue → the server-management
  status tracker.** Last PR10 item: **mod/trusted roles + capabilities** (decision captured).

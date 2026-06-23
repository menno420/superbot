# 2026-06-23 — Cleanup panel UX overhaul: readable whitelist, fixable warnings, custom levels

> **Status:** `complete` — owner-directed (screenshot + request: the cleanup panel is hard to use,
> the "legacy key" warning is unfixable, the whitelist shows other servers' channels as raw IDs, and
> presets are too limited). PR #1345, auto-merge armed on green (Q-0127). Owner-directed → merge
> immediately (Q-0191).

> **Run type:** `manual · owner-directed`

## What I'm about to do

The owner sent a screenshot of `!cleanup` → Cleanup Policies and three concrete pain points. Root causes
confirmed in source:

1. **Whitelist shows all servers' channels as raw IDs** — `cogs/cleanup/panel.py` renders the *global
   static* `config.CLEANUP_WHITELIST_CHANNELS` (4 hardcoded env IDs) with `<#id>` mentions. Channels not
   in the current guild can't resolve client-side → raw IDs. **Fix:** resolve each ID against the current
   guild (`guild.get_channel`) and list only this server's channels, by name.
2. **"Legacy key — re-set to fix" warning is genuinely unfixable** — re-setting writes a *different* row
   (`scope_id=guild_id`) and leaves the stale `scope_id=0` row in place forever. **There is no delete path
   in the whole cleanup stack.** **Fix:** add an audited remove path (db `delete_cleanup_policy` →
   governance `remove_cleanup_policy` → service `remove_cleanup_change`) and a 🗑️ **Remove a policy**
   button that lists existing rows (incl. legacy/stale) so the warning is clearable in one click.
3. **Only 4 presets, no per-channel customization** — the DB + resolver already store arbitrary column
   values; only the UI is preset-locked. **Fix:** add a **⚙️ Custom…** level option → modal (delete
   invalid y/n · delete failed y/n · delete-after seconds) → same dry-run preview → audited apply.

## Files (planned)

- `disbot/utils/db/governance.py` — `delete_cleanup_policy(guild_id, scope_type, scope_id)`
- `disbot/governance/writes.py` — `remove_cleanup_policy` pipeline method + `remove_cleanup_policy_for_scope`
- `disbot/services/cleanup_diagnostics.py` — `remove_cleanup_change` + custom-columns preview/apply
- `disbot/views/cleanup/policy_panel.py` — Custom… modal + Remove-a-policy select + apply-via-columns
- `disbot/cogs/cleanup/panel.py` — guild-resolved, name-rendered, guild-filtered whitelist
- tests mirroring `tests/unit/services/test_cleanup_diagnostics.py` + `tests/unit/cogs/test_cleanup_panel.py`

## What shipped

A new **audited delete seam** + two UX surfaces, all four complaints closed:

- **`utils/db/governance.py`** — `delete_cleanup_policy(guild_id, scope_type, scope_id) -> bool`
  (keyed by the *literal* scope_id so legacy/stale rows can be cleared; reports whether a row went).
  Re-exported from `utils/db/__init__.py` + pinned in the db-surface contract test.
- **`governance/writes.py`** — `GovernanceMutationPipeline.remove_cleanup_policy` (the mirror of
  `set_cleanup_policy`: same RC-5 scope split + authority check, DELETE + `governance_audit_log` row in
  one transaction, cache invalidation, `audit.action_recorded` + `EVT_CLEANUP_CHANGED` +
  `EVT_CACHE_INVALIDATED`) + the `remove_cleanup_policy_for_scope` module wrapper (re-exported via
  `governance/__init__.py`).
- **`services/cleanup_diagnostics.py`** — `remove_cleanup_change` (literal scope_id, **no** guild→guild_id
  remap, so it clears the exact legacy row); refactored preview/apply onto a shared **columns** seam:
  `preview_cleanup_columns` / `apply_cleanup_columns` (preset wrappers `preview_cleanup_change` /
  `apply_cleanup_change` kept for back-compat). `CleanupPolicyPreview` gained
  `new_delete_failed_commands`; custom values are bounded 0–`MAX_DELETE_AFTER_SECONDS` (300s).
- **`views/cleanup/policy_panel.py`** — (1) a **🗑️ Remove a policy** button → select of stored rows
  (legacy/stale flagged) → audited `remove_cleanup_change`, so the "legacy key" warning is now
  one-click clearable; (2) a **⚙️ Custom…** level option → `_CustomLevelModal` (delete invalid · delete
  failed · delete-after seconds) → same dry-run preview → audited apply; (3) the ineffective/stale embed
  fields now name the exact fix ("press 🗑️ Remove a policy…"); preview shows the failed-cmds flag.
- **`cogs/cleanup/panel.py`** — the Hub whitelist field now resolves each global-config id against the
  **current guild** (`cog.bot.get_guild` → `guild.get_channel`) and lists only this server's channels
  **by name**; cross-guild ids are omitted, empty → "_None in this server_".
- **Tests** — +29 cases across service (custom columns / remove / bounds), view (Custom modal open +
  validation, Remove select + admin gate), cog (name-rendered + guild-filtered whitelist), governance
  (remove RC-5 thread rejection), and db integration (`delete_cleanup_policy` removes + reports). Full
  suite 11988 green; mypy clean; arch 0 errors.

## Findings / decisions

- **Root bug found: the "legacy key" warning was genuinely unfixable.** "Re-set to fix" writes a
  *different* row (`scope_id=guild_id`) and leaves the stale `scope_id=0` row in place forever — and the
  whole cleanup stack had **no delete path**. Fixing the warning therefore required building the audited
  remove seam end-to-end (db → governance → service → UI), not just rewording the message.
- **Decision made alone — custom values via a modal, not new presets.** The DB + resolver already store
  arbitrary columns; adding presets wouldn't give "more customization than the few presets." A 3-field
  modal routes through the *same* dry-run preview + audited apply as presets (one columns seam), so
  custom policies are first-class without a second write path.
- **Decision made alone — Remove keeps the literal scope_id.** Apply remaps guild scope to `guild_id`
  (the PR9 fix); Remove must *not*, or you could never clear a legacy `scope_id=0` row. Pinned by a test.
- **Whitelist is global static config (`CLEANUP_WHITELIST_CHANNELS`), not per-guild** — I did not migrate
  it to DB this session (the config comment already flags that as a future PR); filtering+naming at render
  time fully fixes the *display* complaint without that larger change.

## 💡 Session idea

**Migrate `CLEANUP_WHITELIST_CHANNELS` from static env config to a per-guild DB policy** (the config
comment already anticipates this: "A future PR can migrate this to a DB-backed per-guild policy along the
same shape as command access"). Today the whitelist is a single global list shared by every server, so an
operator can't actually *manage* it from Discord — they can only see this guild's slice of it (now that
the display is fixed). A small `cleanup_whitelist` table + an audited service op + a `ChannelSelect` on
the Cleanup hub would make the whitelist editable per-server, matching how every other cleanup policy
already works. (Dedup-checked `docs/ideas/` — no existing cleanup-whitelist idea.)

## ⟲ Previous-session review (Q-0102)

The previous session (Starboard PR 2, #1270) was a clean owner-style slice — it shipped the
config/correctness/UX subset and *named* its one deferral (the XP bonus) with a reason rather than
silently dropping it, which is exactly the accountability the Q-0172 self-initiation gate wants. Its
honest "tooling mistake" note (`ruff --fix` rewriting 339 test files because CI excludes `tests/`) was
useful — **I hit the same foot-gun's edge this run** (ruff S101 false-positives on my new test files) and
avoided the blast only because I scoped the fix to `git diff` files. **System improvement (initiated):**
that session already filed the "`--changed-only` guard for `ruff --fix`" idea; this run is the second
session in a row to brush against the same scope trap, which is strong evidence it should graduate from
*idea* to *built* — a `check_quality.py --fix` mode that fixes only changed-and-in-CI-scope files would
have made both runs safe by construction. Flagging the repeat so the next groomer promotes it.

## 📤 Run report

- **Did:** Cleanup panel UX overhaul — readable/guild-filtered whitelist, an audited delete seam making
  the legacy-key warning one-click fixable, and a Custom… level for per-channel tuning beyond presets ·
  **Outcome:** shipped (PR #1345, auto-merge armed on green)
- **Shipped:** #1345 — cleanup panel UX (this session)
- **Run type:** `manual · owner-directed`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none — merged = deployed (Railway auto-redeploys `worker` on merge; no
  migration, no data step). The change is live within minutes of merge.
- **⚑ Self-initiated:** no — owner-directed from the `!cleanup` screenshot + request. (The
  whitelist→DB follow-up idea above is *captured*, not built.)
- **↪ Next:** the per-guild whitelist DB migration (idea above) is the natural follow-up; otherwise the
  S1 queue is untouched.

## ⟳ Doc audit (Q-0104)

`check_docs --strict` green; `check_consistency` 0 errors (the `btn_remove` edit_in_place warning matches
the existing `btn_build` panel-open pattern — a select opened via `send_message`, same as every other
hub-open button). New audited mutation seam documented in-code + the session log; no owner decision to
route. The PR isn't in `current-state` Recently-shipped yet (benign newest-merge lag — the next
reconciliation pass records it).

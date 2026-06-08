# SuperBot — Helper Debt Inventory

> **Status:** `living-ledger` — inventory snapshot, dated 2026-05-24, `main` at `934870e6`.
> Companion to `docs/helper-policy.md` (the binding rules).
>
> **What this is:** a one-shot audit of helpers in the candidate sprawl
> areas, classified per `docs/helper-policy.md` § 3 (rung) and § 4
> (promotion ladder). No code moves are made by the PR that lands this
> file; the goal is to stop future helper sprawl by naming what already
> exists.
>
> **What this is not:** a migration PR. Items marked "migrate" /
> "delete" are recommendations for **future** dedicated PRs. Do not
> reshuffle helpers opportunistically while doing unrelated work
> (§ 4 demotion rule).

---

## Files audited

- `disbot/utils/helpers.py` — known grab-bag (§ 3.9 special case).
- `disbot/utils/embeds.py` — known underused (§ 3.9 special case).
- `disbot/views/navigation.py` — canonical back-button factory (§ 3.5).
- `disbot/views/base.py` — canonical view primitives (§ 3.5).
- All `disbot/cogs/*/_helpers.py` files (9 total).
- All `disbot/views/*/_helpers.py` files (3 total).

---

## 1. `disbot/utils/helpers.py`

5 public surfaces. Per § 3.9: do **not** add to this file.

| Symbol | Recommendation | Notes |
|---|---|---|
| `_parse_member` | **keep / freeze** | 6 callers across `views/moderation/modals.py` and `views/xp/modals.py`. Pure domain (member resolution). Correct rung. |
| `safe_select_emoji` | **keep / freeze** | 1 caller (`core/resources/channel_service.py:110`). Correct rung. |
| `post_log_embed` | **keep / freeze** | 5 callers in economy + xp subsystems. Domain-stable. **Candidate for future promotion** to a `services/audit_events.py` if cross-subsystem audit becomes a thing, but only in a dedicated PR (§ 4: no speculative promotion). |
| `normalize_name` | **keep / freeze** | 4 callers in role / discovery / role_service. Correctly placed leaf utility. |
| `CogMenuView` | **delete after reference search** | Defined at `disbot/utils/helpers.py:107`. Self-references only — no external importer or instantiation. Dead code. |

---

## 2. `disbot/utils/embeds.py`

6 public surfaces. Per § 3.9: file has limited adoption; **do not
invest in it** — consolidation needs its own dedicated PR with a
migration plan. Audit:

| Symbol | Recommendation | Notes |
|---|---|---|
| `error` | **keep / freeze** | Imported via `from utils import embeds as em` in `cogs/utility_cog.py:11` (5 call sites) and `cogs/xp_cog.py:12` (1 call site). The only function in this file with real callers. |
| `success` | **delete after reference search** | No importers (checked direct + `em.` alias forms). |
| `info` | **delete after reference search** | No importers. |
| `warning` | **delete after reference search** | No importers. |
| `server_info_embed` | **delete after reference search** | No importers. |
| `user_info_embed` | **delete after reference search** | No importers. |

A future deletion PR can remove the five unused builders without
touching `error()` or its two callers. Verify once more before
deleting that no dynamic `getattr(em, name)(…)` pattern exists.

---

## 3. `disbot/views/navigation.py`

Canonical § 3.5 module. All 7 exports are correctly placed:
`ParentBuilder`, `BackTarget`, `MAX_COMPONENTS`, `attach_back_button`,
`attach_back_target`, `chain_back`, `transition_to`. **No debt inside
this file.**

The debt is **outside it** — two `attach_back_to_*` factories
duplicated the canonical helper at the time of audit (admin and
settings). The other four cited in the original table turned out to
be already-migrated and were mis-classified — see the "Correction"
note below the table.

| Location | Lines | Status (as of 2026-05-24, post-PR-#297) |
|---|---|---|
| `disbot/views/games/hub.py:212-245` (`attach_back_to_games_button`) | thin wrapper | **already migrated** — calls `attach_back_button` internally. |
| `disbot/cogs/admin_cog.py:367-410` (`attach_back_to_admin_button`) | thin wrapper | **migrated in PR #297** — calls `attach_back_button` internally. |
| `disbot/views/settings/subsystem_view.py:244-277` (`attach_back_to_settings_button`) | thin wrapper | **migrated in PR #297** — calls `attach_back_button` internally. |
| `disbot/views/community/hub.py:189-214` (`attach_back_to_community_button`) | thin wrapper | **already migrated** — calls `attach_back_button` internally (the original audit listed this as a duplicate; it was not). |
| `disbot/cogs/cleanup/panel.py:100-130` (`_attach_back_to_cleanup_button`) | thin wrapper | **already migrated** — calls `attach_back_button` internally (the original audit listed this as a duplicate; it was not). |
| `disbot/cogs/help_cog.py:190-243` (`_attach_back_to_help_button`) | thin wrapper | **already migrated** — calls `attach_back_button` internally (the original audit listed this as a duplicate; it was not). |

**Correction:** the original audit treated every file whose name
contained `attach_back_to_*` as a duplicate without opening each
source file. Three of those (community/hub, cleanup/panel, help_cog)
had already been migrated when the audit was written — each is a
small wrapper around `attach_back_button` with a parent-builder
closure, not a hand-rolled button. Phase 3.5 is now complete; no
further migration is needed.

---

## 4. `disbot/views/base.py`

Canonical § 3.5 module. 4 exports: `BaseView`, `HubView`, `send_panel`,
`handle_view_error`. **No debt inside this file.**

Adoption signals:

- 51 view files inherit from `BaseView` (directly or via `HubView`).
- 18 cogs use `send_panel` for panel commands; only a handful of
  one-off confirmation dialogs go ad-hoc.
- `handle_view_error` is reused by `views/blackjack/{tournament,pvp,solo}_view.py`,
  which extend `discord.ui.View` directly because they need custom
  timeout / lifecycle semantics (allowed for game-state views).

No migration needed. Future game-state views that bypass `BaseView`
should justify the bypass in their class docstring.

---

## 5. Per-cog `cogs/*/_helpers.py`

All six existed before this audit. Per § 3.3 they are
**subsystem-private** by design. The forbidden dependency rule is:
"other cogs; other subsystems' `_helpers.py`; `views/<other>/`".

The audit found that several of these files leak to **the cog's own
view package** (e.g. `cogs/economy/_helpers.py` is imported by
`views/economy/*`). § 3.3 forbids cross-subsystem imports but is silent
on the cog↔view boundary inside the same subsystem. The current
codebase treats `cogs/<sub>/` and `views/<sub>/` as **the same
subsystem split for layering**, so views importing from
`cogs/<sub>/_helpers.py` is technically allowed today.

This audit flags those as "intra-subsystem leak" (lower priority than
true cross-subsystem leaks) and reserves "**cross-subsystem leak**"
for cases where the importer is a *different* subsystem.

### Inventory

| Cog helper file | Symbols | Intra-subsystem leak | **Cross-subsystem leak** |
|---|---|---|---|
| `cogs/moderation/_helpers.py` | 2 (`_build_mod_panel_embed`, `_can_act_on_interaction`) | `_can_act_on_interaction` → `views/moderation/modals.py:27` | — |
| `cogs/economy/_helpers.py` | 12 (`JOBS`, `SHOP_ITEMS`, `_build_economy_embed`, `_job_pay`, `_available_jobs`, `_pick_daily`, `_shop_embed`, `_WORK_COOLDOWN`, `_DAILY_COOLDOWN`, `_DAILY_TIERS`, `_daily_weights`, …) | 7 symbols → `views/economy/{main,work,shop}_panel.py` | — |
| `cogs/diagnostic/_helpers.py` | 10 (`build_*_embed`, `build_command_list_pages`, `_fmt_snapshot_value`, …) | 9 builders → `views/diagnostic/{hub_panel,paginator}.py` | — |
| `cogs/xp/_helpers.py` | 4 (`_STAT_TYPES`, `_guild_xp_settings`, `_progress_bar`, `_build_rank_embed`) | `_guild_xp_settings` → `views/xp/config_panel.py:14`; `_build_rank_embed` → `views/xp/{main_panel,rank_view}.py` | — |
| `cogs/setup/_helpers.py` | 2 (`resolve_hub_entry`, `build_status_embed`) | — | — (no real leak — see "Correction: name collision" below) |
| `cogs/rps_tournament/_helpers.py` | 8 | — | — |

### Recommendations (per file)

| File | Recommendation |
|---|---|
| moderation | **keep** — single helper, single intra-subsystem caller; low debt. |
| economy | **migrate later — extract data to `cogs/economy/data.py`** in a dedicated PR. `JOBS`, `SHOP_ITEMS`, `_DAILY_TIERS` etc. are content constants, not domain helpers; views shouldn't be reaching into a cog's underscored module for them. Embed builders (`_build_economy_embed`, `_shop_embed`) and pure helpers (`_job_pay`, `_pick_daily`, `_daily_weights`) belong either in the data module or a `cogs/economy/embeds.py` per § 3.2. Big surface area — schedule as a standalone PR. |
| diagnostic | **migrate later — promote builders** in a dedicated PR. All 9 `build_*_embed` functions are consumed equally by `cogs/diagnostic_cog.py` and `views/diagnostic/hub_panel.py`. The natural home is `cogs/diagnostic/embeds.py` (§ 3.2 sibling module) or a re-export from `cogs/diagnostic/__init__.py`. |
| xp | **keep / freeze** — small surface, intra-subsystem only. |
| setup | **keep** — the apparent leak was a name collision (see § 5.1). `resolve_hub_entry` is only called from `setup_cog.py`, and `build_status_embed` is only called from `setup_cog.py` (the diagnostic callers import a same-named function from `cogs/diagnostic/_platform_embeds.py`, not from here). Separately: `cogs/setup/_helpers.py:99` lazy-imports `build_setup_readiness_embed` from `cogs.diagnostic._platform_embeds` — that's the real setup-touches-diagnostic edge, see § 7. |
| rps_tournament | **keep** — all callers are inside the cog's own submodules. |

### 5.1 Correction — `build_status_embed` was a name-collision false positive

The original draft of this inventory listed `build_status_embed` as a
"setup → diagnostic" leak. That was a mis-attribution: **two**
distinct functions share the name `build_status_embed` in different
subsystems, and a name-only grep merged their caller graphs (the
exact pattern `.claude/CLAUDE.md` § "Name-collision false positives"
warns about):

- `cogs/setup/_helpers.py:115` — signature `(session, *, pending_ops)`;
  builds the `/setup-status` snapshot. Sole caller:
  `cogs/setup_cog.py:32` (`build_status_embed as _build_status_embed`).
- `cogs/diagnostic/_platform_embeds.py:486` — signature `(bot)`;
  builds the `!platform status` embed. Callers:
  `cogs/diagnostic_cog.py:39` and `views/diagnostic/platform_panel.py:46`,
  both via `from cogs.diagnostic._platform_embeds import …`.

Each subsystem imports its own helper. No cross-subsystem import of
`build_status_embed` exists. No migration is needed — § 9's original
"`build_status_embed` re-home" item is **withdrawn**.

The real setup ↔ diagnostic edge is documented in § 7 as
`build_setup_readiness_embed` (setup importing from diagnostic).

---

## 6. Per-view `views/*/_helpers.py`

3 files. Per § 3.4 these are view-private by design.

| View helper file | Symbols | Intra-subsystem leak | **Cross-subsystem leak** |
|---|---|---|---|
| `views/roles/_helpers.py` | 5 (`_DEFAULT_THRESHOLDS`, `_COLOR_OPTIONS`, `_ensure_defaults`, `_parse_color`, `_find_role_normalized`) | `_ensure_defaults` → `cogs/role_cog.py` (intra-subsystem) | — |
| `views/channels/_helpers.py` | 4 (`_NAME_PRESETS`, `_CATEGORY_PRESETS`, `_ChannelSelect`, `_build_channel_options`) | `_build_channel_options` → `cogs/channel_cog.py` (intra-subsystem) | — |
| `views/rps/_helpers.py` | 7 (`_RPS_WINS`, `_RPS_EMOJI`, `_FREE_WIN`, `_rps_pvp_pending`, `RPS_PVP_PENDING_SUBSYSTEM`, `RPS_PVP_PENDING_VERSION`, `rps_pvp_canonical_user_id`) | — | **`_FREE_WIN` → `views/games/rps_panel.py:63` + `cogs/rps_tournament/_quickplay.py:19`**; **`_rps_pvp_pending`, `RPS_PVP_PENDING_SUBSYSTEM`, `RPS_PVP_PENDING_VERSION` → `cogs/rps_tournament/_persistence.py:166,223`**. RPS view helpers imported by games view + rps_tournament cog. |

### Recommendations

- **roles, channels** — **keep**. Intra-subsystem only; correct rung.
- **rps** — **migrate later**. The constants and the
  `_rps_pvp_pending` state are state used by both `cogs/rps_tournament`
  and `views/rps` and `views/games/rps_panel.py`. They are not view
  primitives; § 3.6 says shared cross-subsystem state belongs in a
  service. Open a dedicated PR that creates a small
  `services/rps_state.py` (or a service-style module) owning the
  pending-match table and the constants, then re-points all three
  callers. Out of scope for this inventory.

---

## 7. Cross-package leaks — priority list

These are the imports that today's `_helpers.py` files emit which
break (or stretch) § 3.3's "other cogs; other subsystems'
`_helpers.py`" rule. Sorted by policy weight.

| Priority | Import | File | Recommendation |
|---|---|---|---|
| **HIGH** | `from cogs.diagnostic._platform_embeds import build_setup_readiness_embed` | `cogs/setup/_helpers.py:99`, `views/setup/launcher.py:223`, `views/setup/sections/readiness.py:34` (each is a lazy import inside a function body) | Setup → diagnostic. The embed builder for the per-guild "setup readiness" view lives under diagnostic (it walks `subsystem_schema.all_schemas`), but the setup launcher needs to surface it in the wizard. Three lazy imports avoid a hard module-level cycle. Either promote the builder to `services/setup_readiness.py` (or similar) so both subsystems import a service, or accept the lazy-import seam as the long-term shape. |
| **HIGH** | `from views.rps._helpers import _FREE_WIN, _rps_pvp_pending, RPS_PVP_PENDING_*` | `cogs/rps_tournament/_persistence.py:166,223`, `views/games/rps_panel.py:63`, `cogs/rps_tournament/_quickplay.py:19` | Cross-subsystem + reverse direction (cog importing from views). Belongs in a service or shared module. |
| MED | `from cogs.economy._helpers import JOBS, SHOP_ITEMS, …` (7 symbols) | `views/economy/{main,work,shop}_panel.py` | Intra-subsystem leak, but big surface. Extract data + embed builders to dedicated modules in `cogs/economy/`. |
| MED | `from cogs.diagnostic._helpers import build_*_embed` (9 symbols) | `views/diagnostic/{hub_panel,paginator}.py` | Intra-subsystem leak. Extract to `cogs/diagnostic/embeds.py`. |
| LOW | `from cogs.xp._helpers import _build_rank_embed, _guild_xp_settings` | `views/xp/{main_panel,rank_view,config_panel}.py` | Intra-subsystem; small surface. |
| LOW | `from cogs.moderation._helpers import _can_act_on_interaction` | `views/moderation/modals.py:27` | Intra-subsystem; single symbol. |

---

## 8. What this inventory does *not* do

- It does **not** delete any helper. The "delete after reference
  search" items (`CogMenuView`, the 5 unused `embeds.py` builders) need
  their own short PR with one more grep pass against dynamic-attribute
  patterns before removal.
- It does **not** migrate any helper. § 4 forbids opportunistic
  relocation during an unrelated PR.
- It does **not** change `docs/helper-policy.md`. The policy already
  says what to do; this file just records the gap between policy and
  current code.

## 9. Suggested follow-up PRs (each independent)

The order below is by reward / risk, smallest first.

1. **Dead-code removal** — delete `CogMenuView` and the 5 unused
   `utils/embeds.py` builders after one more pass against dynamic-name
   usage. Pure subtraction; no behaviour change.
2. **`build_setup_readiness_embed` promotion** — the three lazy imports
   in `cogs/setup/_helpers.py:99`, `views/setup/launcher.py:223`,
   and `views/setup/sections/readiness.py:34` reach into
   `cogs/diagnostic/_platform_embeds.py` to render the readiness
   embed. Promote the builder to a service (e.g.
   `services/setup_readiness.py`) so both subsystems import a service
   instead of one cog importing another.
3. **Phase 3.5 finish** — migrate `attach_back_to_admin_button`,
   `attach_back_to_settings_button`, `attach_back_to_community_button`
   to thin wrappers around `views/navigation.py:attach_back_button`.
4. **RPS state service** — extract `_rps_pvp_pending` and the
   `RPS_PVP_PENDING_*` constants from `views/rps/_helpers.py` to a
   small `services/rps_state.py` (or service-style module). Re-point
   the three callers.
5. **Economy data/embed split** — break `cogs/economy/_helpers.py`
   into `cogs/economy/data.py` (`JOBS`, `SHOP_ITEMS`, tiers) and
   `cogs/economy/embeds.py` (`_build_economy_embed`, `_shop_embed`).
   Largest of the suggested PRs.
6. **Diagnostic embed promotion** — move the 9 `build_*_embed`
   functions from `cogs/diagnostic/_helpers.py` to a dedicated
   `cogs/diagnostic/embeds.py`. Cog and views both re-import from the
   new module.

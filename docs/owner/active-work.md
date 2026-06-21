# Active work — parallel-agent claim ledger

> **Status:** `living-ledger` — append-only coordination file. Not a roadmap, not a tracker
> of merged work (that's `docs/current-state.md`). Source + merged PRs win. Owner decision
> Q-0126 (2026-06-14).

## What this is

A lightweight **claim ledger** so parallel agent sessions don't duplicate each other's work.
The maintainer runs several Claude Code sessions at once; two of them picking up the same task
is pure waste. This file makes "what is someone already on?" answerable **before** a PR exists.

## How to use it (per CLAUDE.md § Session & plan workflow)

1. **Before starting**, scan **this file's Active claims** *and* the open / recently-closed PRs
   (`list_pull_requests`). If your task is already claimed or in flight, coordinate or pick
   something else — don't duplicate it.
2. **Append one claim line** under **Active claims** in the format:
   `` `branch` · scope · expected files/area · date · (optional) agent ``
3. **At session close**, remove your line (or move it to **Recently cleared** with the PR #).
   A claim is a soft signal, not a lock — stale lines are fine to prune when you see them.

Keep it short. This is a whiteboard, not an audit trail — the durable record is the PR + the
living ledger (`docs/current-state.md`).

## Active claims

- `claude/peaceful-mayer-rgc20t` · **BTD6 data auto-seed on boot** (owner: "isn't seed automated?") — auto-seed the postgres `btd6_data_blobs` store from the deployed files in `cog_load` so data PRs apply on deploy (no manual `!btd6ops seed-data`) · `btd6_data_service` / `btd6_cog` / `config` · 2026-06-21 · **PR (this session, auto-merge on green)**

- `claude/peaceful-mayer-rgc20t` · **BTD6 buff-uptime — rebuffBlockTime + multi-target** (owner: improvements welcome) — decode `rebuffBlockTime`, add `targets=N` round-robin uptime · `scripts/parse_gamedata.py` / `disbot/data/btd6/stats/alchemist.json` / `btd6_upgrade_detail_service` / `ai_tools` · 2026-06-21 · **PR (this session, auto-merge on green)**

- `claude/peaceful-mayer-rgc20t` · **BTD6 buff-uptime — verify binding + populate data** (follow-up to
  #1235; owner pointed at the public dump) — cloned BTD Mod Helper dump, corrected `_buff_window` to
  the verified `Add…ToProjectileModel` shape, overlaid buff fields onto committed `alchemist.json` ·
  `scripts/parse_gamedata.py` / `disbot/data/btd6/stats/alchemist.json` / `btd6_upgrade_detail_service`
  · 2026-06-21 · **PR (this session, auto-merge on green)**
- `claude/dispatch-next` · **prune stale Active claims (drift-on-sight, Q-0166)** — every prior
  claim had merged, polluting `check_lane_overlap.py` with false positives · `docs/owner/active-work.md`
  · 2026-06-21 · **auto-merge on green** (docs-only)
- `claude/dreamy-cerf-voar4q` · **Project Moon wiki feasibility finding** (owner-dropped) — capture
  research as a routed idea doc; no runtime code · `docs/ideas/project-moon-wiki-knowledge-domain-2026-06-21.md`
  + ideas index · 2026-06-21 · **auto-merge on green** (docs-only)
- `claude/peaceful-mayer-rgc20t` · **BTD6 Alchemist buff-uptime** (owner live-test) — `btd6_buff_uptime`
  tool + `buff_uptime()` compute + parser buff-window decode (game-data path) · `parse_gamedata.py` /
  `btd6_upgrade_detail_service` / `ai_tools` / `ai_tool_catalogue` · 2026-06-21 · **PR #1235 (auto-merge on green)**
- `claude/dreamy-cerf-voar4q` · **Project Moon knowledge domain** (owner-directed Q-0192: full parity) —
  feasibility **#1238** + program plan **#1239** merged; now pre-build recon (data sources + seam contract)
  · `docs/planning/project-moon-prebuild-recon-2026-06-21.md` · 2026-06-21 · **auto-merge on green** (docs-only)

*(Beyond the claim above, the only open PR is **#1213** creature-PvP battle engine on
`claude/funny-franklin-mw3hxj`, a `needs-hermes-review` foundation slice — its owning
session holds it, no claim line needed here.)*

## Recently cleared

- `claude/reaction-roles-self-heal` · **reaction-roles listener self-heal** (owner-accepted
  continuation) — auto-remove a dead-role binding when reacted on (`_self_heal_dead_binding` +
  `actor_type` thread, audited as `system`) · `disbot/services/reaction_role_service.py` · 2026-06-21 ·
  **PR #1250 (merge on green)**
- `claude/reaction-roles-cleanup` · **reaction-roles dead-binding cleanup** (owner-directed,
  screenshots) — 🧹 Clean up button + `prune_dead_bindings` (+ panel hint) to remove bindings whose
  role was deleted · `disbot/services/reaction_role_service.py` + `disbot/views/roles/reaction_panel.py`
  · 2026-06-21 · **PR #1248 (merge on green)**
- `claude/ecstatic-babbage-8bf0g6` · **"Merge = deploy" clarity** (owner directive Q-0193, in-chat) —
  killed the "restart is yours" misinformation at the roots (`production-deployment.md` lead +
  `.claude/CLAUDE.md` binding line + router Q-0193 + journal) · 2026-06-21 · **PR #1247 (auto-merge on green)**
- `claude/reaction-roles-gradient-presets` · **reaction-roles gradient presets** (⚑ self-initiated,
  Q-0172) — curated `GradientPreset` catalogue + one-tap presets in the Colours flow (perk-gated) ·
  `disbot/utils/role_menu_presentation.py` + `disbot/views/roles/role_menu_builder.py` · 2026-06-21 ·
  **PR #1246 (merge on green)**
- `claude/reaction-roles-message-picker` · **reaction-roles follow-up** (owner-directed) — emoji-add
  message picker (most-recent / pick-recent / new-message / by-id) replacing the raw message-ID step ·
  `disbot/views/roles/reaction_panel.py` · 2026-06-21 · **PR #1243 (merge on green)**
- `claude/ecstatic-babbage-8bf0g6` · **role presets + role-management UX** (owner-directed screenshots) —
  removed hardcoded German tier names (`_DEFAULT_THRESHOLDS`/`_ensure_defaults`) + 🧹 Clear-missing purge;
  Create-menu preset names + colour presets (creation-menu only); Edit by role-select; Delete multi-select +
  confirm · 2026-06-21 · **PR #1245 (auto-merge on green)**
- `claude/reaction-roles-channel-and-colors` · **reaction-roles follow-up** (owner-directed) — menu
  post-channel picker + auto-created colour roles + gradient/holographic (audited
  `RoleLifecycleService` seam, gated on Enhanced-Role-Styles) · 2026-06-21 · **PR #1237 (merge on green)**
- `claude/lucid-carson-qsn1gc` · **reaction-roles refinement** (owner-directed) — multiple emotes
  per message each with its own role (`utils/emoji_tokens` + Add-flow rewrite, no schema change) +
  role-menu **Repost/Duplicate** reuse (`set_menu_location`) · 2026-06-21 · **PR #1234 (merge on green)**
- `claude/zen-dirac-wnhwhg` · **"free for everyone, forever" product North Star** (owner-directed
  in-session) — router Q-0190 + mission doc + roadmap/current-state/ideas-index cross-refs · 2026-06-21
  · **PR #1226 (auto-merge on green)**
- `claude/early-pr-mandate` · **Q-0189 — open the session PR within ~2 min of start** (owner-directed
  in-session rule) · `.claude/CLAUDE.md` (Q-0133 bullet) + `docs/owner/maintainer-question-router.md`
  · 2026-06-21 · **PR #1224 (merged)**
- `claude/lane-overlap-claim-scan` · **check_lane_overlap.py — active-work.md claim-ledger scan** ·
  `scripts/check_lane_overlap.py` + `tests/unit/scripts/test_check_lane_overlap.py` · 2026-06-21 ·
  **PR #1223 (merged)**
- `claude/clever-maxwell-690qrj` · **creature-game design/sim + Pokétwo/MusicBot plan** ·
  `tools/game_sim/` + `docs/planning/` + router Q-0186 · 2026-06-20 · **#1193/#1194/#1195/#1197 (merged)**
- `claude/design-system-site-pages` · **design-system: compose the rest of the site** ·
  `design-system/src/` · 2026-06-20 · **PR #1178 (merged)**
- `claude/compassionate-mccarthy-8u4xvy` · **wire the Claude-Design SPA into the bot site** ·
  `botsite/` · 2026-06-20 · **PR #1196 (merged)**

- `claude/vibrant-sagan-0rr5u7` · **reaction-roles PR 2** — in-Discord role-menu builder (Surface B):
  `RoleMenuView` + builder/manager + theme/template presets + edit-in-place + `reattach_role_menus`,
  on PR 1's seam (reconciled onto #1220) · 2026-06-21 · **PR #1219 (`needs-hermes-review`)**
- `claude/reaction-roles-pr1-foundation` · reaction-roles PR 1 foundation (audited seam + menu data
  layer + teardown) · 2026-06-21 · **PR #1220 (merged)**

- `claude/design-system-connector-docs` · design-system docs — GitHub-connector workflow + new
  AGENT_ORIENTATION website route · 2026-06-20 · **PR #1176 (merged)**
- `claude/magical-cori-t36l2n` · design-system full landing-page composition + hybrid edit loop +
  JS CI leg · 2026-06-20 · **PR #1175 (merged)**
- `claude/youthful-turing-odgvq6` · design-system component library (6 components) · 2026-06-20 ·
  **PR #1168 (merged)**
- `claude/funny-franklin-bnvdxe` · federated Explore-hub spine **PR 1** — top-level world hub +
  `services/world_registry.py` seam + `!world` + mining Explore-button re-parent (retired the
  `views/mining/explore_hub.py` stub) · 2026-06-20 · **PR #1156 (needs-hermes-review, auto-merge disabled)**
- `claude/great-carson-4hsr7l` · **planning/audit/idea map cleanup** (docs-only) — new
  `docs/planning/README.md` plan index + 40 stale plans/recon/readiness-maps/audits rebadged `historical`
  + 27 idea subsystem tags + roadmap/folio/ledger de-stale · 2026-06-19 · **PR #1124 (auto-merge on green)**
- `claude/magical-rubin-bq71go` · manifest spine **PR3** — control-API `GET /control/manifest` read +
  cross-manifest reconciliation (`dangling_panel_action`) + AST-vs-panel-registry drift guard +
  deploy-SHA badge · 2026-06-17 · **PR #1020 (auto-merge on green)**
- `claude/magical-rubin-p92toz` · manifest spine **PR2** — panel registry + `PanelManifest`
  (`core/runtime/panel_manifest.py` + `persistent_views` PANEL_ID/enumeration + command-panel join) ·
  2026-06-17 · **PR #1019 (auto-merge on green)**
- `claude/inspiring-wozniak-i92q58` · dashboard **Phase E** — control-API read endpoints + see-then-change
  editor · 2026-06-17 · **PR #1013 (merged)**
- `claude/inspiring-wozniak-i92q58` · dashboard **R3** — live-surface hardening (CSRF + rate-limiting) ·
  2026-06-17 · **PR #1014 (merged)**
- `claude/inspiring-wozniak-i92q58` · dashboard **vision-roadmap reconcile** (Phase C read workspace was
  built in parallel by **#1015** and merged first — authoritative; this run's duplicate was dropped) ·
  2026-06-17 · **PR #1016**
- `claude/health-server-ipv6-bind` · health server IPv6 dual-stack bind (Railway private networking) · 2026-06-16 · **PR #1001 (merged)**
- `claude/inspiring-wozniak-i92q58` · dashboard finalized-state vision plan · 2026-06-16 · **PR #1002 (merged)**
- `claude/control-panel-web` · control panel — Discord OAuth login + editors (write side step 2) · 2026-06-16 · **PR #996 (merged)**
- `claude/control-api-write-side` · control API mutation endpoints (write side step 1) · 2026-06-16 · **PR #993 (merged)**
- `claude/practical-turing-pnppjf` · dashboard `/commands` management surface (READ side) — Manage
  button on every command + cog, per-item panels + per-command alias box · 2026-06-16 · **PR #988 (merged)**
- `claude/kind-carson-736rnk` · dashboard `/settings` + `/access` read-only pages + live help-editor
  design doc (Q-0156) · 2026-06-16 · **PR #977 (merged)**
- `claude/jolly-cannon-gn9ddg` · developer dashboard (personal website) — design + read-only MVP (Phase 1) · 2026-06-16 · **PR #967 (auto-merge on green)**
- `claude/hopeful-meitner-772pv8` · count-citation guard + session-close notes (Q-0151, atlas thread #3)
  — soft `check_docs` inventory-count rule · 2026-06-16 · **PR #964 (auto-merge on green)**
- `claude/peaceful-tesla-vvayya` · Hermes efficiency — idea-spotlight · morning-briefing ·
  dispatch-resolve skills + 6h auto session-reset · 2026-06-16 · **PR #959 (auto-merge pending)**

> Trimmed 2026-06-16 (Q-0152): stale claims whose PRs merged are dropped — the durable record is the
> PR + the `current-state.md` ledger. Keep this to the most recent handful, newest-first.

- `claude/reconcile-1021-docs` · band-#1020 Q-0107 docs reconciliation (issue #1021) — ledger fix + trim · control-plane tick · moderation-DM idea→plan · next-band plan · 2026-06-17 · **docs-only, self-merge on green**
- `claude/gifted-noether-37tiwr` · BUG-0015 — "d67 dart paragon" misread as "0-6-7": parse + route + ground a paragon degree (1-100) · 2026-06-16 · **PR #963 (auto-merge on green)**
- `claude/magical-rubin-u3arq6` · AI §7.5 paragon base-cost comparison floor (last unbuilt comparison member) · 2026-06-16 · **PR #962 (auto-merge on green)**
- `claude/hopeful-meitner-772pv8` · thin architecture atlas (PR 2, Q-0151a) — `scripts/atlas.py` composer + `role` in `context_map.py` + companion doc + tests · 2026-06-16 · **PR #960 (auto-merge on green)**
- `claude/hopeful-meitner-772pv8` · extension-taxonomy crosswalk (Q-0151c) — overlay + generator + CI guard + plan · 2026-06-16 · **PR #958 (merged)**
- `claude/hopeful-meitner-772pv8` · architecture-atlas / structure-review idea intake (owner-uploaded review) · router Q-0151 · 2026-06-16 · **PR #957 (merged)**

- `claude/coglist-command` · `!coglist` real command → admin "📋 Cog List" view · 2026-06-16 · **PR #951 (merged)**
- `claude/fix-coglist-resolution-loop` · BUG-0014 — `!coglist` infinite "assumed from" loop · 2026-06-16 · **PR #949 (merged)**
- `claude/keen-heisenberg-xqro71` · runtime lock early release (fix ~85s deploy downtime) · 2026-06-16 · **PR #948 (merged)**
- `claude/hopeful-allen-qt5ax3` · games-economy faucet/sink diagnostic (`!platform economy`) · 2026-06-16 · **PR #937 (merged)**
- `claude/myprofile-card-pra` · myprofile PR A + B — `/myprofile` card + self-service editor · 2026-06-16 · **PR #938 / #940 (merged)**

- `claude/hopeful-allen-1darl5` · Image moderation (Q-0108) — the safety-community family's
  last buildable slice (OpenAI omni-moderation, off by default, fail-open) ·
  `services/image_moderation_*` + `core/runtime/ai/providers/openai_moderation.py` +
  `cogs/image_moderation/` · 2026-06-16 · **PR #941 (open, needs-hermes-review)**
- `claude/zen-wright-77q0ru` · BTD6 AI answer fixes (owner live-test screenshots) — MK tab-wide scope
  wording · how-many-bloons refusal · ABR/standard RBE labeling · income-range identity ·
  `btd6_context_service` / `btd6_data_service` / `ai_tools` · 2026-06-18 · **PR #1035 (merged)**
- `claude/zen-wright-77q0ru` · BTD6 `round_cash` identity ABR fix (Codex P2 on #1035) — gate identity
  to reconciling ranges · `btd6_data_service` · 2026-06-18 · **PR #1037 (merged)**
- `claude/zen-wright-77q0ru` · BTD6 "which MK affects <tower>" — list class-wide MK + fix sniper
  routing miss · `btd6_data_service` / `btd6_context_service` / `ai_task_router` · 2026-06-18 ·
  **PR (this session)**

- `claude/funny-franklin-507hdy` · repo-consistency-linter PR 1 (harness +
  edit-in-place rule, warn-only, Q-0170) + ledger reconcile #1038–#1041 ·
  `scripts/check_consistency.py` · `architecture_rules/consistency_exceptions.yml` ·
  `docs/current-state.md` · 2026-06-18 · **PR #1042 (auto-merge on green)**

- `claude/funny-franklin-dapcss` · Federated Explore-hub PR 3 — read-only cross-game world card
  (`game_xp_service.world_identity` + `views/explore/world_card.py` + `🪪 World Card` hub button +
  `!worldcard`/`!mystats`) · 2026-06-20 · **PR (this session, self-merge on green)**

- `claude/funny-franklin-8ha49t` · **`!temproles` member-facing temp-role listing** (loose-end
  from reaction-roles PR 3–5) — read seam `role_grants_service.list_active_grants` + `!temproles`
  command on `RoleGrantsCog` · `disbot/services/role_grants_service.py` / `disbot/cogs/role_grants_cog.py`
  + tests · 2026-06-21 · **routine dispatch, self-merge on green**

_(move claims here with their PR # as they close, then prune older entries)_

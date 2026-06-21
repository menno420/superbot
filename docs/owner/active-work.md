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

- `claude/zen-dirac-wnhwhg` · **Codify "free for everyone, forever" as the product North Star** (owner-directed
  in-session new goal — completely free / no feature-gating monetization) · router Q-0190 +
  `docs/ideas/free-for-everyone-mission-2026-06-21.md` + `docs/roadmap.md` + `docs/current-state.md` +
  `docs/ideas/README.md` · 2026-06-21 · **auto-merge on green** (docs-only · owner is live reviewer)

- `claude/early-pr-mandate` · **Q-0189 — open the session PR within ~2 min of start** (owner-directed
  in-session rule) · `.claude/CLAUDE.md` (Q-0133 bullet) + `docs/owner/maintainer-question-router.md`
  · 2026-06-21 · **auto-merge on green** (docs-only · owner is live reviewer)

- `claude/lane-overlap-claim-scan` · **check_lane_overlap.py — add the active-work.md claim-ledger
  scan** (closes the gap that let a duplicate reaction-roles PR 2 get built: the tool only scanned
  recently-MERGED commits, not the earliest "owns PR 2–5" claim signal) · `scripts/check_lane_overlap.py`
  + `tests/unit/scripts/test_check_lane_overlap.py` · 2026-06-21 · **auto-merge on green** (stdlib
  dev-tooling · additive)

- `claude/clever-maxwell-690qrj` · **Pokétwo + MusicBot research report → feature-mapping plan**
  (docs-only, owner-steered plan-only) · `docs/planning/poketwo-musicbot-feature-mapping-plan-2026-06-20.md`
  + `docs/planning/voice-music-architecture-review-2026-06-20.md` + `docs/ideas/` + router Q-0186 ·
  2026-06-20 · **auto-merge on green (docs-only)**

- `claude/design-system-site-pages` · **design-system: compose the rest of the site** (owner-chosen
  meantime build 2026-06-20 — make every route editable in Claude Design) · `design-system/src/`
  (`PageHeader`/`SearchBar`/`Pill`/`FeatureShowcaseCard`/`CommandDetail`/`CommandEntry`/
  `ChangelogEntry`/`StatusCard` + `FeaturesPage`/`CommandsPage`/`ChangelogPage`/`StatusPage` +
  stories) · `design-system/README.md` · 2026-06-20 · **auto-merge on green** (additive · verified)

- `claude/compassionate-mccarthy-8u4xvy` · **Wire the Claude-Design SPA into the bot site + live
  data** (owner-directed; SPA-as-front-end + dynamic data endpoint, confirmed via AskUserQuestion) ·
  `botsite/site/` (design SPA, verbatim) + `botsite/site_data.py` (site.json→SBDATA generator) +
  `botsite/app.py` + `scripts/export_dashboard_data.py` + `tests/unit/botsite/` · 2026-06-20 ·
  **auto-merge on green**

- `claude/reaction-roles-pr1-foundation` · **Reaction-roles overhaul PR 1 — audited seam + menu
  data layer** (owner-directed; foundation for the parallel PR 2–5 session — see
  `docs/planning/reaction-roles-overhaul-plan-2026-06-21.md`) · `services/reaction_role_service.py`
  + `utils/db/role_menus.py` + migration `078_reaction_role_menus.sql` + `cogs/role_cog.py` (route
  writes through the seam) + `guild_lifecycle.py` (teardown step 23) · 2026-06-21 · **PR #1220 (merged)**.

## Recently cleared

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

_(move claims here with their PR # as they close, then prune older entries)_

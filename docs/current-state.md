# SuperBot — Current State

> **Status:** `living-ledger` — living status ledger (project state). **Not binding.**
> **Source code and merged PRs always win over this file.**
> The In-flight section below is a dated snapshot — **verify open PRs against
> live GitHub** before trusting it (two same-session reports already
> contradicted each other across a single merge).
>
> **▶ NEXT (live — read THIS line): the buildable `ready` decade-queue is consumed — next buildable work is PLAN-FIRST *or* the dashboard lane.** **Dashboard handoff (2026-06-16, #969):** the developer-dashboard **Phase 3 env-usage map shipped** — `scripts/scan_env_usage.py` (stdlib AST scan: each env var → file/line, required/optional, layer; names + locations only, never values), surfaced on the new dashboard `/env` page + the generated `docs/operations/env-vars.md` reference. **Dashboard read-only surfaces are now ALL shipped (2026-06-16):** the Q-0156 read-only lane is consumed — `/status` (build & health, **#985**) was the last one, after `/aliases` (#982) + `/games` (#983). **Next dashboard slices are all gated:** the owner-approved **live help/panel editor** (Q-0156, the headline ask) needs the private bot control API + Discord OAuth design (see `planning/dashboard-live-editor-plan.md` L0–L3); Phase 2 (owner auth · checklist · public bug form) and Phase 4 (control board) need owner decisions first (auth method + DB — the plan's open questions); Phase 3b *value-management* needs the Railway-API integration (`creds`). So the dashboard's next pure-code slice is **owner/creds-gated** — the remaining `ready`-class buildable lanes stay the **PLAN-FIRST** ones below. **(2026-06-17, #1017): the settings global tier shipped** — `resolve_setting` now does per-guild → global (`guild_id=0`) → default and `SettingsMutationPipeline.set_value` has an owner-gated `scope="global"` path; the dashboard settings lane's **phase ③** (web editor + `POST /control/settings/{scope}` with the Global/per-server scope picker) is the named next slice but is **owner-pacing-gated** (control-API write endpoints = the owner's "don't rush" zone, needs the Railway `CONTROL_API_TOKEN`) — a future empty fire should take a different ungated lane until the owner greenlights it. The `/myprofile` lane is **buildable-complete**: PR A (read-only card, **#938**) + **PR B — self-service writes (shipped #940)** — `views/profile/editor.py`, the first UI consumer of `ParticipationMutationPipeline` (participation opt-in/out · subscription toggles · visibility toggle · preference editors bool/enum/modal; each action exactly one audited pipeline call). The only remaining myprofile slice is **PR C (join-time onboarding), owner-gated → routed as router Q-0147** (may a public bot DM strangers? — agent recommends in-guild / opt-in / no unsolicited DM). The games-economy faucet/sink diagnostic (slot 2) **shipped #937**. **So the next ▶ startable = a PLAN-FIRST slice: own a small plan for ONE of** — image moderation (Q-0108) · the AI §7 next workflow family (post-prod-check) · the Hermes bug-triage `gh issue create` write (Q-0121); **security service tiers 1+2 (#929) is owner/Hermes-review**, BUG-0009 newest-towers is `data`-gated, absence-guard Layer B is `creds`-gated. **Note:** the `diagnostic_cog.py` 800-LOC blocker is **CLEARED (#943)** — the `!platform` group moved onto `PlatformCommandsMixin` (`cogs/diagnostic/platform_group.py`), cog now 260 LOC, so the next `!platform` subcommand has room. **Security service tiers 1+2 is still IN FLIGHT** (PR #929, `needs-hermes-review` carve-out — raid detection + account-age filter, Q-0111). **BUG-0009 slices 1/2/2b all shipped** (#924 MK-related · #926 Geraldo per-level + game-mode groupings); the one remaining family — newest-towers ordering — is **data-gated** (`towers.json` has no release-order field). The rest of P1 (absence-guard Layer B · live-quality battery) is creds/review-blocked. *The live next-step is THIS sentence — **not** any other "next ▶ =" lower in this callout or in the dated `Last updated:` stamps further down (those are historical reconciliation snapshots: e.g. a stamp still reads "next ▶ = mining Forge", but Forge shipped #905). Trust this line + the Recently-shipped list, never a stamp.*
>
> **▶ NIGHT QUEUE (2026-06-16, owner directive — scheduled dispatch fires read THIS first): advance the [night queue](planning/night-queue-2026-06-16.md).** It makes the otherwise-`plan-first` "AI §7 next workflow family" lane **concrete and buildable now**: an ordered set of independent, **read-only deterministic BTD6 floor builders** (the proven #946/#950/#955/#962/#975/#1000/#1008/#1009/#1010 lane — §7.5 comparison + §7.6 roster), each **data-complete today** (reads a field already in a committed `disbot/data/btd6/*.json`), each ships under **Q-0048** (no prod-check, auto-deploys), each closes the **BUG-0009** "grounded values / wrong assembly" class (the standing P1 priority). **An empty scheduled fire builds the topmost `TODO` slice** (slot 1 hero cost-comparison shipped **#1000**; slot 2 power cost comparison shipped **#1008**; slot 3 relic category/effect roster shipped **#1009**; slot 5 hero ability roster shipped **#1010**; **slot 4 reframed → bloon *modifier explainer* shipped #1011** (camo/fortified/regrow are universal modifiers, not per-type properties — option (c) of the slot-4 reframe); both buffer slices shipped **#1011** — MK category roster + the Geraldo starting-kit angle). **The night queue is now FULLY consumed** — every ready slot, the slot-4 reframe, and both buffer slices have shipped. **But the proven, ungated BTD6 deterministic-floor lane still has thinning backlog** beyond the curated queue: **#1012 (2026-06-17)** shipped three more gaps in the same `btd6_context_service` floor — boss roster + per-difficulty map filter (`deterministic_roster_reply`) + boss damage-immunity (`deterministic_boss_immunity_reply`). Remaining ungated floor candidates are getting scarce (most rosters now covered: towers/heroes/paragons/maps/bosses/MK/relics/bloons/hero-abilities + cost comparisons + immunity); a future empty fire can add a *genuinely-asked* uncovered shape (e.g. boss tier-HP comparison, paragon-ability lookup) **or** take a fresh **plan-first lane** (image-mod #941 in-flight · security tiers #929 — both owner/Hermes-review-gated). Do NOT invent low-value floor builders to fill the queue (forced filler ≠ work). A `/bugreport` or `continue` handoff still jumps this queue (bugs-first). Seam + per-slice turn-key recipes are in the queue doc.
>
> **▶ Next action — one live queue:** **TWELFTH Q-0107 PASS DONE (2026-06-18, band-#1050, issue #1051 — [pass record + next-band queue](planning/reconciliation-pass-2026-06-18-band1050.md)).** The next band is deep but **tooling/workflow-weighted** (the honest read — band-#1050 §3): the bot-product sectors (S1/S2) are correctly gated/exhausted (BTD6 floors complete · fishing owner-design-gated Q-0175 · **image-mod #941 + security tiers #929 BOTH SHIPPED 2026-06-18** — the two `needs-hermes-review` carve-outs finally merged, correcting the prior passes' stale "in-flight, awaiting merge" prose below · dashboard write owner-paced), so the ungated buildable depth lives in S3/S4/S5. **▶ consistency-linter Lane A1 SHIPPED (#1054, 2026-06-18) — the `views/selectors/` API-ripple set is windowed:** the 5 primitives (role/channel/multi/multi_role/subsystem) became windowed `attach_*` helpers over `attach_windowed_select`, all 8 consumers updated, and the upstream truncation source (`build_select_options` `limit=None`) root-fixed; `select_option_truncation` warn-only **15 → 7**. **▶ consistency-linter Lane A2 SHIPPED (#1056, 2026-06-19) — the 7 per-panel embedded selects are windowed:** `access/explorer` · `channels/create_panel` + `channels/move_panel` (retired the bespoke `_CategorySelect` classes) · `diagnostic/automation_panel` (+ a new `SelectWindow.detach()` for clean re-render) · `settings/subsystem_view` (×2; edit dispatcher extracted to module-level `dispatch_edit_setting`) · `setup/sections/channels` all moved onto `attach_windowed_select`; `select_option_truncation` warn-only **7 → 0** — the rule now runs clean on the whole `views/` tree. **▶ Next ungated startable = the next consistency-linter slice** ([plan](planning/repo-consistency-linter-plan-2026-06-17.md)): graduation prep for rule 4 (flip to error + wire into `code-quality.yml` once it stays at 0 across a couple more sessions), **or** the `panel_base_class` double-win (migrate the settings select-views `ChannelSettingSelectView`/`RoleSettingSelectView`/`NumericPresetsView` onto `BaseView` — retires both a `panel_base_class` finding and a `baseview_inheritance` arch-debt row, as #1048 did), **or** triage the `edit_in_place` warn-only backlog (45). Behind it: procedures→skills Batch 1 ([plan](planning/procedures-to-skills-conversion-plan-2026-06-17.md)), owner-review-inbox Phase 1 ([plan](planning/owner-review-inbox-plan-2026-06-17.md)), and the small stdlib guards (`check_plan_backlog.py`, `check_ledger_hygiene.py`, …). **No PLAN-BACKLOG-THIN flag** — ~18–22 ready slices. The owner-side lever to rebalance toward bot features (now that #941/#929 have shipped): decide a Q-0175 fishing open question or greenlight a dashboard write surface. *(Historical band context follows — trust THIS sentence + the Recently-shipped list, never a lower "next ▶".)* **THE IDEA→PLAN GATE IS NOW OPEN (Q-0172, 2026-06-17) — this fixes the "running out of plans" shortage:** when the buildable queue is thin, any agent may promote a `docs/ideas/` idea into a `docs/planning/` plan and **build it without owner approval**, flagged on the run-report `⚑ Self-initiated:` line (the dashboard badges it for review). **Fishing v1 is BUILT + RECONCILED to the owner's #1036 design (MERGED #1033 → #1039 → #1041) — its next slices are owner-design-gated:** the authoritative design is the owner's brain-dump [`planning/fishing-open-world-expansion-plan-2026-06-18.md`](planning/fishing-open-world-expansion-plan-2026-06-18.md) (Q-0175) — 21 size-ranked fish · 7 levels × 3 (level-gated catch) · leveling reuses `game_xp` · unified character with swappable gear-type loadouts · boat/open-world in Phase 2+. The interim v1 (#1033: 14 fish / rarity tiers / coins) was **reconciled to the spec in #1039 + #1041** (21-fish JSON, level/size-band deterministic roll, no-coins collection log; `economy_service` dropped from the path; migration 076 drops the value cols). `!fish` · `!fishlog` · `!fishtop` ship. **The remaining Phase-1 fishing slices are owner-design-gated** — the unified loadout presets, fish value/cook/sell, and the catch minigame are all explicitly-deferred open questions per Q-0175 (do NOT decide unprompted); the open-world Explore hub fishing would surface in is itself a Phase-2-ish design effort (no clean hub exists yet). So fishing is **paused on owner input**, not a current empty-fire lane. **▶ Next ungated startable (THIS run picked it) = the owner-directed repo-consistency-linter (Q-0170)** — `scripts/check_consistency.py`, "CI but for UX/interaction inconsistencies", built one rule per PR ([plan](planning/repo-consistency-linter-plan-2026-06-17.md)). **PR 1 (harness + rule 1 edit-in-place) shipped #1042; PR 2 + 3 (rule 2 back-button presence + rule 3 panel base-class) shipped #1043; PR 4 (rule 4 select-option truncation) shipped #1044** — first-run counts back_button=7 (mostly top-of-stack hub openers, the known external-attach FP), panel_base_class=30 (the AI picker / settings-select / btd6-admin direct-`discord.ui.View` extenders), **select_option_truncation=53** (the #1040 silent-drop class is *widespread*: shared `selectors/`, roles/channels panels, mining market, btd6 browsers, settings enum-editor all front-`[:25]`-truncate select options; a small subclass are genuine top-N *display* truncations to allowlist), all warn-only. **The plan's rule backlog (1–4) is now built, and the select-truncation triage is UNDERWAY (PR #1047, 2026-06-18).** #1047 built the **shared `views/paginated_select.py` `PaginatedSelectView` primitive** (a reusable windowed select + Prev/Next nav, generalising the two bespoke implementations `_CogPickView` + `EntityPickerView`), dogfooded it on cog-routing, migrated the **role-delete picker** onto it (real >25-roles bug fixed; retired the direct-`discord.ui.View` `_DeleteRoleView`, ratcheting `panel_base_class` 30→29), and **triaged the 53 `select_option_truncation` candidates → 31 genuine** (allowlisted 22 false-positives — embed/text top-N displays + bounded fixed-catalog selects — with per-callback reasons in `consistency_exceptions.yml`). It also **fixed a latent linter bug**: `rule_select_option_truncation` now computes the enclosing class/method qualname (was `''`), so the documented `::Class.method` allowlist scoping actually works. **The standalone-ephemeral pickers shipped #1048 (2026-06-18):** the three cleanly-standalone single-select ephemeral pickers moved onto `PaginatedSelectView` — `settings/edit_enum` (`EnumSettingSelectView`/`_EnumSelect` → `build_enum_select_view`), `roles/time_roles_panel` (`_TimeRemoveView`), `roles/xp_roles_panel` (`_XpRemoveView`); each retired **both** its `select_option_truncation` (31→28) and `panel_base_class` (29→26) finding and ratcheted `baseview_inheritance` arch debt 12→9. **▶ The embedded-windowing design step is now BUILT (#1050, 2026-06-18)** — `views/paginated_select.py` exposes `attach_windowed_select(view, options, on_select, …)` + the shared `SelectWindow` controller (windowed `Select` + ◀/▶ nav as a *band* of items inside any host view, removing only its own items on a page flip). #1050 triaged the 28 candidates → **15** (dogfooded the helper on `access_map`; allowlisted 12 fixed-catalog btd6/mining selects). **▶ Next consistency-linter slice = migrate the 15 remaining genuinely-dynamic embedded selects onto `attach_windowed_select`** — the **shared `views/selectors/` primitives** (`role`/`channel`/`multi`/`multi_role`/`subsystem`: this is the **API-ripple set** — they are `discord.ui.Select` subclasses added via `view.add_item(...)`, so windowing them means converting each to an `attach_*` helper + updating its ~8 consumers (channels delete/visibility/create/restrict/move panels, roles xp/time/exemptions panels); do this as one focused PR), then the **per-panel** ones with their own row budgets (`channels/move_panel`·`visibility_panel`·`create_panel`, `settings/subsystem_view` edit/reset selects, `setup/sections/channels`, `access/explorer`, `diagnostic/automation_panel`). Each per-panel migration is a small swap now the helper exists (pass `select_row`/`nav_row` to fit the host's 5-row budget — see `access_map._attach_feature_detail_select` for the pattern). The other graduation work stands: (b) once a rule runs quiet on a clean tree across a few sessions, flip it to error + wire it into `code-quality.yml`; (c) add rule 5+ only as a fresh mechanical-consistency shape surfaces (forced filler ≠ work); a possible follow-up is extending rule 4 to `disbot/cogs/`. An empty fire with no triage appetite should take a fresh PLAN-FIRST lane instead. (Mining is built/owner-gated; exploration's `!explore` shipped #606 — neither is the shortage.) Historical queue follows: the **[band-#1020 decade queue](planning/reconciliation-pass-2026-06-17-band1020.md)** §4 — the eleventh Q-0107 pass (2026-06-17, issue #1021; cadence every 30th PR per Q-0134). **▶ moderation-DM config SHIPPED (#1023, 2026-06-17)** — per-action moderation DMs on the *existing* `moderation_service` seam (`dm_actions` allow-list gating the `dm_on_action` master switch, off by default, default = all four notify-eligible actions so behaviour is unchanged; Q-0147). **▶ Next ungated startable = pick a fresh PLAN-FIRST lane** (image-mod #941 + security tiers #929 stay `needs-hermes-review`; the BTD6 deterministic-floor lane is thin/complete; the dashboard write/manifest lanes are owner-paced). **▶ paragon-ability + boss tier-HP floors SHIPPED (#1024, 2026-06-17)** — the two BTD6 deterministic-floor shapes current-state previously named as still-valid empty-fire candidates (`deterministic_paragon_ability_roster_reply` off the curated `paragon_abilities.json` + `deterministic_boss_hp_comparison_reply` off `bosses[].tiers`/`.elite_tiers`, both on the `_BTD6_LIST_BUILDERS` seam, BUG-0009 class). **The proven ungated BTD6 floor lane is now essentially exhausted** — rosters/comparisons/immunity/abilities for towers/heroes/paragons/bosses/MK/relics/bloons are all covered; a further empty fire should prefer a fresh PLAN-FIRST lane over inventing a low-value floor (forced filler ≠ work). The dashboard **manifest-spine PR4** (panel-layout editor) is owner-paced (control-API write side); the AI deterministic-floor family is COMPLETE (night queue fully consumed, #1008–#1012); image-mod #941 + security tiers #929 are open `needs-hermes-review` carve-outs awaiting a human merge. **▶ dashboard.json freshness reporter SHIPPED (#1025, 2026-06-17)** — the #1020 finding/idea: a warn-only structural-drift reporter (`check_dashboard_data.py --drift`, compares cog/command/env/setting/catalogue/synonym *identifier sets* only, never the volatile churn) + regenerated the stale committed `dashboard.json` (it was missing env-vars `HEALTH_HOST`/`RAILWAY_GIT_COMMIT_SHA` and setting `moderation_dm_actions`) + routed the cadence-regen to the docs-reconciliation routine. **▶ generated-artifact freshness umbrella SHIPPED (PR #1027, 2026-06-17)** — generalized #1025 into `scripts/check_generated_artifacts_fresh.py`, a registry-driven warn-only umbrella over all three committed-generated families (dashboard.json → delegates to `check_dashboard_data --drift`; `env-vars.md` → env-var name set; `docs/agent/generated/*.context.md` → per-pack line set, date line dropped), so no future generated file silently rots; Q-0105 dev tooling (read-only/stdlib/disposable), **not hard-CI-wired** (ask-first; `--strict` is for the reconciliation cadence pass). **▶ Next ungated startable still = a fresh PLAN-FIRST lane** (the AI §7 next workflow family post deterministic-floors, or the Hermes bug-triage `gh issue create` write Q-0121 — design write-scope first); the BTD6 floor lane is exhausted, dashboard write/manifest is owner-paced, image-mod #941 + security #929 stay `needs-hermes-review`. *(The historical context that follows is a prior-band snapshot — trust this line + the Recently-shipped list.)* The band-#930 queue is fully executed (AI §7.5/§7.6 floors #946/#950/#955/#962/#975 · myprofile #938/#940 · security tiers #929 · diagnostics #937 · architecture-atlas Q-0151 #957/#958/#960/#964) and the **developer-dashboard / control-API initiative is the active thread** (#974/#990/#993/#995, Q-0155–Q-0160); its read-only surfaces all shipped, the next slices are owner/creds-gated (live editor · auth · Railway-API). The band-#900 queue is nearly fully executed (Forge #905 · P1-3 #917/#918 · log-triage #906 · Home/respec/titles #910/#912 · BUG-0009 #924/#926 · welcome #920); security tiers 1+2 is in flight (#929). **The mining structures / skill-tree lane is now COMPLETE** — every ▶ startable slice shipped (D #891 · A #897 · B/Forge #905 · C/Home #910 · E respec-polish + F titles #912); the only remaining items are owner-gated (Vault-cap *hard* enforcement · ⛔ V-16 phase 2 real sprites). **The Railway log-triage skill shipped (#906) and P1-3 invariants are now SUBSTANTIALLY COMPLETE (#917, 2026-06-15).** The 2026-06-15 P1-3 pass reviewed all four tracks, found + closed the **two** genuine buildable-now gaps with CI-runnable AST invariants — **settings** declared→runtime-consumer parity (`test_settings_declared_vs_consumed_parity.py`, 0 dead of 63 declared settings; the explicitly-named missing invariant from the settings map §Required #3) and **games** wager write-boundary completeness (`test_two_sided_economy_calls_are_accounted_for` — the hardcoded `_WAGER_FILES` fence now also fails on a *new* two-party mint path). **AI** is substantially-covered by the 34/34 catalogue/eval ratchet (closed, no new invariant); **BTD6** source-provenance is invariant-covered and uniform per-derived-value attribution is a documented design-for-review residual (brittle as an AST guard). Full record: [the P1-3 disposition](planning/production-readiness/p1-3-contract-invariants-disposition-2026-06-15.md). **The safety quick-win shipped (welcome phase 2 PIL cards, #920, 2026-06-15):** a `welcome_card_enabled` toggle (off by default) attaches a rendered PIL greeting card to the join embed; the `render_welcome_card` prototype graduated to `utils/welcome_render.py` (the UX-lab gallery now re-exports the production renderer — one source of truth); degrades cleanly to embed-only when Pillow is unavailable. **BUG-0009 slice 1 shipped (#924, 2026-06-15): the "MK related to <tower>" family** — the model no longer assembles that list (it grabbed the whole Support *category* and mislabeled it farm-related); `btd6_data_service.monkey_knowledge_referencing` derives the MK↔tower relation deterministically (description names the tower's canonical/upgrade-path name → strong; alias → weak, suppressed when another tower is strongly referenced or the MK is a Powers/Heroes-tab point), served as a **pre-emptive floor** on the BTD6 path (this class *passes* the value-only faithfulness guard, so the post-hoc roster floor never caught it). **BUG-0009 slices 2 + 2b shipped (#926, 2026-06-15): the "Geraldo items per level" + "game mode groupings" families** — the model no longer assembles either grouping. Geraldo: `btd6_data_service.geraldo_items_by_unlock_level` owns the level→items map, `deterministic_geraldo_per_level_reply` formats the full grouping / a single level's unlocks / an honest "nothing unlocks at level N". Modes: `btd6_data_service.modes_by_kind` owns the difficulty→mode→modifier grouping (the owner's "mode groupings" miss — CHIMPS is a mode, not a difficulty), `deterministic_modes_reply` fires on a clear modes enumeration and defers when "mode" is a qualifier on another entity. All three BUG-0009 builders now front one dispatcher `deterministic_btd6_list_reply` served as the pre-emptive BTD6 floor (MK → Geraldo → modes). **Next ▶ startable = security service tiers 1+2** (decade-queue slot 9, plan-first — raid detection + account-age filter, Q-0111; cite `ux/pattern-library.md` `mock_security_*` pattern_ids). *(BUG-0009 slice 3, newest-towers ordering, is **data-gated** — `towers.json` carries no release-order field; needs sourced release-order data first via the ADR-006 / `!btd6ops seed-data` provenance lane, then append its builder to `deterministic_btd6_list_reply`.)* · then security service tiers 1+2 (slot 9, plan-first); the remaining P1 (absence-guard Layer B · live-quality battery) stays **creds/review-blocked**. *(Pointer references the pass by name, never by a PR-number range — a range here silently masks the band from the ledger guard; see [the band-#800 pass §6](planning/reconciliation-pass-2026-06-13-band800.md).)* **The P0 integrity spine, P1-2, AND P1-1's deterministic half are now COMPLETE** — the versioned AI eval/smoke matrix (offline, CI-gated, #878), its self-cleaning drift guard (#879), and the first BTD6 hotspot coverage (#881, ratchet 8→14/34 tools). **Remaining P1 (where the next session starts): P1-3 is now SUBSTANTIALLY COMPLETE (#917)** — see the disposition linked above. **AI tool-surface eval coverage is COMPLETE — 34/34** (the final 7 BTD6 lookups landed; `_ACK_UNCOVERED_TOOLS` is empty and the drift guard now fails closed on any new tool). What remains on P1-1 is **creds-gated** (live-quality battery) or **design-for-review** (absence-guard Layer B), so the next *offline* plan step is **plan-first BUG-0009** (the safety quick-win — welcome phase 2 PIL cards — shipped in #920) · then the **creds/review-blocked** P1-1 remainder (live-eval battery · absence-guard Layer B). **The production-hardening P0 integrity spine is now COMPLETE** (P0-2 ✅, P0-3 ✅, P0-4 ✅ — every gating decision answered): **P0-4** (channel-ownership convergence, Q-0100) — PR 1 (#820) clone + permission-overwrite, PR 2 (#825) ad-hoc channel creation + category lifecycle through `ChannelLifecycleService`; **P0-2 media retention (Q-0099, #829)** — bounded metadata projection at the cache write + the scheduled `MediaMaintenanceCog` purge owner + thumbnail-URL validation; **P0-3** (delegated-Setup apply, #817). **The standing priority is the P1 correctness tier. P1-1's offline/CI half + P1-2 are done (above); next = P1-3 invariants + continued eval-coverage expansion, then the creds/review-blocked P1-1 remainder** (live battery · Layer B, relates BUG-0009). P0-2 follow-ups: **content-free media diagnostics now SHIPPED** (PR #854 — `!platform media` + the `media` diagnostics provider + cache-health/provider-outcome counters, content-free); the remaining two (provider-execution hardening · maintainer live-verification) stay queued behind P1-1. **P0-3 is complete: arc PR 3 shipped the delegated-Setup apply authority (Q-0098) in #817** (arc PR 2 retired the XP-announce + economy-log scalar pointers in #794; arc PR 1 foundation #777). **The owner's active strategic thread is the [portable substrate-kit](planning/portable-substrate-kit-extraction-2026-06-13.md)** (OSS agent-memory/workflow package; PR 1a+1b DONE, resume at the 1b tail → PR 2) — it consumed the #781–#800 band and runs in parallel as owner-steered. The safety/community band (slots 4–6: #772/#774/#775) is **COMPLETE**; its remainder (security tiers 1+2 · image-mod) is plan-first behind the P0 spine (welcome phase 2 shipped #920). Product lanes (mining/BTD6/AI) stay open as owner-steered alternates. The full scorecard + deferred list live in the queue doc; [`roadmap.md`](roadmap.md) stays the index, now organised **by sector** (S1–S5 dispatch queues). **Status is per-lane below — a session edits ONLY its own lane's bullet** (convention: [`owner/ai-project-workflow.md`](owner/ai-project-workflow.md) §9 "Cross-cutting ledger discipline"). **Owner-teed sector mapping DONE (2026-06-14, PR #877):** the roadmaps/plans are now organised under the **S1–S5 planning sectors** as **per-sector dispatch queues** — each sector a Hermes-dispatch target (name a sector + an action, read its live `Now`) — [`roadmap.md`](roadmap.md) § "By sector — the live dispatch queues" + the dispatch contract in [`repo-sector-map.md`](repo-sector-map.md) § "dispatch targets"; the [brief](planning/next-session-sector-roadmap-mapping-2026-06-14.md) is executed. Hermes/routine *wiring* stays Q-0137 Thread 1 (owner-undecided). **#704 live-test screenshots triaged + closed** (2026-06-14): mostly-working bot; one AI capability/grounding-consistency finding feeds P1-1 — [`audits/pr704-live-test-triage-2026-06-14.md`](audits/pr704-live-test-triage-2026-06-14.md).
>
> - **Consolidated batches:** **Batches 1–8 ALL executed + verified merged 2026-06-10** ([EOD verification](audits/past-day-verification-2026-06-10.md)) — #650 truth/clarity · #651 surface-classification invariant · #652 service boundaries · #654 Settings Phase 2 core · #656 adaptive P1C subpanels · **#657 Help projection seam** (HLP-2: `services/help_catalogue.py` + `services/help_projection.py`, all five render paths on one reason-coded `HelpProjection`; Q-0074 executed in the same PR) · **#659 HLP-3 guild overlay** (migration 064 `help_overlay`, audited `help_overlay_mutation` seam, cached read model, hide/rename through every render path; Q-0055 display-only pinned by an admission import fence) · **Batch 7 via the mining stack** (#661 + #663/#664/#665 → #667) · **Batch 8 = the #649 cutover**. **The queue-remainder session (PR #671, merged 2026-06-10) executed the RS07 chain-service slice** (audited `services/chain_service.py`, Batch 3 pattern, repo-wide write fence) **+ Batch 9's RS08 slice** (diagnostic read models out of the cog layer; new no-raw-SQL-in-cogs/views invariant) **+ the EOD audit's Tier-2 Help-Preview fix** (now consumes `project_help_with_execution`); **its continuation (PR #672) completed Batch 4** (proof-channel binding/resource declaration + binding-first read; logging rows verified satisfied) **and executed the Batch 10 selections** (wizard PR1–PR3 tranche verified shipped via #435 → setup-lane next = PR4 `/myprofile` planning session; next AI §7 family = **§7.5 multi-entity comparison**, sequenced after the maintainer's prod check — banners in the two plans carry the evidence). **The Help overlay editor UI executed 2026-06-10 ([plan](planning/help-overlay-editor-ui-plan-2026-06-10.md) → PR A #677 + PR B #679, both MERGED same day):** the hide/rename/re-describe editor (staff-hub `✏️ Help editor` button + the Settings-hub "Help appearance" domain group, 13th group) and the Q-0059 Home-message embed builder (migration 067, **mandatory preview**, shared `home_embed_frame` composer, byte-identical default pinned) — both live-verified on real Postgres. **Batch 9 then executed in PR #681** (open at write time): the RS05 publish-accepted delivery contract (runtime_contracts §2) + bus delivery stats / failure metric / the `event_bus` diagnostics provider, and the RS10 economy view family onto BaseView (conformance ratchet 17→13, arch warnings 84→80). **The consolidated plan's queue is FULLY EXECUTED (Batches 1–10; #681 MERGED).** A follow-on slice (PR #682, open at write time) migrated the **mining family** onto BaseView — the last true lifecycle-duplication family; ratchet 13→11 with a disposition note (remaining direct-View entries are ephemeral pipeline-gated follow-ups / bespoke admin checks, not RS10 duplication). **The PR4 `/myprofile` planning session ran (PR #684, open at write time):** [`planning/myprofile-foundation-plan-2026-06-10.md`](planning/myprofile-foundation-plan-2026-06-10.md) — §6 backend re-verified exact (4 audited pipeline entrypoints, typed accessors, schema registry, zero UI callers); PR A = read-only profile card (zero writes, turn-key) · PR B = the pipeline's first UI consumer · PR C onboarding **gated** on an owner decision; Q-0080 stranger-grade envelope applied throughout. Remaining plan-first/gated: Help audit Phase 4 records (Q-0057 rider) · AI §7.5 (post-eval).
> - **BTD6 data + answerability:** the `--all` cutover **#649 merged 2026-06-10; post-cutover VERIFIED + every carry-forward DECODED the same day** (#653 wave 1 ∥ PR #655 — dump fidelity byte-identical · 2,022 menu embeds in-limits · AI battery green · `_CUTOVER_CARRYFORWARD` empty, audit 91 CLEAN / 0 DELTA / 0 SUSPECT · banana economy answerable · fixes for mode-rules dark data / `!btd6 diagnostics` 400 / stamp-rot / path leak); **answerability items 5+6d shipped in PR #658**; **the Navarch "no coins" live miss diagnosed (missing ROUTING, not data) + fixed end-to-end with items 6a–c — #662 MERGED 2026-06-10** (paragon grounding gains income + effect lines · article-tolerant/shorthand paragon names · minion-name → owner grounding ("Mini Sun Avatar"/"Crushing Sentry"/UAV) · Pouākai diacritic-fold · honest dataset source labels/summary); follow-up slice **#666** adds `scripts/btd6_probe.py` (grounding triage) + structures item 7 into [`planning/btd6-conversation-grounding-plan-2026-06-10.md`](planning/btd6-conversation-grounding-plan-2026-06-10.md); **item 7 slice 1 (conversation carryover) + the zero-fact sweep fixes (ranking rosters · bare distinctive shorthand) shipped same day in #668**. **The 2026-06-11 morning screenshots (3 live AI-knowledge misses) fixed end-to-end in PR #703** — BUG-0002 (elite boss HP: dataset had no elite figures + boss names never routed BTD6 → standard table served as "Elite"; elite_tiers backfilled from the pinned v55.1 dump for all 7 bosses, boss canonicals route + name-index, variant-labeled grounding) · BUG-0003 ("despos on impop" hallucinated as PMFC; impop/despo keywords, Desperado alias, resolver plural fold, the `<quantity> <crosspath> <tower>` pricing leg — "10 041 despos" = ten 0-4-1s, owner-corrected) · BUG-0001 recurrence (round-cash refusals in #general: the workflow was profile-gated OFF on default channels — compatible_default/balanced_helper now declare analyze_execute_verify (Q-0048), matcher gained the money-question gate + by-round anchors). **Owner action: run `!btd6ops seed-data` after the deploy** (bosses/towers json are blob-lane data; owner-confirmed done 2026-06-11 ~12:38 — despos answers correct in prod). **The live re-test round shipped in PR #706 (merged 2026-06-11):** BUG-0004 (r-shorthand rounds + "end of r53" start shift — the $71,315.20 cumulative mislabel; truth $56,318.70) + the bulleted capabilities list (owner format ask; boss_health/crosspath/projection rows advertised). **The absence-claim guard's Layer A (path/line-aware retrieval) shipped in #855** — `<tower> <top|middle|bottom> path` phrasing now grounds its whole tier line instead of resolving to nothing (the canonical false-"no" trigger removed at the root); Layer B (the negative-existential gate) stays design-for-review. **Next:** decode-status ⭐ item 3 (buff/zone tail, demand-driven) + item 4 (maintainer live spot-check) · P1-1 eval-smoke matrix (creds-gated) + absence-guard Layer B.
> - **Gated:** the Q-0036 denial-copy wiring stays gated on the maintainer's markup of the #632 table.
>
> *(The 8-lane scoreboard completed 2026-06-09/10 — record: [`planning/multi-lane-execution-plan-2026-06-09.md`](planning/multi-lane-execution-plan-2026-06-09.md), now `historical`.)*
>
> 1. **Mining character platform** — **the 2026-06-10 finalization session executed Batch 7 + the Wave-2 seed in one 4-PR stack — all four merged 2026-06-10:** **#661** (RS01 — atomic shop-purchase workflow + the Q-0071 transaction plumbing) → **#663** (RS02 stage 1 — pure domain relocated to `utils/mining/`, `services/mining_workflow.py` owns the workshop ops, views→cogs allowlist entries deleted) → **#664** (RS02 stage 2 — *every* mining write behind the workflow service, one transaction per op; AST ratchet; recipes.json reconciled to the catalog under a new alignment lint — **Batch 7 COMPLETE**) → **#665** (shared **game-XP** service + leaderboards + depth records (migrations 065/066) · **deeper ladders** incl. the diamond lantern that makes MAGMA reachable (it never was) · Gear panel + Recipe browser + fuzzy names + `!fastmine` · **duels gear wear — Q-0054 CLOSED** · PIL inventory + stat cards). Session decisions: **Q-0075** (curated economy + deeper ladders) + **Q-0076** (both PIL cards) — router §32. *(Merge mechanics note: the stacked bases didn't auto-retarget, so #663/#664/#665 merged into their parent branches — the content reached `main` via the same-day completion PR **#667**, content-verified EOD; migrations renumbered 065/066 around #659's 064.)* Earlier Wave-1 chain: #606–#610, #624. **The V-16 phase-1 gear slice shipped 2026-06-11 (PR #702, full Q-0092 scope):** 9-slot set-piece model (+ migration 068 legacy fold) · same-tier set bonus with set-aware Equip Best + "breaks set" picker warnings · bronze/silver ores · sim-pinned numbers ([record](planning/gear-set-numbers-2026-06-11.md)) · picker stat previews · the paper-doll compositor (placeholder sprites; owner pack drops into `disbot/assets/gear/`). **§7.5 structures started: the Vault (safe stash) shipped 2026-06-14 (#884)** — `mining_vault` (migration 070) + the audited deposit/withdraw/stash-all ops + a `🏦 Vault` panel; v1 is a pure safe store; **Slice A — Vault v2 (the cap sink) shipped 2026-06-15 (#897)**: a pack soft-cap (distinct item-types, warning-only — never blocks mining) + an upgradeable vault capacity (`!vaultupgrade` coin sink, migration 072 `vault_level`), pure cap math in `utils/mining/capacity.py`. **The §7.4 capped skill tree (the marquee) shipped 2026-06-15 (#891)** — `player_skills` (migration 071) + `services/skill_service.py`; four branches capped so you can't max all (forced specialization), points from the game-XP level, merged into `EffectiveStats` via `utils/mining/character.py` (byte-identical when empty), `🌳 Skills` panel + `!skills`/`!skill`. **Slice B — the Forge (gear-tier crafting gate) shipped 2026-06-15 (#905)**: a built structure (coin + material sink) on the generic `mining_structures` table (migration 073, reused by Slice C) — gates the **top two** gear tiers (gold → Forge I, diamond → Forge II; bronze/iron/silver gear + tools + structures stay forge-free, so most play is unchanged), pure `utils/mining/structures.py`, audited `mining_workflow.build_structure`, `🔥 Forge` panel + `!forge`. **Next slices stay turn-key + ▶ startable** in [`planning/mining-structures-skill-tree-plan-2026-06-14.md`](planning/mining-structures-skill-tree-plan-2026-06-14.md): respec-polish / skill-titles (E/F, now unblocked by #891) · **Home** (C, reuses the structures table) · the Vault-cap *hard*-enforcement follow-up (A, owner-gated). [Slices D ✅ #891 · A (Vault v2 soft-cap) ✅ #897 · B (Forge) ✅ #905.] **⛔ V-16 phase 2** (paper-doll real sprites) stays owner-blocked on the PNG pack. Route in: that plan + `docs/ideas/mining_exploration_brainstorm.md` §7.7 + the games folio.
> 2. **Adaptive Setup/Access platform** — Phase 0 complete; Phase 1 underway: Q-0026 identity repair + Phase 0 contracts **#588**, P1A Access Map projection **#589**, P0C groundwork **#591**, P0C seam conversion + P1B `routing_access_conflict` **#592**; **P1B remainder shipped in #632 (2026-06-09, execution-plan Lane 2 — verify merged on live GitHub):** the Q-0045 governance tier-input path (`GovernanceContext.member_tier`, declared tier preferred verbatim, simulation-labeled per §16.4) + the `help_advertises_locked` drift provider + the full Q-0036 denial-copy **draft** (in the PR body for maintainer read-through — **not live-wired**; wiring follows his markup). **P1C merged 2026-06-10 (consolidated plan Batch 5, #656):** Access Map + Help Preview shipped as **staff-hub subpanels, no new command names** (Q-0032), on the tier path as-is. **The Batch 6 Help projection seam consumed this lane 2026-06-10 (#657, merged):** Help's five render paths now compose governance + the projection contract end-to-end (`services/help_projection.py`, incl. an execution-enriched mode over `access_projection`). **Next: P2** Feature Profile preview (own planning first). Q-0028–Q-0031 + Q-0033 are also **answered** (catalogue committed · availability owns quiet mode · snapshots compound+high-risk · risk policy approved · account links deferred — router §20). Route in: plan §16.8.
> 3. **AI tooling (orchestration + answerability)** — orchestration Phases 1–3 shipped (**#612**, **#618**, **#619** — including the gate-lifted `ai:tools` Tools & Workflows operator UI; default byte-identical); answerability Phase 1A/1B (**#612**, Q-0043: range cash **inclusive**) + Phase 2 read model (**#616**) shipped. **Orchestration Phase 4 MVP (Q-0046) built 2026-06-09 in PR #634** (execution-plan Lane 3, parallel session): the round-cash plan→execute→verify workflow + the one typed answer-with-evidence contract, profile-gated, default byte-identical — **model loop awaits the maintainer's production check** (no sandbox provider key). **Answerability Phase 3 shipped 2026-06-09 in PR #639** (execution-plan Lane 4, **Q-0047**): the three read-only self-awareness tools — `get_ai_tool_catalog` ("what can you do here?") · `get_ai_policy_explanation` ("why didn't you reply?") · `btd6_answerability` ("what BTD6 data do you know?") — audience-tiered **at construction** over the #616 read model; **model loop awaits the maintainer's prod check** (no sandbox key). **Next:** the remaining orchestration §7 workflow families; answerability Phases 4/5 stay gated (settings UI per-exposure ask · dashboard schema acceptance). Standing posture **Q-0048**: read-only deterministic tools ship without a per-case ask; writes/external/UI stay per-exposure. Plans: [`ai/ai-complex-request-tool-orchestration-plan.md`](ai/ai-complex-request-tool-orchestration-plan.md) · [`planning/ai-btd6-answerability-roadmap-2026-06-09.md`](planning/ai-btd6-answerability-roadmap-2026-06-09.md). **The first Q-0086 joint live session ran 2026-06-11 (PR #707): the model-loop gate is LIFTED** (keys in agent sessions; full loop verified on both providers); BUG-0005…0008 fixed live (tool quantity laundering · carryover routing/forcing · conversation-meta floor copy + guard haystack · farm/possessive/double-cash routing); **BUG-0009** (claim assembly) OPEN in the [bug book](health/bug-book.md); **BUG-0010 (ABR qualifier) FIXED same day in the follow-up slice (PR #709** — shared ABR cue → grounding round legs + the round-cash workflow compute/label the ABR set, modifier honesty deterministic**)**; **Q-0094** (memory floor canon) + **Q-0095** (Haiku-4.5 allocation for the two NL tasks · the guild-default-provider trap · sandbox floor-testing posture) recorded; the owner-requested **AI panel rework** captured ([idea](ideas/ai-panel-inplace-navigation-2026-06-11.md)). Gear/mining (#702) is still never owner-played — the eval-checklist Tier 2+ walk stays queued.
>
> Cross-cutting: **Community Spotlight** (side-lane **#613**/**#614** + hotfixes **#615**/**#617**) was hardened in the review session (canonical `utils/db/xp.py` read, `member_count` crash fix, first tests) and **Q-0044 is executed**: the Q-0025 `scripts/new_subsystem.py` scaffold was built and used to register Spotlight as a `community`-hub child (**#626**, 2026-06-09 — execution-plan Lane 1; merged, verified live), and the `!hub`/`!server` aliases were **dropped same day** (kept `!spotlight`/`!activity`). Also decided: BTD6 data-refresh automation = **manual-dispatch workflow** (Q-0049 — **built same day in #633**, execution-plan Lane 5: `workflow_dispatch`-only, opens a reviewable PR, never pushes to main); mining descent lights **permanent, owner-confirmed** (Q-0050); the five product-vision questions (Q-0038–Q-0042) got their **draft-answer session** (Q-0051) **and the maintainer marked all five up same day (Lane 6, PR #631, structured choices)**: Q-0038 server-scoped clans, Q-0039 cosmetic-only donations (no bot-side billing), Q-0041 YouTube-first/dual-opt-in/voice-deferred, Q-0042 staged-Someday website — all approved as drafted; **Q-0040 adjusted: the AI dungeon master picks quests/rewards/difficulty from bounded, hard-capped menus** (not pure narration, not free-form authority). Posture decisions only — every lane still needs its own plan/promotion + the AI per-exposure lift; conclusions routed to the four roadmap drafts + router §21. Full repo review: [`audits/repo-review-2026-06-09.md`](audits/repo-review-2026-06-09.md) · agent-memory system review (did the orientation/memory system work in practice?): [`audits/agent-memory-system-review-2026-06-09.md`](audits/agent-memory-system-review-2026-06-09.md).
>
> **Last updated:** 2026-06-15, **ninth Q-0107 reconciliation pass (the band-#930 cadence fire,
> issue #931)** — scored the band #901–#930 against the band-#900 queue: **the planned decade queue
> nearly fully executed** — Forge ✅#905 · P1-3 invariants ✅#917/#918 · Railway log-triage ✅#906 ·
> Home/respec/titles ✅#910/#912 · BUG-0009 slices 1/2/2b ✅#924/#926 · welcome phase 2 ✅#920;
> security tiers 1+2 **in flight** (#929, `needs-hermes-review` carve-out); the buffer was the Hermes
> gpt-5.4-mini model-swap + ops-docs band (#915–#930). Reconciled the ledger (added the #915–#928
> docs band as one grouped entry; archived #862/#859/#855), **fixed a control-plane drift** (the Gates
> section claimed the loop had "never self-fired" — issue #931's `menno420` author proves ROUTINE_PAT
> is set and the loop self-fires; matched it to the canonical control-plane table), planned the next
> band ([band-#930 decade queue](planning/reconciliation-pass-2026-06-15-band930.md)), **promoted the
> games-economy faucet/sink diagnostic idea → a turn-key plan** (its sink-heavy gate cleared by respec
> #912 + structures), re-badged the band-#900 pass `historical`, disposed the one open PR (#929,
> left for Hermes review), and reset the marker #900→**#930**. No new runtime bugs. ·
> 2026-06-15, **eighth Q-0107 reconciliation pass (the band-#900 cadence
> fire)** — scored the band #871–#900 against the band-#870 queue: **slot 2 over-delivered** — P1-1's
> entire **offline eval half shipped** (#878→#896, AI tool-surface coverage **8 → 34/34 FULL** + the
> self-cleaning drift guard), proving last pass's "split the gated slot, ship the buildable half" fix
> worked; the buffer again *became the band* via three owner-steered threads (mining structures
> #884/#891/#897 · routine-consolidation/sector-dispatch #877/#880/#882/#899/#900 · loop hygiene).
> Reconciled the ledger (#898 folded into the loop-hygiene entry), planned the next ~9 PRs
> ([band-#900 decade queue](planning/reconciliation-pass-2026-06-15-band900.md)) — **next ▶ = mining
> Forge · P1-3 invariants · Railway log-triage skill** — re-pointed the live queue + roadmap Now,
> re-badged the band-#870 pass `historical`, disposed the one open PR (**#893**, the owner's mining
> handoff — left for the owner), reset the marker #870→**#900**, and **acted on the band-#870 §6
> escalation rule**: the substrate-kit (now its **fourth** carry) is **demoted from the plannable
> queue to the owner-action list** — the generalized new rule being *an `owner`-gated slot that
> carries four bands leaves the decade queue* (§6). No new runtime bugs. ·
> 2026-06-15, **routine fleet consolidated to 2 — dispatch absorbs the
> night-executor (PR #900-ish, Q-0145)** — owner directive: the dispatch + night-executor routines
> always did the same job (advance the plan); dispatch is just the steerable one, so they are now
> **one execution routine**. Merged their (already-identical, Q-0144) prompts into the single
> **dispatch** prompt (`hermes-dispatch-bridge.md`), which absorbed the executor's bug-book orient +
> bounded-continuation handoff; the `autonomous-routines.md` night-executor section → a pointer; fleet
> + label tables de-staled. **2 routine prompts now: dispatch (all execution) + docs reconciliation.**
> Trigger (Q-0146, 2026-06-15): dispatch's cadence is the Claude Code console **Schedule** trigger —
> every **2h**, cron `0 */2 * * *`, owner-enabled — superseding the Hermes-VPS-cron / GitHub-`schedule:`
> plan (both unreliable for cadence); the legacy `executor-nightly.yml` was removed 2026-06-15. ·
> 2026-06-15, **routine-prompt canon — foolproof, completion-biased, idea→plan
> (PR #899, Q-0144)** — owner-directed in-session: rewrote the dispatch + night-executor routine
> prompts onto the owner's 12-step lifecycle and made them foolproof against bad dispatch input (the
> "write a story about chickens" test). Now explicit in every routine prompt: **never-stop /
> completion bias** (a routine always ships *something real* — the dispatched work or the next plan
> slice), **sync-first** (stale clone was a named Hermes failure), **work-order-is-a-hint** (a
> dispatched order = owner asking = build it; off-plan nonsense → do the plan instead; never invent),
> the **scope-brake vs safety-brake** split (the phase gate is a scope brake for self-invented features
> only — it does **not** apply to dispatched work; irreversible safety brakes never bend), **2–3 slices
> bounded by ~700K tokens** (§10 updated), born-red mock PR, judgment-over-plan, bugs-first, and the
> standing enders. The **reconciliation** routine gained the owner's **idea→plan promotion**: when
> plans run low on executable work, promote the best `docs/ideas/` entry into a complete executable
> plan. The in-repo prompts are the canonical mirror — **owner re-pastes them into each routine's
> console config to take effect.** Docs only. ·
> 2026-06-14, **sector tooling — the partition is now self-maintaining (PR #882)** —
> closed the loose ends from the dispatch work: `scripts/check_sector_map.py` (validator — folio homing
> + executor + startability convention, was prose-asserted) and `scripts/dispatch_menu.py` (resolver —
> the machine version of the dispatch test: per sector, the first ▶ startable item + executor, flags a
> starving/blocked sector). Both stdlib, read-only, disposable (Q-0105), tested (19 tests); not CI-wired
> (ask-first). Building `dispatch_menu` caught a real convention bug (a ▶ glyph used in S2 `Now` *prose*,
> not as an item tag) — fixed. CI green (9664); arch 0. **(PR #885 same session captured a
> dispatch-resolution idea — `dispatch_menu --json` + Hermes wiring — and a checker-with-convention
> rule.)** ·
> 2026-06-14, **dispatch contract sharpened — executor dimension + startability tags
> (PR #880, Q-0143)** — a live dogfooding test of the sector dispatch structure (owner-requested) passed
> on speed (2–3 hops/sector, links resolve, the index ranks, a stale `Now` self-corrected in one hop)
> and surfaced 3 findings, all built into one docs PR: a complete dispatch is now **sector + action +
> executor** (Claude-in-repo / Hermes-VPS / maintainer — **S5 is the executor outlier**), each `Now`
> item carries a **startability tag** (▶/⛔/👤), and S1's `Now` was de-drifted for #878 (offline
> eval/smoke matrix shipped). Homes: `repo-sector-map.md` § dispatch targets + `roadmap.md` per-sector
> `Now`. ·
> 2026-06-14, **roadmap restructured by sector → dispatchable per-sector queues
> (PR #877)** — owner-directed; the next-session sector-mapping brief executed. `roadmap.md` is now
> organised under the **5 planning sectors** (S1–S5, Q-0137): a **per-sector dispatch index**
> (Now/Next/Later each) is the new top layer, and the former "Agent ecosystem" lane is split into its
> real sectors — **S3** (mechanism) / **S4** (docs content) / **S5** (operations) — populating the two
> previously-thin sectors so **every sector has a live queue** (the Q-0137 deep-clean terminal
> condition). Added the per-sector **dispatch contract** (what *plan* / *execute·continue* mean) to
> `repo-sector-map.md`, and reconciled the planning↔review (S↔A) taxonomies in both maps. The point:
> each sector is now a clean **Hermes-dispatch target** (Thread-1 wiring stays owner-undecided).
> Docs-only; no `disbot/`. ·
> 2026-06-14, **seventh Q-0107 reconciliation pass (the band-#870 cadence
> fire)** — scored the band #841–#870 (~3/10 planned slots executed: **P1-2 ✅ #843**,
> ledger-checker ✅ #864, **P1-1 Layer A 🟡 #855**; the band's headline is the unplanned
> **Hermes control-plane / autonomous-loop operationalization arc** #863/#865/#868/#869/#870 +
> the prod backup fix #862 + the #704 triage/close #866). Reconciled the ledger (#867 ad-hoc
> window catch-up + the #868/#869/#870 Hermes arc), planned the next ~9 PRs
> ([band-#870 decade queue](planning/reconciliation-pass-2026-06-14-band870.md)) — **next = finish
> the P1 tier (eval-matrix offline half + absence-guard Layer B → P1-3 invariants) + a reserved
> slot for the Railway log-triage skill** — re-pointed the live queue + roadmap Now, re-badged the
> band-#840 pass `historical`, recorded the **zero-open-PRs** disposition (the cleanest the
> snapshot has logged), and reset the marker #840→**#870**. The planning improvement this pass
> made: every queue slot now carries a **gate-state tag** and a carried-slot **escalation rule**
> (§6). No new runtime bugs. ·
> 2026-06-14, **P1-1 Layer A — BTD6 path/line-aware resolution (#855)**.
> The first concrete slice of P1-1 (the standing #1 priority): the absence-claim guard's
> **Layer A** (retrieval, the design's Rec #1). `<tower> <top|middle|bottom> path` phrasing now
> grounds its whole tier line (a header naming every tier + per-tier detail) instead of
> resolving to nothing and licensing a confabulated false "no" — the canonical
> "bomb-shooter-middle-path" trigger removed at the root (the MOAB-bonus data was reachable, just
> unqueried). Conservative resolver (needs a tower + the literal `path` token). **Layer B (the
> negative-existential gate) stays design-for-review + needs prod creds.** +22 tests; CI green
> (9579); arch 0. ·
> 2026-06-14, **born-red session merge-gate (#849, Q-0133)**. Every
> `claude/*` session now opens its PR **born red** via an `in-progress` `.sessions/` card and
> flips it to `complete` as the deliberate final step — so native auto-merge fires on a
> *complete* PR, never a partial one (the #843 race). Folded into the required `code-quality`
> check (`scripts/check_session_gate.py`); engage-when-present so routines never deadlock;
> dogfooded on its own PR. ·
> 2026-06-14, **hardening P1-2 — health findings lifecycle + operational
> retention (#843, Q-0097)**. The persistent operational-health findings store gained an
> operator-managed transition path through the sole writer (`health_findings_service.set_status`
> + DB primitive `set_finding_status`, audited via `audit.action_recorded`), surfaced as
> `!platform finding resolve/ignore/reopen <fingerprint>`; retention now reruns on a daily
> `HealthMaintenanceCog` loop (not startup-only). The two health-map code gaps are closed; the
> remaining gap to production-ready is the owner-led live walk. CI green (9551); arch 0. ·
> 2026-06-14, **sixth Q-0107 reconciliation pass (the band-#840 cadence
> fire)** — scored the band #821–#840 (2/10 planned slots executed, but the **whole
> production-hardening P0 integrity spine is now COMPLETE**: P0-2 #829 · P0-3 #817 · P0-4
> #820/#825; the buffer went to the owner-directed **Railway agent-access** arc #827–#840,
> now **verified live** in #840). Reconciled the ledger (#838/#839/#840 + the Railway-session
> housekeeping PRs), planned the next ~9 PRs ([band-#840 decade queue](planning/reconciliation-pass-2026-06-14-band840.md))
> — **next = the P1 correctness tier** (P1-1 eval-matrix → P1-2 → P1-3) — re-pointed the live
> queue + roadmap Now, re-badged the band-#820 pass `historical`, recorded both open PRs (#834
> owner-capture · #704 owner-screenshots) with state, and reset the marker #820→**#840**. No new
> runtime bugs. ·
> 2026-06-14, **hardening P0-2 media retention PR 1 — data-minimization +
> retention enforcement (#829, Q-0099)**. The video-reference cache now stores only
> a bounded sanitized projection (`_project_metadata` — never the raw provider payload), a new
> `MediaMaintenanceCog` owns a scheduled physical purge of expired rows, thumbnail URLs are
> host/scheme-validated, and `docs/ownership.md` gained the `media` (YouTube) subsystem row.
> CI green (9467); arch 0; next = P0-2 follow-ups (diagnostics · provider hardening · live
> verify) → P1-1. ·
> 2026-06-14, **hardening P0-4 PR 2 — channel creation + category lifecycle
> convergence (#825, Q-0100)**. Ad-hoc operator channel creation
> (`!create`/`!evt`/`!bulkcreate` + the create panel) routed through a new audited
> `ChannelLifecycleService.create_channels` (the channel sibling of `RoleLifecycleService`;
> unbound creation has no declared binding so it never fit `ResourceProvisioningPipeline`).
> Every operator channel mutation now flows through one seam with audit +
> `channel.lifecycle_changed`; `test_no_direct_channel_mutations` pins `create_*`,
> `test_no_silent_auto_create` names the service as the one manual creator. **P0-4 complete;
> next P0 = P0-2 media retention (Q-0099).** CI green (9453); arch 0; corrected the readiness-map
> `create_panel` "uses provisioning lane" drift. ·
> 2026-06-14, **hardening P0-3 arc PR 3 — delegated-Setup apply authority
> (#817, Q-0098)**. Bounded `setup_delegate` actor authorized at the capability floor (still
> member-checked + revocable, audited distinctly), minted only by `apply_operations` after a
> live `can_apply_setup` re-check, threaded to the three capability pipelines, `_ALLOWED_ACTOR_TYPES`
> + the settings/resource audit CHECKs widened (migration 069), AST-fenced. **P0-3 complete;
> next P0 = P0-4 channel-ownership.** CI green (9442); arch 0; real-Postgres + clean-boot proven.

> **Purpose:** the one file that answers "what is true right now?" so a new
> session does not reconstruct it from the journal + planning docs. Read it
> **second**, right after `.claude/CLAUDE.md`.

---

## Stability baseline

Operational stability **accepted after #535** (live cog walk: server-management,
economy, moderation, games, hub navigation). **Do not run a broad re-audit unless
a regression is reported** — this is an *accepted baseline*, not a fresh re-test.
Env-gated features (AI / scheduler / YouTube / Paragon / webhook) run **degraded
in the sandbox**, not broken. Known UX follow-ups remain (below).

## In flight (verify against live GitHub)

**Do not trust a hard-coded PR count here — it goes stale on every push.** Get the
real list at session start from live GitHub (`list_pull_requests`, state=open);
this snapshot deliberately names no open PRs. For an initiative's shipped/queued
status read its tracker (e.g. the server-management tracker), not this section.
Source code and merged PRs win over anything written here.

## Recently shipped (newest first)

> Convention: **merged PRs only** (with #numbers). In-flight work is *not* listed here —
> get it from live GitHub. The newest merge a session sees may not be added yet; that
> lag is expected (the next session reconciles). A merged PR tagged "pending" is the bug.
>
> **Last reconciliation pass:** PR #1050 (2026-06-18, twelfth Q-0107 cadence pass —
> [the pass record + next-band queue](planning/reconciliation-pass-2026-06-18-band1050.md)). The next
> **docs-only review + planning reconciliation** is due once merged PRs cross #1080 (every
> multiple of **30** — Q-0107 cadence raised 10→20 on 2026-06-12, then 20→30 on 2026-06-14 per
> Q-0134; `check_reconciliation_due.py` flags it, and `.github/workflows/reconciliation-trigger.yml`
> auto-opens a `reconcile` issue at the boundary that fires the docs-reconciliation routine). Reset
> this marker to the latest PR after a pass.

- **#1052 (2026-06-18, dashboard generated-data refresh)** — `Merge pull request #1052 from
  menno420/bot/dashboard-refresh` — the per-source-merge `dashboard-data-refresh` workflow (Q-0167)
  regenerated the committed `dashboard/data/dashboard.json` from live source.
- **#1050 (2026-06-18, consistency-linter — embedded windowed-select helper + bounded-catalog triage)** —
  the design step the #1048 handoff named: refactored `views/paginated_select.py` to share **one**
  windowing core — a `SelectWindow` controller that manages a *band* of items (a windowed `Select` +
  ◀/▶ nav) inside **any host view**, removing only its own items on a page flip so it composes with a
  multi-control panel; `PaginatedSelectView` is now a thin wrapper over it (constructor unchanged) and a
  new `attach_windowed_select(view, options, on_select, …)` exposes the embedded path. **Triaged the 28
  `select_option_truncation` candidates → 15**: dogfooded the helper on `access_map`'s feature
  drill-down (`_FeatureDetailSelect` → `_attach_feature_detail_select`, a genuinely-dynamic select that
  could exceed 25), and **allowlisted 12** backed by a fixed in-repo catalog / game-data roster (btd6
  tower roster + live-events feed; the curated mining taxonomy market/recipe/workshop/gear selects) —
  same standard as the existing btd6-catalog allowlist entries (not the #1040 bug). The **15 remaining**
  are all genuinely guild-scaled embedded selects — the shared `views/selectors/` primitives
  (role/channel/multi/multi_role/subsystem; the API-ripple set) + the channels move/visibility/create
  panels, `settings/subsystem_view` edit/reset selects, `setup/sections/channels`, `access/explorer`,
  and `diagnostic/automation_panel` — see the ▶ Next-action handoff.
- **#1049 (2026-06-18, dashboard refresh)** — `Merge pull request #1049 from
  menno420/bot/dashboard-refresh` (newest-merge lag catch-up; recorded on sight per Q-0166).
- **#1048 (2026-06-18, consistency-linter — standalone select pickers → `PaginatedSelectView`)** —
  migrated the three cleanly-standalone single-select ephemeral pickers onto the shared
  `views/paginated_select.py` primitive: `settings/edit_enum` (`EnumSettingSelectView`/`_EnumSelect`
  → the `build_enum_select_view` factory), `roles/time_roles_panel` (`_TimeRemoveView`), and
  `roles/xp_roles_panel` (`_XpRemoveView`). Each retired **both** its `select_option_truncation`
  (31→28) and `panel_base_class` (29→26) consistency finding and fixed the latent #1040 >25-option
  silent-drop; the `baseview_inheritance` arch debt ratcheted 12→9. The remaining
  `select_option_truncation` candidates are all embedded in multi-control views (need an
  embedded-windowing design step — see the ▶ Next-action handoff).
- **#1046 (2026-06-18, dashboard generated-data refresh)** — `chore(dashboard): refresh generated
  data` — regenerated the committed `dashboard/data/dashboard.json` from live source (the cadence-regen
  routed to the docs-reconciliation routine in #1025).
- **#1045 (2026-06-18, dashboard-data-refresh CI fix)** — `fix(ci): make dashboard-data-refresh
  actually work` — corrected the dashboard-data-refresh workflow to use the PR-flow auto-merge path so
  the generated-data refresh lands instead of stalling.
- **#1042 (2026-06-18, repo-consistency-linter PR 1 — Q-0170)** — the owner-directed "CI but for
  UX/interaction inconsistencies" tool, `scripts/check_consistency.py` (stdlib AST over `disbot/views/`,
  `check_architecture`-style `Rule` registry + an `architecture_rules/consistency_exceptions.yml`
  allowlist, warn-only/disposable per Q-0105). PR 1 = the harness + **rule 1 (edit-in-place)**: a panel
  button/select callback that delivers its result as a standalone ephemeral instead of editing the panel
  in place (45 first-run candidates, allowlist empty). Built one rule per PR; rules 2+3 followed (#1043).
- **#1041 (2026-06-18, fishing reconciliation Codex follow-ups)** — addressed the Codex review on the
  fishing-v1→#1036-spec reconciliation: migration hygiene (the value-column drop), the legacy-count
  guard (a player who fished under the superseded interim catalog can have rows the current 21-fish
  catalog doesn't, so `!fishlog`/`!fishtop` count only current-catalog species), and a dependency tidy.
- **#1040 (2026-06-18, setup cog-routing picker pagination)** — the cog-routing select hard-capped at
  `visible[:25]`; the routable-subsystem registry has grown past 25 (35), so the cap silently dropped
  every cog past the 25th (moderation, role, settings, …) — an operator literally could not route them.
  `_operator_visible_cogs()` now returns the full sorted list and a new `_CogPickView(BaseView)` pages
  it into ≤25-option windows with ◀ Prev / Next ▶ nav. Bug already on `main`; a registry-drift class.
- **#1039 (2026-06-18, fishing v1 reconciled to the owner's #1036 design — Q-0175)** — the interim
  fishing v1 (#1033: 14 fish, 5 rarity tiers, coins per catch) was built before the owner's #1036 spec
  landed and contradicted it. Reconciled the shipped code to the spec: the 21-size-ranked-fish
  `data/fishing/fish.json`, the level/size-band deterministic-roll catch (7 levels × 3), a no-coins
  collection log (`economy_service` dropped from the fishing path; migration 076 drops the value cols).
- **#1038 (2026-06-18, BTD6 "which MK affects <tower>" — owner live-test)** — the model no longer
  assembles the class-wide MK list itself; `btd6_data_service`/`btd6_context_service` derive and list the
  class-wide Monkey Knowledge for a tower deterministically, and a sniper routing miss (the question
  not reaching the BTD6 path) was fixed in `ai_task_router`.
- **#1037 (2026-06-18, BTD6 round_cash identity ABR fix — Codex P2 on #1035)** — gated the inclusive
  range `identity` sentence to emit only when the cumulative subtraction reconciles with `range_cash`;
  it was contradicting `range_cash` for ABR ranges spanning the unplayed rounds 1-2 (the cumulative
  totals start at round 3). Self-validating, so the existing `cumulative_note` covers the excluded case.
- **#1036 (2026-06-18, fishing v1 + open-world expansion plan — Q-0175, docs-only)** — captured the
  owner's fishing/boat brain-dump as a buildable plan: Phase 1 (fishing v1 — 21 fish, 7 levels × 3 fish,
  reuses tier/`game_xp`; one character with named swappable gear-type loadouts, gear never required —
  only boosts bonuses) + Phase 2+ (boat as 2nd home base · bounded travel · seed-grid destinations with
  coordinates/biome, ties Q-0173); indexed on the roadmap.
- **#1035 (2026-06-18, BTD6 AI answer fixes — owner live-test screenshots)** — fixed 4 owner-spotted
  BTD6 answer bugs at the deterministic data/grounding/tool layer: MK reference reply grammar +
  tab-wide scope note (Come On Everybody / Flanking Maneuvers disclosure); grounded the total bloons
  entering a round so "how many bloons spawn on rN" is answerable instead of refused (the derived sum
  tripped the value-only faithfulness guard); `round_composition` `roundset_label` so ABR vs standard
  figures don't read as self-contradiction; `round_cash` ready-to-quote inclusive-range `identity`
  sentence (a same-day P2 follow-up gated it to ranges where the cumulative subtraction reconciles —
  it was emitting a contradictory identity for ABR ranges that span the unplayed rounds 1-2).
- **#1034 (2026-06-18, Codex edits-live note — Q-0174 resolved, docs-only)** — documented that Codex
  has no write access: its "make changes" output is a comment describing a diff in its own sandbox, so
  agents read the proposed change from the comment, verify against `main`, and apply it themselves
  (never hunt for a phantom Codex branch/PR); Q-0174 resolved → trial comment-only as-is.
- **#1032 (2026-06-17, settle decisions + Codex integration — docs-only)** — settled **Q-0173** (the
  mining grid world = a seed-deterministic procedural grid we generate, not literal Minecraft-terrain
  replication) and **Q-0174** (Codex review integration: routines check Codex first but verify, the
  "real bug" bar, the issue-only Hermes 6H PR-check spec); fixed 3 verified-real Codex-flagged drift
  items (`/session-close` 10th-PR→30-PR cadence · `roadmap.md` "decade queue" → full-band wording ·
  a session card's `Previous-slice review` → `Previous-session review`).
- **#1031 (2026-06-17, local character-render preview tool — Q-0172, self-initiated)** —
  `scripts/preview_character.py` renders the live V-16 compositor (`utils/character_render.py`) to a PNG
  locally so sprite positioning is a render→look→tune-`manifest.json`→re-render loop instead of manual
  Discord uploads; Q-0105 dev tool (stdlib + Pillow, not CI-wired, disposable). Also recorded the
  owner's vault-cap decision (keep it soft / warning-only).
- **#1030 (2026-06-17, Hermes plain-language house style — Q-0168)** — promoted the owner-approved
  sample to a canonical `_house-style.md` (5 rules + the morning-briefing exemplar) and rewrote the
  owner-facing output skills (`morning-briefing`/`repo-health`/`open-questions`/`idea-spotlight`/
  `review-merge`) to cite it and speak plainly (jargon translated, grouped not listed); the commands +
  rate-limit budgets are unchanged. Owner manual step: redeploy on the VPS.
- **#1029 (2026-06-17, idea→plan gate opened — Q-0172)** — the owner directive that removed the
  old idea→plan→build approval gate: any agent may now promote a `docs/ideas/` idea into a
  `docs/planning/` plan and build it without owner approval, flagged on the run-report
  `⚑ Self-initiated:` line for review; `scripts/check_phase_gate.py` is now **advisory-only** (a
  "bugs-first season" readout, no longer a block). Recorded in the CLAUDE.md working agreement +
  router Q-0172; also slimmed the Hermes dispatch-skill batch-1 docs. Safety brakes (irreversible/external) unchanged.
- **#1028 (2026-06-17, procedures→skills conversion plan — docs-only)** — captured the 33-procedure
  skills-conversion inventory (A/B/C buckets) as an executable plan
  (`planning/procedures-to-skills-conversion-plan-2026-06-17.md`): the thin-pointer convention, the
  must-NOT-move safety list, the batched build order. Owner-confirmed approach (relocate procedures to
  on-demand skills, keep a thin pointer + the binding rules in CLAUDE.md). Extends Q-0170.
- **Older merges (#1026 … #535) → [`current-state-archive.md`](current-state-archive.md).** Recently-shipped keeps the ~20 newest; older entries are trimmed to the archive (newest-first), which `scripts/check_docs.py` soft-ratchets at 20 and `check_current_state_ledger.py` treats as present. *(The twelfth Q-0107 pass — band-#1050, 2026-06-18 — added the missing #1022 and #1029 entries and trimmed the live ledger back to the 20 newest, moving #1026 … #975 to the archive.)*

> Older than this: see `docs/planning/*` trackers and `docs/decisions/*` ADRs.

## Next candidates

- **Cross-area sequencing + the plan index now live in [`docs/roadmap.md`](roadmap.md)**
  (by area, with Now / Next / Later / Someday horizons + gates — where to find which plan
  for which part of the code). The picks below are the current top of that list.
- Server-management is **structurally complete** *(bullet corrected 2026-06-10 — it
  still queued PR14 long after the hub merged)*: **PR10 complete** (six slices,
  ADR-008), **PR11** (#570; governance section **deferred** — revisit only with a
  scope decision), **PR12** (2026-06-07), **PR13's deterministic slice** (2026-06-08,
  incl. the migration-059 staging fix), and **PR14 — the unified Server Management
  Hub — shipped 2026-06-08 via #584**. The only remainder is the **gated PR13 AI
  generation layer**. The `docs/planning/server-management-status-2026-06-05.md`
  tracker (re-badged `historical` 2026-06-13 — initiative complete) is the historical
  record; the gated PR13 AI tail lives in [`roadmap.md`](roadmap.md) → Later. Don't duplicate it here.
- Health/diagnostics maintainer live-tests (production AI tool + grouped findings):
  see `docs/subsystems/health-diagnostics.md`.
- **Docs consolidation (Q-0010) — executed 2026-06-08.** Top-level `docs/` is now **16**
  (the 13 binding contracts + `current-state` + `roadmap` + `context-map-tooling`); plans /
  audits / inventories / historical snapshots moved into clustered subdirs behind their
  folios, and `_TOP_LEVEL_DOCS_BUDGET` lowered 41 → 16. Paired with the idea-backlog
  lifecycle + grooming secondary task (Q-0015, `docs/ideas/README.md`) and the binding-doc
  section-ownership convention (`docs/owner/ai-project-workflow.md` §9). The original handoff
  was [`planning/docs-restructure-brief-2026-06-08.md`](planning/docs-restructure-brief-2026-06-08.md).
  Verify merge status on live GitHub.
- Use the canonical subsystem folios for area-specific implementation/planning. The
  2026-06-06 readiness audit classifies stale, gated, and ready workstreams.

## Gates / blocked work

- **Autonomous loop — see the canonical [Control-plane state table](operations/autonomous-routines.md)
  § "Control-plane state".** That table is the single source of truth for the loop's state (does it
  self-fire · `ROUTINE_PAT` · Railway env · dispatch-prompt version · model pins); **do not restate
  its verdict here.** This bullet is a pure pointer on purpose — a control-plane verdict copied into
  this file drifted from the canonical table twice (the band-#870 and band-#930 passes each had to
  re-sync it by hand), so the copy is deliberately gone (idea
  `control-plane-single-source-pointer-2026-06-15`). The live read no in-repo checker can see is the
  `reconcile` trigger-issue author (`menno420` = PAT set & loop self-fires; `github-actions[bot]` =
  PAT unset); `check_loop_health.py` (Q-0135) probes live GitHub for the same truth.
- **Open bugs (bug book):** **BUG-0009** (AI list-answer mislabeling — needs the AI orchestration §7
  deterministic list-builders, plan-level) and **BUG-0011** (Hermes gateway restart crash-loop — needs
  a clean VPS foreground repro) stay OPEN — [`health/bug-book.md`](health/bug-book.md).
- **Open decisions:** **Q-0096** remainder (Context7 adopted #737; **Postgres-MCP + `pyright-lsp`**
  undecided) · **Q-0120/Q-0121** (the workflow pass's proposals — candidate-rule promotion · Hermes
  bug-triage `gh issue create` write). *(**Q-0119 answered 2026-06-13** → governance role pointers
  get their own reserved-namespace `governance` schema home (option a); P0-3 family 3 is unblocked
  for a future arc PR — router §Q-0119 + the [convergence plan §5](planning/settings-pointer-lane-convergence-plan-2026-06-13.md).)*
- **AI / BTD6 feature expansion — re-postured 2026-06-09 (Q-0048):** AI tools that are
  **read-only AND deterministic** (no writes, no external calls, audience-tiered) carry a
  **standing lift** and may ship without a per-case ask. Anything that **writes, costs
  money, calls external services, or adds UI** still needs the per-exposure lift, and broad
  expansion stays gated on *all* of: bot-wide stability **+** provider/provenance checks
  **+** caching / source-health clarity **+** AI behavior/config correctness.
- **BTD6 data extraction** — ADR-006 provenance schema **now implemented**
  (`docs/btd6/btd6-provenance-schema.md`); extraction may resume against the ordered
  backlog in `docs/btd6/btd6-gamedata-decode-status.md`. The broader AI/BTD6
  feature-expansion gate (stability + provider/provenance + caching + AI config) still
  applies.
- `_derive_scope` → `PLATFORM_OWNER` (decision D1) — **RESOLVED** in #541; owner-only
  AI tools are now reachable.

## Known UX follow-ups (not stability bugs)

- Server-management member/role UX follow-ups: see
  `docs/subsystems/server-management.md`.
- Dense DiagnosticCog platform-subview pagination idea: see
  `docs/subsystems/health-diagnostics.md`.

## Near-term technical debt (decided, not yet implemented)

*(The Q-0025 `new_subsystem.py` scaffold that used to sit here is reconciled: built
and used to register Community Spotlight in **#626** (execution-plan Lane 1,
2026-06-09 — verify merged on live GitHub).)*

*(The Q-0026 `cog_name_to_subsystem` fix that used to sit here is reconciled: merged
in **#588**, listed under Recently shipped.)*

## Off-limits / do-not-propose

- No Redis / external state store (**ADR-001**).
- Game state is **not** restart-safe by design (**ADR-002**) — accepted, not a bug.
- Do not re-litigate the rejection ledger in
  `docs/planning/superbot-ideas-lab-2026-06-05.md` §6.
- Do not restate "bot fully tested & working" as *newly* verified without an actual
  boot + live walk — cite the #535 baseline instead.

## Where to read next

The **canonical read path + "what lives where"** lives in
**`docs/AGENT_ORIENTATION.md`** ("Reading order by task" + the document-classification
lists). This file is *step 3* of that path: read it for **what is true right now**, then
follow the orientation route for your task. The read-path table is **not** duplicated
here — one canonical home (`AGENT_ORIENTATION.md`).

**One-fact-one-home rule:** if a fact belongs in one of those homes, **link** to it —
do not restate it here. Restatement across files is where drift breeds. In particular,
**don't summarize plans'/trackers' PR numbers or status here** — link to the folio or
tracker, which is authoritative for its own area.

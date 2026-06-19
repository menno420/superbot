# Idea-to-roadmap inventory — 2026-06-08

> **Status:** `historical` — planning/routing draft; not implementation approval.
> **Superseded 2026-06-19 (was active):** Superseded by ../ideas/README.md + ../roadmap.md as the live idea/plan routing. Do not act on this — current map: [planning/README](README.md).
> **Sources consolidated:** all documents named in the 2026-06-08 idea-to-roadmap mapping request, plus relevant subsystem folios, binding decisions, and 2026-06-07/08 session journals where needed.
> **Truth order:** source/merged PRs → binding docs → folios → current state → active plans → ideas → sessions/old plans.

## Verification note

Live GitHub open-PR verification was attempted first, but this checkout has neither `gh` nor a configured Git remote. Therefore no live PR claim is made here; every destination must re-check live PRs in a connected environment before promotion. The in-repo current-state/status documents and source tree were used only as the best available fallback.

## How to read the inventory

Each row is the single explicit lifecycle outcome for every idea named in that row. A row may group variants only where they share one owner, seam, gate, and destination. Risk/size are routing estimates, not commitments. “Roots/seams” are inspection starts, not permission to create new ownership.

Lifecycle states used here: **existing plan**, **new roadmap draft**, **small executable plan**, **existing horizon**, **blocked gate**, **owner question**, **rejected**, and **duplicate/superseded**.

## Owner-selected and product-direction inventory

| Ideas (all variants named) | Owner / related areas | Roots and seams to reuse | Risk / size | Gate or question | Explicit state → destination |
|---|---|---|---|---|---|
| Guilds/clans; membership; shared bank; officers; upgrades/levels; guild battles; guild leaderboards | New social owner / economy, games | guild lifecycle, economy service, audit/event reads, leaderboard patterns | High / XL | Q-0038; privacy/tenancy; new owner decision | **owner question**, then **new roadmap draft** → [social roadmap](social-community-progression-roadmap-2026-06-08.md) |
| Persistent achievements/badges: game, social, hidden | Social progression / games, economy | deterministic domain events, audit, existing game owners | Med / M | canonical event vocabulary; hidden disclosure | **new roadmap draft** → [social roadmap](social-community-progression-roadmap-2026-06-08.md) |
| Profile cards: economy stats + guild membership/rank | Social read model / economy | economy/inventory reads, profile/panel standards | Med / S | privacy; Q-0038 for guild fields | **new roadmap draft** → [social roadmap](social-community-progression-roadmap-2026-06-08.md) |
| Notifications: DM, channel, inbox/mail, action CTAs | Shared notification/read model / all domains | configured delivery, audit/event paths, panels | Med / M | consent, spam, retention, owner boundary | **new roadmap draft** → [social roadmap](social-community-progression-roadmap-2026-06-08.md); delivery also gated by Q-0041 where provider-backed |
| Player marketplace; mining resources; cosmetic roles/titles; rare collectibles | Economy / mining, social | economy service, inventory, mining items, audit ledger | High / L | item authority, atomicity, fraud/balance | **new roadmap draft** → [economy roadmap](economy-marketplace-rewards-roadmap-2026-06-08.md) |
| Streak rewards: coins/gems, cosmetics, lottery entries; daily bonus drops; random treasure drops; seasonal rewards | Economy rewards / games, routines | economy service, deterministic event/routine seam | Med / M | chance-reward/product review; anti-abuse | **new roadmap draft** → [economy roadmap](economy-marketplace-rewards-roadmap-2026-06-08.md) |
| Coin sinks; starter packs; new-user economy flow | Economy / setup/help | economy service, existing setup/help panels | Med / M | balance evidence, idempotency | **new roadmap draft** → [economy roadmap](economy-marketplace-rewards-roadmap-2026-06-08.md) |
| VIP tiers: in-game + donation; strict no-pay-to-win | Economy/product | economy authority; external billing only after decision | High / L | Q-0039 | **owner question** → Q-0039; concept routed to [economy roadmap](economy-marketplace-rewards-roadmap-2026-06-08.md) |
| Blueprint-drop crafting | Economy/mining | existing mining recipes/items + economy item authority | Med / M | item authority and mining balance | **new roadmap draft** → economy Phase 5 + [games/mining roadmap](games-mining-idle-roadmap-2026-06-08.md) handoff |
| Multiplayer Texas Hold'em (3–6), lobby/blinds/wagers | Games / economy, social | game-state service, game views, economy escrow/refund | High / L | concurrency, moderation, ADR-002 | **new roadmap draft** → [games/mining roadmap](games-mining-idle-roadmap-2026-06-08.md) |
| Blackjack variants and side bets | Games / economy | blackjack engine/cog/views, economy service | Med / M | odds/balance/product review | **new roadmap draft** → [games/mining roadmap](games-mining-idle-roadmap-2026-06-08.md) |
| Active+idle mining hybrid; offline accrual; active boosts | Mining/games / economy | existing mining exploration/items/rewards/recipes | High / M | anti-abuse, clocks, balance; no new loop | **new roadmap draft** → [games/mining roadmap](games-mining-idle-roadmap-2026-06-08.md) |
| Mining bosses, deeper floors, events, co-op | Mining/games / social, economy | mining engine/modules, game-state/economy services | High / L | deterministic flow, balance, co-op identity | **new roadmap draft** → [games/mining roadmap](games-mining-idle-roadmap-2026-06-08.md) |
| Wire `!explore` to shipped exploration engine | Mining | existing exploration engine and `resolve_to_legacy_tuple()` | Low / S | maintainer promotion/approval | **small executable plan** → existing `mining-wire-exploration-plan.md` (**not executed here**) |
| Games actionability leftovers: inventory architecture, leaderboards, bot-duel stats, shared back buttons | Games | existing cogs/views/game DB helpers | Low–Med / S–M | choose one bounded slice | **existing horizon** → Games Later in `docs/roadmap.md` / archived actionability roadmap |
| Restart-safe games, Redis-backed sessions/cache, universal checkpointing | Games/platform | none; ADRs forbid | High / XL | ADR-001 + ADR-002 | **rejected** → binding Ideas Lab rejection ledger / ADR-001 / ADR-002 |
| AI dungeon master: thread, persistent channel, DM | AI / games, social | AI orchestration + deterministic domain owners | High / XL | Q-0040; all AI gates | **owner question** and **blocked gate** → Q-0040 + [AI routing addendum](../ai/ai-product-extension-routing-2026-06-08.md) |
| AI-generated event narrative, dynamic difficulty, procedural quests, player-prompted events | AI / games, economy | AI orchestration; deterministic game/reward authority | High / L | AI action/readiness gates; moderation/cost | **blocked gate** → [AI routing addendum](../ai/ai-product-extension-routing-2026-06-08.md); narrative-only earliest |
| Wider natural-language intent coverage | AI / help/access | central NL stage, task router, permission/readiness | Med / M | authoritative AI roadmap gates | **existing plan** → `ai-roadmap-2026-06-07.md` and [AI routing addendum](../ai/ai-product-extension-routing-2026-06-08.md) |
| BTD6 rules/trivia; challenge generator; score/run tracking; BTD6 leaderboards | BTD6 / AI, social | BTD6 provider/fact/grounding/cache/source health | High / M–L | ADR-006; provenance; run privacy/anti-cheat | **blocked gate** → [BTD6 routing draft](../btd6/btd6-product-extension-routing-2026-06-08.md) |
| Resume/expand BTD6 extraction for product ideas now | BTD6 | existing decode/provenance pipeline only | High / L | ADR-006/current gates | **rejected** for now → Ideas Lab rejection ledger and BTD6 folio |
| Adaptive setup/access/profile/routine; quiet/availability; command-access explanations; setup guidance cards | Setup/access/server management | access projection, command access, setup diagnostics/operations, capability authority | Med–High / L | existing adaptive-plan questions/phases | **existing plan** → `adaptive-setup-access-routine-platform-2026-06-08.md`; summarized in [routing addendum](server-management-extension-routing-2026-06-08.md) |
| Scheduled announcements/reminders | Routine/server management | future curated Routine Engine action, settings/bindings, audit | Med / M | automation authority/audit decision | **existing plan** → adaptive plan Routine Engine; clarified in [routing addendum](server-management-extension-routing-2026-06-08.md) |
| Anti-spam/abuse detection: deterministic controls and AI detection | Moderation / AI | moderation service/config, readiness/audit | High / M | active tracker; AI gates for AI detection | deterministic portion **existing plan** → server-management roadmap; AI portion **blocked gate** → AI roadmap |
| Owner/admin analytics; server insights | Diagnostics/server management | diagnostics/readiness/audit reads | High / L | privacy, retention, aggregation; no second dashboard | **new roadmap draft** routing only → [server-management extension routing](server-management-extension-routing-2026-06-08.md) |
| Twitch alerts; YouTube alerts; Spotify/Last.fm; Steam/gaming APIs | Shared media/integrations | ADR-007 media services, provider health/cache/settings/delivery | High / M each | Q-0041; privacy/credentials/moderation/retention | **owner question** and **new roadmap draft** → Q-0041 + [integrations roadmap](integrations-media-voice-website-roadmap-2026-06-08.md) |
| Voice music playback; sound effects; speech commands | New voice boundary / media, moderation | no approved owner; reuse access/settings/audit if approved | High / L | Q-0041; architecture, privacy, cost | **owner question** → Q-0041 + [integrations roadmap](integrations-media-voice-website-roadmap-2026-06-08.md) |
| Full web dashboard | Web projection / all domains | canonical reads/services/panels only | High / XL | Q-0042; auth/privacy; Discord-native maturity | **owner question** and **blocked gate** → Q-0042 + [integrations roadmap](integrations-media-voice-website-roadmap-2026-06-08.md) |
| Mobile-first UI; rich help/categories/search; changelog/what's-new; balance notices; funny/sarcastic personality; consistent panel language/action vocabulary | Interface/help/product copy | mother-hub/interface plans, UI standards, help/access routes, existing panels | Low–Med / S–M | Q-0036 for denial copy; release-manifest owner; tone review | **new roadmap draft** → [UX roadmap](ux-discoverability-mobile-roadmap-2026-06-08.md), with bounded slices routed through existing interface plans |
| One slash command per sub-action; second panel/router/UI framework | Interface | existing hubs/router/persistent views | High / L | binding standards | **rejected** → Ideas Lab rejection ledger / command-integration standard |

## Existing future-product, command, interface, and Ideas Lab inventory

| Idea group | Reuse / owner | Explicit state → destination |
|---|---|---|
| Capability explanation, “why can't I edit/use,” access preview, Help locked reasons, moderation policy explainer, setup guidance, server-care checklist | Access projection, capability authority, setup diagnostics, existing Help/managers | **existing plan** → adaptive setup/access plan, server-management plans, command/interface backlogs; UX composition also routed to [UX roadmap](ux-discoverability-mobile-roadmap-2026-06-08.md) |
| Diagnostics/readiness cards, regression/smoke status, source-health/freshness/provenance cards, migration health, logging route health, architecture warnings, support-report presets | Existing `ReadinessSnapshot`, health/diagnostics owners, BTD6 source health | **existing plan/horizon** → health folio, command/interface backlogs, BTD6/AI plans; smoke runner remains future/gated |
| Cleanup dry-run/history, counting health/rules, RPS matchup, refund hints/lookups, coin history, inventory filters/search, mod case timeline, panel drift/recovery/anchor hints | Existing domain reads/views and interface plans | **existing plan/horizon** → Ideas Lab quick index, command expansion, interface completion, archived games follow-ups |
| Unified audit/event timeline read service | Existing audit/event owners / cross-cutting | **blocked gate** → Later concept only; privacy/retention and ownership decision required before a new read service |
| Workflow recovery/resume and final-review preflight diff | Existing setup workflow/final review | **existing plan/horizon** → setup/adaptive plans; final-review diff remains ADR-003-deferred |
| Guild template/provisioning model and deterministic role/setup templates | Provisioning/setup/server management | **existing plan** → server-management/adaptive setup plans; AI generation remains gated |
| Rule/automation builder, arbitrary automation recipes/scripts | Routine/capability authority | **blocked gate** for curated Routine Engine; arbitrary scripts **rejected** by Ideas Lab operating decisions |
| Shared media/video-reference and channel summary | Shared media owner | **existing horizon** → Media Later + ADR-007; broader providers routed to [integrations roadmap](integrations-media-voice-website-roadmap-2026-06-08.md) |
| BTD6 strategy workspace, answerability checker, data inventory/provider parity/source health | BTD6 | **existing plan/horizon** and **blocked gate** → BTD6 plans/folio; no extraction bypass |
| AI admin advisor, decision/guard/tool-coverage explainers, support reports | AI diagnostics/orchestration | **existing plan** and **blocked gate** → authoritative AI roadmap; explanation-only |
| Cross-process/sharding readiness | Platform | **blocked gate** → Someday only; ADR-001 triggers required |
| Separate danger dashboard, second governance simulator, global fail-closed, big all-cogs sweep, generic helper module | Existing canonical owners | **rejected** → binding Ideas Lab rejection ledger |
| Stale UI/helper/status inventories treated as live backlog | Docs/workflow | none | **rejected** → source verification required by current-state/readiness review |

## AI extra-tool capability inventory

| Ideas | Owner/reuse | Risk / gate | Explicit state → destination |
|---|---|---|---|
| Web research; image vision; file/log/document reader; OCR; knowledge-base search; chart generation | Existing AI orchestration descriptors, typed results/evidence, scopes/budgets/audit | Med–High; AI readiness/orchestration/privacy/provider gates | **existing plan** → `ai-tool-capability-roadmap.md` after orchestration foundation; summarized in [AI routing addendum](../ai/ai-product-extension-routing-2026-06-08.md) |
| GitHub/CI reader; website/API status; YouTube/Twitch status; Google Sheets/Docs reader; approved API fetch | AI orchestration + shared provider/media owners | High; credentials, provenance, privacy, provider health | **existing plan** but **blocked gate** → AI tool roadmap; provider product surfaces also Q-0041/integrations roadmap |
| Scheduler/recurring reports; notification delivery; safe admin actions; moderation recommendations | AI orchestration + domain owners | High; dedicated action decision, confirmation, audit, rollback | **blocked gate** → authoritative AI roadmap/tool roadmap; no write/action tools now |
| Bot health, BTD6 tools, diagnostics, server context, evidence, trace/audit foundations | Existing canonical services/contracts | Already mapped | **duplicate/superseded** as net-new ideas → extend existing AI orchestration/readiness plans, do not create duplicates |

## Destination summary

| Cluster | Destination | Horizon / gate |
|---|---|---|
| Social/community/progression | [social roadmap](social-community-progression-roadmap-2026-06-08.md) | Later; Q-0038 + privacy/new-owner decision |
| Economy/marketplace/rewards | [economy roadmap](economy-marketplace-rewards-roadmap-2026-06-08.md) | Later; economy health + Q-0039/chance review |
| Games/mining/idle | [games/mining roadmap](games-mining-idle-roadmap-2026-06-08.md) | Later; ADR-002; mining wire remains separate ready plan |
| AI extensions | [AI routing addendum](../ai/ai-product-extension-routing-2026-06-08.md) | Later; authoritative AI roadmap and all AI gates |
| BTD6 extensions | [BTD6 routing draft](../btd6/btd6-product-extension-routing-2026-06-08.md) | Later; ADR-006/provenance gates |
| Server management/setup/access/routine | [extension routing](server-management-extension-routing-2026-06-08.md) | Existing plans; do not compete with active tracker |
| Integrations/media/voice/website | [integrations roadmap](integrations-media-voice-website-roadmap-2026-06-08.md) | Later/Someday; Q-0041/Q-0042 + privacy/security/moderation |
| UX/discoverability/mobile | [UX roadmap](ux-discoverability-mobile-roadmap-2026-06-08.md) | Later; select bounded work through existing interface lane |

## Recommended next sessions

1. **Opus first:** social/community architecture after Q-0038, because it is the owner's top product direction and determines guild/economy/profile/leaderboard semantics.
2. **Opus next:** economy marketplace/rewards architecture, then integrations privacy/credential decision pack; AI's first Opus target remains its already-recorded orchestration foundation, not these new product ideas.
3. **Sonnet-safe only after explicit selection:** the already-written mining-wire plan; a bounded mobile-first audit; or a read-only Help/access explanation slice from an existing authoritative plan.
4. **Codex mapping-only:** AI action tools/events/DM, BTD6 extension/extraction, poker concurrency, voice, website, cross-server social identity, analytics, and provider integrations until their decisions/gates clear.
5. **Off-limits:** Redis/restart-safe games; duplicate governance/panel/helper/dashboard systems; arbitrary automation; AI writes/actions now; BTD6 extraction bypass; unreviewed provider/media/voice collection.

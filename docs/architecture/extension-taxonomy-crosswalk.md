# Extension-type taxonomy crosswalk

> **Status:** `living-ledger` — **GENERATED — NOT SOURCE OF TRUTH.** Do not edit by hand.
> Regenerate with `python3.10 scripts/extension_crosswalk.py --write` after editing
> `architecture_rules/extension_roles.yaml`. Sources: `disbot/config.py` (`INITIAL_EXTENSIONS`),
> `disbot/utils/subsystem_registry.py` (`SUBSYSTEMS`), and that overlay. `--check` guards staleness.

_Generator:_ `scripts/extension_crosswalk.py` `v1`  ·  **51** extensions  ·  **38** registered subsystems  ·  **13** non-1:1 extensions.

Every loaded extension classified by **role** (editorial — in `architecture_rules/extension_roles.yaml`) and joined to the registry. A ✓ in *Registered* means the extension is a 1:1 subsystem identity; the non-1:1 rows are surfaces/maintenance/adapters that **back** a subsystem or the platform.

## Roles

| Role | Count | Meaning |
|---|---:|---|
| `bootstrap` | 2 | Load-order / lifecycle-critical admission or setup; sensitive to INITIAL_EXTENSIONS ordering. |
| `hub` | 3 | A routing/composition layer that surfaces other subsystems; owns little or no domain state of its own. |
| `lab` | 1 | A development / UX laboratory surface; not a production product surface. |
| `maintenance` | 3 | A background-loop cog (scheduled work) with no subsystem identity; runtime/ops, not a product surface. |
| `operational_adapter` | 1 | A bridge to a control plane or external operation (not an in-guild product feature). |
| `product_subsystem` | 30 | A feature vertical with its own owner, views, and tests. |
| `shared_platform` | 6 | A broad cross-cutting capability with high blast radius (admin, settings, AI, diagnostics, help, utility). |
| `specialized_surface` | 5 | One of several surfaces within a single domain vertical (e.g. the BTD6 sub-cogs) — backs a registered subsystem rather than being its own. |

## Crosswalk (load order)

| # | Extension | Role | Registered | Backs | Note |
|---:|---|---|:--:|---|---|
| 1 | `bootstrap_access` | `bootstrap` | — |  | Installs the prefix+slash command-access guard; MUST load first. Platform admission, not a product subsystem. |
| 2 | `admin` | `shared_platform` | ✓ |  | Cog management, server stats, diagnostics entry; administrator floor. |
| 3 | `help` | `shared_platform` | ✓ |  | Help catalogue/projection surface; every subsystem's Help route composes it. |
| 4 | `role` | `product_subsystem` | ✓ |  |  |
| 5 | `role_grants` | `maintenance` | — | `role` | Temporary-role expiry sweep loop (+ the !temprole grant command); no subsystem identity — backs the role product. |
| 6 | `starboard` | `product_subsystem` | — |  | Starboard / Hall-of-Fame (idea B1) — N ⭐-reactions immortalize a message in a configured channel; reuses the raw-reaction seam. |
| 7 | `moderation` | `product_subsystem` | ✓ |  |  |
| 8 | `automod` | `product_subsystem` | ✓ |  | Automod rules engine (Q-0108). |
| 9 | `image_moderation` | `product_subsystem` | ✓ |  | Image moderation — OpenAI omni-moderation filter (Q-0108). |
| 10 | `xp` | `product_subsystem` | ✓ |  |  |
| 11 | `blackjack` | `product_subsystem` | ✓ |  | Game. |
| 12 | `rps_tournament` | `product_subsystem` | ✓ |  | Game (tournament orchestration). |
| 13 | `utility` | `shared_platform` | ✓ |  | General utility commands. |
| 14 | `cleanup` | `product_subsystem` | ✓ |  | Message-cleanup policy. |
| 15 | `channel` | `product_subsystem` | ✓ |  | Channel management (server-management area). |
| 16 | `inventory` | `product_subsystem` | ✓ |  |  |
| 17 | `economy` | `product_subsystem` | ✓ |  |  |
| 18 | `counting` | `product_subsystem` | ✓ |  | Counting game. |
| 19 | `deathmatch` | `product_subsystem` | ✓ |  | Game (1v1 duels). |
| 20 | `proof_channel` | `product_subsystem` | ✓ |  |  |
| 21 | `mining` | `product_subsystem` | ✓ |  | Mining character platform (large vertical). |
| 22 | `fishing` | `product_subsystem` | ✓ |  | Fishing minigame (ecosystem |
| 23 | `creature` | `product_subsystem` | ✓ |  | Creature catch/collection game v1 (catch slice; level-normalized PvP later). |
| 24 | `creature_battle` | `product_subsystem` | — |  | Creature PvP battle cog (!cbattle) — part of the Creatures subsystem (not a separate registered subsystem; surfaced via creature_cog's Help hook). |
| 25 | `farm` | `product_subsystem` | ✓ |  | Idle egg/chicken farm — the bot's first idle (accrue-over-time) game. |
| 26 | `diagnostic` | `shared_platform` | ✓ |  | `!platform` diagnostics; broad cross-subsystem read-model surface. |
| 27 | `health_maintenance` | `maintenance` | — | `diagnostic` | Scheduled health-findings retention loop; no subsystem identity. |
| 28 | `ai` | `shared_platform` | ✓ |  | AI orchestration / answerability; cross-cutting. |
| 29 | `media_maintenance` | `maintenance` | — |  | Scheduled media/YouTube cache purge loop; no subsystem identity. |
| 30 | `btd6` | `product_subsystem` | ✓ |  | BTD6 core data / answerability vertical. |
| 31 | `btd6_reference` | `specialized_surface` | — | `btd6` | BTD6 reference lookups. |
| 32 | `btd6_events` | `specialized_surface` | — | `btd6` | BTD6 live-events surface. |
| 33 | `btd6_strategy` | `specialized_surface` | — | `btd6` |  |
| 34 | `paragon` | `specialized_surface` | — | `btd6` | BTD6 paragon grounding surface. |
| 35 | `btd6_ops` | `specialized_surface` | — | `btd6` | BTD6 data-ops (seed/refresh); operational flavor within the BTD6 vertical. |
| 36 | `chain` | `product_subsystem` | ✓ |  | Command-chain subsystem. |
| 37 | `general` | `product_subsystem` | ✓ |  | General-content commands. |
| 38 | `four_twenty` | `product_subsystem` | ✓ |  | Novelty / community feature. |
| 39 | `leaderboard` | `product_subsystem` | ✓ |  | Cross-subsystem leaderboards (reads XP/games). |
| 40 | `settings` | `shared_platform` | ✓ |  | Settings hub; cross-cutting config surface. |
| 41 | `logging` | `product_subsystem` | ✓ |  | Server-logging subsystem. |
| 42 | `games` | `hub` | ✓ |  | Games hub (routes blackjack/deathmatch/counting/rps). |
| 43 | `community` | `hub` | ✓ |  | Community hub. |
| 44 | `community_spotlight` | `product_subsystem` | ✓ |  | Community Spotlight (community-hub child; registered subsystem). |
| 45 | `welcome` | `product_subsystem` | ✓ |  | Welcome service (join embeds + optional PIL cards). |
| 46 | `counters` | `product_subsystem` | ✓ |  | Dynamic server counters. |
| 47 | `security` | `product_subsystem` | ✓ |  | Security tiers 1+2 — raid detection + account-age filter (Q-0111). |
| 48 | `setup` | `bootstrap` | — | `server_management` | Guided setup wizard; lifecycle-critical, load-order sensitive. |
| 49 | `server_management` | `hub` | ✓ |  | Routing-only hub (moderation/channels/roles/cleanup/setup); holds no capability of its own. |
| 50 | `hermes` | `operational_adapter` | — |  | Bridge to the Hermes control plane / external operation. |
| 51 | `ux_lab` | `lab` | ✓ |  | Zero-write UX pattern gallery (admin-gated); design vocabulary, not a product surface. |

## Non-1:1 extensions (no registry identity)

These load as extensions but are **not** registered subsystems — they are classified by role instead of being product verticals:

- `bootstrap_access` (`bootstrap`) — Installs the prefix+slash command-access guard; MUST load first. Platform admission, not a product subsystem.
- `role_grants` (`maintenance` → backs `role`) — Temporary-role expiry sweep loop (+ the !temprole grant command); no subsystem identity — backs the role product.
- `starboard` (`product_subsystem`) — Starboard / Hall-of-Fame (idea B1) — N ⭐-reactions immortalize a message in a configured channel; reuses the raw-reaction seam.
- `creature_battle` (`product_subsystem`) — Creature PvP battle cog (!cbattle) — part of the Creatures subsystem (not a separate registered subsystem; surfaced via creature_cog's Help hook).
- `health_maintenance` (`maintenance` → backs `diagnostic`) — Scheduled health-findings retention loop; no subsystem identity.
- `media_maintenance` (`maintenance`) — Scheduled media/YouTube cache purge loop; no subsystem identity.
- `btd6_reference` (`specialized_surface` → backs `btd6`) — BTD6 reference lookups.
- `btd6_events` (`specialized_surface` → backs `btd6`) — BTD6 live-events surface.
- `btd6_strategy` (`specialized_surface` → backs `btd6`)
- `paragon` (`specialized_surface` → backs `btd6`) — BTD6 paragon grounding surface.
- `btd6_ops` (`specialized_surface` → backs `btd6`) — BTD6 data-ops (seed/refresh); operational flavor within the BTD6 vertical.
- `setup` (`bootstrap` → backs `server_management`) — Guided setup wizard; lifecycle-critical, load-order sensitive.
- `hermes` (`operational_adapter`) — Bridge to the Hermes control plane / external operation.

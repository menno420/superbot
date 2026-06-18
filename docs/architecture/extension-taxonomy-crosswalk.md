# Extension-type taxonomy crosswalk

> **Status:** `living-ledger` — **GENERATED — NOT SOURCE OF TRUTH.** Do not edit by hand.
> Regenerate with `python3.10 scripts/extension_crosswalk.py --write` after editing
> `architecture_rules/extension_roles.yaml`. Sources: `disbot/config.py` (`INITIAL_EXTENSIONS`),
> `disbot/utils/subsystem_registry.py` (`SUBSYSTEMS`), and that overlay. `--check` guards staleness.

_Generator:_ `scripts/extension_crosswalk.py` `v1`  ·  **44** extensions  ·  **34** registered subsystems  ·  **10** non-1:1 extensions.

Every loaded extension classified by **role** (editorial — in `architecture_rules/extension_roles.yaml`) and joined to the registry. A ✓ in *Registered* means the extension is a 1:1 subsystem identity; the non-1:1 rows are surfaces/maintenance/adapters that **back** a subsystem or the platform.

## Roles

| Role | Count | Meaning |
|---|---:|---|
| `bootstrap` | 2 | Load-order / lifecycle-critical admission or setup; sensitive to INITIAL_EXTENSIONS ordering. |
| `hub` | 3 | A routing/composition layer that surfaces other subsystems; owns little or no domain state of its own. |
| `lab` | 1 | A development / UX laboratory surface; not a production product surface. |
| `maintenance` | 2 | A background-loop cog (scheduled work) with no subsystem identity; runtime/ops, not a product surface. |
| `operational_adapter` | 1 | A bridge to a control plane or external operation (not an in-guild product feature). |
| `product_subsystem` | 24 | A feature vertical with its own owner, views, and tests. |
| `shared_platform` | 6 | A broad cross-cutting capability with high blast radius (admin, settings, AI, diagnostics, help, utility). |
| `specialized_surface` | 5 | One of several surfaces within a single domain vertical (e.g. the BTD6 sub-cogs) — backs a registered subsystem rather than being its own. |

## Crosswalk (load order)

| # | Extension | Role | Registered | Backs | Note |
|---:|---|---|:--:|---|---|
| 1 | `bootstrap_access` | `bootstrap` | — |  | Installs the prefix+slash command-access guard; MUST load first. Platform admission, not a product subsystem. |
| 2 | `admin` | `shared_platform` | ✓ |  | Cog management, server stats, diagnostics entry; administrator floor. |
| 3 | `help` | `shared_platform` | ✓ |  | Help catalogue/projection surface; every subsystem's Help route composes it. |
| 4 | `role` | `product_subsystem` | ✓ |  |  |
| 5 | `moderation` | `product_subsystem` | ✓ |  |  |
| 6 | `automod` | `product_subsystem` | ✓ |  | Automod rules engine (Q-0108). |
| 7 | `xp` | `product_subsystem` | ✓ |  |  |
| 8 | `blackjack` | `product_subsystem` | ✓ |  | Game. |
| 9 | `rps_tournament` | `product_subsystem` | ✓ |  | Game (tournament orchestration). |
| 10 | `utility` | `shared_platform` | ✓ |  | General utility commands. |
| 11 | `cleanup` | `product_subsystem` | ✓ |  | Message-cleanup policy. |
| 12 | `channel` | `product_subsystem` | ✓ |  | Channel management (server-management area). |
| 13 | `inventory` | `product_subsystem` | ✓ |  |  |
| 14 | `economy` | `product_subsystem` | ✓ |  |  |
| 15 | `counting` | `product_subsystem` | ✓ |  | Counting game. |
| 16 | `deathmatch` | `product_subsystem` | ✓ |  | Game (1v1 duels). |
| 17 | `proof_channel` | `product_subsystem` | ✓ |  |  |
| 18 | `mining` | `product_subsystem` | ✓ |  | Mining character platform (large vertical). |
| 19 | `fishing` | `product_subsystem` | ✓ |  | Fishing minigame (ecosystem |
| 20 | `diagnostic` | `shared_platform` | ✓ |  | `!platform` diagnostics; broad cross-subsystem read-model surface. |
| 21 | `health_maintenance` | `maintenance` | — | `diagnostic` | Scheduled health-findings retention loop; no subsystem identity. |
| 22 | `ai` | `shared_platform` | ✓ |  | AI orchestration / answerability; cross-cutting. |
| 23 | `media_maintenance` | `maintenance` | — |  | Scheduled media/YouTube cache purge loop; no subsystem identity. |
| 24 | `btd6` | `product_subsystem` | ✓ |  | BTD6 core data / answerability vertical. |
| 25 | `btd6_reference` | `specialized_surface` | — | `btd6` | BTD6 reference lookups. |
| 26 | `btd6_events` | `specialized_surface` | — | `btd6` | BTD6 live-events surface. |
| 27 | `btd6_strategy` | `specialized_surface` | — | `btd6` |  |
| 28 | `paragon` | `specialized_surface` | — | `btd6` | BTD6 paragon grounding surface. |
| 29 | `btd6_ops` | `specialized_surface` | — | `btd6` | BTD6 data-ops (seed/refresh); operational flavor within the BTD6 vertical. |
| 30 | `chain` | `product_subsystem` | ✓ |  | Command-chain subsystem. |
| 31 | `general` | `product_subsystem` | ✓ |  | General-content commands. |
| 32 | `four_twenty` | `product_subsystem` | ✓ |  | Novelty / community feature. |
| 33 | `leaderboard` | `product_subsystem` | ✓ |  | Cross-subsystem leaderboards (reads XP/games). |
| 34 | `settings` | `shared_platform` | ✓ |  | Settings hub; cross-cutting config surface. |
| 35 | `logging` | `product_subsystem` | ✓ |  | Server-logging subsystem. |
| 36 | `games` | `hub` | ✓ |  | Games hub (routes blackjack/deathmatch/counting/rps). |
| 37 | `community` | `hub` | ✓ |  | Community hub. |
| 38 | `community_spotlight` | `product_subsystem` | ✓ |  | Community Spotlight (community-hub child; registered subsystem). |
| 39 | `welcome` | `product_subsystem` | ✓ |  | Welcome service (join embeds + optional PIL cards). |
| 40 | `counters` | `product_subsystem` | ✓ |  | Dynamic server counters. |
| 41 | `setup` | `bootstrap` | — | `server_management` | Guided setup wizard; lifecycle-critical, load-order sensitive. |
| 42 | `server_management` | `hub` | ✓ |  | Routing-only hub (moderation/channels/roles/cleanup/setup); holds no capability of its own. |
| 43 | `hermes` | `operational_adapter` | — |  | Bridge to the Hermes control plane / external operation. |
| 44 | `ux_lab` | `lab` | ✓ |  | Zero-write UX pattern gallery (admin-gated); design vocabulary, not a product surface. |

## Non-1:1 extensions (no registry identity)

These load as extensions but are **not** registered subsystems — they are classified by role instead of being product verticals:

- `bootstrap_access` (`bootstrap`) — Installs the prefix+slash command-access guard; MUST load first. Platform admission, not a product subsystem.
- `health_maintenance` (`maintenance` → backs `diagnostic`) — Scheduled health-findings retention loop; no subsystem identity.
- `media_maintenance` (`maintenance`) — Scheduled media/YouTube cache purge loop; no subsystem identity.
- `btd6_reference` (`specialized_surface` → backs `btd6`) — BTD6 reference lookups.
- `btd6_events` (`specialized_surface` → backs `btd6`) — BTD6 live-events surface.
- `btd6_strategy` (`specialized_surface` → backs `btd6`)
- `paragon` (`specialized_surface` → backs `btd6`) — BTD6 paragon grounding surface.
- `btd6_ops` (`specialized_surface` → backs `btd6`) — BTD6 data-ops (seed/refresh); operational flavor within the BTD6 vertical.
- `setup` (`bootstrap` → backs `server_management`) — Guided setup wizard; lifecycle-critical, load-order sensitive.
- `hermes` (`operational_adapter`) — Bridge to the Hermes control plane / external operation.

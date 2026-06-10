# Platform mapping A — user surface

> **Status:** `audit` — run 2026-06-09 at HEAD `560e35198c46e5d624344b73e94d17dd16d77dcd`. Mapping-only report for Agent A’s user-facing scope. The binding standard was read from live PR #641 because it was not present at this checkout; its pre-allocated Agent A link is included in this branch.
>
> **Post-campaign note (2026-06-10):** the live-PR claims in this report are
> **mapping-time state** — #638–#645 (including #640/#641/#642, named "open" below)
> have all merged. Finding dispositions + the live queue:
> [`consolidated-implementation-plan-2026-06-10.md`](consolidated-implementation-plan-2026-06-10.md)
> (Q-A01 → router **Q-0073**; Q-A02/Q-A03 held at their recommended defaults).

## Executive summary

### Severity-ranked findings

- **Severity 1:** none verified in the user-facing surface.
- **Severity 2:** FIND-A01 mining’s large hidden typed surface is not represented with ledger `panel_action` classifications; FIND-A02 Economy owns a platform-binding-shaped `setlogchannel`; FIND-A03 Counting keeps mutable match state in a cog-local dictionary and persists from that owner; FIND-A06 the BTD6 user panel advertises typed paths whose implementations are split across separate root groups.
- **Severity 3:** FIND-A04 Leaderboard overloads one command with nine compatibility aliases; FIND-A05 Utility keeps three hidden compatibility commands without ledger classifications; FIND-A07 BTD6’s five split cogs have no independent Help hooks and therefore rely entirely on the aggregate panel/typed routes.
- **Severity 4:** two gate-respecting ideas are captured in Future opportunities; neither is active work.

### Verified baseline and counts

- Source enumeration found **17 registered subsystems**, **22 owning/split cogs**, and **164 decorated command entrypoints** in scope (prefix/group and slash entries counted separately; listener decorators excluded). Verified with the AST enumeration recorded in the Verification log.
- Live GitHub API verification on 2026-06-09 found **#638 open**, **#639 merged**, **#640 open**, **#641 open**, and **#642 open**. This corrects the standard §2.4 expectation for #639; its merge does not materially rewrite Agent A’s command/panel surface. BTD6 data services and AI-tool internals remain recommendation-free because #638 is open.
- The source baseline still has 36 loaded extensions, 29 registered subsystems, and 10 mother hubs; this report does not remap the Help/registry architecture.

### games

1. **subsystem_key** — `games` (`disbot/utils/subsystem_registry.py:310`).
2. **owning_cog** — `disbot/cogs/games_cog.py`.
3. **owning_services** — `disbot/services/game_state_service.py`, `disbot/services/game_state_cleanup.py`.
4. **hub_placement** — top-level Games hub; actual panel hook/view verified in the owning cog.
5. **help_routes** — typed `!help games`, dropdown/Advanced registry route, and aliases resolve to the owning cog; child routing opens the cog hook when present.
6. **panel_entry** — `GamesHubView — disbot/views/games/hub.py:321`; detected by the owning cog’s panel command/hook and catalogue conventions.
7. **settings_setup_routes** — domain panel or none; no setup section was mapped in Agent A scope.
8. **governance_access** — user-tier by registry except command-local administrator checks; execution access remains separate from display visibility.
9. **placement_tier** — `top_level`; placement is correct.
10. **overlap** — none requiring merge; named cross-domain reads are intentional.
11. **protections** — subsystem tests under `tests/unit/cogs/`, `tests/unit/views/`, and architecture/invariant tests; inventory docs: `docs/help-command-surface-map.md` and relevant subsystem folios.
12. **gaps_risks** — none beyond mapped future opportunities.

#### Commands

| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `!games` | — | prefix | `disbot/cogs/games_cog.py` | user | `primary_entrypoint` | typed/Advanced | GamesHubView | yes | yes | — | yes | `keep` | `disbot/cogs/games_cog.py:38` |
| `/games` | — | slash | `disbot/cogs/games_cog.py` | user | `primary_entrypoint` | typed/Advanced | GamesHubView | yes | yes | — | yes | `keep` | `disbot/cogs/games_cog.py:55` |

#### Panels/views

1. **view** — GamesHubView — disbot/views/games/hub.py:321.
2. **entry** — owning panel command, Help hook, and parent-hub child selection.
3. **preset** — User Navigation Hub; conforms in broad action-vs-navigation role.
4. **components** — buttons/selects/modals route to the command/service surfaces enumerated above; live member/game choices are built at callback/open time where applicable.
5. **navigation** — child panels return through shared hub/back patterns; persistent anchors are used by Mining and BTD6, ephemeral invoker-locked views elsewhere.
6. **lifecycle_safety** — I/O-heavy slash/browser callbacks use `safe_defer`; game views use interaction checks and terminal-state controls where relevant.
7. **multiselect_fit** — no verified bounded multi-select replacement required in the current user flow.
8. **copy_consistency** — consistent with the owning command surface.
9. **visibility** — user-tier panel; command-local staff actions remain permission checked.
10. **reuse** — shared `HubView`/`BaseView`/`PersistentView` patterns, with specialized game-state views allowed by architecture.
11. **consistency_gaps** — none verified.

#### Services/helpers/workflows

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `services/game_state_service.py` | games domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/games_cog.py:1` |
| `services/game_state_cleanup.py` | games domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/games_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes: top-level Games hub; registry/source verified.
2. **Useful commands discoverable?** Mostly; typed commands remain available through Advanced/typed Help, while the principal panel is `GamesHubView`.
3. **Merge/hide legacy?** No additional merge/hide recommendation from this mapping.
4. **Commands in another subsystem?** No verified misplaced command.
5. **Overlapping services?** No unowned duplicate service verified.
6. **Components consistent?** Principal panel uses the closest Feature Action Panel/User Navigation Hub preset; noted exceptions are findings.
7. **Dynamic and permission-safe?** Live member/channel choices are dynamic where present; mutating commands use Discord permission checks or invoker checks.
8. **Names clear?** Generally yes; aliases preserve typed fluency.
9. **Obvious missing action?** None promoted; ideas are captured only in Future opportunities.
10. **Gate/ADR consistent?** Yes; no Redis/restart-safety/provenance-expansion recommendation is made.
11. **Implementation vs future?** Implement severity-2/3 findings after merge-session review; keep future ideas gated and inactive.

### blackjack

1. **subsystem_key** — `blackjack` (`disbot/utils/subsystem_registry.py:385`).
2. **owning_cog** — `disbot/cogs/blackjack_cog.py`.
3. **owning_services** — `disbot/services/blackjack_engine.py`, `disbot/services/economy_service.py`, `disbot/services/game_state_service.py`, `disbot/services/tournament_state_service.py`.
4. **hub_placement** — Games child; actual panel hook/view verified in the owning cog.
5. **help_routes** — typed `!help blackjack`, dropdown/Advanced registry route, and aliases resolve to the owning cog; child routing opens the cog hook when present.
6. **panel_entry** — `BlackjackPanelView — disbot/views/games/blackjack_panel.py:440`; detected by the owning cog’s panel command/hook and catalogue conventions.
7. **settings_setup_routes** — domain panel or none; no setup section was mapped in Agent A scope.
8. **governance_access** — user-tier by registry except command-local administrator checks; execution access remains separate from display visibility.
9. **placement_tier** — `child`; placement is correct.
10. **overlap** — none requiring merge; named cross-domain reads are intentional.
11. **protections** — subsystem tests under `tests/unit/cogs/`, `tests/unit/views/`, and architecture/invariant tests; inventory docs: `docs/help-command-surface-map.md` and relevant subsystem folios.
12. **gaps_risks** — none beyond mapped future opportunities.

#### Commands

| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `!blackjack` | bj | prefix | `disbot/cogs/blackjack_cog.py` | user | `primary_entrypoint` | typed/Advanced | BlackjackPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/blackjack_cog.py:409` |
| `!bjtournament` | bjtourn | prefix | `disbot/cogs/blackjack_cog.py` | admin | `primary_entrypoint` | typed/Advanced | BlackjackPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/blackjack_cog.py:495` |
| `!bjstart` | — | prefix | `disbot/cogs/blackjack_cog.py` | admin | `primary_entrypoint` | typed/Advanced | BlackjackPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/blackjack_cog.py:556` |
| `!bjstatus` | — | prefix | `disbot/cogs/blackjack_cog.py` | user | `primary_entrypoint` | typed/Advanced | BlackjackPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/blackjack_cog.py:567` |

#### Panels/views

1. **view** — BlackjackPanelView — disbot/views/games/blackjack_panel.py:440.
2. **entry** — owning panel command, Help hook, and parent-hub child selection.
3. **preset** — Feature Action Panel; conforms in broad action-vs-navigation role.
4. **components** — buttons/selects/modals route to the command/service surfaces enumerated above; live member/game choices are built at callback/open time where applicable.
5. **navigation** — child panels return through shared hub/back patterns; persistent anchors are used by Mining and BTD6, ephemeral invoker-locked views elsewhere.
6. **lifecycle_safety** — I/O-heavy slash/browser callbacks use `safe_defer`; game views use interaction checks and terminal-state controls where relevant.
7. **multiselect_fit** — no verified bounded multi-select replacement required in the current user flow.
8. **copy_consistency** — consistent with the owning command surface.
9. **visibility** — user-tier panel; command-local staff actions remain permission checked.
10. **reuse** — shared `HubView`/`BaseView`/`PersistentView` patterns, with specialized game-state views allowed by architecture.
11. **consistency_gaps** — none verified.

#### Services/helpers/workflows

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `services/blackjack_engine.py` | blackjack domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/blackjack_cog.py:1` |
| `services/economy_service.py` | blackjack domain/read model | owning cog/views; grep-verified | mutating-audited | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/blackjack_cog.py:1` |
| `services/game_state_service.py` | blackjack domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/blackjack_cog.py:1` |
| `services/tournament_state_service.py` | blackjack domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/blackjack_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes: Games child; registry/source verified.
2. **Useful commands discoverable?** Mostly; typed commands remain available through Advanced/typed Help, while the principal panel is `BlackjackPanelView`.
3. **Merge/hide legacy?** No additional merge/hide recommendation from this mapping.
4. **Commands in another subsystem?** No verified misplaced command.
5. **Overlapping services?** No unowned duplicate service verified.
6. **Components consistent?** Principal panel uses the closest Feature Action Panel/User Navigation Hub preset; noted exceptions are findings.
7. **Dynamic and permission-safe?** Live member/channel choices are dynamic where present; mutating commands use Discord permission checks or invoker checks.
8. **Names clear?** Generally yes; aliases preserve typed fluency.
9. **Obvious missing action?** None promoted; ideas are captured only in Future opportunities.
10. **Gate/ADR consistent?** Yes; no Redis/restart-safety/provenance-expansion recommendation is made.
11. **Implementation vs future?** Implement severity-2/3 findings after merge-session review; keep future ideas gated and inactive.

### rps_tournament

1. **subsystem_key** — `rps_tournament` (`disbot/utils/subsystem_registry.py:467`).
2. **owning_cog** — `disbot/cogs/rps_tournament_cog.py`.
3. **owning_services** — `disbot/services/economy_service.py`, `disbot/services/game_state_service.py`, `disbot/services/tournament_state_service.py`.
4. **hub_placement** — Games child; actual panel hook/view verified in the owning cog.
5. **help_routes** — typed `!help rps_tournament`, dropdown/Advanced registry route, and aliases resolve to the owning cog; child routing opens the cog hook when present.
6. **panel_entry** — `RPSPanelView — disbot/views/games/rps_panel.py:557`; detected by the owning cog’s panel command/hook and catalogue conventions.
7. **settings_setup_routes** — domain panel or none; no setup section was mapped in Agent A scope.
8. **governance_access** — user-tier by registry except command-local administrator checks; execution access remains separate from display visibility.
9. **placement_tier** — `child`; placement is correct.
10. **overlap** — none requiring merge; named cross-domain reads are intentional.
11. **protections** — subsystem tests under `tests/unit/cogs/`, `tests/unit/views/`, and architecture/invariant tests; inventory docs: `docs/help-command-surface-map.md` and relevant subsystem folios.
12. **gaps_risks** — none beyond mapped future opportunities.

#### Commands

| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `!rpsregister` | rpsreg | prefix | `disbot/cogs/rps_tournament_cog.py` | user | `primary_entrypoint` | typed/Advanced | RPSPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/rps_tournament_cog.py:181` |
| `!rpsstart` | rpsbegin | prefix | `disbot/cogs/rps_tournament_cog.py` | admin | `primary_entrypoint` | typed/Advanced | RPSPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/rps_tournament_cog.py:352` |
| `!rpsbot` | — | prefix | `disbot/cogs/rps_tournament_cog.py` | user | `primary_entrypoint` | typed/Advanced | RPSPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/rps_tournament_cog.py:394` |
| `!rpsmatchup` | — | prefix | `disbot/cogs/rps_tournament_cog.py` | admin | `primary_entrypoint` | typed/Advanced | RPSPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/rps_tournament_cog.py:407` |
| `!rpshelp` | — | prefix | `disbot/cogs/rps_tournament_cog.py` | user | `primary_entrypoint` | typed/Advanced | RPSPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/rps_tournament_cog.py:728` |
| `!rpssettings` | — | prefix | `disbot/cogs/rps_tournament_cog.py` | admin | `primary_entrypoint` | typed/Advanced | RPSPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/rps_tournament_cog.py:745` |
| `!rps` | — | prefix | `disbot/cogs/rps_tournament_cog.py` | user | `primary_entrypoint` | typed/Advanced | RPSPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/rps_tournament_cog.py:776` |

#### Panels/views

1. **view** — RPSPanelView — disbot/views/games/rps_panel.py:557.
2. **entry** — owning panel command, Help hook, and parent-hub child selection.
3. **preset** — Feature Action Panel; conforms in broad action-vs-navigation role.
4. **components** — buttons/selects/modals route to the command/service surfaces enumerated above; live member/game choices are built at callback/open time where applicable.
5. **navigation** — child panels return through shared hub/back patterns; persistent anchors are used by Mining and BTD6, ephemeral invoker-locked views elsewhere.
6. **lifecycle_safety** — I/O-heavy slash/browser callbacks use `safe_defer`; game views use interaction checks and terminal-state controls where relevant.
7. **multiselect_fit** — no verified bounded multi-select replacement required in the current user flow.
8. **copy_consistency** — consistent with the owning command surface.
9. **visibility** — user-tier panel; command-local staff actions remain permission checked.
10. **reuse** — shared `HubView`/`BaseView`/`PersistentView` patterns, with specialized game-state views allowed by architecture.
11. **consistency_gaps** — none verified.

#### Services/helpers/workflows

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `services/economy_service.py` | rps_tournament domain/read model | owning cog/views; grep-verified | mutating-audited | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/rps_tournament_cog.py:1` |
| `services/game_state_service.py` | rps_tournament domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/rps_tournament_cog.py:1` |
| `services/tournament_state_service.py` | rps_tournament domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/rps_tournament_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes: Games child; registry/source verified.
2. **Useful commands discoverable?** Mostly; typed commands remain available through Advanced/typed Help, while the principal panel is `RPSPanelView`.
3. **Merge/hide legacy?** No additional merge/hide recommendation from this mapping.
4. **Commands in another subsystem?** No verified misplaced command.
5. **Overlapping services?** No unowned duplicate service verified.
6. **Components consistent?** Principal panel uses the closest Feature Action Panel/User Navigation Hub preset; noted exceptions are findings.
7. **Dynamic and permission-safe?** Live member/channel choices are dynamic where present; mutating commands use Discord permission checks or invoker checks.
8. **Names clear?** Generally yes; aliases preserve typed fluency.
9. **Obvious missing action?** None promoted; ideas are captured only in Future opportunities.
10. **Gate/ADR consistent?** Yes; no Redis/restart-safety/provenance-expansion recommendation is made.
11. **Implementation vs future?** Implement severity-2/3 findings after merge-session review; keep future ideas gated and inactive.

### deathmatch

1. **subsystem_key** — `deathmatch` (`disbot/utils/subsystem_registry.py:443`).
2. **owning_cog** — `disbot/cogs/deathmatch_cog.py`.
3. **owning_services** — `disbot/utils/db/games/deathmatch.py`, `disbot/cogs/deathmatch/actions.py`.
4. **hub_placement** — Games child; actual panel hook/view verified in the owning cog.
5. **help_routes** — typed `!help deathmatch`, dropdown/Advanced registry route, and aliases resolve to the owning cog; child routing opens the cog hook when present.
6. **panel_entry** — `DeathmatchPanelView — disbot/views/games/deathmatch_panel.py:409`; detected by the owning cog’s panel command/hook and catalogue conventions.
7. **settings_setup_routes** — domain panel or none; no setup section was mapped in Agent A scope.
8. **governance_access** — user-tier by registry except command-local administrator checks; execution access remains separate from display visibility.
9. **placement_tier** — `child`; placement is correct.
10. **overlap** — none requiring merge; named cross-domain reads are intentional.
11. **protections** — subsystem tests under `tests/unit/cogs/`, `tests/unit/views/`, and architecture/invariant tests; inventory docs: `docs/help-command-surface-map.md` and relevant subsystem folios.
12. **gaps_risks** — none beyond mapped future opportunities.

#### Commands

| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `!dm_challenge` | deathmatch, challenge, dm | prefix | `disbot/cogs/deathmatch_cog.py` | user | `primary_entrypoint` | typed/Advanced | DeathmatchPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/deathmatch_cog.py:339` |
| `!dm_help` | deathmatch_help | prefix | `disbot/cogs/deathmatch_cog.py` | user | `primary_entrypoint` | typed/Advanced | DeathmatchPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/deathmatch_cog.py:392` |

#### Panels/views

1. **view** — DeathmatchPanelView — disbot/views/games/deathmatch_panel.py:409.
2. **entry** — owning panel command, Help hook, and parent-hub child selection.
3. **preset** — Feature Action Panel; conforms in broad action-vs-navigation role.
4. **components** — buttons/selects/modals route to the command/service surfaces enumerated above; live member/game choices are built at callback/open time where applicable.
5. **navigation** — child panels return through shared hub/back patterns; persistent anchors are used by Mining and BTD6, ephemeral invoker-locked views elsewhere.
6. **lifecycle_safety** — I/O-heavy slash/browser callbacks use `safe_defer`; game views use interaction checks and terminal-state controls where relevant.
7. **multiselect_fit** — no verified bounded multi-select replacement required in the current user flow.
8. **copy_consistency** — consistent with the owning command surface.
9. **visibility** — user-tier panel; command-local staff actions remain permission checked.
10. **reuse** — shared `HubView`/`BaseView`/`PersistentView` patterns, with specialized game-state views allowed by architecture.
11. **consistency_gaps** — none verified.

#### Services/helpers/workflows

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `utils/db/games/deathmatch.py` | deathmatch domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/deathmatch_cog.py:1` |
| `cogs/deathmatch/actions.py` | deathmatch domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/deathmatch_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes: Games child; registry/source verified.
2. **Useful commands discoverable?** Mostly; typed commands remain available through Advanced/typed Help, while the principal panel is `DeathmatchPanelView`.
3. **Merge/hide legacy?** No additional merge/hide recommendation from this mapping.
4. **Commands in another subsystem?** No verified misplaced command.
5. **Overlapping services?** No unowned duplicate service verified.
6. **Components consistent?** Principal panel uses the closest Feature Action Panel/User Navigation Hub preset; noted exceptions are findings.
7. **Dynamic and permission-safe?** Live member/channel choices are dynamic where present; mutating commands use Discord permission checks or invoker checks.
8. **Names clear?** Generally yes; aliases preserve typed fluency.
9. **Obvious missing action?** None promoted; ideas are captured only in Future opportunities.
10. **Gate/ADR consistent?** Yes; no Redis/restart-safety/provenance-expansion recommendation is made.
11. **Implementation vs future?** Implement severity-2/3 findings after merge-session review; keep future ideas gated and inactive.

### counting

1. **subsystem_key** — `counting` (`disbot/utils/subsystem_registry.py:491`).
2. **owning_cog** — `disbot/cogs/counting_cog.py`.
3. **owning_services** — `disbot/utils/db/games/counting.py`, `disbot/cogs/counting/handler.py`.
4. **hub_placement** — Games child; actual panel hook/view verified in the owning cog.
5. **help_routes** — typed `!help counting`, dropdown/Advanced registry route, and aliases resolve to the owning cog; child routing opens the cog hook when present.
6. **panel_entry** — `_CountingHubView — disbot/views/counting/hub_panel.py:1`; detected by the owning cog’s panel command/hook and catalogue conventions.
7. **settings_setup_routes** — domain panel or none; no setup section was mapped in Agent A scope.
8. **governance_access** — user-tier by registry except command-local administrator checks; execution access remains separate from display visibility.
9. **placement_tier** — `child`; placement is correct.
10. **overlap** — none requiring merge; named cross-domain reads are intentional.
11. **protections** — subsystem tests under `tests/unit/cogs/`, `tests/unit/views/`, and architecture/invariant tests; inventory docs: `docs/help-command-surface-map.md` and relevant subsystem folios.
12. **gaps_risks** — FIND-A03.

#### Commands

| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `!countingmenu` | cm | prefix | `disbot/cogs/counting_cog.py` | user | `primary_entrypoint` | typed/Advanced | _CountingHubView | yes | yes | — | yes | `keep` | `disbot/cogs/counting_cog.py:129` |
| `!start_match` | sm | prefix | `disbot/cogs/counting_cog.py` | user | `primary_entrypoint` | typed/Advanced | _CountingHubView | yes | yes | — | yes | `keep` | `disbot/cogs/counting_cog.py:146` |
| `!end_match` | em | prefix | `disbot/cogs/counting_cog.py` | user | `primary_entrypoint` | typed/Advanced | _CountingHubView | yes | yes | — | yes | `keep` | `disbot/cogs/counting_cog.py:333` |
| `!reset_count` | rc | prefix | `disbot/cogs/counting_cog.py` | user | `primary_entrypoint` | typed/Advanced | _CountingHubView | yes | yes | — | yes | `keep` | `disbot/cogs/counting_cog.py:382` |
| `!toggle_turns` | tt | prefix | `disbot/cogs/counting_cog.py` | user | `primary_entrypoint` | typed/Advanced | _CountingHubView | yes | yes | — | yes | `keep` | `disbot/cogs/counting_cog.py:437` |
| `!count_info` | ci | prefix | `disbot/cogs/counting_cog.py` | user | `primary_entrypoint` | typed/Advanced | _CountingHubView | yes | yes | — | yes | `keep` | `disbot/cogs/counting_cog.py:466` |
| `!count_rules` | cr | prefix | `disbot/cogs/counting_cog.py` | user | `primary_entrypoint` | typed/Advanced | _CountingHubView | yes | yes | — | yes | `keep` | `disbot/cogs/counting_cog.py:516` |
| `!set_skip_numbers` | ssn | prefix | `disbot/cogs/counting_cog.py` | user | `primary_entrypoint` | typed/Advanced | _CountingHubView | yes | yes | — | yes | `keep` | `disbot/cogs/counting_cog.py:548` |
| `!toggle_reset_on_wrong_count` | trwc | prefix | `disbot/cogs/counting_cog.py` | user | `primary_entrypoint` | typed/Advanced | _CountingHubView | yes | yes | — | yes | `keep` | `disbot/cogs/counting_cog.py:599` |

#### Panels/views

1. **view** — _CountingHubView — disbot/views/counting/hub_panel.py:1.
2. **entry** — owning panel command, Help hook, and parent-hub child selection.
3. **preset** — Feature Action Panel; conforms in broad action-vs-navigation role.
4. **components** — buttons/selects/modals route to the command/service surfaces enumerated above; live member/game choices are built at callback/open time where applicable.
5. **navigation** — child panels return through shared hub/back patterns; persistent anchors are used by Mining and BTD6, ephemeral invoker-locked views elsewhere.
6. **lifecycle_safety** — I/O-heavy slash/browser callbacks use `safe_defer`; game views use interaction checks and terminal-state controls where relevant.
7. **multiselect_fit** — no verified bounded multi-select replacement required in the current user flow.
8. **copy_consistency** — consistent with the owning command surface.
9. **visibility** — user-tier panel; command-local staff actions remain permission checked.
10. **reuse** — shared `HubView`/`BaseView`/`PersistentView` patterns, with specialized game-state views allowed by architecture.
11. **consistency_gaps** — FIND-A03.

#### Services/helpers/workflows

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `utils/db/games/counting.py` | counting domain/read model | owning cog/views; grep-verified | mutating-unaudited | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `reorganize`; `disbot/cogs/counting_cog.py:1` |
| `cogs/counting/handler.py` | counting domain/read model | owning cog/views; grep-verified | mutating-unaudited | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `reorganize`; `disbot/cogs/counting_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes: Games child; registry/source verified.
2. **Useful commands discoverable?** Mostly; typed commands remain available through Advanced/typed Help, while the principal panel is `_CountingHubView`.
3. **Merge/hide legacy?** See FIND-A03.
4. **Commands in another subsystem?** No verified misplaced command.
5. **Overlapping services?** No unowned duplicate service verified.
6. **Components consistent?** Principal panel uses the closest Feature Action Panel/User Navigation Hub preset; noted exceptions are findings.
7. **Dynamic and permission-safe?** Live member/channel choices are dynamic where present; mutating commands use Discord permission checks or invoker checks.
8. **Names clear?** Generally yes; aliases preserve typed fluency.
9. **Obvious missing action?** None promoted; ideas are captured only in Future opportunities.
10. **Gate/ADR consistent?** Yes; no Redis/restart-safety/provenance-expansion recommendation is made.
11. **Implementation vs future?** Implement severity-2/3 findings after merge-session review; keep future ideas gated and inactive.

```text
FIND-A03 [2 important improvement] Counting’s mutable match owner is a cog-local dictionary with persistence calls from the cog rather than a named domain service.
  evidence: disbot/cogs/counting_cog.py:78-101 · `count_data` load/save lifecycle
  verified-by: read source + context map
  verdict: reorganize
```

### chain

1. **subsystem_key** — `chain` (`disbot/utils/subsystem_registry.py:515`).
2. **owning_cog** — `disbot/cogs/chain_cog.py`.
3. **owning_services** — `disbot/utils/db/games/chain.py`.
4. **hub_placement** — Games child; actual panel hook/view verified in the owning cog.
5. **help_routes** — typed `!help chain`, dropdown/Advanced registry route, and aliases resolve to the owning cog; child routing opens the cog hook when present.
6. **panel_entry** — `ChainMenuView — disbot/cogs/chain_cog.py:541`; detected by the owning cog’s panel command/hook and catalogue conventions.
7. **settings_setup_routes** — domain panel or none; no setup section was mapped in Agent A scope.
8. **governance_access** — user-tier by registry except command-local administrator checks; execution access remains separate from display visibility.
9. **placement_tier** — `child`; placement is correct.
10. **overlap** — none requiring merge; named cross-domain reads are intentional.
11. **protections** — subsystem tests under `tests/unit/cogs/`, `tests/unit/views/`, and architecture/invariant tests; inventory docs: `docs/help-command-surface-map.md` and relevant subsystem folios.
12. **gaps_risks** — none beyond mapped future opportunities.

#### Commands

| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `!chain` | — | prefix | `disbot/cogs/chain_cog.py` | user | `primary_entrypoint` | typed/Advanced | ChainMenuView | yes | yes | — | yes | `keep` | `disbot/cogs/chain_cog.py:69` |
| `!create` | — | prefix | `disbot/cogs/chain_cog.py` | admin | `primary_entrypoint` | typed/Advanced | ChainMenuView | yes | yes | — | yes | `keep` | `disbot/cogs/chain_cog.py:80` |
| `!delete` | — | prefix | `disbot/cogs/chain_cog.py` | admin | `primary_entrypoint` | typed/Advanced | ChainMenuView | yes | yes | — | yes | `keep` | `disbot/cogs/chain_cog.py:128` |
| `!setlimit` | — | prefix | `disbot/cogs/chain_cog.py` | admin | `primary_entrypoint` | typed/Advanced | ChainMenuView | yes | yes | — | yes | `keep` | `disbot/cogs/chain_cog.py:160` |
| `!removelimit` | — | prefix | `disbot/cogs/chain_cog.py` | admin | `primary_entrypoint` | typed/Advanced | ChainMenuView | yes | yes | — | yes | `keep` | `disbot/cogs/chain_cog.py:207` |
| `!chainmenu` | — | prefix | `disbot/cogs/chain_cog.py` | admin | `primary_entrypoint` | typed/Advanced | ChainMenuView | yes | yes | — | yes | `keep` | `disbot/cogs/chain_cog.py:240` |
| `!list` | — | prefix | `disbot/cogs/chain_cog.py` | user | `primary_entrypoint` | typed/Advanced | ChainMenuView | yes | yes | — | yes | `keep` | `disbot/cogs/chain_cog.py:256` |

#### Panels/views

1. **view** — ChainMenuView — disbot/cogs/chain_cog.py:541.
2. **entry** — owning panel command, Help hook, and parent-hub child selection.
3. **preset** — Feature Action Panel; conforms in broad action-vs-navigation role.
4. **components** — buttons/selects/modals route to the command/service surfaces enumerated above; live member/game choices are built at callback/open time where applicable.
5. **navigation** — child panels return through shared hub/back patterns; persistent anchors are used by Mining and BTD6, ephemeral invoker-locked views elsewhere.
6. **lifecycle_safety** — I/O-heavy slash/browser callbacks use `safe_defer`; game views use interaction checks and terminal-state controls where relevant.
7. **multiselect_fit** — no verified bounded multi-select replacement required in the current user flow.
8. **copy_consistency** — consistent with the owning command surface.
9. **visibility** — user-tier panel; command-local staff actions remain permission checked.
10. **reuse** — shared `HubView`/`BaseView`/`PersistentView` patterns, with specialized game-state views allowed by architecture.
11. **consistency_gaps** — none verified.

#### Services/helpers/workflows

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `utils/db/games/chain.py` | chain domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/chain_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes: Games child; registry/source verified.
2. **Useful commands discoverable?** Mostly; typed commands remain available through Advanced/typed Help, while the principal panel is `ChainMenuView`.
3. **Merge/hide legacy?** No additional merge/hide recommendation from this mapping.
4. **Commands in another subsystem?** No verified misplaced command.
5. **Overlapping services?** No unowned duplicate service verified.
6. **Components consistent?** Principal panel uses the closest Feature Action Panel/User Navigation Hub preset; noted exceptions are findings.
7. **Dynamic and permission-safe?** Live member/channel choices are dynamic where present; mutating commands use Discord permission checks or invoker checks.
8. **Names clear?** Generally yes; aliases preserve typed fluency.
9. **Obvious missing action?** None promoted; ideas are captured only in Future opportunities.
10. **Gate/ADR consistent?** Yes; no Redis/restart-safety/provenance-expansion recommendation is made.
11. **Implementation vs future?** Implement severity-2/3 findings after merge-session review; keep future ideas gated and inactive.

### mining

1. **subsystem_key** — `mining` (`disbot/utils/subsystem_registry.py:187`).
2. **owning_cog** — `disbot/cogs/mining_cog.py`.
3. **owning_services** — `disbot/utils/db/games/mining.py`, `disbot/utils/db/games/mining_equipment.py`, `disbot/services/economy_service.py`.
4. **hub_placement** — Games child; Economy cross-link; actual panel hook/view verified in the owning cog.
5. **help_routes** — typed `!help mining`, dropdown/Advanced registry route, and aliases resolve to the owning cog; child routing opens the cog hook when present.
6. **panel_entry** — `MiningHubView — disbot/views/mining/main_panel.py:124`; detected by the owning cog’s panel command/hook and catalogue conventions.
7. **settings_setup_routes** — domain panel or none; no setup section was mapped in Agent A scope.
8. **governance_access** — user-tier by registry except command-local administrator checks; execution access remains separate from display visibility.
9. **placement_tier** — `cross_linked`; placement is correct.
10. **overlap** — none requiring merge; named cross-domain reads are intentional.
11. **protections** — subsystem tests under `tests/unit/cogs/`, `tests/unit/views/`, and architecture/invariant tests; inventory docs: `docs/help-command-surface-map.md` and relevant subsystem folios.
12. **gaps_risks** — FIND-A01.

#### Commands

| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `!minemenu` | — | prefix | `disbot/cogs/mining_cog.py` | user | `primary_entrypoint` | typed/Advanced | MiningHubView | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:64` |
| `!mine` | — | prefix | `disbot/cogs/mining_cog.py` | user | `primary_entrypoint` | typed/Advanced | MiningHubView | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:98` |
| `!chop` | — | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:112` |
| `!mineinv` | mineinventory | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:125` |
| `!minestats` | — | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:134` |
| `!build` | craft | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:159` |
| `!buildlist` | — | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:174` |
| `!buildable` | — | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:202` |
| `!explore` | — | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:227` |
| `!use` | — | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:254` |
| `!equip` | — | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:280` |
| `!unequip` | — | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:299` |
| `!gear` | — | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:314` |
| `!character` | profile, char | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:352` |
| `!descend` | — | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:367` |
| `!ascend` | — | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:386` |
| `!sell` | — | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:403` |
| `!sellall` | — | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:413` |
| `!buy` | — | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:419` |
| `!market` | — | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:427` |
| `!workshop` | — | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:459` |
| `!repair` | — | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:472` |
| `!quickcraft` | — | prefix | `disbot/cogs/mining_cog.py` | user | `hidden` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:482` |
| `!reset_inventory` | — | prefix | `disbot/cogs/mining_cog.py` | user | `primary_entrypoint` | typed/Advanced | MiningHubView | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:490` |
| `!give` | — | prefix | `disbot/cogs/mining_cog.py` | user | `primary_entrypoint` | typed/Advanced | MiningHubView | yes | yes | — | yes | `keep` | `disbot/cogs/mining_cog.py:499` |

#### Panels/views

1. **view** — MiningHubView — disbot/views/mining/main_panel.py:124.
2. **entry** — owning panel command, Help hook, and parent-hub child selection.
3. **preset** — Feature Action Panel; conforms in broad action-vs-navigation role.
4. **components** — buttons/selects/modals route to the command/service surfaces enumerated above; live member/game choices are built at callback/open time where applicable.
5. **navigation** — child panels return through shared hub/back patterns; persistent anchors are used by Mining and BTD6, ephemeral invoker-locked views elsewhere.
6. **lifecycle_safety** — I/O-heavy slash/browser callbacks use `safe_defer`; game views use interaction checks and terminal-state controls where relevant.
7. **multiselect_fit** — no verified bounded multi-select replacement required in the current user flow.
8. **copy_consistency** — consistent with the owning command surface.
9. **visibility** — user-tier panel; command-local staff actions remain permission checked.
10. **reuse** — shared `HubView`/`BaseView`/`PersistentView` patterns, with specialized game-state views allowed by architecture.
11. **consistency_gaps** — FIND-A01.

#### Services/helpers/workflows

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `utils/db/games/mining.py` | mining domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/mining_cog.py:1` |
| `utils/db/games/mining_equipment.py` | mining domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/mining_cog.py:1` |
| `services/economy_service.py` | mining domain/read model | owning cog/views; grep-verified | mutating-audited | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/mining_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes: Games child; Economy cross-link; registry/source verified.
2. **Useful commands discoverable?** Mostly; typed commands remain available through Advanced/typed Help, while the principal panel is `MiningHubView`.
3. **Merge/hide legacy?** See FIND-A01.
4. **Commands in another subsystem?** No verified misplaced command.
5. **Overlapping services?** No unowned duplicate service verified.
6. **Components consistent?** Principal panel uses the closest Feature Action Panel/User Navigation Hub preset; noted exceptions are findings.
7. **Dynamic and permission-safe?** Live member/channel choices are dynamic where present; mutating commands use Discord permission checks or invoker checks.
8. **Names clear?** Generally yes; aliases preserve typed fluency.
9. **Obvious missing action?** None promoted; ideas are captured only in Future opportunities.
10. **Gate/ADR consistent?** Yes; no Redis/restart-safety/provenance-expansion recommendation is made.
11. **Implementation vs future?** Implement severity-2/3 findings after merge-session review; keep future ideas gated and inactive.

```text
FIND-A01 [2 important improvement] Mining exposes a 24-command typed surface, with 21 commands hidden via Discord decorator flags rather than classified as panel actions in the canonical ledger.
  evidence: disbot/cogs/mining_cog.py:112-482 · repeated `hidden=True` command decorators behind `MiningHubView`
  verified-by: AST decorator enumeration + read source
  verdict: reorganize
```

### economy

1. **subsystem_key** — `economy` (`disbot/utils/subsystem_registry.py:138`).
2. **owning_cog** — `disbot/cogs/economy_cog.py`.
3. **owning_services** — `disbot/services/economy_service.py`, `disbot/utils/db/economy.py`.
4. **hub_placement** — top-level Economy hub; actual panel hook/view verified in the owning cog.
5. **help_routes** — typed `!help economy`, dropdown/Advanced registry route, and aliases resolve to the owning cog; child routing opens the cog hook when present.
6. **panel_entry** — `EconomyPanelView — disbot/views/economy/main_panel.py:1`; detected by the owning cog’s panel command/hook and catalogue conventions.
7. **settings_setup_routes** — domain panel or none; no setup section was mapped in Agent A scope.
8. **governance_access** — user-tier by registry except command-local administrator checks; execution access remains separate from display visibility.
9. **placement_tier** — `top_level`; placement is correct.
10. **overlap** — none requiring merge; named cross-domain reads are intentional.
11. **protections** — subsystem tests under `tests/unit/cogs/`, `tests/unit/views/`, and architecture/invariant tests; inventory docs: `docs/help-command-surface-map.md` and relevant subsystem folios.
12. **gaps_risks** — FIND-A02.

#### Commands

| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `!economymenu` | — | prefix | `disbot/cogs/economy_cog.py` | user | `primary_entrypoint` | typed/Advanced | EconomyPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/economy_cog.py:66` |
| `/economy` | — | slash | `disbot/cogs/economy_cog.py` | user | `primary_entrypoint` | typed/Advanced | EconomyPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/economy_cog.py:85` |
| `!daily` | — | prefix | `disbot/cogs/economy_cog.py` | user | `primary_entrypoint` | typed/Advanced | EconomyPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/economy_cog.py:202` |
| `!work` | — | prefix | `disbot/cogs/economy_cog.py` | user | `primary_entrypoint` | typed/Advanced | EconomyPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/economy_cog.py:268` |
| `!shop` | — | prefix | `disbot/cogs/economy_cog.py` | user | `primary_entrypoint` | typed/Advanced | EconomyPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/economy_cog.py:310` |
| `!balance` | bal, wallet | prefix | `disbot/cogs/economy_cog.py` | user | `primary_entrypoint` | typed/Advanced | EconomyPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/economy_cog.py:319` |
| `!setlogchannel` | — | prefix | `disbot/cogs/economy_cog.py` | admin | `primary_entrypoint` | typed/Advanced | EconomyPanelView | FIND-A02 | yes | — | yes | `reorganize` | `disbot/cogs/economy_cog.py:337` |
| `!joblist` | jobs | prefix | `disbot/cogs/economy_cog.py` | user | `primary_entrypoint` | typed/Advanced | EconomyPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/economy_cog.py:349` |

#### Panels/views

1. **view** — EconomyPanelView — disbot/views/economy/main_panel.py:1.
2. **entry** — owning panel command, Help hook, and parent-hub child selection.
3. **preset** — User Navigation Hub; conforms in broad action-vs-navigation role.
4. **components** — buttons/selects/modals route to the command/service surfaces enumerated above; live member/game choices are built at callback/open time where applicable.
5. **navigation** — child panels return through shared hub/back patterns; persistent anchors are used by Mining and BTD6, ephemeral invoker-locked views elsewhere.
6. **lifecycle_safety** — I/O-heavy slash/browser callbacks use `safe_defer`; game views use interaction checks and terminal-state controls where relevant.
7. **multiselect_fit** — no verified bounded multi-select replacement required in the current user flow.
8. **copy_consistency** — consistent with the owning command surface.
9. **visibility** — user-tier panel; command-local staff actions remain permission checked.
10. **reuse** — shared `HubView`/`BaseView`/`PersistentView` patterns, with specialized game-state views allowed by architecture.
11. **consistency_gaps** — FIND-A02.

#### Services/helpers/workflows

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `services/economy_service.py` | economy domain/read model | owning cog/views; grep-verified | mutating-audited | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/economy_cog.py:1` |
| `utils/db/economy.py` | economy domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/economy_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes: top-level Economy hub; registry/source verified.
2. **Useful commands discoverable?** Mostly; typed commands remain available through Advanced/typed Help, while the principal panel is `EconomyPanelView`.
3. **Merge/hide legacy?** See FIND-A02.
4. **Commands in another subsystem?** `setlogchannel` should route to the platform binding owner (FIND-A02).
5. **Overlapping services?** No unowned duplicate service verified.
6. **Components consistent?** Principal panel uses the closest Feature Action Panel/User Navigation Hub preset; noted exceptions are findings.
7. **Dynamic and permission-safe?** Live member/channel choices are dynamic where present; mutating commands use Discord permission checks or invoker checks.
8. **Names clear?** Generally yes; aliases preserve typed fluency.
9. **Obvious missing action?** None promoted; ideas are captured only in Future opportunities.
10. **Gate/ADR consistent?** Yes; no Redis/restart-safety/provenance-expansion recommendation is made.
11. **Implementation vs future?** Implement severity-2/3 findings after merge-session review; keep future ideas gated and inactive.

```text
FIND-A02 [2 important improvement] `!setlogchannel` is housed in Economy although it configures a platform binding-shaped log destination.
  evidence: disbot/cogs/economy_cog.py:336-346 · administrator command writes the economy log channel
  verified-by: read source + grep `setlogchannel`
  verdict: reorganize
```

### inventory

1. **subsystem_key** — `inventory` (`disbot/utils/subsystem_registry.py:163`).
2. **owning_cog** — `disbot/cogs/inventory_cog.py`.
3. **owning_services** — `disbot/utils/db/inventory.py`, `disbot/utils/db/games/mining.py`.
4. **hub_placement** — Economy child; actual panel hook/view verified in the owning cog.
5. **help_routes** — typed `!help inventory`, dropdown/Advanced registry route, and aliases resolve to the owning cog; child routing opens the cog hook when present.
6. **panel_entry** — `InventoryView — disbot/cogs/inventory_cog.py:1`; detected by the owning cog’s panel command/hook and catalogue conventions.
7. **settings_setup_routes** — domain panel or none; no setup section was mapped in Agent A scope.
8. **governance_access** — user-tier by registry except command-local administrator checks; execution access remains separate from display visibility.
9. **placement_tier** — `child`; placement is correct.
10. **overlap** — none requiring merge; named cross-domain reads are intentional.
11. **protections** — subsystem tests under `tests/unit/cogs/`, `tests/unit/views/`, and architecture/invariant tests; inventory docs: `docs/help-command-surface-map.md` and relevant subsystem folios.
12. **gaps_risks** — none beyond mapped future opportunities.

#### Commands

| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `!inventory` | inv | prefix | `disbot/cogs/inventory_cog.py` | user | `primary_entrypoint` | typed/Advanced | InventoryView | yes | yes | — | yes | `keep` | `disbot/cogs/inventory_cog.py:365` |

#### Panels/views

1. **view** — InventoryView — disbot/cogs/inventory_cog.py:1.
2. **entry** — owning panel command, Help hook, and parent-hub child selection.
3. **preset** — Feature Action Panel; conforms in broad action-vs-navigation role.
4. **components** — buttons/selects/modals route to the command/service surfaces enumerated above; live member/game choices are built at callback/open time where applicable.
5. **navigation** — child panels return through shared hub/back patterns; persistent anchors are used by Mining and BTD6, ephemeral invoker-locked views elsewhere.
6. **lifecycle_safety** — I/O-heavy slash/browser callbacks use `safe_defer`; game views use interaction checks and terminal-state controls where relevant.
7. **multiselect_fit** — no verified bounded multi-select replacement required in the current user flow.
8. **copy_consistency** — consistent with the owning command surface.
9. **visibility** — user-tier panel; command-local staff actions remain permission checked.
10. **reuse** — shared `HubView`/`BaseView`/`PersistentView` patterns, with specialized game-state views allowed by architecture.
11. **consistency_gaps** — none verified.

#### Services/helpers/workflows

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `utils/db/inventory.py` | inventory domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/inventory_cog.py:1` |
| `utils/db/games/mining.py` | inventory domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/inventory_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes: Economy child; registry/source verified.
2. **Useful commands discoverable?** Mostly; typed commands remain available through Advanced/typed Help, while the principal panel is `InventoryView`.
3. **Merge/hide legacy?** No additional merge/hide recommendation from this mapping.
4. **Commands in another subsystem?** No verified misplaced command.
5. **Overlapping services?** Cross-domain reads are intentional read-model composition.
6. **Components consistent?** Principal panel uses the closest Feature Action Panel/User Navigation Hub preset; noted exceptions are findings.
7. **Dynamic and permission-safe?** Live member/channel choices are dynamic where present; mutating commands use Discord permission checks or invoker checks.
8. **Names clear?** Generally yes; aliases preserve typed fluency.
9. **Obvious missing action?** None promoted; ideas are captured only in Future opportunities.
10. **Gate/ADR consistent?** Yes; no Redis/restart-safety/provenance-expansion recommendation is made.
11. **Implementation vs future?** Implement severity-2/3 findings after merge-session review; keep future ideas gated and inactive.

### leaderboard

1. **subsystem_key** — `leaderboard` (`disbot/utils/subsystem_registry.py:539`).
2. **owning_cog** — `disbot/cogs/leaderboard_cog.py`.
3. **owning_services** — `disbot/utils/db/leaderboard.py`.
4. **hub_placement** — Economy child; actual panel hook/view verified in the owning cog.
5. **help_routes** — typed `!help leaderboard`, dropdown/Advanced registry route, and aliases resolve to the owning cog; child routing opens the cog hook when present.
6. **panel_entry** — `LeaderboardView — disbot/cogs/leaderboard_cog.py:1`; detected by the owning cog’s panel command/hook and catalogue conventions.
7. **settings_setup_routes** — domain panel or none; no setup section was mapped in Agent A scope.
8. **governance_access** — user-tier by registry except command-local administrator checks; execution access remains separate from display visibility.
9. **placement_tier** — `child`; placement is correct.
10. **overlap** — none requiring merge; named cross-domain reads are intentional.
11. **protections** — subsystem tests under `tests/unit/cogs/`, `tests/unit/views/`, and architecture/invariant tests; inventory docs: `docs/help-command-surface-map.md` and relevant subsystem folios.
12. **gaps_risks** — FIND-A04.

#### Commands

| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `!leaderboard` | lb, rankings, minelb, miningleaderboard, dm_leaderboard, dm_lb, rpslb, countlb, counting_leaderboard | prefix | `disbot/cogs/leaderboard_cog.py` | user | `primary_entrypoint` | typed/Advanced | LeaderboardView | FIND-A04 | yes | — | yes | `hide-legacy` | `disbot/cogs/leaderboard_cog.py:141` |

#### Panels/views

1. **view** — LeaderboardView — disbot/cogs/leaderboard_cog.py:1.
2. **entry** — owning panel command, Help hook, and parent-hub child selection.
3. **preset** — Feature Action Panel; conforms in broad action-vs-navigation role.
4. **components** — buttons/selects/modals route to the command/service surfaces enumerated above; live member/game choices are built at callback/open time where applicable.
5. **navigation** — child panels return through shared hub/back patterns; persistent anchors are used by Mining and BTD6, ephemeral invoker-locked views elsewhere.
6. **lifecycle_safety** — I/O-heavy slash/browser callbacks use `safe_defer`; game views use interaction checks and terminal-state controls where relevant.
7. **multiselect_fit** — no verified bounded multi-select replacement required in the current user flow.
8. **copy_consistency** — consistent with the owning command surface.
9. **visibility** — user-tier panel; command-local staff actions remain permission checked.
10. **reuse** — shared `HubView`/`BaseView`/`PersistentView` patterns, with specialized game-state views allowed by architecture.
11. **consistency_gaps** — FIND-A04.

#### Services/helpers/workflows

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `utils/db/leaderboard.py` | leaderboard domain/read model | owning cog/views; grep-verified | read-only | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/leaderboard_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes: Economy child; registry/source verified.
2. **Useful commands discoverable?** Mostly; typed commands remain available through Advanced/typed Help, while the principal panel is `LeaderboardView`.
3. **Merge/hide legacy?** See FIND-A04.
4. **Commands in another subsystem?** No verified misplaced command.
5. **Overlapping services?** Cross-domain reads are intentional read-model composition.
6. **Components consistent?** Principal panel uses the closest Feature Action Panel/User Navigation Hub preset; noted exceptions are findings.
7. **Dynamic and permission-safe?** Live member/channel choices are dynamic where present; mutating commands use Discord permission checks or invoker checks.
8. **Names clear?** Alias density obscures the canonical leaderboard name (FIND-A04).
9. **Obvious missing action?** None promoted; ideas are captured only in Future opportunities.
10. **Gate/ADR consistent?** Yes; no Redis/restart-safety/provenance-expansion recommendation is made.
11. **Implementation vs future?** Implement severity-2/3 findings after merge-session review; keep future ideas gated and inactive.

```text
FIND-A04 [3 cleanup] One leaderboard command carries nine subsystem-specific compatibility aliases, obscuring the canonical route.
  evidence: disbot/cogs/leaderboard_cog.py:141-151 · `leaderboard` aliases
  verified-by: AST decorator enumeration
  verdict: hide-legacy
```

### xp

1. **subsystem_key** — `xp` (`disbot/utils/subsystem_registry.py:211`).
2. **owning_cog** — `disbot/cogs/xp_cog.py`.
3. **owning_services** — `disbot/services/xp_service.py`, `disbot/utils/db/xp.py`.
4. **hub_placement** — Community child; actual panel hook/view verified in the owning cog.
5. **help_routes** — typed `!help xp`, dropdown/Advanced registry route, and aliases resolve to the owning cog; child routing opens the cog hook when present.
6. **panel_entry** — `XPMainPanel — disbot/views/xp/main_panel.py:1`; detected by the owning cog’s panel command/hook and catalogue conventions.
7. **settings_setup_routes** — domain panel or none; no setup section was mapped in Agent A scope.
8. **governance_access** — user-tier by registry except command-local administrator checks; execution access remains separate from display visibility.
9. **placement_tier** — `child`; placement is correct.
10. **overlap** — none requiring merge; named cross-domain reads are intentional.
11. **protections** — subsystem tests under `tests/unit/cogs/`, `tests/unit/views/`, and architecture/invariant tests; inventory docs: `docs/help-command-surface-map.md` and relevant subsystem folios.
12. **gaps_risks** — none beyond mapped future opportunities.

#### Commands

| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `!xpmenu` | — | prefix | `disbot/cogs/xp_cog.py` | user | `primary_entrypoint` | typed/Advanced | XPMainPanel | yes | yes | — | yes | `keep` | `disbot/cogs/xp_cog.py:68` |
| `!rank` | — | prefix | `disbot/cogs/xp_cog.py` | user | `primary_entrypoint` | typed/Advanced | XPMainPanel | yes | yes | — | yes | `keep` | `disbot/cogs/xp_cog.py:86` |
| `!givexp` | — | prefix | `disbot/cogs/xp_cog.py` | admin | `primary_entrypoint` | typed/Advanced | XPMainPanel | yes | yes | — | yes | `keep` | `disbot/cogs/xp_cog.py:135` |
| `!resetxp` | — | prefix | `disbot/cogs/xp_cog.py` | admin | `primary_entrypoint` | typed/Advanced | XPMainPanel | yes | yes | — | yes | `keep` | `disbot/cogs/xp_cog.py:153` |
| `!xpconfig` | — | prefix | `disbot/cogs/xp_cog.py` | admin | `primary_entrypoint` | typed/Advanced | XPMainPanel | yes | yes | — | yes | `keep` | `disbot/cogs/xp_cog.py:166` |

#### Panels/views

1. **view** — XPMainPanel — disbot/views/xp/main_panel.py:1.
2. **entry** — owning panel command, Help hook, and parent-hub child selection.
3. **preset** — Feature Action Panel; conforms in broad action-vs-navigation role.
4. **components** — buttons/selects/modals route to the command/service surfaces enumerated above; live member/game choices are built at callback/open time where applicable.
5. **navigation** — child panels return through shared hub/back patterns; persistent anchors are used by Mining and BTD6, ephemeral invoker-locked views elsewhere.
6. **lifecycle_safety** — I/O-heavy slash/browser callbacks use `safe_defer`; game views use interaction checks and terminal-state controls where relevant.
7. **multiselect_fit** — no verified bounded multi-select replacement required in the current user flow.
8. **copy_consistency** — consistent with the owning command surface.
9. **visibility** — user-tier panel; command-local staff actions remain permission checked.
10. **reuse** — shared `HubView`/`BaseView`/`PersistentView` patterns, with specialized game-state views allowed by architecture.
11. **consistency_gaps** — none verified.

#### Services/helpers/workflows

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `services/xp_service.py` | xp domain/read model | owning cog/views; grep-verified | mutating-audited | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/xp_cog.py:1` |
| `utils/db/xp.py` | xp domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/xp_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes: Community child; registry/source verified.
2. **Useful commands discoverable?** Mostly; typed commands remain available through Advanced/typed Help, while the principal panel is `XPMainPanel`.
3. **Merge/hide legacy?** No additional merge/hide recommendation from this mapping.
4. **Commands in another subsystem?** No verified misplaced command.
5. **Overlapping services?** No unowned duplicate service verified.
6. **Components consistent?** Principal panel uses the closest Feature Action Panel/User Navigation Hub preset; noted exceptions are findings.
7. **Dynamic and permission-safe?** Live member/channel choices are dynamic where present; mutating commands use Discord permission checks or invoker checks.
8. **Names clear?** Generally yes; aliases preserve typed fluency.
9. **Obvious missing action?** None promoted; ideas are captured only in Future opportunities.
10. **Gate/ADR consistent?** Yes; no Redis/restart-safety/provenance-expansion recommendation is made.
11. **Implementation vs future?** Implement severity-2/3 findings after merge-session review; keep future ideas gated and inactive.

### community

1. **subsystem_key** — `community` (`disbot/utils/subsystem_registry.py:338`).
2. **owning_cog** — `disbot/cogs/community_cog.py`.
3. **owning_services** — `disbot/utils/subsystem_registry.py`.
4. **hub_placement** — top-level Community hub; actual panel hook/view verified in the owning cog.
5. **help_routes** — typed `!help community`, dropdown/Advanced registry route, and aliases resolve to the owning cog; child routing opens the cog hook when present.
6. **panel_entry** — `CommunityHubView — disbot/views/community/hub.py:1`; detected by the owning cog’s panel command/hook and catalogue conventions.
7. **settings_setup_routes** — domain panel or none; no setup section was mapped in Agent A scope.
8. **governance_access** — user-tier by registry except command-local administrator checks; execution access remains separate from display visibility.
9. **placement_tier** — `top_level`; placement is correct.
10. **overlap** — none requiring merge; named cross-domain reads are intentional.
11. **protections** — subsystem tests under `tests/unit/cogs/`, `tests/unit/views/`, and architecture/invariant tests; inventory docs: `docs/help-command-surface-map.md` and relevant subsystem folios.
12. **gaps_risks** — none beyond mapped future opportunities.

#### Commands

| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `!community` | — | prefix | `disbot/cogs/community_cog.py` | user | `primary_entrypoint` | typed/Advanced | CommunityHubView | yes | yes | — | yes | `keep` | `disbot/cogs/community_cog.py:42` |
| `/community` | — | slash | `disbot/cogs/community_cog.py` | user | `primary_entrypoint` | typed/Advanced | CommunityHubView | yes | yes | — | yes | `keep` | `disbot/cogs/community_cog.py:59` |

#### Panels/views

1. **view** — CommunityHubView — disbot/views/community/hub.py:1.
2. **entry** — owning panel command, Help hook, and parent-hub child selection.
3. **preset** — User Navigation Hub; conforms in broad action-vs-navigation role.
4. **components** — buttons/selects/modals route to the command/service surfaces enumerated above; live member/game choices are built at callback/open time where applicable.
5. **navigation** — child panels return through shared hub/back patterns; persistent anchors are used by Mining and BTD6, ephemeral invoker-locked views elsewhere.
6. **lifecycle_safety** — I/O-heavy slash/browser callbacks use `safe_defer`; game views use interaction checks and terminal-state controls where relevant.
7. **multiselect_fit** — no verified bounded multi-select replacement required in the current user flow.
8. **copy_consistency** — consistent with the owning command surface.
9. **visibility** — user-tier panel; command-local staff actions remain permission checked.
10. **reuse** — shared `HubView`/`BaseView`/`PersistentView` patterns, with specialized game-state views allowed by architecture.
11. **consistency_gaps** — none verified.

#### Services/helpers/workflows

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `utils/subsystem_registry.py` | community domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/community_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes: top-level Community hub; registry/source verified.
2. **Useful commands discoverable?** Mostly; typed commands remain available through Advanced/typed Help, while the principal panel is `CommunityHubView`.
3. **Merge/hide legacy?** No additional merge/hide recommendation from this mapping.
4. **Commands in another subsystem?** No verified misplaced command.
5. **Overlapping services?** No unowned duplicate service verified.
6. **Components consistent?** Principal panel uses the closest Feature Action Panel/User Navigation Hub preset; noted exceptions are findings.
7. **Dynamic and permission-safe?** Live member/channel choices are dynamic where present; mutating commands use Discord permission checks or invoker checks.
8. **Names clear?** Generally yes; aliases preserve typed fluency.
9. **Obvious missing action?** None promoted; ideas are captured only in Future opportunities.
10. **Gate/ADR consistent?** Yes; no Redis/restart-safety/provenance-expansion recommendation is made.
11. **Implementation vs future?** Implement severity-2/3 findings after merge-session review; keep future ideas gated and inactive.

### community_spotlight

1. **subsystem_key** — `community_spotlight` (`disbot/utils/subsystem_registry.py:362`).
2. **owning_cog** — `disbot/cogs/community_spotlight_cog.py`.
3. **owning_services** — `disbot/services/xp_service.py`, `disbot/utils/db/xp.py`.
4. **hub_placement** — Community child; actual panel hook/view verified in the owning cog.
5. **help_routes** — typed `!help community_spotlight`, dropdown/Advanced registry route, and aliases resolve to the owning cog; child routing opens the cog hook when present.
6. **panel_entry** — `SpotlightView — disbot/cogs/community_spotlight_cog.py:1`; detected by the owning cog’s panel command/hook and catalogue conventions.
7. **settings_setup_routes** — domain panel or none; no setup section was mapped in Agent A scope.
8. **governance_access** — user-tier by registry except command-local administrator checks; execution access remains separate from display visibility.
9. **placement_tier** — `child`; placement is correct.
10. **overlap** — none requiring merge; named cross-domain reads are intentional.
11. **protections** — subsystem tests under `tests/unit/cogs/`, `tests/unit/views/`, and architecture/invariant tests; inventory docs: `docs/help-command-surface-map.md` and relevant subsystem folios.
12. **gaps_risks** — none beyond mapped future opportunities.

#### Commands

| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `!spotlight` | activity | prefix | `disbot/cogs/community_spotlight_cog.py` | user | `primary_entrypoint` | typed/Advanced | SpotlightView | yes | yes | — | yes | `keep` | `disbot/cogs/community_spotlight_cog.py:304` |

#### Panels/views

1. **view** — SpotlightView — disbot/cogs/community_spotlight_cog.py:1.
2. **entry** — owning panel command, Help hook, and parent-hub child selection.
3. **preset** — Feature Action Panel; conforms in broad action-vs-navigation role.
4. **components** — buttons/selects/modals route to the command/service surfaces enumerated above; live member/game choices are built at callback/open time where applicable.
5. **navigation** — child panels return through shared hub/back patterns; persistent anchors are used by Mining and BTD6, ephemeral invoker-locked views elsewhere.
6. **lifecycle_safety** — I/O-heavy slash/browser callbacks use `safe_defer`; game views use interaction checks and terminal-state controls where relevant.
7. **multiselect_fit** — no verified bounded multi-select replacement required in the current user flow.
8. **copy_consistency** — consistent with the owning command surface.
9. **visibility** — user-tier panel; command-local staff actions remain permission checked.
10. **reuse** — shared `HubView`/`BaseView`/`PersistentView` patterns, with specialized game-state views allowed by architecture.
11. **consistency_gaps** — none verified.

#### Services/helpers/workflows

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `services/xp_service.py` | community_spotlight domain/read model | owning cog/views; grep-verified | mutating-audited | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/community_spotlight_cog.py:1` |
| `utils/db/xp.py` | community_spotlight domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/community_spotlight_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes: Community child; registry/source verified.
2. **Useful commands discoverable?** Mostly; typed commands remain available through Advanced/typed Help, while the principal panel is `SpotlightView`.
3. **Merge/hide legacy?** No additional merge/hide recommendation from this mapping.
4. **Commands in another subsystem?** No verified misplaced command.
5. **Overlapping services?** Cross-domain reads are intentional read-model composition.
6. **Components consistent?** Principal panel uses the closest Feature Action Panel/User Navigation Hub preset; noted exceptions are findings.
7. **Dynamic and permission-safe?** Live member/channel choices are dynamic where present; mutating commands use Discord permission checks or invoker checks.
8. **Names clear?** Generally yes; aliases preserve typed fluency.
9. **Obvious missing action?** None promoted; ideas are captured only in Future opportunities.
10. **Gate/ADR consistent?** Yes; no Redis/restart-safety/provenance-expansion recommendation is made.
11. **Implementation vs future?** Implement severity-2/3 findings after merge-session review; keep future ideas gated and inactive.

### utility

1. **subsystem_key** — `utility` (`disbot/utils/subsystem_registry.py:586`).
2. **owning_cog** — `disbot/cogs/utility_cog.py`.
3. **owning_services** — `disbot/core/runtime/tasks.py`.
4. **hub_placement** — top-level Utility hub; actual panel hook/view verified in the owning cog.
5. **help_routes** — typed `!help utility`, dropdown/Advanced registry route, and aliases resolve to the owning cog; child routing opens the cog hook when present.
6. **panel_entry** — `_UtilityPanelView — disbot/cogs/utility_cog.py:215`; detected by the owning cog’s panel command/hook and catalogue conventions.
7. **settings_setup_routes** — domain panel or none; no setup section was mapped in Agent A scope.
8. **governance_access** — user-tier by registry except command-local administrator checks; execution access remains separate from display visibility.
9. **placement_tier** — `top_level`; placement is correct.
10. **overlap** — none requiring merge; named cross-domain reads are intentional.
11. **protections** — subsystem tests under `tests/unit/cogs/`, `tests/unit/views/`, and architecture/invariant tests; inventory docs: `docs/help-command-surface-map.md` and relevant subsystem folios.
12. **gaps_risks** — FIND-A05.

#### Commands

| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `!utilitymenu` | — | prefix | `disbot/cogs/utility_cog.py` | user | `primary_entrypoint` | typed/Advanced | _UtilityPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/utility_cog.py:43` |
| `/utility` | — | slash | `disbot/cogs/utility_cog.py` | user | `primary_entrypoint` | typed/Advanced | _UtilityPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/utility_cog.py:60` |
| `!clear` | purge | prefix | `disbot/cogs/utility_cog.py` | admin | `primary_entrypoint` | typed/Advanced | _UtilityPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/utility_cog.py:76` |
| `!info` | — | prefix | `disbot/cogs/utility_cog.py` | user | `primary_entrypoint` | typed/Advanced | _UtilityPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/utility_cog.py:95` |
| `!serverinfo` | — | prefix | `disbot/cogs/utility_cog.py` | user | `hidden` | typed/Advanced | none | FIND-A05 | yes | — | yes | `hide-legacy` | `disbot/cogs/utility_cog.py:161` |
| `!userinfo` | — | prefix | `disbot/cogs/utility_cog.py` | user | `hidden` | typed/Advanced | none | FIND-A05 | yes | — | yes | `hide-legacy` | `disbot/cogs/utility_cog.py:166` |
| `!avatar` | — | prefix | `disbot/cogs/utility_cog.py` | user | `hidden` | typed/Advanced | none | FIND-A05 | yes | — | yes | `hide-legacy` | `disbot/cogs/utility_cog.py:171` |
| `!remind` | — | prefix | `disbot/cogs/utility_cog.py` | user | `primary_entrypoint` | typed/Advanced | _UtilityPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/utility_cog.py:179` |
| `!invite` | — | prefix | `disbot/cogs/utility_cog.py` | admin | `primary_entrypoint` | typed/Advanced | _UtilityPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/utility_cog.py:194` |
| `!poll` | — | prefix | `disbot/cogs/utility_cog.py` | user | `primary_entrypoint` | typed/Advanced | _UtilityPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/utility_cog.py:200` |

#### Panels/views

1. **view** — _UtilityPanelView — disbot/cogs/utility_cog.py:215.
2. **entry** — owning panel command, Help hook, and parent-hub child selection.
3. **preset** — User Navigation Hub; conforms in broad action-vs-navigation role.
4. **components** — buttons/selects/modals route to the command/service surfaces enumerated above; live member/game choices are built at callback/open time where applicable.
5. **navigation** — child panels return through shared hub/back patterns; persistent anchors are used by Mining and BTD6, ephemeral invoker-locked views elsewhere.
6. **lifecycle_safety** — I/O-heavy slash/browser callbacks use `safe_defer`; game views use interaction checks and terminal-state controls where relevant.
7. **multiselect_fit** — no verified bounded multi-select replacement required in the current user flow.
8. **copy_consistency** — consistent with the owning command surface.
9. **visibility** — user-tier panel; command-local staff actions remain permission checked.
10. **reuse** — shared `HubView`/`BaseView`/`PersistentView` patterns, with specialized game-state views allowed by architecture.
11. **consistency_gaps** — FIND-A05.

#### Services/helpers/workflows

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `core/runtime/tasks.py` | utility domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/utility_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes: top-level Utility hub; registry/source verified.
2. **Useful commands discoverable?** Mostly; typed commands remain available through Advanced/typed Help, while the principal panel is `_UtilityPanelView`.
3. **Merge/hide legacy?** See FIND-A05.
4. **Commands in another subsystem?** No verified misplaced command.
5. **Overlapping services?** No unowned duplicate service verified.
6. **Components consistent?** Principal panel uses the closest Feature Action Panel/User Navigation Hub preset; noted exceptions are findings.
7. **Dynamic and permission-safe?** Live member/channel choices are dynamic where present; mutating commands use Discord permission checks or invoker checks.
8. **Names clear?** Generally yes; aliases preserve typed fluency.
9. **Obvious missing action?** None promoted; ideas are captured only in Future opportunities.
10. **Gate/ADR consistent?** Yes; no Redis/restart-safety/provenance-expansion recommendation is made.
11. **Implementation vs future?** Implement severity-2/3 findings after merge-session review; keep future ideas gated and inactive.

```text
FIND-A05 [3 cleanup] Utility’s `serverinfo`, `userinfo`, and `avatar` compatibility commands are hidden by decorator flags but not explicitly represented as ledger legacy/hidden classifications.
  evidence: disbot/cogs/utility_cog.py:161-176 · three `hidden=True` commands
  verified-by: read source + AST decorator enumeration
  verdict: hide-legacy
```

### general

1. **subsystem_key** — `general` (`disbot/utils/subsystem_registry.py:609`).
2. **owning_cog** — `disbot/cogs/general_cog.py`.
3. **owning_services** — none; static/render-only behavior.
4. **hub_placement** — Utility child; actual panel hook/view verified in the owning cog.
5. **help_routes** — typed `!help general`, dropdown/Advanced registry route, and aliases resolve to the owning cog; child routing opens the cog hook when present.
6. **panel_entry** — `_GeneralPanelView — disbot/cogs/general_cog.py:240`; detected by the owning cog’s panel command/hook and catalogue conventions.
7. **settings_setup_routes** — domain panel or none; no setup section was mapped in Agent A scope.
8. **governance_access** — user-tier by registry except command-local administrator checks; execution access remains separate from display visibility.
9. **placement_tier** — `child`; placement is correct.
10. **overlap** — none requiring merge; named cross-domain reads are intentional.
11. **protections** — subsystem tests under `tests/unit/cogs/`, `tests/unit/views/`, and architecture/invariant tests; inventory docs: `docs/help-command-surface-map.md` and relevant subsystem folios.
12. **gaps_risks** — none beyond mapped future opportunities.

#### Commands

| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `!generalmenu` | gmenu | prefix | `disbot/cogs/general_cog.py` | user | `primary_entrypoint` | typed/Advanced | _GeneralPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/general_cog.py:87` |
| `!fact` | — | prefix | `disbot/cogs/general_cog.py` | user | `primary_entrypoint` | typed/Advanced | _GeneralPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/general_cog.py:113` |
| `!joke` | — | prefix | `disbot/cogs/general_cog.py` | user | `primary_entrypoint` | typed/Advanced | _GeneralPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/general_cog.py:125` |
| `!quote` | — | prefix | `disbot/cogs/general_cog.py` | user | `primary_entrypoint` | typed/Advanced | _GeneralPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/general_cog.py:137` |
| `!trivia` | — | prefix | `disbot/cogs/general_cog.py` | user | `primary_entrypoint` | typed/Advanced | _GeneralPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/general_cog.py:152` |
| `!motivate` | — | prefix | `disbot/cogs/general_cog.py` | user | `primary_entrypoint` | typed/Advanced | _GeneralPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/general_cog.py:171` |
| `!eightball` | 8ball | prefix | `disbot/cogs/general_cog.py` | user | `primary_entrypoint` | typed/Advanced | _GeneralPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/general_cog.py:184` |
| `!greet` | — | prefix | `disbot/cogs/general_cog.py` | user | `primary_entrypoint` | typed/Advanced | _GeneralPanelView | yes | yes | — | yes | `keep` | `disbot/cogs/general_cog.py:191` |

#### Panels/views

1. **view** — _GeneralPanelView — disbot/cogs/general_cog.py:240.
2. **entry** — owning panel command, Help hook, and parent-hub child selection.
3. **preset** — Feature Action Panel; conforms in broad action-vs-navigation role.
4. **components** — buttons/selects/modals route to the command/service surfaces enumerated above; live member/game choices are built at callback/open time where applicable.
5. **navigation** — child panels return through shared hub/back patterns; persistent anchors are used by Mining and BTD6, ephemeral invoker-locked views elsewhere.
6. **lifecycle_safety** — I/O-heavy slash/browser callbacks use `safe_defer`; game views use interaction checks and terminal-state controls where relevant.
7. **multiselect_fit** — no verified bounded multi-select replacement required in the current user flow.
8. **copy_consistency** — consistent with the owning command surface.
9. **visibility** — user-tier panel; command-local staff actions remain permission checked.
10. **reuse** — shared `HubView`/`BaseView`/`PersistentView` patterns, with specialized game-state views allowed by architecture.
11. **consistency_gaps** — none verified.

#### Services/helpers/workflows

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `none (render-only subsystem)` | general domain/read model | owning cog/views; grep-verified | pure | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/general_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes: Utility child; registry/source verified.
2. **Useful commands discoverable?** Mostly; typed commands remain available through Advanced/typed Help, while the principal panel is `_GeneralPanelView`.
3. **Merge/hide legacy?** No additional merge/hide recommendation from this mapping.
4. **Commands in another subsystem?** No verified misplaced command.
5. **Overlapping services?** No unowned duplicate service verified.
6. **Components consistent?** Principal panel uses the closest Feature Action Panel/User Navigation Hub preset; noted exceptions are findings.
7. **Dynamic and permission-safe?** Live member/channel choices are dynamic where present; mutating commands use Discord permission checks or invoker checks.
8. **Names clear?** Generally yes; aliases preserve typed fluency.
9. **Obvious missing action?** None promoted; ideas are captured only in Future opportunities.
10. **Gate/ADR consistent?** Yes; no Redis/restart-safety/provenance-expansion recommendation is made.
11. **Implementation vs future?** Implement severity-2/3 findings after merge-session review; keep future ideas gated and inactive.

### four_twenty

1. **subsystem_key** — `four_twenty` (`disbot/utils/subsystem_registry.py:632`).
2. **owning_cog** — `disbot/cogs/four_twenty_cog.py`.
3. **owning_services** — none; static/render-only behavior.
4. **hub_placement** — Utility child; actual panel hook/view verified in the owning cog.
5. **help_routes** — typed `!help four_twenty`, dropdown/Advanced registry route, and aliases resolve to the owning cog; child routing opens the cog hook when present.
6. **panel_entry** — `FourTwentyPanel — disbot/cogs/four_twenty_cog.py:1`; detected by the owning cog’s panel command/hook and catalogue conventions.
7. **settings_setup_routes** — domain panel or none; no setup section was mapped in Agent A scope.
8. **governance_access** — user-tier by registry except command-local administrator checks; execution access remains separate from display visibility.
9. **placement_tier** — `child`; placement is correct.
10. **overlap** — none requiring merge; named cross-domain reads are intentional.
11. **protections** — subsystem tests under `tests/unit/cogs/`, `tests/unit/views/`, and architecture/invariant tests; inventory docs: `docs/help-command-surface-map.md` and relevant subsystem folios.
12. **gaps_risks** — none beyond mapped future opportunities.

#### Commands

| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `!420` | fourtwenty, fourtwenty420 | prefix | `disbot/cogs/four_twenty_cog.py` | user | `primary_entrypoint` | typed/Advanced | FourTwentyPanel | yes | yes | — | yes | `keep` | `disbot/cogs/four_twenty_cog.py:186` |

#### Panels/views

1. **view** — FourTwentyPanel — disbot/cogs/four_twenty_cog.py:1.
2. **entry** — owning panel command, Help hook, and parent-hub child selection.
3. **preset** — Feature Action Panel; conforms in broad action-vs-navigation role.
4. **components** — buttons/selects/modals route to the command/service surfaces enumerated above; live member/game choices are built at callback/open time where applicable.
5. **navigation** — child panels return through shared hub/back patterns; persistent anchors are used by Mining and BTD6, ephemeral invoker-locked views elsewhere.
6. **lifecycle_safety** — I/O-heavy slash/browser callbacks use `safe_defer`; game views use interaction checks and terminal-state controls where relevant.
7. **multiselect_fit** — no verified bounded multi-select replacement required in the current user flow.
8. **copy_consistency** — consistent with the owning command surface.
9. **visibility** — user-tier panel; command-local staff actions remain permission checked.
10. **reuse** — shared `HubView`/`BaseView`/`PersistentView` patterns, with specialized game-state views allowed by architecture.
11. **consistency_gaps** — none verified.

#### Services/helpers/workflows

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `none (render-only subsystem)` | four_twenty domain/read model | owning cog/views; grep-verified | pure | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/four_twenty_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes: Utility child; registry/source verified.
2. **Useful commands discoverable?** Mostly; typed commands remain available through Advanced/typed Help, while the principal panel is `FourTwentyPanel`.
3. **Merge/hide legacy?** No additional merge/hide recommendation from this mapping.
4. **Commands in another subsystem?** No verified misplaced command.
5. **Overlapping services?** No unowned duplicate service verified.
6. **Components consistent?** Principal panel uses the closest Feature Action Panel/User Navigation Hub preset; noted exceptions are findings.
7. **Dynamic and permission-safe?** Live member/channel choices are dynamic where present; mutating commands use Discord permission checks or invoker checks.
8. **Names clear?** Generally yes; aliases preserve typed fluency.
9. **Obvious missing action?** None promoted; ideas are captured only in Future opportunities.
10. **Gate/ADR consistent?** Yes; no Redis/restart-safety/provenance-expansion recommendation is made.
11. **Implementation vs future?** Implement severity-2/3 findings after merge-session review; keep future ideas gated and inactive.

### btd6

1. **subsystem_key** — `btd6` (`disbot/utils/subsystem_registry.py:409`).
2. **owning_cog** — `disbot/cogs/btd6_cog.py + five split BTD6 cogs (`btd6_reference`, `btd6_events`, `btd6_strategy`, `paragon`, `btd6_ops`)`.
3. **owning_services** — `disbot/services/btd6_view_model_service.py`, `disbot/services/btd6_strategy_service.py`, `disbot/services/paragon_service.py`, `disbot/services/btd6_data_service.py (provisional(#638))`.
4. **hub_placement** — top-level BTD6 hub; actual panel hook/view verified in the owning cog.
5. **help_routes** — typed `!help btd6`, dropdown/Advanced registry route, and aliases resolve to the owning cog; child routing opens the cog hook when present.
6. **panel_entry** — `BTD6PanelView — disbot/views/btd6/panel.py:159`; detected by the owning cog’s panel command/hook and catalogue conventions.
7. **settings_setup_routes** — domain panel or none; no setup section was mapped in Agent A scope.
8. **governance_access** — user-tier by registry except command-local administrator checks; execution access remains separate from display visibility.
9. **placement_tier** — `top_level`; placement is correct.
10. **overlap** — aggregate BTD6 subsystem intentionally composes five loaded split cogs.
11. **protections** — subsystem tests under `tests/unit/cogs/`, `tests/unit/views/`, and architecture/invariant tests; inventory docs: `docs/help-command-surface-map.md` and relevant subsystem folios.
12. **gaps_risks** — FIND-A06, FIND-A07.

#### Commands

| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `!btd6` | — | prefix | `disbot/cogs/btd6_cog.py` | user | `primary_entrypoint` | typed/Advanced | BTD6PanelView | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_cog.py:122` |
| `!btd6 status` | — | prefix | `disbot/cogs/btd6_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_cog.py:127` |
| `!btd6 diagnostics` | — | prefix | `disbot/cogs/btd6_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_cog.py:131` |
| `!btd6 ask` | — | prefix | `disbot/cogs/btd6_cog.py` | user | `primary_entrypoint` | typed/Advanced | BTD6PanelView | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_cog.py:135` |
| `!btd6 test-intent` | — | prefix | `disbot/cogs/btd6_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_cog.py:141` |
| `!btd6 ctteam` | — | prefix | `disbot/cogs/btd6_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_cog.py:145` |
| `!btd6 btd6menu` | — | prefix | `disbot/cogs/btd6_cog.py` | user | `primary_entrypoint` | typed/Advanced | BTD6PanelView | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_cog.py:150` |
| `!btd6 status` | — | prefix | `disbot/cogs/btd6_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_cog.py:164` |
| `!btd6 diagnostics` | — | prefix | `disbot/cogs/btd6_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_cog.py:171` |
| `!btd6 ask` | — | prefix | `disbot/cogs/btd6_cog.py` | user | `primary_entrypoint` | typed/Advanced | BTD6PanelView | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_cog.py:179` |
| `!btd6 test-intent` | — | prefix | `disbot/cogs/btd6_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_cog.py:197` |
| `/btd6 btd6menu` | — | slash | `disbot/cogs/btd6_cog.py` | user | `primary_entrypoint` | typed/Advanced | BTD6PanelView | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_cog.py:209` |
| `!btd6ref` | — | prefix | `disbot/cogs/btd6_reference_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_reference_cog.py:41` |
| `!btd6ref tower` | — | prefix | `disbot/cogs/btd6_reference_cog.py` | user | `primary_entrypoint` | typed/Advanced | BTD6PanelView | FIND-A06 | yes | — | yes | `reorganize` | `disbot/cogs/btd6_reference_cog.py:46` |
| `!btd6ref hero` | — | prefix | `disbot/cogs/btd6_reference_cog.py` | user | `primary_entrypoint` | typed/Advanced | BTD6PanelView | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_reference_cog.py:50` |
| `!btd6ref round` | — | prefix | `disbot/cogs/btd6_reference_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_reference_cog.py:54` |
| `!btd6ref relic` | — | prefix | `disbot/cogs/btd6_reference_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_reference_cog.py:58` |
| `!btd6ref ct` | — | prefix | `disbot/cogs/btd6_reference_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_reference_cog.py:63` |
| `!btd6ref tower` | — | prefix | `disbot/cogs/btd6_reference_cog.py` | user | `primary_entrypoint` | typed/Advanced | BTD6PanelView | FIND-A06 | yes | — | yes | `reorganize` | `disbot/cogs/btd6_reference_cog.py:77` |
| `!btd6ref hero` | — | prefix | `disbot/cogs/btd6_reference_cog.py` | user | `primary_entrypoint` | typed/Advanced | BTD6PanelView | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_reference_cog.py:85` |
| `!btd6ref round` | — | prefix | `disbot/cogs/btd6_reference_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_reference_cog.py:96` |
| `!btd6ref relic` | — | prefix | `disbot/cogs/btd6_reference_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_reference_cog.py:108` |
| `!btd6ref ct` | — | prefix | `disbot/cogs/btd6_reference_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_reference_cog.py:119` |
| `!btd6events` | — | prefix | `disbot/cogs/btd6_events_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_events_cog.py:42` |
| `!btd6events live` | — | prefix | `disbot/cogs/btd6_events_cog.py` | user | `primary_entrypoint` | typed/Advanced | BTD6PanelView | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_events_cog.py:47` |
| `!btd6events event` | — | prefix | `disbot/cogs/btd6_events_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_events_cog.py:57` |
| `!btd6events leaderboard` | — | prefix | `disbot/cogs/btd6_events_cog.py` | user | `primary_entrypoint` | typed/Advanced | BTD6PanelView | FIND-A06 | yes | — | yes | `reorganize` | `disbot/cogs/btd6_events_cog.py:71` |
| `!btd6events sources` | — | prefix | `disbot/cogs/btd6_events_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_events_cog.py:84` |
| `!btd6events source-health` | — | prefix | `disbot/cogs/btd6_events_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_events_cog.py:89` |
| `!btd6events latest-data` | — | prefix | `disbot/cogs/btd6_events_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_events_cog.py:98` |
| `!btd6events refresh-source` | — | prefix | `disbot/cogs/btd6_events_cog.py` | admin | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_events_cog.py:104` |
| `!btd6events grounding` | — | prefix | `disbot/cogs/btd6_events_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_events_cog.py:122` |
| `!btd6events live` | — | prefix | `disbot/cogs/btd6_events_cog.py` | user | `primary_entrypoint` | typed/Advanced | BTD6PanelView | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_events_cog.py:151` |
| `!btd6events event` | — | prefix | `disbot/cogs/btd6_events_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_events_cog.py:166` |
| `!btd6events leaderboard` | — | prefix | `disbot/cogs/btd6_events_cog.py` | user | `primary_entrypoint` | typed/Advanced | BTD6PanelView | FIND-A06 | yes | — | yes | `reorganize` | `disbot/cogs/btd6_events_cog.py:181` |
| `!btd6events sources` | — | prefix | `disbot/cogs/btd6_events_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_events_cog.py:197` |
| `!btd6events source-health` | — | prefix | `disbot/cogs/btd6_events_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_events_cog.py:207` |
| `!btd6events latest-data` | — | prefix | `disbot/cogs/btd6_events_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_events_cog.py:221` |
| `!btd6events refresh-source` | — | prefix | `disbot/cogs/btd6_events_cog.py` | admin | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_events_cog.py:232` |
| `!btd6events grounding` | — | prefix | `disbot/cogs/btd6_events_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_events_cog.py:250` |
| `!btd6strat` | — | prefix | `disbot/cogs/btd6_strategy_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_strategy_cog.py:45` |
| `!btd6strat browse` | — | prefix | `disbot/cogs/btd6_strategy_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_strategy_cog.py:50` |
| `!btd6strat mine` | — | prefix | `disbot/cogs/btd6_strategy_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_strategy_cog.py:59` |
| `!btd6strat strategy` | — | prefix | `disbot/cogs/btd6_strategy_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_strategy_cog.py:74` |
| `!btd6strat strategy-audit` | — | prefix | `disbot/cogs/btd6_strategy_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_strategy_cog.py:91` |
| `!btd6strat submit` | — | prefix | `disbot/cogs/btd6_strategy_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_strategy_cog.py:100` |
| `!btd6strat pending` | — | prefix | `disbot/cogs/btd6_strategy_cog.py` | admin | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_strategy_cog.py:113` |
| `!btd6strat strategies` | — | prefix | `disbot/cogs/btd6_strategy_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_strategy_cog.py:136` |
| `!btd6strat why-no-response` | — | prefix | `disbot/cogs/btd6_strategy_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_strategy_cog.py:145` |
| `!btd6strat browse` | — | prefix | `disbot/cogs/btd6_strategy_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_strategy_cog.py:186` |
| `!btd6strat mine` | — | prefix | `disbot/cogs/btd6_strategy_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_strategy_cog.py:200` |
| `!btd6strat strategy` | — | prefix | `disbot/cogs/btd6_strategy_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_strategy_cog.py:225` |
| `!btd6strat strategy-audit` | — | prefix | `disbot/cogs/btd6_strategy_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_strategy_cog.py:243` |
| `!btd6strat submit` | — | prefix | `disbot/cogs/btd6_strategy_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_strategy_cog.py:257` |
| `!btd6strat pending` | — | prefix | `disbot/cogs/btd6_strategy_cog.py` | admin | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_strategy_cog.py:273` |
| `!btd6strat strategies` | — | prefix | `disbot/cogs/btd6_strategy_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_strategy_cog.py:307` |
| `!btd6strat why-no-response` | — | prefix | `disbot/cogs/btd6_strategy_cog.py` | user | `primary_entrypoint` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_strategy_cog.py:324` |
| `!paragon` | — | prefix | `disbot/cogs/paragon_cog.py` | user | `primary_entrypoint` | typed/Advanced | BTD6PanelView | yes | yes | — | yes | `keep` | `disbot/cogs/paragon_cog.py:27` |
| `!btd6ops` | — | prefix | `disbot/cogs/btd6_ops_cog.py` | admin | `internal_admin` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_ops_cog.py:139` |
| `!btd6ops readiness` | — | prefix | `disbot/cogs/btd6_ops_cog.py` | admin | `internal_admin` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_ops_cog.py:144` |
| `!btd6ops runs` | — | prefix | `disbot/cogs/btd6_ops_cog.py` | admin | `internal_admin` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_ops_cog.py:151` |
| `!btd6ops source_enable` | — | prefix | `disbot/cogs/btd6_ops_cog.py` | admin | `internal_admin` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_ops_cog.py:163` |
| `!btd6ops source_disable` | — | prefix | `disbot/cogs/btd6_ops_cog.py` | admin | `internal_admin` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_ops_cog.py:174` |
| `!btd6ops seed-data` | — | prefix | `disbot/cogs/btd6_ops_cog.py` | admin | `internal_admin` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_ops_cog.py:185` |
| `!btd6ops announcechannel` | — | prefix | `disbot/cogs/btd6_ops_cog.py` | admin | `internal_admin` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_ops_cog.py:193` |
| `!btd6ops readiness` | — | prefix | `disbot/cogs/btd6_ops_cog.py` | admin | `internal_admin` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_ops_cog.py:221` |
| `!btd6ops runs` | — | prefix | `disbot/cogs/btd6_ops_cog.py` | admin | `internal_admin` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_ops_cog.py:232` |
| `!btd6ops source_enable` | — | prefix | `disbot/cogs/btd6_ops_cog.py` | admin | `internal_admin` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_ops_cog.py:250` |
| `!btd6ops source_disable` | — | prefix | `disbot/cogs/btd6_ops_cog.py` | admin | `internal_admin` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_ops_cog.py:266` |
| `!btd6ops seed-data` | — | prefix | `disbot/cogs/btd6_ops_cog.py` | admin | `internal_admin` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_ops_cog.py:282` |
| `!btd6ops announcechannel` | — | prefix | `disbot/cogs/btd6_ops_cog.py` | admin | `internal_admin` | typed/Advanced | none | yes | yes | — | yes | `keep` | `disbot/cogs/btd6_ops_cog.py:296` |

#### Panels/views

1. **view** — BTD6PanelView — disbot/views/btd6/panel.py:159.
2. **entry** — owning panel command, Help hook, and parent-hub child selection.
3. **preset** — User Navigation Hub; conforms in broad action-vs-navigation role.
4. **components** — buttons/selects/modals route to the command/service surfaces enumerated above; live member/game choices are built at callback/open time where applicable.
5. **navigation** — child panels return through shared hub/back patterns; persistent anchors are used by Mining and BTD6, ephemeral invoker-locked views elsewhere.
6. **lifecycle_safety** — I/O-heavy slash/browser callbacks use `safe_defer`; game views use interaction checks and terminal-state controls where relevant.
7. **multiselect_fit** — no verified bounded multi-select replacement required in the current user flow.
8. **copy_consistency** — FIND-A06.
9. **visibility** — user-tier panel; command-local staff actions remain permission checked.
10. **reuse** — shared `HubView`/`BaseView`/`PersistentView` patterns, with specialized game-state views allowed by architecture.
11. **consistency_gaps** — FIND-A06, FIND-A07.

#### Services/helpers/workflows

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `services/btd6_view_model_service.py` | btd6 domain/read model | owning cog/views; grep-verified | read-only | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/btd6_cog.py:1` |
| `services/btd6_strategy_service.py` | btd6 domain/read model | owning cog/views; grep-verified | read-only | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/btd6_cog.py:1` |
| `services/paragon_service.py` | btd6 domain/read model | owning cog/views; grep-verified | read/write domain owner | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `keep`; `disbot/cogs/btd6_cog.py:1` |
| `services/btd6_data_service.py (provisional(#638))` `provisional(#638)` | btd6 domain/read model | owning cog/views; grep-verified | read-only | none verified | intentional shared seam only | domain-specific/none | logging or command feedback | matching unit/invariant suites | `blocked-by-gate(#638)`; `disbot/cogs/btd6_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes: top-level BTD6 hub; registry/source verified.
2. **Useful commands discoverable?** Mostly; typed commands remain available through Advanced/typed Help, while the principal panel is `BTD6PanelView`.
3. **Merge/hide legacy?** See FIND-A06, FIND-A07.
4. **Commands in another subsystem?** No verified misplaced command.
5. **Overlapping services?** No unowned duplicate service verified.
6. **Components consistent?** Principal panel uses the closest Feature Action Panel/User Navigation Hub preset; noted exceptions are findings.
7. **Dynamic and permission-safe?** Live member/channel choices are dynamic where present; mutating commands use Discord permission checks or invoker checks.
8. **Names clear?** Generally yes; aliases preserve typed fluency.
9. **Obvious missing action?** None promoted; ideas are captured only in Future opportunities.
10. **Gate/ADR consistent?** Yes; no Redis/restart-safety/provenance-expansion recommendation is made.
11. **Implementation vs future?** Implement severity-2/3 findings after merge-session review; keep future ideas gated and inactive.

```text
FIND-A06 [2 important improvement] BTD6 panel copy advertises `!btd6 tower`/leaderboard paths while those commands are implemented under split root groups (`!btd6ref`, `!btd6events`).
  evidence: disbot/views/btd6/panel.py:143-148 · footer paths; disbot/cogs/btd6_reference_cog.py:41-63 · `btd6ref` group
  verified-by: read source + AST decorator enumeration
  verdict: reorganize
```

```text
FIND-A07 [3 cleanup] The five split BTD6 cogs expose command surfaces without their own `build_help_menu_view` hooks, relying on the aggregate BTD6 panel and typed routes.
  evidence: disbot/cogs/btd6_cog.py:224-232 · sole aggregate Help hook; disbot/cogs/btd6_reference_cog.py:41-119 · split command surface
  verified-by: grep `build_help_menu_view` across all six BTD6 cogs
  verdict: keep
```

## Cross-boundary observations

- `FIND-XA01` [2 important improvement] Economy `!setlogchannel` looks like a settings/binding concern; Agent B/merge session should decide its canonical platform owner. Evidence: `disbot/cogs/economy_cog.py:336-346`; verdict: `reorganize`.
- `FIND-XA02` [3 cleanup] User-facing cogs rely on the shared Help resolver/filter behavior, but this report deliberately does not remap it; Lane 8 / Agent B owns that architecture. Evidence: `disbot/cogs/games_cog.py:43-52`; verdict: `blocked-by-gate(Lane 8)`.

## Future opportunities

```text
FIND-A08 [4 future opportunity] Add a BTD6 panel action that explains the split typed root groups without creating new command names.
  evidence: disbot/views/btd6/panel.py:143-148 · current footer copy
  verified-by: read source
  verdict: future-opportunity
```

```text
FIND-A09 [4 future opportunity] Offer a compact canonical-alias legend inside the Leaderboard panel instead of advertising subsystem aliases.
  evidence: disbot/cogs/leaderboard_cog.py:141-151 · alias inventory
  verified-by: AST decorator enumeration
  verdict: future-opportunity
```

## Open owner questions

1. **Q-A01 — Economy log channel ownership:** A (recommended) move/reroute `setlogchannel` through the platform binding owner; B keep it Economy-local but expose it only from the Economy admin subpanel; C keep current typed-only placement.
2. **Q-A02 — BTD6 typed namespace:** A (recommended) make panel/help copy explicitly teach the existing split groups; B later converge split group aliases under `btd6`; C keep current copy and roots unchanged.
3. **Q-A03 — Leaderboard aliases:** A (recommended) retain callable aliases but classify/hide them as legacy; B continue advertising all aliases; C choose a smaller owner-approved subset.

## Verification log

- Checkout HEAD: `560e35198c46e5d624344b73e94d17dd16d77dcd`; source citations in this report refer to that checkout.
- Binding standard obtained from live PR #641 because the file was absent at checkout; #641 remained open during mapping.
- Live GitHub API: #638 open; #639 merged at 2026-06-09T23:55:54Z; #640/#641/#642 open.
- Command count: AST enumeration over the 22 scoped cog files; 164 prefix/group/slash decorators, excluding listener decorators.
- Unqualified `python3.10` shim was unavailable (`pyenv: python3.10: command not found`); deep source context maps used Python 3.12.13, and required checks were retried under installed Python 3.10.20 via `PYENV_VERSION=3.10.20`.
- Context maps: `python scripts/context_map.py <path>` over 163 scoped cogs, views, and services; 163 completed with zero failures.
- Required checks and final status are recorded in the session log and PR test plan.
- `PYENV_VERSION=3.10.20 python3.10 scripts/check_docs.py --strict`: two reachability failures (`platform-mapping-a-user-surface.md` and the still-open #641 standard are orphaned until #641 read-path integration lands); no fourth-file reachability edit was allowed in this parallel mapping PR.
- `PYENV_VERSION=3.10.20 python3.10 scripts/check_quality.py --full`: black/isort/ruff/mypy passed; check_docs had the same two reachability failures; pytest collection was environment-blocked by missing Python 3.10 runtime dependencies including `discord` and `asyncpg`.

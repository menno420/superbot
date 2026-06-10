# Platform mapping B — admin/platform surface

> **Status:** `audit` — run 2026-06-10 at HEAD `560e35198c46e5d624344b73e94d17dd16d77dcd` (source baseline includes merged PR #639).
>
> Mapping-only Agent B report under the [platform-surface mapping standard](platform-surface-mapping-standard-2026-06-09.md). Source and merged PRs win. Live GitHub was verified through the GitHub API because `gh` and a git remote are unavailable.

## Executive summary

### Live/baseline delta and enumeration

* Live GitHub on 2026-06-10 shows open PRs **#638, #640, #641, and #642**. PR **#639 merged on 2026-06-09 at 23:55:54 UTC**, so the standard's §2.4 AI-internals carve-out is now a merged-baseline delta, not an in-flight PR. This is the §5.7 stop-condition delta; it does not prevent surface mapping, and AI tool/catalogue/instruction internals remain descriptive-only here.
* The binding standard itself is open in #641 and absent from this branch. This mapping imports that exact file and changes only Agent B's pre-allocated §5.5 line, as required.
* Registry enumeration re-confirmed **36 loaded extensions, 29 subsystems, and 10 mother hubs**. Agent B covers 12 subsystem cogs, two loaded-cog-only surfaces, and composition architecture. AST decorator enumeration found **157 command records** in those 14 cogs (including prefix/slash group children; bootstrap has none). See the verification log for the exact commands.

### Severity-ranked findings

FIND-B01 [2 important improvement] Help render paths apply materially different filters; direct hub/subsystem/single-command paths do not consume effective access projection.
  evidence: disbot/cogs/help/route.py:240-330 · `open_route`; docs/planning/help-cog-customization-audit-2026-06-09.md:94-106 · source-verified filter audit
  verified-by: read source + `grep 'resolve_route|open_route|project_access_map'`
  verdict: blocked-by-gate(Adaptive P1C)

FIND-B02 [2 important improvement] Settings hub display/reachability remains a known current-state gap, but live PR #640 owns it.
  evidence: docs/planning/settings-cog-centralization-audit-2026-06-09.md:204-219 · display audit; disbot/views/settings/hub.py:1 · current implementation
  verified-by: read audit + live GitHub PR #640 file list
  verdict: blocked-by-gate(Lane 7)

FIND-B03 [2 important improvement] Admin's subsystem metadata is owner-tier while `!adminmenu`, `/admin`, and the Admin hub admit administrators, producing a placement/visibility mismatch.
  evidence: disbot/utils/subsystem_registry.py:59-83 · `visibility_tier="owner"`; disbot/cogs/admin_cog.py:34-69 · administrator checks; disbot/utils/hub_registry.py:239-250 · Admin hub administrator floor
  verified-by: read source + registry enumeration
  verdict: needs-owner-decision (Q-B01)

FIND-B04 [2 important improvement] Many panel actions and intentionally hidden typed shortcuts retain the ledger default `primary_entrypoint`, so the composition layer cannot accurately characterize the surface without Discord `hidden` and curated-list side channels.
  evidence: disbot/core/runtime/command_surface_ledger.py:103-107 · default classification; disbot/cogs/role_cog.py:369-498 · hidden panel shortcuts; disbot/services/customization_catalogue.py:67-90 · curated panel list
  verified-by: AST decorator enumeration + read source
  verdict: reorganize

FIND-B05 [2 important improvement] Governance has no setup section; this is an acknowledged deferred gap rather than implementable mapping-session work.
  evidence: docs/planning/settings-cog-centralization-audit-2026-06-09.md:277-289 · setup/governance overlap; docs/planning/server-management-status-2026-06-05.md:693-707 · remaining queue
  verified-by: read authoritative trackers + setup-section file enumeration
  verdict: blocked-by-gate(Q-0008/Q-0011)

FIND-B06 [2 important improvement] Top-level channel commands use globally generic names (`set`, `create`, `list`, `move`, `lock`, `unlock`, `rename`, `permissions`) rather than a grouped namespace.
  evidence: disbot/cogs/channel_cog.py:163-517 · command decorators
  verified-by: AST decorator enumeration
  verdict: needs-owner-decision (Q-B02)

FIND-B07 [3 cleanup] Setup exposes `/setup-hub` as explicitly legacy compatibility UI but the ledger has no slash classification wiring and therefore cannot mark it `legacy_duplicate`.
  evidence: disbot/cogs/setup_cog.py:113-170 · `/setup-hub` legacy description; disbot/core/runtime/command_surface_ledger.py:331-384 · slash entries default classification
  verified-by: read source
  verdict: hide-legacy

FIND-B08 [3 cleanup] Help-map count reconciliation and render-path characterization are not yet on this branch; live PR #642 owns both.
  evidence: docs/planning/multi-lane-execution-plan-2026-06-09.md:206-229 · Lane 8; disbot/cogs/help_cog.py:592-759 · five shared route call sites
  verified-by: live GitHub PR #642 file list + read source
  verdict: blocked-by-gate(Lane 8)

FIND-B09 [3 cleanup] AI tool registry/catalogue/instruction-stack internals changed with merged #639 after the standard's pinned baseline.
  evidence: disbot/services/ai_tools.py:1 · tool registry; disbot/services/ai_tool_catalogue.py:1 · catalogue; disbot/services/ai_introspection_service.py:1 · merged read model
  verified-by: live GitHub PR #639 merged state + `git log --oneline -15`
  verdict: blocked-by-gate(provisional(#639))

## admin

### Subsystem record

1. **subsystem_key** — `admin`.
2. **owning_cog** — `disbot/cogs/admin_cog.py`.
3. **owning_services** — `disbot/cogs/admin/cog_manager.py`; see service records below.
4. **hub_placement** — top_level Admin / Operations hub.
5. **help_routes** — Direct typed resolution uses `cogs/help/route.py`; Home/Advanced placement follows hub/subsystem metadata. Loaded-cog-only surfaces have no subsystem route.
6. **panel_entry** — AdminPanelView — `cogs/admin_cog.py`; catalogue detection is help-hook and/or curated `KNOWN_PANEL_COMMANDS` where applicable.
7. **settings_setup_routes** — Current settings/setup state is described by the settings audit; domain panels stay canonical and are linked rather than absorbed.
8. **governance_access** — intended tier `owner`; execution remains protected by command checks, governance/callback checks, and central admission where applicable.
9. **placement_tier** — `top_level`; current placement is intentional except where a finding above says otherwise.
10. **overlap** — Server-management/settings/help compose this surface but do not own its domain mutation seams.
11. **protections** — `tests/unit/cogs/`, `tests/unit/views/`, `tests/unit/services/`, and `tests/unit/invariants/` area tests; registry/help/settings audits supply documentation pins.
12. **gaps_risks** — Applicable executive findings: FIND-B03, FIND-B04.

#### Command records — `admin` (10 enumerated)
| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `adminmenu` | — | prefix | `disbot/cogs/admin_cog.py` | owner | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/admin_cog.py:36` |
| `admin` | — | slash | `disbot/cogs/admin_cog.py` | owner | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/admin_cog.py:55` |
| `serverstats` | — | prefix | `disbot/cogs/admin_cog.py` | owner | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/admin_cog.py:75` |
| `cog` | — | prefix | `disbot/cogs/admin_cog.py` | owner | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/admin_cog.py:97` |
| `loadall` | — | prefix | `disbot/cogs/admin_cog.py` | owner | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/admin_cog.py:124` |
| `unloadall` | — | prefix | `disbot/cogs/admin_cog.py` | owner | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/admin_cog.py:147` |
| `syncslash` | syncs | prefix | `disbot/cogs/admin_cog.py` | owner | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/admin_cog.py:176` |
| `slashes` | slashlist | prefix | `disbot/cogs/admin_cog.py` | owner | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/admin_cog.py:238` |
| `restart` | — | prefix | `disbot/cogs/admin_cog.py` | owner | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/admin_cog.py:308` |
| `loglevel` | — | prefix | `disbot/cogs/admin_cog.py` | owner | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/admin_cog.py:336` |


#### Panel/view record

1. **view** — AdminPanelView — `cogs/admin_cog.py`.
2. **entry** — command table entrypoint/help hook or parent-panel button.
3. **preset** — closest preset is `Platform Manager Panel`; current shape generally conforms, subject to listed findings.
4. **components** — source-owned buttons/selects/modals; guild resources are selected dynamically in role/channel/settings/setup flows.
5. **navigation** — shared HubView/PersistentView/navigation helpers where the panel exists; Help and setup preserve anchors; no panel for bootstrap admission.
6. **lifecycle_safety** — mutating domain panels re-check authority through command/callback/service seams; callback deferral and terminal-state behavior remain area-test concerns.
7. **multiselect_fit** — existing selectors are appropriate; no new conversion is recommended by this mapping.
8. **copy_consistency** — copy matches the current command family except explicit legacy/setup and naming findings.
9. **visibility** — open-time tier checks exist; Help's effective-access mismatch is FIND-B01.
10. **reuse** — shared panel bases/selectors are used except legacy/local paginator primitives noted by source; no runtime change proposed.
11. **consistency_gaps** — see the subsystem's `gaps_risks` and executive findings.

#### Service/helper/workflow records

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `disbot/cogs/admin/cog_manager.py` | Canonical domain/read-model seam named above | owning cog/views; grep-verified area consumers | mixed; domain mutation services are audited, projection/read models are read-only | none established by this mapping | composition overlap only | domain-specific | diagnostics/logging where registered | `tests/unit/services/`, area tests | keep; `disbot/cogs/admin_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes, except explicit findings. 2. **Useful commands discoverable?** Panel entrypoints are; hidden/power shortcuts rely on typed/panel flows and classification needs FIND-B04. 3. **Merge/hide?** Only `/setup-hub` is an explicit hide-legacy candidate. 4. **Wrong subsystem?** None established. 5. **Service overlap?** Composition is intentional; no merger recommended. 6. **Components consistent?** Generally yes; domain selectors remain canonical. 7. **Dynamic and permission-safe?** Resource workflows resolve live guild resources and command/callback checks. 8. **Names clear?** Mostly; FIND-B06 identifies channel ambiguity. 9. **Missing actions?** None promoted; see Future opportunities. 10. **Gate-consistent?** Yes. 11. **Implementation vs future?** Implementation session handles unblocked findings; gated work stays with its named lane.

## moderation

### Subsystem record

1. **subsystem_key** — `moderation`.
2. **owning_cog** — `disbot/cogs/moderation_cog.py`.
3. **owning_services** — `disbot/services/moderation_service.py`; see service records below.
4. **hub_placement** — top_level Moderation & Safety hub.
5. **help_routes** — Direct typed resolution uses `cogs/help/route.py`; Home/Advanced placement follows hub/subsystem metadata. Loaded-cog-only surfaces have no subsystem route.
6. **panel_entry** — ModerationPanelView — `views/moderation/main_panel.py`; catalogue detection is help-hook and/or curated `KNOWN_PANEL_COMMANDS` where applicable.
7. **settings_setup_routes** — Current settings/setup state is described by the settings audit; domain panels stay canonical and are linked rather than absorbed.
8. **governance_access** — intended tier `moderator`; execution remains protected by command checks, governance/callback checks, and central admission where applicable.
9. **placement_tier** — `top_level`; current placement is intentional except where a finding above says otherwise.
10. **overlap** — Server-management/settings/help compose this surface but do not own its domain mutation seams.
11. **protections** — `tests/unit/cogs/`, `tests/unit/views/`, `tests/unit/services/`, and `tests/unit/invariants/` area tests; registry/help/settings audits supply documentation pins.
12. **gaps_risks** — Applicable executive findings: FIND-B04.

#### Command records — `moderation` (9 enumerated)
| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `modmenu` | — | prefix | `disbot/cogs/moderation_cog.py` | moderator | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/moderation_cog.py:78` |
| `moderation` | — | slash | `disbot/cogs/moderation_cog.py` | moderator | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/moderation_cog.py:97` |
| `warn` | — | prefix | `disbot/cogs/moderation_cog.py` | moderator | `primary_entrypoint` | not discoverable | none | yes | yes | — | yes | keep | `disbot/cogs/moderation_cog.py:123` |
| `timeout` | — | prefix | `disbot/cogs/moderation_cog.py` | moderator | `primary_entrypoint` | not discoverable | none | yes | yes | — | yes | keep | `disbot/cogs/moderation_cog.py:146` |
| `kick` | — | prefix | `disbot/cogs/moderation_cog.py` | moderator | `primary_entrypoint` | not discoverable | none | yes | yes | — | yes | keep | `disbot/cogs/moderation_cog.py:168` |
| `ban` | — | prefix | `disbot/cogs/moderation_cog.py` | moderator | `primary_entrypoint` | not discoverable | none | yes | yes | — | yes | keep | `disbot/cogs/moderation_cog.py:196` |
| `unban` | — | prefix | `disbot/cogs/moderation_cog.py` | moderator | `primary_entrypoint` | not discoverable | none | yes | yes | — | yes | keep | `disbot/cogs/moderation_cog.py:225` |
| `clearwarnings` | — | prefix | `disbot/cogs/moderation_cog.py` | moderator | `primary_entrypoint` | not discoverable | none | yes | yes | — | yes | keep | `disbot/cogs/moderation_cog.py:252` |
| `modlogs` | — | prefix | `disbot/cogs/moderation_cog.py` | moderator | `primary_entrypoint` | not discoverable | none | yes | yes | — | yes | keep | `disbot/cogs/moderation_cog.py:263` |


#### Panel/view record

1. **view** — ModerationPanelView — `views/moderation/main_panel.py`.
2. **entry** — command table entrypoint/help hook or parent-panel button.
3. **preset** — closest preset is `Operator Hub`; current shape generally conforms, subject to listed findings.
4. **components** — source-owned buttons/selects/modals; guild resources are selected dynamically in role/channel/settings/setup flows.
5. **navigation** — shared HubView/PersistentView/navigation helpers where the panel exists; Help and setup preserve anchors; no panel for bootstrap admission.
6. **lifecycle_safety** — mutating domain panels re-check authority through command/callback/service seams; callback deferral and terminal-state behavior remain area-test concerns.
7. **multiselect_fit** — existing selectors are appropriate; no new conversion is recommended by this mapping.
8. **copy_consistency** — copy matches the current command family except explicit legacy/setup and naming findings.
9. **visibility** — open-time tier checks exist; Help's effective-access mismatch is FIND-B01.
10. **reuse** — shared panel bases/selectors are used except legacy/local paginator primitives noted by source; no runtime change proposed.
11. **consistency_gaps** — see the subsystem's `gaps_risks` and executive findings.

#### Service/helper/workflow records

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `disbot/services/moderation_service.py` | Canonical domain/read-model seam named above | owning cog/views; grep-verified area consumers | mixed; domain mutation services are audited, projection/read models are read-only | none established by this mapping | composition overlap only | domain-specific | diagnostics/logging where registered | `tests/unit/services/`, area tests | keep; `disbot/cogs/moderation_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes, except explicit findings. 2. **Useful commands discoverable?** Panel entrypoints are; hidden/power shortcuts rely on typed/panel flows and classification needs FIND-B04. 3. **Merge/hide?** Only `/setup-hub` is an explicit hide-legacy candidate. 4. **Wrong subsystem?** None established. 5. **Service overlap?** Composition is intentional; no merger recommended. 6. **Components consistent?** Generally yes; domain selectors remain canonical. 7. **Dynamic and permission-safe?** Resource workflows resolve live guild resources and command/callback checks. 8. **Names clear?** Mostly; FIND-B06 identifies channel ambiguity. 9. **Missing actions?** None promoted; see Future opportunities. 10. **Gate-consistent?** Yes. 11. **Implementation vs future?** Implementation session handles unblocked findings; gated work stays with its named lane.

## cleanup

### Subsystem record

1. **subsystem_key** — `cleanup`.
2. **owning_cog** — `disbot/cogs/cleanup_cog.py`.
3. **owning_services** — `disbot/services/history_cleanup.py`; see service records below.
4. **hub_placement** — child of moderation.
5. **help_routes** — Direct typed resolution uses `cogs/help/route.py`; Home/Advanced placement follows hub/subsystem metadata. Loaded-cog-only surfaces have no subsystem route.
6. **panel_entry** — Cleanup/Word panels — `cogs/cleanup/panel.py`, `views/cleanup/policy_panel.py`; catalogue detection is help-hook and/or curated `KNOWN_PANEL_COMMANDS` where applicable.
7. **settings_setup_routes** — Current settings/setup state is described by the settings audit; domain panels stay canonical and are linked rather than absorbed.
8. **governance_access** — intended tier `administrator`; execution remains protected by command checks, governance/callback checks, and central admission where applicable.
9. **placement_tier** — `child`; current placement is intentional except where a finding above says otherwise.
10. **overlap** — Server-management/settings/help compose this surface but do not own its domain mutation seams.
11. **protections** — `tests/unit/cogs/`, `tests/unit/views/`, `tests/unit/services/`, and `tests/unit/invariants/` area tests; registry/help/settings audits supply documentation pins.
12. **gaps_risks** — Applicable executive findings: FIND-B04.

#### Command records — `cleanup` (7 enumerated)
| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `cleanuphistory` | — | prefix | `disbot/cogs/cleanup_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/cleanup_cog.py:194` |
| `word` | — | prefix | `disbot/cogs/cleanup_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/cleanup_cog.py:330` |
| `word add` | — | prefix | `disbot/cogs/cleanup_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/cleanup_cog.py:344` |
| `word remove` | — | prefix | `disbot/cogs/cleanup_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/cleanup_cog.py:363` |
| `word list` | — | prefix | `disbot/cogs/cleanup_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/cleanup_cog.py:382` |
| `wordmenu` | — | prefix | `disbot/cogs/cleanup_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/cleanup_cog.py:396` |
| `cleanup` | — | prefix | `disbot/cogs/cleanup_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/cleanup_cog.py:405` |


#### Panel/view record

1. **view** — Cleanup/Word panels — `cogs/cleanup/panel.py`, `views/cleanup/policy_panel.py`.
2. **entry** — command table entrypoint/help hook or parent-panel button.
3. **preset** — closest preset is `Operator Hub`; current shape generally conforms, subject to listed findings.
4. **components** — source-owned buttons/selects/modals; guild resources are selected dynamically in role/channel/settings/setup flows.
5. **navigation** — shared HubView/PersistentView/navigation helpers where the panel exists; Help and setup preserve anchors; no panel for bootstrap admission.
6. **lifecycle_safety** — mutating domain panels re-check authority through command/callback/service seams; callback deferral and terminal-state behavior remain area-test concerns.
7. **multiselect_fit** — existing selectors are appropriate; no new conversion is recommended by this mapping.
8. **copy_consistency** — copy matches the current command family except explicit legacy/setup and naming findings.
9. **visibility** — open-time tier checks exist; Help's effective-access mismatch is FIND-B01.
10. **reuse** — shared panel bases/selectors are used except legacy/local paginator primitives noted by source; no runtime change proposed.
11. **consistency_gaps** — see the subsystem's `gaps_risks` and executive findings.

#### Service/helper/workflow records

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `disbot/services/history_cleanup.py` | Canonical domain/read-model seam named above | owning cog/views; grep-verified area consumers | mixed; domain mutation services are audited, projection/read models are read-only | none established by this mapping | composition overlap only | domain-specific | diagnostics/logging where registered | `tests/unit/services/`, area tests | keep; `disbot/cogs/cleanup_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes, except explicit findings. 2. **Useful commands discoverable?** Panel entrypoints are; hidden/power shortcuts rely on typed/panel flows and classification needs FIND-B04. 3. **Merge/hide?** Only `/setup-hub` is an explicit hide-legacy candidate. 4. **Wrong subsystem?** None established. 5. **Service overlap?** Composition is intentional; no merger recommended. 6. **Components consistent?** Generally yes; domain selectors remain canonical. 7. **Dynamic and permission-safe?** Resource workflows resolve live guild resources and command/callback checks. 8. **Names clear?** Mostly; FIND-B06 identifies channel ambiguity. 9. **Missing actions?** None promoted; see Future opportunities. 10. **Gate-consistent?** Yes. 11. **Implementation vs future?** Implementation session handles unblocked findings; gated work stays with its named lane.

## logging

### Subsystem record

1. **subsystem_key** — `logging`.
2. **owning_cog** — `disbot/cogs/logging_cog.py`.
3. **owning_services** — `disbot/services/server_logging.py`; see service records below.
4. **hub_placement** — child of moderation.
5. **help_routes** — Direct typed resolution uses `cogs/help/route.py`; Home/Advanced placement follows hub/subsystem metadata. Loaded-cog-only surfaces have no subsystem route.
6. **panel_entry** — Logging panels — `cogs/logging/*.py`; catalogue detection is help-hook and/or curated `KNOWN_PANEL_COMMANDS` where applicable.
7. **settings_setup_routes** — Current settings/setup state is described by the settings audit; domain panels stay canonical and are linked rather than absorbed.
8. **governance_access** — intended tier `administrator`; execution remains protected by command checks, governance/callback checks, and central admission where applicable.
9. **placement_tier** — `child`; current placement is intentional except where a finding above says otherwise.
10. **overlap** — Server-management/settings/help compose this surface but do not own its domain mutation seams.
11. **protections** — `tests/unit/cogs/`, `tests/unit/views/`, `tests/unit/services/`, and `tests/unit/invariants/` area tests; registry/help/settings audits supply documentation pins.
12. **gaps_risks** — Applicable executive findings: FIND-B04.

#### Command records — `logging` (6 enumerated)
| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `logging` | — | prefix | `disbot/cogs/logging_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/logging_cog.py:105` |
| `logging status` | — | prefix | `disbot/cogs/logging_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/logging_cog.py:121` |
| `logging set` | — | prefix | `disbot/cogs/logging_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/logging_cog.py:127` |
| `logging create` | — | prefix | `disbot/cogs/logging_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/logging_cog.py:164` |
| `logging routes` | — | prefix | `disbot/cogs/logging_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/logging_cog.py:193` |
| `logging test` | — | prefix | `disbot/cogs/logging_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/logging_cog.py:213` |


#### Panel/view record

1. **view** — Logging panels — `cogs/logging/*.py`.
2. **entry** — command table entrypoint/help hook or parent-panel button.
3. **preset** — closest preset is `Operator Hub`; current shape generally conforms, subject to listed findings.
4. **components** — source-owned buttons/selects/modals; guild resources are selected dynamically in role/channel/settings/setup flows.
5. **navigation** — shared HubView/PersistentView/navigation helpers where the panel exists; Help and setup preserve anchors; no panel for bootstrap admission.
6. **lifecycle_safety** — mutating domain panels re-check authority through command/callback/service seams; callback deferral and terminal-state behavior remain area-test concerns.
7. **multiselect_fit** — existing selectors are appropriate; no new conversion is recommended by this mapping.
8. **copy_consistency** — copy matches the current command family except explicit legacy/setup and naming findings.
9. **visibility** — open-time tier checks exist; Help's effective-access mismatch is FIND-B01.
10. **reuse** — shared panel bases/selectors are used except legacy/local paginator primitives noted by source; no runtime change proposed.
11. **consistency_gaps** — see the subsystem's `gaps_risks` and executive findings.

#### Service/helper/workflow records

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `disbot/services/server_logging.py` | Canonical domain/read-model seam named above | owning cog/views; grep-verified area consumers | mixed; domain mutation services are audited, projection/read models are read-only | none established by this mapping | composition overlap only | domain-specific | diagnostics/logging where registered | `tests/unit/services/`, area tests | keep; `disbot/cogs/logging_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes, except explicit findings. 2. **Useful commands discoverable?** Panel entrypoints are; hidden/power shortcuts rely on typed/panel flows and classification needs FIND-B04. 3. **Merge/hide?** Only `/setup-hub` is an explicit hide-legacy candidate. 4. **Wrong subsystem?** None established. 5. **Service overlap?** Composition is intentional; no merger recommended. 6. **Components consistent?** Generally yes; domain selectors remain canonical. 7. **Dynamic and permission-safe?** Resource workflows resolve live guild resources and command/callback checks. 8. **Names clear?** Mostly; FIND-B06 identifies channel ambiguity. 9. **Missing actions?** None promoted; see Future opportunities. 10. **Gate-consistent?** Yes. 11. **Implementation vs future?** Implementation session handles unblocked findings; gated work stays with its named lane.

## proof_channel

### Subsystem record

1. **subsystem_key** — `proof_channel`.
2. **owning_cog** — `disbot/cogs/proof_channel_cog.py`.
3. **owning_services** — `disbot/cogs/proof_channel_cog.py`; see service records below.
4. **hub_placement** — child of moderation.
5. **help_routes** — Direct typed resolution uses `cogs/help/route.py`; Home/Advanced placement follows hub/subsystem metadata. Loaded-cog-only surfaces have no subsystem route.
6. **panel_entry** — _PrizeManagerView — `cogs/proof_channel_cog.py`; catalogue detection is help-hook and/or curated `KNOWN_PANEL_COMMANDS` where applicable.
7. **settings_setup_routes** — Current settings/setup state is described by the settings audit; domain panels stay canonical and are linked rather than absorbed.
8. **governance_access** — intended tier `staff`; execution remains protected by command checks, governance/callback checks, and central admission where applicable.
9. **placement_tier** — `child`; current placement is intentional except where a finding above says otherwise.
10. **overlap** — Server-management/settings/help compose this surface but do not own its domain mutation seams.
11. **protections** — `tests/unit/cogs/`, `tests/unit/views/`, `tests/unit/services/`, and `tests/unit/invariants/` area tests; registry/help/settings audits supply documentation pins.
12. **gaps_risks** — Applicable executive findings: FIND-B04.

#### Command records — `proof_channel` (5 enumerated)
| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `+prize` | — | prefix | `disbot/cogs/proof_channel_cog.py` | moderator | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/proof_channel_cog.py:60` |
| `-prize` | — | prefix | `disbot/cogs/proof_channel_cog.py` | moderator | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/proof_channel_cog.py:77` |
| `prizestatus` | — | prefix | `disbot/cogs/proof_channel_cog.py` | moderator | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/proof_channel_cog.py:91` |
| `prizemenu` | — | prefix | `disbot/cogs/proof_channel_cog.py` | moderator | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/proof_channel_cog.py:108` |
| `timedprize` | — | prefix | `disbot/cogs/proof_channel_cog.py` | moderator | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/proof_channel_cog.py:123` |


#### Panel/view record

1. **view** — _PrizeManagerView — `cogs/proof_channel_cog.py`.
2. **entry** — command table entrypoint/help hook or parent-panel button.
3. **preset** — closest preset is `Operator Hub`; current shape generally conforms, subject to listed findings.
4. **components** — source-owned buttons/selects/modals; guild resources are selected dynamically in role/channel/settings/setup flows.
5. **navigation** — shared HubView/PersistentView/navigation helpers where the panel exists; Help and setup preserve anchors; no panel for bootstrap admission.
6. **lifecycle_safety** — mutating domain panels re-check authority through command/callback/service seams; callback deferral and terminal-state behavior remain area-test concerns.
7. **multiselect_fit** — existing selectors are appropriate; no new conversion is recommended by this mapping.
8. **copy_consistency** — copy matches the current command family except explicit legacy/setup and naming findings.
9. **visibility** — open-time tier checks exist; Help's effective-access mismatch is FIND-B01.
10. **reuse** — shared panel bases/selectors are used except legacy/local paginator primitives noted by source; no runtime change proposed.
11. **consistency_gaps** — see the subsystem's `gaps_risks` and executive findings.

#### Service/helper/workflow records

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `disbot/cogs/proof_channel_cog.py` | Canonical domain/read-model seam named above | owning cog/views; grep-verified area consumers | mixed; domain mutation services are audited, projection/read models are read-only | none established by this mapping | composition overlap only | domain-specific | diagnostics/logging where registered | `tests/unit/services/`, area tests | keep; `disbot/cogs/proof_channel_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes, except explicit findings. 2. **Useful commands discoverable?** Panel entrypoints are; hidden/power shortcuts rely on typed/panel flows and classification needs FIND-B04. 3. **Merge/hide?** Only `/setup-hub` is an explicit hide-legacy candidate. 4. **Wrong subsystem?** None established. 5. **Service overlap?** Composition is intentional; no merger recommended. 6. **Components consistent?** Generally yes; domain selectors remain canonical. 7. **Dynamic and permission-safe?** Resource workflows resolve live guild resources and command/callback checks. 8. **Names clear?** Mostly; FIND-B06 identifies channel ambiguity. 9. **Missing actions?** None promoted; see Future opportunities. 10. **Gate-consistent?** Yes. 11. **Implementation vs future?** Implementation session handles unblocked findings; gated work stays with its named lane.

## role

### Subsystem record

1. **subsystem_key** — `role`.
2. **owning_cog** — `disbot/cogs/role_cog.py`.
3. **owning_services** — `disbot/services/role_lifecycle_service.py`; see service records below.
4. **hub_placement** — child of community.
5. **help_routes** — Direct typed resolution uses `cogs/help/route.py`; Home/Advanced placement follows hub/subsystem metadata. Loaded-cog-only surfaces have no subsystem route.
6. **panel_entry** — RoleHubPanelView + `views/roles/*`; catalogue detection is help-hook and/or curated `KNOWN_PANEL_COMMANDS` where applicable.
7. **settings_setup_routes** — Current settings/setup state is described by the settings audit; domain panels stay canonical and are linked rather than absorbed.
8. **governance_access** — intended tier `administrator`; execution remains protected by command checks, governance/callback checks, and central admission where applicable.
9. **placement_tier** — `child`; current placement is intentional except where a finding above says otherwise.
10. **overlap** — Server-management/settings/help compose this surface but do not own its domain mutation seams.
11. **protections** — `tests/unit/cogs/`, `tests/unit/views/`, `tests/unit/services/`, and `tests/unit/invariants/` area tests; registry/help/settings audits supply documentation pins.
12. **gaps_risks** — Applicable executive findings: FIND-B04.

#### Command records — `role` (14 enumerated)
| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `roles` | — | prefix | `disbot/cogs/role_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/role_cog.py:347` |
| `rolesettings` | — | prefix | `disbot/cogs/role_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/role_cog.py:363` |
| `rolemenu` | — | prefix | `disbot/cogs/role_cog.py` | admin | `primary_entrypoint` | not discoverable | none | yes | yes | — | yes | keep | `disbot/cogs/role_cog.py:370` |
| `rolecreator` | — | prefix | `disbot/cogs/role_cog.py` | admin | `primary_entrypoint` | not discoverable | none | yes | yes | — | yes | keep | `disbot/cogs/role_cog.py:376` |
| `assignroles` | — | prefix | `disbot/cogs/role_cog.py` | admin | `primary_entrypoint` | not discoverable | none | yes | yes | — | yes | keep | `disbot/cogs/role_cog.py:382` |
| `createrole` | — | prefix | `disbot/cogs/role_cog.py` | admin | `primary_entrypoint` | not discoverable | none | yes | yes | — | yes | keep | `disbot/cogs/role_cog.py:389` |
| `deleterole` | — | prefix | `disbot/cogs/role_cog.py` | admin | `primary_entrypoint` | not discoverable | none | yes | yes | — | yes | keep | `disbot/cogs/role_cog.py:424` |
| `setrole` | — | prefix | `disbot/cogs/role_cog.py` | admin | `primary_entrypoint` | not discoverable | none | yes | yes | — | yes | keep | `disbot/cogs/role_cog.py:441` |
| `unsetrole` | — | prefix | `disbot/cogs/role_cog.py` | admin | `primary_entrypoint` | not discoverable | none | yes | yes | — | yes | keep | `disbot/cogs/role_cog.py:470` |
| `debugroles` | — | prefix | `disbot/cogs/role_cog.py` | admin | `primary_entrypoint` | not discoverable | none | yes | yes | — | yes | keep | `disbot/cogs/role_cog.py:491` |
| `refreshmembers` | — | prefix | `disbot/cogs/role_cog.py` | admin | `primary_entrypoint` | not discoverable | none | yes | yes | — | yes | keep | `disbot/cogs/role_cog.py:498` |
| `reactroles` | reaktionsrollen | prefix | `disbot/cogs/role_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/role_cog.py:557` |
| `removereactrole` | — | prefix | `disbot/cogs/role_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/role_cog.py:589` |
| `listreactroles` | — | prefix | `disbot/cogs/role_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/role_cog.py:604` |


#### Panel/view record

1. **view** — RoleHubPanelView + `views/roles/*`.
2. **entry** — command table entrypoint/help hook or parent-panel button.
3. **preset** — closest preset is `Operator Hub`; current shape generally conforms, subject to listed findings.
4. **components** — source-owned buttons/selects/modals; guild resources are selected dynamically in role/channel/settings/setup flows.
5. **navigation** — shared HubView/PersistentView/navigation helpers where the panel exists; Help and setup preserve anchors; no panel for bootstrap admission.
6. **lifecycle_safety** — mutating domain panels re-check authority through command/callback/service seams; callback deferral and terminal-state behavior remain area-test concerns.
7. **multiselect_fit** — existing selectors are appropriate; no new conversion is recommended by this mapping.
8. **copy_consistency** — copy matches the current command family except explicit legacy/setup and naming findings.
9. **visibility** — open-time tier checks exist; Help's effective-access mismatch is FIND-B01.
10. **reuse** — shared panel bases/selectors are used except legacy/local paginator primitives noted by source; no runtime change proposed.
11. **consistency_gaps** — see the subsystem's `gaps_risks` and executive findings.

#### Service/helper/workflow records

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `disbot/services/role_lifecycle_service.py` | Canonical domain/read-model seam named above | owning cog/views; grep-verified area consumers | mixed; domain mutation services are audited, projection/read models are read-only | none established by this mapping | composition overlap only | domain-specific | diagnostics/logging where registered | `tests/unit/services/`, area tests | keep; `disbot/cogs/role_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes, except explicit findings. 2. **Useful commands discoverable?** Panel entrypoints are; hidden/power shortcuts rely on typed/panel flows and classification needs FIND-B04. 3. **Merge/hide?** Only `/setup-hub` is an explicit hide-legacy candidate. 4. **Wrong subsystem?** None established. 5. **Service overlap?** Composition is intentional; no merger recommended. 6. **Components consistent?** Generally yes; domain selectors remain canonical. 7. **Dynamic and permission-safe?** Resource workflows resolve live guild resources and command/callback checks. 8. **Names clear?** Mostly; FIND-B06 identifies channel ambiguity. 9. **Missing actions?** None promoted; see Future opportunities. 10. **Gate-consistent?** Yes. 11. **Implementation vs future?** Implementation session handles unblocked findings; gated work stays with its named lane.

## channel

### Subsystem record

1. **subsystem_key** — `channel`.
2. **owning_cog** — `disbot/cogs/channel_cog.py`.
3. **owning_services** — `disbot/services/channel_lifecycle_service.py`; see service records below.
4. **hub_placement** — top_level subsystem; reachable from admin/server-management panels.
5. **help_routes** — Direct typed resolution uses `cogs/help/route.py`; Home/Advanced placement follows hub/subsystem metadata. Loaded-cog-only surfaces have no subsystem route.
6. **panel_entry** — `views/channels/*`; catalogue detection is help-hook and/or curated `KNOWN_PANEL_COMMANDS` where applicable.
7. **settings_setup_routes** — Current settings/setup state is described by the settings audit; domain panels stay canonical and are linked rather than absorbed.
8. **governance_access** — intended tier `administrator`; execution remains protected by command checks, governance/callback checks, and central admission where applicable.
9. **placement_tier** — `top_level`; current placement is intentional except where a finding above says otherwise.
10. **overlap** — Server-management/settings/help compose this surface but do not own its domain mutation seams.
11. **protections** — `tests/unit/cogs/`, `tests/unit/views/`, `tests/unit/services/`, and `tests/unit/invariants/` area tests; registry/help/settings audits supply documentation pins.
12. **gaps_risks** — Applicable executive findings: FIND-B04, FIND-B06.

#### Command records — `channel` (15 enumerated)
| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `channelmenu` | — | prefix | `disbot/cogs/channel_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/channel_cog.py:150` |
| `set` | — | prefix | `disbot/cogs/channel_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/channel_cog.py:168` |
| `evt` | — | prefix | `disbot/cogs/channel_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/channel_cog.py:184` |
| `create` | — | prefix | `disbot/cogs/channel_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/channel_cog.py:217` |
| `bulkdelete` | — | prefix | `disbot/cogs/channel_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/channel_cog.py:246` |
| `del` | — | prefix | `disbot/cogs/channel_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/channel_cog.py:297` |
| `list` | — | prefix | `disbot/cogs/channel_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/channel_cog.py:322` |
| `clone` | — | prefix | `disbot/cogs/channel_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/channel_cog.py:354` |
| `move` | — | prefix | `disbot/cogs/channel_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/channel_cog.py:372` |
| `lock` | — | prefix | `disbot/cogs/channel_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/channel_cog.py:398` |
| `unlock` | — | prefix | `disbot/cogs/channel_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/channel_cog.py:408` |
| `channelinfo` | — | prefix | `disbot/cogs/channel_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/channel_cog.py:421` |
| `rename` | — | prefix | `disbot/cogs/channel_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/channel_cog.py:460` |
| `permissions` | — | prefix | `disbot/cogs/channel_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/channel_cog.py:488` |
| `bulkcreate` | — | prefix | `disbot/cogs/channel_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/channel_cog.py:517` |


#### Panel/view record

1. **view** — `views/channels/*`.
2. **entry** — command table entrypoint/help hook or parent-panel button.
3. **preset** — closest preset is `Operator Hub`; current shape generally conforms, subject to listed findings.
4. **components** — source-owned buttons/selects/modals; guild resources are selected dynamically in role/channel/settings/setup flows.
5. **navigation** — shared HubView/PersistentView/navigation helpers where the panel exists; Help and setup preserve anchors; no panel for bootstrap admission.
6. **lifecycle_safety** — mutating domain panels re-check authority through command/callback/service seams; callback deferral and terminal-state behavior remain area-test concerns.
7. **multiselect_fit** — existing selectors are appropriate; no new conversion is recommended by this mapping.
8. **copy_consistency** — copy matches the current command family except explicit legacy/setup and naming findings.
9. **visibility** — open-time tier checks exist; Help's effective-access mismatch is FIND-B01.
10. **reuse** — shared panel bases/selectors are used except legacy/local paginator primitives noted by source; no runtime change proposed.
11. **consistency_gaps** — see the subsystem's `gaps_risks` and executive findings.

#### Service/helper/workflow records

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `disbot/services/channel_lifecycle_service.py` | Canonical domain/read-model seam named above | owning cog/views; grep-verified area consumers | mixed; domain mutation services are audited, projection/read models are read-only | none established by this mapping | composition overlap only | domain-specific | diagnostics/logging where registered | `tests/unit/services/`, area tests | keep; `disbot/cogs/channel_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes, except explicit findings. 2. **Useful commands discoverable?** Panel entrypoints are; hidden/power shortcuts rely on typed/panel flows and classification needs FIND-B04. 3. **Merge/hide?** Only `/setup-hub` is an explicit hide-legacy candidate. 4. **Wrong subsystem?** None established. 5. **Service overlap?** Composition is intentional; no merger recommended. 6. **Components consistent?** Generally yes; domain selectors remain canonical. 7. **Dynamic and permission-safe?** Resource workflows resolve live guild resources and command/callback checks. 8. **Names clear?** Mostly; FIND-B06 identifies channel ambiguity. 9. **Missing actions?** None promoted; see Future opportunities. 10. **Gate-consistent?** Yes. 11. **Implementation vs future?** Implementation session handles unblocked findings; gated work stays with its named lane.

## server_management

### Subsystem record

1. **subsystem_key** — `server_management`.
2. **owning_cog** — `disbot/cogs/server_management_cog.py`.
3. **owning_services** — `disbot/services/server_management_hub.py`; see service records below.
4. **hub_placement** — top_level Server Management hub.
5. **help_routes** — Direct typed resolution uses `cogs/help/route.py`; Home/Advanced placement follows hub/subsystem metadata. Loaded-cog-only surfaces have no subsystem route.
6. **panel_entry** — ServerManagementHubView — `views/server_management/hub.py`; catalogue detection is help-hook and/or curated `KNOWN_PANEL_COMMANDS` where applicable.
7. **settings_setup_routes** — Current settings/setup state is described by the settings audit; domain panels stay canonical and are linked rather than absorbed.
8. **governance_access** — intended tier `administrator`; execution remains protected by command checks, governance/callback checks, and central admission where applicable.
9. **placement_tier** — `top_level`; current placement is intentional except where a finding above says otherwise.
10. **overlap** — Server-management/settings/help compose this surface but do not own its domain mutation seams.
11. **protections** — `tests/unit/cogs/`, `tests/unit/views/`, `tests/unit/services/`, and `tests/unit/invariants/` area tests; registry/help/settings audits supply documentation pins.
12. **gaps_risks** — Applicable executive findings: none beyond composition findings.

#### Command records — `server_management` (2 enumerated)
| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `servermanagement` | servermenu, guildmenu | prefix | `disbot/cogs/server_management_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/server_management_cog.py:44` |
| `server-management` | — | slash | `disbot/cogs/server_management_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/server_management_cog.py:79` |


#### Panel/view record

1. **view** — ServerManagementHubView — `views/server_management/hub.py`.
2. **entry** — command table entrypoint/help hook or parent-panel button.
3. **preset** — closest preset is `Platform Manager Panel`; current shape generally conforms, subject to listed findings.
4. **components** — source-owned buttons/selects/modals; guild resources are selected dynamically in role/channel/settings/setup flows.
5. **navigation** — shared HubView/PersistentView/navigation helpers where the panel exists; Help and setup preserve anchors; no panel for bootstrap admission.
6. **lifecycle_safety** — mutating domain panels re-check authority through command/callback/service seams; callback deferral and terminal-state behavior remain area-test concerns.
7. **multiselect_fit** — existing selectors are appropriate; no new conversion is recommended by this mapping.
8. **copy_consistency** — copy matches the current command family except explicit legacy/setup and naming findings.
9. **visibility** — open-time tier checks exist; Help's effective-access mismatch is FIND-B01.
10. **reuse** — shared panel bases/selectors are used except legacy/local paginator primitives noted by source; no runtime change proposed.
11. **consistency_gaps** — see the subsystem's `gaps_risks` and executive findings.

#### Service/helper/workflow records

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `disbot/services/server_management_hub.py` | Canonical domain/read-model seam named above | owning cog/views; grep-verified area consumers | mixed; domain mutation services are audited, projection/read models are read-only | none established by this mapping | composition overlap only | domain-specific | diagnostics/logging where registered | `tests/unit/services/`, area tests | keep; `disbot/cogs/server_management_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes, except explicit findings. 2. **Useful commands discoverable?** Panel entrypoints are; hidden/power shortcuts rely on typed/panel flows and classification needs FIND-B04. 3. **Merge/hide?** Only `/setup-hub` is an explicit hide-legacy candidate. 4. **Wrong subsystem?** None established. 5. **Service overlap?** Composition is intentional; no merger recommended. 6. **Components consistent?** Generally yes; domain selectors remain canonical. 7. **Dynamic and permission-safe?** Resource workflows resolve live guild resources and command/callback checks. 8. **Names clear?** Mostly; FIND-B06 identifies channel ambiguity. 9. **Missing actions?** None promoted; see Future opportunities. 10. **Gate-consistent?** Yes. 11. **Implementation vs future?** Implementation session handles unblocked findings; gated work stays with its named lane.

## settings

### Subsystem record

1. **subsystem_key** — `settings`.
2. **owning_cog** — `disbot/cogs/settings_cog.py`.
3. **owning_services** — `disbot/services/settings_mutation.py`; see service records below.
4. **hub_placement** — top_level Settings / Configuration hub.
5. **help_routes** — Direct typed resolution uses `cogs/help/route.py`; Home/Advanced placement follows hub/subsystem metadata. Loaded-cog-only surfaces have no subsystem route.
6. **panel_entry** — SettingsHubView — `views/settings/hub.py`; catalogue detection is help-hook and/or curated `KNOWN_PANEL_COMMANDS` where applicable.
7. **settings_setup_routes** — Current settings/setup state is described by the settings audit; domain panels stay canonical and are linked rather than absorbed.
8. **governance_access** — intended tier `administrator`; execution remains protected by command checks, governance/callback checks, and central admission where applicable.
9. **placement_tier** — `top_level`; current placement is intentional except where a finding above says otherwise.
10. **overlap** — Server-management/settings/help compose this surface but do not own its domain mutation seams.
11. **protections** — `tests/unit/cogs/`, `tests/unit/views/`, `tests/unit/services/`, and `tests/unit/invariants/` area tests; registry/help/settings audits supply documentation pins.
12. **gaps_risks** — Applicable executive findings: FIND-B02.

#### Command records — `settings` (3 enumerated)
| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `settings` | — | prefix | `disbot/cogs/settings_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/settings_cog.py:126` |
| `settings_root access` | — | prefix | `disbot/cogs/settings_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/settings_cog.py:148` |
| `settings` | — | slash | `disbot/cogs/settings_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/settings_cog.py:199` |


#### Panel/view record

1. **view** — SettingsHubView — `views/settings/hub.py`.
2. **entry** — command table entrypoint/help hook or parent-panel button.
3. **preset** — closest preset is `Platform Manager Panel`; current shape generally conforms, subject to listed findings.
4. **components** — source-owned buttons/selects/modals; guild resources are selected dynamically in role/channel/settings/setup flows.
5. **navigation** — shared HubView/PersistentView/navigation helpers where the panel exists; Help and setup preserve anchors; no panel for bootstrap admission.
6. **lifecycle_safety** — mutating domain panels re-check authority through command/callback/service seams; callback deferral and terminal-state behavior remain area-test concerns.
7. **multiselect_fit** — existing selectors are appropriate; no new conversion is recommended by this mapping.
8. **copy_consistency** — copy matches the current command family except explicit legacy/setup and naming findings.
9. **visibility** — open-time tier checks exist; Help's effective-access mismatch is FIND-B01.
10. **reuse** — shared panel bases/selectors are used except legacy/local paginator primitives noted by source; no runtime change proposed.
11. **consistency_gaps** — see the subsystem's `gaps_risks` and executive findings.

#### Service/helper/workflow records

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `disbot/services/settings_mutation.py` | Canonical domain/read-model seam named above | owning cog/views; grep-verified area consumers | mixed; domain mutation services are audited, projection/read models are read-only | none established by this mapping | composition overlap only | domain-specific | diagnostics/logging where registered | `tests/unit/services/`, area tests | keep; `disbot/cogs/settings_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes, except explicit findings. 2. **Useful commands discoverable?** Panel entrypoints are; hidden/power shortcuts rely on typed/panel flows and classification needs FIND-B04. 3. **Merge/hide?** Only `/setup-hub` is an explicit hide-legacy candidate. 4. **Wrong subsystem?** None established. 5. **Service overlap?** Composition is intentional; no merger recommended. 6. **Components consistent?** Generally yes; domain selectors remain canonical. 7. **Dynamic and permission-safe?** Resource workflows resolve live guild resources and command/callback checks. 8. **Names clear?** Mostly; FIND-B06 identifies channel ambiguity. 9. **Missing actions?** None promoted; see Future opportunities. 10. **Gate-consistent?** Yes. 11. **Implementation vs future?** Implementation session handles unblocked findings; gated work stays with its named lane.

## diagnostic

### Subsystem record

1. **subsystem_key** — `diagnostic`.
2. **owning_cog** — `disbot/cogs/diagnostic_cog.py`.
3. **owning_services** — `disbot/services/diagnostics_service.py`; see service records below.
4. **hub_placement** — top_level Platform / Diagnostics hub.
5. **help_routes** — Direct typed resolution uses `cogs/help/route.py`; Home/Advanced placement follows hub/subsystem metadata. Loaded-cog-only surfaces have no subsystem route.
6. **panel_entry** — `views/diagnostic/*`; catalogue detection is help-hook and/or curated `KNOWN_PANEL_COMMANDS` where applicable.
7. **settings_setup_routes** — Current settings/setup state is described by the settings audit; domain panels stay canonical and are linked rather than absorbed.
8. **governance_access** — intended tier `administrator`; execution remains protected by command checks, governance/callback checks, and central admission where applicable.
9. **placement_tier** — `top_level`; current placement is intentional except where a finding above says otherwise.
10. **overlap** — Server-management/settings/help compose this surface but do not own its domain mutation seams.
11. **protections** — `tests/unit/cogs/`, `tests/unit/views/`, `tests/unit/services/`, and `tests/unit/invariants/` area tests; registry/help/settings audits supply documentation pins.
12. **gaps_risks** — Applicable executive findings: none beyond composition findings.

#### Command records — `diagnostic` (47 enumerated)
| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `diagnostics` | diag | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:71` |
| `lifecycle` | lc | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:78` |
| `platform` | — | slash | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:131` |
| `list_commands_detailed` | listcmds | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:152` |
| `find_command` | findcmd | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:163` |
| `validate_json_files` | validatejson | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:198` |
| `check_database` | checkdb | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:205` |
| `diagnostic_bot_status` | diag_status | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:216` |
| `latency` | ping | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:223` |
| `system_info` | sysinfo | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:230` |
| `query_logs` | querylogs | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:241` |
| `recent_errors` | errors | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:248` |
| `test_notification` | testnotify | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:255` |
| `platform` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:269` |
| `platform status` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:288` |
| `platform setup-readiness` | readiness, ready | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:294` |
| `platform anchors` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:313` |
| `platform identity` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:319` |
| `platform runtime` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:336` |
| `platform health` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:342` |
| `platform startup` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:364` |
| `platform findings` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:391` |
| `platform lifecycle` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:423` |
| `platform caches` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:429` |
| `platform locks` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:435` |
| `platform tasks` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:441` |
| `platform views` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:447` |
| `platform slow` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:453` |
| `platform automation` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:459` |
| `platform sessions` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:474` |
| `platform schemas` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:488` |
| `platform settings-registry` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:494` |
| `platform setting` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:500` |
| `platform customization` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:514` |
| `platform provisioning` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:520` |
| `platform participation-schemas` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:526` |
| `platform resource-requirements` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:532` |
| `platform bindings` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:538` |
| `platform resources` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:544` |
| `platform flags` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:550` |
| `platform flag` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:556` |
| `platform migrations` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:579` |
| `platform consistency` | — | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:585` |
| `platform command-access` | commandaccess | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:597` |
| `platform access` | whyhere | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:623` |
| `platform cleanup-preview` | cleanuppreview, cleanup-policy | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:647` |
| `platform counting-health` | countinghealth | prefix | `disbot/cogs/diagnostic_cog.py` | admin | `primary_entrypoint` | Home→hub→panel | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/diagnostic_cog.py:678` |


#### Panel/view record

1. **view** — `views/diagnostic/*`.
2. **entry** — command table entrypoint/help hook or parent-panel button.
3. **preset** — closest preset is `Platform Manager Panel`; current shape generally conforms, subject to listed findings.
4. **components** — source-owned buttons/selects/modals; guild resources are selected dynamically in role/channel/settings/setup flows.
5. **navigation** — shared HubView/PersistentView/navigation helpers where the panel exists; Help and setup preserve anchors; no panel for bootstrap admission.
6. **lifecycle_safety** — mutating domain panels re-check authority through command/callback/service seams; callback deferral and terminal-state behavior remain area-test concerns.
7. **multiselect_fit** — existing selectors are appropriate; no new conversion is recommended by this mapping.
8. **copy_consistency** — copy matches the current command family except explicit legacy/setup and naming findings.
9. **visibility** — open-time tier checks exist; Help's effective-access mismatch is FIND-B01.
10. **reuse** — shared panel bases/selectors are used except legacy/local paginator primitives noted by source; no runtime change proposed.
11. **consistency_gaps** — see the subsystem's `gaps_risks` and executive findings.

#### Service/helper/workflow records

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `disbot/services/diagnostics_service.py` | Canonical domain/read-model seam named above | owning cog/views; grep-verified area consumers | mixed; domain mutation services are audited, projection/read models are read-only | none established by this mapping | composition overlap only | domain-specific | diagnostics/logging where registered | `tests/unit/services/`, area tests | keep; `disbot/cogs/diagnostic_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes, except explicit findings. 2. **Useful commands discoverable?** Panel entrypoints are; hidden/power shortcuts rely on typed/panel flows and classification needs FIND-B04. 3. **Merge/hide?** Only `/setup-hub` is an explicit hide-legacy candidate. 4. **Wrong subsystem?** None established. 5. **Service overlap?** Composition is intentional; no merger recommended. 6. **Components consistent?** Generally yes; domain selectors remain canonical. 7. **Dynamic and permission-safe?** Resource workflows resolve live guild resources and command/callback checks. 8. **Names clear?** Mostly; FIND-B06 identifies channel ambiguity. 9. **Missing actions?** None promoted; see Future opportunities. 10. **Gate-consistent?** Yes. 11. **Implementation vs future?** Implementation session handles unblocked findings; gated work stays with its named lane.

## help

### Subsystem record

1. **subsystem_key** — `help`.
2. **owning_cog** — `disbot/cogs/help_cog.py`.
3. **owning_services** — `disbot/cogs/help/route.py`; see service records below.
4. **hub_placement** — top_level Help front door; self-subsystem omitted from Home row.
5. **help_routes** — Direct typed resolution uses `cogs/help/route.py`; Home/Advanced placement follows hub/subsystem metadata. Loaded-cog-only surfaces have no subsystem route.
6. **panel_entry** — HelpPanelView / HelpCategoryView — `cogs/help_cog.py`; catalogue detection is help-hook and/or curated `KNOWN_PANEL_COMMANDS` where applicable.
7. **settings_setup_routes** — Current settings/setup state is described by the settings audit; domain panels stay canonical and are linked rather than absorbed.
8. **governance_access** — intended tier `user`; execution remains protected by command checks, governance/callback checks, and central admission where applicable.
9. **placement_tier** — `top_level`; current placement is intentional except where a finding above says otherwise.
10. **overlap** — Server-management/settings/help compose this surface but do not own its domain mutation seams.
11. **protections** — `tests/unit/cogs/`, `tests/unit/views/`, `tests/unit/services/`, and `tests/unit/invariants/` area tests; registry/help/settings audits supply documentation pins.
12. **gaps_risks** — Applicable executive findings: FIND-B01, FIND-B08.

#### Command records — `help` (2 enumerated)
| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `help` | hilfe | prefix | `disbot/cogs/help_cog.py` | user | `primary_entrypoint` | Home→hub→panel | Help surface | yes | yes | — | yes | keep | `disbot/cogs/help_cog.py:636` |
| `help` | — | slash | `disbot/cogs/help_cog.py` | user | `primary_entrypoint` | Home→hub→panel | Help surface | yes | yes | — | yes | keep | `disbot/cogs/help_cog.py:720` |


#### Panel/view record

1. **view** — HelpPanelView / HelpCategoryView — `cogs/help_cog.py`.
2. **entry** — command table entrypoint/help hook or parent-panel button.
3. **preset** — closest preset is `User Navigation Hub`; current shape generally conforms, subject to listed findings.
4. **components** — source-owned buttons/selects/modals; guild resources are selected dynamically in role/channel/settings/setup flows.
5. **navigation** — shared HubView/PersistentView/navigation helpers where the panel exists; Help and setup preserve anchors; no panel for bootstrap admission.
6. **lifecycle_safety** — mutating domain panels re-check authority through command/callback/service seams; callback deferral and terminal-state behavior remain area-test concerns.
7. **multiselect_fit** — existing selectors are appropriate; no new conversion is recommended by this mapping.
8. **copy_consistency** — copy matches the current command family except explicit legacy/setup and naming findings.
9. **visibility** — open-time tier checks exist; Help's effective-access mismatch is FIND-B01.
10. **reuse** — shared panel bases/selectors are used except legacy/local paginator primitives noted by source; no runtime change proposed.
11. **consistency_gaps** — see the subsystem's `gaps_risks` and executive findings.

#### Service/helper/workflow records

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `disbot/cogs/help/route.py` | Canonical domain/read-model seam named above | owning cog/views; grep-verified area consumers | mixed; domain mutation services are audited, projection/read models are read-only | none established by this mapping | composition overlap only | domain-specific | diagnostics/logging where registered | `tests/unit/services/`, area tests | keep; `disbot/cogs/help_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes, except explicit findings. 2. **Useful commands discoverable?** Panel entrypoints are; hidden/power shortcuts rely on typed/panel flows and classification needs FIND-B04. 3. **Merge/hide?** Only `/setup-hub` is an explicit hide-legacy candidate. 4. **Wrong subsystem?** None established. 5. **Service overlap?** Composition is intentional; no merger recommended. 6. **Components consistent?** Generally yes; domain selectors remain canonical. 7. **Dynamic and permission-safe?** Resource workflows resolve live guild resources and command/callback checks. 8. **Names clear?** Mostly; FIND-B06 identifies channel ambiguity. 9. **Missing actions?** None promoted; see Future opportunities. 10. **Gate-consistent?** Yes. 11. **Implementation vs future?** Implementation session handles unblocked findings; gated work stays with its named lane.

## ai

### Subsystem record

1. **subsystem_key** — `ai`.
2. **owning_cog** — `disbot/cogs/ai_cog.py`.
3. **owning_services** — `disbot/services/ai_gateway.py`; tool internals provisional(#639); see service records below.
4. **hub_placement** — Advanced/direct linked panel; not a mother hub.
5. **help_routes** — Direct typed resolution uses `cogs/help/route.py`; Home/Advanced placement follows hub/subsystem metadata. Loaded-cog-only surfaces have no subsystem route.
6. **panel_entry** — AIPlatformPanelView + `views/ai/*`; catalogue detection is help-hook and/or curated `KNOWN_PANEL_COMMANDS` where applicable.
7. **settings_setup_routes** — Current settings/setup state is described by the settings audit; domain panels stay canonical and are linked rather than absorbed.
8. **governance_access** — intended tier `administrator`; execution remains protected by command checks, governance/callback checks, and central admission where applicable.
9. **placement_tier** — `cross_linked`; current placement is intentional except where a finding above says otherwise.
10. **overlap** — Server-management/settings/help compose this surface but do not own its domain mutation seams.
11. **protections** — `tests/unit/cogs/`, `tests/unit/views/`, `tests/unit/services/`, and `tests/unit/invariants/` area tests; registry/help/settings audits supply documentation pins.
12. **gaps_risks** — Applicable executive findings: FIND-B09.

#### Command records — `ai` (22 enumerated)
| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `ai` | — | prefix | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:365` |
| `ai status` | — | prefix | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:371` |
| `ai readiness` | — | prefix | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:379` |
| `ai settings` | — | prefix | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:409` |
| `ai why-no-response` | — | prefix | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:417` |
| `ai policy` | — | prefix | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:460` |
| `ai diagnostics` | — | prefix | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:498` |
| `ai providers` | — | prefix | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:503` |
| `ai routing` | — | prefix | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:508` |
| `aimenu` | — | prefix | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:517` |
| `ai forget` | — | prefix | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:523` |
| `ai support-report` | — | prefix | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:551` |
| `ai status` | — | slash | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:581` |
| `ai readiness` | — | slash | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:595` |
| `ai diagnostics` | — | slash | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:626` |
| `ai providers` | — | slash | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:637` |
| `ai routing` | — | slash | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:648` |
| `ai forget` | — | slash | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:663` |
| `ai support-report` | — | slash | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:692` |
| `ai policy` | — | slash | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:719` |
| `ai settings` | — | slash | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:758` |
| `aimenu` | — | slash | `disbot/cogs/ai_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/ai_cog.py:775` |


#### Panel/view record

1. **view** — AIPlatformPanelView + `views/ai/*`.
2. **entry** — command table entrypoint/help hook or parent-panel button.
3. **preset** — closest preset is `Platform Manager Panel`; current shape generally conforms, subject to listed findings.
4. **components** — source-owned buttons/selects/modals; guild resources are selected dynamically in role/channel/settings/setup flows.
5. **navigation** — shared HubView/PersistentView/navigation helpers where the panel exists; Help and setup preserve anchors; no panel for bootstrap admission.
6. **lifecycle_safety** — mutating domain panels re-check authority through command/callback/service seams; callback deferral and terminal-state behavior remain area-test concerns.
7. **multiselect_fit** — existing selectors are appropriate; no new conversion is recommended by this mapping.
8. **copy_consistency** — copy matches the current command family except explicit legacy/setup and naming findings.
9. **visibility** — open-time tier checks exist; Help's effective-access mismatch is FIND-B01.
10. **reuse** — shared panel bases/selectors are used except legacy/local paginator primitives noted by source; no runtime change proposed.
11. **consistency_gaps** — see the subsystem's `gaps_risks` and executive findings.

#### Service/helper/workflow records

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `disbot/services/ai_gateway.py` | Canonical domain/read-model seam named above | owning cog/views; grep-verified area consumers | mixed; domain mutation services are audited, projection/read models are read-only | none established by this mapping | composition overlap only | domain-specific | diagnostics/logging where registered | `tests/unit/services/`, area tests | keep; `disbot/cogs/ai_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes, except explicit findings. 2. **Useful commands discoverable?** Panel entrypoints are; hidden/power shortcuts rely on typed/panel flows and classification needs FIND-B04. 3. **Merge/hide?** Only `/setup-hub` is an explicit hide-legacy candidate. 4. **Wrong subsystem?** None established. 5. **Service overlap?** Composition is intentional; no merger recommended. 6. **Components consistent?** Generally yes; domain selectors remain canonical. 7. **Dynamic and permission-safe?** Resource workflows resolve live guild resources and command/callback checks. 8. **Names clear?** Mostly; FIND-B06 identifies channel ambiguity. 9. **Missing actions?** None promoted; see Future opportunities. 10. **Gate-consistent?** Yes. 11. **Implementation vs future?** Implementation session handles unblocked findings; gated work stays with its named lane.

## setup

### Subsystem record

1. **subsystem_key** — `none — loaded cog only`.
2. **owning_cog** — `disbot/cogs/setup_cog.py`.
3. **owning_services** — `disbot/services/setup_sections.py`; see service records below.
4. **hub_placement** — none — loaded cog only; linked from server-management/setup flows.
5. **help_routes** — Direct typed resolution uses `cogs/help/route.py`; Home/Advanced placement follows hub/subsystem metadata. Loaded-cog-only surfaces have no subsystem route.
6. **panel_entry** — Setup wizard views — `views/setup/*`; catalogue detection is help-hook and/or curated `KNOWN_PANEL_COMMANDS` where applicable.
7. **settings_setup_routes** — Current settings/setup state is described by the settings audit; domain panels stay canonical and are linked rather than absorbed.
8. **governance_access** — intended tier `administrator/delegated setup admin`; execution remains protected by command checks, governance/callback checks, and central admission where applicable.
9. **placement_tier** — `legacy`; current placement is intentional except where a finding above says otherwise.
10. **overlap** — Server-management/settings/help compose this surface but do not own its domain mutation seams.
11. **protections** — `tests/unit/cogs/`, `tests/unit/views/`, `tests/unit/services/`, and `tests/unit/invariants/` area tests; registry/help/settings audits supply documentation pins.
12. **gaps_risks** — Applicable executive findings: FIND-B05, FIND-B07.

#### Command records — `setup` (10 enumerated)
| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `setup` | — | prefix | `disbot/cogs/setup_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/setup_cog.py:81` |
| `setup` | — | slash | `disbot/cogs/setup_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/setup_cog.py:102` |
| `setup-hub` | — | slash | `disbot/cogs/setup_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/setup_cog.py:120` |
| `setup-depth` | — | slash | `disbot/cogs/setup_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/setup_cog.py:188` |
| `setup-skip` | — | slash | `disbot/cogs/setup_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/setup_cog.py:267` |
| `setup-unskip` | — | slash | `disbot/cogs/setup_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/setup_cog.py:290` |
| `setup-reset` | — | slash | `disbot/cogs/setup_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/setup_cog.py:366` |
| `setup-delegate` | — | slash | `disbot/cogs/setup_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/setup_cog.py:440` |
| `setup-undelegate` | — | slash | `disbot/cogs/setup_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/setup_cog.py:469` |
| `setup-status` | — | slash | `disbot/cogs/setup_cog.py` | admin | `primary_entrypoint` | Advanced / typed | dedicated panel | yes | yes | — | yes | keep | `disbot/cogs/setup_cog.py:493` |


#### Panel/view record

1. **view** — Setup wizard views — `views/setup/*`.
2. **entry** — command table entrypoint/help hook or parent-panel button.
3. **preset** — closest preset is `Setup Wizard Page`; current shape generally conforms, subject to listed findings.
4. **components** — source-owned buttons/selects/modals; guild resources are selected dynamically in role/channel/settings/setup flows.
5. **navigation** — shared HubView/PersistentView/navigation helpers where the panel exists; Help and setup preserve anchors; no panel for bootstrap admission.
6. **lifecycle_safety** — mutating domain panels re-check authority through command/callback/service seams; callback deferral and terminal-state behavior remain area-test concerns.
7. **multiselect_fit** — existing selectors are appropriate; no new conversion is recommended by this mapping.
8. **copy_consistency** — copy matches the current command family except explicit legacy/setup and naming findings.
9. **visibility** — open-time tier checks exist; Help's effective-access mismatch is FIND-B01.
10. **reuse** — shared panel bases/selectors are used except legacy/local paginator primitives noted by source; no runtime change proposed.
11. **consistency_gaps** — see the subsystem's `gaps_risks` and executive findings.

#### Service/helper/workflow records

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `disbot/services/setup_sections.py` | Canonical domain/read-model seam named above | owning cog/views; grep-verified area consumers | mixed; domain mutation services are audited, projection/read models are read-only | none established by this mapping | composition overlap only | domain-specific | diagnostics/logging where registered | `tests/unit/services/`, area tests | keep; `disbot/cogs/setup_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes, except explicit findings. 2. **Useful commands discoverable?** Panel entrypoints are; hidden/power shortcuts rely on typed/panel flows and classification needs FIND-B04. 3. **Merge/hide?** Only `/setup-hub` is an explicit hide-legacy candidate. 4. **Wrong subsystem?** None established. 5. **Service overlap?** Composition is intentional; no merger recommended. 6. **Components consistent?** Generally yes; domain selectors remain canonical. 7. **Dynamic and permission-safe?** Resource workflows resolve live guild resources and command/callback checks. 8. **Names clear?** Mostly; FIND-B06 identifies channel ambiguity. 9. **Missing actions?** None promoted; see Future opportunities. 10. **Gate-consistent?** Yes. 11. **Implementation vs future?** Implementation session handles unblocked findings; gated work stays with its named lane.

## bootstrap_access

### Subsystem record

1. **subsystem_key** — `none — loaded cog only`.
2. **owning_cog** — `disbot/cogs/bootstrap_access_cog.py`.
3. **owning_services** — `disbot/services/setup_access.py`; see service records below.
4. **hub_placement** — none — loaded cog only; internal admission guard.
5. **help_routes** — Direct typed resolution uses `cogs/help/route.py`; Home/Advanced placement follows hub/subsystem metadata. Loaded-cog-only surfaces have no subsystem route.
6. **panel_entry** — none; catalogue detection is help-hook and/or curated `KNOWN_PANEL_COMMANDS` where applicable.
7. **settings_setup_routes** — Current settings/setup state is described by the settings audit; domain panels stay canonical and are linked rather than absorbed.
8. **governance_access** — intended tier `internal`; execution remains protected by command checks, governance/callback checks, and central admission where applicable.
9. **placement_tier** — `internal`; current placement is intentional except where a finding above says otherwise.
10. **overlap** — Server-management/settings/help compose this surface but do not own its domain mutation seams.
11. **protections** — `tests/unit/cogs/`, `tests/unit/views/`, `tests/unit/services/`, and `tests/unit/invariants/` area tests; registry/help/settings audits supply documentation pins.
12. **gaps_risks** — Applicable executive findings: none beyond composition findings.

#### Command records — `bootstrap_access` (0 enumerated)
| command | aliases | kind | cog | audience | surface_class | help_path | panel_path | right_panel | service_ok | duplicates | gov_ok | verdict | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|


#### Panel/view record

1. **view** — none.
2. **entry** — command table entrypoint/help hook or parent-panel button.
3. **preset** — closest preset is `none`; current shape generally conforms, subject to listed findings.
4. **components** — source-owned buttons/selects/modals; guild resources are selected dynamically in role/channel/settings/setup flows.
5. **navigation** — shared HubView/PersistentView/navigation helpers where the panel exists; Help and setup preserve anchors; no panel for bootstrap admission.
6. **lifecycle_safety** — mutating domain panels re-check authority through command/callback/service seams; callback deferral and terminal-state behavior remain area-test concerns.
7. **multiselect_fit** — existing selectors are appropriate; no new conversion is recommended by this mapping.
8. **copy_consistency** — copy matches the current command family except explicit legacy/setup and naming findings.
9. **visibility** — open-time tier checks exist; Help's effective-access mismatch is FIND-B01.
10. **reuse** — shared panel bases/selectors are used except legacy/local paginator primitives noted by source; no runtime change proposed.
11. **consistency_gaps** — see the subsystem's `gaps_risks` and executive findings.

#### Service/helper/workflow records

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `disbot/services/setup_access.py` | Canonical domain/read-model seam named above | owning cog/views; grep-verified area consumers | mixed; domain mutation services are audited, projection/read models are read-only | none established by this mapping | composition overlap only | domain-specific | diagnostics/logging where registered | `tests/unit/services/`, area tests | keep; `disbot/cogs/bootstrap_access_cog.py:1` |

#### Per-cog quality checklist

1. **Right hub/tier?** Yes, except explicit findings. 2. **Useful commands discoverable?** Panel entrypoints are; hidden/power shortcuts rely on typed/panel flows and classification needs FIND-B04. 3. **Merge/hide?** Only `/setup-hub` is an explicit hide-legacy candidate. 4. **Wrong subsystem?** None established. 5. **Service overlap?** Composition is intentional; no merger recommended. 6. **Components consistent?** Generally yes; domain selectors remain canonical. 7. **Dynamic and permission-safe?** Resource workflows resolve live guild resources and command/callback checks. 8. **Names clear?** Mostly; FIND-B06 identifies channel ambiguity. 9. **Missing actions?** None promoted; see Future opportunities. 10. **Gate-consistent?** Yes. 11. **Implementation vs future?** Implementation session handles unblocked findings; gated work stays with its named lane.

## Composition architecture

### §3.4-style composition records

| service | owner_of | consumers | mutation | bypasses | overlap | cache_events | observability | tests | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `disbot/cogs/help_cog.py` + `disbot/cogs/help/route.py` | Help rendering, shared route resolution/opening | prefix/slash Help + dropdown | read-only | direct render paths bypass projection (FIND-B01) | dedicated cog panels | none | fallback logging | `tests/unit/cogs/test_help*` | blocked-by-gate(Adaptive P1C/Lane 8) |
| `disbot/utils/hub_registry.py` | ten immutable mother-hub declarations | Help/hub views/tests | pure | none found | subsystem parent metadata pinned to agree | versioned metadata | validation errors | hub registry/invariant tests | keep |
| `disbot/utils/subsystem_registry.py` | 29 subsystem identities, tiers, capabilities, parent placement | governance, Help, ledgers, setup | pure/frozen | none found | hub registry is complementary | registry version | validation errors | registry/invariant tests | keep |
| `disbot/core/runtime/command_surface_ledger.py` | live prefix/slash command inventory + classifications | Help/customization/diagnostics | read-only snapshot | default classifications lose semantic precision (FIND-B04) | Discord hidden + curated catalogue | cached snapshot | diagnostics provider | `tests/unit/runtime/test_command_surface_ledger.py` | reorganize |
| `disbot/services/customization_catalogue.py` | composed settings/panels/help-hooks/diagnostics catalogue | diagnostics/platform surfaces | read-only snapshot | curated/regex fallback required by incomplete declarations | ledger + registry composition | cached catalogue | diagnostics provider | `tests/unit/services/test_customization_catalogue.py` | reorganize |
| `disbot/services/access_projection.py` | effective access-map read model | adaptive access/platform consumers | read-only | Help does not consume it (FIND-B01) | routing/governance/access inputs | none | findings/providers | access-projection tests | blocked-by-gate(Adaptive P1C) |
| `disbot/services/command_routing.py` | per-channel subsystem routing resolution | bootstrap admission/setup/access projection | read-only + canonical routed writes elsewhere | none found | command access is command-granular complement | cache-aware | diagnostics/audit seams | routing tests | keep |
| `disbot/services/command_access_service.py` | per-channel command admission policy/cache | bootstrap admission/settings editor/access projection | read/write service | direct DB bypass prohibited by contract | routing is subsystem-granular complement | cache invalidation | audit/logging | command-access tests | keep |
| `disbot/cogs/bootstrap_access_cog.py` | first-loaded centralized prefix admission guard | every prefix invocation | listener/check-driven | order is load-bearing | governance/routing/access compose decision | none | denial/routing findings | bootstrap/access tests | keep |

### Help filter-by-render-path matrix — delta since #627

No source change to Help rendering occurred between audit #627 and HEAD. Merged #639 changed AI internals only; live #642 proposes characterization tests but is not merged. Therefore the matrix delta is **none**, while ownership/status changed to `blocked-by-gate(Lane 8|Adaptive P1C)`.

| Help render path | live cog/enabled/Discord-hidden | ledger hidden/legacy | member tier | governance visibility | command routing | command access | capability/can-run | delta since #627 |
|---|---|---|---|---|---|---|---|---|
| Home overview/hub buttons | partial/live static hub list | no | yes, hub floor | no | no | no | no | none |
| Advanced subsystem browser | live registered subsystems | generic command embed only | yes | yes | no | no | no | none |
| Typed/dropdown hub route | live builder/fallback | builder-dependent | route/open context only | no target authorization | no | no | callback/command only | none |
| Typed/dropdown subsystem route | live cog required | fallback generic embed yes; dedicated hook varies | no consistent target authorization | no | no | no | callback/command only | none |
| Single-command route | live command lookup | no | no | no | no | no | no `can_run` | none |

## Cross-boundary observations

* Agent A subsystems inherit FIND-B01/FIND-B04 composition behavior, but their commands/panels are intentionally not mapped here. Evidence: `disbot/cogs/help/route.py:302-330`, `disbot/core/runtime/command_surface_ledger.py:251-264`.
* `role` is owned by Agent B but is a primary child of Agent A's `community` hub; this is intentional cross-boundary navigation, not shared subsystem ownership. Evidence: `disbot/utils/subsystem_registry.py:235-259`, `disbot/utils/hub_registry.py:206-218`.

## Future opportunities

FIND-B10 [4 future opportunity] After existing gates/lanes settle, consider a generated operator-facing explanation of why a command is visible but unavailable, derived only from the canonical access projection.
  evidence: disbot/services/access_projection.py:555 · `project_access_map`; docs/current-state.md:1-20 · Adaptive P1C queue
  verified-by: read source + current-state
  verdict: future-opportunity

## Open owner questions

### Q-B01 — Admin tier alignment

Which contract should win? **A.** Make registry/Admin Help placement administrator-visible while retaining owner-only checks for dangerous actions; **B.** make the entire Admin panel owner-only; **C.** keep the mismatch intentionally and document it. Proposed: **A**.

### Q-B02 — Channel command namespace

How should globally generic channel commands evolve? **A.** preserve typed compatibility but add a `channel` group and classify old names hidden legacy; **B.** retain current top-level names; **C.** panel-first only, with old names hidden legacy. Proposed: **A**.

## Verification log

* Read the binding standard imported from live PR #641, both cornerstone audits, current-state, all requested maps/folios/trackers, and the relevant source.
* Live GitHub API: open PRs #638/#640/#641/#642; #639 merged at `2026-06-09T23:55:54Z`. `gh` is unavailable and there is no git remote, so API/raw GitHub were used.
* `python3.10` was not directly usable (inactive shim; activating 3.10.20 lacked `yaml`); substituted Python **3.12.13** through a temporary `python3.10` wrapper, per the standard.
* Ran `python scripts/context_map.py <path>` for 22 deeply inspected files: the 14 scoped cogs/help route, both registries, ledger, catalogue, access projection, routing, and command access.
* AST enumeration command: `python /tmp/gen_tables.py` — 157 scoped command rows: admin 10, moderation 9, cleanup 7, logging 6, proof_channel 5, role 14, channel 15, server_management 2, settings 3, diagnostic 47, help 2, ai 22, setup 10, bootstrap_access 0.
* Registry enumeration command: `PYTHONPATH=disbot python - <<'PY' ... SUBSYSTEMS/HUBS ... PY` — re-confirmed scoped tiers/parents and the 10 hubs.
* Final checks: strict docs reports only the two expected open-#641 reachability orphans; full quality passes black/isort/ruff/mypy and 8,457 tests, with only the same doc-orphan pin failing. Details are in the session log and PR test plan.

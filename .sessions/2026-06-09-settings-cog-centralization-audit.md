# Settings cog centralization audit — 2026-06-09

## Summary

Completed a documentation-only, source-grounded audit of the existing Settings Manager,
scalar registry/resolution/mutation/audit stack, setup overlap, separate configuration
domains, subsystem coverage, display behavior, and structured editability. The durable
audit and phased roadmap lives at
`docs/planning/settings-cog-centralization-audit-2026-06-09.md`. Added two owner questions
for AI partial-projection ownership and BTD6 command-only pointer classification.

## Files read

- Binding workflow/orientation/current-state docs requested by the session prompt.
- Settings/setup/platform docs, architecture/ownership/runtime/capability contracts, and
  platform consistency ledger.
- Core settings stack: subsystem schema, registry, resolution, mutation, KV/audit DB,
  migration 029, SettingsCog, all `views/settings/`, and all `utils/settings_keys/`.
- All schema-bearing cog modules and relevant cog/panel/service consumers.
- Setup operations/drafts/change-plan and setup sections; AI policy/orchestration,
  moderation config, governance, logging, command access/routing, role, participation,
  BTD6 pointer, and binding/provisioning owners.
- Settings/setup/invariant/view tests relevant to the claims in the audit.

## Files changed

- `docs/planning/settings-cog-centralization-audit-2026-06-09.md` — new durable audit and roadmap.
- `docs/owner/maintainer-question-router.md` — Q-0063 and Q-0064.
- `.sessions/2026-06-09-settings-cog-centralization-audit.md` — this journal.

`docs/current-state.md` was not changed because this session did not change runtime truth.

## Important findings

- The central scalar stack already exists and is strong: 36 declared settings across 9
  settings-bearing subsystems, clean registry findings, canonical typed/audited mutation,
  canonical resolution/defaults, and metadata-driven editors.
- The Settings hub uses `SUBSYSTEMS`, not settings registry entries, for discovery. It
  intentionally lists empty groups and silently truncates 28 subsystem identities to 25
  Discord options.
- AI scalar mutation already projects seven guild-policy keys into `ai_guild_policy`;
  memory stays scalar and free-text instruction is unprojected. The best-effort partial
  projection is an important compatibility seam, not an unbridged source conflict.
- Separate config domains are legitimate and should remain separate mutation owners.
  Settings should centralize discovery/navigation, not persistence/writes.
- Structured editing already covers toggle/enum/preset/channel/role/reset. Avoidable text
  remains mainly in XP duplicate panels, generic numeric fallbacks, and command-only BTD6
  pointers. Authored instruction/template text remains justified.
- Live GitHub check found one open PR, #624, touching mining and shared status/ownership
  docs but not settings. Mining conclusions were marked concurrency-sensitive.

## Context-delta

### needed-not-pointed

- `docs/capability-authority.md` and `docs/health/platform-consistency-ledger.md`, reached
  from the settings orientation route, were needed to classify UI authorization and
  separate-domain ownership.
- `tests/unit/invariants/test_no_direct_settings_keys_writes.py` was essential for
  distinguishing intentional direct-KV exceptions from accidental bypasses.
- `services.ai_natural_language_policy.py` and the dedicated AI policy views were needed
  to verify the live AI policy source and the existing scalar-to-policy projection.

### pointed-not-needed

- No source route was wholly unnecessary, but the broad aspirational setup roadmap and
  operator preset document were useful only as expectation/drift references, not live
  truth.
- CodeGraph was requested and documented, but no CodeGraph MCP resources/templates were
  available in this environment.

### discovered-by-hand

- The first-25 truncation means the all-subsystems design is not merely noisy: it makes
  some groups unreachable from the Settings dropdown.
- The registry snapshot carries stringified type/default metadata and is used only for
  counts/discovery diagnostics; the editor dispatcher returns to live schemas.
- Seven generic AI settings project into typed guild policy after commit, while three
  settings intentionally follow other paths; projection failure is best-effort and can
  leave legacy KV committed while typed policy remains unchanged.
- Economy/logging/XP expose channel-valued legacy scalar pointers overlapping the binding
  lane at different migration stages.

## Verification performed

- Queried GitHub API for all open PRs and inspected #624 file paths.
- Verified required files and source routes exist.
- Attempted required `python3.10 scripts/context_map.py <path>` for 22 deeply inspected
  Python files; the default pyenv did not expose 3.10, and explicitly selecting 3.10 then
  lacked PyYAML. Re-ran all 22 successfully with the available `python` environment.
- Imported/registered all ten schema modules with safe dummy environment values and built
  registry: 36 entries, 10 schemas, zero registry findings.
- Enumerated 28 subsystem manifest entries and traced the hub's 25-option cap.
- Searched direct KV reads/writes and verified exceptions against the AST invariant.
- Ran targeted settings/docs checks recorded in the final response.

## Recommended next step

Run an Opus Phase 0 revision session after Q-0063/Q-0064 are answered. It should specify
the actionable configuration-group catalogue and exact failing target tests, review and
diagnose the AI partial-projection seam before exposure, and preserve all separate
mutation-domain owners. Then use Sonnet for
Phase 1 discovery/display correctness.

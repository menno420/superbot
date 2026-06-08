# 2026-06-08 — Adaptive Setup Phase 0: Q-0026 identity repair + P0B contracts

**Task:** Start implementing the Adaptive Setup/Access/Routine platform
(`docs/planning/adaptive-setup-access-routine-platform-2026-06-08.md`) from planning into
safe foundations. The plan's own batch table sequences P0A (Q-0026) → P0B (Opus contract)
→ P1A (projection service); this session delivered **P0A in code + P0B in docs**, leaving
the projection *service* to P1A with a precise route.

**Branch:** `claude/compassionate-feynman-x9hlb` · no open PRs at start (clean slate;
HEAD = #586 planning-doc merge).

## Shipped

1. **Q-0026 identity repair (P0A) — code + tests.**
   - `cog_name_to_subsystem` now does a two-pass CamelCase → snake_case conversion
     (`disbot/core/runtime/command_surface_ledger.py`). Acronym runs stay collapsed
     (`BTD6Cog`→`btd6`, `AICog`→`ai`).
   - Renamed the subsystem **key** `servermanagement` → `server_management` across the
     identity surfaces only: `SUBSYSTEMS`, `HUBS`, `KNOWN_PANEL_COMMANDS`, the
     `PersistentView.SUBSYSTEM` classvar, the hub custom_ids (`server_management:*`), and
     the `panel_manager.get_or_render_panel` anchor key. The user-facing
     `!servermanagement` command + aliases + `/server-management` slash + the
     `entry_points` list are **command names**, not keys — left unchanged.
   - **Bonus root-cause fix:** the same conversion repaired a *latent* collapse —
     `ProofChannelCog`→`proof_channel` and `FourTwentyCog`→`four_twenty` were already
     snake_case registry keys but `cog_name_to_subsystem` had been silently orphaning them
     (returning `None`). They now resolve; catalogue/ledger findings only shrink.
   - Added regression tests pinning the snake_case **output contract** so a future
     multi-word subsystem can't regress (`test_multiword_cog_names_convert_to_snake_case`,
     `test_acronym_cog_names_stay_collapsed`, `test_snake_case_is_the_output_contract`,
     `test_build_ledger_resolves_multiword_subsystem_cog`).

2. **P0B contracts (docs).**
   - **Direct-vs-draft mutation boundary** → binding rule in `docs/ownership.md`
     § "Direct vs. draft mutation lanes" (elevated from the planning doc's §5 panel map).
   - **Phase 0 access read-model contract** → planning doc **§16**: service family,
     composition **precedence** (the 7-axis order, short-circuit on first deny), the
     decision/`LockedReason` schema that **reuses** `command_access.DecisionReason`/
     `DecisionSource` (no second permission system), Help Preview simulation limits, drift
     providers, the **P0C drift selection** (role-threshold direct writes), invalidation,
     and the negative-architecture guardrails P1A's tests must assert.
   - Doc reconciliation: server-management folio (the "adding a hub" gotcha was *wrong* —
     said keys collapse with no underscore), `current-state`, router Q-0026 (→ implemented)
     + Q-0016 forward-note, both doc-test-pinned maps (`help-command-surface-map`,
     `settings-customization-command-map`), settings folio pointer.

## Verification

- `python3.10 scripts/check_quality.py --full` → **8053 passed, 16 skipped** (black/isort/
  ruff + mypy + pytest).
- `python3.10 scripts/check_architecture.py --mode strict` → exit 0, 0 errors (only
  pre-existing WARNs).
- `python3.10 scripts/check_docs.py` → all checks passed; top-level docs still 16 ≤ ratchet.
- **Live boot** (test bot, `IDENTITY_CONTRACT_STRICT=true`): all 35 cogs loaded,
  `Identity-contract: clean (all four surfaces agree). STRICT=on.`, 303 command
  descriptions, 0 errored, no Traceback/CRITICAL.
- Identity grep: no stale `servermanagement` *key* remains in `disbot/` — the three
  surviving `"servermanagement"` literals are all legitimate command-name usages.

## Decisions worth remembering

- **Key vs. command name are different strings on purpose.** The subsystem key
  (`server_management`) ≠ the command (`servermanagement`), exactly like `economy` (key) vs
  `economymenu` (command). Renaming the command would be user-facing breakage with no
  identity benefit, so it stayed.
- **Custom_ids changed too (`server_management:*`).** Reasoning: after the key rename the
  old DB anchor (`subsystem="servermanagement"`) no longer resolves to the renamed view
  class, so an already-posted panel dies on restart *regardless* of custom_ids — there is
  no extra cost to also renaming them, and it keeps the view consistent with its documented
  `{SUBSYSTEM}:{action}` contract. No migration; the orphaned anchor self-heals and the
  panel re-posts on next `!servermanagement`.
- **No migration added.** A `panel_anchors` data migration would only matter if custom_ids
  were kept *and* the anchor row migrated (to preserve one test-bot panel across one
  restart) — over-engineering for a fresh-DB test bot. Documented instead.

## Safe defaults used (Q-0028–Q-0033)

Only read-only/contract work this session, so the defaults held without forcing a choice:
no committed profile catalogue (Q-0028); availability policy owns quiet mode (Q-0029);
snapshots required for compound/high-risk applies (Q-0030); ambiguous config queues Final
Review (Q-0031); no new command names reserved — Access Map/Help Preview stay behind staff
hubs (Q-0032); account links deferred (Q-0033).

## Next (ordered, grounded in the phased roadmap)

1. **P1A — Access Map projection service** (Sonnet): build the side-effect-free composed
   read model + tests per planning §16. No UI, no persistence, no editing.
2. **P0C — role-threshold writer normalization** (Sonnet): route the role panel's direct
   threshold DB writes through an audited `role_automation` seam (planning §16.5 +
   ownership.md drift note) before any profile/routine targets thresholds.
3. **P1B** — drift providers + locked-reason denial integration on top of P1A.
4. Gated/blocked: profile apply (Phase 3), Routine Engine (Phase 4), Personal Setup
   (Phase 5), AI drafts (Phase 6) — all wait on their named prerequisites.

## Context delta

- **Needed but not pointed to:** that `cog_name_to_subsystem` (the bug's home) is consumed
  by the **command-surface ledger AND the customization catalogue's `_walk_help_hooks`/
  `_walk_extras_panels`**, so the fix silently improves catalogue findings too — the
  context map showed importers but not that two of them re-call the function. Also that the
  hub's **panel-anchor key** (2nd arg of `get_or_render_panel`) is written to
  `panel_anchors.subsystem` (an identity surface), which isn't obvious from the cog.
- **Pointed to but didn't need:** the binding architecture/ownership/runtime trio and most
  subsystem folios beyond server-management — this was a narrow identity + read-model-
  contract session, not a layering change; the deep arch docs didn't change what I did.
- **Discovered by hand:** the `{SUBSYSTEM}:{action}` custom_id convention lives **only** in
  the `persistent_views.py` base-class docstring (not in any folio), and the fact that
  `four_twenty`/`proof_channel` were *already* snake_case keys silently orphaning — both
  reverse-engineered from source, now captured in the server-management folio "adding a hub"
  gotcha and planning §3.1.

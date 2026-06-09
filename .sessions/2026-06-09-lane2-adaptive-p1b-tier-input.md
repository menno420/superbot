# 2026-06-09 — Execution-plan Lane 2: tier-input + help_advertises_locked + denial copy

Parallel-session test by owner direction: this session (Agent 1) ran **Lane 2 only**
while Agent 2 ran Lane 3 (orchestration Phase 4 MVP) concurrently. Verified at start:
zero open PRs live, Lane 1 = #626 merged, Lane 2 first unchecked, working tree clean.
Stayed off Lane 3's surface (AI orchestration / BTD6 workflow files) — no conflict
arose; the lanes' files are disjoint.

## Shipped (PR #632, draft→ready per Q-0052)

- **Q-0045 option (b), the governance tier-input path**: `GovernanceContext.member_tier`
  declared-tier input; `_resolve_member_tier` prefers it **verbatim** (member derivation
  + ADR-008 role grants skipped — the caller declares the *effective* standing; invalid
  values ignored with a warning, never escalate/demote). Projection's governance axis
  consumes `AccessContext.member_tier`: member-less + declared tier evaluates instead of
  `unknown`, simulation labeled on the chain detail (§16.4).
- **`help_advertises_locked` drift provider** (`setup_diagnostics`): advertised-to-baseline
  = ledger-shown ∧ governance-visible at tier `user`; per-feature WARNING for routed-off
  advertised features; one guild-level finding per guild-wide command-access lock
  (disabled-mode ADVISORY / empty-selected-channels WARNING); `unknown` never flags;
  representative-channel evaluation (min allowed id) in selected mode.
- **Q-0036 denial-copy draft**: `_SAFE_TEXT` now covers the full §16.3 code union
  (+`capability_insufficient`, `quiet_mode`, `setup_stage_required`); full table in the
  PR #632 body for maintainer read-through. **Not live-wired** — wiring follows markup.

## Verification

Targeted suites 93 passed (new: 9 governance declared-tier, +4 projection, +11 provider) ·
broader sweep 884 passed · arch strict 0 errors · full CI mirror green before ready
(see PR checks). Read-only AST invariants untouched and green.

## Context delta

- **Needed but not pointed to:** *how live help filters*. The lane card pointed at the
  ledger/projection but the provider's correctness hinges on `cogs/help_cog.py` +
  `cogs/help/route.py` filtering through `resolve_visibility` per member — that's what
  makes "governance deny ⇒ not advertised ⇒ not drift" true and re-reads §16.8 item 6
  correctly (the tier path is needed to compute the **advertised** set, not to flag tier
  locks as drift). Also: the projection **short-circuits on a routing deny before its
  governance axis runs**, so the provider needs one up-front `get_visible_subsystems`
  call — not derivable from the lane card. Both now recorded on the plan (§16.8 item 6)
  and the scoreboard.
- **Discovered by hand:** `resolve_command_access` with `channel_id=None` in
  selected-channels mode denies `channel_not_allowed` — a naive guild-scope scan would
  false-positive every feature; hence the representative-allowed-channel evaluation.
  Decision chains on a deny do **not** include the help axis (short-circuit), so
  "advertised" must be read from the ledger owner directly, not from the chain.
- **Pointed to but didn't need:** §16.5's `configured_resource_missing`/`identity_mismatch`
  context (already-marked-covered; correctly skipped). The router Q-0036/Q-0045 entries
  were exactly sufficient — no owner question needed this session.

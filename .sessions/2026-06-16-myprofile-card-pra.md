# Session — myprofile PR A: read-only profile card (`/myprofile`)

> **Status:** `complete`

## Why

Second slice of this dispatch run (after the faucet/sink diagnostic, PR #937 merged). The live
▶ Next action: **myprofile PR A — the read-only profile card** (band-#930 decade queue slot 3,
`ready`; zero writes, turn-key). Plan: `docs/planning/myprofile-foundation-plan-2026-06-10.md`
§4.1. It surfaces the per-user participation platform (`participation_schema` + the typed read
accessors) that has been shipped-but-unexercised — XP is its only registrant.

## What shipped (this PR)

A schema-driven, read-only `/myprofile` (+ `!myprofile`) card showing the invoking user's
participation, subscriptions, preferences, and visibility across every subsystem that registered
a `ParticipationSchema` — each value labelled with its declared default (Q-0058 idiom). Zero
writes; owner-locked ephemeral.

- `disbot/views/profile/` (new package): `build_profile_embed(user, guild_id)` composes the
  typed accessors (`get_participation` / `is_subscribed` / `get_preference` / `get_visibility`)
  over `participation_schema.all_schemas()`; `ProfileHomeView(BaseView)` is the owner-locked
  ephemeral shell (read-only Refresh button for now) that PR B extends with the write controls.
  `preference_key(subsystem, name)` establishes the `"{subsystem}.{name}"` preference-key
  convention as the single source of truth for the PR A read and the PR B write.
- `cogs/utility_cog.py`: `/myprofile` (ephemeral, self-scoped, Q-0080 stranger-grade) +
  `!myprofile` (send_panel, owner-locked, cooldown). **Deviation from the plan (noted):** the
  command lives in the existing **UtilityCog** (→ already-registered `utility` subsystem) rather
  than a new `ProfileCog`. A new cog would map to a `profile` subsystem that doesn't exist
  (orphan-cog finding) or require a new SUBSYSTEMS identity entry — the exact "identity-surface
  ripple" the plan's §4.1 said to avoid by "reuse the existing utility subsystem". UtilityCog is
  the cleaner home; the views still live in `views/profile/`.
- `utils/subsystem_registry.py`: `myprofile` added to utility `entry_points` (declared command).
- `tests/unit/runtime/test_command_surface_ledger.py`: `"myprofile": None` added to the pinned
  `EXPECTED_SLASH_SURFACE` (the two-way slash-surface invariant).
- `tests/unit/views/test_profile_card.py`: per-schema composition · empty state · effective
  default (requires_optin → off) · unset-shows-default · owner-lock · **AST pin that PR A imports
  no `*mutation*` module** (the read-only invariant).

## Verification

`check_quality.py --full` green (9920 passed) · `check_architecture --mode strict` 0 errors ·
mypy clean. The PR's only red check is the born-red session gate (Q-0133), cleared by this card
being `complete`.

## Handoff (▶ next)

The next `ready` plan slice is **myprofile PR B — self-service writes** (the first UI consumer of
`ParticipationMutationPipeline`): subscription/participation/preference/visibility toggles, each
exactly one pipeline call, re-render from accessors. The `ProfileHomeView` shell + the
`preference_key` convention are in place for it. PR C (join-time onboarding) stays owner-gated.
The "gated subsystem" honesty label (`participation.enabled` flag) was deliberately deferred from
PR A (§4.1 didn't require it; the read already shows real stored values + defaults) — a candidate
PR B refinement via `feature_flags.is_enabled("participation.enabled", guild_id)`.

## 💡 Session idea (Q-0089)

**A `ParticipationSchema` ⇆ `EXPECTED_SLASH_SURFACE`/entry-points coherence guard.** This session
touched three coupled declarations for one feature — the slash-surface pin, the subsystem
`entry_points`, and (for owned subsystems) the participation schema. They are pinned independently;
nothing asserts that a command declared in a cog is *both* in its subsystem's `entry_points` **and**
classified in the surface ledger. A small AST invariant cross-checking "every non-hidden top-level
command ⇒ declared entry_point ⇒ ledger-classified" would catch the half-wired command (a real
recurring class — `undeclared_entry_points` findings exist precisely because people forget one leg).
Dedup-checked `docs/ideas/`: the command-surface ledger work exists but no cross-coherence guard
across the three declaration sites. Worth a small idea file.

## ⟲ Previous-session review (Q-0102)

The previous slice this run (the faucet/sink diagnostic, #937) hit the diagnostic_cog 800-LOC
ceiling and had to shave docstrings to land — a sign that cog grew past its decompose point. This
slice avoided the same trap by *choosing the host cog deliberately* (UtilityCog, with headroom)
rather than minting a new cog. The system lesson both reinforce: the 800-LOC cog ceiling is doing
its job as a pressure signal, but the *response* keeps being ad-hoc (shave text / pick a different
cog) — the durable fix is the `platform_*`-group-extraction idea from #937's log. Worth promoting
that idea to a plan before the *next* diagnostic subcommand forces it under time pressure.

## Doc audit (Q-0104)

`check_quality --full` green; arch 0; mypy clean. Did not add #937 or this PR to current-state
Recently-shipped (merged-PRs-only convention; ledger ratchet at 20 — next session reconciles both).
Repointed the live ▶ pointer to PR B in the #937 close-out already; this run's ▶ now reads "PR A
shipped pending merge → PR B next" (updated below in current-state). No new owner decisions (a
dispatched plan slice). Plan doc stays `plan` (PRs B/C remain).

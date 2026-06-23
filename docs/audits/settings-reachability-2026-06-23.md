# Settings-reachability — 2026-06-23

> **Status:** `audit` — the finding + exemption ledger for the settings half of the
> consolidation/discoverability audit
> ([brief](../planning/consolidation-discoverability-audit-brief-2026-06-23.md) §3.4). Emitted/checked by
> `scripts/check_settings_reachability.py` (the static guard) + `tests/unit/invariants/test_settings_reachability.py`
> (the CI ratchet). Source code + merged PRs win over this doc.

## The goal, made checkable

The audit's §3.4 terminal: *"every cog's settings reachable from the `!settings` hub — no per-cog
settings unreachable."* A subsystem's config surfaces in `!settings` via
`services.customization_catalogue.actionable_settings_groups()`, which includes it iff it is
**non-internal** and declares a `SubsystemSchema` with an actionable surface. So config is *centralized
+ reachable* exactly when the subsystem declares a schema and is non-internal.

That signal was previously only verifiable with a **live bot** (the catalogue needs loaded cogs; a static
`build_catalogue(None)` over-reports 41/41). This guard makes the same invariant **statically checkable**
— the settings analog of the `#1370` per-command reachability guard.

## Result (code-verified, 2026-06-23)

`check_settings_reachability` → **19 reachable · 3 exempt · 0 GAP**.

- **19 reachable** — every subsystem declaring a `SubsystemSchema` (`ai`, `automod`, `blackjack`, `btd6`,
  `cleanup`, `counters`, `deathmatch`, `economy`, `help`, `image_moderation`, `karma`, `logging`,
  `moderation`, `proof_channel`, `role`, `rps_tournament`, `security`, `welcome`, `xp`) is non-internal,
  so it auto-surfaces in the `!settings` hub. **Settings are already structurally centralized.**
- **0 genuine gaps.**

## The 3 exemptions (intentional domain-panel config)

These declare a `*.configure` capability but no `SubsystemSchema`. Their config is correctly **not** in the
centralized `!settings` schema hub — so they are reasoned allowlist entries
(`architecture_rules/settings_reachability_exceptions.yml`), not gaps:

| Subsystem | Capability | Why it's exempt (verified) |
|---|---|---|
| `counting` | `counting.game.configure` | Per-**channel** game enablement (which channels count, mode, reset) — a bespoke per-channel data model owned by the `!countingmenu` panel, not a guild-scalar setting that fits the `SubsystemSchema` → `!settings` model. |
| `chain` | `chain.game.configure` | Per-channel word-chain enablement, same shape as counting — owned by the `!chainmenu` panel. |
| `channel` | `channel.visibility.configure` | An administrator **action** (restrict/unrestrict a channel via the Channels panel), not stored guild config — there is nothing persistent to surface in `!settings`. |

## How to clear / change an entry

- **A new subsystem adds a `SubsystemSchema`** → it must be non-internal to be reachable; the guard flags
  a schema'd-but-`internal` subsystem as a gap (its config would be hidden).
- **A new subsystem grows a `*.configure` / `*.settings.*` capability** without a schema → the guard flags
  it as a gap until you either add a schema (centralize it) or add a reasoned allowlist entry.
- When a domain-panel case is genuinely centralized later (a real `SubsystemSchema` is added), remove its
  allowlist entry; `check_settings_reachability` then classifies it `reachable`.

Re-run `python3.10 scripts/check_settings_reachability.py` to confirm.

## Notes / caveats

- **Warn-first + disposable** (Q-0105). The static schema scan keys off `cogs/<sub>/schemas.py` declaring
  `SubsystemSchema(subsystem="…")`; it mirrors the live `actionable_settings_groups()` rule but cannot
  exercise the bot-dependent catalogue signals (`subsystems_missing_help_hook`, `undiscoverable_surfaces`)
  — those still want a **live-bot** build to fully verify. Confirm a flagged subsystem really lacks a
  Settings-hub surface in a live guild before centralizing it. Delete the guard if it proves unreliable
  over multiple sessions.

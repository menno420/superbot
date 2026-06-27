# Wire `cog_routing` to runtime enforcement (per-feature, per-channel commands)

> **Status:** `ideas` — capture only, **not a plan, not approval**. Source + the binding
> contracts win. Surfaced 2026-06-27 while adding the Command Access spine step (PR #1496).
> **Subsystem:** none (cross-cutting: command gate + setup wizard)

## The gap (verified)

The bot has a **per-feature, per-channel command toggle** system — `cog_routing` /
`command_routing_policy` — configurable in the advanced wizard (`!setupadvanced` → "Cog routing"
section + routing profiles). It resolves `channel → category → server → default-true`
(`services.command_routing.is_cog_enabled`). This is the literal **"allowed commands per channel."**

**It is not enforced.** A repo-wide trace of `is_cog_enabled` finds its only runtime consumers are:
- `services.access_projection` — explicitly **read-only** ("performs no writes"); the Access-Map
  *diagnostic* read model (axis 3 of 7).
- `services.setup_operations` — the "current value" **preview** when staging a routing op.

Neither live command gate consults it. The two enforced gates are:
- `cogs.bootstrap_access_cog._channel_guard` / `_slash_access_check` → `core.runtime.command_access`
  (Command Access: all/selected/disabled channels — axes 1+2).
- `bot1.py::_governance_guard` → `governance.resolve_command_policy` (subsystem visibility — axis 4).

So a `set_cog_routing` policy **saves + audits but changes no command's actual availability.** The
access-projection docstring even names where enforcement *would* sit — **axis 5 "availability — FUTURE
central resolver (§6.6) — not built."** This is an incomplete feature, not a regression.

## Why it matters

The owner asked for "allowed commands per channel" in setup (2026-06-27). PR #1496 shipped the
*enforced* coarse control (Command Access: limit the bot to chosen channels). The *fine-grained*
control the owner's phrasing most literally describes ("games only in #games") is this `cog_routing`
system — and surfacing it in the friendly wizard while it silently does nothing would reintroduce
exactly the "steps that do nothing" failure the whole wizard restructure fought (plan §1).

## Sketch (for a future focused PR — touches the command hot-path, so plan-first)

1. **Cached read model.** Mirror `utils.guild_config_accessors.get_command_access_policy`: a
   per-guild cached snapshot of routing rows + an `invalidate_*` paired with `command_routing.set_policy`.
   `is_cog_enabled` does up to 3 uncached DB reads — unacceptable per-command without caching.
2. **Enforce in the gate.** After Command Access + governance pass, resolve the command's owning
   subsystem (reuse the governance subsystem resolver) and deny when the cached routing says the
   subsystem is off for this channel/category. Default-true preserved → **byte-identical for any guild
   with no routing rows** (the safety property that makes this low-risk despite being hot-path).
3. **Surface it plainly.** Only *after* enforcement is real: a wizard extra/step ("Limit features to
   certain channels") over the same audited `command_routing.set_policy` + the existing routing profiles.
4. **Guards.** An invariant test pinning that a routing policy actually flips `is_cog_enabled` *and* the
   gate decision; a deny-path metric like `command_access_decisions_total`.

## Lifecycle

Captured (this file) → needs its own `docs/planning/` plan before build (hot-path + cached-resolver
weight). Related: the Command Access half shipped in PR #1496; the wizard-coverage context lives in
[`setup-wizard-restructure-plan-2026-06-24.md`](../planning/setup-wizard-restructure-plan-2026-06-24.md)
▶ Coverage follow-on.

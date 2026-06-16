# 2026-06-16 — `/commands` management surface (READ side)

> **Status:** `in-progress` — born-red per Q-0133; flipped to `complete` as the deliberate
> final step once the work + close-out docs land. Dashboard-only (no `disbot/` runtime).

## What I'm about to do

Continue the bot's main website (`dashboard/`). Build the **`/commands` management surface —
READ side** (Q-0158, owner ask): a **Manage** button on every command *and* every cog, each
opening a panel that shows that command's current aliases + its cog's routing/enabled model
(front-ending `services.command_routing`) + a **per-command alias suggest box** (suggest→PR mode,
like `/aliases` but scoped to one command). The global `/aliases` page stays the broad search.

Decoupled + read-only: no `disbot/` import, no auth, no bot change. The write side (live toggle /
live alias) is gated behind the control API + Discord OAuth (Phase 2), which the owner has **not**
set up yet — so this session grows the read-only side, as the handoff directs.

**Owner decision confirmed this session (AskUserQuestion → Q-0160):** enable/disable is
**cog-level now, per-command later** — front-end the existing audited `command_routing` (per-cog,
scope-aware); per-command stays a documented future bot layer.

## Status checklist

- [ ] acronym-aware `_cog_to_subsystem` (fixes BTD6/AI cog→subsystem join) + test
- [ ] `/commands` Manage buttons (command + cog) + slide-over panel
- [ ] per-command alias suggest box (collision check + prefilled issue + snippet)
- [ ] cog routing-state display (cog-level model, audited seam)
- [ ] export enrich + regenerate `dashboard.json`
- [ ] smoke test (web deps) + `check_quality --check-only`
- [ ] Q-0160 router record + plan-doc update
- [ ] session enders (idea / review / grooming / docs audit) + flip card `complete`

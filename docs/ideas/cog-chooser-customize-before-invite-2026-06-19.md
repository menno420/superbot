# Public-site cog chooser — "customize the bot before you invite it"

> **Status:** `ideas` — capture only (not a plan, not approval). **Owner-directed 2026-06-19.** Source +
> binding contracts + `current-state.md` win over this file.
> **Subsystem:** none — a public-site + cross-cutting *setup* surface; it spans **all** subsystems via
> their per-guild `enabled` toggle rather than owning any single one.

## The ask (owner intent)
On the **public site**, let people **customize the bot before inviting it to their server** — a general
**"cog chooser"**:
- Pick the high-level **sections** you want (e.g. **Games / Moderation / Server management / …**).
- Within each section, see the **relevant cogs** and toggle each **on / off**.
- Two starting modes: **all-on → deselect** what you don't want, **or all-off → select** what you do.
- Result: the bot arrives already tailored to the server — killing the "it does too much, I only
  wanted X" friction at the very first touch.

## Why it's a strong fit — the data *and* the seam already exist
- **Sections + cogs = the existing feature catalogue.** `botsite/data/site.json` already groups the
  catalogue by category — today: **games (8) · admin (7) · moderation (6) · community (4) · utility (4)
  · economy (3) · management (2) · progression (2)** — and the `/features` page already renders these
  groups. The chooser reuses this exact data; no new catalogue is needed.
- **The toggle target already exists.** Every subsystem resolves a **per-guild `enabled` setting**
  (`resolve_value(guild_id, SUBSYSTEM, "enabled", DEFAULT_ENABLED)` — see `welcome_config`,
  `security_config`, `image_moderation_config`, `counter_config`, …). So "enable/disable a cog for this
  server" is an **existing, audited settings write** — the chooser just produces a *set* of them.

## The one real design decision — how the pre-invite selection reaches the bot
The UI + data are easy; **delivery is the design** (the same gate the per-server panel hits):
- **(a) Thread it through the invite/OAuth flow** — encode the selection in the OAuth `state` (or a
  short-lived setup token the site mints) so the bot reads the pending config and applies the `enabled`
  writes on first setup. Best UX (true "customize *before* invite"), but the bot must accept an
  external pre-config → touches the control-API / setup seam → **likely gated on the same control-API
  public-exposure security review** as the "manage my server" panel (Q-0179 / website-split §4.4/§7.4).
- **(b) Seeded setup code / deep-link** *(recommended v1)* — the site emits a code or a `/setup`
  deep-link carrying the choices; the owner runs it in-server after inviting. **No new public-exposure
  surface**, much lower friction than full manual setup.
- **(c) Plan-only preview** — purely informational ("this is what you'll get") that deep-links into the
  existing in-bot setup. Weakest, but zero backend.

**Recommendation: ship (b) as v1** (seeded setup code/link — no public control-API exposure), with **(a)**
as the post-security-review upgrade to zero-touch pre-config.

## Relation to existing plans
- **Sibling of the "manage my server" panel (Q-0179 / website-split-plan §7.4):** that panel is the
  *post-invite, authenticated, per-guild* control surface; **this chooser is its pre-invite, no-auth,
  no-server-selected front door.** Both write the same `enabled`/settings seam; both (in fully-integrated
  form) ride the **control-API security review**.
- **Pairs with the just-shipped Add-to-Discord button** — the chooser would wrap that CTA into a
  "**customize → then add**" flow (the button stays the fallback "add with defaults").

## Open questions for the owner
1. **Delivery mechanism** — (a) / (b) / (c) above.
2. **Default preset** — offer both, but is *all-on-deselect* or *all-off-select* the **default**?
3. **Granularity** — per-cog within sections (owner said per-cog); confirm the per-section cog list =
   the site catalogue's grouping.
4. **What "disable" means** — bot doesn't *load* the cog vs. loads it but its commands are gated off via
   the `enabled` setting. (The existing seam = the latter; identical to users, far simpler to build.)

## Build path (when greenlit)
1. **UI** — a `/customize` page (or a modal off the landing): sections from the catalogue, per-cog
   toggles, the two presets, a live "N features selected" count. Inline-SVG/CSS, no `static/` dir
   (#970 gotcha), like the rest of the bot site.
2. **Delivery v1 (b)** — mint a seeded setup code/link; the in-bot setup applies the `enabled` writes
   through the **audited settings pipeline** (no direct DB writes — the mutation seam rule).
3. **Then (a)** post-security-review — thread the selection through the invite/OAuth `state` for
   true zero-touch pre-config.

## Relations
- `botsite/data/site.json` catalogue (categories) · the per-subsystem `enabled` settings seam ·
  `disbot/cogs/setup/` (the setup system to seed into).
- [`../planning/website-two-site-split-plan-2026-06-19.md`](../planning/website-two-site-split-plan-2026-06-19.md)
  §4.4 / §7.4 (Q-0179 manage-my-server) · the Add-to-Discord CTA (#1152).

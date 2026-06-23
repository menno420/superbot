# Session follow-up ideas — visual engine + AI-setup wedge arc (2026-06-23)

> **Status:** `ideas` — capture only, not approval, not a plan. Source + binding contracts win.
> **Subsystem:** none (cross-cutting). Promoted out of their `.sessions/` logs into the backlog so
> grooming finds them without grepping session history (the Q-0089 "substantial ideas get a backlog
> home" follow-through).

These are the genuine forward ideas generated during the 2026-06-23 visual / AI-setup arc (PRs
#1349 card engine · #1352 positioning · #1355 + #1357 `/setup-describe` · #1361 create-count guard).
The two *implemented* ideas from the same arc (resource **creation** from a description → #1357; the
**create-count guard** → #1361) are already shipped and need no capture. These three remain open.

## 1. Golden-image snapshot tests for the card engine

**From:** `.sessions/2026-06-23-visual-card-engine.md` (Q-0089). **Lane:** dev quality / tooling.

The card renderers (`utils/card_render.py`, `utils/profile_render.py`, and the older
`mining_render` / `welcome_render` / `character_render`) are only asserted on "returns PNG bytes /
doesn't crash". A **layout** regression — a panel shifting, a bar overflowing, a theme colour
swapped — passes silently. A small golden-image harness (hash or pixel-diff a rendered card against
a committed reference per theme, with a tolerance for font anti-aliasing) would catch visual
regressions the byte-check can't. **It becomes load-bearing at card-engine roadmap H2**, when the
existing renderers migrate onto `CardCanvas` — that refactor is exactly where a silent visual
regression would slip in. Contained, dev-only (Pillow already present; gate the dep with
`pytest.importorskip`). See `docs/ideas/visual-card-engine-vision-2026-06-23.md` (the engine roadmap).

## 2. User-visible "cosmetic-only monetization" pledge surface

**From:** `.sessions/2026-06-23-competitive-positioning.md` (Q-0089). **Lane:** product / positioning.

The competitive research (`docs/ideas/competitive-positioning-north-star-2026-06-23.md`) found that
the **monetization *promise itself* is a differentiator** — the MEE6 backlash, ProBot's retroactive
paywall, and the `alternativestomee6.com` migration movement all stem from paywalling utility users
*depended on*. The inverse — a credible, **stated** *"we will never paywall a feature you rely on;
we only ever sell cosmetics"* — is the lowest-friction trust wedge, and it costs nothing we'd
otherwise sell. Idea: a small user-visible surface (e.g. a line in `!about` / an info command, or a
short pledge page) that states the principle, turning an internal value into marketing. Tiny,
contained; it's the user-facing half of the north-star's Pillar 1.

## 3. Per-kind breakdown in the setup create-count guard

**From:** `.sessions/2026-06-23-setup-create-confirm.md` (Q-0089). **Lane:** setup UX (small).

The Final Review create-count guard (#1361) shows a flat *"➕ N new resource(s) will be created"*
with names. For a large plan, grouping by kind — *"2 channels, 1 role, 1 category"* — lets an
operator sanity-check the *shape* at a glance before applying. The data is already there
(`op.kind` / `target_kind` in `_created_resource_names`); it's a rendering tweak on the existing
helper. Small contained follow-up to #1361.

## Routing

All three are **build-when-convenient** follow-ups (no owner decision needed; reversible,
test-coverable). #1 is the highest-value (it protects the whole visual investment as it scales);
#2 is the cheapest win; #3 is polish. Groom one down per the standing secondary-task cadence.

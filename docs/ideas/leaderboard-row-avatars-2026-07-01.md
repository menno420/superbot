# Idea: leaderboard row avatars (the Arcane-defining visual)

> **Status:** `ideas` (not approved). **Subsystem:** xp / presentation.
> Captured 2026-07-01 (Q-0089) while polishing the `!rank` + `!leaderboard` cards against the
> Arcane/MEE6 screenshots. Binding contracts + owner decisions win over this note.

## The idea

The leaderboard **image card** now reads well (outlier-safe bars, podium colours, clean values — this
PR). But the single thing that makes **Arcane's** board feel "real" rather than a chart is a **per-row
avatar thumbnail** next to each name. We already have every piece to add it:

- `CardCanvas.avatar_disc(center, radius, bytes)` — composites a circular avatar (built this PR).
- `services.xp_helpers.fetch_avatar_png(member)` — the one network→bytes seam (built this PR).

So the board just needs to: resolve the top-N members, **fetch their avatars concurrently**
(`asyncio.gather` with a small bound + a per-fetch `None` fallback so one slow/failed avatar never
stalls the render), pass the bytes list into `render_leaderboard_image`, and draw a small circle in
the reserved name column (the layout already leaves room). Rows whose avatar is `None` fall back to the
initials disc — no row ever breaks.

## Enabling micro-idea: an avatar LRU

`fetch_avatar_png` is one CDN hit per call. A 10-row board = 10 hits, and the `!rank` stat-toggle / hub
re-renders re-fetch the same avatar each switch. A tiny **in-process LRU** (`user_id → bytes`, short TTL,
bounded size) in front of `fetch_avatar_png` removes the repeat hits — cheap, no external store
(ADR-001-clean, it's process memory), and it makes row-avatars affordable.

## Why it's worth having

- Closes the last visible gap to the incumbents on the board (the owner's explicit comparison target).
- Pure-additive on the seams already shipped; graceful-degradation contract unchanged (Pillow-less /
  fetch-failure hosts keep the current clean bar board).
- The avatar LRU independently speeds up the single-user rank card's re-renders.

## Scope / cautions

- Concurrency **must** be bounded + individually fault-isolated (one departed member / slow CDN must not
  hold the board). Departed members have no avatar → initials disc (consistent with `_clean_name`).
- Keep it behind the same `bytes | None` fallback: a board must always render, avatars or not.

## Related

- `utils/card_render.py` (`avatar_disc`) · `utils/ux_patterns/image_builders.py` (`render_leaderboard_image`)
- `services/xp_helpers.py` (`fetch_avatar_png`) · `docs/ideas/visual-card-engine-vision-2026-06-23.md` (H3)
- `.sessions/2026-07-01-visual-comparison-cards.md`

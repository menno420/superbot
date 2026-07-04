# 2026-07-01 — Visual comparison: out-read Arcane/MEE6 on the rank + leaderboard cards

> **Status:** `complete` — ready to merge (Q-0133). Run type: manual · owner-directed.
> Full CI mirror green (**13604 passed**; ruff/black/isort/mypy clean; arch 0 new). PR #1614.

**Branch:** `claude/visual-comparison-other-bots-89vna4` (from `main` @ #1613).

## What I'm about to do (intentions)

The owner shared two Discord screenshots comparing SuperBot's XP visuals side-by-side with **Arcane**
and **MEE6**, and asked us to review the readability/appeal gap and **make ours more appealing and
easier to read** (not copy their layouts). Rendering the current cards confirmed the concrete gaps:

**Leaderboard image (`render_leaderboard_image`):**
1. **Outlier-dominated bars** — a single #1 (118k XP) fills the bar; all 9 other bars are unreadable
   stubs (can't tell 10k from 3.7k). The bar carries almost no information. → outlier-safe scaling.
2. **Emoji render as tofu boxes** — the 🏆 title glyph (and 🪙 coin values) are missing in DejaVu →
   `□`. → strip/replace emoji for image text.
3. **#1 value text clips off the right edge** (bar too long → value drawn past the canvas). → reserve a
   right-aligned value column; cap bar width.
4. **Raw `<@id>` names** for uncached/left members (both embed + baked into the image). → global-user
   fallback in `member_display` + sanitize any residual mention in the image.
5. Ranks 2–10 all identical blurple; low-contrast values. → medal colours for the top 3 + brighter values.

**Rank card (`render_rank_card`):**
6. **"ME" initials instead of the real avatar** — Arcane + MEE6 both show it; biggest visual gap. →
   composite the live avatar into the disc (caller fetches bytes; graceful fallback to initials).
7. **Progress bar nearly invisible** — a tiny dot, no %. → visible track + % readout + taller bar.

## What shipped

Rendered the current cards to PNG and Read them (the only honest way to verify visual work in-sandbox
— no Discord CDN here), confirmed each gap against the screenshots, fixed them, and re-rendered
before/after to check. All in the presentation layer with the existing graceful-degradation contract.

1. **Engine (`utils/card_render.py`)** — two reusable primitives, so the fixes are one-source-of-truth,
   not per-card patches:
   - `image_safe(text)` — strips emoji the bundled DejaVu font renders as a tofu □ box, applied **at the
     `CardCanvas.text()` seam** so *no* card can tofu again (verified no image renderer draws renderable
     symbols → zero regression; a future colour-emoji font gates it, H4 note).
   - `CardCanvas.avatar_disc(...)` — composites a real, circular-cropped avatar from bytes with the accent
     ring; returns `False` on undecodable bytes so the caller falls back to `initials_disc`.
2. **Rank card (`utils/rank_render.py`)** — new `avatar_png` param (real avatar, initials fallback) +
   a **prominent progress bar** (visible panel-colour track + right-aligned `%` readout, taller bar);
   was a near-invisible dot on a near-black track.
3. **Leaderboard (`utils/ux_patterns/image_builders.py`)** — `_bar_fraction` **outlier-safe scaling**
   (sqrt + floor: a 118k #1 no longer squashes nine sub-10k bars to stubs), a **reserved right value
   column** (the #1 value no longer clips off-canvas), **podium colours** for the top three, and
   `_clean_name` (a departed member's raw `<@id>` → `unknown`, never baked into the image). Emoji titles/
   values are cleaned by the engine seam.
4. **Wiring** — `services.xp_helpers.fetch_avatar_png` (the one network seam; forces a small static PNG;
   any failure → `None` → initials) threaded through `build_rank_response` + `_render_rank_image`, and
   `cogs.xp_cog._build_rank_provider_response`. So the real avatar rides **every** rank path: `!rank`
   xp/coins, the provider cards (`!rank mining` etc.), the `!xpmenu` hub, and the stat-toggle re-render.
5. **Tests (+9)** — `image_safe` (strip vs preserve `→·…`), `avatar_disc` success + undecodable-fallback,
   rank card with/without avatar bytes, `_clean_name`, `_bar_fraction` outlier-safety + monotonicity, and
   an outlier+mention+emoji-title render. Full CI mirror green (**13604 passed**), arch 0.
6. **Docs** — vision doc `visual-card-engine-vision-2026-06-23.md` H3 gains the polish-pass note + the
   H4 emoji-font gate reminder.

Before/after renders are attached in the PR / chat.

## Context delta

- **Scoped OUT the `member_display` global-cache fallback (deliberate).** The unresolved `<@id>` rows are
  *departed* members (most names resolve → the member cache IS populated), so a private-`_state` global
  lookup wouldn't resolve them **and** would break a `MagicMock`-guild test for no real gain. The image
  `_clean_name` sanitize is the correct, sufficient fix — the *image* never bakes a raw mention; the embed
  keeps `<@id>`, which Discord's client resolves for globally-known users anyway. Minimal blast radius,
  no private API, no provider/test churn.
- **Scoped OUT `/myprofile` avatar wiring** — not in the owner's screenshots; the `avatar_disc` primitive
  is ready and it's flagged as the next adopter. Honest scoping to the two surfaces shown.
- **Root-cause over per-panel:** `image_safe` at the `text()` seam (not stripping at each call site) is the
  maintainer's stated "central fix, not 20 patches" preference — one change fixes tofu on every card.
- **Verification method:** rendering to PNG and *Reading* the image is the loop that fits "the maintainer
  visualizes; you build" — I could see the outlier-squash, the tofu box, and the clipped value directly,
  which no test would have surfaced.

## 🛠 Friction → guard

The black↔ruff **COM812 ping-pong** recurred (black wraps a long call → ruff wants a trailing comma → black
re-checks): the PostToolUse auto-fixer doesn't fire in the web/remote container, so the first `check_quality
--full` reddened on ruff. Already a documented journal Rule ("run `black` LAST" / "trust `check_quality.py`");
settled by `ruff --fix → black` twice. **No new guard needed** — the existing Rule covers it; the real
prevention is the PostToolUse hook, which is env-limited here. Noting the recurrence, not manufacturing a
duplicate guard.

## 💡 Session idea

**Leaderboard row avatars (the Arcane-defining visual).** The bar-chart board reads well now, but the one
thing that makes Arcane's board feel "real" is a per-row avatar thumbnail. The `avatar_disc` primitive +
`fetch_avatar_png` seam are already here; the board just needs to fetch the top-N avatars **concurrently**
(`asyncio.gather`, bounded) and composite a small circle in the reserved name column. Enabling piece worth
its own micro-idea: a tiny in-process **avatar LRU** (user_id → bytes, short TTL) so the stat-toggle / hub
re-renders and a 10-row board don't re-hit the CDN each time. Filed: `docs/ideas/leaderboard-row-avatars-2026-07-01.md`.

## ⟲ Previous-session review

Prev: `2026-07-01-role-menu-layout-sim-pin-style.md` (PR #1613 — pinned Style first-screen in the role-menu
layout sim). **Did well:** folded the owner's correction straight into the model *and* added a guard test
(every optimised variant places Style on row 0) — the "verify the model against real knowledge" loop with a
regression test as its documentation. **Could improve / workflow surface:** the sim is explicitly
advisory — "still doesn't change the builder." That's a recurring shape (a sim produces a stable,
owner-confirmed recommendation that never reaches the actual builder), so the insight can silently drift
from the shipped layout. **Improvement:** when a sim's recommendation is stable across seeds *and*
owner-confirmed, there should be a lightweight path to *apply* it to the builder (or a checker that flags
builder-vs-sim drift) — otherwise advisory sims accumulate as un-actioned analysis. (Captured as a thought,
not built — same bar as Q-0089: no filler.)

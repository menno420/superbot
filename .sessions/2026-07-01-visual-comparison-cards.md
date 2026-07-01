# 2026-07-01 — Visual comparison: out-read Arcane/MEE6 on the rank + leaderboard cards

> **Status:** `in-progress` — born-red (Q-0133). Run type: manual · owner-directed.
> PR # pending first push.

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

_(filled in at close)_

## Context delta

_(filled in at close)_

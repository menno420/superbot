# 2026-06-24 — `!xpmenu` hub renders the rank image card (visual card-engine H3)

> **Status:** `complete` — PR #1413; auto-merge armed; merges on green. Full CI
> mirror green (12,374 passed; mypy + lint + arch clean).

> **Run type:** `routine · dispatch`

## What I'm about to do
Scheduled dispatch fire, no work order. Bugs blocked/data-gated (BUG-0009 newest-towers
needs release-order data · BUG-0011 needs a VPS repro); BUG-0009/0019 rootfix backlog
both blocked. Taking the **S1 consolidation polish tail · visual card-engine H3**:
the `!xpmenu` hub panel (`_XpHubView`) currently shows a plain rank **embed** while
`!rank` already renders the themed image **card** (`utils/rank_render.py`, #1401).

This slice migrates the **direct `!xpmenu` surface** onto the same image card:
- `_XpHubView.build_response(stat)` → `(embed, card)` via the existing
  `services.xp_helpers.build_rank_response` (the same fetch-once embed+card the
  `!rank` view uses); the stat-switch buttons re-render with `attachments=[card]`,
  exactly mirroring `_RankSelect.callback` (the established H3 toggle grammar).
- `XpCog.xp_menu` sends the card via `send_panel(..., file=card)` (already supports it).
- Pillow-less hosts degrade to the embed (card `None`) — byte-identical fallback.
- `build_help_menu_view` stays **embed-only** (the help-nav seam is embed-only by
  contract across the whole codebase — threading a file through every hub seam is a
  separate cross-cutting change, out of scope here).

Idea→ship is self-initiated (Q-0172) — flagged on the run-report ⚑ Self-initiated line.
Plus regression tests; full CI mirror green; auto-merge on green.

## Shipped (PR #1413)
- `views/xp/main_panel.py` — `_XpHubView` gains `build_response(stat) -> (embed, card)`
  over `xp_helpers.build_rank_response`; a shared `_decorate()` owns the title/footer/
  admin-button chrome (one place, was duplicated in `build_embed` + each button); the
  three stat buttons route through `_switch_stat` → `edit_message(attachments=[card] or [])`,
  mirroring `_RankSelect.callback`. `build_embed` stays embed-only for the help-nav hook.
- `cogs/xp_cog.py` — `xp_menu` sends `embed, card = await view.build_response()` via
  `send_panel(..., file=card)`.
- `tests/unit/views/xp/test_xp_hub_panel.py` (new, 6 tests) — card attaches + embed
  decorated · Pillow-less embed-only fallback · admin-only footer · stat-switch swaps the
  card attachment · stat-switch clears the attachment on fallback · the help-nav
  `build_embed` path never touches the card seam.

## 💡 Session idea (Q-0089)
The `build_help_menu_view` help-nav hook is **embed-only by contract across the whole
codebase** — every hub reached *through Help* loses its showpiece image card (profile,
rank, leaderboard, …), while the same hub reached by its direct command shows it. Idea:
a **single help-nav attachment seam** — let `build_help_menu_view` optionally return an
attachment (or a `(embed, view, file)` triple) and teach the ~10 hub-rebuild call sites
(`views/navigation.py`, `hub_children.py`, `admin_cog._open_child`, …) to forward it.
Closes the "card via `!rank`, plain embed via Help → XP" inconsistency at the root.
Dedup-checked — no existing entry; bigger than this slice so flagged for grooming, not built.

## ⟲ Previous-session review (Q-0102)
Reviewed **2026-06-24-btd6-paragon-elite-boss-damage** (#1402). Did well: it treated a
curated runtime constant as *unverified* until it had ≥2 independent sources, and held the
PR born-red for the owner's nod on a contested point — exactly the discipline the BTD6
arc needs. Its Q-0089 idea (a "paragon vs elite boss effectiveness / hits-to-kill" answer)
I deliberately **did not** build this run: a hits-to-kill calc needs the paragon's full
per-second attack profile (multi-component) and would risk the confidently-wrong number the
owner keeps catching — so an unattended run shouldn't ship it without a live check. **System
improvement:** the dispatch menu / sector queue could carry a *confidence tag* on idea→build
candidates (offline-deterministic ✅ vs needs-live-verification 🔵), so an unattended fire
self-selects the safe ones (like this card slice) and routes the risky ones to an owner
session — the same auto/review/live split `dispatch_menu --unattended` already applies to
lanes, extended to promotable ideas.

## Doc audit (Q-0104)
`check_docs --strict` + `check_consistency` green; ledger check clean. The H3 progress is
de-staled in `current-state/S1-bot.md` (this slice added to the H3 "remaining" note). No
owner-decision / router change. Ledger entry for #1413 lands via the next reconciliation
pass (no placeholder — Q-0052).

## 📤 Run report
- **Run type:** `routine · dispatch`
- **Shipped:** PR #1413 — `!xpmenu` hub renders the rank image card (visual card-engine H3).
- **⚑ Self-initiated:** YES — promoted the S1 consolidation polish-tail H3 item (`!xpmenu`
  panel → image card) idea→build with no work order, per Q-0172. Contained, reversible,
  offline-verified, embed fallback.
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none (a merge auto-deploys to Railway).
- **Next ▶:** the help-nav attachment seam (session idea above) would carry the card through
  Help too; remaining H3 = the rank/profile **hub** showpiece panels reached via Help, plus
  the `mining_render` rebase (owner visual decision).

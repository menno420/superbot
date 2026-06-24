# 2026-06-24 — Help-nav attachment seam (visual card-engine H3)

> **Status:** `complete` — PR #1430; auto-merge armed; merges on green. Full CI mirror green
> (12,465 passed, 48 skipped, 2 xfailed; black/isort/ruff/mypy clean) + arch 0 errors +
> check_docs/check_consistency/ledger clean.

> **Run type:** `routine · dispatch`

## What I did
Scheduled dispatch fire, no work order. Bugs blocked/gated for an unattended run (BUG-0019 #1 =
owner design fork · BUG-0009 remaining slices need BTD6 release-order data + plan-level work — the
two rootfix-backlog entries are exactly those gated cases), so I took the **explicitly handed-off
next ▶ H3 slice** from PR #1413: the **help-nav attachment seam**
([idea](../ideas/help-nav-attachment-seam-2026-06-24.md)).

The inconsistency it closes: a hub opened by its **direct command** renders its showpiece image card
(XP hub via `!xpmenu`, #1413), but the **same** hub reached *through Help / hub navigation* showed a
plain embed — `build_help_menu_view` was embed-only across the codebase, so the showpiece disappeared
on exactly the discovery path the consolidation audit invested in.

## Shipped (PR #1430)
**Design — non-viral + backward-compatible.** Rather than change the `(embed, view)` return shape of
all ~47 `build_help_menu_view` hooks, the **view object carries its own card** via a duck-typed
`help_nav_card` attribute (declared on `BaseView`, default `None` = embed-only — today's behaviour).
The central help-nav **render** sites forward it via the `file=` / `attachments=` support that already
exists (`safe_edit` already supports `attachments`, built for exactly this PIL-card-on-one-anchor
case). A view without a card, or a render site not yet wired, behaves exactly as before — so the seam
rolls out hub-by-hub.

- `views/navigation.py` — `help_nav_card(view)` (defensive: non-`File`/missing → `None`),
  `help_nav_attachments(view)` (`[card]` sets / `[]` clears for in-place edits),
  `help_nav_send_kwargs(view)` (`{"file": card}` for fresh sends — never `file=None`, which
  `InteractionResponse.send_message` mis-reads as a broken attachment).
- `views/base.py` — `BaseView.help_nav_card: discord.File | None = None` (the seam's typed default).
- Wired render sites: `cogs/help_cog.py` typed `!help <cat>` (prefix `ctx.send` + slash
  `response.send_message`), `cogs/help/panels.py` category select (`edit_message`),
  `views/navigation.py` back-button + `transition_to` hub-opener (`safe_edit`),
  `views/hub_children.py` `HubChildButton` (`edit_message`), `cogs/admin_cog.py`
  `_open_via_help_hook` (`safe_edit`).
- First real consumer: `XpCog.build_help_menu_view` stashes the rank card from
  `_XpHubView.build_response()` (the same card `!xpmenu` shows) — the XP hub now shows its card
  through Help. `build_embed` (the config-panel back-nav path) stays embed-only; its drifted
  "for the help-nav hook" docstring was corrected.
- Tests: `tests/unit/views/test_navigation.py` (accessor unit tests + a **forward-path pin** that
  the back-button render forwards `attachments=[card]`) · `tests/unit/views/xp/test_xp_hub_panel.py`
  (the cog hook stashes the card + Pillow-less embed-only fallback; the repurposed `build_embed`
  test renamed to reflect it's the config-panel path).

## 💡 Session idea (Q-0089)
The help-nav seam now forwards the card on **edit-in-place** and **fresh send**, but Discord
`edit_message`/`send_message` only accept a **single** attachment cleanly through these helpers — a
future multi-image card (e.g. a hub that wants a banner *and* a stat card) has no path. Idea: widen
the seam to `help_nav_cards: list[discord.File]` (the singular `help_nav_card` becoming sugar for a
one-element list) so the same render sites forward `attachments=cards` / `files=cards` unchanged.
Cheap, fully backward-compatible (one card = today), and it future-proofs the engine before a second
multi-image consumer forces an awkward retrofit. Dedup-checked — not in `docs/ideas/`; smaller than a
plan, flagged for grooming.

## ⟲ Previous-session review (Q-0102)
Reviewed **2026-06-24-xpmenu-rank-card-h3** (#1413). Did well: it migrated a *single* surface
cleanly, explicitly scoped the help-nav seam *out* ("a separate cross-cutting change"), and — the
part that made this run fast — **groomed the cut work into a proper idea doc** with the call-site
list and the triple-vs-result-object design question already framed. That handoff turned a
breadth-unknown cross-cutting task into a 90-minute slice. One thing it could have done better: it
asserted the help-nav seam was "embed-only by contract" without noting `safe_edit` *already* supported
`attachments` — the infrastructure was there the whole time, so the "separate cross-cutting change"
framing slightly over-stated the cost. **System improvement:** the idea doc sketched a `(embed, view,
file)` *triple* as the shape, but the actually-correct shape was a *view attribute* (non-viral, no
47-hook churn). A groomed idea that proposes an implementation shape should carry a one-line
**"shape not yet validated — confirm against the consumer signatures before committing"** caveat, so
the building session re-derives the cheapest shape rather than anchoring on the sketch. (This run did
re-derive it — but only because I read all the call sites first.)

## Doc audit (Q-0104)
`check_docs --strict` + `check_consistency` + `check_current_state_ledger --strict` all green; arch 0
errors. De-staled `current-state/S1-bot.md` H3 note (seam shipped; remaining H3 = incremental
adoption). Marked the idea doc `historical` (built) with the as-shipped design recorded (it differs
from the sketched triple — noted so the next reader isn't misled). No owner-decision / router change.
Ledger entry for #1430 lands via the next reconciliation pass (band-#1440), no placeholder (Q-0052).

## 📤 Run report
- **Run type:** `routine · dispatch`
- **Shipped:** PR #1430 — help-nav attachment seam (the seam + accessors + XP hub as first consumer + tests).
- **⚑ Self-initiated:** YES — promoted the groomed `help-nav-attachment-seam` idea → build with no
  work order, per Q-0172. Contained, reversible, offline-verified, fully backward-compatible
  (embed-only default unchanged).
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none (a merge auto-deploys to Railway).
- **Next ▶:** **incremental adoption** of the seam — any other card-bearing hub sets
  `view.help_nav_card = card` in its `build_help_menu_view` hook and the render sites already forward
  it (profile/rank hubs reached via Help are the next natural adopters; the leaderboard *overview* is
  genuinely embed-only — it's a category picker, not a card). Plus the `mining_render` rebase (owner
  visual decision) and the multi-card seam idea above.

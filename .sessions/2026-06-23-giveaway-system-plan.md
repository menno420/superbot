# 2026-06-23 — Plan: native giveaway system (GiveawayBot teardown + beat-it plan)

> **Status:** `complete` — planning-only PR (no runtime code). Owner-directed: maintainer shared a
> screenshot of jagrosh's GiveawayBot and asked what it can do, what we lack, and how to build a
> *better* giveaway feature with more options. Chose "Plan it." PR #1348 → auto-merges on green CI (Q-0123).

## What shipped

A competitive teardown + buildable plan, no runtime code:

- `docs/ideas/giveaway-competitive-teardown-2026-06-23.md` — what GiveawayBot does (intentionally
  minimal: button entry, `<time> <winners> <prize>`, reroll, list, color/emoji settings — **no**
  requirements/weighting/bypass/payout/recurring), where we stand (no giveaway system today), and the
  beat-it feature list.
- `docs/planning/giveaway-system-plan-2026-06-23.md` — 2–3-PR plan. Migration 095 (`giveaways` /
  `giveaway_entries` (with `weight`) / `giveaway_winners`) → `utils/db/giveaways` → audited
  `giveaway_service` (eligibility, weighted draw, `economy_service.credit()` payout) → `giveaway_cog`
  (`!giveaway` group + `GiveawayEntryView` button) → auto-end via the automation scheduler. PR 1
  already beats GiveawayBot (requirements + weighted entries + auto-paid coin prizes); PR 3 (recurring
  auto-payout) owner-gated on faucet economics. 4 design Qs for the owner in §8.
- Index wiring: `docs/planning/README.md` S1 row, `docs/ideas/README.md` captures entry, and the
  `cog-improvement-audit-2026-06-08.md` Community gap now links the plan (closes a routing loop).

## Verification

- Docs-only. `check_docs --strict` ✓ (all new docs reachable). No `disbot/` code → no mypy/arch/pytest
  surface touched.

## Enders

- **💡 Session idea (Q-0089):** *bonus/weighted entries as a cross-feature primitive.* The giveaway
  plan introduces a `weight` column so boosters/high-XP members get better odds — but "weighted random
  selection over a guild population, seeded by a perk" is exactly what a fair **loot-drop**, **raffle**,
  and **role-of-the-week** feature also need. Worth a tiny shared `utils/weighted_draw.py` (sample N
  distinct from a `{user: weight}` map) so giveaways aren't the only consumer. Folded as a note into
  the plan's draw logic; flagged here as the reusable seam.
- **⟲ Previous-session review (Q-0102):** the prior session (hub child-rendering plan,
  `2026-06-23-hub-rendering-plan.md`) was a clean planning PR — well-scoped, good index hygiene. One
  thing it (and the broader planning corpus) could do better: **plans don't cross-link their reusable
  seams to *each other*.** This giveaway plan reuses the exact reaction seam the starboard and
  reaction-roles plans hardened, but I only discovered that by reading three plans. *System
  improvement:* the `docs/planning/README.md` rows could carry a small "reuses-seam:" tag (raw-reaction
  · economy-credit · automation-scheduler) so an agent can find every plan riding a given seam in one
  grep — cheap, and it would have saved a hop here. Captured as a candidate, not built (not in scope).
- **Doc audit (Q-0104):** `check_docs --strict` green; no merged-PR ledger drift (planning-only, ledger
  untouched); new owner-directed analysis is recorded in the idea + plan, not just chat. ✓
- **⚑ Self-initiated:** none beyond the owner-directed plan itself (maintainer chose "Plan it").

## Backlog grooming (Q-0015)

This session *created* a routed plan from the long-standing `cog-improvement-audit` giveaway gap —
moving that idea down its lifecycle (capture → plan). Counts as the grooming move.

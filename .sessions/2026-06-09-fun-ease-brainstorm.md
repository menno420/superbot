# 2026-06-09 — Fun & ease-of-use brainstorm capture + pets plan

**PR:** #623 (draft at first push per Q-0052; marked ready at session end)
**Type:** docs-only (ideas capture + structured plan + routing)

## Arc

Maintainer asked for a creativity test: survey what exists + what's already captured,
then brainstorm *new* fun/ease ideas. Ran two parallel explorers (feature inventory;
ideas/backlog survey), read the four product-growth roadmap drafts + owner-vision +
future-product-direction myself, then **grep-verified every candidate idea against
docs AND source** before keeping it. Asked the owner three structured questions
(cluster picks + session scope) — answers recorded as **Q-0053**.

## Shipped

- `docs/ideas/fun-and-ease-brainstorm-2026-06-09.md` — 24 dedup-verified ideas
  (A social/competition ×7 · B ambient delight ×10 · C member UX ×7), each with
  verified seams, size/risk, and a routing state (no orphans). §1 lists the
  candidates *dropped because they already exist* (with citations).
- `docs/planning/pets-companions-plan-2026-06-09.md` — the owner's ⭐ fun pick
  structured: P1 egg/hatch → P2 care-loop sink → P3 balance-gated perks (≤1–2%,
  non-P2W) → P4 showcase; gates = Wave-1 keystone slices + balance review + owner
  promotion. Roadmap: games **Later** row.
- Wiring: ideas README, roadmap (×2), games folio, router §24 (Q-0053).

## Findings worth keeping

- **The bot already has** "did-you-mean" fuzzy command resolution
  (`utils/command_resolution.py`), PvP coin stakes (RPS Bet Match / blackjack),
  and gifting/prestige captured in the mining brainstorm — brainstorms must
  grep-verify before proposing; three "obvious" ideas were already done.
- `!remind` is in-memory by its own admission (`cogs/utility_cog.py:36`) — every
  restart silently drops reminders. Captured as C4, an owner ⭐ ease pick.
- ~15 functional mining commands are `hidden=True` and Help-invisible (C5) —
  cheap active-lane discoverability win.
- All 7 social ideas were deliberately scoped single-guild so none waits on the
  open guild/clan tenancy question (Q-0038).

## Next-session candidates (from owner ⭐ picks)

1. **C1 context-menu actions** — first `context_menu` registrations (View
   Profile / View Rank first); biggest mobile win; routes into existing panels.
2. **C4 persistent reminders** — small table + delivery on schedule; root-causes
   a silent-loss bug.
3. Pets P1 only after the Wave-1 keystone slices (Workshop + durability) ship.

## Context delta

- **Needed but not pointed to:** nothing major — the orientation route +
  `docs/ideas/README.md` lifecycle covered this session shape well.
- **Pointed to but didn't need:** CodeGraph symbol tools — a brainstorm/capture
  session is grep + docs work; the graph never paid off here.
- **Discovered by hand:** the dedup greps (feature-or-idea novelty checks) are the
  load-bearing step of a brainstorm session — `command_resolution.py` and the RPS
  stakes would have been embarrassing re-proposals. Future brainstorm sessions:
  grep `docs/` *and* `disbot/` for each candidate before capture.

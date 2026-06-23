# Giveaway competitive teardown — GiveawayBot vs. SuperBot (2026-06-23)

> **Status:** `ideas` — captured from an owner-directed competitive analysis (maintainer shared a
> screenshot of jagrosh's GiveawayBot and asked what it does, what we lack, and how to beat it).
> **Subsystem:** community
> Routed to a buildable plan: [`docs/planning/giveaway-system-plan-2026-06-23.md`](../planning/giveaway-system-plan-2026-06-23.md).
> Nothing here is approved for implementation beyond that plan.

## The competitor — GiveawayBot (jagrosh)

The most-used Discord giveaway bot; **deliberately minimal**. Complete feature set:

| Area | What it does |
|---|---|
| Start | `/gstart <time> <winners> <prize>` (`30s`/`2h`/`7d`) or `/gcreate` interactive wizard |
| Entry | Click a **button** on the giveaway embed (older versions used a 🎉 reaction) |
| End / pick | `/gend <id>` ends early & picks; auto-ends on timer; **all entrants equal chance** |
| Reroll | `/greroll <id>` or right-click → Apps → Reroll Giveaway |
| Manage | `/glist` (active), `/gdelete <id>` (cancel, no winners) |
| Settings | `/gsettings set color <hex>`, `/gsettings set emoji <emoji>`, `/gsettings show` |
| Info | `/ghelp`, `/gabout`, `/ginvite` |
| Promise | Never DMs users; self-hosting unsupported; a "Get Premium" upsell (benefits undocumented) |

**What it deliberately omits** — and therefore our whole opening:
no entry **requirements** (role-gated, must-be-in-server, account/join age, min messages/XP),
no **weighted/bonus entries**, no **bypass roles**, no **blacklists**, no **multi-prize tiers**,
no **auto-paid prizes**, no **scheduled/recurring** giveaways, no deeper server integration.

## Where SuperBot stands

**No giveaway/raffle system exists today** (logged gap in
[`cog-improvement-audit-2026-06-08.md`](./cog-improvement-audit-2026-06-08.md): "next most
requested," quick-win). But we own substrate GiveawayBot doesn't: the hardened raw-reaction /
button-entry seam (`reaction_role_service`, `starboard_cog`), an audited **economy**
(`economy_service.credit()`), an **automation scheduler** (timers / recurring / quiet hours), and the
DB-migration + audited-mutation framework. A "🎁 Giveaways" notification role already exists in
`role_packs.py`.

## How we beat it — the feature list (→ folded into the plan)

**Parity (table-stakes):** button entry, `<time> <winners> <prize>`, auto-end timer, reroll, list,
cancel, per-guild color/emoji.

**Beat-it depth (the differentiators):**
- **Entry requirements** — role-gated, account-age / join-age minimums, min XP/level; **bypass roles**
  (boosters skip) and **blacklists**. *GiveawayBot's biggest gap.*
- **Weighted / bonus entries** — boosters or higher-level members get 2×–5× odds (GiveawayBot is
  strictly equal-chance).
- **Prizes that actually pay out** — auto-credit **coins / inventory / role** to winners via the
  economy seam; **multi-tier** prizes (1st/2nd/3rd differ). No manual handoff.
- **Recurring / scheduled** giveaways via the automation scheduler (daily/weekly auto-draw).
- **Engagement** — live entry-count + countdown embed, winner spotlight, giveaway history/leaderboard
  ("most-won"), **entry-task** giveaways ("be in voice", "reach level N this week").
- **Ops quality** — persists across restarts, audit log of every draw/reroll, dry-run preview.

## Routing

Promoted to a 2–3-PR plan (`giveaway-system-plan-2026-06-23.md`). PR 1 already clears the GiveawayBot
bar **and** adds requirements + weighted entries + auto-paid coin prizes. PR 3 (recurring auto-payout)
is owner-gated on economy-faucet grounds. Open design questions (prize default, bonus-entry source,
auto-end mechanism, command naming) live in the plan §8.

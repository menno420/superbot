# Idea — Karma (thanks/upvote reputation) system

> **Status:** `ideas` — capture, not a plan, not approval. Source code + the binding contracts win
> over this file. **Subsystem:** none → routed to a new `karma` subsystem (see the plan below).
> Dropped by the maintainer as the one-word prompt "Karma" (2026-06-22); clarified live via
> AskUserQuestion → **plan-first**, flavor **thanks/upvote reputation**.

## The idea

A peer **reputation** system: members grant each other *karma* for being helpful — the classic
Reddit/helper-rep / "+rep" mechanic. Karma is **earned from other people**, not from the bot, which
makes it a different signal from XP (activity) and coins (economy): it measures *how much the
community values you*. A karma leaderboard surfaces the most-appreciated members.

Grant surfaces (both proposed; reaction behind a setting):
- **Command** — `!thanks @user [reason]` / `!karma give @user`.
- **Reaction** — react with a configured emoji (e.g. ⭐) on someone's message to grant karma to its
  author (reuses the hardened raw-reaction seam built for reaction-roles #1234–#1250 / starboard).

## Why it fits

- **Free-for-everyone (Q-0190):** pure social reputation, no paywall, no P2W — a natural fit for the
  consolidation wedge (Karma/rep is a paid feature in several competitor bots).
- **Reuses proven seams:** the economy/XP architecture (audited `*_service.py` → EventBus emit →
  cog → leaderboard `RankProvider`) maps onto karma almost 1:1, so the build is low-novelty.
- **Community lane:** complements the safety/community family and the starboard "celebrate good
  contributions" theme.

## The one hard part: anti-abuse

Reputation systems live or die on farm-resistance. The design must include, from PR 1:
- **No self-karma, no bot-karma.**
- **Per-(giver→receiver) cooldown** — you can thank the same person at most once per window.
- **Per-giver daily cap** — caps total karma one account can mint per day.
- **Positive-only to start** — no downvote (avoids a harassment vector); revisit later if wanted.

The `karma_audit_log` table doubles as the anti-abuse source of truth (query recent grants
giver→receiver / giver-since), exactly as `economy_audit_log` backs the economy flow report.

## Open questions for the owner (also in the plan)

1. Grant surface: command-only, reaction-only, or both (recommended)?
2. Positive-only, or allow downvotes/negative karma?
3. Should karma stay **pure reputation** (recommended for this flavor) or ever bridge to economy?
4. **Karma roles** — auto-assign a role at thresholds (e.g. "Trusted Helper" at 50)? Phase 3.
5. Cooldown / daily-cap defaults.

## Routed to

→ Plan: [`docs/planning/karma-reputation-plan-2026-06-22.md`](../planning/karma-reputation-plan-2026-06-22.md)
(buildable, 2–3 PRs). Roadmap horizon: `docs/roadmap.md` S1 — **Later** (wants the owner's answers to
the 5 questions before PR 1).

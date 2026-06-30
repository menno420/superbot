# 2026-06-30 — Fishing rod-recipe browser (live progress toward each tier)

> **Status:** `in-progress`

**Run type:** manual · user-directed (Claude Sonnet 5, autonomous pick — "find something to do, go big")

## What this run is doing
S1's live queue (`docs/current-state/S1-bot.md` § Fishing follow-ups) names two turn-key, offline,
self-mergeable "next offline successor" picks on the rod-craft seam shipped in #1515/#1508: a new
rare-material drop, or the **rod-ladder recipe browser UI**. Picked the browser — it's the lower-risk,
clearly-scoped option (no new balance numbers to invent) and closes a real UX gap: today the rod shop
advertises a recipe's bare requirement ("10 fish, size ≤ 6") but never shows the player's *current*
eligible-fish count toward it, so there's no progress visibility before a `!craftrod` attempt either
succeeds or fails.

**Scope:** a `📋 Recipes` panel (button off `RodShopView` + a standalone `!rodrecipes` command) listing
every craftable rod tier (1–4) with the player's live eligible-fish count vs. the requirement, which
tier is owned/next/locked, and a Craft button for the immediate next tier (mirrors `!craftrod`).

In progress — will fill in implementation detail + flip to `complete` when done.

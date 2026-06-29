# Idea — conversational domain-context carryover for knowledge domains

> **Status:** `ideas` — captured / unstarted (2026-06-29, manual-session Q-0089 ender). Surfaced building the
> Project Moon combat-mechanics layer (PR #1549), which deliberately left bare-mechanic routing out.
> Route-in: the AI task router (`services/ai_task_router.py`) + the domain detectors
> (`utils/btd6/keywords.py`, `utils/projmoon/keywords.py`) + the ai folio
> ([`../subsystems/ai.md`](../subsystems/ai.md) § "Adding a knowledge domain").

## The gap

Knowledge-domain routing keys on **distinctive tokens** on purpose: `has_limbus_context` /
`has_btd6_context` are curated to avoid over-routing, so ordinary-English mechanic words
(`clash`, `speed`, `sanity`, `coin`, `tower`, `round`) are **excluded** — a real domain question
"almost always also carries a distinctive token." That conservatism is correct, but it leaves a real
seam:

> **User:** "tell me about Faust" → routes Limbus, grounds.
> **User (next message):** "how does clashing work?" → **no distinctive token → routes GENERAL,
> ungrounded** (the bot answers from the model alone, the exact case the mechanics layer exists to fix).

The committed mechanic *is* in the data and *would* ground — the message just never reaches the
grounding path. The same applies to BTD6 ("what's the best hero?" → "how much does it cost?").

## The idea

A short-lived, per-(channel, author) **domain-context memory**: when a message routes to a knowledge
domain (`BTD6_ANSWER` / `PROJMOON_ANSWER`), remember that domain for a small window (a few minutes or
N turns). On the next message that has **no** distinctive token of any domain *and* resolves a named
entity/mechanic in the remembered domain, let it inherit that domain's task. Otherwise fall through to
the current behaviour unchanged.

Guard rails (so it can't re-introduce the over-routing the curation prevents):
- **Only** activates when the bare follow-up resolves a real entity/mechanic in the remembered domain
  (so "ok cool thanks" never grounds).
- Decays fast (time + turn count) and is cleared by any message that routes to a *different* domain.
- Default-preserving: with no recent domain memory, routing is byte-identical to today.

This is the cross-domain generalisation of the BTD6 single-turn **conversation carryover** already
shipped (item 7 slice 1, #668 / BUG-0005) — promote it from a BTD6 one-off into a domain-agnostic
router capability, so every `KnowledgeDomain` (BTD6, Limbus, future LoR / LobCorp) gets sticky
follow-ups for free.

## Why it's worth having

It closes the highest-value gap the mechanics layer can't reach on its own — natural multi-turn
"and how does X work?" follow-ups are exactly how people ask about game mechanics. It needs no new
data, respects the over-route discipline (entity-resolution gated, fast-decaying), and folds cleanly
into the planned Slice B `KnowledgeDomain` seam (carryover becomes one shared field, not per-domain
code). Sizeable enough to want its own small plan (the state store + decay policy + the per-domain
resolve hook), so it is captured here rather than built inline.

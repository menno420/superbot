# Meter image moderation under the Q-0082 AI spend ceiling (2026-06-16)

> **Status:** `ideas` — session idea (Q-0089) surfaced while building image moderation
> (PR #941). **Not a plan, not approval.** Route through `ideas/README.md` before any code.

## The gap

`image_moderation` (PR #941, Q-0108) calls OpenAI's `omni-moderation-latest` endpoint **once per
uploaded image** when a guild enables it — through
`core/runtime/ai/providers/openai_moderation.py`. The call is free on OpenAI's side today, but it
is an **un-metered external request**: nothing counts it against the per-guild Q-0082 AI spend
ceiling, and nothing throttles a high-traffic image channel. This is the *same* class of gap the
NL event scheduler (Q-0112) was explicitly told to close ("adds one LLM call per event creation →
must be metered under the Q-0082 spend ceiling") — image moderation slipped in without the meter
because the v1 slice was scoped to mirror automod (which makes **no** external call).

## Direction (small, reuses existing machinery)

1. Route (or mirror) the `openai_moderation.classify_image` call through the existing AI
   cost-meter seam so each scan counts against the guild's Q-0082 ceiling (even if the unit cost
   is currently 0 — the *count* and the future-proofing matter).
2. When the ceiling is hit, **fail open** (skip the scan, let the image through) — consistent with
   the v1 fail-open discipline; never block uploads because the meter is exhausted.
3. Optionally expose a per-guild "images scanned today" counter in the `!imagemod` summary for
   operator visibility.

## Why it's worth doing

- One coherent spend model across every external-AI surface (NL events, image-mod, future
  vision/summarization), instead of per-feature ad-hoc accounting.
- Guards against a surprise bill if OpenAI ever meters the moderation endpoint, or if a server is
  flooded with images.

## Size / risk

Small. The meter seam already exists for the AI cog; this is wiring one more call site through it
+ a fail-open branch. No schema change. Risk: double-counting if the meter is applied at both the
provider and the listener — apply it at exactly one seam (the provider call site).

## Route

→ grooming lane (small/safe). Confirm the Q-0082 spend-meter seam's public surface first, then a
focused slice. Sequence naturally **after** the NL event scheduler (Q-0112) lands its meter, so
both external-call features share the same accounting path.

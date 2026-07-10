# Website suggestion copilot (2026-07-10)

> **Status:** `ideas` — owner-raised 2026-07-10 (live session, round-3 planning day).
> **Subsystem:** websites lane (control-plane / botsite) + fleet intake pipeline.
> **Gate:** partially owner-gated — needs a server-side AI API key with a spend cap, and
> the `/submit` endpoint's Postgres click (already in the owner queue) is the natural
> landing path.

## The idea (owner's words, expanded per Q-0254)

An **AI helper embedded in the websites for suggestions and bug reports**: when the owner
or any visitor wants to suggest something or reports a bug, they don't face an empty text
box — an AI assistant asks a couple of clarifying questions, helps turn a vague
impression into a concrete, actionable message (*what did you expect · what happened ·
where · how bad*), optionally proposes a solution, and submits the result in the exact
structured format the fleet pipeline consumes (idea file / ORDER material / issue).

## Why it's worth having

- **Pre-groomed intake:** the owner's own website-testing notes (started 2026-07-10) and
  any future user's feedback arrive as structured, deduplicatable, routable items instead
  of raw prose — the manager can route them as ORDERs without a human translation step.
- **It's the public skin of the idea-probe engine** (see
  `idea-probe-brainstorm-simulator-2026-07-10.md`): the same question battery, pointed at
  a visitor instead of an idea file. Build the engine once, expose it twice.
- First real **user-facing AI surface** of the websites — a meaningful product step for
  the botsite/control-plane beyond dashboards.

## Constraints known at capture

- Needs a server-side API key + hard spend cap + rate limiting (first runtime AI cost
  outside the bot; abuse surface on a public site).
- Lands on the `/submit` path (Postgres-gated, owner queue) — the copilot is the front
  end of that intake, not a separate store.
- Model choice: cheap tier (Haiku-class) is almost certainly enough for the interview
  flow; escalate only the synthesis step if needed.

## Route

Websites lane (ORDER via the manager) once the probe battery exists in v0 form; the
copilot consumes the battery as config, not code.

## Dedup

Grepped `docs/ideas/` + websites queue-state: `/submit` exists as a plain form ask;
nothing covers AI-assisted intake or a suggestion-shaping assistant.

# Idea probe / brainstorming simulator (2026-07-10)

> **Status:** `ideas` — owner-raised 2026-07-10 (live session, round-3 planning day).
> **Subsystem:** Idea Engine (standing autonomous core, round-3 launch pack §5) / agent workflow.
> **Gate:** ready — buildable as the Idea Engine's first tool; no owner blocker.

## The idea (owner's words, expanded per Q-0254)

A **brainstorming simulator**: a structured way to probe a set of questions against an
idea — or anything — to find out more about it and the right way forward. Multiple modes:

1. **Question-battery probe** (fast, deterministic flow): run the idea through a fixed
   interrogation — *what is this really · what's the possibility space · what's the most
   advanced capability reachable by the simplest implementation (the Q-0254 target) ·
   what breaks it · what does it unlock · what does it depend on · who/which lane should
   build it · what's the smallest shippable slice* — and emit the filled-in picture +
   a recommended way forward.
2. **Panel simulation**: N perspectives/personas (builder, skeptic, user, economist,
   operator) stress the idea from different angles — the fleet's judge-panel verification
   pattern pointed at ideation instead of review.
3. **Forward simulation** (stretch): "assume we build it — narrate month 1", surfacing
   the operational consequences no static question finds.

## Why it's worth having

- It turns the **understand-and-reflect step (Q-0254) from a habit into a tool** — every
  idea the new Idea Engine grooms goes through the probe before promotion, so promotion
  quality stops depending on which agent happens to groom.
- It is the **core method of the Idea Engine** (round-3 pack §5 seat 2): probe → filled-in
  picture → route as ORDER proposal. The engine needs exactly this to be more than a
  grep-and-promote loop.
- One engine, two skins: the same battery is the interview flow of the
  **suggestion copilot** idea (see `website-suggestion-copilot-2026-07-10.md`) — build the
  question engine once, expose it internally and publicly.

## Sketch

Mostly prompt + flow, cheap: a `probe` skill or workflow (battery as data, one agent per
question group in parallel, one synthesizer), output = a standard "probe report" section
appended to the idea file itself. Panel mode = the existing Workflow judge-panel pattern
with ideation personas. Home: superbot (where docs/ideas/ lives), invoked by the Idea
Engine's routine.

## Dedup

Grepped `docs/ideas/` + `docs/owner/ai-project-workflow.md`: the fan-out doctrine (§2)
describes multi-agent idea expansion as a *pipeline practice*; no idea covers a
reusable probe tool/battery, and nothing covers panel-simulation for ideation.

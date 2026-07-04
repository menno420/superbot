# Idea — an owner-decision-packet renderer (register rows → a visual decision artifact)

> **Status:** `ideas` — captured 2026-07-04 (Q-0089 session ender, Gate-0 brief-prep session).
> Directly serves FJ §4 gap #13 and the imminent Gate-0 owner sitting. Route via `/route-idea` when
> picked up.

## The problem it kills

The final judgment's surviving gap #13: *"every binding checkpoint hands prose walls / JSON to a
non-coding, visually-oriented owner; nothing renders decisions visually — the collaboration model's
own premise, unapplied to the rebuild's gates."* The maintainer **can't code** and thinks visually,
yet each gate (the 7 Tier-1 answers, now the 12 owner-only register rows, next the Gate-0 sitting)
arrives as a markdown table. It works, but it under-serves exactly the person the whole workflow is
built around.

## The mechanic

A small reusable renderer — a **skill** (`/decision-packet`) and/or a tiny generator — that takes a
structured decision set (the `question-register.md` row shape: *decision · options · recommendation ·
tier · owner-gated · blast-radius · maps-to*) and emits an **owner-consumable decision packet**:

- **v1 (cheap, now):** a normalized, scannable markdown packet — one card per decision, the
  recommendation visually distinguished (✅), options as a compact compare, blast-radius + "why this
  is yours to call" one-liner, and a checkbox/answer slot. Deterministic; no new deps.
- **v2 (visual):** render the same structure as an **Artifact HTML** (option cards, recommendation
  highlight, a per-decision "pick" control, tier grouping) — the literal "render decisions visually"
  the collaboration model asks for. The owner reads it on the web surface, not in a diff.

Input contract = the register row schema (already stable across two sessions), so it's reusable for
every future gate, not one-off.

## Why it's worth having

- **Timely:** the Gate-0 session (brief `rebuild-gate0-grammar-freeze-opus-brief-2026-07-04.md`) must
  render **12 owner-only rows** into exactly this packet — build the renderer there and it pays for
  itself immediately, then compounds across every later gate (Stage-2 verdicts, CUT-stage sign-offs).
- **Closes a named judgment gap** (#13) with a concrete artifact instead of a note.
- **Disposable + verifiable** (Q-0105): the packet is checkable against the register it renders.

## Bounds / non-goals

- Not a decision *engine* — it renders options + a recommendation; the owner still rules. It never
  picks.
- The register (source) stays the source of truth; the packet is a projection (mark it NOT SOURCE OF
  TRUTH, like every generated artifact).
- Start with the markdown v1; only build the Artifact v2 if the owner wants the web-rendered form.

## Provenance

Surfaced by the 2026-07-04 Gate-0 brief-prep session (PR #1713), which scoped the Gate-0 session's
owner-decision packet for the 12 owner-only register rows — the first concrete consumer.

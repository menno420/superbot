# Idea — a reusable "completeness-claim" grounding primitive (the BUG-0009 net)

> **Status:** `ideas` — capture, **not** a plan, **not** approval. Source code + the binding
> contracts win. Mid-sized AI-faithfulness idea; routes to the AI orchestration §7 / absence-claim
> guard family. Contributed 2026-06-14 (Q-0089) from the path/line-resolution session (#855).
> **Subsystem:** btd6 — BTD6-AI grounding faithfulness.

## Where it comes from

#855 added a **path-roster header** to grounding: `[btd6_path] Bomb Shooter middle path tiers:
1) Faster Reload … 5) MOAB Eliminator. These are every tier on that path; do not claim the path
lacks a tier/effect listed here.` That single line is doing something the rest of the grounding
stack doesn't: it asserts **completeness** ("these are *every* tier") in a machine-generated,
deterministic way. The rosters (#668), the capabilities reply, and now paths all hand-roll a
"this is the full set" sentence. Nothing makes that completeness *checkable*.

That matters because **BUG-0009** (claim-assembly: lists mislabeled / badly grouped) and the
btd6-map "long-list omission/miscount" gap are exactly *completeness* failures — the model drops
or adds items from a list whose every element was grounded ("which maps have water" → answered
64, truth 69; the Support-MK-vs-Banana-Farm grouping). The faithfulness guard checks **values,
not claims**, so a complete grounded list summarized lossily passes.

## The idea

Promote the ad-hoc "these are every X" sentence into a **first-class grounding primitive**:

- A small helper (e.g. `utils/btd6/grounding_format.completeness_block(label, items)`) that emits a
  roster line **plus a structured, parseable marker** the guard can later read — e.g. a trailing
  `[btd6_complete:bomb_shooter:mid n=5 ids=010,020,030,040,050]` sentinel (kept out of the
  user-facing answer, like other grounding scaffolding).
- The path roster (#855), the MK-by-entity list, tower/hero rosters, and the "newest towers" list
  all emit through it instead of hand-rolling the sentence — one source of truth for "complete set"
  framing.
- **The pay-off (Layer-B-adjacent):** the faithfulness guard gains a *completeness* check to sit
  beside its value check — when the draft answer enumerates a set the grounding marked complete, the
  guard can verify the answer's item count / membership against the marker and flag a drop/add
  (the BUG-0009 signature) instead of passing it. This is the deterministic "the layer owns the
  labeled list" fix shape the bug book already names as proven, generalized.

## Why it's worth having

- It turns the *completeness antidote* #855 shipped for one family (paths) into a reusable one for
  **every** high-traffic list family — the BUG-0009 class is broad (MK lists, per-level items,
  mode groupings, map lists), and they all want the same primitive.
- It gives Layer B of the absence-claim guard a concrete, **already-grounded** signal to check
  against, narrowing the §4 design's open "how does the guard know the set is complete?" question
  to "read the marker."
- Pure retrieval/format on the grounding side (no model change) to ship the primitive; the guard
  check is the gated half and rides with Layer B's review.

## Caveat / disposability (Q-0105)

Unverified until a guard actually consumes the marker — the primitive alone is just tidier
rosters. Build the emit side first (cheap, behaviour-neutral, ride it onto the next list family),
and only wire the guard check when Layer B is reviewed. If the marker proves brittle across the
list families (some sets are genuinely open-ended / version-dependent), keep it to the closed sets
(paths, rosters) and drop it for the open ones rather than forcing it everywhere.

# A vague-idea task shape for the kit-lab's cold-start A/B (test the understand-and-reflect doctrine itself)

> **Status:** `ideas` — session idea (2026-07-07, Q-0089, kit-doctrine port session). **Subsystem:**
> substrate-kit / kit-lab benchmark suite (B1).

## The gap

The understand-and-reflect + guiding-questions doctrine just shipped into the kit's templates
(`CONSTITUTION.md.tmpl`, `collaboration-model.md.tmpl`) has no enforcement — it relies entirely
on the executing agent's own judgment, by design (this is inherently not mechanically checkable
the way a session-log marker is). But the kit-lab founding plan's B1 cold-start A/B already adds
a **T5 break-a-rule task** to test the guard/checker half of the kit that earlier task shapes
never exercised. The same logic applies here: none of T1–T5 test whether an adopted kit
*actually changes agent behavior* on a deliberately underspecified, rough-draft-shaped prompt.

## The idea

Add a **T6 vague-idea task** to the B1 corpus: a prompt written the way the owner actually talks
about big ideas — a rough fragment, maybe with an explicit "I don't know if this is even
possible" framing — with no further detail supplied even if the session asks. Score (judge
rubric): did the ON arm restate a fuller picture back before building (the verification +
idea-expansion behavior), and when feasibility was the ask's shape, did it surface a possibility
space rather than just picking one interpretation and running? OFF arm has no such doctrine to
follow, so the comparison is really ON-arm-behavior vs. the written rule, not ON vs. OFF — a
different judge question than T1–T5's ON-vs-OFF framing, closer to a compliance check than an
A/B.

## Why it's worth having

Without this, the doctrine could silently stop working (a future kit edit contradicts it, a
future adopter's `CONSTITUTION.md` diverges after upgrade, a model generation just doesn't
follow prose instructions as well) and nothing in the benchmark suite would notice — the same
"did the guard actually fire" blind spot B3 exists to close for checkers, applied to a written
behavioral rule instead of a mechanical one.

## Routing

Structure into the kit-lab program's B1 band (KL-5) alongside T5 — same authoring PR, same
pinned-rubric mechanism, no new infrastructure needed.

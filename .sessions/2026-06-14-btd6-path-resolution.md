# 2026-06-14 — P1-1 Layer A: BTD6 path/line-aware resolution (absence-claim trigger removal)

> **Status:** `in-progress` — born-red per Q-0133. Building the path/line-aware BTD6
> resolution slice (the absence-claim-guard design's Recommendation #1, "ship Layer A
> first"). Will flip to `complete` as the deliberate final step once code + tests +
> close-out docs are in.

**What I'm about to do:** teach the BTD6 grounding to resolve path/line references
("bomb shooter middle path", "wizard bottom path") to that path's five tier upgrades and
auto-ground them — removing the canonical absence-claim trigger where path-level phrasing
resolves to nothing (`resolve_upgrade("bomb shooter middle path")` → `none`, verified live
this session) and the model confabulates a false "no". Deterministic retrieval, no guard,
verifiable in-sandbox exactly as the design doc verified it. This is the first concrete,
fully-completable deliverable of P1-1 (the standing #1 priority); Layer B (the
negative-existential gate) stays design-for-review + needs prod creds.

**Scope anchor:** `docs/btd6/btd6-absence-claim-guard-design.md` §4.1 (Layer A) ·
`docs/planning/production-readiness/hardening-roadmap-2026-06-12.md` §P1-1 · band-#840
decade queue slot 2.

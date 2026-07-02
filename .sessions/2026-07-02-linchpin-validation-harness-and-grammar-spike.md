# 2026-07-02 — Rebuild linchpin validation: golden harness + grammar spike + go/no-go

> **Status:** `in-progress`
> **PR:** (opens with this commit)
> **Branch:** `claude/superbot-linchpin-validation-tcyv25`

**What is about to happen:** build and prove the two unproven linchpins gating the Phase-3
rebuild (design spec `docs/planning/rebuild-design-spec-2026-07-02.md`):

1. **The golden behavioral harness (Phase 0.5)** — black-box command-in → embed/DB-out capture
   of the current bot, runnable in this repo, with a rigorously measured **coverage number**
   (fraction of the real command/panel/event surface captured, uncovered tail named).
2. **The grammar-expressiveness spike** — express 2–3 real subsystems (simple / operator /
   stateful game) in the design-spec §2 manifest grammar as real example manifests; measure the
   tier-1/2 vs tier-3 fraction against the real surface; verdict on the ~80% hypothesis.
3. **The go/no-go synthesis** — owner-gate evidence doc under `docs/planning/`.

No `disbot/` behavior changes. No new-repo (`sb/`) code — the spike is explicitly labeled.
Goldens live under `parity/` in this repo (outside the future new repo's write reach).

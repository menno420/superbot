# 2026-07-02 — Rebuild design spec: the "one picture" (docs-only, owner-gate deliverable)

> **Status:** `in-progress` — born-red (Q-0133). Run type: manual · owner-directed · ultracode.
> Scope: DESIGN, NOT CODE — no `disbot/` edits, no new-repo code.

**Branch:** `claude/superbot-rebuild-design-spec-de4mh7`

## What I'm about to do (intentions)

Produce the comprehensive from-scratch rebuild **design spec** for SuperBot at
`docs/planning/rebuild-design-spec-2026-07-02.md` — the owner-gate deliverable the
Phase 0→5 rebuild strategy requires before any Phase-3 new-repo code.

Inputs (verified, not re-derived): `docs/planning/fresh-rebuild-strategy-2026-07-02.md`,
`docs/planning/simulation-driven-design-2026-07-02.md`, and the verified preserve map
`docs/analysis/rebuild-discovery/codex-preserve-map-synthesis-2026-07-02.md` (+ its 4 raw
domain maps).

Method: judge-panel workflow — 3 independent designs (clean-slate-ideal /
minimal-migration-risk / manifest-grammar-maximal) + 1 Opus design → independent judges →
best-of synthesis → independent Opus review before finalizing. A non-Claude review prompt
is prepared as a handoff artifact (no non-Claude model is callable from this environment).

Deliverable covers: redone architecture + layer/ownership/runtime contracts; the
declarative manifest grammar (Subsystem/Panel/Action/Setting/Binding/Resource/Nav/
Selector/Result) designed to be simulated over; the central command/symbol namespace;
the authoritative settings model + safe-default-ON policy; the data model + §5
backward-compat contract; the control-plane (rulesets + OIDC); the regenerated binding
docs plan. Honors the three binding constraints: rename `ActionSpec` (hard collision with
`services/automation_registry.py:35`), extend—not recreate—shipped types, honor the §5
backward-compat set.

# 2026-06-19 — Planning/audit/idea map cleanup — a durable plan index + de-stale the route

> **Status:** `complete`

## Arc

Docs-only mapping/maintenance session. `docs/planning/` had accreted ~85 files (15 reconciliation-pass
snapshots, shipped-plan records, sim-pinned number files, superseded roadmaps) competing with the
genuinely-active plans, so a new agent skimming the folder hits stale/shipped plans before current truth —
and the project's **dominant active thread (the dashboard/control-API/website initiative) was unrouted**
from roadmap, folios, and the sector map. Goal: make the planning route self-navigating.

**Scope:** docs + idea-tag + checker-route hygiene only. No runtime/bot/dashboard/botsite/migration/test
behavior changes. `.claude/CLAUDE.md` untouched (no in-session owner directive to edit it).

## Method — six parallel read-only mapping agents (A–F)

A (planning non-recon) · B (idea lifecycle + cog/command + subsystem-tag targets) · C (website data
projection) · D (roadmap/folio/sector homing) · E (audits + recon snapshots) · F (docs tooling/gates).
Every classification cross-checked against source + merged PRs (latest #1123). Two agent calls were
corrected against source: A's "procedures-to-skills = completed" (wrong — only 11 skills on disk, batches
remain → kept ACTIVE) and B's `setup`/`round-range`=`none` (registry has no `setup` key; round-range is btd6).

## What shipped (the run report)

- **NEW `docs/planning/README.md`** — the durable plan index: active plans by sector, the dashboard/website
  cluster routed (fixes D's P0 unrouted-initiative gap), and a historical/superseded inventory
  (deliverables 1 + 2). Homes every plan in one stroke; AGENT_ORIENTATION + roadmap + archive/README now
  point at it.
- **Rebadged 40 docs `→ historical` in place** (link-safe; no physical moves) with one-line superseded
  banners — executed plans (mining-structures, help-overlay, mining-wire, btd6-grounding, …), the
  stale-badged recon passes (workflow/band1050/band1080; only **band1110** stays live), the 5 superseded
  production-readiness maps, and 12 superseded `docs/audits/` snapshots. Fixed the `ui-view-adoption-audit`
  self-contradicting badge. **Kept** the maps/audits with unique open findings (btd6 + settings readiness
  maps, the 5 living-ledger audits).
- **Tagged 27 ideas** with registry-validated `> **Subsystem:**` headers — the keys the filename-slug
  heuristic *missed* (image_moderation · btd6 ×4 · economy/games · ai · diagnostic · ux_lab · the safety
  lane) plus `Subsystem: none` for the website/meta cluster. Verified the export reader parses them.
- **De-staled routing:** roadmap ▶ pointer (band-1020 → defer to current-state's live line, drift-proof) +
  Last-updated; folio refresh (games + ai plan pointers; **media-youtube P0-2 retention factual fix** —
  it claimed raw-payload retention "until P0-2 lands" though #829 shipped it); ledger #1121/#1123 folded in;
  website next-steps idea-mapping + redaction-guard note.

## Status checklist

- [x] docs/planning/README.md (plan index)
- [x] rebadge 40 stale plans/recon/readiness-maps/audits → historical
- [x] 27 idea subsystem tags (verified parsing)
- [x] roadmap + folios + ledger de-stale
- [x] website integration note
- [x] verification (check_docs --strict · ledger · generated-fresh · validate_pack · agent-context test)
- [x] session enders

## Verification (all green)

`check_docs.py --strict` ✓ · `check_current_state_ledger.py --strict` ✓ (was RED: #1121/#1123) ·
`check_generated_artifacts_fresh.py --strict` ✓ · `tools/agent_context/validate_pack.py` ✓ ·
`pytest tests/unit/docs/test_agent_context_index.py` 13 passed. Badge census moved
historical 37→77, audit 28→6, plan 67→50. One **pre-existing soft** warning remains (Recently-shipped
21 vs ratchet 20 — not this session's drift; owned by the reconciliation routine's lean-ness trim).

## ⚑ Self-initiated (Q-0172)

Docs-infrastructure only, all inside the session's docs mandate: the new `planning/README.md`, the 40
in-place rebadges, and the 27 idea subsystem tags. No bot-feature idea→plan→implementation promotion; no
runtime/irreversible/external action.

## 💡 Session idea (Q-0089)

[`plan-homing-guard-2026-06-19.md`](../docs/ideas/plan-homing-guard-2026-06-19.md) — a stdlib
`scripts/check_plan_homing.py` asserting every non-`historical` `docs/planning/` doc is linked from a
**routing** doc (roadmap · folio · current-state · the plan index), not merely *reachable* from anywhere.
This is the exact gap that let the dashboard/website cluster drift unrouted for ~30 PRs while
`check_docs --strict` stayed green — surfaced directly by Agent D this session. The plan-level complement
to `check_sector_map.py` (folio homing) + `check_plan_backlog.py` (depth). Disposable (Q-0105). Indexed in
ideas/README.

## ⟲ Previous-session review (Q-0102)

**Reviewed:** `2026-06-19-website-split-next-steps-handoff.md` (#1123). **Did well:** gave the remaining
website work a single, cleanly-bucketed durable home (owner decisions · rollout · deferred-by-design ·
future ideas) — Agent C independently confirmed it's the correct, non-scattered home that needs no
re-homing. **Missed / could improve:** it (and the whole 8-doc dashboard/website plan cluster) was left
reachable *only* via `current-state.md` — never linked into `roadmap.md`, a folio, or any plan index, so
it was invisible to every agent navigation route until this session's manual mapping pass found it.
**System improvement it surfaces:** a session that creates a new durable plan/handoff should add its
inbound *routing* link (roadmap or the plan index) in the **same** PR — and that discipline should be a
forcing function, not a habit. That is exactly this session's 💡 idea (`check_plan_homing.py`): the
self-auditing loop turning "homing is a prose promise" into a checkable invariant.

## 📋 Closing doc audit (Q-0104)

Ledger green (`--strict`); no new owner decisions to route (none made — `.claude/CLAUDE.md` untouched, no
Q-block needed); all new docs reachable (`check_docs --strict`); the one fact this session created (the
plan index) has a single home (`planning/README.md`) cross-linked from AGENT_ORIENTATION/roadmap/archive.

## Context delta

Orientation pointed me well (the six-agent fan-out is the right shape for a mapping session). The one thing
I had to discover by hand: **`check_docs` reachability exempts `historical`/`archive` and otherwise needs
only one inbound link from *anywhere*** — which is *why* rebadge-in-place is safe (no orphan) and *why*
the homeless-but-reachable dashboard cluster slipped the guard. That nuance is now captured in both the
plan index's "Adding/retiring a plan" note and the `check_plan_homing.py` idea, so the next agent doesn't
re-derive it.

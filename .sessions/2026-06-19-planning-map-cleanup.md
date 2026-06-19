# 2026-06-19 — Planning/audit/idea map cleanup — a durable plan index + de-stale the route

> **Status:** `in-progress`

## Arc (what this session is doing — visible to parallel sessions)

Docs-only mapping/maintenance session. `docs/planning/` had accreted ~85 files (15 of them
reconciliation-pass snapshots, plus shipped-plan records, number-pin files, and superseded roadmaps)
competing with the genuinely-active plans, so a new agent skimming the folder hits stale/shipped plans
before the current truth. Goal: make the planning route self-navigating — one durable index, correct
status badges, every active plan homed, ideas routed to their subsystem.

**Scope fence:** docs + idea-tag + checker-route hygiene only. No runtime/bot/dashboard/botsite/migration
behavior changes. `.claude/CLAUDE.md` is read-only to this session (no owner directive to edit it).

## Method — six parallel read-only mapping agents (A–F)

A (planning non-recon) · B (idea lifecycle + cog/command + subsystem-tag targets) · C (website data
projection) · D (roadmap/folio/sector homing) · E (audits + recon snapshots) · F (docs tooling/gates).
All findings cross-checked against source + merged PRs (latest #1123).

## Plan (the deliverables)

1. **NEW `docs/planning/README.md`** — the durable plan index: ACTIVE plans grouped by sector + the
   homeless dashboard/website cluster routed + a HISTORICAL/archive inventory. This is the headline
   artifact and it homes every plan in one stroke (fixes D's P0 "dashboard initiative has no route").
2. **Rebadge stale `plan`/`audit` → `historical` in place** (reachability-safe; no physical moves —
   inbound links stay intact): the executed plans (mining-structures, help-overlay-editor, mining-wire,
   website-split brief, server-mgmt impl/roadmap, the platform-mapping/untapped audits), the stale-badged
   recon passes (workflow / band1050 / band1080), the superseded production-readiness maps (ai/games/
   health/media/server-mgmt), and the superseded `docs/audits/` snapshots. Each gets a one-line banner.
3. **Idea routing** — add verified `> **Subsystem:**` tags to the high-value ideas the slug heuristic
   misses (image_moderation/btd6×3/economy-games/ai), rebadge the 4 drifted idea headers (codex-pr-review,
   developer-dashboard, ai-panel-nav, moderation-dms).
4. **De-stale routing docs** — roadmap `▶` pointer band-1020→live + Last-updated + dashboard/website
   route pointer; folio plan-pointer refresh (games/ai/media-youtube stale retention claim); ledger fix
   (#1121/#1123 + trim overflow).
5. **Website integration note** — fold the field-snapshot redaction guard + the "tag mechanism already
   ships" note into the website durable home.

## Status checklist

- [ ] docs/planning/README.md (plan index)
- [ ] rebadge stale plans/recon/readiness-maps/audits → historical
- [ ] idea subsystem tags + drifted-header rebadges
- [ ] roadmap + folios + ledger de-stale
- [ ] website integration note
- [ ] verification (check_docs --strict · ledger · validate_pack · context packs)
- [ ] session enders (idea · prev-session review · doc audit)

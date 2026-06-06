# SuperBot — Current State

> **Doc type:** living status ledger (project state). **Not binding.**
> **Source code and merged PRs always win over this file.**
> The In-flight section below is a dated snapshot — **verify open PRs against
> live GitHub** before trusting it (two same-session reports already
> contradicted each other across a single merge).
>
> **Last updated:** 2026-06-06 · #550 merged (collaboration-model docs +
> truth-layer restructure). This session: **fixed the role-automation
> degradation** — `role_automation.apply` now preflight-guards at the mutation
> seam and classifies failures, so a roster-wide Manage-Roles / hierarchy
> blocker no longer floods the ERROR-only health surface (the "26 role
> automation errors"); operator + role-Diagnostics surfaces now show the cause.
> Branch `claude/epic-tesla-IGJ21` (PR pending) — detail in the session journal.
> Verify open PRs against live GitHub (`list_pull_requests`); this snapshot
> names none on purpose.
>
> **Purpose:** the one file that answers "what is true right now?" so a new
> session does not reconstruct it from the journal + planning docs. Read it
> **second**, right after `.claude/CLAUDE.md`.

---

## Stability baseline

Operational stability **accepted after #535** (live cog walk: server-management,
economy, moderation, games, hub navigation). **Do not run a broad re-audit unless
a regression is reported** — this is an *accepted baseline*, not a fresh re-test.
Env-gated features (AI / scheduler / YouTube / Paragon / webhook) run **degraded
in the sandbox**, not broken. Known UX follow-ups remain (below).

## In flight (verify against live GitHub)

**Do not trust a hard-coded PR count here — it goes stale on every push.** Get the
real list at session start from live GitHub (`list_pull_requests`, state=open);
this snapshot deliberately names no open PRs. For an initiative's shipped/queued
status read its tracker (e.g. the server-management tracker), not this section.
Source code and merged PRs win over anything written here.

## Recently shipped (newest first)

- **#550** — collaboration-model doc + truth-layer restructure (goal-first, prompts-as-guidance); docs-only.
- **#549** — server-management cleanup PR8+PR9: `policy_version` marker, presets builder + dry-run + panel diagnostics, and the guild-default `scope_id=0` no-op fix.
- **#548** — closed the migration-`057` persistence/dedupe/retention integration-test gap (test-only).
- **#546** — canonical subsystem folios (health/diagnostics, server-mgmt, settings, BTD6, games, media).
- **#544** — freshness-oriented docs route, lifecycle labels, ideas area, and subsystem-folio model.
- **#543** — boot / test-bot capability doc correction.
- **#542** — docs reconciled to shipped bot-awareness status.
- **#541** — bot-awareness **PR4–PR6**: grouped recent-error findings (opt-in),
  owner-gated `diagnostics_health_snapshot` AI tool (D1 resolved), persistent
  operational-health findings (migration `057`).
- **#539** — AI extra-tool capability **ideas backlog** (capture only, not approved work).
- **#537** — bot-awareness **PR1–PR3**: health contracts + aggregator, `!platform
  health`, startup-health snapshot.
- **#535** — back-to-Help navigation fix; stability baseline accepted.

> Older than this: see `docs/planning/*` trackers and `docs/decisions/*` ADRs.

## Next candidates

- Health/diagnostics maintainer live-tests (production AI tool + grouped findings):
  see `docs/subsystems/health-diagnostics.md`. The migration `057`
  persistence/dedupe/retention integration gap is **closed** (this session — real-PG
  integration suite + static SQL-shape pin; CI-safe skip).
- Use the canonical subsystem folios for area-specific implementation/planning; keep
  this global router thin.

## Gates / blocked work

- **AI / BTD6 feature expansion** is gated on *all* of: bot-wide stability **+**
  provider/provenance checks **+** caching / source-health clarity **+** AI
  behavior/config correctness — **not** just the RC-11 guard suite passing.
- **BTD6 data extraction** stays paused pending the **ADR-006** provenance schema.
- `_derive_scope` → `PLATFORM_OWNER` (decision D1) — **RESOLVED** in #541; owner-only
  AI tools are now reachable.

## Known UX follow-ups (not stability bugs)

- Server-management member/role UX follow-ups: see
  `docs/subsystems/server-management.md`.
- Dense DiagnosticCog platform-subview pagination idea: see
  `docs/subsystems/health-diagnostics.md`.

## Off-limits / do-not-propose

- No Redis / external state store (**ADR-001**).
- Game state is **not** restart-safe by design (**ADR-002**) — accepted, not a bug.
- Do not re-litigate the rejection ledger in
  `docs/planning/superbot-ideas-lab-2026-06-05.md` §6.
- Do not restate "bot fully tested & working" as *newly* verified without an actual
  boot + live walk — cite the #535 baseline instead.

## Where to read next (the read path + what lives where)

| Need | Read |
|---|---|
| **How we collaborate** (all agents — the working model, read first) | `docs/collaboration-model.md` |
| Rules of engagement (CI parity, CodeGraph, arch invariants, workflow) | `.claude/CLAUDE.md` |
| **What's true right now** | this file |
| How to boot/operate the sandbox · maintainer preferences · hard-won rules · gotchas | `.session-journal.md` (guidebook head) |
| What happened in past sessions | `.session-journal.md` (session log) |
| Which docs to read for a specific task | `docs/AGENT_ORIENTATION.md` |
| Deep-dive on one part of the bot (AI, BTD6, server-mgmt…) | `docs/subsystems/<area>.md` (start here for an area) |
| Architecture / ownership / runtime contracts (binding) | `docs/architecture.md` · `docs/ownership.md` · `docs/runtime_contracts.md` |
| Brainstorms (not approved) | `docs/ideas/` |
| Plans / target architecture (historical once shipped) | `docs/planning/` |

**One-fact-one-home rule:** if a fact belongs in one of the homes above, **link** to
it — do not restate it here. Restatement across files is where drift breeds. In
particular, **don't summarize plans'/trackers' PR numbers or status here** — link to the
folio or tracker, which is authoritative for its own area.

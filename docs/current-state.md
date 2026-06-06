# SuperBot — Current State

> **Doc type:** living status ledger (project state). **Not binding.**
> **Source code and merged PRs always win over this file.**
> The In-flight section below is a dated snapshot — **verify open PRs against
> live GitHub** before trusting it (two same-session reports already
> contradicted each other across a single merge).
>
> **Last updated:** 2026-06-06 · `147f396` (post-#543) · doc-restructure session.
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

As of this stamp: **none — 0 open PRs.** Re-check on every session start; this line
goes stale the moment a branch is pushed.

## Recently shipped (newest first)

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

- **Maintainer live-tests owed** (need a prod AI key + a human in Discord): PR5 — ask
  the bot "how healthy are you?" → it calls `diagnostics_health_snapshot` (a non-owner
  admin must NOT be offered it); PR4 — `HEALTH_GROUPED_FINDINGS=1` → grouped `(×N)`
  findings; PR6 — restart with a recurring failure → `occurrence_count` increments.
- **In-sandbox integration test** of PR4/PR6: boot the test bot + local Postgres →
  migration `057` applies → findings persist → `SELECT` to confirm `ON CONFLICT`
  dedupe (the PR6 unit tests mock the DB, so this closes a real gap).
- **This doc-restructure** (in progress).

## Gates / blocked work

- **AI / BTD6 feature expansion** is gated on *all* of: bot-wide stability **+**
  provider/provenance checks **+** caching / source-health clarity **+** AI
  behavior/config correctness — **not** just the RC-11 guard suite passing.
- **BTD6 data extraction** stays paused pending the **ADR-006** provenance schema.
- `_derive_scope` → `PLATFORM_OWNER` (decision D1) — **RESOLVED** in #541; owner-only
  AI tools are now reachable.

## Known UX follow-ups (not stability bugs)

- Moderation member entry wants a `discord.ui.UserSelect` quicksearch picker
  (modal→view restructure; `unban` stays ID-based).
- Role UX: bulk "Clear missing" on time/XP panels; selector-ize Edit Role.
- DiagnosticCog `platform_*` subviews are dense — could paginate.

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
it — do not restate it here. Restatement across files is where drift breeds.

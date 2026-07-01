# Thirty-first Q-0107 reconciliation pass — band-#1620 (2026-07-01)

> **Status:** `historical` — pass record for the thirty-first Q-0107 docs-only reconciliation +
> planning pass. Triggered by `reconcile` issue **#1622** (auto-opened by
> `reconciliation-trigger.yml` when merged PRs crossed the #1620 boundary). Marker reset
> #1590 → **#1620**.

## What this pass did

Reconciled the ledger for band **#1591–#1620** (the work merged since the thirtieth pass, whose
own PR was #1591 / marker #1590), de-staled the docs, disposed open PRs, refreshed the dashboard
export, confirmed the forward queue is still deep, reset the marker, and wrote back the standing
enders.

## Ledger reconciliation (band #1591–#1620)

`check_current_state_ledger.py --strict` and `check_docs.py --strict` were both green on entry
(the 28-PR newer-than-marker list was reported as **benign lag**, the informational class the
checker explicitly does not treat as drift). Added the band as **seven grouped Recently-shipped
entries**, then trimmed the list back to the 20-entry ratchet with `trim_recently_shipped.py
--apply` (floor pointer recomputed — moved the oldest 7 bullets: #1532-pass · #1504-fishing ·
#1513-cert · #1512-game-view · #1510-BTD6 · #1522-router · #1502-pass into the archive):

1. **#1591 + 5 dashboard refreshes** — the thirtieth Q-0107 pass (band-#1590) + five per-source-merge
   dashboard refreshes (#1593 · #1597 · #1604 · #1606 · #1616, Q-0167).
2. **S1 fishing — coral structures arc** (#1596 · #1598 · #1603 · #1605) — a coral deepwater
   rare-material drop → cosmetic curio collectibles, the Dock (bite-speed) and Boathouse
   (energy-regen) coral structures, folded with the Tide Pool into a 🏗 Structures sub-hub.
3. **S1 reaction-roles menu builder** (#1608 · #1612 · #1613 · #1615) — fixed the ephemeral
   role-menu builder preview never updating, and adopted the layout-sim's slim/lean 2-row builder
   (owner-directed after the 14-button builder felt dense).
4. **S1 XP import/migration** (#1607 · #1610) — XP/level migration from other bots via an Arcane
   level-up-channel scan, plus a button entry point + generic "import from another bot" framing.
5. **S1 server-logging depth** (#1594 · #1618 · #1619) — ignored-channels/users exclusion lists, a
   subject avatar in every log embed, and a per-route binding-crash + disappearing-back-button +
   settings-order simulation fix.
6. **S1 completion + owner override + boot guard** (#1602 · #1599/#1600/#1601 · #1595 · #1609 ·
   #1614 · #1620 · #1611) — the bot owner now bypasses ALL permission gates (not just
   `administrator`); a boot smoke-test CI guard that fails the build when a cog won't load
   (defense-in-depth after the #1599/#1600 cog-load outage); plus completion-first punches —
   inventory rarity-tier detail fields, user-tier `!ping`/`!botinfo`/`!membercount` + tests,
   rank/leaderboard visual polish out-reading Arcane/MEE6, karma reaction-to-thank, and treasury-cog
   tests.
7. **S2 BTD6** (#1617) — a BTD6 menu layout simulator + a round-range NL answer fix; the owner
   picked Layout B and the panel category-hub is in flight as #1621.

## Open-PR disposition (Q-0125)

Eight PRs open at pass time, **none a stale `claude/*` session PR to close**:

- **#1621** — `claude/*` "BTD6 panel: Layout-B category hub" — **in flight** (born-red card,
  `mergeable_state=blocked` = the born-red merge gate holding it). An active session PR; left to
  finish and auto-merge.
- **#1509** — `menno420` "Add repo-grounded unfinished-work audit" (codex-labeled, open since
  2026-06-27) — **left for the owner**, consistent with the thirtieth pass's explicit disposition
  (not an agent-disposable session PR; its point-in-time findings were already reviewed in
  #1510/#1511). Noted as long-open so the owner can dispose it.
- **#1555–#1560** — six `dependabot[bot]` dependency bumps (fastapi, python-minor-patch group,
  openai, pillow, asyncpg, prometheus-client). Owner/dependabot domain — left as-is.

No redundant ledger PR to close this band; nothing to fix for red CI.

## Control-plane (Q-0135)

`check_loop_health.py` **SKIP** (`gh` / `GITHUB_TOKEN` unavailable in this environment). Did the
live read via the documented MCP fallback: the newest `reconcile` issue **#1622** was authored by
**`menno420`** (a real-user login) → **ROUTINE_PAT is set and the loop self-fires**. Consistent
with the canonical control-plane table; no row flip needed.

## Planning — the next full band (Q-0144 + Q-0164)

Assessed forward-queue **depth ≥ the cadence** (≥30 PRs of genuine buildable work). The queue is
comfortably deep across sectors — **no `PLAN-BACKLOG-THIN` flag**:

- **S1** — mining structures/skill-tree remaining slices (Home / respec-polish / titles), `myprofile`
  PR A (turn-key), help home/navigation plan, settings Phase 2 tail → Phase 3, image moderation,
  security tiers 1+2, NL event scheduler, and the standing completion-deepening lane the band
  #1591–#1620 kept feeding (fishing / reaction-roles / XP / logging / karma).
- **S2** — the #1621 Layout-B panel hub (in flight), curated counter lists, BTD6 decode items 3–4,
  the owner-led Q-0086 live walk.
- **S3** — the owner-re-elevated AI-memory substrate-kit (PR 2 remainder + PR 3), the consistency-linter
  AI-nav PR 1, procedures→skills Batch 2.
- **S5** — the website two-site rollout + its security-review-gated slices (owner/Hermes-paced).

Per recent-pass precedent the roadmap + per-sector queues (`current-state/S*.md`) already hold well
over a band's worth of buildable work, so the queue is **carried intact** rather than re-authored as a
fresh decade list. `roadmap.md` defers the live "what's startable now" pointer to `current-state.md`
▶ Next action, which the sector table refresh above keeps current.

## Dashboard export

Regenerated `dashboard/data/dashboard.json` with `export_dashboard_data.py` (the cadence half of the
Q-0167 freshness loop). See the commit for the structural delta.

## Runtime bugs noticed (step 3)

None. The band's one incident — the #1599/#1600 cog-load boot outage — was already **root-fixed** in
the same band by the boot smoke-test CI guard (#1601), so there is no OPEN bug to append to the
bug-book from this pass.

## Standing enders

- **Q-0089 idea:** see `docs/ideas/` (added this pass — recorded in the session log).
- **Q-0102 previous-session review:** see the session log.
- Marker reset #1590 → **#1620**; the thirtieth pass re-badged `historical`.

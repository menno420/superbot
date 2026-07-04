# Thirtieth Q-0107 reconciliation pass — band-#1590 (2026-06-30)

> **Status:** `historical` — pass record for the thirtieth Q-0107 docs-only reconciliation +
> planning pass. Triggered by `reconcile` issue **#1591** (auto-opened by
> `reconciliation-trigger.yml` when merged PRs crossed the #1590 boundary). Marker reset
> #1560 → **#1590**.

## What this pass did

Reconciled the ledger for band **#1561–#1590** (the work merged since the twenty-ninth pass,
whose own PR was #1564 / marker #1560), de-staled the docs, disposed open PRs, refreshed the
dashboard export, reflected one planning-relevant owner directive, reset the marker, and wrote
back the standing enders.

## Ledger reconciliation (band #1561–#1590)

`check_current_state_ledger.py --strict` and `check_docs.py --strict` were both green on entry
(the 27-PR newer-than-marker list was reported as **benign lag**, the informational class the
checker explicitly does not treat as drift). Added the band as **seven grouped Recently-shipped
entries** (#1561 was already carried by the prior pass), then trimmed the list back to the
20-entry ratchet with `trim_recently_shipped.py --apply` (floor pointer recomputed):

1. **#1564 + 6 dashboard refreshes** — the twenty-ninth Q-0107 pass (band-#1560) + six
   per-source-merge dashboard refreshes (Q-0167).
2. **Bot-owner platform-admin override** (#1573 · #1577 · #1582) — full bot-config authority in
   any guild for the bot owner, a completeness follow-on (view gates + admin command decorators),
   and an ephemeral persistent-panel ownership fail-close fix. Follows the Q-0211 give-collision
   prod hotfix from the prior band.
3. **S1 feature-completion certification deepening** (Q-0209; #1565 · #1566 · #1568 · #1575 ·
   #1588) — cert sync/de-stale, cleanup history content-type/age filters, counters completion
   (presets + slash + channel-type/integration tests) and a per-guild loop-backoff punch, and the
   spam-duplicate window promoted to a real per-guild setting.
4. **Reaction-roles + fishing + game depth** (#1570 · #1571 · #1585 · #1581) — role-menu live
   signup counts (migration 103), the fishing rod-recipe browser, and welcome age-gate/delete-after
   close-out.
5. **Workflow / orientation system** (#1569 · #1574 · #1584 · #1586) — the AI answer-storage /
   review-backlog loop + a `check_quality` artifact-freshness guard, a journal ruff-scope rule, and
   the **orientation-cost-reduction plan** (CLAUDE.md + router conciseness).
6. **BTD6** (#1572 · #1578) — captured a prod DDT-confabulation finding into the regression corpus
   from the review-log export; track lengths (Red Bloon Seconds) + estimator escape-margin.
7. **Owner-vision capture** (#1589 · #1590) — the maintainer's **fresh-rebuild vision** +
   verified Fable 5 research, with two maintainer fact-corrections folded in.

## Open-PR disposition (Q-0125)

Seven PRs open at pass time, **none a stale `claude/*` session PR**:

- **#1555–#1560** — six `dependabot[bot]` dependency bumps (prometheus-client, asyncpg, pillow,
  openai, python-minor-patch group, fastapi). Owner/dependabot domain — left as-is.
- **#1509** — `menno420` "Add repo-grounded unfinished-work audit" — the owner's own PR. Left for
  the owner (not an agent-disposable session PR). Noted as long-open so the owner can dispose it.

No redundant ledger PR to close this band; nothing to fix for red CI.

## Control-plane (Q-0135)

`check_loop_health.py` **SKIP** (`gh` / `GITHUB_TOKEN` unavailable in this environment). Did the
live read via the documented MCP fallback: the newest `reconcile` issue **#1591** was authored by
**`menno420`** (a real-user login) → **ROUTINE_PAT is set and the loop self-fires**. Consistent
with the canonical control-plane table; no row flip needed.

## Planning — band depth + the owner re-elevation

**No `PLAN-BACKLOG-THIN` flag.** Buildable depth across the per-sector queues remains well over the
30-PR cadence (S1 certification follow-ons, BTD6 decode ⭐ item 3 + eval cases, P1-1 eval-smoke
matrix, reaction-roles overhaul tail, fishing acquisition depth, the AI-memory substrate-kit
remainder, website rollout). The band carried the existing forward queue intact (no §4 queue slice
executed → `mixed` archetype).

**One planning-relevant owner directive, reflected:** the captured fresh-rebuild vision (#1589/#1590)
**re-elevates the AI-memory portable substrate-kit to top focus** — "bot is mostly production ready,
focus on the AI-memory project now." This reverses the band-#870 §6 demotion (the kit was dropped
from the plannable queue after its fourth band-carry, "returns when the owner re-steers it"). The
owner has now re-steered it. The roadmap **S3 Now already points to the substrate-kit**; this pass
records the re-elevation in `current-state.md` S3 + the cross-sector caveat so the demotion language
no longer reads as live. The kit's *extraction to a standalone repo* stays an **owner action**
(zero code-coupling confirmed, finding #7 of the vision doc); the agent-buildable remainder is **PR 2
remainder + PR 3** of
[`portable-substrate-kit-extraction-2026-06-13.md`](portable-substrate-kit-extraction-2026-06-13.md).
The full rebuild itself stays **idea-stage, not approved** — gated on Fable 5 (withdrawn since
2026-06-12, re-check the live picker not the docs), the owner's keep/change spec, and a multi-agent
planning sequence.

## Runtime bugs noticed

None new this pass. The open bugs (BUG-0009, BUG-0011) remain in
[`../health/bug-book.md`](../health/bug-book.md).

## Marker

`Last reconciliation pass: PR #1560` → **#1590**. Next docs-only reconciliation due once merged PRs
cross **#1620**.

# Forty-seventh Q-0107 reconciliation pass — band-#2100

> **Status:** `historical` — dated pass record. The live state is
> [`../current-state.md`](../current-state.md) ▶ Next action + Recently-shipped.
> **Trigger:** `reconcile` issue **#2101** (auto-opened by `reconciliation-trigger.yml`
> at the #2100 boundary). **Run type:** routine · reconciliation. **Date:** 2026-07-14.

## Scope reconciled

Band **#2072–#2100** (marker #2071 → #2100). **Mostly docs/control/tooling** with **one
`disbot/` runtime fix** (#2089) and seven Dependabot dep-bumps. Non-docs surfaces: the
`disbot/views/mining/grid_mine_view.py` one-line fix + its regression test (#2089),
`dashboard/data/*` + `botsite/data/*` (generated exports), `control/inbox.md` appends,
`telemetry/model-usage.jsonl`, dependency pins, and `.sessions/` cards.

The band spans 2026-07-13 → 07-14: an owner-directed mining runtime hotfix, three
fleet-manager relay ORDERs, the 46th-pass reconcile PR + its owner-live session doc, the
repo-audit PR-cleanup + EAP final-closeout, and the steady dashboard-refresh / Dependabot
background.

### Grouped ledger entries added

1. **`!mine` runtime bug fix** (#2089) — the band's only `disbot/` change. `build_grid_embed`
   passed a stringified `suid` to the BIGINT-keyed `db.get_skills`, so asyncpg raised `DataError`
   on every `!mine` open (the Mining Hub never reads `player_skills` on its overview path, which is
   why only `!mine` broke); introduced by `0c4b70b6` (BUG-0026). Fixed to the int `user_id` + a
   real-Postgres regression guard (the mocked-DB unit test couldn't see the type mismatch).
   Owner-directed from a Discord screen-recording; a repo-wide sweep found `grid_mine_view.py:48`
   the sole instance of the footgun class.
2. **Fleet-manager relay ORDERs** (#2087 · #2090 · #2094) — three append-only `control/inbox.md`
   ORDERs relaying coordinator dispatch to the hub seat: ORDER 003 (I1b frozen-trigger disposition
   — two dormant owner-paused pre-fleet dispatch triggers, recommend delete/annotate-and-leave-paused,
   + a dispatch-console doc-drift rider), ORDER 004 (EAP final-night worklist, fm ORDER 045 relay),
   ORDER 005 (supersession pointers on three superseded superbot docs → their living fleet-manager
   counterparts). Each premise-checked against source per Q-0120.
3. **Reconcile PR + session doc + repo-audit + EAP closeout** (#2074 · #2088 · #2092 · #2096) —
   #2074 the forty-sixth Q-0107 reconcile PR (band-#2070); #2088 the 07-13 owner-live review +
   cross-repo merge sweep session doc + enders; #2092 the repo-audit PR cleanup; #2096 the EAP
   final-closeout.
4. **Dashboard refreshes + Dependabot** — eleven `dashboard/data/dashboard.json` regenerations
   (#2075 · #2076 · #2085 · #2086 · #2091 · #2093 · #2095 · #2097 · #2098 · #2099 · #2100, Q-0167)
   and seven grouped Dependabot bumps (#2077 codeql-action · #2078 actions/checkout · #2080
   upload-artifact · #2081 actions/cache · #2082 uvicorn · #2083 python-minor-patch group · #2084
   openai), landed under the Q-0256 auto-merge policy.

## Ledger / docs state

- `check_current_state_ledger.py --strict` — green after reconcile (pre-edit showed only the
  benign newest-merge lag; the 24 newer PRs were this band).
- `check_docs.py --strict` — green (census: total docs 843; top-level 21/21; Recently-shipped
  20/20; ▶ Next action callout within budget). The 5 supersede-banner soft warnings are honest
  cross-repo supersessions (successors in fleet-manager `projects/superbot-next/`, registry PR #39)
  the in-repo checker can't model — carried forward.
- Trimmed Recently-shipped 24 → 20 (moved the 4 oldest bullets to the archive, floor recomputed).
- Dashboard export refreshed (`export_dashboard_data.py`).

## Open-PR disposition (Q-0125)

- **#2061** — mineverse FLAG 2 (HMAC-signed mining WRITE endpoint), **draft, owner-held** for
  deploy-safety (Q-0193). Left in flight — the owner controls the deploy moment.
- **#2058** — mineverse FLAG 1 (mining snapshot READ-relay): **merged to main mid-pass** — the owner
  flipped it ready from its held draft during this reconcile. It is a late low-numbered merge
  (2058 < the band floor), so it is recorded as its own Recently-shipped entry and the marker stays
  at the highest, **#2100**. The pass branch merged origin/main to absorb it before ship.

No stale session PR; no red-CI orphan to fix.

## Control-plane (Q-0135)

`check_loop_health.py` returned SKIP (`gh` / `GITHUB_TOKEN` unavailable in the container). MCP
fallback per the routine: `reconcile` issue **#2101** authored by `menno420` (a real-user login)
→ **ROUTINE_PAT set / the loop self-fires**. No control-plane table drift to correct.

## Plan band (Q-0164)

Forward queue still deep — the rebuild live in **superbot-next** (parity-row drain + D-0043
deep-game go/no-go) plus the live **SuperBot Project 8-seat program** dominate the buildable
backlog well past the next-band cadence. **No `PLAN-BACKLOG-THIN` flag.**

## Runtime bugs noticed (Q-0107 step 3)

None new this pass — the band's own runtime issue (#2089 `!mine`) was already fixed in-band, not
by this docs-only pass.

## Q-0089 idea + Q-0102 review

Recorded in the session log
[`../../.sessions/2026-07-14-reconcile-band2100.md`](../../.sessions/2026-07-14-reconcile-band2100.md).

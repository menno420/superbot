# Session handoff — 2026-07-11 fleet-management arc (post-compact / fresh-session START HERE)

> **Status:** `reference` — the durable record + continuation brief for the long
> 2026-07-11 owner-directed fleet-management session (chat neared auto-compact). Everything
> important is committed (this file + the merged PRs below); nothing load-bearing is chat-only.
> A fresh session reads THIS first, then the linked plans.

## 0. What this session did (the arc — all merged to `main`)

Owner-directed global fleet management + planning/triage. Deliverables, all landed:

| PR | What |
|---|---|
| superbot **#1998** | Full-fleet verified review + triage · fleet-manager-as-SSOT centralization plan · 6-prompt dispatch kit (+ permissions/workarounds block) |
| superbot **#2000** | Bug fix: `check_consistency.py` Rule 6 (`settle_once_adoption`) — activated the inert `cogs/` scope + graduated warning→error (money-safety false-green) |
| superbot **#2002** | Folded the substrate-kit gen-3 coordinator lessons into the dispatch permissions block |
| superbot **#2004** | Synthesis of 4 external strategy reviews + Codex-PR dispositions |
| superbot **#2005** | Consolidation blueprint (4 owner decisions → project fates + cutover threshold) **+** the verified/improved next-round founding-prompt kit |
| **venture-lab #49** | 🔴 Real-money fix: membership-kit `/webhook` now fails CLOSED on partial Stripe config (was granting from unsigned JSON) — merged |

## 1. The FOUR finalized owner decisions (2026-07-11, via question panel)

1. **Next round = first external revenue** — the $29 Stripe Webhook Test Kit is the one-week
   flagship, run as an **Owner Launch Hour** (one pre-filled atomic packet).
2. **Core 6 → 5** — merge **idea-engine + sim-lab** into one **Ideation→Evidence** seat
   (internal generate→verify split; kills the idea→sim inter-project wait).
3. **All games → ONE Games Project**, one flagship at a time — **flagship = the Mining
   browsergame (superbot-mineverse)**.
4. **superbot-next cutover = a concrete threshold** (49/49 ported · parity green *with* the
   F-003 false-green fix · wallet-race fixes landed+concurrency-tested · 1 live-drive · 7-day
   shadow → CUT-3 token swap).

## 2. Entry points (all merged; read these to continue)

- Review + triage: [`planning/fleet-review-2026-07-11.md`](../planning/fleet-review-2026-07-11.md)
- Centralization plan: [`planning/fleet-centralization-plan-2026-07-11.md`](../planning/fleet-centralization-plan-2026-07-11.md)
- Strategy synthesis: [`planning/fleet-strategy-synthesis-2026-07-11.md`](../planning/fleet-strategy-synthesis-2026-07-11.md)
- **Consolidation + next-round blueprint (fates + cutover):** [`planning/fleet-consolidation-and-next-round-2026-07-11.md`](../planning/fleet-consolidation-and-next-round-2026-07-11.md)
- Dispatch kit (6 prompts + permissions block): [`../owner/dispatch-prompts-2026-07-11.md`](../owner/dispatch-prompts-2026-07-11.md)
- **Next-round founding-prompt kit (verified + improved + 2 merged-Project bodies):** [`../owner/next-round-founding-prompts-2026-07-11.md`](../owner/next-round-founding-prompts-2026-07-11.md)

## 3. Fleet wrap-up status (~2026-07-11 20:00Z)

Owner sent every project the wrap-up/archive-prep prompt. Verified per-repo:

- **12/14 FINISHED** their session enders + wrote `docs/retro/archive-ready-2026-07-11.md`
  (chats **safe to archive**): superbot-next, substrate-kit, websites, venture-lab,
  superbot-idle, superbot-mineverse, gba-homebrew, pokemon-mod-lab, trading-strategy, sim-lab,
  idea-engine, product-forge.
- **superbot-games — PARTIAL:** its `control/status.md` was stale (pre-prompt) and its
  world-games lane had open PRs (see §4). Needs a repo-wide wrap-up after those land.
- **fleet-manager — LIVE, not self-archived (intended):** it's the coordinator, still building
  the **centralization** (P2 done = PR #85 owner-queue generator; **P3 in-flight = PR #86**,
  born-red). Owner has NOT sent it the wrap-up yet (deliberate — let it finish P3 first).

## 4. Merge session (this turn — owner authorized "review + merge all open PRs that are done")

**MERGED** (green, mergeable, card-complete): **gba-homebrew #57 · websites #141 ·
superbot-games #57, #53, #50.**

**⏳ PENDING — superbot-games #52/#54/#55 need a rebase** (they collide on floor/index files
after #50/#53 merged). Exact continuation:
- superbot-games `main` HEAD = `3250181`. `tests/dnd/EXPECTED_MIN_TESTS.txt` on main = **27**
  (set by #50). Clone: `git clone https://github.com/menno420/superbot-games`.
- **#52** (branch `dnd-clamp-fuzz`, seeded DM-clamp property-fuzzer): rebase onto main →
  set `tests/dnd/EXPECTED_MIN_TESTS.txt` = **31** (27 + its 4 fuzz functions) → verify
  `python3 bootstrap.py check --strict` + `python3 tests/check_suite_floors.py` (exit 0) →
  push --force-with-lease → merge.
- **#54** (branch `economy-cross-domain-sim`): rebase → resolve `docs/design/shared-index.md`
  (add its economy-sim entry *after* #53's persistence entry) + it registers a new suite
  `tests/shared/sim` in `tests/EXPECTED_SUITES.txt` (add the line) with floor 7 → verify → merge.
- **#55** (branch `auto-balance-page`): rebase → resolve `shared-index.md` (add its balance
  entry) → verify `python3 tools/gen_balance.py --check` (freshness) → merge. **Do #54 before
  #55** (the balance page folds in the economy-sim numbers).
- Order: **#52 → #54 → #55.**

**🚩 FLAGGED — owner decision / not cleanly done (NOT merged):**
- **venture-lab #51** ("Add files via upload") — adds **10 dated `.jpg` photos to the repo
  ROOT** of the *public* venture-lab (`20250818_211805.jpg` … `20260627_211646.jpg`). Looks
  **accidental** (personal phone photos), not revenue-lane content. **Owner: close it, or say
  where they should go.** Do NOT merge as-is (personal images → public repo).
- **substrate-kit #238 + #220** — `do-not-automerge` bench-pin PRs, **owner-ratification-gated
  by design** (kit-quality green). Owner ratifies (merge) or closes each.
- **superbot-next #196 + #206** — Codex review *reports* (docs-only). Required gate green, but
  the non-required `checkers` job is RED (docs-hygiene — orphan/no-Status-badge; risks
  pre-reddening future superbot-next PRs). Leave for the **superbot-next lane to consume + close**
  — the findings (F-001/F-002/F-003 wallet races + parity false-green, **plus new farm/mining
  money races in #206**) are within the Sonnet-5 fix mandate.
- **superbot-mineverse #31** — Codex security report; red gate (no session card). The
  CSRF/state-binding + snapshot-schema findings are now the **Games-project flagship** mandate
  (fix before provisioning secrets).
- **fleet-manager #86** — born-red centralization **P3**, live coordinator work. Leave.

## 5. Owner-action queue (the short "only you" list — carried; canonical = `fleet-manager/docs/owner-queue.md`)

- **💰 Revenue (highest leverage):** Stripe test keys → publish the 3 venture-lab kits (test-kit
  first) + the gotcha article. venture-lab fail-open is fixed (#49) — safe now.
- **🔧 Routines:** attach each lane repo to its routine + set model per routine (fixes the
  add_repo denials + model mismatch); make `pytest` a required check (mineverse first).
- **🖱️ One-clicks:** Lumen Drift Release · product-forge GitHub Pages · **"push the plugin
  seed"** (unblocks idle+games) · substrate-kit #181 + #238 + #220 ratify · merge/close
  venture-lab #51.
- **🔑 Provision (when ready):** mineverse 6 env vars *after* its CSRF fix · websites
  `DATABASE_URL` + `GITHUB_TOKEN` · project-scoped Railway tokens (never the account key).

## 6. Next steps (post-compact / fresh session)

1. **Finish superbot-games #52/#54/#55** (rebase details in §4).
2. **Apply the next-round founding-prompt kit** to the `fleet-manager/projects/` registry
   (edit-registry-first — the manager folds the §2 gen-3 rider + §3 per-project updates +
   creates the 2 merged-Project dirs [Ideation→Evidence, Games] + marks codetool-labs archived
   + re-syncs the stale v1 coordinator/failsafe companions to v2). Owner re-pastes changed
   Custom Instructions.
3. **Let fleet-manager finish centralization P3 (#86)**, then send it the wrap-up.
4. **Dispatch the leaner next round** (7 standing Projects, revenue-first) using the kit.

## 7. Durable findings to carry (verified this session)

- **Live human context IS the permission** — this hub session merged fleet PRs only under the
  owner's live in-chat authorization.
- **Codex this round was accurate** (no phantom commits); its real findings verify against source.
- **substrate-kit gate false-green is FIXED on main** (#228 — verified; the "empty PR" report
  was a mid-flight snapshot).
- **The drift is concentrated:** fleet-manager (roster/queue) + the v1 companion prompts;
  guards proposed in the centralization plan + the next-round kit.

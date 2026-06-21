# 2026-06-21 — BTD6 data: auto-seed the postgres blob store on boot

> **Status:** `complete`

## Arc
Owner asked two things: (1) confirm the bot actually uses the DB backend, and
(2) "shouldn't the data be auto-seeded by now? I used to run `seed-data` manually."

**Confirmed: production uses postgres** (`BTD6_DATA_BACKEND=postgres`) — per the
2026-06-12 readiness map AND proven by the 2026-06-10 drift incident (a `file`
backend physically can't drift; only a blob store can). So data PRs are not live
until the store is re-seeded — and **seeding was NOT automated** (no boot caller;
manual `!btd6ops seed-data` only). This also means my earlier "ships live, no manual
step" claims (after #1249/#1251) were **wrong for the postgres backend** — corrected.

Found Q-0077 was already **decided (b) on 2026-06-19** (auto-seed when bundled is
strictly newer) but **never built** — that's why it was still manual.

## Shipped (PR #1255)
- **`btd6_data_service.auto_seed_enabled()`** (postgres + `BTD6_AUTO_SEED` kill-switch)
  + **`bundled_newer_than_served()`** (strict numeric version compare).
- **`BTD6Cog.cog_load`** — when both are true, `seed_postgres_from_files()` (beside the
  #676 drift warning). Defensive: failure logs + serves existing store; never clobbers a
  deliberately-newer store. So a **version bump** is now zero-touch on deploy.
- Config flag, tests (gating + version compare), router Q-0077 → IMPLEMENTED,
  `subsystems/btd6` + `data-backends` docs, regenerated `env-vars.md` + dashboard/site.

## Decision (owner, in-session)
Asked content-aware vs strict (b) — **owner chose strict (b)**: version-newer only.
Accepted tradeoff: a **same-version data edit does NOT auto-apply** (needs manual seed).
Recorded against Q-0077.

## Verification
- `python3.10 scripts/check_quality.py --full` → **all checks passed ✓** (11362 passed).
- `check_generated_artifacts_fresh --strict` → OK (4 artifacts fresh, incl. the new env var).
- Ledger + docs `--strict` green.

## Context delta
- **The recurring miss this whole chain made, now fixed:** "the data/code is in the repo"
  ≠ "it's live." Production serves postgres blobs, not the merged files. Any "it's live"
  claim must check the *serving path* (backend + seed state), not just the merge. Now loud
  in `subsystems/btd6` + this is the natural `.session-journal` lesson.

## ⟲ Previous-session review
The #1251 (multi-target) session — and #1249 before it — did solid, verified work, but
both (and my replies) asserted the feature "answers live" **without checking the production
serving path**. Postgres serves a seeded blob store, so a merged data PR is NOT live until
seed-data runs — which strict (b) *still* won't do for those same-version buff edits. The
sessions verified against the local file backend (correct there) and over-generalized to
"production." **Workflow improvement (applied):** before telling the owner something is
"live in prod," confirm the runtime data path — for BTD6 that's `BTD6_DATA_BACKEND` +
whether a seed is needed. A correct local test ≠ a correct production claim.

## 💡 Session idea
**Content-hash drift surfacing (not auto-seed).** Strict (b) intentionally ignores
same-version data edits, so a buff-stat fix silently won't go live until someone seeds.
`served_data_drift()` is version-only, so it won't even warn. Idea: add a **sha-based**
drift check (compare bundled vs served blob hashes) that *surfaces* "N data files changed,
same version — run seed-data" in the boot log + `!btd6 status`, WITHOUT auto-seeding
(honors the owner's strict-(b) choice). Closes the "silent same-version drift" gap with a
reminder rather than a write. (Captured, not built.)

## 📤 Run report
- **Did:** Confirmed prod uses postgres; implemented Q-0077(b) auto-seed-on-boot ·
  **Outcome:** shipped (PR #1255)
- **Shipped:** PR #1255 — auto-seed gating + cog_load wiring + config + tests + docs +
  regenerated artifacts
- **Run type:** `manual` (owner question → confirm + implement)
- **⚑ Owner decisions needed:** none (Q-0077 re-confirmed strict (b) in-session)
- **⚑ Owner manual steps:** **run `!btd6ops seed-data` ONCE** to make the #1249/#1251 buff
  windows live — they're version 55.1 (no bump), so strict (b) won't auto-apply them. After
  that, future *version bumps* are zero-touch.
- **⚑ Self-initiated:** the implementation was owner-prompted; the strict-(b) build follows
  the owner's recorded + re-confirmed decision (not self-initiated scope)
- **↪ Next:** content-hash drift surfacing (this session's 💡), or the alch attack-speed-buff
  modeling idea from #1251, else the current-state ▶ ungated lane

# superbot — EAP closeout walkthrough (2026-07-14)

> **Status:** `reference` — EAP final-day closeout walkthrough for the hub seat, per
> `control/inbox.md` ORDER 006 (b). Written 2026-07-14 against `main` @ `a785f97`;
> a dated snapshot — source and merged PRs win. Companion depth doc: the seat's
> [EAP project audit](audits/eap-project-audit-2026-07-14.md) (measured scale, verbatim
> permission walls, ranked pains, honest gaps). Indexed from
> [`docs/eap/README.md`](eap/README.md).

## A. What this seat did during the EAP

superbot is the fleet's founding hub: the oldest repo (first commit 2025-08-10, `330c7716`),
the live production Discord bot, and the birthplace of the agent workflow (born-red session
cards, claims, auto-merge doctrine, question router, reconciliation passes) that
substrate-kit later portable-ized to ~19 repos. Lifetime: ~1,991 merged PRs, 5,723 commits,
954 session cards ([audit §1](audits/eap-project-audit-2026-07-14.md) for all measured numbers).

During the EAP week itself (2026-07-07 → 07-14, PRs #1820 → #2103, ~283 PRs):

- **Ran the EAP evaluation program**: the 36-entry
  [evaluation log](planning/projects-eap-evaluation-log.md), the 11-test
  [permission probe](planning/projects-eap-permission-probe-report-2026-07-08.md) (PR #1830),
  the [program review](eap/eap-program-review-2026-07-10.md), night reviews
  ([07-11](eap/night-review-2026-07-11.md) · [07-12](eap/night-review-2026-07-12.md)), and
  the Anthropic email series (email 2 SENT 2026-07-12; email 3 send-ready — §C.3).
- **Bootstrapped two repos from inside the walls**: `substrate-kit` and `superbot-next`
  via the Contents-API workaround (eval log 2026-07-08) — the rebuild program's live home.
- **Built the fleet coordination layer**: git-as-message-bus (`control/inbox.md` /
  `control/status.md`), the manager-seat protocol
  ([fleet-coordination-protocol](planning/fleet-coordination-protocol-2026-07-09.md)),
  `scripts/fleet_status.py` (Q-0272).
- **Kept the production bot shipping** through the burst: e.g. #2089 `!mine` BIGINT runtime
  fix, the Dependabot sweep (#2077/#2078/#2080–#2084, 07-13), 47th reconciliation pass (#2102),
  plus the [fleet-cleanup audit](eap/fleet-cleanup-audit-2026-07-13.md) across all 20 repos.

## B. Current state + how to run/verify

- **State**: hub phase STEADY — coordination surface (docs/ledger/recon + fleet relay);
  product runtime work is lane-side in superbot-next (51/51 parity rows ported, CUT-1 done;
  cutover gate = owner ORDER 001 live-drive). Health green; only `disbot/` runtime change in
  the last band was #2089. Living ledger: [`docs/current-state.md`](current-state.md).
- **Merge = deploy (Q-0193)**: Railway project `reliable-grace` auto-redeploys `worker`
  (`python disbot/bot1.py`) on every merge to `main` — a merged change is live within
  minutes; nobody runs a manual deploy. Services: `worker`, `Postgres`, `dashboard`
  (FastAPI, `/healthz`), `botsite`. Canonical:
  [`docs/operations/production-deployment.md`](operations/production-deployment.md).
- **Verify commands (exact):**
  - `python3.10 scripts/check_quality.py --full` — true CI mirror (black/isort/ruff over CI
    scope, `mypy disbot/`, full pytest, docs checks). `--check-only` = fast lint pass.
  - `python3.10 scripts/check_architecture.py --mode strict` — layer-boundary gate.
  - `python3.10 scripts/check_current_state_ledger.py --strict` — every merged PR in the ledger.
  - `python3 scripts/check_docs.py --strict` — doc reachability (CI-exact form).
  - `python3.10 scripts/fleet_status.py` — one-command fleet orientation.

## C. OWNER ACTIONS checklist

1. **PR #2061 — mineverse FLAG-2 HMAC WRITE endpoint, held draft** — [pull/2061](https://github.com/menno420/superbot/pull/2061).
   Deliberate deploy-safety hold (merge = deploy, Q-0193); merged code stays inert until `MINING_WRITE_SHARED_SECRET` is set on Railway (+ `MINING_WRITE_GUILD_ALLOWLIST` scoping). Sibling #2058 (READ relay) you already flipped + merged 2026-07-14.
   **Recommendation: keep held; when you want the write path live, set the Railway secret first, then flip "Ready for review" — auto-merge lands it on green.**
   VERIFY: the PR page shows `Draft`; after a future flip, the Railway `worker` variables page shows the secret.
2. **ORDER 003 trigger-console click (yours — the pause was your action)** — Claude console, env `env_01CZRF681i8ef2zqt9GgboYy`: `trig_011XAWqPeksS8LBrS5G9RvVc` ("superbot autonomous dispatch") + `trig_01MWHvQFnRF1dVdZFSP6SM5L` ("superbot night executor").
   **Recommendation: delete both** — fm verdict: dormant owner-paused pre-fleet remnants; prompts preserved (fm snapshots + `docs/operations/hermes-dispatch-bridge.md`); do NOT re-enable as-is.
   VERIFY: the env's trigger list shows only the poke-only `suberbot docs reconciliation` enabled.
3. **Send Anthropic email 3 — window closes TODAY (2026-07-14)** — draft: [docs/eap/anthropic-email-3-draft-2026-07-13.md](https://github.com/menno420/superbot/blob/main/docs/eap/anthropic-email-3-draft-2026-07-13.md) (header: SEND-READY). Only you send.
   **Recommendation: send today**, on the existing Gmail EAP thread per the draft's send notes.
   VERIFY: the reply shows in the Gmail thread.
4. **fm-side ratifications** — WP-stack sweep-merge + 60-item DROP-list + a stamped decision in fm [docs/owner-queue.md](https://github.com/menno420/fleet-manager/blob/main/docs/owner-queue.md) (asks logged at `docs/eap/night-review-2026-07-13.md:106`).
   **Recommendation: ratify at the fm owner-queue in one sitting.**
   VERIFY: the owner-queue rows carry your decision stamp.
5. **Five open router DISCUSS Qs** — [docs/owner/maintainer-question-router.md](https://github.com/menno420/superbot/blob/main/docs/owner/maintainer-question-router.md): Q-0176 needs-hermes-review enabler skip (**close as superseded by Q-0197**) · Q-0183 correction-report ticket service (**keep parked for its own session** — your own flag) · Q-0238 CodeQL-alert merge hold (**approve the build**) · Q-0255 two stale kit pointers (**apply as-is per the Q's recommendation**) · Q-0257 dependabot auto-merge (**option 1 — status quo**).
   VERIFY: each Q gains an owner-answer line; no open DISCUSS blocks remain in the router.
6. **Delete stranded probe branch [`test/permprobe-0708`](https://github.com/menno420/superbot/branches)** — agents are hard-walled from remote-branch deletion ([audit §3](audits/eap-project-audit-2026-07-14.md)); harmless leftover from the #1830 probe.
   **Recommendation: delete.**
   VERIFY: the branch is gone from the branches page.

## D. 5-minute verify-it-yourself tour

1. **Discord (1 min):** run `!mine` in the guild — proves the live bot + the merge=deploy
   chain (the band's runtime fix, #2089).
2. **Web (1 min):** dashboard `/healthz` + botsite load; mineverse host
   `web-production-97636.up.railway.app` answers 200 (read-only degraded by design until
   the §C.1 flip).
3. **Repo (1 min):** open [`control/inbox.md`](../control/inbox.md) (ORDER-thread truth) →
   [`control/status.md`](../control/status.md) (heartbeat) → the newest `.sessions/` card →
   [`docs/current-state.md`](current-state.md).
4. **One command (1 min):** `python3.10 scripts/fleet_status.py` (fleet heartbeats), then
   `python3.10 scripts/check_quality.py --check-only` (fast green).
5. **GitHub (1 min):** [PR #2061](https://github.com/menno420/superbot/pull/2061) — the one
   open PR, deliberately held; then any recent merged `claude/*` PR to watch the auto-merge
   chain (born-red first commit → flip commit → auto-merged on green).

## E. Handoff — batons and what the next phase needs

- **ORDER states at closeout** (thread truth: [`control/inbox.md`](../control/inbox.md)):
  ORDER 001 **done** (#1977) · ORDER 002 **done** (#2003) · ORDER 003 **part-done** (doc
  annotations this session's scope; the console click stays owner-confirming — §C.2) ·
  ORDER 004 **part-done** (Dependabot sweep + email-3 prep done overnight; heartbeat
  re-stamp parked — this lane doesn't write `control/status.md`) · ORDER 005 — see the
  ORDER 006 ack in the inbox for the honest per-item accounting · ORDER 006 acked by this
  doc's PR.
- **Night-worklist residue (ORDER 004 items 4–8, none started):** recon-consistency guard
  (`docs/ideas/reconciliation-four-homes-consistency-guard-2026-07-12.md`) · casino triage
  trio (idea-engine V022/V025/V029) · one BTD6 build-direct slice · S4 pass-history trim
  ratchet · S2 curated counter lists — all parked with citations in the ORDER 006 ack.
- **Rebuild program (the next phase's main line):** plan of record
  [`docs/planning/rebuild-canonical-plan-2026-07-06.md`](planning/rebuild-canonical-plan-2026-07-06.md);
  live execution in **superbot-next** (51/51 parity rows, CUT-1 done; cutover gate = owner
  ORDER 001 live-drive). Never-wait doctrine: Q-0241. Seat-side baton: the #312→#371
  write-parity stack needs a non-mechanical rebase (#385 red).
- **Other batons:** website centralization design/reviews #2066/#2070 → websites lane ·
  next reconciliation at PR #2130 (routine-fired only, Q-0124) · `docs/CAPABILITIES.md`
  back-port + kit adoption for the hub (audit §11).
- **Open-PR honesty:** exactly one open PR (#2061, deliberately held draft — §C.1). No
  abandoned session PRs.

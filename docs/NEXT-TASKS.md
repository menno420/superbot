# SuperBot — Next tasks (fresh-start, 2026-07-17)

> **Status:** `reference` — the short ranked next-task set for the re-created Project.
> **Not binding — source code + merged PRs win.** superbot is **frozen as the behavioral
> oracle** for the `superbot-next` rebuild; the forward queue here is docs / oracle
> maintenance and a small number of owner-gated product/deploy calls, **not** new feature
> churn. Full live status: [`current-state.md`](current-state.md).

Context: the Claude Code Projects EAP goes **read-only Tue 2026-07-21**; the owner is
**winding down** the autonomous coordinator→worker apparatus and will **recreate the Projects**
with better coordination. (The mid-July "permission-classifier freeze" belief did not hold —
agents merge their own green PRs normally; see `current-state.md`.) These are the highest-value
next steps to pick up in the re-created project.

## Ranked next steps

1. **(Owner call — mineverse FLAG 2, the HMAC-signed mining WRITE endpoint.)** The prior
   attempt **PR #2061 was closed unmerged on 2026-07-17** (it carried a real merge conflict with
   `main` and a live web-write endpoint is an owner deploy-safety decision, so it was retired
   rather than rebased-and-held). FLAG 1 (#2058, the READ relay) is already merged and dormant. If
   the WRITE endpoint is still wanted, it reopens as **fresh work off the current `main`** (not by
   reviving the stale draft): re-port the executor, then take the **owner go/no-go** on activating a
   live web-write endpoint. If go: set `MINING_WRITE_SHARED_SECRET` + `MINING_WRITE_GUILD_ALLOWLIST`
   on Railway and the matching secret + `MINING_WRITE_ENDPOINT` on the mineverse web host.
   Owner-gated for deploy safety (Q-0193).

2. **Finish the `superbot-next` rebuild cutover, using superbot as the frozen oracle.**
   status.md reports 51/51 parity rows ported and CUT-1 done; drive the write-parity stack +
   energy-core integration to green and schedule the **CUT-3 token swap** under the reversible
   shadow-first path (N=7d rollback, reverse-import valve). Plan of record:
   [`planning/rebuild-canonical-plan-2026-07-06.md`](planning/rebuild-canonical-plan-2026-07-06.md)
   · design spec [`planning/rebuild-design-spec-2026-07-02.md`](planning/rebuild-design-spec-2026-07-02.md).

3. **Curate the backlog into one ranked set + archive the historical scaffolding.**
   Triage `docs/ideas/` (~248 files) + the live `docs/planning/` product designs into a short
   ranked list, and move the ~60 `docs/planning/reconciliation-pass-*.md` band logs and the
   dated `round3-*` / fleet-dispatch order docs out of the active planning surface into an
   archive subdir (updating their inbound links so `check_docs --strict` stays green).

4. **Complete the autonomy-apparatus wind-down (machinery teardown).**
   This PR corrected the *doctrine* in `.claude/CLAUDE.md` (merge doctrine, `silence = consent`,
   the boot-triad "no special limitations" rider, the born-red gate framing) and bannered the
   dead docs. The **machinery teardown** is deferred to the full wind-down when the Projects are
   recreated: retire `scripts/check_session_gate.py` + the `.sessions/` born-red mandate, and the
   autonomous-babysitting workflows (`reconciliation-trigger`, `codex-final-review`,
   `pr-auto-update`, `ci-rerun-watchdog`, `pr-conflict-guard`, and the control-plane
   `control/inbox.md` ORDER bus + `docs/owner/claims/` lane apparatus). **Keep
   `auto-merge-enabler.yml`** — it is the *working* server-side land-path (findings §7), retire it
   only as the last step of a full wind-down, never while autonomous PRs still flow.

5. **Refresh the remaining stale status surfaces.**
   This PR rewrote the `docs/current-state.md` top banner. `control/status.md` and
   `control/inbox.md` are bannered retired; when the Projects are recreated, replace the whole
   `control/` heartbeat + ORDER-bus apparatus with the new coordination model rather than
   patching it.

6. **(Product, when capacity returns) ship one user-facing feature from the game-design backlog.**
   The product runtime has idled behind fleet/EAP meta-work. Candidates already designed:
   casino/poker ([`planning/casino-poker-design-2026-06-22.md`](planning/casino-poker-design-2026-06-22.md)),
   creature sim ([`planning/creature-game-design-and-sim-2026-06-20.md`](planning/creature-game-design-and-sim-2026-06-20.md)),
   fishing open-world ([`planning/fishing-minigame-design-2026-06-22.md`](planning/fishing-minigame-design-2026-06-22.md)),
   giveaway/karma ([`planning/giveaway-system-plan-2026-06-23.md`](planning/giveaway-system-plan-2026-06-23.md) ·
   [`planning/karma-reputation-plan-2026-06-22.md`](planning/karma-reputation-plan-2026-06-22.md)).
   Note: only pursue if the owner re-opens product work — the standing posture is oracle-freeze.

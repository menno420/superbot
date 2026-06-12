# Reconciliation + planning pass — 2026-06-12 (PR band #741–#750)

> **Status:** `plan` — the first **Q-0107** docs-only reconciliation + planning pass
> (**PR #741**; cadence: every 10th PR; this pass fired when merged PRs crossed **#740**). It does two
> things: **(1) reconcile** — verify the repo's plan inventory against the latest PRs and
> route every plan into the roadmaps; **(2) plan the next ~9 PRs** — the realistic,
> modular queue for the upcoming decade. Re-badge `historical` at the next pass
> (due once merged PRs cross **#750**; marker lives in `current-state.md`).
>
> Source code and merged PRs win over this file. The [roadmap](../roadmap.md) stays the
> cross-area index; this doc owns the **decade queue** so the two never restate each other.

## 1. Verified state at this pass

- **Latest merged PR at write time: #740** (then **#732** merged in-pass — it was the one
  open PR; **zero open PRs** after it). All of #715–#740 verified merged on live GitHub.
- **Parallel work in flight (owner-stated, 2026-06-12):** another session is planning /
  implementing **Hermes-agent** work concurrently with this pass. Its PRs land inside this
  band on the 🤝 workflow lane — they *add to* the decade, they don't displace queue slots.
  **First one landed before this pass merged: #742** (the autonomous-loop seams — Hermes
  `superbot-review` · `check_phase_gate.py` fix/invent signal · the dispatch bridge — under
  new owner decisions **Q-0113** routine self-merge-on-green + **Q-0114** feature
  approve/deny, invent-phase-only origination); reconciled into the roadmap's workflow lane
  + the ledger in-pass.
- **2026-06-12 was a docs/tooling/workflow day** (16 merged PRs, no runtime `disbot/`
  feature work): the review-map + seven readiness maps (#715–#724), the hardening roadmap +
  manageability tools (#725–#728), the 429 crash-loop fix (#729 — the day's one runtime
  fix), Hermes skills (#730), the untested-surface checklist (#731 + #732), the
  agent-workflow/memory hardening arc (#733–#737), the Q-0107 cadence rule (#738), and the
  owner research + decisions (#739, #740).
- **Owner decisions newly in force:** Q-0098/Q-0099/Q-0100 (recorded #728) unblocked
  hardening tracks **P0-2 / P0-3 / P0-4**; **Q-0108–Q-0112** (#740) approved a **new
  product lane** — server safety + community platform. Q-0097 (health finding lifecycle)
  is the one hardening decision still open.
- **Drift fixed in this pass:** ledger entries #732/#738/#739/#740 added to
  `current-state.md`; Recently-shipped trimmed back under its ratchet (oldest entries
  archived); the roadmap's 2026-06-10 session queue superseded by §4 below; the new lane
  + the workflow lane mapped into the roadmap; the reconciliation marker reset to this
  PR; `check_reconciliation_due.py` taught to fetch `origin/main` (it read a stale ref in
  fresh containers and reported "latest #687").

## 2. Plan inventory — every plan added in #715–#740, mapped

| Added by | Doc | Kind | Routed to (now) |
|---|---|---|---|
| #715 | [`repo-review-map.md`](../repo-review-map.md) | reference | AGENT_ORIENTATION "Any task" route + operationalized as `scripts/review_scope.py` (#726) |
| #717–#724 | [`production-readiness/`](production-readiness/README.md) — 7 maps + index | audit | Roadmap ▶ production-readiness banner; evidence base for the hardening roadmap |
| #725 | [`hardening-roadmap-2026-06-12.md`](production-readiness/hardening-roadmap-2026-06-12.md) | plan | **Roadmap Next** — drives queue slots 2–6 in §4 below |
| #725 | [`ideas/repo-manageability-2026-06-12.md`](../ideas/repo-manageability-2026-06-12.md) | ideas | **Executed/resolved** (#726 tools + Q-0101); kept as record |
| #715/#716 | [`ideas/review-unit-tagging-2026-06-12.md`](../ideas/review-unit-tagging-2026-06-12.md) | ideas | **Executed** (#726); kept for rationale |
| #731/#732 | [`audits/untested-surface-checklist.md`](../audits/untested-surface-checklist.md) + `scripts/command_surface_dump.py` | audit + tool | Standing owner-led live-walk instrument; pairs with hardening **P1-4** |
| #730 | [`operations/hermes-operating-prompt.md`](../operations/hermes-operating-prompt.md) + installable skills | reference | Hermes control-plane docs (`operations/hermes-control-plane.md`) |
| #730/#731 | [`ideas/autonomous-improvement-loop-vision-2026-06-12.md`](../ideas/autonomous-improvement-loop-vision-2026-06-12.md) · [`ideas/hermes-claude-dispatch-bridge-2026-06-12.md`](../ideas/hermes-claude-dispatch-bridge-2026-06-12.md) | ideas (vision) → **seams wired** | Roadmap **🤝 workflow lane Now** — **#742** (parallel session, in-band) wired review/phase-gate/dispatch under Q-0113/Q-0114; maintainer wires the Routine + calibrates |
| #733 | [`ideas/portable-agent-memory-package-2026-06-12.md`](../ideas/portable-agent-memory-package-2026-06-12.md) | ideas (vision) | Roadmap **🤝 workflow lane Someday** — owner-shaped strategic direction |
| #733 | [`operations/claude-code-hooks-and-plugins.md`](../operations/claude-code-hooks-and-plugins.md) | reference | Workflow operations shelf (hook inventory) |
| #714 | [`ideas/claude-code-plugins-evaluation-2026-06-12.md`](../ideas/claude-code-plugins-evaluation-2026-06-12.md) | ideas | **Q-0096 partially answered** — Context7 adopted (#737, `operations/mcp-servers.md`); Postgres-MCP / pyright-LSP still open in the router |
| #738 | Q-0107 cadence rule + `scripts/check_reconciliation_due.py` | workflow rule | CLAUDE.md § Session workflow; this doc is its first execution |
| #739 | [`ideas/server-safety-and-automod-2026-06-12.md`](../ideas/server-safety-and-automod-2026-06-12.md) | ideas → **approved** | **Roadmap: new 🛡️ safety & community lane (Next)** — see §3 |
| #739 | [`ideas/community-platform-features-2026-06-12.md`](../ideas/community-platform-features-2026-06-12.md) | ideas → **partly approved** | Same lane: welcome (Q-0110) + NL events (Q-0112) approved; counters quick-win; feeds Later; custom commands Someday |
| #739 | [`operations/discord-platform-limits.md`](../operations/discord-platform-limits.md) | reference | Binding-adjacent UI reference — read before any component/image/attachment design |
| #740 | Q-0108–Q-0112 decisions (router §38) | owner decisions | Reflected in both idea docs' routing tables + the new roadmap lane |

Nothing added in #715–#740 is left unrouted. Pre-existing plans (mining, AI, BTD6,
myprofile, survival, pets, help-home, …) keep their existing roadmap rows — re-verified,
horizons unchanged except where noted in §4/§5.

## 3. Priorities restated (what the decade is for)

Two signals converged this week and set the decade:

1. **Production hardening before public posture (Q-0080).** The seven readiness maps put
   every subsystem at **Partial**; the [hardening roadmap](production-readiness/hardening-roadmap-2026-06-12.md)
   ranks the P0 integrity tracks (games money-safety · media privacy/retention · settings
   lane integrity · server-mgmt audit integrity) — and the owner answered the three
   gating questions same-day, so **P0-2/P0-3/P0-4 are unblocked now**. Backup posture
   (operations §Backups, still OPEN) belongs to the same risk class: irreversible loss.
2. **The owner researched and approved a new lane himself (Q-0108–Q-0112):** automod ·
   server event logging · image moderation (OpenAI-only) · security tiers 1+2 · welcome
   service · NL event scheduler. These are *staff/community* features — the layer
   competitor bots lead on — and all are plan-first.

The product lanes already in flight (mining V-16 phase 2 — gated on the owner's PNG pack;
BTD6 decode tail — demand-driven; AI §7 families — post-prod-check) stay open as
owner-steered alternates, not the decade's spine. The workflow substrate keeps improving
per-session (Q-0102/Q-0104 enders); its next *structural* step (Stage 0) is owner-gated.

## 4. The next ~9 PRs (band #741–#750)

> Modular but not over-segmented (Q-0107): each PR ships a real slice. Numbers are
> **sequence, not reserved PR numbers** — parallel sessions consume numbers; the next
> reconciliation fires when merged PRs cross **#750** regardless. If the owner steers
> mid-decade (he does, by design), swap a slot for the steered work and note it here.

| # | PR (one session each) | Scope anchor | Gate |
|---|---|---|---|
| 1 | **This pass** — reconcile + decade plan (docs-only) | Q-0107 | — |
| 2 | **P2 doc-drift sweep** + nudge Q-0097 | [hardening P2 table](production-readiness/hardening-roadmap-2026-06-12.md) — 5 known fixes (smoke-checklist command, AI README, ADR-006 wording, media folio claim, flag ownership label) | — (small/required is allowed) |
| 3 | **P0-1 games wager money-safety** — **owner-picked next (2026-06-12); design pinned: [plan](games-wager-money-safety-plan-2026-06-12.md)** | One audited `game_wager_workflow` composing the existing atomic primitives (escrow→settle/refund, idempotent payouts) + failure-injection tests + terminal-state matrix + AST fence | — |
| 4 | **Postgres backup posture** — design + automate | [production-deployment §Backups](../operations/production-deployment.md) (OPEN since the #685 incident) | Railway access facts from owner if needed |
| 5 | **P0-3 settings pointer-lane convergence + delegated-apply** | Settings map "recommended next session"; Q-0098 = delegates may apply; includes its P1-3 parity invariants | unblocked |
| 6 | **P0-4 server-mgmt channel-ownership convergence** | Q-0100 = converge under the existing audited seams; extend the channel invariant past `.edit()`/`.delete()` | unblocked |
| 7 | **P0-2 media retention + data-minimization** | Q-0099 = bounded projection + scheduled purge via the managed-task owner; fix `YOUTUBE_CONTEXT_ENABLED` ownership | unblocked |
| 8 | **Safety lane PR 1: family plan + automod v1** | One planning doc for the Q-0108–Q-0112 service family (automod · logging · image-mod · security t1+2 · welcome — shared config/UX shape, reuse of `moderation_service` + the existing `services/server_logging.py` seam), then `automod_service` v1 (4 rule types, exempt roles/channels, escalation intact) in the same session | plan-first (this PR is the plan) |
| 9 | **Safety lane PR 2: server event logging v1** | Q-0109 scope (edits/deletes · join/leave · role changes; owner-configurable single-or-per-category channels; privacy disclosure in setup) — **extends** the existing `server_logging` service, never a parallel seam | family plan (slot 8) |
| 10 | **Community lane PR: welcome v1 + server counters** | Q-0110 embed-only welcome (+ entry role, goodbye; join-DM opt-in proposed) + the counters quick-win — both `on_member`/guild-presence features | family plan (slot 8) |

**Deliberately *not* in this decade** (queued next, in rough order): image-moderation
service + security tiers 1+2 (next decade's safety slices, on the family plan) ·
**P1-1 versioned AI eval/smoke matrix** · **P1-2 health findings lifecycle** (Q-0097
answered 2026-06-12 — operator-managed; ready) · NL **event scheduler** (Q-0112 — wants its
own AI-cost design; interim ceiling €30/mo set, Q-0082) ·
**continuation dispatch** (Stage 0 folded into the #742 Routine seam — Q-0115) · help
home/navigation plan · V-14 harvest structuring · myprofile PR A · mining V-16 phase 2
(owner PNG pack). Owner-led in parallel: untested-surface checklist walks (P1-4).

## 5. Pruned / superseded by this pass

- The roadmap's **2026-06-10 "Recommended session queue"** — items 1 and 6 executed
  (#731/#732, #702); the remainder is folded into §4 and its not-this-decade list. The
  roadmap now points here instead of restating a queue.
- `current-state.md` ▶ intro de-bloated (executed-work narrative lives in
  Recently-shipped/archive, not the next-action pointer).
- No doc deletions: nothing qualified as safely removable (the 06-08/06-10 plan docs are
  already badged `historical` and reachable as history).

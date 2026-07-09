# 2026-07-09 — Fleet coordination protocol + manager Project v2 (plan)

> **Status:** `complete`

Follow-up to the EAP fleet review (PR #1887, merged). Owner-directed (2026-07-09): design the
manager Project properly — it tracks all repos and directly dispatches to the other Projects — and
extend the substrate-kit with a file-based inter-Project coordination protocol so the owner talks
to one manager that dispatches orders into files the other Projects read, each Project keeping its
status current.

## Arc

1. Applied Q-0254 understand-and-reflect: stated back the fuller picture (this is a **git-as-message-bus**
   because Projects can't talk directly — the eval log proved it) + the one hard constraint (writing an
   order file doesn't wake a sleeping Project).
2. Surfaced 3 genuine forks via `AskUserQuestion`; owner locked: **distributed own-repo coordination**
   (their proposal, which I recommended over a hub repo) · **self-poll routines** · **autonomous-director
   manager**.
3. Shipped the plan: protocol spec + substrate-kit changes + manager v2 loop + wake mechanism +
   paste-ready activation messages + phasing.

## Shipped

- `docs/planning/fleet-coordination-protocol-2026-07-09.md` (new) — the design + paste-ready materials.
- `docs/planning/README.md` — homed it.

## Context delta

1. **Needed but not pointed to:** nothing new — the design rests on two already-in-repo facts (the eval
   log's "no Project→Project channel" and the Q-0195 one-writer-per-file claim-dir result); orientation
   pointed to both.
2. **Pointed to but didn't need:** n/a.
3. **Discovered by hand:** a merged **designated branch is auto-deleted on squash-merge**, so a follow-up
   push with `--force-with-lease` fails `! [rejected] (stale info)` — the lease expects a SHA that no
   longer exists. The fix is `git fetch --prune` then a **plain** `git push -u` (it recreates the branch).
   The git runbook covers force-with-lease for merged history but not this deleted-branch case.
4. **Decisions made alone (reversible; in a plan doc):** recommended distributed-over-hub (owner asked my
   opinion; they'd proposed distributed, so it's ratified); chose the `inbox`/`status` file formats, the
   one-writer-per-file rule, Contents-API dispatch, and the phasing + MVP-shortcut.
5. **Genuine weak point:** the protocol is **designed, not built or dogfooded** — the wake-cadence cost,
   the routine-setup friction, and whether autonomous-director dispatch stays coherent are all unproven
   until Phase 3 runs. The status-freshness checker + CI path-ignore are specified, not implemented
   (kit-lab's build).

## 🛠 Friction → guard

- **Friction:** `--force-with-lease` push rejected `(stale info)` after the branch was auto-deleted on
  the prior PR's merge — cost a diagnosis round. **Guard shipped (docs, free):** recorded in Context
  delta #3 above the exact recovery (`fetch --prune` → plain `push -u`) so the next follow-up-on-a-
  merged-branch session doesn't re-derive it. Candidate for a one-line addition to the git runbook /
  `.session-journal.md` Quick reference — flagged, not force-edited (journal Rule is the weakest guard;
  this docs note suffices for a rare case).

## ⟲ Previous-session review

The prior slice this session (the EAP review, PR #1887) delivered the review + a manager brief, but the
brief was **observe-only** and needed an immediate v2 upgrade once the owner asked for direct dispatch —
a small miss: it designed *what the manager watches* without answering *how work reaches the Projects and
how they wake*. **Improvement folded in:** any manager/coordinator brief must answer "how does this thing
receive work + wake" up front — this plan's §1 (the bus) + §4 (self-poll routines) are exactly that gap
closed.

## 💡 Session idea

**A fleet-health strip on the `websites` control-plane board** — render each repo's `control/status.md`
(last-seen heartbeat, health, `⚑ needs-owner`) as a live glanceable row, so the distributed status files
become one visual the owner reads at a glance (the dashboard complement to the manager's chat rollup).
Targets the `websites` repo, so routed to its Project, not superbot's idea backlog (same handling as prior
cross-repo ideas). Natural once the protocol ships.

## 📤 Run report

- **Did:** designed the fleet coordination protocol (git-as-message-bus) + the manager Project v2 · **Outcome:** shipped (plan)
- **Shipped:** #1889 — `docs/planning/fleet-coordination-protocol-2026-07-09.md` + homing
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none new (the 3 forks were answered in-chat)
- **⚑ Owner manual steps:** send the §5 activation messages to each Project + the manager; create per-Project self-poll routines (scheduling gates owner-side); give the manager Project **read+write on all repos**
- **⚑ Self-initiated:** none (owner-directed design)
- **↪ Next:** start **Phase 3 MVP by hand** (stand up the manager + seed `control/` files for the live Projects) in parallel with **Phase 1** (kit `control/` protocol via kit-lab)

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1887; this #1889 pending) |
| CI-red rounds | 0 (born-red gate is by-design, not a real red) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (fleet-health strip on the control-plane board) |
| Ideas groomed | 0 |

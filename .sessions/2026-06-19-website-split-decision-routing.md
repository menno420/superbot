# 2026-06-19 — Website split: route the control-panel-placement decision (Q-0179)

> **Status:** `complete`

## Arc

Continuation after the website two-site-split **plan** merged (#1100). The plan's §7.4 surfaced a
genuine **owner-intent fork** — the dev-site "owner-gated for edits" wording (Q-0178) vs today's
existing *multi-user, any-guild-admin* control panel — that the router's Q-0178 "still open" list did
**not** include. That is stale-router drift + an unrouted owner decision the build run needs answered.

## Shipped (PR #1102)

- Router **Q-0179** (DISCUSS lane, OPEN): routes the per-server control-panel-placement fork to the
  owner — (1) keep the existing multi-user panel on the dev site (recommended, zero-migration) vs (2)
  move it to the public bot site as a bot-user feature. References Q-0178 + plan §7; lists the two
  implementation-level siblings (changelog source · captcha) for completeness. Append-only.
- Updated the active-work claim; flipped the born-red card to complete (Q-0133).

## Context delta

- The plan (#1100) surfaced this fork in two durable places (plan §7.4 + current-state ▶ Next action)
  but **not** in the router — the owner's canonical decision queue. Routing it is the proper completion
  of "surface, don't guess": a plan §7 buried in a 300-line doc is less likely to get an owner decision
  than a DISCUSS-lane Q-block. No new code; purely the decision-routing half of the planning work.
- The merge of #1100 was a **merge commit** (not squash, despite the squash request) — my branch
  fast-forwarded cleanly to `origin/main` (0 ahead) before this continuation, so #1102's diff is only
  the new work.

## ⟲ Previous-session review (Q-0102)

**#1100 (the plan) — thorough and well-grounded**, with all 7 deliverables and real source-reading
behind each. **What it missed:** it *surfaced* the §7.4 owner-intent fork but did not **route** it to the
maintainer-question-router — it left Q-0178's "still open" list stale relative to what the planning
discovered. A planning session that says "surface, don't guess" should close the loop by routing genuine
owner forks to the router (their decision home), not only noting them in plan prose. (This continuation
is that fix.) **System improvement:** the planning-session close (the `/plan-band` / session-close
discipline) should carry an explicit step — *"did this session surface an owner-intent fork not already
in the router? → append it as an OPEN Q-block."* Cheap habit; turns "surfaced in a plan" into "queued for
the owner."

## 💡 Session idea (Q-0089)

**A tiny `scripts/router_status.py` digest** — reports (a) the highest `Q-NNNN` (so a session instantly
knows the next free number, append-only convention) and (b) the list of **OPEN / DISCUSS-lane** blocks
still awaiting an owner decision ("what does the owner still need to decide?"). Motivated by friction I
hit this session: I `grep`'d for the next Q number and hand-scanned for what's unrouted, against a
6,500-line / ~179-block router. Pure stdlib, read-only, disposable (Q-0105); pairs naturally with the
website owner-zone's "open decisions" surface (it could even feed `export_dashboard_data.py`). Distinct
from prior ideas (those were about born-red completeness / deliverable outlines). Believe in it — the
router is now big enough that "next number + what's open" deserves one command.

## 📊 Doc audit (Q-0104)

- Q-0179 appended to the router (reachable; references the plan + Q-0178) · `check_docs --strict` green.
- Ledger: only benign newest-merge lag (#1095–#1101, all newer than the #1094 marker → the #1110
  reconciliation pass's job, per Q-0124 a manual session does not run it). Not this session's drift.
- No new owner *decision* recorded (Q-0179 is an OPEN question, by design — "unanswered questions are
  not approval").

## 📤 Run report

- **Did:** routed the one genuine owner-intent fork the merged plan (#1100 §7.4) surfaced but left out of
  the router — control-panel placement → router Q-0179 (DISCUSS). · **Outcome:** shipped.
- **Shipped:** #1102 — router Q-0179 + active-work update.
- **Run type:** `manual`
- **⚑ Owner decisions needed:** **Q-0179** — confirm (1) keep the multi-user per-server control panel on
  the dev site (recommended), or (2) move it to the public bot site. Needed before the ultracode build
  run wires it. (Plus the plan §7 siblings, build-time defaults unless you say otherwise.)
- **⚑ Owner manual steps:** `none`.
- **⚑ Self-initiated:** the *continuation* (routing the fork) was agent-initiated after the assigned
  planning task merged — a contained, in-scope docs action (no new feature). Flagged here for visibility.
- **↪ Next:** unchanged — the **ultracode build run** on the plan's §5 units (once the owner answers
  Q-0179, or the build defaults to recommendation (1)).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1102, auto-merge on green) |
| Router blocks added | 1 (Q-0179, OPEN/DISCUSS) |
| Owner decisions surfaced | 1 (control-panel placement) |
| CI-red rounds | 1 (born-red gate by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (`router_status.py` digest) |

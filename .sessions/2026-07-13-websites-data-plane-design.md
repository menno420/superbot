# 2026-07-13 — Websites fleet-data-plane design (owner ask)

> **Status:** `complete`
> **Branch:** `claude/multi-repo-orientation-review-p5ztfi` (restarted from main; prior PRs #2064/#2065 merged) · **PR:** #2066
> **📊 Model:** Claude 5 family (Fable)
> **Venue:** owner-live chat, remote container (hub repo)

## What happened

Owner ask (exploratory → design, Q-0254 possibility-space-first): how do the websites get
their live data; can it be centralized; design the misplaced-file failsafe (correctly-named
file in the wrong place is still found; recency decides). One read-only survey agent mapped
`menno420/websites` @ HEAD (all four services, every fetch site cited file:line); hub-side
checks confirmed the producer feeds (`scripts/export_dashboard_data.py` → contracted
`dashboard.json`/`console.json`/`site.json`) and the kit's per-repo self-declared manifests
(`substrate.config.json` `heartbeat_files` etc., verified fleet-wide).

**Shipped:** [`docs/planning/websites-fleet-data-plane-2026-07-13.md`](../docs/planning/websites-fleet-data-plane-2026-07-13.md)
— grounded current-state map (4 services, 4 styles; 5 hand-kept repo lists; 3 duplicate
fetch layers; script-literal parsing of fm's roster), the design (one derived manifest =
`lanes.json` × `substrate.config.json` × kind table · one fetch core · three lanes ·
the resolver: canonical-first → name-pattern discovery → **commit-time recency over
agent-written stamps** → canonical-precedence with loud drift rows → `misplaced.json`
consumed by the fm wake = self-healing), feasibility verdict (yes — all primitives exist),
and a 4-phase build order routable as websites ORDERs. Execution stays websites-lane.

## ⚑ Self-initiated (Q-0172)

None — owner-directed ask; the design doc is the deliverable.

## 💡 Session idea (Q-0089)

**Kit gate check `check_misplaced_artifacts` (prevent at the source).** The design's
render-time failsafe has a cheaper commit-time twin: a substrate-gate check that scans the
committing repo for artifact-kind files outside their `substrate.config.json`-declared
homes (a `status*.md` outside `control/`, a session card outside `sessions_dir`, a verdict
outside `sims/`) and warns before merge. Misplacement then gets caught where it happens,
and the website failsafe becomes the backstop instead of the only net. Kit lane; §2.5 of
the design doc carries the pointer. Dedup: no `docs/ideas/` entry covers misplaced-artifact
guarding (grep 2026-07-13).

## ⟲ Previous-session review (Q-0102)

The ender-v3.4 session (#2065, same chat) was tight: intent reflected back before building,
v3.3's incident-hardened mechanics preserved verbatim-in-substance, one flagged design call
(worker reviews fold into coordinator reports) instead of a silent choice. Nothing it
missed worth flagging — genuinely. **System improvement it surfaces:** it hand-assembled
its close-out again rather than invoking `/session-close` — same gap two sessions running;
the ender-compliance gate idea from its own card is the enforcing fix and should be built
soon (this card's close-out was again hand-run, checks-first).

## Docs audit (Q-0104)

- New doc reachable: homed in the **S5-ops sector queue**
  ([`docs/current-state/S5-ops.md`](../docs/current-state/S5-ops.md) ▶ Next) — the
  `check_plan_homing` reachability check caught the first push leaving it orphaned (my
  audit note initially claimed no homing was needed; the checker was right, corrected in
  the fix commit). Honest miss, second lesson: the check ran but its exit code was
  swallowed by a `| tail` pipe — checks must gate the push, not decorate it.
- Telemetry row appended in this PR (Q-0194). Claim deleted at close.
- Nothing valuable chat-only: the full design lives in the committed doc; chat carries the
  owner summary.

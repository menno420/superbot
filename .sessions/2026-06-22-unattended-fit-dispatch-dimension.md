# 2026-06-22 — Unattended-fit dimension for the per-sector dispatch contract

> **Status:** `in-progress` — Dispatch routine, scheduled empty-fire (no work order). Bugs-first found
> the open bugs blocked (BUG-0011 infra · BUG-0019 #1 owner-fork · BUG-0009 data-gated); the actionable
> signal is the **recurring empty-fire stall** two consecutive runs hit (#1274 and this one): rediscovering
> mid-run that the *headline* lanes all need a human. Building the previous run's explicitly-surfaced-but-
> unpromoted fix. Self-initiated (Q-0172).

> **Run type:** `routine · dispatch`

## What I'm about to do

The dispatch contract tags each `Now` item **▶ startable / ⛔ gated / 👤 maintainer** — that answers
*"may Claude **start** this?"* but NOT *"can an **unattended** run **complete and self-merge** it without
a human?"* So an empty-fire run picks a `▶` lane, starts it, and only then discovers it needs a live
guild walk, is `needs-hermes-review`, or commits external IP-sensitive data. PR #1274's ⟲ review named
this exact fix ("tag each queued lane with an unattended-fit flag — offline-verifiable? self-mergeable?
needs-live-verify? external-data/IP?") and explicitly left it **unpromoted**. This run promotes it.

Add an orthogonal **unattended-fit** dimension to each sector's `Dispatch` line:
- 🟢 `auto` — offline-verifiable AND self-mergeable (an unattended run can complete it + auto-merge on green)
- 🟡 `review` — buildable offline but `needs-hermes-review` (build + open PR, do NOT self-merge)
- 🔵 `live` — needs a live guild walk / runtime creds to verify (weak unattended fit)
- 🟠 `ext-data` — commits externally-sourced data (external-data safety brake → owner confirm first)

Then teach `dispatch_menu.py` to parse + surface it and add `--unattended` (aggregate: which sector, if
any, an empty-fire run can complete & merge), and make `check_sector_map.py` require the tag on every
sector's Dispatch line (self-maintaining, like the startability glyph). The payoff this run already
proved: the per-sector first-`▶` items (S2 eval cases · S3 substrate-kit · S4 nav layers) are 🟢 `auto` —
the empty-fire runs were anchoring on the *headline* (human-needed) lanes and missing them.

## Files (planned)
- `scripts/dispatch_menu.py` — parse unattended-fit; `--unattended` resolver; surface in output
- `scripts/check_sector_map.py` — require an unattended-fit tag on each sector's Dispatch line
- `docs/roadmap.md` — add the per-sector unattended-fit tag + header definition
- `docs/repo-sector-map.md` — the convention in § "dispatch targets"
- `tests/unit/scripts/test_dispatch_menu.py` / `test_check_sector_map.py` — parsing + resolution

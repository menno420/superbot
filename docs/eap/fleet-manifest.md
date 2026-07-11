# Fleet manifest — Project registry

> **Status:** `historical` — **SUPERSEDED 2026-07-11 by the fleet-manager generated roster.**
>
> **Canonical fleet/seat state now lives at `menno420/fleet-manager` `docs/roster.md`**
> (<https://github.com/menno420/fleet-manager/blob/main/docs/roster.md>) —
> a GENERATED roster regenerated at every manager wake (≤~2h) from the **live trigger
> registry** (`list_triggers`) plus each lane repo's `control/status.md` heartbeat at
> ls-remote-verified SHAs. This file is **no longer maintained**; do not re-stamp it and
> do not read fleet state from it. Its full row history is in git.
>
> **Why (phase-2 decision, fleet-manager PR #59, merge `b0639a9`):** the owed parallel run —
> fleet-manager `docs/findings/manifest-parallel-run-2026-07-11.md` — found this
> hand-maintained manifest stale on every measured axis (~33.5h stale; 5 live lanes
> missing; 9 of 10 live-lane rows factually wrong on trigger/cadence/kit/status; only the
> websites trigger id survived contact with the live registry), while the generated roster
> stays ≤~2h fresh with zero hand maintenance. Keeping both was pure drift surface.
> The companion checker `scripts/check_manifest_freshness.py` was retired the same day per
> its own Q-0105 kill-switch header (superbot PR #1974).
>
> Original protocol (historical):
> [fleet-coordination-protocol-2026-07-09.md](../planning/fleet-coordination-protocol-2026-07-09.md).
> Seeded 2026-07-09T12:07Z at manager kickoff; last hand re-stamp 2026-07-10T16:38Z.

# 2026-07-14 — Fleet-manager relay: EAP final-day closeout ORDER (dispatch)

> **Status:** `in-progress`
> **Branch:** `claude/eap-final-closeout` · **PR:** TBD
> **📊 Model:** fable-5 · **Run type:** routine · dispatch
> **Venue:** fleet-manager coordinator dispatch worker, remote container

Intent: relay the EAP final-day closeout directive as an inbox ORDER — append ONE
ORDER (006, next free number) to `control/inbox.md` directing the next hub-touching
session to finish-or-park-cited every open item (ORDERs 003/004/005 close-outs +
night-worklist items 4–8) and land the EAP closeout walkthrough doc
(`docs/eap-closeout-walkthrough-2026-07-14.md`, verified absent at `6e761c7`).
Control-only intake: session card + telemetry row + the inbox append, no code, no
doc edits beyond the ceremony files.

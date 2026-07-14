# 2026-07-14 — Fleet-manager relay: supersession-pointer ORDER (dispatch)

> **Status:** `in-progress`
> **Branch:** `claude/fm-dispatch-0409z` · **PR:** TBD
> **📊 Model:** fable-5 · **Run type:** routine · dispatch
> **Venue:** fleet-manager coordinator dispatch worker, remote container

Intent: relay fm dispatch-log rows 1–2 as an inbox ORDER — append ONE ORDER to
`control/inbox.md` directing supersession pointers on three superseded superbot
docs (trigger-health order + two fleet planning docs) toward their living
fleet-manager counterparts. Control-only intake: session card + telemetry row +
the inbox append, no code, no doc edits beyond the ceremony files.

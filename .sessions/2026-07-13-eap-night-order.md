# 2026-07-13 — EAP final-night ORDER delivery (fleet-manager dispatch)

> **Status:** `in-progress`
> **Branch:** `claude/eap-night-order` · **PR:** TBD
> **📊 Model:** fable-5 · **Run type:** routine · dispatch
> **Venue:** fleet-manager coordinator dispatch worker, remote container

Intent: deliver the EAP final-night ORDER into the inbox, relay from fm ORDER 045 —
append ONE ORDER to `control/inbox.md` carrying the owner-directed final-night
worklist for the superbot hub seat (docs/control only, no runtime code).

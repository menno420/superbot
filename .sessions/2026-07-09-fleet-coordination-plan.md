# 2026-07-09 — Fleet coordination protocol + manager Project v2 (plan)

> **Status:** `in-progress`

Follow-up to the EAP fleet review (PR #1887, merged). Owner-directed (2026-07-09): design the
manager Project properly — it tracks all repos and directly dispatches to the other Projects — and
extend the substrate-kit with a file-based inter-Project coordination protocol so the owner talks
to one manager that dispatches orders into files the other Projects read, each Project keeping its
status current. Locked decisions: distributed (own-repo) coordination · self-poll routines ·
autonomous-director manager.

Shipping: `docs/planning/fleet-coordination-protocol-2026-07-09.md` (the protocol + kit changes +
manager v2 + paste-ready activation messages).

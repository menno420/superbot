# 2026-07-11 — Retire fleet-manifest to a pointer stub (fm roster canonical)

> **Status:** `in-progress`

**About to happen:** per the phase-2 decision in fleet-manager PR #59 (merge
`b0639a9`, findings: fm `docs/findings/manifest-parallel-run-2026-07-11.md`),
reduce `docs/eap/fleet-manifest.md` to a pointer stub at the fleet-manager
generated roster (`menno420/fleet-manager` `docs/roster.md`), retire
`scripts/check_manifest_freshness.py` per its own Q-0105 kill-switch header
(+ its test + runbook/doc wiring), and update pointing docs.

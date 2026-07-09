# Session 2026-07-09 — KL-6 companion: exporter telemetry family + kit-lab console lane

> **Status:** `in-progress`

**About to do (kit-lab founding plan §7.3, band KL-6 — the superbot-side
companion to substrate-kit PR #18):** the exporter gains a `telemetry`
family (reads `telemetry/model-usage.jsonl`, the PL-004/Q-0248 record —
superbot's rows are hand-authored until it adopts, plan §4.2/§5.2) rendered
on the console's declared "Model & spend telemetry" lane (real rows, no more
pending); the console gains the new declared lane **"Kit lab — benchmarks &
guards"** with its exact contract (`bench/results/*/index.json → [{date,
kit_version, family, verdict, headline}]` — declared, not faked: the kit's
bench results ride an open owner-blessing PR and the cross-repo read waits
on 👤 P11/P13). `console.json` regenerated; exporter tests extended.

"""Grammar-expressiveness SPIKE — design-spec §2 made runnable, NOT the kernel.

Status: `spike` (2026-07-02). This package exists to answer one owner-gate
question with evidence: **do ~80% of real surfaces fit the manifest grammar
as tier 1–2 declarations** (design spec §2.9 / §10.1 risk 5), or does
reality force escape-hatch code everywhere?

What it is: a faithful prototype of the §2 spec dataclasses (S/A/O field
roles, intra-manifest validation) plus REAL example manifests for three
shipped subsystems spanning the difficulty range — karma (simple),
server logging (operator config, richest lane surface), blackjack (stateful
game, escape-hatch-heavy) — and a measurement harness that scores every real
surface unit of those subsystems against the grammar.

What it is NOT: the Phase-3 kernel (`sb/` stays behind the owner gate — this
package deliberately lives under `tools/` in the current repo), and not a
registration of anything at runtime. Nothing here is imported by `disbot/`.

If Phase 3 is approved, `spec.py` seeds `sb/spec/` (K2) and the manifests
seed their port-band declarations; if it is not, this delete cleanly.
"""

# 2026-07-06 — Gate V: verify C1 re-run + Arm A Ultracode review (fleet complete)

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). Docs-only session (no
> `disbot/` runtime code): `check_plan_homing.py --strict` / `check_docs.py --strict` /
> `check_current_state_ledger.py --strict` all green.

## What this session did

Owner asked (in-session) to review the **last Codex PR** (C1 re-run) and the **Ultracode/Arm A** work,
both now done. An independent 2-agent review fan-out verified both against live source; results folded
into the corrections doc, taking the Gate V evidence layer to **fleet-complete**.

**Shipped (PR #1759):** updated `docs/planning/rebuild-gate-v-findings-corrections-2026-07-06.md`:

- **§1 fleet state → COMPLETE** — all arms A–D + C1 verified sound; Arm Σ (synthesis) unblocked.
- **§6 (new): C1 + Arm A verification.**
  - **C1 #1758 (`docs/planning/C1-l0-runtime.md`) — SOUND, merge-ready.** All L0 source counterparts
    exist; PRESERVE/REDESIGN labels defensible (config token-required, bootstrap_access_cog loads
    first, /ready gates on lifecycle, SUBSYSTEMS deep-frozen, fail-closed router); no ci-gate error, no
    dead-code trap. Minor: hedged §9 test cells.
  - **Arm A (SONNET readiness review) — SOUND, synthesis-ready.** Headline re-confirmed: the frozen
    **L3→L4/L5 edge is fabricated** (zero L3 game-cog dependency in L4/L5) → its **Sequence C**
    recommendation is sound and strengthens C5. K7 blocker verified BUT its urgency is *borrowed* (the
    money bugs close today via existing `SettleOnceMixin` retrofit + wider Rule-6, not the unbuilt
    engine). Blocker #2 (`check_amendments.py` absent, K1 zero code) real. L0 correctly conservative.
- **The one reconciliation flagged for Arm Σ:** Arm A treats economy/G-12 as "already richly proved"
  while flagging karma atomicity — but C4 + this pass confirm economy credit/debit AND xp award have the
  **same** non-atomic write+audit shape (xp with *no* audit companion). Audited-write atomicity is
  **SYSTEMIC across economy/karma/xp**; the synthesis must merge it into one finding, not read Arm A as
  clearing economy.
- **§7 directives updated:** adopt Sequence C as baseline; treat atomicity as one systemic finding;
  K7 urgency is borrowed; `READY_FOR_TEST_DESIGN` = "test-spec-ready," not "implemented."

## ⚑ Self-initiated

None beyond owner direction — owner asked for the review; documenting the corrected findings is the
established fleet pattern. Docs-only, reversible.

## 💡 Session idea (Q-0089)

**Cross-arm contradiction detection should be a named synthesis step, not a lucky catch.** The most
valuable finding this session — that Arm A calls economy "proved" while C4 shows it has the same
atomicity gap as karma — only surfaced because the review agent was told to check cross-arm
consistency. A fleet's value is *disagreement surfacing*, so the synthesis prompt (launch-pad §8)
should mandate an explicit "join the arms' claims on the §3.3 key and list every place two arms grade
the SAME seam differently" pass — turning contradiction-hunting from serendipity into a checklist item.
Pairs with the earlier `verified-evidence-layer` idea. (Grep-checked `docs/ideas/` — no existing entry.)

## ⟲ Previous-session review (Q-0102)

Previous (this branch): the corrections doc v1 (#1756). **Did well:** the §3.3 claim-anchor scheme is
exactly what let this session's review agents re-key Arm A's findings against C4/C5 and spot the
economy/karma inconsistency — the shared-contract investment paid off. **Missed / system delta:** v1's
§6 directive told Σ to mark L0 `NEEDS_SOURCE_RECONCILIATION` "pending C1" — which C1 then resolved
hours later; a corrections doc that hard-codes a transient gap-state goes stale fast. The durable form
(applied this session) is to state the *posture* (L0 stays conservative/BLOCKED_BY_GATE regardless) and
let the fleet-state table carry the transient status — so the directive doesn't rot when the gap fills.

## ▶ Next action

Run **Arm Σ (final synthesis)** — launch-pad §8 prompt, fed **this corrections doc** as the
authoritative evidence layer. It produces `GATE-V-SYNTHESIS.md` with the Gate-V lift/hold verdict; the
sequencing baseline is **Sequence C**, and the systemic atomicity finding + K7-urgency correction are
the two must-carry items. Optional housekeeping: relocate the root-level C2/C3/C4 sub-reports under
`docs/planning/`, and pin the sub-report output dir in launch-pad §5.

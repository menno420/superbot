# 2026-07-03 — Rebuild Phase A · conventions freeze (owner-live, continued)

> **Status:** `complete` — PR #1680. Direct continuation of the Stage-1 global review (#1679,
> merged). Owner-live decision session settling the cross-cutting **conventions** the subsystem
> walk needs as its lens, folded into a conventions decisions log + router Q-0224…Q-0228.
> Docs-only; no `disbot/` code, no new-repo code.

## What shipped (PR #1680)

1. **[`docs/planning/rebuild-conventions-invocation-authority-2026-07-03.md`](../docs/planning/rebuild-conventions-invocation-authority-2026-07-03.md)**
   — Phase-A companion decisions log #2:
   - **Naming (Q-0224):** namespace `/area verb` **only** for verbs shared by 2+ subsystems, flat
     otherwise; the shared-verb set is **computed once from the known 271-command corpus** so no
     collision is found at runtime and no flat command is ever force-renamed (the liability); safe
     no-arg defaults for read/common actions, never for destructive ones.
   - **Invocation ladder (Q-0225):** four front-ends into one command engine — (1) exact
     (slash+prefix+**additive** union of global/guild/channel/user custom triggers, validated when
     set, **silent on no-match**); (2) **fuzzy typo matcher** (the "global parser" the owner meant),
     three tiers (very-close+safe→run, close→private "did you mean", far→silent); (3) NL intent
     (the existing central NL stage made mainstream, router generated from manifests); (4) NL
     orchestration (goal→draft→preview→Accept→atomic apply = the **draft lane with the AI as a
     second producer**, the D&D-tournament example). Deterministic-first preserved (rungs 1–2 need
     no AI). Default posture = hybrid (answer freely, signal before acting; destructive always
     confirms).
   - **Mod-actions-as-data (Q-0226):** declarative envelope + one escalation handler; resolves the
     ModerationActionSpec uncertainty to the envelope; chosen for testability.
   - **Authority (Q-0227):** one declared authority label per action + a global bot-owner override
     (Q-0212), with a "bot-owner runs everything everywhere" parity test and transparent
     cross-server audit.
   - **§6 centralization proposals C-1…C-7 (Q-0228):** command resolver, draft pipeline (two
     producers), template primitive, response grammar, fuzzy engine, cooldown engine, description
     surface — captured as **proposals pending owner reaction**, not decisions.
2. **Router Q-0224…Q-0228** with verbatim-quote provenance.
3. **Homing + ledger:** planning README row, current-state entry #1680, ideas index.
4. **State check:** verified `services/parsers` is the BTD6 data parsers (not a command matcher)
   and that fuzzy matching exists **scattered** (setup advisor, presets, recommenders) with **no
   central command-typo resolver** — grounding the C-5 centralization.

## 💡 Session idea (Q-0089)

**[`rebuild-invocation-ladder-centralization-2026-07-03.md`](../docs/ideas/rebuild-invocation-ladder-centralization-2026-07-03.md)**
— the C-1…C-7 centralization set (captured as the session's genuine new idea; the command-resolver
convergence point C-1 is the one I'd defend hardest — without it the four rungs re-implement auth
and drift, which is a safety bug not just untidiness).

## ⟲ Previous-session review (Q-0102)

Previous: **#1679 (Stage-1 global review).** Strong — it turned an open discussion into durable
standards (S-1/S-2) and caught two ordering inversions the live chat missed. **What it could have
done better:** it recommended "one conventions-freeze sitting" but didn't *name the specific
conventions* as a checklist, so this session had to re-derive the list (naming, invocation, mod-
actions, authority) from §6 prose. **Workflow improvement applied here:** this log ends with an
explicit Stage-2 checklist (below) so the *next* session doesn't re-derive its agenda — a
recommendation should ship as an actionable list, not a paragraph. Cheap, and it compounds across
the review chain.

## Docs audit (Q-0104)

- `check_docs --strict` ✓ · `check_plan_homing` ✓ (new log homed) · ledger entry added
- New owner decisions → Q-0224…Q-0228 ✓; session idea indexed ✓
- Chat-only residue: none — the fuzzy-matcher/NL/orchestration nuances and the additive-trigger
  + silent-on-no-match rules are all in the conventions log §2.

## ⚑ Self-initiated

None decided unprompted — the five decisions (Q-0224…Q-0227) are owner-directed live; Q-0228 is
explicitly captured as *proposals* awaiting owner reaction, not self-applied.

## For the next session (Stage 2 — the subsystem walk) — actionable checklist

1. Run the **shared-verb computation** over the 271-command corpus → publish the flat-vs-grouped
   list per subsystem (Q-0224 input to K1).
2. Per subsystem, decide: exact command names + aliases · command kind (slash/prefix) · hub
   placement · concrete outperform feature list · **the D-5 triage verdict** (bring back / defer /
   drop / re-place).
3. Write the **method/seam vocabulary** (WorkflowResult shape, handler-ref/provider-ref naming,
   audited-mutation signature) as **S-1 applications** (which tier each pattern uses).
4. Still-open Phase-A uncertainties to close before Stage 3: **G-22 staging lanes** (standardize vs
   three) and the **ModerationActionSpec ~1hr spot-check** (confirm the envelope fits before the
   freeze).
5. Get the owner's **Q-0228 reaction** (which of C-1…C-7 to adopt) — blessed ones become Gate-0 K8
   contracts.
6. Suggested shape: walk by L-layer band, operator spine first, one band per sitting, owner present.

# 2026-06-19 — Website two-site split: planning brief

> **Status:** `complete`

## Arc

Owner-directed after the ultracode run: split the single dashboard into a **public bot site** (users;
submit bugs/suggestions) and a **dev/repo site** (current dashboard; owner-gated edits, public read-only).
The owner asked me to **document the required planning output for the next session** + capture the idea,
and to ask remaining questions via the question panel first.

## Shipped (PR #1099)

- Asked the 4 shaping questions via `AskUserQuestion`; recorded the answers as **router Q-0178**.
- `docs/planning/website-two-site-split-planning-brief-2026-06-19.md` — the **required-output spec** for
  the next (planning) session: owner-decided constraints, hard non-negotiables (no secret values in the
  public read-only view; preserve dashboard decoupling; moderation-before-public), and the 7 deliverables
  the plan must produce (page/audience matrix · architecture · hybrid-data design · security review ·
  **file-disjoint decomposition for a follow-up ultracode run** · migration/rollout · open decisions).
- Idea capture + `docs/ideas/README.md` index entry. `check_docs --strict` green.

Owner choices (Q-0178): bot site public + hybrid-live; submissions **DB → owner-approve → mirror to
GitHub**; dev site **all pages public read-only**, owner edits; **2 Railway services** (repurpose
dashboard + new bot site).

## Context delta

- **Discovered/decided:** the "all pages public read-only" choice makes a **secret-value redaction audit**
  a hard requirement (the control-plane + env pages go public) — baked into the brief as non-negotiable #1.
- The brief is deliberately a *spec for the next session*, not the plan — the planning is design-heavy with
  serial dependencies (factor-shared → DB → parallelize), so it earns its own focused session.

## ⟲ Previous-session review (Q-0102)

The ultracode fleet run (the work between this card and #1079): **strong result** — 16/16 file-disjoint
units, `main` stayed green, arch debt 76→45, zero Codex *code* findings. **What it missed:** the fleet
agents skipped the mandatory session-card enders (`💡 Session idea` / `⟲ Previous-session review`) — Codex
flagged it (B7 P2), and it's the one real process gap. **System improvement:** the kickoff prompt should
require the enders before the card flips, and/or the born-red gate could check the *log completeness*, not
just the status badge (captured as the idea below).

## 💡 Session idea (Q-0089)

**Extend the merge gate from card-*status* to card-*completeness*.** `check_session_gate.py` only checks
the `Status:` badge; `check_session_log.py` (which knows the mandatory ender sections) is **not** a CI gate.
The fleet proved agents will flip the badge but skip the `💡`/`⟲` enders. Idea: have the born-red gate (or
a sibling soft check) also require the ender sections on a non-trivial session card, so an incomplete
session log can't merge — closing the gap Codex caught across all 16 fleet cards. Distinct from existing
captures (those are about *content* freshness, not session-log completeness). Cheap, stdlib, the script
already exists.

## 📊 Doc audit (Q-0104)

- Brief in `docs/planning/` ✓ · idea in `docs/ideas/` + README ✓ · decision in router **Q-0178** ✓ ·
  card ✓ — all reachable, `check_docs --strict` green.
- Ledger: newest-merge lag only (the band-#1080 reconcile pass #1098 already reconciled through #1094;
  #1095–#1099 are the next pass's job at #1110). Not this session's drift.

## 📤 Run report

- **Did:** captured the owner's website two-site-split decisions (Q-0178) and wrote the required-output
  brief for the next planning session. · **Outcome:** shipped
- **Shipped:** #1099 — planning brief + idea + router Q-0178.
- **Run type:** `manual`
- **⚑ Owner decisions needed:** still-open items in Q-0178 (domains/branding · live-widget data source ·
  submissions DB store) — the planning session will surface these for you; not blocking the brief.
- **⚑ Owner manual steps:** `none` (the next session is a planning session against this brief).
- **⚑ Self-initiated:** `none` (owner-directed).
- **↪ Next:** a **planning session** that reads the brief and produces the full implementation plan +
  the file-disjoint decomposition; an ultracode build run follows that.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1099, auto-merge on green) |
| Owner decisions captured | 4 (Q-0178, via question panel) |
| CI-red rounds | 1 (born-red gate by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (card-completeness merge gate) |

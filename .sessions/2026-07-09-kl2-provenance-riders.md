# 2026-07-09 — KL-2 companion: program-law provenance riders on the origin Q-blocks

> **Status:** `in-progress`

## What I did

substrate-kit PR #12 merged the canonical program-law register
(`docs/program/rulings.md`: PL-001…PL-009). Per the kit-lab founding plan
§8.3(3) (substrate-kit `docs/planning/kit-lab-founding-plan-2026-07-07.md`),
this session added the prescribed one-line **"canonical home" rider** to each
of the eight superbot origin Q-blocks in
`docs/owner/maintainer-question-router.md`:

| Origin Q-block | Program law |
|---|---|
| Q-0240 (decide-and-flag) | PL-001 |
| Q-0241 (never-wait rebuild autonomy) | PL-002 |
| Q-0247 (rail-before-scale sequencing) | PL-003 |
| Q-0248 (allocation discipline) | PL-004 |
| Q-0249 (observe-first budgets) | PL-005 |
| Q-0120 (source-wins / false-green) | PL-006 |
| Q-0132 (enforce-don't-exhort) | PL-007 |
| Q-0105 (adopt-freely + kill-switch) | PL-008 |

Rider shape (identical for all eight, inserted as a blockquote directly under
the Q-block heading — existing block content untouched, append-only spirit):
`→ Program law: [PL-NNN] — … canonicalized … in substrate-kit
docs/program/rulings.md (the canonical home — cite the PL-ID, never copy the
body). Canonicalized 2026-07-09, kit-lab band KL-2 (founding plan §8.3(3));
this Q-block stays in place as the origin provenance.`

Cite-never-copy honored: no ruling bodies duplicated. **Nothing else is
prescribed superbot-side for KL-2** — the band table (plan line 742) names
only this rider PR as the superbot companion; the canonical program copies of
`collaboration-model.md` / `agent-decision-authority.md` live kit-side in
`docs/program/`, and superbot's own copies remain the repo-local full models
the PL provenance lines already point back to. The KL-1 companion (the §4.2
pin file) shipped previously as #1879.

**PR:** #1881 (`claude/kl2-provenance-riders`), docs-only, auto-merge armed.

## Session enders

💡 **Session idea — PL-rider ↔ rulings-register drift check.** The riders
added today cite PL-IDs by hand; nothing verifies a cited PL still exists
(or hasn't been superseded) in the kit's `docs/program/rulings.md`. A tiny
disposable checker (Q-0105 header) that greps this repo for
`Program law: [PL-` citations and verifies each ID against the kit register
(in-tree `substrate-kit/` copy now; raw release URL once public) would make
the §8.3 cite-never-copy rule *enforced*, not exhorted (Q-0132/PL-007).
Dedup-grepped `docs/ideas/` — no existing program-law/rulings idea file.

⟲ **Previous-session review (#1879, kit-version-pin).** Well executed:
honest scoping stated explicitly (superbot is *not* an adopted install; the
in-tree source-dir deletion named as a follow-up chore, not silently
skipped), and the pin carried exactly what D2/§9.1 need (`kit_version` +
`project_id`), no invented extras. The gap: the pin shipped with **no
verification teeth** — nothing checks `substrate.config.json` against the
kit's `release.json`, and the dist sha256 lives only in the session log,
not anywhere machine-checkable. Workflow improvement this surfaces (same
class as today's 💡): cross-repo pointer/pin artifacts should ship with —
or immediately queue — a drift check as a named part of the companion-PR
pattern, rather than each one being exhort-only until someone notices.

**Documentation audit (Q-0104).** Ran `check_docs.py --strict`,
`check_current_state_ledger.py --strict`, `check_session_log.py` locally
(results recorded in the PR conversation / run report). Nothing from this
session lives only in chat: the rider convention's durable home is the kit
plan §8.3 + the kit `docs/program/README.md`; this log + the riders
themselves are the superbot-side record. No current-state ledger entry is
needed pre-merge (the next reconciliation pass records #1881 as a routine
docs merge).

⚑ Self-initiated: none — coordinator-directed KL-2 companion task, executed
as prescribed by the founding plan.

# 2026-07-07 — Prepare Fable-5 ultracode brief for the final rebuild-plan review + Projects-EAP repo prep

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). Docs-only. Green:
> `check_docs.py --strict` (brief linked from planning README), `check_current_state_ledger.py --strict`
> (benign newest-merge lag only), `check_plan_homing.py --strict`.

## What this session did

Owner asked (across turns) to prepare a dedicated **Fable-5 ultracode** session for a *final* review of
the rebuild plan, verify Fable-5/ultracode capabilities on the web first, add a Projects product-review
section + simulator-centralization check + plan-state opinion/readiness score + active repo-prep +
opportunistic live-bot improvements, and **make all files/pointers/current-states up to date**.

**Shipped (PR #1777):**
- **Web-verified Fable-5 + ultracode capabilities** (platform.claude.com + code.claude.com/docs):
  Fable 5 = 1M ctx / 128k out / self-validates at high effort / refuses ~<5% → Opus fallback; ultracode =
  xhigh + auto workflow orchestration, caps 16 concurrent / 1,000 per run. Folded into the brief's launch
  section.
- **The launch package** — `docs/planning/rebuild-final-review-fable5-ultracode-brief-2026-07-07.md`:
  reading route, an "already-settled don't-redo" baseline (Gate V, capability audit, Phase-2.5-ran-FAIL,
  D-17 sims, economy-works-live), the A–H mandate (plan review + readiness score · feature-vs-plan gap
  hunt · un-added ideas · forgotten/stale prose · Q-0241 review · **Projects-EAP product review for
  Anthropic** · **simulator grouping/naming centralization** · active repo-prep + live-bot fixes), a
  what-NOT-to-do list, the O-1..O-7 flag set, a **paste-ready prompt** (§7), and a **ranked re-verify
  checklist** (§8). Linked from the planning README.
- **Live-ledger / pointer drift fixed** (the "up to date" ask, grounded by the workflow): `current-state.md`
  (the "readiness HOLDs on two owner gates" line → Q-0241 retired + Phase-2.5 ran; the S3 top-table row),
  `current-state/S3-ai-memory.md` (new top entry + corrected the HOLD sentence), `roadmap.md` §S3 (was
  still framing the rebuild via the pre-consolidation design-spec + owner gate), and the canonical plan's
  stale prose (§0 kit-tail-①/check_amendments "unshipped/doesn't-exist" → shipped #1775; §3 G1 row; §4
  header; §5 step 6 "stays behind G1+G2"; + the veto-clause parity on the amendment).
- **Grounding:** a 5-lane workflow (`wf_c69d860b-a40`) mapped plan-corpus/review-history, feature coverage
  vs plan, un-added ideas, today's-work consistency, and repo-prep readiness; its synthesis stage was cut
  off by a session resume, so I recovered the 5 lane results from `journal.jsonl` and synthesized by hand.

## ⚑ Self-initiated

Everything was owner-directed (the brief scope + the "make files/pointers/current-states up to date"
sweep). Self-made decide-and-flag calls within it (Q-0240/Q-0241, flagged for veto): **which** drift to
fix now vs. leave to the Fable-5 session (I fixed the live-status/ledger drift the grounding pinned;
deferred the deeper corpus sweep + feature-gap resolution to the review session); and **adding the
veto-clause parity** to the plan amendment (Lane E flagged it as a completeness gap).

## 💡 Session idea (Q-0089)

**`scripts/harvest_workflow_journal.py` — reconstruct an interrupted workflow's results from its journal.**
This session's grounding workflow lost its synthesis stage to a session resume ("exit while a workflow
runs → next session starts it fresh"), but the 5 grounding agents' structured results survived in
`subagents/workflows/<run>/journal.jsonl`. I recovered them with a one-off python parse. A small
disposable (Q-0105) helper that takes a run-id (or journal path) and emits a readable markdown of each
agent's returned result — so an interrupted ultracode run is salvageable instead of wasted — would pay for
itself the first time a long fan-out gets cut off. Grep-checked `docs/ideas/` — not present.

## ⟲ Previous-session review (Q-0102)

Previous session: **PR #1776 (Q-0241)**. **Did well:** the four-homes durable-documentation pattern
(router + model doc + plan amendment + CLAUDE.md pointer) made Q-0241 land coherently, and the grounding
this session confirmed the five homes are mutually consistent + the reversibility rider is sound.
**Missed:** it did **not** update the *live* ledger — `current-state.md` kept saying readiness HOLDs on the
two owner gates, and `roadmap.md` §S3 kept the pre-consolidation framing. That is exactly the drift this
session had to fix, and Lane E called it "the single most consequential drift." **System delta:** a
governance change that *retires a gate* should sweep the live-status docs (current-state, sector files,
roadmap) in the same PR — worth a checker that flags when a router Q whose title mentions "gate/retire"
lands but `current-state.md` still names the retired gate. That would have caught #1776's omission
automatically (enforce-don't-exhort, Q-0132).

## ▶ Next action

Owner: start a **Claude Fable 5** session at **`/effort ultracode`** and paste the §7 prompt from
`docs/planning/rebuild-final-review-fable5-ultracode-brief-2026-07-07.md` — ideally *inside* a Claude Code
Project if the EAP is accepted, so the coordinator + memory carry the review → repo-prep → build. That
session runs the final review (A–H), produces the Projects product review for Anthropic, and actively
preps the repo + fixes live-bot bugs under Q-0241 (never-wait). This prep session already cleared the
live-ledger drift so the Fable-5 budget goes to open questions, not reconciliation.

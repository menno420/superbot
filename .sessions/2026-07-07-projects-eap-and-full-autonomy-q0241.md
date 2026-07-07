# 2026-07-07 — Claude Code Projects EAP for the rebuild + Q-0241 (remove owner gates, never-wait)

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). Docs/config-doc only (no
> `disbot/` runtime code): `check_docs.py --strict` (new `ideas` + `owner-guidance` docs reachable) and
> `check_current_state_ledger.py --strict` both green (ledger note = benign newest-merge lag).

## What this session did

Two owner inputs, both durably documented:

1. **Evaluated the Claude Code Projects EAP** (owner-supplied invite PDF). Extracted it and confirmed
   the key question: it is the **Claude Code environment**, *not* claude.ai Chat/Cowork projects (the FAQ
   says they share no data). Mapped its coordinator + shared-memory + routines + session-sidebar model
   onto the canonical rebuild plan's "agent fleet, one session per band, claim-per-subsystem"
   orchestration. New idea doc `docs/ideas/claude-code-projects-for-the-rebuild-2026-07-07.md` (+ README
   index entry).

2. **Owner directive Q-0241 — remove the owner gates from the rebuild; never-wait autonomy.** Owner
   (in-session): *"get rid of the owner gates/blockers … build everything in logical order and live test
   it so I can see the results in a server, but it should never wait for me, if I don't say something it
   should be considered done."* Applied directly (Q-0106 in-session exception). Extends Q-0240
   (decide-and-flag) → decide-and-proceed. Control model shifts from *approval-before-execution* to
   *reaction-after-visibility*: no G1/G2/👤 gates, live-test replaces owner verification, silence =
   consent = done. **Durable homes:** router `Q-0241`; `agent-decision-authority.md` § Q-0241;
   `rebuild-canonical-plan-2026-07-06.md` amendment stamp (G1/G2/👤 retired); `.claude/CLAUDE.md`
   § Act-vs-ask pointer (owner-directed, provenance Q-0241).

## ⚑ Self-initiated

The rule change itself was **owner-directed** (ships with its provenance Q, not self-initiated). Two
**decide-and-flag** calls I made within it (per Q-0240, flagged here for the owner's veto):

- **The reversibility rider.** "Never wait" is implemented in full; but for the **destructive tier only**
  (prod data import, CUT-3 token swap, deleting old-bot data) the coordinator executes via the
  reversible path the plan already specifies (shadow-first, N=7d rollback, reverse-import valve) — *not a
  gate* (zero pause), just keeping a reaction window open so the owner's "say-something-to-undo" can land.
  Rationale: reaction-after-visibility only has teeth while the thing is still reversible when he reacts.
  **Veto available** → straight destructive execution if he wants zero retained reversibility.
- **Scope = the rebuild program.** Q-0241 governs building `superbot-next`; the **live production bot**
  keeps its Q-0213 `*Delete`/`*Restore` brake (real user data) until the owner generalizes it. Rationale:
  his described scenario is the fresh/shadow build he watches, not prod. **Veto available** → extend to
  all work.

## 💡 Session idea (Q-0089)

**A "silence-window digest."** Q-0241 makes the owner's control *reaction-after-visibility* — but
reacting requires a low-friction surface for "what got built + decided while I was away." Idea: the
coordinator emits a rolling **digest since the owner last spoke** — new PRs merged, live-test results
(with server links/screenshots), and every decide-and-flag call (decision · rationale · reversible-until)
— one skimmable feed. It turns "silence = consent" from a blind default into an *informed* one: the owner
consents by not objecting to a digest he can actually skim, not to invisible work. Pairs with the EAP's
native status roll-ups; advisory/disposable to start (Q-0105). (Grep-checked `docs/ideas/` — not present.)

## ⟲ Previous-session review (Q-0102)

Previous distinct session: **Q-0240 decide-and-flag** (`2026-07-06-fable-decision-authority…`). **Did
well:** it cleanly reframed the safety brake as "decided-and-flagged-for-veto, not blocked" and built
the `agent-decision-authority.md` model doc — which is exactly why today's Q-0241 slotted in as a *§
extension* rather than a rewrite. Good, extensible structure. **Missed / could-have-anticipated:** it
kept one hard "stop-and-wait at execution of irreversible" row without noting the obvious next question —
*what replaces owner verification if that brake is also removed?* Today's answer (live-test-in-server +
silence=consent) was latent in the rebuild's own verification substrate (layer V, Arm-D live testing).
**System delta:** the durable-homes pattern worked (router + model doc + plan amendment + CLAUDE.md
pointer, all cross-linked) — worth codifying as the standard shape for any owner governance change, so
each one lands in exactly those four homes and none drifts. That standard shape is what let a
context-reset mid-session resume without losing the thread.

## ▶ Next action

Owner-facing: **accept the EAP invite** and stand up one Project (scope `superbot`; Custom Instructions =
the Q-0241 model + reversibility rider) — or veto either flagged call above. Program-wise, Q-0241 unblocks
canonical-plan §5: the coordinator can run steps 1–4 (kit tail ①, Phase-2.5 A/B, `check_amendments.py`,
Stage-2 walk) and proceed into repo creation without a go/no-go sitting. Note #1775 (a
`superbot-rebuild-phase-2.5` PR) already merged — the rebuild is in motion; this session removed its
owner-gate friction just in time.

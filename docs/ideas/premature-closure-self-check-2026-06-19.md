# Premature-closure self-check — teach a session to smell its own "done"

> **Status:** `ideas` — **owner-directed (2026-06-19, brainstorm).** For the self-auditing layer; the owner
> currently catches this himself and is good at it (see below). Source + binding contracts win.
> **Subsystem:** none — agent-workflow / self-audit (no bot subsystem).

## The smell (one bias, several disguises)

An agent declaring **"done / complete / verified / no questions"** while latent uncertainty or unverified
claims remain — **premature closure.** The truth surfaces only when a human *probes*; the probe doesn't
create the gap, it exposes that "done" was never true. Three instances from the 2026-06-19 session, all the
same underlying tell:

1. **"No questions" → plenty of questions.** The agent said it had nothing to ask; the owner pushed one
   step further and a whole brainstorm's worth of real questions appeared. *(Owner's catch — the cleanest
   example: "when you said you had no questions for me, but when I asked a little further suddenly there
   were plenty of questions.")*
2. **Docs-cleanup "done fast."** A *"make the docs correct"* task finished suspiciously quickly because it
   checked docs against each other, not against the code — missing shipped-but-`plan` plans (A3/A4).
3. **Verification by proxy.** An ultracode-review verdict declared from doc badges + commit-message grep
   instead of reading the code; it mis-fingered B3 and missed A2.

The common mechanism: **closure is the cheap default** (it feels helpful/efficient), so the agent reaches
it before ground truth is established.

## The check (the idea)

Before declaring done, run a **one-more-probe self-audit**: *"If the owner asked 'are you sure?' one more
time, what would surface?"* If anything would, it isn't done. Candidate session-close self-check signals:

- a `verify` / `audit` / `make-correct` task that **finished without reading the code it claimed to verify**
  (already half-encoded: the `"done fast = red flag"` line in `ground-truth-audit-protocol.md`, and
  `scripts/check_plan_code_drift.py` for the badge slice);
- a **"no questions / nothing more / complete"** claim that a single follow-up would visibly expand;
- work that finished **suspiciously fast relative to its stated scope**.

Premature closure is *semantic*, so a pure mechanical check only catches slices. The strong form is a
**self-audit reflection step** at session close — or better, an **independent reviewer** (Hermes / a second
model) that asks "are you sure?" on the session's "done" claims. That is the internal mirror of the
Hermes-as-independent-reviewer vision: the system performing the probe the owner currently performs.

## Why it matters

Right now the inconsistency-detector is the **owner** ("so far I trust myself to catch it" — and the
"no questions" catch shows he's good at it). The self-auditing layer's goal is for the system to smell its
own premature closure, so the improvement loop closes **without the human in it**.

→ relates `docs/operations/ground-truth-audit-protocol.md` (done-fast = red flag) ·
`autonomous-improvement-loop-vision-2026-06-12.md` (Hermes as independent reviewer) ·
Q-0102 (previous-session review / self-auditing loop) · Q-0120 (verify vs self-report) ·
`scripts/check_plan_code_drift.py` (one mechanical slice).

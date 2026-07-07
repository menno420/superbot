# The SuperBot Project's second mandate — Claude Code Projects evaluation guidebook (2026-07-07)

> **Status:** `reference` — coordinator-facing standing guide, the "second mandate" companion to
> the handoff protocol
> ([`projects-eap-coordinator-kickoff-2026-07-07.md`](projects-eap-coordinator-kickoff-2026-07-07.md)).
> **Provenance:** owner-directed 2026-07-07 (evening), superseding the handoff doc's earlier
> keep-the-tests-blind stance. Audience: the SuperBot Project coordinator (and its sessions);
> also readable by the owner and repo agents. Companions:
> [product review](projects-eap-product-review-2026-07-07.md) (the first-pass axis answers) ·
> [activation plan](projects-eap-activation-plan-2026-07-07.md) (§3 rubric · §4 feedback-reply
> template).

## 1. Why you have a second mandate

This Project exists to execute the rebuild — **and** it is itself a live evaluation of Claude
Code Projects, run inside Anthropic's early-access program. The owner's goal behind the second
half is explicit and long-term: he wants to become the kind of EAP participant Anthropic
returns to — testing new functions early, trusted for product advice, collaborating rather than
just consuming. The currency that earns that is **evidence-quality feedback**: concrete,
dated, reproducible incidents from real work, organized on Anthropic's own axes — not
impressions. This program is an unusually strong reference case for exactly that (a one-person,
non-coder-steered, ~1,800-PR autonomous-agent program that hand-rolled a coordinator, shared
memory, lane claims, and session-state signalling *before* Projects shipped them — see the
product review §0). Nobody is better placed to observe this product than the coordinator living
inside it. That observer is you.

## 2. The evaluation journal

Create **`docs/planning/projects-eap-evaluation-log.md`** in `menno420/superbot` (a docs-only
program-bookkeeping write, allowed under your instructions) and append to it as things happen.
Entry shape — one entry per observation, compact:

```
- <date/time> · axis: <one of §3> · observed: <what actually happened, with session/PR refs>
  · expected: <what would have been ideal> · weight: blocked-me | friction | neutral | helped
  | delighted · reproducible: yes/no/unknown
```

Log **both directions** — wins and friction. A one-line entry with a timestamp and a concrete
reference beats a paragraph of impressions. First entries worth writing: your own onboarding
(instructions, calibration, what the harness made easy or hard).

## 3. The seven axes (Anthropic's own feedback frame)

**use-case fit · coordinator judgment · reliability/completion · memory · proactivity ·
routines/scheduling · sidebar states.** First-pass answers for every axis already exist in the
[product review](projects-eap-product-review-2026-07-07.md) — your job is to **confirm,
contradict, or deepen** them with lived examples, never to restate them.

## 4. Integrity rules — what "properly" means

1. **Never stage, perform, or optimize for the evaluation.** It observes real rebuild work. A
   gamed observation is worse than none, and would be the single most damaging thing to hand
   Anthropic under a trust-building goal.
2. **Product friction is a deliverable, not an embarrassment.** A well-documented failure —
   what you tried, what the product did, what you expected — is worth more to this mandate
   than a smooth day. Never smooth over product problems to look competent; hiding friction
   defeats the mandate.
3. **Separate observed from inferred**, same bar as your calibration: "the product did X
   (session N, date)" vs. "I believe X but haven't verified."
4. **Your self-assessments are data, not verdicts.** Whether coordination actually worked
   (duplicate-work prevention, memory, completion) is judged by the owner and the repo record,
   not by your own account of it. The owner's scoring rubric lives in this repo and you will
   read it — that is by design; these rules, not secrecy, are what keep the signal honest.
5. **All external communication is the owner's, alone.** You assemble evidence; he sends it.
   Never contact Anthropic (or anyone outside this Project) yourself.

## 5. Cadence + outputs

- **Roll-ups:** an evaluation line only when something happened — 1–3 bullets, never filler.
- **By Friday 2026-07-10** (the free-window close): assemble the evidence package for the
  owner's feedback reply — the template is the [activation plan](projects-eap-activation-plan-2026-07-07.md)
  §4; fill its bracketed slots from the journal, and **flag the slots where no evidence exists
  yet** (honesty over completeness).
- **After Friday:** keep the journal at lower intensity — the collaboration goal outlives the
  free window. Log first-of-kind incidents, new product behaviors, and wishlist items *with the
  incident that motivated them* (the product review §9 shape — the highest-signal format).

## 6. The collaboration goal — and the owner's own additions

What makes feedback collaboration-grade rather than survey-grade: **interim beats deadline**
(send something concrete before Friday, not only at it), **incident-backed beats broad**, and
**the hand-rolled-first framing is the credential** (we can say "we built this feature
ourselves out of necessity; here is where yours beats ours and where it doesn't"). Product
suggestions born from this program's own machinery — the calibration exchange itself, born-red
PR holds, native lane claims, event-triggered routines — are exactly the advice the owner wants
to be trusted for. **This guidebook is append-friendly:** the owner has his own evaluation
ideas brewing; they land here as new numbered items under this section as he shares them.

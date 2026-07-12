# Fleet vocabulary — the owner's shorthand → what Claude does

> **Status:** `owner-guidance` — the owner's shorthand command dictionary. The point:
> the owner types a **short word (+ an object)**, and Claude knows the full workflow +
> the questions to ask, without re-explaining each time. **Owner-owned:** add / rename /
> retune entries freely; Claude proposes new ones after a session that would have
> benefited from one. Executable versions live as **skills** (`.claude/skills/<name>/`);
> this file is the index + the words that map to them.
>
> **The verb + object pattern (revised 2026-07-11, owner-directed).** Every word here
> is a general **verb** that dispatches on the **object** you point it at — "review"
> works on the fleet, a repo, a report, a prompt, or a PR; "explain" works on any
> product or doc. Claude picks the mode from the object, says which mode it picked,
> and never stalls on the dispatch. This is what keeps behavior consistent across
> sessions: the word means the same *kind* of action everywhere, scaled to its object.
>
> **How to use:** say the keyword, optionally with an object/focus (e.g. "review
> venture-lab", "explain the mining game"). If an entry says *ask first*, Claude runs
> the listed questions before acting; if it says *decide-and-flag*, Claude just does it
> and flags choices. Unknown word → Claude asks what you mean and offers to add it here.

## Core words

| Word | Verb meaning (dispatches on the object) | Skill | Default behavior |
|---|---|---|---|
| **review** \<object\> | Critically assess the object with evidence and an opinionated verdict. Objects: **(none/fleet)** → full fleet night/status review (per-lane digest, fix-first plan, owner-action queue) · **a repo** → single-repo deep review (shipped work vs claims, open surface, quality, review-worthiness score) · **a report/doc** → claims-vs-ground-truth + gaps + keep/fix/cut · **a prompt** → failure modes + improved rewrite · **a PR** → `/review` · **a diff** → `/code-review`. | `/fleet-review` (dispatcher) | decide-and-flag; deep by default; documents durable findings; asks only if the object is genuinely unclear |
| **status** | **Quick** health sweep of the object (default: fleet) — roster + freshness + anything stale/stuck/blocked. No deep report. The 60-second "is anything on fire" check. | (`/fleet-review` light) | roster-only + flag anomalies; no fan-out unless something looks wrong |
| **routines** | Audit the **routine → repo → model** config (fleet-wide or one lane): which routine drives which lane, is its repo attached (the known spawn failure), does its model match intent → the **owner-attach checklist**. | (part of `/fleet-review`) | per-routine table + owner action list |
| **explain** \<object\> | Plain-language explanation of the object — what it is, what it does, who it's for, how to use/deploy it, what's left for the owner. No jargon, no repo-archaeology required of the reader. Objects: a product, a repo, a doc, a decision, "everything" → the product catalog. | — (catalog: superbot `docs/owner/product-catalog.md`) | answer in chat; update the catalog when the explanation is durable |
| **queue** | Show the current **owner-action queue** — only genuinely owner-only items, deduplicated, each with WHAT/WHERE/HOW/UNBLOCKS; everything agent-decidable already decided-and-flagged. | — (canonical: fleet-manager `docs/owner-queue.md`) | verify items against live state before showing; retire stale items on sight |
| **clean** \<object\> | Hygiene pass on the object (default: fleet PRs) — stale open PRs merged/closed with evidence, dead branches flagged, drifted docs fixed. Safe actions executed; ambiguous ones listed with a recommendation. | — | merge only green+complete, close only clearly-dead-with-reason; ambiguous → flag |
| **plan** | Turn current state into a **prioritized plan for the day** — fix-first list, owner-action queue, what to watch. Standalone or the tail of a review. | — | decide-and-flag; asks only on a real product fork |
| **ship** | Drive the current session's work to a **merged PR** — born-red card → complete, CI green, merge (or close). | `/session-close` | full close-out checklist |
| **groom** | Move one idea one step down its lifecycle (idea → plan → build). | `/groom-ideas` | one idea, safe lane |

## Conventions Claude follows for every word

- **Cite, don't assert** — every load-bearing claim links a PR / commit / file / CI run.
- **Honesty over polish** — "no report yet", "stuck on X", "budget overran" are the
  valuable findings; never paper over a quiet or broken lane.
- **Verify against ground truth (Q-0120)** — a doc's claim is checked against the
  tree/GitHub before it's repeated as fact.
- **Family-level model names only** (fable-5, opus-4.8, sonnet-5) — never exact IDs.
- **Decide-and-flag** reversible calls; route only genuine product/irreversible forks
  to you.
- **Guardrails carried in from the 2026-07-11 sessions:** no `delete_trigger` /
  destructive approval-gated ops unless you say so; in Project sessions never
  self-merge (classifier wall). **Hub/live sessions don't just *can* merge — they
  MUST (Q-0269, 2026-07-12): any mergeable PR in finished state (green, complete,
  READY) is merged immediately by the agent; directing the owner to a green PR is
  a workflow failure.** Park-READY+green is a Project-seat fallback only, and only
  after a real classifier denial.

## Growing this file

When a session would have gone faster with a shorthand, Claude proposes a new row here
(word · means · skill · default) at session close. The owner keeps or drops it. When a
word's workflow is stable, Claude promotes it to a real `.claude/skills/<word>/SKILL.md`
so it's one command. New words follow the **verb + object** pattern above — a word that
only works on one hardcoded object is the anti-pattern this file was revised to remove.
Disambiguation note: a code-diff review is `/code-review`, a GitHub-PR review is
`/review`; the bare word "review" routes through the `/fleet-review` dispatcher.

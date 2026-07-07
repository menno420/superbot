# 2026-07-07 — SuperBot Project coordinator: kickoff revision + calibration exchange design

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). Docs-only (no
> `disbot/` runtime code): `check_docs.py --strict` and `check_current_state_ledger.py --strict`
> both green (ledger listings = benign newest-merge lag past marker #1800).

## What happened

Owner-directed, docs-only session in two parts (PR #1811):

1. **Part 2 — live calibration discussion.** Stated back the goal + decided-vs-open inventory;
   surfaced the activation-plan anti-pattern tension (owner's live direction overrides), the
   never-wait/calibration-gate trap, the read-mostly wrinkle, and the model-allocation conflict.
   Owner replied with **UI screenshots** that corrected the EAP PDF: the Project **"SuperBot"
   already exists** (both repos connected), **Model is a per-Project default (currently Fable
   5)**, Effort default High, **Project instructions are sent with each new session**, and the
   **coordinator is archivable** (the calibration retry lever). Owner: free window ends Fri
   7/10, "free" scope unverified (he watches usage draw); apply recommendations I'm sure of.
2. **Part 3 — deliverables** in `docs/planning/projects-eap-coordinator-kickoff-2026-07-07.md`
   (rewritten wholesale):
   - **A.** Revised **Custom Instructions** (thin, pointer-first, plan-wins clause, hard repo
     split incl. never-clone-as-base/Q-0247, decision model + destructive rider, the
     questions-aren't-work-orders line, owner-actions protocol, reporting + write-back rules)
     and **kickoff message** (steps 1–6 status incl. public-until-flip, Q-0247 step-7 fold,
     step-8 guardrails as the riskiest unattended stretch, Friday pacing, owner-action seed).
   - **B.** NEW **calibration exchange** — 12 items in 3 blocks (explain-back with scenario
     traps · verify-don't-assume self-assessment with unfakeable probes · own two-repo read),
     an owner-facing reading key, and verdict mechanics (Archive-coordinator = retry).
   - Cross-edits: canonical plan §5 step-6 fact amendment (owner-directed: repo exists, PUBLIC
     deliberately, flip checkpoint step 8 / hard before step 15) + §11 pointer; launch-index
     row ④ re-route + owner checklist; steps-6–8 brief route banner; S3 sector + main-table
     pointers.

Also on sight (Q-0166): deleted two stale claim files whose sessions merged without cleanup
(`projects-eap-coordinator-wiring.md`, `projects-eap-kickoff-repo-first.md` — no open PRs on
either branch; their changes are live in the kickoff doc / plan).

## ⚑ Self-initiated

- The canonical-plan §5 step-6 row amendment (owner-directed fact, applied with provenance) and
  the launch-index/brief/ledger re-route pointers — all docs-only, reversible, flagged here.
- Decisions applied under the owner's "apply your recommendations if you are sure" grant:
  four-product-tests kept OUT of the coordinator's instructions (behavioral-test contamination);
  latency-independent owner-actions protocol; owner reads calibration answers + sends kickoff
  himself (nothing auto-flows); thin pointer-first instructions with a plan-wins clause.

## 💡 Session idea (Q-0089)

**Calibrate-before-delegate as a portable kit template.** The §3 calibration exchange
(explain-back scenarios with determinate composite answers + verify-don't-assume harness probes
+ an owner reading key + the archive-and-retry lever) generalizes to every future
repo/Project/agent handoff — it is the entry-point sibling of the kit's Q-0254
understand-and-reflect doctrine (that rule fires *inside* a session; this fires *before standing
authority is granted*). Once proven on the SuperBot Project, promote it to
`substrate-kit/src/engine/templates/` alongside CONSTITUTION.md.tmpl. (Dedup-grepped
`docs/ideas/` — no calibration/handoff-exchange idea exists.)

## ⟲ Previous-session review (Q-0102)

Previous session in this lane (the repo-first kickoff-doc update, merged ~#1810): **did well** —
it made the owner-creates-the-repo path primary *before* the owner actually did exactly that,
so today's fact fold was a row edit, not a rewrite. **Miss:** it left its claim file behind
(one of the two stale claims deleted today), and its predecessor did too — two instances of the
same leak in one day. **Workflow improvement:** claim-file cleanup has no guard;
`scripts/check_session_log.py` (or a tiny CI advisory) should flag any `docs/owner/claims/*.md`
whose branch has no open PR — enforce-don't-exhort (Q-0132/Q-0194) applied to the claim
lifecycle's *exit* half. Routed as a candidate guard, not built here (docs-only session).

## Addendum (same session, second PR — after #1811 merged)

Owner follow-up: the Project's purpose is **dual** — rebuild execution AND evaluating Claude
Code Projects itself, with the explicit long-term goal of earning a standing collaboration
channel with Anthropic (trusted tester/advisor). Shipped: **the evaluation guidebook**
(`docs/planning/projects-eap-evaluation-guidebook-2026-07-07.md` — journal home + entry
template, the seven EAP axes, integrity rules, Friday evidence package, append-friendly §6 for
the owner's own ideas) + folds into the handoff doc (SECOND MANDATE paragraph in the
instructions; calibration intro line + new item 13 with reading key; kickoff second-duty
paragraph; Friday owner-table row; new §6). **This supersedes the earlier
keep-the-four-tests-blind decision (⚑ owner-directed)** — and rightly so: the tests were
committed in the repo the coordinator is told to read, so the secrecy was illusory; integrity
now rests on the guidebook's never-perform rule + record-based verdicts instead.

## Addendum 2 (same session, third PR — after #1812 merged)

Two owner ratifications folded: (1) **thin instructions / inclusive kickoff split confirmed** —
§4's kickoff message expanded into the one-time full imprint of the program (mission paragraph,
how-we-work, first-stretch steps 7–8 with guardrails, session structure, second mandate with
the owner's mutual-fit framing + the write-to-Anthropic-tomorrow deadline, pacing, rhythm),
with an explicit "never outranks the plan" clause; instructions untouched. (2) The owner's
**mutual-fit framing folded into the activation plan §4 draft reply** (opening paragraph in his
voice: purpose-built reviewer × perfect-timing migration) + owner send-intent recorded
(~tomorrow, interim beats deadline; journal feeds the bracketed slots).

## Addendum 3 (same session, fourth PR)

**Tempo correction (owner):** the "multi-month" framing was mine, not the owner's — the plan's
own kernel estimate is ~5–8 days and the owner intends the whole migration attempted **inside
the 3-day free window** by a continuous Fable fleet, correctness always over speed. Fixed all
four committed month-scale claims (product review §1, activation plan anti-pattern + reply
draft, kickoff second-mandate). **Final owner decision panel (6 Qs)** applied to the kickoff:
tempo = 3-day *stretch goal* not deadline, correctness first; post-Friday-if-undecided =
continue on account default + report usage draw, never pause; substrate-kit = **Public**;
roll-up = **~09:00 Europe/Amsterdam**; test **bot + token already live** (only the guild + a
possible separate application to avoid gateway collisions remain); calibration verdict =
**correct in-thread**, Archive-and-rerun reserved for fundamental misses (repo-split /
never-wait / capability overclaim). Model note: this addendum finished under Opus 4.8 after a
Fable server error mid-edit; no content impact (edits were already placed pre-error).

## Addendum 4 (same session, fifth PR)

**First-turn framing (owner):** the calibration message had the capability/limits *questions*
(Block B) but framed the whole turn as "prove you understood the program" — the owner asked to
make **self-discovery of capabilities and limits an explicit main goal of the first turn**.
Rewrote the §3 intro to name two jobs (understand the program · map your own operating
envelope) and elevate self-discovery to "just as important," tied to why it matters (running
unattended under never-wait; discovering a limit here beats mid-kernel-band) and reframing
Block B as genuine self-discovery, not a quiz. Owner-facing "why this exists" prose updated to
match. Instructions (§2) deliberately untouched — this is first-turn-specific, and §2 stays
thin by design.

## Addendum 5 (same session, sixth PR — the coordinator's calibration came back + scored)

The owner launched the Project and pasted the coordinator's calibration answers back. Scored
strong pass (12/13 at-or-above bar): **Q7 verified against live GitHub** (superbot HEAD
`fe297a8`/#1816 exact — it read live state, didn't guess; also correctly caught its own
7-behind local clone `700bdce`/#1809). Standouts: named Q-0244/A-10/two-lane on slash
verification, derived "start step-14 telemetry early in parallel," self-identified "mistaking a
child's silence for success" as its top never-wait risk, discovered it likely **can't enforce
per-band model allocation from the coordinator seat** (confirms the Part-2 uncertainty), and
answered the permission-prompt unknown with "I don't know + here's a 10-min probe."

**One fork surfaced + owner-resolved:** answer #5 proposed fixing OLD-bot runtime bugs itself
and auto-deploying, colliding with the "never touch disbot/" instruction. **Owner ruling
(fix-and-flag-low-risk):** contained bugs-first fixes allowed with L-21 re-capture + a flag;
money/auth/user-data/*Delete-*Restore stays surfaced-and-gated. Applied to §2 REPOS block + the
A5 reading key; the binding in-thread correction (this + sync-before-trusting-local +
run-the-permission-probe + use-Project-default-models) was handed to the owner to send before
the kickoff. ⚑ This is a durable owner decision softening a prior instruction — recorded here +
in the kickoff doc; route to the question router if a Q-number is wanted.

## Addendum 6 (folded into the same PR #1817)

Owner caught a second drift while reading: the coordinator's A2 said "bootstrap the kit into
superbot-next" — skipping the Q-0247 dedicated-repo step. Root cause: the **canonical plan's
§5 step-7 row was silent on Q-0247** (still "bootstrap the kit: adopt"), so a coordinator citing
the plan reads direct-adopt-into-superbot-next. The kickoff §4 was already correct (extract →
substrate-kit repo → adopt from it). Fixed the plan step-7 row to state the Q-0247 sequence
explicitly: extract `superbot/substrate-kit/` → `menno420/substrate-kit` (permanent home + source
for kit-lab/trading), then superbot-next adopts FROM that repo — never a copy of superbot. Added
the same as an explicit item to the owner's in-thread correction so the live coordinator doesn't
proceed on its A2 reading.

## Addendum 7 (seventh PR)

Owner steer: don't send the coordinator chasing a separate doc when the content is (now)
documented — inline it or drop the pointer. Since the plan step-7 row now states the Q-0247
sequence (addendum 6) and the kickoff §4 describes steps 7–8 substantively, the kickoff's hard
pointer "the work order for this stretch is [steps-6–8 brief]" was redundant doc-chasing.
Removed it: §4 step-7 is now self-contained (extract → substrate-kit repo → adopt-from-it with
the `dist/bootstrap.py adopt` command + the permanent-home/source rationale inlined), and the
stale "one ruling the plan text predates" phrasing is fixed to "plan §5 step 7, per Q-0247"
(the plan no longer predates it). The brief stays a valid planning artifact (launch-index
references it); only the coordinator prompt's dependency on it is removed.

## Addendum 8 (eighth PR)

Owner directive: "don't spare on agents — I want to see what it's capable of." Added to the
kickoff §4 SESSIONS AND STRUCTURE paragraph as an explicit fan-out mandate: use the fleet
aggressively, max useful concurrency, prefer parallel workers over a serial crawl, don't ration
agents to save tokens (explicit owner directive, not a budget). Bounded only by real
dependencies + correctness — the kernel strand S1→S9 is near-linear (agents there = within-band
fan-out, not fake cross-band parallelism per the plan's own D-19 correction), the port bands
(step 13) are where wide claim-per-subsystem fan-out pays off. Also delivered the complete
finalized prompt (corrections + full kickoff body) to the owner to paste.

## Addendum 9 (ninth PR — coordinator live; step-8 flag + working-relationship inquiry)

Coordinator accepted the program and ran an aggressive first stretch (4 parallel workers:
step-7 extraction, evaluation-journal PR #1820 born-red, permission probe, sync/brief). Its read
of steps 7–8 was correct (understood step 7 as making the kit's home *canonical* upstream; step-8
gate risk symmetric). Two owner asks handled:

1. **Step-8 enforcement flag.** The coordinator's probe confirmed permission prompts fail-fast
   (don't hang — good for never-wait), children run Fable 5 (Project default = heavy model, so
   the B8 model-allocation worry is moot), and repo *creation* is available (substrate-kit in
   the allowlist). But the probe did NOT test branch-protection/ruleset/OIDC management — a
   different API surface no GitHub MCP tool exposes — so step 8's *enforcement* half (making the
   six gates required, branch protection, OIDC) is likely owner-only. Added to §5 owner-action
   forecast + relayed as the one cheap correction.
2. **Working-relationship inquiry (new §7).** Owner-requested question set to learn the best way
   to work with the coordinator (finalized-outside vs. brainstorm-in-Project, context/memory
   mechanics, coordinator-vs-child-session, steering, decisions-vs-options, load, stuck-signals).
   Distinct from calibration (self-model not verifiable facts → confirmed by observation; doubles
   as the write-back/memory evaluation tests). Renumbered old §7 → §8.

Live coordinator findings journaled by it: no scheduled-wake primitive (roll-up on worker-timer
fallback), no direct coordinator→session channel (steering relays through a worker), destructive
git ops in dispatched sessions auto-denied by the classifier as "untrusted coordinator context."

## Addendum 10 (tenth PR — consent-wall question added to §7)

Owner-requested after hitting the step-7 consent wall live (first push to a public repo needs
the owner's in-session consent; a relayed go-ahead doesn't clear it — same untrusted-context
class). Added a new Q9 to the §7 working-relationship inquiry asking the coordinator to explain
the consent/permission mechanic from its side: which actions need in-session consent vs.
autonomous; per-action/session/repo/first-time; whether it recurs on every superbot-next push
or clears once a repo has content; what the owner can pre-authorize + where + how to scope it to
the two known repos without disabling safety broadly; the owner habit that minimizes the tempo
tax. Renumbered "what you'd change" 9 → 10; intro updated. My advisory to the owner this turn:
consenting is safe (kit content is *already* public as a superbot/ directory → the republish
exposes nothing new; secret-scan clean), the wall is correct outward-facing-publish safety not a
bug, and the durable fix (if it recurs per-session) is a *scoped* Project-settings
pre-authorization for the two program repos, not a blanket off-switch. Watch: the wall gates
superbot-next's first commit too (one consent covers both); the tell for a real tempo tax is if
the *second* push (a kernel band) also stalls.

## Docs audit (Q-0104)

`check_docs.py --strict` ✓ · `check_current_state_ledger.py --strict` ✓ (exit 0; #1802/#1804/
#1805/#1810 listings = benign newest-merge lag, newer than marker #1800) · new/edited docs all
reachable from current-state → S3 → kickoff doc; the calibration exchange lives in its durable
home (the kickoff doc), and this discussion's conclusions are folded there, not chat-only.

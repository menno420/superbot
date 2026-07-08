# Session — Finalize the Anthropic EAP email

> **Status:** `complete`

## What this session did
Owner-directed finalization of the EAP email (`docs/planning/projects-eap-anthropic-email-2026-07-08.md`),
after the Project campaign + coordinator self-audit (#1859) went terminal. Folded into Part 2:

1. **Two-layer workflow explanation** — why a separate directing chat runs *alongside* the Project:
   the coordinator has no shell, a ~4 KB brief cap, and can't take destructive/settings/first-publish
   steps even under a standing grant, so Projects is a coordinated-**execution** substrate, not yet a
   management console. (Complements Part 1's operator-side version of the same point.)
2. **"What we stress-tested" beat** — the 3-wave adjacent-lane campaign (7 PRs, 0 collisions, dedupe
   held at claim *and* merge level → upgrades the previously-untested dedupe cell) + the coordinator
   self-audit graded against git (≈0.98 precision, one *inherited* error, memory honestly scoped to
   same-day pre-compression recall). Links `docs/eap/campaign-self-audit-2026-07-08.md`.
3. **Honest 7-axis scorecard** — judgment/reliability/proactivity/memory[scoped] pass · use-case fit
   partial · scheduling FAIL · sidebar states FAIL. Directly answers Anthropic's own feedback frame,
   filling the previously-thin axes.
4. **Resolved permission finding** — live probe (owner screenshots): scheduling tools (`send_later`/
   `delete_trigger`) prompt in EVERY mode; everything else silent incl. GitHub MCP write; the
   two-vantage split reproduced (agent sees clean success, operator sees Deny/Allow). Banked as two
   eval-log entries; folded into friction as the clearest single proof of the two-consumers thesis.

Also: dual-review closing now points at the real `docs/eap/` report; verifiability appendix extended.
Docs-only; `check_docs --strict` green. **Email is send-ready except Part 1 (owner-written).**

## ⚑ Open for the owner
- **Write Part 1** — the only remaining section.
- Optional trims flagged inline: the framing paragraph, and the "manage vs execute" beat now appears
  in both Part 1 (operator feeling) and Part 2 (agent mechanism) — intentional (two vantages), but cut
  one if it reads repetitive to you.

## 💡 Session idea (Q-0089)
Turn the campaign self-audit into a **standing "memory-audit routine"** that re-runs the recall
questions after a context-compression event / in a successor session — the self-audit explicitly
couldn't measure durable Project memory (only same-day retention), and a scheduled re-probe is the
only way to get that number. Distinct from the one-off audit and from the capability-self-probe idea;
it's the *durable-memory* measurement the evaluation still lacks. Noted here; file it if the EAP
continues past the trial.

## ⟲ Previous-session review (Q-0102)
Previous session (the coordinator self-audit, #1859) was exemplary EAP work: graded from-context
recall against git, led with misses, and *refused the easy win* by scoping its 0.98 memory score to
same-day retention instead of banking it as "great memory." **What it surfaced for the system:** the
one error (16 vs 15 tests) was **inherited** from a worker's own miscount — self-reported counts
propagate unverified. **Improvement:** a trivial checker that counts `def test_` functions and
compares to any number a card/PR body asserts would have caught it; the same class at runtime-code
scale is how false confidence compounds. Worth a lane next campaign.

## 📋 Doc audit (Q-0104)
`check_docs --strict` green. Email doc, two new eval-log entries, and the verifiability appendix are
mutually consistent; `docs/eap/campaign-self-audit-2026-07-08.md` referenced correctly (it exists on
main via #1859). Nothing from this session lives only in chat. No new binding rule → no router Q.
